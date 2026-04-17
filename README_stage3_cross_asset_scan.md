# Stage 3: Cross-Asset Scan And Optimized Team Strategy Archive

This branch archives the Stage 3 workflow: using the generic single-strategy framework from Stage 1 to run a cross-asset scan, then using that evidence to redesign the final `team01.py` strategy.

## Archive Status

- Branch role: Stage 3 cross-asset scan and optimized team strategy.
- Original remote branch: `origin/cross-asset-scan`.
- Target archive branch name: `coursework_3/stage-3-cross-asset-scan`.
- Stage tag: `stage3-cross-asset-optimized`.
- Key commits:
  - `ac73f40`: completed the 3 strategies x 10 assets cross scan workflow.
  - `3b3d6e5`: archived the optimized Team 01 strategy.

## Why This Stage Matters

Stage 2 produced a practical presubmission baseline:

```text
TF    -> series_1
MR    -> series_10
GARCH -> series_7
```

Stage 3 asked a more systematic question:

```text
If Stage 1 made TF, MR, and GARCH generic, why should each strategy remain tied to its original asset?
```

This branch therefore moved from manual asset selection to a data-driven asset-strategy assignment process. The goal was not only to tune parameters, but to decide which strategy family belonged on which asset and whether all three original legs still deserved capital.

## Cross-Asset Scan Pipeline

The scan pipeline is implemented in:

```text
scripts/cross_asset_scan/common.py
scripts/cross_asset_scan/run_cross_asset_scan.py
scripts/cross_asset_scan/summarize_cross_asset_scan.py
scripts/cross_asset_scan/validate_cross_asset_scan_part2.py
```

Default scan design:

| Dimension | Values |
| --- | --- |
| Strategy families | `tf`, `mr`, `garch` |
| Strategy implementations | `tf_generic_v1`, `mr_generic_v1`, `garch_generic_v1` |
| Assets | `asset01` to `asset10` |
| Default scan tag | `cross_asset_scan_v1` |
| Selection mode | `robust` |
| Primary metric | `true_pd_ratio` |
| Part 1 splits | IS `70-30`, OOS `30-oos`, FULL `100-full` |

The pipeline was designed to produce:

```text
output/cross_asset_scan_v1/summaries/cross_asset_long.csv
output/cross_asset_scan_v1/summaries/matrix_3x10.csv
output/cross_asset_scan_v1/summaries/asset_strategy_assignment.csv
output/cross_asset_scan_v1/summaries/part2_validation.csv
output/cross_asset_scan_v1/summaries/summary.json
```

These outputs are generated under `output/cross_asset_scan_v1/` and are included in this archive branch for CA3 report evidence.

## How To Reproduce The Scan

Use the project conda environment:

```powershell
C:\Python\envs\comp396\python.exe --version
```

Run the Part 1 cross-asset scan:

```powershell
C:\Python\envs\comp396\python.exe scripts\cross_asset_scan\run_cross_asset_scan.py --scan-tag cross_asset_scan_v1 --strategies all --assets all --selection-mode robust --key true_pd_ratio --runs is,oos,full --skip-existing
```

Run Part 2 validation from the selected Part 1 parameters:

```powershell
C:\Python\envs\comp396\python.exe scripts\cross_asset_scan\validate_cross_asset_scan_part2.py --scan-tag cross_asset_scan_v1 --strategies all --assets all --skip-existing
```

Build the long table, 3 x 10 matrix, and assignment table:

```powershell
C:\Python\envs\comp396\python.exe scripts\cross_asset_scan\summarize_cross_asset_scan.py --scan-tag cross_asset_scan_v1 --strategies all --assets all --matrix-metric oos_true_pd_ratio
```

## Included CA3 Output

This branch now includes the regenerated Stage 3 evidence output:

```text
output/cross_asset_scan_v1/
output/ca3_stage3_team01_part1/
output/ca3_stage3_team01_part2/
```

The cross-asset directory contains the 3 strategy families x 10 assets scan records, Part 2 validation runs, and summary matrices. The `ca3_stage3_team01_part1` and `ca3_stage3_team01_part2` directories contain final optimized `team01.py` verification runs on Part 1 and Part 2.

The most useful report evidence files are:

```text
output/cross_asset_scan_v1/summaries/summary.json
output/cross_asset_scan_v1/summaries/matrix_3x10.csv
output/cross_asset_scan_v1/summaries/cross_asset_long.csv
output/cross_asset_scan_v1/summaries/asset_strategy_assignment.csv
output/cross_asset_scan_v1/summaries/part2_validation.csv
output/ca3_stage3_team01_part1/run_summary.json
output/ca3_stage3_team01_part2/run_summary.json
```

## Optimized Team Strategy

The optimized strategy is:

```text
strategies/team01.py
```

Unlike Stage 2, it is no longer the original three-leg allocation. The final optimized mapping in this branch is:

