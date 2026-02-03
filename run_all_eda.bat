:: ----------------------------------------------------
:: COMP396 “军火库” 一键执行脚本 (V3 - 双视图)
:: ----------------------------------------------------

:: 1. 修复 Windows 终端的中文乱码
CHCP 65001 > nul

@echo off
:: --- [配置区域] 在这里修改数据集名称 (PART1 / PART2) ---
set DATASET_NAME=PART1
:: ----------------------------------------------------

set OUTPUT_DIR=EDA\output\%DATASET_NAME%
set ANALYSIS_VIEW_DIR=%OUTPUT_DIR%\charts
set ASSET_VIEW_DIR=%OUTPUT_DIR%\charts_by_asset
if exist %OUTPUT_DIR% ( rmdir /s /q %OUTPUT_DIR% )
mkdir %ANALYSIS_VIEW_DIR%
mkdir %ASSET_VIEW_DIR%
call conda activate comp396
set PYTHONPATH=%PYTHONPATH%;%cd%\EDA
python EDA/plotting/plot_acf_charts.py %DATASET_NAME%
python EDA/plotting/plot_correlation_heatmap.py %DATASET_NAME%
python EDA/plotting/plot_garch_analysis.py %DATASET_NAME%
python EDA/plotting/plot_hurst_analysis.py %DATASET_NAME%
python EDA/plotting/plot_quantile_analysis.py %DATASET_NAME%
python EDA/plotting/plot_return_histograms.py %DATASET_NAME%
python EDA/plotting/plot_rsi_analysis.py %DATASET_NAME%
python EDA/plotting/plot_seasonality_analysis.py %DATASET_NAME%
python EDA/plotting/plot_volatility.py %DATASET_NAME%
python EDA/plotting/plot_volume_analysis.py %DATASET_NAME%

:: (循环遍历所有 10 个资产)
for %%a in (01 02 03 04 05 06 07 08 09 10) do (
    mkdir %ASSET_VIEW_DIR%\%%a
    copy %ANALYSIS_VIEW_DIR%\acf\*%%a*_acf*.png %ASSET_VIEW_DIR%\%%a\ > nul
    copy %ANALYSIS_VIEW_DIR%\garch\*garch*%%a*.png %ASSET_VIEW_DIR%\%%a\ > nul
    copy %ANALYSIS_VIEW_DIR%\hurst\*hurst*%%a*.png %ASSET_VIEW_DIR%\%%a\ > nul
    copy %ANALYSIS_VIEW_DIR%\histograms\*%%a*_histogram*.png %ASSET_VIEW_DIR%\%%a\ > nul
    copy %ANALYSIS_VIEW_DIR%\rsi_analysis\*rsi*%%a*.png %ASSET_VIEW_DIR%\%%a\ > nul
    copy %ANALYSIS_VIEW_DIR%\seasonality\*seasonality*%%a*.png %ASSET_VIEW_DIR%\%%a\ > nul
    copy %ANALYSIS_VIEW_DIR%\volatility\*%%a*_volatility*.png %ASSET_VIEW_DIR%\%%a\ > nul
    copy %ANALYSIS_VIEW_DIR%\volume_analysis\*volume*%%a*.png %ASSET_VIEW_DIR%\%%a\ > nul
)