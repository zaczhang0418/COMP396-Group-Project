import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns 
import os
import glob
from scipy import stats
import sys # 确保导入 sys

# --- 配置 ---
# [路径修复] 我们的 'charts' 文件夹在 'EDA' 内部
CHARTS_BASE_DIR = "./EDA/output/charts" 
VOLUME_SAVE_DIR = os.path.join(CHARTS_BASE_DIR, "volume_analysis") # 新子文件夹

# [路径修复] 当从根目录运行时，路径是 './' 而不是 '../'
DATA_DIR_PATH = "./DATA/PART1/" 
# ---

# --- 策略参数 ---
RSI_PERIOD = 14
MFI_PERIOD = 14
OVERSOLD_THRESHOLD = 30
FORWARD_RETURN_DAYS = 5
# ---

# -------------------------------------------------------------------
# --- 辅助函数 (自包含) ---
# (这些函数 100% 正确，无需改动)

def calculate_rsi(series, period=RSI_PERIOD):
    """ (从 plot_rsi_analysis.py 复制而来) """
    delta = series.diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    if avg_loss.all() == 0:
         # 避免除以零，返回中性值
        return pd.Series(index=series.index, data=50)
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_mfi(high, low, close, volume, period=MFI_PERIOD):
    """
    使用纯 pandas 计算 MFI (资金流指标)。
    """
    typical_price = (high + low + close) / 3
    raw_money_flow = typical_price * volume
    price_change = typical_price.diff(1)
    
    pos_money_flow = raw_money_flow.where(price_change > 0, 0)
    neg_money_flow = raw_money_flow.where(price_change < 0, 0)
    
    pos_mf_sum = pos_money_flow.rolling(window=period, min_periods=period).sum()
    neg_mf_sum = neg_money_flow.rolling(window=period, min_periods=period).sum()
    
    # [修复] 避免除以零
    money_ratio = pos_mf_sum / (neg_mf_sum + 1e-9) # 添加一个极小值
    mfi = 100 - (100 / (1 + money_ratio))
    
    # 将 MFI 限制在 0-100 范围内 (滚动计算可能产生小误差)
    mfi = mfi.clip(0, 100)
    return mfi

def load_single_asset_ohlcv(csv_file_path):
    """
    加载并清洗*单个* CSV 文件，返回可用于 MFI 分析的 OHLCV DataFrame。
    这是一个健壮的加载器，可以处理 'Index' 或 'Date' 列。
    """
    try:
        # 1. 读取 CSV，不预设日期列
        df = pd.read_csv(csv_file_path, thousands=',')
        df.columns = df.columns.str.strip().str.strip('"')

        # 2. 动态识别并统一日期列
        if 'Index' in df.columns:
            df.rename(columns={'Index': 'date'}, inplace=True)
        elif 'Date' in df.columns:
            df.rename(columns={'Date': 'date'}, inplace=True)
        else:
            print(f"  [警告] 跳过 {os.path.basename(csv_file_path)}: 缺少 'Index' 或 'Date' 列。")
            return None

        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)

        # 3. 统一 OHLCV 列名
        df.rename(columns={
            'Open': 'open', 'High': 'high', 'Low': 'low',
            'Close': 'close', 'Volume': 'volume'
        }, inplace=True)

        # 4. 验证并清洗数据
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            print(f"  [警告] 跳过 {os.path.basename(csv_file_path)}: 缺少一个或多个 OHLCV 列。")
            return None
            
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df.dropna(inplace=True)
        df.sort_index(inplace=True)

        return df

    except Exception as e:
        print(f"  [错误] 加载 {os.path.basename(csv_file_path)} 失败: {e}")
        return None
