from __future__ import annotations

import csv
import re
import shutil
from collections import Counter
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[3]
TRACE_DIR = ROOT / "output" / "coursework_3_stage3_v2v3_analysis" / "part3_drawdown_analysis"
CH3_DIR = ROOT / "output" / "coursework_3_stage2_v3_archive" / "chapter3_analysis"
DOC_DIR = ROOT / "DOC" / "coursework_3_stage3_v2v3_3_3_3"
FIG_DIR = DOC_DIR / "figures"


def _load_trace(name: str) -> pd.DataFrame:
    df = pd.read_csv(TRACE_DIR / name)
    df["date"] = pd.to_datetime(df["date"])
    return df


def _gross_series(df: pd.DataFrame) -> pd.Series:
    cols = [col for col in ["tf_pos_pct", "mr_pos_pct", "mr09_pos_pct", "ga_pos_pct"] if col in df.columns]
    return df[cols].fillna(0.0).abs().sum(axis=1)


def _order_parts(value: str) -> list[str]:
    if not value or value == "nan":
        return []
    return [part.strip() for part in value.split("|") if part.strip()]


def _series_tokens(parts: list[str]) -> list[str]:
    out = []
    for part in parts:
        match = re.search(r"(series_\d+)", part)
        if match:
            out.append(match.group(1))
    return out


def build_pressure_summary(version: str, df: pd.DataFrame, activity_pct: float) -> dict:
    gross = _gross_series(df)
    submitted = df["submitted_orders"].fillna("").astype(str)
    filled = df["filled_orders"].fillna("").astype(str)

    order_days = int(submitted.str.len().gt(0).sum())
    fill_days = int(filled.str.len().gt(0).sum())
    multi_order_days = 0
    duplicate_same_series_days = 0
    max_submitted_orders_per_day = 0

    for value in submitted:
        parts = _order_parts(value)
        if not parts:
            continue
        max_submitted_orders_per_day = max(max_submitted_orders_per_day, len(parts))
        if len(parts) > 1:
            multi_order_days += 1
        counts = Counter(_series_tokens(parts))
        if any(count > 1 for count in counts.values()):
            duplicate_same_series_days += 1

    return {
        "version": version,
        "avg_gross_exposure_pct": 100.0 * float(gross.mean()),
        "median_gross_exposure_pct": 100.0 * float(gross.median()),
        "p95_gross_exposure_pct": 100.0 * float(gross.quantile(0.95)),
        "max_gross_exposure_pct": 100.0 * float(gross.max()),
        "days_gross_over_80pct": int((gross > 0.80).sum()),
        "days_gross_over_95pct": int((gross > 0.95).sum()),
        "order_days": order_days,
        "fill_days": fill_days,
        "multi_order_days": multi_order_days,
        "duplicate_same_series_days": duplicate_same_series_days,
        "max_submitted_orders_per_day": max_submitted_orders_per_day,
        "activity_pct": activity_pct,
    }


def build_event_examples(version: str, df: pd.DataFrame) -> list[dict]:
    gross = _gross_series(df)
    rows = []
    for idx, row in df.iterrows():
        submitted_value = str(row.get("submitted_orders", "") or "")
        parts = _order_parts(submitted_value)
        if not parts:
            continue
        series = _series_tokens(parts)
        counts = Counter(series)
        duplicate = any(count > 1 for count in counts.values())
        if not duplicate and len(parts) < 2 and gross.iloc[idx] <= 0.95:
            continue
        rows.append(
            {
                "version": version,
                "date": row["date"].date().isoformat(),
                "gross_exposure_pct": 100.0 * float(gross.iloc[idx]),
                "submitted_order_count": len(parts),
                "duplicate_same_series": duplicate,
                "submitted_orders": submitted_value,
                "filled_orders": str(row.get("filled_orders", "") or ""),
                "tf_pos_pct": row.get("tf_pos_pct", 0.0),
                "mr_pos_pct": row.get("mr_pos_pct", 0.0),
                "mr09_pos_pct": row.get("mr09_pos_pct", 0.0),
                "ga_pos_pct": row.get("ga_pos_pct", 0.0),
            }
        )
    rows.sort(key=lambda item: (item["submitted_order_count"], item["gross_exposure_pct"]), reverse=True)
    return rows[:20]


