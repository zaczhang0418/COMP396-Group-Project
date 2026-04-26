from __future__ import annotations

import csv
import io
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output" / "coursework_3_stage2_v3_archive" / "chapter3_analysis"

REFS = {
    "v1": "summary/coursework_1/stage-5-v1-archive-summary",
    "v2": "summary/coursework_2/stage-4-v2-archive-summary",
    "v3": "summary/coursework_3/stage-2-v3-archive-summary",
}

PATHS = {
    "v1_matrix_summary": "output/coursework_1_stage5_v1_archive/matrix_summary.csv",
    "v1_part3_per_series": "output/coursework_1_stage5_v1_archive/PART3/combo_tf01_mr10_garch07_v1/per_series_pd.json",
    "v2_process_summary": "output/coursework_2_stage4_v2_archive/process_summary.csv",
    "v2_per_leg_summary": "output/coursework_2_stage4_v2_archive/per_leg_summary.csv",
    "v3_process_summary": "output/coursework_3_stage2_v3_archive/process_summary.csv",
    "v3_part1_per_series": "output/coursework_3_stage2_v3_archive/team01_v3_final/part1/per_series_pd.json",
    "v3_part2_per_series": "output/coursework_3_stage2_v3_archive/team01_v3_final/part2/per_series_pd.json",
    "v3_part3_per_series": "output/coursework_3_stage2_v3_archive/team01_v3_final/part3/per_series_pd.json",
    "v3_cross_asset_long": "output/cross_asset_scan_v1/summaries/cross_asset_long.csv",
}

SERIES_TO_LEG = {
    "series_1": "tf",
    "series_7": "garch",
    "series_9": "mr09",
    "series_10": "mr",
}


