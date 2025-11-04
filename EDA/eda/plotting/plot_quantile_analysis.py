import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
import sys # 确保导入 sys
from scipy import stats

# --- 配置 ---
# [路径修复] 修正为 Zac 的本地路径
QUANTILE_SAVE_DIR = "./EDA/charts/quantile_analysis/" 
DATA_DIR_PATH = "./DATA/PART1/" 
N_QUANTILES = 5 # 将资产分为 5 组
# ---

# -----------------------------------------------------------------
# (数据加载函数，使用我们昨天的“最终修复版-老师的逻辑”)
# (这是 'Close-Only' 版本，Quantile 只需要 Close 价格)
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
    # [优化] 向前填充 NaN，以防止 pct_change 计算因假期错位而失败
    merged.ffill(inplace=True) 
    return merged
# -----------------------------------------------------------------
# (数据加载函数结束)
# -----------------------------------------------------------------
# --- [!! 新增的 API 函数 (给 Notebook 调用) !!] ---
def plot_quantile_analysis_v2(merged_prices_df, factor_lookback_days, forward_return_days, factor_name):
    """
    (新增的 V2 API - 供 Notebook 调用)
    执行分位数分析并“显示”图表。
    """
    # [我们从 'perform_quantile_analysis_v2' 复制所有代码]
    print(f"\n--- 正在运行分位数分析: {factor_name} ---")
    
    factor_values = merged_prices_df.pct_change(factor_lookback_days)
    forward_returns = merged_prices_df.pct_change(forward_return_days).shift(-forward_return_days)
    
    factor_long = factor_values.stack().rename('factor')
    fwd_ret_long = forward_returns.stack().rename('fwd_return')
    
    df_long = pd.concat([factor_long, fwd_ret_long], axis=1)
    df_long.index.names = ['Date', 'Asset'] 
    df_long.dropna(inplace=True)
    
    if df_long.empty:
        print(f"  ❌ 错误: 在 {factor_name} 计算中没有剩余数据。")
        return

    df_long['Quantile'] = df_long.groupby(level=0)['factor'].transform(
        lambda x: pd.qcut(x, N_QUANTILES, labels=False, duplicates='drop') + 1
    )
    df_long.dropna(inplace=True)
    quantile_returns = df_long.groupby('Quantile')['fwd_return'].mean()
    print(f"\n{factor_name} - 每个分位数的平均 {forward_return_days}日 收益:")
    print(quantile_returns.to_string(float_format="%.5f")) 
    
    daily_quantile_returns = df_long.groupby(['Date', 'Quantile'])['fwd_return'].mean().unstack()
    mom_ls_portfolio = daily_quantile_returns[N_QUANTILES] - daily_quantile_returns[1]
    rev_ls_portfolio = daily_quantile_returns[1] - daily_quantile_returns[N_QUANTILES]

    print("\n--- 核心论据 (统计显著性) ---")
    q1_returns = df_long[df_long['Quantile'] == 1]['fwd_return']
    qN_returns = df_long[df_long['Quantile'] == N_QUANTILES]['fwd_return']
    t_stat, p_value = stats.ttest_ind(qN_returns, q1_returns, equal_var=False)
    print(f"T-检验 (Q{N_QUANTILES} vs Q1): T-stat={t_stat:.3f}, P-value={p_value:.5f}")
    
    ann_factor = np.sqrt(252 / forward_return_days) 
    mom_sharpe = (mom_ls_portfolio.mean() / mom_ls_portfolio.std()) * ann_factor
    rev_sharpe = (rev_ls_portfolio.mean() / rev_ls_portfolio.std()) * ann_factor
    print(f"多空组合 (Momentum, Q{N_QUANTILES}-Q1) 年化夏普比率: {mom_sharpe:.4f}")
    print(f"多空组合 (Reversal, Q1-Q{N_QUANTILES}) 年化夏普比率: {rev_sharpe:.4f}")

    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(15, 12))
    fig.suptitle(f'Cross-Sectional Analysis: {factor_name} ({N_QUANTILES} Quantiles)', y=1.02, fontsize=16)

    quantile_returns.plot(kind='bar', ax=ax1, 
                          color=plt.cm.coolwarm(np.linspace(0, 1, N_QUANTILES)))
    ax1.set_title(f'Avg. Forward {forward_return_days}-Day Return per Quantile (p-value={p_value:.4f})')
    ax1.set_xlabel('Quantile (1 = Lowest Factor, 5 = Highest Factor)')
    ax1.set_ylabel('Avg. Forward Return')
    ax1.axhline(0, color='black', linestyle='--')

    mom_ls_portfolio.cumsum().plot(ax=ax2, label=f'Momentum (Q{N_QUANTILES}-Q1) (Sharpe: {mom_sharpe:.3f})', color='blue')
    rev_ls_portfolio.cumsum().plot(ax=ax2, label=f'Reversal (Q1-Q{N_QUANTILES}) (Sharpe: {rev_sharpe:.3f})', color='green')
    ax2.set_title('Cumulative Return of Long-Short Portfolios')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Cumulative Return (Non-Compounded)')
    ax2.legend()
    ax2.axhline(0, color='black', linestyle='--')

    plt.tight_layout(rect=[0, 0.03, 1, 0.98])

    # --- [!! 核心区别: "显示" !!] ---
    plt.show()

