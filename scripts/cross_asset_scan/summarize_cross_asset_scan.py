#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize cross-asset scan outputs into long tables and a 3x10 matrix."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJ = Path(__file__).resolve().parents[2]
if str(PROJ) not in sys.path:
    sys.path.insert(0, str(PROJ))

from scripts.cross_asset_scan.common import (  # noqa: E402
    DEFAULT_SCAN_TAG,
    PART_DATA_DIRS,
    asset_tag,
    load_json,
    parse_assets,
    parse_strategies,
    part2_summary,
    pct_return,
    serialize_path,
    strategy_asset_root,
    summaries_root,
    to_float,
    write_csv,
    write_json,
)


def selection_score(row: dict, bankrupt_penalty: float) -> float:
    return (
        1.0 * to_float(row.get("oos_true_pd_ratio"))
        + 0.35 * to_float(row.get("full_true_pd_ratio"))
        + 0.02 * to_float(row.get("full_return_pct"))
        - bankrupt_penalty
        * (
            int(bool(row.get("oos_bankrupt", False)))
            + int(bool(row.get("full_bankrupt", False)))
        )
    )


def build_row(scan_tag: str, strategy_key: str, asset_code: str) -> dict | None:
    asset_root = strategy_asset_root(scan_tag, strategy_key, asset_code)
    record_path = asset_root / "asset_scan_record.json"
    if not record_path.exists():
        return None

    record = load_json(record_path, {})
    splits = record.get("splits", {})
    is_summary = splits.get("is", {}).get("run_summary", {})
    oos_summary = splits.get("oos", {}).get("run_summary", {})
    full_summary = splits.get("full", {}).get("run_summary", {})
    part2_run_dir, part2_run_summary = part2_summary(asset_root)

    return {
        "scan_tag": scan_tag,
        "strategy": strategy_key,
        "asset": asset_code,
        "asset_tag": asset_tag(asset_code),
        "data_name": record.get("data_name", ""),
        "selection_mode": record.get("selection_mode", ""),
        "metric_key": record.get("metric_key", ""),
        "grid_config": record.get("grid_config", ""),
        "best_params_path": record.get("best_params_path", ""),
        "robust_ranking_path": record.get("robust_ranking_path", ""),
        "grid_search_dir": record.get("grid_search_dir", ""),
        "best_runs_dir": record.get("best_runs_dir", ""),
        "is_run_dir": splits.get("is", {}).get("run_dir", ""),
        "is_true_pd_ratio": is_summary.get("true_pd_ratio"),
        "is_open_pnl_pd_ratio": is_summary.get("open_pnl_pd_ratio"),
        "is_activity_pct": is_summary.get("activity_pct"),
        "is_final_value": is_summary.get("final_value"),
        "is_return_pct": pct_return(is_summary.get("final_value")),
        "is_bankrupt": is_summary.get("bankrupt"),
        "oos_run_dir": splits.get("oos", {}).get("run_dir", ""),
        "oos_true_pd_ratio": oos_summary.get("true_pd_ratio"),
        "oos_open_pnl_pd_ratio": oos_summary.get("open_pnl_pd_ratio"),
        "oos_activity_pct": oos_summary.get("activity_pct"),
        "oos_final_value": oos_summary.get("final_value"),
        "oos_return_pct": pct_return(oos_summary.get("final_value")),
        "oos_bankrupt": oos_summary.get("bankrupt"),
        "full_run_dir": splits.get("full", {}).get("run_dir", ""),
        "full_true_pd_ratio": full_summary.get("true_pd_ratio"),
        "full_open_pnl_pd_ratio": full_summary.get("open_pnl_pd_ratio"),
        "full_activity_pct": full_summary.get("activity_pct"),
        "full_final_value": full_summary.get("final_value"),
        "full_return_pct": pct_return(full_summary.get("final_value")),
        "full_bankrupt": full_summary.get("bankrupt"),
        "is_oos_gap": abs(to_float(is_summary.get("true_pd_ratio")) - to_float(oos_summary.get("true_pd_ratio"))),
        "part2_data_dir": serialize_path(PART_DATA_DIRS["part2"]),
        "part2_run_dir": serialize_path(part2_run_dir),
        "part2_true_pd_ratio": part2_run_summary.get("true_pd_ratio"),
        "part2_open_pnl_pd_ratio": part2_run_summary.get("open_pnl_pd_ratio"),
        "part2_activity_pct": part2_run_summary.get("activity_pct"),
        "part2_final_value": part2_run_summary.get("final_value"),
        "part2_return_pct": pct_return(part2_run_summary.get("final_value")) if part2_run_summary else None,
        "part2_bankrupt": part2_run_summary.get("bankrupt"),
    }


