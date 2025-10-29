import pandas as pd
import mplfinance as mpf
import sys
import os
import glob  # 导入 glob 库来查找文件

# --- 1. 定义你的文件夹路径 ---
# [修复 1] 定义数据来源文件夹 (DATA\PART1)
data_dir = r'C:\Users\ALIENWARE\Desktop\COMP396\COMP396-Group-Project\DATA\PART1'

# [修复 2] 定义图表输出文件夹 (将在 eda/ 文件夹下创建一个 'charts' 子文件夹)
# 我们使用相对路径，这更规范
output_dir = 'eda/charts/candlesticks'  # <-- 已修改：添加了 'candlesticks' 子文件夹

# --- 2. 准备工作 ---
# 创建输出文件夹 (如果它还不存在的话)
# os.makedirs 会自动创建所有必需的中间文件夹 (eda, charts, candlesticks)
os.makedirs(output_dir, exist_ok=True)

# 查找所有要处理的 CSV 文件
# os.path.join 会智能地处理路径分隔符 ( \ 或 / )
# *.csv 是一个通配符，意思是 "匹配所有以 .csv 结尾的文件"
csv_files = glob.glob(os.path.join(data_dir, '*.csv'))

if not csv_files:
    print(f"错误: 在 '{data_dir}' 中没有找到任何 .csv 文件。")
    print("请检查 'data_dir' 变量的路径是否正确。")
    sys.exit(1)

print(f"找到了 {len(csv_files)} 个 CSV 文件。开始批量处理...")
print(f"图表将保存到: {os.path.abspath(output_dir)}")
print("-" * 30)

# --- 3. 循环处理所有文件 ---
for csv_file_path in csv_files:
    # os.path.basename 会从完整路径中提取文件名 (e.g., "01.csv")
    file_name = os.path.basename(csv_file_path)

    try:
        print(f"Processing: {file_name} ...")

        # 1. 加载数据 (使用 'Index' 列作为日期索引)
        df = pd.read_csv(
            csv_file_path,
            parse_dates=['Index'],
            index_col='Index'
        )

        # 2. 准备数据 (清理并重命名列)
        df.columns = df.columns.str.strip().str.strip('"')
        df.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)

        # 检查必要的列是否存在
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            print(f"   [跳过] '{file_name}' 缺少必要的列 (Open, High, Low, Close)。")
            continue  # 跳过这个文件，继续下一个

        # 3. 定义输出文件路径 (e.g., "eda/charts/candlesticks/01.png")
        output_file_path = os.path.join(
            output_dir,
            file_name.replace('.csv', '.png')  # 将 .csv 后缀替换为 .png
        )

        # 4. 绘制 K 线图并保存 (!! 核心变更 !!)
        mpf.plot(
            df,
            type='candle',
            style='yahoo',
            title=f'Candlestick Chart - {file_name}',  # 英文标题
            ylabel='Price ($)',
            volume=True,
            ylabel_lower='Volume',
            figratio=(16, 9),
            savefig=output_file_path  # <-- 告诉 mplfinance 保存文件，而不是显示
        )

        print(f"   [成功] 已保存图表到: {output_file_path}")

    except Exception as e:
        # 捕获所有可能的错误 (e.g., 空文件, 格式错误)
        print(f"   [失败] 处理 '{file_name}' 时出错: {e}")

print("-" * 30)
print(f"批量处理完成。所有图表均已保存在 '{output_dir}' 文件夹中。")