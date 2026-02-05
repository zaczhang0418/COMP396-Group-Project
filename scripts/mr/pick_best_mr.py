# -*- coding: utf-8 -*-
# scripts/mr/pick_best_mr.py
import argparse, json, subprocess, sys
from pathlib import Path
from datetime import date

PROJ = Path(__file__).resolve().parents[2]
OUT_ROOT = PROJ / "output" / "part1" / "asset10" / "mr_core4_v1"
RESULTS = OUT_ROOT / "results.csv"
BEST_OUT = OUT_ROOT / "best_params.json"
SPLITS = json.loads((PROJ/"configs"/"splits_asset10.json").read_text(encoding="utf-8"))
RUN_ONCE = PROJ / "scripts" / "mr" / "run_mr_once.py"

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

def run_split(which: str, tag: str, params_path: Path):
    which = which.lower()
    if which == "is":   start, end, split = SPLITS["is_start"], SPLITS["is_end"], "70-30"
    elif which == "oos":  start, end, split = SPLITS["oos_start"], SPLITS["full_end"], "30-oos"
    elif which == "full": start, end, split = SPLITS["full_start"], SPLITS["full_end"], "100-full"
    else: raise ValueError(f"unknown run split: {which}")

    cmd = [sys.executable, str(RUN_ONCE),
           "--start", start, "--end", end,
           "--params", str(params_path), "--split", split, "--tag", tag]
    print(f"[RUN] {which.upper()}  {start} -> {end}")
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default="true_pd_ratio")
    ap.add_argument("--tag", default=f"{date.today():%Y%m%d}_best")
    ap.add_argument("--runs", default="is,oos,full")
    args = ap.parse_args()

    if not RESULTS.exists(): raise SystemExit(f"Not found: {RESULTS}")
    header, rows = parse_results(RESULTS)
    if args.key not in header: raise SystemExit(f"Metric '{args.key}' missing")

    best = max(rows, key=lambda r: r.get(args.key, float("-inf")))
    best_params = {k: best[k] for k in PARAM_KEYS}
    BEST_OUT.write_text(json.dumps(best_params, indent=2), encoding="utf-8")
    print(f"[BEST] {args.key}={best[args.key]:.6g}  params={best_params}\n[SAVE] {BEST_OUT}")

    runs = sorted({x.strip().lower() for x in args.runs.split(",") if x.strip()},
                  key=lambda x: {"is":0, "oos":1, "full":2}.get(x, 99))
    for which in runs: run_split(which, args.tag, BEST_OUT)
    print("[DONE]")