| Leg | Data feed | Role | Base weight |
| --- | --- | --- | ---: |
| TF | `series_1` | Trend-following / leadership leg | 0.65 |
| MR09 | `series_9` | Mean-reversion leg selected after cross-asset analysis | 0.35 |

This is an important design change:

```text
Stage 2 baseline:
  TF series_1 + MR series_10 + GARCH series_7

Stage 3 optimized:
  TF series_1 + MR series_9
```

The GARCH leg is not included in the final optimized `team01.py`. The branch should therefore be described as a cross-asset redesign, not merely a parameter update.

## New Strategy Logic In Optimized `team01.py`

The optimized strategy includes several portfolio-level and signal-quality controls that were not present in the Stage 2 presubmission baseline.

### Hot Leadership / Strong-Move Filter

The TF leg includes a hot-move filter that acts like a "leadership" condition. The code does not use the literal word `leader`, but the logic is implemented through:

```text
tf_hot_enabled
tf_hot_lookback
tf_hot_entry_floor
tf_hot_gap_atr
tf_hot_jump1_atr
tf_hot_jump3_atr
_tf_hot_score()
```

It scores whether `series_1` is showing strong short-term movement relative to its own ATR:

- close above short SMA,
- positive gap versus SMA,
- positive 1-day jump,
- positive 3-day jump.

The TF leg only enters when this hot score and the broader trend score are strong enough.

### Hurst And Trend Strength Sizing

The TF leg uses:

```text
RollingHurst
_tf_score()
_tf_target_pct()
```

This links position size to trend persistence and trend strength. If Hurst/trend evidence is weak, the TF target is reduced.

### Dynamic Allocation

The strategy dynamically adjusts capital between TF and MR09 using:

```text
dynamic_alloc_enabled
dynamic_alloc_strength
_compute_active_weights()
```

It blends base weights with current signal strength, while enforcing floors and caps:

```text
tf_weight_floor / tf_weight_cap
mr_weight_floor / mr_weight_cap
```

### Performance-Aware Budgeting

The allocation also reacts to recent closed-trade performance:

```text
perf_alloc_enabled
perf_alpha
perf_scale
perf_floor_mult
perf_cap_mult
_dynamic_budget_weights()
_perf_multiplier()
```

This gives more budget to a leg that is performing well and reduces the effective budget of a weak leg, subject to floors and caps.

### Loss Freeze

The strategy tracks loss streaks:

```text
loss_freeze_after
loss_freeze_bars
notify_trade()
```

After repeated losing trades, the affected leg can be temporarily frozen before it is allowed to open new positions again.

### Exposure And Rebalance Controls

The strategy also includes:

```text
gross_cap
rebalance_tol
_maybe_rebalance()
```

This caps total gross exposure and avoids rebalancing unless the target position has moved far enough from the current position. This helps reduce unnecessary churn and addresses part of the overspend/rebalance pressure observed in the Stage 2 baseline.

### MR09 Volatility And Z-Score Filters

The MR09 leg uses:

```text
ZScore
RollingQuantile
mr09_atr_pctl_window
mr09_atr_pctl_enter
mr09_vol_relax_mult
mr09_entry_z
mr09_exit_z
mr09_max_hold_days
```

This means the mean-reversion leg only enters when the z-score signal is sufficiently stretched and the volatility regime is acceptable.

## Relationship To Stage 1

Stage 3 depends directly on Stage 1:

```text
coursework_3/stage-1-generic-single-strats
```

Stage 1 made the strategy families asset-agnostic. Stage 3 used that generic architecture to scan:

```text
3 strategy families x 10 assets
```

Without the Stage 1 refactor, the cross-asset matrix would have required manual strategy rewrites for each asset.

## Relationship To Stage 2

Stage 2 branch:

```text
coursework_3/stage-2-presubmission-team01
```

Stage 2 is the presubmission baseline. It proved that the three selected strategy ideas could be packaged into a single assignment-compliant `team01.py`, but the Part 2 rerun produced many overspend-cancellation messages and the mapping was still inherited from earlier asset-specific work.

Stage 3 improves on that by:

1. scanning all generic strategy families across all assets,
2. replacing the inherited mapping with an evidence-driven mapping,
3. simplifying the final deployed portfolio,
4. adding dynamic allocation and stronger signal-quality/risk controls.

## Report Summary

Use this wording in the report:

> Stage 3 converted the presubmission strategy from a manually assembled three-leg portfolio into a cross-asset optimized strategy. We used the generic framework from Stage 1 to scan TF, MR, and GARCH across all ten assets, then used the resulting asset-strategy evidence to redesign `team01.py` around TF on `series_1` and MR on `series_9`. The optimized file also introduced hot leadership filtering, Hurst/trend-weighted sizing, dynamic allocation, performance-aware budget adjustment, loss freezes, gross exposure caps, and rebalance thresholds.

