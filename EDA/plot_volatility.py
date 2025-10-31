import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
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

def plot_volatility_clustering(log_returns_series, asset_name, window=20):
    """
    (供 Notebook 调用)
    计算并绘制对数收益率的滚动波动率，并直接 'show()'。
    """
    if log_returns_series.empty:
        print(f" 警告: {asset_name} 的收益率数据为空，跳过绘图。")
        return

    print(f"--- 波动率聚集分析: {asset_name} ---")
    
    # 3. 计算 20 天滚动标准差 (波动率)
    rolling_vol = log_returns_series.rolling(window=window).std() * np.sqrt(252) # 年化波动率 (可选, 但更标准)
    # 如果你不想年化，就用这行：
    # rolling_vol = log_returns_series.rolling(window=window).std()

    plt.figure(figsize=(12, 6))
    rolling_vol.plot()
    
    plt.title(f'{asset_name} - {window}-Day Rolling Volatility (Clustering)')
    plt.xlabel('Date')
    plt.ylabel(f'Volatility (Rolling StDev, Ann.)') # 如果你年化了
    # plt.ylabel(f'Volatility (Rolling StDev)') # 如果你没年化
    plt.grid(True)
    plt.show()


def save_volatility_plot(log_returns_series, asset_name, window=20, save_path=""):
    """
    (供本地运行调用)
    绘制图表并 'savefig()' 到指定路径。
    """
    if log_returns_series.empty:
        print(f" 警告: {asset_name} 数据为空，跳过保存。")
        return

    # 3. 计算 20 天滚动标准差 (波动率)
    rolling_vol = log_returns_series.rolling(window=window).std() * np.sqrt(252) # 年化
    # rolling_vol = log_returns_series.rolling(window=window).std() # 非年化

    fig, ax = plt.subplots(figsize=(12, 6))
    rolling_vol.plot(ax=ax)
    
    ax.set_title(f'{asset_name} - {window}-Day Rolling Volatility (Clustering)')
    ax.set_xlabel('Date')
    ax.set_ylabel(f'Volatility (Rolling StDev, Ann.)') # 年化
    # ax.set_ylabel(f'Volatility (Rolling StDev)') # 非年化
    ax.grid(True)
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches='tight')
    print(f"  图表已保存到: {save_path}")
    plt.close(fig)


# --- 2. 本地运行块 (Standalone Runner) ---
if __name__ == "__main__":
    
    print("--- 正在以独立模式运行 (Volatility Plotter) ---")
    
    DATA_PATH = "./DATA/PART1/" 
    SAVE_DIR = "./EDA/charts/volatility/" # 你的原始输出路径
    ROLLING_WINDOW = 20 # 你的原始设置
    
    print(f"正在从 '{DATA_PATH}' 加载数据...")
    merged_prices = load_and_merge_data(DATA_PATH) 
    log_returns = calculate_log_returns(merged_prices)
    
    if not log_returns.empty:
        print("✅ 数据加载、合并、计算收益率完毕。")
        print(f"正在为所有资产生成波动率图并保存到 '{SAVE_DIR}'...")
        
        for asset_name in log_returns.columns:
            print(f"  正在处理: {asset_name}")
            asset_returns_series = log_returns[asset_name].dropna()
            
            save_file_path = os.path.join(SAVE_DIR, f"{asset_name}_volatility.png")
            
            save_volatility_plot(asset_returns_series, asset_name, window=ROLLING_WINDOW, save_path=save_file_path)
            
        print("--- 本地运行完毕 ---")
    else:
        print("未能加载测试数据，请检查 DATA_PATH。")