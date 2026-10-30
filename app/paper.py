from __future__ import annotations
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4
from .database import connect, audit
from .market_data import normalize_symbol

class PaperBroker:
    """Persistent, simulated-only broker. Separate USD and INR cash accounts; no live orders."""
    def __init__(self, initial_cash: float = 1_000_000):
        self.initial_cash = float(initial_cash)
        self.lock = Lock()
        conn = connect()
        try:
            for market, currency in [('US', 'USD'), ('IN', 'INR')]:
                conn.execute('INSERT OR IGNORE INTO accounts(market,currency,initial_cash,cash) VALUES(?,?,?,?)',
                             (market, currency, self.initial_cash, self.initial_cash))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def market_currency(symbol: str) -> tuple[str, str]:
        _, market = normalize_symbol(symbol)
        return ('IN', 'INR') if market == 'India (NSE/BSE)' else ('US', 'USD')

    def submit(self, symbol: str, side: str, quantity: float, price: float,
               max_order_notional: float, max_position_notional: float) -> dict:
        from .risk import validate_order
        key, _ = normalize_symbol(symbol)
        market, currency = self.market_currency(key)
        with self.lock:
            conn = connect()
            try:
                conn.execute('BEGIN IMMEDIATE')
                account = conn.execute('SELECT * FROM accounts WHERE market=?', (market,)).fetchone()
                row = conn.execute('SELECT quantity FROM positions WHERE market=? AND symbol=?', (market,key)).fetchone()
                position = float(row['quantity']) if row else 0.0
                decision = validate_order(side, quantity, price, float(account['cash']), position,
                                          max_order_notional, max_position_notional)
                order = {'id': str(uuid4()), 'created_at': datetime.now(timezone.utc).isoformat(),
                         'market': market, 'currency': currency, 'symbol': key, 'side': side,
                         'quantity': float(quantity), 'reference_price': float(price),
                         'notional': round(quantity*price, 2), 'status': 'rejected',
                         'risk_reason': decision.reason, 'broker': 'AURUM_SIMULATED_PAPER_BROKER'}
                if decision.approved:
                    delta = quantity * price * (-1 if side == 'buy' else 1)
                    conn.execute('UPDATE accounts SET cash=cash+? WHERE market=?', (delta, market))
                    new_position = position + quantity if side == 'buy' else position - quantity
                    conn.execute('INSERT INTO positions(market,symbol,quantity) VALUES(?,?,?) ON CONFLICT(market,symbol) DO UPDATE SET quantity=excluded.quantity',
                                 (market,key,new_position))
                    order['status'] = 'filled_simulated'
                conn.execute('''INSERT INTO orders(id,created_at,market,currency,symbol,side,quantity,reference_price,notional,status,risk_reason,broker)
                                VALUES(:id,:created_at,:market,:currency,:symbol,:side,:quantity,:reference_price,:notional,:status,:risk_reason,:broker)''', order)
                conn.execute('INSERT INTO audit_events(created_at,event_type,actor,payload_json) VALUES(?,?,?,?)',
                             (order['created_at'], 'paper_order', 'paper_broker', __import__('json').dumps(order, sort_keys=True)))
                conn.commit()
                return order
            except Exception:
                conn.rollback(); raise
            finally:
                conn.close()

    def snapshot(self) -> dict:
        conn = connect()
        accounts = [dict(r) for r in conn.execute('SELECT * FROM accounts ORDER BY market').fetchall()]
        positions = [dict(r) for r in conn.execute('SELECT p.market,a.currency,p.symbol,p.quantity FROM positions p JOIN accounts a ON a.market=p.market WHERE ABS(p.quantity)>0.0000001 ORDER BY p.market,p.symbol').fetchall()]
        orders = [dict(r) for r in conn.execute('SELECT * FROM orders ORDER BY created_at DESC LIMIT 50').fetchall()]
        conn.close()
        return {'broker':'AURUM_SIMULATED_PAPER_BROKER','accounts':accounts,'positions':positions,'recent_orders':orders,
                'notice':'Persistent simulation only. INR and USD accounts are separate. No live broker is connected.'}
