#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from common_paths import default_data_dir, default_output_root, detect_csv_date_range, detect_overlap_range, ensure_dir


PROJ = Path(__file__).resolve().parents[1]

BEST_PARAM_PATHS = {
    "tf": ("asset01", "tf_core4_v1", PROJ / "scripts" / "tf" / "run_tf_once.py", "01"),
    "mr": ("asset10", "mr_core4_v1", PROJ / "scripts" / "mr" / "run_mr_once.py", "10"),
    "ga": ("asset07", "garch_core4_v1", PROJ / "scripts" / "garch" / "run_garch_once.py", "07"),
}


def run_command(cmd: list[str], step_name: str) -> None:
    print(f"\n[START] {step_name}")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(PROJ))
    print(f"[DONE] {step_name}")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def append_summary_row(csv_path: Path, row: dict) -> None:
    fieldnames = [
        "strategy",
        "asset",
        "source_part",
        "target_part",
        "tag",
        "split",
        "fromdate",
        "todate",
        "true_pd_ratio",
        "open_pnl_pd_ratio",
        "activity_pct",
        "final_value",
        "bankrupt",
        "run_dir",
    ]
    write_header = not csv_path.exists()
    with csv_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def latest_run_dir(base_dir: Path, tag: str) -> Path:
    candidates = sorted((base_dir / tag).glob("run_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No run directory found in {base_dir / tag}")
    return candidates[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-part", default="part1")
    ap.add_argument("--target-part", default="part2")
    ap.add_argument("--tag", default=f"{date.today():%Y%m%d}_part2_from_part1_best")
    ap.add_argument("--cash", type=float, default=1_000_000.0)
    ap.add_argument("--w-tf", type=float, default=0.45)
    ap.add_argument("--w-mr", type=float, default=0.45)
    ap.add_argument("--w-ga", type=float, default=0.10)
    ap.add_argument("--no-plots", action="store_true")
    args = ap.parse_args()

    source_output_root = default_output_root(args.source_part)
    target_output_root = default_output_root(args.target_part)
    target_data_dir = default_data_dir(args.target_part)
    manifest = {
        "source_part": args.source_part,
        "target_part": args.target_part,
        "tag": args.tag,
        "cash": args.cash,
        "weights": {"tf": args.w_tf, "mr": args.w_mr, "ga": args.w_ga},
        "strategies": {},
    }
    ensure_dir(target_output_root)
    summary_csv = target_output_root / f"{args.tag}_summary.csv"
    manifest_path = target_output_root / f"{args.tag}_manifest.json"

    for strategy_key, (asset_tag, best_dir_name, runner, asset_id) in BEST_PARAM_PATHS.items():
        best_params_path = source_output_root / asset_tag / best_dir_name / "best_params.json"
        if not best_params_path.exists():
            raise FileNotFoundError(f"Missing best params: {best_params_path}")

        start, end = detect_csv_date_range(target_data_dir / f"{asset_id}.csv")
        cmd = [
            sys.executable,
            str(runner),
            "--start",
            start,
            "--end",
            end,
            "--params",
            str(best_params_path),
            "--tag",
            args.tag,
            "--split",
            "100-full",
            "--data-dir",
            str(target_data_dir),
            "--output-root",
            str(target_output_root),
        ]
        run_command(cmd, f"{strategy_key.upper()} on {args.target_part.upper()}")

        run_dir = latest_run_dir(target_output_root / asset_tag, args.tag)
        summary = load_json(run_dir / "run_summary.json")
        append_summary_row(summary_csv, {
            "strategy": strategy_key,
            "asset": asset_id,
            "source_part": args.source_part,
            "target_part": args.target_part,
            "tag": args.tag,
            "split": "100-full",
            "fromdate": start,
            "todate": end,
            "true_pd_ratio": summary.get("true_pd_ratio"),
            "open_pnl_pd_ratio": summary.get("open_pnl_pd_ratio"),
            "activity_pct": summary.get("activity_pct"),
            "final_value": summary.get("final_value"),
            "bankrupt": summary.get("bankrupt"),
            "run_dir": str(run_dir.relative_to(PROJ)),
        })
        manifest["strategies"][strategy_key] = {
            "asset": asset_id,
            "best_params_path": str(best_params_path.relative_to(PROJ)),
            "start": start,
            "end": end,
            "run_dir": str(run_dir.relative_to(PROJ)),
        }

    combo_start, combo_end = detect_overlap_range(target_data_dir, ["01", "07", "10"])
    combo_cmd = [
        sys.executable,
        str(PROJ / "scripts" / "combo" / "run_combo_once.py"),
        "--start",
        combo_start,
        "--end",
        combo_end,
        "--tag",
        args.tag,
        "--split",
        "part2-full",
        "--cash",
        str(args.cash),
        "--w-tf",
        str(args.w_tf),
        "--w-mr",
        str(args.w_mr),
        "--w-ga",
        str(args.w_ga),
        "--data-dir",
        str(target_data_dir),
        "--output-root",
        str(target_output_root),
        "--meta-tf-dir",
        str(source_output_root / "asset01" / "tf_core4_v1"),
        "--meta-mr-dir",
        str(source_output_root / "asset10" / "mr_core4_v1"),
        "--meta-ga-dir",
        str(source_output_root / "asset07" / "garch_core4_v1"),
    ]
    if args.no_plots:
        combo_cmd.append("--no-plots")
    run_command(combo_cmd, f"COMBO on {args.target_part.upper()}")

    combo_runs = sorted((target_output_root / "combo").glob("combined_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not combo_runs:
        raise FileNotFoundError("No combo run directory found")
    combo_dir = combo_runs[0]
    combo_summary = load_json(combo_dir / "run_summary.json")
    append_summary_row(summary_csv, {
        "strategy": "combo",
        "asset": "01+07+10",
        "source_part": args.source_part,
        "target_part": args.target_part,
        "tag": args.tag,
        "split": "full-overlap",
        "fromdate": combo_start,
        "todate": combo_end,
        "true_pd_ratio": combo_summary.get("true_pd_ratio"),
        "open_pnl_pd_ratio": combo_summary.get("open_pnl_pd_ratio"),
        "activity_pct": combo_summary.get("activity_pct"),
        "final_value": combo_summary.get("final_value"),
        "bankrupt": combo_summary.get("bankrupt"),
        "run_dir": str(combo_dir.relative_to(PROJ)),
    })
    manifest["combo"] = {
        "start": combo_start,
        "end": combo_end,
        "run_dir": str(combo_dir.relative_to(PROJ)),
    }

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n[SAVED] Archive summary: {summary_csv}")
    print(f"[SAVED] Archive manifest: {manifest_path}")


if __name__ == "__main__":
    main()
