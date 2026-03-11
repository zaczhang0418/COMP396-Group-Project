#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJ = Path(__file__).resolve().parent


def run_command(cmd: list[str], step_name: str) -> None:
    print(f"\n{'=' * 20}\n[START] {step_name}\n{'=' * 20}")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(PROJ))
    print(f"[DONE] {step_name}")


def main() -> None:
    py_exec = sys.executable
    run_command([py_exec, "run_pipeline.py"], "PART1 Pipeline")
    run_command([py_exec, "scripts/evaluate_part2_from_best.py"], "PART2 Evaluation From PART1 Best Params")
    print("\n[SUCCESS] Full workflow completed.")


if __name__ == "__main__":
    main()
