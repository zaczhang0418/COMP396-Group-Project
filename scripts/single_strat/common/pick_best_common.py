#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared helpers for single-strategy parameter selection."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[3]
if str(PROJ) not in sys.path:
    sys.path.insert(0, str(PROJ))

from scripts.common_paths import load_json, rel_path  # noqa: E402


STARTING_CASH = 1_000_000.0
SPLIT_ORDER = {"is": 0, "oos": 1, "full": 2}
SPLIT_LABELS = {"is": "70-30", "oos": "30-oos", "full": "100-full"}


def resolve_path(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else PROJ / path


def to_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def load_grid_spec(path: Path) -> tuple[list[str], dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "search_params" in payload:
        search_keys = list(payload["search_params"].keys())
        fixed_params = payload.get("fixed_params", {})
    else:
        search_keys = list(payload.keys())
        fixed_params = {}
    return search_keys, fixed_params


def parse_results(path: Path) -> tuple[list[str], list[dict]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = [h.strip() for h in (reader.fieldnames or [])]
        rows = []
        for row in reader:
            if not row:
                continue
            parsed = {key.strip(): to_float(value) for key, value in row.items() if key}
            run_dir = row.get("run_dir", "")
            if run_dir:
                parsed["run_dir"] = run_dir.strip()
            rows.append(parsed)
    if not header or not rows:
        raise SystemExit(f"Empty results: {path}")
    return header, rows


def latest_run_dir(root: Path, split: str) -> Path:
    pattern = f"run_*_{split}"
    candidates = sorted(root.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No matches for {pattern} under {root}")
    return candidates[0]


def pick_metric_best(rows: list[dict], key: str) -> dict:
    return max(rows, key=lambda row: row.get(key, float("-inf")))


def candidate_params(row: dict, search_keys: list[str], fixed_params: dict) -> dict:
    params = {key: row[key] for key in search_keys}
    params.update(fixed_params)
    return params


def pct_return(final_value, starting_cash: float = STARTING_CASH) -> float:
    return (to_float(final_value) / starting_cash - 1.0) * 100.0


def score_candidate(
    metric_is: float,
    metric_oos: float,
    metric_full: float,
    bankrupt_oos: bool,
    bankrupt_full: bool,
    oos_weight: float,
    full_weight: float,
    is_weight: float,
    gap_penalty: float,
    bankrupt_penalty: float,
) -> float:
    gap = abs(metric_is - metric_oos)
    bankrupt_hits = int(bankrupt_oos) + int(bankrupt_full)
    return (
        oos_weight * metric_oos
        + full_weight * metric_full
        + is_weight * metric_is
        - gap_penalty * gap
        - bankrupt_penalty * bankrupt_hits
    )


def run_split_eval(
    runner: Path,
    params_path: Path,
    split_name: str,
    timeline: dict,
    tag: str,
    data_dir: Path,
    output_root: Path,
) -> tuple[Path, dict]:
    split_label = SPLIT_LABELS[split_name]
    split_cfg = timeline[split_name]
    cmd = [
        sys.executable,
        str(runner),
        "--start",
        split_cfg["start"],
        "--end",
        split_cfg["end"],
        "--params",
        str(params_path),
        "--split",
        split_label,
        "--tag",
        tag,
        "--data-dir",
        str(data_dir),
        "--output-root",
        str(output_root),
    ]
    subprocess.run(cmd, check=True, cwd=str(PROJ))
    run_dir = latest_run_dir(output_root, split_label)
    return run_dir, load_json(run_dir / "run_summary.json", default={})


def write_ranking_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def robust_select(
    *,
    rows: list[dict],
    key: str,
    top_k: int,
    search_keys: list[str],
    fixed_params: dict,
    out_root: Path,
    best_out: Path,
    robust_dir: Path,
    runner: Path,
    timeline: dict,
    data_dir: Path,
    experiment_tag: str,
    strategy_key: str,
    oos_weight: float,
    full_weight: float,
    is_weight: float,
    gap_penalty: float,
    bankrupt_penalty: float,
) -> dict:
    ranked_is = sorted(rows, key=lambda row: row.get(key, float("-inf")), reverse=True)
    shortlist = ranked_is[: max(1, min(int(top_k), len(ranked_is)))]
    robust_dir.mkdir(parents=True, exist_ok=True)

    ranking_rows = []
    for idx, row in enumerate(shortlist, 1):
        params = candidate_params(row, search_keys, fixed_params)
        candidate_root = robust_dir / f"candidate_{idx:02d}"
        candidate_root.mkdir(parents=True, exist_ok=True)
        params_path = candidate_root / "params.json"
        params_path.write_text(json.dumps(params, indent=2), encoding="utf-8")

        oos_dir, oos_summary = run_split_eval(
            runner=runner,
            params_path=params_path,
            split_name="oos",
            timeline=timeline,
            tag=f"{experiment_tag}_{strategy_key}_robust_{idx:02d}",
            data_dir=data_dir,
            output_root=candidate_root / "oos",
        )
        full_dir, full_summary = run_split_eval(
            runner=runner,
            params_path=params_path,
            split_name="full",
            timeline=timeline,
            tag=f"{experiment_tag}_{strategy_key}_robust_{idx:02d}",
            data_dir=data_dir,
            output_root=candidate_root / "full",
        )

        metric_is = to_float(row.get(key))
        metric_oos = to_float(oos_summary.get(key))
        metric_full = to_float(full_summary.get(key))
        robust_score = score_candidate(
            metric_is=metric_is,
            metric_oos=metric_oos,
            metric_full=metric_full,
            bankrupt_oos=bool(oos_summary.get("bankrupt", False)),
            bankrupt_full=bool(full_summary.get("bankrupt", False)),
            oos_weight=oos_weight,
            full_weight=full_weight,
            is_weight=is_weight,
            gap_penalty=gap_penalty,
            bankrupt_penalty=bankrupt_penalty,
        )

        ranking_row = {
            "candidate_rank_is": idx,
            "robust_score": robust_score,
            "metric_key": key,
            "is_metric": metric_is,
            "oos_metric": metric_oos,
            "full_metric": metric_full,
            "is_oos_gap": abs(metric_is - metric_oos),
            "oos_activity_pct": to_float(oos_summary.get("activity_pct")),
            "full_activity_pct": to_float(full_summary.get("activity_pct")),
            "oos_return_pct": pct_return(oos_summary.get("final_value")),
            "full_return_pct": pct_return(full_summary.get("final_value")),
            "oos_bankrupt": int(bool(oos_summary.get("bankrupt", False))),
            "full_bankrupt": int(bool(full_summary.get("bankrupt", False))),
            "oos_run_dir": rel_path(oos_dir),
            "full_run_dir": rel_path(full_dir),
            "params_path": rel_path(params_path),
        }
        for search_key in search_keys:
            ranking_row[search_key] = row.get(search_key)
        ranking_rows.append(ranking_row)

    ranking_rows.sort(key=lambda item: item["robust_score"], reverse=True)
    for final_rank, item in enumerate(ranking_rows, 1):
        item["candidate_rank_final"] = final_rank

    fieldnames = (
        ["candidate_rank_final", "candidate_rank_is", "robust_score", "metric_key", "is_metric", "oos_metric", "full_metric",
         "is_oos_gap", "oos_activity_pct", "full_activity_pct", "oos_return_pct", "full_return_pct",
         "oos_bankrupt", "full_bankrupt", "oos_run_dir", "full_run_dir", "params_path"]
        + search_keys
    )
    ranking_path = robust_dir / "robust_ranking.csv"
    write_ranking_csv(ranking_path, fieldnames, ranking_rows)

    best = ranking_rows[0]
    best_params = json.loads((PROJ / best["params_path"]).read_text(encoding="utf-8"))
    best_out.write_text(json.dumps(best_params, indent=2), encoding="utf-8")

    return {
        "best_params": best_params,
        "ranking_path": ranking_path,
        "ranking_rows": ranking_rows,
        "best_record": best,
    }
