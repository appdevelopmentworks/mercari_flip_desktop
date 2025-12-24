from app.infra.db.repo import ShippingRule
from app.usecases.estimate_shipping import ShippingInput, estimate_shipping


def test_estimate_shipping_filters_and_sorts():
    rules = [
        ShippingRule(
            id=1,
            carrier="c1",
            service_name="s1",
            max_l=10,
            max_w=10,
            max_h=10,
            max_weight=1000,
            price=500,
            packaging_cost=0,
            enabled=1,
        ),
        ShippingRule(
            id=2,
            carrier="c2",
            service_name="s2",
            max_l=20,
            max_w=20,
            max_h=20,
            max_weight=2000,
            price=300,
            packaging_cost=0,
            enabled=1,
        ),
    ]

    data = ShippingInput(
        length=12,
        width=12,
        height=12,
        weight=1200,
        packaging_cost=50,
    )
    results = estimate_shipping(rules, data)
    assert len(results) == 1
    assert results[0].rule.id == 2
    assert results[0].total_cost == 350