def save_pressure_figure(v2: pd.DataFrame, v3: pd.DataFrame) -> Path:
    v2_gross = _gross_series(v2) * 100.0
    v3_gross = _gross_series(v3) * 100.0

    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=False, constrained_layout=True)
    configs = [
        (axes[0], v2["date"], v2_gross, "V2 Gross Exposure Pressure", "#b24a2b"),
        (axes[1], v3["date"], v3_gross, "V3 Gross Exposure Pressure", "#1f6aa5"),
    ]
    for ax, dates, gross, title, color in configs:
        ax.plot(dates, gross, color=color, linewidth=1.8)
        ax.axhline(80.0, color="#ef6c00", linestyle="--", linewidth=1.0, label="80% gross")
        ax.axhline(95.0, color="#c62828", linestyle="--", linewidth=1.0, label="95% gross")
        ax.set_ylim(0, max(105.0, float(gross.max()) + 3.0))
        ax.set_ylabel("Gross Exposure (%)")
        ax.set_title(title)
        ax.grid(alpha=0.3)
        ax.legend(loc="upper right")
    axes[1].set_xlabel("Date")

    out_path = FIG_DIR / "figure_3_3_3a_gross_exposure_pressure.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


def save_order_pressure_figure(summary_df: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)

    axes[0].bar(
        summary_df["version"],
        summary_df["days_gross_over_95pct"],
        color=["#b24a2b", "#1f6aa5"],
    )
    axes[0].set_title("Days Near Full Capital Commitment")
    axes[0].set_ylabel("Count of Days")
    axes[0].grid(axis="y", alpha=0.3)
    for _, row in summary_df.iterrows():
        axes[0].text(row["version"], row["days_gross_over_95pct"] + 1, f'{int(row["days_gross_over_95pct"])}', ha="center")

    x = range(len(summary_df))
    width = 0.35
    axes[1].bar(
        [i - width / 2 for i in x],
        summary_df["multi_order_days"],
        width=width,
        color="#ef6c00",
        label="Multi-order days",
    )
    axes[1].bar(
        [i + width / 2 for i in x],
        summary_df["duplicate_same_series_days"],
        width=width,
        color="#7b1fa2",
        label="Duplicate same-series days",
    )
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(summary_df["version"])
    axes[1].set_title("Order-Churn Pressure")
    axes[1].set_ylabel("Count of Days")
    axes[1].grid(axis="y", alpha=0.3)
    axes[1].legend(loc="upper right")

    out_path = FIG_DIR / "figure_3_3_3b_order_pressure_summary.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


def save_v2_window_figure(v2: pd.DataFrame) -> Path:
    gross = _gross_series(v2) * 100.0
    window = v2.loc[(v2["date"] >= pd.Timestamp("2075-08-14")) & (v2["date"] <= pd.Timestamp("2075-08-24"))].copy()
    window_gross = gross.loc[window.index]
    order_counts = window["submitted_orders"].fillna("").astype(str).map(lambda value: len(_order_parts(value)))

    fig, axes = plt.subplots(2, 1, figsize=(12, 6.5), sharex=True, constrained_layout=True)

    axes[0].plot(window["date"], window_gross, color="#b24a2b", linewidth=2.0)
    axes[0].fill_between(window["date"], 0.0, window_gross, color="#b24a2b", alpha=0.18)
    axes[0].axhline(80.0, color="#ef6c00", linestyle="--", linewidth=1.0)
    axes[0].axhline(95.0, color="#c62828", linestyle="--", linewidth=1.0)
    axes[0].set_ylabel("Gross Exposure (%)")
    axes[0].set_title("V2 Over-Commitment Window: Repeated Same-Series Rebalancing")
    axes[0].grid(alpha=0.3)

    axes[1].bar(window["date"], order_counts, color="#7b1fa2", width=0.8)
    axes[1].set_ylabel("Submitted Orders")
    axes[1].set_xlabel("Date")
    axes[1].grid(axis="y", alpha=0.3)

    for idx, row in window.iterrows():
        value = str(row.get("submitted_orders", "") or "")
        counts = Counter(_series_tokens(_order_parts(value)))
        if any(count > 1 for count in counts.values()):
            axes[1].text(row["date"], order_counts.loc[idx] + 0.1, "dup", ha="center", va="bottom", fontsize=8, color="#c62828")

    out_path = FIG_DIR / "figure_3_3_3c_v2_overcommitment_window.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


