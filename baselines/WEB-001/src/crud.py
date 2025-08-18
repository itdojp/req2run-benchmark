"""CRUD operations for todos and users."""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from . import models, schemas, auth


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """Get a user by ID."""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Get a user by email."""
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Get a user by username."""
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Create a new user."""
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_todos(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    completed: Optional[bool] = None
) -> tuple[List[models.Todo], int]:
    """Get todos for a user with pagination and filtering."""
    query = db.query(models.Todo).filter(models.Todo.owner_id == user_id)
    
    if completed is not None:
        query = query.filter(models.Todo.completed == completed)
    
    total = query.count()
    todos = query.offset(skip).limit(limit).all()
    
    return todos, total


def get_todo(db: Session, todo_id: int, user_id: int) -> Optional[models.Todo]:
    """Get a specific todo for a user."""
    return db.query(models.Todo).filter(
        and_(models.Todo.id == todo_id, models.Todo.owner_id == user_id)
    ).first()


def create_todo(db: Session, todo: schemas.TodoCreate, user_id: int) -> models.Todo:
    """Create a new todo."""
    db_todo = models.Todo(
        **todo.dict(),
        owner_id=user_id
    )
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo


def update_todo(
    db: Session,
    todo_id: int,
    todo_update: schemas.TodoUpdate,
    user_id: int
) -> Optional[models.Todo]:
    """Update a todo."""
    db_todo = get_todo(db, todo_id, user_id)
    if not db_todo:
        return None
    
    update_data = todo_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_todo, field, value)
    
    db.commit()
    db.refresh(db_todo)
    return db_todo


def delete_todo(db: Session, todo_id: int, user_id: int) -> bool:
    """Delete a todo."""
    db_todo = get_todo(db, todo_id, user_id)
    if not db_todo:
        return False
    
    db.delete(db_todo)
    db.commit()
    return True