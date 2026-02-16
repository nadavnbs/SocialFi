from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import secrets

SECRET_KEY = os.environ.get('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production')
ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('JWT_EXPIRATION', 1440))

security = HTTPBearer(auto_error=False)


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None):
    """Create JWT token with user_id as subject"""
    to_encode = {"sub": user_id}
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire, 'iat': datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> str:
    """Decode JWT and return user_id"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get('sub')
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')
        return user_id
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired token')


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current user from JWT - raises if not authenticated"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')
    token = credentials.credentials
    user_id = decode_token(token)
    return user_id


async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[str]:
    """Get current user from JWT - returns None if not authenticated"""
    if not credentials:
        return None
    try:
        token = credentials.credentials
        user_id = decode_token(token)
        return user_id
    except:
        return None


async def require_admin(current_user: str = Depends(get_current_user), db=None) -> str:
    """Require admin role"""
    from database import get_db
    from bson import ObjectId
    if db is None:
        db = await get_db()
    user = await db.users.find_one({'_id': ObjectId(current_user)})
    if not user or not user.get('is_admin'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin access required')
    return current_user


def generate_challenge() -> str:
    return secrets.token_urlsafe(32)