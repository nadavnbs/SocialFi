"""
Farcaster Frames Tests
=======================
Tests for Frame generation, validation, and security.
"""
import pytest
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, AsyncMock


class TestFrameGeneration:
    """Tests for Frame HTML generation."""
    
    def test_generates_valid_frame_html(self):
        """Generated HTML should have required Frame meta tags."""
        from farcaster_frames import generate_frame_html
        
        html = generate_frame_html(
            title="Test Frame",
            image_url="https://example.com/image.png",
            buttons=[
                {"label": "Button 1", "action": "post"},
                {"label": "Button 2", "action": "link", "target": "https://example.com"}
            ],
            post_url="https://example.com/api/frame",
            state="test:state"
        )
        
        # Check required meta tags
        assert 'fc:frame' in html
        assert 'content="vNext"' in html
        assert 'fc:frame:image' in html
        assert 'fc:frame:post_url' in html
        assert 'fc:frame:button:1' in html
        assert 'fc:frame:button:2' in html
        assert 'fc:frame:state' in html
    
    def test_limits_buttons_to_four(self):
        """Frame should only include max 4 buttons."""
        from farcaster_frames import generate_frame_html
        
        html = generate_frame_html(
            title="Test",
            image_url="https://example.com/img.png",
            buttons=[
                {"label": "B1"}, {"label": "B2"}, 
                {"label": "B3"}, {"label": "B4"}, 
                {"label": "B5"}  # Should be ignored
            ],
            post_url="https://example.com/api"
        )
        
        assert 'fc:frame:button:4' in html
        assert 'fc:frame:button:5' not in html
    
    def test_market_preview_frame_content(self):
        """Market preview frame should show price and buttons."""
        from farcaster_frames import generate_market_preview_frame
        
        html = generate_market_preview_frame(
            market_id="test123",
            post_title="Viral Reddit Post About Crypto",
            current_price=1.5,
            price_change_24h=5.2,
            volume_24h=1000.0,
            base_url="https://socialfi.com"
        )
        
        # Check content
        assert "Buy 1 Share" in html
        assert "Buy 5 Shares" in html
        assert "View Market" in html
        assert "test123" in html


class TestFrameValidation:
    """Tests for Frame message validation."""
    
    @pytest.mark.asyncio
    async def test_rejects_missing_fid(self):
        """Should reject payload without FID."""
        from farcaster_frames import validate_frame_message, FrameActionPayload
        
        payload = FrameActionPayload(
            untrustedData={"buttonIndex": 1, "timestamp": int(time.time() * 1000)},
            trustedData={"messageBytes": "abc123"}
        )
        
        result = await validate_frame_message(payload)
        
        assert result.is_valid is False
        assert "fid" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_rejects_old_timestamp(self):
        """Should reject messages older than 5 minutes."""
        from farcaster_frames import validate_frame_message, FrameActionPayload
        
        old_timestamp = int((time.time() - 400) * 1000)  # 6+ minutes ago
        
        payload = FrameActionPayload(
            untrustedData={
                "fid": 12345,
                "buttonIndex": 1,
                "timestamp": old_timestamp
            },
            trustedData={"messageBytes": "abc123"}
        )
        
        result = await validate_frame_message(payload)
        
        assert result.is_valid is False
        assert "old" in result.error.lower() or "expired" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_rejects_future_timestamp(self):
        """Should reject messages with future timestamps."""
        from farcaster_frames import validate_frame_message, FrameActionPayload
        
        future_timestamp = int((time.time() + 120) * 1000)  # 2 minutes in future
        
        payload = FrameActionPayload(
            untrustedData={
                "fid": 12345,
                "buttonIndex": 1,
                "timestamp": future_timestamp
            },
            trustedData={"messageBytes": "abc123"}
        )
        
        result = await validate_frame_message(payload)
        
        assert result.is_valid is False
        assert "future" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_accepts_valid_message(self):
        """Should accept valid frame message."""
        from farcaster_frames import validate_frame_message, FrameActionPayload
        
        payload = FrameActionPayload(
            untrustedData={
                "fid": 12345,
                "buttonIndex": 1,
                "timestamp": int(time.time() * 1000),
                "inputText": "test input"
            },
            trustedData={"messageBytes": "abc123"}
        )
        
        result = await validate_frame_message(payload)
        
        assert result.is_valid is True
        assert result.fid == 12345
        assert result.button_index == 1
        assert result.input_text == "test input"


