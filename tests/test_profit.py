from app.usecases.calc_profit import calc_profit


def test_calc_profit_basic():
    result = calc_profit(
        sale_price=10000,
        cost_price=5000,
        fee_rate=0.1,
        shipping_cost=500,
        packaging_cost=100,
        other_cost=0,
        target_profit=2000,
    )
    assert result.profit == 10000 - 1000 - 5600
    assert result.breakeven_price > 0
    assert result.min_price_for_target is not None


def test_calc_profit_zero_sale():
    result = calc_profit(
        sale_price=0,
        cost_price=1000,
        fee_rate=0.1,
        shipping_cost=0,
        packaging_cost=0,
    )
    assert result.profit == 0
    assert result.profit_rate == 0.0
