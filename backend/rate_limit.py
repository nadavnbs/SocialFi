"""
Rate limiting configuration and middleware.
Uses slowapi for request rate limiting.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Get client IP from request, handling proxies.
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


# Create limiter instance
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=["1000/hour"],  # Global default
    storage_uri="memory://",  # In-memory for single instance; use Redis for distributed
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
    logger.warning(f"Rate limit exceeded: {get_client_ip(request)} on {request.url.path}")
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "detail": f"Too many requests. Limit: {exc.detail}",
            "retry_after": getattr(exc, 'retry_after', 60)
        },
        headers={
            "Retry-After": str(getattr(exc, 'retry_after', 60)),
            "X-RateLimit-Limit": str(exc.detail) if exc.detail else "unknown"
        }
    )


def setup_rate_limiting(app):
    """Configure rate limiting for the FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
    logger.info("✅ Rate limiting configured")
    return limiter
