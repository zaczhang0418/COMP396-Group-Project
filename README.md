# Coursework 3 V3 Archive Summary

Branch:

```text
summary/coursework_3/stage-2-v3-archive-summary
```

Source branch:

```text
archive/coursework_3/stage-1-cross-asset-scan
```

Reviewed on: 2026-04-23

这个 branch 是 Coursework 3 / CA3 的 V3 留档总结 branch。它从 cross-asset scan archive branch 整理而来，用来集中保存最终策略 V3 的开发逻辑、cross-asset evidence、Team01 V3 final output、报告截图建议和 future merge guidance。

这个 branch 的定位是 V3 evidence archive，不是未来 `main` 的结构来源。

## 1. V3 核心定位

CA3 的最终策略版本命名为：

```text
Team01 V3 final strategy
```

为了和 CA1 / CA2 区分，archive branch 里增加了一个 versioned strategy id：

```text
strategies/team01_v3.py
```

但 assignment-facing submission file 仍然保留为：

```text
strategies/team01.py
```

原因和 CA2 一样：历史 output、框架默认提交约定和最终提交文件都围绕 `team01.py`。所以这个 branch 的做法是：

```text
提交文件: strategies/team01.py
归档版本名: team01_v3 / Team01 V3
复现 alias: strategies/team01_v3.py
```

`team01_v3.py` 只是一个轻量 wrapper，不复制策略逻辑。真正的最终策略实现仍然在 `team01.py`。

## 2. 从 V2 到 V3 的优化路径

V2 已经完成了 generic single-strategy workflow，但最终组合仍然继承了较强的历史资产绑定：

```text
V2 baseline:
  TF series_1 + MR series_10 + GARCH series_7
```

CA3 继续往前走了一步：

1. 用 generic TF / MR / GARCH 框架扫描全部 10 个资产。
2. 用 Part 1 grid search 和 robust selection 得到每个 strategy-asset pair 的候选参数。
3. 用 OOS / FULL / Part 2 validation 检查跨数据段表现。
4. 用 scan evidence 判断哪些 strategy family 在哪些资产上真正有价值。
5. 不再机械沿用 V2 的硬绑定结构，而是重新设计最终组合。
6. 在最终 `team01.py` 中加入 daily market condition 判断、动态 allocation、performance-aware budgeting、loss freeze、gross exposure cap 和 rebalance threshold。
7. 最终用 `team01_v3` 这个 strategy id 重新生成 Part 1、Part 2、Part 3 performance output。

V3 的一句话总结：

```text
V3: cross-asset-refined final strategy with daily market-condition gating and dynamic portfolio controls.
```

## 3. Final Strategy Definition

最终 deployed mapping：

| Leg | Data feed | Role | Base weight |
| --- | --- | --- | ---: |
| TF | `series_1` | Trend-following / leadership leg | 0.65 |
| MR09 | `series_9` | Mean-reversion leg selected after cross-asset analysis | 0.35 |

V3 和 V2 的结构差异：

```text
V2:
  TF series_1 + MR series_10 + GARCH series_7

V3:
  TF series_1 + MR series_9
```

这里有两个重点：

1. V3 保留了 TF on `series_1`，因为 scan 和 Part 2 validation 都支持它作为稳定 leadership / trend leg。
2. MR 从 `series_10` 改为 `series_9`，因为 CA3 的 cross-asset evidence 显示 MR09 在 OOS / FULL 维度更适合作为最终 mean-reversion leg。

GARCH 没有进入最终 deployed `team01.py`。这不是因为 GARCH 完全无效，而是因为最终组合更重视 deployable simplicity、risk control 和 Part 2 / Part 3 稳定性。

## 4. 新增逻辑：不只是 Cross-Asset Scan

CA3 的提升不只是 “scan 了 30 个组合”。最终策略相对 V2 还有几类新增逻辑。

### 4.1 解除历史硬绑定

V2 的结构还带有 CA1 的影子：

```text
TF asset01
MR asset10
GARCH asset07
```

V3 用 cross-asset scan 重新检查每个 strategy family 和每个 asset 的匹配关系。最终没有直接沿用 `MR series_10`，而是改成 `MR series_9`。

这可以在报告里解释为：

```text
We separated strategy-family design from asset selection.
```

### 4.2 多资产池判断

CA3 不是只看单一资产或单一策略，而是把候选池扩展成：

