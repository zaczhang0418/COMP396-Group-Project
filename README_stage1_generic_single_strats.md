# Stage 1: Generic Single-Strategy Workflow Archive

本分支记录 CA3 研发流程中的 Stage 1：从早期“资产专属策略原型”过渡到“可复用、可批量验证的 generic single-strategy workflow”。

这不是最终提交策略本身，而是后续 Stage 2 presubmission strategy 和 Stage 3 cross-asset scan 的研发基础。

## 分支定位

- Branch role: Stage 1 generic single-strategy refactor.
- Cloud branch: `coursework_3/stage-1-generic-single-strats`.
- Original evidence branch: `origin/refine-single-strats`.
- Stage tag: `stage1-generic-single-strats`.
- 该分支曾通过 PR #11 合并进 `main`，本 archive branch 额外保留了 CA3 可复现 output。

## 为什么 Stage 1 重要

早期策略研发是从三个较强的单资产原型开始的：

| Strategy idea | Early branch / evidence | Original asset |
| --- | --- | --- |
| Trend-following | `origin/tr_asset01_v1` | `series_1` / asset01 |
| Mean reversion | `origin/mr_asset10_v1` | `series_10` / asset10 |
| GARCH regime/trend | `origin/gr_asset07-v1` | `series_7` / asset07 |

这个阶段的主要问题是：策略逻辑和资产身份绑定得太紧。比如 TF 策略天然写成 asset01，MR 策略天然写成 asset10，GARCH 策略天然写成 asset07。这样可以快速发现想法，但不利于 CA3 需要展示的系统性研发过程。

Stage 1 的核心优化，是把“策略思想”从“具体资产”里拆出来：

```text
asset-specific prototypes
  -> generic single-strategy implementations
  -> repeatable grid search and robust selection
  -> Part 1 IS/OOS/FULL validation
  -> Part 2 transfer test
  -> Stage 2 presubmission portfolio
  -> Stage 3 cross-asset scan
```

这一步使得同一个 TF/MR/GARCH 策略家族可以通过参数指定 `data_name`，在不同 series 上运行，而不是为每个资产复制一份策略代码。

## 主要代码产出

Generic strategy files:

```text
strategies/tf_generic_v1.py
strategies/mr_generic_v1.py
strategies/garch_generic_v1.py
```

Archived original asset-specific files:

```text
strategies/archive/tf_asset01_v1.py
strategies/archive/mr_asset10_v1.py
strategies/archive/garch_asset07_v1.py
```

Standardized grid configs:

```text
configs/grids/single_strat/tf/baseline/core4_v1.json
configs/grids/single_strat/tf/refined/refined_v1.json
configs/grids/single_strat/mr/baseline/core4_v1.json
configs/grids/single_strat/mr/refined/refined_v1.json
configs/grids/single_strat/garch/baseline/core4_v1.json
configs/grids/single_strat/garch/refined/refined_v1.json
```

Standardized timeline:

```text
configs/timeline.json
```

Single-strategy scripts:

```text
scripts/single_strat/tf/run_grid_search.py
scripts/single_strat/tf/run_once.py
scripts/single_strat/tf/pick_best.py

scripts/single_strat/mr/run_grid_search.py
scripts/single_strat/mr/run_once.py
scripts/single_strat/mr/pick_best.py

scripts/single_strat/garch/run_grid_search.py
scripts/single_strat/garch/run_once.py
scripts/single_strat/garch/pick_best.py

scripts/single_strat/common/pick_best_common.py
```

Evaluation and maintenance helpers:

```text
scripts/evaluation/compare_experiments.py
scripts/evaluation/evaluate_part1_combo_from_best.py
scripts/evaluation/evaluate_part2_from_best.py
scripts/maintenance/archive_legacy_experiment.py
scripts/common_paths.py
```

## 优化过程总结

### 1. 从资产专属策略改为 generic 策略

原始策略阶段的代码逻辑比较直观，但复用性弱：TF/MR/GARCH 都是在各自最早发现有效的资产上开发。Stage 1 重构后，策略文件不再固定交易某个 CSV，而是通过参数选择数据源。

这带来两个好处：

- 同一个策略家族可以在多个资产上复用。
- 后续实验可以由脚本批量运行，而不是人工复制和改代码。

这一步本质上是研究流程的优化，不只是策略参数的优化。

### 2. 标准化参数搜索

每个策略家族都建立了统一的 grid config 和 runner：

- TF 重点搜索 EMA short/long 和 Hurst threshold。
- MR 重点搜索 z-score lookback、entry threshold、exit threshold。
- GARCH 重点搜索 volatility quantile regime 和不同 regime 下的 exposure multiplier。

最终 Stage 1 选出的参数为：

| Strategy | Asset used in Stage 1 | Selected parameters |
| --- | --- | --- |
| TF | `series_1` | `p_ema_short=18`, `p_ema_long=50`, `p_hurst_min_soft=0.55` |
| MR | `series_10` | `p_lookback=30`, `p_entry_z=2.25`, `p_exit_z=0.0` |
| GARCH | `series_7` | `p_sigma_q_low=0.3`, `p_sigma_q_high=0.75`, `p_mult_mid=0.5`, `p_mult_high=0.2` |

对应文件：

```text
output/experiments/ca3_stage1_generic/part1/tf/asset01/grid_search/best_params.json
output/experiments/ca3_stage1_generic/part1/mr/asset10/grid_search/best_params.json
output/experiments/ca3_stage1_generic/part1/garch/asset07/grid_search/best_params.json
```

### 3. 使用 IS/OOS/FULL 结构控制过拟合

Stage 1 使用 `configs/timeline.json` 固定 Part 1 的拆分：

