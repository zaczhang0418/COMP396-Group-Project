# Part 3 Drawdown Event Analysis

This file is designed for Chapter 3.3.1. It ties the equity/drawdown story to concrete Part 3 dates and same-day strategy reactions.

## Key Findings

- V2 reached its deepest Part 3 drawdown on 2075-10-25, falling 99530.89 from the prior peak on 2075-08-06.
- The nearest pre-trough V2 action was on 2075-10-20: SELL series_1 fill_size=7717.0000 fill_px=22.5700.
- The first post-trough V2 action was on 2075-11-15: SELL series_1 size=8505.0000.
- V3 reached its deepest Part 3 drawdown on 2076-03-27, falling 25452.94 from the prior peak on 2076-02-03.
- The nearest pre-trough V3 action was on 2076-03-26: SELL series_9 fill_size=4990.0000 fill_px=112.1250.
- The first post-trough V3 action was on 2076-04-02: BUY series_9 size=4990.0000.
- V2 ended Part 3 with true PD 1.3152 and activity 90.30%.
- V3 ended Part 3 with true PD 8.2884 and activity 53.30%.

## Files

- `v2_part3_bar_trace.csv`: date-level V2 trace with equity, drawdown, signal state, positions, and submitted / filled orders.
- `v3_part3_bar_trace.csv`: date-level V3 trace with equity, drawdown, active weights, signal state, freeze/cooldown state, and orders.
- `part3_max_drawdown_summary.csv`: one-row summary per version for the deepest drawdown window.
- `part3_max_drawdown_window.csv`: +/- 5 trading days around each version's deepest drawdown trough.
- `part3_run_summaries.json`: rerun summary metrics for V2 and V3 on restored PART3 data.

## How To Use In 3.3.1

- Use `part3_max_drawdown_summary.csv` to state the exact peak date, trough date, drawdown depth, and recovery speed.
- Use `part3_max_drawdown_window.csv` to describe what the strategy did around the drawdown: whether it queued exits, reduced exposure, or stayed concentrated in one leg.
- Use the full `v2_part3_bar_trace.csv` and `v3_part3_bar_trace.csv` when you want to justify wording such as 'TF remained dominant', 'MR contribution was weak', or 'V3 cut risk through lower activity and tighter control logic'.
