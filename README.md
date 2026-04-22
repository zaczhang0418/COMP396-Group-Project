# EDA Stage 5 Archive Summary

Branch:

```text
summary/eda/stage-5-archive-summary
```

Source branch:

```text
archive/eda/stage-4-part123-overview
```

Reviewed on: 2026-04-22

这个 branch 是 EDA 工作流的 summary 留档 branch。它从 `archive/eda/stage-4-part123-overview` 整理而来，用来集中保存 Part 1、Part 2、Part 3、Part 1+2+3 的 EDA 流程、关键 output、报告截图线索和后续 merge 指南。

这个 branch 的定位是 EDA evidence archive，不是未来 `main` 的结构来源。

## 1. EDA 核心目标

这个 EDA branch 的目标是给后续 CA1、CA2、CA3 的策略设计提供数据层面的解释依据：

1. 观察 10 个资产在不同数据段里的收益、波动和相关性变化。
2. 用 ACF/PACF、Hurst、GARCH 等图表判断 trend-following、mean-reversion、volatility/regime 思路是否合理。
3. 比较 `PART1`、`PART2`、`PART3`、`PART123` 的整体市场环境差异。
4. 为报告中的策略演化提供证据：为什么先做资产硬绑定策略，为什么之后需要 generic 和 cross-asset scan。

报告中可以把这个 branch 概括为：

```text
EDA: strategy-relevant diagnostics across PART1, PART2, PART3, and PART123
```

## 2. EDA 优化路径

EDA 的整理路径可以按这条线讲：

1. Stage 1：早期价格图和基础可视化，用于理解原始价格行为。
2. Stage 2：扩展到更完整的诊断图，包括波动、分布、自相关、regime 线索等。
3. Stage 3：加入 Part 2 数据流程，让 EDA 不再只服务于 Part 1。
4. Stage 4：加入 Part 3，并生成 `PART123`，形成最终的全数据段 EDA overview。
5. Stage 5：把 EDA 证据集中整理到这个 summary branch，保留真正支持策略设计和报告写作的内容。

这个阶段保留的重点不是所有探索图，而是和 TF / MR / GARCH 策略线直接相关的图表和统计结果。

## 3. 当前数据分区

| Dataset | Date range | Rows | Assets |
| --- | --- | ---: | ---: |
| `PART1` | 2069-12-08 to 2072-09-02 | 10,000 | 10 |
| `PART2` | 2072-09-03 to 2075-05-30 | 10,000 | 10 |
| `PART3` | 2075-05-31 to 2078-02-23 | 10,000 | 10 |
| `PART123` | 2069-12-08 to 2078-02-23 | 30,000 | 10 |

`PART123` 由 `PART1`、`PART2`、`PART3` 合并生成：

```powershell
python EDA\scripts\merge_data_parts.py --parts PART1 PART2 PART3 --output PART123
```

时间线配置保存在：

```text
configs/timeline.json
```

## 4. Active Chart Families

Stage 4 / Stage 5 EDA 只保留和策略开发直接相关的 chart families：

| Chart family | 用途 |
| --- | --- |
| `acf` | 判断收益序列是否存在短期自相关，支持 MR / TF 信号设计 |
| `correlation_heatmap` | 观察资产间相关性，支持组合分散化和资产选择 |
| `garch` | 观察波动聚集，支持 GARCH / regime 类策略 |
| `hurst` | 判断趋势持续或均值回复倾向，支持 TF / MR 选择 |
| `histograms` | 观察收益分布和尾部风险 |
| `quantile_analysis` | 检查 short-term reversal 与 medium-term momentum 是否有分层效果 |
| `volatility` | 观察 ATR 和 rolling volatility，支持止损、过滤和仓位控制 |

以下早期探索图不再作为 active workflow：

```text
candlesticks
seasonality
rsi_analysis
volume_analysis
```

## 5. 留档 Output

核心 EDA output 在：

```text
EDA/output/
```

结构：

```text
EDA/output/
  PART1/
    charts/
    charts_by_asset/
    run_logs/
  PART2/
    charts/
    charts_by_asset/
    run_logs/
  PART3/
    charts/
    charts_by_asset/
    run_logs/
  PART123/
    charts/
    charts_by_asset/
    run_logs/
  stage4_overview/
    asset_summary.csv
    dataset_summary.csv
    risk_return_overview.png
    row_coverage.png
    total_return_heatmap.png
```

重要文档证据保存在：

```text
EDA/docs/stage4-overview.md
EDA/docs/latest-analysis.md
EDA/docs/latest-run.md
EDA/notebooks/EDA_Report_and_Justification.ipynb
```

`DOCS/requirements.txt` 保留为依赖清单。其他通用 project guide / branch archive 文档不再放在这个 summary branch 的根文档体系里，避免 README 分散。

## 6. Overview 结果

来自 `EDA/docs/latest-analysis.md` 和 `EDA/output/stage4_overview/dataset_summary.csv`：