def write_reference_pack(summary_df: pd.DataFrame, figure_paths: dict[str, Path]) -> None:
    v2 = summary_df.loc[summary_df["version"] == "V2"].iloc[0]
    v3 = summary_df.loc[summary_df["version"] == "V3"].iloc[0]

    reference_text = f"""# Section 3.3.3 Reference Pack

This folder contains the evidence pack for Chapter 3.3.3 on overspending pressure and capital over-commitment.

## Recommended Framing

The strongest phrasing for this section is not that V2 literally bankrupted the portfolio in Part 3, because it did not. A more accurate framing is that V2 created persistent overspending pressure by repeatedly pushing gross exposure close to the full-capital boundary while also generating frequent multi-order and duplicate rebalance events. V3 reduced this pressure through explicit gross-cap control and fewer same-day reallocation events.

## Suggested Main-Text Figures

1. Figure 3.3.3a: [Gross exposure pressure](figures/{figure_paths["gross"].name})
   Why to use it: this directly shows that V2 spent far more time near full capital commitment than V3.

2. Figure 3.3.3b: [Order-pressure summary](figures/{figure_paths["orders"].name})
   Why to use it: this quantifies the operational side of overspending pressure through multi-order and duplicate same-series days.

3. Figure 3.3.3c: [V2 over-commitment window](figures/{figure_paths["window"].name})
   Why to use it: this gives a concrete local example of repeated same-series rebalancing while capital usage was already elevated.

## Suggested Main-Text Tables

- Table 3.3.3a: [overspending_pressure_summary.csv](overspending_pressure_summary.csv)
- Table 3.3.3b: [overspending_event_examples.csv](overspending_event_examples.csv)

## Numbers Most Worth Citing

- V2 average gross exposure: {v2["avg_gross_exposure_pct"]:.2f}%
- V2 95th-percentile gross exposure: {v2["p95_gross_exposure_pct"]:.2f}%
- V2 days above 95% gross: {int(v2["days_gross_over_95pct"])}
- V2 multi-order days: {int(v2["multi_order_days"])}
- V2 duplicate same-series days: {int(v2["duplicate_same_series_days"])}
- V3 average gross exposure: {v3["avg_gross_exposure_pct"]:.2f}%
- V3 95th-percentile gross exposure: {v3["p95_gross_exposure_pct"]:.2f}%
- V3 days above 95% gross: {int(v3["days_gross_over_95pct"])}
- V3 multi-order days: {int(v3["multi_order_days"])}
- V3 duplicate same-series days: {int(v3["duplicate_same_series_days"])}

## Cause Analysis To Emphasise

1. In V2, each leg targeted its own percentage independently, but there was no explicit portfolio-level gross cap.
2. The framework overspend guard only blocks orders if forecast next-open cash would turn negative, so it acts as a last-resort safety check rather than a strategic budget allocator.
3. In V3, desired allocations are first combined and then scaled back under `gross_cap=1.00`, with `rebalance_tol=0.015` further reducing unnecessary churn.
"""
    (DOC_DIR / "section_3_3_3_reference_pack.md").write_text(reference_text, encoding="utf-8")

    draft_text = f"""# Section 3.3.3 Draft Text

The overspending issue in Team01 V2 is best understood as persistent capital over-commitment rather than outright bankruptcy. As shown in Figure 3.3.3a and Table 3.3.3a, V2 spent a substantial portion of Part 3 operating close to full capital usage. Its average gross exposure was {v2["avg_gross_exposure_pct"]:.2f}%, the 95th-percentile gross exposure reached {v2["p95_gross_exposure_pct"]:.2f}%, and the strategy spent {int(v2["days_gross_over_95pct"])} trading days above 95% gross exposure. By contrast, V3 was much less aggressive, with average gross exposure of only {v3["avg_gross_exposure_pct"]:.2f}% and no days above 95% gross exposure. This comparison indicates that the V2 design left very little headroom for adverse gaps, slippage, or concurrent rebalancing demands, whereas V3 maintained a far more conservative capital profile.

The operational symptoms of this pressure are shown in Figure 3.3.3b. V2 generated {int(v2["multi_order_days"])} multi-order days and {int(v2["duplicate_same_series_days"])} days on which the same series was targeted more than once within the same session, compared with only {int(v3["multi_order_days"])} and {int(v3["duplicate_same_series_days"])} respectively in V3. Figure 3.3.3c provides a concrete example from the early Part 3 window, where repeated same-series TF rebalancing occurred on consecutive days while overall capital usage was already elevated. This pattern makes the portfolio look operationally unstable: even if the framework prevented literal negative-cash execution, the strategy was still repeatedly trying to recycle large amounts of capital with minimal buffer.

The reason is structural. In V2, the TF, MR, and GARCH legs each called `order_target_percent` independently under static weights, but there was no explicit portfolio-level gross cap to coordinate the combined exposure. The framework-level overspend guard only checked whether forecast next-open cash would fall below zero, so it served as a reactive safety valve rather than a proactive position-budgeting rule. V3 addressed this weakness more directly by computing desired allocations jointly, scaling them back under `gross_cap=1.00`, and applying a rebalance tolerance to avoid unnecessary order churn. For Chapter 3.3.3, the most persuasive conclusion is therefore that V2 suffered from overspending pressure because its capital allocation logic was too close to the full-budget boundary and too willing to rebalance repeatedly, while V3 improved robustness by explicitly constraining both gross exposure and rebalancing frequency.

References:
- Figure 3.3.3a: [figures/{figure_paths["gross"].name}](figures/{figure_paths["gross"].name})
- Figure 3.3.3b: [figures/{figure_paths["orders"].name}](figures/{figure_paths["orders"].name})
- Figure 3.3.3c: [figures/{figure_paths["window"].name}](figures/{figure_paths["window"].name})
- Table 3.3.3a: [overspending_pressure_summary.csv](overspending_pressure_summary.csv)
- Table 3.3.3b: [overspending_event_examples.csv](overspending_event_examples.csv)
"""
    (DOC_DIR / "section_3_3_3_draft.md").write_text(draft_text, encoding="utf-8")