def git_show_text(ref: str, repo_path: str) -> str:
    completed = subprocess.run(
        ["git", "show", f"{ref}:{repo_path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.lstrip("\ufeff")


def read_git_csv(ref: str, repo_path: str) -> list[dict[str, str]]:
    text = git_show_text(ref, repo_path)
    return list(csv.DictReader(io.StringIO(text)))


def read_git_json(ref: str, repo_path: str):
    return json.loads(git_show_text(ref, repo_path))


def to_float(value):
    if value in ("", None):
        return None
    return float(value)


def to_bool(value):
    if isinstance(value, bool):
        return value
    if value in ("", None):
        return None
    return str(value).strip().lower() == "true"


def fmt(value, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def fmt_money(value) -> str:
    if value is None:
        return "n/a"
    return f"{value:,.2f}"


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_v1_progression_rows() -> list[dict]:
    rows = []
    matrix_rows = read_git_csv(REFS["v1"], PATHS["v1_matrix_summary"])
    for row in matrix_rows:
        if row["strategy_id"] != "combo_tf01_mr10_garch07_v1" or row["dataset"] not in {"PART1", "PART2", "PART3"}:
            continue
        rows.append(
            {
                "version": "V1",
                "version_role": "asset-specific prototype",
                "dataset_key": row["dataset"].lower(),
                "dataset_label": row["dataset"],
                "final_value": float(row["final_value"]),
                "true_pd_ratio": float(row["true_pd_ratio"]),
                "open_pnl_pd_ratio": float(row["open_pnl_pd_ratio"]),
                "activity_pct": float(row["activity_pct"]),
                "bankrupt": to_bool(row["bankrupt"]),
                "source_ref": REFS["v1"],
                "source_path": PATHS["v1_matrix_summary"],
            }
        )
    return rows


def load_v2_progression_rows() -> list[dict]:
    rows = []
    process_rows = read_git_csv(REFS["v2"], PATHS["v2_process_summary"])
    for row in process_rows:
        if row["strategy"] != "team01":
            continue
        dataset = row["dataset"]
        dataset_key = "part3" if dataset == "part3_existing" else dataset
        rows.append(
            {
                "version": "V2",
                "version_role": "submitted baseline",
                "dataset_key": dataset_key,
                "dataset_label": dataset,
                "final_value": float(row["final_value"]),
                "true_pd_ratio": float(row["true_pd_ratio"]),
                "open_pnl_pd_ratio": float(row["open_pnl_pd_ratio"]),
                "activity_pct": float(row["activity_pct"]),
                "bankrupt": to_bool(row["bankrupt"]),
                "source_ref": REFS["v2"],
                "source_path": row["source_path"].replace("\\", "/"),
            }
        )
    return rows


def load_v3_progression_rows() -> list[dict]:
    rows = []
    process_rows = read_git_csv(REFS["v3"], PATHS["v3_process_summary"])
    for row in process_rows:
        rows.append(
            {
                "version": "V3",
                "version_role": "CA3 refinement",
                "dataset_key": row["dataset"],
                "dataset_label": row["dataset"],
                "final_value": float(row["final_value"]),
                "true_pd_ratio": float(row["true_pd_ratio"]),
                "open_pnl_pd_ratio": float(row["open_pnl_pd_ratio"]),
                "activity_pct": float(row["activity_pct"]),
                "bankrupt": to_bool(row["bankrupt"]),
                "source_ref": REFS["v3"],
                "source_path": row["output_path"].replace("\\", "/"),
            }
        )
    return rows


def normalize_leg_rows(version: str, dataset_label: str, payload: list[dict], source_ref: str, source_path: str) -> list[dict]:
    leg_rows = []
    raw_leg_rows = []
    for item in payload:
        series = item["series"]
        if series == "portfolio":
            continue
        final_cum_pnl = to_float(item.get("final_cumPnL"))
        pnl_pd_ratio = to_float(item.get("pnl_pd_ratio"))
        max_drawdown = to_float(item.get("max_drawdown"))
        if (final_cum_pnl or 0.0) == 0.0 and pnl_pd_ratio is None and (max_drawdown or 0.0) == 0.0:
            continue
        raw_leg_rows.append(
            {
                "version": version,
                "dataset_label": dataset_label,
                "series": series,
                "leg": SERIES_TO_LEG.get(series, "other"),
                "final_cumPnL": final_cum_pnl,
                "pnl_pd_ratio": pnl_pd_ratio,
                "max_drawdown": max_drawdown,
                "source_ref": source_ref,
                "source_path": source_path,
            }
        )

    total_abs_pnl = sum(abs(row["final_cumPnL"] or 0.0) for row in raw_leg_rows) or 1.0
    for row in raw_leg_rows:
        row["share_of_abs_leg_pnl_pct"] = 100.0 * abs(row["final_cumPnL"] or 0.0) / total_abs_pnl
        row["is_positive_pnl"] = (row["final_cumPnL"] or 0.0) > 0.0
        leg_rows.append(row)
    return leg_rows


def load_part3_leg_rows() -> list[dict]:
    rows = []

    v1_payload = read_git_json(REFS["v1"], PATHS["v1_part3_per_series"])
    rows.extend(
        normalize_leg_rows(
            version="V1",
            dataset_label="PART3",
            payload=v1_payload,
            source_ref=REFS["v1"],
            source_path=PATHS["v1_part3_per_series"],
        )
    )

    v2_rows = read_git_csv(REFS["v2"], PATHS["v2_per_leg_summary"])
    v2_payload = []
    for row in v2_rows:
        if row["dataset"] != "part3_existing" or row["series"] == "portfolio":
            continue
        v2_payload.append(
            {
                "series": row["series"],
                "pnl_pd_ratio": row["pnl_pd_ratio"],
                "final_cumPnL": row["final_cumPnL"],
                "max_drawdown": row["max_drawdown"],
            }
        )
    rows.extend(
        normalize_leg_rows(
            version="V2",
            dataset_label="part3_existing",
            payload=v2_payload,
            source_ref=REFS["v2"],
            source_path=PATHS["v2_per_leg_summary"],
        )
    )

    v3_payload = read_git_json(REFS["v3"], PATHS["v3_part3_per_series"])
    rows.extend(
        normalize_leg_rows(
            version="V3",
            dataset_label="part3",
            payload=v3_payload,
            source_ref=REFS["v3"],
            source_path=PATHS["v3_part3_per_series"],
        )
    )
    return rows


def build_part3_concentration_summary(part3_leg_rows: list[dict], progression_rows: list[dict]) -> list[dict]:
    portfolio_by_version = {
        row["version"]: row for row in progression_rows if row["dataset_key"] == "part3"
    }
    rows = []
    for version in ("V1", "V2", "V3"):
        version_rows = [row for row in part3_leg_rows if row["version"] == version]
        top_row = max(version_rows, key=lambda row: row["share_of_abs_leg_pnl_pct"])
        rows.append(
            {
                "version": version,
                "active_leg_count": len(version_rows),
                "active_series": ", ".join(row["series"] for row in version_rows),
                "top_leg": top_row["leg"],
                "top_series": top_row["series"],
                "top_leg_abs_pnl_share_pct": top_row["share_of_abs_leg_pnl_pct"],
                "portfolio_true_pd_ratio": portfolio_by_version[version]["true_pd_ratio"],
                "portfolio_open_pnl_pd_ratio": portfolio_by_version[version]["open_pnl_pd_ratio"],
                "portfolio_activity_pct": portfolio_by_version[version]["activity_pct"],
            }
        )
    return rows


def build_part3_version_comparison(progression_rows: list[dict]) -> list[dict]:
    by_version = {row["version"]: row for row in progression_rows if row["dataset_key"] == "part3"}
    baseline = by_version["V2"]
    rows = []
    for version in ("V1", "V2", "V3"):
        row = dict(by_version[version])
        row["delta_final_value_vs_v2"] = row["final_value"] - baseline["final_value"]
        row["delta_true_pd_ratio_vs_v2"] = row["true_pd_ratio"] - baseline["true_pd_ratio"]
        row["delta_open_pnl_pd_ratio_vs_v2"] = row["open_pnl_pd_ratio"] - baseline["open_pnl_pd_ratio"]
        row["delta_activity_pct_vs_v2"] = row["activity_pct"] - baseline["activity_pct"]
        rows.append(row)
    return rows


def build_asset_reassignment_evidence() -> list[dict]:
    cross_asset_rows = read_git_csv(REFS["v3"], PATHS["v3_cross_asset_long"])

    by_pair = {(row["strategy"], row["asset"]): row for row in cross_asset_rows}
    family_ranks = {}
    for family in ("tf", "mr", "garch"):
        family_rows = [row for row in cross_asset_rows if row["strategy"] == family]
        family_rows.sort(key=lambda row: to_float(row["oos_true_pd_ratio"]) or float("-inf"), reverse=True)
        family_ranks[family] = {
            (row["strategy"], row["asset"]): rank
            for rank, row in enumerate(family_rows, start=1)
        }

    requested_rows = [
        ("tf", "01", "selected in V2 and V3"),
        ("mr", "10", "selected in V2 only"),
        ("mr", "09", "selected in V3 only"),
        ("mr", "06", "highest OOS MR candidate but weak Part 2 transfer"),
        ("garch", "07", "selected in V2 only"),
        ("garch", "05", "highest OOS GARCH candidate but weak Part 2 transfer"),
        ("garch", "09", "positive Part 2 GARCH alternative but not deployed"),
    ]

    rows = []
    for family, asset, context in requested_rows:
        raw = by_pair[(family, asset)]
        oos_true_pd = to_float(raw["oos_true_pd_ratio"])
        part2_true_pd = to_float(raw["part2_true_pd_ratio"])
        rows.append(
            {
                "strategy_family": family,
                "asset": asset,
                "asset_tag": raw["asset_tag"],
                "data_name": raw["data_name"],
                "selection_context": context,
                "family_oos_rank": family_ranks[family][(family, asset)],
                "oos_true_pd_ratio": oos_true_pd,
                "full_true_pd_ratio": to_float(raw["full_true_pd_ratio"]),
                "part2_true_pd_ratio": part2_true_pd,
                "part2_return_pct": to_float(raw["part2_return_pct"]),
                "oos_to_part2_true_pd_delta": (part2_true_pd - oos_true_pd) if (oos_true_pd is not None and part2_true_pd is not None) else None,
                "part2_bankrupt": to_bool(raw["part2_bankrupt"]),
                "source_ref": REFS["v3"],
                "source_path": PATHS["v3_cross_asset_long"],
            }
        )
    return rows


def build_structure_controls_comparison() -> list[dict]:
    return [
        {
            "version": "V1",
            "version_role": "asset-specific prototype",
            "deployed_legs": 3,
            "mapping": "TF series_1 + MR series_10 + GARCH series_7",
            "base_weights": "1/3, 1/3, 1/3",
            "dynamic_allocation": "no",
            "performance_feedback": "no",
            "loss_freeze": "no",
            "gross_cap": "n/a",
            "rebalance_threshold": "n/a",
            "notable_controls_or_params": "autoload_best single-leg params inside fixed combo",
            "source_ref": REFS["v1"],
            "source_path": "strategies/combo_tf01_mr10_garch07_v1.py",
        },
        {
            "version": "V2",
            "version_role": "submitted baseline",
            "deployed_legs": 3,
            "mapping": "TF series_1 + MR series_10 + GARCH series_7",
            "base_weights": "w_tf=0.45, w_mr=0.45, w_ga=0.10",
            "dynamic_allocation": "no",
            "performance_feedback": "no",
            "loss_freeze": "no",
            "gross_cap": "implicit only through leg vol targets",
            "rebalance_threshold": "always target leg-level vol weights",
            "notable_controls_or_params": "static asset binding, static weights, vol-targeted legs",
            "source_ref": REFS["v2"],
            "source_path": "strategies/team01.py",
        },
        {
            "version": "V3",
            "version_role": "CA3 refinement",
            "deployed_legs": 2,
            "mapping": "TF series_1 + MR series_9",
            "base_weights": "w_tf=0.65, w_mr09=0.35",
            "dynamic_allocation": "yes: dynamic_alloc_enabled, tf/mr weight floors and caps",
            "performance_feedback": "yes: perf_alloc_enabled with floor/cap multipliers",
            "loss_freeze": "yes: 3 losses trigger 12-bar freeze",
            "gross_cap": "1.00",
            "rebalance_threshold": "0.015",
            "notable_controls_or_params": "MR09 z-score + ATR percentile filter; gross cap; rebalance tolerance",
            "source_ref": REFS["v3"],
            "source_path": "strategies/team01.py",
        },
    ]


def build_portfolio_progression_rows() -> list[dict]:
    rows = []
    rows.extend(load_v1_progression_rows())
    rows.extend(load_v2_progression_rows())
    rows.extend(load_v3_progression_rows())
    order = {"V1": 1, "V2": 2, "V3": 3}
    dataset_order = {"part1": 1, "part2": 2, "part3": 3}
    rows.sort(key=lambda row: (order[row["version"]], dataset_order[row["dataset_key"]]))
    return rows


def build_markdown_summary(
    progression_rows: list[dict],
    part3_version_rows: list[dict],
    concentration_rows: list[dict],
    asset_rows: list[dict],
) -> str:
    by_version_part3 = {row["version"]: row for row in part3_version_rows}
    v1 = by_version_part3["V1"]
    v2 = by_version_part3["V2"]
    v3 = by_version_part3["V3"]

    progression_lookup = {(row["version"], row["dataset_key"]): row for row in progression_rows}
    v2_part1 = progression_lookup[("V2", "part1")]
    v2_part2 = progression_lookup[("V2", "part2")]
    v3_part1 = progression_lookup[("V3", "part1")]
    v3_part2 = progression_lookup[("V3", "part2")]

    conc_v2 = next(row for row in concentration_rows if row["version"] == "V2")
    conc_v3 = next(row for row in concentration_rows if row["version"] == "V3")

    mr10 = next(row for row in asset_rows if row["strategy_family"] == "mr" and row["asset"] == "10")
    mr09 = next(row for row in asset_rows if row["strategy_family"] == "mr" and row["asset"] == "09")
    mr06 = next(row for row in asset_rows if row["strategy_family"] == "mr" and row["asset"] == "06")
    garch07 = next(row for row in asset_rows if row["strategy_family"] == "garch" and row["asset"] == "07")
    garch05 = next(row for row in asset_rows if row["strategy_family"] == "garch" and row["asset"] == "05")

    lines = [
        "# Coursework 3 Chapter 3 Analysis Pack",
        "",
        "This folder was generated from the archived summary branches for Coursework 1, 2, and 3. It is designed to give Chapter 3 stronger evidence than a single `run_summary.json`.",
        "",
        "## Files",
        "",
        "- `portfolio_progression_v1_v2_v3.csv`: portfolio-level path from Part 1 to Part 3 for V1, V2, and V3.",
        "- `part3_version_comparison.csv`: direct Part 3 comparison across V1, V2, and V3.",
        "- `part3_leg_breakdown_v1_v2_v3.csv`: Part 3 leg-level contribution and drawdown evidence.",
        "- `part3_concentration_summary.csv`: concentration and activity summary for Part 3.",
        "- `asset_reassignment_evidence.csv`: cross-asset evidence for why CA3 moved away from fixed V2 bindings.",
        "- `structure_controls_comparison.csv`: structural and risk-control differences across V1, V2, and V3.",
        "",
        "## Section Mapping",
        "",
        "### 3.2 Team01 V2 Performance on Part 3",
        "",
        f"- `part3_version_comparison.csv` shows that submitted V2 ended Part 3 at GBP {fmt_money(v2['final_value'])}, below V1's GBP {fmt_money(v1['final_value'])}, with a weaker true PD ratio ({fmt(v2['true_pd_ratio'])} vs {fmt(v1['true_pd_ratio'])}).",
        f"- `portfolio_progression_v1_v2_v3.csv` also shows the V2 path across datasets: true PD moved from {fmt(v2_part1['true_pd_ratio'])} in Part 1 to {fmt(v2_part2['true_pd_ratio'])} in Part 2, then to {fmt(v2['true_pd_ratio'])} in Part 3, so the submitted strategy improved after Part 1 but did not become uniformly strong.",
        "",
        "### 3.3 Limitations Identified in Team01 V2",
        "",
        f"- `part3_leg_breakdown_v1_v2_v3.csv` and `part3_concentration_summary.csv` show that V2 Part 3 was mainly carried by `{conc_v2['top_series']}` (`{conc_v2['top_leg']}`), which contributed {fmt(conc_v2['top_leg_abs_pnl_share_pct'], 2)}% of absolute leg PnL.",
        f"- `asset_reassignment_evidence.csv` shows why fixed asset binding remained a problem in V2: MR10 had OOS true PD {fmt(mr10['oos_true_pd_ratio'])} and Part 2 true PD {fmt(mr10['part2_true_pd_ratio'])}, while GARCH07 had OOS true PD {fmt(garch07['oos_true_pd_ratio'])} and Part 2 true PD {fmt(garch07['part2_true_pd_ratio'])}.",
        f"- The same file also shows why pure OOS optimisation was not enough: MR06 had the highest MR OOS true PD at {fmt(mr06['oos_true_pd_ratio'])}, but its Part 2 true PD dropped to {fmt(mr06['part2_true_pd_ratio'])}; GARCH05 had OOS true PD {fmt(garch05['oos_true_pd_ratio'])}, but Part 2 true PD {fmt(garch05['part2_true_pd_ratio'])}.",
        "",
        "### 3.4 Lessons from Team01 V2 Evaluation",
        "",
        "- `portfolio_progression_v1_v2_v3.csv` supports the point that transferability matters more than isolated in-sample strength.",
        "- `asset_reassignment_evidence.csv` can be cited to show that cross-asset reassessment was necessary because high OOS rows did not always survive Part 2 validation.",
        "",
        "### 3.5 Team01 V3 Performance on Part 3",
        "",
        f"- `part3_version_comparison.csv` shows that V3 finished Part 3 at GBP {fmt_money(v3['final_value'])}, with true PD {fmt(v3['true_pd_ratio'])} and activity {fmt(v3['activity_pct'], 2)}%.",
        f"- Relative to V2, V3 improved final value by GBP {fmt_money(v3['delta_final_value_vs_v2'])}, improved true PD by {fmt(v3['delta_true_pd_ratio_vs_v2'])}, and reduced activity by {fmt(v3['delta_activity_pct_vs_v2'], 2)} percentage points.",
        f"- `portfolio_progression_v1_v2_v3.csv` also shows the CA3 pattern clearly: V3 stayed weak in Part 1 ({fmt(v3_part1['true_pd_ratio'])}), then improved in Part 2 ({fmt(v3_part2['true_pd_ratio'])}), and became strongest in Part 3 ({fmt(v3['true_pd_ratio'])}).",
        "",
        "### 3.6 Key Changes Introduced in Team01 V3",
        "",
        f"- `asset_reassignment_evidence.csv` shows that MR09, chosen in V3, had better OOS/FULL evidence than MR10 ({fmt(mr09['oos_true_pd_ratio'])} / {fmt(mr09['full_true_pd_ratio'])} vs {fmt(mr10['oos_true_pd_ratio'])} / {fmt(mr10['full_true_pd_ratio'])}).",
        "- `structure_controls_comparison.csv` documents the move from static three-leg weights in V2 to dynamic two-leg allocation in V3, including performance-aware budgeting, loss freezes, gross exposure cap, and rebalance tolerance.",
        "",
        "### 3.7 Overall Lessons from Part 3",
        "",
        f"- `part3_concentration_summary.csv` shows that V3 was stronger than V2, but it was still TF-led: `{conc_v3['top_series']}` accounted for {fmt(conc_v3['top_leg_abs_pnl_share_pct'], 2)}% of absolute leg PnL.",
        "- This means the Chapter 3 conclusion can stay balanced: CA3 improved risk-adjusted performance and control quality, but the final strategy was still not evenly supported by every leg.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    progression_rows = build_portfolio_progression_rows()
    part3_version_rows = build_part3_version_comparison(progression_rows)
    part3_leg_rows = load_part3_leg_rows()
    concentration_rows = build_part3_concentration_summary(part3_leg_rows, progression_rows)
    asset_rows = build_asset_reassignment_evidence()
    structure_rows = build_structure_controls_comparison()

    progression_fields = [
        "version",
        "version_role",
        "dataset_key",
        "dataset_label",
        "final_value",
        "true_pd_ratio",
        "open_pnl_pd_ratio",
        "activity_pct",
        "bankrupt",
        "source_ref",
        "source_path",
    ]
    write_csv(OUT_DIR / "portfolio_progression_v1_v2_v3.csv", progression_rows, progression_fields)

    part3_version_fields = progression_fields + [
        "delta_final_value_vs_v2",
        "delta_true_pd_ratio_vs_v2",
        "delta_open_pnl_pd_ratio_vs_v2",
        "delta_activity_pct_vs_v2",
    ]
    write_csv(OUT_DIR / "part3_version_comparison.csv", part3_version_rows, part3_version_fields)

    part3_leg_fields = [
        "version",
        "dataset_label",
        "series",
        "leg",
        "final_cumPnL",
        "pnl_pd_ratio",
        "max_drawdown",
        "share_of_abs_leg_pnl_pct",
        "is_positive_pnl",
        "source_ref",
        "source_path",
    ]
    write_csv(OUT_DIR / "part3_leg_breakdown_v1_v2_v3.csv", part3_leg_rows, part3_leg_fields)

    concentration_fields = [
        "version",
        "active_leg_count",
        "active_series",
        "top_leg",
        "top_series",
        "top_leg_abs_pnl_share_pct",
        "portfolio_true_pd_ratio",
        "portfolio_open_pnl_pd_ratio",
        "portfolio_activity_pct",
    ]
    write_csv(OUT_DIR / "part3_concentration_summary.csv", concentration_rows, concentration_fields)

    asset_fields = [
        "strategy_family",
        "asset",
        "asset_tag",
        "data_name",
        "selection_context",
        "family_oos_rank",
        "oos_true_pd_ratio",
        "full_true_pd_ratio",
        "part2_true_pd_ratio",
        "part2_return_pct",
        "oos_to_part2_true_pd_delta",
        "part2_bankrupt",
        "source_ref",
        "source_path",
    ]
    write_csv(OUT_DIR / "asset_reassignment_evidence.csv", asset_rows, asset_fields)

    structure_fields = [
        "version",
        "version_role",
        "deployed_legs",
        "mapping",
        "base_weights",
        "dynamic_allocation",
        "performance_feedback",
        "loss_freeze",
        "gross_cap",
        "rebalance_threshold",
        "notable_controls_or_params",
        "source_ref",
        "source_path",
    ]
    write_csv(OUT_DIR / "structure_controls_comparison.csv", structure_rows, structure_fields)

    markdown = build_markdown_summary(
        progression_rows=progression_rows,
        part3_version_rows=part3_version_rows,
        concentration_rows=concentration_rows,
        asset_rows=asset_rows,
    )
    write_text(OUT_DIR / "chapter3_analysis_summary.md", markdown)

    print(f"Wrote Chapter 3 analysis pack to: {OUT_DIR}")


if __name__ == "__main__":
    main()
