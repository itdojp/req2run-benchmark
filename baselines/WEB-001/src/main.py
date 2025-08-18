"""Main FastAPI application."""

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional
import math

from . import models, schemas, crud, auth
from .database import engine, get_db
from .config import settings

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.get("/health", response_model=schemas.HealthCheck)
async def health_check():
    """Health check endpoint."""
    return schemas.HealthCheck(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version=settings.app_version
    )


@app.post("/auth/register", response_model=schemas.User)
async def register(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    # Check if user exists
    if crud.get_user_by_email(db, email=user.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    if crud.get_user_by_username(db, username=user.username):
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )
    
    # Create user
    return crud.create_user(db=db, user=user)


@app.post("/auth/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and receive JWT token."""
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/todos", response_model=schemas.TodoList)
async def list_todos(
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    completed: Optional[bool] = None,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all todos for the current user with pagination."""
    skip = (page - 1) * page_size
    todos, total = crud.get_todos(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=page_size,
        completed=completed
    )
    
    pages = math.ceil(total / page_size)
    
    return schemas.TodoList(
        items=todos,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@app.post("/todos", response_model=schemas.Todo, status_code=status.HTTP_201_CREATED)
async def create_todo(
    todo: schemas.TodoCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new todo."""
    return crud.create_todo(db=db, todo=todo, user_id=current_user.id)


@app.get("/todos/{todo_id}", response_model=schemas.Todo)
async def get_todo(
    todo_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific todo."""
    todo = crud.get_todo(db=db, todo_id=todo_id, user_id=current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@app.put("/todos/{todo_id}", response_model=schemas.Todo)
async def update_todo(
    todo_id: int,
    todo_update: schemas.TodoUpdate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a todo."""
    todo = crud.update_todo(
        db=db,
        todo_id=todo_id,
        todo_update=todo_update,
        user_id=current_user.id
    )
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a todo."""
    if not crud.delete_todo(db=db, todo_id=todo_id, user_id=current_user.id):
        raise HTTPException(status_code=404, detail="Todo not found")
    return None


# Rate limiting middleware (basic implementation)
from collections import defaultdict
from time import time

request_counts = defaultdict(lambda: {"count": 0, "window_start": time()})


@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    """Basic rate limiting middleware."""
    if not settings.rate_limit_enabled:
        return await call_next(request)
    
    client_ip = request.client.host
    current_time = time()
    
    # Reset window if needed
    if current_time - request_counts[client_ip]["window_start"] > settings.rate_limit_period:
        request_counts[client_ip] = {"count": 0, "window_start": current_time}
    
    # Check rate limit
    if request_counts[client_ip]["count"] >= settings.rate_limit_requests:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )
    
    request_counts[client_ip]["count"] += 1
    
    response = await call_next(request)
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)