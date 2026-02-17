"""
Security integration tests.
Tests that security controls are properly enforced.
"""
import pytest
import os
from unittest.mock import patch
from datetime import datetime, timezone, timedelta


class TestProductionSecurityEnforcement:
    """Tests that production security requirements are enforced."""
    
    def test_production_fails_without_jwt_secret(self):
        """Production must fail to start without JWT_SECRET."""
        from security import SecurityConfig, SecurityConfigError, reset_security_config
        reset_security_config()
        
        env_vars = {
            'ENV': 'production',
            'JWT_SECRET': '',
            'CORS_ORIGINS': 'https://app.socialfi.com'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = SecurityConfig()
            # Production mode exits, so catch SystemExit
            with pytest.raises((SecurityConfigError, SystemExit)):
                config.validate_and_load()
    
    def test_production_fails_with_weak_jwt_secret(self):
        """Production must reject weak JWT secrets."""
        from security import SecurityConfig, SecurityConfigError, reset_security_config
        reset_security_config()
        
        weak_secrets = ['secret', 'changeme', 'jwt-secret', 'test-secret']
        
        for weak in weak_secrets:
            env_vars = {
                'ENV': 'production',
                'JWT_SECRET': weak,
                'CORS_ORIGINS': 'https://app.socialfi.com'
            }
            
            with patch.dict(os.environ, env_vars, clear=False):
                config = SecurityConfig()
                with pytest.raises((SecurityConfigError, SystemExit)):
                    config.validate_and_load()
    
    def test_production_fails_with_short_jwt_secret(self):
        """Production must reject JWT secrets shorter than 32 chars."""
        from security import SecurityConfig, SecurityConfigError, reset_security_config
        reset_security_config()
        
        env_vars = {
            'ENV': 'production',
            'JWT_SECRET': 'only-25-characters-here!',
            'CORS_ORIGINS': 'https://app.socialfi.com'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = SecurityConfig()
            with pytest.raises((SecurityConfigError, SystemExit)):
                config.validate_and_load()
    
    def test_production_fails_without_cors_origins(self):
        """Production must fail without CORS_ORIGINS."""
        from security import SecurityConfig, SecurityConfigError, reset_security_config
        reset_security_config()
        
        env_vars = {
            'ENV': 'production',
            'JWT_SECRET': 'a-very-secure-jwt-secret-that-is-long-enough-123',
            'CORS_ORIGINS': ''
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = SecurityConfig()
            with pytest.raises((SecurityConfigError, SystemExit)):
                config.validate_and_load()
    
    def test_production_fails_with_wildcard_cors(self):
        """Production must reject wildcard CORS."""
        from security import SecurityConfig, SecurityConfigError, reset_security_config
        reset_security_config()
        
        env_vars = {
            'ENV': 'production',
            'JWT_SECRET': 'a-very-secure-jwt-secret-that-is-long-enough-123',
            'CORS_ORIGINS': '*'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = SecurityConfig()
            with pytest.raises((SecurityConfigError, SystemExit)):
                config.validate_and_load()
    
    def test_production_accepts_valid_config(self):
        """Production should accept valid security config."""
        from security import SecurityConfig, reset_security_config
        reset_security_config()
        
        env_vars = {
            'ENV': 'production',
            'JWT_SECRET': 'a-very-secure-jwt-secret-that-is-definitely-long-enough-123456',
            'CORS_ORIGINS': 'https://app.socialfi.com,https://www.socialfi.com'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = SecurityConfig()
            config.validate_and_load()
            
            assert config._validated is True
            assert len(config.cors_origins) == 2
            assert 'https://app.socialfi.com' in config.cors_origins


class TestDevelopmentSecurityBehavior:
    """Tests that development mode has reasonable defaults."""
    
    def test_development_generates_jwt_secret(self):
        """Development should auto-generate JWT secret if missing."""
        from security import SecurityConfig, reset_security_config
        reset_security_config()
        
        env_vars = {
            'ENV': 'development',
            'JWT_SECRET': '',
            'CORS_ORIGINS': ''
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = SecurityConfig()
            config.validate_and_load()
            
            assert len(config.jwt_secret) >= 32
    
    def test_development_defaults_cors_to_localhost(self):
        """Development should default CORS to localhost."""
        from security import SecurityConfig, reset_security_config
        reset_security_config()
        
        env_vars = {
            'ENV': 'development',
            'JWT_SECRET': 'dev-testing-secret-minimum-32-characters',
            'CORS_ORIGINS': ''
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = SecurityConfig()
            config.validate_and_load()
            
            assert 'http://localhost:3000' in config.cors_origins


class TestSIWEAuthentication:
    """Tests for SIWE message generation and validation."""
    
    def test_siwe_message_contains_required_fields(self):
        """SIWE message must contain EIP-4361 required fields."""
        from siwe import SIWEMessage
        
        msg = SIWEMessage(
            domain="socialfi.com",
            address="0x1234567890abcdef1234567890abcdef12345678",
            statement="Sign in to SocialFi",
            uri="https://socialfi.com",
            chain_type="ethereum"
        )
        
        message = msg.prepare_message()
        
        # EIP-4361 required fields
        assert "socialfi.com wants you to sign in" in message
        assert "0x1234567890abcdef1234567890abcdef12345678" in message
        assert "URI: https://socialfi.com" in message
        assert "Chain ID: 1" in message
        assert "Nonce:" in message
        assert "Issued At:" in message
        assert "Expiration Time:" in message
    
    def test_siwe_nonce_is_unique(self):
        """Each SIWE message should have unique nonce."""
        from siwe import SIWEMessage
        
        nonces = set()
        for _ in range(100):
            msg = SIWEMessage(
                domain="test.com",
                address="0x1234567890abcdef1234567890abcdef12345678",
                statement="Test",
                uri="https://test.com",
                chain_type="ethereum"
            )
            nonces.add(msg.nonce)
        
        assert len(nonces) == 100, "Nonces should be unique"
    
    def test_siwe_validation_rejects_expired(self):
        """SIWE validation should reject expired messages."""
        from siwe import validate_siwe_fields
        
        stored_data = {
            'address': '0x1234567890abcdef1234567890abcdef12345678',
            'nonce': 'test-nonce',
            'expiration_time': datetime.now(timezone.utc) - timedelta(minutes=5)
        }
        
        is_valid, error = validate_siwe_fields(
            stored_data,
            '0x1234567890abcdef1234567890abcdef12345678',
            'test-nonce'
        )
        
        assert is_valid is False
        assert 'expired' in error.lower()
    
    def test_siwe_validation_rejects_wrong_address(self):
        """SIWE validation should reject address mismatch."""
        from siwe import validate_siwe_fields
        
        stored_data = {
            'address': '0x1234567890abcdef1234567890abcdef12345678',
            'nonce': 'test-nonce',
            'expiration_time': datetime.now(timezone.utc) + timedelta(minutes=10)
        }
        
        is_valid, error = validate_siwe_fields(
            stored_data,
            '0xdifferentaddress567890abcdef1234567890ab',
            'test-nonce'
        )
        
        assert is_valid is False
        assert 'mismatch' in error.lower()
    
    def test_siwe_validation_rejects_wrong_nonce(self):
        """SIWE validation should reject nonce mismatch."""
        from siwe import validate_siwe_fields
        
        stored_data = {
            'address': '0x1234567890abcdef1234567890abcdef12345678',
            'nonce': 'correct-nonce',
            'expiration_time': datetime.now(timezone.utc) + timedelta(minutes=10)
        }
        
        is_valid, error = validate_siwe_fields(
            stored_data,
            '0x1234567890abcdef1234567890abcdef12345678',
            'wrong-nonce'
        )
        
        assert is_valid is False
        assert 'nonce' in error.lower()


class TestTradeInvariants:
    """Tests for trading invariants."""
    
    def test_buy_cost_always_positive(self):
        """Buy cost must always be positive."""
        from amm import calculate_buy_cost
        
        for supply in [0, 10, 100, 1000]:
            for shares in [0.1, 1, 10, 100]:
                result = calculate_buy_cost(supply, shares)
                assert result['total_cost'] > 0
                assert result['fee'] >= 0
    
    def test_sell_revenue_less_than_buy_cost(self):
        """Sell revenue must be less than buy cost (fees)."""
        from amm import calculate_buy_cost, calculate_sell_revenue
        
        initial_supply = 100
        shares = 10
        
        buy = calculate_buy_cost(initial_supply, shares)
        sell = calculate_sell_revenue(buy['new_supply'], shares)
        
        # User pays more to buy than they get from selling
        assert buy['total_cost'] > sell['net_revenue']
    
    def test_supply_never_negative_after_sell(self):
        """Supply must never go negative after selling."""
        from amm import calculate_sell_revenue
        
        result = calculate_sell_revenue(100, 100)
        assert result['new_supply'] >= 0
    
    def test_cannot_sell_more_than_supply(self):
        """Cannot sell more shares than available supply."""
        from amm import calculate_sell_revenue
        
        with pytest.raises(ValueError):
            calculate_sell_revenue(100, 150)
