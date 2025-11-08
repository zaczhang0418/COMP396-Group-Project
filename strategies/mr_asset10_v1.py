# MR_Asset10_ZScore_V1.py — Z-Score 均值回归（V1 基线）
# 结构对齐 TF_Asset01_Hurst_V1：四旋钮 + 目标波动率配仓 + 最小1手补丁 + ATR 止损 + 时间止损
# 注意：输出层级/目录由你们外层 runner 决定；本策略通过 data_name 保持与输出命名一致。

import backtrader as bt
import numpy as np


class RollingQuantile(bt.Indicator):
    lines = ('q',)
    params = dict(period=252, quantile=0.90, min_req=5)

    def __init__(self):
        self.addminperiod(1)  # 不再卡到 period

    def next(self):
        avail = len(self.data)
        win = min(avail, int(self.p.period))
        if win < max(int(self.p.min_req), int(self.p.period * 0.2)):
            self.lines.q[0] = float('nan')
            return
        vals = np.array(self.data.get(size=win), dtype=float)
        vals = vals[np.isfinite(vals)]
        self.lines.q[0] = float('nan') if vals.size == 0 else float(np.quantile(vals, float(self.p.quantile)))




class ZScore(bt.Indicator):
    lines = ('z',)
    params = dict(period=60, min_req=10)

    def __init__(self):
        self.addminperiod(1)

    def next(self):
        L = int(self.p.period)
        avail = len(self.data)
        win = min(avail, L)
        if win < max(int(self.p.min_req), int(L * 0.5)):
            self.lines.z[0] = float('nan'); return
        vals = np.array(self.data.get(size=win), dtype=float)
        vals = vals[np.isfinite(vals)]
        if vals.size == 0:
            self.lines.z[0] = float('nan'); return
        m = vals.mean()
        s = vals.std(ddof=0)
        x = float(self.data[0])
        self.lines.z[0] = float('nan') if s <= 0 or not np.isfinite(x) else (x - m) / s



