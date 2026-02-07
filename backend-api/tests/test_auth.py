import pytest
from fastapi import status
import asyncio
from conftest import client, test_user, auth_headers

@pytest.mark.asyncio
async def test_user_registration(client):
    """Test user registration endpoint"""
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "Test123!@#",
        "full_name": "New User",
        "phone": "+1234567890"
    }
    response = client.post("/auth/register", json=user_data)
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.json()}")
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["user"]["username"] == user_data["username"]
    assert data["user"]["email"] == user_data["email"]
    assert "password" not in data["user"]
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_user_login(client):
    """Test user login endpoint"""
    # First register a user
    user_data = {
        "username": "logintest",
        "email": "logintest@example.com", 
        "password": "testpass123",
        "full_name": "Login Test User",
        "phone": "+1234567891"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED

    # Then try to login
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_invalid_login(client):
    """Test login with invalid credentials"""
    login_data = {
        "username": "nonexistent",
        "password": "wrongpass"
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_refresh_token(client, test_user):
    """Test token refresh endpoint"""
    refresh_data = {
        "refresh_token": test_user["refresh_token"]
    }
    response = client.post("/auth/refresh", json=refresh_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_logout(client, auth_headers):
    """Test user logout endpoint"""
    response = client.post("/auth/logout", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data

@pytest.mark.asyncio
async def test_get_roles(client, auth_headers):
    """Test getting roles endpoint"""
    response = client.get("/auth/roles", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_create_role(client, auth_headers):
    """Test role creation endpoint"""
    role_data = {
        "name": "test_role",
        "description": "Test role for unit tests",
        "permissions": ["view_users", "manage_wallet"]
    }
    response = client.post("/auth/roles", json=role_data, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == role_data["name"]
    assert data["description"] == role_data["description"]

@pytest.mark.asyncio
async def test_get_specific_role(client, auth_headers):
    """Test getting a specific role endpoint"""
    # First create a role
    role_data = {
        "name": "view_only",
        "description": "View only access",
        "permissions": ["view_users"]
    }
    create_response = client.post("/auth/roles", json=role_data, headers=auth_headers)
    role_id = create_response.json()["id"]

    # Then get the specific role
    response = client.get(f"/auth/roles/{role_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == role_data["name"]
    assert data["description"] == role_data["description"]

@pytest.mark.asyncio
async def test_update_role(client, auth_headers):
    """Test updating a role endpoint"""
    # First create a role
    role_data = {
        "name": "initial_role",
        "description": "Initial description",
        "permissions": ["view_users"]
    }
    create_response = client.post("/auth/roles", json=role_data, headers=auth_headers)
    role_id = create_response.json()["id"]

    # Then update it
    update_data = {
        "name": "updated_role",
        "description": "Updated description",
        "permissions": ["view_users", "manage_wallet"]
    }
    response = client.put(f"/auth/roles/{role_id}", json=update_data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]

@pytest.mark.asyncio
async def test_delete_role(client, auth_headers):
    """Test deleting a role endpoint"""
    # First create a role
    role_data = {
        "name": "temp_role",
        "description": "Temporary role to delete",
        "permissions": ["view_users"]
    }
    create_response = client.post("/auth/roles", json=role_data, headers=auth_headers)
    role_id = create_response.json()["id"]

    # Then delete it
    response = client.delete(f"/auth/roles/{role_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    # Verify it's deleted
    get_response = client.get(f"/auth/roles/{role_id}", headers=auth_headers)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_user_roles(client, auth_headers):
    """Test getting user roles endpoint"""
    response = client.get("/auth/user/roles", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_assign_role_to_user(client, auth_headers, test_user):
    """Test assigning a role to a user endpoint"""
    # First create a role
    role_data = {
        "name": "assign_test_role",
        "description": "Role for testing assignment",
        "permissions": ["view_users"]
    }
    create_response = client.post("/auth/roles", json=role_data, headers=auth_headers)
    role_id = create_response.json()["id"]

    # Then assign it to the user
    assign_data = {
        "user_id": test_user["id"],
        "role_id": role_id
    }
    response = client.post("/auth/user/roles", json=assign_data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_remove_role_from_user(client, auth_headers, test_user):
    """Test removing a role from a user endpoint"""
    # First create and assign a role
    role_data = {
        "name": "remove_test_role",
        "description": "Role for testing removal",
        "permissions": ["view_users"]
    }
    create_response = client.post("/auth/roles", json=role_data, headers=auth_headers)
    role_id = create_response.json()["id"]

    assign_data = {
        "user_id": test_user["id"],
        "role_id": role_id
    }
    client.post("/auth/user/roles", json=assign_data, headers=auth_headers)

    # Then remove it
    response = client.delete(f"/auth/user/roles/{role_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_invalid_token(client):
    """Test accessing protected endpoint with invalid token"""
    headers = {"Authorization": "Bearer invalidtoken123"}
    response = client.get("/auth/roles", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_expired_token(client):
    """Test accessing protected endpoint with expired token"""
    # Create an expired token (you might need to adjust this based on your token generation logic)
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjE1MTYyMzkwMjJ9.Example-Expired-Token"}
    response = client.get("/auth/roles", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_registration_validation(client):
    """Test user registration with invalid data"""
    # Test with missing required fields
    response = client.post("/auth/register", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test with invalid email format
    invalid_user = {
        "username": "testuser",
        "email": "invalid-email",
        "password": "Test123!@#",
        "full_name": "Test User"
    }
    response = client.post("/auth/register", json=invalid_user)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test with weak password
    weak_password_user = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "weak",
        "full_name": "Test User"
    }
    response = client.post("/auth/register", json=weak_password_user)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_duplicate_username(client):
    """Test registration with existing username"""
    user_data = {
        "username": "duplicatetest",
        "email": "duplicate@example.com",
        "password": "testpass123",
        "full_name": "Duplicate Test User",
        "phone": "+1234567892"
    }
    
    # First register a user
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED

    # Try to register another user with same username
    duplicate_user = user_data.copy()
    duplicate_user["email"] = "another@example.com"
    response = client.post("/auth/register", json=duplicate_user)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_duplicate_email(client):
    """Test registration with existing email"""
    user_data = {
        "username": "emailtest",
        "email": "emailtest@example.com",
        "password": "testpass123",
        "full_name": "Email Test User",
        "phone": "+1234567893"
    }
    
    # First register a user
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED

    # Try to register another user with same email
    duplicate_user = user_data.copy()
    duplicate_user["username"] = "another_username"
    response = client.post("/auth/register", json=duplicate_user)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_role_validation(client, auth_headers):
    """Test role creation with invalid data"""
    # Test with missing required fields
    response = client.post("/auth/roles", json={}, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test with invalid permissions
    invalid_role = {
        "name": "test_role",
        "description": "Test role",
        "permissions": ["invalid_permission"]
    }
    response = client.post("/auth/roles", json=invalid_role, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_role_name_exists(client, auth_headers):
    """Test creating role with existing name"""
    role_data = {
        "name": "unique_role",
        "description": "Test role",
        "permissions": ["view_users"]
    }
    
    # First create a role
    response = client.post("/auth/roles", json=role_data, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED

    # Try to create another role with same name
    response = client.post("/auth/roles", json=role_data, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_user_permissions(client, auth_headers):
    response = client.get("/users/permissions", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