```text
TF / MR / GARCH x asset01 ... asset10
```

这样做的意义是：

1. 每个 strategy family 都可以在完整资产池里竞争。
2. 每个 asset 都可以被不同 strategy family 解释。
3. 最终组合不是 “哪个单策略最高就放进去”，而是在 scan evidence、Part 2 validation、组合复杂度和风险控制之间做取舍。

### 4.3 每日市场行情判断

V3 在交易日内会根据当前市场状态决定是否允许某个 leg 积极参与。这个逻辑主要体现在：

```text
_tf_hot_score()
_tf_score()
_tf_target_pct()
_compute_active_weights()
_dynamic_budget_weights()
```

TF leg 不只是看到 EMA 趋势就交易，还会判断 `series_1` 是否处在强势行情：

| Signal component | Meaning |
| --- | --- |
| close above short SMA | 当前价格是否站上短期均线 |
| gap versus SMA | 当前价格相对短期均线是否足够强 |
| 1-day jump vs ATR | 当日跳动是否相对自身 ATR 足够强 |
| 3-day jump vs ATR | 短期连续动量是否足够强 |
| Hurst / trend score | 趋势 persistence 是否支持更高仓位 |

这就是我们引入的 “判断当日市场行情” 思路：不是每天固定按静态权重交易，而是根据当天的 trend strength、hot move 和 volatility context 调整参与度。

### 4.4 动态资金分配

V2 更接近静态组合权重。V3 加入：

```text
dynamic_alloc_enabled=True
dynamic_alloc_strength=0.35
```

策略会根据当前 TF / MR signal strength 在两个 leg 之间动态调整资金权重，同时受 floor / cap 约束：

```text
tf_weight_floor=0.40
tf_weight_cap=0.82
mr_weight_floor=0.18
mr_weight_cap=0.60
```

这让策略可以在强趋势日更偏 TF，在 MR 信号更清晰时给 MR09 更多预算。

### 4.5 Performance-Aware Budgeting

V3 还会根据近期 closed-trade performance 调整预算：

```text
perf_alloc_enabled=True
perf_alpha=0.25
perf_scale=12.0
perf_floor_mult=0.70
perf_cap_mult=1.40
```

这相当于让策略对最近表现做温和反馈：表现好的 leg 可以获得更高有效预算，表现弱的 leg 会被压低，但不会完全失去机会。

### 4.6 Loss Freeze 和交易冷却

V3 引入 loss streak 后的临时冻结：

```text
loss_freeze_after=3
loss_freeze_bars=12
```

如果某个 leg 连续亏损，它会被短暂冻结，避免在不适合它的 market regime 中连续重复进场。

### 4.7 Gross Exposure 和 Rebalance 控制

V3 加入：

```text
gross_cap=1.00
rebalance_tol=0.015
```

这两个设置是针对 V2 中 activity / rebalance pressure / overspend risk 的修正。策略不会无限扩大 gross exposure，也不会因为很小的目标仓位变化就频繁调仓。

### 4.8 MR09 Volatility 与 Z-Score Filter

MR09 leg 使用：

```text
mr09_entry_z=2.25
mr09_exit_z=0.75
mr09_atr_pctl_enter=0.90
mr09_vol_relax_mult=1.05
mr09_max_hold_days=7
```

它不是简单 “偏离均值就买/卖”，而是同时检查 z-score、ATR percentile、holding period 和 volatility regime。

## 5. Cross-Asset Scan Evidence

核心 scan output：

```text
output/cross_asset_scan_v1/
```

核心 summary files：

```text
output/cross_asset_scan_v1/summaries/summary.json
output/cross_asset_scan_v1/summaries/cross_asset_long.csv
output/cross_asset_scan_v1/summaries/matrix_3x10.csv
output/cross_asset_scan_v1/summaries/asset_strategy_assignment.csv
output/cross_asset_scan_v1/summaries/part2_validation.csv
output/cross_asset_scan_v1/summaries/cross_asset_performance_matrix_tf_mr.csv
output/cross_asset_scan_v1/summaries/strategy_asset_mapping_matrix_tf_mr.csv
output/cross_asset_scan_v1/summaries/strategy_asset_eligibility_tf_mr.csv
```

Main scan setup：

