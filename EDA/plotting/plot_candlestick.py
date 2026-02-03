import pandas as pd
import mplfinance as mpf
import sys
import os
import glob 

# -----------------------------------------------------------------
# (数据加载函数 - 保持和 'plot_volatility.py' 一致)
# (这个加载器 100% 正确，无需改动)
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
            data[col] = pd.to_numeric(data[col], errors='coerce')

        data.dropna(subset=required_cols, inplace=True)
        return data

    except Exception as e:
        print(f" 警告: 加载 {csv_file_path} 时出错: {e}")
        return None
# -----------------------------------------------------------------
# (数据加载函数结束)
# -----------------------------------------------------------------


# --- (V3 辅助函数) ---
def _resample_to_weekly(ohlcv_df):
    """
    将日线 OHLCV 数据重采样 (resample) 为周线 OHLCV 数据。
    """
    resampled_df = ohlcv_df.resample('W-FRI').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })
    resampled_df.dropna(inplace=True)
    return resampled_df

# --- 2. 优化的 API 函数 (V4) ---

def plot_candlestick_v4(ohlcv_df, asset_name, zoom_days=150, show_weekly=True):
    """
    (供 Notebook 调用 - V4 优化版)
    绘制 *两个* 图表：
    1. 完整的周线图（用于战略背景）
    2. 缩放的日线图（用于战术细节）
    """
    if ohlcv_df is None or ohlcv_df.empty:
        print(f" 警告: {asset_name} 的 OHLCV 数据为空，跳过绘图。")
        return
        
    # --- 图 1: 周线图 (战略) ---
    if show_weekly:
        weekly_df = _resample_to_weekly(ohlcv_df)
        if not weekly_df.empty:
            print(f"--- 正在绘制 V4 K 线图 (1/2): {asset_name} (Weekly - Full History) ---")
            mpf.plot(
                weekly_df,
                type='candle',
                style='binance',
                title=f'Candlestick Chart - {asset_name} (Weekly - Full History)',
                ylabel='Price ($)',
                volume=True,
                ylabel_lower='Volume (Weekly)',
                figratio=(16, 9),
                mav=(10, 30) # 10 周 (约 50 天) 和 30 周 (约 150 天) 均线
            )
        
    # --- 图 2: 日线图 (战术) ---
    if len(ohlcv_df) < zoom_days:
        plot_df = ohlcv_df
    else:
        plot_df = ohlcv_df.tail(zoom_days)

    print(f"--- 正在绘制 V4 K 线图 (2/2): {asset_name} (Daily - Last {len(plot_df)} Days) ---")
    
    mpf.plot(
        plot_df,
        type='candle',
        style='binance',
        title=f'Candlestick Chart - {asset_name} (Daily - Last {len(plot_df)} Days)',
        ylabel='Price ($)',
        volume=True,
        ylabel_lower='Volume (Daily)',
        figratio=(16, 9),
        mav=(20, 50) # 20 天 和 50 天 均线
    )

def save_candlestick_plot_v4(ohlcv_df, asset_name, base_save_dir, zoom_days=150):
    """
    (供本地运行调用 - V4 优化版)
    保存 *两个* 图表到 *两个不同* 的子文件夹。
    """
    if ohlcv_df is None or ohlcv_df.empty:
        print(f" 警告: {asset_name} 数据为空，跳过保存。")
        return

    # --- [!! 关键优化 V4: 创建子文件夹 !!] ---
    save_dir_weekly = os.path.join(base_save_dir, "weekly_full")
    save_dir_daily = os.path.join(base_save_dir, f"daily_zoomed_{zoom_days}")
    
    os.makedirs(save_dir_weekly, exist_ok=True)
    os.makedirs(save_dir_daily, exist_ok=True)
    # --- [优化结束] ---

    # --- 1. 保存周线图 ---
    weekly_df = _resample_to_weekly(ohlcv_df)
    if not weekly_df.empty:
        save_path_weekly = os.path.join(save_dir_weekly, f"{asset_name}_candlestick_V4_Weekly_Full.png")
        mpf.plot(
            weekly_df,
            type='candle', style='binance',
            title=f'Candlestick Chart - {asset_name} (Weekly - Full History)',
            ylabel='Price ($)', volume=True, ylabel_lower='Volume (Weekly)',
            figratio=(16, 9), mav=(10, 30),
            savefig=save_path_weekly
        )
        print(f"  [V4] 周线图已保存到: {save_path_weekly}")

    # --- 2. 保存日线图 ---
    if len(ohlcv_df) < zoom_days:
        plot_df = ohlcv_df
    else:
        plot_df = ohlcv_df.tail(zoom_days)
    
    save_path_daily = os.path.join(save_dir_daily, f"{asset_name}_candlestick_V4_Daily_Zoomed.png")
    mpf.plot(
        plot_df,
        type='candle', style='binance',
        title=f'Candlestick Chart - {asset_name} (Daily - Last {len(plot_df)} Days)',
        ylabel='Price ($)', volume=True, ylabel_lower='Volume (Daily)',
        figratio=(16, 9), mav=(20, 50),
        savefig=save_path_daily
    )
    print(f"  [V4] 日线图已保存到: {save_path_daily}")


# --- 3. 本地运行块 (Standalone Runner) [V4] ---
if __name__ == "__main__":
    
    dataset_name = "PART1"
    if len(sys.argv) > 1:
        dataset_name = sys.argv[1]

    print(f"--- 正在以独立模式运行 (Candlestick Plotter) [Dataset: {dataset_name}] ---")
    
    DATA_PATH = f"./DATA/{dataset_name}/" 
    SAVE_DIR_BASE = f"./EDA/output/{dataset_name}/charts/candlesticks/" 
    ZOOM_DAYS = 150 

    print(f"正在从 '{DATA_PATH}' 加载数据...")
    csv_files = glob.glob(os.path.join(DATA_PATH, '*.csv'))
    
    if not csv_files:
        print(f"错误：在 '{DATA_PATH}' 文件夹里没有找到任何 .csv 文件。")
        sys.exit(1)
        
    print(f"找到了 {len(csv_files)} 个 CSV 文件。开始批量处理 (周线 + 日线)...")

    for csv_file_path in csv_files:
        asset_name = os.path.basename(csv_file_path).split('.')[0]
        print(f"  正在处理: {asset_name}")
        
        # 1. 使用我们健壮的 OHLCV 加载器
        full_df = load_single_asset_ohlcv(csv_file_path)
        
        if full_df is not None:
            # 2. 调用我们新的“保存”函数
            save_candlestick_plot_v4(
                full_df, 
                asset_name, 
                base_save_dir=SAVE_DIR_BASE, 
                zoom_days=ZOOM_DAYS
            )
        else:
            print(f"  [跳过] {asset_name} 因加载失败而被跳过。")
            
    print("--- 优化版 K 线图 (V4) 批量生成和保存完毕 ---")