import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
import glob
import os

# --- 1. API 函数 (给 Notebook 调用) ---

def load_and_merge_data(data_directory="./DATA/PART1/"):
    """
    加载所有 CSVs，合并，并返回一个 'merged' DataFrame。
    [最终修复版: 结合了老师的 'merge-on-column' 逻辑 和 我们的 Bug 修复]
    """
    csv_files_path = os.path.join(data_directory, "*.csv")
    files = glob.glob(csv_files_path)
    
    if not files:
        print(f"警告：在 '{data_directory}' 中没有找到 .csv 文件。")
        return pd.DataFrame() 

    dfs = {}
    for f in files:
        asset_name = os.path.basename(f).split('.')[0]
        try:
            # --- 老师的逻辑 (步骤 1): 不设置 index_col ---
            data = pd.read_csv(
                f, 
                parse_dates=['Index'],
                thousands=','  # <-- [!! 关键修正 1 !!] 告诉 pandas "1,234" 是数字
            )
            
            # --- 你的清洗逻辑 (Zac) ---
            data.columns = data.columns.str.strip().str.strip('"')
            data.rename(columns={
                'Open': 'open', 'High': 'high', 'Low': 'low',
                'Close': 'close', 'Volume': 'volume',
                'Index': 'Date' # <-- 老师的逻辑
            }, inplace=True)
            
            if 'close' in data.columns:
                
                # --- [!! 关键修正 2 !!] ---
                # 强制转换为数字 (作为双重保险)
                data['close'] = pd.to_numeric(data['close'], errors='coerce')
                data.dropna(subset=['close'], inplace=True) 

                # --- 老师的逻辑 (步骤 2): 保留 'Date' 列和 'close' 列 ---
                df = data[['Date', 'close']].rename(columns={'close': asset_name})
                dfs[asset_name] = df
            else:
                 print(f" 警告: {asset_name}.csv 缺少 'close' 列，已跳过。")
        
        except Exception as e:
            print(f" 警告: 加载 {f} 出错: {e}")

    if not dfs:
        print("❌ 错误: 未能从任何 CSV 文件中加载有效数据。")
        return pd.DataFrame()

    df_list = list(dfs.values())
    merged = df_list[0]
    
    # --- 老师的逻辑 (步骤 3): 在 'Date' *列* 上合并 ---
    for df_to_join in df_list[1:]:
        # 我们使用 'outer' join 来防止数据丢失
        merged = merged.merge(df_to_join, on='Date', how='outer') 
    
    # --- 老师的逻辑 (步骤 4): *最后* 才设置索引 ---
    merged.set_index('Date', inplace=True)
    merged.sort_index(inplace=True) 
    return merged

def calculate_log_returns(merged_df): 
    return np.log(merged_df / merged_df.shift(1)).dropna()

def plot_normalized_prices(merged_df):
    """ (这个函数保持不变) """
    merged_minmax = (merged_df - merged_df.min()) / (merged_df.max() - merged_df.min())
    merged_minmax.plot(figsize=(12,6), title="Min–Max Normalised Prices (0–1 Scale)")
    plt.xlabel("Date")
    plt.ylabel("Scaled Price (0–1)")
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(True)
    plt.show() 

def save_normalized_prices_plot(merged_df, save_path):
    """ (这个函数保持不变) """
    merged_minmax = (merged_df - merged_df.min()) / (merged_df.max() - merged_df.min())
    fig, ax = plt.subplots(figsize=(12, 6)) 
    merged_minmax.plot(ax=ax, title="Min–Max Normalised Prices (0–1 Scale)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Scaled Price (0–1)")
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
    ax.grid(True)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches='tight') 
    print(f"图表已保存到: {save_path}")
    plt.close(fig)


# --- 2. 本地运行块 (Standalone Runner) ---
if __name__ == "__main__":
    import sys
    dataset_name = "PART1"
    if len(sys.argv) > 1:
        dataset_name = sys.argv[1]
    
    print(f"--- 正在以独立模式运行 (Data Loader) [Dataset: {dataset_name}] ---")
    
    DATA_PATH = f"./DATA/{dataset_name}/" 
    SAVE_PATH = f"./EDA/output/{dataset_name}/charts/00_normalized_prices.png" 
    
    print(f"正在从 '{DATA_PATH}' 加载数据...")
    merged_prices = load_and_merge_data(DATA_PATH)
    
    if not merged_prices.empty:
        log_returns = calculate_log_returns(merged_prices) 
        print("✅ 对数收益率计算完毕。")
        
        print(f"正在生成图表并保存到 '{SAVE_PATH}'...")
        save_normalized_prices_plot(merged_prices, SAVE_PATH)
        print("--- 本地运行完毕 ---")
    else:
        print("未能加载测试数据，请检查 DATA_PATH。")