# --- (核心分析函数，来自队友，已添加 V2 优化) ---
def perform_quantile_analysis_v2(merged_prices_df, factor_lookback_days, forward_return_days, factor_name):
    """
    (已优化 V2)
    对合并的价格数据执行横截面分位数分析。
    [优化]: 添加 T-检验 和 Sharpe Ratio。
    """
    print(f"\n--- 正在运行分位数分析: {factor_name} ---")
    
    # 1. 计算因子值 (来自队友)
    factor_values = merged_prices_df.pct_change(factor_lookback_days)
    
    # 2. 计算未来收益 (来自队友)
    forward_returns = merged_prices_df.pct_change(forward_return_days).shift(-forward_return_days)
    
    # 3. 堆叠数据 (来自队友)
    factor_long = factor_values.stack().rename('factor')
    fwd_ret_long = forward_returns.stack().rename('fwd_return')
    
    df_long = pd.concat([factor_long, fwd_ret_long], axis=1)
    df_long.index.names = ['Date', 'Asset'] 
    df_long.dropna(inplace=True)
    
    if df_long.empty:
        print(f"  ❌ 错误: 在 {factor_name} 计算中没有剩余数据。")
        return

    # 4. 按日期分组，计算分位数 (来自队友)
    df_long['Quantile'] = df_long.groupby(level=0)['factor'].transform(
        lambda x: pd.qcut(x, N_QUANTILES, labels=False, duplicates='drop') + 1
    )
    df_long.dropna(inplace=True)

    # 5. 分析结果
    
    # A. 计算每个分位数的平均未来收益 (来自队友)
    quantile_returns = df_long.groupby('Quantile')['fwd_return'].mean()
    print(f"\n{factor_name} - 每个分位数的平均 {forward_return_days}日 收益:")
    print(quantile_returns.to_string(float_format="%.5f")) # 打印更精确
    
    # B. 计算多空组合 (来自队友)
    daily_quantile_returns = df_long.groupby(['Date', 'Quantile'])['fwd_return'].mean().unstack()
    
    mom_ls_portfolio = daily_quantile_returns[N_QUANTILES] - daily_quantile_returns[1]
    rev_ls_portfolio = daily_quantile_returns[1] - daily_quantile_returns[N_QUANTILES]

    # --- [!! 优化 V2: 统计显著性 !!] ---
    print("\n--- 核心论据 (统计显著性) ---")
    
    # T-检验: 检验 Q5 和 Q1 的均值是否 *不* 相等
    q1_returns = df_long[df_long['Quantile'] == 1]['fwd_return']
    qN_returns = df_long[df_long['Quantile'] == N_QUANTILES]['fwd_return']
    
    t_stat, p_value = stats.ttest_ind(qN_returns, q1_returns, equal_var=False)
    
    print(f"T-检验 (Q{N_QUANTILES} vs Q1): T-stat={t_stat:.3f}, P-value={p_value:.5f}")
    
    # 夏普比率 (Sharpe Ratio)
    # (假设无风险利率为 0，年化因子为 sqrt(252 / N))
    ann_factor = np.sqrt(252 / forward_return_days) 
    
    mom_sharpe = (mom_ls_portfolio.mean() / mom_ls_portfolio.std()) * ann_factor
    rev_sharpe = (rev_ls_portfolio.mean() / rev_ls_portfolio.std()) * ann_factor
    
    print(f"多空组合 (Momentum, Q{N_QUANTILES}-Q1) 年化夏普比率: {mom_sharpe:.4f}")
    print(f"多空组合 (Reversal, Q1-Q{N_QUANTILES}) 年化夏普比率: {rev_sharpe:.4f}")
    # --- [优化结束] ---

    # 6. 可视化 (来自队友)
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(15, 12))
    fig.suptitle(f'Cross-Sectional Analysis: {factor_name} ({N_QUANTILES} Quantiles)', y=1.02, fontsize=16)

    quantile_returns.plot(kind='bar', ax=ax1, 
                          color=plt.cm.coolwarm(np.linspace(0, 1, N_QUANTILES)))
    ax1.set_title(f'Avg. Forward {forward_return_days}-Day Return per Quantile (p-value={p_value:.4f})') # V2: 添加 p-value
    ax1.set_xlabel('Quantile (1 = Lowest Factor, 5 = Highest Factor)')
    ax1.set_ylabel('Avg. Forward Return')
    ax1.axhline(0, color='black', linestyle='--')

    mom_ls_portfolio.cumsum().plot(ax=ax2, label=f'Momentum (Q{N_QUANTILES}-Q1) (Sharpe: {mom_sharpe:.3f})', color='blue') # V2: 添加 Sharpe
    rev_ls_portfolio.cumsum().plot(ax=ax2, label=f'Reversal (Q1-Q{N_QUANTILES}) (Sharpe: {rev_sharpe:.3f})', color='green') # V2: 添加 Sharpe
    ax2.set_title('Cumulative Return of Long-Short Portfolios')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Cumulative Return (Non-Compounded)')
    ax2.legend()
    ax2.axhline(0, color='black', linestyle='--')

    plt.tight_layout(rect=[0, 0.03, 1, 0.98])

    # 7. 保存图表
    os.makedirs(QUANTILE_SAVE_DIR, exist_ok=True) # [修复] 确保在循环外创建
    output_filename = f"quantile_analysis_v2_{factor_name}.png"
    output_path = os.path.join(QUANTILE_SAVE_DIR, output_filename)
    plt.savefig(output_path)
    print(f"  [V2] Chart saved to {output_path}")
    plt.close(fig)

