# Coursework Branch Archive

本文档用于整理 coursework 后续报告所需的 branch 过程留档。当前主线可以按三个 stage 叙述：

1. Stage 1: 将三个资产绑定的单策略系统化重构为 generic 策略。
2. Stage 2: 用 generic 单策略拼装 presubmission 版本的 `team01.py`。
3. Stage 3: 做 3 x 10 cross-asset scan，基于新资产映射矩阵设计优化组合策略。

推荐统一使用截图里的虚拟环境运行复现实验：

```powershell
C:\Python\envs\comp396\python.exe --version
C:\Python\envs\comp396\python.exe -c "import backtrader, numpy, pandas; print('deps ok')"
```

已确认本机环境为 Python 3.11.13，且 `backtrader`、`numpy`、`pandas` 可导入。

## Branch Timeline

| Stage | Branch | Status vs `main` | Key commit(s) | Role in report |
| --- | --- | --- | --- | --- |
| Stage 1 | `origin/refine-single-strats` | 已 merge 到 `main` via PR #11 | `38e1ce1`, `6b28fe9`, `2de51f6` | 说明我们如何从固定资产策略进化到可跨资产复用的研究框架 |
| Stage 2 | `origin/presubmission-team-strategy` | 未 merge，基于 `main` 单独保留 | `f7226fe` | 说明第一次正式 submission 文件如何由三个 generic leg 组合而成 |
| Stage 3 | `origin/cross-asset-scan` | 未 merge，基于 `main` 单独保留 | `ac73f40`, `3b3d6e5` | 说明 cross-asset matrix 如何驱动新组合策略和最终优化方向 |

Related earlier foundations:

- `origin/tr_asset01_v1`: 最早的 TF asset01 单策略。
- `origin/mr_asset10_v1`: 最早的 MR asset10 单策略。
- `origin/gr_asset07-v1`: 最早的 GARCH asset07 单策略。
- `origin/feature/combo-tf01-mr10-ga07-v1`: 早期三腿组合策略，先于本轮 generic 重构。

## EDA Archive Branches

EDA should be treated as its own archive group, not as ordinary merged support work. It is part of the report evidence chain because it explains the market data, motivates strategy choice, and supports later discussion of why TF/MR/GARCH were reasonable families to test.

Recommended EDA archive group:

| Branch | Status | Role |
| --- | --- | --- |
| `origin/feature/run-eda-diagnostics` | merged through earlier project history | Main EDA diagnostics workflow and notebook/report updates |
| `origin/eda_part2` | merged into `main` via PR #10 | Part 2 and combined-data EDA workflow |
| `origin/feat/add-eda-plotting` | merged/reverted earlier, but still useful historically | Batch candlestick plotting and early visual exploration |

How to use this in the report:

- Keep EDA as a separate section before strategy design.
- Use it to explain observed asset behaviours, volatility regimes, trends, mean-reversion patterns, and any anomalies.
- Treat EDA outputs as motivation and diagnostics, not as a minor code-support branch.
- When writing the branch history, describe EDA as "data understanding and hypothesis generation", while Stage 1-3 describe "strategy engineering and optimization".

Suggested archive label:

```text
EDA evidence archive
  feature/run-eda-diagnostics
  eda_part2
  feat/add-eda-plotting
```

Evidence commands:

```powershell
git log origin/feature/run-eda-diagnostics --oneline --date=short --pretty=format:"%h %ad %s" -n 12
git log origin/eda_part2 --oneline --date=short --pretty=format:"%h %ad %s" -n 8
git diff --stat origin/main...origin/eda_part2
```

## Stage 1: Refine Single Strategies Into Generic Workflow

Branch:

```text
origin/refine-single-strats
```

Merge status:

```text
Merged into main by 58afc66 on 2026-03-13
Merge PR: #11 refine-single-strats
Pre-merge base: 3a8e639
Branch tip: 2de51f6
```

Commit narrative:

| Commit | Date | Meaning |
| --- | --- | --- |
| `38e1ce1` | 2026-03-11 | Freeze `pre_refine_v0` baseline and unify experiment layout |
| `6b28fe9` | 2026-03-12 | Add `refined_v1` single-strategy workflow |
| `2de51f6` | 2026-03-13 | Refactor single strategies for generic cross-asset prep |

Main outputs:

- Added generic strategy files:
  - `strategies/tf_generic_v1.py`
  - `strategies/mr_generic_v1.py`
  - `strategies/garch_generic_v1.py`