| Dimension | Value |
| --- | --- |
| Scan tag | `cross_asset_scan_v1` |
| Strategy families | `tf`, `mr`, `garch` |
| Assets | `asset01` to `asset10` |
| Records | 30 |
| Matrix metric | `oos_true_pd_ratio` |
| Selection mode | `robust` |

Winner counts：

| Strategy family | Winner count |
| --- | ---: |
| TF | 3 |
| MR | 5 |
| GARCH | 2 |

## 6. 3 x 10 Matrix

`matrix_3x10.csv` records `oos_true_pd_ratio`:

| Strategy | asset01 | asset02 | asset03 | asset04 | asset05 | asset06 | asset07 | asset08 | asset09 | asset10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TF | 0.704 | -0.735 | -0.164 | -0.172 | -1.000 | 0.216 | -0.015 | -0.199 | -0.202 | -0.542 |
| MR | -0.193 | -0.378 | 0.390 | -0.116 | 0.057 | 2.967 | -0.451 | N/A | 2.351 | 1.213 |
| GARCH | 0.272 | 0.137 | -0.931 | 1.902 | 2.839 | -0.469 | -0.505 | -0.381 | 1.507 | -0.956 |

Top OOS candidates:

| Rank | Strategy | Asset | OOS true PD | Full true PD | Part 2 true PD |
| ---: | --- | --- | ---: | ---: | ---: |
| 1 | MR | asset06 | 2.967 | 8.970 | -0.580 |
| 2 | GARCH | asset05 | 2.839 | 3.097 | -0.910 |
| 3 | MR | asset09 | 2.351 | 4.454 | -0.126 |
| 4 | GARCH | asset04 | 1.902 | 2.330 | 0.314 |
| 5 | GARCH | asset09 | 1.507 | -0.110 | 1.007 |
| 6 | MR | asset10 | 1.213 | 4.270 | -0.898 |
| 7 | TF | asset01 | 0.704 | 2.762 | 0.896 |
| 8 | MR | asset03 | 0.390 | 2.589 | 0.635 |

这个表说明：最高 Part 1 / OOS row 不一定能在 Part 2 上稳定转移。因此 V3 的最终组合不是机械选择单个最高 OOS row，而是综合 scan evidence、validation、组合复杂度和 risk controls。

## 7. Asset Assignment Evidence

`asset_strategy_assignment.csv` 给出每个 asset 的 winner strategy：

| Asset | Winner strategy | OOS true PD | Full true PD | Part 2 true PD |
| --- | --- | ---: | ---: | ---: |
| asset01 | TF | 0.704 | 2.762 | 0.896 |
| asset02 | MR | -0.378 | 0.733 | 1.084 |
| asset03 | MR | 0.390 | 2.589 | 0.635 |
| asset04 | GARCH | 1.902 | 2.330 | 0.314 |
| asset05 | GARCH | 2.839 | 3.097 | -0.910 |
| asset06 | MR | 2.967 | 8.970 | -0.580 |
| asset07 | TF | -0.015 | 0.749 | 1.478 |
| asset08 | TF | -0.199 | 0.273 | 0.103 |
| asset09 | MR | 2.351 | 4.454 | -0.126 |
| asset10 | MR | 1.213 | 4.270 | -0.898 |

最终 deployed V3 使用：

```text
TF asset01 / series_1
MR asset09 / series_9
```

它不部署每个 per-asset winner，而是选择适合最终组合结构的两个 leg。

## 8. V3 Performance Output

V3 final performance output 按 summary branch 命名逻辑整理到：

```text
output/coursework_3_stage2_v3_archive/
```

结构：

```text
output/coursework_3_stage2_v3_archive/
  archive_manifest.json
  process_summary.csv
  team01_v3_final/
    part1/
    part2/
    part3/
```

每个 part 目录包含：

```text
run_summary.json
per_series_pd.json
*.png
```

`process_summary.csv` 是最终 V3 performance 总表。

## 9. V3 Performance Results

Regenerated with:

```text
strategy_id = team01_v3
strategy_class = Team01V3Strategy
s_mult = 2.0
end_policy = liquidate
```

| Dataset | Final value | True PD | Open PnL PD | Activity % | Bankrupt |
| --- | ---: | ---: | ---: | ---: | --- |
| Part 1 | 969048.34 | -0.5153 | -0.0172 | 36.94 | No |
| Part 2 | 1083657.94 | 2.2075 | 3.4826 | 46.10 | No |
| Part 3 | 1210964.70 | 8.2884 | 9.0926 | 53.30 | No |

