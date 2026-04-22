# Coursework 1 Stage 5 V1 Archive Summary

Reviewed on: 2026-04-22

Branch:

```text
summary/coursework_1/stage-5-v1-archive-summary
```

Source branch:

```text
archive/coursework_1/stage-4-initial-combo-team01
```

## Purpose

This branch is a documentation-only summary branch for Coursework 1 V1. It preserves the original V1 strategy implementation from stage 4 and adds a clear archive note for later report writing and final-branch migration.

The original archive branches should remain historical evidence. This summary branch should be used when we need a readable explanation of what V1 was, how it was assembled, and what its limitations were.

## V1 Strategy Definition

Coursework 1 V1 is the initial Team01 combined strategy. It combines three asset-specific single-strategy prototypes:

| Stage | Strategy file | Asset/data feed | Role |
| --- | --- | --- | --- |
| Stage 1 | `strategies/tf_asset01_v1.py` | `series_1` | Trend-following leg |
| Stage 2 | `strategies/mr_asset10_v1.py` | `series_10` | Mean-reversion leg |
| Stage 3 | `strategies/garch_asset07_v1.py` | `series_7` | GARCH/regime trend-following leg |
| Stage 4 | `strategies/combo_tf01_mr10_garch07_v1.py` | `series_1`, `series_10`, `series_7` | Combined V1 portfolio |

The V1 combined strategy uses capital weights across the three legs and keeps each leg tied to its original asset. This is important for the report: V1 is not yet a generic cross-asset strategy. It is an early combined prototype built from three fixed asset-specific ideas.

## Core Files

Main strategy files:

```text
strategies/tf_asset01_v1.py
strategies/mr_asset10_v1.py
strategies/garch_asset07_v1.py
strategies/combo_tf01_mr10_garch07_v1.py
```

Main experiment scripts:

```text
scripts/run_tf_once.py
scripts/run_mr_once.py
scripts/run_garch_once.py
scripts/run_combo_once.py
scripts/run_core4_grid_refine_tf.py
scripts/run_core4_grid_refine_mr.py
scripts/run_core4_grid_garch.py
scripts/pick_best_and_run_oos_full_tf.py
scripts/pick_best_and_run_oos_full_mr.py
scripts/pick_best_and_run_oos_full_garch.py
```

Parameter and split files:

```text
configs/splits_asset01.json
configs/splits_asset07.json
configs/splits_asset10.json
configs/grids/tf_core4_v1.json
configs/grids/core4_v1.json
configs/grids/garch_core4_v1.json
configs/mr_asset10_v1.yaml
```

Data used by this branch:

```text
DATA/PART1/
DATA/PART2/
DATA/PART3/
DATA/PART123/
```

`DATA/PART2`, `DATA/PART3`, `DATA/PART123`, and `configs/timeline.json` were restored from `main` into this summary branch without merging the full `main` hierarchy. This keeps the historical Coursework 1 strategy code intact while allowing the V1 strategies to be evaluated on all available data partitions.

## How To Run

Run the combined strategy directly through the backtester:

```powershell
python main.py --strategy combo_tf01_mr10_garch07_v1 --data-dir .\DATA\PART1
```

Run the sequential combo runner with explicit dates:

```powershell
python scripts\run_combo_once.py --start 2069-12-08 --end 2072-09-02 --split 100-full --tag combo_v1
```

Run the three single legs directly:

```powershell
python main.py --strategy tf_asset01_v1 --data-dir .\DATA\PART1 --param data_name=series_1
python main.py --strategy mr_asset10_v1 --data-dir .\DATA\PART1 --param data_name=series_10
python main.py --strategy garch_asset07_v1 --data-dir .\DATA\PART1 --param data_name=series_7
```

Run the full archive matrix:

```powershell
python scripts\run_coursework_1_stage5_archive_matrix.py
```

The default matrix run keeps the archive lightweight by skipping PNG plots and saving JSON/CSV metrics. To also generate plots:

```powershell
python scripts\run_coursework_1_stage5_archive_matrix.py --with-plots
```

## Archived Output Structure

Coursework 1 Stage 5 output is split first by data partition and then by strategy:

