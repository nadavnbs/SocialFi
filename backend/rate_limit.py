"""
Rate limiting configuration with Redis backend for horizontal scaling.
Uses slowapi with Redis storage for distributed rate limiting.
"""
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Get client IP from request, handling proxies.
    Properly handles X-Forwarded-For from reverse proxies.
    """
    # Check X-Forwarded-For header (from reverse proxy)
    forwarded = request.headers.get('x-forwarded-for')
    if forwarded:
        # Get first IP in chain (original client)
        return forwarded.split(',')[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get('x-real-ip')
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    return get_remote_address(request)


def get_storage_uri() -> str:
    """
    Get rate limiter storage URI.
    Uses Redis if REDIS_URL is set, otherwise falls back to memory.
    """
    redis_url = os.environ.get('REDIS_URL')
    env = os.environ.get('ENV', 'development')
    
    if redis_url:
        logger.info(f"Rate limiter using Redis: {redis_url.split('@')[-1] if '@' in redis_url else redis_url}")
        return redis_url
    
    if env == 'production':
        logger.warning("⚠️ REDIS_URL not set in production - rate limiting will not scale horizontally")
    
    logger.info("Rate limiter using in-memory storage")
    return "memory://"


# Create limiter instance with dynamic storage
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=["1000/hour"],
    storage_uri=get_storage_uri(),
    strategy="fixed-window"
)


# Rate limit configurations for different endpoint types
RATE_LIMITS = {
    'auth_challenge': "10/minute",      # Prevent challenge spam
    'auth_verify': "5/minute",          # Prevent brute force
    'feed_read': "60/minute",           # Normal browsing
    'feed_refresh': "5/minute",         # Prevent refresh spam
    'trade': "30/minute",               # Trading operations
    'paste_url': "10/minute",           # URL listing
    'leaderboard': "30/minute",         # Leaderboard reads
    'portfolio': "30/minute",           # Portfolio reads
}


def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    # Log without sensitive data
    logger.warning(f"Rate limit exceeded on {request.url.path}")
    
    retry_after = getattr(exc, 'retry_after', 60)
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "detail": f"Too many requests. Please wait {retry_after} seconds.",
            "retry_after": retry_after
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(exc.detail) if exc.detail else "unknown"
        }
    )


def setup_rate_limiting(app):
    """Configure rate limiting for the FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
    storage_type = "Redis" if "redis" in get_storage_uri() else "memory"
    logger.info(f"✅ Rate limiting configured ({storage_type} backend)")
    return limiter
