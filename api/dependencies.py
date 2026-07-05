import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import select
from jose import jwt, JWTError
from core.database import AsyncSessionLocal
from models.base import User, TokenBlocklist
from core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        jti: str = payload.get("jti")
        if username is None or jti is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    async with AsyncSessionLocal() as session:
        # Check blocklist
        result = await session.execute(select(TokenBlocklist).where(TokenBlocklist.jti == jti))
        if result.scalar_one_or_none():
            raise credentials_exception

        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_exception
        
        # We attach the token payload jti and exp so logout can access it
        user._current_token_jti = jti
        user._current_token_exp = payload.get("exp")
        return user