Interpretation:

1. Part 1 表现偏弱，说明 V3 不是单纯 in-sample optimizer。
2. Part 2 和 Part 3 表现明显改善，支持最终 cross-asset refinement 和 daily market-condition gating。
3. 三个 part 都没有 bankrupt。
4. Activity 比 V1 的高频组合更受控，同时通过 dynamic allocation 和 rebalance tolerance 降低无意义调仓。

## 10. 报告叙事建议

推荐写法：

```text
In CA3, we used the generic strategy architecture developed in CA2 to run a 3 x 10 cross-asset scan across TF, MR, and GARCH strategy families. The scan showed that strategy-family performance varied substantially by asset and that high Part 1 / OOS performance did not always transfer cleanly to Part 2. We therefore redesigned the final Team01 strategy as Team01 V3: a simpler two-leg portfolio using TF on series_1 and MR on series_9, supported by daily market-condition gating, hot leadership filtering, dynamic allocation, performance-aware budgeting, loss freezes, gross exposure caps, and rebalance thresholds.
```

版本对比：

| Version | Summary |
| --- | --- |
| V1 | Asset-specific combined prototype: TF01 + MR10 + GARCH07 |
| V2 | Generic / presubmission combined strategy with parameter selection and Part 2 validation |
| V3 | Cross-asset-refined final strategy: TF01 + MR09 with daily market-condition gating and dynamic portfolio controls |

## 11. 报告截图建议

Cross-asset scan evidence：

```text
output/cross_asset_scan_v1/summaries/matrix_3x10.csv
output/cross_asset_scan_v1/summaries/asset_strategy_assignment.csv
output/cross_asset_scan_v1/summaries/part2_validation.csv
output/cross_asset_scan_v1/summaries/cross_asset_performance_matrix_tf_mr.csv
output/cross_asset_scan_v1/summaries/strategy_asset_mapping_matrix_tf_mr.csv
```

V3 final performance：

```text
output/coursework_3_stage2_v3_archive/process_summary.csv
output/coursework_3_stage2_v3_archive/team01_v3_final/part1/equity_dashboard_combined.png
output/coursework_3_stage2_v3_archive/team01_v3_final/part2/equity_dashboard_combined.png
output/coursework_3_stage2_v3_archive/team01_v3_final/part3/equity_dashboard_combined.png
```

如果需要说明最终只使用 `series_1` 和 `series_9`：

```text
output/coursework_3_stage2_v3_archive/team01_v3_final/part1/series_1_cumPnL.png
output/coursework_3_stage2_v3_archive/team01_v3_final/part1/series_9_cumPnL.png
output/coursework_3_stage2_v3_archive/team01_v3_final/part2/series_1_cumPnL.png
output/coursework_3_stage2_v3_archive/team01_v3_final/part2/series_9_cumPnL.png
output/coursework_3_stage2_v3_archive/team01_v3_final/part3/series_1_cumPnL.png
output/coursework_3_stage2_v3_archive/team01_v3_final/part3/series_9_cumPnL.png
```

## 12. 复现命令

Run Part 1 cross-asset scan:

```powershell
python scripts\cross_asset_scan\run_cross_asset_scan.py --scan-tag cross_asset_scan_v1 --strategies all --assets all --selection-mode robust --key true_pd_ratio --runs is,oos,full --skip-existing
```

Run Part 2 validation:

```powershell
python scripts\cross_asset_scan\validate_cross_asset_scan_part2.py --scan-tag cross_asset_scan_v1 --strategies all --assets all --skip-existing
```

Build summary tables:

```powershell
python scripts\cross_asset_scan\summarize_cross_asset_scan.py --scan-tag cross_asset_scan_v1 --strategies all --assets all --matrix-metric oos_true_pd_ratio
```

Run final Team01 V3:

```powershell
$env:MPLBACKEND='Agg'
python main.py --strategy team01_v3 --strategy-class Team01V3Strategy --data-dir .\DATA\PART1 --output-dir .\output\coursework_3_stage2_v3_archive\team01_v3_final\part1 --s-mult 2.0
python main.py --strategy team01_v3 --strategy-class Team01V3Strategy --data-dir .\DATA\PART2 --output-dir .\output\coursework_3_stage2_v3_archive\team01_v3_final\part2 --s-mult 2.0
```

