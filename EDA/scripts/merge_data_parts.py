import argparse
from pathlib import Path
import sys

import pandas as pd


DEFAULT_PARTS = ("PART1", "PART2", "PART3")
DEFAULT_OUTPUT = "PART123"
DATE_COLUMNS = ("Index", "Date")


def _read_asset_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, thousands=",")
    df.columns = df.columns.str.strip().str.strip('"')

    date_col = next((col for col in DATE_COLUMNS if col in df.columns), None)
    if date_col is None:
        raise ValueError(f"{path} has no Index/Date column")

    if date_col != "Index":
        df.rename(columns={date_col: "Index"}, inplace=True)

    df["Index"] = pd.to_datetime(df["Index"], errors="coerce")
    df.dropna(subset=["Index"], inplace=True)
    return df


def _asset_names(data_root: Path, parts: list[str]) -> list[str]:
    names = set()
    for part in parts:
        part_dir = data_root / part
        if part_dir.exists():
            names.update(path.stem for path in part_dir.glob("*.csv"))
    return sorted(names)


def merge_parts(data_root: Path, parts: list[str], output: str) -> None:
    missing = [part for part in parts if not (data_root / part).exists()]
    if missing:
        print(f"[ERROR] Missing data directories: {', '.join(missing)}")
        sys.exit(1)

    out_dir = data_root / output
    out_dir.mkdir(parents=True, exist_ok=True)

    assets = _asset_names(data_root, parts)
    if not assets:
        print(f"[WARN] No CSV files found in: {', '.join(parts)}")
        return

    print("[INFO] Merging data parts")
    print(f"  parts : {', '.join(parts)}")
    print(f"  output: {out_dir}")

    for asset in assets:
        frames = []
        used_parts = []

        for part in parts:
            path = data_root / part / f"{asset}.csv"
            if not path.exists():
                continue
            try:
                frames.append(_read_asset_csv(path))
                used_parts.append(part)
            except Exception as exc:
                print(f"[WARN] Skipping {part}/{asset}.csv: {exc}")

        if not frames:
            print(f"[WARN] {asset}: no readable files")
            continue

        merged = pd.concat(frames, ignore_index=True)
        merged.sort_values("Index", inplace=True)
        merged.drop_duplicates(subset=["Index"], keep="last", inplace=True)

        preferred_cols = ["Index", "Open", "High", "Low", "Close", "Volume"]
        ordered_cols = [col for col in preferred_cols if col in merged.columns]
        ordered_cols += [col for col in merged.columns if col not in ordered_cols]
        merged = merged[ordered_cols]

        out_path = out_dir / f"{asset}.csv"
        merged.to_csv(out_path, index=False, date_format="%Y-%m-%d")
        print(f"  [{asset}] {', '.join(used_parts)} -> {len(merged)} rows")

    print("[SUCCESS] Data merge completed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge DATA/PART* asset CSVs while preserving the Index column."
    )
    parser.add_argument(
        "--parts",
        nargs="+",
        default=list(DEFAULT_PARTS),
        help="Data folders under DATA to merge, e.g. PART1 PART2 PART3.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Output folder under DATA. Defaults to PART123.",
    )
    parser.add_argument(
        "--data-root",
        default="DATA",
        help="Root data directory. Defaults to DATA.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    parts = [part.upper() for part in args.parts]
    merge_parts(Path(args.data_root), parts, args.output.upper())


if __name__ == "__main__":
    main()
