COMP396 Group Project - Team01
Final Integration Branch README

1. Project Overview
-------------------

This repository contains the final integrated code, strategies, evidence, and
report-supporting outputs for the Team01 COMP396 group project.

The project builds and evaluates rule-based trading strategies under the COMP396
Backtrader framework. The final branch preserves the development evidence from:

- EDA foundation and diagnostics.
- Coursework 1 / V1 asset-specific prototype.
- Coursework 2 / V2 official presubmission strategy.
- Coursework 3 / V3 cross-asset reassessment and final refinement.
- Final report evidence integration.

The final deployed strategy is:

    Strategies/coursework_3/stage_2_team01_v3_final.py

The default project runner also uses this strategy unless another strategy is
specified.


2. Main Directory Structure
---------------------------

    Configs/
        Project configuration files and parameter grids.

    DATA/
        Input CSV data for PART1, PART2, PART3, and generated PART123.

    Documentation/
        Branch summaries, final-report evidence maps, and Chapter 3 evidence
        packs used to support the written report.

    EDA/
        Exploratory data analysis scripts, chart builders, generated EDA
        evidence, and EDA documentation.

    Framework/
        Backtrader harness helpers, data loader, analyzers, plotting utilities,
        and COMP396 trading-rule enforcement.

    Output/
        Generated evidence outputs grouped by coursework and development stage.

    Scripts/
        Reproduction scripts for archive generation, parameter search,
        cross-asset scan, Chapter 3 evidence, and distribution packaging.

    Strategies/
        Versioned Team01 strategy implementations.

    Tests/
        Rule-level tests for the COMP396 framework behavior.


3. Key Evidence Locations
-------------------------

The most important report-facing evidence index is:

    Documentation/final_report_evidence/final_report_evidence_index.md

The selected EDA asset profile used to support the V2 asset choices is:

    Documentation/final_report_evidence/eda_selected_asset_profile.md

The main generated output folders are:

    Output/coursework_1/stage_5_team01_v1_archive/
    Output/coursework_2/stage_4_team01_v2_archive/
    Output/coursework_3/stage_1_cross_asset_scan/
    Output/coursework_3/stage_2_team01_v3_final/
    Output/coursework_3/stage_3_chapter3_evidence/

The Chapter 3 report-ready evidence packs are:

    Documentation/chapter3_analysis_evidence/3.3/
    Documentation/chapter3_analysis_evidence/3.5/
    Documentation/chapter3_analysis_evidence/3.6/


4. Environment Setup
--------------------

The project is not tied to a specific local conda environment. It can be run on
another computer as long as Python and the packages in requirements.txt are
installed.

Recommended Python version:

    Python 3.10 or newer

Create and activate a virtual environment if desired:

    python -m venv .venv

On Windows PowerShell:

    .\.venv\Scripts\Activate.ps1

On macOS / Linux:

    source .venv/bin/activate

Install dependencies from the project root:

    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt


5. Unified Project Runner
-------------------------

Most common workflows can be run through:

    python run_project.py <command>

Available commands:

    backtest       Run the Backtrader harness.
    eda            Run the EDA workflow.
    archive-cw1    Regenerate compact Coursework 1 / V1 archive summaries.
    archive-cw2    Regenerate compact Coursework 2 / V2 archive summaries.
    cross-scan     Run or summarize the Coursework 3 cross-asset scan.
    chapter3       Regenerate Chapter 3 report evidence packs.
    dist           Build a clean submission ZIP.

Run the final Team01 strategy on PART3:

    python run_project.py backtest --data-dir ./DATA/PART3 --output-dir ./Output/final_run

Run the final Team01 strategy without plots:

    python run_project.py backtest --data-dir ./DATA/PART3 --output-dir ./Output/final_run --no-plot

Run the EDA overview:

    python run_project.py eda OVERVIEW

Run all EDA datasets and rebuild the compact overview:

    python run_project.py eda ALL

Regenerate V1 and V2 archive summaries:

    python run_project.py archive-cw1
    python run_project.py archive-cw2

Regenerate Chapter 3 report evidence:

    python run_project.py chapter3

Summarize existing cross-asset scan evidence:

    python run_project.py cross-scan --mode summarize

Validate cross-asset scan transfer performance on Part 2:

    python run_project.py cross-scan --mode validate-part2

Run the full cross-asset scan:

    python run_project.py cross-scan --mode run

The full cross-asset scan can take longer than the summary and validation
commands because it evaluates multiple strategy and asset combinations.


6. Can The Whole Project Run On Another Computer?
------------------------------------------------

Yes, the project is designed to run from the repository root on another machine
without requiring the original D: drive conda environment.

The other machine needs:

- Python 3.10 or newer.
- The dependencies installed from requirements.txt.
- The DATA/ folder present with PART1, PART2, and PART3 CSV files.
- Write permission to the Output/ and Documentation/ folders when regenerating
  evidence.

The unified runner now calls Python scripts directly. It does not require the
original local conda path. If a user activates any suitable Python environment
and runs:

    python -m pip install -r requirements.txt

then the project commands should use that environment through sys.executable.

There is not one mandatory "run absolutely everything" command, because some
workflows are intentionally expensive. The recommended full evidence refresh is:

    python run_project.py eda OVERVIEW
    python run_project.py archive-cw1
    python run_project.py archive-cw2
    python run_project.py cross-scan --mode summarize
    python run_project.py cross-scan --mode validate-part2
    python run_project.py chapter3
    python run_project.py backtest --data-dir ./DATA/PART3 --output-dir ./Output/final_run

If the cross-asset raw scan must be recomputed from scratch, run:

    python run_project.py cross-scan --mode run

before the summarize and validate-part2 steps.


7. Testing
----------

Run the framework rule tests with:

    python -m pytest Tests

These tests focus on COMP396 trading-rule behavior such as overspend handling,
forced liquidation, and bankruptcy behavior.


8. Packaging
------------

This README file is intended for the final submission package.

To build a clean ZIP later, run:

    python run_project.py dist

To build a smaller ZIP without generated Output/ files:

    python run_project.py dist --no-output

Do not run the packaging command from inside a different project folder. Run it
from this repository root so the intended files are included.


9. Notes For Markers
--------------------

- The final strategy is Team01 V3, not the older V1 or V2 prototype.
- V1 and V2 are retained for development traceability and report evidence.
- The Output/ directory is organized by coursework and development stage.
- Documentation/final_report_evidence/ maps the written report evidence needs
  to concrete branch paths.
- Documentation/chapter3_analysis_evidence/ contains report-ready tables,
  figures, and supporting text for Chapter 3.
