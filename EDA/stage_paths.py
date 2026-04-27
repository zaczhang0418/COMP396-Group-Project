from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "DATA"
EDA_ROOT = ROOT / "EDA"
EDA_DOCS = EDA_ROOT / "docs"
EDA_OUTPUT = EDA_ROOT / "output"

STAGE_4_NAME = "stage_4_part123_overview"
STAGE_5_NAME = "stage_5_archive_summary"

STAGE_4_DOCS = EDA_DOCS / STAGE_4_NAME
STAGE_5_DOCS = EDA_DOCS / STAGE_5_NAME
STAGE_4_OUTPUT = EDA_OUTPUT / STAGE_4_NAME
STAGE_4_DATASET_RUNS = STAGE_4_OUTPUT / "dataset_runs"

STAGE_4_OVERVIEW_REPORT = STAGE_4_DOCS / "stage_4_overview.md"
STAGE_4_ANALYSIS_REPORT = STAGE_4_DOCS / "stage_4_latest_analysis.md"
STAGE_4_RUN_REPORT = STAGE_4_DOCS / "stage_4_latest_run.md"
STAGE_5_NOTEBOOK = STAGE_5_DOCS / "eda_report_and_justification.ipynb"

STAGE_4_ASSET_SUMMARY = "stage_4_asset_summary.csv"
STAGE_4_DATASET_SUMMARY = "stage_4_dataset_summary.csv"
STAGE_4_TOTAL_RETURN_HEATMAP = "stage_4_total_return_heatmap.png"
STAGE_4_RISK_RETURN_OVERVIEW = "stage_4_risk_return_overview.png"
STAGE_4_ROW_COVERAGE = "stage_4_row_coverage.png"


def dataset_output_dir(dataset: str) -> Path:
    return STAGE_4_DATASET_RUNS / dataset.upper()


def chart_dir(dataset: str, family: str | None = None) -> Path:
    base = dataset_output_dir(dataset) / "charts"
    return base / family if family else base
