# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# scripts/garch/pick_best_garch.py
import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
if str(PROJ) not in sys.path:
    sys.path.insert(0, str(PROJ))

from scripts.common_paths import get_stage_dir, load_timeline  # noqa: E402

RUN_ONCE = PROJ / "scripts" / "garch" / "run_garch_once.py"
DEFAULT_EXPERIMENT_TAG = "adhoc"
DEFAULT_GRID_CONFIG = PROJ / "configs" / "grids" / "garch_refined_v1.json"


def resolve_path(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else PROJ / path


def to_float(x):
    try:
        return float(x)
    except Exception:
        return 0.0


def load_grid_spec(path: Path) -> tuple[list[str], dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "search_params" in payload:
        search_keys = list(payload["search_params"].keys())
        fixed_params = payload.get("fixed_params", {})
    else:
        search_keys = list(payload.keys())
        fixed_params = {}
    return search_keys, fixed_params


def parse_results(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = [h.strip() for h in (reader.fieldnames or [])]
        rows = []
        for row in reader:
            if not row:
                continue
            parsed = {key.strip(): to_float(value) for key, value in row.items() if key}
            rows.append(parsed)
    if not header or not rows:
        raise SystemExit(f"Empty results: {path}")
    return header, rows


def run_split(which: str, tag: str, params_path: Path, output_root: Path, timeline: dict):
    if which == "is":
        start, end, split = timeline["is"]["start"], timeline["is"]["end"], "70-30"
    elif which == "oos":
        start, end, split = timeline["oos"]["start"], timeline["oos"]["end"], "30-oos"
    elif which == "full":
        start, end, split = timeline["full"]["start"], timeline["full"]["end"], "100-full"
    else:
        raise ValueError(which)

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
    ap.add_argument("--runs", default="is,oos,full")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--min-activity", type=float, default=0.0)
    args = ap.parse_args()

    timeline = load_timeline()["part1"]
    search_keys, fixed_params = load_grid_spec(resolve_path(args.grid_config))
    out_root = get_stage_dir(args.experiment_tag, "part1", "garch", "grid_search")
    results = out_root / "results.csv"
    best_out = out_root / "best_params.json"
    best_runs_root = get_stage_dir(args.experiment_tag, "part1", "garch", "best_runs")
    run_tag = args.tag or args.experiment_tag

    if not results.exists():
        raise SystemExit(f"Not found: {results}")
    header, rows = parse_results(results)
    if args.key not in header:
        raise SystemExit(f"Key {args.key} missing")
    if args.min_activity > 0 and "activity_pct" in header:
        rows = [row for row in rows if row.get("activity_pct", 0.0) >= float(args.min_activity)]
        if not rows:
            raise SystemExit("No rows left after filtering")

    missing = [key for key in search_keys if key not in header]
    if missing:
        raise SystemExit(f"Missing search params in results: {missing}")

    best = max(rows, key=lambda row: row.get(args.key, float("-inf")))
    best_params = {key: best[key] for key in search_keys}
    best_params.update(fixed_params)
    best_out.write_text(json.dumps(best_params, indent=2), encoding="utf-8")
    print(f"[BEST] {args.key}={best.get(args.key):.6g}  params={best_params}\n[SAVE] {best_out}")

    runs = sorted(
        {item.strip().lower() for item in args.runs.split(",") if item.strip()},
        key=lambda item: {"is": 0, "oos": 1, "full": 2}.get(item, 99),
    )
    for run_name in runs:
        run_split(run_name, run_tag, best_out, best_runs_root, timeline)
    print("[DONE]")
