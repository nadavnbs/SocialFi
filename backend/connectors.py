"""
Connector interface and implementations for multi-network content ingestion.
Connectors fetch public content from social networks without requiring user auth.
"""
import httpx
import re
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from models import UnifiedPost, NetworkSource
import logging

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """Abstract base class for all network connectors"""
    
    network: NetworkSource
    
    @abstractmethod
    async def fetch_trending(self, limit: int = 50) -> List[UnifiedPost]:
        """Fetch trending/hot posts from the network"""
        pass
    
    @abstractmethod
    async def fetch_by_url(self, url: str) -> Optional[UnifiedPost]:
        """Fetch a single post by its URL"""
        pass
    
    @abstractmethod
    def can_handle_url(self, url: str) -> bool:
        """Check if this connector can handle the given URL"""
        pass


class RedditConnector(BaseConnector):
    """
    Reddit connector using public JSON API (no auth required).
    Appending .json to any Reddit URL returns public data.
    Rate limited but compliant with Reddit ToS for public data.
    """
    
    network = NetworkSource.REDDIT
    BASE_URL = "https://www.reddit.com"
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "SocialFi-Ingestion/1.0 (content aggregator)",
                "Accept": "application/json"
            },
            timeout=30.0
        )
    
    def can_handle_url(self, url: str) -> bool:
        patterns = [
            r'reddit\.com/r/\w+/comments/\w+',
            r'redd\.it/\w+',
            r'old\.reddit\.com/r/\w+/comments/\w+'
        ]
        return any(re.search(p, url) for p in patterns)
    
    async def fetch_trending(self, limit: int = 50) -> List[UnifiedPost]:
        """Fetch hot posts from r/all (public, no auth)"""
        posts = []
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/r/all/hot.json",
                params={"limit": min(limit, 100)}
            )
            response.raise_for_status()
            data = response.json()
            
            for child in data.get("data", {}).get("children", []):
                post_data = child.get("data", {})
                if post_data.get("is_self") or post_data.get("stickied"):
                    continue
                    
                unified = self._normalize_post(post_data)
                if unified:
                    posts.append(unified)
                    
        except Exception as e:
            logger.error(f"Reddit fetch_trending error: {e}")
            
        return posts[:limit]
    
    async def fetch_by_url(self, url: str) -> Optional[UnifiedPost]:
        """Fetch a single Reddit post by URL"""
        try:
            # Normalize URL and add .json
            clean_url = url.split("?")[0].rstrip("/")
            if not clean_url.endswith(".json"):
                clean_url += ".json"
            
            # Handle redd.it short URLs
            if "redd.it" in url:
                response = await self.client.get(url, follow_redirects=True)
                clean_url = str(response.url).split("?")[0].rstrip("/") + ".json"
            
            response = await self.client.get(clean_url)
            response.raise_for_status()
            data = response.json()
            
            # Reddit returns array for post pages
            if isinstance(data, list) and len(data) > 0:
                post_data = data[0].get("data", {}).get("children", [{}])[0].get("data", {})
                return self._normalize_post(post_data)
                
        except Exception as e:
            logger.error(f"Reddit fetch_by_url error: {e}")
            
        return None
    
    def _normalize_post(self, data: Dict[str, Any]) -> Optional[UnifiedPost]:
        """Convert Reddit post data to UnifiedPost"""
        try:
            post_id = data.get("id", "")
            subreddit = data.get("subreddit", "")
            
            # Extract media
            media_urls = []
            media_type = None
            
            if data.get("url"):
                url = data["url"]
                if any(ext in url.lower() for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                    media_urls.append(url)
                    media_type = "gif" if ".gif" in url.lower() else "image"
                elif "v.redd.it" in url or "youtube.com" in url or "youtu.be" in url:
                    media_type = "video"
                    media_urls.append(url)
            
            # Preview images
            if not media_urls and data.get("preview", {}).get("images"):
                img_source = data["preview"]["images"][0].get("source", {}).get("url", "")
                if img_source:
                    media_urls.append(img_source.replace("&amp;", "&"))
                    media_type = "image"
            
            # Thumbnail fallback
            if not media_urls and data.get("thumbnail") and data["thumbnail"].startswith("http"):
                media_urls.append(data["thumbnail"])
                media_type = "image"
            
            return UnifiedPost(
                source_network=NetworkSource.REDDIT,
                source_id=post_id,
                source_url=f"https://reddit.com/r/{subreddit}/comments/{post_id}",
                author_username=data.get("author", "[deleted]"),
                author_display_name=data.get("author", "[deleted]"),
                author_profile_url=f"https://reddit.com/u/{data.get('author', '')}",
                content_text=data.get("selftext", "")[:500] if data.get("selftext") else None,
                title=data.get("title", "")[:300],
                subreddit=subreddit,
                media_urls=media_urls,
                media_type=media_type,
                source_likes=data.get("ups", 0),
                source_comments=data.get("num_comments", 0),
                source_created_at=datetime.fromtimestamp(data.get("created_utc", 0), tz=timezone.utc),
                ingested_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Reddit normalize error: {e}")
            return None


class FarcasterConnector(BaseConnector):
    """
    Farcaster connector using public Hubble/Neynar API.
    Farcaster is decentralized - we use public aggregator APIs.
    """
    
    network = NetworkSource.FARCASTER
    # Using Warpcast's public endpoints (no API key needed for basic queries)
    BASE_URL = "https://api.warpcast.com/v2"
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "SocialFi-Ingestion/1.0",
                "Accept": "application/json"
            },
            timeout=30.0
        )
    
    def can_handle_url(self, url: str) -> bool:
        patterns = [
            r'warpcast\.com/\w+/0x[a-fA-F0-9]+',
            r'warpcast\.com/~/conversations/0x[a-fA-F0-9]+'
        ]
        return any(re.search(p, url) for p in patterns)
    
    async def fetch_trending(self, limit: int = 50) -> List[UnifiedPost]:
        """Fetch trending casts from Farcaster"""
        posts = []
        try:
            # Use Warpcast's public trending endpoint
            response = await self.client.get(
                f"{self.BASE_URL}/feed-items",
                params={"feedType": "home", "limit": min(limit, 100)}
            )
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get("result", {}).get("items", []):
                    cast = item.get("cast")
                    if cast:
                        unified = self._normalize_cast(cast)
                        if unified:
                            posts.append(unified)
            else:
                # Fallback: try a simpler public endpoint
                logger.warning(f"Farcaster trending returned {response.status_code}, using fallback")
                
        except Exception as e:
            logger.error(f"Farcaster fetch_trending error: {e}")
            
        return posts[:limit]
    
    async def fetch_by_url(self, url: str) -> Optional[UnifiedPost]:
        """Fetch a single cast by Warpcast URL"""
        try:
            # Extract cast hash from URL
            match = re.search(r'0x([a-fA-F0-9]+)', url)
            if not match:
                return None
                
            cast_hash = f"0x{match.group(1)}"
            
            response = await self.client.get(
                f"{self.BASE_URL}/cast",
                params={"hash": cast_hash}
            )
            
            if response.status_code == 200:
                data = response.json()
                cast = data.get("result", {}).get("cast")
                if cast:
                    return self._normalize_cast(cast)
                    
        except Exception as e:
            logger.error(f"Farcaster fetch_by_url error: {e}")
            
        return None
    
    def _normalize_cast(self, cast: Dict[str, Any]) -> Optional[UnifiedPost]:
        """Convert Farcaster cast to UnifiedPost"""
        try:
            author = cast.get("author", {})
            cast_hash = cast.get("hash", "")
            
            # Extract embeds (images/videos)
            media_urls = []
            media_type = None
            
            for embed in cast.get("embeds", []):
                if embed.get("type") == "image":
                    media_urls.append(embed.get("url", ""))
                    media_type = "image"
                elif embed.get("type") == "video":
                    media_urls.append(embed.get("url", ""))
                    media_type = "video"
            
            return UnifiedPost(
                source_network=NetworkSource.FARCASTER,
                source_id=cast_hash,
                source_url=f"https://warpcast.com/{author.get('username', '')}/{cast_hash}",
                author_username=author.get("username", ""),
                author_display_name=author.get("displayName"),
                author_avatar_url=author.get("pfp", {}).get("url"),
                author_profile_url=f"https://warpcast.com/{author.get('username', '')}",
                content_text=cast.get("text", "")[:500],
                farcaster_channel=cast.get("parentUrl"),
                media_urls=media_urls,
                media_type=media_type,
                source_likes=cast.get("reactions", {}).get("count", 0),
                source_comments=cast.get("replies", {}).get("count", 0),
                source_shares=cast.get("recasts", {}).get("count", 0),
                source_created_at=datetime.fromisoformat(cast.get("timestamp", "").replace("Z", "+00:00")) if cast.get("timestamp") else None,
                ingested_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Farcaster normalize error: {e}")
            return None


class StubConnector(BaseConnector):
    """
    Stub connector for networks that require API keys or OAuth.
    Returns empty results but implements the interface for future use.
    """
    
    def __init__(self, network: NetworkSource):
        self.network = network
        self._url_patterns = {
            NetworkSource.X: [r'twitter\.com/\w+/status/\d+', r'x\.com/\w+/status/\d+'],
            NetworkSource.INSTAGRAM: [r'instagram\.com/p/[\w-]+', r'instagram\.com/reel/[\w-]+'],
            NetworkSource.TWITCH: [r'twitch\.tv/\w+/clip/[\w-]+', r'clips\.twitch\.tv/[\w-]+']
        }
    
    def can_handle_url(self, url: str) -> bool:
        patterns = self._url_patterns.get(self.network, [])
        return any(re.search(p, url) for p in patterns)
    
    async def fetch_trending(self, limit: int = 50) -> List[UnifiedPost]:
        """Stub: Returns empty list"""
        logger.info(f"StubConnector.fetch_trending called for {self.network.value} - no API key configured")
        return []
    
    async def fetch_by_url(self, url: str) -> Optional[UnifiedPost]:
        """Stub: Creates minimal post from URL metadata only"""
        logger.info(f"StubConnector.fetch_by_url for {self.network.value}: {url}")
        
        # Extract basic info from URL structure
        return UnifiedPost(
            source_network=self.network,
            source_id=self._extract_id_from_url(url),
            source_url=url,
            author_username="unknown",
            content_text=f"[Content from {self.network.value} - embed preview only]",
            media_type="embed",
            ingested_at=datetime.now(timezone.utc)
        )
    
    def _extract_id_from_url(self, url: str) -> str:
        """Extract post ID from URL"""
        # Simple extraction - get last path segment or ID pattern
        parts = url.rstrip("/").split("/")
        for part in reversed(parts):
            if part and len(part) > 5:
                return part
        return url


class ConnectorRegistry:
    """Registry for all available connectors"""
    
    def __init__(self):
        self.connectors: Dict[NetworkSource, BaseConnector] = {}
        self._initialize_connectors()
    
    def _initialize_connectors(self):
        """Initialize all connectors"""
        # Working connectors (public API, no auth)
        self.connectors[NetworkSource.REDDIT] = RedditConnector()
        self.connectors[NetworkSource.FARCASTER] = FarcasterConnector()
        
        # Stub connectors (require API keys)
        self.connectors[NetworkSource.X] = StubConnector(NetworkSource.X)
        self.connectors[NetworkSource.INSTAGRAM] = StubConnector(NetworkSource.INSTAGRAM)
        self.connectors[NetworkSource.TWITCH] = StubConnector(NetworkSource.TWITCH)
    
    def get_connector(self, network: NetworkSource) -> Optional[BaseConnector]:
        return self.connectors.get(network)
    
    def find_connector_for_url(self, url: str) -> Optional[BaseConnector]:
        """Find the appropriate connector for a given URL"""
        for connector in self.connectors.values():
            if connector.can_handle_url(url):
                return connector
        return None
    
    async def fetch_all_trending(self, networks: List[NetworkSource] = None, limit_per_network: int = 20) -> List[UnifiedPost]:
        """Fetch trending from multiple networks"""
        if networks is None:
            networks = list(self.connectors.keys())
        
        all_posts = []
        for network in networks:
            connector = self.connectors.get(network)
            if connector:
                try:
                    posts = await connector.fetch_trending(limit=limit_per_network)
                    all_posts.extend(posts)
                except Exception as e:
                    logger.error(f"Error fetching from {network}: {e}")
        
        return all_posts


# Global registry instance
connector_registry = ConnectorRegistry()
