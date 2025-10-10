# strategies/simple_limit.py
import backtrader as bt
from math import isfinite

class SimpleLimit(bt.Strategy):
    """
    BT396 market-making strategy (R-port, no look-ahead by default).

    Core:
      • spread = spreadPercentage * range_source(High - Low)
      • BUY limit  at center - 0.5*spread
      • SELL limit at center + 0.5*spread
      • If |position| > inventoryLimits -> flatten with MARKET
      • Place orders once per calendar day (data0 is the global clock)
      • Framework wrapper injects: place_limit, place_market, overspend_guard

    Params:
      size                : units per limit order
      spreadPercentage    : fraction of (H-L) used for the spread (e.g., 0.30)
      inventoryLimits     : flatten if |pos| exceeds this
      center_on           : 'open' (default, no look-ahead) or 'prev_close' (R-ish)
      range_source        : 'yesterday' (default, no look-ahead) or 'today' (look-ahead on daily bars)
      series_mode         : 'all' (act on every feed daily) or 'rotate' (one feed per day)
      rotate_start        : starting index when using 'rotate'
      log_debug           : print diagnostic lines
    """

    params = (
        ('size', 1),
        ('spreadPercentage', 0.30),
        ('inventoryLimits', 50),
        ('center_on', 'open'),          # 'open' (safe) | 'prev_close' (R-ish)
        ('range_source', 'yesterday'),  # 'yesterday' (safe) | 'today' (look-ahead)
        ('series_mode', 'all'),         # 'all' | 'rotate'
        ('rotate_start', 0),
        ('log_debug', True),
    )

    def __init__(self):
        self._last_clock_date = None
        self._day_index = 0  # for rotation

    # --- helpers -------------------------------------------------------------
    def _targets_today(self):
        """Return the list of data feeds to trade today based on series_mode."""
        if self.p.series_mode == 'rotate':
            i = (self.p.rotate_start + self._day_index) % len(self.datas)
            return [self.datas[i]]
        return list(self.datas)

    def _center_price(self, d):
        if self.p.center_on.lower() == 'prev_close':
            if len(d) < 2:
                return None
            return float(d.close[-1])
        # default: today's open (known at bar open)
        return float(d.open[0])

    def _range_value(self, d):
        if self.p.range_source.lower() == 'today':
            # WARNING: on daily bars this is look-ahead. Prefer 'yesterday'.
            hi = float(d.high[0]); lo = float(d.low[0])
        else:
            if len(d) < 2:
                return None
            hi = float(d.high[-1]); lo = float(d.low[-1])
        rng = hi - lo
        return rng if isfinite(rng) and rng > 0 else None

    # --- main loop -----------------------------------------------------------
    def next(self):
        # Run once per calendar day using data0 as the clock
        clock_today = self.datas[0].datetime.date(0)
        if self._last_clock_date == clock_today:
            return
        self._last_clock_date = clock_today
        self._day_index += 1

        if self.p.log_debug:
            self.log(f"SimpleLimit.next() clock={clock_today} mode={self.p.series_mode}")

        # Ensure the BT396 wrapper injected the helpers
        if not all(hasattr(self, n) for n in ("place_limit", "place_market", "overspend_guard")):
            self.log("FATAL: wrapper not injected; aborting today")
            return

        # Decide which feeds to act on today
        targets = self._targets_today()

        for d in targets:
            # --- 0) Inventory risk control (per series) ---
            pos = self.getposition(d).size
            if abs(pos) > self.p.inventoryLimits:
                sz = -pos
                # only BUY side needs cash guard
                if sz > 0 and not self.overspend_guard([(d, sz)]):
                    if self.p.log_debug:
                        self.log(f"{getattr(d,'_name','series')} OVRSPEND: skip flatten BUY")
                else:
                    self.place_market(d, sz)

            # --- 1) Compute today's quotes ---
            center = self._center_price(d)
            rng = self._range_value(d)
            if center is None or rng is None:
                continue

            spread = self.p.spreadPercentage * rng
            buy_px  = round(center - 0.5 * spread, 6)
            sell_px = round(center + 0.5 * spread, 6)

            # --- 2) Submit one BUY + one SELL limit (framework enforces per-side/day) ---
            self.place_limit(d, +abs(self.p.size), price=buy_px)
            self.place_limit(d, -abs(self.p.size), price=sell_px)

            if self.p.log_debug:
                lo0 = float(d.low[0]); hi0 = float(d.high[0])
                self.log(
                    f"{getattr(d,'_name','series')} "
                    f"rng={rng:.4f} spread={spread:.4f} center={center:.4f} "
                    f"buy@{buy_px:.4f} sell@{sell_px:.4f} "
                    f"lo0={lo0:.4f} hi0={hi0:.4f} "
                    f"touch: BUY={lo0 <= buy_px} SELL={hi0 >= sell_px}"
                )

    # Optional: nice fill logs
    def notify_order(self, order):
        if order.status == order.Completed:
            side = "BUY" if order.isbuy() else "SELL"
            self.log(f"{side} filled @ {order.executed.price:.6f} size {order.executed.size}")
