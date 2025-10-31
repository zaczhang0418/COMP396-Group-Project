import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns # 导入
import os
import sys
import glob 

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

def plot_correlation_heatmap(log_returns_df):
    """
    (供 Notebook 调用)
    计算并绘制对数收益率的相关性热力图，并直接 'show()'。
    """
    if log_returns_df.empty:
        print(f" 警告: 收益率数据为空，跳过绘图。")
        return

    print("--- 正在计算相关性矩阵 ---")
    correlation_matrix = log_returns_df.corr()
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        correlation_matrix, 
        annot=True,       # 在图上显示数值
        cmap='coolwarm',  # 使用冷暖色调
        fmt=".2f",        # 格式化数值为两位小数
        linewidths=.5,
        linecolor='black'
    )
    plt.title('Cross-Asset Log Returns Correlation Heatmap')
    plt.show()

def save_correlation_heatmap(log_returns_df, save_path=""):
    """
    (供本地运行调用)
    绘制图表并 'savefig()' 到指定路径。
    """
    if log_returns_df.empty:
        print(f" 警告: 收益率数据为空，跳过保存。")
        return
        
    print("--- 正在计算相关性矩阵 ---")
    correlation_matrix = log_returns_df.corr()
    print(correlation_matrix) # 在本地运行时打印矩阵
    
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        correlation_matrix, 
        annot=True, 
        cmap='coolwarm', 
        fmt=".2f", 
        linewidths=.5,
        linecolor='black',
        ax=ax # 传入 ax
    )
    ax.set_title('Cross-Asset Log Returns Correlation Heatmap')
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches='tight')
    print(f"  图表已保存到: {save_path}")
    plt.close(fig)


# --- 2. 本地运行块 (Standalone Runner) ---
if __name__ == "__main__":
    
    print("--- 正在以独立模式运行 (Correlation Heatmap Plotter) ---")
    
    DATA_PATH = "./DATA/PART1/" 
    # 你的原始输出路径 (使用我们修正的 EDA 路径)
    SAVE_FILE = "./EDA/charts/correlation_heatmap.png" 
    
    print(f"正在从 '{DATA_PATH}' 加载数据...")
    merged_prices = load_and_merge_data(DATA_PATH) 
    log_returns = calculate_log_returns(merged_prices)
    
    if not log_returns.empty:
        print("✅ 数据加载、合并、计算收益率完毕。")
        print(f"正在生成相关性热力图并保存到 '{SAVE_FILE}'...")
        
        save_correlation_heatmap(log_returns, save_path=SAVE_FILE)
            
        print("--- 本地运行完毕 ---")
    else:
        print("未能加载测试数据，请检查 DATA_PATH。")