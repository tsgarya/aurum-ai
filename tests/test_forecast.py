import numpy as np
import pandas as pd
from app.forecast import forecast_from_frame

def test_forecast_has_expected_shape_and_clamps_return():
    dates = pd.bdate_range("2024-01-01", periods=120)
    close = 100 * np.cumprod(1 + np.repeat(0.02, 120))
    result = forecast_from_frame("AAPL", pd.DataFrame({"Close": close}, index=dates), "test", 5)
    assert result["symbol"] == "AAPL"
    assert -15 <= result["predicted_return_pct"] <= 15
    assert 0.01 <= result["probability_up"] <= 0.99
    assert result["data_source"] == "test"
