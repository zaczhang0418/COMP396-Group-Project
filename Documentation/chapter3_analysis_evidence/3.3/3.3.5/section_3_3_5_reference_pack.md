# Section 3.3.5 Reference Pack

This folder contains a final-report-style summary for Section 3.3.5. The goal of this section is to consolidate the earlier findings from 3.3.1 to 3.3.3 into a compact set of commonly used return, risk, and execution metrics.

## Recommended Main-Text Use

The strongest layout for the main text is table-driven:

1. Use Table 3.3.5a as the primary quantitative comparison of return and risk.
2. Use Table 3.3.5b as a supplementary table for trade quality, capital pressure, and structural concentration.

## Suggested Main-Text Tables

- Table 3.3.5a: `summary_performance_metrics.csv`
- Table 3.3.5b: `summary_execution_metrics.csv`

## Optional Figure Exports

- `figures/figure_3_3_5a_summary_performance_table.png`
- `figures/figure_3_3_5b_summary_execution_table.png`

These PNGs are image versions of the same tables and can be inserted directly into the report if you prefer not to rebuild the layout manually in Word.

## Interpretation To Emphasise

- V3 dominates V2 on the standard return-risk metrics: higher terminal value, higher annualized return, higher Sharpe and Sortino, lower drawdown, and faster recovery.
- V3 also dominates V2 on execution discipline: fewer trades, higher win rate, higher profit factor, no days near full gross commitment, and far fewer multi-order events.
- The one balanced caveat is that concentration did not improve: V3 still relied more heavily on a single dominant leg than V2.
