"""
Locust Load Test Script for SocialFi
=====================================
Simulates concurrent users performing trades, browsing, and API interactions.

Run with:
  locust -f locustfile.py --host=http://localhost:8001 --headless -u 100 -r 10 -t 60s

Options:
  -u 100  : 100 concurrent users
  -r 10   : Spawn 10 users per second
  -t 60s  : Run for 60 seconds
  --headless : Run without web UI
"""
from locust import HttpUser, task, between, events
import secrets
import json
import logging

logging.basicConfig(level=logging.WARNING)


class TradingUser(HttpUser):
    """Simulates a typical SocialFi user."""
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        """Initialize user state."""
        self.wallet = f"0x{secrets.token_hex(20)}"
        self.token = None
        self.market_ids = []
    
    @task(5)
    def view_feed(self):
        """Browse the feed - most common action."""
        with self.client.get(
            "/api/feed",
            catch_response=True,
            name="/api/feed"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Cache market IDs for trading tasks
                for post in data.get('posts', []):
                    if post.get('market'):
                        self.market_ids.append(post['market']['id'])
                response.success()
            elif response.status_code == 429:
                response.success()  # Rate limit is expected under load
            else:
                response.failure(f"Feed failed: {response.status_code}")
    
    @task(3)
    def view_feed_filtered(self):
        """Browse with network filter."""
        networks = ["reddit", "farcaster", "reddit,farcaster"]
        network = secrets.choice(networks)
        self.client.get(f"/api/feed?networks={network}", name="/api/feed?networks=[filter]")
    
    @task(2)
    def view_leaderboard(self):
        """View leaderboard."""
        sort_options = ["xp", "reputation", "balance"]
        sort_by = secrets.choice(sort_options)
        self.client.get(f"/api/leaderboard?sort_by={sort_by}", name="/api/leaderboard")
    
    @task(2)
    def get_networks(self):
        """Get available networks."""
        self.client.get("/api/feed/networks")
    
    @task(1)
    def health_check(self):
        """Health check."""
        with self.client.get("/api/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    response.success()
                else:
                    response.failure("Unhealthy")
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(1)
    def request_challenge(self):
        """Request auth challenge (rate limited)."""
        with self.client.post(
            "/api/auth/challenge",
            json={
                "wallet_address": self.wallet,
                "chain_type": "ethereum"
            },
            catch_response=True,
            name="/api/auth/challenge"
        ) as response:
            if response.status_code in [200, 429]:  # 429 is expected
                response.success()
            else:
                response.failure(f"Challenge failed: {response.status_code}")


class AggressiveTrader(HttpUser):
    """Simulates aggressive trading behavior for stress testing."""
    wait_time = between(0.05, 0.2)
    weight = 2  # 2x weight vs TradingUser
    
    def on_start(self):
        self.wallet = f"0x{secrets.token_hex(20)}"
    
    @task(10)
    def rapid_feed_refresh(self):
        """Rapid feed requests."""
        self.client.get("/api/feed?limit=10", name="/api/feed (rapid)")
    
    @task(5)
    def sorted_feed(self):
        """Feed with different sorts."""
        sorts = ["trending", "new", "price", "volume"]
        self.client.get(f"/api/feed?sort={secrets.choice(sorts)}", name="/api/feed?sort=[type]")
    
    @task(1)
    def paginated_feed(self):
        """Paginated feed requests."""
        offset = secrets.randint(0, 100)
        self.client.get(f"/api/feed?offset={offset}&limit=20", name="/api/feed?offset=[n]")


# Event handlers for metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, **kwargs):
    """Log slow requests."""
    if response_time > 1000:  # > 1 second
        logging.warning(f"Slow request: {name} took {response_time}ms")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary at end."""
    stats = environment.stats
    print("\n" + "="*60)
    print("LOAD TEST SUMMARY")
    print("="*60)
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Failed Requests: {stats.total.num_failures}")
    print(f"Median Response Time: {stats.total.median_response_time}ms")
    print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95)}ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")
    print("="*60)
