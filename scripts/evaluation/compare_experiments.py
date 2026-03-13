# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Compare two experiment tags and export part1/part2 summary tables."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


PROJ = Path(__file__).resolve().parents[2]
if str(PROJ) not in sys.path:
    sys.path.insert(0, str(PROJ))

from scripts.common_paths import EXPERIMENTS_ROOT, get_stage_dir, load_json, part_root, rel_path  # noqa: E402


PART1_SPLITS = ("70-30", "30-oos", "100-full")
PART1_STRATEGIES = ("tf", "mr", "garch")
PART2_STRATEGIES = ("tf", "mr", "garch", "combo")


def read_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def latest_dir(root: Path | None, pattern: str) -> Path | None:
    if root is None or not root.exists():
        return None
    candidates = sorted(root.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def load_run_summary(run_dir: Path | None) -> dict:
    if run_dir is None:
        return {}
    return load_json(run_dir / "run_summary.json", default={})


def as_float(value) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def pct_return(final_value, starting_cash: float) -> float | None:
    value = as_float(final_value)
    if value is None:
        return None
    return (value / starting_cash - 1.0) * 100.0


def delta(new_value, old_value) -> float | None:
    a = as_float(new_value)
    b = as_float(old_value)
    if a is None or b is None:
        return None
    return a - b


def fmt_num(value, digits: int = 3) -> str:
    number = as_float(value)
    if number is None:
        return "NA"
    return f"{number:.{digits}f}"


def classify_part1(row: dict) -> str:
    oos_delta = as_float(row["delta_oos_pd"])
    full_delta = as_float(row["delta_full_pd"])
    ret_delta = as_float(row["delta_full_return_pct"])
    base_is = as_float(row["base_is_pd"])
    base_oos = as_float(row["base_oos_pd"])
    cand_is = as_float(row["candidate_is_pd"])
    cand_oos = as_float(row["candidate_oos_pd"])
    gap_base = abs(base_is - base_oos) if base_is is not None and base_oos is not None else None
    gap_cand = abs(cand_is - cand_oos) if cand_is is not None and cand_oos is not None else None

    if oos_delta is not None and full_delta is not None and ret_delta is not None:
        if oos_delta < 0 and full_delta < 0 and ret_delta < 0:
            return "全面退化"
        if oos_delta > 0 and full_delta > 0 and ret_delta > 0:
            return "整体改善"
    if gap_base is not None and gap_cand is not None and gap_cand < gap_base:
        if oos_delta is None or oos_delta >= 0:
            return "降低过拟合"
    positive_count = sum(1 for item in (oos_delta, full_delta, ret_delta) if item is not None and item > 0)
    return "整体改善" if positive_count >= 2 else "全面退化"


def classify_part2(row: dict) -> str:
    pd_delta = as_float(row["delta_full_pd"])
    ret_delta = as_float(row["delta_full_return_pct"])
    act_delta = as_float(row["delta_full_activity_pct"])

    if pd_delta is not None and ret_delta is not None:
        if pd_delta < 0 and ret_delta < 0:
            return "全面退化"
        if pd_delta > 0 and ret_delta > 0:
            return "整体改善"
    if pd_delta is not None and pd_delta >= 0 and act_delta is not None and act_delta < 0:
        return "降低过拟合"
    return "整体改善" if (pd_delta is not None and pd_delta >= 0) or (ret_delta is not None and ret_delta >= 0) else "全面退化"


def note_part1(row: dict) -> str:
    parts = [
        f"OOS PD {fmt_num(row['base_oos_pd'])} -> {fmt_num(row['candidate_oos_pd'])}",
        f"Full PD {fmt_num(row['base_full_pd'])} -> {fmt_num(row['candidate_full_pd'])}",
        f"Full Ret {fmt_num(row['base_full_return_pct'], 2)}% -> {fmt_num(row['candidate_full_return_pct'], 2)}%",
        f"Act {fmt_num(row['base_full_activity_pct'], 2)}% -> {fmt_num(row['candidate_full_activity_pct'], 2)}%",
    ]
    return "; ".join(parts)


def note_part2(row: dict) -> str:
    parts = [
        f"Full PD {fmt_num(row['base_full_pd'])} -> {fmt_num(row['candidate_full_pd'])}",
        f"Full Ret {fmt_num(row['base_full_return_pct'], 2)}% -> {fmt_num(row['candidate_full_return_pct'], 2)}%",
        f"Act {fmt_num(row['base_full_activity_pct'], 2)}% -> {fmt_num(row['candidate_full_activity_pct'], 2)}%",
    ]
    return "; ".join(parts)


def load_experiment_record(tag: str) -> dict:
    path = EXPERIMENTS_ROOT / tag / "experiment_record.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing experiment_record.json for {tag}: {path}")
    return load_json(path, default={})


