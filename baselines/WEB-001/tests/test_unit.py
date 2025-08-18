"""Unit tests for the Todo REST API."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import Base, get_db
from src.main import app
from src import auth, crud, schemas

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Setup and teardown test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestAuth:
    """Test authentication endpoints."""
    
    def test_register_user(self):
        """Test user registration."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
        assert "id" in data
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        # Register first user
        client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser1",
                "password": "testpass123"
            }
        )
        
        # Try to register with same email
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser2",
                "password": "testpass123"
            }
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_login(self):
        """Test user login."""
        # Register user
        client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpass123"
            }
        )
        
        # Login
        response = client.post(
            "/auth/login",
            data={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = client.post(
            "/auth/login",
            data={
                "username": "nonexistent",
                "password": "wrongpass"
            }
        )
        assert response.status_code == 401


class TestTodos:
    """Test todo CRUD operations."""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers."""
        # Register and login user
        client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpass123"
            }
        )
        
        response = client.post(
            "/auth/login",
            data={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_todo(self, auth_headers):
        """Test creating a todo."""
        response = client.post(
            "/todos",
            json={
                "title": "Test Todo",
                "description": "Test Description",
                "completed": False
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Todo"
        assert data["description"] == "Test Description"
        assert data["completed"] is False
        assert "id" in data
    
    def test_list_todos(self, auth_headers):
        """Test listing todos."""
        # Create some todos
        for i in range(3):
            client.post(
                "/todos",
                json={
                    "title": f"Todo {i}",
                    "description": f"Description {i}",
                    "completed": i % 2 == 0
                },
                headers=auth_headers
            )
        
        # List todos
        response = client.get("/todos", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["pages"] == 1
    
    def test_list_todos_pagination(self, auth_headers):
        """Test todo pagination."""
        # Create 15 todos
        for i in range(15):
            client.post(
                "/todos",
                json={"title": f"Todo {i}"},
                headers=auth_headers
            )
        
        # Get first page
        response = client.get("/todos?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 15
        assert len(data["items"]) == 10
        assert data["pages"] == 2
        
        # Get second page
        response = client.get("/todos?page=2&page_size=10", headers=auth_headers)
        data = response.json()
        assert len(data["items"]) == 5
    
    def test_get_todo(self, auth_headers):
        """Test getting a specific todo."""
        # Create todo
        create_response = client.post(
            "/todos",
            json={"title": "Test Todo"},
            headers=auth_headers
        )
        todo_id = create_response.json()["id"]
        
        # Get todo
        response = client.get(f"/todos/{todo_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert data["title"] == "Test Todo"
    
    def test_update_todo(self, auth_headers):
        """Test updating a todo."""
        # Create todo
        create_response = client.post(
            "/todos",
            json={"title": "Original Title"},
            headers=auth_headers
        )
        todo_id = create_response.json()["id"]
        
        # Update todo
        response = client.put(
            f"/todos/{todo_id}",
            json={
                "title": "Updated Title",
                "completed": True
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["completed"] is True
    
    def test_delete_todo(self, auth_headers):
        """Test deleting a todo."""
        # Create todo
        create_response = client.post(
            "/todos",
            json={"title": "To Delete"},
            headers=auth_headers
        )
        todo_id = create_response.json()["id"]
        
        # Delete todo
        response = client.delete(f"/todos/{todo_id}", headers=auth_headers)
        assert response.status_code == 204
        
        # Verify deletion
        response = client.get(f"/todos/{todo_id}", headers=auth_headers)
        assert response.status_code == 404


class TestHealth:
    """Test health check endpoint."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data


class TestPasswordHashing:
    """Test password hashing utilities."""
    
    def test_password_hash_and_verify(self):
        """Test password hashing and verification."""
        password = "securepassword123"
        hashed = auth.get_password_hash(password)
        
        # Hash should be different from original
        assert hashed != password
        
        # Should verify correctly
        assert auth.verify_password(password, hashed)
        
        # Should not verify with wrong password
        assert not auth.verify_password("wrongpassword", hashed)