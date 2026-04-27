#!/usr/bin/env python3
"""Unified project runner for common COMP396 final-branch tasks."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run(cmd: list[str]) -> int:
    print("Running:", " ".join(cmd))
    env = os.environ.copy()
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    return subprocess.run(cmd, cwd=ROOT, env=env).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run common COMP396 project workflows.")
    sub = parser.add_subparsers(dest="command", required=True)

    backtest = sub.add_parser("backtest", help="Run the Backtrader harness.")
    backtest.add_argument(
        "--strategy",
        default="coursework_3.stage_2_team01_v3_final",
        help="Strategy module name under Strategies/, dotted paths allowed.",
    )
    backtest.add_argument("--strategy-class", help="Optional explicit strategy class.")
    backtest.add_argument("--data-dir", default="./DATA/PART1", help="Dataset folder.")
    backtest.add_argument("--output-dir", default="./Output/final_run", help="Output folder.")
    backtest.add_argument("--no-plot", action="store_true", help="Disable plot generation.")
    backtest.add_argument("--debug", action="store_true", help="Enable framework debug logs.")

    eda = sub.add_parser("eda", help="Run the EDA batch workflow.")
    eda.add_argument("dataset", nargs="?", default="OVERVIEW", help="ALL, OVERVIEW, PART1, PART2, PART3, or PART123.")

    sub.add_parser("archive-cw1", help="Regenerate compact Coursework 1 V1 archive outputs.")
    sub.add_parser("archive-cw2", help="Regenerate compact Coursework 2 V2 archive outputs.")
    cross_scan = sub.add_parser("cross-scan", help="Run Coursework 3 cross-asset scan tooling.")
    cross_scan.add_argument("--mode", choices=["run", "summarize", "validate-part2"], default="summarize")
    cross_scan.add_argument("args", nargs=argparse.REMAINDER, help="Extra args passed to the selected cross-scan script.")
    sub.add_parser("chapter3", help="Regenerate Chapter 3 report evidence packs.")

    dist = sub.add_parser("dist", help="Build a clean distribution ZIP.")
    dist.add_argument("--name", default="COMP396-final-package.zip", help="ZIP filename.")
    dist.add_argument("--no-output", action="store_true", help="Exclude Output/ from the ZIP.")

    args = parser.parse_args()
    py = sys.executable

    if args.command == "backtest":
        cmd = [
            py,
            "main.py",
            "--strategy",
            args.strategy,
            "--data-dir",
            args.data_dir,
            "--output-dir",
            args.output_dir,
        ]
        if args.strategy_class:
            cmd.extend(["--strategy-class", args.strategy_class])
        if args.no_plot:
            cmd.append("--no-plot")
        if args.debug:
            cmd.append("--debug")
        return run(cmd)

    if args.command == "eda":
        return run([py, "EDA/scripts/run_eda_stage4.py", args.dataset])

    if args.command == "archive-cw1":
        return run([py, "Scripts/coursework_1/stage_5_generate_v1_evidence_matrix.py"])

    if args.command == "archive-cw2":
        return run([py, "Scripts/coursework_2/stage_4_generate_v2_evidence_summary.py"])

    if args.command == "cross-scan":
        scripts = {
            "run": "Scripts/coursework_3/stage_1_cross_asset_scan/run_cross_asset_scan.py",
            "summarize": "Scripts/coursework_3/stage_1_cross_asset_scan/summarize_cross_asset_scan.py",
            "validate-part2": "Scripts/coursework_3/stage_1_cross_asset_scan/validate_cross_asset_scan_part2.py",
        }
        extra_args = args.args[1:] if args.args[:1] == ["--"] else args.args
        return run([py, scripts[args.mode], *extra_args])

    if args.command == "chapter3":
        scripts = [
            "Scripts/coursework_3/stage_3_chapter3_evidence/generate_coursework_3_chapter3_analysis.py",
            "Scripts/coursework_3/stage_3_chapter3_evidence/generate_part3_331_doc_pack.py",
            "Scripts/coursework_3/stage_3_chapter3_evidence/generate_part3_332_doc_pack.py",
            "Scripts/coursework_3/stage_3_chapter3_evidence/generate_part3_333_doc_pack.py",
            "Scripts/coursework_3/stage_3_chapter3_evidence/generate_part3_335_doc_pack.py",
            "Scripts/coursework_3/stage_3_chapter3_evidence/generate_part3_35_v3_workflow_pack.py",
            "Scripts/coursework_3/stage_3_chapter3_evidence/generate_part3_36_comparison_pack.py",
        ]
        for script in scripts:
            code = run([py, script])
            if code != 0:
                return code
        return 0

    if args.command == "dist":
        cmd = [py, "Scripts/distribution/make_dist.py", "--name", args.name]
        if args.no_output:
            cmd.append("--no-output")
        return run(cmd)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
