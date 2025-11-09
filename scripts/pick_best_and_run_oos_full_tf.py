#!/usr/bin/env python3
# pick_best_and_run_oos_full_tf.py
import argparse, json, subprocess, sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
OUT_ROOT = PROJ / "output" / "asset01" / "tf_core4_v1"
RESULTS  = OUT_ROOT / "results.csv"
BEST_OUT = OUT_ROOT / "best_params.json"
SPLITS   = json.loads((PROJ/"configs"/"splits_asset01.json").read_text(encoding="utf-8"))
RUN_ONCE = PROJ / "scripts" / "run_tr_once.py"

# 三个固定 + 1 个“止损倍数”列（两种名字任选其一）
BASE_KEYS = ["p_ema_short","p_ema_long","p_hurst_min_soft"]

def parse_results(path: Path):
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    header = lines[0].split(",")
    rows = [dict(zip(header, l.split(","))) for l in lines[1:]]
    def to_float(x):
        try: return float(x)
        except: return 0.0
    # 数值化
    for r in rows:
        for k,v in list(r.items()):
            if k in BASE_KEYS + ["p_stop_multiplier","p_stop_mult"]:
                try:
                    r[k] = int(v) if str(v).isdigit() else float(v)
                except:
                    r[k] = to_float(v)
            else:
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
    ap.add_argument("--key", default="true_pd_ratio")     # 选优指标
    ap.add_argument("--runs", default="is,oos,full")      # is,oos,full 任意组合
    ap.add_argument("--tag", default="v1_best_core4")
    ap.add_argument("--min-activity", type=float, default=0.0, help="过滤最低活动度，默认不过滤")
    args = ap.parse_args()

    if not RESULTS.exists():
        raise SystemExit(f"results.csv not found: {RESULTS}")

    header, rows = parse_results(RESULTS)

    # 兼容两种列名：p_stop_multiplier 优先，其次 p_stop_mult
    if   "p_stop_multiplier" in header: STOP_KEY = "p_stop_multiplier"
    elif "p_stop_mult"      in header: STOP_KEY = "p_stop_mult"
    else:
        raise SystemExit("results.csv 缺少列：p_stop_multiplier / p_stop_mult 其一")

    # 过滤活动度（可选）
    if args.min_activity > 0:
        rows = [r for r in rows if r.get("activity_pct", 0.0) >= args.min_activity]
        if not rows:
            raise SystemExit("过滤后无有效行，请降低 --min-activity 或放宽网格。")

    # 选优
    if args.key not in header:
        raise SystemExit(f"{args.key} 不在列中：{header}")
    best = max(rows, key=lambda r: r.get(args.key, float("-inf")))

    # 写 best_params.json —— 注意把止损键名标准化为 p_stop_multiplier
    best_params = {k: best[k] for k in BASE_KEYS}
    best_params["p_stop_multiplier"] = best[STOP_KEY]
    BEST_OUT.write_text(json.dumps(best_params, indent=2), encoding="utf-8")
    print(f"[BEST] {args.key}={best.get(args.key):.6g}  params={best_params}\n[SAVE] {BEST_OUT}")

    # 跑指定分段
    order = {"is":0,"oos":1,"full":2}
    runs = sorted(set([x.strip().lower() for x in args.runs.split(",") if x.strip()]),
                  key=lambda x: order.get(x,99))
    for r in runs:
        run_split(r, args.tag, BEST_OUT)
    print("[DONE]")
