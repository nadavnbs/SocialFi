"""
Tests for security configuration and validation.
"""
import pytest
import os
from unittest.mock import patch


class TestSecurityConfig:
    """Tests for security configuration."""
    
    def test_development_allows_weak_secret(self):
        """Development mode should allow weak secrets with warning."""
        env_vars = {
            'ENV': 'development',
            'JWT_SECRET': '',
            'CORS_ORIGINS': ''
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            from security import SecurityConfig
            config = SecurityConfig()
            config.validate_and_load()
            
            # Should generate a random secret
            assert len(config.jwt_secret) > 32
    
    def test_production_requires_jwt_secret(self):
        """Production mode should require JWT secret."""
        env_vars = {
            'ENV': 'production',
            'JWT_SECRET': '',
            'CORS_ORIGINS': 'https://app.com'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            from security import SecurityConfig
            config = SecurityConfig()
            
            with pytest.raises(RuntimeError, match="JWT_SECRET"):
                config.validate_and_load()
    
    def test_production_rejects_weak_secret(self):
        """Production mode should reject weak secrets."""
        env_vars = {
            'ENV': 'production',
            'JWT_SECRET': 'secret',
            'CORS_ORIGINS': 'https://app.com'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            from security import SecurityConfig
            config = SecurityConfig()
            
            with pytest.raises(RuntimeError, match="weak"):
                config.validate_and_load()
    
    def test_production_requires_cors_origins(self):
        """Production mode should require CORS origins."""
        env_vars = {
            'ENV': 'production',
            'JWT_SECRET': 'a-very-long-and-secure-jwt-secret-key-123',
            'CORS_ORIGINS': ''
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            from security import SecurityConfig
            config = SecurityConfig()
            
            with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
                config.validate_and_load()
    
    def test_production_rejects_wildcard_cors(self):
        """Production mode should reject wildcard CORS."""
        env_vars = {
            'ENV': 'production',
            'JWT_SECRET': 'a-very-long-and-secure-jwt-secret-key-123',
            'CORS_ORIGINS': '*'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            from security import SecurityConfig
            config = SecurityConfig()
            
            with pytest.raises(RuntimeError, match="cannot contain"):
                config.validate_and_load()
    
    def test_cors_config_returns_dict(self):
        """get_cors_config should return valid dict."""
        env_vars = {
            'ENV': 'development',
            'JWT_SECRET': 'dev-secret-for-testing-minimum-32-chars',
            'CORS_ORIGINS': 'http://localhost:3000,http://localhost:8080'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            from security import SecurityConfig
            config = SecurityConfig()
            config.validate_and_load()
            
            cors_config = config.get_cors_config()
            
            assert 'allow_origins' in cors_config
            assert 'allow_credentials' in cors_config
            assert cors_config['allow_credentials'] is True
            assert 'http://localhost:3000' in cors_config['allow_origins']
