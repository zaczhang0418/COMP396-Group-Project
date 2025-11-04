import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
import glob 

# --- 优化点 1: 导入 'acf', 'pacf' 和 'adfuller' (来自队友) ---
from statsmodels.tsa.stattools import acf, pacf, adfuller

# -----------------------------------------------------------------
# (数据加载函数，使用我们昨天的“最终修复版-老师的逻辑”)
# -----------------------------------------------------------------
def load_and_merge_data(data_directory="./DATA/PART1/"):
    csv_files_path = os.path.join(data_directory, "*.csv")
    files = glob.glob(csv_files_path)
    if not files:
        print(f"警告：在 '{data_directory}' 中没有找到 .csv 文件。")
        return pd.DataFrame() 
    dfs = {}
    for f in files:
        asset_name = os.path.basename(f).split('.')[0]
        try:
            data = pd.read_csv(
                f, 
                parse_dates=['Index'], 
                index_col=None, # [我们的修复] 不设置 index_col
                thousands=','   # [我们的修复] 处理逗号
            )
            data.columns = data.columns.str.strip().str.strip('"')
            data.rename(columns={
                'Open': 'open', 'High': 'high', 'Low': 'low',
                'Close': 'close', 'Volume': 'volume',
                'Index': 'Date' # [我们的修复] 重命名 Index
            }, inplace=True)
            
            if 'close' in data.columns:
                data['close'] = pd.to_numeric(data['close'], errors='coerce')
                data.dropna(subset=['close'], inplace=True) 
                
                df = data[['Date', 'close']].rename(columns={'close': asset_name})
                dfs[asset_name] = df
            
        except Exception as e:
            print(f" 警告: 加载 {f} 出错: {e}")

    if not dfs:
        print("❌ 错误: 未能从任何 CSV 文件中加载有效数据。")
        return pd.DataFrame()

    df_list = list(dfs.values())
    merged = df_list[0]
    for df_to_join in df_list[1:]:
        merged = merged.merge(df_to_join, on='Date', how='outer') # [我们的修复] Outer join
    
    merged.set_index('Date', inplace=True)
    merged.sort_index(inplace=True) 
    return merged

# --- [!! 关键升级 !!] ---
# (计算函数，使用 V2 的 'absolute' 版本，以支持队友的 2x2 图表)
def calculate_log_returns(merged_df): 
    log_returns = np.log(merged_df / merged_df.shift(1)).dropna()
    absolute_log_returns = log_returns.abs().dropna()
    # 返回两个值
    return log_returns, absolute_log_returns
# -----------------------------------------------------------------
# (数据加载函数结束)
# -----------------------------------------------------------------


# --- 优化点 2: V3 核心 - 手动绘图辅助函数 (来自队友) ---
def _plot_manual_stem(ax, values, confint, title, nlags, ylim):
    """
    (V3 辅助函数)
    使用 matplotlib.stem 手动绘制 ACF/PACF 图，以控制 Y 轴缩放。
    """
    lags_range = np.arange(len(values))
    # 从 (N, 2) 数组中提取置信区间
    conf_lower = confint[:, 0] - values # acf/pacf 返回的是 (value, [lower, upper])
    conf_upper = confint[:, 1] - values # 我们需要的是 (value, [value-lower, upper-value])
    # 修正：statsmodels acf 返回 (acf, confint), confint 已经是 [lower, upper]
    conf_lower = confint[:, 0]
    conf_upper = confint[:, 1]

    (markerline, stemlines, baseline) = ax.stem(
        lags_range, values, linefmt='-', markerfmt='o', basefmt=' '
    )
    plt.setp(markerline, 'color', 'C0')
    plt.setp(stemlines, 'color', 'C0')

    # 绘制置信区间（蓝色阴影区域）
    ax.fill_between(lags_range, conf_lower, conf_upper, alpha=0.2, color='b', label='95% Conf. Int.')
    
    # --- 优化点 3: 应用手动缩放 (来自队友) ---
    ax.set_title(title, fontsize=10)
    ax.set_ylim(ylim) # !! 关键 !!
    
    # --- 优化点 4: 隐藏 Lag 0 (来自队友) ---
    ax.set_xlim(0.5, nlags + 0.5) 
    
    ax.axhline(0, color='k', linestyle='-', linewidth=0.5)
    ax.grid(True)
    
    # 修复：手动绘图时，Lag 0 的置信区间是 NaN，会导致 fill_between 失败
    # 我们在绘图前处理一下
    conf_lower[0] = 0
    conf_upper[0] = 0
    values[0] = 0 # 我们也把 lag 0 的值设为 0，因为我们不关心它
    # 重新定义 _plot_manual_stem 以处理这个问题

