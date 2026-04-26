from __future__ import annotations

from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DOC_DIR = ROOT / "DOC" / "coursework_3_stage3_v2v3_3_6"
FIG_DIR = DOC_DIR / "figures"

PERF_PATH = ROOT / "DOC" / "coursework_3_stage3_v2v3_3_3_5" / "summary_performance_metrics.csv"
EXEC_PATH = ROOT / "DOC" / "coursework_3_stage3_v2v3_3_3_5" / "summary_execution_metrics.csv"
OVERSPEND_PATH = ROOT / "DOC" / "coursework_3_stage3_v2v3_3_3_3" / "overspending_pressure_summary.csv"
CONC_PATH = ROOT / "DOC" / "coursework_3_stage3_v2v3_3_3_2" / "leg_contribution_concentration_metrics.csv"
MAPPING_PATH = ROOT / "DOC" / "coursework_3_stage3_v2v3_3_3_2" / "asset_binding_transfer_summary.csv"
CONTROLS_PATH = ROOT / "output" / "coursework_3_stage2_v3_archive" / "chapter3_analysis" / "structure_controls_comparison.csv"
DD_PATH = ROOT / "output" / "coursework_3_stage3_v2v3_analysis" / "part3_drawdown_analysis" / "part3_max_drawdown_summary.csv"


def _fmt_pct(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}%"


