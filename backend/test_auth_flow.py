import requests
from eth_account import Account
from eth_account.messages import encode_defunct
import os

API_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001') + '/api'

# Create a test account
private_key = "0x4c0883a69102937d6231471b5dbb6204fe512961708279f8c5b0c5d3f736e4c5"
account = Account.from_key(private_key)
wallet_address = account.address

print(f"Testing with wallet: {wallet_address}")
print(f"API URL: {API_URL}")
print()

# Step 1: Get challenge
print("Step 1: Getting challenge...")
response = requests.post(f'{API_URL}/auth/challenge', json={
    'wallet_address': wallet_address,
    'chain_type': 'ethereum'
})

if response.status_code != 200:
    print(f"ERROR: {response.status_code} - {response.text}")
    exit(1)

data = response.json()
challenge = data['challenge']
print(f"✅ Challenge received: {challenge[:50]}...")
print()

# Step 2: Sign the challenge
print("Step 2: Signing challenge...")
message_hash = encode_defunct(text=challenge)
signed = account.sign_message(message_hash)
signature = signed.signature.hex()

if not signature.startswith('0x'):
    signature = '0x' + signature

print(f"✅ Signature: {signature[:50]}...")
print()

# Step 3: Verify signature
print("Step 3: Verifying signature...")
response = requests.post(f'{API_URL}/auth/verify', json={
    'wallet_address': wallet_address,
    'challenge': challenge,
    'signature': signature,
    'chain_type': 'ethereum'
})

if response.status_code == 200:
    data = response.json()
    print("✅ SUCCESS! Authentication complete!")
    print(f"Token: {data['access_token'][:50]}...")
    print(f"User balance: {data['user']['balance_credits']} credits")
else:
    print(f"❌ FAILED: {response.status_code}")
    print(f"Response: {response.text}")
