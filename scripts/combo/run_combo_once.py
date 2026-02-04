# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# scripts/combo/run_combo_once.py (Optimized)
import argparse, json, subprocess, sys, time
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
MAIN = PROJ / "main.py"
DATA_DIR = PROJ / "DATA" / "PART1"
OUT_ROOT = PROJ / "output" / "combo"
OUT_ROOT.mkdir(parents=True, exist_ok=True)

META_PATHS = {
    "tf": PROJ / "output" / "asset01" / "tf_core4_v1",
    "mr": PROJ / "output" / "asset10" / "mr_core4_v1",
    "ga": PROJ / "output" / "asset07" / "garch_core4_v1",
}
COMBO_STRAT = "combo_tf01_mr10_garch07_v1"

def load_params_file(dirpath: Path, label: str = "") -> dict:
    if not dirpath.exists():
        print(f"[WARN] {label.upper()} path not found: {dirpath}")
        return {}
    
    # 1. Try best_params.json (Highest Priority)
    f_best = dirpath / "best_params.json"
    if f_best.exists():
        print(f"[{label.upper()}] Found best_params.json: {f_best.relative_to(PROJ)}")
        try: return json.loads(f_best.read_text(encoding="utf-8"))
        except Exception as e: print(f"[ERR] Failed to read {f_best}: {e}")

    # 2. Fallback: find latest meta.json in subdirectories
    metas = sorted(dirpath.rglob("meta.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if metas:
        chosen = metas[0]
        try: display = chosen.relative_to(PROJ)
        except ValueError: display = chosen
        print(f"[{label.upper()}] Fallback to latest run: {display}")
        try: return json.loads(chosen.read_text(encoding="utf-8"))
        except Exception: return {}

    print(f"[WARN] No parameter file (best_params.json or meta.json) found in {dirpath}")
    return {}

def extract_params(data: dict) -> dict:
    if not data: return {}
    # If "params" key exists, use it; otherwise assume the dict IS the params (best_params.json structure)
    p = dict(data.get("params", data))
    # Normalize aliases
    if "p_stop_mult" in p and "p_stop_multiplier" not in p:
        p["p_stop_multiplier"] = p["p_stop_mult"]
    return p

def namespace_params(params: dict, prefix: str) -> dict:
    out = {}
    for k, v in params.items():
        # remove p_ if exists (e.g. p_ema_short -> ema_short)
        suffix = k[2:] if k.startswith("p_") else k
        new_key = f"{prefix}_{suffix}"
        out[new_key] = v
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True); ap.add_argument("--end", required=True)
    ap.add_argument("--split", default="custom")
    ap.add_argument("--w-tf", type=float, default=1/3); ap.add_argument("--w-mr", type=float, default=1/3); ap.add_argument("--w-ga", type=float, default=1/3)
    ap.add_argument("--cash",  type=float, default=1_000_000.0)
    ap.add_argument("--tag",   default="combo_v1")
    ap.add_argument("--no-plots", action="store_true")
    ap.add_argument("--meta-tf-dir", default=None); ap.add_argument("--meta-mr-dir", default=None); ap.add_argument("--meta-ga-dir", default=None)
    args = ap.parse_args()

    w_sum = args.w_tf + args.w_mr + args.w_ga
    if w_sum <= 0: sys.exit("Weights must sum to a positive number.")
    w_tf, w_mr, w_ga = args.w_tf / w_sum, args.w_mr / w_sum, args.w_ga / w_sum

    ts = time.strftime("%Y%m%d_%H%M%S")
    w_tag = f"w{w_tf:.2f}_{w_mr:.2f}_{w_ga:.2f}".replace(".", "")
    # Simplified folder name: combined_{weights}_{timestamp}
    run_id = f"combined_{w_tag}_{ts}"

    # 2) Combined Account Output
    COM_ROOT = OUT_ROOT / run_id
    COM_ROOT.mkdir(parents=True, exist_ok=True)

    tf_data = load_params_file(Path(args.meta_tf_dir) if args.meta_tf_dir else META_PATHS["tf"], "tf")
    mr_data = load_params_file(Path(args.meta_mr_dir) if args.meta_mr_dir else META_PATHS["mr"], "mr")
    ga_data = load_params_file(Path(args.meta_ga_dir) if args.meta_ga_dir else META_PATHS["ga"], "ga")

    tf_params = extract_params(tf_data)
    mr_params = extract_params(mr_data)
    ga_params = extract_params(ga_data)

    # Parameter Namespacing
    combo_params = {}
    combo_params.update(namespace_params(tf_params, "tf"))
    combo_params.update(namespace_params(mr_params, "mr"))
    combo_params.update(namespace_params(ga_params, "ga"))

    # --- Run Combined Strategy ---
    print(f"\n[RUN] COMBINED STRATEGY {args.start} -> {args.end}")
    cmd_combo = [
        sys.executable, str(MAIN),
        "--strategy", COMBO_STRAT,
        "--data-dir", str(DATA_DIR),
        "--fromdate", args.start, "--todate", args.end,
        "--cash", str(args.cash),
        "--output-dir", str(COM_ROOT),
        "--end-policy", "liquidate",
        "--param", f"w_tf={w_tf}",
        "--param", f"w_mr={w_mr}",
        "--param", f"w_ga={w_ga}",
    ]

    # Inject optimized parameters
    print(f"[INFO] Injecting {len(combo_params)} optimized parameters:")
    for k, v in combo_params.items():
        if isinstance(v, (int, float, str)):
            print(f"  --param {k}={v}")
            cmd_combo += ["--param", f"{k}={v}"]

    if args.no_plots: cmd_combo.append("--no-plot")
    subprocess.run(cmd_combo, check=True)

    print(f"\n[DONE] Results saved to: {COM_ROOT}")