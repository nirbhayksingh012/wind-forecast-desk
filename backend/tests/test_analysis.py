"""Comprehensive unit tests for the analysis module.

Tests cover: forecast selection, cutoff logic, DST, metrics, coverage,
hourly vs half-hourly handling, edge cases, and day-rows status fields.
"""
from datetime import date, datetime, timezone

import pytest

from app import analysis as a

UTC = timezone.utc


# --------------- Fixtures ---------------

def ds_two_forecasts():
    # Slot 2026-01-02 12:00Z has three forecasts; cutoff is 2026-01-01 09:00Z.
    slot = "2026-01-02T12:00:00Z"
    return a.build_dataset(
        [(slot, 5000)],
        [
            (slot, "2026-01-01T06:00:00Z", 4000),   # older
            (slot, "2026-01-01T09:00:00Z", 4500),   # exactly at cutoff -> allowed
            (slot, "2026-01-01T09:30:00Z", 9999),   # after cutoff -> must be ignored
        ],
    )


def ds_hourly_only():
    """A dataset that mimics real WINDFOR: forecasts only on whole hours."""
    actuals = [
        ("2026-01-02T00:00:00Z", 1000),
        ("2026-01-02T00:30:00Z", 1050),
        ("2026-01-02T01:00:00Z", 1100),
        ("2026-01-02T01:30:00Z", 1150),
    ]
    forecasts = [
        ("2026-01-02T00:00:00Z", "2026-01-01T08:00:00Z", 900),
        ("2026-01-02T01:00:00Z", "2026-01-01T08:00:00Z", 1000),
        # no forecast for :30 slots -> same as real WINDFOR
    ]
    return a.build_dataset(actuals, forecasts)


# --------------- Original tests ---------------

def test_selects_latest_forecast_at_or_before_cutoff():
    ds = ds_two_forecasts()
    slot = datetime(2026, 1, 2, 12, tzinfo=UTC)
    pub, gen = a.select_forecast(ds, slot, a.cutoff_utc(date(2026, 1, 2), "09:00"))
    assert gen == 4500 and pub == datetime(2026, 1, 1, 9, tzinfo=UTC)


def test_no_forecast_before_cutoff_gives_none():
    ds = ds_two_forecasts()
    slot = datetime(2026, 1, 2, 12, tzinfo=UTC)
    assert a.select_forecast(ds, slot, a.cutoff_utc(date(2026, 1, 2), "05:00")) is None


def test_day_rows_error_and_horizon():
    rows = a.day_rows(ds_two_forecasts(), date(2026, 1, 2), "09:00")
    assert len(rows) == 48
    r = next(r for r in rows if r["forecast"] is not None)
    assert r["error"] == -500          # forecast 4500 - actual 5000
    assert r["horizon_h"] == 27.0      # 09:00 on 1 Jan -> 12:00 on 2 Jan


def test_cutoff_uses_uk_clock_including_summer_time():
    assert a.cutoff_utc(date(2026, 1, 2), "09:00") == datetime(2026, 1, 1, 9, tzinfo=UTC)
    # 09:00 BST is 08:00 UTC
    assert a.cutoff_utc(date(2026, 7, 2), "09:00") == datetime(2026, 7, 1, 8, tzinfo=UTC)


def test_dst_day_lengths():
    assert len(a.delivery_slots(date(2026, 1, 2))) == 48
    assert len(a.delivery_slots(date(2026, 3, 29))) == 46   # clocks go forward
    assert len(a.delivery_slots(date(2026, 10, 25))) == 50  # clocks go back


def test_metrics():
    rows = [
        {"error": 100.0, "actual": 1000.0},
        {"error": -300.0, "actual": 1000.0},
        {"error": None, "actual": 1000.0},   # unscored rows are ignored
    ]
    m = a.metrics(rows)
    assert m["n"] == 2
    assert m["mae"] == pytest.approx(200)
    assert m["bias"] == pytest.approx(-100)
    assert m["rmse"] == pytest.approx(((100**2 + 300**2) / 2) ** 0.5)
    assert m["over_forecast_share"] == 0.5
    assert m["nmae_pct"] == pytest.approx(20)


def test_metrics_empty():
    assert a.metrics([]) == {"n": 0}


def test_quantile_interpolates():
    assert a.quantile([0, 10], 0.5) == 5
    assert a.quantile([1, 2, 3, 4, 5], 0.0) == 1
    assert a.quantile([1, 2, 3, 4, 5], 1.0) == 5


