from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone
import os

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://infofi:infofi123@localhost:5432/infofi_db')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    balance_credits = Column(Float, default=1000.00)
    reputation = Column(Float, default=0.00)
    is_admin = Column(Boolean, default=False)
    is_moderator = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(Text, nullable=True)
    oauth_provider = Column(String(50), nullable=True)
    oauth_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)
    
    posts = relationship('Post', back_populates='user', cascade='all, delete-orphan')
    trades = relationship('Trade', back_populates='user', cascade='all, delete-orphan')
    balances = relationship('Balance', back_populates='user', cascade='all, delete-orphan')
    reports_made = relationship('Report', foreign_keys='Report.reporter_id', back_populates='reporter')
    transactions = relationship('Transaction', back_populates='user', cascade='all, delete-orphan')
    
    __table_args__ = (
        CheckConstraint('balance_credits >= 0', name='positive_balance'),
    )

class Post(Base):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    content = Column(Text, nullable=False)
    image_url = Column(Text, nullable=True)
    link_url = Column(Text, nullable=True)
    status = Column(String(20), default='active', index=True)
    moderation_note = Column(Text, nullable=True)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    user = relationship('User', back_populates='posts')
    market = relationship('Market', back_populates='post', uselist=False, cascade='all, delete-orphan')
    reports = relationship('Report', back_populates='post', cascade='all, delete-orphan')
    
    __table_args__ = (
        CheckConstraint('LENGTH(content) <= 500', name='content_length'),
    )

class Market(Base):
    __tablename__ = 'markets'
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    total_supply = Column(Float, default=100.00)
    total_volume = Column(Float, default=0.00, index=True)
    price_current = Column(Float, default=1.00, index=True)
    fees_collected = Column(Float, default=0.00)
    liquidity_pool = Column(Float, default=0.00)
    creator_earnings = Column(Float, default=0.00)
    is_frozen = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_trade_at = Column(DateTime, nullable=True)
    
    post = relationship('Post', back_populates='market')
    trades = relationship('Trade', back_populates='market', cascade='all, delete-orphan')
    balances = relationship('Balance', back_populates='market', cascade='all, delete-orphan')

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey('markets.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    trade_type = Column(String(4), nullable=False)
    shares = Column(Float, nullable=False)
    price_per_share = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    fee_amount = Column(Float, nullable=False)
    supply_before = Column(Float, nullable=False)
    supply_after = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    market = relationship('Market', back_populates='trades')
    user = relationship('User', back_populates='trades')
    
    __table_args__ = (
        CheckConstraint("trade_type IN ('buy', 'sell')", name='valid_trade_type'),
        CheckConstraint('shares > 0', name='positive_shares'),
    )

class Balance(Base):
    __tablename__ = 'balances'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    market_id = Column(Integer, ForeignKey('markets.id', ondelete='CASCADE'), nullable=False, index=True)
    shares_owned = Column(Float, default=0.00)
    avg_buy_price = Column(Float, default=0.00)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    user = relationship('User', back_populates='balances')
    market = relationship('Market', back_populates='balances')
    
    __table_args__ = (
        UniqueConstraint('user_id', 'market_id', name='unique_user_market'),
        CheckConstraint('shares_owned >= 0', name='positive_shares_balance'),
    )

class Report(Base):
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False, index=True)
    reporter_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reason = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default='pending', index=True)
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    resolution = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at = Column(DateTime, nullable=True)
    
    post = relationship('Post', back_populates='reports')
    reporter = relationship('User', foreign_keys=[reporter_id], back_populates='reports_made')

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    reference_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    user = relationship('User', back_populates='transactions')

class AdminAction(Base):
    __tablename__ = 'admin_actions'
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    action_metadata = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

def init_db():
    Base.metadata.create_all(bind=engine)
