#读取 configs/splits_asset10.json 与 configs/grids/core4_v1.json，对**前70%**跑网格；每组参数调用 main.py --start/--end；把每次 run_summary.json 解析成一行，汇总到
#output/asset10/grid_core4_v1/results.csv。
# scripts/run_core4_grid_refine_mr.py
# scripts/run_core4_grid_refine_mr.py
import json, itertools, subprocess, sys, time
from pathlib import Path

# --- 路径 ---
PROJ = Path(__file__).resolve().parents[1]
MAIN = PROJ / "main.py"
DATA_DIR = PROJ / "DATA" / "PART1"

SPLITS_PATH = PROJ / "configs" / "splits_asset10.json"
GRID_PATH   = PROJ / "configs" / "grids" / "core4_v1.json"

OUT_ROOT = PROJ / "output" / "asset10" / "grid_core4_v1"
OUT_ROOT.mkdir(parents=True, exist_ok=True)
CSV_OUT = OUT_ROOT / "results.csv"

# --- 读取切分 & 网格 ---
SPLITS = json.loads(SPLITS_PATH.read_text(encoding="utf-8"))
GRID   = json.loads(GRID_PATH.read_text(encoding="utf-8"))

# 四核参数列（与 grids/core4_v1.json 的键一致）
PARAM_KEYS = ["p_lookback", "p_entry_z", "p_exit_z", "p_stop_mult"]

# 结果列（与 main.py 的 run_summary.json 可拿到的字段一致）
HEADER = PARAM_KEYS + ["true_pd_ratio", "open_pnl_pd_ratio", "activity_pct", "final_value", "bankrupt"]

def run_one(params: dict, run_dir: Path):
    run_dir.mkdir(parents=True, exist_ok=True)

    # 组装 --param
    param_args = ["--param", "data_name=series_10"]
    for k, v in params.items():
        param_args += ["--param", f"{k}={v}"]

    # 调用 main.py（IS 区间），网格跑批关闭绘图以提速
    cmd = [
        sys.executable, str(MAIN),
        "--strategy", "mr_asset10_v1",
        "--data-dir", str(DATA_DIR),
        "--fromdate", SPLITS["is_start"],
        "--todate",   SPLITS["is_end"],
        "--output-dir", str(run_dir),
        "--no-plot"
    ] + param_args

    subprocess.run(cmd, check=True)

    # 解析回测摘要
    summary_path = run_dir / "run_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    metrics = {
        "true_pd_ratio":   float(summary.get("true_pd_ratio", 0.0)),
        "open_pnl_pd_ratio": float(summary.get("open_pnl_pd_ratio", 0.0)),
        "activity_pct":    float(summary.get("activity_pct", 0.0)),
        "final_value":     float(summary.get("final_value", 0.0)),
        "bankrupt":        int(bool(summary.get("bankrupt", False)))
    }
    return metrics

if __name__ == "__main__":
    # 若已有旧的 results.csv，备份一份，避免覆盖历史
    if CSV_OUT.exists():
        ts = time.strftime("%Y%m%d_%H%M%S")
        CSV_OUT.rename(OUT_ROOT / f"results_{ts}.csv")

    # 写表头
    CSV_OUT.write_text(",".join(HEADER) + "\n", encoding="utf-8")

    combos = list(itertools.product(*[GRID[k] for k in PARAM_KEYS]))
    total = len(combos)

    for i, tup in enumerate(combos, 1):
        params = {k: v for k, v in zip(PARAM_KEYS, tup)}
        run_id = time.strftime("%Y%m%d_%H%M%S") + f"_{i:03d}"
        run_dir = OUT_ROOT / f"run_{run_id}"

        m = run_one(params, run_dir)

        row = [str(params[k]) for k in PARAM_KEYS] + [str(m[h]) for h in HEADER[len(PARAM_KEYS):]]
        with CSV_OUT.open("a", encoding="utf-8") as f:
            f.write(",".join(row) + "\n")

        print(f"[{i}/{total}] OK -> {run_dir}")

