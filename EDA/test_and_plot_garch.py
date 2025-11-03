import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from arch import arch_model # GARCH 库
from arch.unitroot import ADF # (可选) 检查平稳性

# 1. 导入你自己的加载器
try:
    import eda_data_loader
except ImportError:
    print("Error: 'eda_data_loader.py' not found.")
    print("Please ensure this script is in the same 'EDA' folder as your loader.")
    exit()

# --- 配置 ---
CHARTS_BASE_DIR = "charts"
GARCH_SAVE_DIR = os.path.join(CHARTS_BASE_DIR, "garch") # GARCH 图表的新子文件夹
DATA_DIR_PATH = "../DATA/PART1/" # 我们的脚本在 EDA，数据在上一级
# ---

def analyze_and_plot_garch(price_series, asset_name, save_dir):
    """
    对 *单个资产* 的价格序列进行 GARCH 分析并绘图。
    """
    print(f"  Analyzing GARCH for {asset_name}...")

    # 1. 准备数据：GARCH 模型使用收益率，而不是价格
    # 我们使用 100 * 对数收益率，这是金融计量的标准做法，有助于模型收敛
    returns = 100 * np.log(price_series / price_series.shift(1)).dropna()

    if returns.empty:
        print(f"  Skipping {asset_name}: Not enough data to calculate returns.")
        return

    # 2. 拟合 GARCH(1,1) 模型
    # p=1, q=1 是最常见的 GARCH 模型
    # vol='Garch' 指定了 GARCH
    # dist='Studentst' 假设 t 分布，这比正态分布更能捕捉“厚尾”(推论 4)
    try:
        model = arch_model(returns, vol='Garch', p=1, q=1, dist='t')
        results = model.fit(update_freq=10, disp='off') # disp='off' 关闭拟合过程的冗长输出
    except Exception as e:
        print(f"  Error fitting GARCH for {asset_name}: {e}")
        return

    # 3. 打印模型摘要 (COMP396 报告的关键论据)
    print(f"\n--- GARCH(1,1) Summary for {asset_name} ---")
    print(results.summary())
    
    # 关键论据 1 (阶段一): ARCH-LM 检验
    # 'Prob(Q)' 和 'Prob(Q*)' 是 ARCH 效应的 P 值
    # 如果它们 < 0.05，你就证明了“推论 3：波动率是可预测的”
    
    # 关键论据 2 (阶段三): GARCH 参数
    # 'alpha[1]' 和 'beta[1]' 是 GARCH 参数
    # 如果它们的 P 值 'P>|z|' < 0.05 且总和接近 1，
    # 你就证明了“推论 9：波动率有长期记忆”，适合动态仓位

    # 4. 可视化
    fig = results.plot(annualize='D') # D for daily
    fig.set_size_inches(12, 8)
    fig.suptitle(f'GARCH(1,1) Model Diagnostics for {asset_name}', y=1.02)
    
    plt.tight_layout()

    # 5. 保存图表
    output_filename = f"garch_diagnostics_{asset_name}.png"
    output_path = os.path.join(save_dir, output_filename)
    
    plt.savefig(output_path)
    print(f"  Chart saved to {output_path}")
    plt.close(fig) # 关闭图表

def main():
    """
    主执行函数：加载数据，循环处理每个资产。
    """
    print("--- 正在运行 GARCH 分析脚本 ---")
    
    # 1. 确保目标保存目录存在
    os.makedirs(GARCH_SAVE_DIR, exist_ok=True)
    print(f"Charts & summaries will be saved to: {GARCH_SAVE_DIR}")

    # 2. 从你的加载器加载数据
    print(f"Calling eda_data_loader.load_and_merge_data(data_directory='{DATA_DIR_PATH}')...")
    try:
        merged_prices_df = eda_data_loader.load_and_merge_data(DATA_DIR_PATH)
    except Exception as e:
        print(f"Error calling eda_data_loader: {e}")
        return

    if merged_prices_df.empty:
        print("Error: Your loader returned an empty DataFrame. Check DATA_DIR_PATH.")
        return

    print(f"✅ Loader success. Loaded merged DataFrame with {len(merged_prices_df.columns)} assets.")

    # 3. 循环遍历 *合并后 DataFrame 的每一列*
    for asset_name in merged_prices_df.columns:
        price_series = merged_prices_df[asset_name].dropna()
        
        if isinstance(price_series, pd.Series) and not price_series.empty:
            analyze_and_plot_garch(price_series, 
                                   asset_name, 
                                   GARCH_SAVE_DIR)
        else:
            print(f"Skipping {asset_name}: No valid data.")
            
    print("--- GARCH 分析全部完成 ---")

if __name__ == "__main__":
    main()