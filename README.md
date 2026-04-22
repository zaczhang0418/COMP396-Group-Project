# COMP396 Group Project

This repository contains the COMP396 backtesting framework, strategy experiments, EDA workflow, data partitions, and report evidence for the group project.

This branch focuses on cleaning and updating the EDA workflow so that Part 1, Part 2, Part 3, and the combined Part 1+2+3 dataset can be reproduced from one place.

## Current Branch Focus

Branch:

```text
archive/eda/stage-4-part123-overview
```

Main EDA updates in this branch:

- Moved EDA runners, notebooks, docs, and helper scripts under `EDA/`.
- Added `DATA/PART123`, generated from `DATA/PART1`, `DATA/PART2`, and `DATA/PART3`.
- Removed the old `DATA/COMBINED` folder from the active EDA workflow.
- Removed unused EDA chart families from the active workflow: candlesticks, seasonality, RSI analysis, and standalone volume analysis.
- Kept strategy-relevant EDA outputs: ACF/PACF, correlation heatmap, GARCH, Hurst, return histograms, quantile analysis, and volatility.
- Added `EDA/settings.py` so rolling-window assumptions are defined in one place.
- Added run reports, analysis reports, and an executed EDA notebook output.
- Updated `configs/timeline.json` so it now includes `part3` and `part123`.

## Project Structure

```text
COMP396-Group-Project/
  DATA/                  Input datasets: PART1, PART2, PART3, PART123
  EDA/                   EDA scripts, plotting modules, notebook, docs, and outputs
  DOCS/                  Project guide, branch archive, and requirements
  configs/               Timeline and grid-search configuration
  framework/             Backtesting framework code
  scripts/               Strategy, evaluation, maintenance, and distribution scripts
  strategies/            Strategy implementations
  tests/                 Tests
  README.md              Root project overview
```

## Important Documents

| Document | Purpose |
| --- | --- |
| [Project Guide](DOCS/project-guide.md) | Installation, running instructions, project structure, and code summary |
| [Branch Archive](DOCS/branch-archive.md) | Coursework branch map and evidence notes |
| [EDA Stage 4 Overview](EDA/docs/stage4-overview.md) | Current EDA workflow, chart set, commands, and tracked outputs |
| [Latest EDA Analysis](EDA/docs/latest-analysis.md) | Extracted EDA analysis values from the latest run |
| [Latest EDA Run](EDA/docs/latest-run.md) | Latest run status, logs, and generated output summary |
| [EDA Notebook](EDA/notebooks/EDA_Report_and_Justification.ipynb) | Executed notebook version of the current EDA report |
| [Requirements](DOCS/requirements.txt) | Python dependency list |

## Environment

On this machine, the EDA batch runner auto-detects the Anaconda environment:

```text
D:\Anacoda\envs\comp396\python.exe
```

If needed, install dependencies with:

```powershell
pip install -r DOCS\requirements.txt
```

## EDA Workflow

Run the full EDA workflow:

```powershell
.\EDA\run_all_eda.bat ALL
```

Run only the tracked overview:

```powershell
.\EDA\run_all_eda.bat OVERVIEW
```

Run one dataset:

```powershell
.\EDA\run_all_eda.bat PART1
.\EDA\run_all_eda.bat PART2
.\EDA\run_all_eda.bat PART3
.\EDA\run_all_eda.bat PART123
```

Each run refreshes:

```text
EDA/docs/latest-run.md
EDA/docs/latest-analysis.md
EDA/notebooks/EDA_Report_and_Justification.ipynb
```

The tracked overview outputs are stored in:

```text
EDA/output/stage4_overview/
```

Detailed per-dataset chart folders under `EDA/output/PART1`, `EDA/output/PART2`, `EDA/output/PART3`, and `EDA/output/PART123` are generated locally and ignored by Git by default.

## Active EDA Settings

The current EDA workflow does not use a fixed calendar sub-period for charts. It uses the requested dataset and applies strategy-relevant rolling windows from `EDA/settings.py`:

- Trading days per year: `252`
- ACF/PACF lags: `40`
- Hurst rolling window: `252`
- Volatility windows: `20` and `60`
- ATR window: `14`
- Quantile tests: `STR_21D` and `MOM_126D`, both evaluated on 21-day forward returns

## Data Timeline

Current data partitions:

| Dataset | Date range |
| --- | --- |
| `PART1` | 2069-12-08 to 2072-09-02 |
| `PART2` | 2072-09-03 to 2075-05-30 |
| `PART3` | 2075-05-31 to 2078-02-23 |
| `PART123` | 2069-12-08 to 2078-02-23 |

The canonical timeline is stored in `configs/timeline.json`.

## Backtester

The project still includes the main backtesting framework and strategy scripts. Basic usage:

```powershell
python main.py --strategy <strategy_name>
```

For the broader project guide and strategy archive notes, see:

```text
DOCS/project-guide.md
DOCS/branch-archive.md
```

## Git Notes

This branch intentionally keeps only the EDA-relevant workflow active. Generated detailed chart folders are ignored, while the compact Stage 4 overview and EDA documentation are kept for reporting.
