# Latest EDA Analysis

Generated: `2026-04-22T12:04:13`

This report extracts the analysis values printed by the EDA scripts and combines them with the Stage 4 overview tables.

## Method Settings

- Trading days per year: `252`
- ACF/PACF lags: `40`
- ACF/PACF y-axis range: `(-0.3, 0.3)`
- Hurst rolling window: `252`
- Volatility windows: `20`, `60`
- ATR window: `14`
- Quantiles: `5`
- Quantile tests: `STR_21D: lookback=21, forward=21`, `MOM_126D: lookback=126, forward=21`

## Dataset Overview

| Dataset | Assets | Rows | Date range | Mean total return | Mean annualized volatility |
| --- | ---: | ---: | --- | ---: | ---: |
| PART1 | 10 | 10,000 | 2069-12-08 to 2072-09-02 | -4.29% | 16.49% |
| PART2 | 10 | 10,000 | 2072-09-03 to 2075-05-30 | 27.85% | 19.48% |
| PART3 | 10 | 10,000 | 2075-05-31 to 2078-02-23 | 25.96% | 22.65% |
| PART123 | 10 | 30,000 | 2069-12-08 to 2078-02-23 | 51.88% | 19.77% |

## PART1

Chart families: `acf`, `correlation_heatmap`, `garch`, `histograms`, `hurst`, `quantile_analysis`, `volatility`

### Correlation

- Mean pairwise correlation: `0.0504`
- Max positive correlation: `0.6278`
- Min negative correlation: `-0.1607`

### ADF / Autocorrelation

- Stationary log-return series at 5% level: `10/10`

| Asset | ADF p-value |
| --- | ---: |
| 01 | 0.000000 |
| 02 | 0.000000 |
| 03 | 0.000000 |
| 04 | 0.000000 |
| 05 | 0.000000 |
| 06 | 0.000000 |
| 07 | 0.000000 |
| 08 | 0.000000 |
| 09 | 0.000000 |
| 10 | 0.000000 |

### GARCH Volatility Persistence

- Assets with alpha + beta > 0.95: `8/10`

| Asset | Alpha + Beta |
| --- | ---: |
| 01 | 0.9397 |
| 02 | 0.9527 |
| 03 | 0.9790 |
| 04 | 0.9995 |
| 05 | 0.9877 |
| 06 | 1.0000 |
| 07 | 0.9305 |
| 08 | 0.9893 |
| 09 | 0.9815 |
| 10 | 0.9622 |

### Quantile Signal Tests

| Factor | Q1 forward return | Q5 forward return | T-stat | P-value |
| --- | ---: | ---: | ---: | ---: |
| STR_21D | 0.00216 | -0.00590 | -3.682 | 0.00023 |
| MOM_126D | 0.00400 | -0.00205 | -2.621 | 0.00881 |

### Raw Logs

- `EDA\output\stage_4_part123_overview\dataset_runs\PART1\run_logs\data_loader.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART1\run_logs\plot_acf_charts.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART1\run_logs\plot_correlation_heatmap.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART1\run_logs\plot_garch_analysis.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART1\run_logs\plot_hurst_analysis.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART1\run_logs\plot_quantile_analysis.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART1\run_logs\plot_return_histograms.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART1\run_logs\plot_volatility.log`

## PART2

Chart families: `acf`, `correlation_heatmap`, `garch`, `histograms`, `hurst`, `quantile_analysis`, `volatility`

### Correlation

- Mean pairwise correlation: `0.0778`
- Max positive correlation: `0.8362`
- Min negative correlation: `-0.4425`

### ADF / Autocorrelation

- Stationary log-return series at 5% level: `10/10`

| Asset | ADF p-value |
| --- | ---: |
| 01 | 0.000000 |
| 02 | 0.000000 |
| 03 | 0.000000 |
| 04 | 0.000000 |
| 05 | 0.000000 |
| 06 | 0.000000 |
| 07 | 0.000000 |
| 08 | 0.000000 |
| 09 | 0.000000 |
| 10 | 0.000000 |

### GARCH Volatility Persistence

- Assets with alpha + beta > 0.95: `10/10`

| Asset | Alpha + Beta |
| --- | ---: |
| 01 | 0.9918 |
| 02 | 0.9862 |
| 03 | 0.9944 |
| 04 | 0.9579 |
| 05 | 0.9634 |
| 06 | 0.9928 |
| 07 | 0.9800 |
| 08 | 0.9922 |
| 09 | 0.9918 |
| 10 | 0.9833 |

### Quantile Signal Tests

| Factor | Q1 forward return | Q5 forward return | T-stat | P-value |
| --- | ---: | ---: | ---: | ---: |
| STR_21D | 0.01809 | -0.00422 | -8.777 | 0.00000 |
| MOM_126D | 0.01723 | -0.00675 | -8.860 | 0.00000 |

