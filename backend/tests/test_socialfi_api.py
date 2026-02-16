"""
SocialFi Multi-Network Ingestion Platform - Backend API Tests
Tests cover: Health check, Feed API, Networks, Leaderboard, and Auth-required endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthCheck:
    """Health check and root endpoint tests"""
    
    def test_root_endpoint(self):
        """Test root API endpoint returns operational status"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert "SocialFi" in data["message"]
    
    def test_health_endpoint(self):
        """Test health endpoint returns healthy status with DB connection"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"


class TestFeedAPI:
    """Feed endpoint tests - public access"""
    
    def test_feed_returns_posts(self):
        """Test feed endpoint returns posts with market data"""
        response = requests.get(f"{BASE_URL}/api/feed")
        assert response.status_code == 200
        data = response.json()
        
        assert "posts" in data
        assert "total" in data
        assert "has_more" in data
        assert isinstance(data["posts"], list)
        
        # Verify post structure if posts exist
        if len(data["posts"]) > 0:
            post = data["posts"][0]
            assert "id" in post
            assert "source_network" in post
            assert "source_url" in post
            assert "author_username" in post
    
    def test_feed_with_network_filter_reddit(self):
        """Test feed filtering by Reddit network"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"networks": "reddit"})
        assert response.status_code == 200
        data = response.json()
        
        # All posts should be from reddit
        for post in data["posts"]:
            assert post["source_network"] == "reddit"
    
    def test_feed_with_network_filter_farcaster(self):
        """Test feed filtering by Farcaster network"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"networks": "farcaster"})
        assert response.status_code == 200
        data = response.json()
        
        # All posts should be from farcaster
        for post in data["posts"]:
            assert post["source_network"] == "farcaster"
    
    def test_feed_with_network_filter_x(self):
        """Test feed filtering by X network"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"networks": "x"})
        assert response.status_code == 200
        data = response.json()
        
        # All posts should be from x
        for post in data["posts"]:
            assert post["source_network"] == "x"
    
    def test_feed_with_multiple_network_filters(self):
        """Test feed filtering by multiple networks"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"networks": "reddit,farcaster"})
        assert response.status_code == 200
        data = response.json()
        
        # All posts should be from reddit or farcaster
        for post in data["posts"]:
            assert post["source_network"] in ["reddit", "farcaster"]
    
    def test_feed_sort_by_trending(self):
        """Test feed sorting by trending (default)"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"sort": "trending"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["posts"], list)
    
    def test_feed_sort_by_new(self):
        """Test feed sorting by new"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"sort": "new"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["posts"], list)
    
    def test_feed_sort_by_price(self):
        """Test feed sorting by price"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"sort": "price"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["posts"], list)
    
    def test_feed_sort_by_volume(self):
        """Test feed sorting by volume"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"sort": "volume"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["posts"], list)
    
    def test_feed_with_limit(self):
        """Test feed with limit parameter"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"limit": 3})
        assert response.status_code == 200
        data = response.json()
        assert len(data["posts"]) <= 3
    
    def test_feed_with_offset(self):
        """Test feed with offset parameter for pagination"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"limit": 5, "offset": 0})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["posts"], list)
    
    def test_feed_post_has_market_data(self):
        """Test that posts include market data"""
        response = requests.get(f"{BASE_URL}/api/feed")
        assert response.status_code == 200
        data = response.json()
        
        # Check if posts have market data
        posts_with_market = [p for p in data["posts"] if p.get("market")]
        if len(posts_with_market) > 0:
            market = posts_with_market[0]["market"]
            assert "id" in market
            assert "price_current" in market
            assert "total_supply" in market
            assert "total_volume" in market


class TestNetworksAPI:
    """Networks endpoint tests"""
    
    def test_get_available_networks(self):
        """Test getting list of available networks"""
        response = requests.get(f"{BASE_URL}/api/feed/networks")
        assert response.status_code == 200
        data = response.json()
        
        assert "networks" in data
        assert isinstance(data["networks"], list)
        assert len(data["networks"]) >= 5  # reddit, farcaster, x, instagram, twitch
        
        # Verify network structure
        network_ids = [n["id"] for n in data["networks"]]
        assert "reddit" in network_ids
        assert "farcaster" in network_ids
        assert "x" in network_ids
        assert "instagram" in network_ids
        assert "twitch" in network_ids
        
        # Verify each network has required fields
        for network in data["networks"]:
            assert "id" in network
            assert "name" in network
            assert "status" in network
            assert "icon" in network


class TestLeaderboardAPI:
    """Leaderboard endpoint tests"""
    
    def test_get_leaderboard_default(self):
        """Test getting leaderboard with default sort (xp)"""
        response = requests.get(f"{BASE_URL}/api/leaderboard")
        assert response.status_code == 200
        data = response.json()
        
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)
    
    def test_get_leaderboard_by_xp(self):
        """Test getting leaderboard sorted by XP"""
        response = requests.get(f"{BASE_URL}/api/leaderboard", params={"sort_by": "xp"})
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
    
    def test_get_leaderboard_by_reputation(self):
        """Test getting leaderboard sorted by reputation"""
        response = requests.get(f"{BASE_URL}/api/leaderboard", params={"sort_by": "reputation"})
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
    
    def test_get_leaderboard_by_balance(self):
        """Test getting leaderboard sorted by balance"""
        response = requests.get(f"{BASE_URL}/api/leaderboard", params={"sort_by": "balance"})
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
    
    def test_get_leaderboard_with_limit(self):
        """Test getting leaderboard with limit"""
        response = requests.get(f"{BASE_URL}/api/leaderboard", params={"limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert len(data["leaderboard"]) <= 10


class TestAuthRequiredEndpoints:
    """Tests for endpoints that require authentication"""
    
    def test_buy_requires_auth(self):
        """Test buy endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/trades/buy",
            json={"market_id": "test123", "shares": 1}
        )
        assert response.status_code == 401
        data = response.json()
        assert "Authentication required" in data["detail"]
    
    def test_sell_requires_auth(self):
        """Test sell endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/trades/sell",
            json={"market_id": "test123", "shares": 1}
        )
        assert response.status_code == 401
        data = response.json()
        assert "Authentication required" in data["detail"]
    
    def test_portfolio_requires_auth(self):
        """Test portfolio endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/portfolio")
        assert response.status_code == 401
        data = response.json()
        assert "Authentication required" in data["detail"]
    
    def test_paste_url_requires_auth(self):
        """Test paste URL endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/posts/paste-url",
            json={"url": "https://reddit.com/r/test/comments/test123"}
        )
        assert response.status_code == 401
        data = response.json()
        assert "Authentication required" in data["detail"]
    
    def test_auth_me_requires_auth(self):
        """Test /auth/me endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        data = response.json()
        assert "Not authenticated" in data["detail"]