def test_delivery_dates_cover_decisions_in_january():
    days = a.delivery_dates(date(2026, 1, 1), date(2026, 1, 31))
    assert days[0] == date(2026, 1, 2) and days[-1] == date(2026, 2, 1) and len(days) == 31


# --------------- New tests: forecast selection edge cases ---------------

def test_select_forecast_exactly_at_cutoff_is_included():
    """A forecast published exactly at cutoff should be included (<=, not <)."""
    ds = ds_two_forecasts()
    slot = datetime(2026, 1, 2, 12, tzinfo=UTC)
    cutoff = datetime(2026, 1, 1, 9, 0, 0, tzinfo=UTC)  # exactly matches publish time
    pub, gen = a.select_forecast(ds, slot, cutoff)
    assert gen == 4500


def test_select_forecast_one_second_before_cutoff_excludes():
    """Forecast at 09:00 should NOT be selected if cutoff is 08:59:59."""
    ds = ds_two_forecasts()
    slot = datetime(2026, 1, 2, 12, tzinfo=UTC)
    # cutoff at 08:59 - the 09:00 forecast should be excluded, only 06:00 should match
    cutoff = datetime(2026, 1, 1, 8, 59, tzinfo=UTC)
    pub, gen = a.select_forecast(ds, slot, cutoff)
    assert gen == 4000


def test_forecast_after_cutoff_is_excluded():
    """Forecasts published after the cutoff must never be selected."""
    ds = ds_two_forecasts()
    slot = datetime(2026, 1, 2, 12, tzinfo=UTC)
    cutoff = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)
    _, gen = a.select_forecast(ds, slot, cutoff)
    assert gen != 9999  # the 09:30 forecast must not leak through


def test_select_forecast_no_entry_for_slot():
    """A slot with no forecast data at all returns None."""
    ds = ds_two_forecasts()
    unknown_slot = datetime(2099, 1, 1, 0, 0, tzinfo=UTC)
    assert a.select_forecast(ds, unknown_slot, datetime(2099, 1, 1, 12, tzinfo=UTC)) is None


# --------------- New tests: hourly/half-hourly status ---------------

def test_day_rows_status_field():
    """Day rows should have correct status for each slot type."""
    rows = a.day_rows(ds_two_forecasts(), date(2026, 1, 2), "09:00")
    # The 12:00Z slot has both forecast and actual -> matched
    matched = [r for r in rows if r["status"] == "matched"]
    assert len(matched) == 1
    assert matched[0]["forecast"] == 4500 and matched[0]["actual"] == 5000

    # Half-hour slots (not on the hour) with no forecast -> interstitial
    interstitial = [r for r in rows if r["status"] == "interstitial"]
    assert len(interstitial) == 24  # 48 total, 24 on-hour, 24 half-hour


def test_day_rows_is_on_hour_field():
    """is_on_hour should be True for :00 slots and False for :30 slots."""
    rows = a.day_rows(ds_two_forecasts(), date(2026, 1, 2), "09:00")
    on_hour = [r for r in rows if r["is_on_hour"]]
    off_hour = [r for r in rows if not r["is_on_hour"]]
    assert len(on_hour) == 24
    assert len(off_hour) == 24


def test_hourly_forecast_matches_hourly_slots_only():
    """Hourly forecasts should only match on-hour slots, not :30 slots."""
    ds = ds_hourly_only()
    rows = a.day_rows(ds, date(2026, 1, 2), "09:00")
    with_fc = [r for r in rows if r["forecast"] is not None]
    # Only 00:00 and 01:00 should have forecasts
    for r in with_fc:
        assert r["is_on_hour"] is True


# --------------- New tests: zero generation is valid ---------------

def test_zero_generation_is_valid_data():
    """Zero-valued generation must remain valid, not be treated as missing."""
    ds = a.build_dataset(
        [("2026-01-02T12:00:00Z", 0)],  # zero actual
        [("2026-01-02T12:00:00Z", "2026-01-01T08:00:00Z", 0)],  # zero forecast
    )
    rows = a.day_rows(ds, date(2026, 1, 2), "09:00")
    r = next(r for r in rows if r["start"] == "2026-01-02T12:00:00Z")
    assert r["forecast"] == 0
    assert r["actual"] == 0
    assert r["error"] == 0
    assert r["status"] == "matched"


# --------------- New tests: duplicate handling ---------------

