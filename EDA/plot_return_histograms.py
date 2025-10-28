# 导入我们需要的工具包
import pandas as pd
import os
import glob
import numpy as np
import matplotlib.pyplot as plt

# --- 1. 定义文件夹路径 ---
# (我们用“相对路径”，这在你和 Zac 的电脑上都能运行！)
DATA_DIR = 'DATA/PART1'
OUTPUT_DIR = 'eda/charts/histograms' # 这是任务书上要求保存的地方

# --- 2. 准备工作 ---
# 确保保存结果的文件夹存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 找到所有要处理的 CSV 数据文件
# 我们使用 glob 来查找所有以 .csv 结尾的文件
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
    # 任务书要求：log(close / close.shift(1))
    log_returns = np.log(data['Close'] / data['Close'].shift(1))
    
    # 去掉第一个 NaN 值 (因为第一天没有前一天的收盘价)
    log_returns = log_returns.dropna()

    # 2. 计算偏度 (Skewness) 和 峰度 (Kurtosis)
    # 这是任务书里要求分析的
    skewness = log_returns.skew()
    kurtosis = log_returns.kurtosis() # Pandas 默认计算的就是“超额峰度” (Leptokurtic)

    print(f"偏度 (Skewness): {skewness:.4f}")
    print(f"峰度 (Kurtosis): {kurtosis:.4f}")

    # --- 4. 绘图 (Charts) ---
    # 任务书要求：生成 10 个直方图 (Histogram)
    
    plt.figure(figsize=(10, 6)) # 创建一个图表
    
    # 画直方图，bins=100 (分成 100 个柱子)
    log_returns.hist(bins=100, density=True, label='Log Returns Histogram')
    
    # 任务书要求：叠加一个标准正态分布
    # (我们用 log_returns 的均值和标准差来创建这个正态分布)
    mu = log_returns.mean()
    std = log_returns.std()
    x = np.linspace(mu - 3*std, mu + 3*std, 100)
    plt.plot(x, 1/(std * np.sqrt(2 * np.pi)) * np.exp( - (x - mu)**2 / (2 * std**2) ),
             linewidth=2, color='r', label='Normal Distribution')

    
    # 添加标题和标签
    plt.title(f'Log Returns Distribution - {file_name}\nSkew: {skewness:.4f}, Kurtosis: {kurtosis:.4f}')
    plt.xlabel('Log Returns')
    plt.ylabel('Density')
    plt.legend()

    # 5. 保存图表
    # 把文件名里的 .csv 换成 .png
    output_filename = file_name.replace('.csv', '_histogram.png')
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    plt.savefig(output_path)
    print(f"图表已保存到: {output_path}")
    plt.close() # 关闭图表，防止在内存中堆积

print("--- 所有文件处理完毕！ ---")