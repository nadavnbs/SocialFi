from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


async def get_db():
    return db


async def init_db():
    """Create indexes for performance - handles migration from old schema"""
    try:
        # User indexes - wallet based
        await db.users.create_index("wallet_address", unique=True, sparse=True)
        await db.users.create_index("created_at")
        
        # Unified posts indexes
        await db.unified_posts.create_index([("source_network", 1), ("source_id", 1)], unique=True)
        await db.unified_posts.create_index("source_network")
        await db.unified_posts.create_index("status")
        await db.unified_posts.create_index("ingested_at")
        await db.unified_posts.create_index("source_likes")
        await db.unified_posts.create_index("source_url", sparse=True)
        
        # Market indexes
        await db.markets.create_index("post_id", unique=True, sparse=True)
        await db.markets.create_index("total_volume")
        await db.markets.create_index("price_current")
        
        # Position indexes - wallet based
        await db.positions.create_index([("wallet_address", 1), ("market_id", 1)], unique=True)
        await db.positions.create_index("wallet_address")
        
        # Trade indexes
        await db.trades.create_index("market_id")
        await db.trades.create_index("wallet_address")
        await db.trades.create_index("created_at")
        
        # Challenge indexes for wallet auth
        await db.challenges.create_index("wallet_address")
        await db.challenges.create_index("expires_at", expireAfterSeconds=0)
        
        print("✅ Database indexes created for wallet-based multi-network platform")
    except Exception as e:
        print(f"⚠️ Index creation warning (may be OK): {e}")