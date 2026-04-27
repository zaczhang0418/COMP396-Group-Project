# -*- coding: utf-8 -*-
"""Generic z-score mean-reversion strategy."""

import backtrader as bt
import numpy as np


class RollingQuantile(bt.Indicator):
    lines = ("q",)
    params = dict(period=252, quantile=0.90, min_req=5)

    def __init__(self):
        self.addminperiod(1)

    def next(self):
        avail = len(self.data)
        win = min(avail, int(self.p.period))
        if win < max(int(self.p.min_req), int(self.p.period * 0.2)):
            self.lines.q[0] = float("nan")
            return
        vals = np.array(self.data.get(size=win), dtype=float)
        vals = vals[np.isfinite(vals)]
        self.lines.q[0] = float("nan") if vals.size == 0 else float(np.quantile(vals, float(self.p.quantile)))


class ZScore(bt.Indicator):
    lines = ("z",)
    params = dict(period=60, min_req=10)

    def __init__(self):
        self.addminperiod(1)

    def next(self):
        length = int(self.p.period)
        avail = len(self.data)
        win = min(avail, length)
        if win < max(int(self.p.min_req), int(length * 0.5)):
            self.lines.z[0] = float("nan")
            return
        vals = np.array(self.data.get(size=win), dtype=float)
        vals = vals[np.isfinite(vals)]
        if vals.size == 0:
            self.lines.z[0] = float("nan")
            return
        mean = vals.mean()
        std = vals.std(ddof=0)
        current = float(self.data[0])
        self.lines.z[0] = float("nan") if std <= 0 or not np.isfinite(current) else (current - mean) / std


