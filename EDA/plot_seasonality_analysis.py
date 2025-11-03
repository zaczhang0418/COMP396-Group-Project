import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns # 导入 Seaborn
import os

# 1. 导入你自己的加载器
try:
    import eda_data_loader
except ImportError:
    print("Error: 'eda_data_loader.py' not found.")
    print("Please ensure this script is in the same 'EDA' folder as your loader.")
    exit()

# --- 配置 ---
CHARTS_BASE_DIR = "charts"
SEASONALITY_SAVE_DIR = os.path.join(CHARTS_BASE_DIR, "seasonality") # 新的子文件夹
DATA_DIR_PATH = "../DATA/PART1/" 
# ---

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
    # 确保索引是 DatetimeIndex (你的 loader 已经做了)
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except Exception as e:
            print(f"  Skipping {asset_name}: Could not convert index to Datetime. Error: {e}")
            return
            
    df['day_of_week'] = df.index.day_name()
    df['month'] = df.index.month_name()
    
    # 3. 为图表排序
    # 确保周一到周五排序正确
    week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    # 确保月份排序正确
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
    output_filename = f"seasonality_{asset_name}.png"
    output_path = os.path.join(save_dir, output_filename)
    
    plt.savefig(output_path)
    print(f"  Chart saved to {output_path}")
    plt.close(fig)

def main():
    """
    主执行函数：加载数据，循环处理每个资产。
    """
    print("--- 正在运行 Seasonality 分析脚本 ---")
    
    os.makedirs(SEASONALITY_SAVE_DIR, exist_ok=True)
    print(f"Charts will be saved to: {SEASONALITY_SAVE_DIR}")

    print(f"Calling eda_data_loader.load_and_merge_data(data_directory='{DATA_DIR_PATH}')...")
    try:
        merged_prices_df = eda_data_loader.load_and_merge_data(DATA_DIR_PATH)
    except Exception as e:
        print(f"Error calling eda_data_loader: {e}")
        return

    if merged_prices_df.empty:
        print("Error: Your loader returned an empty DataFrame.")
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