# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# pick_best_and_run_oos_full_tf.py
# Select best TF params from results.csv, write best_params.json, and run IS/OOS/FULL.

import argparse, json, subprocess, sys, csv
from pathlib import Path

PROJ     = Path(__file__).resolve().parents[1]
OUT_ROOT = PROJ / "output" / "asset01" / "tf_core4_v1"
RESULTS  = OUT_ROOT / "results.csv"
BEST_OUT = OUT_ROOT / "best_params.json"
SPLITS   = json.loads((PROJ / "configs" / "splits_asset01.json").read_text(encoding="utf-8"))
RUN_ONCE = PROJ / "scripts" / "run_tf_once.py"   # change if your path is different

# keep these keys consistent with your TF grid columns
BASE_KEYS = ["p_ema_short", "p_ema_long", "p_hurst_min_soft"]

def to_float(x):
    s = "" if x is None else str(x).strip()
    if s == "" or s.lower() in {"nan", "none"}:
        return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0

def parse_results(path: Path):
    # robust CSV reader (handles UTF-8 BOM and empty lines)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = [h.strip() for h in (reader.fieldnames or [])]
        rows = []
        for r in reader:
            if not r:
                continue
            rr = {}
            for k, v in r.items():
                if k is None:
                    continue
                k = k.strip()
                rr[k] = to_float(v)
            rows.append(rr)
    if not header or not rows:
        raise SystemExit(f"Empty or invalid results: {path}")
    return header, rows

def run_split(which: str, tag: str, params_path: Path):
    if   which == "is":
        start, end, split = SPLITS["is_start"],  SPLITS["is_end"],   "70-30"
    elif which == "oos":
        start, end, split = SPLITS["oos_start"], SPLITS["full_end"], "30-oos"
    elif which == "full":
        start, end, split = SPLITS["full_start"], SPLITS["full_end"], "100-full"
    else:
        raise ValueError(f"unknown split: {which}")

    cmd = [sys.executable, str(RUN_ONCE),
           "--start", start, "--end", end,
           "--params", str(params_path), "--split", split, "--tag", tag]
    print(f"[RUN] {which.upper()}  {start} -> {end}")
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Pick best TF params from results.csv and run IS/OOS/FULL.")
    ap.add_argument("--key", default="true_pd_ratio", help="metric column used for selection")
    ap.add_argument("--runs", default="is,oos,full", help="comma-separated: any of is,oos,full")
    ap.add_argument("--tag",  default="v1_best_core4", help="tag for output run folders")
    ap.add_argument("--min-activity", type=float, default=0.0, help="min activity_pct filter; 0 means no filter")
    args = ap.parse_args()

    if not RESULTS.exists():
        raise SystemExit(f"results.csv not found: {RESULTS}")

    header, rows = parse_results(RESULTS)

    # stop key compatibility
    if   "p_stop_multiplier" in header:
        STOP_KEY = "p_stop_multiplier"
    elif "p_stop_mult" in header:
        STOP_KEY = "p_stop_mult"
    else:
        raise SystemExit("results.csv must contain p_stop_multiplier or p_stop_mult")

    # optional activity filter (only if the column exists)
    if args.min_activity > 0 and "activity_pct" in header:
        rows = [r for r in rows if r.get("activity_pct", 0.0) >= float(args.min_activity)]
        if not rows:
            raise SystemExit("No rows left after filtering; lower --min-activity or relax the grid.")

    if args.key not in header:
        raise SystemExit(f"selection key '{args.key}' not in columns: {header}")

    best = max(rows, key=lambda r: r.get(args.key, float("-inf")))

    # write best_params.json (normalize stop key name)
    best_params = {k: best[k] for k in BASE_KEYS if k in best}
    best_params["p_stop_multiplier"] = float(best.get(STOP_KEY, 0.0))
    BEST_OUT.write_text(json.dumps(best_params, indent=2), encoding="utf-8")
    print(f"[BEST] {args.key}={best.get(args.key):.6g}  params={best_params}\n[SAVE] {BEST_OUT}")

    # run requested splits
    order = {"is": 0, "oos": 1, "full": 2}
    runs = sorted({x.strip().lower() for x in args.runs.split(",") if x.strip()},
                  key=lambda x: order.get(x, 99))
    for r in runs:
        run_split(r, args.tag, BEST_OUT)
    print("[DONE]")
