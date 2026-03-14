#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run part2 OOS validation for cross-asset scan best params."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJ = Path(__file__).resolve().parents[2]
if str(PROJ) not in sys.path:
    sys.path.insert(0, str(PROJ))

from scripts.cross_asset_scan.common import (  # noqa: E402
    DEFAULT_SCAN_TAG,
    PART_DATA_DIRS,
    STRATEGY_CONFIG,
    asset_tag,
    data_name,
    latest_child_dir,
    load_timeline,
    parse_assets,
    parse_strategies,
    pct_return,
    run_cmd,
    serialize_path,
    strategy_asset_root,
    summaries_root,
    write_csv,
)

FIELDNAMES = [
    "strategy",
    "asset",
    "asset_tag",
    "part2_run_dir",
    "part2_true_pd_ratio",
    "part2_open_pnl_pd_ratio",
    "part2_activity_pct",
    "part2_final_value",
    "part2_return_pct",
    "part2_bankrupt",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan-tag", default=DEFAULT_SCAN_TAG)
    ap.add_argument("--strategies", default="all")
    ap.add_argument("--assets", default="all")
    ap.add_argument("--skip-existing", action="store_true")
    args = ap.parse_args()

    strategies = parse_strategies(args.strategies)
    assets = parse_assets(args.assets)
    timeline = load_timeline()["part2"]["full"]
    rows = []

    for strategy_key in strategies:
        cfg = STRATEGY_CONFIG[strategy_key]
        for asset_code in assets:
            asset_root = strategy_asset_root(args.scan_tag, strategy_key, asset_code)
            params_path = asset_root / "grid_search" / "best_params.json"
            output_root = asset_root / "part2_validation"
            if not params_path.exists():
                print(f"[SKIP] missing params for {strategy_key} {asset_tag(asset_code)}", flush=True)
                continue

            existing_run = latest_child_dir(output_root, "run_*_100-full")
            if args.skip_existing and existing_run is not None:
                summary_path = existing_run / "run_summary.json"
                summary = {}
                if summary_path.exists():
                    summary = json.loads(summary_path.read_text(encoding="utf-8"))
                rows.append(
                    {
                        "strategy": strategy_key,
                        "asset": asset_code,
                        "asset_tag": asset_tag(asset_code),
                        "part2_run_dir": serialize_path(existing_run),
                        "part2_true_pd_ratio": summary.get("true_pd_ratio"),
                        "part2_open_pnl_pd_ratio": summary.get("open_pnl_pd_ratio"),
                        "part2_activity_pct": summary.get("activity_pct"),
                        "part2_final_value": summary.get("final_value"),
                        "part2_return_pct": pct_return(summary.get("final_value")),
                        "part2_bankrupt": summary.get("bankrupt"),
                    }
                )
                continue

            cmd = [
                sys.executable,
                str(cfg["run_once_runner"]),
                "--start",
                timeline["start"],
                "--end",
                timeline["end"],
                "--params",
                str(params_path),
                "--split",
                "100-full",
                "--tag",
                args.scan_tag,
                "--data-dir",
                str(PART_DATA_DIRS["part2"]),
                "--output-root",
                str(output_root),
                "--strategy-id",
                cfg["strategy_id"],
                "--data-name",
                data_name(asset_code),
                "--asset-tag",
                asset_tag(asset_code),
            ]
            run_cmd(cmd)

            run_dir = latest_child_dir(output_root, "run_*_100-full")
            if run_dir is None:
                raise FileNotFoundError(f"No part2 run found under {output_root}")
            summary = json.loads((run_dir / "run_summary.json").read_text(encoding="utf-8"))
            rows.append(
                {
                    "strategy": strategy_key,
                    "asset": asset_code,
                    "asset_tag": asset_tag(asset_code),
                    "part2_run_dir": serialize_path(run_dir),
                    "part2_true_pd_ratio": summary.get("true_pd_ratio"),
                    "part2_open_pnl_pd_ratio": summary.get("open_pnl_pd_ratio"),
                    "part2_activity_pct": summary.get("activity_pct"),
                    "part2_final_value": summary.get("final_value"),
                    "part2_return_pct": pct_return(summary.get("final_value")),
                    "part2_bankrupt": summary.get("bankrupt"),
                }
            )

    out_path = summaries_root(args.scan_tag) / "part2_validation.csv"
    write_csv(out_path, FIELDNAMES, rows)
    print({"part2_validation": serialize_path(out_path)})


if __name__ == "__main__":
    main()
