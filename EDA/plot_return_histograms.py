import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm
import os
import sys
import glob 

# -----------------------------------------------------------------
# (数据加载函数，经 C 计划修复，是正确的，保持不变)
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
# 绘图函数
# -----------------------------------------------------------------

# --- 1. API 函数 (给 Notebook 调用) ---

def plot_histogram(log_returns_series, asset_name, bins=100):
    if log_returns_series.empty:
        print(f" 警告: {asset_name} 的收益率数据为空，跳过绘图。")
        return
    skewness = log_returns_series.skew()
    kurtosis = log_returns_series.kurtosis() 
    plt.figure(figsize=(10, 6))
    
    sns.histplot(log_returns_series, bins=bins, stat="density", label='Log Returns Histogram', alpha=0.7, kde=False)
    
    mu = log_returns_series.mean()
    std = log_returns_series.std()
    x = np.linspace(mu - 4*std, mu + 4*std, 100)
    y = norm.pdf(x, mu, std)
    plt.plot(x, y, linewidth=2, color='r', label='Normal Distribution')
    
    # --- [!! 关键修正 E !!] ---
    # 标题已改为全英文
    title_kurtosis = 3 + kurtosis 
    plt.title(f'Log Returns Distribution - {asset_name}\nSkew: {skewness:.4f}, Kurtosis (W5 Standard): {title_kurtosis:.4f}')
    # --- [修正结束] ---
    
    plt.xlabel('Log Returns')
    plt.ylabel('Density')
    plt.legend()
    plt.grid(True)
    plt.show()
    print(f"--- 统计摘要: {asset_name} ---")
    print(f"偏度 (Skewness): {skewness:.4f}")
    print(f"超额峰度 (Excess Kurtosis): {kurtosis:.4f}")

def save_histogram_plot(log_returns_series, asset_name, bins=100, save_path=""):
    if log_returns_series.empty:
        print(f" 警告: {asset_name} 数据为空，跳过保存。")
        return
    skewness = log_returns_series.skew()
    kurtosis = log_returns_series.kurtosis()
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.histplot(log_returns_series, bins=bins, stat="density", label='Log Returns Histogram', alpha=0.7, kde=False, ax=ax)

    mu = log_returns_series.mean()
    std = log_returns_series.std()
    x = np.linspace(mu - 4*std, mu + 4*std, 100)
    y = norm.pdf(x, mu, std)
    ax.plot(x, y, linewidth=2, color='r', label='Normal Distribution')
    
    # --- [!! 关键修正 E !!] ---
    # 标题已改为全英文
    title_kurtosis = 3 + kurtosis
    ax.set_title(f'Log Returns Distribution - {asset_name}\nSkew: {skewness:.4f}, Kurtosis (W5 Standard): {title_kurtosis:.4f}')
    # --- [修正结束] ---

    ax.set_xlabel('Log Returns')
    ax.set_ylabel('Density')
    ax.legend()
    ax.grid(True)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches='tight')
    print(f"  图表已保存到: {save_path}")
    plt.close(fig)


# --- 2. 本地运行块 (Standalone Runner) ---
if __name__ == "__main__":
    
    print("--- 正在以独立模式运行 (Histogram Plotter) [E 计划] ---")
    
    DATA_PATH = "./DATA/PART1/" 
    SAVE_DIR = "./EDA/charts/histograms/" 
    
    print(f"正在从 '{DATA_PATH}' 加载数据...")
    merged_prices = load_and_merge_data(DATA_PATH) 
    log_returns = calculate_log_returns(merged_prices)
    
    if not log_returns.empty:
        print("✅ 数据加载、合并、计算收益率完毕。")
        print(f"正在为所有资产生成直方图并保存到 '{SAVE_DIR}'...")
        
        for asset_name in log_returns.columns:
            print(f"  正在处理: {asset_name}")
            asset_returns_series = log_returns[asset_name].dropna()
            save_file_path = os.path.join(SAVE_DIR, f"{asset_name}_histogram.png")
            save_histogram_plot(asset_returns_series, asset_name, bins=100, save_path=save_file_path)
            
        print("--- 本地运行完毕 ---")
    else:
        print("未能加载测试数据，请检查 DATA_PATH。")