from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = ROOT / "output" / "coursework_3_stage3_v2v3_analysis" / "part3_drawdown_analysis"
DOC_DIR = ROOT / "DOC" / "coursework_3_stage3_v2v3_3_3_1"
FIG_DIR = DOC_DIR / "figures"


def _load_trace(name: str) -> pd.DataFrame:
    df = pd.read_csv(SRC_DIR / name)
    df["date"] = pd.to_datetime(df["date"])
    return df


def _load_drawdown_summary() -> pd.DataFrame:
    df = pd.read_csv(SRC_DIR / "part3_max_drawdown_summary.csv")
    for col in [
        "peak_date",
        "trough_date",
        "recovery_date",
        "nearest_pre_trough_action_date",
        "nearest_post_trough_action_date",
    ]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _load_run_summaries() -> dict:
    with (SRC_DIR / "part3_run_summaries.json").open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _format_money(value: float) -> str:
    return f"GBP {value:,.2f}"


def _format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _save_combined_figure(v2: pd.DataFrame, v3: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=False, constrained_layout=True)

    v2_norm = v2["equity"] / float(v2["equity"].iloc[0]) * 100.0
    v3_norm = v3["equity"] / float(v3["equity"].iloc[0]) * 100.0

    axes[0].plot(v2["date"], v2_norm, label="V2 normalized equity", linewidth=2.0, color="#b24a2b")
    axes[0].plot(v3["date"], v3_norm, label="V3 normalized equity", linewidth=2.0, color="#1f6aa5")
    axes[0].set_ylabel("Equity Index (Start=100)")
    axes[0].set_title("Part 3 Equity Progression: V2 vs V3")
    axes[0].grid(alpha=0.3)
    axes[0].legend(loc="upper left")

    axes[1].plot(
        v2["date"],
        v2["drawdown_pct"] * 100.0,
        label="V2 drawdown",
        linewidth=2.0,
        color="#b24a2b",
    )
    axes[1].plot(
        v3["date"],
        v3["drawdown_pct"] * 100.0,
        label="V3 drawdown",
        linewidth=2.0,
        color="#1f6aa5",
    )
    axes[1].set_ylabel("Drawdown (%)")
    axes[1].set_xlabel("Date")
    axes[1].set_title("Part 3 Underwater Profile: V2 vs V3")
    axes[1].grid(alpha=0.3)
    axes[1].legend(loc="lower left")

    out_path = FIG_DIR / "figure_3_3_1a_part3_equity_drawdown_comparison.png"
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path


def _save_zoomed_drawdown_figure(
    v2: pd.DataFrame,
    v3: pd.DataFrame,
    v2_summary: pd.Series,
    v3_summary: pd.Series,
) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True, constrained_layout=True)

    configs = [
        (axes[0], v2, v2_summary, "V2 Max Drawdown Window", "#b24a2b"),
        (axes[1], v3, v3_summary, "V3 Max Drawdown Window", "#1f6aa5"),
    ]

    for ax, trace, summary_row, title, color in configs:
        peak_date = summary_row["peak_date"]
        recovery_date = summary_row["recovery_date"]
        trough_date = summary_row["trough_date"]

        end_date = recovery_date if pd.notna(recovery_date) else trough_date + pd.Timedelta(days=30)
        window = trace.loc[
            (trace["date"] >= peak_date - pd.Timedelta(days=10))
            & (trace["date"] <= end_date + pd.Timedelta(days=10))
        ].copy()

        ax.plot(window["date"], window["drawdown_pct"] * 100.0, linewidth=2.2, color=color)
        ax.fill_between(window["date"], 0.0, window["drawdown_pct"] * 100.0, color=color, alpha=0.18)
        ax.axhline(0.0, color="black", linewidth=1.0, alpha=0.7)
        ax.grid(alpha=0.3)
        ax.set_title(title)
        ax.set_xlabel("Date")

        for date_value, label, line_color in [
            (peak_date, "peak", "#2e7d32"),
            (trough_date, "trough", "#c62828"),
            (recovery_date, "recovery", "#1565c0"),
        ]:
            if pd.isna(date_value):
                continue
            ax.axvline(date_value, color=line_color, linestyle="--", linewidth=1.2, alpha=0.85)
            ax.text(
                date_value,
                ax.get_ylim()[1],
                label,
                rotation=90,
                va="top",
                ha="right",
                fontsize=8,
                color=line_color,
                bbox={"facecolor": "white", "edgecolor": line_color, "alpha": 0.75, "pad": 2},
            )

        ax.text(
            0.03,
            0.05,
            f'Max DD: {_format_pct(float(summary_row["max_drawdown_pct"]))}\n'
            f'Days to recover: {int(summary_row["trading_days_peak_to_recovery"])}',
            transform=ax.transAxes,
            fontsize=8,
            va="bottom",
            ha="left",
            bbox={"facecolor": "white", "edgecolor": color, "alpha": 0.8, "pad": 4},
        )

    axes[0].set_ylabel("Drawdown (%)")
    out_path = FIG_DIR / "figure_3_3_1d_zoomed_drawdown_windows.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _annotate_vertical(ax, date_value, label: str, color: str) -> None:
    if pd.isna(date_value):
        return
    ax.axvline(date_value, color=color, linestyle="--", linewidth=1.2, alpha=0.8)
    ax.text(
        date_value,
        ax.get_ylim()[1],
        label,
        rotation=90,
        va="top",
        ha="right",
        fontsize=8,
        color=color,
        bbox={"facecolor": "white", "edgecolor": color, "alpha": 0.75, "pad": 2},
    )