def main() -> None:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    v2 = _load_trace("v2_part3_bar_trace.csv")
    v3 = _load_trace("v3_part3_bar_trace.csv")
    progression = pd.read_csv(CH3_DIR / "portfolio_progression_v1_v2_v3.csv")

    v2_activity = float(progression.loc[(progression["version"] == "V2") & (progression["dataset_key"] == "part3"), "activity_pct"].iloc[0])
    v3_activity = float(progression.loc[(progression["version"] == "V3") & (progression["dataset_key"] == "part3"), "activity_pct"].iloc[0])

    summary_rows = [
        build_pressure_summary("V2", v2, v2_activity),
        build_pressure_summary("V3", v3, v3_activity),
    ]
    summary_df = pd.DataFrame(summary_rows)
    event_rows = build_event_examples("V2", v2) + build_event_examples("V3", v3)
    event_df = pd.DataFrame(event_rows)

    summary_df.to_csv(DOC_DIR / "overspending_pressure_summary.csv", index=False)
    event_df.to_csv(DOC_DIR / "overspending_event_examples.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    shutil.copy2(CH3_DIR / "structure_controls_comparison.csv", DOC_DIR / "structure_controls_comparison.csv")

    figure_paths = {
        "gross": save_pressure_figure(v2, v3),
        "orders": save_order_pressure_figure(summary_df),
        "window": save_v2_window_figure(v2),
    }
    write_reference_pack(summary_df, figure_paths)
    print(f"DOC pack generated at: {DOC_DIR}")


if __name__ == "__main__":
    main()
