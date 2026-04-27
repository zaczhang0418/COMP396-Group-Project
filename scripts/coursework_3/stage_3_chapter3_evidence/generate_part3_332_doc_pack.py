from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = ROOT / "output" / "coursework_3_stage2_v3_archive" / "chapter3_analysis"
DOC_DIR = ROOT / "DOC" / "coursework_3_stage3_v2v3_3_3_2"
FIG_DIR = DOC_DIR / "figures"


def _load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(SRC_DIR / name)


def _fmt_num(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}"


def _fmt_pct(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}%"


def _fmt_money(value: float) -> str:
    return f"GBP {value:,.2f}"


def build_asset_binding_summary(asset_df: pd.DataFrame) -> pd.DataFrame:
    role_map = {
        ("tf", "01"): "deployed in V2 and V3",
        ("mr", "10"): "V2 selected",
        ("mr", "09"): "V3 selected",
        ("mr", "06"): "best OOS MR candidate",
        ("garch", "07"): "V2 selected",
        ("garch", "09"): "positive Part 2 GARCH alternative",
        ("garch", "05"): "best OOS GARCH candidate",
    }
    rows = asset_df.copy()
    rows["role_label"] = rows.apply(
        lambda r: role_map.get((r["strategy_family"], str(r["asset"]).zfill(2)), r["selection_context"]),
        axis=1,
    )
    rows["selected_in_v2"] = rows["role_label"].eq("V2 selected") | rows["role_label"].eq("deployed in V2 and V3")
    rows["selected_in_v3"] = rows["role_label"].eq("V3 selected") | rows["role_label"].eq("deployed in V2 and V3")
    rows["transfer_delta"] = rows["oos_to_part2_true_pd_delta"]
    cols = [
        "strategy_family",
        "asset",
        "data_name",
        "role_label",
        "family_oos_rank",
        "oos_true_pd_ratio",
        "part2_true_pd_ratio",
        "transfer_delta",
        "part2_return_pct",
        "selected_in_v2",
        "selected_in_v3",
        "source_ref",
        "source_path",
    ]
    return rows[cols].sort_values(["strategy_family", "family_oos_rank", "asset"])


def build_leg_concentration_metrics(leg_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for version, group in leg_df.groupby("version"):
        shares = (group["share_of_abs_leg_pnl_pct"] / 100.0).tolist()
        shares_sorted = sorted(shares, reverse=True)
        hhi = sum(s * s for s in shares)
        effective_legs = 1.0 / hhi if hhi > 0 else 0.0
        rows.append(
            {
                "version": version,
                "active_leg_count": int(len(group)),
                "top_leg": group.sort_values("share_of_abs_leg_pnl_pct", ascending=False).iloc[0]["leg"],
                "top_series": group.sort_values("share_of_abs_leg_pnl_pct", ascending=False).iloc[0]["series"],
                "top_leg_share_pct": 100.0 * shares_sorted[0],
                "second_leg_share_pct": 100.0 * shares_sorted[1] if len(shares_sorted) > 1 else 0.0,
                "dominance_gap_pct": 100.0 * (shares_sorted[0] - (shares_sorted[1] if len(shares_sorted) > 1 else 0.0)),
                "hhi_concentration": hhi,
                "effective_leg_count": effective_legs,
                "meaningful_legs_over_10pct": int(sum(1 for s in shares if s >= 0.10)),
                "positive_leg_count": int(group["is_positive_pnl"].fillna(False).sum()),
                "total_abs_leg_pnl": float(group["final_cumPnL"].abs().sum()),
            }
        )
    return pd.DataFrame(rows).sort_values("version")


def save_asset_binding_figure(binding_df: pd.DataFrame) -> Path:
    figure_df = binding_df[binding_df["strategy_family"].isin(["mr", "garch"])].copy()
    figure_df["asset_label"] = figure_df["strategy_family"].str.upper() + figure_df["asset"].astype(str).str.zfill(2)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True, sharey=True)
    family_order = [("mr", "Mean-Reversion Candidates"), ("garch", "GARCH Candidates")]
    colors = {"OOS true PD": "#ef6c00", "Part 2 true PD": "#1f6aa5"}

    for ax, (family, title) in zip(axes, family_order):
        fam = figure_df[figure_df["strategy_family"] == family].copy()
        x = range(len(fam))
        width = 0.35
        ax.bar(
            [i - width / 2 for i in x],
            fam["oos_true_pd_ratio"],
            width=width,
            color=colors["OOS true PD"],
            label="OOS true PD",
        )
        ax.bar(
            [i + width / 2 for i in x],
            fam["part2_true_pd_ratio"],
            width=width,
            color=colors["Part 2 true PD"],
            label="Part 2 true PD",
        )
        ax.axhline(0.0, color="black", linewidth=1.0, alpha=0.7)
        ax.set_xticks(list(x))
        ax.set_xticklabels(fam["asset_label"], rotation=0)
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.3)
        for idx, row in enumerate(fam.itertuples(index=False)):
            if row.selected_in_v2:
                ax.text(idx, ax.get_ylim()[1] * 0.92, "V2", ha="center", va="top", fontsize=9, color="#b71c1c")
            if row.selected_in_v3:
                ax.text(idx, ax.get_ylim()[1] * 0.82, "V3", ha="center", va="top", fontsize=9, color="#0d47a1")

    axes[0].set_ylabel("True PD Ratio")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False)

    out_path = FIG_DIR / "figure_3_3_2a_asset_binding_transfer.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


