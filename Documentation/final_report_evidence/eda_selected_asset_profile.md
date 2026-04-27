# EDA Selected-Asset Profile for V2 Binding

Source data: `EDA/output/stage_4_part123_overview/stage_4_asset_summary.csv`.
The table below summarises the Part 2 EDA evidence for the three assets used in
the Team01 V2 binding: TF on series 1, GARCH on series 7, and MR on series 10.

| Asset | V2 role | Part 2 total return | Annualized volatility | EDA interpretation | Supporting charts |
| --- | --- | ---: | ---: | --- | --- |
| 01 | TF / trend-following leg | 69.07% | 29.15% | Strong directional movement with meaningful volatility, making it a plausible carrier for trend continuation logic. | `EDA/output/stage_4_part123_overview/dataset_runs/PART2/charts_by_asset/01/acf/stage_4_acf_pacf_asset_01_zoomed.png`; `EDA/output/stage_4_part123_overview/dataset_runs/PART2/charts_by_asset/01/hurst/stage_4_hurst_asset_01_w252.png`; `EDA/output/stage_4_part123_overview/dataset_runs/PART2/charts_by_asset/01/volatility/stage_4_volatility_atr_asset_01.png` |
| 07 | GARCH / volatility-aware leg | 3.36% | 2.50% | Low realised volatility and muted return profile, useful as volatility-regime evidence but weaker as a final return driver. | `EDA/output/stage_4_part123_overview/dataset_runs/PART2/charts_by_asset/07/garch/stage_4_garch_diagnostics_asset_07.png`; `EDA/output/stage_4_part123_overview/dataset_runs/PART2/charts_by_asset/07/volatility/stage_4_volatility_atr_asset_07.png`; `EDA/output/stage_4_part123_overview/dataset_runs/PART2/charts_by_asset/07/histograms/stage_4_histogram_asset_07_zoomed.png` |
| 10 | MR / mean-reversion leg | 30.52% | 28.18% | High-volatility asset with large range between minimum and maximum close, giving a reasonable basis for deviation/reversion testing while also creating transfer risk. | `EDA/output/stage_4_part123_overview/dataset_runs/PART2/charts_by_asset/10/acf/stage_4_acf_pacf_asset_10_zoomed.png`; `EDA/output/stage_4_part123_overview/dataset_runs/PART2/charts_by_asset/10/histograms/stage_4_histogram_asset_10_zoomed.png`; `EDA/output/stage_4_part123_overview/dataset_runs/PART2/charts_by_asset/10/volatility/stage_4_volatility_atr_asset_10.png` |

This profile supports the final report's discussion that V2 inherited an
explainable asset binding from the V1/V2 development path, while later CA3
evidence still had reason to reassess whether those bindings remained optimal.
