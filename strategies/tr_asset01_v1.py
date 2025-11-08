# strategies/tr_asset01_v1.py
import backtrader as bt
import numpy as np

class RollingQuantile(bt.Indicator):
    lines = ('q',)
    params = dict(period=252, quantile=0.95)
    def __init__(self): self.addminperiod(self.p.period)
    def next(self):
        vals = np.array(self.data.get(size=self.p.period), dtype=float)
        vals = vals[np.isfinite(vals)]
        self.lines.q[0] = float('nan') if vals.size == 0 else float(np.quantile(vals, self.p.quantile))

class RollingHurst(bt.Indicator):
    lines = ('hurst',)
    params = dict(period=252)
    def __init__(self): self.addminperiod(self.p.period)
    def next(self):
        window = self.data.get(size=self.p.period)
        if window is None or len(window) < self.p.period:
            self.lines.hurst[0] = float('nan'); return
        x = np.log(np.asarray(list(window), dtype=float))
        if not np.isfinite(x).all():
            self.lines.hurst[0] = float('nan'); return
        dev = x - x.mean()
        cum = np.cumsum(dev)
        R = float(np.max(cum) - np.min(cum))
        S = float(np.std(x))
        if S <= 0 or R <= 0:
            self.lines.hurst[0] = 0.5
        else:
            H = np.log(R / S) / np.log(self.p.period)
            self.lines.hurst[0] = float(np.clip(H, 0.0, 1.0))

