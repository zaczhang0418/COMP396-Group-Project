# Branch Summary

This file summarises the branches used for the final submission integration. It is based on the README / summary notes preserved on each branch, but keeps only the key points needed for final marking and report navigation.

## Final Integration Branch

| Item | Summary |
| --- | --- |
| Branch | `final/submission-integration` |
| Baseline | `origin/main` |
| Purpose | Final zip-ready integration branch. It keeps the latest main structure and selectively brings in report evidence, final strategy files, and compact archive outputs from the summary branches. |
| Final strategy | `strategies/coursework_3/stage_2_team01_v3_final.py` |
| Main documentation | `README.md`, `Documentation/branch_summary.md`, `Documentation/chapter3_analysis_evidence/` |
| Unified runner | `run_project.py` |

The final integration avoids full historical branch merges because the summary branches contain old framework layouts, old data layouts, branch-specific READMEs, and generated experiment folders. Only report-relevant and submission-relevant material was brought forward.

## Branches Used

| Branch | Role in Project | Material Kept in Final Integration |
| --- | --- | --- |
| `origin/main` | Latest project structure and clean baseline. | Framework, data layout, EDA workflow structure, and base repository files. |
| `origin/summary/eda/stage-5-archive-summary` | EDA evidence archive for Part 1, Part 2, Part 3, and Part 1+2+3. | `EDA/docs/stage_4_part123_overview/`, `EDA/docs/stage_5_archive_summary/`, `EDA/output/stage_4_part123_overview/`, and `requirements.txt`. |
| `origin/summary/coursework_1/stage-5-v1-archive-summary` | Coursework 1 / Team01 V1 archive. | `strategies/coursework_1/`, `scripts/coursework_1/`, and `output/coursework_1_stage5_v1_archive/`. |
| `origin/summary/coursework_2/stage-4-v2-archive-summary` | Coursework 2 / Team01 V2 official submission archive. | `strategies/coursework_2/`, `scripts/coursework_2/`, and `output/coursework_2_stage4_v2_archive/`. |
| `origin/summary/coursework_3/stage-2-v3-archive-summary` | Coursework 3 / Team01 V3 refinement archive. | `strategies/coursework_3/`, `scripts/coursework_3/`, `output/coursework_3_stage2_v3_archive/`, and `output/cross_asset_scan_v1/summaries/`. |
| `origin/summary/coursework_3/stage-3-v2v3-performance-analysis` | Chapter 3 V2/V3 report analysis package. | `Documentation/chapter3_analysis_evidence/`. |

## Stage Summaries

### EDA Foundation

The EDA branch provides the data-level motivation for the later strategy design. It compares Part 1, Part 2, Part 3, and Part 1+2+3 with strategy-relevant diagnostics: ACF/PACF, Hurst, GARCH, volatility, return distributions, quantile analysis, and correlation heatmaps.

Main retained evidence:

- `EDA/docs/stage_4_part123_overview/stage_4_overview.md`
- `EDA/docs/stage_4_part123_overview/stage_4_latest_analysis.md`
- `EDA/docs/stage_4_part123_overview/stage_4_latest_run.md`
- `EDA/docs/stage_5_archive_summary/eda_report_and_justification.ipynb`
- `EDA/output/stage_4_part123_overview/`

### Coursework 1 / Team01 V1

Coursework 1 developed the first asset-bound combined prototype:

```text
TF series_1 + MR series_10 + GARCH series_7
```

The V1 branch shows how the project moved from individual single-asset strategies to a combined portfolio prototype. The main limitation was that both strategy logic and asset choice were still hard-bound to specific series.

Main retained evidence:

- `strategies/coursework_1/stage_1_tf_asset01_v1.py`
- `strategies/coursework_1/stage_2_mr_asset10_v1.py`
- `strategies/coursework_1/stage_3_garch_asset07_v1.py`
- `strategies/coursework_1/stage_4_initial_combo_team01_v1.py`
- `strategies/coursework_1/stage_5_team01_v1_archive.py`
- `output/coursework_1_stage5_v1_archive/`

### Coursework 2 / Team01 V2

Coursework 2 generalised the V1 ideas into reusable TF / MR / GARCH strategy families. It added Part 1 parameter search, robust candidate selection, and Part 2 transfer validation. The official V2 presubmission still used the historical Team01 structure, but the branch established the generic workflow needed for cross-asset reassessment.

Main retained evidence:

- `strategies/coursework_2/stage_2_tf_generic_v2.py`
- `strategies/coursework_2/stage_2_mr_generic_v2.py`
- `strategies/coursework_2/stage_2_garch_generic_v2.py`
- `strategies/coursework_2/stage_3_team01_v2_presubmission.py`
- `output/coursework_2_stage4_v2_archive/`
- `scripts/coursework_2/stage_1_part1_params_on_part2_validation/`
- `scripts/coursework_2/stage_2_single_strategy_optimization/`
- `scripts/coursework_2/stage_4_generate_v2_evidence_summary.py`

### Coursework 3 / Team01 V3

Coursework 3 used the generic workflow from V2 to scan TF / MR / GARCH across 10 assets. The final strategy was simplified and refined into:

```text
TF series_1 + MR series_9
```

GARCH was removed from final deployment. V3 adds daily market-condition gating, dynamic allocation, performance-aware budgeting, loss-freeze controls, gross exposure limits, and rebalance tolerance.

Main retained evidence:

- `strategies/coursework_3/stage_2_team01_v3_final.py`
- `scripts/coursework_3/stage_1_cross_asset_scan/`
- `scripts/coursework_3/stage_3_chapter3_evidence/`
- `output/coursework_3_stage2_v3_archive/`
- `output/cross_asset_scan_v1/summaries/`

### Chapter 3 Analysis Evidence

The Chapter 3 analysis package compares the V2 diagnosis with V3 refinement. It is kept as a folder because it contains multiple subsections, figures, CSV tables, JSON summaries, and reference packs.

Main retained evidence:

- `Documentation/chapter3_analysis_evidence/3.3/`
- `Documentation/chapter3_analysis_evidence/3.5/`
- `Documentation/chapter3_analysis_evidence/3.6/`

## Report Flow Mapping

| Report Stage | Repository Evidence |
| --- | --- |
| Stage A: EDA evidence foundation | `EDA/docs/stage_4_part123_overview/`, `EDA/docs/stage_5_archive_summary/`, `EDA/output/stage_4_part123_overview/` |
| Stage B: CA1 V1 prototype | `output/coursework_1_stage5_v1_archive/`, `strategies/coursework_1/` |
| Stage C: CA2 V2 official submission | `output/coursework_2_stage4_v2_archive/`, `strategies/coursework_2/` |
| Stage D: V2 output diagnosis | `Documentation/chapter3_analysis_evidence/3.3/` |
| Stage E: V3 refinement | `strategies/coursework_3/`, `Documentation/chapter3_analysis_evidence/3.5/` |
| Stage F: final comparison and report integration | `Documentation/chapter3_analysis_evidence/3.6/` |

## Deliberately Excluded From Final Integration

The final branch does not import:

- old `framework/` versions from coursework archive branches,
- old `DATA/` layouts,
- unused `strategies/archive/` single-asset strategy files,
- full raw cross-asset scan outputs with thousands of intermediate run files,
- old branch-specific root README files,
- cache folders and bytecode files,
- superseded temporary report folders.

This keeps the final zip focused on the current project structure plus report-ready evidence.
