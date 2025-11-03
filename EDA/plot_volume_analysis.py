import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
from scipy import stats

# --- 配置 ---
CHARTS_BASE_DIR = "charts"
VOLUME_SAVE_DIR = os.path.join(CHARTS_BASE_DIR, "volume_analysis") # 新子文件夹
DATA_DIR_PATH = "../DATA/PART1/" # 脚本在 EDA/，数据在上一级

# --- 策略参数 ---
RSI_PERIOD = 14
MFI_PERIOD = 14
OVERSOLD_THRESHOLD = 30
FORWARD_RETURN_DAYS = 5
# ---

# -------------------------------------------------------------------
# --- 辅助函数 (自包含) ---

def calculate_rsi(series, period=RSI_PERIOD):
    """ (从 plot_rsi_analysis.py 复制而来) """
    delta = series.diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_mfi(high, low, close, volume, period=MFI_PERIOD):
    """
    使用纯 pandas 计算 MFI (资金流指标)。
    """
    # 1. 典型价格 (Typical Price)
    typical_price = (high + low + close) / 3
    
    # 2. 原始资金流 (Raw Money Flow)
    raw_money_flow = typical_price * volume
    
    # 3. 资金流方向 (Positive/Negative Money Flow)
    price_change = typical_price.diff(1)
    
    pos_money_flow = raw_money_flow.where(price_change > 0, 0)
    neg_money_flow = raw_money_flow.where(price_change < 0, 0)
    
    # 4. 14 日资金流
    pos_mf_sum = pos_money_flow.rolling(window=period, min_periods=period).sum()
    neg_mf_sum = neg_money_flow.rolling(window=period, min_periods=period).sum()
    
    # 5. MFI
    if neg_mf_sum.all() == 0: # 避免除以零
        return pd.Series(index=high.index, data=100)
        
    money_ratio = pos_mf_sum / neg_mf_sum
    mfi = 100 - (100 / (1 + money_ratio))
    
    return mfi

# -------------------------------------------------------------------

def analyze_volume_signal(df, asset_name, save_dir):
    """
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
    print("--- 正在运行 Volume 信号分析脚本 (独立版) ---")
    
    os.makedirs(VOLUME_SAVE_DIR, exist_ok=True)
    print(f"Charts & stats will be saved to: {VOLUME_SAVE_DIR}")

    # 1. 独立查找所有 CSV 文件
    csv_files_path = os.path.join(DATA_DIR_PATH, "*.csv")
    files = glob.glob(csv_files_path)
    
    if not files:
        print(f"❌ 错误: 在 '{DATA_DIR_PATH}' 中没有找到 .csv 文件。")
        return

    print(f"Found {len(files)} assets. Processing...")

    # 2. 循环加载和分析
    for f in files:
        asset_name = os.path.basename(f).split('.')[0]
        try:
            # 3. 复制你 loader 里的清洗逻辑
            df = pd.read_csv(
                f, 
                parse_dates=['Index'],
                thousands=','
            )
            df.columns = df.columns.str.strip().str.strip('"')
            df.rename(columns={
                'Index': 'date', 'Open': 'open', 'High': 'high',
                'Low': 'low', 'Close': 'close', 'Volume': 'volume'
            }, inplace=True)
            
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                print(f"Skipping {asset_name}: 缺少 OHLCV 列。")
                continue
                
            for col in required_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df.dropna(inplace=True)
            
            if df.empty:
                print(f"Skipping {asset_name}: 加载后数据为空。")
                continue
            
            # 4. 传入 *完整的* DataFrame 进行分析
            analyze_volume_signal(df, asset_name, VOLUME_SAVE_DIR)
            
        except Exception as e:
            print(f" 警告: 处理 {asset_name} 出错: {e}")
            
    print("--- Volume 信号分析全部完成 ---")

if __name__ == "__main__":
    main()