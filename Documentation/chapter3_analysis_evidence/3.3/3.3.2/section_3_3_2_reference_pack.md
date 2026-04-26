# Section 3.3.2 Reference Pack

This folder contains the evidence pack for Chapter 3.3.2 on asset hard binding and uneven leg contribution.

## Core Questions This Section Answers

1. Did V2 keep legacy asset choices even when their transfer into Part 2 was weak?
2. Even when V3 improved performance, was the final Part 3 result still dominated by one leg rather than jointly supported across legs?

## Suggested Main-Text Figures

1. Figure 3.3.2a: [Asset-binding transfer evidence](figures/figure_3_3_2a_asset_binding_transfer.png)
   Data source: [asset_binding_transfer_summary.csv](asset_binding_transfer_summary.csv)
   Why to use it: this shows that several selected or candidate assets looked acceptable in OOS, but their Part 2 transfer quality diverged sharply, which is exactly the problem with hard binding.

2. Figure 3.3.2b: [Part 3 leg contribution shares](figures/figure_3_3_2b_part3_leg_contribution_shares.png)
   Data source: [part3_leg_breakdown_v1_v2_v3.csv](part3_leg_breakdown_v1_v2_v3.csv)
   Why to use it: this visualises how much of total absolute leg PnL came from each leg in V1, V2, and V3.

3. Figure 3.3.2c: [Concentration metrics](figures/figure_3_3_2c_concentration_metrics.png)
   Data source: [leg_contribution_concentration_metrics.csv](leg_contribution_concentration_metrics.csv)
   Why to use it: this converts the contribution story into compact quantitative indicators such as top-leg share and effective leg count.

## Suggested Main-Text Tables

- Table 3.3.2a: [asset_binding_transfer_summary.csv](asset_binding_transfer_summary.csv)
- Table 3.3.2b: [leg_contribution_concentration_metrics.csv](leg_contribution_concentration_metrics.csv)

## Most Important Numbers To Cite

- MR10, which was selected in V2, had OOS true PD 1.2131 but Part 2 true PD -0.8983.
- MR09, later adopted in V3, had OOS true PD 2.3510 and Part 2 true PD -0.1261.
- GARCH07, which remained in V2, had OOS true PD -0.5051 and Part 2 true PD -0.6419.
- GARCH09, which was not deployed, still showed a positive Part 2 true PD of 1.0070.
- V2 top-leg share was 84.71%, with effective leg count 1.37.
- V3 top-leg share was 99.13%, with effective leg count 1.02.
