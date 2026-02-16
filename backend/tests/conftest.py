"""
Backend test configuration and fixtures.
"""
import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os

# Set test environment
os.environ['ENV'] = 'development'
os.environ['JWT_SECRET'] = 'test-secret-for-testing-minimum-32-characters'
os.environ['CORS_ORIGINS'] = 'http://localhost:3000'
os.environ['MONGO_URL'] = 'mongodb://localhost:27017'
os.environ['DB_NAME'] = 'socialfi_test'


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def mongo_client():
    """Create MongoDB client for tests."""
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    yield client
    client.close()


@pytest.fixture(scope="function")
async def test_db(mongo_client):
    """Create fresh test database for each test."""
    db_name = f"socialfi_test_{datetime.now(timezone.utc).timestamp()}"
    db = mongo_client[db_name]
    yield db
    # Cleanup after test
    await mongo_client.drop_database(db_name)


@pytest.fixture
def sample_user():
    """Sample user data."""
    return {
        "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
        "chain_type": "ethereum",
        "balance_credits": 1000.0,
        "level": 1,
        "xp": 0,
        "reputation": 0.0,
        "is_admin": False,
        "created_at": datetime.now(timezone.utc)
    }


@pytest.fixture
def sample_post():
    """Sample post data."""
    return {
        "source_network": "reddit",
        "source_id": "test123",
        "source_url": "https://reddit.com/r/test/comments/test123",
        "author_username": "testuser",
        "title": "Test Post Title",
        "content_text": "This is test content",
        "source_likes": 100,
        "source_comments": 10,
        "status": "active",
        "ingested_at": datetime.now(timezone.utc)
    }


@pytest.fixture
def sample_market():
    """Sample market data."""
    return {
        "post_id": "test_post_id",
        "total_supply": 100.0,
        "total_volume": 0.0,
        "price_current": 1.0,
        "fees_collected": 0.0,
        "is_frozen": False,
        "version": 0,
        "created_at": datetime.now(timezone.utc)
    }
