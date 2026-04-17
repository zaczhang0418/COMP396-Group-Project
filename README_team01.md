# Stage 2: Team 01 Presubmission Strategy Archive

本分支记录 CA3 研发流程中的 Stage 2：把 Stage 1 形成的 TF/MR/GARCH 三个 generic single-strategy idea，封装成一个符合 coursework 提交格式的 `team01.py`。

这个版本对应我们的 presubmission / CA2 baseline。它不是最终 Stage 3 cross-asset optimized strategy，而是一个重要的中间版本：它证明三类策略可以被组合成可提交、可运行、未破产的 portfolio，同时也暴露了后续需要优化的风险和执行问题。

## 分支定位

- Branch role: Stage 2 presubmission baseline.
- Cloud branch: `coursework_3/stage-2-presubmission-team01`.
- Original remote branch: `origin/presubmission-team-strategy`.
- Strategy file: `strategies/team01.py`.
- Strategy file status: confirmed identical to the final submitted desktop copy at `C:\Users\30745\Desktop\Team01 Presubmission\team01.py`.
- SHA256 for both copies: `E4FC4B65DA7834FA791FE3B846C52B8061876D0940340B1E0B5B1225570E82BF`.

## 策略结构

Stage 2 presubmission portfolio 是三腿组合：

| Leg | Data feed | Strategy idea | Default capital weight |
| --- | --- | --- | ---: |
| TF | `series_1` | EMA trend-following with ATR volatility targeting and trailing stop | 0.45 |
| MR | `series_10` | z-score mean reversion with ATR volatility targeting and stop | 0.45 |
| GARCH | `series_7` | GARCH volatility-regime trend leg with EMA filter and ATR stop | 0.10 |

它使用的资产映射是 Stage 1 之前形成的 pre-cross-asset mapping：

```text
TF generic idea    -> series_1
MR generic idea    -> series_10
GARCH generic idea -> series_7
```

这套映射来自早期单策略研发结果，而不是 Stage 3 的全资产扫描结果。因此在 CA3 报告里应把它描述为 presubmission baseline，而不是最终优化后的 portfolio。

## 从 Stage 1 到 Stage 2 的优化过程

Stage 1 完成了三件事：

- 把 TF/MR/GARCH 从资产专属版本改成 generic strategy family。
- 用 grid search 和 IS/OOS/FULL 选择参数。
- 用 Part 2 transfer test 检查 Part 1 参数是否能迁移。

Stage 2 的任务不是重新做完整研究，而是把这些研发结果包装成一个 assignment-compliant 单文件策略：

```text
Stage 1: generic strategies + grid-search output
Stage 2: self-contained team01.py submission file
```

这个包装步骤本身很重要，因为 coursework 提交要求策略能由框架直接加载运行，而不能依赖外部 JSON、实验目录或手工注入参数。因此 Stage 2 把关键参数和默认权重写进 `TeamStrategy.params`，让 `team01.py` 可以独立运行。

## 策略内部逻辑

### 1. TF leg: `series_1`

TF leg 负责捕捉趋势行情。它使用 EMA trend signal 判断方向，并通过 ATR volatility targeting 控制仓位规模。该 leg 在 Stage 1 和 Stage 2 中都是主要收益来源。

Part 2 per-series evidence:

```text
series_1 final_cumPnL = 187,487.59
series_1 pnl_pd_ratio = 3.3295
```

### 2. MR leg: `series_10`

MR leg 使用 z-score mean reversion。当价格相对近期均值偏离足够大时开仓，回归后退出。该 leg 的目标是补充趋势策略，在不同市场状态下提供反向 alpha。

Part 2 per-series evidence:

```text
series_10 final_cumPnL = 17,880.00
series_10 pnl_pd_ratio = 0.5870
```

### 3. GARCH leg: `series_7`

GARCH leg 通过 volatility-regime/trend filter 控制风险暴露。它在 Stage 2 中权重较小，主要作为 regime-sensitive diversifier。

Part 2 per-series evidence:

```text
series_7 final_cumPnL = -1,183.77
series_7 pnl_pd_ratio = -0.0407
```

这个结果也说明，GARCH leg 在 presubmission baseline 中贡献较弱，为 Stage 3 中重新评估是否保留 GARCH leg 提供了证据。

## 为什么选择三腿组合

Stage 2 的设计逻辑是组合互补：

- TF 负责趋势捕捉，是主要收益来源。
- MR 负责均值回归，尝试补充不同市场状态下的机会。
- GARCH 负责 volatility regime 过滤，作为小权重 diversifier。

默认权重是：

```text
TF = 0.45
MR = 0.45
GARCH = 0.10
```

这个权重选择较保守地给 TF/MR 主要资本，同时限制 GARCH 的影响。现在回看，GARCH 权重较低是合理的，因为它在 Part 2 和后续分析中稳定性不足。

