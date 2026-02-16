"""
JWT authentication module.
Uses security config for secret validation.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import secrets

# Import will validate security on first access
from security import get_security_config

ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('JWT_EXPIRATION', 1440))

security = HTTPBearer(auto_error=False)


def get_jwt_secret() -> str:
    """Get validated JWT secret from security config."""
    return get_security_config().jwt_secret


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
    
    encoded_jwt = jwt.encode(to_encode, get_jwt_secret(), algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> str:
    """Decode JWT and return wallet_address."""
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[ALGORITHM])
        wallet_address: str = payload.get('sub')
        
        if wallet_address is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid token: missing subject'
            )
        
        return wallet_address
        
    except JWTError as e:
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
    
    token = credentials.credentials
    wallet_address = decode_token(token)
    return wallet_address


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[str]:
    """Get current wallet from JWT - returns None if not authenticated."""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        wallet_address = decode_token(token)
        return wallet_address
    except HTTPException:
        return None


async def require_admin(
    current_wallet: str = Depends(get_current_user),
    db=None
) -> str:
    """Require admin role."""
    from database import get_db
    
    if db is None:
        db = await get_db()
    
    user = await db.users.find_one({'wallet_address': current_wallet.lower()})
    
    if not user or not user.get('is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Admin access required'
        )
    
    return current_wallet


def generate_challenge() -> str:
    """Generate secure random challenge."""
    return secrets.token_urlsafe(32)
