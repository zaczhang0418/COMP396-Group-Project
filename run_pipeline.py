# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# run_pipeline.py
"""
一键执行 COMP396 项目从网格搜索到组合策略的全流程。

功能:
1. 清理旧的 output 文件夹。
2. 依次为 TF, MR, GARCH 策略执行网格搜索。
3. 根据网格搜索结果，为各策略选出最优参数并跑完 IS/OOS/Full 样本。
4. 自动计算三个资产共有的全样本日期范围。
5. 使用最优参数和自动获取的日期，运行最终的组合策略。

使用:
在项目根目录下执行 `python run_pipeline.py`
"""
import subprocess
import sys
import shutil
from pathlib import Path
import json

PROJ = Path(__file__).resolve().parent

def run_command(cmd, step_name):
    """执行一个命令并打印日志"""
    print(f"\n{'='*20}\n[START] {step_name}\n{'='*20}")
    print(f"Executing: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, text=True)
        print(f"[DONE] {step_name}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {step_name} failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(1) # 如果某一步失败，则终止整个流程

def get_combo_dates():
    """从 splits 文件中自动计算组合策略的全样本日期范围"""
    splits_paths = [
        PROJ / "configs" / "splits_asset01.json",
        PROJ / "configs" / "splits_asset10.json",
        PROJ / "configs" / "splits_asset07.json",
    ]
    starts, ends = [], []
    for p in splits_paths:
        data = json.loads(p.read_text(encoding="utf-8"))
        starts.append(data["full_start"])
        ends.append(data["full_end"])
    
    # 组合策略的开始时间应为所有资产中最晚的开始时间
    # 组合策略的结束时间应为所有资产中最早的结束时间
    # 这样可以确保在整个回测期间，所有资产都有数据
    combo_start = max(starts)
    combo_end = min(ends)
    print(f"\n[INFO] Auto-detected combo date range: {combo_start} -> {combo_end}")
    return combo_start, combo_end

if __name__ == "__main__":
    # 0. 清理旧产出
    output_dir = PROJ / "output"
    if output_dir.exists():
        print(f"[CLEANUP] Removing old directory: {output_dir}")
        shutil.rmtree(output_dir)

    py_exec = sys.executable # 使用当前 Python 解释器

    # 1. Trend Following (TF) - Asset 01
    run_command([py_exec, "scripts/tf/run_core4_grid_tf.py"], "TF Grid Search")
    run_command([py_exec, "scripts/tf/pick_best_tf.py", "--runs", "is,oos,full", "--key", "true_pd_ratio"], "TF Pick Best")

    # 2. Mean Reversion (MR) - Asset 10
    run_command([py_exec, "scripts/mr/run_core4_grid_mr.py"], "MR Grid Search")
    run_command([py_exec, "scripts/mr/pick_best_mr.py", "--runs", "is,oos,full", "--key", "true_pd_ratio"], "MR Pick Best")

    # 3. GARCH - Asset 07
    run_command([py_exec, "scripts/garch/run_core4_grid_garch.py"], "GARCH Grid Search")
    run_command([py_exec, "scripts/garch/pick_best_garch.py", "--runs", "is,oos,full", "--key", "true_pd_ratio"], "GARCH Pick Best")

    # 4. Combo Strategy (组合策略)
    start_date, end_date = get_combo_dates()
    run_command([
        py_exec, "scripts/combo/run_combo_once.py",
        "--start", start_date,
        "--end", end_date,
        "--cash", "1000000",
        "--w-tf", "0.45",
        "--w-mr", "0.45",
        "--w-ga", "0.10"
    ], "Combo Strategy Run")

    print("\n[SUCCESS] All pipeline steps completed successfully.")