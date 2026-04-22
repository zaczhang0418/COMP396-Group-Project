# BT396 Backtester Framework

## Coursework 1 V1 Archive Summary

This branch is the stage 5 summary branch for Coursework 1 V1:

```text
summary/coursework_1/stage-5-v1-archive-summary
```

The V1 archive summary is documented in:

```text
DOCS/coursework_1_stage5_v1_archive_summary.md
```

This branch preserves the original stage 4 strategy logic and only adds archive documentation.

Archived CA1/V1 matrix outputs are stored by dataset:

```text
output/coursework_1_stage5_v1_archive/PART1/
output/coursework_1_stage5_v1_archive/PART2/
output/coursework_1_stage5_v1_archive/PART3/
output/coursework_1_stage5_v1_archive/PART123/
```

## Future Merge Guidance

Do not merge this summary branch wholesale into the latest `main`. This branch is based on the historical Coursework 1 stage 4 layout and intentionally preserves the old V1 code structure.

For a future final/main branch, pick or manually copy only:

```text
DOCS/coursework_1_stage5_v1_archive_summary.md
output/coursework_1_stage5_v1_archive/
```

Optional, only if the final branch needs to reproduce this exact V1 archive matrix:

```text
scripts/run_coursework_1_stage5_archive_matrix.py
```

Do not pick/merge these from this branch unless there is a deliberate reason:

```text
README.md
.gitignore
DATA/PART2/
DATA/PART3/
DATA/PART123/
configs/timeline.json
framework/
strategies/
scripts/ other than scripts/run_coursework_1_stage5_archive_matrix.py
```

The latest `main` already owns the current project hierarchy, EDA workflow, data layout, and reusable strategy tooling. Treat this branch as V1 evidence, not as a structural base.

BT396 is the **Backtest Framework** for COMP396.  
It is built on [Backtrader](https://www.backtrader.com/) and provides a controlled environment where student strategies are run under standardised rules (slippage, bankruptcy checks, overspend guards, etc.).

---

## Installation (Windows)

Follow these steps on a **fresh Windows machine**:

1. **Install Python**  
   - Download and install [Python 3.10+](https://www.python.org/downloads/).  
   - During installation, **tick "Add Python to PATH"**.

2. **Install Git (optional)**  
   - If you want to clone the repository directly, install [Git for Windows](https://git-scm.com/download/win).  
   - Otherwise, you can just unzip the provided `BT396.zip`.

3. **Unzip / Clone the Framework**  
   - Place the folder somewhere convenient, e.g. `C:\Users\<YourName>\BT396`.

4. **Open Command Prompt (cmd) or PowerShell**  
   - Navigate to the project root folder:
     ```bash
     cd C:\Users\<YourName>\BT396
     ```

5. **Create a Virtual Environment (recommended)**  
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

6. **Install Dependencies**  
   ```bash
   pip install --upgrade pip
   pip install backtrader pandas matplotlib pyyaml
   ```

   These are the core requirements:
   - `backtrader` – backtesting engine  
   - `pandas` – data handling  
   - `matplotlib` – plotting  
   - `pyyaml` – config file support (optional, falls back to JSON)

---

## Running the Backtester

The entry point is **`main.py`**.  
It takes a strategy (from the `strategies/` folder) and runs it against sample data in `DATA/`.

Basic usage:

```bash
python main.py --strategy <name>
```

---

##  Example Runs

### 1. Run the **Copycat** strategy
This is a simple demo strategy that goes long if yesterday’s close > open, otherwise short:

```bash
python main.py --strategy copycat
```

### 2. Run with **debug logging** enabled
This prints order fills, slippage, and trade PnL to the console:

```bash
python main.py --strategy copycat --debug
```

### 3. Run with a different dataset
If you have your own CSVs in a folder (must contain at least 10 aligned OHLCV files):

```bash
python main.py --strategy copycat --data-dir ./DATA/MYCSV
```

### 4. Run the **Portfolio Bankrupt Demo**
This shows what happens with extreme leverage and bad allocation:

```bash
python main.py --strategy p_bankrupt
```

---

## Project Structure

```
BT396/
│── main.py                 # Entry point
│── framework/              # Core framework (rules, analyzers, plotting)
│── strategies/             # Example + student strategies
│── DATA/                   # Sample CSV data
│── output/                 # Results are saved here
│── config.yaml             # Default config file
```

- Results (equity curves, JSON summaries, plots) are saved into the `output/` folder.
- You can override most settings via command line arguments (cash, commission, policies, etc.).

---

## Next Steps

- Copy `strategies/template_strategy.py` and start building your own trading ideas.  
- Always test with:
  ```bash
  python main.py --strategy <your_strategy>
  ```
- Check the `output/` folder for plots and summaries.

---

## Notes

- BT396 enforces **COMP396 trading rules** automatically.  
- Market orders include slippage, overspending cancels all trades for the day, and bankruptcy halts your run.  
- Plots include portfolio equity curves, per-series PnL, activity ratios, and realized PnL dashboards.  

---

Happy Backtesting

---

Distribution / Packaging
------------------------

If you want to zip this project for distribution, it is safe to exclude or delete the following from the archive:

- .git/ (Git repository metadata)
- .idea/ (JetBrains/IDE project files)
- __pycache__/ (Python bytecode caches) — these will be re-created automatically
- .pytest_cache/, .mypy_cache/ (tool caches)
- OS junk files like .DS_Store, Thumbs.db

Optionally exclude generated outputs to keep the archive small:

- output/ (plots and run summaries created by main.py)

Nothing in the list above is required to run the backtester.

Quick way to create a clean ZIP:

- From the project root, run:
  
  ```bash
  python scripts/make_dist.py           # creates BT396-dist.zip in the project root
  python scripts/make_dist.py --no-output  # also excludes the output/ folder
  python scripts/make_dist.py --name BT396_0.1.0_win.zip
  ```

When a user unzips the archive, they can run:

```bash
python main.py               # shows project version and date
python main.py --strategy copycat
```