# =========[ 策略主体：Z-Score MR + ATR% 分位过滤 + 目标波动率配仓 ]=========
class MR_Asset10_ZScore_V1(bt.Strategy):
    params = dict(
        # --- Core-4（入网格） ---
        p_lookback=60,         # Z-Score 窗口
        p_entry_z=1.6,         # 入场阈值（双边）
        p_exit_z=0.4,          # 回归离场阈值（|z| <= exit_z）
        p_stop_mult=2.0,       # ATR 止损倍数（静态）

        # --- 固定侧 ---
        p_max_hold_days=7,     # 时间止损（持仓条数）
        p_atr_period=14,
        p_atr_pctl_window=252, # 滚动分位窗口
        p_atr_pctl_enter=0.90, # 仅 ATR% ≤ 此分位才允许新开仓

        p_target_vol_ann=0.18, # 目标年化波动率
        p_pos_cap=1.0,         # 最大杠杆上限
        p_w_z_cap=3.0,         # 距离权重上限（|z| / w_z_cap → [0,1]）
        p_w_power=1.0,         # 距离权重幂次
        p_min_w_for_1=0.12,    # 最小 1 手补丁阈值

        # --- 其他 ---
        p_debug=False,
        data_name='asset_10',
    )

    def __init__(self):
        # 数据绑定（与 TF 策略保持一致的 data_name 语义）
        try:
            self.d = self.getdatabyname(self.p.data_name)
        except Exception:
            self.d = self.datas[0]

        # 指标
        self.z = ZScore(self.d.close, period=self.p.p_lookback)
        self.atr = bt.ind.ATR(self.d, period=self.p.p_atr_period)
        self.atr_pct = self.atr / self.d.close
        self.atr_pct_q = RollingQuantile(
            self.atr_pct, period=self.p.p_atr_pctl_window, quantile=self.p.p_atr_pctl_enter
        )

        # 订单/持仓状态
        self._main_order = None
        self._sl_order = None
        self._sl_price = None
        self._entry_bar = None
        self._entry_price = None

        # 只按必要窗口限制起算；分位数/ ZScore 自己做短样本兜底
        self.addminperiod(max(int(self.p.p_lookback), int(self.p.p_atr_period), 5))



    # --- 工具：计算年化 ATR% ---
    def _atr_ann_pct(self) -> float:
        c = float(self.d.close[0]); a = float(self.atr[0])
        if not (np.isfinite(c) and c > 0 and np.isfinite(a) and a > 0):
            return np.nan
        return (a / c) * np.sqrt(252.0)

    # --- 工具：目标手数（含最小 1 手补丁 & 距离权重），按方向带符号 ---
    def _target_size(self, direction: int, z_val: float) -> int:
        ann_atr_pct = self._atr_ann_pct()
        if not (np.isfinite(ann_atr_pct) and ann_atr_pct > 1e-8):
            return 0
        base_w = min(self.p.p_target_vol_ann / ann_atr_pct, self.p.p_pos_cap)
        dist_w = min(1.0, abs(z_val) / max(1e-12, float(self.p.p_w_z_cap))) ** float(self.p.p_w_power)
        w = max(0.0, min(1.0, base_w * dist_w))
        if w <= 0:
            return 0
        close = float(self.d.close[0])
        raw_units = (self.broker.get_value() * w) / max(1e-12, close)
        # 最小 1 手补丁
        if w >= float(self.p.p_min_w_for_1) and abs(raw_units) < 1.0:
            raw_units = 1.0
        return int(direction * max(0.0, raw_units))

    # --- 主循环 ---
    def next(self):
        # 等待挂单完成
        if self._main_order and self._main_order.status in (bt.Order.Submitted, bt.Order.Accepted):
            return

        pos = int(self.getposition(self.d).size)
        z_now = float(self.z.z[0]) if np.isfinite(self.z.z[0]) else np.nan
        atrp = float(self.atr_pct[0]) if np.isfinite(self.atr_pct[0]) else np.nan
        qthr = float(self.atr_pct_q[0]) if np.isfinite(self.atr_pct_q[0]) else np.nan
        allow_enter = np.isfinite(atrp) and np.isfinite(qthr) and (atrp <= qthr)

        # ===== 先处理出场 =====
        if pos != 0:
            # 时间止损
            if self._entry_bar is not None:
                held = len(self) - self._entry_bar
                if self.p.p_max_hold_days > 0 and held >= int(self.p.p_max_hold_days):
                    self._close_position(reason=f"time({held}>= {self.p.p_max_hold_days})")
                    return
            # Z 回归出场：|z| <= exit_z
            if np.isfinite(z_now) and abs(z_now) <= float(self.p.p_exit_z):
                self._close_position(reason=f"z_exit(|z|={abs(z_now):.2f}<= {self.p.p_exit_z})")
                return

        # ===== 再考虑开仓（同根不反手） =====
        if pos == 0 and allow_enter and np.isfinite(z_now):
            direction = 0
            if z_now <= -float(self.p.p_entry_z):
                direction = +1
            elif z_now >= float(self.p.p_entry_z):
                direction = -1

            if direction != 0:
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

    # --- 平仓与止损管理 ---
    def notify_order(self, order):
        if order.data != self.d:
            return
        if order.status in (order.Submitted, order.Accepted):
            return

        if order.status == order.Completed:
            if order.isbuy() or order.issell():
                # 如果是开仓成交（无持仓→有持仓）
                pos = int(self.getposition(self.d).size)
                if pos != 0 and self._entry_bar is None:
                    self._entry_bar = len(self)
                    self._entry_price = float(order.executed.price)
                    # 设置静态 ATR 止损
                    a = float(self.atr[0])
                    if np.isfinite(a) and a > 0:
                        if pos > 0:
                            self._sl_price = self._entry_price - float(self.p.p_stop_mult) * a
                            self._sl_order = self.sell(data=self.d, exectype=bt.Order.Stop,
                                                       price=self._sl_price, size=pos)
                        else:
                            self._sl_price = self._entry_price + float(self.p.p_stop_mult) * a
                            self._sl_order = self.buy(data=self.d, exectype=bt.Order.Stop,
                                                      price=self._sl_price, size=abs(pos))
                        self._log(f"SL set @{self._sl_price:.4f}")
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

    # 平仓助手：取消止损→市价平仓
    def _close_position(self, reason: str = ""):
        if self._sl_order:
            try:
                self.cancel(self._sl_order)
            except Exception:
                pass
            self._sl_order = None
        self._main_order = self.close(data=self.d)
        self._log(f"EXIT | {reason}")
        self._entry_bar = None
        self._entry_price = None
        self._sl_price = None

    def _log(self, msg):
        if self.p.p_debug:
            dt = self.d.datetime.date(0)
            name = getattr(self.d, "_name", self.p.data_name)
            print(f"[{dt}] {name} | {msg}")
