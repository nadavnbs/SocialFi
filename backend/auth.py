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

security = HTTPBearer()

def create_access_token(wallet_address: str, expires_delta: Optional[timedelta] = None):
    to_encode = {"sub": wallet_address}
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire, 'iat': datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        wallet_address: str = payload.get('sub')
        if wallet_address is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')
        return wallet_address
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired token')

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    wallet_address = decode_token(token)
    return wallet_address

async def require_admin(current_wallet: str = Depends(get_current_user), db=None) -> str:
    from database import get_db
    if db is None:
        db = await get_db()
    user = await db.users.find_one({'wallet_address': current_wallet.lower()})
    if not user or not user.get('is_admin'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin access required')
    return current_wallet

def generate_challenge() -> str:
    return secrets.token_urlsafe(32)