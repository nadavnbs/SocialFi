"""
Signature verification for EVM and Solana chains.
Handles verification without logging sensitive data.
"""
from web3 import Web3
from eth_account.messages import encode_defunct
import base58
import nacl.signing
import nacl.exceptions
import logging

logger = logging.getLogger(__name__)


class SignatureVerifier:
    """Verify cryptographic signatures from wallets."""
    
    @staticmethod
    def verify_evm_signature(message: str, signature: str, address: str) -> bool:
        """
        Verify EVM chain signature (Ethereum, Base, Polygon, BNB).
        Uses personal_sign format which most wallets use.
        """
        try:
            # Validate address format
            if not Web3.is_address(address):
                logger.warning("Invalid EVM address format")
                return False
            
            checksum_address = Web3.to_checksum_address(address)
            
            # Ensure signature has 0x prefix
            if not signature.startswith('0x'):
                signature = '0x' + signature
            
            # Validate signature length (65 bytes = 130 hex chars + 0x)
            if len(signature) != 132:
                logger.warning("Invalid signature length")
                return False
            
            # Encode message for personal_sign verification
            message_hash = encode_defunct(text=message)
            
            # Recover signer address
            from web3.auto import w3
            recovered_address = w3.eth.account.recover_message(message_hash, signature=signature)
            
            # Compare addresses (case-insensitive)
            is_valid = recovered_address.lower() == checksum_address.lower()
            
            # Log result without sensitive data
            logger.info(f"EVM signature verification: valid={is_valid}, address_match={recovered_address.lower()[:10]}...")
            
            return is_valid
            
        except ValueError as e:
            logger.warning(f"EVM signature format error: {type(e).__name__}")
            return False
        except Exception as e:
            logger.error(f"EVM verification error: {type(e).__name__}")
            return False
    
    @staticmethod
    def verify_solana_signature(message: str, signature: str, address: str) -> bool:
        """
        Verify Solana signature using Ed25519.
        """
        try:
            message_bytes = message.encode('utf-8')
            
            # Handle different signature formats
            if signature.startswith('0x'):
                signature_bytes = bytes.fromhex(signature[2:])
            elif len(signature) > 100:
                # Likely base58 encoded
                signature_bytes = base58.b58decode(signature)
            else:
                signature_bytes = bytes.fromhex(signature)
            
            # Validate signature length (64 bytes for Ed25519)
            if len(signature_bytes) != 64:
                logger.warning("Invalid Solana signature length")
                return False
            
            # Decode public key from address
            pubkey_bytes = base58.b58decode(address)
            
            # Verify signature
            verify_key = nacl.signing.VerifyKey(pubkey_bytes)
            verify_key.verify(message_bytes, signature_bytes)
            
            logger.info(f"Solana signature verification: valid=True, address={address[:10]}...")
            return True
            
        except nacl.exceptions.BadSignatureError:
            logger.warning("Solana signature verification failed: bad signature")
            return False
        except Exception as e:
            logger.error(f"Solana verification error: {type(e).__name__}")
            return False
    
    @classmethod
    def verify_signature(cls, message: str, signature: str, address: str, chain_type: str) -> bool:
        """
        Verify signature for any supported chain.
        
        Args:
            message: The message that was signed
            signature: The signature to verify
            address: The wallet address
            chain_type: One of 'ethereum', 'base', 'polygon', 'bnb', 'solana'
        
        Returns:
            True if signature is valid, False otherwise
        """
        if chain_type == 'solana':
            return cls.verify_solana_signature(message, signature, address)
        else:
            # All EVM chains use same verification
            return cls.verify_evm_signature(message, signature, address)
