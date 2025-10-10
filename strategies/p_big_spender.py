# strategies/p_big_spender.py
#
# Big Spender
# - Every bar, submit fixed-size MARKET orders per feed (params.sizes).
# - BEFORE submitting, do the R-style affordability estimate:
#       priceEst_i    = sizes[i] * Close_i[today]
#       slippageEst_i = slippage_mult * |sizes[i]| * |Close_i[yday] - Open_i[today]|
#   If sum(priceEst) + sum(slippageEst) > cash → cancel all for today.
# - Orders are routed via COMP396Base (injected by the loader) → buffered,
#   overspend-guarded, and filled next open with framework slippage applied.
#
# Defaults:
#   sizes: None → auto [1.0] * nfeeds at runtime
#   slippage_mult: 0.20
#   printlog: False


import backtrader as bt


class TeamStrategy(bt.Strategy):
    """Portfolio strategy that attempts fixed-size market buys/sells each day across feeds, with a pre-trade affordability check."""
    params = dict(
        sizes=None,          # list[float] per-feed daily market order sizes (can be +/-)
        slippage_mult=0.20,  # affordability proxy (R-style pre-check)
        printlog=False,      # verbose logs
    )

    # ----- utility logging -----
    def _log(self, msg):
        if self.p.printlog and len(self.datas) > 0:
            dt = self.datas[0].datetime.date(0)
            print(f"{dt} {msg}")

    # ----- lifecycle -----
    def __init__(self):
        self.datas_list = list(self.datas)
        self._sizes = None  # will be resolved in start() when nfeeds is known

    def start(self):
        n = len(self.datas_list)
        if n == 0:
            raise ValueError("No data feeds. Provide --portfolio with a matching --data-glob.")
        # Resolve sizes default now (needs nfeeds)
        if self.p.sizes is None:
            self._sizes = [1.0] * n
        else:
            if len(self.p.sizes) != n:
                raise ValueError(f"len(sizes) must equal number of feeds ({n}), got {len(self.p.sizes)}")
            self._sizes = [float(x) for x in self.p.sizes]

        self._log("=== p_big_spender (wrapped) wired ===")
        self._log(f"feeds={n} names={[d._name for d in self.datas_list]}")
        self._log(f"sizes={self._sizes}")
        self._log(f"slippage_mult={self.p.slippage_mult}")

    def next(self):
        # ---- R-style affordability estimate on today's bar ----
        cash = float(self.broker.getcash())
        total_price = 0.0
        total_slip  = 0.0

        for i, d in enumerate(self.datas_list):
            qty = float(self._sizes[i])
            if qty == 0:
                continue

            close_today = float(d.close[0])
            open_today  = float(d.open[0])
            close_yday  = float(d.close[-1]) if len(d) > 1 else close_today

            price_est = qty * close_today
            slip_est  = float(self.p.slippage_mult) * abs(qty) * abs(close_yday - open_today)

            total_price += price_est
            total_slip  += slip_est

        if total_price + total_slip > cash:
            self._log(f"[CANCEL] est_cost={total_price:.2f} est_slip={total_slip:.2f} cash={cash:.2f}")
            return

        # ---- Queue market orders for ALL feeds (buffered; guard will run at flush) ----
        for i, d in enumerate(self.datas_list):
            qty = float(self._sizes[i])
            if qty == 0:
                continue
            self.place_market(d, qty)  # provided by wrapper’s COMP396Base
            self._log(f"[ORDER QUEUED] {d._name} size={qty:+.4f}")

    # ----- detailed logging: orders + trades -----
    def notify_order(self, order):
        # Wrapper calls COMP396Base.notify_order first (slippage, etc.),
        # then this method. We log status transitions & executions.
        d = order.data
        if order.status == order.Submitted:
            self._log(f"[ORDER SUBMITTED] {d._name} type={order.exectype} size={order.size:+.4f}")
        elif order.status == order.Accepted:
            self._log(f"[ORDER ACCEPTED]  {d._name} type={order.exectype} size={order.size:+.4f}")
        elif order.status == order.Completed:
            side = "BUY" if order.isbuy() else "SELL"
            self._log(
                f"[FILL] {side} {d._name} px={order.executed.price:.4f} "
                f"size={order.executed.size:+.4f} "
                f"value={order.executed.value:.2f} comm={order.executed.comm:.2f}"
            )
        elif order.status in [order.Canceled, order.Rejected, order.Margin]:
            self._log(f"[ORDER {order.getstatusname().upper()}] {d._name} size={order.size:+.4f}")

    def notify_trade(self, trade):
        # Called when a trade updates/closes; log PnL details.
        if trade.isclosed:
            self._log(
                f"[TRADE CLOSED] {trade.data._name} pnl={trade.pnl:.2f} pnl_comm={trade.pnlcomm:.2f} "
                f"size={trade.size:+.4f}"
            )
        else:
            # Mark-to-market update (optional)
            self._log(
                f"[TRADE UPDATE] {trade.data._name} size={trade.size:+.4f} "
                f"pnl={trade.pnl:.2f} pnl_comm={trade.pnlcomm:.2f}"
            )
