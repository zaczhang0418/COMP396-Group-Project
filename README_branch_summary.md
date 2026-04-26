# Branch Summary: Chapter 3 V2/V3 Part 3 Analysis

This file summarises the main workflow and deliverables of the current branch. It is intended as the single branch-level README for wrap-up and later merge planning.

## Branch Purpose

The branch expands the Chapter 3 analysis for the COMP396 final report, with a specific focus on:

- restoring and analysing `Part 3` data,
- strengthening the evidence behind the V2 diagnosis,
- mirroring the same workflow for V3,
- and building a clean comparison layer between V2 and V3.

The final output is organised under:

- [DOC/chapter3](/C:/Users/ALIENWARE/Desktop/COMP396/COMP396-Group-Project/DOC/chapter3)

## Workflow Completed on This Branch

1. Restored `DATA/PART3/01.csv` to `DATA/PART3/10.csv` from historical branch history so that Part 3 analysis could be reproduced locally.
2. Built a drawdown-event analysis pipeline for V2 and V3, including date-level traces and maximum drawdown windows.
3. Built dedicated subsection packs for Chapter 3.3:
   - `3.3.1` equity curve and drawdown
   - `3.3.2` asset hard binding and uneven leg contribution
   - `3.3.3` overspending pressure / capital over-commitment
   - `3.3.5` summary performance metrics
4. Built a mirrored V3-only workflow for Chapter 3.5:
   - expected design
   - observed Part 3 result
   - drawdown profile
   - structural behaviour
   - exposure and execution control
   - summary metrics
5. Built a paired comparison layer for Chapter 3.6 that directly compares:
   - `3.3.1` vs `3.5.3`
   - `3.3.2` vs `3.5.4`
   - `3.3.3` vs `3.5.5`
   - `3.3.5` vs `3.5.6`
6. Reorganised all retained report materials into one chapter-level folder so they are easier to locate on GitHub when drafting the final report.

## Main Deliverables

### 1. Restored data

- `DATA/PART3/01.csv`
- `DATA/PART3/02.csv`
- `DATA/PART3/03.csv`
- `DATA/PART3/04.csv`
- `DATA/PART3/05.csv`
- `DATA/PART3/06.csv`
- `DATA/PART3/07.csv`
- `DATA/PART3/08.csv`
- `DATA/PART3/09.csv`
- `DATA/PART3/10.csv`

### 2. Analysis scripts

- `scripts/generate_part3_drawdown_event_analysis.py`
- `scripts/generate_coursework_3_chapter3_analysis.py`
- `scripts/generate_part3_331_doc_pack.py`
- `scripts/generate_part3_332_doc_pack.py`
- `scripts/generate_part3_333_doc_pack.py`
- `scripts/generate_part3_335_doc_pack.py`
- `scripts/generate_part3_35_v3_workflow_pack.py`
- `scripts/generate_part3_36_comparison_pack.py`

### 3. Final report materials

- [DOC/chapter3/3.3](/C:/Users/ALIENWARE/Desktop/COMP396/COMP396-Group-Project/DOC/chapter3/3.3)
- [DOC/chapter3/3.5](/C:/Users/ALIENWARE/Desktop/COMP396/COMP396-Group-Project/DOC/chapter3/3.5)
- [DOC/chapter3/3.6](/C:/Users/ALIENWARE/Desktop/COMP396/COMP396-Group-Project/DOC/chapter3/3.6)

Most important section-entry files:

- [DOC/chapter3/3.3/section_3_3_final.md](/C:/Users/ALIENWARE/Desktop/COMP396/COMP396-Group-Project/DOC/chapter3/3.3/section_3_3_final.md)
- [DOC/chapter3/3.5/section_3_5_final.md](/C:/Users/ALIENWARE/Desktop/COMP396/COMP396-Group-Project/DOC/chapter3/3.5/section_3_5_final.md)
- [DOC/chapter3/3.6/section_3_6_final.md](/C:/Users/ALIENWARE/Desktop/COMP396/COMP396-Group-Project/DOC/chapter3/3.6/section_3_6_final.md)

## Merge Guidance

This branch was created from a branch that is not the latest integration point. Because of that, the safest merge strategy is not a full branch merge into `main`.

Recommended approach:

1. Update a fresh target branch from the latest `main`.
2. Cherry-pick or manually copy only the files that belong to this Chapter 3 analysis package.
3. Avoid bringing across unrelated historical branch state.

### Files / paths recommended for cherry-pick

If you want the full Chapter 3 analysis package, cherry-pick the commits that introduce changes in these paths:

- `DATA/PART3/`
- `DOC/chapter3/`
- `scripts/generate_part3_drawdown_event_analysis.py`
- `scripts/generate_coursework_3_chapter3_analysis.py`
- `scripts/generate_part3_331_doc_pack.py`
- `scripts/generate_part3_332_doc_pack.py`
- `scripts/generate_part3_333_doc_pack.py`
- `scripts/generate_part3_335_doc_pack.py`
- `scripts/generate_part3_35_v3_workflow_pack.py`
- `scripts/generate_part3_36_comparison_pack.py`

### Files / paths not required for cherry-pick

These should not be necessary if the goal is only to preserve the final Chapter 3 report pack:

- deleted temporary `DOC/coursework_3_stage3_v2v3_*` folders
- transient `output/` artifacts that are already reproduced by the scripts

### Practical merge note

If there are conflicts later, prioritise keeping:

- the latest `main` versions of general project files,
- and this branch's versions of `DATA/PART3`, `DOC/chapter3`, and the new Chapter 3 generation scripts.

That keeps the merge scope narrow and avoids accidentally reintroducing stale branch state.