Part 3 note:

```text
This historical CA3 branch only has DATA/PART1, DATA/PART2, and DATA/COMBINED.
The archived Part 3 performance was regenerated using DATA/PART3 from main as a temporary local data source.
DATA/PART3 is not committed to this summary branch.
```

## 13. Future Merge Guidance

不要把这个 summary branch 整体 merge 到最新 `main`。这个 branch 包含历史 framework、DATA、scripts、strategies 和大量 generated output。后期合入 main 时应该按展示需求选择性 pick / copy。

### 13.1 推荐方案：轻量展示版

如果 final main 只需要展示最终 V3 策略、Part 1 / Part 2 / Part 3 表现、以及 cross-asset scan 的 summary evidence，建议只带这些：

```text
strategies/team01.py
strategies/team01_v3.py
output/coursework_3_stage2_v3_archive/
output/cross_asset_scan_v1/summaries/
```

README 的处理建议：

```text
不要直接用本 branch 的 README.md 覆盖 main README.md。
建议把本 README 内容复制成 main 里的 CA3 留档文档，例如：
DOCS/coursework_3_stage2_v3_archive_summary.md
```

轻量展示版的优点：

1. main 可以展示最终 V3 策略和最终 performance。
2. main 可以展示 cross-asset scan 的核心表格和选择逻辑。
3. 不会把几万个 scan raw output 文件带进 main。
4. 冲突和仓库体积都更可控。

### 13.2 可选方案：完整 Cross-Asset Scan 展示版

如果最后展示效果需要完整保留 cross-asset scan，也就是希望 main 里能展开查看每个 strategy-asset pair 的 grid search、candidate、best runs 和 Part 2 validation，可以额外带：

```text
output/cross_asset_scan_v1/
```

注意：完整 `output/cross_asset_scan_v1/` 很大，当前包含：

```text
tf/
mr/
garch/
summaries/
```

其中 raw scan records 大约 24,000+ files，`run_summary.json` 大约 5,000+ 个。它的展示价值很强，但会显著增加 main 的体积。

如果选择完整 scan 展示版，还建议同时带复现依赖：

```text
scripts/cross_asset_scan/
configs/grids/single_strat/
strategies/tf_generic_v1.py
strategies/mr_generic_v1.py
strategies/garch_generic_v1.py
```

这样 main 不只是能展示 scan output，也能解释这些 output 是怎么生成的。

### 13.3 不建议合入 main 的内容

这些不要从本 branch 直接带回 main：

```text
DATA/
framework/
scripts/ other than scripts/cross_asset_scan/
strategies/archive/
__pycache__/
*.pyc
.vscode/
README_stage3_cross_asset_scan.md
output/ca3_stage3_team01_part1/
output/ca3_stage3_team01_part2/
```

原因：

1. `DATA/` 和 `framework/` 属于历史 branch 结构，容易覆盖 main 的最新结构。
2. 旧 `scripts/` 里有很多历史实验入口，不适合作为 main 的当前工具来源。
3. `output/ca3_stage3_team01_part1/` 和 `output/ca3_stage3_team01_part2/` 已经被新的规范目录取代：

```text
output/coursework_3_stage2_v3_archive/team01_v3_final/part1/
output/coursework_3_stage2_v3_archive/team01_v3_final/part2/
output/coursework_3_stage2_v3_archive/team01_v3_final/part3/
```

### 13.4 最终建议

默认推荐轻量展示版：

```text
DOCS/coursework_3_stage2_v3_archive_summary.md
strategies/team01.py
strategies/team01_v3.py
output/coursework_3_stage2_v3_archive/
output/cross_asset_scan_v1/summaries/
```

如果报告展示或答辩需要打开完整 scan 过程，再升级为完整 Cross-Asset Scan 展示版，把 `output/cross_asset_scan_v1/` 整体带入 main。

## 14. Verification

Syntax check passed:

```powershell
python -m py_compile strategies\team01.py strategies\team01_v3.py
```

V3 final runs regenerated successfully with `MPLBACKEND=Agg` and `s_mult=2.0` for:

```text
Part 1: output/coursework_3_stage2_v3_archive/team01_v3_final/part1
Part 2: output/coursework_3_stage2_v3_archive/team01_v3_final/part2
Part 3: output/coursework_3_stage2_v3_archive/team01_v3_final/part3
```
