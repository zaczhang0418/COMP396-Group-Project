# Section 3.3.2 Draft Text

The first structural weakness in Team01 V2 was asset hard binding. Figure 3.3.2a and Table 3.3.2a show that V2 continued to rely on inherited series choices even though the transfer evidence into Part 2 was weak. For example, MR10, which remained in the V2 combination, achieved an OOS true PD ratio of 1.2131 but fell to -0.8983 on Part 2. GARCH07 was even less convincing, with OOS true PD -0.5051 and Part 2 true PD -0.6419. This matters because the issue was not simply that every alternative also failed: GARCH09, which was not deployed, still recorded a positive Part 2 true PD of 1.0070. The evidence therefore supports the claim that V2 suffered from static asset binding rather than from a uniformly impossible asset universe.

The second weakness was uneven leg contribution. Figure 3.3.2b shows that the V2 Part 3 result was mainly carried by the TF leg, while the MR and GARCH legs contributed far less to total absolute leg PnL. Table 3.3.2b makes this more explicit: V2's top leg contributed 84.71% of absolute leg PnL, leaving an effective leg count of only 1.37 despite having three active legs. In other words, the portfolio looked diversified in structure but not in realised contribution. V3 improved the overall Part 3 outcome, but Figure 3.3.2c shows that the concentration problem did not disappear; it became more extreme. The top-leg share rose further to 99.13%, and the effective leg count fell to 1.02, indicating that the final portfolio was even more dependent on one dominant return engine.

Taken together, these results support a balanced interpretation for Chapter 3.3.2. The V2 design was unconvincing because it combined static asset binding with weak realised diversification across legs. The V3 refinement solved part of the first problem by reconsidering the mapping, but it did not fully solve the second problem because the final Part 3 performance still relied overwhelmingly on the TF leg. This means the section can argue both that reassignment was necessary and that better performance alone does not prove balanced multi-leg robustness.

References:
- Figure 3.3.2a: [figures/figure_3_3_2a_asset_binding_transfer.png](figures/figure_3_3_2a_asset_binding_transfer.png)
- Figure 3.3.2b: [figures/figure_3_3_2b_part3_leg_contribution_shares.png](figures/figure_3_3_2b_part3_leg_contribution_shares.png)
- Figure 3.3.2c: [figures/figure_3_3_2c_concentration_metrics.png](figures/figure_3_3_2c_concentration_metrics.png)
- Table 3.3.2a: [asset_binding_transfer_summary.csv](asset_binding_transfer_summary.csv)
- Table 3.3.2b: [leg_contribution_concentration_metrics.csv](leg_contribution_concentration_metrics.csv)