- Archived asset-specific strategy files:
  - `strategies/archive/tf_asset01_v1.py`
  - `strategies/archive/mr_asset10_v1.py`
  - `strategies/archive/garch_asset07_v1.py`
- Reorganized grid configs:
  - `configs/grids/single_strat/tf/baseline/core4_v1.json`
  - `configs/grids/single_strat/tf/refined/refined_v1.json`
  - `configs/grids/single_strat/mr/baseline/core4_v1.json`
  - `configs/grids/single_strat/mr/refined/refined_v1.json`
  - `configs/grids/single_strat/garch/baseline/core4_v1.json`
  - `configs/grids/single_strat/garch/refined/refined_v1.json`
- Added shared experiment timeline:
  - `configs/timeline.json`
- Added reusable single-strategy runners and selectors:
  - `scripts/single_strat/tf/run_grid_search.py`
  - `scripts/single_strat/tf/run_once.py`
  - `scripts/single_strat/tf/pick_best.py`
  - `scripts/single_strat/mr/run_grid_search.py`
  - `scripts/single_strat/mr/run_once.py`
  - `scripts/single_strat/mr/pick_best.py`
  - `scripts/single_strat/garch/run_grid_search.py`
  - `scripts/single_strat/garch/run_once.py`
  - `scripts/single_strat/garch/pick_best.py`
  - `scripts/single_strat/common/pick_best_common.py`
- Added evaluation/maintenance helpers:
  - `scripts/evaluation/compare_experiments.py`
  - `scripts/evaluation/evaluate_part1_combo_from_best.py`
  - `scripts/evaluation/evaluate_part2_from_best.py`
  - `scripts/maintenance/archive_legacy_experiment.py`
  - `scripts/common_paths.py`

What changed conceptually:

- Before Stage 1, the three main strategy ideas were tied to fixed instruments:
  - TF on `series_1` / asset01
  - GARCH on `series_7` / asset07
  - MR on `series_10` / asset10
- Stage 1 extracted these ideas into generic implementations that accept `data_name`, `asset_tag`, `strategy_id`, and common run metadata.
- This made later cross-asset research possible because the same TF/MR/GARCH logic could be run against all 10 assets instead of only their original assets.

Useful report angle:

> We first separated strategy logic from asset identity. This converted three manually tuned, asset-specific prototypes into a reusable research pipeline with common grid-search, parameter selection, and IS/OOS/FULL evaluation conventions.

Evidence commands:

```powershell
git log 58afc66^1..origin/refine-single-strats --oneline --date=short --pretty=format:"%h %ad %s"
git diff --stat 58afc66^1..origin/refine-single-strats
git diff --name-status 58afc66^1..origin/refine-single-strats
```

Local results currently visible on `main`:

```text
output/part1/asset01/tf_core4_v1/best_params.json
output/part1/asset07/garch_core4_v1/best_params.json
output/part1/asset10/mr_core4_v1/best_params.json
```

Best params currently present:

```json
TF asset01:
{
  "p_ema_short": 10.0,
  "p_ema_long": 60.0,
  "p_hurst_min_soft": 0.55,
  "p_stop_multiplier": 2.5
}

GARCH asset07:
{
  "p_sigma_q_low": 0.3,
  "p_sigma_q_high": 0.8,
  "p_mult_mid": 0.6,
  "p_mult_high": 0.4
}

MR asset10:
{
  "p_lookback": 40,
  "p_entry_z": 2.0,
  "p_exit_z": 0.0,
  "p_stop_mult": 2.0
}
```

## Stage 2: Presubmission Team Strategy

Branch:

```text
origin/presubmission-team-strategy
```

Merge status:

```text
Not merged into main
Base: main at 58afc66
Branch tip: f7226fe
```

Commit narrative:

| Commit | Date | Meaning |
| --- | --- | --- |
| `f7226fe` | 2026-03-15 | Add unoptimized Team 01 presubmission strategy |

Main outputs:

- Added `strategies/team01.py`
- Added `README_team01.md`

Strategy structure:

- Single-file submission strategy named `TeamStrategy`.
- Uses three legs:
  - TF leg on `series_1`
  - MR leg on `series_10`
  - GARCH leg on `series_7`
- Default capital weights in the file:
  - `w_tf = 0.45`
  - `w_mr = 0.45`
  - `w_ga = 0.10`
- Runtime does not depend on external JSON files or helper scripts, matching the assignment requirement for a standalone `team01.py`.

Useful report angle:

