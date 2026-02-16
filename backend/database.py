from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'infofi_db')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


async def get_db():
    return db


async def init_db():
    """Create indexes for performance - handles migration from old schema"""
    try:
        # Clean up old wallet-based users that don't have email
        await db.users.delete_many({"email": {"$exists": False}})
        await db.users.delete_many({"email": None})
        
        # Drop old indexes that might conflict
        try:
            await db.users.drop_index("wallet_address_1")
        except:
            pass
        
        # User indexes
        await db.users.create_index("email", unique=True, sparse=True)
        await db.users.create_index("username", unique=True, sparse=True)
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
        
        # Position indexes
        await db.positions.create_index([("user_id", 1), ("market_id", 1)], unique=True)
        await db.positions.create_index("user_id")
        
        # Trade indexes
        await db.trades.create_index("market_id")
        await db.trades.create_index("user_id")
        await db.trades.create_index("created_at")
        
        print("✅ Database indexes created for multi-network ingestion")
    except Exception as e:
        print(f"⚠️ Index creation warning (may be OK): {e}")