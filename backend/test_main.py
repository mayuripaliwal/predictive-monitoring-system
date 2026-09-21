from fastapi.testclient import TestClient
from main import app
import pytest
import os
import psycopg
import sys,asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(autouse=True)
def reset_test_state():
    conn=psycopg.connect(os.getenv("DATABASE_URL"))

    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM monitors")

            cursor.execute("DELETE FROM monitor_events")

            conn.commit()
    finally:
        conn.close()

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