# Coursework Branch Archive

Last reviewed: 2026-04-22

This document is the branch map for the coursework evidence archive. It should describe the current GitHub branch structure, not the old temporary branch names that were used during development.

## Current Rule

- Keep `main` as the clean project baseline.
- Keep historical coursework, EDA, and output evidence on `origin/archive/...` branches.
- Do not merge every archive branch into `main`; only merge a final deliverable branch if the team agrees that `main` should contain those outputs.
- If a branch contains generated `Output/` files, that is intentional when the branch is used as report evidence or shared results for teammates.

## Strategy Version Naming

Use `V1`, `V2`, and `V3` for combined strategy versions. Do not use `V0` in the report.

| Version | Development stage | Meaning in the report |
| --- | --- | --- |
| `V1` | CA1 / early coursework | Initial combined strategy built from three asset-specific standalone strategies: TF asset01, MR asset10, and GARCH asset07 |
| `V2` | CA2 / generic refinement | Refined/presubmission Team01 strategy after converting the standalone ideas into a more generic workflow |
| `V3` | CA3 / final refinement | Final cross-asset-informed strategy after scanning 3 strategy families across the 10-asset universe |

When writing the report, describe the progression as:

```text
V1: asset-specific combined prototype
V2: generic/presubmission combined strategy
V3: cross-asset-refined final strategy
```

## Current Remote Hierarchy

```text
origin/main

origin/archive/coursework_1/
  stage-1-tf-asset01-v1
  stage-2-mr-asset10-v1
  stage-3-garch-asset07-v1
  stage-4-initial-combo-team01

origin/archive/coursework_2/
  stage-1-part1-params-on-part2
  stage-2-generic-single-strats
  stage-3-presubmission-team01

origin/archive/coursework_3/
  stage-1-cross-asset-scan

origin/archive/eda/
  stage-1-initial-plotting
  stage-2-full-diagnostics-v3
  stage-3-part2-data-workflow
  stage-4-part123-overview
```

## Branch Timeline

| Group | Branch | Report role | Version link |
| --- | --- | --- | --- |
| Main | `origin/main` | Clean shared baseline after merged framework work | Baseline only |
| EDA | `origin/archive/eda/stage-1-initial-plotting` | Early visual inspection of price behaviour | Research evidence |
| EDA | `origin/archive/eda/stage-2-full-diagnostics-v3` | Full diagnostics used to motivate strategy families | Research evidence |
| EDA | `origin/archive/eda/stage-3-part2-data-workflow` | Part 1, Part 2, and combined-data EDA workflow | Research evidence |
| EDA | `origin/archive/eda/stage-4-part123-overview` | Part 1, Part 2, Part 3, and all-parts overview workflow | Research evidence |
| Coursework 1 | `origin/archive/coursework_1/stage-1-tf-asset01-v1` | Early trend-following standalone strategy | V1 component |
| Coursework 1 | `origin/archive/coursework_1/stage-2-mr-asset10-v1` | Early mean-reversion standalone strategy | V1 component |
| Coursework 1 | `origin/archive/coursework_1/stage-3-garch-asset07-v1` | Early GARCH/regime standalone strategy | V1 component |
| Coursework 1 | `origin/archive/coursework_1/stage-4-initial-combo-team01` | Initial combined Team01 strategy | V1 |
| Coursework 2 | `origin/archive/coursework_2/stage-1-part1-params-on-part2` | Part 2 validation of Part 1-selected parameters | V1 to V2 transition |
| Coursework 2 | `origin/archive/coursework_2/stage-2-generic-single-strats` | Generic single-strategy workflow | V2 foundation |
| Coursework 2 | `origin/archive/coursework_2/stage-3-presubmission-team01` | Presubmission Team01 strategy and evidence | V2 |
| Coursework 3 | `origin/archive/coursework_3/stage-1-cross-asset-scan` | Cross-asset scan and final refined Team01 strategy | V3 |

## Per-Branch Summaries

### `origin/main`

Clean baseline branch for the shared framework and merged support work. It should stay readable and light; later archive outputs are intentionally not all merged into `main`.

### `origin/archive/eda/stage-1-initial-plotting`

First EDA stage. This branch introduced early batch plotting, especially candlestick-style visual inspection, to understand the raw price series before formal strategy design.

Report use:

- Supports the "data understanding" part of CA1.
- Provides visual evidence that strategy design began from observed market behaviour rather than arbitrary parameter choices.
- Should be treated as research context rather than as a submitted strategy branch.

### `origin/archive/eda/stage-2-full-diagnostics-v3`

Full EDA diagnostics stage. This branch expanded the analysis toolkit beyond simple plotting into a broader diagnostic workflow covering volatility, distributional behaviour, autocorrelation, regime clues, and other chart families.

Report use:

- Helps justify why trend following, mean reversion, and GARCH/regime ideas were reasonable strategy families to test.
- Supports Section 2.2 in the CA3 report, especially EDA and identification of market patterns.
- Can be referenced before discussing V1 strategy construction.

