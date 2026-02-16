"""
SIWE (Sign-In with Ethereum) implementation for secure wallet authentication.
Implements EIP-4361 for EVM chains and structured messages for Solana.
"""
import re
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class SIWEMessage:
    """EIP-4361 compliant Sign-In with Ethereum message."""
    
    TEMPLATE = """{domain} wants you to sign in with your Ethereum account:
{address}

{statement}

URI: {uri}
Version: {version}
Chain ID: {chain_id}
Nonce: {nonce}
Issued At: {issued_at}
Expiration Time: {expiration_time}"""
    
    CHAIN_IDS = {
        'ethereum': 1,
        'base': 8453,
        'polygon': 137,
        'bnb': 56,
    }
    
    def __init__(
        self,
        domain: str,
        address: str,
        statement: str,
        uri: str,
        chain_type: str,
        nonce: Optional[str] = None,
        issued_at: Optional[datetime] = None,
        expiration_minutes: int = 15
    ):
        self.domain = domain
        self.address = address
        self.statement = statement
        self.uri = uri
        self.chain_type = chain_type
        self.chain_id = self.CHAIN_IDS.get(chain_type, 1)
        self.version = "1"
        self.nonce = nonce or secrets.token_urlsafe(16)
        self.issued_at = issued_at or datetime.now(timezone.utc)
        self.expiration_time = self.issued_at + timedelta(minutes=expiration_minutes)
    
    def prepare_message(self) -> str:
        """Generate the SIWE message string."""
        return self.TEMPLATE.format(
            domain=self.domain,
            address=self.address,
            statement=self.statement,
            uri=self.uri,
            version=self.version,
            chain_id=self.chain_id,
            nonce=self.nonce,
            issued_at=self.issued_at.isoformat(),
            expiration_time=self.expiration_time.isoformat()
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'domain': self.domain,
            'address': self.address.lower(),
            'statement': self.statement,
            'uri': self.uri,
            'chain_type': self.chain_type,
            'chain_id': self.chain_id,
            'version': self.version,
            'nonce': self.nonce,
            'issued_at': self.issued_at,
            'expiration_time': self.expiration_time,
            'message': self.prepare_message()
        }


class SolanaMessage:
    """Structured message for Solana wallet authentication."""
    
    TEMPLATE = """SocialFi Authentication

Domain: {domain}
Address: {address}

{statement}

Nonce: {nonce}
Issued At: {issued_at}
Expires: {expiration_time}

Sign this message to authenticate. This will not trigger a blockchain transaction."""
    
    def __init__(
        self,
        domain: str,
        address: str,
        statement: str,
        nonce: Optional[str] = None,
        issued_at: Optional[datetime] = None,
        expiration_minutes: int = 15
    ):
        self.domain = domain
        self.address = address
        self.statement = statement
        self.nonce = nonce or secrets.token_urlsafe(16)
        self.issued_at = issued_at or datetime.now(timezone.utc)
        self.expiration_time = self.issued_at + timedelta(minutes=expiration_minutes)
    
    def prepare_message(self) -> str:
        """Generate the structured message string."""
        return self.TEMPLATE.format(
            domain=self.domain,
            address=self.address,
            statement=self.statement,
            nonce=self.nonce,
            issued_at=self.issued_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
            expiration_time=self.expiration_time.strftime('%Y-%m-%d %H:%M:%S UTC')
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'domain': self.domain,
            'address': self.address,
            'statement': self.statement,
            'chain_type': 'solana',
            'nonce': self.nonce,
            'issued_at': self.issued_at,
            'expiration_time': self.expiration_time,
            'message': self.prepare_message()
        }


def create_auth_message(
    domain: str,
    uri: str,
    address: str,
    chain_type: str,
    statement: str = "Sign in to SocialFi to trade social content markets."
) -> Tuple[str, dict]:
    """
    Create an authentication message for the given chain type.
    
    Returns:
        Tuple of (message_string, message_data_dict)
    """
    if chain_type == 'solana':
        msg = SolanaMessage(
            domain=domain,
            address=address,
            statement=statement
        )
    else:
        msg = SIWEMessage(
            domain=domain,
            address=address,
            statement=statement,
            uri=uri,
            chain_type=chain_type
        )
    
    return msg.prepare_message(), msg.to_dict()


def parse_siwe_message(message: str) -> Optional[dict]:
    """
    Parse a SIWE message and extract fields.
    Returns None if parsing fails.
    """
    try:
        patterns = {
            'domain': r'^(.+) wants you to sign in',
            'address': r'Ethereum account:\n(0x[a-fA-F0-9]{40})',
            'uri': r'URI: (.+)',
            'version': r'Version: (\d+)',
            'chain_id': r'Chain ID: (\d+)',
            'nonce': r'Nonce: ([a-zA-Z0-9_-]+)',
            'issued_at': r'Issued At: (.+)',
            'expiration_time': r'Expiration Time: (.+)',
        }
        
        result = {}
        for field, pattern in patterns.items():
            match = re.search(pattern, message, re.MULTILINE)
            if match:
                result[field] = match.group(1)
        
        if 'address' not in result:
            return None
        
        return result
    except Exception as e:
        logger.error(f"SIWE parse error: {e}")
        return None


def validate_siwe_fields(
    stored_data: dict,
    provided_address: str,
    provided_nonce: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Validate SIWE message fields.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    now = datetime.now(timezone.utc)
    
    # Check expiration
    exp_time = stored_data.get('expiration_time')
    if exp_time and exp_time < now:
        return False, "Message has expired"
    
    # Check address match
    stored_address = stored_data.get('address', '').lower()
    if stored_address != provided_address.lower():
        return False, "Address mismatch"
    
    # Check nonce if provided
    if provided_nonce:
        stored_nonce = stored_data.get('nonce')
        if stored_nonce != provided_nonce:
            return False, "Nonce mismatch"
    
    return True, ""
