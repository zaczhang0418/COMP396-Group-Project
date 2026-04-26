from __future__ import annotations

import json
import math
import re
import shutil
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
TRACE_DIR = ROOT / "output" / "coursework_3_stage3_v2v3_analysis" / "part3_drawdown_analysis"
V3_ARCHIVE_DIR = ROOT / "output" / "coursework_3_stage2_v3_archive" / "team01_v3_final" / "part3"
DOC_DIR = ROOT / "DOC" / "coursework_3_stage3_v2v3_3_5"
FIG_DIR = DOC_DIR / "figures"

CH3_ANALYSIS_DIR = ROOT / "output" / "coursework_3_stage2_v3_archive" / "chapter3_analysis"
DOC_332_DIR = ROOT / "DOC" / "coursework_3_stage3_v2v3_3_3_2"
DOC_333_DIR = ROOT / "DOC" / "coursework_3_stage3_v2v3_3_3_3"
DOC_335_DIR = ROOT / "DOC" / "coursework_3_stage3_v2v3_3_3_5"


def _load_trace(name: str) -> pd.DataFrame:
    df = pd.read_csv(TRACE_DIR / name)
    df["date"] = pd.to_datetime(df["date"])
    return df


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _gross_series(df: pd.DataFrame) -> pd.Series:
    cols = [col for col in ["tf_pos_pct", "mr09_pos_pct", "ga_pos_pct"] if col in df.columns]
    return df[cols].fillna(0.0).abs().sum(axis=1)


def _fmt_pct(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}%"


