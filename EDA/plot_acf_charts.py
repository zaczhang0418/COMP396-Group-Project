# 导入我们需要的工具包
import pandas as pd
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import sys  # 导入 sys 库
# 导入 "任务 2" 特别需要的工具包
from statsmodels.graphics.tsaplots import plot_acf

# --- 1. 定义文件夹路径 (使用相对路径，保持跨平台兼容性) ---
# 假设我们总是在项目根目录 (COMP396-Group-Project) 运行
DATA_DIR = 'DATA/PART1'
OUTPUT_DIR = 'eda/charts/acf' # 这是任务书上要求保存的地方 [cite: 26]

# --- 2. 准备工作 ---
# 确保保存结果的文件夹存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 找到所有要处理的 CSV 数据文件
csv_files = glob.glob(os.path.join(DATA_DIR, '*.csv'))

# 检查一下是否找到了文件
if not csv_files:
    print(f"错误：在 '{DATA_DIR}' 文件夹里没有找到任何 .csv 文件。")
    print("请检查你的路径是否正确。")
    sys.exit() # 如果没找到文件，就退出程序

print(f"找到了 {len(csv_files)} 个 CSV 文件。开始处理 ACF 分析...")

# --- 3. 循环处理每一个文件 ---
for csv_file_path in csv_files:
    # 从完整路径里提取出文件名 (比如 '01.csv')
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
            
        # 2. 计算对数收益率 (Log Returns) [cite: 9, 23]
        # (使用我们清洗后的 'close' 列)
        log_returns = np.log(data['close'] / data['close'].shift(1))

        # 去掉第一个 NaN 值
        log_returns = log_returns.dropna()

        if log_returns.empty:
            print(f"   [跳过] '{file_name}' 计算收益率后为空。")
            continue

        # --- 4. 绘图 (ACF Charts) --- [cite: 25]
        fig, ax = plt.subplots(figsize=(10, 6)) # 创建一个图表

        # 使用 statsmodels 来画 ACF 图
        # 我们画 20 期的滞后 (lags=20)，这样你可以清楚地看到 Lag 1
        plot_acf(log_returns, lags=20, ax=ax, title=f'Autocorrelation (ACF) - {file_name}')

        # 5. 保存图表
        # 把文件名里的 .csv 换成 .png
        output_filename = file_name.replace('.csv', '_acf.png')
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        plt.savefig(output_path)
        print(f"   ACF 图表已保存到: {output_path}")
        plt.close(fig) # 关闭图表

    except Exception as e:
        print(f"   [失败] 处理 '{file_name}' 时出错: {e}")

print("--- 所有文件处理完毕！ ---")