> The presubmission branch translated the research framework into the required deployment format: a single `team01.py` file. It preserved the three strongest existing ideas and embedded their selected/default parameters directly into the strategy so that it could run under the marking framework without external dependencies.

Reproduction command from branch README:

```powershell
C:\Python\envs\comp396\python.exe main.py --strategy team01 --data-dir .\DATA\PART2 --fromdate 2072-09-03 --todate 2075-05-30 --output-dir output\presubmission_part2
```

Local presubmission outputs currently visible:

| Dataset/output dir | Final value | true PD ratio | open PnL PD ratio | Activity | Bankrupt |
| --- | ---: | ---: | ---: | ---: | --- |
| `output/presubmission_part1` | 948,298.86 | -0.6922 | -0.2841 | 67.27% | false |
| `output/presubmission_part2` | 1,166,853.42 | 2.2440 | 3.3408 | 81.48% | false |
| `output/presubmission_part3` | 1,130,900.67 | 1.3152 | 3.2499 | 90.30% | false |

Interpretation for report:

- Part 1 result was weak/negative, so this version should be described as presubmission or unoptimized rather than final.
- Part 2 and Part 3 local outputs were profitable and non-bankrupt, which gave enough confidence to continue refining the deployment format.
- The branch is useful as an audit point: it shows the first clean handoff from research scripts to assignment-compliant strategy packaging.

Evidence commands:

```powershell
git log main..origin/presubmission-team-strategy --oneline --date=short --pretty=format:"%h %ad %s"
git diff --stat main..origin/presubmission-team-strategy
git show origin/presubmission-team-strategy:README_team01.md
```

## Stage 3: Cross-Asset Scan And Optimized Team Strategy

Branch:

```text
origin/cross-asset-scan
```

Merge status:

```text
Not merged into main
Base: main at 58afc66
Branch tip: 3b3d6e5
```

Commit narrative:

| Commit | Date | Meaning |
| --- | --- | --- |
| `ac73f40` | 2026-03-14 | Completed 3 strategies x 10 assets cross scan, not yet analyzed/tuned |
| `3b3d6e5` | 2026-03-17 | Archive optimized Team01 strategy |

Main outputs:

- Added cross-asset scan scripts:
  - `scripts/cross_asset_scan/common.py`
  - `scripts/cross_asset_scan/run_cross_asset_scan.py`
  - `scripts/cross_asset_scan/summarize_cross_asset_scan.py`
  - `scripts/cross_asset_scan/validate_cross_asset_scan_part2.py`
- Modified `scripts/single_strat/common/pick_best_common.py` to support the scan workflow.
- Added optimized `strategies/team01.py`.

Cross-asset scan design:

- Strategies scanned:
  - `tf_generic_v1`
  - `mr_generic_v1`
  - `garch_generic_v1`
- Assets scanned:
  - `asset01` to `asset10`
- Default scan tag:
  - `cross_asset_scan_v1`
- Split labels:
  - IS: `70-30`
  - OOS: `30-oos`
  - FULL: `100-full`
- Default selection mode:
  - `robust`
- Default key:
  - `true_pd_ratio`
- Summary outputs generated by the branch scripts:
  - `output/cross_asset_scan_v1/summaries/cross_asset_long.csv`
  - `output/cross_asset_scan_v1/summaries/matrix_3x10.csv`
  - `output/cross_asset_scan_v1/summaries/asset_strategy_assignment.csv`
  - `output/cross_asset_scan_v1/summaries/summary.json`
  - `output/cross_asset_scan_v1/summaries/part2_validation.csv`

Optimized `team01.py` structure:

- The optimized branch does not simply reuse the old three-leg `series_1/series_7/series_10` allocation.
- It changes the final portfolio mapping to a two-leg structure:
  - TF leg on `series_1`
  - MR leg on `series_9`
- Default capital weights:
  - `w_tf = 0.65`
  - `w_mr09 = 0.35`
- Adds dynamic allocation and risk controls:
  - performance-aware budget adjustment
  - allocation floors and caps
  - loss-streak freeze logic
  - TF Hurst/trend/hot-move filters
  - MR z-score and volatility percentile filter
  - gross exposure cap
  - rebalance tolerance

Useful report angle:

> After making the three single strategies asset-agnostic, we ran a systematic 3 x 10 scan to test whether each strategy idea generalized across instruments. The scan produced both a performance matrix and an asset-to-strategy assignment table. This shifted the final portfolio from the original TF/MR/GARCH asset01/10/07 bundle to an optimized mapping focused on TF asset01 and MR asset09, with dynamic allocation and additional risk controls.

