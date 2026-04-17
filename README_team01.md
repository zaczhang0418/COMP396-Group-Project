# Team 01 Presubmission Strategy Archive

This branch archives the Team 01 presubmission strategy in:

`strategies/team01.py`

## Archive Status

- Branch role: Stage 2 presubmission baseline.
- Working branch name used locally: `coursework_3/stage-2-presubmission-team01`.
- Original remote branch: `origin/presubmission-team-strategy`.
- Strategy file status: confirmed identical to the final submitted desktop copy at `C:\Users\30745\Desktop\Team01 Presubmission\team01.py`.
- SHA256 for both copies: `E4FC4B65DA7834FA791FE3B846C52B8061876D0940340B1E0B5B1225570E82BF`.

## Strategy Summary

The presubmission portfolio is a three-leg strategy:

| Leg | Data feed | Strategy idea | Default capital weight |
| --- | --- | --- | ---: |
| TF | `series_1` | EMA trend-following with ATR volatility targeting and trailing stop | 0.45 |
| MR | `series_10` | z-score mean reversion with ATR volatility targeting and stop | 0.45 |
| GARCH | `series_7` | GARCH volatility-regime trend leg with EMA filter and ATR stop | 0.10 |

This version should be described as an unoptimized presubmission baseline. It packages the three strongest single-strategy ideas into a single assignment-compliant `team01.py`, but it does not yet include the later cross-asset remapping or dynamic allocation controls from Stage 3.

## Development Provenance

This branch does not contain the full single-strategy optimization history by itself. Its role is the packaging step that turns earlier optimized/generic single strategies into a deployable three-leg submission file.

The development chain is:

| Phase | Branch / evidence | Contribution |
| --- | --- | --- |
| Early single-strategy prototypes | `origin/tr_asset01_v1`, `origin/mr_asset10_v1`, `origin/gr_asset07-v1` | Developed the original TF, MR, and GARCH ideas on their first chosen assets |
| Generic single-strategy workflow | `origin/refine-single-strats` / tag `stage1-generic-single-strats` | Refactored the three asset-specific strategies into generic strategy families and standardized grid search, run-once, pick-best, and IS/OOS/FULL evaluation scripts |
| Presubmission packaging | this branch / tag `stage2-presubmission-team01` | Embedded the selected three legs into a single-file `team01.py` that satisfies the coursework submission format |

In report terms, the main optimization work before this branch lives in the single-strategy/prototype and `refine-single-strats` branches. This branch records the next step: combining those selected ideas into a practical presubmission portfolio.

The mapping used here was the pre-cross-asset mapping:

```text
TF generic idea    -> series_1
MR generic idea    -> series_10
GARCH generic idea -> series_7
```

The default parameters and weights were carried into `team01.py` so the strategy could run without external config files during marking. This design choice made the submission robust and self-contained, but it also meant that this branch is best understood as a baseline ensemble rather than the final cross-asset optimized strategy.

The later Stage 3 work in `origin/cross-asset-scan` revisited the asset mapping systematically across all ten assets and added more explicit allocation/risk controls.

## How To Run

Run through the provided backtester entrypoint (`main.py`) exactly as in the distributed framework.

Example local verification command on Part 2 data:

```powershell
C:\Python\envs\comp396\python.exe main.py --strategy team01 --data-dir .\DATA\PART2 --fromdate 2072-09-03 --todate 2075-05-30 --output-dir output\presubmission_part2
```

The CA3 archive output uses the standardized directory names listed below.

Example with debug logging:

```powershell
C:\Python\envs\comp396\python.exe main.py --strategy team01 --data-dir .\DATA\PART2 --fromdate 2072-09-03 --todate 2075-05-30 --debug --output-dir output\presubmission_part2_debug
```

At marking time, the framework can run the same strategy on Part 3 data. No additional CLI parameter overrides are required because the strategy defaults are defined inside the file.

## Included CA3 Verification Output

This branch now includes the regenerated Stage 2 presubmission baseline outputs:

```text
output/ca3_stage2_presubmission_part1/
output/ca3_stage2_presubmission_part2/
output/ca3_stage2_presubmission_part3_existing/
```

The Part 1 and Part 2 directories were regenerated locally from this branch. The Part 3 directory is a preserved copy of the existing presubmission Part 3 output, because Part 3 data is not available in this repository for rerunning.

Main summary paths:

```text
output/ca3_stage2_presubmission_part1/run_summary.json
output/ca3_stage2_presubmission_part2/run_summary.json
output/ca3_stage2_presubmission_part3_existing/run_summary.json
```

Part 2 summary:

```json
{
  "final_value": 1166853.424538599,
  "bankrupt": false,
  "bankrupt_date": null,
  "open_pnl_pd_ratio": 3.3407848322005416,
  "true_pd_ratio": 2.2440207062337763,
  "activity_pct": 81.48148148148148,
  "end_policy": "liquidate",
  "s_mult": 2.0
}
```

## Compliance With The Assignment Requirements

- The submission is a single file named `team01.py`.
- The file defines exactly one Backtrader strategy class named `TeamStrategy`.
- `TeamStrategy` subclasses `bt.Strategy`.
- The parameter list is declared at the top of the class in `params`.
- All required imports are included in the file.
- The strategy does not depend on external helper scripts, JSON parameter files, or local output folders at runtime.
- The strategy is intended to be run through `main.py` in the provided framework, matching the assignment instructions.

## Notes

- The strategy trades only the required series it uses: `series_1`, `series_7`, and `series_10`.
- For our testing, we used Part 1-selected parameters and evaluated them on Part 2 data.
- The same file is designed to work when the framework loads Part 3 data during marking.
- The Part 2 rerun completed successfully and did not bankrupt.
- The run produced many framework overspend-cancellation messages. This is an important limitation of the presubmission baseline and a useful motivation for the later Stage 3 redesign, where allocation and asset mapping were revisited.
