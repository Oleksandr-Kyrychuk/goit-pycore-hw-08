# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from main import app, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Base, get_db

# Налаштування тестової бази даних
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Перевизначення залежності get_db для тестів
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_register_user():
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert response.json()["verified"] is False

@pytest.mark.asyncio
async def test_register_user_duplicate_email():
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_login_user():
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_verify_email():
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "test@example.com").first()
    response = client.get(f"/auth/verify?token={user.verification_token}")
    assert response.status_code == 200
    assert response.json()["message"] == "Email verified successfully"

@pytest.mark.asyncio
async def test_create_contact():
    # Реєстрація та логін
    client.post("/auth/register", json={"email": "test@example.com", "password": "password123"})
    login_response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = login_response.json()["access_token"]
    # Верифікація email
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "test@example.com").first()
    client.get(f"/auth/verify?token={user.verification_token}")
    # Створення контакту
    response = client.post(
        "/contacts/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone_number": "1234567890",
            "birthday": "2025-05-18",
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    assert response.json()["first_name"] == "John"