def part1_best_runs_dir(tag: str, record: dict, strategy: str) -> Path | None:
    path = record.get("part1", {}).get("strategies", {}).get(strategy, {}).get("best_runs_dir")
    return PROJ / path if path else get_stage_dir(tag, "part1", strategy, "best_runs", create=False)


def part1_combo_dir(tag: str, record: dict) -> Path | None:
    path = record.get("part1", {}).get("combo", {}).get("combo_dir")
    return PROJ / path if path else get_stage_dir(tag, "part1", "combo", "combo", create=False)


def part2_summary_path(tag: str, record: dict) -> Path | None:
    path = record.get("part2", {}).get("transfer_summary")
    return PROJ / path if path else (part_root(tag, "part2", create=False) / "transfer_summary.csv")


def extract_part1_metrics(tag: str, record: dict) -> dict:
    metrics: dict[str, dict[str, dict]] = {}
    for strategy in PART1_STRATEGIES:
        best_runs = part1_best_runs_dir(tag, record, strategy)
        strategy_metrics = {}
        for split in PART1_SPLITS:
            run_dir = latest_dir(best_runs, f"run_*_{split}")
            strategy_metrics[split] = load_run_summary(run_dir)
            strategy_metrics[split]["run_dir"] = rel_path(run_dir) if run_dir else ""
        metrics[strategy] = strategy_metrics

    combo_dir = part1_combo_dir(tag, record)
    combo_run = latest_dir(combo_dir, "combined_*")
    metrics["combo"] = {"100-full": load_run_summary(combo_run)}
    metrics["combo"]["100-full"]["run_dir"] = rel_path(combo_run) if combo_run else ""
    return metrics


def extract_part2_metrics(tag: str, record: dict) -> dict:
    summary_path = part2_summary_path(tag, record)
    rows = read_csv_rows(summary_path) if summary_path else []
    return {row["strategy"]: row for row in rows}


def build_part1_rows(base_tag: str, cand_tag: str, base_metrics: dict, cand_metrics: dict, starting_cash: float) -> list[dict]:
    rows = []
    for strategy in ("tf", "mr", "garch", "combo"):
        base = base_metrics.get(strategy, {})
        cand = cand_metrics.get(strategy, {})
        row = {
            "strategy": strategy,
            "base_experiment": base_tag,
            "candidate_experiment": cand_tag,
            "base_is_pd": as_float(base.get("70-30", {}).get("true_pd_ratio")),
            "candidate_is_pd": as_float(cand.get("70-30", {}).get("true_pd_ratio")),
            "delta_is_pd": delta(cand.get("70-30", {}).get("true_pd_ratio"), base.get("70-30", {}).get("true_pd_ratio")),
            "base_oos_pd": as_float(base.get("30-oos", {}).get("true_pd_ratio")),
            "candidate_oos_pd": as_float(cand.get("30-oos", {}).get("true_pd_ratio")),
            "delta_oos_pd": delta(cand.get("30-oos", {}).get("true_pd_ratio"), base.get("30-oos", {}).get("true_pd_ratio")),
            "base_full_pd": as_float(base.get("100-full", {}).get("true_pd_ratio")),
            "candidate_full_pd": as_float(cand.get("100-full", {}).get("true_pd_ratio")),
            "delta_full_pd": delta(cand.get("100-full", {}).get("true_pd_ratio"), base.get("100-full", {}).get("true_pd_ratio")),
            "base_full_return_pct": pct_return(base.get("100-full", {}).get("final_value"), starting_cash),
            "candidate_full_return_pct": pct_return(cand.get("100-full", {}).get("final_value"), starting_cash),
            "delta_full_return_pct": delta(
                pct_return(cand.get("100-full", {}).get("final_value"), starting_cash),
                pct_return(base.get("100-full", {}).get("final_value"), starting_cash),
            ),
            "base_full_activity_pct": as_float(base.get("100-full", {}).get("activity_pct")),
            "candidate_full_activity_pct": as_float(cand.get("100-full", {}).get("activity_pct")),
            "delta_full_activity_pct": delta(
                cand.get("100-full", {}).get("activity_pct"),
                base.get("100-full", {}).get("activity_pct"),
            ),
            "base_full_run_dir": base.get("100-full", {}).get("run_dir", ""),
            "candidate_full_run_dir": cand.get("100-full", {}).get("run_dir", ""),
        }
        row["change_note"] = note_part1(row)
        row["assessment"] = classify_part1(row)
        rows.append(row)
    return rows