```text
output/coursework_1_stage5_v1_archive/
  matrix_summary.csv
  matrix_summary.json
  archive_manifest.json
  PART1/
    tf_asset01_v1/
    mr_asset10_v1/
    garch_asset07_v1/
    combo_tf01_mr10_garch07_v1/
  PART2/
    tf_asset01_v1/
    mr_asset10_v1/
    garch_asset07_v1/
    combo_tf01_mr10_garch07_v1/
  PART3/
    tf_asset01_v1/
    mr_asset10_v1/
    garch_asset07_v1/
    combo_tf01_mr10_garch07_v1/
  PART123/
    tf_asset01_v1/
    mr_asset10_v1/
    garch_asset07_v1/
    combo_tf01_mr10_garch07_v1/
```

Each strategy folder contains:

```text
run_summary.json
per_series_pd.json
*.png
```

## Archive Matrix Results

Matrix run date: 2026-04-22

Command:

```powershell
python scripts\run_coursework_1_stage5_archive_matrix.py --with-plots
```

| Dataset | Strategy | Final value | True PD | Open PnL PD | Activity % | Bankrupt |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| PART1 | TF asset01 V1 | 1148068.52 | 1.4050 | 2.4700 | 25.83 | No |
| PART1 | MR asset10 V1 | 1090352.16 | 1.8245 | 4.3541 | 31.70 | No |
| PART1 | GARCH asset07 V1 | 1002568.38 | 0.1651 | 0.4806 | 13.70 | No |
| PART1 | Combo V1 | 998083.95 | -0.0249 | 0.2270 | 74.97 | No |
| PART2 | TF asset01 V1 | 997663.14 | -0.0230 | 0.2764 | 29.23 | No |
| PART2 | MR asset10 V1 | 955611.35 | -0.3195 | 0.3482 | 29.63 | No |
| PART2 | GARCH asset07 V1 | 988387.08 | -0.4697 | -0.4340 | 12.40 | No |
| PART2 | Combo V1 | 1036933.25 | 0.4834 | 1.3694 | 84.48 | No |
| PART3 | TF asset01 V1 | 1026463.85 | 1.5872 | 2.6754 | 4.60 | No |
| PART3 | MR asset10 V1 | 827948.56 | -0.7471 | -0.2909 | 27.80 | No |
| PART3 | GARCH asset07 V1 | 999267.30 | -0.0621 | 0.0316 | 16.40 | No |
| PART3 | Combo V1 | 1195196.46 | 2.6626 | 3.1977 | 88.19 | No |
| PART123 | TF asset01 V1 | -98448.60 | -0.7490 | -0.5706 | 46.56 | Yes, 2076-07-30 |
| PART123 | MR asset10 V1 | 918148.74 | -0.2622 | 2.5977 | 31.70 | No |
| PART123 | GARCH asset07 V1 | 989402.10 | -0.3904 | -0.1796 | 14.17 | No |
| PART123 | Combo V1 | 1218435.74 | 2.8371 | 4.1094 | 87.83 | No |

## Report Narrative

Use this branch to describe V1 as:

```text
V1: asset-specific combined prototype
```

Recommended explanation:

- The team first developed three separate alpha families: trend following, mean reversion, and volatility/regime-aware trend following.
- Each family was tested on one selected asset.
- The first Team01 combined strategy allocated capital across those three fixed legs.
- The combined design gave early diversification across strategy style and asset identity.
- Its main limitation was that strategy logic and asset choice were still coupled.
- This limitation motivated Coursework 2, where the team converted the ideas into more generic reusable strategy families.

## Stage 5 Policy

This summary branch should not change the historical V1 trading logic unless a small path or execution fix is needed to reproduce the branch.

For future merging into the current `main` hierarchy, do not merge this branch wholesale. Instead, migrate only:

```text
DOCS/coursework_1_stage5_v1_archive_summary.md
```

or selectively cherry-pick documentation changes.

## Verification

The following syntax check passed on 2026-04-22:

```powershell
python -m py_compile strategies\tf_asset01_v1.py strategies\mr_asset10_v1.py strategies\garch_asset07_v1.py strategies\combo_tf01_mr10_garch07_v1.py scripts\run_combo_once.py scripts\pick_best_and_run_oos_full_tf.py scripts\pick_best_and_run_oos_full_mr.py scripts\pick_best_and_run_oos_full_garch.py
```

Known historical note: some comments in this branch display as mojibake in the current terminal encoding. The summary branch leaves that historical code untouched.