def _save_event_window_figure(
    trace: pd.DataFrame,
    summary_row: pd.Series,
    title: str,
    lower_cols: list[tuple[str, str, str]],
    output_name: str,
) -> Path:
    peak_date = summary_row["peak_date"]
    trough_date = summary_row["trough_date"]
    post_date = summary_row["nearest_post_trough_action_date"]

    start = peak_date - pd.Timedelta(days=7)
    end = (post_date if pd.notna(post_date) else trough_date) + pd.Timedelta(days=12)
    window = trace.loc[(trace["date"] >= start) & (trace["date"] <= end)].copy()

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True, constrained_layout=True)

    axes[0].plot(window["date"], window["equity"], linewidth=2.0, color="#2f3b4f")
    axes[0].set_ylabel("Equity")
    axes[0].set_title(title)
    axes[0].grid(alpha=0.3)

    for col, label, color in lower_cols:
        if col in window.columns:
            axes[1].plot(window["date"], window[col], label=label, linewidth=2.0, color=color)

    axes[1].set_ylabel("Position Size")
    axes[1].set_xlabel("Date")
    axes[1].grid(alpha=0.3)
    axes[1].legend(loc="upper right")

    _annotate_vertical(axes[0], peak_date, "peak", "#2e7d32")
    _annotate_vertical(axes[0], trough_date, "trough", "#c62828")
    _annotate_vertical(
        axes[0],
        summary_row["nearest_pre_trough_action_date"],
        "pre-trough action",
        "#ef6c00",
    )
    _annotate_vertical(
        axes[0],
        summary_row["nearest_post_trough_action_date"],
        "post-trough action",
        "#1565c0",
    )
    for date_col, _, color in [
        ("peak_date", "peak", "#2e7d32"),
        ("trough_date", "trough", "#c62828"),
        ("nearest_pre_trough_action_date", "pre", "#ef6c00"),
        ("nearest_post_trough_action_date", "post", "#1565c0"),
    ]:
        date_value = summary_row[date_col]
        if pd.isna(date_value):
            continue
        axes[1].axvline(date_value, color=color, linestyle="--", linewidth=1.0, alpha=0.7)

    out_path = FIG_DIR / output_name
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path


