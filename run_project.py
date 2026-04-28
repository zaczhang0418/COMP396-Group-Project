#!/usr/bin/env python3
"""Unified project runner for common COMP396 final-branch tasks."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from collections.abc import Callable


ROOT = Path(__file__).resolve().parent


def run(cmd: list[str]) -> int:
    print("Running:", " ".join(cmd))
    env = os.environ.copy()
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    return subprocess.run(cmd, cwd=ROOT, env=env).returncode


def format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {secs:02d}s"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def print_progress(completed: int, total: int, started_at: float, label: str) -> None:
    width = 28
    filled = int(width * completed / total) if total else width
    bar = "#" * filled + "-" * (width - filled)
    elapsed = time.monotonic() - started_at
    if completed:
        eta = elapsed / completed * (total - completed)
        eta_text = format_duration(eta)
    else:
        eta_text = "estimating"
    pct = int(100 * completed / total) if total else 100
    print(
        f"\n[{bar}] {completed}/{total} {pct:3d}% | "
        f"elapsed {format_duration(elapsed)} | ETA {eta_text} | {label}",
        flush=True,
    )


FullStep = tuple[str, list[str] | Callable[[], int]]


def check_existing_cross_asset_evidence() -> int:
    required = [
        ROOT / "Output" / "coursework_3" / "stage_1_cross_asset_scan" / "summaries" / "cross_asset_long.csv",
        ROOT / "Output" / "coursework_3" / "stage_1_cross_asset_scan" / "summaries" / "matrix_3x10.csv",
        ROOT / "Output" / "coursework_3" / "stage_1_cross_asset_scan" / "summaries" / "asset_strategy_assignment.csv",
        ROOT / "Output" / "coursework_3" / "stage_1_cross_asset_scan" / "summaries" / "part2_validation.csv",
        ROOT / "Output" / "coursework_3" / "stage_1_cross_asset_scan" / "summaries" / "summary.json",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        print("Missing existing cross-asset evidence files:")
        for path in missing:
            print(f"  - {path.relative_to(ROOT)}")
        print("Run without --skip-cross-scan-run to regenerate the raw scan and summary evidence.")
        return 1
    print("Existing cross-asset summary evidence found:")
    for path in required:
        print(f"  - {path.relative_to(ROOT)}")
    return 0


def run_full_pipeline(steps: list[FullStep]) -> int:
    started_at = time.monotonic()
    total = len(steps)
    print_progress(0, total, started_at, "starting full workflow")
    for index, (label, action) in enumerate(steps, start=1):
        print(f"\n=== Step {index}/{total}: {label} ===", flush=True)
        code = action() if callable(action) else run(action)
        if code != 0:
            print_progress(index - 1, total, started_at, f"failed: {label}")
            return code
        print_progress(index, total, started_at, f"completed: {label}")
    return 0


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
    backtest.add_argument(
        "--output-dir",
        default="./Output/coursework_3/stage_2_team01_v3_final/manual_backtest",
        help="Output folder.",
    )
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

    full = sub.add_parser("full", help="Run the complete final-branch workflow with progress and ETA.")
    full.add_argument("--eda", choices=["ALL", "OVERVIEW"], default="ALL", help="EDA scope to run.")
    full.add_argument(
        "--skip-cross-scan-run",
        action="store_true",
        help="Skip the expensive raw cross-asset scan and use existing scan outputs.",
    )
    full.add_argument("--skip-tests", action="store_true", help="Skip pytest.")
    full.add_argument("--plots", action="store_true", help="Generate plots for the final backtest checks.")
    full.add_argument(
        "--output-root",
        default="./Output/coursework_3/stage_2_team01_v3_final/full_pipeline_backtests",
        help="Folder for final backtest checks.",
    )

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

    if args.command == "full":
        steps: list[FullStep] = []
        if not args.skip_tests:
            steps.append(("framework rule tests", [py, "-m", "pytest", "Tests"]))
        steps.extend(
            [
                (f"EDA {args.eda}", [py, "EDA/scripts/run_eda_stage4.py", args.eda]),
                ("Coursework 1 V1 archive", [py, "Scripts/coursework_1/stage_5_generate_v1_evidence_matrix.py"]),
                ("Coursework 2 V2 archive", [py, "Scripts/coursework_2/stage_4_generate_v2_evidence_summary.py"]),
            ]
        )
        if not args.skip_cross_scan_run:
            steps.append(
                (
                    "Coursework 3 raw cross-asset scan",
                    [py, "Scripts/coursework_3/stage_1_cross_asset_scan/run_cross_asset_scan.py"],
                )
            )
            steps.extend(
                [
                    (
                        "Coursework 3 cross-asset scan summary",
                        [py, "Scripts/coursework_3/stage_1_cross_asset_scan/summarize_cross_asset_scan.py"],
                    ),
                    (
                        "Coursework 3 Part 2 validation",
                        [py, "Scripts/coursework_3/stage_1_cross_asset_scan/validate_cross_asset_scan_part2.py"],
                    ),
                ]
            )
        else:
            steps.append(("Coursework 3 existing cross-asset evidence check", check_existing_cross_asset_evidence))
        steps.extend(
            [
                (
                    "Chapter 3 base analysis",
                    [py, "Scripts/coursework_3/stage_3_chapter3_evidence/generate_coursework_3_chapter3_analysis.py"],
                ),
                (
                    "Chapter 3 section 3.3.1 pack",
                    [py, "Scripts/coursework_3/stage_3_chapter3_evidence/generate_part3_331_doc_pack.py"],
                ),
                (
                    "Chapter 3 section 3.3.2 pack",
                    [py, "Scripts/coursework_3/stage_3_chapter3_evidence/generate_part3_332_doc_pack.py"],
                ),
                (
                    "Chapter 3 section 3.3.3 pack",
                    [py, "Scripts/coursework_3/stage_3_chapter3_evidence/generate_part3_333_doc_pack.py"],
                ),
                (
                    "Chapter 3 section 3.3.5 pack",
                    [py, "Scripts/coursework_3/stage_3_chapter3_evidence/generate_part3_335_doc_pack.py"],
                ),
                (
                    "Chapter 3 section 3.5 pack",
                    [py, "Scripts/coursework_3/stage_3_chapter3_evidence/generate_part3_35_v3_workflow_pack.py"],
                ),
                (
                    "Chapter 3 section 3.6 pack",
                    [py, "Scripts/coursework_3/stage_3_chapter3_evidence/generate_part3_36_comparison_pack.py"],
                ),
            ]
        )
        for part in ("PART1", "PART2", "PART3"):
            cmd = [
                py,
                "main.py",
                "--strategy",
                "coursework_3.stage_2_team01_v3_final",
                "--data-dir",
                f"./DATA/{part}",
                "--output-dir",
                f"{args.output_root}/{part.lower()}",
            ]
            if not args.plots:
                cmd.append("--no-plot")
            steps.append((f"final V3 backtest {part}", cmd))
        return run_full_pipeline(steps)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