class TestFrameRateLimiting:
    """Tests for Frame-specific rate limiting."""
    
    def test_allows_requests_under_limit(self):
        """Should allow requests under rate limit."""
        from farcaster_frames import FrameRateLimiter
        
        limiter = FrameRateLimiter(max_requests=10, window_seconds=60)
        
        # Make 10 requests - all should succeed
        for i in range(10):
            allowed, _ = limiter.is_allowed(fid=12345)
            assert allowed is True
    
    def test_blocks_requests_over_limit(self):
        """Should block requests over rate limit."""
        from farcaster_frames import FrameRateLimiter
        
        limiter = FrameRateLimiter(max_requests=5, window_seconds=60)
        
        # Make 5 requests (should all succeed)
        for _ in range(5):
            limiter.is_allowed(fid=12345)
        
        # 6th request should fail
        allowed, retry_after = limiter.is_allowed(fid=12345)
        assert allowed is False
        assert retry_after > 0
    
    def test_different_fids_have_separate_limits(self):
        """Different FIDs should have independent rate limits."""
        from farcaster_frames import FrameRateLimiter
        
        limiter = FrameRateLimiter(max_requests=2, window_seconds=60)
        
        # FID 1 uses up limit
        limiter.is_allowed(fid=1)
        limiter.is_allowed(fid=1)
        allowed_1, _ = limiter.is_allowed(fid=1)
        
        # FID 2 should still be allowed
        allowed_2, _ = limiter.is_allowed(fid=2)
        
        assert allowed_1 is False
        assert allowed_2 is True


class TestFrameReplayPrevention:
    """Tests for replay attack prevention."""
    
    def test_detects_replay_attack(self):
        """Should detect replayed message hash."""
        from farcaster_frames import FrameNonceTracker
        
        tracker = FrameNonceTracker(ttl_seconds=300)
        
        message_hash = "abc123def456"
        
        # First use should succeed
        is_new_1 = tracker.check_and_record(message_hash)
        assert is_new_1 is True
        
        # Second use (replay) should fail
        is_new_2 = tracker.check_and_record(message_hash)
        assert is_new_2 is False
    
    def test_different_hashes_allowed(self):
        """Different message hashes should be allowed."""
        from farcaster_frames import FrameNonceTracker
        
        tracker = FrameNonceTracker(ttl_seconds=300)
        
        is_new_1 = tracker.check_and_record("hash1")
        is_new_2 = tracker.check_and_record("hash2")
        
        assert is_new_1 is True
        assert is_new_2 is True
    
    def test_expires_old_hashes(self):
        """Old message hashes should be cleaned up."""
        from farcaster_frames import FrameNonceTracker
        
        tracker = FrameNonceTracker(ttl_seconds=1)  # 1 second TTL
        
        message_hash = "test_hash"
        tracker.check_and_record(message_hash)
        
        # Wait for expiry
        import time
        time.sleep(1.5)
        
        # Should be allowed again after expiry
        is_new = tracker.check_and_record(message_hash)
        assert is_new is True


class TestFrameBuyProcessing:
    """Tests for frame buy action processing."""
    
    @pytest.mark.asyncio
    async def test_rate_limits_frame_buys(self):
        """Should rate limit frame buy requests."""
        from farcaster_frames import FrameRateLimiter
        
        limiter = FrameRateLimiter(max_requests=2, window_seconds=60)
        
        # Exhaust rate limit
        limiter.is_allowed(fid=99999)
        limiter.is_allowed(fid=99999)
        
        # Third should be blocked
        allowed, retry = limiter.is_allowed(fid=99999)
        assert allowed is False
        assert retry > 0


class TestFrameSecurityEdgeCases:
    """Edge case tests for frame security."""
    
    @pytest.mark.asyncio
    async def test_handles_malformed_payload(self):
        """Should handle malformed frame payloads gracefully."""
        from farcaster_frames import validate_frame_message, FrameActionPayload
        
        # Missing fields
        payload = FrameActionPayload(
            untrustedData={},
            trustedData={}
        )
        
        result = await validate_frame_message(payload)
        assert result.is_valid is False
    
    @pytest.mark.asyncio
    async def test_handles_invalid_button_index(self):
        """Should validate button index is 1-4 in FrameMessage."""
        from farcaster_frames import FrameMessage
        from pydantic import ValidationError
        
        # Button index must be 1-4 in FrameMessage model
        with pytest.raises(ValidationError):
            FrameMessage(
                fid=12345,
                url="https://example.com",
                messageHash="abc123",
                timestamp=int(time.time() * 1000),
                buttonIndex=5  # Invalid - must be 1-4
            )
    
    def test_state_encoding(self):
        """State should be properly encoded in frame HTML."""
        from farcaster_frames import generate_frame_html
        
        # State with special characters
        state = "market:abc123:user:0x1234"
        
        html = generate_frame_html(
            title="Test",
            image_url="https://example.com/img.png",
            buttons=[{"label": "Test"}],
            post_url="https://example.com/api",
            state=state
        )
        
        assert state in html
        assert 'fc:frame:state' in html
