# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Run part1 combo using best params from part1 single-strategy searches."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJ = Path(__file__).resolve().parents[2]
if str(PROJ) not in sys.path:
    sys.path.insert(0, str(PROJ))

from scripts.common_paths import (  # noqa: E402
    PART_DATA_DIRS,
    get_stage_dir,
    load_json,
    load_timeline,
    rel_path,
    update_experiment_record,
)


COMBO_RUNNER = PROJ / "scripts" / "combo" / "run_combo_once.py"


def latest_child_dir(root: Path, pattern: str) -> Path:
    candidates = sorted(root.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No matches for {pattern} under {root}")
    return candidates[0]


def run_part1_combo(start: str, end: str, experiment_tag: str, cash: float, weights: dict) -> dict:
    combo_root = get_stage_dir(experiment_tag, "part1", "combo", "combo")
    cmd = [
        sys.executable,
        str(COMBO_RUNNER),
        "--start",
        start,
        "--end",
        end,
        "--split",
        "100-full",
        "--tag",
        experiment_tag,
        "--experiment-tag",
        experiment_tag,
        "--data-dir",
        str(PART_DATA_DIRS["part1"]),
        "--output-root",
        str(combo_root),
        "--cash",
        str(cash),
        "--w-tf",
        str(weights["tf"]),
        "--w-mr",
        str(weights["mr"]),
        "--w-ga",
        str(weights["garch"]),
        "--meta-tf-dir",
        str(get_stage_dir(experiment_tag, "part1", "tf", "grid_search", create=False)),
        "--meta-mr-dir",
        str(get_stage_dir(experiment_tag, "part1", "mr", "grid_search", create=False)),
        "--meta-ga-dir",
        str(get_stage_dir(experiment_tag, "part1", "garch", "grid_search", create=False)),
    ]
    subprocess.run(cmd, check=True, cwd=str(PROJ))

    run_dir = latest_child_dir(combo_root, "combined_*")
    summary = load_json(run_dir / "run_summary.json", {})
    update_experiment_record(
        experiment_tag,
        {
            "experiment_tag": experiment_tag,
            "timeline_config": rel_path(PROJ / "configs" / "timeline.json"),
            "part1": {
                "combo": {
                    "combo_dir": rel_path(combo_root),
                }
            },
        },
    )
    return {
        "run_dir": rel_path(run_dir),
        "true_pd_ratio": summary.get("true_pd_ratio"),
        "open_pnl_pd_ratio": summary.get("open_pnl_pd_ratio"),
        "activity_pct": summary.get("activity_pct"),
        "final_value": summary.get("final_value"),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment-tag", default="adhoc")
    ap.add_argument("--cash", type=float, default=1_000_000.0)
    ap.add_argument("--w-tf", type=float, default=0.45)
    ap.add_argument("--w-mr", type=float, default=0.45)
    ap.add_argument("--w-garch", type=float, default=0.10)
    args = ap.parse_args()

    timeline = load_timeline()
    start = timeline["part1"]["full"]["start"]
    end = timeline["part1"]["full"]["end"]
    result = run_part1_combo(
        start,
        end,
        args.experiment_tag,
        args.cash,
        {"tf": args.w_tf, "mr": args.w_mr, "garch": args.w_garch},
    )
    print(result)