Evidence commands:

```powershell
git log main..origin/cross-asset-scan --oneline --date=short --pretty=format:"%h %ad %s"
git diff --stat main..origin/cross-asset-scan
git diff --name-status main..origin/cross-asset-scan
git show origin/cross-asset-scan:scripts/cross_asset_scan/common.py
git show origin/cross-asset-scan:strategies/team01.py
```

Reproduction workflow on the branch:

```powershell
git switch cross-asset-scan

C:\Python\envs\comp396\python.exe scripts\cross_asset_scan\run_cross_asset_scan.py --scan-tag cross_asset_scan_v1 --strategies all --assets all --selection-mode robust --key true_pd_ratio --runs is,oos,full --skip-existing

C:\Python\envs\comp396\python.exe scripts\cross_asset_scan\validate_cross_asset_scan_part2.py --scan-tag cross_asset_scan_v1 --strategies all --assets all --skip-existing

C:\Python\envs\comp396\python.exe scripts\cross_asset_scan\summarize_cross_asset_scan.py --scan-tag cross_asset_scan_v1 --strategies all --assets all --matrix-metric oos_true_pd_ratio
```

Reproduction from the original branch:

```powershell
git switch cross-asset-scan

C:\Python\envs\comp396\python.exe scripts\cross_asset_scan\summarize_cross_asset_scan.py --scan-tag cross_asset_scan_v1 --strategies all --assets all --matrix-metric oos_true_pd_ratio
```

Current evidence gap:

- On the current `main` worktree, `scripts/cross_asset_scan/` is absent because Stage 3 was not merged.
- On the current `main` worktree, `output/cross_asset_scan_v1/` is also not present.
- To include actual matrix values in the report, we need either:
  - switch into `cross-asset-scan` and locate existing generated outputs, or
  - rerun the cross-asset scan from that branch with the `comp396` environment.

## Branch Organization Plan

Goal:

- Keep the report evidence chain intact.
- Make Git Graph easier to read.
- Avoid deleting useful coursework history before the report is finished.
- Avoid rewriting history.

Current merge status from `main`:

```text
Merged into origin/main:
  origin/Docs/add-project-code-summary
  origin/eda_part2
  origin/feat/add-eda-plotting
  origin/feature/combo-tf01-mr10-ga07-v1
  origin/feature/run-eda-diagnostics
  origin/fix_bug_para
  origin/fix_sh_jy
  origin/gr_asset07-v1
  origin/mr_asset10_v1
  origin/refine-single-strats
  origin/testing
  origin/tr_asset01_v1

Not merged into origin/main:
  origin/cross-asset-scan
  origin/part1paramsinpart2
  origin/presubmission-team-strategy
```

Recommended branch groups:

```text
Core coursework strategy branches
  main
  refine-single-strats
  presubmission-team-strategy
  cross-asset-scan

EDA evidence archive
  feature/run-eda-diagnostics
  eda_part2
  feat/add-eda-plotting

Prototype strategy branches
  tr_asset01_v1
  mr_asset10_v1
  gr_asset07-v1
  feature/combo-tf01-mr10-ga07-v1
  testing

Validation / transition branches
  part1paramsinpart2

Merged engineering support branches
  Docs/add-project-code-summary
  fix_sh_jy
  fix_bug_para
```

Recommended cleanup order:

1. Safe now: add milestone tags.
2. During active cleanup, switch to the original branch names and commit directly there.
3. Safe after report evidence is checked: create `archive/...` remote branch names.
4. Only after team agreement: delete old noisy remote branch names.

### Step 1: Add Milestone Tags

Tags make the report chronology stable even if branch names later move or are archived.

```powershell
git tag stage1-generic-single-strats origin/refine-single-strats
git tag stage2-presubmission-team01 origin/presubmission-team-strategy
git tag stage3-cross-asset-optimized origin/cross-asset-scan
git tag eda-v1-diagnostics origin/feature/run-eda-diagnostics
git tag eda-part2-combined origin/eda_part2
```

Push tags if the team wants them visible on GitHub:

```powershell
git push origin stage1-generic-single-strats stage2-presubmission-team01 stage3-cross-asset-optimized eda-v1-diagnostics eda-part2-combined
```

### Step 2: Switch Original Branches For Active Cleanup

Do not create parallel active branches while cleaning up the historical work. Use the original branch names so the development chronology remains simple.

