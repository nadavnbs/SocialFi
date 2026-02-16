from eth_account.messages import encode_defunct
from eth_account import Account

# Test signature verification
message = "Test message 123"
private_key = "0x4c0883a69102937d6231471b5dbb6204fe512961708279f8c5b0c5d3f736e4c5"  # Random test key
account = Account.from_key(private_key)
address = account.address

print(f"Test address: {address}")
print(f"Message: {message}")

# Sign the message
message_hash = encode_defunct(text=message)
signed = account.sign_message(message_hash)
signature = signed.signature.hex()

print(f"Signature: {signature}")

# Verify
from web3.auto import w3
recovered = w3.eth.account.recover_message(message_hash, signature=signature)
print(f"Recovered address: {recovered}")
print(f"Match: {recovered.lower() == address.lower()}")
