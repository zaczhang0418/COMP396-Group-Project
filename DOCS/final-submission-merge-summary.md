# Final Submission Merge Summary

This final integration was built from the latest remote `main` branch rather than by merging every historical branch wholesale.

The reason is that the summary branches were evidence archives. Several of them explicitly warn that they contain old framework layouts, historical script structures, generated outputs, or branch-specific README files. A full branch merge would risk replacing the latest `main` structure with stale coursework-era files.

## Baseline

Final integration branch:

```text
final/submission-integration
```

Baseline:

```text
origin/main
```

## Selected Material

| Source branch | Material brought into final branch |
| --- | --- |
| `origin/summary/eda/stage-5-archive-summary` | EDA docs, executed EDA notebook, compact stage 4 overview output, and EDA requirements. |
| `origin/summary/coursework_1/stage-5-v1-archive-summary` | `team01_v1.py`, V1 archive matrix script, and V1 archive output. |
| `origin/summary/coursework_2/stage-4-v2-archive-summary` | `team01_v2.py`, V2 archive matrix script, and V2 archive output. |
| `origin/summary/coursework_3/stage-2-v3-archive-summary` | Final `team01.py`, `team01_v3.py`, V3 archive output, and lightweight cross-asset scan summaries. |
| `origin/summary/coursework_3/stage-3-v2v3-performance-analysis` | Chapter 3 report-ready document pack for V2 diagnosis, V3 analysis, and V2/V3 comparison. |
| Local protected stash | Chapter 3 generation scripts that were present locally but not committed on the remote branch. |

## Deliberately Excluded

The final branch avoids importing these from historical branches:

- old `framework/` versions,
- old `DATA/` layouts,
- full raw cross-asset scan output with thousands of intermediate run files,
- old generic experiment directories superseded by compact archive folders,
- branch-specific root README files,
- caches and bytecode files.

This keeps the final zip focused on the latest project structure plus the evidence needed for marking and final report writing.

## Report Flow Mapping

| Report stage | Repository evidence |
| --- | --- |
| Stage A: EDA evidence foundation | `EDA/docs/`, `EDA/output/stage4_overview/` |
| Stage B: CA1 V1 prototype | `output/coursework_1_stage5_v1_archive/`, `strategies/team01_v1.py` |
| Stage C: CA2 V2 official submission | `output/coursework_2_stage4_v2_archive/`, `strategies/team01_v2.py` |
| Stage D: V2 output diagnosis | `DOC/chapter3/3.3/` |
| Stage E: V3 refinement | `strategies/team01.py`, `strategies/team01_v3.py`, `DOC/chapter3/3.5/` |
| Stage F: final comparison and report integration | `DOC/chapter3/3.6/` |

## Final Strategy

The final deployed strategy is:

```text
strategies/team01.py
```

It represents Team01 V3: TF on series 1 plus MR on series 9, with dynamic allocation, performance-aware budgeting, loss-freeze controls, gross exposure limits, and rebalance tolerance.
