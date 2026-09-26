from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, HttpUrl, AwareDatetime
import httpx
from contextlib import asynccontextmanager
import time
import psycopg
import os
from dotenv import load_dotenv
from psycopg_pool import AsyncConnectionPool
from datetime import datetime,timezone
from arq import create_pool
from arq.connections import RedisSettings
from fastapi.middleware.cors import CORSMiddleware;

load_dotenv()

DATABASE_URL=os.getenv("DATABASE_URL")

#create a db pool
pool=AsyncConnectionPool(
    conninfo=DATABASE_URL,
    check=AsyncConnectionPool.check_connection,
    open=False
)

async def create_tables():
    async with pool.connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("CREATE TABLE IF NOT EXISTS monitors ( " \
            "id SERIAL PRIMARY KEY, " \
            "name TEXT NOT NULL, " \
            "url TEXT NOT NULL UNIQUE" \
            ")")

            await cursor.execute("CREATE TABLE IF NOT EXISTS monitor_events (" \
            "id SERIAL PRIMARY KEY," \
            "status TEXT NOT NULL, " \
            "status_code INTEGER, " \
            "response_time_ms INTEGER," \
            "checked_at TIMESTAMPTZ NOT NULL, " \
            "monitor_id INTEGER REFERENCES monitors(id) ON DELETE CASCADE " \
            ")")

            await conn.commit()
        

#define model for valid urls
class RequestURL(BaseModel):
    url:HttpUrl

#define model for a monitor
class Monitor(BaseModel):
    name:str
    url:HttpUrl

#define model for a monitor event
class MonitorEvent(BaseModel):
    monitor_id:int
    status:str
    status_code:int | None
    response_time_ms:int | None
    checked_at:AwareDatetime

REDIS_URL=os.getenv("REDIS_URL")

@asynccontextmanager
async def lifespan(app:FastAPI):
    #create a persistent httpx async client in app 
    app.state.http_client=httpx.AsyncClient()
    await pool.open()
    await create_tables()
    yield
    await pool.close()
    await app.state.http_client.aclose()

app=FastAPI(lifespan=lifespan)

FRONTEND_URL=os.getenv("FRONTEND_URL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET","POST","OPTIONS"],
    allow_headers=["Content-Type"]
)

RESPONSE_TIME_MS_SCALE=100

# dependency to lease db connections safely
async def get_db():
    async with pool.connection() as conn:
        yield conn

#base api
@app.get('/')
def home():
    return {
        "message":"Backend is working"
    }


#this api creates a monitor for a given url 
@app.post('/monitors')
async def addMonitor(monitor:Monitor,conn=Depends(get_db)):
    try:
        await saveMonitor(monitor,conn)
    #when monitor already exists
    except psycopg.errors.UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="A monitor for this URL already exists."
        )

    return {
        "message":"Monitor created successfully."
    }

#this api fetches all the monitors and their status from db
#if no records exist, then return []
@app.get('/monitors')
async def getMonitors(conn=Depends(get_db)):
    monitors=await getStatusOfMonitors(conn)

    if monitors is None:
        return {
            "success":True,
            "message":"You have not created any monitors yet.",
            "data":[]
        }

    return {
        "success":True,
        "data":monitors
    }  

@app.get('/monitors/{monitor_id}/metrics')
async def getMonitorMetrics(monitor_id:int,conn=Depends(get_db)):
    metrics=await fetchMonitorMetrics(monitor_id,conn)

    if metrics is None:
        return {
            "success":True,
            "message":"No metrics to display.",
            "data":[]
        }

    return {
        "success":True,
        "data":metrics
    }

#this api returns the 10 most recent monitor events for a given monitor id
@app.get('/monitors/{monitor_id}/events')
async def getMonitorEvents(monitor_id:int,conn=Depends(get_db)):
    events=await fetchMonitorEvents(monitor_id,conn)

    if events is None:
        return {
            "success":True,
            "message":"No events to display.",
            "data":[]
        }
    
    return {
        "success":True,
        "data":events
    }
    
