from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def default_data_dir(part_label: str) -> Path:
    return PROJECT_ROOT / "DATA" / part_label.upper()


def default_output_root(part_label: str) -> Path:
    return PROJECT_ROOT / "output" / part_label.lower()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def detect_csv_date_range(csv_path: Path) -> tuple[str, str]:
    min_dt = None
    max_dt = None
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {csv_path}")

        date_key = None
        for field in reader.fieldnames:
            low = field.strip().lower()
            if low in {"date", "datetime", "timestamp", "time", "index", "unnamed: 0"}:
                date_key = field
                break
        if date_key is None:
            raise ValueError(f"Could not find date column in {csv_path}")

        for row in reader:
            raw = (row.get(date_key) or "").strip()
            if not raw:
                continue
            dt = datetime.fromisoformat(raw)
            if min_dt is None or dt < min_dt:
                min_dt = dt
            if max_dt is None or dt > max_dt:
                max_dt = dt

    if min_dt is None or max_dt is None:
        raise ValueError(f"No usable dates found in {csv_path}")

    return min_dt.date().isoformat(), max_dt.date().isoformat()


def detect_overlap_range(data_dir: Path, asset_ids: list[str]) -> tuple[str, str]:
    starts = []
    ends = []
    for asset_id in asset_ids:
        start, end = detect_csv_date_range(data_dir / f"{asset_id}.csv")
        starts.append(start)
        ends.append(end)
    return max(starts), min(ends)
