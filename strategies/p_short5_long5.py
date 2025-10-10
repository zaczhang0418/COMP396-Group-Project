# strategies/p_short5_long5.py
#
# Portfolio strategy that:
# - Day 1: takes equal-sized SHORT positions across series 1–5, with total
#          short exposure = `leverage` (e.g., £40M total → £8M per series).
# - Day 2: invests (cash - cash_buffer) equally LONG across series 6–10.
#
# This is an intentionally extreme strategy with ~40:1 gearing, designed to
# highlight risk of leverage and demonstrate portfolio mechanics.
#
# Usage example:
#   python run_backtest.py \
#       --strategy p_short5_long5 \
#       --data-glob "DATA/PART1/*.csv" \
#       --portfolio \
#       --cash 1000000 \
#       --commission 0.0
#
# Notes:
# - Expects at least 10 data feeds; will raise if fewer.
# - Orders are market orders: submitted on Day 1 and Day 2, executed next bar.
# - After Day 2, positions are simply held until the end.
#
# python run_backtest.py --strategy p_short5_long5 --data-glob "DATA/PART1/*.csv" --portfolio --cash 1000000 --commission 0.0
#
import backtrader as bt


class TeamStrategy(bt.Strategy):
    """Two-phase portfolio strategy: short series 1–5 on day one with fixed total exposure, then go long series 6–10 on day two."""
    params = dict(
        leverage=40_000_000,   # total short exposure across series 1–5
        cash_buffer=1_000_000, # keep £1M unspent before going long
        printlog=False,
    )

    def __init__(self):
        self._did_shorts = False
        self._did_longs = False
        self.datas_list = list(self.datas)

        # Sanity check: this strategy is defined for exactly 10 series.
        if len(self.datas_list) < 10:
            raise ValueError(
                f"p_short5_long5 expects at least 10 data feeds; got {len(self.datas_list)}. "
                "Run with --portfolio and a glob that matches 10 CSV files."
            )

    def log(self, txt, dt=None):
        """Logging function for debug/trace (enabled by printlog=True)."""
        if self.p.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} {txt}")

    def next(self):
        # Day 1 action: submit shorts on series 1–5 (indexes 0..4)
        if not self._did_shorts:
            exposure_total = float(self.p.leverage)
            per_series_exposure = exposure_total / 5.0

            for i in range(5):
                d = self.datas_list[i]
                opx = float(d.open[0])
                if opx <= 0 or not opx:
                    continue

                size = - per_series_exposure / opx  # negative for short
                self.sell(data=d, size=size)
                self.log(f"SHORT data[{i}] @open≈{opx:.2f} size={size:.2f}")

            self._did_shorts = True
            return  # stop here; long phase comes next day

        # Day 2 action: submit longs on series 6–10 (indexes 5..9)
        if self._did_shorts and not self._did_longs:
            cash = float(self.broker.getcash())
            to_spend = max(0.0, cash - float(self.p.cash_buffer))
            per_series_exposure = to_spend / 5.0 if to_spend > 0 else 0.0

            for i in range(5, 10):
                d = self.datas_list[i]
                opx = float(d.open[0])
                if opx <= 0 or not opx:
                    continue

                size = per_series_exposure / opx
                self.buy(data=d, size=size)
                self.log(f"LONG  data[{i}] @open≈{opx:.2f} size={size:.2f}")

            self._did_longs = True
            return

        # After Day 2, hold positions until liquidation
        return
