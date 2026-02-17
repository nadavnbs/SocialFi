"""
Security configuration and startup validation.
Enforces security requirements at application boot.
FAILS HARD in production if security requirements not met.
"""
import os
import secrets
import logging
import sys

logger = logging.getLogger(__name__)

# Known weak/default secrets that MUST be rejected
WEAK_JWT_SECRETS = {
    'your-super-secret-jwt-key-change-in-production',
    'secret',
    'jwt-secret',
    'changeme',
    'development-secret',
    'dev-secret',
    'test-secret',
    'change-me',
    'placeholder',
    ''
}

MIN_JWT_SECRET_LENGTH = 32


class SecurityConfigError(Exception):
    """Raised when security configuration is invalid."""
    pass


class SecurityConfig:
    """Security configuration with strict validation."""
    
    def __init__(self):
        self.jwt_secret: str = ""
        self.cors_origins: list = []
        self.rate_limit_enabled: bool = True
        self.env: str = "development"
        self._validated = False
    
    def validate_and_load(self):
        """
        Load and validate all security configuration.
        FAILS HARD in production if misconfigured.
        """
        self.env = os.environ.get('ENV', 'development').lower()
        is_production = self.env == 'production'
        
        # ===== JWT SECRET VALIDATION =====
        self.jwt_secret = os.environ.get('JWT_SECRET', '')
        
        if is_production:
            if not self.jwt_secret:
                self._fatal("JWT_SECRET environment variable is REQUIRED in production")
            
            if self.jwt_secret.lower() in WEAK_JWT_SECRETS:
                self._fatal("JWT_SECRET is using a known weak/default value")
            
            if any(weak in self.jwt_secret.lower() for weak in ['secret', 'change', 'test', 'dev']):
                logger.warning("⚠️ JWT_SECRET may contain weak patterns")
            
            if len(self.jwt_secret) < MIN_JWT_SECRET_LENGTH:
                self._fatal(f"JWT_SECRET must be at least {MIN_JWT_SECRET_LENGTH} characters")
        else:
            # Development: generate if weak/missing
            if not self.jwt_secret or self.jwt_secret.lower() in WEAK_JWT_SECRETS:
                self.jwt_secret = secrets.token_urlsafe(48)
                logger.warning("⚠️ JWT_SECRET weak/missing. Generated random secret for development.")
        
        # ===== CORS VALIDATION =====
        cors_env = os.environ.get('CORS_ORIGINS', '')
        
        if cors_env:
            self.cors_origins = [
                origin.strip() 
                for origin in cors_env.split(',') 
                if origin.strip()
            ]
        
        if is_production:
            if not self.cors_origins:
                self._fatal("CORS_ORIGINS must be explicitly set in production")
            
            if '*' in self.cors_origins:
                self._fatal("CORS_ORIGINS cannot contain '*' in production (unsafe with credentials)")
            
            # Validate each origin
            for origin in self.cors_origins:
                if not origin.startswith(('http://', 'https://')):
                    self._fatal(f"Invalid CORS origin format: {origin}")
                if 'localhost' in origin or '127.0.0.1' in origin:
                    logger.warning(f"⚠️ CORS allows localhost in production: {origin}")
        else:
            # Development: use localhost defaults
            if not self.cors_origins:
                self.cors_origins = [
                    'http://localhost:3000',
                    'http://127.0.0.1:3000',
                    'http://localhost:8080'
                ]
                logger.info("CORS_ORIGINS defaulted to localhost for development")
        
        self._validated = True
        logger.info(f"✅ Security config validated (env={self.env}, origins={len(self.cors_origins)})")
        
        return self
    
    def _fatal(self, message: str):
        """Log fatal error and exit in production, raise in development."""
        full_message = f"SECURITY FATAL: {message}"
        logger.critical(full_message)
        
        if self.env == 'production':
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"SECURITY CONFIGURATION ERROR", file=sys.stderr)
            print(f"{'='*60}", file=sys.stderr)
            print(f"\n{message}\n", file=sys.stderr)
            print(f"The application cannot start with insecure configuration.", file=sys.stderr)
            print(f"{'='*60}\n", file=sys.stderr)
            sys.exit(1)
        else:
            raise SecurityConfigError(full_message)
    
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
    
    def get_jwt_secret(self) -> str:
        """Get validated JWT secret."""
        if not self._validated:
            raise RuntimeError("Security config not validated. Call validate_and_load() first.")
        return self.jwt_secret


# Global singleton
_security_config = None


def get_security_config() -> SecurityConfig:
    """Get the global security configuration (singleton)."""
    global _security_config
    
    if _security_config is None:
        _security_config = SecurityConfig()
        _security_config.validate_and_load()
    
    return _security_config


def reset_security_config():
    """Reset security config (for testing only)."""
    global _security_config
    _security_config = None