```powershell
git status --short --branch
git switch presubmission-team-strategy
git switch cross-asset-scan
git switch part1paramsinpart2
```

Before switching away from a branch, make sure its work is either committed or intentionally stashed. Do not delete or rename the original remote branches.

### Step 3: Optional Remote Archive Namespace

If the Git Graph is still too noisy, create new archive-named branches pointing to the same commits. Do this before deleting old names.

```powershell
git branch archive/eda/run-eda-diagnostics origin/feature/run-eda-diagnostics
git branch archive/eda/part2-combined origin/eda_part2
git branch archive/eda/candlestick-plotting origin/feat/add-eda-plotting

git branch coursework_1/prototype/tf-asset01-v1 origin/tr_asset01_v1
git branch coursework_1/prototype/mr-asset10-v1 origin/mr_asset10_v1
git branch coursework_1/prototype/garch-asset07-v1 origin/gr_asset07-v1
git branch coursework_1/prototype/combo-tf01-mr10-garch07-v1 origin/feature/combo-tf01-mr10-ga07-v1

git branch coursework_3/stage-1-generic-single-strats origin/refine-single-strats
git branch coursework_3/stage-2-presubmission-team01 origin/presubmission-team-strategy
git branch coursework_3/stage-3-cross-asset-scan origin/cross-asset-scan
git branch coursework_3/validation/part1-params-on-part2 origin/part1paramsinpart2

git branch archive/support/docs-code-summary origin/Docs/add-project-code-summary
git branch archive/support/path-fixes origin/fix_sh_jy
git branch archive/support/framework-output-fixes origin/fix_bug_para
```

Push archive branches:

```powershell
git push origin archive/eda/run-eda-diagnostics archive/eda/part2-combined archive/eda/candlestick-plotting
git push origin coursework_1/prototype/tf-asset01-v1 coursework_1/prototype/mr-asset10-v1 coursework_1/prototype/garch-asset07-v1 coursework_1/prototype/combo-tf01-mr10-garch07-v1
git push origin coursework_3/stage-1-generic-single-strats coursework_3/stage-2-presubmission-team01 coursework_3/stage-3-cross-asset-scan coursework_3/validation/part1-params-on-part2
git push origin archive/support/docs-code-summary archive/support/path-fixes archive/support/framework-output-fixes
```

### Step 4: Optional Deletion Of Old Remote Names

Only do this after:

- tags have been pushed,
- archive branches have been pushed,
- the team agrees,
- report evidence has been copied into this document or the report draft.

Do not delete these before the report is finished:

```text
origin/presubmission-team-strategy
origin/cross-asset-scan
origin/part1paramsinpart2
```

Old merged names that could be deleted later:

```powershell
git push origin --delete Docs/add-project-code-summary
git push origin --delete eda_part2
git push origin --delete feat/add-eda-plotting
git push origin --delete feature/run-eda-diagnostics
git push origin --delete feature/combo-tf01-mr10-ga07-v1
git push origin --delete fix_sh_jy
git push origin --delete fix_bug_para
git push origin --delete tr_asset01_v1
git push origin --delete mr_asset10_v1
git push origin --delete gr_asset07-v1
git push origin --delete testing
```

After remote cleanup:

```powershell
git fetch --prune
```

Recommended practical choice for now:

- Do Step 1 immediately.
- Do Step 2 branch-by-branch as we clean the project.
- Do not delete any remote branches yet.
- Use Step 3 only if Git Graph remains unreadable.
- Leave Step 4 until the report is finished.

Applied locally on 2026-04-16:

```text
Created local milestone tags:
  eda-part2-combined
  eda-v1-diagnostics
  stage1-generic-single-strats
  stage2-presubmission-team01
  stage3-cross-asset-optimized

Created and then removed sibling worktrees after review:
  C:/Users/30745/Desktop/COMP396/COMP396-presubmission
  C:/Users/30745/Desktop/COMP396/COMP396-cross-asset-scan
  C:/Users/30745/Desktop/COMP396/COMP396-validation-part1params

Presubmission cleanup commit preserved on local branch:
  presubmission-team-strategy -> 55b5fa8 docs(presubmission): archive stage 2 team strategy
```

No branches were deleted or renamed.

Working rule after review:

- During active cleanup, modify the original historical branch names.
- Do not create parallel coursework alias branches for active development.
- Do not use extra worktrees for this cleanup pass.
- Keep the `coursework_1/...`, `coursework_3/...`, and `archive/...` naming scheme as a future remote archive/alias plan only.
- This keeps the development chronology simple: original branch -> cleanup/documentation commits.

