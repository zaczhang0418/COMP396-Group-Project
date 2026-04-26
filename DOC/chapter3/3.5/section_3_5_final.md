# Section 3.5 Final Report Version

## 3.5.1 Expected Performance of Team01 V3

Team01 V3 was expected to improve on the submitted V2 strategy because it directly addressed the main weaknesses identified in Chapter 3.3. First, the strategy-asset mapping was reassessed through cross-asset testing, which retained TF on `series_1` but replaced the earlier MR10 leg with MR09. Second, V3 introduced stronger portfolio-level controls, including dynamic allocation, performance-aware budgeting, a gross exposure cap, rebalance tolerance, and loss-freeze logic. These changes meant that V3 was expected not only to improve return, but also to show better capital discipline, lower execution pressure, and stronger adaptability under unseen Part 3 conditions.

## 3.5.2 Observed V3 Results on Part 3

The observed Part 3 results support that expectation. Team01 V3 finished Part 3 with a final portfolio value of GBP 1,210,964.70, a true PD ratio of 8.2884, and an open PnL PD ratio of 9.09. The strategy did not become bankrupt, and its activity level remained moderate at 53.30%. These headline outcomes indicate that the CA3 refinement was deployable on unseen data and that the revised design remained active without relying on the excessive trading pressure that had characterised the weaker baseline.

## 3.5.3 Equity Curve and Drawdown Analysis

Figure 3.5.3 shows that V3 maintained a comparatively smooth Part 3 equity path and a controlled underwater profile. The strategy reached its local peak on 2076-02-03 and recorded its deepest drawdown on 2076-03-27, but the maximum loss was limited to 2.49% and recovery required only 100 trading days. The drawdown episode was therefore meaningful but contained. The evidence suggests that V3 could absorb a losing sequence without developing the prolonged underwater behaviour that would normally undermine confidence in live deployment.

## 3.5.4 Leg Contribution and Structural Behaviour

Figure 3.5.4 shows that V3's Part 3 performance was structurally simple but not fully balanced. Only two legs were active, and the TF leg on `series_1` dominated the realised contribution profile. The top leg accounted for 99.13% of absolute leg PnL, while the effective leg count was only 1.02. This means that V3's success should be interpreted carefully. The revised mapping improved deployability and reduced reliance on historically fixed assets, but the final result was still overwhelmingly driven by one main return engine rather than by evenly distributed support across multiple legs.

## 3.5.5 Exposure Control and Execution Discipline

The clearest operational improvement in V3 was its stronger exposure control. Figure 3.5.5 shows that gross exposure remained moderate across Part 3, with average gross exposure of 16.72% and no trading days above 95% gross exposure. Order pressure was also restrained: the strategy recorded only 11 multi-order days and no duplicate same-series rebalancing days. This is consistent with the intended role of the V3 control framework. By combining desired allocations before execution, scaling them under `gross_cap=1.00`, and applying rebalance tolerance, V3 avoided the capital over-commitment pressure that had previously weakened the baseline system.

## 3.5.6 Summary of Common Performance Metrics

Table 3.5.6 consolidates the main performance indicators for V3. In return-risk terms, the strategy combined positive total and annualised returns with controlled volatility, a Sharpe ratio of 1.56, a Sortino ratio of 2.20, and a Calmar ratio of 2.28. In execution terms, it completed 47 closed trades with a win rate of 61.70% and a profit factor of 3.41. Taken together, these metrics support a positive evaluation of Team01 V3 on Part 3: the CA3 refinement produced a strategy that was profitable, more controlled, and operationally more robust, although its final return profile still remained highly concentrated in the trend-following leg.

References:
- 3.5.1 table: [v3_expected_design_summary.csv](v3_expected_design_summary.csv)
- 3.5.2 table: [v3_observed_part3_results.csv](v3_observed_part3_results.csv)
- 3.5.3 figure: [figures/figure_3_5_3_v3_equity_drawdown_profile.png](figures/figure_3_5_3_v3_equity_drawdown_profile.png)
- 3.5.4 figure: [figures/figure_3_5_4_v3_leg_contribution.png](figures/figure_3_5_4_v3_leg_contribution.png)
- 3.5.5 figure: [figures/figure_3_5_5_v3_exposure_control.png](figures/figure_3_5_5_v3_exposure_control.png)
- 3.5.6 table: [v3_common_performance_metrics.csv](v3_common_performance_metrics.csv)
- Optional 3.5.6 image export: [figures/figure_3_5_6_v3_common_metrics_table.png](figures/figure_3_5_6_v3_common_metrics_table.png)
