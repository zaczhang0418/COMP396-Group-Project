# strategies/p_mm_spread.py
#
# Portfolio "pseudo market making" strategy:
# - If |position| > inventoryLimits → flatten (market) and skip quoting today.
# - Else place 1 BUY limit and 1 SELL limit per instrument each day.
# - Limits are auto-cancelled at the end of the day (we cancel at next bar open).
#
# spread_i[today] = spreadPercentage * (High_i[yday] - Low_i[yday])
# Quotes centered on Close_i[yday]:
#   buy_limit  = Close_yday - spread/2
#   sell_limit = Close_yday + spread/2
#
# Usage:
#   python run_backtest.py \
#     --strategy p_mm_spread \
#     --data-glob "DATA/PART1/*.csv" \
#     --portfolio \
#     --cash 1000000 \
#     --commission 0.0
#
# Notes:
# - Framework slippage (--smult) applies to realized PnL (limit orders in your
#   framework are treated with no slippage).
# - inventoryLimits can be scalar or list[len(feeds)].

import backtrader as bt
import math


class TeamStrategy(bt.Strategy):
    """Portfolio pseudo market-making strategy that places daily buy/sell limits within a spread unless inventory limits are breached."""
    params = dict(
        spreadPercentage=0.10,     # e.g., 10% of prior day's range
        inventoryLimits=1000,      # scalar or list per feed (units)
        quote_size=1,              # how many units to place for each limit
        printlog=False,
    )

    def __init__(self):
        self.datas_list = list(self.datas)
        n = len(self.datas_list)
        if n == 0:
            raise ValueError("No data feeds. Use --portfolio with a matching --data-glob.")

        # Normalize inventoryLimits to a per-feed list
        if isinstance(self.p.inventoryLimits, (list, tuple)):
            if len(self.p.inventoryLimits) != n:
                raise ValueError(
                    f"inventoryLimits length {len(self.p.inventoryLimits)} must match number of feeds {n}."
                )
            self.inv_limits = [float(x) for x in self.p.inventoryLimits]
        else:
            self.inv_limits = [float(self.p.inventoryLimits)] * n

        # Track today's outstanding limit orders so we can cancel them tomorrow
        self.open_buy_orders = {d: None for d in self.datas_list}
        self.open_sell_orders = {d: None for d in self.datas_list}

    def log(self, txt, dt=None):
        if self.p.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} {txt}")

    def _cancel_if_open(self, o):
        if o is not None and o.status in [bt.Order.Submitted, bt.Order.Accepted]:
            try:
                self.cancel(o)
            except Exception:
                pass  # ignore cancel failures if already completed/rejected

    def next(self):
        # 1) Cancel yesterday's still-open limits (auto-cancel at day end semantics)
        for d in self.datas_list:
            self._cancel_if_open(self.open_buy_orders[d])
            self._cancel_if_open(self.open_sell_orders[d])
            self.open_buy_orders[d] = None
            self.open_sell_orders[d] = None

        # 2) For each instrument, either flatten (if over inventory limit) or place fresh quotes
        for i, d in enumerate(self.datas_list):
            pos = self.getposition(d).size
            lim = self.inv_limits[i]

            # If over inventory limit → flatten to zero position
            if abs(pos) > lim:
                self.order_target_size(data=d, size=0)
                self.log(f"[data[{i}]] |pos|={abs(pos):.0f} > limit={lim:.0f} → flatten")
                continue

            # Need at least 2 bars to compute yesterday's range
            if len(d) < 2:
                continue

            close_yday = float(d.close[-1])
            high_yday = float(d.high[-1])
            low_yday = float(d.low[-1])

            day_range = max(0.0, high_yday - low_yday)
            spread = float(self.p.spreadPercentage) * day_range

            # If range is zero, place very tight quotes around close
            half = spread * 0.5
            buy_px = close_yday - half
            sell_px = close_yday + half

            # Guard against nonsensical prices
            if not (math.isfinite(buy_px) and math.isfinite(sell_px)):
                continue

            qty = float(self.p.quote_size)
            if qty <= 0:
                continue

            # 3) Place new daily limit orders
            # BUY limit below/at current reference
            self.open_buy_orders[d] = self.buy(data=d, size=qty, exectype=bt.Order.Limit, price=buy_px)
            # SELL limit above/at current reference
            self.open_sell_orders[d] = self.sell(data=d, size=qty, exectype=bt.Order.Limit, price=sell_px)

            if self.p.printlog:
                self.log(
                    f"[data[{i}]] pos={pos:+.0f} lim={lim:.0f} "
                    f"close_yday={close_yday:.4f} rng={day_range:.4f} "
                    f"buy@{buy_px:.4f} sell@{sell_px:.4f} qty={qty}"
                )
