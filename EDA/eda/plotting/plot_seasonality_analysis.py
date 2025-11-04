import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns # 导入 Seaborn
import os
import glob
import sys # 确保导入 sys
from scipy import stats

# --- 配置 ---
# [路径修复] 修正为 Zac 的本地路径
SEASONALITY_SAVE_DIR = "./EDA/charts/seasonality/" 
DATA_DIR_PATH = "./DATA/PART1/" 
# ---

# -----------------------------------------------------------------
# (数据加载函数，使用我们昨天的“最终修复版-老师的逻辑”)
# (这是 'Close-Only' 版本，季节性分析只需要 Close 价格)
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
    # [优化] 向前填充 NaN
    merged.ffill(inplace=True) 
    return merged
# -----------------------------------------------------------------
# (数据加载函数结束)
# -----------------------------------------------------------------
# --- [!! 新增的 API 函数 (给 Notebook 调用) !!] ---
def plot_seasonality_show(price_series, asset_name):
    """
    (新增的 API - 供 Notebook 调用)
    对 *单个资产* 的收益率进行“星期几”和“月份”效应分析，并“显示”图表。
    """
    # [我们从 'plot_seasonality' 复制所有代码]
    print(f"  Analyzing Seasonality for {asset_name}...")
    log_returns = np.log(price_series / price_series.shift(1)).dropna()
    if log_returns.empty:
        print(f"  Skipping {asset_name}: Not enough data for returns.")
        return

    df = pd.DataFrame({'returns': log_returns})
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except Exception as e:
            print(f"  Skipping {asset_name}: Could not convert index to Datetime. Error: {e}")
            return
    df['day_of_week'] = df.index.day_name()
    df['month'] = df.index.month_name()
    
    week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    months = ["January", "February", "March", "April", "May", "June", 
              "July", "August", "September", "October", "November", "December"]
    
    day_order = [day for day in week_days if day in df['day_of_week'].unique()]
    month_order = [mon for mon in months if mon in df['month'].unique()]

    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(15, 12))
    fig.suptitle(f'Seasonality Analysis for {asset_name}', y=1.02, fontsize=16)

    sns.boxplot(ax=ax1, data=df, x='day_of_week', y='returns', 
                order=day_order, palette="pastel")
    ax1.axhline(0, color='red', linestyle='--', alpha=0.7)
    ax1.set_title('Day-of-Week Effect')
    ax1.set_xlabel('Day of the Week')
    ax1.set_ylabel('Log Returns')

    sns.boxplot(ax=ax2, data=df, x='month', y='returns', 
                order=month_order, palette="Spectral")
    ax2.axhline(0, color='red', linestyle='--', alpha=0.7)
    ax2.set_title('Month-of-Year Effect')
    ax2.set_xlabel('Month')
    ax2.set_ylabel('Log Returns')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.98]) 

    # --- [!! 核心区别: "显示" !!] ---
    plt.show()

# --- (队友的核心分析函数 - 100% 保留) ---
def plot_seasonality(price_series, asset_name, save_dir):
    """
    对 *单个资产* 的收益率进行“星期几”和“月份”效应分析。
    """
    print(f"  Analyzing Seasonality for {asset_name}...")

    # 1. 准备数据：季节性分析应在收益率上进行
    log_returns = np.log(price_series / price_series.shift(1)).dropna()

    if log_returns.empty:
        print(f"  Skipping {asset_name}: Not enough data for returns.")
        return

    # 2. 创建一个包含收益率和日历特征的 DataFrame
    df = pd.DataFrame({'returns': log_returns})
    
    # 确保索引是 DatetimeIndex (我们的 loader 已经做了)
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except Exception as e:
            print(f"  Skipping {asset_name}: Could not convert index to Datetime. Error: {e}")
            return
            
    df['day_of_week'] = df.index.day_name()
    df['month'] = df.index.month_name()
    
    # 3. 为图表排序
    week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    months = ["January", "February", "March", "April", "May", "June", 
              "July", "August", "September", "October", "November", "December"]
    
    # 过滤掉数据中不存在的日期
    day_order = [day for day in week_days if day in df['day_of_week'].unique()]
    month_order = [mon for mon in months if mon in df['month'].unique()]

    # 4. 可视化 (一张图包含两个子图)
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(15, 12))
    fig.suptitle(f'Seasonality Analysis for {asset_name}', y=1.02, fontsize=16)

    # 子图 1: 周内效应 (Day of Week)
    sns.boxplot(ax=ax1, data=df, x='day_of_week', y='returns', 
                order=day_order, palette="pastel")
    ax1.axhline(0, color='red', linestyle='--', alpha=0.7) # 零收益线
    ax1.set_title('Day-of-Week Effect')
    ax1.set_xlabel('Day of the Week')
    ax1.set_ylabel('Log Returns')

    # 子图 2: 月度效应 (Month of Year)
    sns.boxplot(ax=ax2, data=df, x='month', y='returns', 
                order=month_order, palette="Spectral")
    ax2.axhline(0, color='red', linestyle='--', alpha=0.7) # 零收益线
    ax2.set_title('Month-of-Year Effect')
    ax2.set_xlabel('Month')
    ax2.set_ylabel('Log Returns')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.98]) # 调整布局以适应主标题

    # 5. 保存图表
    os.makedirs(save_dir, exist_ok=True) # [修复] 确保在函数内创建
    output_filename = f"seasonality_{asset_name}.png"
    output_path = os.path.join(save_dir, output_filename)
    
    plt.savefig(output_path)
    print(f"  Chart saved to {output_path}")
    plt.close(fig)

def main():
    """
    主执行函数：加载数据，循环处理每个资产。
    """
    print("--- 正在运行 Seasonality 分析脚本 [V2 - Zac 已修复路径] ---")
    
    os.makedirs(SEASONALITY_SAVE_DIR, exist_ok=True)
    print(f"Charts will be saved to: {SEASONALITY_SAVE_DIR}")

    # --- [!! 关键修复 !!] ---
    # 1. 调用 *内部* 的加载器
    # 2. 使用我们 100% 正确的 DATA_DIR_PATH
    print(f"Calling internal load_and_merge_data(data_directory='{DATA_DIR_PATH}')...")
    
    merged_prices_df = load_and_merge_data(DATA_DIR_PATH)
    # --- [修复结束] ---

    if merged_prices_df.empty:
        print("Error: Loader returned an empty DataFrame.")
        return

    print(f"✅ Loader success. Loaded merged DataFrame with {len(merged_prices_df.columns)} assets.")

    # 循环遍历 *合并后 DataFrame 的每一列*
    for asset_name in merged_prices_df.columns:
        price_series = merged_prices_df[asset_name].dropna()
        
        if isinstance(price_series, pd.Series) and not price_series.empty:
            plot_seasonality(price_series, 
                             asset_name, 
                             SEASONALITY_SAVE_DIR)
        else:
            print(f"Skipping {asset_name}: No valid data.")
            
    print("--- Seasonality 分析全部完成 ---")


if __name__ == "__main__":
    main()