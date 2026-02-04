# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# scripts/tf/pick_best_tf.py
import argparse, json, subprocess, sys, csv
from pathlib import Path
from datetime import date

PROJ     = Path(__file__).resolve().parents[2]
OUT_ROOT = PROJ / "output" / "asset01" / "tf_core4_v1"
RESULTS  = OUT_ROOT / "results.csv"
BEST_OUT = OUT_ROOT / "best_params.json"
SPLITS   = json.loads((PROJ / "configs" / "splits_asset01.json").read_text(encoding="utf-8"))
RUN_ONCE = PROJ / "scripts" / "tf" / "run_tf_once.py"

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
    ap.add_argument("--min-activity", type=float, default=0.0)
    args = ap.parse_args()

    if not RESULTS.exists(): raise SystemExit(f"Not found: {RESULTS}")
    header, rows = parse_results(RESULTS)

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
    BEST_OUT.write_text(json.dumps(best_params, indent=2), encoding="utf-8")
    print(f"[BEST] {args.key}={best.get(args.key):.6g}  params={best_params}\n[SAVE] {BEST_OUT}")

    order = {"is": 0, "oos": 1, "full": 2}
    runs = sorted({x.strip().lower() for x in args.runs.split(",") if x.strip()},
                  key=lambda x: order.get(x, 99))
    for r in runs: run_split(r, args.tag, BEST_OUT)
    print("[DONE]")