# Latest EDA Run

- Requested command: `EDA/run_all_eda.bat ALL`
- Started: `2026-04-22T12:01:39`
- Finished: `2026-04-22T12:04:14`
- Python: `D:\Anacoda\envs\comp396\python.exe`
- Exit code: `0`

## Active Chart Families

The Stage 4 runner only generates strategy-relevant charts:

- `acf`
- `correlation_heatmap`
- `garch`
- `histograms`
- `hurst`
- `quantile_analysis`
- `volatility`

Removed from the active workflow: `candlesticks`, `seasonality`, `rsi_analysis`, `volume_analysis`.

## Merge Steps

### DATA/PART123 (ok)

```text
[INFO] Merging data parts
  parts : PART1, PART2, PART3
  output: DATA\PART123
  [01] PART1, PART2, PART3 -> 3000 rows
  [02] PART1, PART2, PART3 -> 3000 rows
  [03] PART1, PART2, PART3 -> 3000 rows
  [04] PART1, PART2, PART3 -> 3000 rows
  [05] PART1, PART2, PART3 -> 3000 rows
  [06] PART1, PART2, PART3 -> 3000 rows
  [07] PART1, PART2, PART3 -> 3000 rows
  [08] PART1, PART2, PART3 -> 3000 rows
  [09] PART1, PART2, PART3 -> 3000 rows
  [10] PART1, PART2, PART3 -> 3000 rows
[SUCCESS] Data merge completed.
```

## Dataset Runs

### PART1 (ok)

- Output: `EDA\output\PART1`
- Files: `112`
- Size: `13.48 MB`
- Chart families: `acf`, `correlation_heatmap`, `garch`, `histograms`, `hurst`, `quantile_analysis`, `volatility`
- Charts per asset: `5`

| Script | Status | Log |
| --- | --- | --- |
| `EDA/data_loader.py` | ok | `EDA\output\PART1\run_logs\data_loader.log` |
| `EDA/plotting/plot_acf_charts.py` | ok | `EDA\output\PART1\run_logs\plot_acf_charts.log` |
| `EDA/plotting/plot_correlation_heatmap.py` | ok | `EDA\output\PART1\run_logs\plot_correlation_heatmap.log` |
| `EDA/plotting/plot_garch_analysis.py` | ok | `EDA\output\PART1\run_logs\plot_garch_analysis.log` |
| `EDA/plotting/plot_hurst_analysis.py` | ok | `EDA\output\PART1\run_logs\plot_hurst_analysis.log` |
| `EDA/plotting/plot_quantile_analysis.py` | ok | `EDA\output\PART1\run_logs\plot_quantile_analysis.log` |
| `EDA/plotting/plot_return_histograms.py` | ok | `EDA\output\PART1\run_logs\plot_return_histograms.log` |
| `EDA/plotting/plot_volatility.py` | ok | `EDA\output\PART1\run_logs\plot_volatility.log` |

### PART2 (ok)

- Output: `EDA\output\PART2`
- Files: `112`
- Size: `12.88 MB`
- Chart families: `acf`, `correlation_heatmap`, `garch`, `histograms`, `hurst`, `quantile_analysis`, `volatility`
- Charts per asset: `5`

| Script | Status | Log |
| --- | --- | --- |
| `EDA/data_loader.py` | ok | `EDA\output\PART2\run_logs\data_loader.log` |
| `EDA/plotting/plot_acf_charts.py` | ok | `EDA\output\PART2\run_logs\plot_acf_charts.log` |
| `EDA/plotting/plot_correlation_heatmap.py` | ok | `EDA\output\PART2\run_logs\plot_correlation_heatmap.log` |
| `EDA/plotting/plot_garch_analysis.py` | ok | `EDA\output\PART2\run_logs\plot_garch_analysis.log` |
| `EDA/plotting/plot_hurst_analysis.py` | ok | `EDA\output\PART2\run_logs\plot_hurst_analysis.log` |
| `EDA/plotting/plot_quantile_analysis.py` | ok | `EDA\output\PART2\run_logs\plot_quantile_analysis.log` |
| `EDA/plotting/plot_return_histograms.py` | ok | `EDA\output\PART2\run_logs\plot_return_histograms.log` |
| `EDA/plotting/plot_volatility.py` | ok | `EDA\output\PART2\run_logs\plot_volatility.log` |

### PART3 (ok)

- Output: `EDA\output\PART3`
- Files: `112`
- Size: `13.14 MB`
- Chart families: `acf`, `correlation_heatmap`, `garch`, `histograms`, `hurst`, `quantile_analysis`, `volatility`
- Charts per asset: `5`

| Script | Status | Log |
| --- | --- | --- |
| `EDA/data_loader.py` | ok | `EDA\output\PART3\run_logs\data_loader.log` |
| `EDA/plotting/plot_acf_charts.py` | ok | `EDA\output\PART3\run_logs\plot_acf_charts.log` |
| `EDA/plotting/plot_correlation_heatmap.py` | ok | `EDA\output\PART3\run_logs\plot_correlation_heatmap.log` |
| `EDA/plotting/plot_garch_analysis.py` | ok | `EDA\output\PART3\run_logs\plot_garch_analysis.log` |
| `EDA/plotting/plot_hurst_analysis.py` | ok | `EDA\output\PART3\run_logs\plot_hurst_analysis.log` |
| `EDA/plotting/plot_quantile_analysis.py` | ok | `EDA\output\PART3\run_logs\plot_quantile_analysis.log` |
| `EDA/plotting/plot_return_histograms.py` | ok | `EDA\output\PART3\run_logs\plot_return_histograms.log` |
| `EDA/plotting/plot_volatility.py` | ok | `EDA\output\PART3\run_logs\plot_volatility.log` |

### PART123 (ok)

- Output: `EDA\output\PART123`
- Files: `112`
- Size: `12.63 MB`
- Chart families: `acf`, `correlation_heatmap`, `garch`, `histograms`, `hurst`, `quantile_analysis`, `volatility`
- Charts per asset: `5`

| Script | Status | Log |
| --- | --- | --- |
| `EDA/data_loader.py` | ok | `EDA\output\PART123\run_logs\data_loader.log` |
| `EDA/plotting/plot_acf_charts.py` | ok | `EDA\output\PART123\run_logs\plot_acf_charts.log` |
| `EDA/plotting/plot_correlation_heatmap.py` | ok | `EDA\output\PART123\run_logs\plot_correlation_heatmap.log` |
| `EDA/plotting/plot_garch_analysis.py` | ok | `EDA\output\PART123\run_logs\plot_garch_analysis.log` |
| `EDA/plotting/plot_hurst_analysis.py` | ok | `EDA\output\PART123\run_logs\plot_hurst_analysis.log` |
| `EDA/plotting/plot_quantile_analysis.py` | ok | `EDA\output\PART123\run_logs\plot_quantile_analysis.log` |
| `EDA/plotting/plot_return_histograms.py` | ok | `EDA\output\PART123\run_logs\plot_return_histograms.log` |
| `EDA/plotting/plot_volatility.py` | ok | `EDA\output\PART123\run_logs\plot_volatility.log` |

## Overview (ok)

- Output: `EDA\output\stage4_overview`
- Files: `5`
- Size: `0.25 MB`

- `asset_summary.csv`
- `dataset_summary.csv`
- `risk_return_overview.png`
- `row_coverage.png`
- `total_return_heatmap.png`
