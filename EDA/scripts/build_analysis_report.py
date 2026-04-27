import re
from datetime import datetime
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
    STAGE_4_DATASET_RUNS,
    STAGE_4_DATASET_SUMMARY,
    STAGE_4_OUTPUT,
)

REPORT_PATH = STAGE_4_ANALYSIS_REPORT


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _fmt_pct(value: float) -> str:
    return f"{value:.2%}" if pd.notna(value) else "n/a"


def _fmt_float(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}" if pd.notna(value) else "n/a"


def _dataset_dirs() -> list[Path]:
    if not STAGE_4_DATASET_RUNS.exists():
        return []
    order = {"PART1": 1, "PART2": 2, "PART3": 3, "PART123": 4}
    return [
        path
        for path in sorted(STAGE_4_DATASET_RUNS.iterdir(), key=lambda item: order.get(item.name.upper(), 99))
        if path.is_dir() and path.name.upper().startswith("PART")
    ]


def _load_dataset_summary() -> pd.DataFrame:
    path = STAGE_4_OUTPUT / STAGE_4_DATASET_SUMMARY
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _parse_adf(log_text: str) -> list[tuple[str, str]]:
    rows = []
    current_asset = None
    for line in log_text.splitlines():
        match_asset = re.search(r":\s*(\d{2})\s*$", line)
        if match_asset:
            current_asset = match_asset.group(1)
            continue
        match_p = re.search(r"ADF Test .*?p-value:\s*([0-9.]+)", line)
        if match_p and current_asset:
            rows.append((current_asset, match_p.group(1)))
    return rows


def _parse_correlation(log_text: str) -> dict[str, str]:
    keys = {
        "mean": r"Mean Correlation\):\s*([-0-9.]+)",
        "max": r"Max Positive Correlation\):\s*([-0-9.]+)",
        "min": r"Min Negative Correlation\):\s*([-0-9.]+)",
    }
    result = {}
    for key, pattern in keys.items():
        match = re.search(pattern, log_text)
        if match:
            result[key] = match.group(1)
    return result


def _parse_garch(log_text: str) -> list[tuple[str, str]]:
    rows = []
    current_asset = None
    for line in log_text.splitlines():
        match_asset = re.search(r"GARCH\(1,1\) Summary for (\d{2})", line)
        if match_asset:
            current_asset = match_asset.group(1)
            continue
        match_persistence = re.search(r"Alpha \+ Beta\):\s*([0-9.]+)", line)
        if match_persistence and current_asset:
            rows.append((current_asset, match_persistence.group(1)))
            current_asset = None
    return rows


def _parse_quantile(log_text: str) -> list[dict[str, str]]:
    rows = []
    current = None
    quantiles = {}
    for line in log_text.splitlines():
        factor = re.match(r"^(STR_21D|MOM_126D)\s+-", line)
        if factor:
            current = factor.group(1)
            quantiles = {}
            continue

        qrow = re.match(r"^\s*([1-5])\s+([-0-9.]+)\s*$", line)
        if qrow and current:
            quantiles[qrow.group(1)] = qrow.group(2)
            continue

        tstat = re.search(r"T-stat=([-0-9.]+), P-value=([0-9.]+)", line)
        if tstat and current:
            rows.append(
                {
                    "factor": current,
                    "q1": quantiles.get("1", ""),
                    "q5": quantiles.get("5", ""),
                    "t_stat": tstat.group(1),
                    "p_value": tstat.group(2),
                }
            )
            current = None
            quantiles = {}
    return rows


def _chart_families(dataset_dir: Path) -> list[str]:
    charts_dir = dataset_dir / "charts"
    if not charts_dir.exists():
        return []
    families = {path.name for path in charts_dir.iterdir() if path.is_dir()}
    return sorted(families)


