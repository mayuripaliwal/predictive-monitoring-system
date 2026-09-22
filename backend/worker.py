from arq import cron
from arq.connections import RedisSettings
import time
import psycopg
from main import MonitorEvent, REDIS_URL
from datetime import timezone,datetime
import httpx
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool
import sys
import asyncio

#create db pool connection
pool=AsyncConnectionPool(
    conninfo=os.getenv("DATABASE_URL"),
    min_size=1,
    max_size=5,
    check=AsyncConnectionPool.check_connection,
    open=False,
)

async def startup(ctx):
    #create a app level persistent httpx async client
    ctx["http_client"]=httpx.AsyncClient()
    await pool.open()

async def shutdown(ctx):
    await ctx["http_client"].aclose()
    await pool.close()

#this function returns the monitor event for a given monitor
#fetch the monitor url and create the monitor event
#handle any exceptions such as timeout or request error
async def check_monitor(ctx,monitor) -> MonitorEvent:
    monitor_url=monitor[1]

    start=time.perf_counter()

    monitor_event=MonitorEvent(
        monitor_id=monitor[0],
        status="down",
        status_code=None,
        response_time_ms=None,
        checked_at=datetime.now(timezone.utc)
        )

    try:
        client=ctx["http_client"]
        response=await client.get(monitor_url,timeout=5)

        monitor_event.status_code=response.status_code

        if 200<=response.status_code<500:
            monitor_event.status="up"
        else:
            monitor_event.status="down"

        monitor_event.response_time_ms=round((time.perf_counter()-start)*1000,2)*100

        return monitor_event
    
    except httpx.RequestError:
        monitor_event.response_time_ms=round((time.perf_counter()-start)*1000,2)*100

        return monitor_event

#this function saves the monitor event in db
async def save_monitor_event(ctx,monitor_event:MonitorEvent):
    async with pool.connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("INSERT INTO monitor_events" \
            " (monitor_id,status,status_code,response_time_ms,checked_at) " \
            "  VALUES (%s,%s,%s,%s,%s)",
            (monitor_event.monitor_id,
             monitor_event.status,
             monitor_event.status_code,
             monitor_event.response_time_ms,
             monitor_event.checked_at))

            await conn.commit()
    

# this function gets all monitors and checks them
async def check_monitors(ctx):
    start=time.perf_counter()
    async with pool.connection() as conn:
        async with conn.cursor() as cursor:
            #TODO: update the query to only fetch monitors whose checked_at<=now() -5 minutes
            await cursor.execute("SELECT id, url " \
            "FROM monitors")

            monitors=await cursor.fetchall()

    if not monitors:
        return 

    tasks_check_monitor=[]
    tasks_save_monitor_event=[]

    #check_monitor for all monitors is performed concurrently
    for monitor in monitors:
        task=asyncio.create_task(check_monitor(ctx,monitor))
        tasks_check_monitor.append(task)

    #return exceptions is false by default here
    check_results=await asyncio.gather(*tasks_check_monitor)

    #save_monitor_event for all monitor events is performed concurrently
    for monitor_event in check_results:
        task=asyncio.create_task(save_monitor_event(ctx,monitor_event))
        tasks_save_monitor_event.append(task)

    await asyncio.gather(*tasks_save_monitor_event)

    end=time.perf_counter()

    print(f"Took time: {end-start} seconds")

class WorkerSettings:
    on_startup=startup
    on_shutdown=shutdown
    functions=[check_monitors]
    #cron job to run check_monitors every 5 minutes
    cron_jobs=[cron(
        check_monitors,
        minute={0,5,10,15,20,25,30,35,40,45,50,55})]
    redis_settings=RedisSettings.from_dsn(REDIS_URL)
    #poll delay is default 0.5 seconds in ARQ, here I set it to 10 seconds to reduce commands usage on Redis Free tier
    poll_delay=10