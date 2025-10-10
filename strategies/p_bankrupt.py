# strategies/p_bankrupt.py
#
# Portfolio strategy:
# - Day 1: SHORT series 1–5 equally so total short exposure = `leverage`.
# - Day 2: LONG the remaining series (6..N), spending (cash - cash_buffer) equally.
#
# Intentional “blow-up” demo: very high gearing (e.g., 40:1) and asymmetric
# allocation make this likely to go bankrupt—useful for teaching risk.
#
# Notes:
# - Works with N >= 6 feeds. Shorts always target the first 5 feeds (1..5).
# - Longs allocate across the rest (6..N). If N == 10, that’s 5 longs (6..10).
# - Orders are market orders (submit on Day 1/2, fill next bar by default).
# - After Day 2, positions are held to the end.


import backtrader as bt

class TeamStrategy(bt.Strategy):
    """Two-phase portfolio demo designed to illustrate bankruptcy risk: short first five series on day one, then go long the rest on day two."""
    params = dict(
        leverage=40_000_000,   # total short exposure across series 1–5
        cash_buffer=1_000_000, # keep £1M unspent before going long
        printlog=False,
    )

    def __init__(self):
        self._did_shorts = False
        self._did_longs = False
        self.datas_list = list(self.datas)

        if len(self.datas_list) < 6:
            raise ValueError(
                f"p_bankrupt expects at least 6 data feeds (got {len(self.datas_list)}). "
                "Run with --portfolio and a glob that matches enough CSV files."
            )

    def log(self, txt, dt=None):
        if self.p.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} {txt}")

    def next(self):
        # Phase 1 (Day 1): short series 1..5
        if not self._did_shorts:
            exposure_total = float(self.p.leverage)
            per_series_exposure = exposure_total / 5.0

            for i in range(5):
                d = self.datas_list[i]
                opx = float(d.open[0])
                if opx > 0:
                    size = - per_series_exposure / opx  # negative for short
                    self.sell(data=d, size=size)
                    self.log(f"SHORT data[{i}] @open≈{opx:.2f} size={size:.2f}")

            self._did_shorts = True
            return  # do one phase per bar

        # Phase 2 (Day 2): long series 6..N
        if self._did_shorts and not self._did_longs:
            cash = float(self.broker.getcash())
            to_spend = max(0.0, cash - float(self.p.cash_buffer))

            # remaining instruments: indices 5..(N-1)
            longs = self.datas_list[5:]
            if longs:
                per_series_exposure = to_spend / float(len(longs)) if to_spend > 0 else 0.0

                for j, d in enumerate(longs, start=5):
                    opx = float(d.open[0])
                    if opx > 0 and per_series_exposure > 0:
                        size = per_series_exposure / opx
                        self.buy(data=d, size=size)
                        self.log(f"LONG  data[{j}] @open≈{opx:.2f} size={size:.2f}")

            self._did_longs = True
            return

        # After both phases: hold
        return
