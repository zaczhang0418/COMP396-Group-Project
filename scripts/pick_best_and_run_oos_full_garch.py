# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# scripts/pick_best_and_run_oos_full_garch.py
# Pick best params from GARCH results.csv and run IS/OOS/FULL.

import argparse, json, subprocess, sys, csv
from pathlib import Path

PROJ     = Path(__file__).resolve().parents[1]
OUT_ROOT = PROJ / "output" / "asset07" / "garch_core4_v1"
RESULTS  = OUT_ROOT / "results.csv"
BEST_OUT = OUT_ROOT / "best_params.json"
SPLITS   = json.loads((PROJ / "configs" / "splits_asset07.json").read_text(encoding="utf-8"))

# ✅ 用新的单次运行脚本名
RUN_ONCE = PROJ / "scripts" / "run_garch_once.py"

def to_float(x):
    s = "" if x is None else str(x).strip()
    if s == "" or s.lower() in {"nan", "none"}:
        return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0

def parse_results(path: Path):
    # 兼容 UTF-8 BOM、空行
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
        raise ValueError(which)

    cmd = [sys.executable, str(RUN_ONCE),
           "--start", start, "--end", end,
           "--params", str(params_path), "--split", split, "--tag", tag]
    print(f"[RUN] {which.upper()}  {start} -> {end}")
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Pick best GARCH params and run IS/OOS/FULL.")
    ap.add_argument("--key", default="true_pd_ratio", help="metric column used for selection")
    ap.add_argument("--runs", default="is,oos,full",  help="comma-separated: any of is,oos,full")
    ap.add_argument("--tag",  default="v1_best_core4")
    args = ap.parse_args()

    if not RESULTS.exists():
        raise SystemExit(f"results.csv not found: {RESULTS}")

    header, rows = parse_results(RESULTS)

    # 自动识别参数列：所有以 p_ 开头的列
    PARAM_COLS = [h for h in header if h.startswith("p_")]
    if not PARAM_COLS:
        raise SystemExit("No parameter columns (prefix 'p_') found in results.csv")

    if args.key not in header:
        raise SystemExit(f"selection key '{args.key}' not in columns: {header}")

    best = max(rows, key=lambda r: r.get(args.key, float("-inf")))

    best_params = {k: best[k] for k in PARAM_COLS if k in best}
    BEST_OUT.write_text(json.dumps(best_params, indent=2), encoding="utf-8")
    print(f"[BEST] {args.key}={best.get(args.key):.6g}  params={best_params}\n[SAVE] {BEST_OUT}")

    order = {"is": 0, "oos": 1, "full": 2}
    runs = sorted({x.strip().lower() for x in args.runs.split(",") if x.strip()},
                  key=lambda x: order.get(x, 99))
    for r in runs:
        run_split(r, args.tag, BEST_OUT)
    print("[DONE]")