# this fn saves a monitor in db
# if already exists then rollback, raise exception
async def saveMonitor(monitor:Monitor,conn:psycopg.Connection):
    try:
        async with conn.cursor() as cursor:
            await cursor.execute("INSERT INTO monitors ( " \
            "name,url) " \
            "VALUES (%s,%s)",(monitor.name,str(monitor.url)))
    except psycopg.errors.UniqueViolation:
        await conn.rollback()
        raise
async def getStatusOfMonitors(conn:psycopg.Connection):
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT DISTINCT ON(monitors.id) "\
            "monitors.id, monitors.name,monitors.url ,"\
            "monitor_events.status, monitor_events.status_code, " \
            "monitor_events.response_time_ms, " \
            "monitor_events.checked_at "\
            "FROM monitors "\
            "LEFT JOIN monitor_events "\
            "ON monitors.id=monitor_events.monitor_id "\
            "ORDER BY monitors.id ASC, checked_at DESC ")

        rows=await cursor.fetchall()

        if not rows:
            return None

        results=[]

        for row in rows:
            results.append({
                "id":row[0],
                "name":row[1],
                "url":row[2],
                "status":row[3],
                "status_code":row[4],
                "response_time_ms":row[5] if row[5] is None else row[5]/RESPONSE_TIME_MS_SCALE,
                "checked_at":row[6]
                })

        return results

async def fetchMonitorMetrics(monitor_id:int,conn:psycopg.Connection):
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT monitors.name, monitors.url, " \
            "COUNT(*) as total_checks, "
            "COUNT(*) FILTER (WHERE status='up') as successful_checks, " \
            "SUM(response_time_ms) FILTER (WHERE status='up') as successful_latency_sum_ms "\
            "FROM monitor_events " \
            "JOIN monitors " \
            "ON monitors.id=monitor_events.monitor_id "\
            "WHERE monitor_id=%s "\
            "AND checked_at>=NOW()-INTERVAL '24 hours' " \
            "GROUP BY monitors.id, monitors.url, monitors.name",(monitor_id,))

        row=await cursor.fetchone()

    #find uptime percentage

    #monitor has not been checked in the past 24 hours
    if row is None:
        return None

    monitor_name=row[0]
    monitor_url=row[1]
    total_count=row[2]
    up_count=row[3]
    successful_latency_sum_ms=row[4]

    if total_count==0:
        return None    

    average_latency_ms=None

    #scale down if exist
    if successful_latency_sum_ms is not None:
        successful_latency_sum_ms/=RESPONSE_TIME_MS_SCALE

        average_latency_ms=successful_latency_sum_ms/up_count

    uptime=up_count/total_count

    uptime_percentage=uptime*100

    error_rate=((total_count-up_count)/total_count)*100

    return {
        "monitor_name":monitor_name,
        "monitor_url":monitor_url,
        "uptime_percentage":uptime_percentage,
        "average_latency_ms":average_latency_ms,
        "error_rate":error_rate
    }

async def fetchMonitorEvents(monitor_id:int,conn:psycopg.Connection):
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT monitor_events.id, monitor_events.checked_at, monitor_events.status, " \
        "monitor_events.response_time_ms, monitor_events.status_code " \
        "FROM monitor_events " \
        "JOIN monitors " \
        "ON monitors.id=monitor_events.monitor_id " \
        "WHERE monitor_events.monitor_id=%s " \
        "ORDER BY monitor_events.checked_at DESC " \
        "LIMIT 10",(monitor_id,))

        rows=await cursor.fetchall()

    if not rows:
        return None

    results=[]
    
    for row in rows:
        results.append({
            "id":row[0],
            "checked_at":row[1],
            "status":row[2],
            "response_time_ms":row[3]/RESPONSE_TIME_MS_SCALE,
            "status_code":row[4]
        })

    return results