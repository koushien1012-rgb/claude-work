import json
from unittest.mock import patch

import generate_econ_calendar as mod


def test_main_writes_payload_with_events(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "dashboard").mkdir()

    fake_events = [
        {"date": "2026-09-24", "time": "10:30", "country": "豪", "country_code": "AU",
         "indicator_name": "豪・雇用統計 08月 [失業率]", "indicator_url": "https://fx.minkabu.jp/indicators/AU-UR",
         "importance": 3, "prev_usdjpy_move": "+2.3pips", "previous": "4.5%", "forecast": "4.5%", "result": "---"},
    ]
    with patch.object(mod, "get_econ_indicator_calendar", return_value=fake_events) as mock_get:
        mod.main()

    mock_get.assert_called_once()
    out_path = tmp_path / "dashboard" / "econ_calendar_data.json"
    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["events"] == fake_events
    assert data["within_days"] == mod.WITHIN_DAYS
    assert "generated_at" in data
    assert data["source"] == "https://fx.minkabu.jp/indicators"