| Dataset | Assets | Rows | Date range | Mean total return | Mean annualized volatility |
| --- | ---: | ---: | --- | ---: | ---: |
| PART1 | 10 | 10,000 | 2069-12-08 to 2072-09-02 | -4.29% | 16.49% |
| PART2 | 10 | 10,000 | 2072-09-03 to 2075-05-30 | 27.85% | 19.48% |
| PART3 | 10 | 10,000 | 2075-05-31 to 2078-02-23 | 25.96% | 22.65% |
| PART123 | 10 | 30,000 | 2069-12-08 to 2078-02-23 | 51.88% | 19.77% |

关键观察：

1. `PART1` 平均 total return 为负，环境更弱，适合解释早期策略为什么需要更谨慎的参数和风险控制。
2. `PART2` 和 `PART3` 平均收益明显更强，但 `PART3` 的平均波动也更高。
3. `PART123` 汇总了完整周期，适合做最终报告里的整体市场背景图。

## 7. Strategy Implications

EDA 对策略设计的主要贡献：

1. ACF/PACF 和 quantile analysis 支持我们同时测试 short-term reversal 与 medium-term momentum。
2. GARCH 结果显示多数资产存在较强 volatility persistence，这支持 GARCH / regime-aware 策略线。
3. Hurst 和 volatility 图帮助解释为什么同一个策略 family 在不同资产、不同 Part 上表现不同。
4. Correlation heatmap 说明资产之间并非完全同质，组合策略需要考虑分散化和资产选择。
5. `PART1`、`PART2`、`PART3` 环境不同，说明只在一个 Part 上调参很容易过拟合，这为 CA2 的 generic validation 和 CA3 的 cross-asset scan 提供动机。

## 8. 报告截图建议

建议优先使用这些总览图：

```text
EDA/output/stage4_overview/risk_return_overview.png
EDA/output/stage4_overview/row_coverage.png
EDA/output/stage4_overview/total_return_heatmap.png
EDA/output/stage4_overview/dataset_summary.csv
EDA/output/stage4_overview/asset_summary.csv
```

如果报告需要解释策略 family 的来源，可以补充：

```text
EDA/output/PART123/charts/correlation_heatmap.png
EDA/output/PART123/charts/quantile_analysis/quantile_analysis_v2_STR_21D.png
EDA/output/PART123/charts/quantile_analysis/quantile_analysis_v2_MOM_126D.png
EDA/output/PART123/charts/garch/garch_diagnostics_07.png
EDA/output/PART123/charts/hurst/hurst_v2_dual_axis_01_w252.png
EDA/output/PART123/charts/volatility/01_volatility_v2_atr.png
```

如果要对比不同数据段，可以分别截：

```text
EDA/output/PART1/charts/correlation_heatmap.png
EDA/output/PART2/charts/correlation_heatmap.png
EDA/output/PART3/charts/correlation_heatmap.png
EDA/output/PART123/charts/correlation_heatmap.png
```

## 9. 复现命令

运行完整 EDA workflow：

```powershell
.\EDA\run_all_eda.bat ALL
```

只生成 tracked overview：

```powershell
.\EDA\run_all_eda.bat OVERVIEW
```

运行单个 dataset：

```powershell
.\EDA\run_all_eda.bat PART1
.\EDA\run_all_eda.bat PART2
.\EDA\run_all_eda.bat PART3
.\EDA\run_all_eda.bat PART123
```

本机历史运行使用的 Python：

```text
D:\Anacoda\envs\comp396\python.exe
```

如果换机器运行，先安装依赖：

```powershell
pip install -r DOCS\requirements.txt
```

## 10. Future Merge Guidance

不要把这个 summary branch 整体 merge 到最新 `main`。这个 branch 包含历史 EDA workflow、生成图表、旧 framework/scripts 结构和大量 evidence output。

后期如果需要把 EDA 证据带回最新 main，只建议 pick / copy：

```text
README.md
DOCS/requirements.txt
EDA/docs/stage4-overview.md
EDA/docs/latest-analysis.md
EDA/docs/latest-run.md
EDA/notebooks/EDA_Report_and_Justification.ipynb
EDA/output/stage4_overview/
```

可选，只有最新 main 需要复现这个 EDA workflow 时再带：

```text
EDA/run_all_eda.bat
EDA/settings.py
EDA/data_loader.py
EDA/scripts/
EDA/plotting/
```

不要从这个 branch 直接带回：

```text
DATA/
framework/
strategies/
scripts/
tests/
EDA/output/PART1/
EDA/output/PART2/
EDA/output/PART3/
EDA/output/PART123/
```

`EDA/output/PART1` 到 `EDA/output/PART123` 的详细图表可以作为本 branch 的报告证据留档，但不建议合入干净的 latest main。

## 11. Verification

最近一次完整 EDA 运行记录：

```text
Requested command: EDA/run_all_eda.bat ALL
Started: 2026-04-22T12:01:39
Finished: 2026-04-22T12:04:14
Exit code: 0
```

运行摘要见：

```text
EDA/docs/latest-run.md
```

分析结果见：

```text
EDA/docs/latest-analysis.md
```
