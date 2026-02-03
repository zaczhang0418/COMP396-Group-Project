import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import matplotlib.ticker as mticker
import seaborn as sns 
import glob # 确保导入
import sys # 确保导入

# -----------------------------------------------------------------
# (数据加载函数 - 这是一个独立的 OHLCV 加载器)
# (它和 'plot_candlestick.py' 里的加载器逻辑一致)
# -----------------------------------------------------------------
def load_single_asset_ohlcv(csv_file_path):
    """
    加载并清洗*单个* CSV 文件，返回可用于 K 线图和 ATR 的 OHLCV DataFrame。
    [这是我们最健壮的 OHLCV 加载器]
    """
    try:
        data = pd.read_csv(
            csv_file_path, 
            parse_dates=['Index'], 
            index_col=None, # [我们的修复]
            thousands=','   # [我们的修复]
        )
        
        data.columns = data.columns.str.strip().str.strip('"')
        data.rename(columns={
            'Open': 'open', 'High': 'high', 'Low': 'low',
            'Close': 'close', 'Volume': 'volume',
            'Index': 'date' # [我们的修复]
        }, inplace=True)

        if 'date' not in data.columns:
            print(f" 警告: {os.path.basename(csv_file_path)} 缺少 'Index'/'date' 列。")
            return None

        data.set_index('date', inplace=True)
        
        required_cols = ['open', 'high', 'low', 'close']
        for col in required_cols:
            if col not in data.columns:
                print(f" 警告: {os.path.basename(csv_file_path)} 缺少 '{col}' 列。")
                return None
            # [我们的修复] 强制转换为数字
            data[col] = pd.to_numeric(data[col], errors='coerce')

        data.dropna(subset=required_cols, inplace=True)
        return data

    except Exception as e:
        print(f" 警告: 加载 {csv_file_path} 时出错: {e}")
        return None
# -----------------------------------------------------------------
# (数据加载函数结束)
# -----------------------------------------------------------------


# --- 1. 队友的 ATR 计算函数 (完美, 保留) ---
def calculate_atr(df, length=14):
    """
    计算 Average True Range (ATR)。
    """
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift(1))
    low_close = np.abs(df['low'] - df['close'].shift(1))
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    
    atr = true_range.ewm(span=length, adjust=False).mean()
    
    return atr

# --- 2. 核心绘图逻辑 (来自队友, 封装为 API) ---

def _plot_volatility_core(ohlcv_df, asset_name):
    """
    (V2 辅助函数)
    包含队友的所有核心计算和绘图设置，返回 fig, ax1。
    """
    plot_df = ohlcv_df.copy() 
    
    # 队友的核心计算
    plot_df['Log_Returns'] = np.log(plot_df['close'] / plot_df['close'].shift(1))
    plot_df['Vol_20D'] = plot_df['Log_Returns'].rolling(window=20).std() * np.sqrt(252) # 年化
    plot_df['Vol_60D'] = plot_df['Log_Returns'].rolling(window=60).std() * np.sqrt(252) # 年化
    plot_df['ATR'] = calculate_atr(plot_df, length=14)
    
    plot_df.dropna(subset=['Vol_60D', 'ATR'], inplace=True)
    
    if plot_df.empty:
        print(f"警告：{asset_name} 在清理 NaN 值后数据为空，无法绘图。")
        return None, None
        
    # 队友的绘图设置
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax1 = plt.subplots(figsize=(14, 6))

    ax1.plot(plot_df.index, plot_df['Vol_60D'], label='60-Day Ann. Rolling StDev (Smoothed)', color='tab:blue', linewidth=1.5)
    ax1.plot(plot_df.index, plot_df['Vol_20D'], label='20-Day Ann. Rolling StDev (Sensitive)', color='tab:blue', alpha=0.5, linestyle='--')
    ax1.set_ylabel('Volatility (Annualized Rolling StDev)', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax1.set_title(f'{asset_name} - Volatility Clustering Analysis (StDev vs ATR)')
    ax1.set_xlabel('Date')
    
    ax2 = ax1.twinx() 
    ax2.plot(plot_df.index, plot_df['ATR'], label='14-Day ATR (Right Axis)', color='tab:red', linewidth=1)
    ax2.set_ylabel('Average True Range (ATR)', color='tab:red')
    ax2.tick_params(axis='y', labelcolor='tab:red')
    
    fig.legend(loc='upper right', bbox_to_anchor=(0.9, 0.9))
    
    return fig, ax1

def plot_volatility_analysis_v2(ohlcv_df, asset_name):
    """
    (供 Notebook 调用)
    绘制 V2 波动率图表并直接 'show()'。
    """
    fig, ax1 = _plot_volatility_core(ohlcv_df, asset_name)
    if fig is not None:
        plt.show()

def save_volatility_analysis_v2(ohlcv_df, asset_name, save_path=""):
    """
    (供本地运行调用)
    绘制 V2 波动率图表并 'savefig()'。
    """
    fig, ax1 = _plot_volatility_core(ohlcv_df, asset_name)
    if fig is None:
        return # 如果绘图失败，则不保存

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig.savefig(save_path, bbox_inches='tight') 
    plt.close(fig) 
    print(f"  [V2] 图表已保存到: {save_path}")


# --- 3. 主执行逻辑 (Standalone Runner) ---
if __name__ == "__main__":
    
    dataset_name = "PART1"
    if len(sys.argv) > 1:
        dataset_name = sys.argv[1]

    print(f"--- 正在以独立模式运行 (Volatility Plotter) [Dataset: {dataset_name}] ---")
    
    DATA_PATH = f"./DATA/{dataset_name}/" 
    SAVE_DIR = f"./EDA/output/{dataset_name}/charts/volatility/" 

    print(f"正在从 '{DATA_PATH}' 加载数据...")
    csv_files = glob.glob(os.path.join(DATA_PATH, '*.csv'))
    
    if not csv_files:
        print(f"错误：在 '{DATA_PATH}' 文件夹里没有找到任何 .csv 文件。")
        sys.exit(1)
        
    print(f"找到了 {len(csv_files)} 个 CSV 文件。开始批量处理...")

    for csv_file_path in csv_files:
        asset_name = os.path.basename(csv_file_path).split('.')[0]
        print(f"  正在处理: {asset_name}")
        
        # --- [!! 关键升级 !!] ---
        # 1. 使用我们健壮的 OHLCV 加载器
        full_df = load_single_asset_ohlcv(csv_file_path)
        # --- [升级结束] ---
        
        if full_df is not None:
            # 2. 构造保存路径
            save_file_path = os.path.join(SAVE_DIR, f"{asset_name}_volatility_v2_atr.png")
            
            # 3. 调用我们新的“保存”函数
            save_volatility_analysis_v2(full_df, asset_name, save_path=save_file_path)
        else:
            print(f"  [跳过] {asset_name} 因加载失败而被跳过。")
            
    print("--- 波动率图表批量生成和保存完毕 ---")