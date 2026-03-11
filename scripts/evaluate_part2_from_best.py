# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Run part2 transfer tests from part1 best params under an experiment layout."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path


PROJ = Path(__file__).resolve().parents[1]
if str(PROJ) not in sys.path:
    sys.path.insert(0, str(PROJ))

from scripts.common_paths import (  # noqa: E402
    PART_DATA_DIRS,
    STRATEGY_LAYOUT,
    part_root,
    get_stage_dir,
    load_json,
    load_timeline,
    rel_path,
    update_experiment_record,
    write_json,
)


RUNNERS = {
    "tf": PROJ / "scripts" / "tf" / "run_tf_once.py",
    "mr": PROJ / "scripts" / "mr" / "run_mr_once.py",
    "garch": PROJ / "scripts" / "garch" / "run_garch_once.py",
}
COMBO_RUNNER = PROJ / "scripts" / "combo" / "run_combo_once.py"


def latest_child_dir(root: Path, pattern: str) -> Path:
    candidates = sorted(root.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No matches for {pattern} under {root}")
    return candidates[0]


def run_single_transfer(strategy_key: str, start: str, end: str, experiment_tag: str) -> dict:
    params_dir = get_stage_dir(experiment_tag, "part1", strategy_key, "grid_search", create=False)
    params_path = params_dir / "best_params.json"
    if not params_path.exists():
        raise FileNotFoundError(f"Missing best params: {params_path}")

    output_root = get_stage_dir(experiment_tag, "part2", strategy_key, "transfer_runs")
    cmd = [
        sys.executable,
        str(RUNNERS[strategy_key]),
        "--start",
        start,
        "--end",
        end,
        "--params",
        str(params_path),
        "--split",
        "100-full",
        "--tag",
        experiment_tag,
        "--data-dir",
        str(PART_DATA_DIRS["part2"]),
        "--output-root",
        str(output_root),
    ]
    subprocess.run(cmd, check=True, cwd=str(PROJ))

    run_dir = latest_child_dir(output_root, "run_*_100-full")
    summary = load_json(run_dir / "run_summary.json", {})
    layout = STRATEGY_LAYOUT[strategy_key]
    return {
        "strategy": strategy_key,
        "asset": layout["asset"],
        "source_part": "part1",
        "target_part": "part2",
        "experiment_tag": experiment_tag,
        "split": "100-full",
        "fromdate": start,
        "todate": end,
        "true_pd_ratio": summary.get("true_pd_ratio"),
        "open_pnl_pd_ratio": summary.get("open_pnl_pd_ratio"),
        "activity_pct": summary.get("activity_pct"),
        "final_value": summary.get("final_value"),
        "bankrupt": summary.get("bankrupt"),
        "best_params_path": rel_path(params_path),
        "run_dir": rel_path(run_dir),
    }


def run_combo_transfer(start: str, end: str, experiment_tag: str, cash: float, weights: dict) -> dict:
    combo_root = get_stage_dir(experiment_tag, "part2", "combo", "combo")
    cmd = [
        sys.executable,
        str(COMBO_RUNNER),
        "--start",
        start,
        "--end",
        end,
        "--tag",
        experiment_tag,
        "--data-dir",
        str(PART_DATA_DIRS["part2"]),
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
    return {
        "strategy": "combo",
        "asset": "01+07+10",
        "source_part": "part1",
        "target_part": "part2",
        "experiment_tag": experiment_tag,
        "split": "100-full",
        "fromdate": start,
        "todate": end,
        "true_pd_ratio": summary.get("true_pd_ratio"),
        "open_pnl_pd_ratio": summary.get("open_pnl_pd_ratio"),
        "activity_pct": summary.get("activity_pct"),
        "final_value": summary.get("final_value"),
        "bankrupt": summary.get("bankrupt"),
        "best_params_path": "",
        "run_dir": rel_path(run_dir),
    }


def write_summary_csv(path: Path, rows: list[dict]):
    fieldnames = [
        "strategy",
        "asset",
        "source_part",
        "target_part",
        "experiment_tag",
        "split",
        "fromdate",
        "todate",
        "true_pd_ratio",
        "open_pnl_pd_ratio",
        "activity_pct",
        "final_value",
        "bankrupt",
        "best_params_path",
        "run_dir",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment-tag", default="adhoc")
    ap.add_argument("--cash", type=float, default=1_000_000.0)
    ap.add_argument("--w-tf", type=float, default=0.45)
    ap.add_argument("--w-mr", type=float, default=0.45)
    ap.add_argument("--w-garch", type=float, default=0.10)
    args = ap.parse_args()

    timeline = load_timeline()
    start = timeline["part2"]["full"]["start"]
    end = timeline["part2"]["full"]["end"]
    weights = {"tf": args.w_tf, "mr": args.w_mr, "garch": args.w_garch}

    rows = [
        run_single_transfer("tf", start, end, args.experiment_tag),
        run_single_transfer("mr", start, end, args.experiment_tag),
        run_single_transfer("garch", start, end, args.experiment_tag),
        run_combo_transfer(start, end, args.experiment_tag, args.cash, weights),
    ]

    transfer_root = part_root(args.experiment_tag, "part2", create=False)
    summary_path = transfer_root / "transfer_summary.csv"
    record_path = transfer_root / "transfer_record.json"

    write_summary_csv(summary_path, rows)
    write_json(
        record_path,
        {
            "experiment_tag": args.experiment_tag,
            "source_part": "part1",
            "target_part": "part2",
            "timeline": {"start": start, "end": end},
            "cash": args.cash,
            "weights": weights,
            "rows": rows,
        },
    )

    update_experiment_record(
        args.experiment_tag,
        {
            "experiment_tag": args.experiment_tag,
            "timeline_config": rel_path(PROJ / "configs" / "timeline.json"),
            "part2": {
                "transfer_summary": rel_path(summary_path),
                "transfer_record": rel_path(record_path),
                "strategies": {
                    "tf": {
                        "grid_search_dir": rel_path(get_stage_dir(args.experiment_tag, "part1", "tf", "grid_search", create=False)),
                        "transfer_runs_dir": rel_path(get_stage_dir(args.experiment_tag, "part2", "tf", "transfer_runs", create=False)),
                    },
                    "mr": {
                        "grid_search_dir": rel_path(get_stage_dir(args.experiment_tag, "part1", "mr", "grid_search", create=False)),
                        "transfer_runs_dir": rel_path(get_stage_dir(args.experiment_tag, "part2", "mr", "transfer_runs", create=False)),
                    },
                    "garch": {
                        "grid_search_dir": rel_path(get_stage_dir(args.experiment_tag, "part1", "garch", "grid_search", create=False)),
                        "transfer_runs_dir": rel_path(get_stage_dir(args.experiment_tag, "part2", "garch", "transfer_runs", create=False)),
                    },
                },
                "combo": {
                    "combo_dir": rel_path(get_stage_dir(args.experiment_tag, "part2", "combo", "combo", create=False)),
                },
            },
        },
    )
