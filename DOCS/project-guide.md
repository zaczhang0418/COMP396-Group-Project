# Project Guide

This document combines the previous root-level README, installation guide, and project code summary.

## Overview

BT396 is the backtesting framework used for the COMP396 group project. It is built on Backtrader and provides a controlled environment where strategies are run under standardised rules, including slippage, bankruptcy checks, overspend guards, and portfolio-level result reporting.

The repository also contains coursework archive branches, EDA tooling, generated evidence outputs, and strategy experiments used in the final report.

## Installation

These steps assume Windows PowerShell from the project root.

1. Install Python 3.10 or newer.
2. Create and activate a virtual environment:

```powershell
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:

```powershell
pip install --upgrade pip
pip install -r DOCS\requirements.txt
```

The dependency list is stored in [requirements.txt](requirements.txt).

## Running The Backtester

The entry point is [main.py](../main.py). It loads a strategy from [strategies](../strategies) and runs it against CSV data from [DATA](../DATA).

Basic usage:

```powershell
python main.py --strategy <strategy_name>
```

Example:

```powershell
python main.py --strategy copycat
```

Run with debug logging:

```powershell
python main.py --strategy copycat --debug
```

Run with a specific dataset folder:

```powershell
python main.py --strategy copycat --data-dir .\DATA\PART1
```

## EDA Workflow

EDA tools live under [EDA](../EDA), with plotting scripts in [EDA/plotting](../EDA/plotting).
EDA-specific runners, notebooks, and notes are kept inside [EDA/scripts](../EDA/scripts), [EDA/notebooks](../EDA/notebooks), and [EDA/docs](../EDA/docs).

The current tracked data folders are:

```text
DATA/PART1/
DATA/PART2/
DATA/PART3/
DATA/PART123/
```

Run the EDA batch script with a dataset name. `ALL` runs the stage 4 workflow for Part 1, Part 2, Part 3, and the merged `PART123` overview dataset:

```powershell
.\EDA\run_all_eda.bat ALL
.\EDA\run_all_eda.bat PART1
.\EDA\run_all_eda.bat PART2
.\EDA\run_all_eda.bat PART3
.\EDA\run_all_eda.bat PART123
```

On the lab machine, the batch runner auto-detects `D:\Anacoda\envs\comp396\python.exe`. On another machine, set `COMP396_PYTHON` to the preferred environment Python, or make sure `python` points to the right environment.

When `PART123` is selected, the workflow merges Part 1, Part 2, and Part 3:

```powershell
python EDA\scripts\merge_data_parts.py
python EDA\scripts\merge_data_parts.py --parts PART1 PART2 PART3 --output PART123
```

Stage 4 overview summaries are saved under `EDA/output/stage4_overview`.

The active Stage 4 EDA runner keeps only strategy-relevant chart families: autocorrelation, correlation, GARCH, Hurst, return histograms, quantile analysis, and volatility. Earlier exploratory candlestick, seasonality, RSI, and volume/MFI plots are not part of the active Stage 4 workflow.

## Project Structure

```text
COMP396-Group-Project/
  main.py                 Backtester entry point
  config.yaml             Default config
  DATA/                   Tracked coursework data folders
  EDA/                    EDA loader, plotting scripts, EDA runners, notebooks, and EDA notes
  framework/              Core framework logic
  EDA/notebooks/          EDA notebook-based analysis
  output/                 Generated strategy outputs on selected branches
  scripts/                Strategy experiment, packaging, and maintenance scripts
  strategies/             Example, generic, archive, and Team01 strategies
  tests/                  Framework rule tests
  DOCS/                   Project documentation and dependency list
```

## Core Framework Files

### `framework/analyzers.py`

Calculates strategy performance metrics from the backtest results. This includes equity curve analysis, drawdown, PnL, and reporting values used in output summaries.

### `framework/data_loader.py`

Loads OHLCV CSV files and prepares them for the backtesting engine. It supports loading multiple aligned series from a selected data directory.

### `framework/plotting.py`

Creates result charts such as equity curves, underwater plots, per-series PnL charts, and dashboards.

### `framework/strategies_loader.py`

Discovers and imports strategy classes from the [strategies](../strategies) directory so that `main.py` can run them by name.

### `framework/strategy_base.py`

Defines the base strategy interface and helper methods used by project strategies. New strategies should inherit from this base class.

## Strategy Areas

The repository includes several strategy categories:

- Example framework strategies, such as `copycat`, `fixed`, and `sma_cross`.
- Diagnostic and stress-test strategies, such as `p_bankrupt`, `p_big_spender`, and `p_random`.
- Generic coursework strategy families, including trend following, mean reversion, and GARCH/regime logic.
- Team submission strategies such as `team01.py` on selected coursework archive branches.

Combined strategy versions are named `V1`, `V2`, and `V3` in the report. We do not use `V0` for the initial combined strategy.

For the current branch hierarchy and which branch contains each stage of the coursework evidence, see [branch-archive.md](branch-archive.md).

## Scripts

### `EDA/scripts/merge_data_parts.py`

Builds merged data folders from selected `DATA/PART*` inputs. By default it creates `DATA/PART123` from Part 1, Part 2, and Part 3:

```powershell
python EDA\scripts\merge_data_parts.py --parts PART1 PART2 PART3 --output PART123
```

### `EDA/scripts/run_eda_stage4.py`

Runs the stage 4 EDA workflow and builds the Part 1 / Part 2 / Part 3 overview outputs.

### `scripts/distribution/make_dist.py`

Creates a clean distribution ZIP of the project.

```powershell
python scripts\distribution\make_dist.py
python scripts\distribution\make_dist.py --no-output
python scripts\distribution\make_dist.py --name BT396_0.1.0_win.zip
```

### `scripts/single_strat/`

Contains reusable runners and selectors for generic single-strategy experiments.

### `scripts/evaluation/`

Contains evaluation helpers for comparing outputs and testing selected parameters on later datasets.

## Testing

Framework tests are stored in [tests](../tests).

Run tests from the project root:

```powershell
python -m pytest
```

If `pytest` is not installed, install it in the active environment:

```powershell
pip install pytest
```

## Output Policy

`output/` is normally generated by local runs. Some archive branches intentionally track selected output folders so teammates can view evidence without rerunning long experiments.

Do not merge every archive branch into `main` just to collect outputs. Use the branch archive document to decide which output branch is relevant.

## Packaging Notes

When distributing the project, it is safe to exclude:

- `.git/`
- `.idea/`
- `.vscode/`
- `__pycache__/`
- `.pytest_cache/`
- `.mypy_cache/`
- OS junk files such as `.DS_Store` and `Thumbs.db`

Use `--no-output` if generated outputs should be excluded from the ZIP.
