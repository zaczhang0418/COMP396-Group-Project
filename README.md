# COMP396 Group Project Final Submission

This repository is the final integration branch for the COMP396 group project. It uses the latest remote `main` branch as the structural baseline and selectively brings back evidence and strategy materials from the EDA, Coursework 1, Coursework 2, and Coursework 3 summary branches.

## Development Flow

The project evolved through the following stages:

| Stage | Purpose | Main Evidence |
| --- | --- | --- |
| EDA foundation | Cross-asset diagnostics and strategy motivation | `EDA/docs/stage_4_part123_overview/`, `EDA/docs/stage_5_archive_summary/`, `EDA/output/stage_4_part123_overview/` |
| Coursework 1 / V1 | Asset-bound TF01, MR10, GARCH07 prototype and combined Team01 V1 | `Output/coursework_1/stage_5_team01_v1_archive/` |
| Coursework 2 / V2 | Generic TF / MR / GARCH workflow, parameter search, transfer validation, Team01 V2 presubmission | `Output/coursework_2/stage_4_team01_v2_archive/` |
| Coursework 3 / V3 | Cross-asset reassessment, final Team01 V3 refinement, V2/V3 comparison | `Output/coursework_3/stage_1_cross_asset_scan/`, `Output/coursework_3/stage_2_team01_v3_final/`, `Output/coursework_3/stage_3_chapter3_evidence/`, `Documentation/chapter3_analysis_evidence/` |
| Final report | Report-ready evidence integration and development path summary | `Documentation/final_report_evidence/final_report_evidence_index.md`, `Documentation/branch_summary.md` |

## Unified Runner

Use the root-level runner for common final-branch tasks:

```powershell
python run_project.py backtest
python run_project.py eda OVERVIEW
python run_project.py full --plots --skip-cross-scan-run
python run_project.py cross-scan --mode summarize -- --help
python run_project.py chapter3
python run_project.py dist
```

`main.py` remains the lower-level Backtrader harness used by the workflow scripts.

To run the complete final workflow in one command, use:

```powershell
python run_project.py full --plots --skip-cross-scan-run
```

This reruns tests, EDA, archive summaries, Chapter 3 evidence packs, and final
V3 backtests while reusing the tracked cross-asset scan summary evidence. To
recompute the raw cross-asset scan from scratch as well, run:

```powershell
python run_project.py full --plots
```

The raw cross-asset scan evaluates many strategy/asset combinations and can take
a long time, so the `--skip-cross-scan-run` command is the recommended full
verification command when the existing summary evidence is sufficient.

## Final Strategy Versions

| Version | File | Summary |
| --- | --- | --- |
| Team01 V1 | `Strategies/coursework_1/stage_5_team01_v1_archive.py` | Wrapper for the original asset-bound combined prototype. |
| Team01 V2 | `Strategies/coursework_2/stage_3_team01_v2_presubmission.py` | Coursework 2 official presubmission strategy. |
| Team01 V3 | `Strategies/coursework_3/stage_2_team01_v3_final.py` | Final cross-asset-refined strategy with TF01 + MR09 and dynamic controls. |

The assignment-facing final strategy is:

```text
Strategies/coursework_3/stage_2_team01_v3_final.py
```

## Key Evidence Locations

| Path | Purpose |
| --- | --- |
| `EDA/docs/stage_4_part123_overview/stage_4_overview.md` | EDA workflow and chart-family explanation. |
| `EDA/docs/stage_4_part123_overview/stage_4_latest_analysis.md` | Extracted EDA statistics used for report discussion. |
| `EDA/docs/stage_4_part123_overview/stage_4_latest_run.md` | Reproducible EDA run log summary. |
| `EDA/docs/stage_5_archive_summary/eda_report_and_justification.ipynb` | Notebook evidence archive integrated into EDA docs. |
| `EDA/output/stage_4_part123_overview/` | Compact EDA overview charts and CSV summaries. |
| `Documentation/final_report_evidence/final_report_evidence_index.md` | Final-report evidence map from report needs to branch paths. |
| `Documentation/final_report_evidence/eda_selected_asset_profile.md` | Report-facing EDA support for assets 01, 07, and 10. |
| `Output/coursework_1/stage_5_team01_v1_archive/` | V1 matrix outputs across Part 1, Part 2, Part 3, and Part 1+2+3. |
| `Output/coursework_2/stage_4_team01_v2_archive/` | V2 generic workflow, transfer validation, and presubmission evidence. |
| `Output/coursework_3/stage_1_cross_asset_scan/summaries/` | Lightweight cross-asset scan summary evidence. |
| `Output/coursework_3/stage_2_team01_v3_final/` | Final V3 performance outputs across Part 1, Part 2, and Part 3. |
| `Output/coursework_3/stage_3_chapter3_evidence/` | Chapter 3 drawdown and V2/V3 comparison evidence outputs. |
| `Scripts/coursework_2/stage_1_part1_params_on_part2_validation/` | Stage 1 transfer check: Part 1-selected parameters tested on Part 2. |
| `Scripts/coursework_2/stage_2_single_strategy_optimization/` | Generic TF / MR / GARCH optimization commands. |
| `Scripts/coursework_3/stage_1_cross_asset_scan/` | Cross-asset scan, summary, and transfer-validation commands. |
| `Documentation/branch_summary.md` | Simple summary of the branches used for final integration. |
| `Documentation/branch_archive.md` | Detailed per-branch development summary. |
| `Documentation/chapter3_analysis_evidence/` | Report-ready Chapter 3 V2 diagnosis, V3 refinement, and V2/V3 comparison packs. |

## Data

The final branch keeps the latest main data layout:

```text
DATA/PART1/
DATA/PART2/
DATA/PART3/
DATA/PART123/
```

`PART123` is the combined Part 1 + Part 2 + Part 3 dataset used by the EDA overview workflow.

## Reproduction Notes

Run the final strategy through the normal backtester:

```powershell
python run_project.py backtest
```

Run the full final workflow with progress and ETA:

```powershell
python run_project.py full --plots --skip-cross-scan-run
```

Run the same workflow and also recompute the raw cross-asset scan:

```powershell
python run_project.py full --plots
```

The raw cross-asset scan can take substantially longer than the rest of the
workflow because it evaluates multiple strategy and asset combinations.

Regenerate compact archive summaries:

```powershell
python run_project.py archive-cw1
python run_project.py archive-cw2
```

Regenerate Chapter 3 report packs:

```powershell
python run_project.py chapter3
```

Run the Coursework 3 cross-asset scan tooling directly:

```powershell
python Scripts\coursework_3\stage_1_cross_asset_scan\run_cross_asset_scan.py --help
python Scripts\coursework_3\stage_1_cross_asset_scan\summarize_cross_asset_scan.py --help
python Scripts\coursework_3\stage_1_cross_asset_scan\validate_cross_asset_scan_part2.py --help
```

Run EDA overview:

```powershell
python run_project.py eda OVERVIEW
```
