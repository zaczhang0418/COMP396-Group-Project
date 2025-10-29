# 导入我们需要的工具包
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
import sys
import seaborn as sns # 导入 Task 4 需要的库 

# --- 1. 定义文件夹路径 (使用相对路径，保持跨平台兼容性) ---
DATA_DIR = 'DATA/PART1'
# W5 概要要求保存为一张图表 
OUTPUT_FILE = 'eda/charts/correlation_heatmap.png' 

# 确保 charts 文件夹存在
os.makedirs('eda/charts', exist_ok=True)

# --- 2. 准备工作 ---
csv_files = glob.glob(os.path.join(DATA_DIR, '*.csv'))

if not csv_files:
    print(f"错误：在 '{DATA_DIR}' 文件夹里没有找到任何 .csv 文件。")
    sys.exit()

print(f"找到了 {len(csv_files)} 个 CSV 文件。开始计算跨资产相关性...")

# 创建一个空的 DataFrame 用于存储所有资产的对数收益率
all_returns = pd.DataFrame() 

# --- 3. 循环处理每一个文件 ---
for csv_file_path in csv_files:
    file_name = os.path.basename(csv_file_path)
    
    try:
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

        # 3. 将 Log_Returns 列添加到 all_returns DataFrame 中
        # (使用文件名作为列名，e.g., '01', '02')
        column_name = file_name.replace('.csv', '')
        all_returns[column_name] = log_returns

    except Exception as e:
        print(f"   [失败] 处理 '{file_name}' 时出错: {e}")

# --- 4. 计算并绘制相关性矩阵 ---

# 清理 NaN 值 (第一行收益率是 NaN)
returns_clean = all_returns.dropna()

if returns_clean.empty:
    print("错误：计算所有收益率后，DataFrame 为空。无法生成热力图。")
    sys.exit()

# 计算相关性矩阵 [cite: 53]
correlation_matrix = returns_clean.corr()

print("--- 资产相关性矩阵 (Correlation Matrix) ---")
print(correlation_matrix)

# 绘制热力图
plt.figure(figsize=(10, 8))
sns.heatmap(
    correlation_matrix, 
    annot=True,          # 在图上显示数值
    cmap='coolwarm',     # 使用冷暖色调
    fmt=".2f",           # 格式化数值为两位小数
    linewidths=.5,
    linecolor='black'
)
plt.title('Cross-Asset Log Returns Correlation Heatmap')

# 5. [!! 关键修正 !!] 保存图表，而不是 plt.show()
plt.savefig(OUTPUT_FILE)
print(f"--- 相关性热力图已保存到: {OUTPUT_FILE} ---")
plt.close()