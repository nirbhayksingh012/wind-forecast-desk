"""Central configuration. Everything an analyst might want to change lives here."""
import os
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

LONDON = ZoneInfo("Europe/London")

# Purchase decisions in this window (inclusive). A decision made on day D-1
# is for delivery on day D, so delivery days run 2 Jan .. 1 Feb 2026.
DECISION_START = date(2026, 1, 1)
DECISION_END = date(2026, 1, 31)

# Day-ahead auction gate closure is mid/late morning UK time on D-1
# (EPEX ~09:20, N2EX ~09:50). We default to 09:00 so the forecast the buyer
# is looking at was surely published before they must bid. Adjustable in the UI.
DEFAULT_CUTOFF = "09:00"
CUTOFF_OPTIONS = ["06:00", "08:00", "09:00", "10:00", "12:00"]

ELEXON_BASE = "https://data.elexon.co.uk/bmrs/api/v1"

_backend_dir = Path(__file__).resolve().parent.parent
_candidate_data = _backend_dir / "data" / "snapshot.json.gz"
if not _candidate_data.exists():
    for _fb in [
        Path("backend/data/snapshot.json.gz"),
        Path("data/snapshot.json.gz"),
        Path("/var/task/backend/data/snapshot.json.gz"),
    ]:
        if _fb.exists():
            _candidate_data = _fb
            break

DATA_PATH = Path(os.getenv("DATA_PATH", str(_candidate_data)))
STATIC_DIR = Path(os.getenv("STATIC_DIR", str(_backend_dir.parent / "frontend" / "dist")))
