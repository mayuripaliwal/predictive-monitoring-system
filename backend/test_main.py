from fastapi.testclient import TestClient
from main import app, MonitorEvent
import pytest
import os
import psycopg
import sys,asyncio
from worker import save_monitor_event
from datetime import datetime, timezone
@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(autouse=True)
def reset_test_state():
    conn=psycopg.connect(os.getenv("DATABASE_URL"))

    try:
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE monitor_events, monitors RESTART IDENTITY")

            conn.commit()
    finally:
        conn.close()

#this function saves the monitor event in db
def save_monitor_event(monitor_event:MonitorEvent):
    conn=psycopg.connect(os.getenv("DATABASE_URL"))
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO monitor_events" \
        " (monitor_id,status,status_code,response_time_ms,checked_at) " \
        "  VALUES (%s,%s,%s,%s,%s)",
        (monitor_event.monitor_id,
            monitor_event.status,
            monitor_event.status_code,
            monitor_event.response_time_ms,
            monitor_event.checked_at))

        conn.commit()

def test_home(client):
    response=client.get('/')

    assert response.status_code==200

    assert response.json()== {
        "message":"Backend is working"
    }

# this test checks if a monitor is created successfully
def test_create_monitor(client):
    response=client.post('/monitors',json={
        "name":"demo",
        "url":"https://example.com"
    })

    assert response.status_code==200

#this test asserts that duplicate monitor creation  (same url) are not allowed
def test_create_existing_monitor(client):
    response=client.post('/monitors',json={
        "name":"demo",
        "url":"https://example.com"
    })

    assert response.status_code==200

    response=client.post('/monitors',json={
        "name":"demo",
        "url":"https://example.com"
    })

    assert response.status_code==409

def test_get_all_monitors(client):
    response=client.get('/monitors')

    assert response.status_code==200

    assert "data" in response.json()

    assert response.json()["success"]==True

def test_get_monitor_metrics(client):
    #create a monitor
    response=client.post('/monitors',json={
        "name":"monitor A",
        "url":"https://example.com"
    })

    assert response.status_code==200

    #test metrics before inserting events
    monitor_id=1

    metrics_response=client.get(f'/monitors/{monitor_id}')
    
    assert metrics_response.status_code==200
    
    metrics=metrics_response.json()

    assert "data" in metrics

    metrics_data=metrics["data"]
    
    assert len(metrics_data)==0

    #insert monitor events
    #test metrics after inserting events
    monitor_event=MonitorEvent(
        monitor_id=1,
        status='up',
        status_code=200,
        response_time_ms=20155,
        checked_at=datetime.now(timezone.utc)
    )
    save_monitor_event(monitor_event)
    monitor_event=MonitorEvent(
        monitor_id=1,
        status='up',
        status_code=200,
        response_time_ms=20145,
        checked_at=datetime.now(timezone.utc)
    )
    save_monitor_event(monitor_event)
    monitor_event=MonitorEvent(
        monitor_id=1,
        status='down',
        status_code=500,
        response_time_ms=300000,
        checked_at=datetime.now(timezone.utc)
    )
    save_monitor_event(monitor_event)
    
    
    metrics_response=client.get(f'/monitors/{monitor_id}')

    assert metrics_response.status_code==200
    
    metrics=metrics_response.json()
    
    assert "data" in metrics

    metrics_data=metrics["data"]

    assert len(metrics_data)==5

    assert metrics_data["monitor_name"]=="monitor A"

    assert metrics_data["monitor_url"]=="https://example.com/"

    assert metrics_data["uptime_percentage"]==(2/3)*100

    assert metrics_data["average_latency_ms"]==201.5

    assert metrics_data["error_rate"]==(1/3)*100
