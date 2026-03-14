#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared helpers for cross-asset scan scripts."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


PROJ = Path(__file__).resolve().parents[2]
if str(PROJ) not in sys.path:
    sys.path.insert(0, str(PROJ))

from scripts.common_paths import PART_DATA_DIRS, load_timeline, rel_path  # noqa: E402


DEFAULT_SCAN_TAG = "cross_asset_scan_v1"
ALL_STRATEGIES = ("tf", "mr", "garch")
ALL_ASSETS = tuple(f"{idx:02d}" for idx in range(1, 11))
SPLIT_LABELS = {"is": "70-30", "oos": "30-oos", "full": "100-full"}

STRATEGY_CONFIG = {
    "tf": {
        "strategy_id": "tf_generic_v1",
        "grid_config": PROJ / "configs" / "grids" / "single_strat" / "tf" / "refined" / "refined_v1.json",
        "grid_search_runner": PROJ / "scripts" / "single_strat" / "tf" / "run_grid_search.py",
        "run_once_runner": PROJ / "scripts" / "single_strat" / "tf" / "run_once.py",
    },
    "mr": {
        "strategy_id": "mr_generic_v1",
        "grid_config": PROJ / "configs" / "grids" / "single_strat" / "mr" / "refined" / "refined_v1.json",
        "grid_search_runner": PROJ / "scripts" / "single_strat" / "mr" / "run_grid_search.py",
        "run_once_runner": PROJ / "scripts" / "single_strat" / "mr" / "run_once.py",
    },
    "garch": {
        "strategy_id": "garch_generic_v1",
        "grid_config": PROJ / "configs" / "grids" / "single_strat" / "garch" / "refined" / "refined_v1.json",
        "grid_search_runner": PROJ / "scripts" / "single_strat" / "garch" / "run_grid_search.py",
        "run_once_runner": PROJ / "scripts" / "single_strat" / "garch" / "run_once.py",
    },
}


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(path: Path, default=None):
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_cmd(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, cwd=str(PROJ))


def to_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def pct_return(final_value, starting_cash: float = 1_000_000.0) -> float:
    return (to_float(final_value) / starting_cash - 1.0) * 100.0


def normalize_asset_code(raw: str) -> str:
    token = str(raw).strip().lower().replace("asset", "")
    if not token:
        raise ValueError("empty asset token")
    value = int(token)
    if value < 1 or value > 10:
        raise ValueError(f"asset out of range: {raw}")
    return f"{value:02d}"


def parse_assets(raw: str) -> list[str]:
    token = (raw or "").strip().lower()
    if token in ("", "all", "*"):
        return list(ALL_ASSETS)
    items = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            left, right = [normalize_asset_code(x) for x in part.split("-", 1)]
            start = int(left)
            end = int(right)
            step = 1 if start <= end else -1
            items.extend(f"{idx:02d}" for idx in range(start, end + step, step))
        else:
            items.append(normalize_asset_code(part))
    seen = set()
    ordered = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def parse_strategies(raw: str) -> list[str]:
    token = (raw or "").strip().lower()
    if token in ("", "all", "*"):
        return list(ALL_STRATEGIES)
    items = []
    for part in raw.split(","):
        key = part.strip().lower()
        if not key:
            continue
        if key not in STRATEGY_CONFIG:
            raise ValueError(f"unknown strategy: {key}")
        if key not in items:
            items.append(key)
    return items


def asset_tag(asset_code: str) -> str:
    return f"asset{normalize_asset_code(asset_code)}"


def data_name(asset_code: str) -> str:
    return f"series_{int(normalize_asset_code(asset_code))}"


def scan_root(scan_tag: str) -> Path:
    return ensure_dir(PROJ / "output" / scan_tag)


def strategy_root(scan_tag: str, strategy_key: str) -> Path:
    return ensure_dir(scan_root(scan_tag) / strategy_key)


def strategy_asset_root(scan_tag: str, strategy_key: str, asset_code: str) -> Path:
    return ensure_dir(strategy_root(scan_tag, strategy_key) / asset_tag(asset_code))


def summaries_root(scan_tag: str) -> Path:
    return ensure_dir(scan_root(scan_tag) / "summaries")


def latest_child_dir(root: Path, pattern: str) -> Path | None:
    if not root.exists():
        return None
    candidates = sorted(root.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def latest_summary_for_split(best_runs_root: Path, split_name: str) -> tuple[Path | None, dict]:
    run_dir = latest_child_dir(best_runs_root, f"run_*_{SPLIT_LABELS[split_name]}")
    return run_dir, load_json(run_dir / "run_summary.json", {}) if run_dir else {}


def part2_summary(asset_root: Path) -> tuple[Path | None, dict]:
    run_dir = latest_child_dir(asset_root / "part2_validation", "run_*_100-full")
    return run_dir, load_json(run_dir / "run_summary.json", {}) if run_dir else {}


def serialize_path(path: Path | None) -> str:
    return rel_path(path) if path else ""

