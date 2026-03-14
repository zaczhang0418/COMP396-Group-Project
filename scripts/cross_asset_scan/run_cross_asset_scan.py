#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run part1 cross-asset scans for all requested strategy/asset pairs."""

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
    SPLIT_LABELS,
    STRATEGY_CONFIG,
    asset_tag,
    data_name,
    latest_summary_for_split,
    load_json,
    load_timeline,
    parse_assets,
    parse_strategies,
    pct_return,
    run_cmd,
    serialize_path,
    strategy_asset_root,
    to_float,
    write_json,
)
from scripts.single_strat.common.pick_best_common import (  # noqa: E402
    load_grid_spec,
    parse_results,
    pick_metric_best,
    resolve_path,
    robust_select,
)


def run_best_split(
    *,
    runner: Path,
    start: str,
    end: str,
    split_name: str,
    params_path: Path,
    output_root: Path,
    tag: str,
    strategy_id: str,
    data_name_value: str,
    asset_tag_value: str,
    data_dir: Path,
) -> None:
    cmd = [
        sys.executable,
        str(runner),
        "--start",
        start,
        "--end",
        end,
        "--params",
        str(params_path),
        "--split",
        SPLIT_LABELS[split_name],
        "--tag",
        tag,
        "--data-dir",
        str(data_dir),
        "--output-root",
        str(output_root),
        "--strategy-id",
        strategy_id,
        "--data-name",
        data_name_value,
        "--asset-tag",
        asset_tag_value,
    ]
    run_cmd(cmd)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan-tag", default=DEFAULT_SCAN_TAG)
    ap.add_argument("--strategies", default="all")
    ap.add_argument("--assets", default="all")
    ap.add_argument("--grid-limit", type=int, default=0)
    ap.add_argument("--key", default="true_pd_ratio")
    ap.add_argument("--selection-mode", choices=["metric", "robust"], default="robust")
    ap.add_argument("--min-activity", type=float, default=0.0)
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--oos-weight", type=float, default=0.60)
    ap.add_argument("--full-weight", type=float, default=0.30)
    ap.add_argument("--is-weight", type=float, default=0.10)
    ap.add_argument("--gap-penalty", type=float, default=0.25)
    ap.add_argument("--bankrupt-penalty", type=float, default=5.0)
    ap.add_argument("--runs", default="is,oos,full")
    ap.add_argument("--skip-existing", action="store_true")
    ap.add_argument("--tf-grid-config", default=None)
    ap.add_argument("--mr-grid-config", default=None)
    ap.add_argument("--garch-grid-config", default=None)
    return ap


