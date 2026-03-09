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
def load_and_merge_data(data_directory):
    # 1. 查找所有 CSV 文件
    csv_files_path = os.path.join(data_directory, "*.csv")
    files = glob.glob(csv_files_path)
    if not files:
        print(f"警告：在 '{data_directory}' 中没有找到 .csv 文件。")
        return pd.DataFrame() 
    
    dfs = {}
    for f in files:
        asset_name = os.path.basename(f).split('.')[0]
        try:
            # [关键修复] 读取时不指定 parse_dates，避免因找不到列名报错
            data = pd.read_csv(f, thousands=',')
            
            # 清理列名（去除空格或引号）
            data.columns = data.columns.str.strip().str.strip('"')
            
            # [关键修复] 动态处理日期列：支持 'Index' 或 'Date'
            if 'Index' in data.columns:
                data.rename(columns={'Index': 'Date'}, inplace=True)
            
            if 'Date' in data.columns:
                data['Date'] = pd.to_datetime(data['Date'])
            else:
                # 如果两个都没有，跳过该文件
                print(f"  跳过 {asset_name}: 缺少 'Date' 或 'Index' 列")
                continue

            # 提取 Close 列
            if 'Close' in data.columns:
                # 确保是数值类型
                data['Close'] = pd.to_numeric(data['Close'], errors='coerce')
                data.dropna(subset=['Date', 'Close'], inplace=True) 
                
                # 重命名 Close 为资产名称，方便后续合并
                df = data[['Date', 'Close']].rename(columns={'Close': asset_name})
                dfs[asset_name] = df
            else:
                print(f"  跳过 {asset_name}: 缺少 'Close' 列")
                continue
                
        except Exception as e:
            print(f" 警告: 加载 {f} 出错: {e}")

    if not dfs:
        print("❌ 错误: 未能从任何 CSV 文件中加载有效数据。")
        return pd.DataFrame()

    # 2. 合并所有数据
    df_list = list(dfs.values())
    merged = df_list[0]
    for df_to_join in df_list[1:]:
        # 使用 outer join 确保保留所有日期，避免因某个资产缺失某天数据导致整行被删
        merged = merged.merge(df_to_join, on='Date', how='outer')
    
    # 3. 设置索引并排序
    merged.set_index('Date', inplace=True)
    merged.sort_index(inplace=True) 
    
    # 4. 填充缺失值 (Forward Fill) - 这是一个可选但推荐的操作，防止计算指标时因 NaN 报错
    merged.ffill(inplace=True) 
    
    return merged



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
        # 1. 加载单个资产的 OHLCV 数据
        try:
            data = pd.read_csv(csv_file_path, thousands=',')
            data.columns = data.columns.str.strip().str.strip('"')
            
            if 'Index' in data.columns:
                data.rename(columns={'Index': 'Date'}, inplace=True)
            
            if 'Date' in data.columns:
                data['Date'] = pd.to_datetime(data['Date'])
                data.set_index('Date', inplace=True)
            
            # 转换列名为小写以匹配计算函数
            data.columns = data.columns.str.lower()
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
            
            data.dropna(inplace=True)
            full_df = data if not data.empty else None
        except Exception as e:
            print(f"  警告: 加载 {csv_file_path} 出错: {e}")
            full_df = None
        # --- [升级结束] ---
        
        if full_df is not None:
            # 2. 构造保存路径
            save_file_path = os.path.join(SAVE_DIR, f"{asset_name}_volatility_v2_atr.png")
            
            # 3. 调用我们新的“保存”函数
            save_volatility_analysis_v2(full_df, asset_name, save_path=save_file_path)
        else:
            print(f"  [跳过] {asset_name} 因加载失败而被跳过。")
            
    print("--- 波动率图表批量生成和保存完毕 ---")