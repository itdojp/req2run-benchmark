"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """User login schema."""
    username: str
    password: str


class User(UserBase):
    """User response schema."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TodoBase(BaseModel):
    """Base todo schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    completed: bool = False


class TodoCreate(TodoBase):
    """Todo creation schema."""
    pass


class TodoUpdate(BaseModel):
    """Todo update schema."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    completed: Optional[bool] = None


class Todo(TodoBase):
    """Todo response schema."""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TodoList(BaseModel):
    """Paginated todo list response."""
    items: list[Todo]
    total: int
    page: int
    page_size: int
    pages: int


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """JWT token payload."""
    username: Optional[str] = None


class HealthCheck(BaseModel):
    """Health check response."""
    status: str = "healthy"
    timestamp: datetime
    version: str