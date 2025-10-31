import pandas as pd
import mplfinance as mpf
import sys
import os
import glob 

# -----------------------------------------------------------------
# (这个脚本是独立的，它不依赖 eda_data_loader.py)
# -----------------------------------------------------------------

# --- 1. 独立的数据加载器 (Helper Function) ---
# 这个加载器是 K 线图专用的，因为它保留了 OHLCV

def load_single_asset_ohlcv(csv_file_path):
    """
    加载并清洗*单个* CSV 文件，返回可用于 K 线图的 OHLCV DataFrame。
    """
    try:
        data = pd.read_csv(
            csv_file_path,
            parse_dates=['Index'],
            index_col='Index'
        )
        
        # 你的标准清洗流程 (非常好)
        data.columns = data.columns.str.strip().str.strip('"')
        data.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)

        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in data.columns for col in required_cols):
            print(f"  [跳过] {os.path.basename(csv_file_path)} 缺少必要的 OHLC 列。")
            return None # 返回 None
            
        return data

    except Exception as e:
        print(f"  [失败] 加载 {os.path.basename(csv_file_path)} 时出错: {e}")
        return None

# --- 2. API 函数 (给 Notebook 调用) ---

def plot_candlestick(ohlcv_df, asset_name):
    """
    (供 Notebook 调用)
    绘制 K 线图并直接 'show()' (在 Notebook 中会内联显示)。
    """
    if ohlcv_df is None or ohlcv_df.empty:
        print(f" 警告: {asset_name} 的 OHLCV 数据为空，跳过绘图。")
        return

    print(f"--- 正在绘制 K 线图: {asset_name} ---")
    
    mpf.plot(
        ohlcv_df,
        type='candle',
        style='yahoo',
        title=f'Candlestick Chart - {asset_name}',
        ylabel='Price ($)',
        volume=True,
        ylabel_lower='Volume',
        figratio=(16, 9)
        # 注意：没有 'savefig' 参数，它会自动 'show()'
    )

def save_candlestick_plot(ohlcv_df, asset_name, save_path=""):
    """
    (供本地运行调用)
    绘制图表并 'savefig()' 到指定路径。
    """
    if ohlcv_df is None or ohlcv_df.empty:
        print(f" 警告: {asset_name} 数据为空，跳过保存。")
        return

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    mpf.plot(
        ohlcv_df,
        type='candle',
        style='yahoo',
        title=f'Candlestick Chart - {asset_name}',
        ylabel='Price ($)',
        volume=True,
        ylabel_lower='Volume',
        figratio=(16, 9),
        savefig=save_path # <-- 核心区别
    )
    print(f"  图表已保存到: {save_path}")
    # mplfinance 在保存时会自动 'close()' 图表


# --- 3. 本地运行块 (Standalone Runner) ---
# (这基本就是你原来的脚本，只是现在它调用了上面的函数)
if __name__ == "__main__":
    
    print("--- 正在以独立模式运行 (Candlestick Plotter) ---")
    
    # [修复] 总是使用相对路径，而不是绝对路径
    DATA_PATH = "./DATA/PART1/" 
    SAVE_DIR = "./EDA/charts/candlesticks/" # 你的原始输出路径
    
    print(f"正在从 '{DATA_PATH}' 加载数据...")
    csv_files = glob.glob(os.path.join(DATA_PATH, '*.csv'))

    if not csv_files:
        print(f"错误：在 '{DATA_PATH}' 文件夹里没有找到任何 .csv 文件。")
        sys.exit(1)
    
    print(f"找到了 {len(csv_files)} 个 CSV 文件。开始批量处理...")
    
    for csv_file_path in csv_files:
        file_name = os.path.basename(csv_file_path)
        asset_name = file_name.replace('.csv', '')
        
        print(f"--- 正在处理: {file_name} ---")
        
        # 1. 加载单个文件
        ohlcv_data = load_single_asset_ohlcv(csv_file_path)
        
        if ohlcv_data is not None:
            # 2. 定义保存路径
            save_file_path = os.path.join(SAVE_DIR, f"{asset_name}_candlestick.png")
            
            # 3. 调用“保存”函数
            save_candlestick_plot(ohlcv_data, asset_name, save_path=save_file_path)
            
    print("--- 本地运行完毕 ---")