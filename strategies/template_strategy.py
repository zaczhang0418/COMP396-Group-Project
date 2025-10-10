# strategies/template_strategy.py
"""
TemplateStrategy
----------------

This is a skeleton strategy file you can copy and edit for COMP396.

- DO NOT call super().next() — the wrapper already handles COMP396Base logic first.
- Use overspend_guard before sending market orders.
- Use place_market and place_limit helpers (they’re injected by the wrapper).
"""

import backtrader as bt

class TemplateStrategy(bt.Strategy):
    """Template Backtrader strategy for COMP396 demonstrating how to use the wrapper’s helpers and guardrails."""
    # -------------------------------------------------------------------------
    # Params can be ANYTHING you need for your strategy.
    # They are accessible inside the class as self.p.<name>.
    #
    # Examples:
    #   ('stake', 10)             -> self.p.stake == 10
    #   ('use_limits', True)      -> self.p.use_limits == True
    #   ('limit_offset', 0.01)    -> self.p.limit_offset == 0.01
    #   ('instrument', 'series_1')-> self.p.instrument == 'series_1'
    #
    # The loader will also inject ('_comp396', None) for framework config.
    # -------------------------------------------------------------------------
    params = (
        ('stake', 10),  # number of units to trade
        ('series_index', 0),  # which data feed to act on (0 = first CSV)
        ('use_limits', False),
        ('limit_offset', 0.01),
    )

    def start(self):
        # Called once at the beginning.
        # You can set up indicators, variables, etc. here.
        pass  # do nothing yet

    def next(self):
        # Called once per bar (i.e. per day).
        # COMP396 rules are already enforced before this runs.

        d = self.datas[self.p.series_index]

        # Example: simple buy once if we have no position
        if not self.getposition(d):
            intents = [(d, self.p.stake)]
            if self.overspend_guard(intents):   # check budget before sending
                self.place_market(d, self.p.stake)
            else:
                self.log("Overspend! No trades today")

        # Example: try limit orders (only 1 buy + 1 sell per series/day allowed)
        # open_px = float(d.open[0])
        # self.place_limit(d, +self.p.stake, price=open_px * 0.99)  # buy 1% below open
        # self.place_limit(d, -self.p.stake, price=open_px * 1.01)  # sell 1% above open

    def notify_order(self, order):
        # Called when an order is completed, rejected, or cancelled.
        # COMP396 slippage is already applied automatically to market orders.

        if order.status in [order.Completed]:
            action = "BUY" if order.isbuy() else "SELL"
            self.log(f"{action} executed at {order.executed.price:.2f} for size {order.executed.size}")
