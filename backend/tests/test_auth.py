import pytest
from fastapi import status

def test_register_user(client):
    """Test user registration"""
    response = client.post("/auth/register", json={
        "username": "newuser",
        "email": "newuser@example.com",
        "full_name": "New User",
        "password": "newpassword123",
        "role": "staff"
    })
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "password" not in data

def test_login_user(client, test_user):
    """Test user login"""
    response = client.post("/auth/token", data={
        "username": "testuser",
        "password": "testpassword"
    })
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post("/auth/token", data={
        "username": "wronguser",
        "password": "wrongpassword"
    })
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_current_user(client, auth_headers):
    """Test getting current user info"""
    response = client.get("/auth/me", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"

def test_get_current_user_unauthorized(client):
    """Test getting current user without authentication"""
    response = client.get("/auth/me")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_register_duplicate_username(client, test_user):
    """Test registration with duplicate username"""
    response = client.post("/auth/register", json={
        "username": "testuser",  # Already exists
        "email": "different@example.com",
        "full_name": "Different User",
        "password": "password123",
        "role": "staff"
    })
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username already registered" in response.json()["detail"]

def test_register_duplicate_email(client, test_user):
    """Test registration with duplicate email"""
    response = client.post("/auth/register", json={
        "username": "differentuser",
        "email": "test@example.com",  # Already exists
        "full_name": "Different User",
        "password": "password123",
        "role": "staff"
    })
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email already registered" in response.json()["detail"] 