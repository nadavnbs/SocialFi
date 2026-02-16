import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'infofi_db')

async def seed_data():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Test wallet addresses
    wallets = [
        '0x742d35cc6634c0532925a3b844bc9e7595f0beb1',
        '0x5a0b54d5dc17e0aadc383d2db43b0a0d3e029c4c',
        '0x147d8b2a9c3e7f4a3b9d8e2c1f5a6b3c4d5e6f7a'
    ]
    
    # Create users if they don't exist
    for i, wallet in enumerate(wallets):
        existing = await db.users.find_one({'wallet_address': wallet.lower()})
        if not existing:
            await db.users.insert_one({
                'wallet_address': wallet.lower(),
                'chain_type': 'ethereum',
                'balance_credits': 1000.0,
                'level': 1,
                'xp': 0,
                'reputation': 5.0,
                'is_admin': i == 0,
                'created_at': datetime.now(timezone.utc),
                'last_login': datetime.now(timezone.utc)
            })
            print(f'✅ Created user: {wallet}')
    
    # Sample posts
    sample_posts = [
        "🚀 Bitcoin will hit $100k in 2026. The halvening and ETF flows make this inevitable.",
        "⚡ AI coding assistants will replace 50% of junior dev jobs by 2027. Adapt or get left behind.",
        "💼 Remote work is dead. Companies forcing RTO will lose their best talent to startups.",
        "📈 Prediction: Tesla stock hits $500 by end of 2026. FSD v13 is the catalyst.",
        "⚛️ Hot take: React is becoming the new jQuery. Too much magic. Go back to basics.",
        "🎮 GameFi will overtake DeFi in TVL by 2027. Play-to-earn 2.0 is coming.",
        "🌐 Base will flip Polygon in daily active users within 6 months.",
        "💎 NFTs aren't dead - they're evolving into something better. Dynamic NFTs are the future."
    ]
    
    for i, content in enumerate(sample_posts):
        wallet = wallets[i % len(wallets)]
        
        # Check if post exists
        existing = await db.posts.find_one({'content': content})
        if existing:
            continue
        
        # Create post
        post_result = await db.posts.insert_one({
            'user_wallet': wallet.lower(),
            'content': content,
            'image_url': None,
            'link_url': None,
            'status': 'active',
            'view_count': 0,
            'created_at': datetime.now(timezone.utc)
        })
        post_id = str(post_result.inserted_id)
        
        # Create market
        from amm import get_price
        market_result = await db.markets.insert_one({
            'post_id': post_id,
            'total_supply': 100.0,
            'total_volume': 0.0,
            'price_current': get_price(100.0),
            'fees_collected': 0.0,
            'creator_earnings': 0.0,
            'liquidity_pool': 0.0,
            'is_frozen': False,
            'created_at': datetime.now(timezone.utc)
        })
        market_id = str(market_result.inserted_id)
        
        # Create balance for creator
        await db.balances.insert_one({
            'user_wallet': wallet.lower(),
            'market_id': market_id,
            'shares_owned': 100.0,
            'avg_buy_price': 1.0,
            'created_at': datetime.now(timezone.utc)
        })
        
        print(f'✅ Created post: {content[:50]}...')
    
    client.close()
    print('\n✅ Seed data complete!')
    print('\nTest wallet addresses (use any for MetaMask):')
    for wallet in wallets:
        print(f'  {wallet}')

if __name__ == '__main__':
    asyncio.run(seed_data())
