# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# scripts/tf/pick_best_tf.py
import argparse, json, subprocess, sys, csv
from pathlib import Path

PROJ     = Path(__file__).resolve().parents[2]
if str(PROJ) not in sys.path:
    sys.path.insert(0, str(PROJ))

from scripts.common_paths import get_stage_dir  # noqa: E402

TIMELINE = json.loads((PROJ / "configs" / "timeline.json").read_text(encoding="utf-8"))
PART1    = TIMELINE["part1"]
RUN_ONCE = PROJ / "scripts" / "tf" / "run_tf_once.py"
DEFAULT_EXPERIMENT_TAG = "adhoc"

BASE_KEYS = ["p_ema_short", "p_ema_long", "p_hurst_min_soft"]

def to_float(x):
    try: return float(x)
    except: return 0.0

def parse_results(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = [h.strip() for h in (reader.fieldnames or [])]
        rows = []
        for r in reader:
            if not r: continue
            rr = {k.strip(): to_float(v) for k, v in r.items() if k}
            rows.append(rr)
    if not header or not rows: raise SystemExit(f"Empty results: {path}")
    return header, rows

def run_split(which: str, tag: str, params_path: Path, output_root: Path):
    if   which == "is":   start, end, split = PART1["is"]["start"],   PART1["is"]["end"],   "70-30"
    elif which == "oos":  start, end, split = PART1["oos"]["start"],  PART1["oos"]["end"],  "30-oos"
    elif which == "full": start, end, split = PART1["full"]["start"], PART1["full"]["end"], "100-full"
    else: raise ValueError(which)

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
    ap.add_argument("--runs", default="is,oos,full")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--min-activity", type=float, default=0.0)
    args = ap.parse_args()

    out_root = get_stage_dir(args.experiment_tag, "part1", "tf", "grid_search")
    results = out_root / "results.csv"
    best_out = out_root / "best_params.json"
    best_runs_root = get_stage_dir(args.experiment_tag, "part1", "tf", "best_runs")
    run_tag = args.tag or args.experiment_tag

    if not results.exists(): raise SystemExit(f"Not found: {results}")
    header, rows = parse_results(results)

    if "p_stop_multiplier" in header: STOP_KEY = "p_stop_multiplier"
    elif "p_stop_mult" in header:     STOP_KEY = "p_stop_mult"
    else: raise SystemExit("Missing p_stop_multiplier")

    if args.min_activity > 0 and "activity_pct" in header:
        rows = [r for r in rows if r.get("activity_pct", 0.0) >= float(args.min_activity)]
        if not rows: raise SystemExit("No rows left after filtering")

    if args.key not in header: raise SystemExit(f"Key {args.key} not in header")

    best = max(rows, key=lambda r: r.get(args.key, float("-inf")))
    best_params = {k: best[k] for k in BASE_KEYS if k in best}
    best_params["p_stop_multiplier"] = float(best.get(STOP_KEY, 0.0))
    best_out.write_text(json.dumps(best_params, indent=2), encoding="utf-8")
    print(f"[BEST] {args.key}={best.get(args.key):.6g}  params={best_params}\n[SAVE] {best_out}")

    order = {"is": 0, "oos": 1, "full": 2}
    runs = sorted({x.strip().lower() for x in args.runs.split(",") if x.strip()},
                  key=lambda x: order.get(x, 99))
    for r in runs: run_split(r, run_tag, best_out, best_runs_root)
    print("[DONE]")
