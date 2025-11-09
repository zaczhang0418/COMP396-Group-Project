# strategies/gr_asset07_v1.py
# GARCH 风险分档 + 趋势入场（四核：p_sigma_q_low / p_sigma_q_high / p_mult_mid / p_mult_high）
import math
import numpy as np
import backtrader as bt
from collections import deque

class GarchSwitchTFV1(bt.Strategy):
    params = dict(
        # ---- 四个核心（进网格）----
        p_sigma_q_low=0.35,      # 低分位阈值（年化波动的滚动分位）
        p_sigma_q_high=0.80,     # 高分位阈值
        p_mult_mid=0.9,          # 中波动 regime 的仓位倍率
        p_mult_high=0.4,         # 高波动 regime 的仓位倍率

        # ---- 其他默认（不改特性）----
        p_garch_alpha=0.08, p_garch_beta=0.90, p_garch_init_lookback=60,
        p_sigma_q_lookback=252, p_ann_factor=252,
        p_ema_short=12, p_ema_long=60,
        p_atr_period=14, p_stop_multiplier=2.0,
        p_target_vol_ann=0.20, p_pos_cap=1.0,
        p_min_w_for_1=0.02,          # 最小建 1 手的权重阈值（与脚本一致）
        p_reenter_cooldown=1,
        data_name='series_7',        # ← 强制 07；若被改动将直接报错
    )

    def __init__(self):
        # —— 强制只交易 series_7（无回退、找不到即报错）——
        if str(self.p.data_name) != "series_7":
            raise ValueError(
                f"[{self.__class__.__name__}] 本策略强制绑定 data_name='series_7'，当前为 '{self.p.data_name}'。"
            )
        names = [d._name for d in self.datas]
        if "series_7" not in names:
            raise ValueError(
                f"[{self.__class__.__name__}] 未找到数据 'series_7'。可用数据：{names}"
            )
        self.d = self.getdatabyname("series_7")

        # 指标
        self.ema_s = bt.ind.EMA(self.d.close, period=int(self.p.p_ema_short))
        self.ema_l = bt.ind.EMA(self.d.close, period=int(self.p.p_ema_long))
        self.atr   = bt.ind.ATR(self.d, period=int(self.p.p_atr_period))

        # GARCH 状态
        self._sigma2 = None; self._omega = None; self._init_done = False
        self._last_ret = 0.0; self._init_buf = []
        self._sigma_ann_hist = deque(maxlen=int(self.p.p_sigma_q_lookback))

        # 交易状态
        self._sl_order = None; self._sl_price = None
        self._cooldown = 0

        need = max(int(self.p.p_ema_long),
                   int(self.p.p_sigma_q_lookback),
                   int(self.p.p_garch_init_lookback)) + 1
        self.addminperiod(need)

    # log return（t-1 -> t）
    def _logret(self):
        if len(self.d) < 2: return 0.0
        p0, p1 = float(self.d.close[0]), float(self.d.close[-1])
        return 0.0 if p1 <= 0 else math.log(p0 / p1)

    # 逐步更新 GARCH(1,1)
    def _update_garch(self, r_t):
        a = float(self.p.p_garch_alpha)
        b = float(self.p.p_garch_beta)
        if not self._init_done:
            self._init_buf.append(r_t)
            if len(self._init_buf) >= int(self.p.p_garch_init_lookback):
                var_lr = np.var(np.asarray(self._init_buf), ddof=1) if len(self._init_buf) > 1 else r_t*r_t
                var_lr = max(var_lr, 1e-12)
                one_minus_ab = max(1e-6, 1.0 - a - b)
                self._omega = one_minus_ab * var_lr
                self._sigma2 = var_lr
                self._init_done = True
            return
        prev = max(self._sigma2, 1e-12)
        self._sigma2 = self._omega + a * (self._last_ret ** 2) + b * prev
        self._sigma2 = max(self._sigma2, 1e-16)

    def _sigma_ann(self):
        if not self._init_done or self._sigma2 is None: return None
        daily = math.sqrt(max(self._sigma2, 1e-16))
        return daily * math.sqrt(float(self.p.p_ann_factor))

    # 根据当前年化波动与分位 regime 生成目标权重
    def _tgt_pct_from_sigma(self, sigma_ann):
        if not (sigma_ann and sigma_ann > 0): return 0.0
        if len(self._sigma_ann_hist) < max(20, int(self.p.p_sigma_q_lookback)//4):
            mult = float(self.p.p_mult_mid)
        else:
            arr = np.asarray(self._sigma_ann_hist, dtype=float)
            ql = np.quantile(arr, float(self.p.p_sigma_q_low))
            qh = np.quantile(arr, float(self.p.p_sigma_q_high))
            if sigma_ann <= ql:  mult = 1.0
            elif sigma_ann >= qh: mult = float(self.p.p_mult_high)
            else:                 mult = float(self.p.p_mult_mid)

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

        bull = self.ema_s[0] > self.ema_l[0] and self.ema_s[-1] <= self.ema_l[-1]
        bear = self.ema_s[0] < self.ema_l[0] and self.ema_s[-1] >= self.ema_l[-1]

        tgt_pct  = self._tgt_pct_from_sigma(sigma_ann)
        openable = abs(tgt_pct) >= float(self.p.p_min_w_for_1)

        pos   = self.getposition(self.d).size
        close = float(self.d.close[0])

        # 已有仓位：止损 / 反向 / 追踪止损 / 再平衡
        if pos != 0:
            if self._sl_price is not None and not math.isnan(self.atr[0]):
                if close <= float(self._sl_price):
                    self.order_target_percent(data=self.d, target=0.0)
                    self._sl_order = None; self._sl_price = None
                    self._last_ret = r_t; return
            if bear:
                self.order_target_percent(data=self.d, target=0.0)
                self._sl_order = None; self._sl_price = None
                self._last_ret = r_t; return

        # 开仓
        if pos == 0:
            if bull and openable and self._cooldown == 0:
                self.order_target_percent(data=self.d,
                                          target=max(tgt_pct, float(self.p.p_min_w_for_1)))
                if not math.isnan(self.atr[0]):
                    self._sl_price = close - float(self.p.p_stop_multiplier) * float(self.atr[0])
                    self._sl_order = self.sell(data=self.d, exectype=bt.Order.Stop, price=self._sl_price)
                self._cooldown = int(self.p.p_reenter_cooldown)
        else:
            # 追踪止损
            if not math.isnan(self.atr[0]):
                new_sl = close - float(self.p.p_stop_multiplier) * float(self.atr[0])
                if (self._sl_price is None) or (new_sl > self._sl_price):
                    self._sl_price = new_sl
                    if self._sl_order: self.cancel(self._sl_order)
                    self._sl_order = self.sell(data=self.d, exectype=bt.Order.Stop,
                                               price=self._sl_price, size=pos)
            # 再平衡
            cur_val = self.broker.get_value()
            cur_pct = (pos * close) / max(cur_val, 1e-9)
            if abs(tgt_pct - cur_pct) >= max(float(self.p.p_min_w_for_1), 0.02):
                self.order_target_percent(data=self.d, target=tgt_pct)

        if self._cooldown > 0: self._cooldown -= 1
        self._last_ret = r_t

Strategy = GarchSwitchTFV1
