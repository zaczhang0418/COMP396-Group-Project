#!/usr/bin/env python3
# 单次回测（IS/OOS/Full 通用）
import argparse, json, subprocess, sys, time
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
MAIN = PROJ / "main.py"
DATA_DIR = PROJ / "DATA" / "PART1"

ASSET_TAG = "asset07"
DATA_NAME = "series_7"
STRATEGY  = "gr_asset07_v1"
DEFAULT_P_MIN_W_FOR_1 = 0.03

def norm_split_token(s): return s.replace("-", "")

def run_once(start: str, end: str, params_path: str, tag: str, split: str):
    ts = time.strftime("%Y%m%d_%H%M%S")
    run_id = f"{ts}_{ASSET_TAG}_{norm_split_token(split)}_{start}_{end}"
    out_dir = PROJ / "output" / ASSET_TAG / tag / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    best = json.loads(Path(params_path).read_text(encoding="utf-8"))
    param_args = [
        "--param", f"data_name={DATA_NAME}",
        "--param", f"p_min_w_for_1={DEFAULT_P_MIN_W_FOR_1}",
    ] + sum((["--param", f"{k}={v}"] for k,v in best.items()), [])

    cmd = [
        sys.executable, str(MAIN),
        "--strategy", STRATEGY,
        "--data-dir", str(DATA_DIR),
        "--fromdate", start, "--todate", end,
        "--output-dir", str(out_dir),
        *param_args
    ]
    subprocess.run(cmd, check=True)

    # meta & metrics
    (out_dir/"meta.json").write_text(json.dumps({
        "strategy_id": STRATEGY, "asset": "07", "data_name": DATA_NAME,
        "split": split, "tag": tag, "run_id": run_id,
        "fromdate": start, "todate": end, "params": best,
        "defaults": {"p_min_w_for_1": DEFAULT_P_MIN_W_FOR_1}
    }, indent=2), encoding="utf-8")

    summary = json.loads((out_dir/"run_summary.json").read_text(encoding="utf-8"))
    header = ["split","true_pd_ratio","open_pnl_pd_ratio","activity_pct","final_value","bankrupt"]
    row = [
        split,
        summary.get("true_pd_ratio",0.0),
        summary.get("open_pnl_pd_ratio",0.0),
        summary.get("activity_pct",0.0),
        summary.get("final_value",0.0),
        int(bool(summary.get("bankrupt",False)))
    ]
    (out_dir/"metrics.csv").write_text(",".join(header)+"\n"+",".join(map(str,row)), encoding="utf-8")
    print(f"[OK] saved to {out_dir}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--params", required=True)
    ap.add_argument("--tag", default="v1_best_core4")
    ap.add_argument("--split", choices=["70-30","30-oos","100-full"], required=True)
    args = ap.parse_args()
    run_once(args.start, args.end, args.params, args.tag, args.split)
