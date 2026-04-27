#!/usr/bin/env python3
"""Generate the Coursework 1 V1 evidence matrix across PART1, PART2, PART3, and PART123."""

import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAIN = PROJECT_ROOT / "main.py"
OUTPUT_ROOT = PROJECT_ROOT / "Output" / "coursework_1" / "stage_5_team01_v1_archive"

DATASETS = ["PART1", "PART2", "PART3", "PART123"]

STRATEGIES = [
    {
        "id": "tf_asset01_v1",
        "strategy": "coursework_1.stage_1_tf_asset01_v1",
        "params": ["data_name=series_1"],
    },
    {
        "id": "mr_asset10_v1",
        "strategy": "coursework_1.stage_2_mr_asset10_v1",
        "params": ["data_name=series_10"],
    },
    {
        "id": "garch_asset07_v1",
        "strategy": "coursework_1.stage_3_garch_asset07_v1",
        "params": ["data_name=series_7"],
    },
    {
        "id": "combo_tf01_mr10_garch07_v1",
        "strategy": "coursework_1.stage_4_initial_combo_team01_v1",
        "params": [],
    },
]

SUMMARY_FIELDS = [
    "dataset",
    "strategy_id",
    "final_value",
    "bankrupt",
    "bankrupt_date",
    "open_pnl_pd_ratio",
    "true_pd_ratio",
    "activity_pct",
    "end_policy",
    "s_mult",
    "output_dir",
]


def build_command(dataset: str, strategy_cfg: dict, with_plots: bool) -> tuple[list[str], Path]:
    output_dir = OUTPUT_ROOT / dataset / strategy_cfg["id"]
    cmd = [
        sys.executable,
        str(MAIN),
        "--strategy",
        strategy_cfg["strategy"],
        "--data-dir",
        str(PROJECT_ROOT / "DATA" / dataset),
        "--output-dir",
        str(output_dir),
    ]
    if not with_plots:
        cmd.append("--no-plot")
    for param in strategy_cfg["params"]:
        cmd.extend(["--param", param])
    return cmd, output_dir


def run_one(dataset: str, strategy_cfg: dict, with_plots: bool) -> dict:
    cmd, output_dir = build_command(dataset, strategy_cfg, with_plots)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[RUN] {dataset} / {strategy_cfg['id']}")
    env = os.environ.copy()
    env.setdefault("MPLBACKEND", "Agg")
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True, env=env)

    summary_path = output_dir / "run_summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing run summary: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    row = {
        "dataset": dataset,
        "strategy_id": strategy_cfg["id"],
        "output_dir": str(output_dir.relative_to(PROJECT_ROOT)),
    }
    row.update(summary)
    return row


def write_outputs(rows: list[dict], commands: list[list[str]]) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    csv_path = OUTPUT_ROOT / "matrix_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in SUMMARY_FIELDS})

    json_path = OUTPUT_ROOT / "matrix_summary.json"
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    manifest = {
        "branch_purpose": "Coursework 1 Stage 5 V1 evidence matrix",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "datasets": DATASETS,
        "strategies": [s["id"] for s in STRATEGIES],
        "output_root": str(OUTPUT_ROOT.relative_to(PROJECT_ROOT)),
        "commands": [" ".join(cmd) for cmd in commands],
    }
    (OUTPUT_ROOT / "archive_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"[SAVED] {csv_path}")
    print(f"[SAVED] {json_path}")
    print(f"[SAVED] {OUTPUT_ROOT / 'archive_manifest.json'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-plots",
        action="store_true",
        help="Generate PNG plots as well as JSON summaries. Default keeps the archive lightweight.",
    )
    args = parser.parse_args()

    rows = []
    commands = []
    for dataset in DATASETS:
        for strategy_cfg in STRATEGIES:
            cmd, _ = build_command(dataset, strategy_cfg, args.with_plots)
            commands.append(cmd)
            rows.append(run_one(dataset, strategy_cfg, args.with_plots))
    write_outputs(rows, commands)


if __name__ == "__main__":
    main()
