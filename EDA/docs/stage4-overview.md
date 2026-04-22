# EDA Stage 4 Overview

Branch: `archive/eda/stage-4-part123-overview`

## Purpose

This branch updates the EDA workflow for the final data layout:

- `DATA/PART1`
- `DATA/PART2`
- `DATA/PART3`
- `DATA/PART123` generated from all three parts

The goal is to keep detailed EDA charts reproducible while tracking a compact cross-part overview for reporting.

## Strategy-Relevant Chart Set

Stage 4 keeps the EDA chart families that map directly to the current strategy development:

- `acf`: autocorrelation and PACF evidence for return persistence or mean reversion.
- `correlation_heatmap`: cross-asset diversification and assignment context.
- `garch`: volatility clustering and GARCH/regime evidence.
- `hurst`: trend-persistence evidence used by the trend-following family.
- `histograms`: return distribution and tail-risk context.
- `quantile_analysis`: momentum/reversal style signal checks.
- `volatility`: ATR and volatility context used by position sizing, filters, and stops.

The following earlier exploratory chart families were removed from the active Stage 4 workflow because they were not used in the current TF/MR/GARCH strategy line:

- `candlesticks`
- `seasonality`
- `rsi_analysis`
- `volume_analysis`

## Rolling Windows

The EDA charts do not use a fixed calendar sub-period. They run on whichever dataset is requested (`PART1`, `PART2`, `PART3`, or `PART123`) and use strategy-relevant rolling windows from `EDA/settings.py`:

- ACF/PACF: 40 lags.
- Volatility: 20-day and 60-day annualized rolling standard deviation.
- ATR: 14-day.
- Hurst: 252-day rolling window.
- Quantile tests: 21-day short-term reversal and 126-day momentum, both evaluated on 21-day forward returns.
- Annualization: 252 trading days.

## Commands

Run the full detailed workflow:

```powershell
.\EDA\run_all_eda.bat ALL
```

Run only the tracked overview:

```powershell
.\EDA\run_all_eda.bat OVERVIEW
```

Each run writes the run status summary to:

```text
EDA/docs/latest-run.md
```

Each run also extracts the EDA analysis values from the generated logs into:

```text
EDA/docs/latest-analysis.md
```

Each run also refreshes the executed EDA notebook:

```text
EDA/notebooks/EDA_Report_and_Justification.ipynb
```

On this machine the batch file auto-detects:

```text
D:\Anacoda\envs\comp396\python.exe
```

## Tracked Outputs

`EDA/output/stage4_overview` contains:

- `asset_summary.csv`
- `dataset_summary.csv`
- `risk_return_overview.png`
- `row_coverage.png`
- `total_return_heatmap.png`

Detailed chart folders under `EDA/output/PART1`, `PART2`, `PART3`, and `PART123` are generated locally and ignored by Git by default. The active per-asset view now contains 5 charts per asset: ACF/PACF, GARCH diagnostics, return histogram, Hurst, and volatility.

## Current Overview Snapshot

| Dataset | Assets | Rows | Date range | Mean total return | Mean annualized volatility |
| --- | ---: | ---: | --- | ---: | ---: |
| PART1 | 10 | 10,000 | 2069-12-08 to 2072-09-02 | -4.29% | 16.49% |
| PART2 | 10 | 10,000 | 2072-09-03 to 2075-05-30 | 27.85% | 19.48% |
| PART3 | 10 | 10,000 | 2075-05-31 to 2078-02-23 | 25.96% | 22.65% |
| PART123 | 10 | 30,000 | 2069-12-08 to 2078-02-23 | 51.88% | 19.77% |