### `origin/archive/eda/stage-3-part2-data-workflow`

EDA data workflow stage. This branch introduced the Part 1, Part 2, and `COMBINED` data layout and the batch runner that can run EDA on a selected dataset.

Report use:

- Shows that the team moved from one fixed dataset to a more structured data workflow.
- Supports the transition from CA1 to CA2 because Part 2 data became available for validation.
- Should be described as "Part 1 + Part 2 + combined-data workflow", not as a real `DATA/PART3` workflow.

### `origin/archive/eda/stage-4-part123-overview`

EDA overview stage for the final data layout. This branch starts from the updated main baseline with `DATA/PART3`, keeps the strategy-relevant EDA scripts, and adds a Part 1 / Part 2 / Part 3 overview workflow.

Report use:

- Supports the final EDA narrative after Part 3 data became available.
- Builds `DATA/PART123` from Part 1, Part 2, and Part 3 while preserving the original `Index`-based CSV format.
- Keeps only EDA chart families that support the current TF/MR/GARCH strategy development: autocorrelation, correlation, GARCH, Hurst, return histograms, quantile analysis, and volatility.
- Saves cross-part summary tables and overview plots under `EDA/output/stage_4_part123_overview`.

### `origin/archive/coursework_1/stage-1-tf-asset01-v1`

Early standalone trend-following branch. It focused on a TF idea applied to asset01 and provided one of the three original components used later in the first combined strategy.

Report use:

- V1 component.
- Demonstrates the first alpha family: continuation/trend behaviour.
- Useful when explaining how the initial combined strategy was assembled from separate prototypes.

### `origin/archive/coursework_1/stage-2-mr-asset10-v1`

Early standalone mean-reversion branch. It focused on an MR idea applied to asset10 and became another component of the first combined strategy.

Report use:

- V1 component.
- Demonstrates the second alpha family: deviation from local mean and reversion.
- Useful when explaining diversification across alpha types.

### `origin/archive/coursework_1/stage-3-garch-asset07-v1`

Early standalone GARCH/regime branch. It focused on asset07 and explored volatility/regime-aware trading logic.

Report use:

- V1 component.
- Demonstrates the third alpha family: volatility-state or regime-sensitive behaviour.
- Useful when explaining why V1 combined different strategy styles rather than only different assets.

### `origin/archive/coursework_1/stage-4-initial-combo-team01`

Initial combined Team01 branch. This is the first combined strategy version and should be called `V1` in the report.

Report use:

- Defines V1: the initial combined strategy built from TF asset01, MR asset10, and GARCH asset07.
- Shows the first attempt at portfolio construction across three standalone alpha legs.
- Main limitation: each leg was still tied to a fixed asset, so the team could not yet test whether the strategy logic generalised across the full 10-asset universe.

### `origin/archive/coursework_2/stage-1-part1-params-on-part2`

Validation/transition branch. It tested whether parameters selected from Part 1 still worked on Part 2.

Report use:

- Bridges V1 and V2.
- Supports discussion of out-of-sample thinking and early robustness checks.
- Shows why the team needed a more systematic validation and optimisation process.

### `origin/archive/coursework_2/stage-2-generic-single-strats`

Generic single-strategy branch. It converted the original asset-specific TF/MR/GARCH ideas into reusable strategy forms and standardised experiment tooling.

Report use:

- Foundation for V2.
- Key methodological improvement: separate strategy logic from asset identity.
- Enables later cross-asset testing because the same TF/MR/GARCH logic can be run on all 10 assets.

### `origin/archive/coursework_2/stage-3-presubmission-team01`

Presubmission Team01 branch. This is the second combined strategy version and should be called `V2` in the report.

Report use:

- Defines V2: the refined/presubmission combined strategy after the generic workflow was introduced.
- Contains generated evidence under `Output/ca3_stage2_presubmission_*`.
- Main limitation: it improved packaging and validation, but did not yet fully exploit cross-asset strategy-family selection.

### `origin/archive/coursework_3/stage-1-cross-asset-scan`

Cross-asset scan branch. This is the final combined strategy version and should be called `V3` in the report.

Report use:

- Defines V3: the final strategy informed by a 3 strategy families x 10 assets scan.
- Contains cross-asset scan evidence under `Output/coursework_3/stage_1_cross_asset_scan`.
- Contains final stage outputs under `Output/ca3_stage3_team01_part1` and `Output/ca3_stage3_team01_part2`.
- This is the most important branch for explaining the final strategy choice and justification in CA3.

## Old Name To Archive Name Map

The following old remote branch names have been deleted from GitHub and replaced by archive names.

