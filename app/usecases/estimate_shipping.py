from __future__ import annotations

from dataclasses import dataclass

from app.infra.db.repo import ShippingRule


@dataclass(frozen=True)
class ShippingInput:
    length: int
    width: int
    height: int
    weight: int
    packaging_cost: int


@dataclass(frozen=True)
class ShippingEstimate:
    rule: ShippingRule
    total_cost: int


def estimate_shipping(
    rules: list[ShippingRule], data: ShippingInput
) -> list[ShippingEstimate]:
    candidates: list[ShippingEstimate] = []
    for rule in rules:
        if not _fits(rule, data):
            continue
        total = rule.price + data.packaging_cost
        candidates.append(ShippingEstimate(rule=rule, total_cost=total))

    candidates.sort(key=lambda x: x.total_cost)
    return candidates


def _fits(rule: ShippingRule, data: ShippingInput) -> bool:
    if rule.max_l is not None and data.length > rule.max_l:
        return False
    if rule.max_w is not None and data.width > rule.max_w:
        return False
    if rule.max_h is not None and data.height > rule.max_h:
        return False
    if rule.max_weight is not None and data.weight > rule.max_weight:
        return False
    return True
