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
    """Create indexes for performance"""
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.posts.create_index("user_id")
    await db.posts.create_index("created_at")
    await db.markets.create_index("post_id", unique=True)
    await db.markets.create_index("total_volume")
    await db.trades.create_index("market_id")
    await db.trades.create_index("user_id")
    await db.balances.create_index([("user_id", 1), ("market_id", 1)], unique=True)
    print("Database indexes created")