### Branch Naming Convention Going Forward

Important Git naming note:

- `origin/...` is not part of the branch name. It only means "remote-tracking branch from the remote named origin".
- The real inconsistency is that the project currently mixes:
  - bare names: `eda_part2`, `testing`, `fix_bug_para`
  - feature namespaces: `feature/...`
  - shorter feature namespaces: `feat/...`
  - coursework-stage names: `refine-single-strats`, `presubmission-team-strategy`, `cross-asset-scan`

Recommended future naming scheme:

```text
coursework_3/stage-1-generic-single-strats
coursework_3/stage-2-presubmission-team01
coursework_3/stage-3-cross-asset-scan

archive/eda/run-eda-diagnostics
archive/eda/part2-combined
archive/eda/candlestick-plotting

coursework_1/prototype/tf-asset01-v1
coursework_1/prototype/mr-asset10-v1
coursework_1/prototype/garch-asset07-v1
coursework_1/prototype/combo-tf01-mr10-garch07-v1

coursework_3/validation/part1-params-on-part2

archive/support/docs-code-summary
archive/support/path-fixes
archive/support/framework-output-fixes
```

Recommended naming rules for new work:

- Use `coursework_3/stage-N-short-description` for report-critical Coursework 3 stages.
- Use `archive/eda/...` for data exploration and diagnostic branches.
- Use `coursework_1/prototype/...` for early strategy experiments from the first coursework cycle.
- Use `coursework_3/validation/...` for Coursework 3 evaluation-only branches.
- Use `fix/...` for small current bugfixes.
- Use `docs/...` for current documentation work.
- Avoid mixing `feat/` and `feature/`; if needed, use `feature/...` consistently for active product-style feature work, but for this project `coursework_1/...`, `coursework_3/...`, and `archive/...` are clearer.

What to do now:

1. Keep all old branches untouched until the report evidence is stable.
2. Use milestone tags as stable references.
3. Switch to original branches directly when cleaning them.
4. If the Git Graph view is visually noisy, filter to:
   - `main`
   - tags beginning with `stage`
   - current original branch under cleanup
5. Later, if the team wants a cleaner remote, create new archive-named remote branches first.
6. Only after everyone agrees, delete old noisy remote names. This is optional and should wait until after report drafting.

Why not rename/delete immediately:

- Remote branch "renaming" is effectively create-new-name plus delete-old-name.
- Since old branch names may be referenced in PRs, commit history, chat, screenshots, and report notes, deleting or renaming too early can make evidence harder to trace.
- Adding archive aliases now is safe, but if old names stay too, Git Graph may temporarily become even busier.

## Suggested Report Structure

1. Baseline and problem:
   - Three initial strategies existed as successful but asset-specific prototypes.
   - This limited systematic validation and made it hard to know whether performance came from logic quality or asset choice.

2. Stage 1 methodology:
   - Convert TF/MR/GARCH to generic strategies.
   - Standardize grids, split dates, run folders, and selection scripts.
   - Preserve old asset-specific strategies in `strategies/archive/` as baselines.

3. Stage 2 submission packaging:
   - Build assignment-compliant `team01.py`.
   - Combine TF asset01, MR asset10, GARCH asset07.
   - Evaluate on Part 2 and keep outputs as presubmission evidence.

4. Stage 3 cross-asset expansion:
   - Run 3 strategy families across 10 assets.
   - Build performance matrix and winner assignment table.
   - Use the evidence to revise asset mapping and simplify the deployed portfolio.

5. Final discussion:
   - Explain why generic design reduced selection bias.
   - Discuss overfitting controls: IS/OOS/FULL splits, robust selection, Part 2 validation, non-bankruptcy checks, activity thresholds.
   - Contrast presubmission vs optimized `team01.py`.

## Immediate Next Actions

1. Finish or commit the current `main` documentation update before switching branches.
2. Switch to `cross-asset-scan` using the original branch name.
3. Check whether `output/cross_asset_scan_v1/summaries/` exists on that branch.
4. If missing, rerun only the summary first; if raw scan records are missing too, rerun the full scan.
5. Copy the final `matrix_3x10.csv`, `asset_strategy_assignment.csv`, and `part2_validation.csv` values into the report appendix.
6. Decide whether final report should describe Stage 2 as "presubmission/unoptimized" and Stage 3 as "optimized/final" based on official coursework chronology.