# -------------------------------------------------------------------
# --- [!! 新增的 API 函数 (给 Notebook 调用) !!] ---
def plot_volume_signal_analysis(df, asset_name):
    """
    (新增的 API - 供 Notebook 调用)
    对 *单个资产* 的 RSI vs RSI+MFI 信号进行对比分析，并“显示”图表。
    """
    # [我们从 'analyze_volume_signal' 复制所有代码]
    print(f"  Analyzing Volume-Filtered Signals for {asset_name}...")

    df['rsi'] = calculate_rsi(df['close'], period=RSI_PERIOD)
    df['mfi'] = calculate_mfi(df['high'], df['low'], df['close'], df['volume'], period=MFI_PERIOD)
    df['fwd_returns'] = df['close'].pct_change(FORWARD_RETURN_DAYS).shift(-FORWARD_RETURN_DAYS)
    df.dropna(inplace=True)
    if df.empty:
        print(f"  Skipping {asset_name}: Not enough data.")
        return

    signals_rsi_only = df[df['rsi'] < OVERSOLD_THRESHOLD]
    signals_rsi_and_mfi = df[
        (df['rsi'] < OVERSOLD_THRESHOLD) & 
        (df['mfi'] < OVERSOLD_THRESHOLD)
    ]

    if signals_rsi_only.empty:
        print(f"  Skipping {asset_name}: No RSI signals found.")
        return
    if signals_rsi_and_mfi.empty:
        print(f"  Skipping {asset_name}: No MFI-confirmed signals found.")
        return

    print(f"\n--- Volume Filter Analysis for {asset_name} (N={FORWARD_RETURN_DAYS} Days) ---")
    print(f"  Signal (RSI < {OVERSOLD_THRESHOLD}):")
    print(f"    Signal Count: {len(signals_rsi_only)}")
    print(f"    Avg. Fwd Return: {signals_rsi_only['fwd_returns'].mean():.4f}")
    print(f"\n  Signal (RSI < {OVERSOLD_THRESHOLD} AND MFI < {OVERSOLD_THRESHOLD}):")
    print(f"    Signal Count: {len(signals_rsi_and_mfi)} (Filtered out {len(signals_rsi_only) - len(signals_rsi_and_mfi)} signals)")
    print(f"    Avg. Fwd Return: {signals_rsi_and_mfi['fwd_returns'].mean():.4f}")

    t_stat, p_value = stats.ttest_ind(
        signals_rsi_and_mfi['fwd_returns'], 
        signals_rsi_only['fwd_returns'], 
        equal_var=False, 
        alternative='greater'
    )
    print(f"\n  T-test (Filtered > RSI-Only): T-stat={t_stat:.3f}, P-value={p_value:.5f}")
    if p_value < 0.1:
        print("  ✅ 结论: MFI 过滤器 *显著* 提升了信号质量。")
    else:
        print("  ❌ 结论: MFI 过滤器未显示统计上显著的提升。")
    print("--------------------------------------------------")

    plt.figure(figsize=(12, 7))
    sns.histplot(signals_rsi_only['fwd_returns'], kde=True, bins=50, 
                 color='blue', label=f'RSI-Only (Avg: {signals_rsi_only["fwd_returns"].mean():.4f})', 
                 stat="density")
    sns.histplot(signals_rsi_and_mfi['fwd_returns'], kde=True, bins=50, 
                 color='green', label=f'RSI+MFI (Avg: {signals_rsi_and_mfi["fwd_returns"].mean():.4f})', 
                 stat="density")
    plt.title(f'Signal Quality Comparison for {asset_name}')
    plt.xlabel(f'Forward {FORWARD_RETURN_DAYS}-Day Return')
    plt.legend()
    
    # --- [!! 核心区别: "显示" !!] ---
    plt.show()
