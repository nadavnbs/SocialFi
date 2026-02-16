"""
Security configuration and startup validation.
Enforces security requirements at application boot.
"""
import os
import secrets
import logging

logger = logging.getLogger(__name__)

# Security constants
WEAK_JWT_SECRETS = {
    'your-super-secret-jwt-key-change-in-production',
    'secret',
    'jwt-secret',
    'changeme',
    'development-secret',
    ''
}

MIN_JWT_SECRET_LENGTH = 32


class SecurityConfig:
    """Security configuration with validation."""
    
    def __init__(self):
        self.jwt_secret: str = ""
        self.cors_origins: list = []
        self.rate_limit_enabled: bool = True
        self.env: str = "development"
        self._validated = False
    
    def validate_and_load(self):
        """Load and validate all security configuration. Raises on failure."""
        self.env = os.environ.get('ENV', 'development')
        
        # JWT Secret validation
        self.jwt_secret = os.environ.get('JWT_SECRET', '')
        
        if self.env == 'production':
            if not self.jwt_secret:
                raise RuntimeError("FATAL: JWT_SECRET environment variable is required in production")
            
            if self.jwt_secret.lower() in WEAK_JWT_SECRETS:
                raise RuntimeError("FATAL: JWT_SECRET is using a known weak/default value. Set a strong random secret.")
            
            if len(self.jwt_secret) < MIN_JWT_SECRET_LENGTH:
                raise RuntimeError(f"FATAL: JWT_SECRET must be at least {MIN_JWT_SECRET_LENGTH} characters in production")
        else:
            # Development: use provided or generate random
            if not self.jwt_secret or self.jwt_secret.lower() in WEAK_JWT_SECRETS:
                self.jwt_secret = secrets.token_urlsafe(48)
                logger.warning("⚠️ JWT_SECRET not set or weak. Generated random secret for development.")
        
        # CORS validation
        cors_env = os.environ.get('CORS_ORIGINS', '')
        if cors_env:
            self.cors_origins = [origin.strip() for origin in cors_env.split(',') if origin.strip()]
        
        if self.env == 'production':
            if not self.cors_origins:
                raise RuntimeError("FATAL: CORS_ORIGINS must be explicitly set in production")
            
            if '*' in self.cors_origins:
                raise RuntimeError("FATAL: CORS_ORIGINS cannot contain '*' in production with credentials")
            
            # Validate each origin is a proper URL
            for origin in self.cors_origins:
                if not origin.startswith(('http://', 'https://')):
                    raise RuntimeError(f"FATAL: Invalid CORS origin: {origin}")
        else:
            # Development: allow localhost
            if not self.cors_origins:
                self.cors_origins = ['http://localhost:3000', 'http://127.0.0.1:3000']
                logger.warning("⚠️ CORS_ORIGINS not set. Using localhost defaults for development.")
        
        self._validated = True
        logger.info(f"✅ Security config validated (env={self.env})")
        
        return self
    
    def get_cors_config(self) -> dict:
        """Get CORS middleware configuration."""
        if not self._validated:
            raise RuntimeError("Security config not validated. Call validate_and_load() first.")
        
        return {
            'allow_origins': self.cors_origins,
            'allow_credentials': True,
            'allow_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'allow_headers': ['*'],
        }


# Global singleton
security_config = SecurityConfig()


def get_security_config() -> SecurityConfig:
    """Get the global security configuration."""
    if not security_config._validated:
        security_config.validate_and_load()
    return security_config
