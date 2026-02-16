
BASE_PRICE = 0.01
EXPONENT = 1.5
FEE_RATE = 0.02


def get_price(supply: float) -> float:
    """Calculate price per share at given supply."""
    if supply <= 0:
        return BASE_PRICE
    return BASE_PRICE * (supply ** EXPONENT)


def calculate_buy_cost(current_supply: float, shares: float) -> dict:
    """Calculate cost to buy shares including fees."""
    if shares <= 0:
        raise ValueError('Shares must be positive')
    if current_supply < 0:
        raise ValueError('Current supply cannot be negative')
    
    exp_plus_one = EXPONENT + 1
    
    cost_before_fee = (BASE_PRICE / exp_plus_one) * (
        (current_supply + shares) ** exp_plus_one - current_supply ** exp_plus_one
    )
    
    fee = cost_before_fee * FEE_RATE
    total_cost = cost_before_fee + fee
    
    avg_price = cost_before_fee / shares
    new_supply = current_supply + shares
    new_price = get_price(new_supply)
    
    return {
        'cost_before_fee': round(cost_before_fee, 6),
        'fee': round(fee, 6),
        'total_cost': round(total_cost, 6),
        'avg_price': round(avg_price, 6),
        'new_supply': round(new_supply, 6),
        'new_price': round(new_price, 6)
    }


def calculate_sell_revenue(current_supply: float, shares: float) -> dict:
    """Calculate revenue from selling shares after fees."""
    if shares <= 0:
        raise ValueError('Shares must be positive')
    if shares > current_supply:
        raise ValueError('Cannot sell more shares than supply')
    if current_supply <= 0:
        raise ValueError('Current supply must be positive')
    
    exp_plus_one = EXPONENT + 1
    
    revenue_before_fee = (BASE_PRICE / exp_plus_one) * (
        current_supply ** exp_plus_one - (current_supply - shares) ** exp_plus_one
    )
    
    fee = revenue_before_fee * FEE_RATE
    net_revenue = revenue_before_fee - fee  # FIXED: Renamed from total_revenue
    
    avg_price = revenue_before_fee / shares
    new_supply = current_supply - shares
    new_price = get_price(new_supply) if new_supply > 0 else 0
    
    return {
        'revenue_before_fee': round(revenue_before_fee, 6),
        'fee': round(fee, 6),
        'net_revenue': round(net_revenue, 6),  # FIXED: Consistent naming
        'avg_price': round(avg_price, 6),
        'new_supply': round(new_supply, 6),
        'new_price': round(new_price, 6)
    }


def distribute_fees(fee_amount: float) -> dict:
    """Split fee: 50% creator, 30% platform, 20% liquidity."""
    return {
        'creator_fee': round(fee_amount * 0.50, 6),
        'platform_fee': round(fee_amount * 0.30, 6),
        'liquidity_fee': round(fee_amount * 0.20, 6)
    }
