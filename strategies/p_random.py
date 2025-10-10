# strategies/p_random.py
#
# Portfolio strategy:
# - Every day, for each instrument, submit a market order with a random
#   integer size in [-maxLots, +maxLots].
# - Ignores available cash; framework may cancel if overspend.
#
# Usage (example with 10 feeds):
#   python run_backtest.py \
#       --strategy p_random \
#       --data-glob "DATA/PART1/*.csv" \
#       --portfolio \
#       --cash 1000000 \
#       --commission 0.0
#
# Notes:
# - Slippage (--smult) still applies in results.
# - This is deliberately chaotic and not capital-aware.

import backtrader as bt
import random


class TeamStrategy(bt.Strategy):
    """Portfolio demo strategy that submits random market orders each day across all feeds (for testing the framework)."""
    params = dict(
        maxLots=10,     # maximum absolute size per order
        printlog=False,
    )

    def __init__(self):
        self.datas_list = list(self.datas)
        if not self.datas_list:
            raise ValueError("No data feeds provided. Use --portfolio with a data glob.")

    def log(self, txt, dt=None):
        if self.p.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} {txt}")

    def next(self):
        m = int(self.p.maxLots)
        if m <= 0:
            return

        for i, d in enumerate(self.datas_list):
            # Pick random int between -m and +m inclusive
            qty = random.randint(-m, m)
            if qty > 0:
                self.buy(data=d, size=qty)
            elif qty < 0:
                self.sell(data=d, size=abs(qty))

            if self.p.printlog and qty != 0:
                self.log(f"[data[{i}]] random market order size={qty:+d}")
