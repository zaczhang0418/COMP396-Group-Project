#单次回测/复验脚本（OOS & Full）
#路径： scripts/run_mr_once.py
#用途：用最佳参数分别跑 OOS 和 Full，并把 main 的输出“搬运”到统一目录结构（meta/params/metrics…）。
# scripts/run_mr_once.py
# scripts/run_mr_once.py
import argparse, json, subprocess, sys, time
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
MAIN = PROJ / "main.py"
DATA_DIR = PROJ / "DATA" / "PART1"

def run_once(start: str, end: str, params_path: str, tag: str, split: str):
    run_id = time.strftime("%Y%m%d_%H%M%S")
    out_dir = PROJ / "output" / "asset10" / tag / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # 读取参数 → 组装 --param
    best = json.loads(Path(params_path).read_text(encoding="utf-8"))
    param_args = ["--param", "data_name=series_10"]
    for k, v in best.items():
        param_args += ["--param", f"{k}={v}"]

    # 调 main.py（保留默认绘图）
    cmd = [
        sys.executable, str(MAIN),
        "--strategy", "mr_asset10_v1",
        "--data-dir", str(DATA_DIR),
        "--fromdate", start, "--todate", end,
        "--output-dir", str(out_dir),
    ] + param_args

    subprocess.run(cmd, check=True)

    # meta
    (out_dir/"meta.json").write_text(json.dumps({
        "strategy_id": "mr_asset10_v1",
        "asset": "10",
        "split": split,
        "tag": tag,
        "run_id": run_id,
        "fromdate": start,
        "todate": end,
        "params": best
    }, indent=2), encoding="utf-8")

    # metrics（按 main.py 的 run_summary.json 字段）
    summary = json.loads((out_dir/"run_summary.json").read_text(encoding="utf-8"))
    header = ["split","true_pd_ratio","open_pnl_pd_ratio","activity_pct","final_value","bankrupt"]
    row = [
        split,
        summary.get("true_pd_ratio", 0.0),
        summary.get("open_pnl_pd_ratio", 0.0),
        summary.get("activity_pct", 0.0),
        summary.get("final_value", 0.0),
        int(bool(summary.get("bankrupt", False)))
    ]
    (out_dir/"metrics.csv").write_text(",".join(header)+"\n"+",".join(map(str,row)), encoding="utf-8")
    print(f"[OK] saved to {out_dir}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--params", required=True)   # e.g. output/asset10/grid_core4_v1/best_params.json
    ap.add_argument("--tag", default="v1_best_core4")
    ap.add_argument("--split", choices=["30-oos","100-full","70-30"], required=True)
    args = ap.parse_args()
    run_once(args.start, args.end, args.params, args.tag, args.split)

