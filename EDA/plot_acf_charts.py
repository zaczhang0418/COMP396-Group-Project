# 导入我们需要的工具包
import pandas as pd
import os
import glob
import numpy as np
import matplotlib.pyplot as plt

# 导入 "任务 2" 特别需要的工具包
# (我们稍后需要安装它)
from statsmodels.graphics.tsaplots import plot_acf

# --- 1. 定义文件夹路径 ---
DATA_DIR = 'DATA/PART1'
OUTPUT_DIR = 'eda/charts/acf' # 这是任务书上要求保存的地方

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

print(f"找到了 {len(csv_files)} 个 CSV 文件。开始处理...")

# --- 3. 循环处理每一个文件 ---
# (这是你任务书里最核心的部分)

for csv_file_path in csv_files:
    # 从完整路径里提取出文件名 (比如 '01.csv')
    file_name = os.path.basename(csv_file_path)
    print(f"--- 正在处理: {file_name} ---")

    # 读取 CSV 数据
    data = pd.read_csv(csv_file_path)

    # 1. 计算对数收益率 (Log Returns)
    # 我们从任务 1 得知，正确的列名是 'Close' (大写)
    log_returns = np.log(data['Close'] / data['Close'].shift(1))
    
    # 去掉第一个 NaN 值
    log_returns = log_returns.dropna()

    # --- 4. 绘图 (ACF Charts) ---
    # 任务书要求：生成 10 个 ACF 图
    
    fig, ax = plt.subplots(figsize=(10, 6)) # 创建一个图表
    
    # 使用 statsmodels 来画 ACF 图
    # 我们画 20 期的滞后 (lags=20)，这样你可以清楚地看到 Lag 1
    plot_acf(log_returns, lags=20, ax=ax, title=f'Autocorrelation (ACF) - {file_name}')
    
    # 5. 保存图表
    # 把文件名里的 .csv 换成 .png
    output_filename = file_name.replace('.csv', '_acf.png')
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    plt.savefig(output_path)
    print(f"ACF 图表已保存到: {output_path}")
    plt.close(fig) # 关闭图表

print("--- 所有文件处理完毕！ ---")