def _write_reference_pack(
    summary_df: pd.DataFrame,
    run_summaries: dict,
    figure_paths: dict[str, Path],
) -> None:
    v2 = summary_df.loc[summary_df["version"] == "V2"].iloc[0]
    v3 = summary_df.loc[summary_df["version"] == "V3"].iloc[0]

    reference_md = f"""# Section 3.3.1 Reference Pack

This folder contains the evidence pack for Chapter 3.3.1 on Part 3 equity curve and drawdown behaviour.

## Where The Original Analysis Output Lives

- Main analysis output: `output/coursework_3_stage3_v2v3_analysis/part3_drawdown_analysis/`
- This DOC pack: `DOC/coursework_3_stage3_v2v3_3_3_1/`

## Suggested Main-Text Figures

1. Figure 3.3.1a: [Part 3 equity and drawdown comparison](figures/{figure_paths["combined"].name})
   Data source: `output/coursework_3_stage3_v2v3_analysis/part3_drawdown_analysis/v2_part3_bar_trace.csv` and `output/coursework_3_stage3_v2v3_analysis/part3_drawdown_analysis/v3_part3_bar_trace.csv`
   Why to use it: this is the cleanest one-chart comparison showing that V3 both compounded more and stayed shallower underwater than V2.

2. Figure 3.3.1b: [V2 drawdown event window](figures/{figure_paths["v2_event"].name})
   Data source: `output/coursework_3_stage3_v2v3_analysis/part3_drawdown_analysis/v2_part3_bar_trace.csv`
   Why to use it: this isolates the V2 peak-to-trough sequence and shows that the deepest loss phase was carried mainly by the TF leg while the other legs were largely inactive.

3. Figure 3.3.1c: [V3 drawdown event window](figures/{figure_paths["v3_event"].name})
   Data source: `output/coursework_3_stage3_v2v3_analysis/part3_drawdown_analysis/v3_part3_bar_trace.csv`
   Why to use it: this shows that V3's deepest drawdown was shorter and linked mainly to a single MR09 short, not a broad multi-leg failure.

4. Figure 3.3.1d: [Zoomed max-drawdown windows](figures/{figure_paths["zoomed_drawdown"].name})
   Data source: `output/coursework_3_stage3_v2v3_analysis/part3_drawdown_analysis/v2_part3_bar_trace.csv`, `v3_part3_bar_trace.csv`, and `part3_max_drawdown_summary.csv`
   Why to use it: this is the best figure for visually comparing the depth, duration, and recovery speed of the worst drawdown episode in each version.

## Suggested Main-Text Table

Table 3.3.1 should use [part3_max_drawdown_summary.csv](part3_max_drawdown_summary.csv).

Recommended fields to cite:
- V2 peak date `{v2["peak_date"].date()}` and trough date `{v2["trough_date"].date()}`
- V2 max drawdown `{_format_money(float(v2["max_drawdown_abs"]))}` or `{_format_pct(float(v2["max_drawdown_pct"]))}`
- V2 recovery in `{int(v2["trading_days_peak_to_recovery"])}` trading days
- V3 peak date `{v3["peak_date"].date()}` and trough date `{v3["trough_date"].date()}`
- V3 max drawdown `{_format_money(float(v3["max_drawdown_abs"]))}` or `{_format_pct(float(v3["max_drawdown_pct"]))}`
- V3 recovery in `{int(v3["trading_days_peak_to_recovery"])}` trading days

## Optional Appendix Items

- [part3_max_drawdown_window.csv](part3_max_drawdown_window.csv)
  Use this when you want line-by-line evidence for the +/- 5 trading days around each trough.

- `output/coursework_3_stage2_v3_archive/team01_v3_final/part3/equity_dashboard_combined.png`
  This is still useful as a fuller single-version dashboard for V3, but it is better as appendix support than as the main comparative figure.

- `output/coursework_3_stage2_v3_archive/team01_v3_final/part3/portfolio_underwater.png`
  This is useful if you want a standalone V3 underwater chart, again mainly as appendix material.

## Core Numbers For 3.3.1

- V2 final portfolio value: {_format_money(float(run_summaries["V2"]["final_value"]))}
- V2 true PD: {run_summaries["V2"]["true_pd_ratio"]:.4f}
- V2 activity: {run_summaries["V2"]["activity_pct"]:.1f}%
- V3 final portfolio value: {_format_money(float(run_summaries["V3"]["final_value"]))}
- V3 true PD: {run_summaries["V3"]["true_pd_ratio"]:.4f}
- V3 activity: {run_summaries["V3"]["activity_pct"]:.1f}%
"""
    (DOC_DIR / "section_3_3_1_reference_pack.md").write_text(reference_md, encoding="utf-8")

    draft_md = f"""# Section 3.3.1 Draft Text

Figure 3.3.1a shows that the V3 portfolio delivered a stronger Part 3 equity curve than V2 while also keeping a materially shallower underwater profile. Using the same restored Part 3 dataset, V2 finished at {_format_money(float(run_summaries["V2"]["final_value"]))} with a true PD of {run_summaries["V2"]["true_pd_ratio"]:.4f}, whereas V3 finished at {_format_money(float(run_summaries["V3"]["final_value"]))} with a true PD of {run_summaries["V3"]["true_pd_ratio"]:.4f}. The drawdown evidence is equally important: V2 reached its deepest loss on {v2["trough_date"].date()}, falling {_format_money(float(v2["max_drawdown_abs"]))} ({_format_pct(float(v2["max_drawdown_pct"]))}) from the previous peak on {v2["peak_date"].date()}, and it needed {int(v2["trading_days_peak_to_recovery"])} trading days to recover. By contrast, V3 bottomed on {v3["trough_date"].date()} with a much smaller drawdown of {_format_money(float(v3["max_drawdown_abs"]))} ({_format_pct(float(v3["max_drawdown_pct"]))}) from its {v3["peak_date"].date()} peak and recovered within {int(v3["trading_days_peak_to_recovery"])} trading days.

The event-window figures explain why the two equity curves behaved differently. Figure 3.3.1b shows that the V2 trough was concentrated in the TF leg: the nearest pre-trough action occurred on {v2["nearest_pre_trough_action_date"].date()}, when the strategy filled `SELL series_1 fill_size=7717.0000 fill_px=22.5700`, yet the portfolio still fell into its trough on {v2["trough_date"].date()} with little support from the other legs. This is consistent with V2's higher activity rate of {run_summaries["V2"]["activity_pct"]:.1f}% and suggests that repeated trend-following adjustments did not meaningfully reduce risk during the sell-off. Figure 3.3.1c shows a different pattern for V3: the deepest drawdown was tied mainly to a single MR09 short initiated on {v3["nearest_pre_trough_action_date"].date()} and then covered on {v3["nearest_post_trough_action_date"].date()}. In other words, V3 still experienced a losing episode, but the loss was narrower in depth, shorter in duration, and easier to attribute to one contained position rather than to a broad portfolio-level loss of control.

If you want a more visual drawdown-focused presentation in the main text, Figure 3.3.1d can be cited alongside Figure 3.3.1a. It zooms directly into the worst underwater window for each version and makes the contrast easier to see: V2's loss was both deeper and much slower to recover, whereas V3's worst episode stayed comparatively shallow and normalized more quickly.

References:
- Figure 3.3.1a: [figures/{figure_paths["combined"].name}](figures/{figure_paths["combined"].name})
- Figure 3.3.1b: [figures/{figure_paths["v2_event"].name}](figures/{figure_paths["v2_event"].name})
- Figure 3.3.1c: [figures/{figure_paths["v3_event"].name}](figures/{figure_paths["v3_event"].name})
- Figure 3.3.1d: [figures/{figure_paths["zoomed_drawdown"].name}](figures/{figure_paths["zoomed_drawdown"].name})
- Table 3.3.1: [part3_max_drawdown_summary.csv](part3_max_drawdown_summary.csv)
- Appendix evidence: [part3_max_drawdown_window.csv](part3_max_drawdown_window.csv)
"""
    (DOC_DIR / "section_3_3_1_draft.md").write_text(draft_md, encoding="utf-8")


