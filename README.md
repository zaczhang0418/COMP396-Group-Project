# Coursework 2 V2 归档总结

Branch:

```text
summary/coursework_2/stage-4-v2-archive-summary
```

这个 branch 是 CA2 / Coursework 2 V2 优化流程的证据归档 branch。它的作用是支持最终报告写作和后续留档，不应该被当作未来 `main` 的代码结构来源。

## 核心路径

Coursework 2 是从 CA1 中三个有用的策略想法继续发展出来的：

```text
TF on asset 01
MR on asset 10
GARCH on asset 07
```

CA2 的优化路径是：

```text
资产硬绑定的单策略
  -> generic TF / MR / GARCH 策略族
  -> Part 1 grid search 与 robust candidate selection
  -> Part 2 transfer validation
  -> Team01 V2 presubmission combo strategy
```

最终 presubmission 策略文件仍然是：

```text
strategies/team01.py
```

为了和 CA1 / CA3 的 summary branch 命名保持一致，这个 branch 增加了一个版本化 alias：

```text
strategies/team01_v2.py
```

也就是说：

```text
提交文件: strategies/team01.py
归档版本名: team01_v2 / Team01 V2
复现 alias: Team01V2Strategy
```

不要把历史实现文件 `team01.py` 直接重命名。历史提交和现有 output 仍然对应原始 `team01` strategy id；`team01_v2.py` 只是一个轻量 wrapper，用来让 summary branch 的版本命名和 V1 / V3 保持一致。

## 证据目录

所有保留的 output 证据都在：

```text
output/coursework_2_stage4_v2_archive/
```

当前 output 结构：

```text
asset_bound_grid_search_run_summaries/   # 历史 IS grid-search run_summary
parameter_selection_candidates/          # 每个策略族 5 个 candidate + best_params
generic_single_strats_output/            # TF/MR/GARCH 单策略 Part 1 和 Part 2 output
team01_presubmission/                    # Team01 Part 1、Part 2、保留的 Part 3 output
archive_manifest.json
process_summary.csv
per_leg_summary.csv
```

根目录 summary 文件：

```text
process_summary.csv   # 9 行高层结果汇总
per_leg_summary.csv   # Team01 各 leg 表现拆分
archive_manifest.json # source branches 和归档结构说明
```

## 优化证据

Grid-search run summary 数量：

| Strategy idea | Fixed asset | Grid candidate summaries | Robust validation summaries |
| --- | --- | ---: | ---: |
| `tf_asset01_v1` | `series_1` | 125 | 10 |
| `mr_asset10_v1` | `series_10` | 125 | 10 |
| `garch_asset07_v1` | `series_7` | 256 | 10 |

参数筛选证据：

```text
output/coursework_2_stage4_v2_archive/parameter_selection_candidates/
```

每个策略族保留：

```text
candidates/candidate_01/params.json
candidates/candidate_02/params.json
candidates/candidate_03/params.json
candidates/candidate_04/params.json
candidates/candidate_05/params.json
candidates/robust_ranking.csv
best_params.json
```

CA2 最终选择的参数：

| Family | Asset | Selected parameters |
| --- | --- | --- |
| TF | `series_1` | `p_ema_short=18`, `p_ema_long=50`, `p_hurst_min_soft=0.55` |
| MR | `series_10` | `p_lookback=30`, `p_entry_z=2.25`, `p_exit_z=0.0` |
| GARCH | `series_7` | `p_sigma_q_low=0.3`, `p_sigma_q_high=0.75`, `p_mult_mid=0.5`, `p_mult_high=0.2` |

## 单策略结果

Generic single-strategy Part 1 full-run 结果：

| Strategy | Asset | Final value | True PD | Open PnL PD | Activity % |
| --- | --- | ---: | ---: | ---: | ---: |
| TF generic | `series_1` | 5119713.55 | 2.7617 | 2.9370 | 83.88 |
| MR generic | `series_10` | 1087902.35 | 4.2700 | 4.3682 | 5.60 |
| GARCH generic | `series_7` | 1003531.25 | 0.6119 | 2.0448 | 3.80 |

Part 2 transfer 结果，也就是直接把 Part 1 选出的参数迁移到 Part 2，不重新优化：

| Strategy | Asset | Final value | True PD | Open PnL PD | Activity % |
| --- | --- | ---: | ---: | ---: | ---: |
| TF generic | `series_1` | 2667396.07 | 0.8959 | 0.9913 | 49.55 |
| MR generic | `series_10` | 910043.42 | -0.8983 | -0.8492 | 3.90 |
| GARCH generic | `series_7` | 989246.67 | -0.6419 | -0.5781 | 9.40 |

结果解读：

