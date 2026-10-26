"""SYNTHETIC data generator - for tests and offline UI development ONLY.

It mimics the shape of FUELHH/WINDFOR (a smooth wind series; hourly-published
forecasts whose noise grows with horizon) but it is NOT real Elexon data. The
snapshot is tagged source="synthetic" and the UI shows a warning banner.

Usage (from backend/):  DATA_PATH=/tmp/synthetic.json.gz python -m app.synthetic
"""
import math
import random
from datetime import datetime, timedelta, timezone

from .config import DATA_PATH
from .store import save_snapshot

UTC = timezone.utc
iso = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")


def generate(seed: int = 7):
    rng = random.Random(seed)
    t0 = datetime(2025, 12, 29, tzinfo=UTC)
    n = 36 * 48
    truth, x = {}, 0.0
    for i in range(n):
        x = 0.985 * x + rng.gauss(0, 0.12)
        level = 8500 + 5500 * math.tanh(x) + 1500 * math.sin(i / 48 * 2 * math.pi / 3)
        truth[t0 + timedelta(minutes=30 * i)] = max(300.0, level)

    actuals = [(iso(t), round(g + rng.gauss(0, 60), 1)) for t, g in truth.items()]
    forecasts = []
    pub = datetime(2025, 12, 30, tzinfo=UTC)
    while pub < datetime(2026, 2, 1, tzinfo=UTC):
        for k in range(1, 97):  # up to 48h ahead, half-hourly
            start = pub + timedelta(minutes=30 * k)
            if start in truth:
                horizon = k / 2
                forecasts.append((iso(start), iso(pub),
                                  round(max(0.0, truth[start] + rng.gauss(0, 250 + 55 * horizon)), 1)))
        pub += timedelta(hours=1)
    return actuals, forecasts


if __name__ == "__main__":
    a, f = generate()
    save_snapshot(DATA_PATH, [list(x) for x in a], [list(x) for x in f], "synthetic")
    print(f"Wrote SYNTHETIC snapshot to {DATA_PATH} ({len(a)} actuals, {len(f)} forecasts)")
