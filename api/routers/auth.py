from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlmodel import Session, select
from jose import jwt
from passlib.context import CryptContext
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
import uuid

def get_real_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

limiter = Limiter(key_func=get_real_ip)
from core.database import AsyncSessionLocal, get_session
from models.base import User
from core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

class UserCreate(BaseModel):
    username: str
    password: str

@router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, user: UserCreate, session: Session = Depends(get_session)):
    result = await session.execute(select(User).where(User.username == user.username))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
            
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return {"message": "User registered successfully"}

@router.post("/token")
@limiter.limit("10/minute")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    result = await session.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
            
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

from api.dependencies import get_current_user
from models.base import TokenBlocklist

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    jti = getattr(current_user, "_current_token_jti", None)
    exp = getattr(current_user, "_current_token_exp", None)
    if jti and exp:
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
        blocklist_entry = TokenBlocklist(jti=jti, expires_at=expires_at)
        session.add(blocklist_entry)
        await session.commit()
    return {"message": "Successfully logged out"}
