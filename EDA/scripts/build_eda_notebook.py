import base64
from datetime import datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from EDA.settings import (
    ACF_LAGS,
    ACF_YLIM,
    ATR_WINDOW,
    HURST_WINDOW,
    N_QUANTILES,
    QUANTILE_TESTS,
    TRADING_DAYS_PER_YEAR,
    VOL_LONG_WINDOW,
    VOL_SHORT_WINDOW,
)
from EDA.stage_paths import (
    STAGE_4_ANALYSIS_REPORT,
    STAGE_4_ASSET_SUMMARY,
    STAGE_4_DATASET_SUMMARY,
    STAGE_4_OUTPUT,
    STAGE_4_RISK_RETURN_OVERVIEW,
    STAGE_4_ROW_COVERAGE,
    STAGE_4_TOTAL_RETURN_HEATMAP,
    STAGE_5_NOTEBOOK,
)


NOTEBOOK_PATH = STAGE_5_NOTEBOOK
OVERVIEW_DIR = STAGE_4_OUTPUT
ANALYSIS_REPORT = STAGE_4_ANALYSIS_REPORT


def _cell(cell_type: str, source: str, outputs=None, execution_count=None) -> dict:
    cell = {
        "cell_type": cell_type,
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }
    if cell_type == "code":
        cell["execution_count"] = execution_count
        cell["outputs"] = outputs or []
    return cell


def _stream(text: str) -> dict:
    if not text.endswith("\n"):
        text += "\n"
    return {
        "name": "stdout",
        "output_type": "stream",
        "text": text.splitlines(keepends=True),
    }


def _image_output(path: Path) -> dict:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return {
        "data": {"image/png": encoded, "text/plain": [f"<Image: {path.name}>"]},
        "metadata": {},
        "output_type": "display_data",
    }


def _fmt_pct(value: float) -> str:
    return f"{value:.2%}" if pd.notna(value) else "n/a"


def _dataset_overview_text() -> str:
    path = OVERVIEW_DIR / STAGE_4_DATASET_SUMMARY
    if not path.exists():
        return "stage_4_dataset_summary.csv is missing. Run .\\EDA\\run_all_eda.bat OVERVIEW first."

    df = pd.read_csv(path)
    lines = [
        "Dataset overview",
        "================",
        "",
        f"{'Dataset':<8} {'Assets':>6} {'Rows':>8} {'Date range':<25} {'Mean return':>12} {'Mean vol':>10}",
        "-" * 75,
    ]
    for _, row in df.iterrows():
        date_range = f"{row['start_date']} to {row['end_date']}"
        lines.append(
            f"{row['dataset']:<8} {int(row['asset_count']):>6} {int(row['total_rows']):>8,} "
            f"{date_range:<25} {_fmt_pct(row['mean_total_return']):>12} "
            f"{_fmt_pct(row['mean_annualized_volatility']):>10}"
        )
    return "\n".join(lines)


def _asset_snapshot_text(dataset: str = "PART123") -> str:
    path = OVERVIEW_DIR / STAGE_4_ASSET_SUMMARY
    if not path.exists():
        return "stage_4_asset_summary.csv is missing. Run .\\EDA\\run_all_eda.bat OVERVIEW first."

    df = pd.read_csv(path)
    subset = df[df["dataset"] == dataset].copy()
    if subset.empty:
        return f"No asset rows found for {dataset}."

    best = subset.sort_values("total_return", ascending=False).head(3)
    weakest = subset.sort_values("total_return", ascending=True).head(3)
    riskiest = subset.sort_values("annualized_volatility", ascending=False).head(3)

    lines = [f"{dataset} asset snapshot", "=" * (len(dataset) + 15), ""]
    lines.append("Top total return assets:")
    for _, row in best.iterrows():
        lines.append(f"- Asset {row['asset']}: {_fmt_pct(row['total_return'])}, vol {_fmt_pct(row['annualized_volatility'])}")

    lines.append("")
    lines.append("Weakest total return assets:")
    for _, row in weakest.iterrows():
        lines.append(f"- Asset {row['asset']}: {_fmt_pct(row['total_return'])}, vol {_fmt_pct(row['annualized_volatility'])}")

    lines.append("")
    lines.append("Highest volatility assets:")
    for _, row in riskiest.iterrows():
        lines.append(f"- Asset {row['asset']}: vol {_fmt_pct(row['annualized_volatility'])}, return {_fmt_pct(row['total_return'])}")

    return "\n".join(lines)


def _part123_analysis_text() -> str:
    if not ANALYSIS_REPORT.exists():
        return "stage_4_latest_analysis.md is missing. Run .\\EDA\\run_all_eda.bat ALL first."

    text = ANALYSIS_REPORT.read_text(encoding="utf-8", errors="replace")
    start = text.find("## PART123")
    if start == -1:
        return "PART123 section was not found in stage_4_latest_analysis.md."
    next_section = text.find("\n## PART", start + 1)
    section = text[start:] if next_section == -1 else text[start:next_section]
    return section.strip()


def _settings_text() -> str:
    tests = ", ".join(
        f"{name}: lookback={lookback}, forward={forward}"
        for name, lookback, forward in QUANTILE_TESTS
    )
    return "\n".join(
        [
            "Active EDA method settings",
            "==========================",
            f"Trading days per year: {TRADING_DAYS_PER_YEAR}",
            f"ACF/PACF lags: {ACF_LAGS}",
            f"ACF/PACF y-axis range: {ACF_YLIM}",
            f"Hurst rolling window: {HURST_WINDOW}",
            f"Volatility windows: {VOL_SHORT_WINDOW}, {VOL_LONG_WINDOW}",
            f"ATR window: {ATR_WINDOW}",
            f"Quantiles: {N_QUANTILES}",
            f"Quantile tests: {tests}",
        ]
    )