def analyze_volume_signal(df, asset_name, save_dir):
    """
    (此函数 100% 正确，无需改动)
    对 *单个资产* 的 RSI vs RSI+MFI 信号进行对比分析。
    """
    print(f"  Analyzing Volume-Filtered Signals for {asset_name}...")

    # 1. 计算指标
    df['rsi'] = calculate_rsi(df['close'], period=RSI_PERIOD)
    df['mfi'] = calculate_mfi(df['high'], df['low'], df['close'], df['volume'], period=MFI_PERIOD)
    
    # 2. 计算未来收益
    df['fwd_returns'] = df['close'].pct_change(FORWARD_RETURN_DAYS).shift(-FORWARD_RETURN_DAYS)
    
    df.dropna(inplace=True)
    if df.empty:
        print(f"  Skipping {asset_name}: Not enough data.")
        return

    # 3. 定义信号组 (这是核心对比)
    signals_rsi_only = df[df['rsi'] < OVERSOLD_THRESHOLD]
    signals_rsi_and_mfi = df[
        (df['rsi'] < OVERSOLD_THRESHOLD) & 
        (df['mfi'] < OVERSOLD_THRESHOLD) # MFI 也超卖 (即恐慌性抛售)
    ]

    if signals_rsi_only.empty:
        print(f"  Skipping {asset_name}: No RSI signals found.")
        return
    if signals_rsi_and_mfi.empty:
        print(f"  Skipping {asset_name}: No MFI-confirmed signals found.")
        return

    # 4. 统计分析
    print(f"\n--- Volume Filter Analysis for {asset_name} (N={FORWARD_RETURN_DAYS} Days) ---")
    print(f"  Signal (RSI < {OVERSOLD_THRESHOLD}):")
    print(f"    Signal Count: {len(signals_rsi_only)}")
    print(f"    Avg. Fwd Return: {signals_rsi_only['fwd_returns'].mean():.4f}")
    
    print(f"\n  Signal (RSI < {OVERSOLD_THRESHOLD} AND MFI < {OVERSOLD_THRESHOLD}):")
    print(f"    Signal Count: {len(signals_rsi_and_mfi)} (Filtered out {len(signals_rsi_only) - len(signals_rsi_and_mfi)} signals)")
    print(f"    Avg. Fwd Return: {signals_rsi_and_mfi['fwd_returns'].mean():.4f}")

    # t-检验：(B 组) vs (A 组)
    t_stat, p_value = stats.ttest_ind(
        signals_rsi_and_mfi['fwd_returns'], 
        signals_rsi_only['fwd_returns'], 
        equal_var=False, 
        alternative='greater' # 检验 B 组是否 *显著更好*
    )
    print(f"\n  T-test (Filtered > RSI-Only): T-stat={t_stat:.3f}, P-value={p_value:.5f}")
    
    if p_value < 0.1: # 使用 90% 置信
        print("  ✅ 结论: MFI 过滤器 *显著* 提升了信号质量。")
    else:
        print("  ❌ 结论: MFI 过滤器未显示统计上显著的提升。")
    print("--------------------------------------------------")

    # 5. 可视化
    plt.figure(figsize=(12, 7))
    sns.histplot(signals_rsi_only['fwd_returns'], kde=True, bins=50, 
                 color='blue', label=f'RSI-Only (Avg: {signals_rsi_only["fwd_returns"].mean():.4f})', 
                 stat="density")
    sns.histplot(signals_rsi_and_mfi['fwd_returns'], kde=True, bins=50, 
                 color='green', label=f'RSI+MFI (Avg: {signals_rsi_and_mfi["fwd_returns"].mean():.4f})', 
                 stat="density")
    
    plt.title(f'Signal Quality Comparison for {asset_name}')
    plt.xlabel(f'Forward {FORWARD_RETURN_DAYS}-Day Return')
    plt.legend()
    
    # 6. 保存图表
    output_filename = f"volume_filter_comp_{asset_name}.png"
    output_path = os.path.join(save_dir, output_filename)
    plt.savefig(output_path)
    print(f"  Chart saved to {output_path}")
    plt.close()


def main():
    """
    主执行函数：独立加载数据，循环处理。
    """
    dataset_name = "PART1"
    if len(sys.argv) > 1:
        dataset_name = sys.argv[1]

    local_data_dir = f"./DATA/{dataset_name}/"
    local_save_dir = f"./EDA/output/{dataset_name}/charts/volume_analysis/"

    print(f"--- 正在运行 Volume 信号分析脚本 [Dataset: {dataset_name}] ---")
    
    os.makedirs(local_save_dir, exist_ok=True)
    print(f"Charts & stats will be saved to: {local_save_dir}")

    # 1. 独立查找所有 CSV 文件
    csv_files_path = os.path.join(local_data_dir, "*.csv")
    files = glob.glob(csv_files_path)
    
    if not files:
        print(f"❌ 错误: 在 '{local_data_dir}' 中没有找到 .csv 文件。")
        print(f"   (绝对路径检查: {os.path.abspath(local_data_dir)})")
        return

    print(f"Found {len(files)} assets. Processing...")

    # 2. 循环加载和分析
    for f in files:
        asset_name = os.path.basename(f).split('.')[0]
        
        # 调用新的健壮加载器
        df = load_single_asset_ohlcv(f)
        
        if df is not None and not df.empty:
            # 传入 *完整的* DataFrame 进行分析
            analyze_volume_signal(df, asset_name, local_save_dir)
        # 错误和跳过信息现在由加载器内部处理
            
    print("--- Volume 信号分析全部完成 ---")

if __name__ == "__main__":
    main()