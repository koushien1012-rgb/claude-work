import json
from datetime import date, datetime
from pathlib import Path

from macro import get_econ_indicator_calendar

OUT_PATH = Path("dashboard/econ_calendar_data.json")
WITHIN_DAYS = 31


def main():
    today = date.today()
    events = get_econ_indicator_calendar(today, within_days=WITHIN_DAYS)

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "within_days": WITHIN_DAYS,
        "source": "https://fx.minkabu.jp/indicators",
        "events": events,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PATH} ({len(events)} events)")


if __name__ == "__main__":
    main()