def _fmt_ratio(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def _fmt_money(value: float, digits: int = 2) -> str:
    return f"GBP {value:,.{digits}f}"


def _make_table_image(df: pd.DataFrame, out_path: Path, title: str, fig_w: float = 10.6) -> None:
    fig_h = 0.62 * (len(df) + 2)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
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
    table.scale(1, 1.35)

    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#dbe7f3")
            cell.set_text_props(weight="bold")
        elif row % 2 == 1:
            cell.set_facecolor("#f7f9fc")

    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_pack() -> None:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    perf = pd.read_csv(PERF_PATH).set_index("version")
    exec_df = pd.read_csv(EXEC_PATH).set_index("version")
    over = pd.read_csv(OVERSPEND_PATH).set_index("version")
    conc = pd.read_csv(CONC_PATH).set_index("version")
    mapping = pd.read_csv(MAPPING_PATH)
    controls = pd.read_csv(CONTROLS_PATH).set_index("version")
    dd = pd.read_csv(DD_PATH).set_index("version")

    v2_perf = perf.loc["V2"]
    v3_perf = perf.loc["V3"]
    v2_exec = exec_df.loc["V2"]
    v3_exec = exec_df.loc["V3"]
    v2_over = over.loc["V2"]
    v3_over = over.loc["V3"]
    v2_conc = conc.loc["V2"]
    v3_conc = conc.loc["V3"]
    v2_ctrl = controls.loc["V2"]
    v3_ctrl = controls.loc["V3"]
    v2_dd = dd.loc["V2"]
    v3_dd = dd.loc["V3"]

    mr10 = mapping.loc[(mapping["strategy_family"] == "mr") & (mapping["asset"] == 10)].iloc[0]
    mr09 = mapping.loc[(mapping["strategy_family"] == "mr") & (mapping["asset"] == 9)].iloc[0]
    garch07 = mapping.loc[(mapping["strategy_family"] == "garch") & (mapping["asset"] == 7)].iloc[0]
    tf01 = mapping.loc[(mapping["strategy_family"] == "tf") & (mapping["asset"] == 1)].iloc[0]

    return_risk = pd.DataFrame(
        [
            {
                "Criterion": "Final portfolio value",
                "V2": _fmt_money(v2_perf["final_value_gbp"]),
                "V3": _fmt_money(v3_perf["final_value_gbp"]),
                "Change in V3": _fmt_money(v3_perf["final_value_gbp"] - v2_perf["final_value_gbp"]),
            },
            {
                "Criterion": "Total return",
                "V2": _fmt_pct(v2_perf["total_return_pct"]),
                "V3": _fmt_pct(v3_perf["total_return_pct"]),
                "Change in V3": _fmt_pct(v3_perf["total_return_pct"] - v2_perf["total_return_pct"]),
            },
            {
                "Criterion": "Annualized return",
                "V2": _fmt_pct(v2_perf["annualized_return_pct"]),
                "V3": _fmt_pct(v3_perf["annualized_return_pct"]),
                "Change in V3": _fmt_pct(v3_perf["annualized_return_pct"] - v2_perf["annualized_return_pct"]),
            },
            {
                "Criterion": "Sharpe ratio",
                "V2": _fmt_ratio(v2_perf["sharpe_ratio"]),
                "V3": _fmt_ratio(v3_perf["sharpe_ratio"]),
                "Change in V3": _fmt_ratio(v3_perf["sharpe_ratio"] - v2_perf["sharpe_ratio"]),
            },
            {
                "Criterion": "Sortino ratio",
                "V2": _fmt_ratio(v2_perf["sortino_ratio"]),
                "V3": _fmt_ratio(v3_perf["sortino_ratio"]),
                "Change in V3": _fmt_ratio(v3_perf["sortino_ratio"] - v2_perf["sortino_ratio"]),
            },
            {
                "Criterion": "Max drawdown",
                "V2": _fmt_pct(v2_perf["max_drawdown_pct"]),
                "V3": _fmt_pct(v3_perf["max_drawdown_pct"]),
                "Change in V3": _fmt_pct(v3_perf["max_drawdown_pct"] - v2_perf["max_drawdown_pct"]),
            },
            {
                "Criterion": "Recovery time",
                "V2": f'{int(v2_perf["days_to_recovery"])} trading days',
                "V3": f'{int(v3_perf["days_to_recovery"])} trading days',
                "Change in V3": f'{int(v3_perf["days_to_recovery"] - v2_perf["days_to_recovery"])} days',
            },
            {
                "Criterion": "True PD ratio",
                "V2": _fmt_ratio(v2_perf["true_pd_ratio"], 4),
                "V3": _fmt_ratio(v3_perf["true_pd_ratio"], 4),
                "Change in V3": _fmt_ratio(v3_perf["true_pd_ratio"] - v2_perf["true_pd_ratio"], 4),
            },
            {
                "Criterion": "Open PnL PD ratio",
                "V2": _fmt_ratio(v2_perf["open_pnl_pd_ratio"]),
                "V3": _fmt_ratio(v3_perf["open_pnl_pd_ratio"]),
                "Change in V3": _fmt_ratio(v3_perf["open_pnl_pd_ratio"] - v2_perf["open_pnl_pd_ratio"]),
            },
        ]
    )
    return_risk.to_csv(DOC_DIR / "v2_v3_return_risk_comparison.csv", index=False)

    structure = pd.DataFrame(
        [
            {
                "Theme": "Deployed mapping",
                "V2": v2_ctrl["mapping"],
                "V3": v3_ctrl["mapping"],
                "Interpretation": "V3 removed hard binding to MR10 and dropped the weak GARCH leg.",
            },
            {
                "Theme": "TF transfer evidence",
                "V2": f'OOS {_fmt_ratio(tf01["oos_true_pd_ratio"], 3)} / Part 2 {_fmt_ratio(tf01["part2_true_pd_ratio"], 3)}',
                "V3": f'OOS {_fmt_ratio(tf01["oos_true_pd_ratio"], 3)} / Part 2 {_fmt_ratio(tf01["part2_true_pd_ratio"], 3)}',
                "Interpretation": "TF on series_1 was the only leg with stable evidence across stages.",
            },
            {
                "Theme": "MR leg evidence",
                "V2": f'MR10: OOS {_fmt_ratio(mr10["oos_true_pd_ratio"], 3)} / Part 2 {_fmt_ratio(mr10["part2_true_pd_ratio"], 3)}',
                "V3": f'MR09: OOS {_fmt_ratio(mr09["oos_true_pd_ratio"], 3)} / Part 2 {_fmt_ratio(mr09["part2_true_pd_ratio"], 3)}',
                "Interpretation": "MR09 still weakened in transfer, but materially less than MR10.",
            },
            {
                "Theme": "Dropped GARCH leg",
                "V2": f'GARCH07: OOS {_fmt_ratio(garch07["oos_true_pd_ratio"], 3)} / Part 2 {_fmt_ratio(garch07["part2_true_pd_ratio"], 3)}',
                "V3": "Not deployed",
                "Interpretation": "V3 avoided carrying forward the weakest transferred leg.",
            },
            {
                "Theme": "Allocation logic",
                "V2": "Static 0.45 / 0.45 / 0.10 leg weights",
                "V3": "Dynamic TF/MR active weights around 0.65 / 0.35 base",
                "Interpretation": "V3 used portfolio-level adaptation rather than fixed leg budgeting.",
            },
            {
                "Theme": "Concentration outcome",
                "V2": f'Top leg {_fmt_pct(v2_conc["top_leg_share_pct"])}; effective legs {_fmt_ratio(v2_conc["effective_leg_count"])}',
                "V3": f'Top leg {_fmt_pct(v3_conc["top_leg_share_pct"])}; effective legs {_fmt_ratio(v3_conc["effective_leg_count"])}',
                "Interpretation": "Performance improved, but final return concentration became even more extreme in V3.",
            },
        ]
    )
    structure.to_csv(DOC_DIR / "v2_v3_structure_mapping_comparison.csv", index=False)

    execution = pd.DataFrame(
        [
            {
                "Criterion": "Activity",
                "V2": _fmt_pct(v2_perf["activity_pct"]),
                "V3": _fmt_pct(v3_perf["activity_pct"]),
                "Change in V3": _fmt_pct(v3_perf["activity_pct"] - v2_perf["activity_pct"]),
            },
            {
                "Criterion": "Average gross exposure",
                "V2": _fmt_pct(v2_over["avg_gross_exposure_pct"]),
                "V3": _fmt_pct(v3_over["avg_gross_exposure_pct"]),
                "Change in V3": _fmt_pct(v3_over["avg_gross_exposure_pct"] - v2_over["avg_gross_exposure_pct"]),
            },
            {
                "Criterion": "95th pct gross exposure",
                "V2": _fmt_pct(v2_over["p95_gross_exposure_pct"]),
                "V3": _fmt_pct(v3_over["p95_gross_exposure_pct"]),
                "Change in V3": _fmt_pct(v3_over["p95_gross_exposure_pct"] - v2_over["p95_gross_exposure_pct"]),
            },
            {
                "Criterion": "Days above 95% gross",
                "V2": str(int(v2_over["days_gross_over_95pct"])),
                "V3": str(int(v3_over["days_gross_over_95pct"])),
                "Change in V3": str(int(v3_over["days_gross_over_95pct"] - v2_over["days_gross_over_95pct"])),
            },
            {
                "Criterion": "Multi-order days",
                "V2": str(int(v2_exec["multi_order_days"])),
                "V3": str(int(v3_exec["multi_order_days"])),
                "Change in V3": str(int(v3_exec["multi_order_days"] - v2_exec["multi_order_days"])),
            },
            {
                "Criterion": "Duplicate same-series days",
                "V2": str(int(v2_exec["duplicate_same_series_days"])),
                "V3": str(int(v3_exec["duplicate_same_series_days"])),
                "Change in V3": str(int(v3_exec["duplicate_same_series_days"] - v2_exec["duplicate_same_series_days"])),
            },
            {
                "Criterion": "Trade count",
                "V2": str(int(v2_exec["trade_count"])),
                "V3": str(int(v3_exec["trade_count"])),
                "Change in V3": str(int(v3_exec["trade_count"] - v2_exec["trade_count"])),
            },
            {
                "Criterion": "Win rate",
                "V2": _fmt_pct(v2_exec["win_rate_pct"]),
                "V3": _fmt_pct(v3_exec["win_rate_pct"]),
                "Change in V3": _fmt_pct(v3_exec["win_rate_pct"] - v2_exec["win_rate_pct"]),
            },
            {
                "Criterion": "Profit factor",
                "V2": _fmt_ratio(v2_exec["profit_factor"]),
                "V3": _fmt_ratio(v3_exec["profit_factor"]),
                "Change in V3": _fmt_ratio(v3_exec["profit_factor"] - v2_exec["profit_factor"]),
            },
        ]
    )
    execution.to_csv(DOC_DIR / "v2_v3_execution_exposure_comparison.csv", index=False)

    change_summary = pd.DataFrame(
        [
            {
                "Headline change": "Return quality",
                "Supporting evidence": f'Final value +{_fmt_money(v3_perf["final_value_gbp"] - v2_perf["final_value_gbp"])}; true PD +{_fmt_ratio(v3_perf["true_pd_ratio"] - v2_perf["true_pd_ratio"], 4)}',
            },
            {
                "Headline change": "Risk control",
                "Supporting evidence": f'Max drawdown {_fmt_pct(v2_perf["max_drawdown_pct"])} to {_fmt_pct(v3_perf["max_drawdown_pct"])}; recovery {int(v2_perf["days_to_recovery"])} to {int(v3_perf["days_to_recovery"])} days',
            },
            {
                "Headline change": "Execution discipline",
                "Supporting evidence": f'Activity {_fmt_pct(v2_perf["activity_pct"])} to {_fmt_pct(v3_perf["activity_pct"])}; duplicate same-series days {int(v2_exec["duplicate_same_series_days"])} to {int(v3_exec["duplicate_same_series_days"])}',
            },
            {
                "Headline change": "Structural revision",
                "Supporting evidence": "MR10 and GARCH07 were replaced or removed; V3 used gross cap, rebalance tolerance, and loss-freeze logic.",
            },
            {
                "Headline change": "Remaining limitation",
                "Supporting evidence": f'Top-leg share rose from {_fmt_pct(v2_conc["top_leg_share_pct"])} to {_fmt_pct(v3_conc["top_leg_share_pct"])}.',
            },
        ]
    )
    change_summary.to_csv(DOC_DIR / "v2_v3_change_summary.csv", index=False)

    _make_table_image(
        return_risk,
        FIG_DIR / "figure_3_6_1_return_risk_comparison.png",
        "Table 3.6.1. V2 vs V3 Return and Risk Comparison",
    )
    _make_table_image(
        structure,
        FIG_DIR / "figure_3_6_2_structure_mapping_comparison.png",
        "Table 3.6.2. V2 vs V3 Structural and Mapping Comparison",
        fig_w=12.8,
    )
    _make_table_image(
        execution,
        FIG_DIR / "figure_3_6_3_execution_exposure_comparison.png",
        "Table 3.6.3. V2 vs V3 Execution and Exposure Comparison",
    )
    _make_table_image(
        change_summary,
        FIG_DIR / "figure_3_6_4_change_summary.png",
        "Table 3.6.4. Headline Changes from V2 to V3",
        fig_w=12.0,
    )

    reference_text = f"""# Section 3.6 Reference Pack

This folder is the comparison layer built directly on top of the completed Section 3.3 and Section 3.5 analyses. The aim is not to introduce a new workflow. Instead, each subsection should pair one V2 result block from Chapter 3.3 with the corresponding V3 result block from Chapter 3.5.

## Recommended Section Structure

1. 3.6.1 Comparison of Equity Curve and Drawdown Results
2. 3.6.2 Comparison of Leg Contribution and Structural Behaviour
3. 3.6.3 Comparison of Exposure Control and Execution Discipline
4. 3.6.4 Comparison of Common Performance Metrics

## Section Pairing Logic

- 3.6.1 should compare the findings from Section 3.3.1 and Section 3.5.3.
- 3.6.2 should compare the findings from Section 3.3.2 and Section 3.5.4.
- 3.6.3 should compare the findings from Section 3.3.3 and Section 3.5.5.
- 3.6.4 should compare the summary conclusions from Section 3.3.5 and Section 3.5.6.

## Suggested Main-Text Assets

- 3.6.1: `v2_v3_return_risk_comparison.csv` or [figures/figure_3_6_1_return_risk_comparison.png](figures/figure_3_6_1_return_risk_comparison.png)
- 3.6.2: `v2_v3_structure_mapping_comparison.csv` or [figures/figure_3_6_2_structure_mapping_comparison.png](figures/figure_3_6_2_structure_mapping_comparison.png)
- 3.6.3: `v2_v3_execution_exposure_comparison.csv` or [figures/figure_3_6_3_execution_exposure_comparison.png](figures/figure_3_6_3_execution_exposure_comparison.png)
- 3.6.4: `v2_v3_change_summary.csv` or [figures/figure_3_6_4_change_summary.png](figures/figure_3_6_4_change_summary.png)

## Core Comparative Message

- The comparison should read as a paired contrast between V2 and V3 outcomes, not as an independent third analysis.
- V3 outperformed V2 on return quality, drawdown control, recovery speed, and execution discipline.
- The structural explanation for that improvement comes from the mapping revision and the stronger portfolio-level controls introduced in V3.
- The main residual caveat remains concentration: V3 was stronger overall, but even more dependent on one dominant TF leg.
"""
    (DOC_DIR / "section_3_6_reference_pack.md").write_text(reference_text, encoding="utf-8")

    final_text = f"""# Section 3.6 Final Report Version

## 3.6.1 Comparison of Equity Curve and Drawdown Results

This subsection directly compares the evidence developed earlier in Section 3.3.1 for V2 and Section 3.5.3 for V3. The contrast is clear. V2 finished Part 3 at {_fmt_money(v2_perf["final_value_gbp"])} and experienced a maximum drawdown of {_fmt_pct(v2_perf["max_drawdown_pct"])}, with recovery requiring {int(v2_perf["days_to_recovery"])} trading days. V3, by contrast, finished at {_fmt_money(v3_perf["final_value_gbp"])}, limited its worst drawdown to {_fmt_pct(v3_perf["max_drawdown_pct"])}, and recovered within only {int(v3_perf["days_to_recovery"])} trading days. When the Section 3.3.1 drawdown evidence is read together with the Section 3.5.3 V3 profile, the conclusion is that the refined strategy achieved not only a higher terminal value, but also a materially shallower and shorter worst-case loss episode. Table 3.6.1 condenses that paired comparison into one return-risk view.

## 3.6.2 Comparison of Leg Contribution and Structural Behaviour

This subsection combines the structural weakness identified in Section 3.3.2 with the V3-only evidence from Section 3.5.4. In V2, the portfolio preserved the fixed combination of TF on `series_1`, MR on `series_10`, and GARCH on `series_7`, even though MR10 deteriorated from an OOS true PD ratio of {_fmt_ratio(mr10["oos_true_pd_ratio"], 3)} to a Part 2 true PD ratio of {_fmt_ratio(mr10["part2_true_pd_ratio"], 3)}, while GARCH07 remained weak in both OOS and Part 2 evidence. V3 revised that structure by retaining TF on `series_1`, replacing MR10 with MR09, and removing the GARCH leg altogether. This revision made the final portfolio more evidence-driven and more deployable under Part 3 conditions. However, when the realised leg-contribution evidence from Sections 3.3.2 and 3.5.4 is compared side by side, the diversification problem remains visible: the top-leg share rose from {_fmt_pct(v2_conc["top_leg_share_pct"])} in V2 to {_fmt_pct(v3_conc["top_leg_share_pct"])} in V3. Table 3.6.2 therefore supports a balanced conclusion: V3 improved structural design quality, but not realised balance across return sources.

## 3.6.3 Comparison of Exposure Control and Execution Discipline

This subsection compares the capital-pressure evidence from Section 3.3.3 with the V3 control evidence from Section 3.5.5. V2 operated with high activity at {_fmt_pct(v2_perf["activity_pct"])}, average gross exposure of {_fmt_pct(v2_over["avg_gross_exposure_pct"])}, {int(v2_over["days_gross_over_95pct"])} days above 95% gross exposure, {int(v2_exec["multi_order_days"])} multi-order days, and {int(v2_exec["duplicate_same_series_days"])} duplicate same-series rebalancing days. By contrast, V3 reduced activity to {_fmt_pct(v3_perf["activity_pct"])}, lowered average gross exposure to {_fmt_pct(v3_over["avg_gross_exposure_pct"])}, eliminated all days above 95% gross exposure, and removed duplicate same-series rebalancing altogether. Read together, Sections 3.3.3 and 3.5.5 show that the difference was not cosmetic. V3 replaced reactive overspend prevention with explicit portfolio-level control through dynamic allocation, `gross_cap=1.00`, rebalance tolerance, and loss-freeze logic. Table 3.6.3 summarises this operational improvement clearly.

## 3.6.4 Comparison of Common Performance Metrics

The final comparison brings together the summary conclusions from Section 3.3.5 and Section 3.5.6. Across the standard metrics, V3 dominated V2 on both return quality and execution quality. It achieved a higher true PD ratio of {_fmt_ratio(v3_perf["true_pd_ratio"], 4)} versus {_fmt_ratio(v2_perf["true_pd_ratio"], 4)}, a higher Sharpe ratio of {_fmt_ratio(v3_perf["sharpe_ratio"])} versus {_fmt_ratio(v2_perf["sharpe_ratio"])}, a higher Sortino ratio of {_fmt_ratio(v3_perf["sortino_ratio"])} versus {_fmt_ratio(v2_perf["sortino_ratio"])}, a higher win rate of {_fmt_pct(v3_exec["win_rate_pct"])} versus {_fmt_pct(v2_exec["win_rate_pct"])}, and a higher profit factor of {_fmt_ratio(v3_exec["profit_factor"])} versus {_fmt_ratio(v2_exec["profit_factor"])}. The summary metrics therefore confirm the same message already seen in the paired subsection evidence above: Team01 V3 was a materially stronger Part 3 trading system than Team01 V2. The only important qualification is that stronger performance should not be mistaken for full structural robustness, because the final V3 outcome remained even more concentrated in one dominant trend-following leg.

References:
- Table 3.6.1: [v2_v3_return_risk_comparison.csv](v2_v3_return_risk_comparison.csv)
- Table 3.6.2: [v2_v3_structure_mapping_comparison.csv](v2_v3_structure_mapping_comparison.csv)
- Table 3.6.3: [v2_v3_execution_exposure_comparison.csv](v2_v3_execution_exposure_comparison.csv)
- Table 3.6.4: [v2_v3_change_summary.csv](v2_v3_change_summary.csv)
- Optional image export: [figures/figure_3_6_1_return_risk_comparison.png](figures/figure_3_6_1_return_risk_comparison.png)
- Optional image export: [figures/figure_3_6_2_structure_mapping_comparison.png](figures/figure_3_6_2_structure_mapping_comparison.png)
- Optional image export: [figures/figure_3_6_3_execution_exposure_comparison.png](figures/figure_3_6_3_execution_exposure_comparison.png)
- Optional image export: [figures/figure_3_6_4_change_summary.png](figures/figure_3_6_4_change_summary.png)
"""
    (DOC_DIR / "section_3_6_final.md").write_text(final_text, encoding="utf-8")

    print(f"3.6 comparison pack generated at: {DOC_DIR}")
    print(f"V2 peak-to-trough drawdown: {v2_dd['max_drawdown_pct']:.6f}")
    print(f"V3 peak-to-trough drawdown: {v3_dd['max_drawdown_pct']:.6f}")


if __name__ == "__main__":
    build_pack()
