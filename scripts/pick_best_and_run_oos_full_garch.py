#!/usr/bin/env python3
# 从 IS 结果挑最优，然后批跑 IS + OOS + Full
import argparse, json, subprocess, sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
OUT_ROOT = PROJ / "output" / "asset07" / "garch_core4_v1"
RESULTS  = OUT_ROOT / "results.csv"
BEST_OUT = OUT_ROOT / "best_params.json"

SPLITS   = json.loads((PROJ/"configs"/"splits_asset07.json").read_text(encoding="utf-8"))
RUN_ONCE = PROJ / "scripts" / "run_once_asset07.py"

BASE_KEYS = ["p_sigma_q_low","p_sigma_q_high","p_mult_mid","p_mult_high"]

def parse_results(path: Path):
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    header = lines[0].split(",")
    rows = [dict(zip(header, l.split(","))) for l in lines[1:]]

    def to_float(x):
        try: return float(x)
        except: return 0.0

    for r in rows:
        for k,v in list(r.items()):
            if k in BASE_KEYS:
                try:
                    r[k] = int(v) if str(v).isdigit() else float(v)
                except:
                    r[k] = to_float(v)
            elif k != "run_dir":
                r[k] = to_float(v)
    return header, rows

def run_split(which: str, tag: str, params_path: Path):
    if   which=="is":   start,end,split = SPLITS["is_start"],  SPLITS["is_end"],  "70-30"
    elif which=="oos":  start,end,split = SPLITS["oos_start"], SPLITS["full_end"],"30-oos"
    elif which=="full": start,end,split = SPLITS["full_start"],SPLITS["full_end"],"100-full"
    else: raise ValueError(which)
    cmd = [sys.executable, str(RUN_ONCE),
           "--start", start, "--end", end,
           "--params", str(params_path), "--split", split, "--tag", tag]
    print(f"[RUN] {which.upper()}  {start} → {end}")
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default="true_pd_ratio")
    ap.add_argument("--runs", default="is,oos,full")
    ap.add_argument("--tag", default="v1_best_core4")
    ap.add_argument("--min-activity", type=float, default=0.0)
    args = ap.parse_args()

    if not RESULTS.exists():
        raise SystemExit(f"results.csv not found: {RESULTS}")

    header, rows = parse_results(RESULTS)

    if args.min_activity > 0:
        rows = [r for r in rows if float(r.get("activity_pct", 0.0)) >= args.min_activity]
        if not rows:
            raise SystemExit("过滤后无有效行，请降低 --min-activity。")

    if args.key not in header:
        raise SystemExit(f"{args.key} 不在列中：{header}")

    best = max(rows, key=lambda r: r.get(args.key, float("-inf")))
    best_params = {k: best[k] for k in BASE_KEYS}
    BEST_OUT.write_text(json.dumps(best_params, indent=2), encoding="utf-8")
    print(f"[BEST] {args.key}={best.get(args.key):.6g}  params={best_params}\n[SAVE] {BEST_OUT}")

    order = {"is":0,"oos":1,"full":2}
    runs = sorted(set([x.strip().lower() for x in args.runs.split(",") if x.strip()]),
                  key=lambda x: order.get(x, 99))
    for r in runs:
        run_split(r, args.tag, BEST_OUT)
    print("[DONE]")
