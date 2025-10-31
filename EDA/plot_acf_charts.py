import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
import glob 

# 导入 ACFPACF 绘图工具
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf


# -----------------------------------------------------------------
# (数据加载函数，从 C 计划复制过来，保持不变)
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
                f, parse_dates=['Index'], index_col='Index'
            )
            data.columns = data.columns.str.strip().str.strip('"')
            data.rename(columns={
                'Open': 'open', 'High': 'high', 'Low': 'low',
                'Close': 'close', 'Volume': 'volume'
            }, inplace=True)
            if 'close' in data.columns:
                df = data[['close']].rename(columns={'close': asset_name})
                dfs[asset_name] = df
            else:
                print(f" 警告: {asset_name}.csv 缺少 'close' 列，已跳过。")
        except Exception as e:
            print(f" 警告: 加载 {f} 出错: {e}")
    if not dfs:
        return pd.DataFrame()
    df_list = list(dfs.values())
    if not df_list:
        return pd.DataFrame()
    merged = df_list[0]
    for df_to_join in df_list[1:]:
        merged = merged.join(df_to_join, how='inner') 
    merged.sort_index(inplace=True) 
    return merged

def calculate_log_returns(merged_df): 
    return np.log(merged_df / merged_df.shift(1)).dropna()
# -----------------------------------------------------------------
# (数据加载函数结束)
# -----------------------------------------------------------------


# --- 1. API 函数 (给 Notebook 调用) ---

def plot_acf_pacf(log_returns_series, asset_name, lags=40):
    """
    (供 Notebook 调用)
    为给定的资产对数收益率绘制 ACF 和 PACF 图，并直接 'show()'。
    [已升级: 同时绘制 ACF 和 PACF]
    """
    if log_returns_series.empty:
        print(f" 警告: {asset_name} 的收益率数据为空，跳过绘图。")
        return

    print(f"--- ACF/PACF 分析: {asset_name} ---")
    
    # 创建一个 2x1 的子图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # 绘制 ACF
    plot_acf(log_returns_series, lags=lags, ax=ax1, title=f'Autocorrelation (ACF) - {asset_name}')
    ax1.grid(True)
    
    # 绘制 PACF
    plot_pacf(log_returns_series, lags=lags, ax=ax2, title=f'Partial Autocorrelation (PACF) - {asset_name}')
    ax2.grid(True)
    
    plt.tight_layout() # 自动调整子图间距
    plt.show()

def save_acf_pacf_plot(log_returns_series, asset_name, lags=40, save_path=""):
    """
    (供本地运行调用)
    绘制图表并 'savefig()' 到指定路径。
    """
    if log_returns_series.empty:
        print(f" 警告: {asset_name} 数据为空，跳过保存。")
        return

    # 创建一个 2x1 的子图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # 绘制 ACF
    plot_acf(log_returns_series, lags=lags, ax=ax1, title=f'Autocorrelation (ACF) - {asset_name}')
    ax1.grid(True)
    
    # 绘制 PACF
    plot_pacf(log_returns_series, lags=lags, ax=ax2, title=f'Partial Autocorrelation (PACF) - {asset_name}')
    ax2.grid(True)

    plt.tight_layout()
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches='tight')
    print(f"  图表已保存到: {save_path}")
    plt.close(fig)


# --- 2. 本地运行块 (Standalone Runner) ---
if __name__ == "__main__":
    
    print("--- 正在以独立模式运行 (ACF/PACF Plotter) ---")
    
    DATA_PATH = "./DATA/PART1/" 
    SAVE_DIR = "./EDA/charts/acf/" # 你的原始输出路径
    LAG_PERIODS = 40 # 默认看 40 期
    
    print(f"正在从 '{DATA_PATH}' 加载数据...")
    merged_prices = load_and_merge_data(DATA_PATH) 
    log_returns = calculate_log_returns(merged_prices)
    
    if not log_returns.empty:
        print("✅ 数据加载、合并、计算收益率完毕。")
        print(f"正在为所有资产生成 ACF/PACF 图并保存到 '{SAVE_DIR}'...")
        
        for asset_name in log_returns.columns:
            print(f"  正在处理: {asset_name}")
            asset_returns_series = log_returns[asset_name].dropna()
            
            save_file_path = os.path.join(SAVE_DIR, f"{asset_name}_acf_pacf.png") # 文件名已更新
            
            save_acf_pacf_plot(asset_returns_series, asset_name, lags=LAG_PERIODS, save_path=save_file_path)
            
        print("--- 本地运行完毕 ---")
    else:
        print("未能加载测试数据，请检查 DATA_PATH。")