import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from EDA.settings import TRADING_DAYS_PER_YEAR
from EDA.stage_paths import (
    DATA_ROOT,
    STAGE_4_ASSET_SUMMARY,
    STAGE_4_DATASET_SUMMARY,
    STAGE_4_OUTPUT,
    STAGE_4_RISK_RETURN_OVERVIEW,
    STAGE_4_ROW_COVERAGE,
    STAGE_4_TOTAL_RETURN_HEATMAP,
)

OUTPUT_DIR = STAGE_4_OUTPUT


def _read_asset(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, thousands=",")
    df.columns = df.columns.str.strip().str.strip('"')
    if "Date" in df.columns and "Index" not in df.columns:
        df.rename(columns={"Date": "Index"}, inplace=True)
    if "Index" not in df.columns:
        raise ValueError(f"{path} has no Index/Date column")
    if "Close" not in df.columns:
        raise ValueError(f"{path} has no Close column")

    df["Index"] = pd.to_datetime(df["Index"], errors="coerce")
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    if "Volume" in df.columns:
        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")
    else:
        df["Volume"] = np.nan

    df.dropna(subset=["Index", "Close"], inplace=True)
    df.sort_values("Index", inplace=True)
    return df


def _asset_summary(dataset: str, asset_path: Path) -> dict[str, object]:
    df = _read_asset(asset_path)
    close = df["Close"]
    log_returns = np.log(close / close.shift(1)).replace([np.inf, -np.inf], np.nan).dropna()

    return {
        "dataset": dataset,
        "asset": asset_path.stem,
        "rows": int(len(df)),
        "start_date": df["Index"].min().date().isoformat(),
        "end_date": df["Index"].max().date().isoformat(),
        "close_start": float(close.iloc[0]),
        "close_end": float(close.iloc[-1]),
        "total_return": float(close.iloc[-1] / close.iloc[0] - 1),
        "mean_daily_log_return": float(log_returns.mean()) if not log_returns.empty else np.nan,
        "annualized_volatility": float(log_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)) if len(log_returns) > 1 else np.nan,
        "min_close": float(close.min()),
        "max_close": float(close.max()),
        "avg_volume": float(df["Volume"].mean()) if "Volume" in df.columns else np.nan,
        "missing_close": int(df["Close"].isna().sum()),
        "missing_volume": int(df["Volume"].isna().sum()) if "Volume" in df.columns else 0,
    }


def build_summaries(datasets: list[str]) -> pd.DataFrame:
    rows = []
    for dataset in datasets:
        data_dir = DATA_ROOT / dataset
        if not data_dir.exists():
            print(f"[WARN] Missing dataset folder: {data_dir}")
            continue
        for asset_path in sorted(data_dir.glob("*.csv")):
            try:
                rows.append(_asset_summary(dataset, asset_path))
            except Exception as exc:
                print(f"[WARN] Skipping {dataset}/{asset_path.name}: {exc}")

    if not rows:
        raise RuntimeError("No asset summaries could be built.")

    return pd.DataFrame(rows)


def _dataset_summary(asset_summary: pd.DataFrame) -> pd.DataFrame:
    grouped = asset_summary.groupby("dataset", sort=False)
    return grouped.agg(
        asset_count=("asset", "nunique"),
        total_rows=("rows", "sum"),
        min_rows=("rows", "min"),
        max_rows=("rows", "max"),
        start_date=("start_date", "min"),
        end_date=("end_date", "max"),
        mean_total_return=("total_return", "mean"),
        median_total_return=("total_return", "median"),
        mean_annualized_volatility=("annualized_volatility", "mean"),
        mean_daily_log_return=("mean_daily_log_return", "mean"),
        mean_avg_volume=("avg_volume", "mean"),
    ).reset_index()


def _plot_total_return_heatmap(asset_summary: pd.DataFrame, save_path: Path) -> None:
    pivot = asset_summary.pivot(index="dataset", columns="asset", values="total_return")
    fig, ax = plt.subplots(figsize=(12, 4.8))
    im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn")
    ax.set_xticks(range(len(pivot.columns)), pivot.columns)
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    ax.set_title("Total Return by Dataset and Asset")
    ax.set_xlabel("Asset")
    ax.set_ylabel("Dataset")

    for y in range(pivot.shape[0]):
        for x in range(pivot.shape[1]):
            value = pivot.iloc[y, x]
            if pd.notna(value):
                ax.text(x, y, f"{value:.1%}", ha="center", va="center", fontsize=8)

    fig.colorbar(im, ax=ax, label="Total return")
    fig.tight_layout()
    fig.savefig(save_path, dpi=160)
    plt.close(fig)


def _plot_risk_return(asset_summary: pd.DataFrame, save_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 6))
    datasets = list(asset_summary["dataset"].drop_duplicates())
    cmap = plt.get_cmap("tab10")

    for idx, dataset in enumerate(datasets):
        subset = asset_summary[asset_summary["dataset"] == dataset]
        ax.scatter(
            subset["annualized_volatility"],
            subset["mean_daily_log_return"],
            label=dataset,
            s=60,
            alpha=0.8,
            color=cmap(idx % 10),
        )
        for _, row in subset.iterrows():
            ax.annotate(
                row["asset"],
                (row["annualized_volatility"], row["mean_daily_log_return"]),
                fontsize=7,
                xytext=(4, 3),
                textcoords="offset points",
            )

    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Risk/Return Overview by Dataset")
    ax.set_xlabel("Annualized volatility")
    ax.set_ylabel("Mean daily log return")
    ax.legend(title="Dataset")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=160)
    plt.close(fig)


def _plot_row_coverage(asset_summary: pd.DataFrame, save_path: Path) -> None:
    pivot = asset_summary.pivot(index="asset", columns="dataset", values="rows")
    fig, ax = plt.subplots(figsize=(11, 5.5))
    pivot.plot(kind="bar", ax=ax)
    ax.set_title("Row Coverage by Asset and Dataset")
    ax.set_xlabel("Asset")
    ax.set_ylabel("Rows")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=160)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build cross-dataset EDA stage 4 summaries.")
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=["PART1", "PART2", "PART3", "PART123"],
        help="Datasets under DATA to include in the overview.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    datasets = [dataset.upper() for dataset in args.datasets]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    asset_summary = build_summaries(datasets)
    dataset_summary = _dataset_summary(asset_summary)

    asset_summary.to_csv(OUTPUT_DIR / STAGE_4_ASSET_SUMMARY, index=False)
    dataset_summary.to_csv(OUTPUT_DIR / STAGE_4_DATASET_SUMMARY, index=False)

    _plot_total_return_heatmap(asset_summary, OUTPUT_DIR / STAGE_4_TOTAL_RETURN_HEATMAP)
    _plot_risk_return(asset_summary, OUTPUT_DIR / STAGE_4_RISK_RETURN_OVERVIEW)
    _plot_row_coverage(asset_summary, OUTPUT_DIR / STAGE_4_ROW_COVERAGE)

    print(f"[success] Overview saved to {OUTPUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