class TestAuthChallengeEndpoint:
    """Tests for wallet authentication challenge endpoint"""
    
    def test_get_challenge_valid_ethereum(self):
        """Test getting challenge for Ethereum wallet"""
        response = requests.post(
            f"{BASE_URL}/api/auth/challenge",
            json={
                "wallet_address": "0x1234567890123456789012345678901234567890",
                "chain_type": "ethereum"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "challenge" in data
        assert "message" in data
        assert "expires_at" in data
        assert len(data["challenge"]) > 0
    
    def test_get_challenge_valid_base(self):
        """Test getting challenge for Base chain wallet"""
        response = requests.post(
            f"{BASE_URL}/api/auth/challenge",
            json={
                "wallet_address": "0x1234567890123456789012345678901234567890",
                "chain_type": "base"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "challenge" in data
    
    def test_get_challenge_valid_polygon(self):
        """Test getting challenge for Polygon wallet"""
        response = requests.post(
            f"{BASE_URL}/api/auth/challenge",
            json={
                "wallet_address": "0x1234567890123456789012345678901234567890",
                "chain_type": "polygon"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "challenge" in data
    
    def test_get_challenge_invalid_chain_type(self):
        """Test challenge with invalid chain type returns error"""
        response = requests.post(
            f"{BASE_URL}/api/auth/challenge",
            json={
                "wallet_address": "0x1234567890123456789012345678901234567890",
                "chain_type": "invalid_chain"
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_get_challenge_short_wallet_address(self):
        """Test challenge with too short wallet address"""
        response = requests.post(
            f"{BASE_URL}/api/auth/challenge",
            json={
                "wallet_address": "0x123",
                "chain_type": "ethereum"
            }
        )
        assert response.status_code == 422  # Validation error


class TestFeedRefreshEndpoint:
    """Tests for feed refresh endpoint"""
    
    def test_feed_refresh_default(self):
        """Test feed refresh with default networks"""
        response = requests.post(f"{BASE_URL}/api/feed/refresh")
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "networks" in data
        assert "Feed refresh started" in data["message"]
    
    def test_feed_refresh_specific_networks(self):
        """Test feed refresh with specific networks"""
        response = requests.post(
            f"{BASE_URL}/api/feed/refresh",
            params={"networks": "reddit"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "reddit" in data["networks"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