```text
IS:   2069-12-08 -> 2071-11-07
OOS:  2071-11-08 -> 2072-09-02
FULL: 2069-12-08 -> 2072-09-02
```

这样做的目的不是单纯追求 IS 上最高收益，而是检查策略参数是否能在 OOS 和 FULL 上继续保持可解释表现。

在 `pick_best.py` 和 `pick_best_common.py` 中，best-parameter selection 不只是保存一个最高分结果，还会生成 best runs 和 robust-selection 记录，方便后续追溯“为什么选这个参数组合”。

### 4. 把单策略结果组合成三腿 portfolio

Stage 1 最后用选出的 TF/MR/GARCH 参数跑了一个组合策略：

```text
TF     -> series_1
MR     -> series_10
GARCH  -> series_7
weights: 0.45 / 0.45 / 0.10
```

这个组合不是最终 CA2 提交文件，但它验证了一个关键想法：三类不同逻辑的 alpha 可以被合并到一个 portfolio 层面。

对应输出：

```text
output/experiments/ca3_stage1_generic/part1/combo/
output/experiments/ca3_stage1_generic/part2/combo/
```

### 5. Part 2 transfer test 检查稳定性

Stage 1 的关键验证，是把 Part 1 选出的 best parameters 直接迁移到 Part 2，不重新调参。

Part 2 transfer summary:

| Strategy | Asset | Final value | True PD ratio | Activity | Bankrupt |
| --- | --- | ---: | ---: | ---: | --- |
| TF | `series_1` | 2,667,396.07 | 0.8959 | 49.55% | false |
| MR | `series_10` | 910,043.42 | -0.8983 | 3.90% | false |
| GARCH | `series_7` | 989,246.67 | -0.6419 | 9.40% | false |
| Combo | `series_1 + series_7 + series_10` | 1,021,619.72 | 0.1359 | 81.88% | false |

对应文件：

```text
output/experiments/ca3_stage1_generic/part2/transfer_summary.csv
output/experiments/ca3_stage1_generic/part2/transfer_record.json
```

这个结果说明：

- TF leg 在 Part 2 上迁移表现非常强，是后续 portfolio 中最重要的收益来源。
- MR 和 GARCH 在原始资产映射下迁移表现较弱。
- 三腿组合没有破产，并且略微盈利，但 activity 很高，说明组合层面存在调仓压力和资金使用效率问题。

这个发现直接推动了 Stage 2 和 Stage 3 的进一步设计：Stage 2 先把三腿策略封装成 assignment-compliant `team01.py`，Stage 3 再系统性重新检查“每个策略应该配哪个资产”。

## Included Reproducible Output

本分支已经包含重新生成的 Stage 1 output：

```text
output/experiments/ca3_stage1_generic/
```

这个目录包含：

- Part 1 grid searches
- robust-selection records
- IS/OOS/FULL best runs
- combined three-leg run
- Part 2 transfer validation

最适合在 CA3 report 里引用的文件：

```text
output/experiments/ca3_stage1_generic/experiment_record.json
output/experiments/ca3_stage1_generic/part2/transfer_summary.csv
output/experiments/ca3_stage1_generic/part2/transfer_record.json
```

## 和 Stage 2 的关系

Stage 2 branch:

```text
coursework_3/stage-2-presubmission-team01
```

Stage 2 没有重新做完整单策略优化，而是把 Stage 1 选出的三个策略想法封装成符合 coursework 格式的单文件提交策略：

```text
TF generic idea    -> series_1
MR generic idea    -> series_10
GARCH generic idea -> series_7
```

也就是说，Stage 1 提供研究和参数选择框架，Stage 2 负责把它包装成可提交的 `strategies/team01.py`。

## 和 Stage 3 的关系

Stage 3 branch:

```text
coursework_3/stage-3-cross-asset-scan
```

Stage 3 依赖 Stage 1 的 generic strategy architecture。如果没有 Stage 1 的重构，就无法系统运行：

```text
3 strategy families x 10 assets
```

Stage 3 的核心问题是：既然 TF/MR/GARCH 已经 generic 化，为什么它们一定要继续绑定在最早发现它们的资产上？

因此 Stage 3 使用 cross-asset scan 重新评估策略和资产的匹配关系，并最终推动 portfolio 从 Stage 2 的：

```text
TF series_1 + MR series_10 + GARCH series_7
```

转向更简洁、更有风控控制的：

```text
TF series_1 + MR series_9
```

## 组员总结时可以强调的点

1. Stage 1 的贡献不是“最终赚钱最多”，而是把研究流程系统化。
2. Generic strategy refactor 让后续 cross-asset scan 成为可能。
3. IS/OOS/FULL 和 Part 2 transfer test 是防止过拟合的重要证据。
4. Part 2 transfer 显示 TF leg 很强，但 MR/GARCH 原始资产映射不够稳健。
5. Stage 1 的结果解释了为什么 Stage 2 可以形成三腿 baseline，也解释了为什么 Stage 3 需要重新做资产映射和风险控制。

## Useful Evidence Commands

```powershell
git log 58afc66^1..stage1-generic-single-strats --oneline --date=short --pretty=format:"%h %ad %s"
git diff --stat 58afc66^1..stage1-generic-single-strats
git diff --name-status 58afc66^1..stage1-generic-single-strats
```

If the tag is not available locally, use the archive branch:

```powershell
git log origin/coursework_3/stage-1-generic-single-strats --oneline --date=short --pretty=format:"%h %ad %s" -n 10
git diff --stat 58afc66^1..origin/coursework_3/stage-1-generic-single-strats
git diff --name-status 58afc66^1..origin/coursework_3/stage-1-generic-single-strats
```
