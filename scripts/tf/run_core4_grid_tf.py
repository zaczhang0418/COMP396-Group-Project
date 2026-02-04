# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# scripts/tf/run_core4_grid_tf.py
import itertools, json, subprocess, sys, time
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
MAIN = PROJ / "main.py"
DATA_DIR = PROJ / "DATA" / "PART1"

SPLITS = json.loads((PROJ / "configs" / "splits_asset01.json").read_text(encoding="utf-8"))
GRID   = json.loads((PROJ / "configs" / "grids" / "tf_core4_v1.json").read_text(encoding="utf-8"))

OUT_ROOT = PROJ / "output" / "asset01" / "tf_core4_v1"
OUT_ROOT.mkdir(parents=True, exist_ok=True)
CSV_OUT = OUT_ROOT / "results.csv"

STRATEGY  = "tf_asset01_v1"
DATA_NAME = "series_1"
ASSET_TAG = "asset01"

PARAM_KEYS = ["p_ema_short", "p_ema_long", "p_hurst_min_soft", "p_stop_multiplier"]
HEADER = ["run_dir"] + PARAM_KEYS + ["true_pd_ratio", "open_pnl_pd_ratio", "activity_pct", "final_value", "bankrupt"]
SKIP_ZERO_ACTIVITY = False
DEFAULT_P_MIN_W_FOR_1 = 0.03

def _asfloat(x, default=0.0):
    try: return float(x) if x is not None else default
    except Exception: return default

def write_meta(run_dir: Path, params: dict, splits: dict):
    meta = {
        "strategy_id": STRATEGY, "asset_tag": ASSET_TAG, "data_name": DATA_NAME,
        "split": "IS(70%)", "fromdate": splits["is_start"], "todate": splits["is_end"],
        "params": params, "defaults": {"p_min_w_for_1": DEFAULT_P_MIN_W_FOR_1}
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

def run_one(params: dict, run_dir: Path) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    param_args = [
        "--param", f"data_name={DATA_NAME}",
        "--param", f"p_min_w_for_1={DEFAULT_P_MIN_W_FOR_1}",
    ]
    for k, v in params.items(): param_args += ["--param", f"{k}={v}"]

    cmd = [
        sys.executable, str(MAIN),
        "--strategy", STRATEGY,
        "--data-dir", str(DATA_DIR),
        "--fromdate", SPLITS["is_start"],
        "--todate",   SPLITS["is_end"],
        "--output-dir", str(run_dir),
        "--no-plot", *param_args
    ]
    subprocess.run(cmd, check=True)

    summary_path = run_dir / "run_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    metrics = {
        "true_pd_ratio":     _asfloat(summary.get("true_pd_ratio")),
        "open_pnl_pd_ratio": _asfloat(summary.get("open_pnl_pd_ratio")),
        "activity_pct":      _asfloat(summary.get("activity_pct")),
        "final_value":       _asfloat(summary.get("final_value")),
        "bankrupt":          int(bool(summary.get("bankrupt", False))),
    }
    write_meta(run_dir, params, SPLITS)
    return metrics

if __name__ == "__main__":
    if CSV_OUT.exists():
        CSV_OUT.rename(OUT_ROOT / f"results_{time.strftime('%Y%m%d_%H%M%S')}.csv")
    CSV_OUT.write_text(",".join(HEADER) + "\n", encoding="utf-8")

    try: grids = [GRID[k] for k in PARAM_KEYS]
    except KeyError as e: raise SystemExit(f"[ERR] Missing key: {e}")

    combos = list(itertools.product(*grids))
    total = len(combos)

    for i, tup in enumerate(combos, 1):
        params = {k: v for k, v in zip(PARAM_KEYS, tup)}
        ts = time.strftime("%Y%m%d")
        run_name = f"run_{ts}_IS_{i:03d}"
        run_dir  = OUT_ROOT / run_name

        try: m = run_one(params, run_dir)
        except Exception as e:
            m = {"true_pd_ratio": 0.0, "open_pnl_pd_ratio": 0.0, "activity_pct": 0.0, "final_value": 0.0, "bankrupt": 0}
            print(f"[{i}/{total}] FAIL -> {run_dir} ({e})")

        if SKIP_ZERO_ACTIVITY and m.get("activity_pct", 0.0) == 0.0:
            print(f"[{i}/{total}] skip(no trades) -> {run_dir}")
            continue

        row = [run_name, *(str(params[k]) for k in PARAM_KEYS),
               str(m["true_pd_ratio"]), str(m["open_pnl_pd_ratio"]), str(m["activity_pct"]),
               str(m["final_value"]), str(m["bankrupt"])]
        with CSV_OUT.open("a", encoding="utf-8") as f: f.write(",".join(row) + "\n")
        print(f"[{i}/{total}] OK -> {run_dir}")