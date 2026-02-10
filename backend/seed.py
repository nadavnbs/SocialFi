from database import SessionLocal, User, Post, Market, Balance
from auth import get_password_hash
from amm import get_price
from datetime import datetime, timezone

db = SessionLocal()

# Create admin user
admin = db.query(User).filter(User.email == 'admin@infofi.com').first()
if not admin:
    admin = User(
        email='admin@infofi.com',
        username='admin',
        password_hash=get_password_hash('admin123'),
        balance_credits=10000.00,
        reputation=100.0,
        is_admin=True,
        is_moderator=True,
        oauth_provider='email'
    )
    db.add(admin)
    db.commit()
    print(f"Created admin user: admin@infofi.com / admin123")
else:
    print("Admin user already exists")

# Create test users
test_users = [
    {'email': 'alice@test.com', 'username': 'alice', 'password': 'test123'},
    {'email': 'bob@test.com', 'username': 'bob', 'password': 'test123'},
    {'email': 'charlie@test.com', 'username': 'charlie', 'password': 'test123'},
]

for user_data in test_users:
    user = db.query(User).filter(User.email == user_data['email']).first()
    if not user:
        user = User(
            email=user_data['email'],
            username=user_data['username'],
            password_hash=get_password_hash(user_data['password']),
            balance_credits=1000.00,
            reputation=5.0,
            oauth_provider='email'
        )
        db.add(user)
        print(f"Created user: {user_data['email']} / {user_data['password']}")

db.commit()

# Create sample posts with markets
sample_posts = [
    "Bitcoin will hit $100k in 2026. The halvening and ETF flows make this inevitable.",
    "AI coding assistants will replace 50% of junior dev jobs by 2027. Adapt or get left behind.",
    "Remote work is dead. Companies forcing RTO will lose their best talent to startups.",
    "Prediction: Tesla stock hits $500 by end of 2026. FSD v13 is the catalyst.",
    "Hot take: React is becoming the new jQuery. Next.js has too much magic. Go back to basics.",
]

users = db.query(User).filter(User.is_admin == False).all()

for i, content in enumerate(sample_posts):
    user = users[i % len(users)]
    
    existing = db.query(Post).filter(Post.content == content).first()
    if existing:
        continue
    
    post = Post(
        user_id=user.id,
        content=content,
        status='active',
        created_at=datetime.now(timezone.utc)
    )
    db.add(post)
    db.flush()
    
    market = Market(
        post_id=post.id,
        total_supply=100.00,
        price_current=get_price(100.00),
        total_volume=0.00
    )
    db.add(market)
    db.flush()
    
    balance = Balance(
        user_id=user.id,
        market_id=market.id,
        shares_owned=100.00,
        avg_buy_price=1.00
    )
    db.add(balance)
    
    print(f"Created post #{post.id} by {user.username}")

db.commit()
db.close()

print("\nSeed data created successfully!")
print("\nTest credentials:")
print("Admin: admin@infofi.com / admin123")
print("User 1: alice@test.com / test123")
print("User 2: bob@test.com / test123")
print("User 3: charlie@test.com / test123")
