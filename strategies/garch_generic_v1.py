# -*- coding: utf-8 -*-
"""Generic GARCH regime strategy with EMA trend entry."""

import math
from collections import deque

import backtrader as bt
import numpy as np


class GarchGenericV1(bt.Strategy):
    params = dict(
        p_sigma_q_low=0.30,
        p_sigma_q_high=0.85,
        p_mult_mid=0.6,
        p_mult_high=0.4,
        p_garch_alpha=0.08,
        p_garch_beta=0.90,
        p_garch_init_lookback=60,
        p_sigma_q_lookback=252,
        p_ann_factor=252,
        p_ema_short=12,
        p_ema_long=60,
        p_atr_period=14,
        p_stop_multiplier=2.0,
        p_target_vol_ann=0.20,
        p_pos_cap=1.0,
        p_min_w_for_1=0.03,
        p_reenter_cooldown=1,
        p_high_vol_mode="flat",
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

        self.ema_s = bt.ind.EMA(self.d.close, period=int(self.p.p_ema_short))
        self.ema_l = bt.ind.EMA(self.d.close, period=int(self.p.p_ema_long))
        self.atr = bt.ind.ATR(self.d, period=int(self.p.p_atr_period))

        self._sigma2 = None
        self._omega = None
        self._init_done = False
        self._last_ret = 0.0
        self._init_buf = []
        self._sigma_ann_hist = deque(maxlen=int(self.p.p_sigma_q_lookback))
        self._sl_price = None
        self._cooldown = 0

        need = max(
            int(self.p.p_ema_long),
            int(self.p.p_sigma_q_lookback),
            int(self.p.p_garch_init_lookback),
        ) + 1
        self.addminperiod(need)

    def _logret(self) -> float:
        if len(self.d) < 2:
            return 0.0
        p0 = float(self.d.close[0])
        p1 = float(self.d.close[-1])
        return 0.0 if p1 <= 0 else math.log(p0 / p1)

    def _update_garch(self, r_t: float):
        alpha = float(self.p.p_garch_alpha)
        beta = float(self.p.p_garch_beta)
        if not self._init_done:
            self._init_buf.append(r_t)
            if len(self._init_buf) >= int(self.p.p_garch_init_lookback):
                var_lr = np.var(np.asarray(self._init_buf), ddof=1) if len(self._init_buf) > 1 else r_t * r_t
                var_lr = max(var_lr, 1e-12)
                one_minus_ab = max(1e-6, 1.0 - alpha - beta)
                self._omega = one_minus_ab * var_lr
                self._sigma2 = var_lr
                self._init_done = True
            return
        prev = max(self._sigma2 if self._sigma2 is not None else 1e-12, 1e-12)
        self._sigma2 = self._omega + alpha * (self._last_ret ** 2) + beta * prev
        self._sigma2 = max(self._sigma2, 1e-16)

    def _sigma_ann(self):
        if not self._init_done or self._sigma2 is None:
            return None
        daily = math.sqrt(max(self._sigma2, 1e-16))
        return daily * math.sqrt(float(self.p.p_ann_factor))

    def _tgt_pct_from_sigma(self, sigma_ann):
        if not (sigma_ann and sigma_ann > 0):
            return 0.0

        mode = str(self.p.p_high_vol_mode).lower()
        if len(self._sigma_ann_hist) < max(20, int(self.p.p_sigma_q_lookback) // 4):
            mult = float(self.p.p_mult_mid)
        else:
            arr = np.asarray(self._sigma_ann_hist, dtype=float)
            q_low = np.quantile(arr, float(self.p.p_sigma_q_low))
            q_high = np.quantile(arr, float(self.p.p_sigma_q_high))
            if sigma_ann <= q_low:
                mult = 1.0
            elif sigma_ann >= q_high:
                if mode == "flat":
                    return 0.0
                mult = float(self.p.p_mult_high)
            else:
                mult = float(self.p.p_mult_mid)

        vol_tgt_d = float(self.p.p_target_vol_ann) / math.sqrt(float(self.p.p_ann_factor))
        sigma_d = sigma_ann / math.sqrt(float(self.p.p_ann_factor))
        raw = vol_tgt_d / max(sigma_d, 1e-10)
        raw = max(-float(self.p.p_pos_cap), min(float(self.p.p_pos_cap), raw))
        return raw * mult

    def next(self):
        r_t = self._logret()
        self._update_garch(r_t)
        sigma_ann = self._sigma_ann()
        if sigma_ann is not None and np.isfinite(sigma_ann):
            self._sigma_ann_hist.append(float(sigma_ann))

        bull = self.ema_s[0] > self.ema_l[0] and self.ema_s[-1] <= self.ema_l[-1]
        bear = self.ema_s[0] < self.ema_l[0] and self.ema_s[-1] >= self.ema_l[-1]

        tgt_pct = self._tgt_pct_from_sigma(sigma_ann)
        openable = abs(tgt_pct) >= float(self.p.p_min_w_for_1)

        pos = self.getposition(self.d).size
        close = float(self.d.close[0])

        if pos != 0:
            if self._sl_price is not None and not math.isnan(self.atr[0]):
                if close <= float(self._sl_price):
                    self.order_target_percent(data=self.d, target=0.0)
                    self._sl_price = None
                    self._last_ret = r_t
                    return
            if bear:
                self.order_target_percent(data=self.d, target=0.0)
                self._sl_price = None
                self._last_ret = r_t
                return

        if pos == 0:
            if bull and openable and self._cooldown == 0:
                self.order_target_percent(
                    data=self.d,
                    target=max(tgt_pct, float(self.p.p_min_w_for_1)),
                )
                if not math.isnan(self.atr[0]):
                    self._sl_price = close - float(self.p.p_stop_multiplier) * float(self.atr[0])
                self._cooldown = int(self.p.p_reenter_cooldown)
        else:
            if not math.isnan(self.atr[0]):
                new_sl = close - float(self.p.p_stop_multiplier) * float(self.atr[0])
                if (self._sl_price is None) or (new_sl > self._sl_price):
                    self._sl_price = new_sl

            cur_val = self.broker.get_value()
            cur_pct = (pos * close) / max(cur_val, 1e-9)
            if abs(tgt_pct - cur_pct) >= max(float(self.p.p_min_w_for_1), 0.02):
                self.order_target_percent(data=self.d, target=tgt_pct)

        if self._cooldown > 0:
            self._cooldown -= 1
        self._last_ret = r_t


Strategy = GarchGenericV1