def build_matrix(rows: list[dict], value_key: str, strategies: list[str], assets: list[str]) -> list[dict]:
    matrix_rows = []
    for strategy_key in strategies:
        row = {"strategy": strategy_key}
        lookup = {(item["strategy"], item["asset"]): item for item in rows}
        for asset_code in assets:
            item = lookup.get((strategy_key, asset_code), {})
            row[asset_tag(asset_code)] = item.get(value_key)
        matrix_rows.append(row)
    return matrix_rows


def build_assignment(rows: list[dict], assets: list[str], bankrupt_penalty: float) -> list[dict]:
    output = []
    for asset_code in assets:
        candidates = [row for row in rows if row["asset"] == asset_code]
        if not candidates:
            continue
        ranked = sorted(
            candidates,
            key=lambda row: (selection_score(row, bankrupt_penalty), to_float(row.get("oos_true_pd_ratio"))),
            reverse=True,
        )
        winner = ranked[0]
        runner_up = ranked[1] if len(ranked) > 1 else {}
        output.append(
            {
                "asset": asset_code,
                "asset_tag": asset_tag(asset_code),
                "winner_strategy": winner["strategy"],
                "winner_score": selection_score(winner, bankrupt_penalty),
                "winner_oos_true_pd_ratio": winner.get("oos_true_pd_ratio"),
                "winner_full_true_pd_ratio": winner.get("full_true_pd_ratio"),
                "winner_full_return_pct": winner.get("full_return_pct"),
                "winner_part2_true_pd_ratio": winner.get("part2_true_pd_ratio"),
                "runner_up_strategy": runner_up.get("strategy", ""),
                "runner_up_score": selection_score(runner_up, bankrupt_penalty) if runner_up else "",
                "runner_up_oos_true_pd_ratio": runner_up.get("oos_true_pd_ratio", ""),
                "runner_up_part2_true_pd_ratio": runner_up.get("part2_true_pd_ratio", ""),
            }
        )
    return output


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan-tag", default=DEFAULT_SCAN_TAG)
    ap.add_argument("--strategies", default="all")
    ap.add_argument("--assets", default="all")
    ap.add_argument("--matrix-metric", default="oos_true_pd_ratio")
    ap.add_argument("--bankrupt-penalty", type=float, default=5.0)
    args = ap.parse_args()

    strategies = parse_strategies(args.strategies)
    assets = parse_assets(args.assets)
    rows = []
    for strategy_key in strategies:
        for asset_code in assets:
            row = build_row(args.scan_tag, strategy_key, asset_code)
            if row:
                rows.append(row)

    if not rows:
        raise SystemExit(f"No cross-asset scan records found under output/{args.scan_tag}")

    rows.sort(key=lambda item: (item["strategy"], item["asset"]))
    summary_dir = summaries_root(args.scan_tag)
    long_path = summary_dir / "cross_asset_long.csv"
    matrix_path = summary_dir / "matrix_3x10.csv"
    assignment_path = summary_dir / "asset_strategy_assignment.csv"
    summary_json_path = summary_dir / "summary.json"

    write_csv(long_path, list(rows[0].keys()), rows)
    matrix_rows = build_matrix(rows, args.matrix_metric, strategies, assets)
    write_csv(matrix_path, list(matrix_rows[0].keys()), matrix_rows)
    assignment_rows = build_assignment(rows, assets, args.bankrupt_penalty)
    write_csv(assignment_path, list(assignment_rows[0].keys()), assignment_rows)

    win_counts = {}
    for item in assignment_rows:
        win_counts[item["winner_strategy"]] = win_counts.get(item["winner_strategy"], 0) + 1

    write_json(
        summary_json_path,
        {
            "scan_tag": args.scan_tag,
            "matrix_metric": args.matrix_metric,
            "strategies": strategies,
            "assets": assets,
            "records": len(rows),
            "winner_counts": win_counts,
            "paths": {
                "cross_asset_long": serialize_path(long_path),
                "matrix_3x10": serialize_path(matrix_path),
                "asset_strategy_assignment": serialize_path(assignment_path),
            },
        },
    )
    print({"long": serialize_path(long_path), "matrix": serialize_path(matrix_path), "assignment": serialize_path(assignment_path)})


if __name__ == "__main__":
    main()
