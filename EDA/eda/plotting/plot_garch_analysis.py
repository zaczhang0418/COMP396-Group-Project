import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
import sys # 确保导入 sys

# --- [!! 关键依赖 !!] ---
# 这个脚本需要 'arch' 库。
# 你必须先在你的 comp396 环境中安装它：
# pip install arch
# -------------------------
try:
    from arch import arch_model
    from arch.unitroot import ADF # (可选) 检查平稳性
except ImportError:
    print("❌ 致命错误: 'arch' 库未安装。")
    print("   请在你的 VS Code 终端中运行:")
    print("   conda activate comp396")
    print("   pip install arch")
    sys.exit(1)


# --- 配置 ---
# [路径修复] 修正为 Zac 的本地路径
GARCH_SAVE_DIR = "./EDA/charts/garch/" 
DATA_DIR_PATH = "./DATA/PART1/" 
# ---

# -----------------------------------------------------------------
# (数据加载函数，使用我们昨天的“最终修复版-老师的逻辑”)
# (这是 'Close-Only' 版本，GARCH 只需要 Close 价格)
# -----------------------------------------------------------------
def load_and_merge_data(data_directory="./DATA/PART1/"):
    csv_files_path = os.path.join(data_directory, "*.csv")
    files = glob.glob(csv_files_path)
    if not files:
        print(f"警告：在 '{data_directory}' 中没有找到 .csv 文件。")
        return pd.DataFrame() 
    dfs = {}
    for f in files:
        asset_name = os.path.basename(f).split('.')[0]
        try:
            data = pd.read_csv(
                f, 
                parse_dates=['Index'], 
                index_col=None, # [我们的修复]
                thousands=','   # [我们的修复]
            )
            data.columns = data.columns.str.strip().str.strip('"')
            data.rename(columns={
                'Open': 'open', 'High': 'high', 'Low': 'low',
                'Close': 'close', 'Volume': 'volume',
                'Index': 'Date' # [我们的修复]
            }, inplace=True)
            
            if 'close' in data.columns:
                data['close'] = pd.to_numeric(data['close'], errors='coerce')
                data.dropna(subset=['close'], inplace=True) 
                df = data[['Date', 'close']].rename(columns={'close': asset_name})
                dfs[asset_name] = df
            
        except Exception as e:
            print(f" 警告: 加载 {f} 出错: {e}")

    if not dfs:
        print("❌ 错误: 未能从任何 CSV 文件中加载有效数据。")
        return pd.DataFrame()

    df_list = list(dfs.values())
    merged = df_list[0]
    for df_to_join in df_list[1:]:
        merged = merged.merge(df_to_join, on='Date', how='outer') # [我们的修复]
    
    merged.set_index('Date', inplace=True)
    merged.sort_index(inplace=True) 
    # [优化] 向前填充 NaN
    merged.ffill(inplace=True) 
    return merged
# -----------------------------------------------------------------
# (数据加载函数结束)
# -----------------------------------------------------------------
# --- [!! 新增的 API 函数 (给 Notebook 调用) !!] ---
def plot_garch_analysis(price_series, asset_name):
    """
    (新增的 API - 供 Notebook 调用)
    对 *单个资产* 进行 GARCH 分析并“显示”图表。
    """
    # [我们从 'analyze_and_plot_garch' 复制所有代码]
    print(f"  Analyzing GARCH for {asset_name}...")
    returns = 100 * np.log(price_series / price_series.shift(1)).dropna()
    if returns.empty:
        print(f"  Skipping {asset_name}: Not enough data to calculate returns.")
        return

    try:
        model = arch_model(returns, vol='Garch', p=1, q=1, dist='t')
        results = model.fit(update_freq=10, disp='off') 
    except Exception as e:
        print(f"  ❌ 错误: 拟合 GARCH 失败 {asset_name}: {e}")
        return

    print(f"\n--- GARCH(1,1) Summary for {asset_name} ---")
    print(results.summary())
    alpha = results.params['alpha[1]']
    beta = results.params['beta[1]']
    persistence = alpha + beta
    print(f"  GARCH 波动率持续性 (Alpha + Beta): {persistence:.4f}")
    if persistence > 0.95:
        print("  ✅ 论据发现: 波动率高度持续 (> 0.95)，适合动态仓位管理。")
    print("--------------------------------------------------")

    fig = results.plot(annualize='D') 
    fig.set_size_inches(12, 8)
    fig.suptitle(f'GARCH(1,1) Model Diagnostics for {asset_name}', y=1.02)
    plt.tight_layout()

    # --- [!! 核心区别: "显示" !!] ---
    plt.show()