def _fmt_ratio(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def _fmt_money(value: float) -> str:
    return f"GBP {value:,.2f}"


def _parse_trade_pnls(df: pd.DataFrame) -> list[float]:
    values: list[float] = []
    for item in df["closed_trades"].fillna("").astype(str):
        if "pnl_net=" not in item:
            continue
        matches = re.findall(r"pnl_net=([-+]?\d+(?:\.\d+)?)", item)
        for match in matches:
            values.append(float(match))
    return values


def save_drawdown_figure(v3: pd.DataFrame, dd_row: pd.Series) -> Path:
    fig, axes = plt.subplots(2, 1, figsize=(12, 7.5), sharex=False, constrained_layout=True)

    eq_idx = v3["equity"] / float(v3["equity"].iloc[0]) * 100.0
    axes[0].plot(v3["date"], eq_idx, color="#1f6aa5", linewidth=2.0)
    axes[0].set_title("V3 Part 3 Equity Progression")
    axes[0].set_ylabel("Equity Index (Start=100)")
    axes[0].grid(alpha=0.3)

    dd_pct = v3["drawdown_pct"] * 100.0
    axes[1].plot(v3["date"], dd_pct, color="#1f6aa5", linewidth=2.0)
    axes[1].fill_between(v3["date"], 0.0, dd_pct, color="#1f6aa5", alpha=0.18)
    axes[1].set_title("V3 Underwater Profile")
    axes[1].set_ylabel("Drawdown (%)")
    axes[1].set_xlabel("Date")
    axes[1].grid(alpha=0.3)

    for ax in axes:
        for date_value, label, color in [
            (pd.to_datetime(dd_row["peak_date"]), "peak", "#2e7d32"),
            (pd.to_datetime(dd_row["trough_date"]), "trough", "#c62828"),
            (pd.to_datetime(dd_row["recovery_date"]), "recovery", "#1565c0"),
        ]:
            if pd.isna(date_value):
                continue
            ax.axvline(date_value, color=color, linestyle="--", linewidth=1.1, alpha=0.8)
            ax.text(
                date_value,
                ax.get_ylim()[1],
                label,
                rotation=90,
                ha="right",
                va="top",
                fontsize=8,
                color=color,
                bbox={"facecolor": "white", "edgecolor": color, "alpha": 0.75, "pad": 2},
            )

    out_path = FIG_DIR / "figure_3_5_3_v3_equity_drawdown_profile.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


def save_leg_figure(v3_leg: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(8.5, 3.8), constrained_layout=True)
    colors = {"tf": "#b24a2b", "mr09": "#1f6aa5"}
    left = 0.0
    for row in v3_leg.sort_values("share_of_abs_leg_pnl_pct", ascending=False).itertuples(index=False):
        ax.barh(["V3"], [row.share_of_abs_leg_pnl_pct], left=left, color=colors.get(row.leg, "#888888"), label=row.leg.upper())
        if row.share_of_abs_leg_pnl_pct >= 4:
            ax.text(
                left + row.share_of_abs_leg_pnl_pct / 2,
                0,
                f"{row.leg} ({row.series})\n{row.share_of_abs_leg_pnl_pct:.1f}%",
                ha="center",
                va="center",
                color="white",
                fontsize=9,
            )
        left += row.share_of_abs_leg_pnl_pct
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of Absolute Part 3 Leg PnL (%)")
    ax.set_title("V3 Part 3 Leg Contribution Concentration")
    ax.grid(axis="x", alpha=0.3)
    out_path = FIG_DIR / "figure_3_5_4_v3_leg_contribution.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


def save_exposure_figure(v3: pd.DataFrame) -> Path:
    gross = _gross_series(v3) * 100.0
    submitted = v3["submitted_orders"].fillna("").astype(str).map(lambda s: 0 if not s else len([p for p in s.split("|") if p.strip()]))

    fig, axes = plt.subplots(2, 1, figsize=(12, 6.8), sharex=True, constrained_layout=True)
    axes[0].plot(v3["date"], gross, color="#1f6aa5", linewidth=2.0)
    axes[0].axhline(80.0, color="#ef6c00", linestyle="--", linewidth=1.0, label="80% gross")
    axes[0].axhline(95.0, color="#c62828", linestyle="--", linewidth=1.0, label="95% gross")
    axes[0].set_ylabel("Gross Exposure (%)")
    axes[0].set_title("V3 Gross Exposure and Capital Buffer")
    axes[0].grid(alpha=0.3)
    axes[0].legend(loc="upper right")

    axes[1].bar(v3["date"], submitted, width=2.5, color="#4f6f8f")
    axes[1].set_ylabel("Submitted Orders")
    axes[1].set_xlabel("Date")
    axes[1].set_title("V3 Order Pressure by Day")
    axes[1].grid(axis="y", alpha=0.3)

    out_path = FIG_DIR / "figure_3_5_5_v3_exposure_control.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


def save_single_column_table(df: pd.DataFrame, title: str, out_name: str) -> Path:
    fig_h = 0.62 * (len(df) + 2)
    fig, ax = plt.subplots(figsize=(8.6, fig_h))
    ax.axis("off")
    ax.set_title(title, fontsize=16, pad=14)
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        cellLoc="left",
        colLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.3)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#dbe7f3")
            cell.set_text_props(weight="bold")
        elif row % 2 == 1:
            cell.set_facecolor("#f7f9fc")
    out_path = FIG_DIR / out_name
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return out_path


