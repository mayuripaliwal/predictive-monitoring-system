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

if sys.platform=="win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

#create db pool connection
pool=AsyncConnectionPool(
    conninfo=os.getenv("DATABASE_URL"),
    min_size=1,
    max_size=5,
    check=AsyncConnectionPool.check_connection,
    open=False,
)

async def startup(ctx):
    await pool.open()

async def shutdown(ctx):
    await pool.close()

# this fn job is to get all monitors that need to be checked 
async def get_monitors(ctx):
    async with pool.connection() as conn:
        async with conn.cursor() as cursor:
            #TODO: update the query to only fetch monitors whose checked_at<=now() -5 minutes
            await cursor.execute("SELECT name, url " \
            "FROM monitors")

            monitors=await cursor.fetchall()

    if not monitors:
        return 

    for monitor in monitors:
        #TODO: write a fn to check each monitor
        print(monitor)

class WorkerSettings:
    on_startup=startup
    on_shutdown=shutdown
    functions=[get_monitors]
    #cron job to run get_monitors every 5 minutes
    cron_jobs=[cron(
        get_monitors,
        minute={0,5,10,15,20,25,30,35,40,45,50,55})]
    redis_settings=RedisSettings.from_dsn(REDIS_URL)
    #poll delay is default 0.5 seconds in ARQ, here I set it to 10 seconds to reduce commands usage on Redis Free tier
    poll_delay=10