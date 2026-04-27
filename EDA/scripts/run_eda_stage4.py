import argparse
from datetime import datetime
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from EDA.stage_paths import (
    DATA_ROOT,
    EDA_DOCS,
    STAGE_4_OUTPUT,
    STAGE_4_RUN_REPORT,
    dataset_output_dir,
)

LATEST_RUN_REPORT = STAGE_4_RUN_REPORT

DATASET_ALIASES = {
    "ALL_PARTS": "PART123",
}

ANALYSIS_SCRIPTS = [
    "EDA/data_loader.py",
    "EDA/plotting/plot_acf_charts.py",
    "EDA/plotting/plot_correlation_heatmap.py",
    "EDA/plotting/plot_garch_analysis.py",
    "EDA/plotting/plot_hurst_analysis.py",
    "EDA/plotting/plot_quantile_analysis.py",
    "EDA/plotting/plot_return_histograms.py",
    "EDA/plotting/plot_volatility.py",
]

RUN_REPORT = {
    "started_at": None,
    "finished_at": None,
    "requested": None,
    "python": sys.executable,
    "datasets": [],
    "merges": [],
    "overview": None,
    "exit_code": 0,
}


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        part
        for part in [str(ROOT), str(ROOT / "EDA"), env.get("PYTHONPATH", "")]
        if part
    )
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["MPLBACKEND"] = "Agg"
    return env


def _normalise_dataset(dataset: str) -> str:
    dataset = dataset.upper()
    return DATASET_ALIASES.get(dataset, dataset)


def _merge_dataset(dataset: str) -> None:
    if dataset == "PART123":
        command = [
            sys.executable,
            "EDA/scripts/merge_data_parts.py",
            "--parts",
            "PART1",
            "PART2",
            "PART3",
            "--output",
            "PART123",
        ]
    else:
        return

    print(f"[merge] Building DATA/{dataset}", flush=True)
    proc = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        env=_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if proc.stdout:
        print(proc.stdout.rstrip())

    RUN_REPORT["merges"].append(
        {
            "dataset": dataset,
            "returncode": proc.returncode,
            "output": proc.stdout.strip().splitlines() if proc.stdout else [],
        }
    )

    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, command, output=proc.stdout)


def _reset_output_dir(dataset: str) -> Path:
    output_dir = dataset_output_dir(dataset)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    (output_dir / "charts").mkdir(parents=True, exist_ok=True)
    (output_dir / "charts_by_asset").mkdir(parents=True, exist_ok=True)
    (output_dir / "run_logs").mkdir(parents=True, exist_ok=True)
    return output_dir


def _copy_charts_by_asset(dataset: str, output_dir: Path) -> dict[str, int]:
    data_dir = DATA_ROOT / dataset
    if not data_dir.exists():
        return {}

    assets = sorted(path.stem for path in data_dir.glob("*.csv"))
    charts_dir = output_dir / "charts"
    asset_root = output_dir / "charts_by_asset"

    copied_by_asset = {}
    for asset in assets:
        copied = 0
        for chart in charts_dir.rglob("*.png"):
            if asset not in chart.name:
                continue
            rel_parent = chart.parent.relative_to(charts_dir)
            dest_dir = asset_root / asset / rel_parent
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(chart, dest_dir / chart.name)
            copied += 1
        print(f"[asset-view] {dataset}/{asset}: {copied} charts")
        copied_by_asset[asset] = copied
    return copied_by_asset


def _file_stats(path: Path) -> tuple[int, float]:
    if not path.exists():
        return 0, 0.0
    files = [item for item in path.rglob("*") if item.is_file()]
    total_bytes = sum(item.stat().st_size for item in files)
    return len(files), round(total_bytes / (1024 * 1024), 2)


def _chart_families(output_dir: Path) -> list[str]:
    charts_dir = output_dir / "charts"
    if not charts_dir.exists():
        return []
    families = {path.name for path in charts_dir.iterdir() if path.is_dir()}
    if (charts_dir / "correlation_heatmap.png").exists():
        families.add("correlation_heatmap")
    return sorted(families)


def run_dataset(dataset: str) -> int:
    dataset = _normalise_dataset(dataset)
    data_dir = DATA_ROOT / dataset

    _merge_dataset(dataset)
    if not data_dir.exists():
        print(f"[ERROR] Missing data folder: {data_dir}")
        return 1

    output_dir = _reset_output_dir(dataset)
    failures = []
    script_results = []

    print(f"[run] EDA dataset={dataset}")
    for script in ANALYSIS_SCRIPTS:
        script_path = ROOT / script
        log_path = output_dir / "run_logs" / f"{script_path.stem}.log"
        command = [sys.executable, str(script_path), dataset]

        print(f"  -> {script}")
        with log_path.open("w", encoding="utf-8") as log_file:
            proc = subprocess.run(
                command,
                cwd=ROOT,
                env=_env(),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
            )

        if proc.returncode != 0:
            failures.append(script)
            print(f"     [failed] see {log_path.relative_to(ROOT)}")
        else:
            print("     [ok]")
        script_results.append(
            {
                "script": script,
                "returncode": proc.returncode,
                "log": str(log_path.relative_to(ROOT)),
            }
        )

    copied_by_asset = _copy_charts_by_asset(dataset, output_dir)
    file_count, mb = _file_stats(output_dir)
    RUN_REPORT["datasets"].append(
        {
            "dataset": dataset,
            "status": "failed" if failures else "ok",
            "scripts": script_results,
            "asset_charts": copied_by_asset,
            "chart_families": _chart_families(output_dir),
            "file_count": file_count,
            "mb": mb,
            "output_dir": str(output_dir.relative_to(ROOT)),
        }
    )

    if failures:
        print(f"[WARN] {dataset}: {len(failures)} script(s) failed")
        return 1

    print(f"[success] {dataset}: all EDA scripts completed")
    return 0


