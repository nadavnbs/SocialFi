"""
Unit tests for AMM (Automated Market Maker) module.
Tests bonding curve calculations and fee distribution.
"""
import pytest
from amm import (
    get_price,
    calculate_buy_cost,
    calculate_sell_revenue,
    distribute_fees,
    BASE_PRICE,
    EXPONENT,
    FEE_RATE
)


class TestGetPrice:
    """Tests for get_price function."""
    
    def test_price_at_zero_supply(self):
        """Price at zero supply should be base price."""
        price = get_price(0)
        assert price == BASE_PRICE
    
    def test_price_at_negative_supply(self):
        """Price at negative supply should be base price."""
        price = get_price(-10)
        assert price == BASE_PRICE
    
    def test_price_increases_with_supply(self):
        """Price should increase as supply increases."""
        price_10 = get_price(10)
        price_100 = get_price(100)
        price_1000 = get_price(1000)
        
        assert price_10 < price_100 < price_1000
    
    def test_price_follows_bonding_curve(self):
        """Price should follow BASE_PRICE * supply^EXPONENT."""
        supply = 100
        expected = BASE_PRICE * (supply ** EXPONENT)
        actual = get_price(supply)
        
        assert abs(actual - expected) < 0.0001


class TestCalculateBuyCost:
    """Tests for calculate_buy_cost function."""
    
    def test_buy_positive_shares(self):
        """Buying positive shares should return valid calculation."""
        result = calculate_buy_cost(100, 10)
        
        assert 'cost_before_fee' in result
        assert 'fee' in result
        assert 'total_cost' in result
        assert 'avg_price' in result
        assert 'new_supply' in result
        assert 'new_price' in result
        
        assert result['cost_before_fee'] > 0
        assert result['fee'] > 0
        # Allow for floating point precision in rounding
        expected_total = result['cost_before_fee'] + result['fee']
        assert abs(result['total_cost'] - expected_total) < 0.01
        assert result['new_supply'] == 110
    
    def test_buy_zero_shares_raises(self):
        """Buying zero shares should raise ValueError."""
        with pytest.raises(ValueError, match="Shares must be positive"):
            calculate_buy_cost(100, 0)
    
    def test_buy_negative_shares_raises(self):
        """Buying negative shares should raise ValueError."""
        with pytest.raises(ValueError, match="Shares must be positive"):
            calculate_buy_cost(100, -10)
    
    def test_buy_negative_supply_raises(self):
        """Starting with negative supply should raise ValueError."""
        with pytest.raises(ValueError, match="Current supply cannot be negative"):
            calculate_buy_cost(-100, 10)
    
    def test_fee_rate_applied_correctly(self):
        """Fee should be FEE_RATE of cost before fee."""
        result = calculate_buy_cost(100, 10)
        expected_fee = result['cost_before_fee'] * FEE_RATE
        
        assert abs(result['fee'] - expected_fee) < 0.0001


class TestCalculateSellRevenue:
    """Tests for calculate_sell_revenue function."""
    
    def test_sell_positive_shares(self):
        """Selling positive shares should return valid calculation."""
        result = calculate_sell_revenue(100, 10)
        
        assert 'revenue_before_fee' in result
        assert 'fee' in result
        assert 'net_revenue' in result
        assert 'avg_price' in result
        assert 'new_supply' in result
        assert 'new_price' in result
        
        assert result['revenue_before_fee'] > 0
        assert result['fee'] > 0
        assert result['net_revenue'] == result['revenue_before_fee'] - result['fee']
        assert result['new_supply'] == 90
    
    def test_sell_zero_shares_raises(self):
        """Selling zero shares should raise ValueError."""
        with pytest.raises(ValueError, match="Shares must be positive"):
            calculate_sell_revenue(100, 0)
    
    def test_sell_negative_shares_raises(self):
        """Selling negative shares should raise ValueError."""
        with pytest.raises(ValueError, match="Shares must be positive"):
            calculate_sell_revenue(100, -10)
    
    def test_sell_more_than_supply_raises(self):
        """Selling more than supply should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot sell more shares than supply"):
            calculate_sell_revenue(100, 150)
    
    def test_sell_zero_supply_raises(self):
        """Selling from zero supply should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sell_revenue(0, 10)
    
    def test_sell_all_shares(self):
        """Selling all shares should result in zero supply."""
        result = calculate_sell_revenue(100, 100)
        
        assert result['new_supply'] == 0
        assert result['new_price'] == 0


class TestDistributeFees:
    """Tests for distribute_fees function."""
    
    def test_fee_distribution(self):
        """Fees should be distributed correctly."""
        fee = 100.0
        result = distribute_fees(fee)
        
        assert 'creator_fee' in result
        assert 'platform_fee' in result
        assert 'liquidity_fee' in result
        
        assert result['creator_fee'] == 50.0  # 50%
        assert result['platform_fee'] == 30.0  # 30%
        assert result['liquidity_fee'] == 20.0  # 20%
    
    def test_fee_distribution_sums_to_total(self):
        """All fee components should sum to original fee."""
        fee = 123.45
        result = distribute_fees(fee)
        
        total = result['creator_fee'] + result['platform_fee'] + result['liquidity_fee']
        assert abs(total - fee) < 0.01


class TestBuySellRoundTrip:
    """Integration tests for buy/sell cycles."""
    
    def test_buy_sell_same_amount(self):
        """Buy then sell same amount should result in loss (fees)."""
        initial_supply = 100
        shares = 10
        
        buy_result = calculate_buy_cost(initial_supply, shares)
        sell_result = calculate_sell_revenue(buy_result['new_supply'], shares)
        
        # User pays total_cost, receives net_revenue
        user_loss = buy_result['total_cost'] - sell_result['net_revenue']
        
        # Loss should equal total fees paid
        assert user_loss > 0
        assert abs(user_loss - (buy_result['fee'] + sell_result['fee'])) < 0.01
    
    def test_supply_returns_to_original_after_round_trip(self):
        """Supply should return to original after buy then sell."""
        initial_supply = 100
        shares = 10
        
        buy_result = calculate_buy_cost(initial_supply, shares)
        sell_result = calculate_sell_revenue(buy_result['new_supply'], shares)
        
        assert sell_result['new_supply'] == initial_supply
