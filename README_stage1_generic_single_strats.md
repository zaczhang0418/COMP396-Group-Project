# Stage 1: Generic Single-Strategy Workflow Archive

This branch archives the Stage 1 transition from asset-specific strategy prototypes to generic, reusable single-strategy workflows.

## Archive Status

- Branch role: Stage 1 generic single-strategy refactor.
- Original remote branch: `origin/refine-single-strats`.
- Target archive branch name: `coursework_3/stage-1-generic-single-strats`.
- Stage tag: `stage1-generic-single-strats`.
- This branch was already merged into `main` through PR #11 before this archive note was added.

## Why This Stage Matters

Before this stage, the main strategy ideas were tied to specific assets:

| Strategy idea | Early branch / evidence | Original asset |
| --- | --- | --- |
| Trend-following | `origin/tr_asset01_v1` | `series_1` / asset01 |
| Mean reversion | `origin/mr_asset10_v1` | `series_10` / asset10 |
| GARCH regime/trend | `origin/gr_asset07-v1` | `series_7` / asset07 |

That structure was useful for initial discovery, but it made later research too asset-specific. Stage 1 separated strategy logic from asset identity. After this refactor, the same TF, MR, and GARCH ideas could be tested on different data feeds by changing runner parameters rather than rewriting the strategy.

In report terms, this is the key bridge between early strategy prototyping and the later cross-asset matrix:

```text
asset-specific prototypes
  -> generic single-strategy implementations
  -> standardized experiments
  -> presubmission three-leg strategy
  -> cross-asset scan and optimized mapping
```

## Main Outputs

Generic strategy files:

```text
strategies/tf_generic_v1.py
strategies/mr_generic_v1.py
strategies/garch_generic_v1.py
```

Archived original asset-specific files:

```text
strategies/archive/tf_asset01_v1.py
strategies/archive/mr_asset10_v1.py
strategies/archive/garch_asset07_v1.py
```

Standardized grid configs:

```text
configs/grids/single_strat/tf/baseline/core4_v1.json
configs/grids/single_strat/tf/refined/refined_v1.json
configs/grids/single_strat/mr/baseline/core4_v1.json
configs/grids/single_strat/mr/refined/refined_v1.json
configs/grids/single_strat/garch/baseline/core4_v1.json
configs/grids/single_strat/garch/refined/refined_v1.json
```

Standardized experiment timeline:

```text
configs/timeline.json
```

Single-strategy run and selection scripts:

```text
scripts/single_strat/tf/run_grid_search.py
scripts/single_strat/tf/run_once.py
scripts/single_strat/tf/pick_best.py

scripts/single_strat/mr/run_grid_search.py
scripts/single_strat/mr/run_once.py
scripts/single_strat/mr/pick_best.py

scripts/single_strat/garch/run_grid_search.py
scripts/single_strat/garch/run_once.py
scripts/single_strat/garch/pick_best.py

scripts/single_strat/common/pick_best_common.py
```

Evaluation and maintenance helpers:

```text
scripts/evaluation/compare_experiments.py
scripts/evaluation/evaluate_part1_combo_from_best.py
scripts/evaluation/evaluate_part2_from_best.py
scripts/maintenance/archive_legacy_experiment.py
scripts/common_paths.py
```

## Included Reproducible Output

The Stage 1 archive now includes the standard regenerated experiment output:

```text
output/experiments/ca3_stage1_generic/
```

This directory contains the Part 1 grid searches, robust-selection records, IS/OOS/FULL best runs, the combined three-leg run, and the Part 2 transfer validation generated from the selected Part 1 parameters.

The most useful summary files for CA3 report evidence are:

```text
output/experiments/ca3_stage1_generic/experiment_record.json
output/experiments/ca3_stage1_generic/part2/transfer_summary.csv
output/experiments/ca3_stage1_generic/part2/transfer_record.json
```

## Optimization Narrative

This branch is mostly a structural and research-process optimization, not just a parameter tweak.

The important changes were:

1. Strategy logic was decoupled from fixed asset names.
2. Each strategy family received a consistent runner layout.
3. Grid search and best-parameter selection became repeatable.
4. IS/OOS/FULL split dates were centralized in `configs/timeline.json`.
5. Old asset-specific implementations were retained in `strategies/archive/` for traceability.

This made the later stages possible:

- Stage 2 used the selected generic ideas to build the presubmission three-leg `team01.py`.
- Stage 3 used the generic runners to scan TF/MR/GARCH across all ten assets.

## Relationship To Stage 2

Stage 2 branch:

```text
coursework_3/stage-2-presubmission-team01
```

Stage 2 did not redo the full single-strategy optimization. It packaged the outputs of this stage into one assignment-compliant file:

```text
TF generic idea    -> series_1
MR generic idea    -> series_10
GARCH generic idea -> series_7
```

That produced the presubmission three-leg strategy in `strategies/team01.py`.

## Relationship To Stage 3

Stage 3 branch:

```text
origin/cross-asset-scan
```

The cross-asset scan depended on this stage. Without generic strategies and standardized runners, the team could not systematically run:

```text
3 strategy families x 10 assets
```

The Stage 3 branch later used the resulting matrix to revisit asset mapping, simplify the final portfolio, and add stronger allocation/risk controls.

## Useful Evidence Commands

```powershell
git log 58afc66^1..stage1-generic-single-strats --oneline --date=short --pretty=format:"%h %ad %s"
git diff --stat 58afc66^1..stage1-generic-single-strats
git diff --name-status 58afc66^1..stage1-generic-single-strats
```

If the tag is not available locally, use the original remote branch name:

```powershell
git log 58afc66^1..origin/refine-single-strats --oneline --date=short --pretty=format:"%h %ad %s"
git diff --stat 58afc66^1..origin/refine-single-strats
git diff --name-status 58afc66^1..origin/refine-single-strats
```

