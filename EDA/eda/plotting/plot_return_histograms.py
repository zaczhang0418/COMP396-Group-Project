import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm
import os
import sys
import glob 

# -----------------------------------------------------------------
# (数据加载函数，使用我们昨天的“最终修复版-老师的逻辑”)
# (这和 'plot_acf_charts.py' 里的代码一模一样)
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
                index_col=None, # [我们的修复]
                thousands=','   # [我们的修复]
            )
            data.columns = data.columns.str.strip().str.strip('"')
            data.rename(columns={
                'Open': 'open', 'High': 'high', 'Low': 'low',
                'Close': 'close', 'Volume': 'volume',
                'Index': 'Date' # [我们的修复]
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
        merged = merged.merge(df_to_join, on='Date', how='outer') # [我们的修复]
    
    merged.set_index('Date', inplace=True)
    merged.sort_index(inplace=True) 
    return merged

# --- [!! 关键一致性 !!] ---
# (我们使用和 'acf' 脚本 *完全一样* 的计算函数)
def calculate_log_returns(merged_df): 
    log_returns = np.log(merged_df / merged_df.shift(1)).dropna()
    absolute_log_returns = log_returns.abs().dropna()
    # 即使这个脚本用不到 'absolute_log_returns'，
    # 我们也保持函数一致性，返回两个值
    return log_returns, absolute_log_returns
# -----------------------------------------------------------------
# (数据加载函数结束)
# -----------------------------------------------------------------


# --- 1. API 函数 (给 Notebook 调用) ---
# (这是队友的优化版绘图函数 - 我们保留它)
def plot_histogram(log_returns_series, asset_name, bins="fd"): # 默认 'fd'
    if log_returns_series.empty:
        print(f" 警告: {asset_name} 的收益率数据为空，跳过绘图。")
        return
    
    skewness = log_returns_series.skew()
    kurtosis = log_returns_series.kurtosis() 
    mu = log_returns_series.mean()
    std = log_returns_series.std()
    
    plt.figure(figsize=(12, 7))
    ax = plt.gca() # 获取当前 axes
    
    sns.histplot(log_returns_series, bins=bins, stat="density", label='Log Returns Histogram', alpha=0.7, kde=False, ax=ax)
    
    x = np.linspace(mu - 4*std, mu + 4*std, 100)
    y = norm.pdf(x, mu, std)
    ax.plot(x, y, linewidth=2, color='r', linestyle='--', label='Normal Distribution')
    
    ax.axvline(mu, color='darkorange', linestyle='-', linewidth=2, label=f'Mean: {mu:.5f}')
    
    q_low = log_returns_series.quantile(0.005)
    q_high = log_returns_series.quantile(0.995)
    ax.set_xlim(q_low, q_high)

    title_kurtosis = 3 + kurtosis 
    ax.set_title(f'Log Returns Distribution - {asset_name}\nSkew: {skewness:.4f}, Kurtosis (W5 Standard): {title_kurtosis:.4f}')
    ax.set_xlabel('Log Returns (Zoomed to 99% data)') 
    ax.set_ylabel('Density')
    ax.legend()
    ax.grid(True, linestyle=':', alpha=0.6) 
    plt.show()

# --- 2. 优化的“保存”函数 (来自队友) ---
def save_histogram_plot(log_returns_series, asset_name, bins="fd", save_path=""):
    """
    (已优化 - 来自队友)
    """
    if log_returns_series.empty:
        print(f" 警告: {asset_name} 数据为空，跳过保存。")
        return
    
    skewness = log_returns_series.skew()
    kurtosis = log_returns_series.kurtosis()
    mu = log_returns_series.mean()
    std = log_returns_series.std()
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    sns.histplot(log_returns_series, bins=bins, stat="density", label='Log Returns Histogram', alpha=0.7, kde=False, ax=ax)

    x = np.linspace(mu - 4*std, mu + 4*std, 100)
    y = norm.pdf(x, mu, std)
    ax.plot(x, y, linewidth=2, color='r', linestyle='--', label='Normal Distribution')
    
    ax.axvline(mu, color='darkorange', linestyle='-', linewidth=2, label=f'Mean: {mu:.5f}')
    
    q_low = log_returns_series.quantile(0.005)
    q_high = log_returns_series.quantile(0.995)
    ax.set_xlim(q_low, q_high)

    title_kurtosis = 3 + kurtosis
    ax.set_title(f'Log Returns Distribution - {asset_name}\nSkew: {skewness:.4f}, Kurtosis (W5 Standard): {title_kurtosis:.4f}')
    ax.set_xlabel('Log Returns (Zoomed to 99% data)')
    ax.set_ylabel('Density')
    ax.legend()
    ax.grid(True, linestyle=':', alpha=0.6)
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches='tight')
    print(f"  图表已保存到: {save_path}")
    plt.close(fig)


# --- 3. 本地运行块 (Standalone Runner) ---
if __name__ == "__main__":
    
    print("--- 正在以独立模式运行 (Histogram Plotter) [已优化 V2 - 团队版] ---")
    
    # --- [!! 关键路径修正 !!] ---
    # 修正为 Zac 的本地路径
    DATA_PATH = "./DATA/PART1/" 
    SAVE_DIR = "./EDA/charts/histograms/" 
    # --- [修正结束] ---
    
    print(f"正在从 '{DATA_PATH}' 加载数据...")
    merged_prices = load_and_merge_data(DATA_PATH) 
    
    if merged_prices.empty:
        print(f"未能加载数据，请检查 DATA_PATH: {os.path.abspath(DATA_PATH)}")
    else:
        # --- [!! 关键一致性 !!] ---
        # 我们必须调用返回 *两个* 值的版本
        log_returns, absolute_log_returns = calculate_log_returns(merged_prices)
        # --- [修正结束] ---
        
        print("✅ 数据加载、合并、计算收益率完毕。")
        print(f"正在为所有资产生成[优化版]直方图并保存到 '{SAVE_DIR}'...")
        
        for asset_name in log_returns.columns:
            print(f"  正在处理: {asset_name}")
            asset_returns_series = log_returns[asset_name].dropna()
            
            save_file_path = os.path.join(SAVE_DIR, f"{asset_name}_histogram_V2_zoomed.png")
            
            # 调用优化的函数
            save_histogram_plot(asset_returns_series, asset_name, bins="fd", save_path=save_file_path)
            
        print("--- 本地运行完毕 ---")