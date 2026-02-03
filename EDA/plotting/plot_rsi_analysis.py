import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns 
import os
from scipy import stats # 导入 scipy.stats 用于 t-检验
import sys # 确保导入 sys
import glob # 确保导入 glob

# --- 配置 ---
# [路径修复] 修正为 Zac 的本地路径
RSI_SAVE_DIR = "./EDA/output/charts/rsi_analysis/" 
DATA_DIR_PATH = "./DATA/PART1/" 

# --- 策略参数 ---
RSI_PERIOD = 14     # RSI 的计算周期
RSI_OVERSOLD = 30 # 超卖阈值
FORWARD_RETURN_DAYS = 5 # 测试未来 N 天的收益
# ---

# -----------------------------------------------------------------
# (数据加载函数，使用我们昨天的“最终修复版-老师的逻辑”)
# (这是 'Close-Only' 版本，RSI 只需要 Close 价格)
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
    # [优化] 向前填充 NaN，以防止 pct_change 计算因假期错位而失败
    merged.ffill(inplace=True) 
    return merged
# -----------------------------------------------------------------
# (数据加载函数结束)
# -----------------------------------------------------------------


# -------------------------------------------------------------------
# --- [ 队友的 RSI 实现 (完美, 保留) ] ---
def calculate_rsi(series, period=RSI_PERIOD):
    """
    使用纯 pandas 计算 RSI，不依赖外部库。
    使用 Wilder's Smoothing (RMA)，这是 RSI 的标准。
    """
    delta = series.diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    # [修复] 避免除以零
    rs = avg_gain / (avg_loss + 1e-9) 
    rsi = 100 - (100 / (1 + rs))
    
    return rsi
# --- [ 队友的 RSI 实现结束 ] ---
# -------------------------------------------------------------------
# --- [!! 新增的 API 函数 (给 Notebook 调用) !!] ---
def plot_rsi_signal_analysis(price_series, asset_name):
    """
    (新增的 API - 供 Notebook 调用)
    对 *单个资产* 的 RSI 信号进行回测和统计分析，并“显示”图表。
    """
    # [我们从 'analyze_rsi_signal' 复制所有代码]
    print(f"  Analyzing RSI({RSI_PERIOD}) < {RSI_OVERSOLD} signal for {asset_name}...")

    df = pd.DataFrame({'Close': price_series})
    df['rsi'] = calculate_rsi(df['Close'], period=RSI_PERIOD)
    df['fwd_returns'] = df['Close'].pct_change(FORWARD_RETURN_DAYS).shift(-FORWARD_RETURN_DAYS)
    df.dropna(inplace=True)

    if df.empty:
        print(f"  Skipping {asset_name}: Not enough data after calculations.")
        return

    signals = df[df['rsi'] < RSI_OVERSOLD]
    all_non_signals = df[df['rsi'] >= RSI_OVERSOLD] 

    if signals.empty:
        print(f"  Skipping {asset_name}: No RSI < {RSI_OVERSOLD} signals found.")
        return
    if all_non_signals.empty:
        print(f"  Skipping {asset_name}: No non-signal days found for comparison.")
        return

    print(f"\n--- RSI Signal Analysis for {asset_name} (N={FORWARD_RETURN_DAYS} Days) ---")
    print(f"Total days analyzed: {len(df)}")
    print(f"Days with RSI < {RSI_OVERSOLD} signal: {len(signals)}")
    mean_return_signal = signals['fwd_returns'].mean()
    mean_return_all = df['fwd_returns'].mean()
    print(f"  Avg. Forward Return (All Days): {mean_return_all: .4f}")
    print(f"  Avg. Forward Return (Signal Days): {mean_return_signal: .4f}")

    t_stat, p_value = stats.ttest_ind(signals['fwd_returns'], 
                                      all_non_signals['fwd_returns'], 
                                      equal_var=False, 
                                      alternative='greater') 
    print(f"  T-statistic (Signal vs Non-Signal): {t_stat: .3f}")
    print(f"  P-value (Signal > Non-Signal): {p_value: .5f}")
    if p_value < 0.05:
        print("  ✅ 结论: 信号在 95% 置信水平上 *显著* 跑赢 (statistically significant)。")
    else:
        print("  ❌ 结论: 信号未表现出统计显著性。")
    print("--------------------------------------------------")

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
    
    # --- [!! 核心区别: "显示" !!] ---
    plt.show()