# --- (队友的核心分析函数 - 100% 保留) ---
def analyze_and_plot_garch(price_series, asset_name, save_dir):
    """
    对 *单个资产* 的价格序列进行 GARCH 分析并绘图。
    """
    print(f"  Analyzing GARCH for {asset_name}...")

    # 1. 准备数据：GARCH 模型使用收益率，而不是价格
    # (使用 100 * 对数收益率，这是金融计量的标准做法)
    returns = 100 * np.log(price_series / price_series.shift(1)).dropna()

    if returns.empty:
        print(f"  Skipping {asset_name}: Not enough data to calculate returns.")
        return

    # 2. 拟合 GARCH(1,1) 模型 (来自队友)
    try:
        # 使用 GARCH(1,1) 和 学生t 分布
        model = arch_model(returns, vol='Garch', p=1, q=1, dist='t')
        results = model.fit(update_freq=10, disp='off') # disp='off' 关闭输出
    except Exception as e:
        print(f"  ❌ 错误: 拟合 GARCH 失败 {asset_name}: {e}")
        return

    # 3. 打印模型摘要 (COMP396 报告的关键论据)
    print(f"\n--- GARCH(1,1) Summary for {asset_name} ---")
    print(results.summary())
    
    # 打印关键论据 (Alpha 和 Beta)
    alpha = results.params['alpha[1]']
    beta = results.params['beta[1]']
    persistence = alpha + beta
    print(f"  GARCH 波动率持续性 (Alpha + Beta): {persistence:.4f}")
    if persistence > 0.95:
        print("  ✅ 论据发现: 波动率高度持续 (> 0.95)，适合动态仓位管理。")
    
    print("--------------------------------------------------")

    # 4. 可视化 (来自队友)
    fig = results.plot(annualize='D') # D for daily
    fig.set_size_inches(12, 8)
    fig.suptitle(f'GARCH(1,1) Model Diagnostics for {asset_name}', y=1.02)
    
    plt.tight_layout()

    # 5. 保存图表
    os.makedirs(save_dir, exist_ok=True) # [修复] 确保在函数内创建
    output_filename = f"garch_diagnostics_{asset_name}.png"
    output_path = os.path.join(save_dir, output_filename)
    
    plt.savefig(output_path)
    print(f"  Chart saved to {output_path}")
    plt.close(fig) # 关闭图表

def main():
    """
    主执行函数：加载数据，循环处理每个资产。
    """
    print("--- F 正在运行 GARCH 分析脚本 [V2 - Zac 已修复路径] ---")
    
    os.makedirs(GARCH_SAVE_DIR, exist_ok=True)
    print(f"Charts & summaries will be saved to: {GARCH_SAVE_DIR}")

    # --- [!! 关键修复 !!] ---
    # 1. 调用 *内部* 的加载器
    # 2. 使用我们 100% 正确的 DATA_DIR_PATH
    print(f"Calling internal load_and_merge_data(data_directory='{DATA_DIR_PATH}')...")
    
    merged_prices_df = load_and_merge_data(DATA_DIR_PATH)
    # --- [修复结束] ---

    if merged_prices_df.empty:
        print("Error: Loader returned an empty DataFrame.")
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