def build_notebook() -> None:
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)

    chart_paths = [
        OVERVIEW_DIR / STAGE_4_TOTAL_RETURN_HEATMAP,
        OVERVIEW_DIR / STAGE_4_RISK_RETURN_OVERVIEW,
        OVERVIEW_DIR / STAGE_4_ROW_COVERAGE,
    ]
    chart_outputs = [_image_output(path) for path in chart_paths if path.exists()]

    cells = [
        _cell(
            "markdown",
            """# EDA Stage 4 Report

This notebook is the streamlined EDA notebook for the current branch. It focuses on the active strategy-relevant analysis for `PART1`, `PART2`, `PART3`, and `PART123`.
""",
        ),
        _cell(
            "code",
            """from pathlib import Path
import pandas as pd

ROOT = Path.cwd()
DATASETS = ["PART1", "PART2", "PART3", "PART123"]
print(f"Project root: {ROOT}")
print(f"Datasets: {', '.join(DATASETS)}")""",
            outputs=[
                _stream(
                    f"Project root: {ROOT}\n"
                    "Datasets: PART1, PART2, PART3, PART123"
                )
            ],
            execution_count=1,
        ),
        _cell(
            "markdown",
            """## Method Settings

These are rolling analysis windows, not fixed calendar slices. The notebook uses the full requested dataset and applies these windows consistently across parts.
""",
        ),
        _cell(
            "code",
            """from EDA.settings import *

print("Active EDA method settings")
print(f"Trading days per year: {TRADING_DAYS_PER_YEAR}")
print(f"ACF/PACF lags: {ACF_LAGS}")
print(f"Hurst rolling window: {HURST_WINDOW}")
print(f"Volatility windows: {VOL_SHORT_WINDOW}, {VOL_LONG_WINDOW}")
print(f"ATR window: {ATR_WINDOW}")
print(f"Quantiles: {N_QUANTILES}")
print(f"Quantile tests: {QUANTILE_TESTS}")""",
            outputs=[_stream(_settings_text())],
            execution_count=2,
        ),
        _cell(
            "markdown",
            """## Dataset Overview

This section summarizes the four data partitions and the combined `PART123` dataset used for the Stage 4 EDA overview.
""",
        ),
        _cell(
            "code",
            """dataset_summary = pd.read_csv(ROOT / "EDA/output/stage_4_part123_overview/stage_4_dataset_summary.csv")
dataset_summary""",
            outputs=[_stream(_dataset_overview_text())],
            execution_count=3,
        ),
        _cell(
            "markdown",
            """## Overview Charts

These are the tracked overview charts generated by `EDA/scripts/build_part123_overview.py`.
""",
        ),
        _cell(
            "code",
            """from IPython.display import Image, display

for chart in [
    ROOT / "EDA/output/stage_4_part123_overview/stage_4_total_return_heatmap.png",
    ROOT / "EDA/output/stage_4_part123_overview/stage_4_risk_return_overview.png",
    ROOT / "EDA/output/stage_4_part123_overview/stage_4_row_coverage.png",
]:
    display(Image(filename=str(chart)))""",
            outputs=chart_outputs,
            execution_count=4,
        ),
        _cell(
            "markdown",
            """## PART123 Analysis Extract

The following values are extracted from `EDA/docs/stage_4_part123_overview/stage_4_latest_analysis.md`, which is generated from the EDA run logs.
""",
        ),
        _cell(
            "code",
            """analysis_text = (ROOT / "EDA/docs/stage_4_part123_overview/stage_4_latest_analysis.md").read_text(encoding="utf-8")
start = analysis_text.index("## PART123")
end = analysis_text.find("\\n## PART", start + 1)
print(analysis_text[start:end if end != -1 else None])""",
            outputs=[_stream(_part123_analysis_text())],
            execution_count=5,
        ),
        _cell(
            "markdown",
            """## Asset-Level Snapshot

This quick readout highlights where the combined `PART123` data is strongest, weakest, and most volatile.
""",
        ),
        _cell(
            "code",
            """asset_summary = pd.read_csv(ROOT / "EDA/output/stage_4_part123_overview/stage_4_asset_summary.csv")
part123 = asset_summary[asset_summary["dataset"] == "PART123"]
print(part123.sort_values("total_return", ascending=False).head(3)[["asset", "total_return", "annualized_volatility"]])
print(part123.sort_values("total_return", ascending=True).head(3)[["asset", "total_return", "annualized_volatility"]])
print(part123.sort_values("annualized_volatility", ascending=False).head(3)[["asset", "total_return", "annualized_volatility"]])""",
            outputs=[_stream(_asset_snapshot_text())],
            execution_count=6,
        ),
        _cell(
            "markdown",
            """## Reproducibility

Run the full EDA workflow with:

```powershell
.\\EDA\\run_all_eda.bat ALL
```

Run the tracked overview only with:

```powershell
.\\EDA\\run_all_eda.bat OVERVIEW
```

The full analysis text is saved to `EDA/docs/stage_4_part123_overview/stage_4_latest_analysis.md`; run status is saved to `EDA/docs/stage_4_part123_overview/stage_4_latest_run.md`.
""",
        ),
    ]

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.11",
            },
            "last_generated": datetime.now().isoformat(timespec="seconds"),
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    NOTEBOOK_PATH.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[notebook] Saved executed EDA notebook to {NOTEBOOK_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    build_notebook()
