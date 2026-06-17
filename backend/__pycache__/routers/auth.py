from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from backend.database import get_db
from backend.models.user import User
from backend.models.progress import UserProgress
from backend.utils.security import get_password_hash, verify_password, create_access_token, decode_access_token
from backend.config import Config

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.post("/register")
async def register(user_data: dict, db: Session = Depends(get_db)):
    username = user_data.get("username")
    password = user_data.get("password")
    email = user_data.get("email", "")
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    if email and db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(password)
    new_user = User(username=username, password_hash=hashed_password, email=email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Initialize progress
    progress = UserProgress(user_id=new_user.id)
    db.add(progress)
    db.commit()
    
    return {"message": "User registered successfully", "username": new_user.username}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect username or password"
        )
    
    user.last_login = datetime.utcnow()
    user.is_online = True
    db.commit()
    
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {"username": user.username, "id": user.id}
    }

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.is_online = False
    db.commit()
    return {"message": "Logged out successfully"}

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    progress = db.query(UserProgress).filter(UserProgress.user_id == current_user.id).first()
    return {
        "user": {
            "username": current_user.username,
            "id": current_user.id,
            "email": current_user.email or "",
            "created_at": current_user.created_at,
            "is_online": current_user.is_online,
            "settings": current_user.settings or {}
        },
        "progress": progress
    }

@router.put("/settings")
async def update_settings(settings_data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if "api_keys" in settings_data:
        current_user.api_keys = settings_data["api_keys"]
    if "settings" in settings_data:
        current_user.settings = settings_data["settings"]
    
    db.commit()
    return {"message": "Settings updated successfully"}
