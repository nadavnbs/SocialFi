"""
MongoDB database connection and initialization.
"""
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'socialfi_db')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


async def get_db():
    """Get database instance."""
    return db


async def init_db():
    """Create indexes for performance and data integrity."""
    try:
        # User indexes
        await db.users.create_index("wallet_address", unique=True)
        await db.users.create_index("created_at")
        await db.users.create_index("xp")
        await db.users.create_index("reputation")
        await db.users.create_index("balance_credits")
        
        # Unified posts indexes
        await db.unified_posts.create_index(
            [("source_network", 1), ("source_id", 1)],
            unique=True,
            sparse=True
        )
        await db.unified_posts.create_index("source_network")
        await db.unified_posts.create_index("status")
        await db.unified_posts.create_index("ingested_at")
        await db.unified_posts.create_index("source_likes")
        await db.unified_posts.create_index("source_url", sparse=True)
        
        # Market indexes - post_id must be unique
        await db.markets.create_index("post_id", unique=True)
        await db.markets.create_index("total_volume")
        await db.markets.create_index("price_current")
        await db.markets.create_index("version")
        
        # Position indexes - compound unique constraint
        await db.positions.create_index(
            [("wallet_address", 1), ("market_id", 1)],
            unique=True
        )
        await db.positions.create_index("wallet_address")
        
        # Trade indexes
        await db.trades.create_index("market_id")
        await db.trades.create_index("wallet_address")
        await db.trades.create_index("created_at")
        await db.trades.create_index(
            [("wallet_address", 1), ("idempotency_key", 1)],
            unique=True,
            sparse=True  # Only index docs with idempotency_key
        )
        
        # Challenge indexes with TTL for auto-cleanup
        await db.challenges.create_index("wallet_address")
        await db.challenges.create_index("nonce", unique=True)
        await db.challenges.create_index(
            "expiration_time",
            expireAfterSeconds=0  # TTL index - auto-delete expired
        )
        
        logger.info("✅ Database indexes created successfully")
        
    except Exception as e:
        # Log but don't fail - indexes might already exist
        logger.warning(f"Index creation note: {type(e).__name__}: {e}")


async def check_db_connection() -> bool:
    """Check if database is reachable."""
    try:
        await db.command("ping")
        return True
    except Exception:
        return False