| Old name | Current archive branch |
| --- | --- |
| `origin/tr_asset01_v1` | `origin/archive/coursework_1/stage-1-tf-asset01-v1` |
| `origin/mr_asset10_v1` | `origin/archive/coursework_1/stage-2-mr-asset10-v1` |
| `origin/gr_asset07-v1` | `origin/archive/coursework_1/stage-3-garch-asset07-v1` |
| `origin/feature/combo-tf01-mr10-ga07-v1` | `origin/archive/coursework_1/stage-4-initial-combo-team01` |
| `origin/part1paramsinpart2` | `origin/archive/coursework_2/stage-1-part1-params-on-part2` |
| `origin/refine-single-strats` | `origin/archive/coursework_2/stage-2-generic-single-strats` |
| `origin/presubmission-team-strategy` | `origin/archive/coursework_2/stage-3-presubmission-team01` |
| `origin/cross-asset-scan` | `origin/archive/coursework_3/stage-1-cross-asset-scan` |
| `origin/feat/add-eda-plotting` | `origin/archive/eda/stage-1-initial-plotting` |
| `origin/feature/run-eda-diagnostics` | `origin/archive/eda/stage-2-full-diagnostics-v3` |
| `origin/eda_part2` | `origin/archive/eda/stage-3-part2-data-workflow` |

## EDA Data Status

Current EDA data folders:

```text
DATA/PART1/
DATA/PART2/
DATA/PART3/
DATA/PART123/
```

The stage 4 all-parts dataset is generated from Part 1, Part 2, and Part 3:

```powershell
python EDA/scripts/merge_data_parts.py --parts PART1 PART2 PART3 --output PART123
```

The EDA batch runner supports dataset selection and the stage 4 `ALL` workflow:

```powershell
.\EDA\run_all_eda.bat ALL
.\EDA\run_all_eda.bat PART1
.\EDA\run_all_eda.bat PART2
.\EDA\run_all_eda.bat PART3
.\EDA\run_all_eda.bat PART123
```

When `PART123` is selected, `EDA/run_all_eda.bat` calls `EDA/scripts/merge_data_parts.py` before running the analysis scripts.

## Coursework Evidence Status

### Coursework 1

These branches preserve early individual strategy prototypes and the first combined strategy. They are useful for report history but should not be merged into `main` now because later branches supersede them.

```text
origin/archive/coursework_1/stage-1-tf-asset01-v1
origin/archive/coursework_1/stage-2-mr-asset10-v1
origin/archive/coursework_1/stage-3-garch-asset07-v1
origin/archive/coursework_1/stage-4-initial-combo-team01
```

### Coursework 2

These branches describe the transition from fixed-asset strategies to generic strategies, validation on later data, and the presubmission Team01 strategy.

```text
origin/archive/coursework_2/stage-1-part1-params-on-part2
origin/archive/coursework_2/stage-2-generic-single-strats
origin/archive/coursework_2/stage-3-presubmission-team01
```

Known output evidence:

```text
Output/ca3_stage2_presubmission_part1/
Output/ca3_stage2_presubmission_part2/
Output/ca3_stage2_presubmission_part3_existing/
```

### Coursework 3

This branch preserves the cross-asset scan and optimized Team01 evidence. This is the most likely candidate if the team later decides that a final branch should be merged into `main`.

```text
origin/archive/coursework_3/stage-1-cross-asset-scan
```

Known output evidence:

```text
Output/ca3_stage3_team01_part1/
Output/ca3_stage3_team01_part2/
Output/coursework_3/stage_1_cross_asset_scan/
```

## Local Cleanup Notes

After `git fetch --prune`, these local branches may still exist but point to deleted upstream names:

```text
coursework_3/stage-1-generic-single-strats
coursework_3/stage-2-presubmission-team01
coursework_3/stage-3-cross-asset-scan
eda_part2
```

They should either be deleted locally after confirming no local-only commits are needed, or recreated/tracked against the current `origin/archive/...` branches.

Recommended local branch names for cleanup work:

```powershell
git switch --track -c archive/eda/stage-3-part2-data-workflow origin/archive/eda/stage-3-part2-data-workflow
git switch --track -c archive/coursework_2/stage-2-generic-single-strats origin/archive/coursework_2/stage-2-generic-single-strats
git switch --track -c archive/coursework_2/stage-3-presubmission-team01 origin/archive/coursework_2/stage-3-presubmission-team01
git switch --track -c archive/coursework_3/stage-1-cross-asset-scan origin/archive/coursework_3/stage-1-cross-asset-scan
```

## Merge Recommendation

Do not merge all archive branches into `main`.

Use this rule:

- If teammates need an old stage exactly as evidence, they should checkout the matching `origin/archive/...` branch.
- If teammates need only final outputs, consider merging only `origin/archive/coursework_3/stage-1-cross-asset-scan` into `main` after reviewing file size and conflict risk.
- If `main` should stay clean, keep outputs on archive branches and link them from documentation.

## Next Cleanup Targets

1. Update `origin/archive/eda/stage-3-part2-data-workflow` README so it no longer reads like the generic COMP396 framework README only.
2. Update `origin/archive/coursework_2/stage-2-generic-single-strats` README references from old branch names to archive names.
3. Update `origin/archive/coursework_2/stage-3-presubmission-team01` README references from old branch names to archive names.
4. Update `origin/archive/coursework_3/stage-1-cross-asset-scan` README references from old branch names to archive names.
5. Push each cleaned branch after local review.
