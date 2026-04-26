# Section 3.6 Final Report Version

## 3.6.1 Comparison of Equity Curve and Drawdown Results

This subsection directly compares the evidence developed earlier in Section 3.3.1 for V2 and Section 3.5.3 for V3. The contrast is clear. V2 finished Part 3 at GBP 1,130,900.67 and experienced a maximum drawdown of 9.93%, with recovery requiring 401 trading days. V3, by contrast, finished at GBP 1,210,964.70, limited its worst drawdown to 2.49%, and recovered within only 100 trading days. When the Section 3.3.1 drawdown evidence is read together with the Section 3.5.3 V3 profile, the conclusion is that the refined strategy achieved not only a higher terminal value, but also a materially shallower and shorter worst-case loss episode. Table 3.6.1 condenses that paired comparison into one return-risk view.

## 3.6.2 Comparison of Leg Contribution and Structural Behaviour

This subsection combines the structural weakness identified in Section 3.3.2 with the V3-only evidence from Section 3.5.4. In V2, the portfolio preserved the fixed combination of TF on `series_1`, MR on `series_10`, and GARCH on `series_7`, even though MR10 deteriorated from an OOS true PD ratio of 1.213 to a Part 2 true PD ratio of -0.898, while GARCH07 remained weak in both OOS and Part 2 evidence. V3 revised that structure by retaining TF on `series_1`, replacing MR10 with MR09, and removing the GARCH leg altogether. This revision made the final portfolio more evidence-driven and more deployable under Part 3 conditions. However, when the realised leg-contribution evidence from Sections 3.3.2 and 3.5.4 is compared side by side, the diversification problem remains visible: the top-leg share rose from 84.71% in V2 to 99.13% in V3. Table 3.6.2 therefore supports a balanced conclusion: V3 improved structural design quality, but not realised balance across return sources.

## 3.6.3 Comparison of Exposure Control and Execution Discipline

This subsection compares the capital-pressure evidence from Section 3.3.3 with the V3 control evidence from Section 3.5.5. V2 operated with high activity at 90.30%, average gross exposure of 46.83%, 62 days above 95% gross exposure, 170 multi-order days, and 148 duplicate same-series rebalancing days. By contrast, V3 reduced activity to 53.30%, lowered average gross exposure to 16.72%, eliminated all days above 95% gross exposure, and removed duplicate same-series rebalancing altogether. Read together, Sections 3.3.3 and 3.5.5 show that the difference was not cosmetic. V3 replaced reactive overspend prevention with explicit portfolio-level control through dynamic allocation, `gross_cap=1.00`, rebalance tolerance, and loss-freeze logic. Table 3.6.3 summarises this operational improvement clearly.

## 3.6.4 Comparison of Common Performance Metrics

The final comparison brings together the summary conclusions from Section 3.3.5 and Section 3.5.6. Across the standard metrics, V3 dominated V2 on both return quality and execution quality. It achieved a higher true PD ratio of 8.2884 versus 1.3152, a higher Sharpe ratio of 1.56 versus 0.63, a higher Sortino ratio of 2.20 versus 0.93, a higher win rate of 61.70% versus 49.09%, and a higher profit factor of 3.41 versus 1.76. The summary metrics therefore confirm the same message already seen in the paired subsection evidence above: Team01 V3 was a materially stronger Part 3 trading system than Team01 V2. The only important qualification is that stronger performance should not be mistaken for full structural robustness, because the final V3 outcome remained even more concentrated in one dominant trend-following leg.

References:
- Table 3.6.1: [v2_v3_return_risk_comparison.csv](v2_v3_return_risk_comparison.csv)
- Table 3.6.2: [v2_v3_structure_mapping_comparison.csv](v2_v3_structure_mapping_comparison.csv)
- Table 3.6.3: [v2_v3_execution_exposure_comparison.csv](v2_v3_execution_exposure_comparison.csv)
- Table 3.6.4: [v2_v3_change_summary.csv](v2_v3_change_summary.csv)
- Optional image export: [figures/figure_3_6_1_return_risk_comparison.png](figures/figure_3_6_1_return_risk_comparison.png)
- Optional image export: [figures/figure_3_6_2_structure_mapping_comparison.png](figures/figure_3_6_2_structure_mapping_comparison.png)
- Optional image export: [figures/figure_3_6_3_execution_exposure_comparison.png](figures/figure_3_6_3_execution_exposure_comparison.png)
- Optional image export: [figures/figure_3_6_4_change_summary.png](figures/figure_3_6_4_change_summary.png)
