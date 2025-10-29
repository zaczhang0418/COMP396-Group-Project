# 导入我们需要的工具包
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
import sys

# --- 1. 定义文件夹路径 (使用相对路径，保持跨平台兼容性) ---
DATA_DIR = 'DATA/PART1'
OUTPUT_DIR = 'eda/charts/volatility' # 这是 W5 概要要求保存的地方 

# --- 2. 准备工作 ---
os.makedirs(OUTPUT_DIR, exist_ok=True)
csv_files = glob.glob(os.path.join(DATA_DIR, '*.csv'))

if not csv_files:
    print(f"错误：在 '{DATA_DIR}' 文件夹里没有找到任何 .csv 文件。")
    sys.exit()

print(f"找到了 {len(csv_files)} 个 CSV 文件。开始处理波动率聚集分析...")

# --- 3. 循环处理每一个文件 ---
for csv_file_path in csv_files:
    file_name = os.path.basename(csv_file_path)
    
    try:
        print(f"--- 正在处理: {file_name} ---")

        # 1. [!! 关键修正 !!] 使用 K 线图脚本中标准的数据加载和清洗流程
        data = pd.read_csv(
            csv_file_path,
            parse_dates=['Index'],
            index_col='Index'
        )
        data.columns = data.columns.str.strip().str.strip('"')
        data.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)

        if 'close' not in data.columns:
            print(f"   [跳过] '{file_name}' 缺少 'close' 列。")
            continue

        # 2. 计算对数收益率
        log_returns = np.log(data['close'] / data['close'].shift(1))
        log_returns = log_returns.dropna()

        # 3. 计算 20 天滚动标准差 (波动率) [cite: 39]
        rolling_vol = log_returns.rolling(window=20).std()

        if rolling_vol.empty:
            print(f"   [跳过] '{file_name}' 计算波动率后为空。")
            continue

        # --- 4. 绘图与保存 ---
        plt.figure(figsize=(12, 6))
        rolling_vol.plot(title=f'{file_name} - 20-Day Rolling Volatility (Clustering)')
        plt.xlabel('Date')
        plt.ylabel('Volatility (Rolling StDev)')
        
        # 5. [!! 关键修正 !!] 保存图表，而不是 plt.show()
        output_filename = file_name.replace('.csv', '_volatility.png')
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        plt.savefig(output_path)
        print(f"   波动率图表已保存到: {output_path}")
        plt.close()

    except Exception as e:
        print(f"   [失败] 处理 '{file_name}' 时出错: {e}")

print("--- 所有波动率图表处理完毕！ ---")