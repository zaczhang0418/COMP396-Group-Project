# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# scripts/mr/run_core4_grid_mr.py
import argparse, json, itertools, subprocess, sys, time
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
if str(PROJ) not in sys.path:
    sys.path.insert(0, str(PROJ))

from scripts.common_paths import get_stage_dir  # noqa: E402

MAIN = PROJ / "main.py"
DATA_DIR = PROJ / "DATA" / "PART1"

TIMELINE_PATH = PROJ / "configs" / "timeline.json"
GRID_JSON = PROJ / "configs" / "grids" / "mr_core4_v1.json"
GRID_PATH = GRID_JSON
TIMELINE = json.loads(TIMELINE_PATH.read_text(encoding="utf-8"))
PART1 = TIMELINE["part1"]
DEFAULT_EXPERIMENT_TAG = "adhoc"

def load_grid(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

GRID = load_grid(GRID_PATH)
PARAM_KEYS = ["p_lookback", "p_entry_z", "p_exit_z", "p_stop_mult"]
HEADER = PARAM_KEYS + ["true_pd_ratio", "open_pnl_pd_ratio", "activity_pct", "final_value", "bankrupt"]

def run_one(params: dict, run_dir: Path):
    run_dir.mkdir(parents=True, exist_ok=True)
    param_args = ["--param", "data_name=asset_10"]
    for k, v in params.items(): param_args += ["--param", f"{k}={v}"]

    cmd = [
        sys.executable, str(MAIN),
        "--strategy", "mr_asset10_v1",
        "--data-dir", str(DATA_DIR),
        "--fromdate", PART1["is"]["start"],
        "--todate",   PART1["is"]["end"],
        "--output-dir", str(run_dir),
        "--no-plot"
    ] + param_args
    subprocess.run(cmd, check=True, cwd=str(PROJ))

    summary = json.loads((run_dir / "run_summary.json").read_text(encoding="utf-8"))
    metrics = {
        "true_pd_ratio":       float(summary.get("true_pd_ratio", 0.0)),
        "open_pnl_pd_ratio":   float(summary.get("open_pnl_pd_ratio", 0.0)),
        "activity_pct":        float(summary.get("activity_pct", 0.0)),
        "final_value":         float(summary.get("final_value", 0.0)),
        "bankrupt":            int(bool(summary.get("bankrupt", False))),
    }
    return metrics

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment-tag", default=DEFAULT_EXPERIMENT_TAG)
    args = ap.parse_args()

    out_root = get_stage_dir(args.experiment_tag, "part1", "mr", "grid_search")
    csv_out = out_root / "results.csv"
    if csv_out.exists():
        csv_out.rename(out_root / f"results_{time.strftime('%Y%m%d_%H%M%S')}.csv")
    csv_out.write_text(",".join(HEADER) + "\n", encoding="utf-8")

    combos = list(itertools.product(*[GRID[k] for k in PARAM_KEYS]))
    total = len(combos)

    for i, tup in enumerate(combos, 1):
        params = {k: v for k, v in zip(PARAM_KEYS, tup)}
        ts = time.strftime("%Y%m%d")
        run_name = f"run_{ts}_IS_{i:03d}"
        run_dir = out_root / run_name

        try: m = run_one(params, run_dir)
        except Exception as e:
            print(f"[{i}/{total}] FAIL -> {run_dir} ({e})")
            m = {"true_pd_ratio":0.0,"open_pnl_pd_ratio":0.0,"activity_pct":0.0,"final_value":0.0,"bankrupt":0}

        row = [str(params[k]) for k in PARAM_KEYS] + [str(m[h]) for h in HEADER[len(PARAM_KEYS):]]
        with csv_out.open("a", encoding="utf-8") as f: f.write(",".join(row) + "\n")
        print(f"[{i}/{total}] OK -> {run_dir}")
