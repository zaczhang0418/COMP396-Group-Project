# -*- coding: utf-8 -*-
"""Single-file submission strategy for blind-test deployment."""

from __future__ import annotations

import math

import backtrader as bt
import numpy as np


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _current_pct(strategy: bt.Strategy, data) -> float:
    close = float(data.close[0]) if np.isfinite(data.close[0]) else 0.0
    value = max(float(strategy.broker.get_value()), 1e-9)
    return float(strategy.getposition(data).size) * close / value


class RollingQuantile(bt.Indicator):
    lines = ("q",)
    params = dict(period=252, quantile=0.90, min_req=5)

    def __init__(self):
        self.addminperiod(1)

    def next(self):
        period = max(1, int(self.p.period))
        avail = len(self.data)
        win = min(avail, period)
        min_req = int(self.p.min_req)
        if win < min_req:
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
        length = max(1, int(self.p.period))
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
        current = float(self.data[0]) if np.isfinite(self.data[0]) else np.nan
        mean = float(vals.mean())
        std = float(vals.std(ddof=0))
        self.lines.z[0] = float("nan") if (not np.isfinite(current)) or std <= 0 else (current - mean) / std


class RollingHurst(bt.Indicator):
    lines = ("hurst",)
    params = dict(period=126)

    def __init__(self):
        self.addminperiod(self.p.period)

    def next(self):
        window = self.data.get(size=int(self.p.period))
        if window is None or len(window) < int(self.p.period):
            self.lines.hurst[0] = float("nan")
            return
        x = np.log(np.asarray(list(window), dtype=float))
        if not np.isfinite(x).all():
            self.lines.hurst[0] = float("nan")
            return
        dev = x - x.mean()
        cum = np.cumsum(dev)
        r_val = float(np.max(cum) - np.min(cum))
        s_val = float(np.std(x))
        if s_val <= 0 or r_val <= 0:
            self.lines.hurst[0] = 0.5
            return
        hurst = np.log(r_val / s_val) / np.log(float(self.p.period))
        self.lines.hurst[0] = float(np.clip(hurst, 0.0, 1.0))


