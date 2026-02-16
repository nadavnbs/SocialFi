"""
Data models for multi-network content ingestion platform
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


class NetworkSource(str, Enum):
    REDDIT = "reddit"
    FARCASTER = "farcaster"
    X = "x"
    INSTAGRAM = "instagram"
    TWITCH = "twitch"
    MANUAL = "manual"  # User-pasted URL


class PostStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    MODERATED = "moderated"
    DELETED = "deleted"


# Auth Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    username: str = Field(min_length=3, max_length=30)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    balance_credits: float
    level: int
    xp: int
    reputation: float
    is_admin: bool
    created_at: datetime


# Unified Post Model - All ingested content normalizes to this
class UnifiedPost(BaseModel):
    source_network: NetworkSource
    source_id: str  # Original post ID from source
    source_url: str
    
    # Author info
    author_username: str
    author_display_name: Optional[str] = None
    author_avatar_url: Optional[str] = None
    author_profile_url: Optional[str] = None
    
    # Content
    content_text: Optional[str] = None
    content_html: Optional[str] = None
    media_urls: List[str] = []
    media_type: Optional[Literal["image", "video", "gif", "embed"]] = None
    
    # Metadata
    title: Optional[str] = None  # For Reddit posts
    subreddit: Optional[str] = None  # Reddit specific
    farcaster_channel: Optional[str] = None  # Farcaster specific
    
    # Engagement metrics from source
    source_likes: int = 0
    source_comments: int = 0
    source_shares: int = 0
    source_views: int = 0
    
    # Timestamps
    source_created_at: Optional[datetime] = None
    ingested_at: datetime = Field(default_factory=lambda: datetime.now())
    
    # Platform fields (added after ingestion)
    status: PostStatus = PostStatus.ACTIVE


class UnifiedPostDB(UnifiedPost):
    """Database model with MongoDB _id handling"""
    id: Optional[str] = None
    market_id: Optional[str] = None


# Market Models
class MarketCreate(BaseModel):
    post_id: str


class MarketResponse(BaseModel):
    id: str
    post_id: str
    total_supply: float
    total_volume: float
    price_current: float
    fees_collected: float
    is_frozen: bool
    created_at: datetime


# Trade Models
class TradeRequest(BaseModel):
    market_id: str
    shares: float = Field(gt=0)


class TradeResponse(BaseModel):
    success: bool
    trade_type: str
    shares: float
    price_per_share: float
    total_cost: float
    fee_amount: float
    new_balance: float


# URL Paste Fallback
class PasteURLRequest(BaseModel):
    url: str = Field(..., description="URL of social media post to list")


class PasteURLResponse(BaseModel):
    success: bool
    post_id: str
    market_id: str
    network: NetworkSource
    message: str


# Feed/Filter Models
class FeedFilter(BaseModel):
    networks: List[NetworkSource] = []
    sort_by: Literal["trending", "new", "price", "volume"] = "trending"
    limit: int = Field(default=50, le=100)
    offset: int = 0


class FeedResponse(BaseModel):
    posts: List[dict]
    total: int
    has_more: bool