def analyze_rsi_signal(price_series, asset_name, save_dir):
    """
    (队友的核心逻辑 - 100% 保留)
    对 *单个资产* 的 RSI 信号进行回测和统计分析。
    """
    print(f"  Analyzing RSI({RSI_PERIOD}) < {RSI_OVERSOLD} signal for {asset_name}...")

    df = pd.DataFrame({'Close': price_series})
    df['rsi'] = calculate_rsi(df['Close'], period=RSI_PERIOD)
    df['fwd_returns'] = df['Close'].pct_change(FORWARD_RETURN_DAYS).shift(-FORWARD_RETURN_DAYS)
    df.dropna(inplace=True)

    if df.empty:
        print(f"  Skipping {asset_name}: Not enough data after calculations.")
        return

    signals = df[df['rsi'] < RSI_OVERSOLD]
    all_non_signals = df[df['rsi'] >= RSI_OVERSOLD] 

    if signals.empty:
        print(f"  Skipping {asset_name}: No RSI < {RSI_OVERSOLD} signals found.")
        return
    
    if all_non_signals.empty:
        print(f"  Skipping {asset_name}: No non-signal days found for comparison.")
        return

    # --- 统计分析 (COMP396 报告的核心) ---
    print(f"\n--- RSI Signal Analysis for {asset_name} (N={FORWARD_RETURN_DAYS} Days) ---")
    print(f"Total days analyzed: {len(df)}")
    print(f"Days with RSI < {RSI_OVERSOLD} signal: {len(signals)}")
    
    mean_return_signal = signals['fwd_returns'].mean()
    mean_return_all = df['fwd_returns'].mean()
    
    print(f"  Avg. Forward Return (All Days): {mean_return_all: .4f}")
    print(f"  Avg. Forward Return (Signal Days): {mean_return_signal: .4f}")

    # t-检验：检验信号收益率的均值是否 *显著大于* *非*信号日的均值
    t_stat, p_value = stats.ttest_ind(signals['fwd_returns'], 
                                      all_non_signals['fwd_returns'], 
                                      equal_var=False, 
                                      alternative='greater') # 'greater' 检验信号收益是否 > 非信号

    print(f"  T-statistic (Signal vs Non-Signal): {t_stat: .3f}")
    print(f"  P-value (Signal > Non-Signal): {p_value: .5f}")
    
    if p_value < 0.05:
        print("  ✅ 结论: 信号在 95% 置信水平上 *显著* 跑赢 (statistically significant)。")
    else:
        print("  ❌ 结论: 信号未表现出统计显著性。")
    print("--------------------------------------------------")

    # --- 可视化 (来自队友) ---
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
    
    # --- 保存图表 (来自队友) ---
    output_filename = f"rsi_fwd_returns_hist_{asset_name}.png"
    output_path = os.path.join(save_dir, output_filename)
    
    plt.savefig(output_path)
    print(f"  Chart saved to {output_path}")
    plt.close()

def main():
    """
    主执行函数：加载数据，循环处理每个资产。
    """
    dataset_name = "PART1"
    if len(sys.argv) > 1:
        dataset_name = sys.argv[1]

    local_data_dir = f"./DATA/{dataset_name}/"
    local_save_dir = f"./EDA/output/{dataset_name}/charts/rsi_analysis/"

    print(f"--- 正在运行 RSI 信号分析脚本 [Dataset: {dataset_name}] ---")
    
    os.makedirs(local_save_dir, exist_ok=True)
    print(f"Charts & stats will be saved to: {local_save_dir}")

    print(f"Calling internal load_and_merge_data(data_directory='{local_data_dir}')...")
    
    merged_prices_df = load_and_merge_data(local_data_dir)

    if merged_prices_df.empty:
        print("Error: Loader returned an empty DataFrame.")
        return

    print(f"✅ Loader success. Loaded merged DataFrame with {len(merged_prices_df.columns)} assets.")

    # 循环遍历 *合并后 DataFrame 的每一列*
    for asset_name in merged_prices_df.columns:
        price_series = merged_prices_df[asset_name].dropna()
        
        if isinstance(price_series, pd.Series) and not price_series.empty:
            analyze_rsi_signal(price_series, 
                               asset_name, 
                               local_save_dir)
        else:
            print(f"Skipping {asset_name}: No valid data.")
            
    print("--- RSI 信号分析全部完成 ---")


if __name__ == "__main__":
    main()