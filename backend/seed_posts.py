"""
Seed sample posts for the SocialFi platform.
These are example posts to demonstrate the platform functionality.
"""
import asyncio
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / '.env')

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'infofi_db')

# Sample posts representing different networks
SAMPLE_POSTS = [
    {
        "source_network": "reddit",
        "source_id": "sample_reddit_1",
        "source_url": "https://reddit.com/r/technology/comments/example1",
        "author_username": "tech_enthusiast",
        "author_display_name": "Tech Enthusiast",
        "title": "The Future of AI: What to Expect in 2025",
        "content_text": "Artificial intelligence is evolving at an unprecedented pace. Here's what experts predict for the coming year...",
        "subreddit": "technology",
        "media_urls": [],
        "source_likes": 15420,
        "source_comments": 892,
        "source_shares": 0,
        "source_created_at": datetime.now(timezone.utc),
        "ingested_at": datetime.now(timezone.utc),
        "status": "active"
    },
    {
        "source_network": "reddit",
        "source_id": "sample_reddit_2",
        "source_url": "https://reddit.com/r/cryptocurrency/comments/example2",
        "author_username": "crypto_whale",
        "author_display_name": "Crypto Whale",
        "title": "Bitcoin reaches new milestone - market analysis",
        "content_text": "Breaking down the latest market movements and what they mean for investors...",
        "subreddit": "cryptocurrency",
        "media_urls": [],
        "source_likes": 8934,
        "source_comments": 1245,
        "source_shares": 0,
        "source_created_at": datetime.now(timezone.utc),
        "ingested_at": datetime.now(timezone.utc),
        "status": "active"
    },
    {
        "source_network": "reddit",
        "source_id": "sample_reddit_3",
        "source_url": "https://reddit.com/r/gaming/comments/example3",
        "author_username": "gamer_pro",
        "author_display_name": "Gamer Pro",
        "title": "This indie game just changed everything",
        "content_text": "After 100 hours of gameplay, I can confidently say this is the best indie game of the decade.",
        "subreddit": "gaming",
        "media_urls": [],
        "source_likes": 24501,
        "source_comments": 3421,
        "source_shares": 0,
        "source_created_at": datetime.now(timezone.utc),
        "ingested_at": datetime.now(timezone.utc),
        "status": "active"
    },
    {
        "source_network": "farcaster",
        "source_id": "sample_farcaster_1",
        "source_url": "https://warpcast.com/vitalik/0xabc123",
        "author_username": "vitalik",
        "author_display_name": "Vitalik Buterin",
        "content_text": "Excited to share some thoughts on the future of decentralized social networks and why I think we're just getting started...",
        "farcaster_channel": "ethereum",
        "media_urls": [],
        "source_likes": 5420,
        "source_comments": 342,
        "source_shares": 890,
        "source_created_at": datetime.now(timezone.utc),
        "ingested_at": datetime.now(timezone.utc),
        "status": "active"
    },
    {
        "source_network": "farcaster",
        "source_id": "sample_farcaster_2",
        "source_url": "https://warpcast.com/dwr/0xdef456",
        "author_username": "dwr",
        "author_display_name": "Dan Romero",
        "content_text": "Farcaster just hit 500k users! Thank you to this incredible community for building with us.",
        "farcaster_channel": "farcaster",
        "media_urls": [],
        "source_likes": 3210,
        "source_comments": 156,
        "source_shares": 445,
        "source_created_at": datetime.now(timezone.utc),
        "ingested_at": datetime.now(timezone.utc),
        "status": "active"
    },
    {
        "source_network": "x",
        "source_id": "sample_x_1",
        "source_url": "https://x.com/elonmusk/status/123456789",
        "author_username": "elonmusk",
        "author_display_name": "Elon Musk",
        "content_text": "[Content from X - embed preview only]",
        "media_type": "embed",
        "media_urls": [],
        "source_likes": 150000,
        "source_comments": 25000,
        "source_shares": 42000,
        "source_created_at": datetime.now(timezone.utc),
        "ingested_at": datetime.now(timezone.utc),
        "status": "active"
    },
]


async def seed_database():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🌱 Seeding database with sample posts...")
    
    for post_data in SAMPLE_POSTS:
        # Check if post already exists
        existing = await db.unified_posts.find_one({
            "source_network": post_data["source_network"],
            "source_id": post_data["source_id"]
        })
        
        if existing:
            print(f"  ⏭️  Skipping existing: {post_data['source_id']}")
            continue
        
        # Insert post
        result = await db.unified_posts.insert_one(post_data)
        post_id = str(result.inserted_id)
        
        # Create market for post
        market = {
            "post_id": post_id,
            "total_supply": 100.0,
            "total_volume": float(post_data["source_likes"]) / 100,  # Use engagement as initial volume
            "price_current": 1.0 + (post_data["source_likes"] / 10000),  # Price based on engagement
            "fees_collected": 0.0,
            "creator_earnings": 0.0,
            "liquidity_pool": 0.0,
            "is_frozen": False,
            "created_at": datetime.now(timezone.utc)
        }
        await db.markets.insert_one(market)
        
        print(f"  ✅ Added: [{post_data['source_network']}] {post_data.get('title', post_data['content_text'][:40])}")
    
    print("✅ Seeding complete!")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
