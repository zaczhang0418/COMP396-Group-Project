import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
# from scipy import stats # 移除 pandas-ta
from scipy import stats # 导入 scipy.stats 用于 t-检验

# 1. 导入你自己的加载器
try:
    import eda_data_loader
except ImportError:
    print("Error: 'eda_data_loader.py' not found.")
    print("Please ensure this script is in the same 'EDA' folder as your loader.")
    exit()

# --- 配置 ---
CHARTS_BASE_DIR = "charts"
RSI_SAVE_DIR = os.path.join(CHARTS_BASE_DIR, "rsi_analysis") # 新的子文件夹
DATA_DIR_PATH = "../DATA/PART1/" 

# --- 策略参数 ---
RSI_PERIOD = 14     # RSI 的计算周期
RSI_OVERSOLD = 30 # 超卖阈值
FORWARD_RETURN_DAYS = 5 # 测试未来 N 天的收益
# ---

# -------------------------------------------------------------------
# --- [ 替代方案 ] ---
# 我们自己实现 RSI，不使用 pandas-ta
def calculate_rsi(series, period=RSI_PERIOD):
    """
    使用纯 pandas 计算 RSI，不依赖外部库。
    使用 Wilder's Smoothing (RMA)，这是 RSI 的标准。
    """
    # 1. 计算价格变动
    delta = series.diff(1)
    
    # 2. 分离收益和损失
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # 3. 计算 Wilder's Smoothing (RMA)
    # 这等同于 ewm(com=period-1)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    # 4. 计算 RS 和 RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi
# --- [ 替代方案结束 ] ---
# -------------------------------------------------------------------

def analyze_rsi_signal(price_series, asset_name, save_dir):
    """
    对 *单个资产* 的 RSI 信号进行回测和统计分析。
    """
    print(f"  Analyzing RSI({RSI_PERIOD}) < {RSI_OVERSOLD} signal for {asset_name}...")

    # 1. 准备数据 DataFrame
    df = pd.DataFrame({'Close': price_series})

    # 2. 计算 RSI (使用我们自己的函数)
    df['rsi'] = calculate_rsi(df['Close'], period=RSI_PERIOD)

    # 3. 计算未来 N 天的收益率 (我们的目标变量)
    df['fwd_returns'] = df['Close'].pct_change(FORWARD_RETURN_DAYS).shift(-FORWARD_RETURN_DAYS)

    # 4. 丢弃所有包含 NaN 的行 (RSI 早期 和 最后的 fwd_returns)
    df.dropna(inplace=True)

    if df.empty:
        print(f"  Skipping {asset_name}: Not enough data after calculations.")
        return

    # 5. 找出所有信号 (RSI < 30)
    signals = df[df['rsi'] < RSI_OVERSOLD]
    all_non_signals = df[df['rsi'] >= RSI_OVERSOLD] # 作为对比

    if signals.empty:
        print(f"  Skipping {asset_name}: No RSI < {RSI_OVERSOLD} signals found.")
        return

    # 6. 统计分析 (COMP396 报告的核心)
    print(f"\n--- RSI Signal Analysis for {asset_name} (N={FORWARD_RETURN_DAYS} Days) ---")
    print(f"Total days analyzed: {len(df)}")
    print(f"Days with RSI < {RSI_OVERSOLD} signal: {len(signals)}")
    
    mean_return_signal = signals['fwd_returns'].mean()
    mean_return_all = df['fwd_returns'].mean()
    
    print(f"  Avg. Forward Return (All Days): {mean_return_all: .4f}")
    print(f"  Avg. Forward Return (Signal Days): {mean_return_signal: .4f}")

    # t-检验：检验信号收益率的均值是否 *显著大于* 所有日期的均值
    t_stat, p_value = stats.ttest_ind(signals['fwd_returns'], 
                                    all_non_signals['fwd_returns'], 
                                    equal_var=False, 
                                    alternative='greater') 

    print(f"  T-statistic (Signal vs Non-Signal): {t_stat: .3f}")
    print(f"  P-value (Signal > Non-Signal): {p_value: .5f}")
    
    if p_value < 0.05:
        print("  ✅ 结论: 信号在 95% 置信水平上 *显著* 跑赢大盘。")
    else:
        print("  ❌ 结论: 信号未表现出统计显著性。")
    print("--------------------------------------------------")

    # 7. 可视化：绘制信号日未来收益的直方图
    plt.figure(figsize=(12, 7))
    sns.histplot(signals['fwd_returns'], kde=True, bins=50, color='green', 
                 label=f'Forward Returns after RSI < {RSI_OVERSOLD}')
    plt.axvline(0, color='black', linestyle='--', label='Zero Return')
    plt.axvline(mean_return_signal, color='red', linestyle='-', 
                label=f'Mean Return ({mean_return_signal:.4f})')
    
    plt.title(f'Forward {FORWARD_RETURN_DAYS}-Day Return Distribution for {asset_name} (RSI < {RSI_OVERSOLD})')
    plt.xlabel(f'Forward {FORWARD_RETURN_DAYS}-Day Return')
    plt.ylabel('Frequency')
    plt.legend()
    
    # 8. 保存图表
    output_filename = f"rsi_fwd_returns_hist_{asset_name}.png"
    output_path = os.path.join(save_dir, output_filename)
    
    plt.savefig(output_path)
    print(f"  Chart saved to {output_path}")
    plt.close()

def main():
    """
    主执行函数：加载数据，循环处理每个资产。
    """
    print("--- 正在运行 RSI 信号分析脚本 (V2 - 无 pandas-ta) ---")
    
    os.makedirs(RSI_SAVE_DIR, exist_ok=True)
    print(f"Charts & stats will be saved to: {RSI_SAVE_DIR}")

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
            analyze_rsi_signal(price_series, 
                             asset_name, 
                             RSI_SAVE_DIR)
        else:
            print(f"Skipping {asset_name}: No valid data.")
            
    print("--- RSI 信号分析全部完成 ---")

if __name__ == "__main__":
    main()