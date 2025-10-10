# strategies/p_bbands_contrarian.py
#
# Portfolio Bollinger Bands contrarian strategy:
# - Trades ONLY the series listed in params.series (1-based indices, like the R version).
# - If Close < lower band → LONG (mean-reversion bet).
# - If Close > upper band → SHORT.
# - Else → FLAT (0 target).
#
# Target sizes come from params.posSizes (per-series), mirroring the R design.
# We achieve "marketOrders = -currentPos + pos" using order_target_size per feed.
#
#
# Notes:
# - Slippage is handled by your framework (via --smult) at the results layer.
# - series indices are 1-based in params to match the R code.
# - If posSizes is not provided, defaults to a constant size for selected series.

import backtrader as bt


class TeamStrategy(bt.Strategy):
    """Portfolio Bollinger Bands contrarian strategy that targets long below the lower band and short above the upper band on selected series."""
    params = dict(
        lookback=20,           # n (window length)
        sdParam=2.0,           # standard deviation multiplier
        series=None,           # list of 1-based series indices to trade (e.g., [1,3,5,7,9])
        posSizes=None,         # list of per-series sizes (len == number of data feeds)
        default_size=1.0,      # fallback size if posSizes is None
        printlog=False,
    )

    def __init__(self):
        self.datas_list = list(self.datas)
        nfeeds = len(self.datas_list)
        if nfeeds == 0:
            raise ValueError("No data feeds provided. Use --portfolio with a matching --data-glob.")

        # Convert 1-based series list to 0-based indices; default = all feeds
        if self.p.series is None:
            self.series_idx = list(range(nfeeds))
        else:
            # Keep only valid indices (1..nfeeds), convert to 0-based
            self.series_idx = [i - 1 for i in self.p.series if 1 <= i <= nfeeds]
            if not self.series_idx:
                raise ValueError("params.series produced no valid indices for available feeds.")

        # Prepare per-feed target sizes
        if self.p.posSizes is None:
            # default size for selected series; others get 0 target by construction
            self.pos_sizes = [float(self.p.default_size)] * nfeeds
        else:
            if len(self.p.posSizes) != nfeeds:
                raise ValueError(
                    f"posSizes length {len(self.p.posSizes)} must match number of feeds {nfeeds}."
                )
            self.pos_sizes = [float(x) for x in self.p.posSizes]

        # Build Bollinger indicators on Close for all feeds; we’ll consult only for selected series
        self.bbands = []
        for d in self.datas_list:
            bb = bt.indicators.BollingerBands(
                d.close, period=int(self.p.lookback), devfactor=float(self.p.sdParam)
            )
            self.bbands.append(bb)

    def log(self, txt, dt=None):
        if self.p.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} {txt}")

    def next(self):
        # Don’t act until we have enough bars
        if len(self) <= int(self.p.lookback):
            return

        # For each selected series, set target size based on bands
        for i in self.series_idx:
            d = self.datas_list[i]
            bb = self.bbands[i]

            # Backtrader Bollinger: lines.top (upper), lines.bot (lower)
            close = float(d.close[0])
            up = float(bb.lines.top[0])
            dn = float(bb.lines.bot[0])

            target = 0.0
            if close < dn:
                # contrarian long
                target = +self.pos_sizes[i]
            elif close > up:
                # contrarian short
                target = -self.pos_sizes[i]
            else:
                # inside bands → flat
                target = 0.0

            # Reach the target position on this instrument
            # (order_target_size issues the delta internally)
            self.order_target_size(data=d, size=target)

            if self.p.printlog:
                self.log(
                    f"[data[{i}]] close={close:.4f} dn={dn:.4f} up={up:.4f} → target={target:.2f}"
                )
