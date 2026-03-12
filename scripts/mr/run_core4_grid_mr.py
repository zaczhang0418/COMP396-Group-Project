# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# scripts/mr/run_core4_grid_mr.py
import argparse
import itertools
import json
import subprocess
import sys
import time
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
if str(PROJ) not in sys.path:
    sys.path.insert(0, str(PROJ))

from scripts.common_paths import get_stage_dir, load_timeline  # noqa: E402

MAIN = PROJ / "main.py"
DATA_DIR = PROJ / "DATA" / "PART1"
DEFAULT_GRID_CONFIG = PROJ / "configs" / "grids" / "mr_refined_v1.json"
DEFAULT_EXPERIMENT_TAG = "adhoc"
STRATEGY = "mr_asset10_v1"
DATA_NAME = "series_10"
METRIC_KEYS = ["true_pd_ratio", "open_pnl_pd_ratio", "activity_pct", "final_value", "bankrupt"]


def resolve_path(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else PROJ / path


def load_grid_spec(path: Path) -> tuple[dict, dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "search_params" in payload:
        search_params = payload["search_params"]
        fixed_params = payload.get("fixed_params", {})
    else:
        search_params = payload
        fixed_params = {}
    if not search_params:
        raise SystemExit(f"Empty search_params in {path}")
    overlap = set(search_params).intersection(fixed_params)
    if overlap:
        raise SystemExit(f"Duplicate search/fixed params in {path}: {sorted(overlap)}")
    return search_params, fixed_params


def write_meta(run_dir: Path, search_params: dict, fixed_params: dict, grid_config: Path, timeline: dict):
    meta = {
        "strategy_id": STRATEGY,
        "asset_tag": "asset10",
        "data_name": DATA_NAME,
        "split": "IS(70%)",
        "fromdate": timeline["is"]["start"],
        "todate": timeline["is"]["end"],
        "search_params": search_params,
        "fixed_params": fixed_params,
        "grid_config": str(grid_config.relative_to(PROJ)),
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def run_one(search_params: dict, fixed_params: dict, run_dir: Path, timeline: dict, grid_config: Path):
    run_dir.mkdir(parents=True, exist_ok=True)
    param_args = ["--param", f"data_name={DATA_NAME}"]
    merged = {**fixed_params, **search_params}
    for key, value in merged.items():
        param_args += ["--param", f"{key}={value}"]

    cmd = [
        sys.executable,
        str(MAIN),
        "--strategy",
        STRATEGY,
        "--data-dir",
        str(DATA_DIR),
        "--fromdate",
        timeline["is"]["start"],
        "--todate",
        timeline["is"]["end"],
        "--output-dir",
        str(run_dir),
        "--no-plot",
        *param_args,
    ]
    subprocess.run(cmd, check=True, cwd=str(PROJ))

    summary = json.loads((run_dir / "run_summary.json").read_text(encoding="utf-8"))
    metrics = {
        "true_pd_ratio": float(summary.get("true_pd_ratio", 0.0) or 0.0),
        "open_pnl_pd_ratio": float(summary.get("open_pnl_pd_ratio", 0.0) or 0.0),
        "activity_pct": float(summary.get("activity_pct", 0.0) or 0.0),
        "final_value": float(summary.get("final_value", 0.0) or 0.0),
        "bankrupt": int(bool(summary.get("bankrupt", False))),
    }
    write_meta(run_dir, search_params, fixed_params, grid_config, timeline)
    return metrics


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment-tag", default=DEFAULT_EXPERIMENT_TAG)
    ap.add_argument("--grid-config", default=str(DEFAULT_GRID_CONFIG))
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    timeline = load_timeline()["part1"]
    grid_config = resolve_path(args.grid_config)
    search_space, fixed_params = load_grid_spec(grid_config)
    search_keys = list(search_space.keys())
    fixed_keys = list(fixed_params.keys())

    out_root = get_stage_dir(args.experiment_tag, "part1", "mr", "grid_search")
    csv_out = out_root / "results.csv"
    if csv_out.exists():
        csv_out.rename(out_root / f"results_{time.strftime('%Y%m%d_%H%M%S')}.csv")

    header = ["run_dir"] + search_keys + fixed_keys + METRIC_KEYS
    csv_out.write_text(",".join(header) + "\n", encoding="utf-8")

    combos = list(itertools.product(*[search_space[key] for key in search_keys]))
    if args.limit > 0:
        combos = combos[: args.limit]
    total = len(combos)

    for i, combo in enumerate(combos, 1):
        search_params = {key: value for key, value in zip(search_keys, combo)}
        run_name = f"run_{time.strftime('%Y%m%d')}_IS_{i:03d}"
        run_dir = out_root / run_name

        try:
            metrics = run_one(search_params, fixed_params, run_dir, timeline, grid_config)
        except Exception as exc:
            print(f"[{i}/{total}] FAIL -> {run_dir} ({exc})")
            metrics = {
                "true_pd_ratio": 0.0,
                "open_pnl_pd_ratio": 0.0,
                "activity_pct": 0.0,
                "final_value": 0.0,
                "bankrupt": 0,
            }

        row = (
            [run_name]
            + [str(search_params[key]) for key in search_keys]
            + [str(fixed_params[key]) for key in fixed_keys]
            + [str(metrics[key]) for key in METRIC_KEYS]
        )
        with csv_out.open("a", encoding="utf-8") as handle:
            handle.write(",".join(row) + "\n")
        print(f"[{i}/{total}] OK -> {run_dir}")
