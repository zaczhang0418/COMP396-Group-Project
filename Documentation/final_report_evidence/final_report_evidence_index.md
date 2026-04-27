# Final Report Evidence Index

This index maps the final report evidence requests to the current final-branch
layout. It is intended as the bridge between the report draft and the archived
code/output evidence in this branch.

## Output Layout

| Development stage | Current evidence folder |
| --- | --- |
| Coursework 1 / V1 archive | `Output/coursework_1/stage_5_team01_v1_archive/` |
| Coursework 2 / V2 archive | `Output/coursework_2/stage_4_team01_v2_archive/` |
| Coursework 3 / cross-asset scan | `Output/coursework_3/stage_1_cross_asset_scan/` |
| Coursework 3 / V3 final archive | `Output/coursework_3/stage_2_team01_v3_final/` |
| Coursework 3 / Chapter 3 evidence | `Output/coursework_3/stage_3_chapter3_evidence/` |

## Evidence Coverage

| Report need | Branch evidence |
| --- | --- |
| EDA evidence for multi-asset context | `EDA/docs/stage_4_part123_overview/`, `EDA/output/stage_4_part123_overview/stage_4_risk_return_overview.png`, `stage_4_total_return_heatmap.png`, `stage_4_asset_summary.csv` |
| EDA profile for V2-bound assets 01, 07, 10 | `Documentation/final_report_evidence/eda_selected_asset_profile.md` |
| V1 asset-bound prototype evidence | `Strategies/coursework_1/stage_1_tf_asset01_v1.py`, `stage_2_mr_asset10_v1.py`, `stage_3_garch_asset07_v1.py`, `stage_4_initial_combo_team01_v1.py`, `Output/coursework_1/stage_5_team01_v1_archive/matrix_summary.csv` |
| V2 generic strategy families | `Strategies/coursework_2/stage_2_tf_generic_v2.py`, `stage_2_mr_generic_v2.py`, `stage_2_garch_generic_v2.py` |
| V2 grid configs | `Configs/grids_for_single_strategies/tf/`, `mr/`, `garch/` |
| V2 robust parameter selection | `Scripts/coursework_2/stage_2_single_strategy_optimization/common/pick_best_common.py`, plus each family `pick_best.py` |
| V2 submitted strategy | `Strategies/coursework_2/stage_3_team01_v2_presubmission.py` |
| V2 Part 1, Part 2, preserved Part 3 evidence | `Output/coursework_2/stage_4_team01_v2_archive/process_summary.csv`, `per_leg_summary.csv`, `team01_presubmission/` |
| CA3 3x10 strategy-asset scan | `Scripts/coursework_3/stage_1_cross_asset_scan/`, `Output/coursework_3/stage_1_cross_asset_scan/summaries/matrix_3x10.csv`, `asset_strategy_assignment.csv`, `part2_validation.csv`, `summary.json` |
| V3 final strategy | `Strategies/coursework_3/stage_2_team01_v3_final.py` |
| V3 Part 1, Part 2, Part 3 evidence | `Output/coursework_3/stage_2_team01_v3_final/process_summary.csv`, `team01_v3_final/part1/`, `part2/`, `part3/` |
| V2/V3 drawdown, contribution, exposure, and comparison packs | `Documentation/chapter3_analysis_evidence/3.3/`, `3.5/`, `3.6/`, and `Output/coursework_3/stage_3_chapter3_evidence/part3_drawdown_analysis/` |

## Draft Placeholder Mapping

| Draft placeholder or old path | Current branch path |
| --- | --- |
| `EDA/output/stage4_overview/risk_return_overview.png` | `EDA/output/stage_4_part123_overview/stage_4_risk_return_overview.png` |
| `strategies/combo_tf01_mr10_garch07_v1.py` for V2 logic screenshots | `Strategies/coursework_2/stage_3_team01_v2_presubmission.py` |
| `strategies/tf_generic_v1.py` | `Strategies/coursework_2/stage_2_tf_generic_v2.py` |
| `strategies/mr_generic_v1.py` | `Strategies/coursework_2/stage_2_mr_generic_v2.py` |
| `strategies/garch_generic_v1.py` | `Strategies/coursework_2/stage_2_garch_generic_v2.py` |
| `scripts/single_strat/common/pick_best_common.py` | `Scripts/coursework_2/stage_2_single_strategy_optimization/common/pick_best_common.py` |
| `strategies/team01.py` when discussing V2 | `Strategies/coursework_2/stage_3_team01_v2_presubmission.py` |
| `strategies/team01.py` when discussing V3 | `Strategies/coursework_3/stage_2_team01_v3_final.py` |
| `output/coursework_1_stage5_v1_archive/...` | `Output/coursework_1/stage_5_team01_v1_archive/...` |
| `output/coursework_2_stage4_v2_archive/...` | `Output/coursework_2/stage_4_team01_v2_archive/...` |
| `output/cross_asset_scan_v1/...` | `Output/coursework_3/stage_1_cross_asset_scan/...` |
| `output/coursework_3_stage2_v3_archive/...` | `Output/coursework_3/stage_2_team01_v3_final/...` |

## Missing-Material Check

The report's core evidence requests are covered in this branch after the output
layout cleanup. The only report-facing material added here is a concise evidence
index and an EDA selected-asset profile, because the raw EDA charts and CSVs
already existed but did not have a single report-ready summary table.
