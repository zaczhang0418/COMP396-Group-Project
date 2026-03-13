# -*- coding: utf-8 -*-
# scripts/single_strat/mr/run_once.py
import argparse, json, subprocess, sys, time
from pathlib import Path

PROJ = Path(__file__).resolve().parents[3]
MAIN = PROJ / "main.py"
DATA_DIR = PROJ / "DATA" / "PART1"
STRATEGY = "mr_generic_v1"
DATA_NAME = "series_10"
ASSET_TAG = "asset10"

def run_once(
    start: str,
    end: str,
    params_path: str,
    tag: str,
    split: str,
    data_dir: str,
    output_root: str | None,
    strategy_id: str,
    data_name: str,
    asset_tag: str,
):
    ts = time.strftime("%Y%m%d")
    run_id = f"run_{ts}_{split}"
    if output_root:
        out_dir = Path(output_root) / run_id
    else:
        out_dir = PROJ / "output" / "part1" / asset_tag / tag / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    best = json.loads(Path(params_path).read_text(encoding="utf-8"))
    param_args = ["--param", f"data_name={data_name}"]
    for k, v in best.items(): param_args += ["--param", f"{k}={v}"]

    cmd = [
        sys.executable, str(MAIN),
        "--strategy", strategy_id,
        "--data-dir", str(data_dir),
        "--fromdate", start, "--todate", end,
        "--output-dir", str(out_dir),
    ] + param_args
    subprocess.run(cmd, check=True, cwd=str(PROJ))

    (out_dir/"meta.json").write_text(json.dumps({
        "strategy_id": strategy_id, "asset": asset_tag, "data_name": data_name, "split": split, "tag": tag,
        "run_id": run_id, "fromdate": start, "todate": end, "params": best,
        "data_dir": str(data_dir)
    }, indent=2), encoding="utf-8")

    summary = json.loads((out_dir/"run_summary.json").read_text(encoding="utf-8"))
    header = ["split","true_pd_ratio","open_pnl_pd_ratio","activity_pct","final_value","bankrupt"]
    row = [split, summary.get("true_pd_ratio", 0.0), summary.get("open_pnl_pd_ratio", 0.0), summary.get("activity_pct", 0.0), summary.get("final_value", 0.0), int(bool(summary.get("bankrupt", False)))]
    (out_dir/"metrics.csv").write_text(",".join(header)+"\n"+",".join(map(str,row)), encoding="utf-8")
    print(f"[OK] saved to {out_dir}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True); ap.add_argument("--end", required=True)
    ap.add_argument("--params", required=True); ap.add_argument("--tag", default="v1_best_core4")
    ap.add_argument("--split", choices=["30-oos","100-full","70-30"], required=True)
    ap.add_argument("--data-dir", default=str(DATA_DIR))
    ap.add_argument("--output-root", default=None)
    ap.add_argument("--strategy-id", default=STRATEGY)
    ap.add_argument("--data-name", default=DATA_NAME)
    ap.add_argument("--asset-tag", default=ASSET_TAG)
    args = ap.parse_args()
    run_once(
        args.start,
        args.end,
        args.params,
        args.tag,
        args.split,
        args.data_dir,
        args.output_root,
        args.strategy_id,
        args.data_name,
        args.asset_tag,
    )
