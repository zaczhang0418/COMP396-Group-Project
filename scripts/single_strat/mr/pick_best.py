# -*- coding: utf-8 -*-
# scripts/single_strat/mr/pick_best.py
import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[3]
if str(PROJ) not in sys.path:
    sys.path.insert(0, str(PROJ))

from scripts.common_paths import get_stage_dir, load_timeline  # noqa: E402
from scripts.single_strat.common.pick_best_common import (  # noqa: E402
    load_grid_spec,
    parse_results,
    pick_metric_best,
    resolve_path,
    robust_select,
)

RUN_ONCE = PROJ / "scripts" / "single_strat" / "mr" / "run_once.py"
DEFAULT_EXPERIMENT_TAG = "adhoc"
DEFAULT_GRID_CONFIG = PROJ / "configs" / "grids" / "single_strat" / "mr" / "refined" / "refined_v1.json"


def run_split(which: str, tag: str, params_path: Path, output_root: Path, timeline: dict):
    which = which.lower()
    if which == "is":
        start, end, split = timeline["is"]["start"], timeline["is"]["end"], "70-30"
    elif which == "oos":
        start, end, split = timeline["oos"]["start"], timeline["oos"]["end"], "30-oos"
    elif which == "full":
        start, end, split = timeline["full"]["start"], timeline["full"]["end"], "100-full"
    else:
        raise ValueError(f"unknown run split: {which}")

    cmd = [
        sys.executable,
        str(RUN_ONCE),
        "--start",
        start,
        "--end",
        end,
        "--params",
        str(params_path),
        "--split",
        split,
        "--tag",
        tag,
        "--data-dir",
        str(PROJ / "DATA" / "PART1"),
        "--output-root",
        str(output_root),
    ]
    print(f"[RUN] {which.upper()}  {start} -> {end}")
    subprocess.run(cmd, check=True, cwd=str(PROJ))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment-tag", default=DEFAULT_EXPERIMENT_TAG)
    ap.add_argument("--grid-config", default=str(DEFAULT_GRID_CONFIG))
    ap.add_argument("--key", default="true_pd_ratio")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--runs", default="is,oos,full")
    ap.add_argument("--min-activity", type=float, default=0.0)
    ap.add_argument("--selection-mode", choices=["metric", "robust"], default="robust")
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--oos-weight", type=float, default=0.60)
    ap.add_argument("--full-weight", type=float, default=0.30)
    ap.add_argument("--is-weight", type=float, default=0.10)
    ap.add_argument("--gap-penalty", type=float, default=0.25)
    ap.add_argument("--bankrupt-penalty", type=float, default=5.0)
    args = ap.parse_args()

    timeline = load_timeline()["part1"]
    search_keys, fixed_params = load_grid_spec(resolve_path(args.grid_config))
    out_root = get_stage_dir(args.experiment_tag, "part1", "mr", "grid_search")
    results = out_root / "results.csv"
    best_out = out_root / "best_params.json"
    best_runs_root = get_stage_dir(args.experiment_tag, "part1", "mr", "best_runs")
    run_tag = args.tag or args.experiment_tag

    if not results.exists():
        raise SystemExit(f"Not found: {results}")
    header, rows = parse_results(results)
    if args.key not in header:
        raise SystemExit(f"Metric '{args.key}' missing")
    if args.min_activity > 0 and "activity_pct" in header:
        rows = [row for row in rows if row.get("activity_pct", 0.0) >= float(args.min_activity)]
        if not rows:
            raise SystemExit("No rows left after filtering")

    missing = [key for key in search_keys if key not in header]
    if missing:
        raise SystemExit(f"Missing search params in results: {missing}")

    if args.selection_mode == "robust":
        robust_dir = out_root / "robust_selection"
        robust = robust_select(
            rows=rows,
            key=args.key,
            top_k=args.top_k,
            search_keys=search_keys,
            fixed_params=fixed_params,
            out_root=out_root,
            best_out=best_out,
            robust_dir=robust_dir,
            runner=RUN_ONCE,
            timeline=timeline,
            data_dir=PROJ / "DATA" / "PART1",
            experiment_tag=args.experiment_tag,
            strategy_key="mr",
            oos_weight=args.oos_weight,
            full_weight=args.full_weight,
            is_weight=args.is_weight,
            gap_penalty=args.gap_penalty,
            bankrupt_penalty=args.bankrupt_penalty,
        )
        best_params = robust["best_params"]
        best_record = robust["best_record"]
        print(
            f"[BEST-ROBUST] score={best_record['robust_score']:.6g} "
            f"(IS={best_record['is_metric']:.6g}, OOS={best_record['oos_metric']:.6g}, FULL={best_record['full_metric']:.6g}) "
            f"params={best_params}\n[SAVE] {best_out}\n[RANKING] {robust['ranking_path']}"
        )
    else:
        best = pick_metric_best(rows, args.key)
        best_params = {key: best[key] for key in search_keys}
        best_params.update(fixed_params)
        best_out.write_text(json.dumps(best_params, indent=2), encoding="utf-8")
        print(f"[BEST] {args.key}={best[args.key]:.6g}  params={best_params}\n[SAVE] {best_out}")

    runs = sorted(
        {item.strip().lower() for item in args.runs.split(",") if item.strip()},
        key=lambda item: {"is": 0, "oos": 1, "full": 2}.get(item, 99),
    )
    for which in runs:
        run_split(which, run_tag, best_out, best_runs_root, timeline)
    print("[DONE]")
