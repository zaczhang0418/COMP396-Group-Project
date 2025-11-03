import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from hurst import compute_Hc

# 1. 导入你自己的加载器
try:
    import eda_data_loader
except ImportError:
    print("Error: 'eda_data_loader.py' not found.")
    print("Please ensure this script is in the same 'EDA' folder as your loader.")
    exit()

# --- 配置 ---
CHARTS_BASE_DIR = "charts"
HURST_SAVE_DIR = os.path.join(CHARTS_BASE_DIR, "hurst")
DEFAULT_WINDOW_SIZE = 252 # 默认滚动窗口 (约 1 年)

# 你的脚本在 EDA 文件夹运行, DATA 目录在上一级
DATA_DIR_PATH = "../DATA/PART1/" 
# ---

def plot_rolling_hurst(price_series, asset_name, window_size, save_dir):
    """
    计算并绘制 *单个资产 (Series)* 的滚动 Hurst 指数，并保存图表。
    """
    if len(price_series) < window_size:
        print(f"  Skipping {asset_name}: Data length ({len(price_series)}) is shorter than window ({window_size}).")
        return

    print(f"  Calculating Rolling Hurst for {asset_name} (window={window_size})...")
    
    try:
        rolling_h = price_series.rolling(window=window_size).apply(
            lambda x: compute_Hc(x)[0], 
            raw=True
        )
    except Exception as e:
        print(f"  Error calculating Hurst for {asset_name}: {e}")
        return
    
    # --- 可视化 ---
    fig, ax = plt.subplots(figsize=(15, 7))
    rolling_h.plot(ax=ax, label=f'Rolling Hurst (window={window_size})', color='blue')
    ax.axhline(0.5, color='red', linestyle='--', label='H = 0.5 (Random Walk)')
    ax.axhline(0.4, color='green', linestyle=':', label='H < 0.5 (Mean-Reverting)')
    ax.axhline(0.6, color='purple', linestyle=':', label='H > 0.5 (Trending)')
    ax.set_title(f'Rolling Hurst Exponent for {asset_name}')
    ax.set_xlabel('Date')
    ax.set_ylabel('Hurst Value (H)')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # --- 保存图表 ---
    output_filename = f"hurst_rolling_{asset_name}_w{window_size}.png"
    output_path = os.path.join(save_dir, output_filename)
    plt.savefig(output_path)
    print(f"  Chart saved to {output_path}")
    plt.close(fig) # 关闭图表，防止内存泄漏

def main():
    """
    主执行函数：加载所有数据，循环处理并保存图表。
    """
    print("--- 正在运行 Hurst 分析脚本 (V2 - 适配 Loader) ---")
    
    # 1. 确保目标保存目录存在
    os.makedirs(HURST_SAVE_DIR, exist_ok=True)
    print(f"Charts will be saved to: {HURST_SAVE_DIR}")

    # 2. 从你的加载器加载数据
    print(f"Calling eda_data_loader.load_and_merge_data(data_directory='{DATA_DIR_PATH}')...")
    try:
        # *** 这就是修正的地方 ***
        # 我们调用你 loader 里的正确函数
        merged_prices_df = eda_data_loader.load_and_merge_data(DATA_DIR_PATH)
    
    except AttributeError:
        # 万一你又改了函数名，这里会捕获
        print("Error: 'load_and_merge_data' not found in eda_data_loader.")
        print("Please check the function name in your loader script.")
        return
    except Exception as e:
        print(f"Error calling eda_data_loader: {e}")
        return

    if merged_prices_df.empty:
        print("Error: Your loader returned an empty DataFrame. Check DATA_DIR_PATH.")
        return

    print(f"✅ Loader success. Loaded merged DataFrame with {len(merged_prices_df.columns)} assets.")

    # 3. 循环遍历 *合并后 DataFrame 的每一列*
    for asset_name in merged_prices_df.columns:
        price_series = merged_prices_df[asset_name].dropna()
        
        if isinstance(price_series, pd.Series) and not price_series.empty:
            plot_rolling_hurst(price_series, 
                               asset_name, 
                               DEFAULT_WINDOW_SIZE, 
                               HURST_SAVE_DIR)
        else:
            print(f"Skipping {asset_name}: No valid data.")
            
    print("--- Hurst 分析全部完成 ---")


if __name__ == "__main__":
    main()