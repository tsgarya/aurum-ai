from app.risk import validate_order

def test_buy_approved_within_limits():
    d = validate_order("buy", 10, 100, 5000, 0, 2000, 5000)
    assert d.approved

def test_order_notional_limit_rejects():
    d = validate_order("buy", 30, 100, 5000, 0, 2000, 5000)
    assert not d.approved
    assert "maximum order" in d.reason

def test_cannot_sell_short():
    d = validate_order("sell", 2, 100, 5000, 1, 2000, 5000)
    assert not d.approved
    assert "more shares" in d.reason

def test_buy_checks_position_limit():
    d = validate_order("buy", 10, 100, 5000, 40, 2000, 4500)
    assert not d.approved
    assert "maximum position" in d.reason