def main():
    """
    主执行函数：加载数据，运行两种因子分析。
    """
    print("--- 正在运行分位数 (Quantile) 分析脚本 [V2 优化版] ---")
    
    os.makedirs(QUANTILE_SAVE_DIR, exist_ok=True)
    print(f"Charts will be saved to: {QUANTILE_SAVE_DIR}")

    # 1. 加载数据 (使用我们自包含的 'Close-Only' 加载器)
    print(f"Calling internal load_and_merge_data(data_directory='{DATA_DIR_PATH}')...")
    
    merged_prices_df = load_and_merge_data(DATA_DIR_PATH)

    if merged_prices_df.empty:
        print("Error: Loader returned an empty DataFrame.")
        return

    print(f"✅ Loader success. Loaded merged DataFrame with {len(merged_prices_df.columns)} assets.")
    
    # 2. 运行分析 1: 短期反转 (Short-Term Reversal, 1个月)
    perform_quantile_analysis_v2(
        merged_prices_df, 
        factor_lookback_days=21, # ~1 个月
        forward_return_days=21,  # 持有 1 个月
        factor_name="STR_21D"    # 因子名
    )
    
    # 3. 运行分析 2: 动量 (Momentum, 6个月)
    perform_quantile_analysis_v2(
        merged_prices_df, 
        factor_lookback_days=126, # ~6 个月
        forward_return_days=21,   # 持有 1 个月
        factor_name="MOM_126D"    # 因子名
    )

    print("--- 分位数 (Quantile) 分析全部完成 ---")


if __name__ == "__main__":
    main()