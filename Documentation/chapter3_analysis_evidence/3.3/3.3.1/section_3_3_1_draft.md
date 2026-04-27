# Section 3.3.1 Draft Text

Figure 3.3.1a shows that the V3 portfolio delivered a stronger Part 3 equity curve than V2 while also keeping a materially shallower underwater profile. Using the same restored Part 3 dataset, V2 finished at GBP 1,130,900.67 with a true PD of 1.3152, whereas V3 finished at GBP 1,210,964.70 with a true PD of 8.2884. The drawdown evidence is equally important: V2 reached its deepest loss on 2075-10-25, falling GBP 99,530.89 (9.93%) from the previous peak on 2075-08-06, and it needed 401 trading days to recover. By contrast, V3 bottomed on 2076-03-27 with a much smaller drawdown of GBP 25,452.94 (2.49%) from its 2076-02-03 peak and recovered within 100 trading days.

The event-window figures explain why the two equity curves behaved differently. Figure 3.3.1b shows that the V2 trough was concentrated in the TF leg: the nearest pre-trough action occurred on 2075-10-20, when the strategy filled `SELL series_1 fill_size=7717.0000 fill_px=22.5700`, yet the portfolio still fell into its trough on 2075-10-25 with little support from the other legs. This is consistent with V2's higher activity rate of 90.3% and suggests that repeated trend-following adjustments did not meaningfully reduce risk during the sell-off. Figure 3.3.1c shows a different pattern for V3: the deepest drawdown was tied mainly to a single MR09 short initiated on 2076-03-26 and then covered on 2076-04-02. In other words, V3 still experienced a losing episode, but the loss was narrower in depth, shorter in duration, and easier to attribute to one contained position rather than to a broad portfolio-level loss of control.

If you want a more visual drawdown-focused presentation in the main text, Figure 3.3.1d can be cited alongside Figure 3.3.1a. It zooms directly into the worst underwater window for each version and makes the contrast easier to see: V2's loss was both deeper and much slower to recover, whereas V3's worst episode stayed comparatively shallow and normalized more quickly.

References:
- Figure 3.3.1a: [figures/figure_3_3_1a_part3_equity_drawdown_comparison.png](figures/figure_3_3_1a_part3_equity_drawdown_comparison.png)
- Figure 3.3.1b: [figures/figure_3_3_1b_v2_drawdown_event_window.png](figures/figure_3_3_1b_v2_drawdown_event_window.png)
- Figure 3.3.1c: [figures/figure_3_3_1c_v3_drawdown_event_window.png](figures/figure_3_3_1c_v3_drawdown_event_window.png)
- Figure 3.3.1d: [figures/figure_3_3_1d_zoomed_drawdown_windows.png](figures/figure_3_3_1d_zoomed_drawdown_windows.png)
- Table 3.3.1: [part3_max_drawdown_summary.csv](part3_max_drawdown_summary.csv)
- Appendix evidence: [part3_max_drawdown_window.csv](part3_max_drawdown_window.csv)