def build_part2_rows(base_tag: str, cand_tag: str, base_metrics: dict, cand_metrics: dict, starting_cash: float) -> list[dict]:
    rows = []
    for strategy in PART2_STRATEGIES:
        base = base_metrics.get(strategy, {})
        cand = cand_metrics.get(strategy, {})
        row = {
            "strategy": strategy,
            "base_experiment": base_tag,
            "candidate_experiment": cand_tag,
            "base_full_pd": as_float(base.get("true_pd_ratio")),
            "candidate_full_pd": as_float(cand.get("true_pd_ratio")),
            "delta_full_pd": delta(cand.get("true_pd_ratio"), base.get("true_pd_ratio")),
            "base_full_return_pct": pct_return(base.get("final_value"), starting_cash),
            "candidate_full_return_pct": pct_return(cand.get("final_value"), starting_cash),
            "delta_full_return_pct": delta(
                pct_return(cand.get("final_value"), starting_cash),
                pct_return(base.get("final_value"), starting_cash),
            ),
            "base_full_activity_pct": as_float(base.get("activity_pct")),
            "candidate_full_activity_pct": as_float(cand.get("activity_pct")),
            "delta_full_activity_pct": delta(cand.get("activity_pct"), base.get("activity_pct")),
            "base_run_dir": base.get("run_dir", ""),
            "candidate_run_dir": cand.get("run_dir", ""),
        }
        row["change_note"] = note_part2(row)
        row["assessment"] = classify_part2(row)
        rows.append(row)
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-experiment", default="pre_refine_v0")
    ap.add_argument("--candidate-experiment", default="refined_v1")
    ap.add_argument("--starting-cash", type=float, default=1_000_000.0)
    ap.add_argument("--output-dir", default=None)
    args = ap.parse_args()

    base_record = load_experiment_record(args.base_experiment)
    cand_record = load_experiment_record(args.candidate_experiment)

    part1_rows = build_part1_rows(
        args.base_experiment,
        args.candidate_experiment,
        extract_part1_metrics(args.base_experiment, base_record),
        extract_part1_metrics(args.candidate_experiment, cand_record),
        args.starting_cash,
    )
    part2_rows = build_part2_rows(
        args.base_experiment,
        args.candidate_experiment,
        extract_part2_metrics(args.base_experiment, base_record),
        extract_part2_metrics(args.candidate_experiment, cand_record),
        args.starting_cash,
    )

    output_dir = Path(args.output_dir) if args.output_dir else (EXPERIMENTS_ROOT / args.candidate_experiment / "comparisons")
    part1_path = output_dir / f"{args.base_experiment}_vs_{args.candidate_experiment}_part1.csv"
    part2_path = output_dir / f"{args.base_experiment}_vs_{args.candidate_experiment}_part2.csv"

    write_csv(part1_path, part1_rows, list(part1_rows[0].keys()) if part1_rows else [])
    write_csv(part2_path, part2_rows, list(part2_rows[0].keys()) if part2_rows else [])

    print(
        {
            "part1_compare": rel_path(part1_path),
            "part2_compare": rel_path(part2_path),
        }
    )
