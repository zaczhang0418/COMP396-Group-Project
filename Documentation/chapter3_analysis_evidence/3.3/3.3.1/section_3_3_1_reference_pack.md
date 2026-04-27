# Section 3.3.1 Reference Pack

This folder contains the evidence pack for Chapter 3.3.1 on Part 3 equity curve and drawdown behaviour.

## Where The Original Analysis Output Lives

- Main analysis output: `Output/coursework_3/stage_3_chapter3_evidence/part3_drawdown_analysis/`
- This documentation pack: `Documentation/chapter3_analysis_evidence/3.3/3.3.1/`

## Suggested Main-Text Figures

1. Figure 3.3.1a: [Part 3 equity and drawdown comparison](figures/figure_3_3_1a_part3_equity_drawdown_comparison.png)
   Data source: `Output/coursework_3/stage_3_chapter3_evidence/part3_drawdown_analysis/v2_part3_bar_trace.csv` and `Output/coursework_3/stage_3_chapter3_evidence/part3_drawdown_analysis/v3_part3_bar_trace.csv`
   Why to use it: this is the cleanest one-chart comparison showing that V3 both compounded more and stayed shallower underwater than V2.

2. Figure 3.3.1b: [V2 drawdown event window](figures/figure_3_3_1b_v2_drawdown_event_window.png)
   Data source: `Output/coursework_3/stage_3_chapter3_evidence/part3_drawdown_analysis/v2_part3_bar_trace.csv`
   Why to use it: this isolates the V2 peak-to-trough sequence and shows that the deepest loss phase was carried mainly by the TF leg while the other legs were largely inactive.

3. Figure 3.3.1c: [V3 drawdown event window](figures/figure_3_3_1c_v3_drawdown_event_window.png)
   Data source: `Output/coursework_3/stage_3_chapter3_evidence/part3_drawdown_analysis/v3_part3_bar_trace.csv`
   Why to use it: this shows that V3's deepest drawdown was shorter and linked mainly to a single MR09 short, not a broad multi-leg failure.

4. Figure 3.3.1d: [Zoomed max-drawdown windows](figures/figure_3_3_1d_zoomed_drawdown_windows.png)
   Data source: `Output/coursework_3/stage_3_chapter3_evidence/part3_drawdown_analysis/v2_part3_bar_trace.csv`, `v3_part3_bar_trace.csv`, and `part3_max_drawdown_summary.csv`
   Why to use it: this is the best figure for visually comparing the depth, duration, and recovery speed of the worst drawdown episode in each version.

## Suggested Main-Text Table

Table 3.3.1 should use [part3_max_drawdown_summary.csv](part3_max_drawdown_summary.csv).

Recommended fields to cite:
- V2 peak date `2075-08-06` and trough date `2075-10-25`
- V2 max drawdown `GBP 99,530.89` or `9.93%`
- V2 recovery in `401` trading days
- V3 peak date `2076-02-03` and trough date `2076-03-27`
- V3 max drawdown `GBP 25,452.94` or `2.49%`
- V3 recovery in `100` trading days

## Optional Appendix Items

- [part3_max_drawdown_window.csv](part3_max_drawdown_window.csv)
  Use this when you want line-by-line evidence for the +/- 5 trading days around each trough.

- `Output/coursework_3/stage_2_team01_v3_final/team01_v3_final/part3/equity_dashboard_combined.png`
  This is still useful as a fuller single-version dashboard for V3, but it is better as appendix support than as the main comparative figure.

- `Output/coursework_3/stage_2_team01_v3_final/team01_v3_final/part3/portfolio_underwater.png`
  This is useful if you want a standalone V3 underwater chart, again mainly as appendix material.

## Core Numbers For 3.3.1

- V2 final portfolio value: GBP 1,130,900.67
- V2 true PD: 1.3152
- V2 activity: 90.3%
- V3 final portfolio value: GBP 1,210,964.70
- V3 true PD: 8.2884
- V3 activity: 53.3%
