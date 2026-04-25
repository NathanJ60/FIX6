"""Historique persistant des puzzles FIX-6 generes."""
import os
import json
import hashlib
import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = DATA_DIR / "fix6_history.json"


def _flat(grid):
    return "".join(str(cell) if cell is not None else "_" for row in grid for cell in row)


def puzzle_hash(solution, yellows):
    s = _flat(solution) + "|" + "".join("1" if y else "0" for row in yellows for y in row)
    return hashlib.sha256(s.encode()).hexdigest()


def get_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def is_unique(solution, yellows):
    return puzzle_hash(solution, yellows) not in get_history()


def add_to_history(solution, yellows, metadata=None):
    h = get_history()
    h[puzzle_hash(solution, yellows)] = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "metadata": metadata or {},
    }
    with open(HISTORY_FILE, "w") as f:
        json.dump(h, f, indent=2)