### Raw Logs

- `EDA\output\stage_4_part123_overview\dataset_runs\PART2\run_logs\data_loader.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART2\run_logs\plot_acf_charts.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART2\run_logs\plot_correlation_heatmap.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART2\run_logs\plot_garch_analysis.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART2\run_logs\plot_hurst_analysis.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART2\run_logs\plot_quantile_analysis.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART2\run_logs\plot_return_histograms.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART2\run_logs\plot_volatility.log`

## PART3

Chart families: `acf`, `correlation_heatmap`, `garch`, `histograms`, `hurst`, `quantile_analysis`, `volatility`

### Correlation

- Mean pairwise correlation: `0.0806`
- Max positive correlation: `0.9025`
- Min negative correlation: `-0.5838`

### ADF / Autocorrelation

- Stationary log-return series at 5% level: `10/10`

| Asset | ADF p-value |
| --- | ---: |
| 01 | 0.000000 |
| 02 | 0.000000 |
| 03 | 0.000000 |
| 04 | 0.000000 |
| 05 | 0.000000 |
| 06 | 0.000000 |
| 07 | 0.000000 |
| 08 | 0.000000 |
| 09 | 0.000000 |
| 10 | 0.000000 |

### GARCH Volatility Persistence

- Assets with alpha + beta > 0.95: `10/10`

| Asset | Alpha + Beta |
| --- | ---: |
| 01 | 0.9924 |
| 02 | 0.9910 |
| 03 | 0.9958 |
| 04 | 0.9895 |
| 05 | 1.0000 |
| 06 | 0.9934 |
| 07 | 0.9946 |
| 08 | 1.0000 |
| 09 | 1.0000 |
| 10 | 0.9978 |

### Quantile Signal Tests

| Factor | Q1 forward return | Q5 forward return | T-stat | P-value |
| --- | ---: | ---: | ---: | ---: |
| STR_21D | 0.01041 | 0.01444 | 1.319 | 0.18722 |
| MOM_126D | 0.00907 | 0.01817 | 2.729 | 0.00638 |

### Raw Logs

- `EDA\output\stage_4_part123_overview\dataset_runs\PART3\run_logs\data_loader.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART3\run_logs\plot_acf_charts.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART3\run_logs\plot_correlation_heatmap.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART3\run_logs\plot_garch_analysis.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART3\run_logs\plot_hurst_analysis.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART3\run_logs\plot_quantile_analysis.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART3\run_logs\plot_return_histograms.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART3\run_logs\plot_volatility.log`

## PART123

Chart families: `acf`, `correlation_heatmap`, `garch`, `histograms`, `hurst`, `quantile_analysis`, `volatility`

### Correlation

- Mean pairwise correlation: `0.0760`
- Max positive correlation: `0.7029`
- Min negative correlation: `-0.4030`

### ADF / Autocorrelation

- Stationary log-return series at 5% level: `10/10`

| Asset | ADF p-value |
| --- | ---: |
| 01 | 0.000000 |
| 02 | 0.000000 |
| 03 | 0.000000 |
| 04 | 0.000000 |
| 05 | 0.000000 |
| 06 | 0.000000 |
| 07 | 0.000000 |
| 08 | 0.000000 |
| 09 | 0.000000 |
| 10 | 0.000000 |

### GARCH Volatility Persistence

- Assets with alpha + beta > 0.95: `10/10`

| Asset | Alpha + Beta |
| --- | ---: |
| 01 | 0.9875 |
| 02 | 0.9943 |
| 03 | 0.9951 |
| 04 | 0.9827 |
| 05 | 0.9973 |
| 06 | 0.9980 |
| 07 | 0.9750 |
| 08 | 0.9965 |
| 09 | 0.9970 |
| 10 | 0.9972 |

### Quantile Signal Tests

| Factor | Q1 forward return | Q5 forward return | T-stat | P-value |
| --- | ---: | ---: | ---: | ---: |
| STR_21D | 0.00997 | 0.00129 | -5.836 | 0.00000 |
| MOM_126D | 0.01037 | 0.00213 | -5.492 | 0.00000 |

### Raw Logs

- `EDA\output\stage_4_part123_overview\dataset_runs\PART123\run_logs\data_loader.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART123\run_logs\plot_acf_charts.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART123\run_logs\plot_correlation_heatmap.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART123\run_logs\plot_garch_analysis.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART123\run_logs\plot_hurst_analysis.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART123\run_logs\plot_quantile_analysis.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART123\run_logs\plot_return_histograms.log`
- `EDA\output\stage_4_part123_overview\dataset_runs\PART123\run_logs\plot_volatility.log`
