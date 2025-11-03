import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy import stats

# 1. 导入你自己的加载器
try:
    import eda_data_loader
except ImportError:
    print("Error: 'eda_data_loader.py' not found.")
    print("Please ensure this script is in the same 'EDA' folder as your loader.")
    exit()

# --- 配置 ---
CHARTS_BASE_DIR = "charts"
QUANTILE_SAVE_DIR = os.path.join(CHARTS_BASE_DIR, "quantile_analysis") # 新子文件夹
DATA_DIR_PATH = "../DATA/PART1/" 
N_QUANTILES = 5 # 将资产分为 5 组
# ---

def perform_quantile_analysis(merged_prices_df, factor_lookback_days, forward_return_days, factor_name):
    """
    对合并的价格数据执行横截面分位数分析。
    
    :param merged_prices_df: 你的 loader 加载的合并价格 DataFrame
    :param factor_lookback_days: 计算因子（如收益率）的回看期
    :param forward_return_days: 计算未来收益的持有期
    :param factor_name: 用于图表标题的因子名称 (如 'STR_21D' 或 'MOM_126D')
    """
    print(f"\n--- 正在运行分位数分析: {factor_name} ---")
    
    # 1. 计算因子值：过去 N 天的收益率
    # (df / df.shift(N)) - 1
    factor_values = merged_prices_df.pct_change(factor_lookback_days)
    
    # 2. 计算未来 N 天的收益率
    forward_returns = merged_prices_df.pct_change(forward_return_days).shift(-forward_return_days)
    
    # 3. 堆叠数据 (Stacking)：将数据从“宽”格式转为“长”格式
    # 这使得按日期分组变得容易
    factor_long = factor_values.stack().rename('factor')
    fwd_ret_long = forward_returns.stack().rename('fwd_return')
    
    # 合并为一个 DataFrame
    df_long = pd.concat([factor_long, fwd_ret_long], axis=1)
    df_long.index.names = ['Date', 'Asset'] # 命名索引
    df_long.dropna(inplace=True)
    
    if df_long.empty:
        print(f"  ❌ 错误: 在 {factor_name} 计算中没有剩余数据。")
        return

    # 4. 按日期分组，计算分位数
    # groupby(level=0) 按第一个索引 (Date) 分组
    # pd.qcut 将该日期的所有因子值分为 N 组
    df_long['Quantile'] = df_long.groupby(level=0)['factor'].transform(
        lambda x: pd.qcut(x, N_QUANTILES, labels=False, duplicates='drop') + 1
    )
    df_long.dropna(inplace=True) # 丢弃无法分位数的日期

    # 5. 分析结果
    
    # A. 计算每个分位数的平均未来收益
    quantile_returns = df_long.groupby('Quantile')['fwd_return'].mean()
    print(f"\n{factor_name} - 每个分位数的平均 {forward_return_days}日 收益:")
    print(quantile_returns)
    
    # B. 计算多空组合 (Long-Short Portfolio)
    # 动量 (MOM): Q5 (赢家) - Q1 (输家)
    # 均值回归 (STR): Q1 (输家) - Q5 (赢家)
    
    # 按日期和分位数计算平均收益
    daily_quantile_returns = df_long.groupby(['Date', 'Quantile'])['fwd_return'].mean().unstack()
    
    # 动量组合
    mom_ls_portfolio = daily_quantile_returns[N_QUANTILES] - daily_quantile_returns[1]
    # 均值回归/反转组合
    rev_ls_portfolio = daily_quantile_returns[1] - daily_quantile_returns[N_QUANTILES]

    # 6. 可视化
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(15, 12))
    fig.suptitle(f'Cross-Sectional Analysis: {factor_name} ({N_QUANTILES} Quantiles)', y=1.02, fontsize=16)

    # 子图 1: 分位数条形图
    quantile_returns.plot(kind='bar', ax=ax1, 
                          color=plt.cm.coolwarm(np.linspace(0, 1, N_QUANTILES)))
    ax1.set_title(f'Avg. Forward {forward_return_days}-Day Return per Quantile')
    ax1.set_xlabel('Quantile (1 = Lowest Factor, 5 = Highest Factor)')
    ax1.set_ylabel('Avg. Forward Return')
    ax1.axhline(0, color='black', linestyle='--')

    # 子图 2: 多空组合累计收益
    # 假设持有期与重叠期相同，进行简单累计 (非复合)
    mom_ls_portfolio.cumsum().plot(ax=ax2, label=f'Long-Short (Momentum, Q{N_QUANTILES}-Q1)', color='blue')
    rev_ls_portfolio.cumsum().plot(ax=ax2, label=f'Long-Short (Reversal, Q1-Q{N_QUANTILES})', color='green')
    ax2.set_title('Cumulative Return of Long-Short Portfolios')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Cumulative Return (Non-Compounded)')
    ax2.legend()
    ax2.axhline(0, color='black', linestyle='--')

    plt.tight_layout(rect=[0, 0.03, 1, 0.98])

    # 7. 保存图表
    output_filename = f"quantile_analysis_{factor_name}.png"
    output_path = os.path.join(QUANTILE_SAVE_DIR, output_filename)
    plt.savefig(output_path)
    print(f"  Chart saved to {output_path}")
    plt.close(fig)

def main():
    """
    主执行函数：加载数据，运行两种因子分析。
    """
    print("--- 正在运行分位数 (Quantile) 分析脚本 ---")
    
    os.makedirs(QUANTILE_SAVE_DIR, exist_ok=True)
    print(f"Charts will be saved to: {QUANTILE_SAVE_DIR}")

    # 1. 加载数据 (使用你原版的 loader)
    print(f"Calling eda_data_loader.load_and_merge_data(data_directory='{DATA_DIR_PATH}')...")
    try:
        # 注意：这里我们调用 load_and_merge_data
        merged_prices_df = eda_data_loader.load_and_merge_data(DATA_DIR_PATH)
    except Exception as e:
        print(f"Error calling eda_data_loader: {e}")
        return

    if merged_prices_df.empty:
        print("Error: Your loader returned an empty DataFrame.")
        return

    print(f"✅ Loader success. Loaded merged DataFrame with {len(merged_prices_df.columns)} assets.")
    
    # 2. 运行分析 1: 短期反转 (Short-Term Reversal, 1个月)
    # (这与你的 RSI 推论相关)
    perform_quantile_analysis(
        merged_prices_df, 
        factor_lookback_days=21, # ~1 个月
        forward_return_days=21,  # 持有 1 个月
        factor_name="STR_21D"    # 因子名
    )
    
    # 3. 运行分析 2: 动量 (Momentum, 6个月)
    perform_quantile_analysis(
        merged_prices_df, 
        factor_lookback_days=126, # ~6 个月
        forward_return_days=21,   # 持有 1 个月
        factor_name="MOM_126D"   # 因子名
    )

    print("--- 分位数 (Quantile) 分析全部完成 ---")

if __name__ == "__main__":
    main()