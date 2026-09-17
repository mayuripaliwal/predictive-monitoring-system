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

@asynccontextmanager
async def lifespan(app:FastAPI):
    app.state.http_client=httpx.AsyncClient()
    await pool.open()
    await create_tables()
    yield
    await pool.close()
    await app.state.http_client.aclose()

app=FastAPI(lifespan=lifespan)

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

# this fn checks the website status and stores it
async def checkMonitor(request:Request,monitor_id,conn=Depends(get_db)):
    #first get the client for httpx
    client=request.app.state.http_client
    #get url from db
    monitor_url=getMonitorByID(monitor_id,conn)
    
    #create monitor event
    monitor_event=MonitorEvent(
        monitor_id=monitor_id,
        status="down",
        status_code=None,
        response_time_ms=None,
        checked_at=datetime.now(timezone.utc)
    )    

    try:
        start=time.perf_counter()
        r=await client.get(monitor_url)

        end=time.perf_counter()

        #record response time 
        #round upto 2 decimal places, and
        #scale by 100 
        monitor_event.response_time_ms=round((end-start)*1000,2)*10

        monitor_event.status_code=r.status_code

        #website up/down based on status code
        if 200<=monitor_event.status_code<500:
            monitor_event.status="up"
        else:
            monitor_event.status="down"

        await saveMonitorEvent(monitor_event,conn)

        return monitor_event
    
    except httpx.TimeoutException as e:

        await saveMonitorEvent(monitor_event,conn)
        return monitor_event
    
    except httpx.RequestError as e:

        await saveMonitorEvent(monitor_event,conn)
        return monitor_event

# this fn saves a monitor event in db
async def saveMonitorEvent(monitor_event:MonitorEvent,conn:psycopg.Connection):
    async with conn.cursor() as cursor:
        await cursor.execute("INSERT INTO monitor_events ( " \
        "monitor_id, status, status_code, response_time_ms, checked_at) " \
        "VALUES(%s,%s,%s,%s,%s)",(
            monitor_event.monitor_id,
            monitor_event.status,
            monitor_event.status_code,
            monitor_event.response_time_ms,
            monitor_event.checked_at,))


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

async def getMonitorByID(monitor_id:int,conn:psycopg.Connection):
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT url " \
        "FROM monitors " \
        "WHERE id=%s ",(monitor_id,))

    row=cursor.fetchone()

    if row is None:
        return None

    monitor_url=row[0]

    return monitor_url