def main() -> None:
    args = build_parser().parse_args()
    strategies = parse_strategies(args.strategies)
    assets = parse_assets(args.assets)
    timeline = load_timeline()["part1"]
    run_order = sorted(
        {item.strip().lower() for item in args.runs.split(",") if item.strip()},
        key=lambda item: {"is": 0, "oos": 1, "full": 2}.get(item, 99),
    )

    total = len(strategies) * len(assets)
    current = 0
    summary_rows = []

    grid_override_map = {
        "tf": args.tf_grid_config,
        "mr": args.mr_grid_config,
        "garch": args.garch_grid_config,
    }

    for strategy_key in strategies:
        cfg = STRATEGY_CONFIG[strategy_key]
        grid_config = resolve_path(grid_override_map[strategy_key] or str(cfg["grid_config"]))
        search_keys, fixed_params = load_grid_spec(grid_config)

        for asset_code in assets:
            current += 1
            asset_root = strategy_asset_root(args.scan_tag, strategy_key, asset_code)
            grid_root = asset_root / "grid_search"
            best_runs_root = asset_root / "best_runs"
            record_path = asset_root / "asset_scan_record.json"
            data_name_value = data_name(asset_code)
            asset_tag_value = asset_tag(asset_code)

            print(
                f"[{current}/{total}] {strategy_key.upper()} {asset_tag_value} "
                f"-> {serialize_path(asset_root)}",
                flush=True,
            )

            if args.skip_existing and record_path.exists():
                print(f"  [SKIP] existing record: {serialize_path(record_path)}", flush=True)
                summary_rows.append(load_json(record_path, {}))
                continue

            grid_cmd = [
                sys.executable,
                str(cfg["grid_search_runner"]),
                "--experiment-tag",
                args.scan_tag,
                "--grid-config",
                str(grid_config),
                "--limit",
                str(args.grid_limit),
                "--strategy-id",
                cfg["strategy_id"],
                "--data-name",
                data_name_value,
                "--asset-tag",
                asset_tag_value,
                "--output-root",
                str(grid_root),
            ]
            run_cmd(grid_cmd)

            results_path = grid_root / "results.csv"
            if not results_path.exists():
                raise FileNotFoundError(f"Missing grid-search results: {results_path}")

            header, rows = parse_results(results_path)
            if args.key not in header:
                raise SystemExit(f"Metric '{args.key}' missing from {results_path}")
            if args.min_activity > 0 and "activity_pct" in header:
                rows = [row for row in rows if row.get("activity_pct", 0.0) >= float(args.min_activity)]
                if not rows:
                    raise SystemExit(f"No rows left after activity filter: {results_path}")

            best_params_path = grid_root / "best_params.json"
            robust_ranking_path = None
            best_record = {}
            if args.selection_mode == "robust":
                robust = robust_select(
                    rows=rows,
                    key=args.key,
                    top_k=args.top_k,
                    search_keys=search_keys,
                    fixed_params=fixed_params,
                    out_root=grid_root,
                    best_out=best_params_path,
                    robust_dir=grid_root / "robust_selection",
                    runner=cfg["run_once_runner"],
                    timeline=timeline,
                    data_dir=PART_DATA_DIRS["part1"],
                    experiment_tag=args.scan_tag,
                    strategy_key=f"{strategy_key}_{asset_tag_value}",
                    oos_weight=args.oos_weight,
                    full_weight=args.full_weight,
                    is_weight=args.is_weight,
                    gap_penalty=args.gap_penalty,
                    bankrupt_penalty=args.bankrupt_penalty,
                    strategy_id=cfg["strategy_id"],
                    data_name=data_name_value,
                    asset_tag=asset_tag_value,
                )
                robust_ranking_path = robust["ranking_path"]
                best_record = robust["best_record"]
            else:
                best = pick_metric_best(rows, args.key)
                best_params = {key: best[key] for key in search_keys}
                best_params.update(fixed_params)
                best_params_path.write_text(json.dumps(best_params, indent=2), encoding="utf-8")
                best_record = {
                    "metric_key": args.key,
                    "metric_value": to_float(best.get(args.key)),
                    **{key: best.get(key) for key in search_keys},
                }

            for split_name in run_order:
                run_best_split(
                    runner=cfg["run_once_runner"],
                    start=timeline[split_name]["start"],
                    end=timeline[split_name]["end"],
                    split_name=split_name,
                    params_path=best_params_path,
                    output_root=best_runs_root,
                    tag=args.scan_tag,
                    strategy_id=cfg["strategy_id"],
                    data_name_value=data_name_value,
                    asset_tag_value=asset_tag_value,
                    data_dir=PART_DATA_DIRS["part1"],
                )

            split_payload = {}
            for split_name in ("is", "oos", "full"):
                run_dir, run_summary = latest_summary_for_split(best_runs_root, split_name)
                split_payload[split_name] = {
                    "run_dir": serialize_path(run_dir),
                    "run_summary": run_summary,
                    "return_pct": pct_return(run_summary.get("final_value")),
                }

            record = {
                "scan_tag": args.scan_tag,
                "strategy": strategy_key,
                "asset": asset_code,
                "asset_tag": asset_tag_value,
                "data_name": data_name_value,
                "selection_mode": args.selection_mode,
                "metric_key": args.key,
                "grid_config": serialize_path(grid_config),
                "grid_search_dir": serialize_path(grid_root),
                "best_runs_dir": serialize_path(best_runs_root),
                "best_params_path": serialize_path(best_params_path),
                "robust_ranking_path": serialize_path(robust_ranking_path),
                "best_record": best_record,
                "splits": split_payload,
            }
            write_json(record_path, record)
            summary_rows.append(record)

    summary_path = Path(PROJ / "output" / args.scan_tag / "summaries" / "scan_overview.json")
    write_json(
        summary_path,
        {
            "scan_tag": args.scan_tag,
            "strategies": strategies,
            "assets": assets,
            "records": summary_rows,
        },
    )
    print(f"[DONE] {serialize_path(summary_path)}", flush=True)


if __name__ == "__main__":
    main()