def save_leg_contribution_share_figure(leg_df: pd.DataFrame) -> Path:
    plot_df = leg_df.copy()
    plot_df["label"] = plot_df["leg"] + " (" + plot_df["series"] + ")"
    colors = {
        "tf": "#b24a2b",
        "mr": "#7b1fa2",
        "mr09": "#1f6aa5",
        "garch": "#00897b",
    }

    versions = ["V1", "V2", "V3"]
    fig, ax = plt.subplots(figsize=(12, 4.8), constrained_layout=True)
    left = [0.0] * len(versions)

    for leg in ["tf", "mr", "mr09", "garch"]:
        vals = []
        labels = []
        for version in versions:
            row = plot_df[(plot_df["version"] == version) & (plot_df["leg"] == leg)]
            if row.empty:
                vals.append(0.0)
                labels.append("")
            else:
                vals.append(float(row.iloc[0]["share_of_abs_leg_pnl_pct"]))
                labels.append(row.iloc[0]["label"])

        bars = ax.barh(versions, vals, left=left, color=colors[leg], label=leg.upper())
        for i, (bar, val, label) in enumerate(zip(bars, vals, labels)):
            if val >= 7.5:
                ax.text(
                    left[i] + val / 2,
                    bar.get_y() + bar.get_height() / 2,
                    f"{label}\n{val:.1f}%",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="white",
                )
        left = [l + v for l, v in zip(left, vals)]

    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of Absolute Part 3 Leg PnL (%)")
    ax.set_title("Part 3 Leg Contribution Concentration Across V1, V2, and V3")
    ax.grid(axis="x", alpha=0.3)
    ax.legend(loc="lower right")

    out_path = FIG_DIR / "figure_3_3_2b_part3_leg_contribution_shares.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


def save_concentration_metrics_figure(metrics_df: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)

    axes[0].bar(metrics_df["version"], metrics_df["top_leg_share_pct"], color=["#8d6e63", "#b24a2b", "#1f6aa5"])
    axes[0].set_title("Top-Leg Dominance")
    axes[0].set_ylabel("Top Leg Share (%)")
    axes[0].set_ylim(0, 110)
    axes[0].grid(axis="y", alpha=0.3)
    for idx, row in metrics_df.iterrows():
        axes[0].text(row["version"], row["top_leg_share_pct"] + 2, f'{row["top_leg_share_pct"]:.1f}%', ha="center")

    axes[1].bar(metrics_df["version"], metrics_df["effective_leg_count"], color=["#8d6e63", "#b24a2b", "#1f6aa5"])
    axes[1].set_title("Effective Number of Contributing Legs")
    axes[1].set_ylabel("Effective Legs")
    axes[1].set_ylim(0, max(3.0, metrics_df["effective_leg_count"].max() + 0.4))
    axes[1].grid(axis="y", alpha=0.3)
    for idx, row in metrics_df.iterrows():
        axes[1].text(row["version"], row["effective_leg_count"] + 0.06, f'{row["effective_leg_count"]:.2f}', ha="center")

    out_path = FIG_DIR / "figure_3_3_2c_concentration_metrics.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


