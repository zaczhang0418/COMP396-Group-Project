:: ----------------------------------------------------
:: COMP396 “军火库” 一键执行脚本 (V3 - 双视图)
:: ----------------------------------------------------

:: 1. 修复 Windows 终端的中文乱码
CHCP 65001 > nul

@echo off
echo =======================================================
echo --- 🚀 COMP396 EDA 军火库 (V3) ---
echo =======================================================

:: 2. 【 自动清理 】
echo.
echo --- [步骤 1/4] 正在清理旧的图表文件夹... ---
set ANALYSIS_VIEW_DIR=EDA\charts
set ASSET_VIEW_DIR=EDA\charts_by_asset
if exist %ANALYSIS_VIEW_DIR% ( rmdir /s /q %ANALYSIS_VIEW_DIR% )
if exist %ASSET_VIEW_DIR% ( rmdir /s /q %ASSET_VIEW_DIR% )
mkdir %ANALYSIS_VIEW_DIR%
mkdir %ASSET_VIEW_DIR%
echo     -> 已创建新的“干净”图表文件夹。
echo --- ✅ 清理完毕 ---

:: 3. 【 激活环境 】
echo.
echo --- [步骤 2/4] 正在准备 Python 环境... ---
call conda activate comp396
set PYTHONPATH=%PYTHONPATH%;%cd%\EDA
echo --- ✅ 环境 'comp396' 已激活, PYTHONPATH 已设置 ---

:: 4. 【【 阶段一：生成“分析视图” 】】
echo.
echo --- [步骤 3/4] 正在运行 Python 脚本 (生成“分析视图”)... ---
echo (这可能需要几分钟...)
echo.

echo --- [1/10] 正在运行: ACF/PACF (V3) ---
python EDA/eda/plotting/plot_acf_charts.py
echo --- [2/10] 正在运行: Correlation Heatmap (V2) ---
python EDA/eda/plotting/plot_correlation_heatmap.py
echo --- [3/10] 正在运行: GARCH (V2) ---
python EDA/eda/plotting/plot_garch_analysis.py
echo --- [4/10] 正在运行: Hurst (V2) ---
python EDA/eda/plotting/plot_hurst_analysis.py
echo --- [5/10] 正在运行: Quantile Analysis (V2) ---
python EDA/eda/plotting/plot_quantile_analysis.py
echo --- [6/10] 正在运行: Return Histograms (V2) ---
python EDA/eda/plotting/plot_return_histograms.py
echo --- [7/10] 正在运行: RSI Signal (V2) ---
python EDA/eda/plotting/plot_rsi_analysis.py
echo --- [8/10] 正在运行: Seasonality (V2) ---
python EDA/eda/plotting/plot_seasonality_analysis.py
echo --- [9/10] 正在运行: Volatility (V2) ---
python EDA/eda/plotting/plot_volatility.py
echo --- [10/10] 正在运行: Volume (V-Standalone) ---
python EDA/eda/plotting/plot_volume_analysis.py

echo --- ✅ Python 脚本运行完毕。 "分析视图" 已生成在 %ANALYSIS_VIEW_DIR% ---


:: 5. 【【 阶段二：生成“资产视图” (您的需求!) 】】
echo.
echo --- [步骤 4/4] 正在重新组织图表以创建“资产视图”... ---
echo.

:: (循环遍历所有 10 个资产)
for %%a in (01 02 03 04 05 06 07 08 09 10) do (
    echo   ... 正在创建资产 [%%a] 的文件夹
    mkdir %ASSET_VIEW_DIR%\%%a
    
    echo     -> 正在复制 ACF 图表...
    copy %ANALYSIS_VIEW_DIR%\acf\*%%a*_acf*.png %ASSET_VIEW_DIR%\%%a\ > nul
    
    echo     -> 正在复制 GARCH 图表...
    copy %ANALYSIS_VIEW_DIR%\garch\*garch*%%a*.png %ASSET_VIEW_DIR%\%%a\ > nul
    
    echo     -> 正在复制 Hurst 图表...
    copy %ANALYSIS_VIEW_DIR%\hurst\*hurst*%%a*.png %ASSET_VIEW_DIR%\%%a\ > nul
    
    echo     -> 正在复制 Histogram 图表...
    copy %ANALYSIS_VIEW_DIR%\histograms\*%%a*_histogram*.png %ASSET_VIEW_DIR%\%%a\ > nul
    
    echo     -> 正在复制 RSI 图表...
    copy %ANALYSIS_VIEW_DIR%\rsi_analysis\*rsi*%%a*.png %ASSET_VIEW_DIR%\%%a\ > nul
    
    echo     -> 正在复制 Seasonality 图表...
    copy %ANALYSIS_VIEW_DIR%\seasonality\*seasonality*%%a*.png %ASSET_VIEW_DIR%\%%a\ > nul
    
    echo     -> 正在复制 Volatility 图表...
    copy %ANALYSIS_VIEW_DIR%\volatility\*%%a*_volatility*.png %ASSET_VIEW_DIR%\%%a\ > nul
    
    echo     -> 正在复制 Volume 图表...
    copy %ANALYSIS_VIEW_DIR%\volume_analysis\*volume*%%a*.png %ASSET_VIEW_DIR%\%%a\ > nul
)
echo --- ✅ “资产视图” 已生成在 %ASSET_VIEW_DIR% ---


echo.
echo =======================================================
echo --- ✅ “军火库” (V3) 全部执行完毕 ---
echo --- 您现在拥有【两种】图表视图 ---
echo =======================================================
pause