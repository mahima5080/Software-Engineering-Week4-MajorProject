"""
Software Engineering - Week 4 Major Project
Production-Ready SaaS Analytics & Task Platform
Features:
- JWT Authentication & Bcrypt Password Hashing
- SQLAlchemy Database Persistence
- Real-time Analytics & System Monitoring Dashboard Endpoints
- Swagger / OpenAPI Auto-Documentation (/docs)
"""

import os
import time
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
import jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# -----------------------------------------------------------------------------
# DATABASE CONFIGURATION
# -----------------------------------------------------------------------------
DATABASE_URL = "sqlite:///./saas_app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    plan = Column(String, default="Free Tier")

class DBTask(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    status = Column(String, default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------------------------------------------------------
# SECURITY & AUTHENTICATION
# -----------------------------------------------------------------------------
SECRET_KEY = "saas-production-secret-key-week4"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

START_TIME = time.time()

app = FastAPI(
    title="SaaS Analytics & Task Platform API",
    description="Production-Ready SaaS Platform API with Authentication, Database, and Real-time Health Monitoring.",
    version="1.0.0",
)

# -----------------------------------------------------------------------------
# SCHEMAS
# -----------------------------------------------------------------------------
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=6)

class Token(BaseModel):
    access_token: str
    token_type: str

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=2)

class TaskResponse(BaseModel):
    id: int
    title: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=12)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> DBUser:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    user = db.query(DBUser).filter(DBUser.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# -----------------------------------------------------------------------------
# 1. AUTHENTICATION ENDPOINTS
# -----------------------------------------------------------------------------
@app.post("/auth/register", status_code=status.HTTP_201_CREATED, tags=["Auth"])
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    if db.query(DBUser).filter(DBUser.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    new_user = DBUser(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    return {"message": "SaaS account created successfully!"}

@app.post("/auth/login", response_model=Token, tags=["Auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# -----------------------------------------------------------------------------
# 2. SAAS CORE REST API
# -----------------------------------------------------------------------------
@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["SaaS Core"])
def create_task(task: TaskCreate, current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    new_task = DBTask(title=task.title, owner_id=current_user.id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.get("/tasks", response_model=List[TaskResponse], tags=["SaaS Core"])
def get_user_tasks(current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(DBTask).filter(DBTask.owner_id == current_user.id).all()

# -----------------------------------------------------------------------------
# 3. MONITORING & HEALTH DASHBOARD
# -----------------------------------------------------------------------------
@app.get("/health", tags=["Monitoring"])
def health_check():
    uptime_seconds = time.time() - START_TIME
    return {
        "status": "Healthy",
        "service": "SaaS Core Engine",
        "uptime_seconds": round(uptime_seconds, 2),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/analytics/dashboard", tags=["Monitoring"])
def get_dashboard_metrics(db: Session = Depends(get_db)):
    total_users = db.query(DBUser).count()
    total_tasks = db.query(DBTask).count()
    return {
        "total_registered_users": total_users,
        "total_active_tasks": total_tasks,
        "system_status": "Operational",
        "environment": "Production-Ready Docker"
    }