# -*- coding: utf-8 -*-
# scripts/mr/pick_best_mr.py
import argparse, json, subprocess, sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
if str(PROJ) not in sys.path:
    sys.path.insert(0, str(PROJ))

from scripts.common_paths import get_stage_dir  # noqa: E402

TIMELINE = json.loads((PROJ / "configs" / "timeline.json").read_text(encoding="utf-8"))
PART1 = TIMELINE["part1"]
RUN_ONCE = PROJ / "scripts" / "mr" / "run_mr_once.py"
DEFAULT_EXPERIMENT_TAG = "adhoc"

PARAM_KEYS = ["p_lookback","p_entry_z","p_exit_z","p_stop_mult"]

def parse_results(path: Path):
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    if not lines: raise SystemExit(f"empty results: {path}")
    header = lines[0].split(",")
    rows = [dict(zip(header, l.split(","))) for l in lines[1:]]

    def to_float(x):
        try: return float(x)
        except: return 0.0

    for r in rows:
        for k in r:
            if k in PARAM_KEYS:
                try: r[k] = int(r[k]) if r[k].isdigit() else float(r[k])
                except: pass
            else: r[k] = to_float(r[k])
    return header, rows

def run_split(which: str, tag: str, params_path: Path, output_root: Path):
    which = which.lower()
    if which == "is":   start, end, split = PART1["is"]["start"], PART1["is"]["end"], "70-30"
    elif which == "oos":  start, end, split = PART1["oos"]["start"], PART1["oos"]["end"], "30-oos"
    elif which == "full": start, end, split = PART1["full"]["start"], PART1["full"]["end"], "100-full"
    else: raise ValueError(f"unknown run split: {which}")

    cmd = [sys.executable, str(RUN_ONCE),
           "--start", start, "--end", end,
           "--params", str(params_path), "--split", split, "--tag", tag,
           "--data-dir", str(PROJ / "DATA" / "PART1"),
           "--output-root", str(output_root)]
    print(f"[RUN] {which.upper()}  {start} -> {end}")
    subprocess.run(cmd, check=True, cwd=str(PROJ))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment-tag", default=DEFAULT_EXPERIMENT_TAG)
    ap.add_argument("--key", default="true_pd_ratio")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--runs", default="is,oos,full")
    args = ap.parse_args()

    out_root = get_stage_dir(args.experiment_tag, "part1", "mr", "grid_search")
    results = out_root / "results.csv"
    best_out = out_root / "best_params.json"
    best_runs_root = get_stage_dir(args.experiment_tag, "part1", "mr", "best_runs")
    run_tag = args.tag or args.experiment_tag

    if not results.exists(): raise SystemExit(f"Not found: {results}")
    header, rows = parse_results(results)
    if args.key not in header: raise SystemExit(f"Metric '{args.key}' missing")

    best = max(rows, key=lambda r: r.get(args.key, float("-inf")))
    best_params = {k: best[k] for k in PARAM_KEYS}
    best_out.write_text(json.dumps(best_params, indent=2), encoding="utf-8")
    print(f"[BEST] {args.key}={best[args.key]:.6g}  params={best_params}\n[SAVE] {best_out}")

    runs = sorted({x.strip().lower() for x in args.runs.split(",") if x.strip()},
                  key=lambda x: {"is":0, "oos":1, "full":2}.get(x, 99))
    for which in runs: run_split(which, run_tag, best_out, best_runs_root)
    print("[DONE]")
