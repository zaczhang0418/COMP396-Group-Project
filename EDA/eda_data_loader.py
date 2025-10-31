import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

# --- 1. API 函数 (给 Notebook 调用) ---

def load_and_merge_data(data_directory="./DATA/PART1/"): # <--- 路径已修正 (../ 改为 ./)
    """
    加载所有 CSVs，合并，并返回一个 'merged' DataFrame。
    (假设此 .py 和 notebook 都从项目根目录运行)
    """
    csv_files_path = os.path.join(data_directory, "*.csv")
    files = glob.glob(csv_files_path)
    
    if not files:
        print(f"警告：在 '{data_directory}' 中没有找到 .csv 文件。")
        return pd.DataFrame() 

    dfs = {}
    for f in files:
        name = os.path.basename(f).split('.')[0]
        df = pd.read_csv(f)
        df['Index'] = pd.to_datetime(df['Index'])
        df = df[['Index', 'Close']].rename(columns={'Index': 'Date', 'Close': name})
        dfs[name] = df

    if not dfs:
        return pd.DataFrame()

    merged = dfs[list(dfs.keys())[0]]
    for name, df in list(dfs.items())[1:]:
        merged = merged.merge(df, on='Date', how='inner')
    
    merged.set_index('Date', inplace=True)
    return merged

def calculate_returns(merged_df):
    """从 merged 价格计算百分比收益率。"""
    return merged_df.pct_change().dropna()

def plot_normalized_prices(merged_df):
    """
    (供 Notebook 调用)
    绘制老师的 "messy" 0-1 归一化图表，并直接 'show()'。
    """
    merged_minmax = (merged_df - merged_df.min()) / (merged_df.max() - merged_df.min())
    merged_minmax.plot(figsize=(12,6), title="Min–Max Normalised Prices (0–1 Scale)")
    plt.xlabel("Date")
    plt.ylabel("Scaled Price (0–1)")
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(True)
    plt.show() 

def save_normalized_prices_plot(merged_df, save_path):
    """
    (供本地运行调用)
    绘制图表并 'savefig()' 到指定路径。
    """
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
# 只有当你直接运行 `python EDA/eda_data_loader.py` 时，才会执行这部分
if __name__ == "__main__":
    
    print("--- 正在以独立模式运行 (Standalone Mode) ---")
    
    # 1. 设置路径
    # (从项目根目录 CWD 开始)
    DATA_PATH = "./DATA/PART1/" # <--- 路径已修正 (../ 改为 ./)
    
    # (图表保存在 EDA 文件夹下的 charts 文件夹)
    SAVE_PATH = "./EDA/charts/00_normalized_prices.png" # <--- 路径已修正 (添加 ./EDA/)
    
    # 2. 加载数据
    print(f"正在从 '{DATA_PATH}' 加载数据...")
    merged_prices = load_and_merge_data(DATA_PATH)
    
    if not merged_prices.empty:
        # 3. 生成并保存图表
        print(f"正在生成图表并保存到 '{SAVE_PATH}'...")
        save_normalized_prices_plot(merged_prices, SAVE_PATH)
        print("--- 本地运行完毕 ---")
    else:
        print("未能加载测试数据，请检查 DATA_PATH。")