def write_reference_pack(
    binding_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    leg_df: pd.DataFrame,
    figure_paths: dict[str, Path],
) -> None:
    v2_metrics = metrics_df[metrics_df["version"] == "V2"].iloc[0]
    v3_metrics = metrics_df[metrics_df["version"] == "V3"].iloc[0]
    mr10 = binding_df[(binding_df["strategy_family"] == "mr") & (binding_df["asset"].astype(str).str.zfill(2) == "10")].iloc[0]
    mr09 = binding_df[(binding_df["strategy_family"] == "mr") & (binding_df["asset"].astype(str).str.zfill(2) == "09")].iloc[0]
    g07 = binding_df[(binding_df["strategy_family"] == "garch") & (binding_df["asset"].astype(str).str.zfill(2) == "07")].iloc[0]
    g09 = binding_df[(binding_df["strategy_family"] == "garch") & (binding_df["asset"].astype(str).str.zfill(2) == "09")].iloc[0]

    ref_text = f"""# Section 3.3.2 Reference Pack

This folder contains the evidence pack for Chapter 3.3.2 on asset hard binding and uneven leg contribution.

## Core Questions This Section Answers

1. Did V2 keep legacy asset choices even when their transfer into Part 2 was weak?
2. Even when V3 improved performance, was the final Part 3 result still dominated by one leg rather than jointly supported across legs?

## Suggested Main-Text Figures

1. Figure 3.3.2a: [Asset-binding transfer evidence](figures/{figure_paths["binding"].name})
   Data source: [asset_binding_transfer_summary.csv](asset_binding_transfer_summary.csv)
   Why to use it: this shows that several selected or candidate assets looked acceptable in OOS, but their Part 2 transfer quality diverged sharply, which is exactly the problem with hard binding.

2. Figure 3.3.2b: [Part 3 leg contribution shares](figures/{figure_paths["share"].name})
   Data source: [part3_leg_breakdown_v1_v2_v3.csv](part3_leg_breakdown_v1_v2_v3.csv)
   Why to use it: this visualises how much of total absolute leg PnL came from each leg in V1, V2, and V3.

3. Figure 3.3.2c: [Concentration metrics](figures/{figure_paths["metrics"].name})
   Data source: [leg_contribution_concentration_metrics.csv](leg_contribution_concentration_metrics.csv)
   Why to use it: this converts the contribution story into compact quantitative indicators such as top-leg share and effective leg count.

## Suggested Main-Text Tables

- Table 3.3.2a: [asset_binding_transfer_summary.csv](asset_binding_transfer_summary.csv)
- Table 3.3.2b: [leg_contribution_concentration_metrics.csv](leg_contribution_concentration_metrics.csv)

## Most Important Numbers To Cite

- MR10, which was selected in V2, had OOS true PD {_fmt_num(float(mr10["oos_true_pd_ratio"]))} but Part 2 true PD {_fmt_num(float(mr10["part2_true_pd_ratio"]))}.
- MR09, later adopted in V3, had OOS true PD {_fmt_num(float(mr09["oos_true_pd_ratio"]))} and Part 2 true PD {_fmt_num(float(mr09["part2_true_pd_ratio"]))}.
- GARCH07, which remained in V2, had OOS true PD {_fmt_num(float(g07["oos_true_pd_ratio"]))} and Part 2 true PD {_fmt_num(float(g07["part2_true_pd_ratio"]))}.
- GARCH09, which was not deployed, still showed a positive Part 2 true PD of {_fmt_num(float(g09["part2_true_pd_ratio"]))}.
- V2 top-leg share was {_fmt_pct(float(v2_metrics["top_leg_share_pct"]))}, with effective leg count {_fmt_num(float(v2_metrics["effective_leg_count"]), 2)}.
- V3 top-leg share was {_fmt_pct(float(v3_metrics["top_leg_share_pct"]))}, with effective leg count {_fmt_num(float(v3_metrics["effective_leg_count"]), 2)}.
"""
    (DOC_DIR / "section_3_3_2_reference_pack.md").write_text(ref_text, encoding="utf-8")

    draft_text = f"""# Section 3.3.2 Draft Text

The first structural weakness in Team01 V2 was asset hard binding. Figure 3.3.2a and Table 3.3.2a show that V2 continued to rely on inherited series choices even though the transfer evidence into Part 2 was weak. For example, MR10, which remained in the V2 combination, achieved an OOS true PD ratio of {_fmt_num(float(mr10["oos_true_pd_ratio"]))} but fell to {_fmt_num(float(mr10["part2_true_pd_ratio"]))} on Part 2. GARCH07 was even less convincing, with OOS true PD {_fmt_num(float(g07["oos_true_pd_ratio"]))} and Part 2 true PD {_fmt_num(float(g07["part2_true_pd_ratio"]))}. This matters because the issue was not simply that every alternative also failed: GARCH09, which was not deployed, still recorded a positive Part 2 true PD of {_fmt_num(float(g09["part2_true_pd_ratio"]))}. The evidence therefore supports the claim that V2 suffered from static asset binding rather than from a uniformly impossible asset universe.

The second weakness was uneven leg contribution. Figure 3.3.2b shows that the V2 Part 3 result was mainly carried by the TF leg, while the MR and GARCH legs contributed far less to total absolute leg PnL. Table 3.3.2b makes this more explicit: V2's top leg contributed {_fmt_pct(float(v2_metrics["top_leg_share_pct"]))} of absolute leg PnL, leaving an effective leg count of only {_fmt_num(float(v2_metrics["effective_leg_count"]), 2)} despite having three active legs. In other words, the portfolio looked diversified in structure but not in realised contribution. V3 improved the overall Part 3 outcome, but Figure 3.3.2c shows that the concentration problem did not disappear; it became more extreme. The top-leg share rose further to {_fmt_pct(float(v3_metrics["top_leg_share_pct"]))}, and the effective leg count fell to {_fmt_num(float(v3_metrics["effective_leg_count"]), 2)}, indicating that the final portfolio was even more dependent on one dominant return engine.

Taken together, these results support a balanced interpretation for Chapter 3.3.2. The V2 design was unconvincing because it combined static asset binding with weak realised diversification across legs. The V3 refinement solved part of the first problem by reconsidering the mapping, but it did not fully solve the second problem because the final Part 3 performance still relied overwhelmingly on the TF leg. This means the section can argue both that reassignment was necessary and that better performance alone does not prove balanced multi-leg robustness.

References:
- Figure 3.3.2a: [figures/{figure_paths["binding"].name}](figures/{figure_paths["binding"].name})
- Figure 3.3.2b: [figures/{figure_paths["share"].name}](figures/{figure_paths["share"].name})
- Figure 3.3.2c: [figures/{figure_paths["metrics"].name}](figures/{figure_paths["metrics"].name})
- Table 3.3.2a: [asset_binding_transfer_summary.csv](asset_binding_transfer_summary.csv)
- Table 3.3.2b: [leg_contribution_concentration_metrics.csv](leg_contribution_concentration_metrics.csv)
"""
    (DOC_DIR / "section_3_3_2_draft.md").write_text(draft_text, encoding="utf-8")


