# strategies/p_bbands_trend_following.py
#
# Portfolio Bollinger Bands trend-following strategy (breakout):
# - Trades ONLY the series in params.series (1-based indexes, like the R code).
# - If Close > upper band → LONG; if Close < lower band → SHORT.
# - Inside bands: hold prior position (optional: exit to flat when crossing mid).
#
# Usage (example with 10 feeds):

#
# Notes:
# - Slippage is handled by the framework (--smult) during results processing.
# - Provide posSizes of length == number of feeds, or rely on default_size.
# - series is 1-based to match the R originals.

import backtrader as bt


class TeamStrategy(bt.Strategy):
    """Portfolio Bollinger Bands breakout (trend-following) strategy that goes long above the upper band and short below the lower band."""
    params = dict(
        lookback=20,           # Bollinger window length (n)
        sdParam=2.0,           # std dev multiplier
        series=None,           # list of 1-based feed indices to trade; default = all
        posSizes=None,         # per-feed target sizes (len == n_feeds)
        default_size=1.0,      # used if posSizes is None
        exit_on_mid=False,     # if True, exit to flat when price crosses middle band
        printlog=False,
    )

    def __init__(self):
        self.datas_list = list(self.datas)
        nfeeds = len(self.datas_list)
        if nfeeds == 0:
            raise ValueError("No data feeds. Use --portfolio with a matching --data-glob.")

        # Select series (convert 1-based to 0-based)
        if self.p.series is None:
            self.series_idx = list(range(nfeeds))
        else:
            self.series_idx = [i - 1 for i in self.p.series if 1 <= i <= nfeeds]
            if not self.series_idx:
                raise ValueError("params.series produced no valid indices for available feeds.")

        # Per-feed sizes
        if self.p.posSizes is None:
            self.pos_sizes = [float(self.p.default_size)] * nfeeds
        else:
            if len(self.p.posSizes) != nfeeds:
                raise ValueError(
                    f"posSizes length {len(self.p.posSizes)} must match number of feeds {nfeeds}."
                )
            self.pos_sizes = [float(x) for x in self.p.posSizes]

        # Bollinger bands per feed
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
        # Wait for enough data
        if len(self) <= int(self.p.lookback):
            return

        for i in self.series_idx:
            d = self.datas_list[i]
            bb = self.bbands[i]

            close = float(d.close[0])
            up = float(bb.lines.top[0])
            mid = float(bb.lines.mid[0])
            dn = float(bb.lines.bot[0])

            size_base = self.pos_sizes[i]
            target = None  # None means "no change" (hold)

            if close > up:
                target = +size_base
            elif close < dn:
                target = -size_base
            else:
                if self.p.exit_on_mid:
                    # Exit to flat if we’re inside bands AND crossed the mid line
                    prev_close = float(d.close[-1]) if len(d) > 1 else close
                    crossed_mid = (prev_close <= mid < close) or (prev_close >= mid > close)
                    if crossed_mid:
                        target = 0.0
                # else: leave target=None to hold existing position

            if target is not None:
                self.order_target_size(data=d, size=target)
                if self.p.printlog:
                    self.log(
                        f"[data[{i}]] close={close:.4f} dn={dn:.4f} mid={mid:.4f} up={up:.4f} "
                        f"→ target={target:.2f}"
                    )
