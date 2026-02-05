# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# scripts/mr/run_core4_grid_mr.py
import json, itertools, subprocess, sys, time
from pathlib import Path
try: import yaml
except: yaml = None

PROJ = Path(__file__).resolve().parents[2]
MAIN = PROJ / "main.py"
DATA_DIR = PROJ / "DATA" / "PART1"

SPLITS_PATH = PROJ / "configs" / "splits_asset10.json"
GRID_YAML = PROJ / "configs" / "grids" / "mr_core4_v1.yaml"
GRID_JSON = PROJ / "configs" / "grids" / "mr_core4_v1.json"
GRID_PATH  = GRID_YAML if GRID_YAML.exists() else GRID_JSON

OUT_ROOT = PROJ / "output" / "part1" / "asset10" / "mr_core4_v1"
OUT_ROOT.mkdir(parents=True, exist_ok=True)
CSV_OUT = OUT_ROOT / "results.csv"
SPLITS = json.loads(SPLITS_PATH.read_text(encoding="utf-8"))

def load_grid(path: Path):
    if path.suffix.lower() in (".yml", ".yaml"):
        if yaml is None: raise SystemExit("PyYAML missing")
        return yaml.safe_load(path.read_text(encoding="utf-8"))
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
        "--fromdate", SPLITS["is_start"],
        "--todate",   SPLITS["is_end"],
        "--output-dir", str(run_dir),
        "--no-plot"
    ] + param_args
    subprocess.run(cmd, check=True)

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
    if CSV_OUT.exists():
        CSV_OUT.rename(OUT_ROOT / f"results_{time.strftime('%Y%m%d_%H%M%S')}.csv")
    CSV_OUT.write_text(",".join(HEADER) + "\n", encoding="utf-8")

    combos = list(itertools.product(*[GRID[k] for k in PARAM_KEYS]))
    total = len(combos)

    for i, tup in enumerate(combos, 1):
        params = {k: v for k, v in zip(PARAM_KEYS, tup)}
        ts = time.strftime("%Y%m%d")
        run_name = f"run_{ts}_IS_{i:03d}"
        run_dir = OUT_ROOT / run_name

        try: m = run_one(params, run_dir)
        except Exception as e:
            print(f"[{i}/{total}] FAIL -> {run_dir} ({e})")
            m = {"true_pd_ratio":0.0,"open_pnl_pd_ratio":0.0,"activity_pct":0.0,"final_value":0.0,"bankrupt":0}

        row = [str(params[k]) for k in PARAM_KEYS] + [str(m[h]) for h in HEADER[len(PARAM_KEYS):]]
        with CSV_OUT.open("a", encoding="utf-8") as f: f.write(",".join(row) + "\n")
        print(f"[{i}/{total}] OK -> {run_dir}")