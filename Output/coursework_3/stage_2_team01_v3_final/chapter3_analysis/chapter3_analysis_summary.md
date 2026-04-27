# Coursework 3 Chapter 3 Analysis Pack

This folder was generated from the archived summary branches for Coursework 1, 2, and 3. It is designed to give Chapter 3 stronger evidence than a single `run_summary.json`.

## Files

- `portfolio_progression_v1_v2_v3.csv`: portfolio-level path from Part 1 to Part 3 for V1, V2, and V3.
- `part3_version_comparison.csv`: direct Part 3 comparison across V1, V2, and V3.
- `part3_leg_breakdown_v1_v2_v3.csv`: Part 3 leg-level contribution and drawdown evidence.
- `part3_concentration_summary.csv`: concentration and activity summary for Part 3.
- `asset_reassignment_evidence.csv`: cross-asset evidence for why CA3 moved away from fixed V2 bindings.
- `structure_controls_comparison.csv`: structural and risk-control differences across V1, V2, and V3.

## Section Mapping

### 3.2 Team01 V2 Performance on Part 3

- `part3_version_comparison.csv` shows that submitted V2 ended Part 3 at GBP 1,130,900.67, below V1's GBP 1,195,196.46, with a weaker true PD ratio (1.3152 vs 2.6626).
- `portfolio_progression_v1_v2_v3.csv` also shows the V2 path across datasets: true PD moved from -0.6922 in Part 1 to 2.2440 in Part 2, then to 1.3152 in Part 3, so the submitted strategy improved after Part 1 but did not become uniformly strong.

### 3.3 Limitations Identified in Team01 V2

- `part3_leg_breakdown_v1_v2_v3.csv` and `part3_concentration_summary.csv` show that V2 Part 3 was mainly carried by `series_1` (`tf`), which contributed 84.71% of absolute leg PnL.
- `asset_reassignment_evidence.csv` shows why fixed asset binding remained a problem in V2: MR10 had OOS true PD 1.2131 and Part 2 true PD -0.8983, while GARCH07 had OOS true PD -0.5051 and Part 2 true PD -0.6419.
- The same file also shows why pure OOS optimisation was not enough: MR06 had the highest MR OOS true PD at 2.9666, but its Part 2 true PD dropped to -0.5799; GARCH05 had OOS true PD 2.8394, but Part 2 true PD -0.9103.

### 3.4 Lessons from Team01 V2 Evaluation

- `portfolio_progression_v1_v2_v3.csv` supports the point that transferability matters more than isolated in-sample strength.
- `asset_reassignment_evidence.csv` can be cited to show that cross-asset reassessment was necessary because high OOS rows did not always survive Part 2 validation.

### 3.5 Team01 V3 Performance on Part 3

- `part3_version_comparison.csv` shows that V3 finished Part 3 at GBP 1,210,964.70, with true PD 8.2884 and activity 53.30%.
- Relative to V2, V3 improved final value by GBP 80,064.04, improved true PD by 6.9732, and reduced activity by -37.00 percentage points.
- `portfolio_progression_v1_v2_v3.csv` also shows the CA3 pattern clearly: V3 stayed weak in Part 1 (-0.5153), then improved in Part 2 (2.2075), and became strongest in Part 3 (8.2884).

### 3.6 Key Changes Introduced in Team01 V3

- `asset_reassignment_evidence.csv` shows that MR09, chosen in V3, had better OOS/FULL evidence than MR10 (2.3510 / 4.4540 vs 1.2131 / 4.2700).
- `structure_controls_comparison.csv` documents the move from static three-leg weights in V2 to dynamic two-leg allocation in V3, including performance-aware budgeting, loss freezes, gross exposure cap, and rebalance tolerance.

### 3.7 Overall Lessons from Part 3

- `part3_concentration_summary.csv` shows that V3 was stronger than V2, but it was still TF-led: `series_1` accounted for 99.13% of absolute leg PnL.
- This means the Chapter 3 conclusion can stay balanced: CA3 improved risk-adjusted performance and control quality, but the final strategy was still not evenly supported by every leg.
