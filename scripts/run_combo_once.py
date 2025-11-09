# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# Run TF(01), MR(10), GARCH(07) sequentially with capital weights, params from meta.json,
# then aggregate a combo summary. Optionally produce charts via main.py.

import argparse, json, subprocess, sys, time
from pathlib import Path
from shutil import copy2

PROJ = Path(__file__).resolve().parents[1]
MAIN = PROJ / "main.py"
DATA_DIR = PROJ / "DATA" / "PART1"

OUT_ROOT = PROJ / "output" / "combo"
OUT_ROOT.mkdir(parents=True, exist_ok=True)

# where to find latest meta.json produced by your "best run"
META_PATHS = {
    "tf": PROJ / "output" / "asset01" / "v1_best_core4",
    "mr": PROJ / "output" / "asset10" / "v1_best_core4",
    "ga": PROJ / "output" / "asset07" / "v1_best_core4",
}

# map for strategy module + required data_name
LEGS = {
    "tf": dict(strategy="tf_asset01_v1",    data_name="series_1"),
    "mr": dict(strategy="mr_asset10_v1",    data_name="series_10"),
    "ga": dict(strategy="garch_asset07_v1", data_name="series_7"),
}

def latest_meta(dirpath: Path) -> dict:
    if not dirpath.exists(): return {}
    metas = sorted(dirpath.rglob("meta.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not metas: return {}
    try:
        return json.loads(metas[0].read_text(encoding="utf-8"))
    except Exception:
        return {}

def params_from_meta(meta: dict) -> dict:
    """expect keys under meta['params']"""
    if not meta: return {}
    p = dict(meta.get("params", {}))
    # normalize common alias
    if "p_stop_mult" in p and "p_stop_multiplier" not in p:
        p["p_stop_multiplier"] = p["p_stop_mult"]
    return p

def _copy_key_imgs(src_dir: Path, dst_dir: Path, prefix: str):
    # 复制常见命名的关键图表，重命名加 tf_/mr_/ga_ 前缀
    patterns = ["*equity*.png", "*dashboard*.png", "*true*.png",
                "*underwater*.png", "*per_series*.png", "*realized*.png"]
    for pat in patterns:
        for p in src_dir.glob(pat):
            try:
                copy2(p, dst_dir / f"{prefix}_{p.name}")
            except Exception:
                pass

def run_one(start: str, end: str, cash: float, params: dict, out_dir: Path, leg: str, no_plots: bool):
    leg_cfg = LEGS[leg]
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, str(MAIN),
        "--strategy", leg_cfg["strategy"],
        "--data-dir", str(DATA_DIR),
        "--fromdate", start, "--todate", end,
        "--cash", str(float(cash)),
        "--output-dir", str(out_dir),
        "--param", f"data_name={leg_cfg['data_name']}",
    ]
    if no_plots:
        cmd.append("--no-plot")

    # append params from meta.json (if any)
    for k, v in params.items():
        cmd += ["--param", f"{k}={v}"]

    print(f"[RUN] {leg.upper()}  {start} -> {end}  cash={cash:,.2f}  plots={'OFF' if no_plots else 'ON'}")
    subprocess.run(cmd, check=True)

    # read summary of this leg
    summary = json.loads((out_dir / "run_summary.json").read_text(encoding="utf-8"))
    return summary, out_dir

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Run combo once using existing single strategies and meta.json params.")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end",   required=True, help="YYYY-MM-DD")
    ap.add_argument("--split", default="custom", help="label only, e.g., 70-30/30-oos/100-full/custom")
    ap.add_argument("--w-tf", type=float, default=1/3, help="capital weight for TF leg")
    ap.add_argument("--w-mr", type=float, default=1/3, help="capital weight for MR leg")
    ap.add_argument("--w-ga", type=float, default=1/3, help="capital weight for GARCH leg")
    ap.add_argument("--cash",  type=float, default=1_000_000.0, help="total cash")
    ap.add_argument("--tag",   default="combo_v1", help="tag for outputs")
    # ✅ 默认开启画图；只有显式传 --no-plots 才关闭
    ap.add_argument("--no-plots", action="store_true", help="disable plots in each single run")

    ap.add_argument("--meta-tf-dir", default=None, help="override folder containing TF meta.jsons")
    ap.add_argument("--meta-mr-dir", default=None, help="override folder containing MR meta.jsons")
    ap.add_argument("--meta-ga-dir", default=None, help="override folder containing GARCH meta.jsons")
    args = ap.parse_args()

    # normalize weights
    w_sum = args.w_tf + args.w_mr + args.w_ga
    if w_sum <= 0:
        sys.exit("Weights must sum to a positive number.")
    w_tf, w_mr, w_ga = args.w_tf / w_sum, args.w_mr / w_sum, args.w_ga / w_sum

    ts = time.strftime("%Y%m%d_%H%M%S")
    run_id = f"{ts}_{args.split}_{args.start}_{args.end}"
    COMBO_OUT = OUT_ROOT / f"{args.tag}_{run_id}"
    COMBO_OUT.mkdir(parents=True, exist_ok=True)

    # find latest meta.jsons (or use overrides)
    tf_meta = latest_meta(Path(args.meta_tf_dir) if args.meta_tf_dir else META_PATHS["tf"])
    mr_meta = latest_meta(Path(args.meta_mr_dir) if args.meta_mr_dir else META_PATHS["mr"])
    ga_meta = latest_meta(Path(args.meta_ga_dir) if args.meta_ga_dir else META_PATHS["ga"])

    tf_params = params_from_meta(tf_meta)
    mr_params = params_from_meta(mr_meta)
    ga_params = params_from_meta(ga_meta)

    # run each leg with weighted cash
    res = {}
    res["tf"], tf_dir = run_one(args.start, args.end, args.cash * w_tf, tf_params, COMBO_OUT / "tf", "tf", args.no_plots)
    res["mr"], mr_dir = run_one(args.start, args.end, args.cash * w_mr, mr_params, COMBO_OUT / "mr", "mr", args.no_plots)
    res["ga"], ga_dir = run_one(args.start, args.end, args.cash * w_ga, ga_params, COMBO_OUT / "ga", "ga", args.no_plots)

    # aggregate (approx PD by weight)
    final_value = float(res["tf"]["final_value"]) + float(res["mr"]["final_value"]) + float(res["ga"]["final_value"])
    pd_tf = float(res["tf"].get("true_pd_ratio") or 0.0)
    pd_mr = float(res["mr"].get("true_pd_ratio") or 0.0)
    pd_ga = float(res["ga"].get("true_pd_ratio") or 0.0)
    combo_pd_approx = w_tf*pd_tf + w_mr*pd_mr + w_ga*pd_ga

    combo_summary = {
        "run_id": run_id,
        "split": args.split,
        "start": args.start, "end": args.end,
        "weights": {"tf": w_tf, "mr": w_mr, "ga": w_ga},
        "cash_total": args.cash,
        "legs": {"tf": res["tf"], "mr": res["mr"], "ga": res["ga"]},
        "final_value_sum": final_value,
        "true_pd_ratio_approx": combo_pd_approx
    }
    (COMBO_OUT / "combo_summary.json").write_text(json.dumps(combo_summary, indent=2), encoding="utf-8")
    print("\n=== COMBO SUMMARY ===")
    print(json.dumps(combo_summary, indent=2))

    # 把关键图片复制到组合目录
    if not args.no_plots:
        _copy_key_imgs(tf_dir, COMBO_OUT, "tf")
        _copy_key_imgs(mr_dir, COMBO_OUT, "mr")
        _copy_key_imgs(ga_dir, COMBO_OUT, "ga")
        print("[COPIED] key images into combo folder.")
