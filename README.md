# Coursework 1 V1 Archive Summary

Branch:

```text
summary/coursework_1/stage-5-v1-archive-summary
```

Source branch:

```text
archive/coursework_1/stage-4-initial-combo-team01
```

Reviewed on: 2026-04-22

这个 branch 是 Coursework 1 / CA1 的 V1 留档总结 branch。它保留 stage 4 的原始策略逻辑，并补齐了可复现实验 output、结果矩阵和后续报告写作说明。

这个 branch 的定位是证据仓库，不是未来 `main` 的结构来源。

## 0. Versioned Team01 Naming

为了和 CA2 / CA3 的 summary branch 命名保持一致，这个 branch 现在给最早的 Team01 组合策略增加了一个版本化 alias：

```text
strategies/team01_v1.py
```

历史实现文件仍然保留为：

```text
strategies/combo_tf01_mr10_garch07_v1.py
```

也就是说：

```text
历史实现: combo_tf01_mr10_garch07_v1
归档版本名: team01_v1 / Team01 V1
复现 alias: Team01V1Strategy
```

`team01_v1.py` 只是一个轻量 wrapper，不复制或修改 V1 交易逻辑。

## 1. V1 核心思路

Coursework 1 V1 是 Team01 最早的组合策略原型。我们先分别开发三个资产硬绑定的单独策略，然后把它们组合成一个固定资产组合策略。

| Stage | 策略文件 | 绑定资产 | 角色 |
| --- | --- | --- | --- |
| Stage 1 | `strategies/tf_asset01_v1.py` | `series_1` | Trend-following leg |
| Stage 2 | `strategies/mr_asset10_v1.py` | `series_10` | Mean-reversion leg |
| Stage 3 | `strategies/garch_asset07_v1.py` | `series_7` | GARCH / regime trend-following leg |
| Stage 4 | `strategies/combo_tf01_mr10_garch07_v1.py` | `series_1`, `series_10`, `series_7` | Team01 V1 combined portfolio |

报告中可以把这个版本概括为：

```text
V1: asset-specific combined prototype
```

它的优点是已经把不同 alpha family 放进了同一个组合里；缺点也很清楚：策略逻辑和资产选择仍然硬绑定，还没有形成 Coursework 2 里的 generic strategy 思想。

## 2. 优化路径

Coursework 1 的优化路径可以按这条线讲：

1. 先在单个资产上构建三类策略：TF、MR、GARCH。
2. 对每个单独策略做参数搜索和 OOS 检查。
3. 选择表现相对稳定的 asset-bound leg。
4. 组合 TF01 + MR10 + GARCH07，形成 Team01 V1。
5. 在 `PART1`、`PART2`、`PART3`、`PART123` 上统一跑 archive matrix，观察 V1 是否有跨数据段稳定性。

这个阶段的重点不是 generic 泛化，而是证明我们已经完成了从单独策略到组合策略的第一版结构。

## 3. 留档 Output

核心 output 在：

```text
output/coursework_1_stage5_v1_archive/
```

结构：

```text
output/coursework_1_stage5_v1_archive/
  matrix_summary.csv
  matrix_summary.json
  archive_manifest.json
  PART1/
    tf_asset01_v1/
    mr_asset10_v1/
    garch_asset07_v1/
    combo_tf01_mr10_garch07_v1/
  PART2/
    tf_asset01_v1/
    mr_asset10_v1/
    garch_asset07_v1/
    combo_tf01_mr10_garch07_v1/
  PART3/
    tf_asset01_v1/
    mr_asset10_v1/
    garch_asset07_v1/
    combo_tf01_mr10_garch07_v1/
  PART123/
    tf_asset01_v1/
    mr_asset10_v1/
    garch_asset07_v1/
    combo_tf01_mr10_garch07_v1/
```

每个策略目录下包含：

```text
run_summary.json
per_series_pd.json
*.png
```

根目录的 `matrix_summary.csv` 和 `matrix_summary.json` 是总表，适合报告写作时先看整体表现。

## 4. Archive Matrix 结果

Matrix run date: 2026-04-22

Command:

```powershell
python scripts\run_coursework_1_stage5_archive_matrix.py --with-plots
```

