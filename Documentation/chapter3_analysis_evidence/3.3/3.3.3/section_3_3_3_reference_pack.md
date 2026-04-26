# Section 3.3.3 Reference Pack

This folder contains the evidence pack for Chapter 3.3.3 on overspending pressure and capital over-commitment.

## Recommended Framing

The strongest phrasing for this section is not that V2 literally bankrupted the portfolio in Part 3, because it did not. A more accurate framing is that V2 created persistent overspending pressure by repeatedly pushing gross exposure close to the full-capital boundary while also generating frequent multi-order and duplicate rebalance events. V3 reduced this pressure through explicit gross-cap control and fewer same-day reallocation events.

## Suggested Main-Text Figures

1. Figure 3.3.3a: [Gross exposure pressure](figures/figure_3_3_3a_gross_exposure_pressure.png)
   Why to use it: this directly shows that V2 spent far more time near full capital commitment than V3.

2. Figure 3.3.3b: [Order-pressure summary](figures/figure_3_3_3b_order_pressure_summary.png)
   Why to use it: this quantifies the operational side of overspending pressure through multi-order and duplicate same-series days.

3. Figure 3.3.3c: [V2 over-commitment window](figures/figure_3_3_3c_v2_overcommitment_window.png)
   Why to use it: this gives a concrete local example of repeated same-series rebalancing while capital usage was already elevated.

## Suggested Main-Text Tables

- Table 3.3.3a: [overspending_pressure_summary.csv](overspending_pressure_summary.csv)
- Table 3.3.3b: [overspending_event_examples.csv](overspending_event_examples.csv)

## Numbers Most Worth Citing

- V2 average gross exposure: 46.83%
- V2 95th-percentile gross exposure: 99.39%
- V2 days above 95% gross: 62
- V2 multi-order days: 170
- V2 duplicate same-series days: 148
- V3 average gross exposure: 16.72%
- V3 95th-percentile gross exposure: 54.31%
- V3 days above 95% gross: 0
- V3 multi-order days: 11
- V3 duplicate same-series days: 0

## Cause Analysis To Emphasise

1. In V2, each leg targeted its own percentage independently, but there was no explicit portfolio-level gross cap.
2. The framework overspend guard only blocks orders if forecast next-open cash would turn negative, so it acts as a last-resort safety check rather than a strategic budget allocator.
3. In V3, desired allocations are first combined and then scaled back under `gross_cap=1.00`, with `rebalance_tol=0.015` further reducing unnecessary churn.
