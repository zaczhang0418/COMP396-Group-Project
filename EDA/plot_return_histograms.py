# 导入我们需要的工具包
import pandas as pd
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import sys  # 导入 sys 库
from scipy.stats import norm # 导入 norm 来画正态分布曲线

# --- 1. 定义文件夹路径 (使用相对路径，保持跨平台兼容性) ---
DATA_DIR = 'DATA/PART1'
OUTPUT_DIR = 'eda/charts/histograms' # 这是任务书上要求保存的地方

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

print(f"找到了 {len(csv_files)} 个 CSV 文件。开始处理收益率直方图...")

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

        # 2. 计算对数收益率 (Log Returns)
        # (使用我们清洗后的 'close' 列)
        log_returns = np.log(data['close'] / data['close'].shift(1))

        # 去掉第一个 NaN 值
        log_returns = log_returns.dropna()

        if log_returns.empty:
            print(f"   [跳过] '{file_name}' 计算收益率后为空。")
            continue

        # 3. 计算偏度 (Skewness) 和 峰度 (Kurtosis)
        # 峰度 (Kurtosis) > 3 (或 Pandas 计算的超额峰度 > 0) 意味着 "尖峰厚尾"
        skewness = log_returns.skew()
        kurtosis = log_returns.kurtosis() # Pandas 默认计算的是 "超额峰度" (Excess Kurtosis)
        
        print(f"   偏度 (Skewness): {skewness:.4f}")
        print(f"   超额峰度 (Excess Kurtosis): {kurtosis:.4f}")

        # --- 4. 绘图 (Charts) ---
        plt.figure(figsize=(10, 6)) # 创建一个图表

        # 画直方图，bins=100 (分成 100 个柱子), density=True (标准化，使面积为1)
        log_returns.hist(bins=100, density=True, label='Log Returns Histogram', alpha=0.7)

        # 任务书要求：叠加一个标准正态分布
        mu = log_returns.mean()
        std = log_returns.std()
        x = np.linspace(mu - 4*std, mu + 4*std, 100) # 用 4 个标准差覆盖更广范围
        y = norm.pdf(x, mu, std) # 使用 scipy.stats.norm 更标准
        plt.plot(x, y, linewidth=2, color='r', label='Normal Distribution')

        # 添加标题和标签
        # (注意: Pandas 的 kurtosis() 是超额峰度, 3 + kurtosis 才是 W5 概要里的峰度)
        title_kurtosis = 3 + kurtosis 
        plt.title(f'Log Returns Distribution - {file_name}\nSkew: {skewness:.4f}, Kurtosis (W5标准): {title_kurtosis:.4f}')
        plt.xlabel('Log Returns')
        plt.ylabel('Density')
        plt.legend()

        # 5. 保存图表
        output_filename = file_name.replace('.csv', '_histogram.png')
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        plt.savefig(output_path)
        print(f"   图表已保存到: {output_path}")
        plt.close() # 关闭图表

    except Exception as e:
        print(f"   [失败] 处理 '{file_name}' 时出错: {e}")

print("--- 所有文件处理完毕！ ---")