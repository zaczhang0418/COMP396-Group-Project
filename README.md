# COMP396 Group Project Final Submission

This repository is the final integration branch for the COMP396 group project. It uses the latest remote `main` branch as the structural baseline and selectively brings back evidence and strategy materials from the EDA, Coursework 1, Coursework 2, and Coursework 3 summary branches.

## Development Flow

The project evolved through the following stages:

| Stage | Purpose | Main Evidence |
| --- | --- | --- |
| EDA foundation | Cross-asset diagnostics and strategy motivation | `EDA/docs/`, `EDA/output/stage4_overview/` |
| Coursework 1 / V1 | Asset-bound TF01, MR10, GARCH07 prototype and combined Team01 V1 | `output/coursework_1_stage5_v1_archive/` |
| Coursework 2 / V2 | Generic TF / MR / GARCH workflow, parameter search, transfer validation, Team01 V2 presubmission | `output/coursework_2_stage4_v2_archive/` |
| Coursework 3 / V3 | Cross-asset reassessment, final Team01 V3 refinement, V2/V3 comparison | `output/coursework_3_stage2_v3_archive/`, `Documentation/chapter3_analysis_evidence/` |
| Final report | Report-ready evidence integration and development path summary | `Documentation/branch_summary.md` |

## Final Strategy Versions

| Version | File | Summary |
| --- | --- | --- |
| Team01 V1 | `strategies/team01_v1.py` | Wrapper for the original asset-bound combined prototype. |
| Team01 V2 | `strategies/team01_v2.py` | Wrapper for the Coursework 2 presubmission strategy. |
| Team01 V3 | `strategies/team01.py`, `strategies/team01_v3.py` | Final cross-asset-refined strategy with TF01 + MR09 and dynamic controls. |

The assignment-facing final strategy is:

```text
strategies/team01.py
```

`strategies/team01_v3.py` is kept as a versioned alias for archive and report clarity.

## Key Evidence Locations

| Path | Purpose |
| --- | --- |
| `EDA/docs/stage4-overview.md` | EDA workflow and chart-family explanation. |
| `EDA/docs/latest-analysis.md` | Extracted EDA statistics used for report discussion. |
| `EDA/output/stage4_overview/` | Compact EDA overview charts and CSV summaries. |
| `output/coursework_1_stage5_v1_archive/` | V1 matrix outputs across Part 1, Part 2, Part 3, and Part 1+2+3. |
| `output/coursework_2_stage4_v2_archive/` | V2 generic workflow, transfer validation, and presubmission evidence. |
| `output/coursework_3_stage2_v3_archive/` | Final V3 performance outputs across Part 1, Part 2, and Part 3. |
| `output/cross_asset_scan_v1/summaries/` | Lightweight cross-asset scan summary evidence. |
| `Documentation/branch_summary.md` | Simple summary of the branches used for final integration. |
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
python main.py --strategy team01
```

Run the versioned V3 alias:

```powershell
python main.py --strategy team01_v3 --strategy-class Team01V3Strategy
```

Regenerate compact archive summaries:

```powershell
python scripts\run_coursework_1_stage5_archive_matrix.py
python scripts\run_coursework_2_stage4_archive_matrix.py
```

Regenerate Chapter 3 report packs:

```powershell
python scripts\generate_coursework_3_chapter3_analysis.py
python scripts\generate_part3_331_doc_pack.py
python scripts\generate_part3_332_doc_pack.py
python scripts\generate_part3_333_doc_pack.py
python scripts\generate_part3_335_doc_pack.py
python scripts\generate_part3_35_v3_workflow_pack.py
python scripts\generate_part3_36_comparison_pack.py
```

Run EDA overview:

```powershell
.\EDA\run_all_eda.bat OVERVIEW
```
