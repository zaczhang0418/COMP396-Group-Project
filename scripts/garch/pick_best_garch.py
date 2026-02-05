# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# scripts/garch/pick_best_garch.py
import argparse, json, subprocess, sys, csv
from pathlib import Path
from datetime import date

PROJ     = Path(__file__).resolve().parents[2]
OUT_ROOT = PROJ / "output" / "part1" / "asset07" / "garch_core4_v1"
RESULTS  = OUT_ROOT / "results.csv"
BEST_OUT = OUT_ROOT / "best_params.json"
SPLITS   = json.loads((PROJ / "configs" / "splits_asset07.json").read_text(encoding="utf-8"))
RUN_ONCE = PROJ / "scripts" / "garch" / "run_garch_once.py"

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

def run_split(which: str, tag: str, params_path: Path):
    if   which == "is":   start, end, split = SPLITS["is_start"],  SPLITS["is_end"],   "70-30"
    elif which == "oos":  start, end, split = SPLITS["oos_start"], SPLITS["full_end"], "30-oos"
    elif which == "full": start, end, split = SPLITS["full_start"], SPLITS["full_end"], "100-full"
    else: raise ValueError(which)

    cmd = [sys.executable, str(RUN_ONCE),
           "--start", start, "--end", end,
           "--params", str(params_path), "--split", split, "--tag", tag]
    print(f"[RUN] {which.upper()}  {start} -> {end}")
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default="true_pd_ratio")
    ap.add_argument("--runs", default="is,oos,full")
    ap.add_argument("--tag",  default=f"{date.today():%Y%m%d}_best")
    args = ap.parse_args()

    if not RESULTS.exists(): raise SystemExit(f"Not found: {RESULTS}")
    header, rows = parse_results(RESULTS)

    PARAM_COLS = [h for h in header if h.startswith("p_")]
    if not PARAM_COLS: raise SystemExit("No p_ columns")
    if args.key not in header: raise SystemExit(f"Key {args.key} missing")

    best = max(rows, key=lambda r: r.get(args.key, float("-inf")))
    best_params = {k: best[k] for k in PARAM_COLS if k in best}
    BEST_OUT.write_text(json.dumps(best_params, indent=2), encoding="utf-8")
    print(f"[BEST] {args.key}={best.get(args.key):.6g}  params={best_params}\n[SAVE] {BEST_OUT}")

    runs = sorted({x.strip().lower() for x in args.runs.split(",") if x.strip()},
                  key=lambda x: {"is":0, "oos":1, "full":2}.get(x, 99))
    for r in runs: run_split(r, args.tag, BEST_OUT)
    print("[DONE]")