class TeamStrategy(bt.Strategy):
    params = dict(
        tf_data_name="series_1",
        mr09_data_name="series_9",
        w_tf=0.65,
        w_mr09=0.35,
        gross_cap=1.00,
        rebalance_tol=0.015,
        dynamic_alloc_enabled=True,
        dynamic_alloc_strength=0.35,
        perf_alloc_enabled=True,
        budget_floor_tf=0.35,
        budget_floor_mr09=0.20,
        budget_cap_tf=0.80,
        budget_cap_mr09=0.65,
        perf_alpha=0.25,
        perf_scale=12.0,
        perf_floor_mult=0.70,
        perf_cap_mult=1.40,
        perf_freeze_mult=0.85,
        loss_freeze_after=3,
        loss_freeze_bars=12,
        tf_weight_floor=0.40,
        tf_weight_cap=0.82,
        mr_weight_floor=0.18,
        mr_weight_cap=0.60,
        tf_score_norm=1.50,
        mr_score_norm=1.50,
        tf_reentry_on_trend=True,
        tf_entry_score_floor=0.15,
        tf_hot_enabled=True,
        tf_hot_lookback=10,
        tf_hot_entry_floor=0.15,
        tf_hot_hold_floor=0.60,
        tf_hot_gap_atr=0.80,
        tf_hot_jump1_atr=0.70,
        tf_hot_jump3_atr=1.10,
        tf_hot_blend=0.10,
        mr09_vol_relax_mult=1.05,
        mr09_entry_mode="touch",
        mr09_cooldown_bars=1,
        tf_ema_short=18,
        tf_ema_long=50,
        tf_hurst_min_soft=0.55,
        tf_stop_multiplier=2.0,
        tf_hurst_period=126,
        tf_hurst_power=1.0,
        tf_hurst_ema=10,
        tf_atr_period=14,
        tf_target_vol_ann=0.18,
        tf_pos_cap=1.0,
        tf_circuit_breaker_window=126,
        tf_circuit_breaker_pct=0.9999,
        tf_min_w_for_1=0.03,
        tf_cooldown_bars=1,
        mr09_lookback=20,
        mr09_entry_z=2.25,
        mr09_exit_z=0.75,
        mr09_stop_mult=2.0,
        mr09_max_hold_days=7,
        mr09_atr_period=14,
        mr09_atr_pctl_window=252,
        mr09_atr_pctl_enter=0.90,
        mr09_target_vol_ann=0.18,
        mr09_pos_cap=1.0,
        mr09_w_z_cap=3.0,
        mr09_w_power=1.0,
        mr09_min_w_for_1=0.12,
    )

    def __init__(self):
        lookup = {data._name: data for data in self.datas}
        needed = {self.p.tf_data_name, self.p.mr09_data_name}
        missing = sorted(item for item in needed if item not in lookup)
        if missing:
            raise ValueError(f"Missing feeds for TeamStrategy: {missing}")

        self.d_tf = lookup[self.p.tf_data_name]
        self.d_mr09 = lookup[self.p.mr09_data_name]

        total = max(1e-12, max(0.0, float(self.p.w_tf)) + max(0.0, float(self.p.w_mr09)))
        self._base_weights = {
            "tf": max(0.0, float(self.p.w_tf)) / total,
            "mr09": max(0.0, float(self.p.w_mr09)) / total,
        }
        self._active_weights = dict(self._base_weights)

        self.tf_ema_s = bt.ind.EMA(self.d_tf.close, period=int(self.p.tf_ema_short))
        self.tf_ema_l = bt.ind.EMA(self.d_tf.close, period=int(self.p.tf_ema_long))
        self.tf_atr = bt.ind.ATR(self.d_tf, period=int(self.p.tf_atr_period))
        self.tf_hurst = RollingHurst(self.d_tf.close, period=int(self.p.tf_hurst_period))
        self.tf_atr_q = RollingQuantile(
            self.tf_atr,
            period=int(self.p.tf_circuit_breaker_window),
            quantile=float(self.p.tf_circuit_breaker_pct),
            min_req=int(self.p.tf_circuit_breaker_window),
        )
        self.tf_hot_sma = bt.ind.SMA(self.d_tf.close, period=int(self.p.tf_hot_lookback))
        self._tf_weight_state = 0.01
        self._tf_weight_alpha = (
            2.0 / (float(self.p.tf_hurst_ema) + 1.0) if float(self.p.tf_hurst_ema) > 0 else 1.0
        )
        self._tf_stop = None
        self._tf_cooldown = 0

        atr09 = bt.ind.ATR(self.d_mr09, period=int(self.p.mr09_atr_period))
        atr_pct09 = atr09 / self.d_mr09.close
        self._mr09 = {
            "z": ZScore(self.d_mr09.close, period=int(self.p.mr09_lookback)),
            "atr": atr09,
            "atr_pct": atr_pct09,
            "atr_pct_q": RollingQuantile(
                atr_pct09,
                period=int(self.p.mr09_atr_pctl_window),
                quantile=float(self.p.mr09_atr_pctl_enter),
                min_req=max(5, int(self.p.mr09_atr_pctl_window * 0.2)),
            ),
            "stop": None,
            "entry_bar": None,
            "entry_price": None,
            "cooldown": 0,
        }

        self._leg_by_data = {
            self.d_tf: "tf",
            self.d_mr09: "mr09",
        }
        self._alloc_state = {
            "tf": {"perf_ema": 0.0, "loss_streak": 0, "freeze": 0},
            "mr09": {"perf_ema": 0.0, "loss_streak": 0, "freeze": 0},
        }

        self.addminperiod(
            max(
                int(self.p.tf_ema_long),
                int(self.p.tf_hurst_period),
                int(self.p.tf_circuit_breaker_window),
                int(self.p.tf_hot_lookback),
                int(self.p.mr09_lookback),
                int(self.p.mr09_atr_pctl_window),
            )
            + 3
        )

    def _perf_multiplier(self, key: str) -> float:
        state = self._alloc_state[key]
        raw = 1.0 + float(self.p.perf_scale) * state["perf_ema"]
        if state["freeze"] > 0:
            raw = min(raw, float(self.p.perf_freeze_mult))
        return _clamp(raw, float(self.p.perf_floor_mult), float(self.p.perf_cap_mult))

    def _dynamic_budget_weights(self) -> dict[str, float]:
        if not bool(self.p.perf_alloc_enabled):
            return dict(self._base_weights)

        floors = {
            "tf": max(0.0, float(self.p.budget_floor_tf)),
            "mr09": max(0.0, float(self.p.budget_floor_mr09)),
        }
        caps = {
            "tf": max(floors["tf"], float(self.p.budget_cap_tf)),
            "mr09": max(floors["mr09"], float(self.p.budget_cap_mr09)),
        }
        floor_sum = sum(floors.values())
        if floor_sum >= 1.0:
            return {key: value / floor_sum for key, value in floors.items()}

        leftover = 1.0 - floor_sum
        raw = {
            key: max(1e-6, self._base_weights[key] * self._perf_multiplier(key))
            for key in self._base_weights
        }

        budget = dict(floors)
        available = list(raw.keys())
        remaining = leftover

        while available and remaining > 1e-9:
            raw_sum = sum(raw[key] for key in available)
            if raw_sum <= 0:
                raw_sum = float(len(available))
                raw = {key: 1.0 for key in available}

            consumed = 0.0
            still_open = []
            for key in available:
                share = remaining * raw[key] / raw_sum
                room = max(0.0, caps[key] - budget[key])
                add = min(share, room)
                budget[key] += add
                consumed += add
                if budget[key] < caps[key] - 1e-9:
                    still_open.append(key)

            if consumed <= 1e-9:
                break
            remaining -= consumed
            available = still_open

        total = sum(budget.values())
        if total > 0:
            budget = {key: value / total for key, value in budget.items()}
        return budget

    def _tf_score(self) -> float:
        atr = float(self.tf_atr[0]) if np.isfinite(self.tf_atr[0]) else np.nan
        if not np.isfinite(atr) or atr <= 0:
            return 0.0
        spread = float(self.tf_ema_s[0] - self.tf_ema_l[0])
        trend_term = _clamp(spread / atr, -1.0, 2.0)
        hurst = float(self.tf_hurst[0]) if np.isfinite(self.tf_hurst[0]) else float(self.p.tf_hurst_min_soft)
        hurst_term = _clamp(
            (hurst - float(self.p.tf_hurst_min_soft))
            / max(1e-9, 1.0 - float(self.p.tf_hurst_min_soft)),
            -0.25,
            1.5,
        )
        return 0.7 * trend_term + 0.5 * hurst_term

    def _tf_hot_score(self) -> float:
        if not bool(self.p.tf_hot_enabled):
            return 1.0

        close = float(self.d_tf.close[0]) if np.isfinite(self.d_tf.close[0]) else np.nan
        prev1 = (
            float(self.d_tf.close[-1])
            if len(self) > 1 and np.isfinite(self.d_tf.close[-1])
            else np.nan
        )
        prev3 = (
            float(self.d_tf.close[-3])
            if len(self) > 3 and np.isfinite(self.d_tf.close[-3])
            else np.nan
        )
        atr = float(self.tf_atr[0]) if np.isfinite(self.tf_atr[0]) else np.nan
        sma = float(self.tf_hot_sma[0]) if np.isfinite(self.tf_hot_sma[0]) else np.nan

        if not (
            np.isfinite(close)
            and np.isfinite(prev1)
            and np.isfinite(prev3)
            and np.isfinite(atr)
            and atr > 0
            and np.isfinite(sma)
        ):
            return 0.0

        gap = max(0.0, close - sma) / atr
        jump1 = max(0.0, close - prev1) / atr
        jump3 = max(0.0, close - prev3) / max(1e-9, atr * math.sqrt(3.0))

        score_gap = _clamp(gap / max(1e-9, float(self.p.tf_hot_gap_atr)), 0.0, 1.4)
        score_jump1 = _clamp(jump1 / max(1e-9, float(self.p.tf_hot_jump1_atr)), 0.0, 1.4)
        score_jump3 = _clamp(jump3 / max(1e-9, float(self.p.tf_hot_jump3_atr)), 0.0, 1.4)

        raw = 0.35 * score_gap + 0.30 * score_jump1 + 0.35 * score_jump3
        if close <= sma:
            raw *= 0.25
        return _clamp(raw, 0.0, 1.0)

    def _tf_signal_strength(self) -> float:
        if self._alloc_state["tf"]["freeze"] > 0 and int(self.getposition(self.d_tf).size) == 0:
            return 0.0

        base = _clamp(
            max(0.0, self._tf_score()) / max(1e-9, float(self.p.tf_score_norm)),
            0.0,
            1.0,
        )
        if not bool(self.p.tf_hot_enabled):
            return base

        hot = self._tf_hot_score()
        if int(self.getposition(self.d_tf).size) != 0:
            hot = max(hot, float(self.p.tf_hot_hold_floor))
        blend = _clamp(float(self.p.tf_hot_blend), 0.0, 1.0)
        return _clamp((1.0 - blend) * base + blend * hot, 0.0, 1.0)

    def _tf_target_pct(self, budget_weight: float) -> float:
        h_val = float(self.tf_hurst[0]) if np.isfinite(self.tf_hurst[0]) else None
        hmin = float(self.p.tf_hurst_min_soft)
        if h_val is None or h_val <= hmin:
            raw_state = 0.01
        else:
            raw_state = (h_val - hmin) / max(1e-9, 1.0 - hmin)
            raw_state = _clamp(raw_state, 0.01, 1.0)
        raw_state = raw_state ** float(self.p.tf_hurst_power)
        self._tf_weight_state = (
            self._tf_weight_alpha * raw_state
            + (1.0 - self._tf_weight_alpha) * self._tf_weight_state
        )

        close = float(self.d_tf.close[0])
        atr = float(self.tf_atr[0])
        if not (np.isfinite(close) and close > 0 and np.isfinite(atr) and atr > 0):
            return 0.0

        ann_atr_pct = (atr / close) * math.sqrt(252.0)
        if not (np.isfinite(ann_atr_pct) and ann_atr_pct > 1e-8):
            return 0.0

        base = min(float(self.p.tf_target_vol_ann) / ann_atr_pct, float(self.p.tf_pos_cap))
        target = base * self._tf_weight_state * budget_weight
        if target < float(self.p.tf_min_w_for_1) and self._tf_weight_state >= float(self.p.tf_min_w_for_1):
            return float(self.p.tf_min_w_for_1)
        return max(0.0, float(target))

    def _mr09_target_pct(self, z_val: float, direction: int, budget_weight: float) -> float:
        close = float(self.d_mr09.close[0]) if np.isfinite(self.d_mr09.close[0]) else np.nan
        atr = float(self._mr09["atr"][0]) if np.isfinite(self._mr09["atr"][0]) else np.nan
        if not (np.isfinite(close) and close > 0 and np.isfinite(atr) and atr > 0):
            return 0.0

        ann_atr_pct = (atr / close) * math.sqrt(252.0)
        if not (np.isfinite(ann_atr_pct) and ann_atr_pct > 1e-8):
            return 0.0

        base = min(float(self.p.mr09_target_vol_ann) / ann_atr_pct, float(self.p.mr09_pos_cap))
        dist = min(1.0, abs(z_val) / max(1e-12, float(self.p.mr09_w_z_cap)))
        dist = dist ** float(self.p.mr09_w_power)
        target = base * dist * budget_weight
        if target < float(self.p.mr09_min_w_for_1) and dist > 0:
            target = float(self.p.mr09_min_w_for_1)
        return float(direction) * max(0.0, float(target))

    def _mr09_signal_strength(self) -> float:
        if self._alloc_state["mr09"]["freeze"] > 0 and int(self.getposition(self.d_mr09).size) == 0:
            return 0.0

        z_now = float(self._mr09["z"].z[0]) if np.isfinite(self._mr09["z"].z[0]) else np.nan
        if not np.isfinite(z_now):
            return 0.0

        atr_pct = float(self._mr09["atr_pct"][0]) if np.isfinite(self._mr09["atr_pct"][0]) else np.nan
        qthr = float(self._mr09["atr_pct_q"][0]) if np.isfinite(self._mr09["atr_pct_q"][0]) else np.nan
        holding = int(self.getposition(self.d_mr09).size) != 0
        allow_enter = (
            np.isfinite(atr_pct)
            and np.isfinite(qthr)
            and atr_pct <= qthr * float(self.p.mr09_vol_relax_mult)
        )
        if not allow_enter and not holding:
            return 0.0

        entry_z = max(1e-9, float(self.p.mr09_entry_z))
        signal = abs(z_now) / entry_z
        if holding:
            signal += 0.2
        return _clamp(signal / max(1e-9, float(self.p.mr_score_norm)), 0.0, 1.0)

    def _compute_active_weights(self) -> dict[str, float]:
        perf_weights = self._dynamic_budget_weights()
        base_tf = float(perf_weights["tf"])
        base_mr = float(perf_weights["mr09"])
        if not bool(self.p.dynamic_alloc_enabled):
            return {"tf": base_tf, "mr09": base_mr}

        tf_strength = self._tf_signal_strength()
        mr_strength = self._mr09_signal_strength()
        total_strength = tf_strength + mr_strength
        if total_strength <= 1e-9:
            return {"tf": base_tf, "mr09": base_mr}

        score_tf = tf_strength / total_strength
        strength = _clamp(float(self.p.dynamic_alloc_strength), 0.0, 1.0)
        tf_weight = base_tf * (1.0 - strength) + score_tf * strength
        tf_weight = _clamp(tf_weight, float(self.p.tf_weight_floor), float(self.p.tf_weight_cap))
        mr_weight = 1.0 - tf_weight
        mr_weight = _clamp(mr_weight, float(self.p.mr_weight_floor), float(self.p.mr_weight_cap))
        tf_weight = 1.0 - mr_weight
        return {"tf": tf_weight, "mr09": mr_weight}

    def _desired_tf_pct(self, budget_weight: float) -> float:
        pos = int(self.getposition(self.d_tf).size)
        atr_q_val = float(self.tf_atr_q[0]) if np.isfinite(self.tf_atr_q[0]) else float("inf")
        circuit_on = float(self.tf_atr[0]) > atr_q_val
        trend_up = self.tf_ema_s[0] > self.tf_ema_l[0]
        bear_cross = self.tf_ema_s[0] < self.tf_ema_l[0] and self.tf_ema_s[-1] >= self.tf_ema_l[-1]
        score = self._tf_score()
        hot_score = self._tf_hot_score()
        hot_ok = (not bool(self.p.tf_hot_enabled)) or hot_score >= float(self.p.tf_hot_entry_floor)
        target_pct = self._tf_target_pct(budget_weight)

        if pos == 0:
            wants_entry = (
                (not circuit_on)
                and self._tf_cooldown == 0
                and self._alloc_state["tf"]["freeze"] == 0
                and hot_ok
                and (
                    (trend_up and bool(self.p.tf_reentry_on_trend))
                    or (
                        self.tf_ema_s[0] > self.tf_ema_l[0]
                        and self.tf_ema_s[-1] <= self.tf_ema_l[-1]
                    )
                )
                and score >= float(self.p.tf_entry_score_floor)
            )
            if wants_entry:
                close = float(self.d_tf.close[0])
                atr = float(self.tf_atr[0])
                if np.isfinite(close) and np.isfinite(atr):
                    self._tf_stop = close - float(self.p.tf_stop_multiplier) * atr
                return target_pct
            return 0.0

        close = float(self.d_tf.close[0]) if np.isfinite(self.d_tf.close[0]) else np.nan
        if np.isfinite(close) and np.isfinite(self.tf_atr[0]):
            new_stop = close - float(self.p.tf_stop_multiplier) * float(self.tf_atr[0])
            if self._tf_stop is None or new_stop > self._tf_stop:
                self._tf_stop = new_stop

        if bear_cross or (self._tf_stop is not None and np.isfinite(close) and close <= self._tf_stop):
            self._tf_stop = None
            self._tf_cooldown = max(self._tf_cooldown, int(self.p.tf_cooldown_bars))
            return 0.0

        return 0.0 if circuit_on else target_pct

    def _mr09_exit_signal(self, z_now: float) -> bool:
        pos = int(self.getposition(self.d_mr09).size)
        if pos == 0:
            return False
        if self._mr09["entry_bar"] is not None:
            held = len(self) - self._mr09["entry_bar"]
            if int(self.p.mr09_max_hold_days) > 0 and held >= int(self.p.mr09_max_hold_days):
                return True
        if np.isfinite(z_now) and abs(z_now) <= float(self.p.mr09_exit_z):
            return True

        stop = self._mr09["stop"]
        close = float(self.d_mr09.close[0]) if np.isfinite(self.d_mr09.close[0]) else np.nan
        if stop is not None and np.isfinite(close):
            if pos > 0 and close <= stop:
                return True
            if pos < 0 and close >= stop:
                return True
        return False

    def _desired_mr09_pct(self, budget_weight: float) -> float:
        pos = int(self.getposition(self.d_mr09).size)
        z_now = float(self._mr09["z"].z[0]) if np.isfinite(self._mr09["z"].z[0]) else np.nan
        z_prev = (
            float(self._mr09["z"].z[-1])
            if len(self) > 1 and np.isfinite(self._mr09["z"].z[-1])
            else np.nan
        )
        atr_pct = float(self._mr09["atr_pct"][0]) if np.isfinite(self._mr09["atr_pct"][0]) else np.nan
        qthr = float(self._mr09["atr_pct_q"][0]) if np.isfinite(self._mr09["atr_pct_q"][0]) else np.nan
        allow_enter = (
            np.isfinite(atr_pct)
            and np.isfinite(qthr)
            and atr_pct <= qthr * float(self.p.mr09_vol_relax_mult)
        )

        if pos != 0:
            if self._mr09_exit_signal(z_now):
                self._mr09["stop"] = None
                self._mr09["entry_bar"] = None
                self._mr09["entry_price"] = None
                self._mr09["cooldown"] = max(self._mr09["cooldown"], int(self.p.mr09_cooldown_bars))
                return 0.0
            return _current_pct(self, self.d_mr09)

        if (
            self._mr09["cooldown"] > 0
            or self._alloc_state["mr09"]["freeze"] > 0
            or not allow_enter
            or not np.isfinite(z_now)
        ):
            return 0.0

        direction = 0
        if z_now <= -float(self.p.mr09_entry_z):
            direction = 1
        elif z_now >= float(self.p.mr09_entry_z):
            direction = -1
        if direction == 0:
            return 0.0

        if str(self.p.mr09_entry_mode).lower() != "touch":
            if not np.isfinite(z_prev):
                return 0.0
            if direction > 0 and not (z_now > z_prev):
                return 0.0
            if direction < 0 and not (z_now < z_prev):
                return 0.0

        return self._mr09_target_pct(z_now, direction, budget_weight)

    def next(self):
        if self._tf_cooldown > 0:
            self._tf_cooldown -= 1
        if self._mr09["cooldown"] > 0:
            self._mr09["cooldown"] -= 1
        for state in self._alloc_state.values():
            if state["freeze"] > 0:
                state["freeze"] -= 1

        self._active_weights = self._compute_active_weights()
        desired = {
            "tf": self._desired_tf_pct(self._active_weights["tf"]),
            "mr09": self._desired_mr09_pct(self._active_weights["mr09"]),
        }

        gross = sum(abs(value) for value in desired.values())
        gross_cap = max(0.0, float(self.p.gross_cap))
        if gross_cap > 0 and gross > gross_cap:
            scale = gross_cap / gross
            desired = {key: value * scale for key, value in desired.items()}

        self._maybe_rebalance(self.d_tf, desired["tf"])
        self._maybe_rebalance(self.d_mr09, desired["mr09"])

    def _maybe_rebalance(self, data, target_pct: float):
        current_pct = _current_pct(self, data)
        if abs(target_pct - current_pct) >= float(self.p.rebalance_tol):
            self.order_target_percent(data=data, target=target_pct)

    def notify_order(self, order):
        if order.status in (order.Submitted, order.Accepted):
            return
        leg = self._leg_by_data.get(order.data)
        if leg is None:
            return

        if leg == "tf":
            if order.status in (order.Canceled, order.Margin, order.Rejected):
                return
            pos = int(self.getposition(order.data).size)
            if pos == 0:
                self._tf_stop = None
                self._tf_cooldown = max(self._tf_cooldown, int(self.p.tf_cooldown_bars))
            elif order.isbuy() and np.isfinite(self.tf_atr[0]):
                self._tf_stop = float(order.executed.price) - float(self.p.tf_stop_multiplier) * float(self.tf_atr[0])
            return

        if order.status in (order.Canceled, order.Margin, order.Rejected):
            return
        pos = int(self.getposition(order.data).size)
        if pos == 0:
            self._mr09["stop"] = None
            self._mr09["entry_bar"] = None
            self._mr09["entry_price"] = None
            self._mr09["cooldown"] = max(self._mr09["cooldown"], int(self.p.mr09_cooldown_bars))
            return

        if self._mr09["entry_bar"] is not None:
            return

        self._mr09["entry_bar"] = len(self)
        self._mr09["entry_price"] = float(order.executed.price)
        atr = float(self._mr09["atr"][0])
        if not (np.isfinite(atr) and atr > 0):
            return
        if pos > 0:
            self._mr09["stop"] = self._mr09["entry_price"] - float(self.p.mr09_stop_mult) * atr
            return
        self._mr09["stop"] = self._mr09["entry_price"] + float(self.p.mr09_stop_mult) * atr

    def notify_trade(self, trade):
        if not trade.isclosed or trade.data not in self._leg_by_data:
            return

        key = self._leg_by_data[trade.data]
        state = self._alloc_state[key]
        pnl_return = float(trade.pnlcomm) / max(float(self.broker.get_value()), 1e-9)
        alpha = float(self.p.perf_alpha)
        state["perf_ema"] = alpha * pnl_return + (1.0 - alpha) * state["perf_ema"]

        if trade.pnlcomm <= 0:
            state["loss_streak"] += 1
            if state["loss_streak"] >= int(self.p.loss_freeze_after):
                state["freeze"] = max(state["freeze"], int(self.p.loss_freeze_bars))
                state["loss_streak"] = 0
            return

        state["loss_streak"] = 0
