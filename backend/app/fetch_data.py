"""Download January-2026 data from Elexon into backend/data/snapshot.json.gz.

Run from the backend/ directory:   python -m app.fetch_data
"""
from .config import DATA_PATH
from .store import fetch_live_and_save

if __name__ == "__main__":
    print("Fetching FUELHH (WIND) and WINDFOR from Elexon ...")
    fetch_live_and_save(DATA_PATH)
    print(f"Saved {DATA_PATH}")
