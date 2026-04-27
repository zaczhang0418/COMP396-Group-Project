# -*- coding: utf-8 -*-
# strategies/garch_asset07_v1.py
# GARCH regime sizing + EMA trend entry (asset07 only)

import math
import numpy as np
import backtrader as bt
from collections import deque

class GarchSwitchTFV1(bt.Strategy):
    params = dict(
        # ---- core grid params ----
        p_sigma_q_low=0.35,       # lower quantile for ann. vol
        p_sigma_q_high=0.80,      # upper quantile for ann. vol
        p_mult_mid=0.9,           # position multiplier in mid-vol regime
        p_mult_high=0.4,          # position multiplier in high-vol regime

        # ---- other defaults ----
        p_garch_alpha=0.08, p_garch_beta=0.90, p_garch_init_lookback=60,
        p_sigma_q_lookback=252, p_ann_factor=252,
        p_ema_short=12, p_ema_long=60,
        p_atr_period=14, p_stop_multiplier=2.0,
        p_target_vol_ann=0.20, p_pos_cap=1.0,
        p_min_w_for_1=0.02,          # min weight to place a unit position
        p_reenter_cooldown=1,        # bars to wait before re-entry
        data_name='series_7',        # hard bind to asset07
    )

    def __init__(self):
        # hard bind: must trade series_7 only
        if str(self.p.data_name) != "series_7":
            raise ValueError(
                f"[{self.__class__.__name__}] data_name must be 'series_7', got '{self.p.data_name}'"
            )
        names = [d._name for d in self.datas]
        if "series_7" not in names:
            raise ValueError(
                f"[{self.__class__.__name__}] data feed 'series_7' not found; available={names}"
            )
        self.d = self.getdatabyname("series_7")

        # indicators
        self.ema_s = bt.ind.EMA(self.d.close, period=int(self.p.p_ema_short))
        self.ema_l = bt.ind.EMA(self.d.close, period=int(self.p.p_ema_long))
        self.atr   = bt.ind.ATR(self.d, period=int(self.p.p_atr_period))

        # GARCH state
        self._sigma2 = None
        self._omega = None
        self._init_done = False
        self._last_ret = 0.0
        self._init_buf = []
        self._sigma_ann_hist = deque(maxlen=int(self.p.p_sigma_q_lookback))

        # trade state
        self._sl_price = None      # trailing stop price (no pending order; we manage it in logic)
        self._cooldown = 0

        need = max(
            int(self.p.p_ema_long),
            int(self.p.p_sigma_q_lookback),
            int(self.p.p_garch_init_lookback)
        ) + 1
        self.addminperiod(need)

    def _logret(self):
        """log return from t-1 to t"""
        if len(self.d) < 2:
            return 0.0
        p0, p1 = float(self.d.close[0]), float(self.d.close[-1])
        return 0.0 if p1 <= 0 else math.log(p0 / p1)

    def _update_garch(self, r_t):
        a = float(self.p.p_garch_alpha)
        b = float(self.p.p_garch_beta)
        if not self._init_done:
            self._init_buf.append(r_t)
            if len(self._init_buf) >= int(self.p.p_garch_init_lookback):
                var_lr = np.var(np.asarray(self._init_buf), ddof=1) if len(self._init_buf) > 1 else r_t * r_t
                var_lr = max(var_lr, 1e-12)
                one_minus_ab = max(1e-6, 1.0 - a - b)
                self._omega = one_minus_ab * var_lr
                self._sigma2 = var_lr
                self._init_done = True
            return
        prev = max(self._sigma2 if self._sigma2 is not None else 1e-12, 1e-12)
        self._sigma2 = self._omega + a * (self._last_ret ** 2) + b * prev
        self._sigma2 = max(self._sigma2, 1e-16)

    def _sigma_ann(self):
        if not self._init_done or self._sigma2 is None:
            return None
        daily = math.sqrt(max(self._sigma2, 1e-16))
        return daily * math.sqrt(float(self.p.p_ann_factor))

    def _tgt_pct_from_sigma(self, sigma_ann):
        """convert current sigma_ann to target position percent under vol target + regime multipliers"""
        if not (sigma_ann and sigma_ann > 0):
            return 0.0

        # pick multiplier by regime
        if len(self._sigma_ann_hist) < max(20, int(self.p.p_sigma_q_lookback) // 4):
            mult = float(self.p.p_mult_mid)
        else:
            arr = np.asarray(self._sigma_ann_hist, dtype=float)
            ql = np.quantile(arr, float(self.p.p_sigma_q_low))
            qh = np.quantile(arr, float(self.p.p_sigma_q_high))
            if sigma_ann <= ql:
                mult = 1.0
            elif sigma_ann >= qh:
                mult = float(self.p.p_mult_high)
            else:
                mult = float(self.p.p_mult_mid)

        # daily scaling to meet target vol (capped by pos_cap)
        vol_tgt_d = float(self.p.p_target_vol_ann) / math.sqrt(float(self.p.p_ann_factor))
        sigma_d   = sigma_ann / math.sqrt(float(self.p.p_ann_factor))
        raw = vol_tgt_d / max(sigma_d, 1e-10)
        raw = max(-float(self.p.p_pos_cap), min(float(self.p.p_pos_cap), raw))
        return raw * mult

    def next(self):
        r_t = self._logret()
        self._update_garch(r_t)
        sigma_ann = self._sigma_ann()
        if sigma_ann is not None and np.isfinite(sigma_ann):
            self._sigma_ann_hist.append(float(sigma_ann))

        # EMA cross (long-only entry)
        bull = self.ema_s[0] > self.ema_l[0] and self.ema_s[-1] <= self.ema_l[-1]
        bear = self.ema_s[0] < self.ema_l[0] and self.ema_s[-1] >= self.ema_l[-1]

        tgt_pct  = self._tgt_pct_from_sigma(sigma_ann)
        openable = abs(tgt_pct) >= float(self.p.p_min_w_for_1)

        pos   = self.getposition(self.d).size
        close = float(self.d.close[0])

        # exit / reverse / trailing stop
        if pos != 0:
            # stop: logical check (we do not place an exchange stop order to avoid size sync issues)
            if self._sl_price is not None and not math.isnan(self.atr[0]):
                if close <= float(self._sl_price):
                    self.order_target_percent(data=self.d, target=0.0)
                    self._sl_price = None
                    self._last_ret = r_t
                    return
            # reverse on bear cross
            if bear:
                self.order_target_percent(data=self.d, target=0.0)
                self._sl_price = None
                self._last_ret = r_t
                return

        # entry
        if pos == 0:
            if bull and openable and self._cooldown == 0:
                self.order_target_percent(data=self.d,
                                          target=max(tgt_pct, float(self.p.p_min_w_for_1)))
                if not math.isnan(self.atr[0]):
                    self._sl_price = close - float(self.p.p_stop_multiplier) * float(self.atr[0])
                self._cooldown = int(self.p.p_reenter_cooldown)
        else:
            # trailing stop update
            if not math.isnan(self.atr[0]):
                new_sl = close - float(self.p.p_stop_multiplier) * float(self.atr[0])
                if (self._sl_price is None) or (new_sl > self._sl_price):
                    self._sl_price = new_sl

            # rebalance toward target
            cur_val = self.broker.get_value()
            cur_pct = (pos * close) / max(cur_val, 1e-9)
            if abs(tgt_pct - cur_pct) >= max(float(self.p.p_min_w_for_1), 0.02):
                self.order_target_percent(data=self.d, target=tgt_pct)

        if self._cooldown > 0:
            self._cooldown -= 1
        self._last_ret = r_t

Strategy = GarchSwitchTFV1
