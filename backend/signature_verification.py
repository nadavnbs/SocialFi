from web3 import Web3
from eth_account.messages import encode_defunct
import base58
import nacl.signing
import nacl.exceptions
import logging

logger = logging.getLogger(__name__)

class SignatureVerifier:
    @staticmethod
    def verify_evm_signature(message: str, signature: str, address: str) -> bool:
        """Verify EVM chain signature (Ethereum, Base, Polygon, BNB)"""
        try:
            logger.info(f"Verifying EVM signature for address: {address}")
            logger.info(f"Message: {message[:50]}...")
            logger.info(f"Signature: {signature[:20]}...")
            
            if not Web3.is_address(address):
                logger.error(f"Invalid address format: {address}")
                return False
            
            checksum_address = Web3.to_checksum_address(address)
            
            # Try personal_sign format (most wallets use this)
            message_hash = encode_defunct(text=message)
            recovered_address = Web3.eth.account.recover_message(message_hash, signature=signature)
            
            logger.info(f"Recovered address: {recovered_address}")
            logger.info(f"Expected address: {checksum_address}")
            
            is_valid = recovered_address.lower() == checksum_address.lower()
            logger.info(f"Signature valid: {is_valid}")
            
            return is_valid
        except Exception as e:
            logger.error(f"EVM signature verification error: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def verify_solana_signature(message: str, signature: str, address: str) -> bool:
        """Verify Solana signature"""
        try:
            message_bytes = message.encode('utf-8')
            
            if signature.startswith('0x'):
                signature_bytes = bytes.fromhex(signature[2:])
            else:
                signature_bytes = base58.b58decode(signature) if len(signature) > 100 else bytes.fromhex(signature)
            
            pubkey_bytes = base58.b58decode(address)
            verify_key = nacl.signing.VerifyKey(pubkey_bytes)
            verify_key.verify(message_bytes, signature_bytes)
            
            return True
        except Exception as e:
            logger.error(f"Solana signature verification error: {str(e)}")
            return False
    
    @classmethod
    def verify_signature(cls, message: str, signature: str, address: str, chain_type: str) -> bool:
        if chain_type == 'solana':
            return cls.verify_solana_signature(message, signature, address)
        else:
            return cls.verify_evm_signature(message, signature, address)