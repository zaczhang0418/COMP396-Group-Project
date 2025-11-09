# -*- coding: utf-8 -*-
# strategies/combo_tf01_mr10_garch07_v1.py
# Portfolio combiner: TF on series_1, MR on series_10, GARCH-switch TF on series_7
import math, json
from pathlib import Path
from collections import deque
import backtrader as bt
import numpy as np

# ---------------- utils ----------------
def _safe_float(x, d=0.0):
    try: return float(x)
    except Exception: return d

def _latest_meta_params(root: Path) -> dict:
    if not root.exists(): return {}
    metas = sorted(root.rglob("meta.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for m in metas:
        try:
            meta = json.loads(m.read_text(encoding="utf-8"))
            params = dict(meta.get("params", {}))
            if params: return params
        except Exception: pass
    return {}

def _load_best_then_meta(best_path: Path, meta_root: Path) -> dict:
    if best_path.exists():
        try: return json.loads(best_path.read_text(encoding="utf-8"))
        except Exception: pass
    return _latest_meta_params(meta_root)

# 目标波动 -> 目标权重（按年化波动缩放，限制在 [-pos_cap, pos_cap]）
def _vol_target_pct(vol_target_ann, sigma_ann, pos_cap, ann_factor=252.0):
    if sigma_ann is None or not np.isfinite(sigma_ann) or sigma_ann <= 0:
        return 0.0
    v_d = float(vol_target_ann) / math.sqrt(float(ann_factor))
    s_d = float(sigma_ann)      / math.sqrt(float(ann_factor))
    raw = v_d / max(s_d, 1e-10)
    return max(-pos_cap, min(pos_cap, raw))

# ---------------- strategy ----------------
class ComboTF01MR10Garch07V1(bt.Strategy):
    params = dict(
        # 资金权重（内部会归一化）
        w_tf=1/3, w_mr=1/3, w_ga=1-2/3,

        # 各腿年化目标波动 & 持仓上限
        tf_target_vol_ann=0.18, mr_target_vol_ann=0.18, ga_target_vol_ann=0.20,
        tf_pos_cap=1.0,         mr_pos_cap=1.0,         ga_pos_cap=1.0,

        # ---- TF（EMA 多头即可，组合层不加 Hurst 门槛）----
        tf_ema_short=12, tf_ema_long=60,
        tf_atr_period=14, tf_stop_multiplier=2.0, tf_min_w_for_1=0.02,

        # ---- MR（z 阈值入/出）----
        mr_lookback=40, mr_entry_z=0.8, mr_exit_z=0.2,
        mr_atr_period=14, mr_stop_mult=2.0, mr_min_w_for_1=0.02,

        # ---- GARCH（分位分档×EMA方向）----
        ga_sigma_q_low=0.35, ga_sigma_q_high=0.80,
        ga_mult_mid=0.9, ga_mult_high=0.4,
        ga_garch_alpha=0.08, ga_garch_beta=0.90, ga_garch_init_lookback=60,
        ga_sigma_q_lookback=252, ga_ann_factor=252,
        ga_ema_short=12, ga_ema_long=60,
        ga_atr_period=14, ga_stop_multiplier=2.0, ga_min_w_for_1=0.02, ga_reenter_cooldown=1,

        # 自动加载最佳参数
        autoload_best=True,
    )

    def __init__(self):
        # 绑定数据（data_loader 命名）
        names = [d._name for d in self.datas]
        need = {"series_1", "series_10", "series_7"}
        miss = sorted(list(need - set(names)))
        if miss:
            raise ValueError(f"[Combo] missing feeds: {miss}; available={names}")
        self.d_tf = self.getdatabyname("series_1")
        self.d_mr = self.getdatabyname("series_10")
        self.d_ga = self.getdatabyname("series_7")

        # 自动读取最优参数（best -> meta）
        if bool(self.p.autoload_best):
            proj = Path(__file__).resolve().parents[1]
            tf_best = proj/"output/asset01/tf_core4_v1/best_params.json"
            tf_meta = proj/"output/asset01/tf_core4_v1/v1_best_core4"
            mr_best = proj/"output/asset10/grid_core4_v1/best_params.json"
            mr_meta = proj/"output/asset10/grid_core4_v1/v1_best_core4"
            ga_best = proj/"output/asset07/garch_core4_v1/best_params.json"
            ga_meta = proj/"output/asset07/garch_core4_v1/v1_best_core4"

            tfp = _load_best_then_meta(tf_best, tf_meta)
            mrp = _load_best_then_meta(mr_best, mr_meta)
            gap = _load_best_then_meta(ga_best, ga_meta)

            # 别名兼容
            if "p_stop_mult" in mrp and "p_stop_multiplier" not in mrp:
                mrp["p_stop_multiplier"] = mrp["p_stop_mult"]
            if "p_stop_mult" in gap and "p_stop_multiplier" not in gap:
                gap["p_stop_multiplier"] = gap["p_stop_mult"]

            # 应用 TF
            self.p.tf_ema_short       = _safe_float(tfp.get("p_ema_short", self.p.tf_ema_short))
            self.p.tf_ema_long        = _safe_float(tfp.get("p_ema_long",  self.p.tf_ema_long))
            self.p.tf_stop_multiplier = _safe_float(tfp.get("p_stop_multiplier", self.p.tf_stop_multiplier))
            # 应用 MR
            self.p.mr_lookback  = int(_safe_float(mrp.get("p_lookback", self.p.mr_lookback)))
            self.p.mr_entry_z   = _safe_float(mrp.get("p_entry_z", self.p.mr_entry_z))
            self.p.mr_exit_z    = _safe_float(mrp.get("p_exit_z",  self.p.mr_exit_z))
            self.p.mr_stop_mult = _safe_float(mrp.get("p_stop_multiplier", self.p.mr_stop_mult))
            # 应用 GARCH
            self.p.ga_sigma_q_low   = _safe_float(gap.get("p_sigma_q_low",  self.p.ga_sigma_q_low))
            self.p.ga_sigma_q_high  = _safe_float(gap.get("p_sigma_q_high", self.p.ga_sigma_q_high))
            self.p.ga_mult_mid      = _safe_float(gap.get("p_mult_mid",     self.p.ga_mult_mid))
            self.p.ga_mult_high     = _safe_float(gap.get("p_mult_high",    self.p.ga_mult_high))
            self.p.ga_stop_multiplier = _safe_float(gap.get("p_stop_multiplier", self.p.ga_stop_multiplier))

        # 权重归一化
        s = float(self.p.w_tf + self.p.w_mr + self.p.w_ga)
        self.p.w_tf, self.p.w_mr, self.p.w_ga = (
            (1/3,1/3,1-2/3) if s <= 0 else (self.p.w_tf/s, self.p.w_mr/s, self.p.w_ga/s)
        )

        # 指标/缓存
        # TF
        self.tf_ema_s = bt.ind.EMA(self.d_tf.close, period=int(self.p.tf_ema_short))
        self.tf_ema_l = bt.ind.EMA(self.d_tf.close, period=int(self.p.tf_ema_long))
        self.tf_atr   = bt.ind.ATR(self.d_tf, period=int(self.p.tf_atr_period))
        self._tf_sl = None
        # MR
        lb = max(10, int(self.p.mr_lookback))
        self.mr_ma  = bt.ind.SMA(self.d_mr.close, period=lb)
        self.mr_std = bt.ind.StdDev(self.d_mr.close, period=lb)
        self.mr_atr = bt.ind.ATR(self.d_mr, period=int(self.p.mr_atr_period))
        self._mr_sl = None
        # GARCH
        self.ga_ema_s = bt.ind.EMA(self.d_ga.close, period=int(self.p.ga_ema_short))
        self.ga_ema_l = bt.ind.EMA(self.d_ga.close, period=int(self.p.ga_ema_long))
        self.ga_atr   = bt.ind.ATR(self.d_ga, period=int(self.p.ga_atr_period))
        self._ga_sigma2=None; self._ga_omega=None; self._ga_init_done=False
        self._ga_last_ret=0.0; self._ga_init_buf=[]; self._ga_sigma_hist=deque(maxlen=int(self.p.ga_sigma_q_lookback))
        self._ga_sl=None; self._ga_cooldown=0

        needp = max(int(self.p.tf_ema_long), int(self.p.mr_lookback),
                    int(self.p.ga_ema_long), int(self.p.ga_sigma_q_lookback),
                    int(self.p.ga_garch_init_lookback)) + 1
        self.addminperiod(needp)

    # ---- GARCH helpers ----
    def _sigma_ann_ga(self):
        if not self._ga_init_done or self._ga_sigma2 is None: return None
        daily = math.sqrt(max(self._ga_sigma2, 1e-16))
        return daily * math.sqrt(float(self.p.ga_ann_factor))

    def _update_garch(self, r_t):
        a=float(self.p.ga_garch_alpha); b=float(self.p.ga_garch_beta)
        if not self._ga_init_done:
            self._ga_init_buf.append(r_t)
            if len(self._ga_init_buf) >= int(self.p.ga_garch_init_lookback):
                var_lr = np.var(np.asarray(self._ga_init_buf), ddof=1) if len(self._ga_init_buf)>1 else r_t*r_t
                var_lr = max(var_lr, 1e-12)
                self._ga_omega = max(1e-6, 1.0-a-b) * var_lr
                self._ga_sigma2 = var_lr; self._ga_init_done = True
            return
        prev = max(self._ga_sigma2 if self._ga_sigma2 is not None else 1e-12, 1e-12)
        self._ga_sigma2 = self._ga_omega + a*(self._ga_last_ret**2) + b*prev
        self._ga_sigma2 = max(self._ga_sigma2, 1e-16)

    # ------------------- trading loop -------------------
    def next(self):
        # ===== TF (series_1): EMA 多头即可；sigma_ann 用 ATR/Close =====
        tf_pos = self.getposition(self.d_tf).size
        tf_close = float(self.d_tf.close[0])
        if not math.isfinite(tf_close) or tf_close <= 0: tf_close = 1.0
        tf_sigma_ann = (float(self.tf_atr[0]) / max(tf_close, 1e-12)) * math.sqrt(252.0) \
                        if not math.isnan(self.tf_atr[0]) else None
        tf_tgt = _vol_target_pct(self.p.tf_target_vol_ann*self.p.w_tf, tf_sigma_ann, self.p.tf_pos_cap)
        tf_up = (self.tf_ema_s[0] > self.tf_ema_l[0])

        if tf_pos == 0:
            if tf_up and abs(tf_tgt) >= float(self.p.tf_min_w_for_1):
                self.order_target_percent(self.d_tf, max(tf_tgt, float(self.p.tf_min_w_for_1)))
                if not math.isnan(self.tf_atr[0]):
                    self._tf_sl = tf_close - float(self.p.tf_stop_multiplier)*float(self.tf_atr[0])
        else:
            # ATR 追踪止损 + 再平衡
            if not math.isnan(self.tf_atr[0]):
                new_sl = tf_close - float(self.p.tf_stop_multiplier)*float(self.tf_atr[0])
                if self._tf_sl is None or new_sl > self._tf_sl: self._tf_sl = new_sl
                if tf_close <= self._tf_sl:
                    self.order_target_percent(self.d_tf, 0.0); self._tf_sl=None
            cur_val = self.broker.get_value(); cur_pct = (tf_pos*tf_close)/max(cur_val,1e-9)
            if abs(tf_tgt-cur_pct) >= max(float(self.p.tf_min_w_for_1),0.02):
                self.order_target_percent(self.d_tf, tf_tgt)
            if not tf_up:
                self.order_target_percent(self.d_tf, 0.0); self._tf_sl=None

        # ===== MR (series_10): sigma_ann 用 ATR/Close；z≤-entry 入，z≥-exit 出 =====
        mr_pos = self.getposition(self.d_mr).size
        mr_close = float(self.d_mr.close[0])
        if not math.isfinite(mr_close) or mr_close <= 0: mr_close = 1.0
        mr_mu = float(self.mr_ma[0]) if not math.isnan(self.mr_ma[0]) else mr_close
        mr_sd = float(self.mr_std[0]) if not math.isnan(self.mr_std[0]) and self.mr_std[0] > 1e-12 else 1.0
        z = (mr_close - mr_mu)/mr_sd
        mr_sigma_ann = (float(self.mr_atr[0]) / max(mr_close, 1e-12)) * math.sqrt(252.0) \
                        if not math.isnan(self.mr_atr[0]) else None
        mr_tgt = _vol_target_pct(self.p.mr_target_vol_ann*self.p.w_mr, mr_sigma_ann, self.p.mr_pos_cap)

        if mr_pos == 0:
            if z <= -float(self.p.mr_entry_z) and abs(mr_tgt) >= float(self.p.mr_min_w_for_1):
                self.order_target_percent(self.d_mr, max(mr_tgt, float(self.p.mr_min_w_for_1)))
                if not math.isnan(self.mr_atr[0]):
                    self._mr_sl = mr_close - float(self.p.mr_stop_mult)*float(self.mr_atr[0])
        else:
            if getattr(self, "_mr_sl", None) is not None and not math.isnan(self.mr_atr[0]) and mr_close <= self._mr_sl:
                self.order_target_percent(self.d_mr, 0.0); self._mr_sl=None
            elif z >= -float(self.p.mr_exit_z):
                self.order_target_percent(self.d_mr, 0.0); self._mr_sl=None
            else:
                if not math.isnan(self.mr_atr[0]):
                    new_sl = mr_close - float(self.p.mr_stop_mult)*float(self.mr_atr[0])
                    if self._mr_sl is None or new_sl > self._mr_sl: self._mr_sl = new_sl
                cur_val = self.broker.get_value(); cur_pct = (mr_pos*mr_close)/max(cur_val,1e-9)
                if abs(mr_tgt-cur_pct) >= max(float(self.p.mr_min_w_for_1),0.02):
                    self.order_target_percent(self.d_mr, mr_tgt)

        # ===== GARCH (series_7): EMA方向 + 分位分档倍率 × 目标波动 =====
        ga_pos = self.getposition(self.d_ga).size
        ga_close = float(self.d_ga.close[0])
        # 递推 GARCH
        ga_ret = 0.0
        if len(self.d_ga) >= 2:
            p0, p1 = float(self.d_ga.close[0]), float(self.d_ga.close[-1])
            if p1 > 0: ga_ret = math.log(p0/p1)
        self._update_garch(ga_ret)
        ga_sigma_ann = self._sigma_ann_ga()
        if ga_sigma_ann is not None and np.isfinite(ga_sigma_ann):
            self._ga_sigma_hist.append(float(ga_sigma_ann))

        ga_bull = self.ga_ema_s[0] > self.ga_ema_l[0]
        # regime 倍率
        if len(self._ga_sigma_hist) < max(20, int(self.p.ga_sigma_q_lookback)//4):
            mult = float(self.p.ga_mult_mid)
        else:
            arr = np.asarray(self._ga_sigma_hist, dtype=float)
            ql = np.quantile(arr, float(self.p.ga_sigma_q_low))
            qh = np.quantile(arr, float(self.p.ga_sigma_q_high))
            if ga_sigma_ann is not None and ga_sigma_ann <= ql:   mult = 1.0
            elif ga_sigma_ann is not None and ga_sigma_ann >= qh: mult = float(self.p.ga_mult_high)
            else:                                                 mult = float(self.p.ga_mult_mid)

        ga_base = _vol_target_pct(self.p.ga_target_vol_ann*self.p.w_ga, ga_sigma_ann, self.p.ga_pos_cap, self.p.ga_ann_factor)
        ga_tgt  = ga_base * mult

        if ga_pos == 0:
            if ga_bull and abs(ga_tgt) >= float(self.p.ga_min_w_for_1) and self._ga_cooldown==0:
                self.order_target_percent(self.d_ga, max(ga_tgt, float(self.p.ga_min_w_for_1)))
                if not math.isnan(self.ga_atr[0]):
                    self._ga_sl = ga_close - float(self.p.ga_stop_multiplier)*float(self.ga_atr[0])
                self._ga_cooldown = int(self.p.ga_reenter_cooldown)
        else:
            if getattr(self, "_ga_sl", None) is not None and not math.isnan(self.ga_atr[0]) and ga_close <= self._ga_sl:
                self.order_target_percent(self.d_ga, 0.0); self._ga_sl=None
            else:
                if not math.isnan(self.ga_atr[0]):
                    new_sl = ga_close - float(self.p.ga_stop_multiplier)*float(self.ga_atr[0])
                    if self._ga_sl is None or new_sl > self._ga_sl: self._ga_sl = new_sl
                cur_val = self.broker.get_value(); cur_pct = (ga_pos*ga_close)/max(cur_val,1e-9)
                if abs(ga_tgt-cur_pct) >= max(float(self.p.ga_min_w_for_1),0.02):
                    self.order_target_percent(self.d_ga, ga_tgt)

            # 若转为空头，平仓
            if not ga_bull:
                self.order_target_percent(self.d_ga, 0.0); self._ga_sl=None
        if self._ga_cooldown > 0: self._ga_cooldown -= 1
        self._ga_last_ret = ga_ret

# loader alias
Strategy = ComboTF01MR10Garch07V1