def main() -> None:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    v2 = _load_trace("v2_part3_bar_trace.csv")
    v3 = _load_trace("v3_part3_bar_trace.csv")
    summary_df = _load_drawdown_summary()
    run_summaries = _load_run_summaries()

    shutil.copy2(SRC_DIR / "part3_max_drawdown_summary.csv", DOC_DIR / "part3_max_drawdown_summary.csv")
    shutil.copy2(SRC_DIR / "part3_max_drawdown_window.csv", DOC_DIR / "part3_max_drawdown_window.csv")
    shutil.copy2(SRC_DIR / "part3_run_summaries.json", DOC_DIR / "part3_run_summaries.json")

    v2_summary = summary_df.loc[summary_df["version"] == "V2"].iloc[0]
    v3_summary = summary_df.loc[summary_df["version"] == "V3"].iloc[0]

    combined_fig = _save_combined_figure(v2, v3)
    zoomed_drawdown_fig = _save_zoomed_drawdown_figure(v2, v3, v2_summary, v3_summary)
    v2_event_fig = _save_event_window_figure(
        trace=v2,
        summary_row=v2_summary,
        title="V2 Part 3 Drawdown Window: Equity and Position Concentration",
        lower_cols=[
            ("tf_pos_size", "TF position", "#b24a2b"),
            ("mr_pos_size", "MR position", "#7b1fa2"),
            ("ga_pos_size", "GARCH position", "#00897b"),
        ],
        output_name="figure_3_3_1b_v2_drawdown_event_window.png",
    )
    v3_event_fig = _save_event_window_figure(
        trace=v3,
        summary_row=v3_summary,
        title="V3 Part 3 Drawdown Window: Equity and Position Concentration",
        lower_cols=[
            ("tf_pos_size", "TF position", "#b24a2b"),
            ("mr09_pos_size", "MR09 position", "#1f6aa5"),
            ("ga_pos_size", "GARCH position", "#00897b"),
        ],
        output_name="figure_3_3_1c_v3_drawdown_event_window.png",
    )

    _write_reference_pack(
        summary_df=summary_df,
        run_summaries=run_summaries,
        figure_paths={
            "combined": combined_fig,
            "zoomed_drawdown": zoomed_drawdown_fig,
            "v2_event": v2_event_fig,
            "v3_event": v3_event_fig,
        },
    )

    print(f"DOC pack generated at: {DOC_DIR}")


if __name__ == "__main__":
    main()
