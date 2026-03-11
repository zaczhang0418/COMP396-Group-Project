# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Copy legacy output trees into the experiment layout without mutating originals."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


PROJ = Path(__file__).resolve().parents[1]
if str(PROJ) not in sys.path:
    sys.path.insert(0, str(PROJ))

from scripts.common_paths import get_stage_dir, part_root, rel_path, update_experiment_record, write_json  # noqa: E402


def copy_children(src: Path, dst: Path):
    if not src.exists():
        return []
    dst.mkdir(parents=True, exist_ok=True)
    copied = []
    for child in src.iterdir():
        target = dst / child.name
        if target.exists():
            continue
        if child.is_dir():
            shutil.copytree(child, target)
        else:
            shutil.copy2(child, target)
        copied.append(target)
    return copied


def copy_single(src: Path, dst: Path):
    if not src.exists() or dst.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment-tag", default="pre_refine_v0")
    args = ap.parse_args()

    legacy_root = PROJ / "output"

    mappings = {
        ("part1", "tf", "grid_search"): legacy_root / "part1" / "asset01" / "tf_core4_v1",
        ("part1", "tf", "best_runs"): legacy_root / "part1" / "asset01" / "20260311_best",
        ("part1", "mr", "grid_search"): legacy_root / "part1" / "asset10" / "mr_core4_v1",
        ("part1", "mr", "best_runs"): legacy_root / "part1" / "asset10" / "20260311_best",
        ("part1", "garch", "grid_search"): legacy_root / "part1" / "asset07" / "garch_core4_v1",
        ("part1", "garch", "best_runs"): legacy_root / "part1" / "asset07" / "20260311_best",
        ("part1", "combo", "combo"): legacy_root / "part1" / "combo",
        ("part2", "tf", "transfer_runs"): legacy_root / "part2" / "asset01" / "20260311_part2_from_part1_best",
        ("part2", "mr", "transfer_runs"): legacy_root / "part2" / "asset10" / "20260311_part2_from_part1_best",
        ("part2", "garch", "transfer_runs"): legacy_root / "part2" / "asset07" / "20260311_part2_from_part1_best",
        ("part2", "combo", "combo"): legacy_root / "part2" / "combo",
    }

    copied_summary = {}
    for (part, strategy, stage), src in mappings.items():
        dst = get_stage_dir(args.experiment_tag, part, strategy, stage)
        copied = copy_children(src, dst)
        copied_summary[f"{part}.{strategy}.{stage}"] = {
            "source": rel_path(src),
            "dest": rel_path(dst),
            "copied_count": len(copied),
        }

    legacy_transfer_manifest = legacy_root / "part2" / "20260311_part2_from_part1_best_manifest.json"
    legacy_transfer_summary = legacy_root / "part2" / "20260311_part2_from_part1_best_summary.csv"
    new_part2_root = part_root(args.experiment_tag, "part2", create=False)

    transfer_record = new_part2_root / "transfer_record.json"
    transfer_summary = new_part2_root / "transfer_summary.csv"

    if legacy_transfer_manifest.exists():
        payload = {
            "legacy_source": rel_path(legacy_transfer_manifest),
            "legacy_tag": "20260311_part2_from_part1_best",
            "experiment_tag": args.experiment_tag,
            "source_part": "part1",
            "target_part": "part2",
            "copied_into": rel_path(new_part2_root),
        }
        payload.update(json.loads(legacy_transfer_manifest.read_text(encoding="utf-8")))
        write_json(transfer_record, payload)

    copy_single(legacy_transfer_summary, transfer_summary)

    update_experiment_record(
        args.experiment_tag,
        {
            "experiment_tag": args.experiment_tag,
            "legacy_sources": {
                "part1_root": rel_path(legacy_root / "part1"),
                "part2_root": rel_path(legacy_root / "part2"),
            },
            "copied_summary": copied_summary,
            "part1": {
                "strategies": {
                    "tf": {
                        "grid_search_dir": rel_path(get_stage_dir(args.experiment_tag, "part1", "tf", "grid_search", create=False)),
                        "best_runs_dir": rel_path(get_stage_dir(args.experiment_tag, "part1", "tf", "best_runs", create=False)),
                    },
                    "mr": {
                        "grid_search_dir": rel_path(get_stage_dir(args.experiment_tag, "part1", "mr", "grid_search", create=False)),
                        "best_runs_dir": rel_path(get_stage_dir(args.experiment_tag, "part1", "mr", "best_runs", create=False)),
                    },
                    "garch": {
                        "grid_search_dir": rel_path(get_stage_dir(args.experiment_tag, "part1", "garch", "grid_search", create=False)),
                        "best_runs_dir": rel_path(get_stage_dir(args.experiment_tag, "part1", "garch", "best_runs", create=False)),
                    },
                },
                "combo": {
                    "combo_dir": rel_path(get_stage_dir(args.experiment_tag, "part1", "combo", "combo", create=False)),
                },
            },
            "part2": {
                "transfer_record": rel_path(transfer_record),
                "transfer_summary": rel_path(transfer_summary),
                "strategies": {
                    "tf": {
                        "transfer_runs_dir": rel_path(get_stage_dir(args.experiment_tag, "part2", "tf", "transfer_runs", create=False)),
                    },
                    "mr": {
                        "transfer_runs_dir": rel_path(get_stage_dir(args.experiment_tag, "part2", "mr", "transfer_runs", create=False)),
                    },
                    "garch": {
                        "transfer_runs_dir": rel_path(get_stage_dir(args.experiment_tag, "part2", "garch", "transfer_runs", create=False)),
                    },
                },
                "combo": {
                    "combo_dir": rel_path(get_stage_dir(args.experiment_tag, "part2", "combo", "combo", create=False)),
                },
            },
        },
    )