def _build_dataset_section(dataset_dir: Path) -> list[str]:
    dataset = dataset_dir.name
    logs = dataset_dir / "run_logs"
    lines = [f"## {dataset}", ""]

    families = _chart_families(dataset_dir)
    if families:
        lines.append(f"Chart families: {', '.join(f'`{item}`' for item in families)}")
        lines.append("")

    corr = _parse_correlation(_read_text(logs / "plot_correlation_heatmap.log"))
    if corr:
        lines.extend(
            [
                "### Correlation",
                "",
                f"- Mean pairwise correlation: `{corr.get('mean', 'n/a')}`",
                f"- Max positive correlation: `{corr.get('max', 'n/a')}`",
                f"- Min negative correlation: `{corr.get('min', 'n/a')}`",
                "",
            ]
        )

    adf_rows = _parse_adf(_read_text(logs / "plot_acf_charts.log"))
    if adf_rows:
        stationary = sum(float(p_value) < 0.05 for _, p_value in adf_rows)
        lines.extend(
            [
                "### ADF / Autocorrelation",
                "",
                f"- Stationary log-return series at 5% level: `{stationary}/{len(adf_rows)}`",
                "",
                "| Asset | ADF p-value |",
                "| --- | ---: |",
            ]
        )
        for asset, p_value in adf_rows:
            lines.append(f"| {asset} | {p_value} |")
        lines.append("")

    garch_rows = _parse_garch(_read_text(logs / "plot_garch_analysis.log"))
    if garch_rows:
        persistent = sum(float(value) > 0.95 for _, value in garch_rows)
        lines.extend(
            [
                "### GARCH Volatility Persistence",
                "",
                f"- Assets with alpha + beta > 0.95: `{persistent}/{len(garch_rows)}`",
                "",
                "| Asset | Alpha + Beta |",
                "| --- | ---: |",
            ]
        )
        for asset, value in garch_rows:
            lines.append(f"| {asset} | {value} |")
        lines.append("")

    quantile_rows = _parse_quantile(_read_text(logs / "plot_quantile_analysis.log"))
    if quantile_rows:
        lines.extend(
            [
                "### Quantile Signal Tests",
                "",
                "| Factor | Q1 forward return | Q5 forward return | T-stat | P-value |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in quantile_rows:
            lines.append(
                f"| {row['factor']} | {row['q1']} | {row['q5']} | {row['t_stat']} | {row['p_value']} |"
            )
        lines.append("")

    lines.extend(
        [
            "### Raw Logs",
            "",
        ]
    )
    for log in sorted(logs.glob("*.log")):
        lines.append(f"- `{log.relative_to(ROOT)}`")
    lines.append("")
    return lines


def build_report() -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Latest EDA Analysis",
        "",
        f"Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "This report extracts the analysis values printed by the EDA scripts and combines them with the Stage 4 overview tables.",
        "",
        "## Method Settings",
        "",
        f"- Trading days per year: `{TRADING_DAYS_PER_YEAR}`",
        f"- ACF/PACF lags: `{ACF_LAGS}`",
        f"- ACF/PACF y-axis range: `{ACF_YLIM}`",
        f"- Hurst rolling window: `{HURST_WINDOW}`",
        f"- Volatility windows: `{VOL_SHORT_WINDOW}`, `{VOL_LONG_WINDOW}`",
        f"- ATR window: `{ATR_WINDOW}`",
        f"- Quantiles: `{N_QUANTILES}`",
        f"- Quantile tests: {', '.join(f'`{name}: lookback={lookback}, forward={forward}`' for name, lookback, forward in QUANTILE_TESTS)}",
        "",
    ]

    summary = _load_dataset_summary()
    if not summary.empty:
        lines.extend(
            [
                "## Dataset Overview",
                "",
                "| Dataset | Assets | Rows | Date range | Mean total return | Mean annualized volatility |",
                "| --- | ---: | ---: | --- | ---: | ---: |",
            ]
        )
        for _, row in summary.iterrows():
            date_range = f"{row['start_date']} to {row['end_date']}"
            lines.append(
                "| {dataset} | {assets} | {rows:,} | {date_range} | {ret} | {vol} |".format(
                    dataset=row["dataset"],
                    assets=int(row["asset_count"]),
                    rows=int(row["total_rows"]),
                    date_range=date_range,
                    ret=_fmt_pct(row["mean_total_return"]),
                    vol=_fmt_pct(row["mean_annualized_volatility"]),
                )
            )
        lines.append("")

    for dataset_dir in _dataset_dirs():
        lines.extend(_build_dataset_section(dataset_dir))

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[analysis] Saved analysis report to {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    build_report()
