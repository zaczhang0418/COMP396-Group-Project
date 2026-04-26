# Section 3.3.1 Draft Text

Figures 3.3.1a and 3.3.1d jointly show that Team01 V3 delivered a stronger and more resilient Part 3 equity profile than Team01 V2. On the restored Part 3 dataset, V2 finished at GBP 1,130,900.67 with a true PD ratio of 1.3152, whereas V3 finished at GBP 1,210,964.70 with a true PD ratio of 8.2884. The difference is even clearer in the drawdown evidence. As shown in Figure 3.3.1d, V2 entered its deepest drawdown after the peak on 2075-08-06 and reached a trough on 2075-10-25, implying a loss of GBP 99,530.89, or 9.93% of peak equity. Recovery was also slow, requiring 401 trading days to regain the previous high. By contrast, V3 peaked on 2076-02-03 and reached its worst trough on 2076-03-27, but the drawdown was limited to GBP 25,452.94, or 2.49%, and the portfolio recovered within 100 trading days. Figure 3.3.1d is therefore the clearest visual summary of the section's main result: V3 not only produced higher terminal value, but also experienced a materially shallower and shorter worst-case loss episode.

Figures 3.3.1b and 3.3.1c help explain why the two drawdown paths differed. In V2, the nearest pre-trough action occurred on 2075-10-20, when the strategy filled `SELL series_1 fill_size=7717.0000 fill_px=22.5700`, yet the portfolio still moved into its trough on 2075-10-25 with little effective support from the other legs. This is consistent with V2's higher activity rate of 90.3% and suggests that repeated trend-following adjustments did not materially reduce downside risk during the sell-off. In V3, the deepest drawdown was associated mainly with a single MR09 short initiated on 2076-03-26 and covered on 2076-04-02. Although V3 still experienced a losing episode, Figures 3.3.1c and 3.3.1d show that the loss was narrower in depth, shorter in duration, and easier to attribute to one contained position rather than to a broader failure of portfolio control.

References:
- Figure 3.3.1a: [figures/figure_3_3_1a_part3_equity_drawdown_comparison.png](figures/figure_3_3_1a_part3_equity_drawdown_comparison.png)
- Figure 3.3.1b: [figures/figure_3_3_1b_v2_drawdown_event_window.png](figures/figure_3_3_1b_v2_drawdown_event_window.png)
- Figure 3.3.1c: [figures/figure_3_3_1c_v3_drawdown_event_window.png](figures/figure_3_3_1c_v3_drawdown_event_window.png)
- Figure 3.3.1d: [figures/figure_3_3_1d_zoomed_drawdown_windows.png](figures/figure_3_3_1d_zoomed_drawdown_windows.png)
- Table 3.3.1: [part3_max_drawdown_summary.csv](part3_max_drawdown_summary.csv)
- Appendix evidence: [part3_max_drawdown_window.csv](part3_max_drawdown_window.csv)
