# -*- coding: utf-8 -*-
# scripts/pick_best_and_run_oos.py
import argparse, json, subprocess, sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
OUT_ROOT = PROJ / "output" / "asset10" / "grid_core4_v1"
RESULTS = OUT_ROOT / "results.csv"
BEST_OUT = OUT_ROOT / "best_params.json"
SPLITS = json.loads((PROJ/"configs"/"splits_asset10.json").read_text(encoding="utf-8"))
RUN_ONCE = PROJ / "scripts" / "run_mr_once.py"

PARAM_KEYS = ["p_lookback","p_entry_z","p_exit_z","p_stop_mult"]

def parse_results(path: Path):
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        raise SystemExit(f"empty results: {path}")
    header = lines[0].split(",")
    rows = [dict(zip(header, l.split(","))) for l in lines[1:]]

    def to_float(x):
        try: return float(x)
        except: return 0.0

    for r in rows:
        for k in r:
            if k in PARAM_KEYS:
                # 参数尽量转成数值
                try:
                    r[k] = int(r[k]) if r[k].isdigit() else float(r[k])
                except:
                    pass
            else:
                r[k] = to_float(r[k])
    return header, rows

def run_split(which: str, tag: str, params_path: Path):
    which = which.lower()
    if which == "is":
        start, end, split = SPLITS["is_start"], SPLITS["is_end"], "70-30"
    elif which == "oos":
        start, end, split = SPLITS["oos_start"], SPLITS["full_end"], "30-oos"
    elif which == "full":
        start, end, split = SPLITS["full_start"], SPLITS["full_end"], "100-full"
    else:
        raise ValueError(f"unknown run split: {which}")

    cmd = [
        sys.executable, str(RUN_ONCE),
        "--start", start, "--end", end,
        "--params", str(params_path),
        "--split", split, "--tag", tag
    ]
    print(f"[RUN] {which.upper()}  {start} → {end}")
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default="true_pd_ratio",
                    help="选优指标（需在 results.csv 表头里），如 true_pd_ratio/open_pnl_pd_ratio/activity_pct")
    ap.add_argument("--tag", default="v1_best_core4", help="输出目录用的标签名")
    # 新增：一次性跑哪些区段；可选 is,oos,full 的逗号列表。若未提供，则按兼容逻辑只跑 OOS/可选 Full。
    ap.add_argument("--runs", default=None, help="逗号分隔：is,oos,full（例如 --runs is,oos,full）")
    # 兼容旧用法
    ap.add_argument("--also-full", action="store_true", help="（向后兼容）同时跑 Full")
    ap.add_argument("--also-is", action="store_true", help="（向后兼容）同时跑 IS")
    args = ap.parse_args()

    if not RESULTS.exists():
        raise SystemExit(f"results.csv not found: {RESULTS}")

    header, rows = parse_results(RESULTS)
    if args.key not in header:
        raise SystemExit(f"metric '{args.key}' not in results header: {header}")

    best = max(rows, key=lambda r: r.get(args.key, float("-inf")))
    best_params = {k: best[k] for k in PARAM_KEYS}
    BEST_OUT.write_text(json.dumps(best_params, indent=2), encoding="utf-8")
    print(f"[BEST] {args.key}={best[args.key]:.6g}  params={best_params}")
    print(f"[SAVE] {BEST_OUT}")

    # 解析要跑的区段
    if args.runs:
        runs = [x.strip().lower() for x in args.runs.split(",") if x.strip()]
    else:
        # 兼容旧逻辑：默认只跑 OOS；可叠加 also-full / also-is
        runs = ["oos"]
        if args.also_full: runs.append("full")
        if args.also_is:   runs.append("is")

    # 去重并按 IS→OOS→Full 顺序
    order = {"is":0, "oos":1, "full":2}
    runs = sorted(set(runs), key=lambda x: order.get(x, 99))

    for which in runs:
        run_split(which, args.tag, BEST_OUT)

    print("[DONE]")
