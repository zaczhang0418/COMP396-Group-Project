#!/usr/bin/env python3
"""Generate the Coursework 2 V2 evidence summary.

This script reads only Output/coursework_2/stage_4_team01_v2_archive. It does not rely
on older raw output folders.
"""

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "Output" / "coursework_2" / "stage_4_team01_v2_archive"

GENERIC_SINGLE_RUNS = [
    (
        "coursework2_stage1_generic",
        "part1_full_generic_single",
        "part1",
        "tf",
        "01",
        DEFAULT_OUTPUT_ROOT / "generic_single_strats_output" / "part1_full" / "tf_generic_v1",
    ),
    (
        "coursework2_stage1_generic",
        "part1_full_generic_single",
        "part1",
        "mr",
        "10",
        DEFAULT_OUTPUT_ROOT / "generic_single_strats_output" / "part1_full" / "mr_generic_v1",
    ),
    (
        "coursework2_stage1_generic",
        "part1_full_generic_single",
        "part1",
        "garch",
        "07",
        DEFAULT_OUTPUT_ROOT / "generic_single_strats_output" / "part1_full" / "garch_generic_v1",
    ),
    (
        "coursework2_stage1_generic",
        "part2_transfer_generic_single",
        "part2",
        "tf",
        "01",
        DEFAULT_OUTPUT_ROOT / "generic_single_strats_output" / "part2_transfer" / "tf_generic_v1",
    ),
    (
        "coursework2_stage1_generic",
        "part2_transfer_generic_single",
        "part2",
        "mr",
        "10",
        DEFAULT_OUTPUT_ROOT / "generic_single_strats_output" / "part2_transfer" / "mr_generic_v1",
    ),
    (
        "coursework2_stage1_generic",
        "part2_transfer_generic_single",
        "part2",
        "garch",
        "07",
        DEFAULT_OUTPUT_ROOT / "generic_single_strats_output" / "part2_transfer" / "garch_generic_v1",
    ),
]

TEAM01_RUNS = [
    (
        "coursework2_stage2_presubmission",
        "team01_presubmission",
        "part1",
        "team01",
        "01+07+10",
        DEFAULT_OUTPUT_ROOT / "team01_presubmission" / "part1",
    ),
    (
        "coursework2_stage2_presubmission",
        "team01_presubmission",
        "part2",
        "team01",
        "01+07+10",
        DEFAULT_OUTPUT_ROOT / "team01_presubmission" / "part2",
    ),
    (
        "coursework2_stage2_presubmission_preserved",
        "team01_presubmission",
        "part3_existing",
        "team01",
        "01+07+10",
        DEFAULT_OUTPUT_ROOT / "team01_presubmission" / "part3_existing",
    ),
]

SUMMARY_FIELDS = [
    "workflow_stage",
    "evidence_type",
    "dataset",
    "strategy",
    "asset",
    "final_value",
    "true_pd_ratio",
    "open_pnl_pd_ratio",
    "activity_pct",
    "bankrupt",
    "source_path",
]

LEG_FIELDS = [
    "workflow_stage",
    "dataset",
    "series",
    "leg",
    "final_cumPnL",
    "pnl_pd_ratio",
    "max_drawdown",
    "source_path",
]

LEG_MAP = {
    "series_1": "tf",
    "series_7": "garch",
    "series_10": "mr",
    "portfolio": "portfolio",
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict | list:
    if not path.exists():
        raise FileNotFoundError(f"Missing required archive file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def as_bool_text(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value).strip()
    if text.lower() in {"false", "0", "no", ""}:
        return "false"
    if text.lower() in {"true", "1", "yes"}:
        return "true"
    return text


def add_run_rows(rows: list[dict], runs: list[tuple[str, str, str, str, str, Path]]) -> None:
    for workflow_stage, evidence_type, dataset, strategy, asset, run_dir in runs:
        summary_path = run_dir / "run_summary.json"
        summary = read_json(summary_path)
        rows.append(
            {
                "workflow_stage": workflow_stage,
                "evidence_type": evidence_type,
                "dataset": dataset,
                "strategy": strategy,
                "asset": asset,
                "final_value": summary.get("final_value"),
                "true_pd_ratio": summary.get("true_pd_ratio"),
                "open_pnl_pd_ratio": summary.get("open_pnl_pd_ratio"),
                "activity_pct": summary.get("activity_pct"),
                "bankrupt": as_bool_text(summary.get("bankrupt")),
                "source_path": rel(summary_path),
            }
        )


def add_team01_leg_rows(leg_rows: list[dict]) -> None:
    for workflow_stage, _evidence_type, dataset, _strategy, _asset, run_dir in TEAM01_RUNS:
        per_series_path = run_dir / "per_series_pd.json"
        if not per_series_path.exists():
            continue
        for item in read_json(per_series_path):
            series = item.get("series")
            if series not in LEG_MAP:
                continue
            leg_rows.append(
                {
                    "workflow_stage": workflow_stage,
                    "dataset": dataset,
                    "series": series,
                    "leg": LEG_MAP.get(series, ""),
                    "final_cumPnL": item.get("final_cumPnL"),
                    "pnl_pd_ratio": item.get("pnl_pd_ratio"),
                    "max_drawdown": item.get("max_drawdown"),
                    "source_path": rel(per_series_path),
                }
            )


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def write_outputs(output_root: Path, rows: list[dict], leg_rows: list[dict]) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    write_csv(output_root / "process_summary.csv", rows, SUMMARY_FIELDS)
    write_csv(output_root / "per_leg_summary.csv", leg_rows, LEG_FIELDS)

    manifest = {
        "branch_purpose": "Coursework 2 Stage 4 V2 evidence summary",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_branches": [
            "archive/coursework_2/stage-2-generic-single-strats",
            "archive/coursework_2/stage-3-presubmission-team01",
        ],
        "summary_rows": len(rows),
        "per_leg_rows": len(leg_rows),
        "output_root": rel(output_root),
        "asset_bound_grid_search_run_summaries": rel(output_root / "asset_bound_grid_search_run_summaries"),
        "parameter_selection_candidates": rel(output_root / "parameter_selection_candidates"),
        "generic_single_strats_output": rel(output_root / "generic_single_strats_output"),
        "note": "Summarizes normalized Coursework 2 archive evidence; does not rerun grid searches.",
    }
    (output_root / "archive_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Directory for concise archive summary outputs.",
    )
    args = parser.parse_args()
    output_root = Path(args.output_root)

    rows: list[dict] = []
    leg_rows: list[dict] = []
    add_run_rows(rows, GENERIC_SINGLE_RUNS)
    add_run_rows(rows, TEAM01_RUNS)
    add_team01_leg_rows(leg_rows)
    write_outputs(output_root, rows, leg_rows)

    print(f"[SAVED] {output_root / 'process_summary.csv'}")
    print(f"[SAVED] {output_root / 'per_leg_summary.csv'}")
    print(f"[SAVED] {output_root / 'archive_manifest.json'}")


if __name__ == "__main__":
    main()
