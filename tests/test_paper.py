import pytest
from app.paper import PaperBroker

@pytest.fixture
def broker(tmp_path, monkeypatch):
    monkeypatch.setenv('AURUM_DB_PATH', str(tmp_path / 'test.db'))
    return PaperBroker(10000)

def test_paper_order_fills_and_updates_cash(broker):
    order = broker.submit('AAPL', 'buy', 10, 100, 2000, 5000)
    assert order['status'] == 'filled_simulated'
    snapshot = broker.snapshot()
    us = next(a for a in snapshot['accounts'] if a['market'] == 'US')
    assert us['cash'] == 9000
    assert snapshot['positions'][0]['quantity'] == 10

def test_rejected_order_does_not_change_cash(broker):
    order = broker.submit('AAPL', 'buy', 100, 100, 2000, 5000)
    assert order['status'] == 'rejected'
    us = next(a for a in broker.snapshot()['accounts'] if a['market'] == 'US')
    assert us['cash'] == 10000

def test_markets_have_separate_currency_accounts(broker):
    broker.submit('RELIANCE.NS', 'buy', 1, 1000, 2000, 5000)
    snap = broker.snapshot()
    assert {a['currency'] for a in snap['accounts']} == {'USD', 'INR'}
    assert len(snap['positions']) == 1 and snap['positions'][0]['market'] == 'IN'

def test_cannot_sell_shares_not_held(broker):
    order = broker.submit('AAPL', 'sell', 1, 100, 2000, 5000)
    assert order['status'] == 'rejected'

def test_ledger_persists_across_broker_instances(tmp_path, monkeypatch):
    monkeypatch.setenv('AURUM_DB_PATH', str(tmp_path / 'persistent.db'))
    first = PaperBroker(10000)
    first.submit('AAPL', 'buy', 2, 50, 1000, 2000)
    second = PaperBroker(10000)
    snap = second.snapshot()
    us = next(a for a in snap['accounts'] if a['market'] == 'US')
    assert us['cash'] == 9900
    assert snap['positions'][0]['quantity'] == 2
    assert len(snap['recent_orders']) == 1