def main() -> None:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    asset_df = _load_csv("asset_reassignment_evidence.csv")
    leg_df = _load_csv("part3_leg_breakdown_v1_v2_v3.csv")
    concentration_df = _load_csv("part3_concentration_summary.csv")

    binding_summary = build_asset_binding_summary(asset_df)
    metrics_df = build_leg_concentration_metrics(leg_df)

    binding_summary.to_csv(DOC_DIR / "asset_binding_transfer_summary.csv", index=False)
    metrics_df.to_csv(DOC_DIR / "leg_contribution_concentration_metrics.csv", index=False)
    shutil.copy2(SRC_DIR / "part3_leg_breakdown_v1_v2_v3.csv", DOC_DIR / "part3_leg_breakdown_v1_v2_v3.csv")
    shutil.copy2(SRC_DIR / "part3_concentration_summary.csv", DOC_DIR / "part3_concentration_summary.csv")
    shutil.copy2(SRC_DIR / "asset_reassignment_evidence.csv", DOC_DIR / "asset_reassignment_evidence.csv")

    figure_paths = {
        "binding": save_asset_binding_figure(binding_summary),
        "share": save_leg_contribution_share_figure(leg_df),
        "metrics": save_concentration_metrics_figure(metrics_df),
    }

    write_reference_pack(
        binding_df=binding_summary,
        metrics_df=metrics_df,
        leg_df=leg_df,
        figure_paths=figure_paths,
    )

    print(f"DOC pack generated at: {DOC_DIR}")


if __name__ == "__main__":
    main()
