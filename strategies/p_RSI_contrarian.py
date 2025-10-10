# strategies/p_rsi_contrarian.py
#
# Portfolio RSI contrarian strategy:
# - Trades ONLY the series in params.series (1-based indexes, like the R code).
# - If RSI > 50 + threshold → SHORT (contrarian).
# - If RSI < 50 - threshold → LONG  (contrarian).
# - Else → FLAT.
#
# Uses market orders via order_target_size to implement:
#   orders = (desired_position) - (current_position)
#
# Example:
#   python run_backtest.py \
#       --strategy p_rsi_contrarian \
#       --data-glob "DATA/PART1/*.csv" \
#       --portfolio \
#       --cash 1000000 \
#       --commission 0.0
#
# Notes:
# - We require at least (lookback + 2) bars before acting (matches the R comment).
# - Provide posSizes as a full-length list (len == n_feeds) or rely on default_size.
# - Framework slippage (--smult) still applies during results processing.

import backtrader as bt


class TeamStrategy(bt.Strategy):
    """Portfolio contrarian strategy that targets long when RSI is below 50−threshold and short when above 50+threshold on selected series."""
    params = dict(
        lookback=14,           # RSI window (n)
        threshold=5.0,         # 0..50: contrarian band around 50
        series=None,           # list of 1-based feed indices to trade; default = all feeds
        posSizes=None,         # per-feed absolute sizes (len == n_feeds)
        default_size=1.0,      # used if posSizes is None
        printlog=False,
    )

    def __init__(self):
        self.datas_list = list(self.datas)
        nfeeds = len(self.datas_list)
        if nfeeds == 0:
            raise ValueError("No data feeds. Use --portfolio with a matching --data-glob.")

        # Validate threshold similarly to R
        if not (0 <= float(self.p.threshold) <= 50):
            raise ValueError("threshold must be between 0 and 50.")

        # Select series (convert 1-based to 0-based). Default = all feeds.
        if self.p.series is None:
            self.series_idx = list(range(nfeeds))
        else:
            self.series_idx = [i - 1 for i in self.p.series if 1 <= i <= nfeeds]
            if not self.series_idx:
                raise ValueError("params.series produced no valid indices for available feeds.")

        # Per-feed target sizes
        if self.p.posSizes is None:
            self.pos_sizes = [float(self.p.default_size)] * nfeeds
        else:
            if len(self.p.posSizes) != nfeeds:
                raise ValueError(
                    f"posSizes length {len(self.p.posSizes)} must match number of feeds {nfeeds}."
                )
            self.pos_sizes = [float(x) for x in self.p.posSizes]

        # Build RSI indicators per feed
        self.rsi = []
        for d in self.datas_list:
            self.rsi.append(bt.indicators.RSI(d.close, period=int(self.p.lookback)))

    def log(self, txt, dt=None):
        if self.p.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} {txt}")

    def next(self):
        # Match the R note: need lookback + 2 bars before using RSI
        if len(self) < int(self.p.lookback) + 2:
            return

        up_lvl = 50.0 + float(self.p.threshold)
        dn_lvl = 50.0 - float(self.p.threshold)

        for i in self.series_idx:
            d = self.datas_list[i]
            r = float(self.rsi[i][0])

            # Decide desired direction: +1 long, -1 short, 0 flat (contrarian)
            if r > up_lvl:
                dir_signal = -1
            elif r < dn_lvl:
                dir_signal = +1
            else:
                dir_signal = 0

            target = dir_signal * self.pos_sizes[i]

            # This issues the delta needed to reach the absolute target
            self.order_target_size(data=d, size=target)

            if self.p.printlog:
                self.log(f"[data[{i}]] RSI={r:.2f} (>{up_lvl:.2f} short / <{dn_lvl:.2f} long) → target={target:+.2f}")
