from __future__ import annotations
import json, os, sqlite3
from pathlib import Path
from datetime import datetime, timezone
from threading import Lock

_DB_LOCK = Lock()

def db_path() -> str:
    return os.getenv('AURUM_DB_PATH', './aurum.db')

def connect():
    path = Path(db_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('''CREATE TABLE IF NOT EXISTS accounts (
        market TEXT PRIMARY KEY, currency TEXT NOT NULL, initial_cash REAL NOT NULL, cash REAL NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS positions (
        market TEXT NOT NULL, symbol TEXT NOT NULL, quantity REAL NOT NULL,
        PRIMARY KEY(market, symbol))''')
    conn.execute('''CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY, created_at TEXT NOT NULL, market TEXT NOT NULL, currency TEXT NOT NULL,
        symbol TEXT NOT NULL, side TEXT NOT NULL, quantity REAL NOT NULL, reference_price REAL NOT NULL,
        notional REAL NOT NULL, status TEXT NOT NULL, risk_reason TEXT NOT NULL, broker TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS audit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, event_type TEXT NOT NULL,
        actor TEXT NOT NULL, payload_json TEXT NOT NULL)''')
    conn.commit()
    return conn

def audit(event_type: str, payload: dict, actor: str = 'system') -> None:
    with _DB_LOCK:
        conn = connect()
        conn.execute('INSERT INTO audit_events(created_at,event_type,actor,payload_json) VALUES(?,?,?,?)',
                     (datetime.now(timezone.utc).isoformat(), event_type, actor,
                      json.dumps(payload, sort_keys=True, default=str)))
        conn.commit(); conn.close()

def recent_audit(limit: int = 100) -> list[dict]:
    conn = connect()
    rows = conn.execute('SELECT * FROM audit_events ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return [dict(r, payload=json.loads(r['payload_json'])) for r in rows]
