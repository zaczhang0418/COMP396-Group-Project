# Section 3.3 Final Report Version

## 3.3 Team01 V2 Performance on Part 3

Section 3.3 evaluates the submitted Team01 V2 strategy on Part 3 and explains why its performance was not sufficiently convincing as a final deployable portfolio. The weakness was not limited to one isolated output statistic. Instead, the Part 3 evidence shows a connected pattern across four layers: unstable drawdown behaviour, hard-bound asset selection, uneven realised contribution across legs, and persistent capital over-commitment. Read together, these results explain why the later V3 refinement was necessary.

## 3.3.1 Equity Curve and Drawdown Analysis

The drawdown evidence shows that V2 was materially less resilient than the later refined design. As documented in [3.3.1](3.3.1), V2 finished Part 3 at GBP 1,130,900.67 with a true PD ratio of 1.3152, but its worst loss episode was deep and prolonged. After peaking on 2075-08-06, the portfolio fell to a trough on 2075-10-25, losing GBP 99,530.89, or 9.93% of peak equity, and it required 401 trading days to recover. This matters because the drawdown pattern was not offset by the rest of the portfolio structure. Near the trough, the strategy was still reacting through repeated trend-following adjustments in `series_1`, yet those actions did not materially reduce downside pressure. The main lesson from Section 3.3.1 is therefore that V2 could remain active during stress, but not sufficiently resilient.

## 3.3.2 Asset Hard Binding and Uneven Leg Contribution

The structural diagnosis in [3.3.2](3.3.2) explains why the portfolio was not convincing at the design level. First, V2 preserved inherited asset choices even when transfer evidence had weakened. MR10 achieved an OOS true PD ratio of 1.2131 but fell to -0.8983 on Part 2, while GARCH07 was weak in both OOS and Part 2 evidence. This supports the view that V2 suffered from asset hard binding rather than from an entirely impossible asset universe. Second, the realised Part 3 contribution profile was much less diversified than the three-leg structure implied. The TF leg accounted for 84.71% of absolute leg PnL, leaving an effective leg count of only 1.37. In practical terms, V2 looked multi-leg in construction, but not in realised return support. This means the portfolio was weak both in how it selected assets and in how it actually distributed performance across them.

## 3.3.3 Overspending Pressure and Capital Over-Commitment

The execution evidence in [3.3.3](3.3.3) shows that the V2 weakness was also operational. The issue is best described as persistent capital over-commitment rather than literal bankruptcy. V2 recorded average gross exposure of 46.83%, a 95th-percentile gross exposure of 99.39%, and 62 trading days above 95% gross exposure. It also generated 170 multi-order days and 148 duplicate same-series rebalancing days. These figures show that the strategy was repeatedly operating close to the full-capital boundary while still churning orders within already tight budget conditions. The underlying reason was structural: each leg adjusted through independent `order_target_percent` calls under static leg weights, but there was no explicit portfolio-level gross cap to coordinate total exposure. The framework overspend guard acted only as a reactive negative-cash blocker, not as a proactive allocation control. As a result, V2 displayed both weak capital discipline and unnecessary order pressure.

## 3.3.5 Summary of Common Performance Metrics

The summary metrics in [3.3.5](3.3.5) confirm the same story in compact quantitative form. Relative to the later V3 refinement, V2 delivered weaker terminal value, weaker total and annualised returns, lower Sharpe and Sortino ratios, a much larger maximum drawdown, and a much slower recovery. It was also less efficient operationally, with more trades, a lower win rate, a lower profit factor, more near-full-gross episodes, and much heavier same-series rebalancing pressure. The one important caution carried through to the later comparison is that stronger performance alone does not imply full structural robustness; however, Section 3.3 makes clear that V2 was already unconvincing before that later caveat was even considered.

Taken together, the evidence in Section 3.3 supports a clear diagnosis of Team01 V2 on Part 3. The submitted strategy was not weak because of one unlucky regime or one bad metric. It was weakened by a combination of low drawdown resilience, static asset binding, thin realised diversification, and persistent over-commitment of capital. These findings provide the analytical foundation for the later Chapter 3.5 V3 evaluation and Chapter 3.6 paired comparison.

References:
- 3.3.1 pack: [3.3.1](3.3.1)
- 3.3.2 pack: [3.3.2](3.3.2)
- 3.3.3 pack: [3.3.3](3.3.3)
- 3.3.5 pack: [3.3.5](3.3.5)
- Section guide: [section_3_3_reference_pack.md](section_3_3_reference_pack.md)