class TF_Asset01_Hurst_V1(bt.Strategy):
    params = dict(
        # ——四核（网格会调这四个）——
        p_ema_short=12,
        p_ema_long=90,
        p_hurst_min_soft=0.54,
        p_stop_multiplier=2.0,

        # ——其余默认参数（不进网格，但可 CLI 覆盖）——
        p_hurst_period=252, p_hurst_power=1.0, p_hurst_ema=10,
        p_atr_period=14, p_target_vol_ann=0.18, p_pos_cap=1.0,
        p_circuit_breaker_window=252, p_circuit_breaker_pct=0.9999,
        p_min_w_for_1=0.12, p_rebalance_tol=999, p_pyr_n=0, p_pyr_step_atr=1.0,
        p_debug=False, data_name='series_1',
    )

    def __init__(self):
        try: self.d = self.getdatabyname(self.p.data_name)
        except Exception: self.d = self.datas[0]

        self.ema_s = bt.ind.EMA(self.d.close, period=int(self.p.p_ema_short))
        self.ema_l = bt.ind.EMA(self.d.close, period=int(self.p.p_ema_long))
        self.atr   = bt.ind.ATR(self.d, period=int(self.p.p_atr_period))
        self.hurst = RollingHurst(self.d.close, period=int(self.p.p_hurst_period))
        self.atr_q = RollingQuantile(self.atr,
                                     period=int(self.p.p_circuit_breaker_window),
                                     quantile=float(self.p.p_circuit_breaker_pct))
        self._w_state = 0.01
        self._alpha_w = 2.0 / (float(self.p.p_hurst_ema) + 1.0) if float(self.p.p_hurst_ema) > 0 else 1.0
        self._main_order = None; self._sl_order = None; self._sl_price = None
        self._pyr_last_entry = None; self._pyr_count = 0
        self.addminperiod(max(int(self.p.p_ema_long), int(self.p.p_hurst_period), int(self.p.p_circuit_breaker_window)) + 1)

    def _update_weight(self):
        h = float(self.hurst[0]) if np.isfinite(self.hurst[0]) else None
        hmin = float(self.p.p_hurst_min_soft)
        if h is None or h <= hmin: w_raw = 0.01
        else:
            w_raw = (h - hmin) / max(1e-9, (1.0 - hmin))
            w_raw = min(1.0, max(0.01, w_raw))
        w_raw = w_raw ** float(self.p.p_hurst_power)
        self._w_state = self._alpha_w * w_raw + (1.0 - self._alpha_w) * self._w_state

    def _target_size(self) -> int:
        close = float(self.d.close[0]); atr = float(self.atr[0])
        if not (np.isfinite(close) and close > 0 and np.isfinite(atr) and atr > 0): return 0
        ann_atr_pct = (atr / close) * np.sqrt(252.0)
        if not (np.isfinite(ann_atr_pct) and ann_atr_pct > 1e-8): return 0
        lev = min(float(self.p.p_target_vol_ann) / ann_atr_pct, float(self.p.p_pos_cap))
        base_shares = (self.broker.get_value() * lev) / close
        raw = base_shares * self._w_state
        if raw < 1.0 and self._w_state >= float(self.p.p_min_w_for_1): return 1
        return int(max(0.0, raw))

    def next(self):
        atr_q_val = float(self.atr_q[0]) if np.isfinite(self.atr_q[0]) else float('inf')
        circuit_on = float(self.atr[0]) > atr_q_val
        self._update_weight()
        if self._main_order and self._main_order.status in (bt.Order.Submitted, bt.Order.Accepted): return

        pos = int(self.getposition(self.d).size)
        bull = self.ema_s[0] > self.ema_l[0] and self.ema_s[-1] <= self.ema_l[-1]
        bear = self.ema_s[0] < self.ema_l[0] and self.ema_s[-1] >= self.ema_l[-1]
        target = self._target_size()
        if target == 0 and (self._w_state >= float(self.p.p_min_w_for_1)) and (not circuit_on): target = 1

        if pos == 0 and (not circuit_on) and bull:
            if target > 0:
                self._sl_price = float(self.d.close[0] - float(self.p.p_stop_multiplier) * self.atr[0])
                self._main_order = self.buy(data=self.d, size=target)
                self._pyr_last_entry = float(self.d.close[0]); self._pyr_count = 0
            return

        if pos != 0 and bear:
            if self._sl_order: self.cancel(self._sl_order)
            self._main_order = self.close(data=self.d)
            self._pyr_last_entry = None; self._pyr_count = 0
            return

        if pos != 0:
            if not circuit_on:
                tol = float(self.p.p_rebalance_tol); diff = target - pos
                if target > 0 and abs(diff) >= max(1, int(abs(pos) * tol)):
                    self._main_order = self.buy(data=self.d, size=diff) if diff > 0 else self.sell(data=self.d, size=abs(diff))
            if not circuit_on and self._pyr_last_entry is not None and self._pyr_count < int(self.p.p_pyr_n):
                step = float(self.p.p_pyr_step_atr) * float(self.atr[0]); trigger = self._pyr_last_entry + step
                if float(self.d.close[0]) >= trigger and target > pos:
                    add = max(1, target - pos); self._main_order = self.buy(data=self.d, size=add)
                    self._pyr_last_entry = float(self.d.close[0]); self._pyr_count += 1

            new_sl = float(self.d.close[0] - float(self.p.p_stop_multiplier) * self.atr[0])
            if self._sl_price is None: self._sl_price = new_sl
            improve = new_sl - (self._sl_price or new_sl)
            if improve > max(0.0, 0.001 * self._sl_price):
                if self._sl_order: self.cancel(self._sl_order)
                self._sl_price = new_sl
                self._sl_order = self.sell(data=self.d, exectype=bt.Order.Stop, price=self._sl_price, size=pos, transmit=True)

    def notify_order(self, order):
        if order.data != self.d: return
        if order.status in (order.Submitted, order.Accepted): return
        if order.status == order.Completed:
            if order.isbuy():
                if self._sl_order and self._sl_order.status in (bt.Order.Submitted, bt.Order.Accepted):
                    self.cancel(self._sl_order)
                self._sl_order = self.sell(data=self.d, exectype=bt.Order.Stop, price=self._sl_price, size=order.executed.size, transmit=True)
                self._pyr_last_entry = float(order.executed.price); self._main_order = None
            else:
                if self._sl_order and order.ref != self._sl_order.ref: self.cancel(self._sl_order)
                self._sl_order = None; self._main_order = None
        elif order.status in (order.Canceled, order.Margin, order.Rejected):
            if self._sl_order and order.ref == self._sl_order.ref: self._sl_order = None
            if self._main_order and order.ref == self._main_order.ref: self._main_order = None

Strategy = TF_Asset01_Hurst_V1  # 供框架加载