def _plot_manual_stem_v2(ax, values, confint, title, nlags, ylim):
    """
    (V3 辅助函数 - 已修复)
    手动绘制 ACF/PACF 图，并正确处理 Lag 0。
    """
    lags_range = np.arange(len(values))
    conf_lower = confint[:, 0]
    conf_upper = confint[:, 1]

    # [修复] Lag 0 的置信区间是 [nan, nan]，我们手动设为 [0, 0]
    conf_lower[0] = 0
    conf_upper[0] = 0
    
    (markerline, stemlines, baseline) = ax.stem(
        lags_range, values, linefmt='-', markerfmt='o', basefmt=' '
    )
    plt.setp(markerline, 'color', 'C0')
    plt.setp(stemlines, 'color', 'C0')

    ax.fill_between(lags_range, conf_lower, conf_upper, alpha=0.2, color='b', label='95% Conf. Int.')
    
    ax.set_title(title, fontsize=10)
    ax.set_ylim(ylim) 
    ax.set_xlim(0.5, nlags + 0.5) # 隐藏 Lag 0
    ax.axhline(0, color='k', linestyle='-', linewidth=0.5)
    ax.grid(True)

# --- [!! 新增的 API 函数 (给 Notebook 调用) !!] ---
def plot_acf_pacf_plot_v3(
    log_returns_series, 
    absolute_log_returns_series,
    asset_name, 
    lags=40, 
    ylim=(-0.3, 0.3) 
):
    """
    (新增的 V3 API - 供 Notebook 调用)
    “显示” 2x2 四宫格图。
    """
    # [我们从 'save_acf_pacf_plot_v3' 复制所有绘图代码]
    if log_returns_series.empty or absolute_log_returns_series.empty:
        print(f" 警告: {asset_name} 数据为空，跳过绘图。")
        return

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(f'Autocorrelation Analysis (Zoomed) - {asset_name}', fontsize=16, y=1.02)
    alpha = 0.05 
    nlags = lags 

    acf_vals, acf_conf = acf(log_returns_series, nlags=nlags, alpha=alpha, fft=False)
    _plot_manual_stem_v2(axes[0, 0], acf_vals, acf_conf, 'ACF (Log Returns)', nlags, ylim)
    
    pacf_vals, pacf_conf = pacf(log_returns_series, nlags=nlags, alpha=alpha, method='ywm')
    _plot_manual_stem_v2(axes[0, 1], pacf_vals, pacf_conf, 'PACF (Log Returns)', nlags, ylim)
    
    abs_acf_vals, abs_acf_conf = acf(absolute_log_returns_series, nlags=nlags, alpha=alpha, fft=False)
    _plot_manual_stem_v2(axes[1, 0], abs_acf_vals, abs_acf_conf, 'ACF (Absolute Log Returns) - Volatility Proxy', nlags, ylim)

    abs_pacf_vals, abs_pacf_conf = pacf(absolute_log_returns_series, nlags=nlags, alpha=alpha, method='ywm')
    _plot_manual_stem_v2(axes[1, 1], abs_pacf_vals, abs_pacf_conf, 'PACF (Absolute Log Returns) - Volatility Proxy', nlags, ylim)

    plt.tight_layout()
    
    # --- [!! 核心区别: "显示" !!] ---
    plt.show()
