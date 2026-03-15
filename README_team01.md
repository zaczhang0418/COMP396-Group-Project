# Team 01 Strategy Submission

This repository contains our COMP396 Assessment 2 submission strategy in:

`strategies/team01.py`

## How To Run

Run through the provided backtester entrypoint (`main.py`) exactly as in the distributed framework.

Example local verification command on Part 2 data:

```powershell
python main.py --strategy team01 --data-dir .\DATA\PART2 --fromdate 2072-09-03 --todate 2075-05-30 --output-dir output\presubmission_part2
```

Example with debug logging:

```powershell
python main.py --strategy team01 --data-dir .\DATA\PART2 --fromdate 2072-09-03 --todate 2075-05-30 --debug --output-dir output\presubmission_part2_debug
```

At marking time, the framework can run the same strategy on Part 3 data. No additional CLI parameter overrides are required because the strategy defaults are defined inside the file.

## Compliance With The Assignment Requirements

- The submission is a single file named `team01.py`.
- The file defines exactly one Backtrader strategy class named `TeamStrategy`.
- `TeamStrategy` subclasses `bt.Strategy`.
- The parameter list is declared at the top of the class in `params`.
- All required imports are included in the file.
- The strategy does not depend on external helper scripts, JSON parameter files, or local output folders at runtime.
- The strategy is intended to be run through `main.py` in the provided framework, matching the assignment instructions.

## Notes

- The strategy trades only the required series it uses: `series_1`, `series_7`, and `series_10`.
- For our testing, we used Part 1-selected parameters and evaluated them on Part 2 data.
- The same file is designed to work when the framework loads Part 3 data during marking.
