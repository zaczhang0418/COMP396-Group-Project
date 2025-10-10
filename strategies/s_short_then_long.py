# strategies/s_short_then_long.py
#
# Single-series strategy:
# - Day 1: SHORT the instrument with fixed notional exposure = `leverage`.
# - Day 2: LONG the instrument, spending (cash - cash_buffer).
# - Then hold.
#
# This mirrors the portfolio p_short5_long5 “short then long” pattern but
# applies to EACH feed independently (useful for per-series runs).
#
# Usage example (single series):
#   python run_backtest.py \
#       --strategy s_short_then_long \
#       --data-glob "DATA/PART1/01.csv" \
#       --cash 1000000 \
#       --commission 0.0
#
# If you pass multiple CSVs WITHOUT --portfolio, your runner may execute the
# same strategy separately for each series (depending on your framework logic).

import backtrader as bt


class TeamStrategy(bt.Strategy):
    """Single-series demo that shorts on day one by a fixed notional and goes long on day two with available cash, then holds."""
    params = dict(
        leverage=8_000_000,    # notional to short on Day 1 (per instrument)
        cash_buffer=1_000_000, # keep £1M unspent before going long on Day 2
        printlog=False,
    )

    def __init__(self):
        self._did_shorts = set()  # per-data flags
        self._did_longs = set()
        # prepare flags for all feeds
        for d in self.datas:
            self._did_shorts.add((d._name, False))
            self._did_longs.add((d._name, False))
        # for quick lookup/update
        self._shorts = {d: False for d in self.datas}
        self._longs  = {d: False for d in self.datas}

    def log(self, txt, dt=None):
        if self.p.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} {txt}")

    def next(self):
        # Apply the same 2-phase logic independently to each feed
        for d in self.datas:
            if not self._shorts[d]:
                opx = float(d.open[0])
                if opx > 0:
                    size = - float(self.p.leverage) / opx
                    self.sell(data=d, size=size)
                    self.log(f"[{d._name}] SHORT @open≈{opx:.2f} size={size:.2f}")
                    self._shorts[d] = True
                continue  # place one phase per bar

            if self._shorts[d] and not self._longs[d]:
                opx = float(d.open[0])
                if opx > 0:
                    cash = float(self.broker.getcash())
                    to_spend = max(0.0, cash - float(self.p.cash_buffer))
                    size = to_spend / opx if to_spend > 0 else 0.0
                    if size > 0:
                        self.buy(data=d, size=size)
                        self.log(f"[{d._name}] LONG  @open≈{opx:.2f} size={size:.2f}")
                    self._longs[d] = True
                continue

        # Afterwards: do nothing (hold)
        return
