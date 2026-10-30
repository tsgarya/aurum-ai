from fastapi.testclient import TestClient
from app.main import app

def test_health_endpoint():
    client = TestClient(app)
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['trading_mode'] == 'paper_only'

def test_dashboard_is_served():
    client = TestClient(app)
    response = client.get('/')
    assert response.status_code == 200
    assert 'AURUM AI' in response.text

def test_forecast_endpoint_returns_forecast():
    client = TestClient(app)
    response = client.get('/api/forecast/AAPL')
    assert response.status_code == 200
    body = response.json()
    assert body['symbol'] == 'AAPL'
    assert body['horizon_trading_days'] == 5
