from __future__ import annotations

import csv
import io
import json
import math
import subprocess
import sys
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path

import backtrader as bt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from framework.analyzers import Activity, OpenOpenPnL, PDRatio, RealizedPnL, TruePortfolioPD
from framework.data_loader import add_10_csv_feeds
from framework.strategies_loader import _wrap_with_comp396, load_strategy_class
from framework.strategy_base import COMP396BrokerConfig

OUT_DIR = ROOT / "output" / "coursework_3_stage3_v2v3_analysis" / "part3_drawdown_analysis"
PART3_DIR = ROOT / "DATA" / "PART3"
STARTING_CASH = 1_000_000.0
SLIPPAGE_MULT = 2.0

V2_REF = "summary/coursework_2/stage-4-v2-archive-summary"
V2_PATH = "strategies/team01.py"


def _git_show_text(ref: str, repo_path: str) -> str:
    completed = subprocess.run(
        ["git", "show", f"{ref}:{repo_path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    _ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload) -> None:
    _ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    _ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def _vol_target_pct(vol_target_ann, sigma_ann, pos_cap, ann_factor=252.0):
    if sigma_ann is None or not np.isfinite(sigma_ann) or sigma_ann <= 0:
        return 0.0
    vol_target_daily = float(vol_target_ann) / math.sqrt(float(ann_factor))
    sigma_daily = float(sigma_ann) / math.sqrt(float(ann_factor))
    raw = vol_target_daily / max(sigma_daily, 1e-10)
    return max(-pos_cap, min(pos_cap, raw))


def _format_order(order) -> str:
    action = "BUY" if order.isbuy() else "SELL"
    size = abs(float(order.created.size))
    return f"{action} {order.data._name} size={size:.4f}"


def _format_fill(order) -> str:
    action = "BUY" if order.isbuy() else "SELL"
    size = abs(float(order.executed.size))
    price = float(order.executed.price)
    return f"{action} {order.data._name} fill_size={size:.4f} fill_px={price:.4f}"


def _format_trade(trade) -> str:
    return f"CLOSE {trade.data._name} pnl_net={float(trade.pnlcomm):.2f}"


def _join_messages(items: list[str]) -> str:
    return " | ".join(items) if items else ""


def _current_pct(strategy: bt.Strategy, data) -> float:
    close = float(data.close[0]) if np.isfinite(data.close[0]) else 0.0
    value = max(float(strategy.broker.get_value()), 1e-9)
    return float(strategy.getposition(data).size) * close / value


def _safe_float(value):
    try:
        value = float(value)
    except Exception:
        return None
    return value if np.isfinite(value) else None


@dataclass
class RunArtifacts:
    version: str
    summary: dict
    trace_rows: list[dict]
    max_drawdown_rows: list[dict]
    event_window_rows: list[dict]


class _TraceMixin:
    trace_version = "unknown"

    def start(self):
        super().start()
        self._trace_rows = []
        self._fill_messages_by_date: dict[str, list[str]] = defaultdict(list)
        self._trade_messages_by_date: dict[str, list[str]] = defaultdict(list)

    def notify_order(self, order):
        super().notify_order(order)
        if order.status == order.Completed:
            dt = self.datas[0].datetime.date(0).isoformat()
            self._fill_messages_by_date[dt].append(_format_fill(order))

    def notify_trade(self, trade):
        super().notify_trade(trade)
        if trade.isclosed:
            dt = self.datas[0].datetime.date(0).isoformat()
            self._trade_messages_by_date[dt].append(_format_trade(trade))

    def next(self):
        super().next()
        dt = self.datas[0].datetime.date(0).isoformat()
        row = self._snapshot_row(dt)
        row["submitted_orders"] = _join_messages([_format_order(order) for order in getattr(self, "_today_market_orders", [])])
        row["filled_orders"] = _join_messages(self._fill_messages_by_date.pop(dt, []))
        row["closed_trades"] = _join_messages(self._trade_messages_by_date.pop(dt, []))
        self._trace_rows.append(row)

    def _snapshot_row(self, dt: str) -> dict:
        raise NotImplementedError


def _make_v3_trace_class():
    wrapped = load_strategy_class("coursework_3.stage_2_team01_v3_final", "TeamStrategy")

    class V3TraceStrategy(_TraceMixin, wrapped):
        trace_version = "V3"

        def _snapshot_row(self, dt: str) -> dict:
            mr_z = _safe_float(self._mr09["z"].z[0])
            atr_pct = _safe_float(self._mr09["atr_pct"][0])
            atr_q = _safe_float(self._mr09["atr_pct_q"][0])
            return {
                "date": dt,
                "version": "V3",
                "equity": float(self.broker.get_value()),
                "tf_pos_size": float(self.getposition(self.d_tf).size),
                "mr09_pos_size": float(self.getposition(self.d_mr09).size),
                "tf_pos_pct": _current_pct(self, self.d_tf),
                "mr09_pos_pct": _current_pct(self, self.d_mr09),
                "tf_active_weight": _safe_float(self._active_weights.get("tf")),
                "mr09_active_weight": _safe_float(self._active_weights.get("mr09")),
                "tf_score": _safe_float(self._tf_score()),
                "tf_hot_score": _safe_float(self._tf_hot_score()),
                "tf_signal_strength": _safe_float(self._tf_signal_strength()),
                "mr09_z_score": mr_z,
                "mr09_signal_strength": _safe_float(self._mr09_signal_strength()),
                "mr09_atr_pct": atr_pct,
                "mr09_atr_q": atr_q,
                "tf_freeze": int(self._alloc_state["tf"]["freeze"]),
                "mr09_freeze": int(self._alloc_state["mr09"]["freeze"]),
                "tf_loss_streak": int(self._alloc_state["tf"]["loss_streak"]),
                "mr09_loss_streak": int(self._alloc_state["mr09"]["loss_streak"]),
                "tf_perf_ema": _safe_float(self._alloc_state["tf"]["perf_ema"]),
                "mr09_perf_ema": _safe_float(self._alloc_state["mr09"]["perf_ema"]),
                "tf_stop": _safe_float(self._tf_stop),
                "mr09_stop": _safe_float(self._mr09["stop"]),
                "tf_cooldown": int(self._tf_cooldown),
                "mr09_cooldown": int(self._mr09["cooldown"]),
            }

    return V3TraceStrategy


def _load_v2_strategy_class():
    source = _git_show_text(V2_REF, V2_PATH)
    namespace = {
        "__name__": "team01_v2_archive_runtime",
        "math": math,
        "deque": deque,
        "bt": bt,
        "np": np,
    }
    exec(source, namespace)
    team_strategy = namespace["TeamStrategy"]
    return _wrap_with_comp396(team_strategy)


def _make_v2_trace_class():
    wrapped = _load_v2_strategy_class()

    class V2TraceStrategy(_TraceMixin, wrapped):
        trace_version = "V2"

        def _snapshot_row(self, dt: str) -> dict:
            tf_close = float(self.d_tf.close[0]) if np.isfinite(self.d_tf.close[0]) else np.nan
            tf_sigma_ann = None
            if np.isfinite(self.tf_atr[0]) and np.isfinite(tf_close) and tf_close > 0:
                tf_sigma_ann = (float(self.tf_atr[0]) / tf_close) * math.sqrt(252.0)
            tf_target = _vol_target_pct(
                self.p.tf_target_vol_ann * self.p.w_tf,
                tf_sigma_ann,
                self.p.tf_pos_cap,
            )

            mr_close = float(self.d_mr.close[0]) if np.isfinite(self.d_mr.close[0]) else np.nan
            mr_mu = float(self.mr_ma[0]) if np.isfinite(self.mr_ma[0]) else mr_close
            mr_sd = float(self.mr_std[0]) if np.isfinite(self.mr_std[0]) and self.mr_std[0] > 1e-12 else np.nan
            mr_z = (mr_close - mr_mu) / mr_sd if np.isfinite(mr_close) and np.isfinite(mr_mu) and np.isfinite(mr_sd) and mr_sd > 0 else np.nan
            mr_sigma_ann = None
            if np.isfinite(self.mr_atr[0]) and np.isfinite(mr_close) and mr_close > 0:
                mr_sigma_ann = (float(self.mr_atr[0]) / mr_close) * math.sqrt(252.0)
            mr_target = _vol_target_pct(
                self.p.mr_target_vol_ann * self.p.w_mr,
                mr_sigma_ann,
                self.p.mr_pos_cap,
            )

            ga_sigma_ann = self._sigma_ann_ga()
            ga_base = _vol_target_pct(
                self.p.ga_target_vol_ann * self.p.w_ga,
                ga_sigma_ann,
                self.p.ga_pos_cap,
                self.p.ga_ann_factor,
            )

            if len(self._ga_sigma_hist) < max(20, int(self.p.ga_sigma_q_lookback) // 4):
                ga_mult = float(self.p.ga_mult_mid)
            else:
                arr = np.asarray(self._ga_sigma_hist, dtype=float)
                q_low = np.quantile(arr, float(self.p.ga_sigma_q_low))
                q_high = np.quantile(arr, float(self.p.ga_sigma_q_high))
                if ga_sigma_ann is not None and ga_sigma_ann <= q_low:
                    ga_mult = 1.0
                elif ga_sigma_ann is not None and ga_sigma_ann >= q_high:
                    ga_mult = float(self.p.ga_mult_high)
                else:
                    ga_mult = float(self.p.ga_mult_mid)

            return {
                "date": dt,
                "version": "V2",
                "equity": float(self.broker.get_value()),
                "tf_pos_size": float(self.getposition(self.d_tf).size),
                "mr_pos_size": float(self.getposition(self.d_mr).size),
                "ga_pos_size": float(self.getposition(self.d_ga).size),
                "tf_pos_pct": _current_pct(self, self.d_tf),
                "mr_pos_pct": _current_pct(self, self.d_mr),
                "ga_pos_pct": _current_pct(self, self.d_ga),
                "tf_trend_up": bool(self.tf_ema_s[0] > self.tf_ema_l[0]),
                "tf_target_pct": _safe_float(tf_target),
                "tf_stop": _safe_float(self._tf_sl),
                "mr_z_score": _safe_float(mr_z),
                "mr_target_pct": _safe_float(mr_target),
                "mr_stop": _safe_float(self._mr_sl),
                "ga_bull": bool(self.ga_ema_s[0] > self.ga_ema_l[0]),
                "ga_sigma_ann": _safe_float(ga_sigma_ann),
                "ga_mult": _safe_float(ga_mult),
                "ga_target_pct": _safe_float(ga_base * ga_mult),
                "ga_stop": _safe_float(self._ga_sl),
                "ga_cooldown": int(self._ga_cooldown),
            }

    return V2TraceStrategy


def _build_trace_rows(strat, oopnl: dict) -> list[dict]:
    daily_by_date = {date.isoformat(): value for date, value in zip(oopnl["dates"], oopnl["portfolio_daily"])}
    cum_by_date = {date.isoformat(): value for date, value in zip(oopnl["dates"], oopnl["portfolio_cum"])}
    running_peak = -float("inf")
    peak_date = None

    rows = []
    for row in strat._trace_rows:
        equity = float(row["equity"])
        running_peak = max(running_peak, equity)
        if math.isclose(running_peak, equity) or equity >= running_peak:
            peak_date = row["date"]
        enriched = dict(row)
        enriched["cum_open_open_pnl"] = daily_by_date.get(row["date"], 0.0)
        enriched["portfolio_cum_open_open_pnl"] = cum_by_date.get(row["date"], 0.0)
        enriched["running_peak_equity"] = running_peak
        enriched["drawdown_abs"] = running_peak - equity
        enriched["drawdown_pct"] = (running_peak - equity) / running_peak if running_peak > 0 else 0.0
        enriched["current_peak_date"] = peak_date
        rows.append(enriched)
    return rows


def _find_recovery_index(rows: list[dict], trough_idx: int, peak_equity: float):
    for idx in range(trough_idx, len(rows)):
        if rows[idx]["equity"] >= peak_equity:
            return idx
    return None


def _summarize_drawdown(rows: list[dict], version: str) -> tuple[list[dict], list[dict]]:
    if not rows:
        return [], []
    trough_idx = max(range(len(rows)), key=lambda idx: rows[idx]["drawdown_abs"])
    trough = rows[trough_idx]
    peak_idx = next(
        idx for idx in range(trough_idx, -1, -1)
        if rows[idx]["date"] == trough["current_peak_date"]
    )
    peak = rows[peak_idx]
    recovery_idx = _find_recovery_index(rows, trough_idx, peak["equity"])
    recovery = rows[recovery_idx] if recovery_idx is not None else None

    def nearest_action(start_idx: int, stop_idx: int, step: int):
        idx = start_idx
        while idx != stop_idx:
            row = rows[idx]
            messages = [row.get("submitted_orders", ""), row.get("filled_orders", ""), row.get("closed_trades", "")]
            message = " | ".join(item for item in messages if item)
            if message:
                return row["date"], message
            idx += step
        return "", ""

    pre_action_date, pre_action = nearest_action(trough_idx, -1, -1)
    post_action_date, post_action = nearest_action(trough_idx + 1, len(rows), 1)

    summary = {
        "version": version,
        "peak_date": peak["date"],
        "peak_equity": peak["equity"],
        "trough_date": trough["date"],
        "trough_equity": trough["equity"],
        "max_drawdown_abs": trough["drawdown_abs"],
        "max_drawdown_pct": trough["drawdown_pct"],
        "recovery_date": recovery["date"] if recovery else "",
        "recovery_equity": recovery["equity"] if recovery else "",
        "trading_days_peak_to_trough": trough_idx - peak_idx,
        "trading_days_peak_to_recovery": (recovery_idx - peak_idx) if recovery_idx is not None else "",
        "submitted_orders_at_trough": trough.get("submitted_orders", ""),
        "filled_orders_at_trough": trough.get("filled_orders", ""),
        "closed_trades_at_trough": trough.get("closed_trades", ""),
        "nearest_pre_trough_action_date": pre_action_date,
        "nearest_pre_trough_action": pre_action,
        "nearest_post_trough_action_date": post_action_date,
        "nearest_post_trough_action": post_action,
    }

    window_rows = []
    start = max(0, trough_idx - 5)
    end = min(len(rows), trough_idx + 6)
    for idx in range(start, end):
        item = dict(rows[idx])
        item["window_role"] = (
            "peak" if idx == peak_idx else
            "trough" if idx == trough_idx else
            "recovery" if recovery_idx is not None and idx == recovery_idx else
            "context"
        )
        item["version"] = version
        window_rows.append(item)
    return [summary], window_rows


def _run_strategy(version: str, strategy_class: type, out_dir: Path) -> RunArtifacts:
    _ensure_dir(out_dir)
    cerebro = bt.Cerebro(stdstats=False, preload=True, runonce=True)
    cerebro.broker.setcash(STARTING_CASH)
    add_10_csv_feeds(cerebro, PART3_DIR)

    params = {
        "_comp396": COMP396BrokerConfig(
            s_mult=SLIPPAGE_MULT,
            end_policy="liquidate",
            output_dir=str(out_dir),
            debug=False,
        )
    }

    cerebro.addstrategy(strategy_class, **params)
    cerebro.addanalyzer(OpenOpenPnL, _name="oopnl")
    cerebro.addanalyzer(PDRatio, _name="pd")
    cerebro.addanalyzer(Activity, _name="activity")
    cerebro.addanalyzer(RealizedPnL, _name="realpnl")
    cerebro.addanalyzer(TruePortfolioPD, _name="truepd")

    strat = cerebro.run(maxcpus=1)[0]

    oopnl = strat.analyzers.oopnl.get_analysis()
    pdres = strat.analyzers.pd.get_analysis()
    act = strat.analyzers.activity.get_analysis()
    truepd = strat.analyzers.truepd.get_analysis()

    summary = {
        "version": version,
        "final_value": float(cerebro.broker.getvalue()),
        "bankrupt": bool(oopnl.get("bankrupt", False)),
        "bankrupt_date": oopnl.get("bankrupt_date").isoformat() if oopnl.get("bankrupt_date") else "",
        "open_pnl_pd_ratio": pdres.get("portfolio", {}).get("pd_ratio"),
        "true_pd_ratio": truepd.get("pd_ratio") if truepd else None,
        "activity_pct": act.get("activity_pct"),
        "s_mult": SLIPPAGE_MULT,
    }

    trace_rows = _build_trace_rows(strat, oopnl)
    max_drawdown_rows, event_window_rows = _summarize_drawdown(trace_rows, version)
    return RunArtifacts(
        version=version,
        summary=summary,
        trace_rows=trace_rows,
        max_drawdown_rows=max_drawdown_rows,
        event_window_rows=event_window_rows,
    )


def _build_summary_markdown(v2: RunArtifacts, v3: RunArtifacts) -> str:
    v2_dd = v2.max_drawdown_rows[0]
    v3_dd = v3.max_drawdown_rows[0]
    lines = [
        "# Part 3 Drawdown Event Analysis",
        "",
        "This file is designed for Chapter 3.3.1. It ties the equity/drawdown story to concrete Part 3 dates and same-day strategy reactions.",
        "",
        "## Key Findings",
        "",
        f"- V2 reached its deepest Part 3 drawdown on {v2_dd['trough_date']}, falling {v2_dd['max_drawdown_abs']:.2f} from the prior peak on {v2_dd['peak_date']}.",
        f"- The nearest pre-trough V2 action was on {v2_dd['nearest_pre_trough_action_date']}: {v2_dd['nearest_pre_trough_action'] or 'no recorded order action'}.",
        f"- The first post-trough V2 action was on {v2_dd['nearest_post_trough_action_date']}: {v2_dd['nearest_post_trough_action'] or 'no recorded order action'}.",
        f"- V3 reached its deepest Part 3 drawdown on {v3_dd['trough_date']}, falling {v3_dd['max_drawdown_abs']:.2f} from the prior peak on {v3_dd['peak_date']}.",
        f"- The nearest pre-trough V3 action was on {v3_dd['nearest_pre_trough_action_date']}: {v3_dd['nearest_pre_trough_action'] or 'no recorded order action'}.",
        f"- The first post-trough V3 action was on {v3_dd['nearest_post_trough_action_date']}: {v3_dd['nearest_post_trough_action'] or 'no recorded order action'}.",
        f"- V2 ended Part 3 with true PD {v2.summary['true_pd_ratio']:.4f} and activity {v2.summary['activity_pct']:.2f}%.",
        f"- V3 ended Part 3 with true PD {v3.summary['true_pd_ratio']:.4f} and activity {v3.summary['activity_pct']:.2f}%.",
        "",
        "## Files",
        "",
        "- `v2_part3_bar_trace.csv`: date-level V2 trace with equity, drawdown, signal state, positions, and submitted / filled orders.",
        "- `v3_part3_bar_trace.csv`: date-level V3 trace with equity, drawdown, active weights, signal state, freeze/cooldown state, and orders.",
        "- `part3_max_drawdown_summary.csv`: one-row summary per version for the deepest drawdown window.",
        "- `part3_max_drawdown_window.csv`: +/- 5 trading days around each version's deepest drawdown trough.",
        "- `part3_run_summaries.json`: rerun summary metrics for V2 and V3 on restored PART3 data.",
        "",
        "## How To Use In 3.3.1",
        "",
        "- Use `part3_max_drawdown_summary.csv` to state the exact peak date, trough date, drawdown depth, and recovery speed.",
        "- Use `part3_max_drawdown_window.csv` to describe what the strategy did around the drawdown: whether it queued exits, reduced exposure, or stayed concentrated in one leg.",
        "- Use the full `v2_part3_bar_trace.csv` and `v3_part3_bar_trace.csv` when you want to justify wording such as 'TF remained dominant', 'MR contribution was weak', or 'V3 cut risk through lower activity and tighter control logic'.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    if not PART3_DIR.exists():
        raise SystemExit(f"Missing PART3 data directory: {PART3_DIR}")

    v2_cls = _make_v2_trace_class()
    v3_cls = _make_v3_trace_class()

    v2_run = _run_strategy("V2", v2_cls, OUT_DIR / "v2_part3_rerun")
    v3_run = _run_strategy("V3", v3_cls, OUT_DIR / "v3_part3_rerun")

    common_trace_fields = sorted({key for row in (v2_run.trace_rows + v3_run.trace_rows) for key in row.keys()})
    _write_csv(OUT_DIR / "v2_part3_bar_trace.csv", v2_run.trace_rows, common_trace_fields)
    _write_csv(OUT_DIR / "v3_part3_bar_trace.csv", v3_run.trace_rows, common_trace_fields)

    dd_fields = list(v2_run.max_drawdown_rows[0].keys())
    _write_csv(OUT_DIR / "part3_max_drawdown_summary.csv", v2_run.max_drawdown_rows + v3_run.max_drawdown_rows, dd_fields)

    window_fields = sorted({key for row in (v2_run.event_window_rows + v3_run.event_window_rows) for key in row.keys()})
    _write_csv(OUT_DIR / "part3_max_drawdown_window.csv", v2_run.event_window_rows + v3_run.event_window_rows, window_fields)

    _write_json(
        OUT_DIR / "part3_run_summaries.json",
        {
            "V2": v2_run.summary,
            "V3": v3_run.summary,
        },
    )

    _write_text(OUT_DIR / "part3_drawdown_analysis_summary.md", _build_summary_markdown(v2_run, v3_run))
    print(f"Wrote Part 3 drawdown analysis to: {OUT_DIR}")


if __name__ == "__main__":
    main()
