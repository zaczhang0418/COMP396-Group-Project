# -*- coding: utf-8 -*-
"""Shared output path helpers for experiment runs."""

from __future__ import annotations

import json
from pathlib import Path


PROJ = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJ / "output"
EXPERIMENTS_ROOT = OUTPUT_ROOT / "experiments"
TIMELINE_PATH = PROJ / "configs" / "timeline.json"

PART_DATA_DIRS = {
    "part1": PROJ / "DATA" / "PART1",
    "part2": PROJ / "DATA" / "PART2",
}

STRATEGY_LAYOUT = {
    "tf": {
        "asset": "01",
        "asset_dir": "asset01",
        "strategy_id": "tf_generic_v1",
        "data_name": "series_1",
    },
    "mr": {
        "asset": "10",
        "asset_dir": "asset10",
        "strategy_id": "mr_generic_v1",
        "data_name": "series_10",
    },
    "garch": {
        "asset": "07",
        "asset_dir": "asset07",
        "strategy_id": "garch_generic_v1",
        "data_name": "series_7",
    },
}


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(path: Path, default=None):
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict):
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_timeline() -> dict:
    return load_json(TIMELINE_PATH, {})


def experiment_root(experiment_tag: str, create: bool = True) -> Path:
    path = EXPERIMENTS_ROOT / experiment_tag
    return ensure_dir(path) if create else path


def part_root(experiment_tag: str, part: str, create: bool = True) -> Path:
    path = experiment_root(experiment_tag, create=create) / part
    return ensure_dir(path) if create else path


def combo_root(experiment_tag: str, part: str, create: bool = True) -> Path:
    path = part_root(experiment_tag, part, create=create) / "combo"
    return ensure_dir(path) if create else path


def get_stage_dir(
    experiment_tag: str,
    part: str,
    strategy_key: str,
    stage: str,
    create: bool = True,
) -> Path:
    if strategy_key == "combo":
        path = combo_root(experiment_tag, part, create=create)
    else:
        base = part_root(experiment_tag, part, create=create)
        asset_dir = STRATEGY_LAYOUT[strategy_key]["asset_dir"]
        path = base / strategy_key / asset_dir / stage
    return ensure_dir(path) if create else path


def experiment_record_path(experiment_tag: str) -> Path:
    return experiment_root(experiment_tag) / "experiment_record.json"


def rel_path(path: Path | str) -> str:
    path = Path(path).resolve()
    try:
        rel = path.relative_to(PROJ.resolve())
        return str(rel).replace("/", "\\")
    except ValueError:
        return str(path)


def _merge_dicts(base: dict, patch: dict) -> dict:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def update_experiment_record(experiment_tag: str, patch: dict):
    path = experiment_record_path(experiment_tag)
    current = load_json(path, default={})
    merged = _merge_dicts(current, patch)
    write_json(path, merged)
