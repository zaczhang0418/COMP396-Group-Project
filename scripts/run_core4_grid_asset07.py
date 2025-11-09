#!/usr/bin/env python3
# 70% IS 网格（不出图）→ results.csv
import itertools, json, subprocess, sys, time
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
MAIN = PROJ / "main.py"
DATA_DIR = PROJ / "DATA" / "PART1"

SPLITS = json.loads((PROJ / "configs" / "splits_asset07.json").read_text(encoding="utf-8"))
GRID   = json.loads((PROJ / "configs" / "grids" / "garch_core4_v1.json").read_text(encoding="utf-8"))

OUT_ROOT = PROJ / "output" / "asset07" / "garch_core4_v1"
OUT_ROOT.mkdir(parents=True, exist_ok=True)
CSV_OUT = OUT_ROOT / "results.csv"

STRATEGY  = "gr_asset07_v1"
DATA_NAME = "series_7"
ASSET_TAG = "asset07"

PARAM_KEYS = ["p_sigma_q_low","p_sigma_q_high","p_mult_mid","p_mult_high"]
HEADER = ["run_dir"] + PARAM_KEYS + ["true_pd_ratio","open_pnl_pd_ratio","activity_pct","final_value","bankrupt"]
DEFAULT_P_MIN_W_FOR_1 = 0.03

def _asfloat(x, default=0.0):
    try: return float(x) if x is not None else default
    except Exception: return default

def write_meta(run_dir: Path, params: dict):
    meta = {
        "strategy_id": STRATEGY, "asset_tag": ASSET_TAG, "data_name": DATA_NAME,
        "split": "IS(70%)", "fromdate": SPLITS["is_start"], "todate": SPLITS["is_end"],
        "params": params, "defaults": {"p_min_w_for_1": DEFAULT_P_MIN_W_FOR_1}
    }
    (run_dir/"meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

def run_one(params: dict, run_dir: Path):
    run_dir.mkdir(parents=True, exist_ok=True)
    param_args = [
        "--param", f"data_name={DATA_NAME}",
        "--param", f"p_min_w_for_1={DEFAULT_P_MIN_W_FOR_1}",
    ] + sum((["--param", f"{k}={v}"] for k,v in params.items()), [])

    cmd = [
        sys.executable, str(MAIN),
        "--strategy", STRATEGY,
        "--data-dir", str(DATA_DIR),
        "--fromdate", SPLITS["is_start"],
        "--todate",   SPLITS["is_end"],
        "--output-dir", str(run_dir),
        "--no-plot",
        *param_args
    ]
    subprocess.run(cmd, check=True)

    summary = json.loads((run_dir/"run_summary.json").read_text(encoding="utf-8"))
    metrics = {
        "true_pd_ratio":     _asfloat(summary.get("true_pd_ratio")),
        "open_pnl_pd_ratio": _asfloat(summary.get("open_pnl_pd_ratio")),
        "activity_pct":      _asfloat(summary.get("activity_pct")),
        "final_value":       _asfloat(summary.get("final_value")),
        "bankrupt":          int(bool(summary.get("bankrupt", False))),
    }
    write_meta(run_dir, params)
    return metrics

if __name__ == "__main__":
    if CSV_OUT.exists():
        CSV_OUT.rename(OUT_ROOT / f"results_{time.strftime('%Y%m%d_%H%M%S')}.csv")
    CSV_OUT.write_text(",".join(HEADER) + "\n", encoding="utf-8")

    grids = [GRID[k] for k in PARAM_KEYS]
    combos = list(itertools.product(*grids))
    total = len(combos)

    for i, tup in enumerate(combos, 1):
        params = {k:v for k,v in zip(PARAM_KEYS, tup)}
        ts = time.strftime("%Y%m%d_%H%M%S")
        run_name = f"run_{ts}_{ASSET_TAG}_IS_{SPLITS['is_start']}_{SPLITS['is_end']}_{i:03d}"
        run_dir  = OUT_ROOT / run_name
        try:
            m = run_one(params, run_dir)
        except Exception as e:
            print(f"[{i}/{total}] FAIL -> {run_dir} ({e})")
            m = {"true_pd_ratio":0.0,"open_pnl_pd_ratio":0.0,"activity_pct":0.0,"final_value":0.0,"bankrupt":0}

        row = [run_name, *(str(params[k]) for k in PARAM_KEYS),
               str(m["true_pd_ratio"]), str(m["open_pnl_pd_ratio"]), str(m["activity_pct"]),
               str(m["final_value"]), str(m["bankrupt"])]
        with CSV_OUT.open("a", encoding="utf-8") as f:
            f.write(",".join(row)+"\n")
        print(f"[{i}/{total}] OK -> {run_dir}")
