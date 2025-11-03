import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
import sys # 确保导入 sys

# --- [!! 关键依赖 !!] ---
# 这个脚本需要 'hurst' 库。
# 你必须先在你的 comp396 环境中安装它：
# pip install hurst
# -------------------------
try:
    from hurst import compute_Hc
except ImportError:
    print("❌ 致命错误: 'hurst' 库未安装。")
    print("   请在你的 VS Code 终端中运行:")
    print("   conda activate comp396")
    print("   pip install hurst")
    sys.exit(1)

# --- 配置 ---
# [路径修复] 修正为 Zac 的本地路径
HURST_SAVE_DIR = "./EDA/charts/hurst/"
DATA_DIR_PATH = "./DATA/PART1/" 
DEFAULT_WINDOW_SIZE = 252 # 默认滚动窗口 (约 1 年)
# ---

# -----------------------------------------------------------------
# (数据加载函数，使用我们昨天的“最终修复版-老师的逻辑”)
# (这是 'Close-Only' 版本，Hurst 只需要 Close 价格)
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
# -----------------------------------------------------------------
# (数据加载函数结束)
# -----------------------------------------------------------------


# --- [!! 优化 V2: 双轴图表 !!] ---

def save_rolling_hurst_v2(price_series, asset_name, window_size, save_dir):
    """
    (已优化 V2)
    计算滚动 Hurst，并绘制“价格 vs Hurst”的双轴图表。
    """
    if len(price_series) < window_size:
        print(f"  Skipping {asset_name}: Data length ({len(price_series)}) is shorter than window ({window_size}).")
        return

    print(f"  Calculating Rolling Hurst for {asset_name} (window={window_size})...")
    
    try:
        # 1. 计算滚动 H
        rolling_h = price_series.rolling(window=window_size).apply(
            lambda x: compute_Hc(x)[0], 
            raw=True
        ).dropna()
        
        # 2. 为了对齐，我们也截取价格数据
        log_price = np.log(price_series).loc[rolling_h.index]
        
    except Exception as e:
        print(f"  Error calculating Hurst for {asset_name}: {e}")
        return
    
    if rolling_h.empty:
        print(f"  Skipping {asset_name}: Hurst calculation returned empty series.")
        return

    # --- 可视化 (V2 双轴) ---
    fig, ax1 = plt.subplots(figsize=(15, 7))
    
    # Y1 轴 (左): 绘制 Log(Price)
    color1 = 'tab:blue'
    ax1.plot(log_price.index, log_price, color=color1, label='Log(Price) (Left Axis)', alpha=0.6)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Log(Price)', color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)
    
    # Y2 轴 (右): 绘制 Hurst
    ax2 = ax1.twinx()
    color2 = 'tab:red'
    ax2.plot(rolling_h.index, rolling_h, color=color2, label=f'Rolling Hurst (w={window_size}) (Right Axis)')
    
    # 绘制关键阈值线
    ax2.axhline(0.5, color='black', linestyle='--', label='H = 0.5 (Random Walk)')
    ax2.axhline(0.4, color='green', linestyle=':', label='H < 0.5 (Mean-Reverting)')
    ax2.axhline(0.6, color='purple', linestyle=':', label='H > 0.5 (Trending)')
    
    ax2.set_ylabel('Hurst Value (H)', color=color2)
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.set_ylim(0, 1) # Hurst 必须在 0 和 1 之间
    
    fig.suptitle(f'Rolling Hurst Exponent vs. Log(Price) for {asset_name}', fontsize=16)
    fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9)) # 整合两个图例
    
    # --- 保存图表 ---
    os.makedirs(save_dir, exist_ok=True)
    output_filename = f"hurst_v2_dual_axis_{asset_name}_w{window_size}.png"
    output_path = os.path.join(save_dir, output_filename)
    plt.savefig(output_path, bbox_inches='tight')
    print(f"  [V2] Dual-Axis chart saved to {output_path}")
    plt.close(fig)

def main():
    """
    主执行函数：加载所有数据，循环处理并保存图表。
    """
    print("--- 正在运行 Hurst 分析脚本 (V2 - 双轴优化) ---")
    
    os.makedirs(HURST_SAVE_DIR, exist_ok=True)
    print(f"Charts will be saved to: {HURST_SAVE_DIR}")

    # 2. 从我们 *自包含* 的加载器加载数据
    print(f"Calling internal load_and_merge_data(data_directory='{DATA_DIR_PATH}')...")
    
    merged_prices_df = load_and_merge_data(DATA_DIR_PATH)

    if merged_prices_df.empty:
        print("Error: Loader returned an empty DataFrame. Check DATA_DIR_PATH.")
        return

    print(f"✅ Loader success. Loaded merged DataFrame with {len(merged_prices_df.columns)} assets.")

    # 3. 循环遍历 *合并后 DataFrame 的每一列*
    for asset_name in merged_prices_df.columns:
        price_series = merged_prices_df[asset_name].dropna()
        
        if isinstance(price_series, pd.Series) and not price_series.empty:
            # [!! 优化 !!] 调用 V2 绘图函数
            save_rolling_hurst_v2(price_series, 
                                  asset_name, 
                                  DEFAULT_WINDOW_SIZE, 
                                  HURST_SAVE_DIR)
        else:
            print(f"Skipping {asset_name}: No valid data.")
            
    print("--- Hurst 分析全部完成 ---")


if __name__ == "__main__":
    main()