def run_overview() -> int:
    command = [
        sys.executable,
        "EDA/scripts/build_part123_overview.py",
        "--datasets",
        "PART1",
        "PART2",
        "PART3",
        "PART123",
    ]
    print("[overview] Building stage4 overview", flush=True)
    proc = subprocess.run(command, cwd=ROOT, env=_env())
    output_dir = STAGE_4_OUTPUT
    file_count, mb = _file_stats(output_dir)
    RUN_REPORT["overview"] = {
        "returncode": proc.returncode,
        "output_dir": str(output_dir.relative_to(ROOT)),
        "file_count": file_count,
        "mb": mb,
        "files": sorted(path.name for path in output_dir.glob("*") if path.is_file()),
    }
    return proc.returncode


def build_analysis_report() -> int:
    command = [sys.executable, "EDA/scripts/build_analysis_report.py"]
    print("[analysis] Building latest EDA analysis report", flush=True)
    proc = subprocess.run(command, cwd=ROOT, env=_env())
    return proc.returncode


def build_eda_notebook() -> int:
    command = [sys.executable, "EDA/scripts/build_eda_notebook.py"]
    print("[notebook] Building executed EDA notebook", flush=True)
    proc = subprocess.run(command, cwd=ROOT, env=_env())
    return proc.returncode


def _write_run_report() -> None:
    EDA_DOCS.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Latest EDA Run",
        "",
        f"- Requested command: `{RUN_REPORT['requested']}`",
        f"- Started: `{RUN_REPORT['started_at']}`",
        f"- Finished: `{RUN_REPORT['finished_at']}`",
        f"- Python: `{RUN_REPORT['python']}`",
        f"- Exit code: `{RUN_REPORT['exit_code']}`",
        "",
        "## Active Chart Families",
        "",
        "The Stage 4 runner only generates strategy-relevant charts:",
        "",
    ]
    for family in [
        "acf",
        "correlation_heatmap",
        "garch",
        "histograms",
        "hurst",
        "quantile_analysis",
        "volatility",
    ]:
        lines.append(f"- `{family}`")

    lines.extend(["", "Removed from the active workflow: `candlesticks`, `seasonality`, `rsi_analysis`, `volume_analysis`.", ""])

    if RUN_REPORT["merges"]:
        lines.extend(["## Merge Steps", ""])
        for merge in RUN_REPORT["merges"]:
            status = "ok" if merge["returncode"] == 0 else "failed"
            lines.append(f"### DATA/{merge['dataset']} ({status})")
            lines.append("")
            lines.append("```text")
            lines.extend(merge["output"])
            lines.append("```")
            lines.append("")

    if RUN_REPORT["datasets"]:
        lines.extend(["## Dataset Runs", ""])
        for record in RUN_REPORT["datasets"]:
            lines.append(f"### {record['dataset']} ({record['status']})")
            lines.append("")
            lines.append(f"- Output: `{record['output_dir']}`")
            lines.append(f"- Files: `{record['file_count']}`")
            lines.append(f"- Size: `{record['mb']} MB`")
            lines.append(f"- Chart families: {', '.join(f'`{item}`' for item in record['chart_families'])}")
            if record["asset_charts"]:
                values = sorted(set(record["asset_charts"].values()))
                lines.append(f"- Charts per asset: `{', '.join(str(item) for item in values)}`")
            lines.append("")
            lines.append("| Script | Status | Log |")
            lines.append("| --- | --- | --- |")
            for script in record["scripts"]:
                status = "ok" if script["returncode"] == 0 else "failed"
                lines.append(f"| `{script['script']}` | {status} | `{script['log']}` |")
            lines.append("")

    overview = RUN_REPORT["overview"]
    if overview:
        status = "ok" if overview["returncode"] == 0 else "failed"
        lines.extend(
            [
                f"## Overview ({status})",
                "",
                f"- Output: `{overview['output_dir']}`",
                f"- Files: `{overview['file_count']}`",
                f"- Size: `{overview['mb']} MB`",
                "",
            ]
        )
        for filename in overview["files"]:
            lines.append(f"- `{filename}`")
        lines.append("")

    LATEST_RUN_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[report] Saved run summary to {LATEST_RUN_REPORT.relative_to(ROOT)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the EDA stage 4 workflow.")
    parser.add_argument(
        "dataset",
        nargs="?",
        default="ALL",
        help="PART1, PART2, PART3, PART123, OVERVIEW, or ALL.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    requested = args.dataset.upper()
    RUN_REPORT["started_at"] = datetime.now().isoformat(timespec="seconds")
    RUN_REPORT["requested"] = f"EDA/run_all_eda.bat {requested}"

    if requested == "ALL":
        datasets = ["PART1", "PART2", "PART3", "PART123"]
    elif requested == "OVERVIEW":
        datasets = []
    else:
        datasets = [_normalise_dataset(requested)]

    exit_code = 0
    for dataset in datasets:
        exit_code = run_dataset(dataset) or exit_code

    if requested in {"ALL", "OVERVIEW", "PART123", "ALL_PARTS"}:
        if "PART123" not in datasets:
            _merge_dataset("PART123")
        exit_code = run_overview() or exit_code

    exit_code = build_analysis_report() or exit_code
    exit_code = build_eda_notebook() or exit_code
    RUN_REPORT["finished_at"] = datetime.now().isoformat(timespec="seconds")
    RUN_REPORT["exit_code"] = exit_code
    _write_run_report()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