| Dataset | Strategy | Final value | True PD | Open PnL PD | Activity % | Bankrupt |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| PART1 | TF asset01 V1 | 1148068.52 | 1.4050 | 2.4700 | 25.83 | No |
| PART1 | MR asset10 V1 | 1090352.16 | 1.8245 | 4.3541 | 31.70 | No |
| PART1 | GARCH asset07 V1 | 1002568.38 | 0.1651 | 0.4806 | 13.70 | No |
| PART1 | Combo V1 | 998083.95 | -0.0249 | 0.2270 | 74.97 | No |
| PART2 | TF asset01 V1 | 997663.14 | -0.0230 | 0.2764 | 29.23 | No |
| PART2 | MR asset10 V1 | 955611.35 | -0.3195 | 0.3482 | 29.63 | No |
| PART2 | GARCH asset07 V1 | 988387.08 | -0.4697 | -0.4340 | 12.40 | No |
| PART2 | Combo V1 | 1036933.25 | 0.4834 | 1.3694 | 84.48 | No |
| PART3 | TF asset01 V1 | 1026463.85 | 1.5872 | 2.6754 | 4.60 | No |
| PART3 | MR asset10 V1 | 827948.56 | -0.7471 | -0.2909 | 27.80 | No |
| PART3 | GARCH asset07 V1 | 999267.30 | -0.0621 | 0.0316 | 16.40 | No |
| PART3 | Combo V1 | 1195196.46 | 2.6626 | 3.1977 | 88.19 | No |
| PART123 | TF asset01 V1 | -98448.60 | -0.7490 | -0.5706 | 46.56 | Yes, 2076-07-30 |
| PART123 | MR asset10 V1 | 918148.74 | -0.2622 | 2.5977 | 31.70 | No |
| PART123 | GARCH asset07 V1 | 989402.10 | -0.3904 | -0.1796 | 14.17 | No |
| PART123 | Combo V1 | 1218435.74 | 2.8371 | 4.1094 | 87.83 | No |

## 5. 结果分析

V1 的组合策略在 `PART2`、`PART3`、`PART123` 上表现比很多单独 leg 更稳定，说明组合确实带来了分散化效果。

但它也暴露了两个问题：

1. 单独策略表现不稳定。比如 TF 在 `PART123` 出现 bankruptcy，MR 在 `PART3` 明显亏损。
2. 组合的高 activity 说明它更像多个固定资产 leg 的叠加，而不是一个真正泛化的策略框架。

所以 Coursework 1 的结论可以写成：V1 证明了多策略组合有价值，但资产硬绑定限制了泛化能力。这直接引出 Coursework 2 的 generic strategy 优化方向。

## 6. 报告截图建议

建议报告中优先使用这些图和表：

```text
output/coursework_1_stage5_v1_archive/matrix_summary.csv
output/coursework_1_stage5_v1_archive/PART1/combo_tf01_mr10_garch07_v1/equity_dashboard_combined.png
output/coursework_1_stage5_v1_archive/PART2/combo_tf01_mr10_garch07_v1/equity_dashboard_combined.png
output/coursework_1_stage5_v1_archive/PART3/combo_tf01_mr10_garch07_v1/equity_dashboard_combined.png
output/coursework_1_stage5_v1_archive/PART123/combo_tf01_mr10_garch07_v1/equity_dashboard_combined.png
```

如果要说明单独 leg 的局限，可以补充：

```text
output/coursework_1_stage5_v1_archive/PART123/tf_asset01_v1/equity_dashboard_combined.png
output/coursework_1_stage5_v1_archive/PART3/mr_asset10_v1/equity_dashboard_combined.png
```

## 7. 复现命令

完整复现 archive matrix：

```powershell
python scripts\run_coursework_1_stage5_archive_matrix.py --with-plots
```

只生成轻量 JSON/CSV，不生成 PNG：

```powershell
python scripts\run_coursework_1_stage5_archive_matrix.py
```

直接运行 V1 combo：

```powershell
python main.py --strategy combo_tf01_mr10_garch07_v1 --data-dir .\DATA\PART1
```

使用版本化 alias 运行同一个 V1 combo：

```powershell
python main.py --strategy team01_v1 --strategy-class Team01V1Strategy --data-dir .\DATA\PART1
```

## 8. Future Merge Guidance

不要把这个 summary branch 整体 merge 到最新 `main`。这个 branch 基于历史 Coursework 1 stage 4 结构，保留了旧 framework、旧 DATA layout 和旧策略文件。

后期如果需要把 CA1/V1 证据带回最新 main，只建议 pick / copy：

```text
README.md
strategies/team01_v1.py
output/coursework_1_stage5_v1_archive/
```

可选，只有在最新 main 也需要复现这套 V1 archive matrix 时再带：

```text
scripts/run_coursework_1_stage5_archive_matrix.py
```

不要从这个 branch 带回：

```text
.gitignore
DATA/
configs/
framework/
strategies/
scripts/ other than scripts/run_coursework_1_stage5_archive_matrix.py
```

最新 `main` 应该继续拥有当前项目结构、EDA 流程、数据布局和通用策略工具。这个 branch 只作为 CA1/V1 evidence archive。

## 9. Verification

以下 syntax check 在 2026-04-22 通过：

```powershell
python -m py_compile strategies\tf_asset01_v1.py strategies\mr_asset10_v1.py strategies\garch_asset07_v1.py strategies\combo_tf01_mr10_garch07_v1.py scripts\run_combo_once.py scripts\pick_best_and_run_oos_full_tf.py scripts\pick_best_and_run_oos_full_mr.py scripts\pick_best_and_run_oos_full_garch.py
```

历史说明：这个 branch 的部分旧代码注释在当前终端编码下可能显示为 mojibake。本 summary branch 不修改旧策略逻辑，只整理留档说明和证据路径。
