# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Run the part1 pipeline under the experiment layout."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from scripts.common_paths import experiment_root, get_stage_dir, rel_path, update_experiment_record


PROJ = Path(__file__).resolve().parent
TIMELINE = json.loads((PROJ / "configs" / "timeline.json").read_text(encoding="utf-8"))
DEFAULT_EXPERIMENT_TAG = "adhoc"


def run_command(cmd, step_name):
    print(f"\n{'=' * 20}\n[START] {step_name}\n{'=' * 20}")
    print(f"Executing: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, text=True)
        print(f"[DONE] {step_name}")
    except subprocess.CalledProcessError as exc:
        print(f"[ERROR] {step_name} failed with exit code {exc.returncode}", file=sys.stderr)
        sys.exit(1)


def get_combo_dates():
    """Load the shared part1 full date range for the combined run."""
    combo_start = TIMELINE["part1"]["full"]["start"]
    combo_end = TIMELINE["part1"]["full"]["end"]
    print(f"\n[INFO] Auto-detected combo date range: {combo_start} -> {combo_end}")
    return combo_start, combo_end


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment-tag", default=DEFAULT_EXPERIMENT_TAG)
    ap.add_argument("--clean-experiment", action="store_true")
    return ap.parse_args()


if __name__ == "__main__":
    args = parse_args()
    exp_root = experiment_root(args.experiment_tag, create=False)
    if args.clean_experiment and exp_root.exists():
        print(f"[CLEANUP] Removing experiment directory: {exp_root}")
        shutil.rmtree(exp_root)

    py_exec = sys.executable

    run_command([py_exec, "scripts/tf/run_core4_grid_tf.py", "--experiment-tag", args.experiment_tag], "TF Grid Search")
    run_command(
        [py_exec, "scripts/tf/pick_best_tf.py", "--experiment-tag", args.experiment_tag, "--runs", "is,oos,full", "--key", "true_pd_ratio"],
        "TF Pick Best",
    )

    run_command([py_exec, "scripts/mr/run_core4_grid_mr.py", "--experiment-tag", args.experiment_tag], "MR Grid Search")
    run_command(
        [py_exec, "scripts/mr/pick_best_mr.py", "--experiment-tag", args.experiment_tag, "--runs", "is,oos,full", "--key", "true_pd_ratio"],
        "MR Pick Best",
    )

    run_command([py_exec, "scripts/garch/run_core4_grid_garch.py", "--experiment-tag", args.experiment_tag], "GARCH Grid Search")
    run_command(
        [py_exec, "scripts/garch/pick_best_garch.py", "--experiment-tag", args.experiment_tag, "--runs", "is,oos,full", "--key", "true_pd_ratio"],
        "GARCH Pick Best",
    )

    start_date, end_date = get_combo_dates()
    combo_root = get_stage_dir(args.experiment_tag, "part1", "combo", "combo")
    run_command(
        [
            py_exec,
            "scripts/combo/run_combo_once.py",
            "--experiment-tag",
            args.experiment_tag,
            "--start",
            start_date,
            "--end",
            end_date,
            "--output-root",
            str(combo_root),
            "--cash",
            "1000000",
            "--w-tf",
            "0.45",
            "--w-mr",
            "0.45",
            "--w-ga",
            "0.10",
        ],
        "Combo Strategy Run",
    )

    update_experiment_record(
        args.experiment_tag,
        {
            "experiment_tag": args.experiment_tag,
            "timeline_config": rel_path(PROJ / "configs" / "timeline.json"),
            "part1": {
                "strategies": {
                    "tf": {
                        "grid_search_dir": rel_path(get_stage_dir(args.experiment_tag, "part1", "tf", "grid_search", create=False)),
                        "best_runs_dir": rel_path(get_stage_dir(args.experiment_tag, "part1", "tf", "best_runs", create=False)),
                    },
                    "mr": {
                        "grid_search_dir": rel_path(get_stage_dir(args.experiment_tag, "part1", "mr", "grid_search", create=False)),
                        "best_runs_dir": rel_path(get_stage_dir(args.experiment_tag, "part1", "mr", "best_runs", create=False)),
                    },
                    "garch": {
                        "grid_search_dir": rel_path(get_stage_dir(args.experiment_tag, "part1", "garch", "grid_search", create=False)),
                        "best_runs_dir": rel_path(get_stage_dir(args.experiment_tag, "part1", "garch", "best_runs", create=False)),
                    },
                },
                "combo": {
                    "combo_dir": rel_path(get_stage_dir(args.experiment_tag, "part1", "combo", "combo", create=False)),
                },
            },
        },
    )

    print("\n[SUCCESS] All pipeline steps completed successfully.")
