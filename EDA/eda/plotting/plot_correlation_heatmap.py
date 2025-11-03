import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns # 导入
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
def plot_correlation_heatmap(log_returns_df):
    if log_returns_df.empty:
        print(f" 警告: 收益率数据为空，跳过绘图。")
        return

    correlation_matrix = log_returns_df.corr()
    
    # 优化: 增加图表尺寸 (来自队友)
    plt.figure(figsize=(12, 10)) 
    sns.heatmap(
        correlation_matrix, 
        annot=True,       
        cmap='coolwarm',  
        fmt=".2f",        
        linewidths=.5,
        linecolor='black',
        annot_kws={"size": 8}, # 优化: 减小注解字体大小 (来自队友)
        vmin=-1, vmax=1 # 确保颜色条是 -1 到 1
    )
    plt.title('Cross-Asset Log Returns Correlation Heatmap (Optimized)')
    plt.show()

# --- 2. 优化的“保存”函数 (来自队友) ---
def save_correlation_heatmap(log_returns_df, save_path=""):
    if log_returns_df.empty:
        print(f" 警告: 收益率数据为空，跳过保存。")
        return
        
    correlation_matrix = log_returns_df.corr()
    
    # --- 优化点: 打印核心统计数据 (来自队友) ---
    # (这对于报告论据非常宝贵)
    corr_for_stats = correlation_matrix.copy() # 复制一个用于计算
    np.fill_diagonal(corr_for_stats.values, np.nan) 
    mean_corr = corr_for_stats.stack().mean()
    max_corr = corr_for_stats.stack().max()
    min_corr = corr_for_stats.stack().min()
    
    print("\n--- 报告核心统计数据 ---")
    print(f" 平均相关性 (Mean Correlation): {mean_corr:.4f}")
    print(f" 最大正相关性 (Max Positive Correlation): {max_corr:.4f}")
    print(f" 最小负相关性 (Min Negative Correlation): {min_corr:.4f}")
    print("\n--- 完整相关性矩阵 (用于复制) ---")
    print(correlation_matrix.to_string(float_format="%.4f")) # 打印更整齐
    
    # 优化: 增加图表尺寸 (来自队友)
    fig, ax = plt.subplots(figsize=(12, 10))
    
    sns.heatmap(
        correlation_matrix, 
        annot=True, 
        cmap='coolwarm', 
        fmt=".2f", 
        linewidths=.5,
        linecolor='black',
        annot_kws={"size": 8}, # 优化: 减小注解字体大小 (来自队友)
        vmin=-1, vmax=1,
        ax=ax 
    )
    ax.set_title('Cross-Asset Log Returns Correlation Heatmap (Optimized)')
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches='tight')
    print(f"  图表已保存到: {save_path}")
    plt.close(fig)

    
# --- 3. 本地运行块 (Standalone Runner) ---
if __name__ == "__main__":
    
    print("--- 正在以独立模式运行 (Correlation Heatmap Plotter) [已优化 V2 - 团队版] ---")
    
    # --- [!! 路径确认 !!] ---
    # (这些路径对 Zac 的本地环境是正确的)
    DATA_PATH = "./DATA/PART1/" 
    SAVE_FILE = "./EDA/charts/correlation_heatmap.png" 
    # --- [确认结束] ---
    
    print(f"正在从 '{DATA_PATH}' 加载数据...")
    merged_prices = load_and_merge_data(DATA_PATH) 
    
    if merged_prices.empty:
        print(f"未能加载数据，请检查 DATA_PATH: {os.path.abspath(DATA_PATH)}")
    else:
        # --- [!! 关键一致性 !!] ---
        # 我们必须调用返回 *两个* 值的版本
        # 我们用 '_' 来忽略我们不需要的 'absolute_log_returns'
        log_returns, _ = calculate_log_returns(merged_prices) 
        # --- [修正结束] ---
        
        print("✅ 数据加载、合并、计算收益率完毕。")
        print(f"正在生成[优化版]相关性热力图并保存到 '{SAVE_FILE}'...")
        
        save_correlation_heatmap(log_returns, save_path=SAVE_FILE)
            
        print("--- 本地运行完毕 ---")