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

    return monitors    

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
        await cursor.execute("SELECT DISTINCT ON (monitors.id) "\
            "monitors.name,monitors.url ,"\
            "monitor_events.status, monitor_events.checked_at "\
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
                "name":row[0],
                "url":row[1],
                "status":row[2],
                "checked_at":row[3]
                })

        return results
                