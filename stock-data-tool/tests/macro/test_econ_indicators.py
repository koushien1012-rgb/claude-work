from datetime import date
from unittest.mock import patch

from macro.econ_indicators import get_calendar, parse_calendar_html

# A trimmed-down fixture mirroring fx.minkabu.jp/indicators' real markup: one
# day, two indicators (one with a forecast/result already filled in, one
# still pending), each with the data_importance/data_country attributes and
# the per-indicator detail-page link the real page uses.
_FIXTURE_HTML = """
<html><body>
<table class="tbl-border tbl-fixed tbl-alternate mt5 mb5">
<caption class="tbl__caption tlft pl10 pt5 pb5 fs-s fbd">2026年09月23日(水)</caption>
<tr class="fs-s" data_importance="2" data_country="DE">
  <td class="eilist__time p5 tbl__time-soon"><span>16:30</span></td>
  <td class="tbl__middle eilist__time p5"><div class="flag_container"><svg></svg></div></td>
  <td class="tbl__middle p5"><a class="flexbox" href="/indicators/DE-PMIP"><p class="flexbox__grow fbd">ドイツ・製造業PMI（購買担当者景気指数）（速報値） 09月 [製造業PMI（購買担当者指数）]</p></a></td>
  <td class="tbl__middle eilist__star p5"><span></span></td>
  <td class="tbl__middle eilist__move trit pt5 pr5 is-minus"><span>-10.2pips</span></td>
  <td class="tbl__middle eilist__data trit pt5 pr5"><span>54.3</span></td>
  <td class="tbl__middle eilist__data trit pt5 pr5"><span>---</span></td>
  <td class="tbl__middle eilist__data trit pt5 pr5"><span>---</span></td>
</tr>
<tr class="fs-s" data_importance="3" data_country="ZA">
  <td class="eilist__time p5 tbl__time-soon"><span>未定</span></td>
  <td class="tbl__middle eilist__time p5"><div class="flag_container"><svg></svg></div></td>
  <td class="tbl__middle p5"><a class="flexbox" href="/indicators/ZA-CPI"><p class="flexbox__grow fbd">南ア・消費者物価指数 08月 [前年比]</p></a></td>
  <td class="tbl__middle eilist__star p5"><span></span></td>
  <td class="tbl__middle eilist__move trit pt5 pr5 is-minus"><span>-4.3pips</span></td>
  <td class="tbl__middle eilist__data trit pt5 pr5"><span>4.3%</span></td>
  <td class="tbl__middle eilist__data trit pt5 pr5"><span>4.6%</span></td>
  <td class="tbl__middle eilist__data trit pt5 pr5"><span>4.7%</span></td>
</tr>
</table>
</body></html>
"""


def test_parse_calendar_html_extracts_all_fields():
    events = parse_calendar_html(_FIXTURE_HTML)
    assert len(events) == 2

    de = events[0]
    assert de["date"] == "2026-09-23"
    assert de["time"] == "16:30"
    assert de["country"] == "ドイツ"
    assert de["country_code"] == "DE"
    assert de["indicator_name"].startswith("ドイツ・製造業PMI")
    assert de["indicator_url"] == "https://fx.minkabu.jp/indicators/DE-PMIP"
    assert de["importance"] == 2
    assert de["prev_usdjpy_move"] == "-10.2pips"
    assert de["previous"] == "54.3"
    assert de["forecast"] == "---"
    assert de["result"] == "---"


def test_parse_calendar_html_handles_undetermined_time():
    events = parse_calendar_html(_FIXTURE_HTML)
    za = events[1]
    assert za["time"] == "未定"
    assert za["importance"] == 3
    assert za["result"] == "4.7%"


def test_get_calendar_dedupes_overlapping_weeks_and_filters_by_window():
    # Two consecutive week-fetches returning the SAME fixture (as real overlapping
    # weeks would for a shared date) must not produce duplicate events, and events
    # outside the requested window must be dropped.
    with patch("macro.econ_indicators.get_calendar_week", return_value=parse_calendar_html(_FIXTURE_HTML)):
        events = get_calendar(date(2026, 9, 23), within_days=7)

    assert len(events) == 2  # deduped, not 2 * (number of week-fetches)
    assert all(e["date"] == "2026-09-23" for e in events)


def test_get_calendar_excludes_events_before_today():
    with patch("macro.econ_indicators.get_calendar_week", return_value=parse_calendar_html(_FIXTURE_HTML)):
        events = get_calendar(date(2026, 9, 24), within_days=7)
    assert events == []


def test_get_calendar_sorts_timed_events_before_undetermined_ones():
    with patch("macro.econ_indicators.get_calendar_week", return_value=parse_calendar_html(_FIXTURE_HTML)):
        events = get_calendar(date(2026, 9, 23), within_days=0)
    assert [e["time"] for e in events] == ["16:30", "未定"]
