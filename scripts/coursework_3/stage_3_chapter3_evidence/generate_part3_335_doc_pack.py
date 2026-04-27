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


ROOT = Path(__file__).resolve().parents[3]
TRACE_DIR = ROOT / "output" / "coursework_3_stage3_v2v3_analysis" / "part3_drawdown_analysis"
DOC_DIR = ROOT / "DOC" / "coursework_3_stage3_v2v3_3_3_5"
FIG_DIR = DOC_DIR / "figures"

CONC_PATH = ROOT / "DOC" / "coursework_3_stage3_v2v3_3_3_2" / "leg_contribution_concentration_metrics.csv"
OVERSPEND_PATH = ROOT / "DOC" / "coursework_3_stage3_v2v3_3_3_3" / "overspending_pressure_summary.csv"

ANN_FACTOR = 252.0
STARTING_CASH = 1_000_000.0


def _load_trace(name: str) -> pd.DataFrame:
    df = pd.read_csv(TRACE_DIR / name)
    df["date"] = pd.to_datetime(df["date"])
    return df


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _fmt_pct(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}%"


def _fmt_ratio(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def _fmt_money(value: float) -> str:
    return f"GBP {value:,.0f}"


def _parse_trade_pnls(df: pd.DataFrame) -> list[float]:
    values: list[float] = []
    for item in df["closed_trades"].fillna("").astype(str):
        if "pnl_net=" not in item:
            continue
        matches = re.findall(r"pnl_net=([-+]?\d+(?:\.\d+)?)", item)
        for match in matches:
            values.append(float(match))
    return values


def _performance_metrics(version: str, df: pd.DataFrame, run_summary: dict, dd_summary: pd.Series, conc_row: pd.Series, overspend_row: pd.Series) -> dict:
    equity = df["equity"].astype(float)
    returns = equity.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    daily_mean = float(returns.mean()) if not returns.empty else 0.0
    daily_std = float(returns.std(ddof=0)) if not returns.empty else 0.0
    downside = returns[returns < 0]
    downside_std = float(downside.std(ddof=0)) if not downside.empty else 0.0
    days = max(1, len(returns))

    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
    ann_return = float((equity.iloc[-1] / equity.iloc[0]) ** (ANN_FACTOR / days) - 1.0)
    ann_vol = float(daily_std * math.sqrt(ANN_FACTOR))
    downside_vol = float(downside_std * math.sqrt(ANN_FACTOR))
    sharpe = float((daily_mean / daily_std) * math.sqrt(ANN_FACTOR)) if daily_std > 0 else float("nan")
    sortino = float((daily_mean / downside_std) * math.sqrt(ANN_FACTOR)) if downside_std > 0 else float("nan")
    max_dd = float(dd_summary["max_drawdown_pct"])
    calmar = float(ann_return / max_dd) if max_dd > 0 else float("nan")

    return {
        "version": version,
        "final_value_gbp": float(run_summary["final_value"]),
        "total_return_pct": 100.0 * total_return,
        "annualized_return_pct": 100.0 * ann_return,
        "annualized_vol_pct": 100.0 * ann_vol,
        "downside_vol_pct": 100.0 * downside_vol,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "max_drawdown_pct": 100.0 * max_dd,
        "days_to_recovery": int(dd_summary["trading_days_peak_to_recovery"]),
        "calmar_ratio": calmar,
        "true_pd_ratio": float(run_summary["true_pd_ratio"]),
        "open_pnl_pd_ratio": float(run_summary["open_pnl_pd_ratio"]),
        "activity_pct": float(run_summary["activity_pct"]),
        "avg_gross_exposure_pct": float(overspend_row["avg_gross_exposure_pct"]),
        "effective_leg_count": float(conc_row["effective_leg_count"]),
        "top_leg_share_pct": float(conc_row["top_leg_share_pct"]),
    }


def _execution_metrics(version: str, df: pd.DataFrame, overspend_row: pd.Series, conc_row: pd.Series) -> dict:
    pnls = _parse_trade_pnls(df)
    wins = [value for value in pnls if value > 0]
    losses = [value for value in pnls if value < 0]
    trade_count = len(pnls)
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    win_rate = (len(wins) / trade_count * 100.0) if trade_count else float("nan")
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("nan")
    avg_trade = float(np.mean(pnls)) if pnls else float("nan")
    median_trade = float(np.median(pnls)) if pnls else float("nan")
    payoff_ratio = (float(np.mean(wins)) / abs(float(np.mean(losses)))) if wins and losses and np.mean(losses) != 0 else float("nan")

    return {
        "version": version,
        "trade_count": trade_count,
        "win_rate_pct": win_rate,
        "profit_factor": profit_factor,
        "avg_trade_pnl_gbp": avg_trade,
        "median_trade_pnl_gbp": median_trade,
        "payoff_ratio": payoff_ratio,
        "multi_order_days": int(overspend_row["multi_order_days"]),
        "duplicate_same_series_days": int(overspend_row["duplicate_same_series_days"]),
        "days_gross_over_95pct": int(overspend_row["days_gross_over_95pct"]),
        "meaningful_legs_over_10pct": int(conc_row["meaningful_legs_over_10pct"]),
        "top_leg_share_pct": float(conc_row["top_leg_share_pct"]),
    }


def _make_table_image(df: pd.DataFrame, out_path: Path, title: str) -> None:
    fig_h = 0.65 * (len(df) + 2)
    fig, ax = plt.subplots(figsize=(10.5, fig_h))
    ax.axis("off")
    ax.set_title(title, fontsize=16, pad=14)

    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        cellLoc="center",
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


def _display_main_table(metrics_df: pd.DataFrame) -> pd.DataFrame:
    v2 = metrics_df.loc[metrics_df["version"] == "V2"].iloc[0]
    v3 = metrics_df.loc[metrics_df["version"] == "V3"].iloc[0]
    rows = [
        ("Final value", _fmt_money(v2["final_value_gbp"]), _fmt_money(v3["final_value_gbp"])),
        ("Total return", _fmt_pct(v2["total_return_pct"]), _fmt_pct(v3["total_return_pct"])),
        ("Annualized return", _fmt_pct(v2["annualized_return_pct"]), _fmt_pct(v3["annualized_return_pct"])),
        ("Annualized volatility", _fmt_pct(v2["annualized_vol_pct"]), _fmt_pct(v3["annualized_vol_pct"])),
        ("Sharpe ratio", _fmt_ratio(v2["sharpe_ratio"]), _fmt_ratio(v3["sharpe_ratio"])),
        ("Sortino ratio", _fmt_ratio(v2["sortino_ratio"]), _fmt_ratio(v3["sortino_ratio"])),
        ("Max drawdown", _fmt_pct(v2["max_drawdown_pct"]), _fmt_pct(v3["max_drawdown_pct"])),
        ("Days to recovery", str(int(v2["days_to_recovery"])), str(int(v3["days_to_recovery"]))),
        ("Calmar ratio", _fmt_ratio(v2["calmar_ratio"]), _fmt_ratio(v3["calmar_ratio"])),
        ("True PD ratio", _fmt_ratio(v2["true_pd_ratio"], 4), _fmt_ratio(v3["true_pd_ratio"], 4)),
        ("Open PnL PD ratio", _fmt_ratio(v2["open_pnl_pd_ratio"]), _fmt_ratio(v3["open_pnl_pd_ratio"])),
        ("Activity", _fmt_pct(v2["activity_pct"]), _fmt_pct(v3["activity_pct"])),
    ]
    return pd.DataFrame(rows, columns=["Metric", "V2", "V3"])


def _display_exec_table(exec_df: pd.DataFrame) -> pd.DataFrame:
    v2 = exec_df.loc[exec_df["version"] == "V2"].iloc[0]
    v3 = exec_df.loc[exec_df["version"] == "V3"].iloc[0]
    rows = [
        ("Trade count", str(int(v2["trade_count"])), str(int(v3["trade_count"]))),
        ("Win rate", _fmt_pct(v2["win_rate_pct"]), _fmt_pct(v3["win_rate_pct"])),
        ("Profit factor", _fmt_ratio(v2["profit_factor"]), _fmt_ratio(v3["profit_factor"])),
        ("Average trade PnL", _fmt_money(v2["avg_trade_pnl_gbp"]), _fmt_money(v3["avg_trade_pnl_gbp"])),
        ("Median trade PnL", _fmt_money(v2["median_trade_pnl_gbp"]), _fmt_money(v3["median_trade_pnl_gbp"])),
        ("Payoff ratio", _fmt_ratio(v2["payoff_ratio"]), _fmt_ratio(v3["payoff_ratio"])),
        ("Days above 95% gross", str(int(v2["days_gross_over_95pct"])), str(int(v3["days_gross_over_95pct"]))),
        ("Multi-order days", str(int(v2["multi_order_days"])), str(int(v3["multi_order_days"]))),
        ("Duplicate same-series days", str(int(v2["duplicate_same_series_days"])), str(int(v3["duplicate_same_series_days"]))),
        ("Meaningful legs (>10% PnL share)", str(int(v2["meaningful_legs_over_10pct"])), str(int(v3["meaningful_legs_over_10pct"]))),
        ("Top-leg share", _fmt_pct(v2["top_leg_share_pct"]), _fmt_pct(v3["top_leg_share_pct"])),
    ]
    return pd.DataFrame(rows, columns=["Metric", "V2", "V3"])


def write_reference_pack(main_table: pd.DataFrame, exec_table: pd.DataFrame) -> None:
    ref_text = """# Section 3.3.5 Reference Pack

This folder contains a final-report-style summary for Section 3.3.5. The goal of this section is to consolidate the earlier findings from 3.3.1 to 3.3.3 into a compact set of commonly used return, risk, and execution metrics.

## Recommended Main-Text Use

The strongest layout for the main text is table-driven:

1. Use Table 3.3.5a as the primary quantitative comparison of return and risk.
2. Use Table 3.3.5b as a supplementary table for trade quality, capital pressure, and structural concentration.

## Suggested Main-Text Tables

- Table 3.3.5a: `summary_performance_metrics.csv`
- Table 3.3.5b: `summary_execution_metrics.csv`

## Optional Figure Exports

- `figures/figure_3_3_5a_summary_performance_table.png`
- `figures/figure_3_3_5b_summary_execution_table.png`

These PNGs are image versions of the same tables and can be inserted directly into the report if you prefer not to rebuild the layout manually in Word.

## Interpretation To Emphasise

- V3 dominates V2 on the standard return-risk metrics: higher terminal value, higher annualized return, higher Sharpe and Sortino, lower drawdown, and faster recovery.
- V3 also dominates V2 on execution discipline: fewer trades, higher win rate, higher profit factor, no days near full gross commitment, and far fewer multi-order events.
- The one balanced caveat is that concentration did not improve: V3 still relied more heavily on a single dominant leg than V2.
"""
    (DOC_DIR / "section_3_3_5_reference_pack.md").write_text(ref_text, encoding="utf-8")

    final_text = f"""# Section 3.3.5 Final Report Version

Table 3.3.5a summarises the standard return and risk metrics for Team01 V2 and Team01 V3 on Part 3. The comparison confirms that V3 was superior on nearly every conventional performance criterion. V3 finished with a higher portfolio value, stronger total and annualised returns, higher Sharpe and Sortino ratios, a much smaller maximum drawdown, and a substantially faster recovery time. These results are fully consistent with the detailed discussion in Sections 3.3.1 to 3.3.3: the refined strategy did not merely earn more in absolute terms, but also converted risk into return more efficiently and with a more stable equity path.

Table 3.3.5b extends the evaluation beyond pure return-risk measures to include trade quality, capital pressure, and structural concentration. V3 again showed stronger execution quality, with fewer trades, a higher win rate, a higher profit factor, and a complete removal of the near-full-gross commitment episodes that characterised V2. The strategy also eliminated the repeated same-series rebalancing pressure observed in V2. However, the table also preserves an important limitation identified earlier in Section 3.3.2: the improved V3 result remained highly concentrated in one dominant leg. In other words, V3 was clearly better as a practical trading system, but its final Part 3 performance was still not fully balanced across return sources.

Taken together, Tables 3.3.5a and 3.3.5b provide a concise quantitative conclusion for Section 3.3. The evidence supports the view that the CA3 refinements materially improved both portfolio performance and execution discipline relative to the submitted V2 baseline. At the same time, the concentration metrics show that higher performance should not be interpreted as complete structural robustness. The final evaluation is therefore positive but qualified: V3 was a meaningfully stronger strategy, yet it still depended heavily on one leading component.

References:
- Table 3.3.5a: [summary_performance_metrics.csv](summary_performance_metrics.csv)
- Table 3.3.5b: [summary_execution_metrics.csv](summary_execution_metrics.csv)
- Optional image export: [figures/figure_3_3_5a_summary_performance_table.png](figures/figure_3_3_5a_summary_performance_table.png)
- Optional image export: [figures/figure_3_3_5b_summary_execution_table.png](figures/figure_3_3_5b_summary_execution_table.png)
"""
    (DOC_DIR / "section_3_3_5_final.md").write_text(final_text, encoding="utf-8")


def main() -> None:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    v2 = _load_trace("v2_part3_bar_trace.csv")
    v3 = _load_trace("v3_part3_bar_trace.csv")
    run_summary = _load_json(TRACE_DIR / "part3_run_summaries.json")
    dd_summary = pd.read_csv(TRACE_DIR / "part3_max_drawdown_summary.csv")
    conc_df = pd.read_csv(CONC_PATH)
    overspend_df = pd.read_csv(OVERSPEND_PATH)

    metrics_rows = []
    exec_rows = []
    for version, df in [("V2", v2), ("V3", v3)]:
        dd_row = dd_summary.loc[dd_summary["version"] == version].iloc[0]
        conc_row = conc_df.loc[conc_df["version"] == version].iloc[0]
        overspend_row = overspend_df.loc[overspend_df["version"] == version].iloc[0]
        metrics_rows.append(_performance_metrics(version, df, run_summary[version], dd_row, conc_row, overspend_row))
        exec_rows.append(_execution_metrics(version, df, overspend_row, conc_row))

    metrics_df = pd.DataFrame(metrics_rows)
    exec_df = pd.DataFrame(exec_rows)
    metrics_df.to_csv(DOC_DIR / "summary_performance_metrics.csv", index=False)
    exec_df.to_csv(DOC_DIR / "summary_execution_metrics.csv", index=False)

    main_display = _display_main_table(metrics_df)
    exec_display = _display_exec_table(exec_df)
    _make_table_image(main_display, FIG_DIR / "figure_3_3_5a_summary_performance_table.png", "Table 3.3.5a. Summary Performance Metrics")
    _make_table_image(exec_display, FIG_DIR / "figure_3_3_5b_summary_execution_table.png", "Table 3.3.5b. Summary Execution and Structure Metrics")

    write_reference_pack(main_display, exec_display)
    print(f"DOC pack generated at: {DOC_DIR}")


if __name__ == "__main__":
    main()