def build_pack() -> None:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    v3 = _load_trace("v3_part3_bar_trace.csv")
    dd_summary = pd.read_csv(TRACE_DIR / "part3_max_drawdown_summary.csv")
    run_summary = _load_json(TRACE_DIR / "part3_run_summaries.json")["V3"]
    leg_breakdown = pd.read_csv(CH3_ANALYSIS_DIR / "part3_leg_breakdown_v1_v2_v3.csv")
    asset_reassign = pd.read_csv(CH3_ANALYSIS_DIR / "asset_reassignment_evidence.csv")
    structure_controls = pd.read_csv(CH3_ANALYSIS_DIR / "structure_controls_comparison.csv")
    conc_metrics = pd.read_csv(DOC_332_DIR / "leg_contribution_concentration_metrics.csv")
    overspend = pd.read_csv(DOC_333_DIR / "overspending_pressure_summary.csv")
    perf_metrics = pd.read_csv(DOC_335_DIR / "summary_performance_metrics.csv")
    exec_metrics = pd.read_csv(DOC_335_DIR / "summary_execution_metrics.csv")

    v3_dd = dd_summary.loc[dd_summary["version"] == "V3"].iloc[0]
    v3_leg = leg_breakdown.loc[leg_breakdown["version"] == "V3"].copy()
    v3_conc = conc_metrics.loc[conc_metrics["version"] == "V3"].iloc[0]
    v3_over = overspend.loc[overspend["version"] == "V3"].iloc[0]
    v3_perf = perf_metrics.loc[perf_metrics["version"] == "V3"].iloc[0]
    v3_exec = exec_metrics.loc[exec_metrics["version"] == "V3"].iloc[0]

    expected_rows = pd.DataFrame(
        [
            {
                "Change area": "Asset mapping",
                "V3 design choice": "Retain TF on series_1 and replace MR10 with MR09",
                "Expected impact": "Better transferability and lower dependence on historical hard binding",
            },
            {
                "Change area": "Dynamic allocation",
                "V3 design choice": "Use performance-aware active weights instead of static three-leg allocation",
                "Expected impact": "More adaptive capital deployment under changing market conditions",
            },
            {
                "Change area": "Exposure control",
                "V3 design choice": "Apply gross_cap=1.00 and rebalance tolerance",
                "Expected impact": "Lower overspending pressure and less unnecessary rebalancing",
            },
            {
                "Change area": "Risk control",
                "V3 design choice": "Use cooldowns and loss-freeze logic",
                "Expected impact": "Reduce repeated re-entry after unfavorable sequences",
            },
        ]
    )
    expected_rows.to_csv(DOC_DIR / "v3_expected_design_summary.csv", index=False)

    observed_rows = pd.DataFrame(
        [
            {
                "Dataset": "Part 3",
                "Final value": run_summary["final_value"],
                "True PD ratio": run_summary["true_pd_ratio"],
                "Open PnL PD ratio": run_summary["open_pnl_pd_ratio"],
                "Activity pct": run_summary["activity_pct"],
                "Bankrupt": run_summary["bankrupt"],
            }
        ]
    )
    observed_rows.to_csv(DOC_DIR / "v3_observed_part3_results.csv", index=False)

    drawdown_rows = pd.DataFrame(
        [
            {
                "Peak date": v3_dd["peak_date"],
                "Peak equity": v3_dd["peak_equity"],
                "Trough date": v3_dd["trough_date"],
                "Trough equity": v3_dd["trough_equity"],
                "Max drawdown abs": v3_dd["max_drawdown_abs"],
                "Max drawdown pct": v3_dd["max_drawdown_pct"],
                "Recovery date": v3_dd["recovery_date"],
                "Days to recovery": v3_dd["trading_days_peak_to_recovery"],
                "Nearest pre-trough action": v3_dd["nearest_pre_trough_action"],
                "Nearest post-trough action": v3_dd["nearest_post_trough_action"],
            }
        ]
    )
    drawdown_rows.to_csv(DOC_DIR / "v3_drawdown_summary.csv", index=False)

    leg_rows = pd.DataFrame(
        [
            {
                "Active legs": int(v3_conc["active_leg_count"]),
                "Top leg": v3_conc["top_leg"],
                "Top series": v3_conc["top_series"],
                "Top-leg share pct": v3_conc["top_leg_share_pct"],
                "Second-leg share pct": v3_conc["second_leg_share_pct"],
                "Effective leg count": v3_conc["effective_leg_count"],
                "Meaningful legs >10 pct": int(v3_conc["meaningful_legs_over_10pct"]),
            }
        ]
    )
    leg_rows.to_csv(DOC_DIR / "v3_leg_structure_summary.csv", index=False)

    exposure_rows = pd.DataFrame(
        [
            {
                "Average gross exposure pct": v3_over["avg_gross_exposure_pct"],
                "Median gross exposure pct": v3_over["median_gross_exposure_pct"],
                "95th pct gross exposure": v3_over["p95_gross_exposure_pct"],
                "Max gross exposure pct": v3_over["max_gross_exposure_pct"],
                "Days above 80 pct gross": int(v3_over["days_gross_over_80pct"]),
                "Days above 95 pct gross": int(v3_over["days_gross_over_95pct"]),
                "Multi-order days": int(v3_over["multi_order_days"]),
                "Duplicate same-series days": int(v3_over["duplicate_same_series_days"]),
            }
        ]
    )
    exposure_rows.to_csv(DOC_DIR / "v3_exposure_control_summary.csv", index=False)

    common_metrics_rows = pd.DataFrame(
        [
            {"Metric": "Final value", "V3": _fmt_money(v3_perf["final_value_gbp"])},
            {"Metric": "Total return", "V3": _fmt_pct(v3_perf["total_return_pct"])},
            {"Metric": "Annualized return", "V3": _fmt_pct(v3_perf["annualized_return_pct"])},
            {"Metric": "Annualized volatility", "V3": _fmt_pct(v3_perf["annualized_vol_pct"])},
            {"Metric": "Sharpe ratio", "V3": _fmt_ratio(v3_perf["sharpe_ratio"])},
            {"Metric": "Sortino ratio", "V3": _fmt_ratio(v3_perf["sortino_ratio"])},
            {"Metric": "Max drawdown", "V3": _fmt_pct(v3_perf["max_drawdown_pct"])},
            {"Metric": "Days to recovery", "V3": str(int(v3_perf["days_to_recovery"]))},
            {"Metric": "Calmar ratio", "V3": _fmt_ratio(v3_perf["calmar_ratio"])},
            {"Metric": "True PD ratio", "V3": _fmt_ratio(v3_perf["true_pd_ratio"], 4)},
            {"Metric": "Open PnL PD ratio", "V3": _fmt_ratio(v3_perf["open_pnl_pd_ratio"])},
            {"Metric": "Activity", "V3": _fmt_pct(v3_perf["activity_pct"])},
            {"Metric": "Trade count", "V3": str(int(v3_exec["trade_count"]))},
            {"Metric": "Win rate", "V3": _fmt_pct(v3_exec["win_rate_pct"])},
            {"Metric": "Profit factor", "V3": _fmt_ratio(v3_exec["profit_factor"])},
            {"Metric": "Top-leg share", "V3": _fmt_pct(v3_exec["top_leg_share_pct"])},
        ]
    )
    common_metrics_rows.to_csv(DOC_DIR / "v3_common_performance_metrics.csv", index=False)

    mapping_subset = asset_reassign.loc[
        (asset_reassign["strategy_family"] == "tf") & (asset_reassign["asset"] == 1)
        | (asset_reassign["strategy_family"] == "mr") & (asset_reassign["asset"].isin([9, 10]))
    ].copy()
    mapping_subset.to_csv(DOC_DIR / "v3_asset_mapping_evidence.csv", index=False)

    controls_subset = structure_controls.loc[structure_controls["version"] == "V3"].copy()
    controls_subset.to_csv(DOC_DIR / "v3_structure_controls.csv", index=False)

    # Copies of core source files
    shutil.copy2(TRACE_DIR / "part3_run_summaries.json", DOC_DIR / "part3_run_summaries.json")
    shutil.copy2(TRACE_DIR / "part3_max_drawdown_summary.csv", DOC_DIR / "part3_max_drawdown_summary.csv")
    shutil.copy2(CH3_ANALYSIS_DIR / "asset_reassignment_evidence.csv", DOC_DIR / "asset_reassignment_evidence.csv")
    shutil.copy2(CH3_ANALYSIS_DIR / "part3_leg_breakdown_v1_v2_v3.csv", DOC_DIR / "part3_leg_breakdown_v1_v2_v3.csv")

    fig_drawdown = save_drawdown_figure(v3, v3_dd)
    fig_leg = save_leg_figure(v3_leg)
    fig_exposure = save_exposure_figure(v3)
    fig_metrics = save_single_column_table(
        common_metrics_rows,
        "Table 3.5.6. Common V3 Performance Metrics",
        "figure_3_5_6_v3_common_metrics_table.png",
    )

    reference_text = f"""# Section 3.5 Reference Pack

This pack mirrors the Chapter 3.3 workflow, but applies it only to Team01 V3 on Part 3. It is designed so that Section 3.5 can stand on its own as a V3-only analysis, while Section 3.6 can later compare V2 and V3 side by side.

## Recommended Section Structure

1. 3.5.1 Expected Performance of Team01 V3
2. 3.5.2 Observed V3 Results on Part 3
3. 3.5.3 Equity Curve and Drawdown Analysis
4. 3.5.4 Leg Contribution and Structural Behaviour
5. 3.5.5 Exposure Control and Execution Discipline
6. 3.5.6 Summary of Common Performance Metrics

## Suggested Main-Text Assets

- 3.5.1: `v3_expected_design_summary.csv`
- 3.5.2: `v3_observed_part3_results.csv`
- 3.5.3: [figures/{fig_drawdown.name}](figures/{fig_drawdown.name}) and `v3_drawdown_summary.csv`
- 3.5.4: [figures/{fig_leg.name}](figures/{fig_leg.name}) and `v3_leg_structure_summary.csv`
- 3.5.5: [figures/{fig_exposure.name}](figures/{fig_exposure.name}) and `v3_exposure_control_summary.csv`
- 3.5.6: `v3_common_performance_metrics.csv` or [figures/{fig_metrics.name}](figures/{fig_metrics.name})

## Core V3 Results

- Final value: {_fmt_money(run_summary["final_value"])}
- True PD ratio: {_fmt_ratio(run_summary["true_pd_ratio"], 4)}
- Open PnL PD ratio: {_fmt_ratio(run_summary["open_pnl_pd_ratio"])}
- Activity: {_fmt_pct(run_summary["activity_pct"])}
- Max drawdown: {_fmt_pct(v3_perf["max_drawdown_pct"])}
- Recovery time: {int(v3_perf["days_to_recovery"])} trading days
- Top-leg share: {_fmt_pct(v3_conc["top_leg_share_pct"])}
- Average gross exposure: {_fmt_pct(v3_over["avg_gross_exposure_pct"])}
"""
    (DOC_DIR / "section_3_5_reference_pack.md").write_text(reference_text, encoding="utf-8")

    final_text = f"""# Section 3.5 Final Report Version

## 3.5.1 Expected Performance of Team01 V3

Team01 V3 was expected to improve on the submitted V2 strategy because it directly addressed the main weaknesses identified in Chapter 3.3. First, the strategy-asset mapping was reassessed through cross-asset testing, which retained TF on `series_1` but replaced the earlier MR10 leg with MR09. Second, V3 introduced stronger portfolio-level controls, including dynamic allocation, performance-aware budgeting, a gross exposure cap, rebalance tolerance, and loss-freeze logic. These changes meant that V3 was expected not only to improve return, but also to show better capital discipline, lower execution pressure, and stronger adaptability under unseen Part 3 conditions.

## 3.5.2 Observed V3 Results on Part 3

The observed Part 3 results support that expectation. Team01 V3 finished Part 3 with a final portfolio value of {_fmt_money(run_summary["final_value"])}, a true PD ratio of {_fmt_ratio(run_summary["true_pd_ratio"], 4)}, and an open PnL PD ratio of {_fmt_ratio(run_summary["open_pnl_pd_ratio"])}. The strategy did not become bankrupt, and its activity level remained moderate at {_fmt_pct(run_summary["activity_pct"])}. These headline outcomes indicate that the CA3 refinement was deployable on unseen data and that the revised design remained active without relying on the excessive trading pressure that had characterised the weaker baseline.

## 3.5.3 Equity Curve and Drawdown Analysis

Figure 3.5.3 shows that V3 maintained a comparatively smooth Part 3 equity path and a controlled underwater profile. The strategy reached its local peak on {pd.to_datetime(v3_dd["peak_date"]).date()} and recorded its deepest drawdown on {pd.to_datetime(v3_dd["trough_date"]).date()}, but the maximum loss was limited to {_fmt_pct(v3_perf["max_drawdown_pct"])} and recovery required only {int(v3_perf["days_to_recovery"])} trading days. The drawdown episode was therefore meaningful but contained. The evidence suggests that V3 could absorb a losing sequence without developing the prolonged underwater behaviour that would normally undermine confidence in live deployment.

## 3.5.4 Leg Contribution and Structural Behaviour

Figure 3.5.4 shows that V3's Part 3 performance was structurally simple but not fully balanced. Only two legs were active, and the TF leg on `series_1` dominated the realised contribution profile. The top leg accounted for {_fmt_pct(v3_conc["top_leg_share_pct"])} of absolute leg PnL, while the effective leg count was only {_fmt_ratio(v3_conc["effective_leg_count"])}. This means that V3's success should be interpreted carefully. The revised mapping improved deployability and reduced reliance on historically fixed assets, but the final result was still overwhelmingly driven by one main return engine rather than by evenly distributed support across multiple legs.

## 3.5.5 Exposure Control and Execution Discipline

The clearest operational improvement in V3 was its stronger exposure control. Figure 3.5.5 shows that gross exposure remained moderate across Part 3, with average gross exposure of {_fmt_pct(v3_over["avg_gross_exposure_pct"])} and no trading days above 95% gross exposure. Order pressure was also restrained: the strategy recorded only {int(v3_over["multi_order_days"])} multi-order days and no duplicate same-series rebalancing days. This is consistent with the intended role of the V3 control framework. By combining desired allocations before execution, scaling them under `gross_cap=1.00`, and applying rebalance tolerance, V3 avoided the capital over-commitment pressure that had previously weakened the baseline system.

## 3.5.6 Summary of Common Performance Metrics

Table 3.5.6 consolidates the main performance indicators for V3. In return-risk terms, the strategy combined positive total and annualised returns with controlled volatility, a Sharpe ratio of {_fmt_ratio(v3_perf["sharpe_ratio"])}, a Sortino ratio of {_fmt_ratio(v3_perf["sortino_ratio"])}, and a Calmar ratio of {_fmt_ratio(v3_perf["calmar_ratio"])}. In execution terms, it completed {int(v3_exec["trade_count"])} closed trades with a win rate of {_fmt_pct(v3_exec["win_rate_pct"])} and a profit factor of {_fmt_ratio(v3_exec["profit_factor"])}. Taken together, these metrics support a positive evaluation of Team01 V3 on Part 3: the CA3 refinement produced a strategy that was profitable, more controlled, and operationally more robust, although its final return profile still remained highly concentrated in the trend-following leg.

References:
- 3.5.1 table: [v3_expected_design_summary.csv](v3_expected_design_summary.csv)
- 3.5.2 table: [v3_observed_part3_results.csv](v3_observed_part3_results.csv)
- 3.5.3 figure: [figures/{fig_drawdown.name}](figures/{fig_drawdown.name})
- 3.5.4 figure: [figures/{fig_leg.name}](figures/{fig_leg.name})
- 3.5.5 figure: [figures/{fig_exposure.name}](figures/{fig_exposure.name})
- 3.5.6 table: [v3_common_performance_metrics.csv](v3_common_performance_metrics.csv)
- Optional 3.5.6 image export: [figures/{fig_metrics.name}](figures/{fig_metrics.name})
"""
    (DOC_DIR / "section_3_5_final.md").write_text(final_text, encoding="utf-8")


if __name__ == "__main__":
    build_pack()