## CA3 Verification Output

本分支已经包含 Stage 2 presubmission baseline 的标准 output：

```text
output/ca3_stage2_presubmission_part1/
output/ca3_stage2_presubmission_part2/
output/ca3_stage2_presubmission_part3_existing/
```

Part 1 和 Part 2 是从本分支重新运行生成的。Part 3 是 preserved existing presubmission output，因为本仓库没有提供 Part 3 data，无法重新跑。

主要 summary 文件：

```text
output/ca3_stage2_presubmission_part1/run_summary.json
output/ca3_stage2_presubmission_part2/run_summary.json
output/ca3_stage2_presubmission_part3_existing/run_summary.json
output/ca3_stage2_presubmission_part2/per_series_pd.json
```

## 表现总结

| Data part | Final value | True PD ratio | Open PnL PD ratio | Activity | Bankrupt |
| --- | ---: | ---: | ---: | ---: | --- |
| Part 1 | 948,298.86 | -0.6922 | -0.2841 | 67.27% | false |
| Part 2 | 1,166,853.42 | 2.2440 | 3.3408 | 81.48% | false |
| Part 3 existing | 1,130,900.67 | 1.3152 | 3.2499 | 90.30% | false |

这些结果说明：

- Stage 2 baseline 在 Part 2 和已有 Part 3 output 上都盈利且没有破产。
- Part 1 表现较弱，说明它不是简单的 Part 1 overfit。
- Part 2 和 Part 3 的 activity 很高，说明交易和调仓压力偏大。
- 该策略能作为提交 baseline，但仍有明显优化空间。

## 重要限制：Overspend cancellation

Stage 2 rerun 中出现了大量 framework overspend-cancellation messages。这个问题非常重要，不能在 CA3 报告中隐藏。

它说明：

- 三个 leg 独立产生目标仓位时，组合层面的资金竞争没有被充分控制。
- 即使每个 leg 有自己的 volatility targeting，portfolio-level allocation 仍然可能过度激进。
- 高 activity 和频繁 rebalance 增加了交易执行压力。

这正是 Stage 3 继续优化的动机之一。Stage 3 后续加入了更明确的 portfolio-level controls，例如 dynamic allocation、gross exposure cap、rebalance tolerance、loss freeze 等。

## Assignment compliance

Stage 2 的一个关键贡献是满足 coursework 提交格式：

- The submission is a single file named `team01.py`.
- The file defines exactly one Backtrader strategy class named `TeamStrategy`.
- `TeamStrategy` subclasses `bt.Strategy`.
- The parameter list is declared at the top of the class in `params`.
- All required imports are included in the file.
- The strategy does not depend on external helper scripts, JSON parameter files, or local output folders at runtime.
- The strategy is intended to be run through `main.py` in the provided framework.

## How To Run

Example Part 2 run:

```powershell
D:\Anacoda\envs\comp396\python.exe main.py --strategy team01 --data-dir .\DATA\PART2 --fromdate 2072-09-03 --todate 2075-05-30 --output-dir output\ca3_stage2_presubmission_part2
```

Example with debug logging:

```powershell
D:\Anacoda\envs\comp396\python.exe main.py --strategy team01 --data-dir .\DATA\PART2 --fromdate 2072-09-03 --todate 2075-05-30 --debug --output-dir output\ca3_stage2_presubmission_part2_debug
```

At marking time, the framework can run the same strategy on Part 3 data. No additional CLI parameter overrides are required because the strategy defaults are defined inside the file.

## 和 Stage 3 的关系

Stage 3 branch:

```text
coursework_3/stage-3-cross-asset-scan
```

Stage 2 的作用是形成一个可提交、可运行、可解释的 baseline。Stage 3 则在这个 baseline 的基础上提出进一步问题：

```text
If TF/MR/GARCH are already generic, why must they remain on series_1/series_10/series_7?
```

因此 Stage 3 做了 cross-asset scan，重新评估策略和资产的匹配关系，并最终从三腿 baseline：

```text
TF series_1 + MR series_10 + GARCH series_7
```

转向优化后的：

```text
TF series_1 + MR series_9
```

同时，Stage 3 也针对 Stage 2 暴露出的 overspend/high-activity 问题加入了更强的 portfolio-level risk controls。

## 组员总结时可以强调的点

1. Stage 2 是 CA2/presubmission baseline，不是最终 Stage 3 optimized strategy。
2. 它把 Stage 1 的 generic research outputs 封装成 assignment-compliant `team01.py`。
3. 三腿组合在 Part 2 和已有 Part 3 output 上盈利且未破产。
4. TF leg 是主要收益来源，MR 有正贡献，GARCH 在 Part 2 中贡献较弱。
5. 大量 overspend cancellation 和高 activity 是后续 Stage 3 继续优化的重要动机。