- TF 的迁移表现最好，是主要收益驱动。
- MR 和 GARCH 作为 research family 有价值，但原来的固定资产映射在 Part 2 上变弱。
- 这个结果说明，CA2 后续应该继续做 cross-asset reassessment 和更强的 portfolio-level risk control。

## Team01 Presubmission 结果

Team01 V2 combo output：

| Dataset | Final value | True PD | Open PnL PD | Activity % |
| --- | ---: | ---: | ---: | ---: |
| Part 1 | 948298.86 | -0.6922 | -0.2841 | 67.27 |
| Part 2 | 1166853.42 | 2.2440 | 3.3408 | 81.48 |
| Part 3 existing | 1130900.67 | 1.3152 | 3.2499 | 90.30 |

Part 3 leg breakdown：

| Leg | Series | Final cumulative PnL | PnL / DD |
| --- | --- | ---: | ---: |
| TF | `series_1` | 186898.57 | 2.8628 |
| GARCH | `series_7` | 25830.61 | 2.3091 |
| MR | `series_10` | 7916.50 | 0.2506 |
| Portfolio | all | n/a | 3.2499 |

## 报告写作要点

建议 CA2 报告按这个逻辑展开：

1. 先总结我们对 CA2 的期望：generic strategy family 应该让 CA1 的想法更可复用，减少对单个 hard-coded asset strategy 的依赖。
2. 总结 Part 3 表现时不要只看 final value，也要结合 true PD、open PnL PD、activity、per-leg contribution 和图表。
3. 对比最初期望与实际结果：TF 是最能迁移的收益来源，MR 和 GARCH 在 transfer 后较弱。
4. 总结 CA2 应该改进的地方：
   - 资产选择仍然过于硬绑定，不能默认 asset 01 / 10 / 07 就是最优选择。
   - Team01 的 activity 仍然偏高，也存在 framework execution constraints 下的 overspend 风险。
   - 资金分配是静态权重，没有动态优化，也没有 drawdown-aware reallocation。
5. 总结学到的经验：
   - 只做参数优化不够，asset selection 和 portfolio construction 同样重要。
   - Transfer testing 很关键，因为 Part 1 表现强不代表 Part 2 也稳。
   - 后续版本应该结合 cross-asset selection、更强 risk control 和动态 position sizing。

建议报告引用或截图的证据：

```text
output/coursework_2_stage4_v2_archive/process_summary.csv
output/coursework_2_stage4_v2_archive/per_leg_summary.csv
output/coursework_2_stage4_v2_archive/team01_presubmission/part3_existing/equity_dashboard_combined.png
output/coursework_2_stage4_v2_archive/team01_presubmission/part3_existing/all_equity_curves.png
```

如果需要 terminal 截图，可以重新运行：

```powershell
python scripts\run_coursework_2_stage4_archive_matrix.py
```

如需用版本化 alias 复现 V2 presubmission strategy，可运行：

```powershell
python main.py --strategy team01_v2 --strategy-class Team01V2Strategy --data-dir .\DATA\PART1
```

预期会输出三个 regenerated summary files：

```text
process_summary.csv
per_leg_summary.csv
archive_manifest.json
```

## 复现命令

这个 branch 主要保留历史 evidence。若要重新生成简洁 summary tables：

```powershell
python scripts\run_coursework_2_stage4_archive_matrix.py
```

该脚本会读取现有 archive output，并写入：

```text
output/coursework_2_stage4_v2_archive/process_summary.csv
output/coursework_2_stage4_v2_archive/per_leg_summary.csv
output/coursework_2_stage4_v2_archive/archive_manifest.json
```

## 后续合入 main 的建议

不要把这个 branch 整体 merge 到最新 `main`。

这个 branch 的价值是归档证据，不是提供未来 main 的项目结构。后续如果需要把 CA2 留档内容带回 `main`，建议只 cherry-pick 或手动 copy 以下内容：

```text
README.md
strategies/team01_v2.py
scripts/run_coursework_2_stage4_archive_matrix.py
output/coursework_2_stage4_v2_archive/
```

其中 `output/coursework_2_stage4_v2_archive/` 如果被 `.gitignore` 忽略，提交时需要使用：

```powershell
git add -f output/coursework_2_stage4_v2_archive/
```

不建议带回 `main` 的内容：

```text
旧 framework/
旧 DATA/
旧 output/ca3_stage2_presubmission_*/
旧 scripts/combo/
旧 scripts/cross_asset_scan/
旧 scripts/data/
旧 scripts/distribution/
旧 scripts/maintenance/
旧 generic-combo output
```

核心原则：summary branch 是证据仓库，不是未来 main 的结构来源。
