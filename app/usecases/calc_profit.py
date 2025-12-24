from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProfitResult:
    profit: int
    profit_rate: float
    breakeven_price: int
    min_price_for_target: int | None


def calc_profit(
    sale_price: int,
    cost_price: int,
    fee_rate: float,
    shipping_cost: int,
    packaging_cost: int,
    other_cost: int = 0,
    target_profit: int = 0,
) -> ProfitResult:
    if sale_price <= 0:
        return ProfitResult(0, 0.0, 0, None)

    total_cost = cost_price + shipping_cost + packaging_cost + other_cost
    fee = int(round(sale_price * fee_rate))
    profit = sale_price - fee - total_cost
    profit_rate = profit / sale_price

    if fee_rate >= 1:
        breakeven = 0
        min_target = None
    else:
        breakeven = int((total_cost / (1 - fee_rate)) + 0.9999)
        if target_profit > 0:
            min_target = int(
                ((total_cost + target_profit) / (1 - fee_rate)) + 0.9999
            )
        else:
            min_target = None

    return ProfitResult(
        profit=profit,
        profit_rate=profit_rate,
        breakeven_price=breakeven,
        min_price_for_target=min_target,
    )
