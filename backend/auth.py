"""
JWT authentication module.
Uses security config for validated secret.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('JWT_EXPIRATION', 1440))

security = HTTPBearer(auto_error=False)

# Lazy import to avoid circular dependency
_jwt_secret = None


def get_jwt_secret() -> str:
    """Get validated JWT secret from security config."""
    global _jwt_secret
    if _jwt_secret is None:
        from security import get_security_config
        _jwt_secret = get_security_config().get_jwt_secret()
    return _jwt_secret


def create_access_token(wallet_address: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT token with wallet_address as subject."""
    to_encode = {"sub": wallet_address.lower()}
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        'exp': expire,
        'iat': datetime.now(timezone.utc),
        'type': 'access'
    })
    
    return jwt.encode(to_encode, get_jwt_secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> str:
    """Decode JWT and return wallet_address."""
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[ALGORITHM])
        wallet_address: str = payload.get('sub')
        
        if wallet_address is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid token'
            )
        
        return wallet_address
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired token'
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Get current wallet from JWT - raises if not authenticated."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Authentication required',
            headers={'WWW-Authenticate': 'Bearer'}
        )
    
    return decode_token(credentials.credentials)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[str]:
    """Get current wallet from JWT - returns None if not authenticated."""
    if not credentials:
        return None
    
    try:
        return decode_token(credentials.credentials)
    except HTTPException:
        return None