def test_duplicate_forecast_timestamps_deterministic():
    """When two forecasts have the same publishTime, deduplication should not crash."""
    ds = a.build_dataset(
        [("2026-01-02T12:00:00Z", 5000)],
        [
            ("2026-01-02T12:00:00Z", "2026-01-01T06:00:00Z", 4000),
            ("2026-01-02T12:00:00Z", "2026-01-01T06:00:00Z", 4100),  # same pub time!
        ],
    )
    # build_dataset uses dict keyed by publish time, so last write wins
    slot = datetime(2026, 1, 2, 12, tzinfo=UTC)
    result = a.select_forecast(ds, slot, datetime(2026, 1, 1, 9, tzinfo=UTC))
    assert result is not None
    _, gen = result
    assert gen in (4000, 4100)  # either is acceptable; key is no crash


# --------------- New tests: metrics edge cases ---------------

def test_metrics_single_observation():
    """Metrics should work with a single observation."""
    rows = [{"error": 500.0, "actual": 3000.0}]
    m = a.metrics(rows)
    assert m["n"] == 1
    assert m["mae"] == pytest.approx(500)
    assert m["rmse"] == pytest.approx(500)
    assert m["bias"] == pytest.approx(500)
    assert m["nmae_pct"] == pytest.approx(500 / 3000 * 100)


def test_metrics_all_over_forecast():
    """If all errors are positive, over-forecast share should be 1.0."""
    rows = [
        {"error": 100.0, "actual": 1000.0},
        {"error": 200.0, "actual": 1000.0},
    ]
    m = a.metrics(rows)
    assert m["over_forecast_share"] == 1.0


def test_metrics_all_under_forecast():
    """If all errors are negative, over-forecast share should be 0.0."""
    rows = [
        {"error": -100.0, "actual": 1000.0},
        {"error": -200.0, "actual": 1000.0},
    ]
    m = a.metrics(rows)
    assert m["over_forecast_share"] == 0.0


# --------------- New tests: coverage ---------------

def test_accuracy_report_coverage_fields():
    """Coverage response should contain all expected fields."""
    ds = ds_two_forecasts()
    rep = a.accuracy_report(ds, date(2026, 1, 1), date(2026, 1, 2), "09:00")
    cov = rep["coverage"]
    assert "total_hh_slots" in cov
    assert "hourly_slots" in cov
    assert "with_forecast" in cov
    assert "with_actual" in cov
    assert "matched" in cov
    assert "forecast_coverage_pct" in cov
    assert "hh_coverage_pct" in cov
    assert "note" in cov


def test_accuracy_report_matched_equals_scored():
    """The matched count in coverage should equal overall n in metrics."""
    ds = ds_two_forecasts()
    rep = a.accuracy_report(ds, date(2026, 1, 1), date(2026, 1, 2), "09:00")
    assert rep["coverage"]["matched"] == rep["overall"]["n"]


# --------------- New tests: latest_publish ---------------

def test_latest_publish_returns_max():
    """latest_publish should return the max publish time, not the first."""
    rows = [
        {"publish": "2026-01-01T06:00:00Z"},
        {"publish": "2026-01-01T08:00:00Z"},
        {"publish": None},
        {"publish": "2026-01-01T07:00:00Z"},
    ]
    assert a.latest_publish(rows) == "2026-01-01T08:00:00Z"


def test_latest_publish_all_none():
    """latest_publish should return None if no rows have a publish time."""
    rows = [{"publish": None}, {"publish": None}]
    assert a.latest_publish(rows) is None


# --------------- New tests: January decision → February delivery ---------------

def test_january_decision_feb_1_delivery():
    """Decision on Jan 31 should create delivery for Feb 1."""
    days = a.delivery_dates(date(2026, 1, 1), date(2026, 1, 31))
    assert date(2026, 2, 1) in days


def test_cutoff_for_feb_1_delivery():
    """Cutoff for Feb 1 delivery is Jan 31 09:00 UK = 09:00 UTC (winter)."""
    cutoff = a.cutoff_utc(date(2026, 2, 1), "09:00")
    assert cutoff == datetime(2026, 1, 31, 9, 0, tzinfo=UTC)


# --------------- New tests: parse_ts ---------------

def test_parse_ts_with_z_suffix():
    ts = a.parse_ts("2026-01-15T12:00:00Z")
    assert ts == datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)


def test_parse_ts_with_offset():
    ts = a.parse_ts("2026-01-15T12:00:00+00:00")
    assert ts == datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)


def test_parse_ts_naive_treated_as_utc():
    ts = a.parse_ts("2026-01-15T12:00:00")
    assert ts.tzinfo is not None
    assert ts == datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