class MR_Generic_V1(bt.Strategy):
    params = dict(
        p_lookback=40,
        p_entry_z=2.0,
        p_exit_z=0.5,
        p_stop_mult=2.0,
        p_entry_mode="reconfirm",
        p_cooldown_bars=2,
        p_max_hold_days=7,
        p_atr_period=14,
        p_atr_pctl_window=252,
        p_atr_pctl_enter=0.90,
        p_target_vol_ann=0.18,
        p_pos_cap=1.0,
        p_w_z_cap=3.0,
        p_w_power=1.0,
        p_min_w_for_1=0.12,
        p_debug=False,
        data_name=None,
    )

    def __init__(self):
        if self.p.data_name:
            try:
                self.d = self.getdatabyname(self.p.data_name)
            except Exception:
                self.d = self.datas[0]
        else:
            self.d = self.datas[0]

        self.z = ZScore(self.d.close, period=self.p.p_lookback)
        self.atr = bt.ind.ATR(self.d, period=self.p.p_atr_period)
        self.atr_pct = self.atr / self.d.close
        self.atr_pct_q = RollingQuantile(
            self.atr_pct,
            period=self.p.p_atr_pctl_window,
            quantile=self.p.p_atr_pctl_enter,
        )

        self._main_order = None
        self._sl_order = None
        self._sl_price = None
        self._entry_bar = None
        self._entry_price = None
        self._cooldown = 0
        self.addminperiod(max(int(self.p.p_lookback), int(self.p.p_atr_period), 5))

    def _atr_ann_pct(self) -> float:
        close = float(self.d.close[0])
        atr = float(self.atr[0])
        if not (np.isfinite(close) and close > 0 and np.isfinite(atr) and atr > 0):
            return np.nan
        return (atr / close) * np.sqrt(252.0)

    def _target_size(self, direction: int, z_val: float) -> int:
        ann_atr_pct = self._atr_ann_pct()
        if not (np.isfinite(ann_atr_pct) and ann_atr_pct > 1e-8):
            return 0
        base_w = min(self.p.p_target_vol_ann / ann_atr_pct, self.p.p_pos_cap)
        dist_w = min(1.0, abs(z_val) / max(1e-12, float(self.p.p_w_z_cap))) ** float(self.p.p_w_power)
        weight = max(0.0, min(1.0, base_w * dist_w))
        if weight <= 0:
            return 0
        close = float(self.d.close[0])
        raw_units = (self.broker.get_value() * weight) / max(1e-12, close)
        if weight >= float(self.p.p_min_w_for_1) and abs(raw_units) < 1.0:
            raw_units = 1.0
        return int(direction * max(0.0, raw_units))

    def _entry_ready(self, z_now: float, z_prev: float, direction: int) -> bool:
        mode = str(self.p.p_entry_mode).lower()
        if mode == "touch":
            return True
        if not np.isfinite(z_prev):
            return False
        if direction > 0:
            return z_now > z_prev
        return z_now < z_prev

    def next(self):
        if self._main_order and self._main_order.status in (bt.Order.Submitted, bt.Order.Accepted):
            return

        if self._cooldown > 0:
            self._cooldown -= 1

        pos = int(self.getposition(self.d).size)
        z_now = float(self.z.z[0]) if np.isfinite(self.z.z[0]) else np.nan
        z_prev = float(self.z.z[-1]) if len(self) > 1 and np.isfinite(self.z.z[-1]) else np.nan
        atr_pct = float(self.atr_pct[0]) if np.isfinite(self.atr_pct[0]) else np.nan
        qthr = float(self.atr_pct_q[0]) if np.isfinite(self.atr_pct_q[0]) else np.nan
        allow_enter = np.isfinite(atr_pct) and np.isfinite(qthr) and (atr_pct <= qthr)

        if pos != 0:
            if self._entry_bar is not None:
                held = len(self) - self._entry_bar
                if self.p.p_max_hold_days > 0 and held >= int(self.p.p_max_hold_days):
                    self._close_position(reason=f"time({held}>={self.p.p_max_hold_days})")
                    return
            if np.isfinite(z_now) and abs(z_now) <= float(self.p.p_exit_z):
                self._close_position(reason=f"z_exit(|z|={abs(z_now):.2f}<={self.p.p_exit_z})")
                return

        if pos == 0 and allow_enter and np.isfinite(z_now) and self._cooldown == 0:
            direction = 0
            if z_now <= -float(self.p.p_entry_z):
                direction = +1
            elif z_now >= float(self.p.p_entry_z):
                direction = -1

            if direction != 0 and self._entry_ready(z_now, z_prev, direction):
                tgt = self._target_size(direction, z_now)
                if abs(tgt) > 0:
                    if direction > 0:
                        self._main_order = self.buy(data=self.d, size=abs(tgt))
                    else:
                        self._main_order = self.sell(data=self.d, size=abs(tgt))
                    self._log(f"ENTRY dir={direction:+d} size={abs(tgt)} z={z_now:.2f}")
                else:
                    self._log("FILTERED size=0 (weight too small)")
            else:
                self._log("NO SIGNAL (z within band)")

    def notify_order(self, order):
        if order.data != self.d:
            return
        if order.status in (order.Submitted, order.Accepted):
            return

        if order.status == order.Completed:
            if order.isbuy() or order.issell():
                pos = int(self.getposition(self.d).size)
                if pos != 0 and self._entry_bar is None:
                    self._entry_bar = len(self)
                    self._entry_price = float(order.executed.price)
                    atr = float(self.atr[0])
                    if np.isfinite(atr) and atr > 0:
                        if pos > 0:
                            self._sl_price = self._entry_price - float(self.p.p_stop_mult) * atr
                            self._sl_order = self.sell(
                                data=self.d,
                                exectype=bt.Order.Stop,
                                price=self._sl_price,
                                size=pos,
                            )
                        else:
                            self._sl_price = self._entry_price + float(self.p.p_stop_mult) * atr
                            self._sl_order = self.buy(
                                data=self.d,
                                exectype=bt.Order.Stop,
                                price=self._sl_price,
                                size=abs(pos),
                            )
                        self._log(f"SL set @{self._sl_price:.4f}")
                elif pos == 0:
                    self._cooldown = max(self._cooldown, int(self.p.p_cooldown_bars))
                    self._entry_bar = None
                    self._entry_price = None
                    self._sl_price = None
                    self._sl_order = None
                self._main_order = None
        elif order.status in (order.Canceled, order.Margin, order.Rejected):
            self._log(f"ORDER {order.getstatusname()}")
            if self._main_order and order.ref == self._main_order.ref:
                self._main_order = None
            if self._sl_order and order.ref == self._sl_order.ref:
                self._sl_order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self._log(f"TRADE PNL(Comm): {trade.pnlcomm:.2f}")

    def _close_position(self, reason: str = ""):
        if self._sl_order:
            try:
                self.cancel(self._sl_order)
            except Exception:
                pass
            self._sl_order = None
        self._main_order = self.close(data=self.d)
        self._log(f"EXIT | {reason}")
        self._cooldown = max(self._cooldown, int(self.p.p_cooldown_bars))
        self._entry_bar = None
        self._entry_price = None
        self._sl_price = None

    def _log(self, msg: str):
        if self.p.p_debug:
            dt = self.d.datetime.date(0)
            name = getattr(self.d, "_name", self.p.data_name or "data0")
            print(f"[{dt}] {name} | {msg}")


Strategy = MR_Generic_V1
