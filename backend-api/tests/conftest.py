import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.database import Base, get_db
from main import app
import os
import sys
import asyncio

# Import all models so they are registered with Base
from services.models.models import *
from services.models.transaction_models import *
from services.models.service_models import *

# Setup test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="session")
def test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest_asyncio.fixture(autouse=True)
def clean_db(test_db):
    """Clean the database before each test"""
    # Delete all data but keep the tables
    with test_engine.connect() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
        connection.commit()

@pytest_asyncio.fixture
def client(clean_db):
    return TestClient(app)

@pytest_asyncio.fixture
def test_user(client):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User",
        "phone": "+1234567890"
    }
    # Register user
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    
    # Login to get auth token
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    login_response = client.post("/auth/login", data=login_data)
    assert login_response.status_code == 200
    token_data = login_response.json()
    
    user_data["access_token"] = token_data["access_token"]
    user_data["refresh_token"] = token_data["refresh_token"]
    user_data["token_type"] = token_data["token_type"]
    user_data["id"] = token_data.get("user_id")
    return user_data

@pytest_asyncio.fixture
def auth_headers(test_user):
    """Return authorization headers for authenticated requests"""
    return {"Authorization": f"Bearer {test_user['access_token']}"}
