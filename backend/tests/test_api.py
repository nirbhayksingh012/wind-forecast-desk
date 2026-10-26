"""Integration and end-to-end tests for the FastAPI API endpoints."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_meta_endpoint():
    res = client.get("/api/meta")
    assert res.status_code == 200
    data = res.json()
    assert "delivery_dates" in data
    assert len(data["delivery_dates"]) == 31
    assert data["delivery_dates"][0] == "2026-01-02"
    assert data["delivery_dates"][-1] == "2026-02-01"
    assert data["default_cutoff"] == "09:00"
    assert "09:00" in data["cutoff_options"]
    assert data["timezone"] == "Europe/London"


def test_forecast_endpoint_valid():
    res = client.get("/api/forecast?delivery_date=2026-01-15&cutoff=09:00")
    assert res.status_code == 200
    data = res.json()
    assert data["delivery_date"] == "2026-01-15"
    assert data["cutoff"] == "09:00"
    assert "cutoff_utc" in data
    assert "latest_publish" in data
    assert "slots" in data
    assert len(data["slots"]) == 48
    assert "summary" in data
    assert "coverage" in data
    assert data["coverage"]["total_hh_slots"] == 48
    assert data["coverage"]["hourly_slots"] == 24
    assert data["coverage"]["with_forecast"] == 24
    assert data["coverage"]["matched"] == 24


def test_forecast_endpoint_invalid_date():
    # Outside analysis window
    res = client.get("/api/forecast?delivery_date=2025-12-31&cutoff=09:00")
    assert res.status_code == 400
    assert "outside the analysis window" in res.json()["detail"]


def test_forecast_endpoint_invalid_cutoff():
    res = client.get("/api/forecast?delivery_date=2026-01-15&cutoff=25:99")
    assert res.status_code == 422


def test_accuracy_endpoint():
    res = client.get("/api/accuracy?cutoff=09:00")
    assert res.status_code == 200
    data = res.json()
    assert "overall" in data
    assert "coverage" in data
    assert "by_day" in data
    assert "by_hour" in data
    assert "by_horizon" in data

    overall = data["overall"]
    assert overall["n"] == 744
    assert round(overall["mae"], 1) == 2022.5
    assert round(overall["rmse"], 1) == 2497.4
    assert round(overall["bias"], 1) == 1745.9
    assert round(overall["nmae_pct"], 2) == 17.92

    coverage = data["coverage"]
    assert coverage["total_hh_slots"] == 1488
    assert coverage["hourly_slots"] == 744
    assert coverage["matched"] == 744
    assert coverage["forecast_coverage_pct"] == 100.0


def test_cutoff_sensitivity_endpoint():
    res = client.get("/api/cutoff-sensitivity")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    cutoffs = [item["cutoff"] for item in data]
    assert "09:00" in cutoffs
    # Later cutoff should generally have equal or better (lower) MAE than 06:00
    mae_map = {item["cutoff"]: item["mae"] for item in data}
    assert mae_map["12:00"] <= mae_map["06:00"]


def test_spa_serving():
    res = client.get("/")
    assert res.status_code == 200
    assert "<!doctype html>" in res.text.lower() or "<html" in res.text.lower()


def test_cors_headers():
    # Allowed origin gets access-control-allow-origin header
    res = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"

    # Disallowed external origin does NOT get access-control-allow-origin header
    res_disallowed = client.get("/api/health", headers={"Origin": "http://evil-site.com"})
    assert res_disallowed.status_code == 200
    assert res_disallowed.headers.get("access-control-allow-origin") is None

