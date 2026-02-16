"""
Tests for SIWE (Sign-In with Ethereum) implementation.
"""
from datetime import datetime, timezone, timedelta
from siwe import (
    SIWEMessage,
    SolanaMessage,
    create_auth_message,
    parse_siwe_message,
    validate_siwe_fields
)


class TestSIWEMessage:
    """Tests for SIWE message generation."""
    
    def test_creates_valid_message(self):
        """SIWE message should contain required fields."""
        msg = SIWEMessage(
            domain="socialfi.com",
            address="0x1234567890abcdef1234567890abcdef12345678",
            statement="Sign in to SocialFi",
            uri="https://socialfi.com",
            chain_type="ethereum"
        )
        
        message = msg.prepare_message()
        
        assert "socialfi.com" in message
        assert "0x1234567890abcdef1234567890abcdef12345678" in message
        assert "Sign in to SocialFi" in message
        assert "Chain ID: 1" in message
        assert "Nonce:" in message
    
    def test_chain_id_mapping(self):
        """Chain type should map to correct chain ID."""
        chains = {
            'ethereum': 1,
            'base': 8453,
            'polygon': 137,
            'bnb': 56
        }
        
        for chain_type, expected_id in chains.items():
            msg = SIWEMessage(
                domain="test.com",
                address="0x1234567890abcdef1234567890abcdef12345678",
                statement="Test",
                uri="https://test.com",
                chain_type=chain_type
            )
            
            assert msg.chain_id == expected_id
    
    def test_nonce_generation(self):
        """Nonce should be auto-generated if not provided."""
        msg = SIWEMessage(
            domain="test.com",
            address="0x1234567890abcdef1234567890abcdef12345678",
            statement="Test",
            uri="https://test.com",
            chain_type="ethereum"
        )
        
        assert msg.nonce is not None
        assert len(msg.nonce) > 10
    
    def test_expiration_time(self):
        """Expiration should be set correctly."""
        msg = SIWEMessage(
            domain="test.com",
            address="0x1234567890abcdef1234567890abcdef12345678",
            statement="Test",
            uri="https://test.com",
            chain_type="ethereum",
            expiration_minutes=30
        )
        
        expected_exp = msg.issued_at + timedelta(minutes=30)
        assert abs((msg.expiration_time - expected_exp).total_seconds()) < 1
    
    def test_to_dict(self):
        """to_dict should include all fields."""
        msg = SIWEMessage(
            domain="test.com",
            address="0x1234567890abcdef1234567890abcdef12345678",
            statement="Test",
            uri="https://test.com",
            chain_type="ethereum"
        )
        
        data = msg.to_dict()
        
        assert 'domain' in data
        assert 'address' in data
        assert 'nonce' in data
        assert 'message' in data
        assert data['address'] == "0x1234567890abcdef1234567890abcdef12345678".lower()


class TestSolanaMessage:
    """Tests for Solana message generation."""
    
    def test_creates_valid_message(self):
        """Solana message should contain required fields."""
        msg = SolanaMessage(
            domain="socialfi.com",
            address="7EcDhSYGxXyscszYEp35KHN8vvw3svAuLKTzXwCFLtV",
            statement="Sign in to SocialFi"
        )
        
        message = msg.prepare_message()
        
        assert "socialfi.com" in message
        assert "7EcDhSYGxXyscszYEp35KHN8vvw3svAuLKTzXwCFLtV" in message
        assert "Sign in to SocialFi" in message
        assert "Nonce:" in message


class TestCreateAuthMessage:
    """Tests for create_auth_message helper."""
    
    def test_creates_siwe_for_evm(self):
        """Should create SIWE message for EVM chains."""
        message, data = create_auth_message(
            domain="test.com",
            uri="https://test.com",
            address="0x1234567890abcdef1234567890abcdef12345678",
            chain_type="ethereum"
        )
        
        assert "wants you to sign in" in message
        assert data['chain_id'] == 1
    
    def test_creates_solana_message(self):
        """Should create Solana message for solana chain."""
        message, data = create_auth_message(
            domain="test.com",
            uri="https://test.com",
            address="7EcDhSYGxXyscszYEp35KHN8vvw3svAuLKTzXwCFLtV",
            chain_type="solana"
        )
        
        assert "SocialFi Authentication" in message
        assert data['chain_type'] == 'solana'


class TestParseSIWEMessage:
    """Tests for SIWE message parsing."""
    
    def test_parses_valid_message(self):
        """Should parse a valid SIWE message."""
        msg = SIWEMessage(
            domain="test.com",
            address="0x1234567890abcdef1234567890abcdef12345678",
            statement="Test",
            uri="https://test.com",
            chain_type="ethereum"
        )
        
        message = msg.prepare_message()
        parsed = parse_siwe_message(message)
        
        assert parsed is not None
        assert parsed['address'].lower() == msg.address.lower()
    
    def test_returns_none_for_invalid_message(self):
        """Should return None for invalid message."""
        result = parse_siwe_message("This is not a SIWE message")
        
        # Should return partial result or None depending on what can be parsed
        assert result is None or 'address' not in result


class TestValidateSIWEFields:
    """Tests for SIWE field validation."""
    
    def test_valid_fields(self):
        """Should pass for valid fields."""
        stored = {
            'address': '0x1234567890abcdef1234567890abcdef12345678',
            'nonce': 'test-nonce',
            'expiration_time': datetime.now(timezone.utc) + timedelta(minutes=10)
        }
        
        is_valid, error = validate_siwe_fields(
            stored,
            '0x1234567890abcdef1234567890abcdef12345678',
            'test-nonce'
        )
        
        assert is_valid is True
        assert error == ""
    
    def test_expired_message(self):
        """Should fail for expired message."""
        stored = {
            'address': '0x1234567890abcdef1234567890abcdef12345678',
            'expiration_time': datetime.now(timezone.utc) - timedelta(minutes=10)
        }
        
        is_valid, error = validate_siwe_fields(
            stored,
            '0x1234567890abcdef1234567890abcdef12345678'
        )
        
        assert is_valid is False
        assert "expired" in error.lower()
    
    def test_address_mismatch(self):
        """Should fail for address mismatch."""
        stored = {
            'address': '0x1234567890abcdef1234567890abcdef12345678',
            'expiration_time': datetime.now(timezone.utc) + timedelta(minutes=10)
        }
        
        is_valid, error = validate_siwe_fields(
            stored,
            '0xdifferentaddress1234567890abcdef12345678'
        )
        
        assert is_valid is False
        assert "mismatch" in error.lower()
    
    def test_nonce_mismatch(self):
        """Should fail for nonce mismatch."""
        stored = {
            'address': '0x1234567890abcdef1234567890abcdef12345678',
            'nonce': 'stored-nonce',
            'expiration_time': datetime.now(timezone.utc) + timedelta(minutes=10)
        }
        
        is_valid, error = validate_siwe_fields(
            stored,
            '0x1234567890abcdef1234567890abcdef12345678',
            'different-nonce'
        )
        
        assert is_valid is False
        assert "nonce" in error.lower()