# --- 3. 优化的“保存”函数 (V3 - 来自队友) ---
def save_acf_pacf_plot_v3(
    log_returns_series, 
    absolute_log_returns_series,
    asset_name, 
    lags=40, 
    save_path="",
    ylim=(-0.3, 0.3) 
):
    """
    (已优化 V3 - A+++ 级别)
    手动绘制 2x2 四宫格图，并应用 Y 轴缩放。
    """
    if log_returns_series.empty or absolute_log_returns_series.empty:
        print(f" 警告: {asset_name} 数据为空，跳过保存。")
        return

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(f'Autocorrelation Analysis (Zoomed) - {asset_name}', fontsize=16, y=1.02)
    
    alpha = 0.05 # 95% 置信区间
    nlags = lags 

    # --- 1. 上-左: ACF (Log Returns) ---
    acf_vals, acf_conf = acf(log_returns_series, nlags=nlags, alpha=alpha, fft=False) # 使用 fft=False
    _plot_manual_stem_v2(axes[0, 0], acf_vals, acf_conf, 'ACF (Log Returns)', nlags, ylim)
    
    # --- 2. 上-右: PACF (Log Returns) ---
    pacf_vals, pacf_conf = pacf(log_returns_series, nlags=nlags, alpha=alpha, method='ywm')
    _plot_manual_stem_v2(axes[0, 1], pacf_vals, pacf_conf, 'PACF (Log Returns)', nlags, ylim)
    
    # --- 3. 下-左: ACF (Absolute Log Returns) ---
    abs_acf_vals, abs_acf_conf = acf(absolute_log_returns_series, nlags=nlags, alpha=alpha, fft=False)
    _plot_manual_stem_v2(axes[1, 0], abs_acf_vals, abs_acf_conf, 'ACF (Absolute Log Returns) - Volatility Proxy', nlags, ylim)

    # --- 4. 下-右: PACF (Absolute Log Returns) ---
    abs_pacf_vals, abs_pacf_conf = pacf(absolute_log_returns_series, nlags=nlags, alpha=alpha, method='ywm')
    _plot_manual_stem_v2(axes[1, 1], abs_pacf_vals, abs_pacf_conf, 'PACF (Absolute Log Returns) - Volatility Proxy', nlags, ylim)

    plt.tight_layout()
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches='tight')
    print(f"  2x2 (Zoomed) V3 图表已保存到: {save_path}")
    plt.close(fig)


# --- 4. 本地运行块 (Standalone Runner) ---
if __name__ == "__main__":
    
    print("--- 正在以独立模式运行 (ACF/PACF Plotter) [已优化 V3 - 手动缩放] ---")
    
    # --- [!! 关键路径修正 !!] ---
    # 修正为 Zac 的本地路径
    DATA_PATH = "./DATA/PART1/" 
    SAVE_DIR = "./EDA/charts/acf/" 
    # --- [修正结束] ---
    
    LAG_PERIODS = 40 
    ZOOMED_YLIM = (-0.3, 0.3) 
    
    print(f"正在从 '{DATA_PATH}' 加载数据...")
    merged_prices = load_and_merge_data(DATA_PATH) 
    
    if merged_prices.empty:
        print(f"未能加载数据，请检查 DATA_PATH: {os.path.abspath(DATA_PATH)}")
    else:
        # --- [!! 关键升级 !!] ---
        # 调用我们升级版的 calculate_log_returns
        log_returns, absolute_log_returns = calculate_log_returns(merged_prices)
        # --- [升级结束] ---
        
        print("✅ 数据加载、合并、计算收益率完毕。")
        print(f"正在为所有资产生成 V3 缩放图表并保存到 '{SAVE_DIR}'...")
        
        for asset_name in log_returns.columns:
            print(f"  正在处理: {asset_name}")
            
            asset_log_returns = log_returns[asset_name].dropna()
            asset_abs_log_returns = absolute_log_returns[asset_name].dropna()
            
            if asset_log_returns.empty:
                print("    [跳过] 收益率数据为空。")
                continue
            
            # --- [!! 队友的 ADF 检验 !!] ---
            # 这是非常有价值的论据
            adf_test_result = adfuller(asset_log_returns)
            print(f"    ADF Test (Log Returns) p-value: {adf_test_result[1]:.6f}")
            if adf_test_result[1] < 0.05:
                print("    >> 论据发现: 数据是平稳的 (p < 0.05)，支持均值回归。")
            else:
                print("    >> 论据发现: 数据是非平稳的 (p > 0.05)，支持动量。")
            # --- [ADF 结束] ---
            
            save_file_path = os.path.join(SAVE_DIR, f"{asset_name}_acf_pacf_V3_zoomed.png")
            
            save_acf_pacf_plot_v3(
                asset_log_returns, 
                asset_abs_log_returns, 
                asset_name, 
                lags=LAG_PERIODS, 
                save_path=save_file_path,
                ylim=ZOOMED_YLIM
            )
            
        print("--- 本地运行完毕 ---")