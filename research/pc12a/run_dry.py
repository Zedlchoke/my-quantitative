"""Dry-run CLI — PC12A implementation lane (NO PnL; RGC-INC-1 law).

Usage:
    .venv/bin/python -m research.pc12a.run_dry \
        --legs research/pc12a/legs_config \
        --window 2024-01-05,2024-02-23 \
        --out <dir> [--tier 1.0]

Streams the Lane-D-audited M1 panels day by day (read-only), runs the
configured legs through the L1-L7 policy skeleton with the cost kernel and
the hash-chained journal, and writes:

- ``journal.jsonl``        append-only hash-chained rows (journal_row@1)
- ``DRY_RUN_REPORT.json``  decision counts, vote distributions, fill counts
                           by outcome enum, blocked-reason histogram,
                           cost-bill totals by component, journal row count,
                           elapsed, code/data digests, leak-scan result.

FORBIDDEN anywhere in the outputs: pnl / sharpe / profit / drawdown /
equity_delta / return / equity (the run greps its own output and FAILS on
a hit).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import time
from typing import Dict, List, Optional

import numpy as np

from . import calendar_service as cal
from . import cost_kernel as _ck
from . import journal as _jr
from . import legs as _legs
from . import panels as _panels
from . import policy as _pol

UTC = dt.timezone.utc
FORBIDDEN_KEYS = ("pnl", "sharpe", "profit", "drawdown", "equity_delta",
                  "return", "equity")
REPORT_SCHEMA = "pc12a_dry_run_report@1"

WARMUP_TRADING_DAYS = {
    "volprof": 25,
    "USDJPY-S001": 60,
    "EURUSD-S009": 280,
    "default_daily": 2,
}
CALENDAR_DAYS_PER_TRADING_DAY = 1.45
FLAT_HOUR_MIN = (19, 54)          # hard-flat decision instant (flat BY 19:55)
FREEZE_MIN = 1200                 # Friday profile freeze cut [0, 20:00)


def _fmt_ts(t: dt.datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class DryRunError(RuntimeError):
    pass


class SymbolEngine:
    """Streams one pair's panels through legs + policy + journal."""

    def __init__(self, symbol: str, leg_cfgs: List[Dict], args,
                 journal: _jr.JournalWriter, guard: _pol.CostGuard,
                 report: Dict):
        self.symbol = symbol
        self.kernel = _ck.CostKernel(symbol, tier=args.tier)
        self.legs: List[_legs.BaseLeg] = [_legs.build_leg(c)
                                          for c in leg_cfgs]
        self.volprof_legs = [l for l in self.legs
                             if isinstance(l, _legs.VolprofLeg)]
        self.daily_legs = [l for l in self.legs
                           if not isinstance(l, _legs.VolprofLeg)]
        self.journal = journal
        self.guard = guard
        self.report = report
        self.window_start = args.window_start
        self.window_end = args.window_end
        self.tier = args.tier
        self.book_units = 0.0
        self.cash = 100_000.0            # internal state; NEVER reported
        self.day_buffer: List[Dict] = []
        self.tr_deque: List[float] = []
        self.last_mid_close: Optional[float] = None
        self.prev_day_agg: Optional[Dict] = None
        self.profile: Optional[_legs.WeeklyProfile] = None
        self.leg_stats: Dict[str, _pol.LegRuntimeStats] = {
            l.identity.candidate_id: _pol.LegRuntimeStats() for l in self.legs}
        self.eligibility = _pol.Eligibility()
        self.netting = _pol.Netting()
        self.caps = _pol.ClusterCaps()
        self.order_seq = 0
        self.leg_desires: Dict[str, int] = {
            l.identity.candidate_id: 0 for l in self.legs}
        self.leg_by_id = {l.identity.candidate_id: l for l in self.legs}
        self.first_decision_ts: Optional[dt.datetime] = None

    # -- warmup ---------------------------------------------------------------

    def _warmup_start(self) -> dt.date:
        need = WARMUP_TRADING_DAYS["volprof"] if self.volprof_legs else 0
        for l in self.daily_legs:
            need = max(need, WARMUP_TRADING_DAYS.get(
                l.identity.candidate_id,
                WARMUP_TRADING_DAYS["default_daily"]))
        cal_days = int(need * CALENDAR_DAYS_PER_TRADING_DAY) + 10
        return self.window_start - dt.timedelta(days=cal_days)

    # -- day loop ---------------------------------------------------------------

    def run(self, store: _panels.PanelStore) -> Dict:
        d = self._warmup_start()
        data_days = 0
        while d <= self.window_end:
            try:
                day = store.load_day(self.symbol, d)
            except (FileNotFoundError, _panels.PanelError):
                d += dt.timedelta(days=1)
                continue
            data_days += 1
            self._process_day(day, d)
            d += dt.timedelta(days=1)
        return {"data_days": data_days}

    def _process_day(self, day: _panels.DayPanel, date: dt.date) -> None:
        tradable = day.tradable_mask()
        n_trad = int(tradable.sum())
        in_window = self.window_start <= date <= self.window_end
        bid_high, bid_low = day.bid.high, day.bid.low
        mid_close = day.mid_close

        # Rolling 60-bar TR state.  PIT law (campaign §8.1 truncation
        # replay, verification-lane fix): on DECISION days the deque
        # advances bar-by-bar INSIDE the decision loop so a decision at
        # minute m only ever sees bars <= m.  The original whole-day
        # pre-pass fed same-day FUTURE bars into ctx.atr60 (stops, VC3
        # deviation) and broke the prefix-identity law; it is retained
        # ONLY on warmup days, where no decisions are journaled.
        def _advance_tr(m: int) -> None:
            if self.last_mid_close is None:
                tr = float(bid_high[m] - bid_low[m])
            else:
                tr = max(bid_high[m] - bid_low[m],
                         abs(bid_high[m] - self.last_mid_close),
                         abs(bid_low[m] - self.last_mid_close))
            self.tr_deque.append(tr)
            if len(self.tr_deque) > 60:
                self.tr_deque.pop(0)
            self.last_mid_close = float(mid_close[m])

        # day buffer for the weekly profile (trailing 20 weekdays)
        if n_trad >= 1 and date.weekday() < 5:
            self.day_buffer.append({
                "date": date,
                "mid_close": mid_close.copy(),
                "bid_vol": day.bid.volume.copy(),
                "bid_high": bid_high.copy(),
                "bid_low": bid_low.copy(),
                "tradable": tradable.copy(),
                "day_high": float(bid_high[tradable].max()),
                "day_low": float(bid_low[tradable].min()),
                "day_close": float(mid_close[tradable][-1]),
                "last_bid_close": float(day.bid.close[tradable][-1]),
                "last_ask_close": float(day.ask.close[tradable][-1]),
            })
            if len(self.day_buffer) > 20:
                self.day_buffer.pop(0)

        if not in_window:
            # indicator warm-up only (no decisions journaled, no fills):
            # daily legs consume the completed prior trading day during
            # the warmup stream so their lookback history exists at the
            # window start
            for m in range(_panels.RECORDS_PER_DAY):
                if tradable[m]:
                    _advance_tr(m)
            if self.prev_day_agg is not None and self.daily_legs:
                for leg in self.daily_legs:
                    leg.on_daily_bar(self.prev_day_agg)
            if date.strftime("%a") == "Fri":
                self._maybe_freeze(date)
            self._update_prev_agg(date)
            return

        midnight = dt.datetime.combine(date, dt.time(0, 0), tzinfo=UTC)
        sessions = cal.session_windows_utc(date)
        flat_ts = midnight + dt.timedelta(hours=FLAT_HOUR_MIN[0],
                                          minutes=FLAT_HOUR_MIN[1])

        # daily legs decide at 00:00 on the completed prior trading day;
        # fill at the first tradable bar of the day (bar index 0+).
        # Weekdays only (the FX trading week is Mon..Fri; a Sunday reopen
        # belongs to Monday's session) and only on days with tradable
        # minutes (Saturdays/holidays are carry-forward).
        if (self.prev_day_agg is not None and self.daily_legs
                and date.weekday() < 5 and n_trad >= 1):
            self._daily_decision(midnight, day)

        for m in range(_panels.RECORDS_PER_DAY):
            if not tradable[m]:
                continue
            _advance_tr(m)   # deque as-of THIS completed bar (PIT: <= m)
            ts_close = midnight + dt.timedelta(minutes=m + 1)
            ctx = self._make_ctx(day, m, ts_close, sessions, flat_ts)
            holding = any(l.desired_units != 0 for l in self.volprof_legs)
            wants = (ctx.in_entry_window or holding or ctx.is_flat_instant
                     or (ts_close >= flat_ts and holding))
            if wants:
                self._minute_decision(ctx, day, m, ts_close)

        if date.strftime("%a") == "Fri":
            self._maybe_freeze(date)
        self._update_prev_agg(date)

        # swap accrual event at 22:00 UTC (DECLARED U4/U5 calendar)
        mult = cal.swap_multiplier(date.strftime("%a"))
        if mult > 0 and self.book_units != 0.0:
            m22 = self._last_tradable_at_or_before(day, 22 * 60)
            mid22 = float(mid_close[m22]) if m22 is not None \
                else float(self.last_mid_close or 0.0)
            swap_usd = self.kernel.swap_usd(abs(self.book_units), mult,
                                            mid22)
            self.cash -= swap_usd
            self.report["cost_bill_totals_usd"]["swap"] += swap_usd
            self.journal.write("SWAP", _jr.swap_row(
                ts_utc=_fmt_ts(dt.datetime.combine(date, dt.time(22, 0),
                                                   tzinfo=UTC)),
                symbol=self.symbol, weekday_utc=date.strftime("%A").lower(),
                units_abs=abs(self.book_units), multiplier=mult,
                swap_usd=swap_usd, wed_x3=mult == 3,
                units_after=self.book_units))
            for lid in sorted(self.leg_stats):
                share = self._leg_share(lid)
                if share > 0:
                    self.leg_stats[lid].cost_events.append(
                        (dt.datetime.combine(date, dt.time(22, 0),
                                             tzinfo=UTC),
                         swap_usd * share))

    # -- contexts ---------------------------------------------------------------

    def _make_ctx(self, day: _panels.DayPanel, m: int, ts_close,
                  sessions, flat_ts) -> _legs.BarContext:
        tradable = day.tradable_mask()
        pm = m - 1
        while pm >= 0 and not tradable[pm]:
            pm -= 1
        prev_mid = float(day.mid_close[pm]) if pm >= 0 else (
            self.last_mid_close if self.last_mid_close is not None
            else float(day.mid_close[m]))
        atr60 = sum(self.tr_deque) / len(self.tr_deque) if self.tr_deque \
            else 0.0
        in_win = any(s <= ts_close < e for s, e, _ in sessions)
        return _legs.BarContext(
            ts=ts_close, symbol=self.symbol,
            mid_close=float(day.mid_close[m]), mid_close_prev=prev_mid,
            bid_open=float(day.bid.open[m]),
            ask_open=float(day.ask.open[m]),
            bid_close=float(day.bid.close[m]),
            ask_close=float(day.ask.close[m]),
            bid_low=float(day.bid.low[m]),
            ask_high=float(day.ask.high[m]),
            atr60=atr60, in_entry_window=in_win,
            is_flat_instant=ts_close == flat_ts, day=ts_close.date(),
            profile=self.profile, last_data_ts=ts_close)

    # -- decisions ----------------------------------------------------------------

    def _daily_decision(self, midnight: dt.datetime,
                        day: _panels.DayPanel) -> None:
        decisions: Dict[str, _legs.LegDecision] = {}
        for leg in self.daily_legs:
            dec = leg.on_daily_bar(self.prev_day_agg)
            if dec is not None:
                decisions[leg.identity.candidate_id] = dec
        if decisions:
            self._apply_decisions(decisions, midnight, day, -1)

    def _minute_decision(self, ctx: _legs.BarContext, day: _panels.DayPanel,
                         m: int, ts_close: dt.datetime) -> None:
        decisions: Dict[str, _legs.LegDecision] = {}
        for leg in self.volprof_legs:
            dec = leg.on_bar(ctx)
            if dec is not None:
                decisions[leg.identity.candidate_id] = dec
        # defensive forced flat (VOLPROF hard-flat law): if the 19:54
        # minute itself was untradable, fire the flat at the first
        # tradable minute at/after it; fill forward-searches honestly.
        if ctx.ts >= ctx.ts.replace(hour=FLAT_HOUR_MIN[0],
                                    minute=FLAT_HOUR_MIN[1], second=0):
            for leg in self.volprof_legs:
                if leg.desired_units != 0 and \
                        leg.identity.candidate_id not in decisions:
                    leg._record_exit(ctx.ts, "TIME_STOP_FLAT_1955")
                    decisions[leg.identity.candidate_id] = _legs.LegDecision(
                        vote=0, desired_units=0,
                        reason_code="TIME_STOP_FLAT_1955", order_kind="CLOSE",
                        feature_pit_snapshot=[
                            {"input_id": f"{self.symbol}_M1_MIDCLOSE",
                             "available_time_utc": _fmt_ts(ctx.ts),
                             "value_digest": "forced_flat",
                             "max_age": "P7D", "max_age_ok": True}])
        if decisions:
            self._apply_decisions(decisions, ts_close, day, m)

    def _apply_decisions(self, decisions: Dict[str, _legs.LegDecision],
                         ts: dt.datetime, day: _panels.DayPanel,
                         m: int) -> None:
        if self.first_decision_ts is None:
            for st in self.leg_stats.values():
                st.leg_start_ts = ts
            self.first_decision_ts = ts
        on = _pol.EligibilityVerdict("ON", None, "eligible")
        eligible: Dict[str, _legs.LegDecision] = {}
        for lid, dec in decisions.items():
            leg = self.leg_by_id[lid]
            st = self.leg_stats[lid]
            st.decisions_total += 1
            self.report["legs"][lid]["decisions"] += 1
            v = self.report["legs"][lid]["votes"]
            v[str(dec.vote)] = v.get(str(dec.vote), 0) + 1
            elig = self.eligibility.evaluate(lid, st,
                                             dec.feature_pit_snapshot, ts)
            fields = self._dec_fields(leg, dec, ts, elig)
            if elig.state != "ON":
                outcome = {"E1": "BLOCKED_FLOOR", "E3": "BLOCKED_STALE",
                           "E4": "BLOCKED_COST_BUDGET"}.get(elig.rule_id or
                                                            "", "BLOCKED_FLOOR")
                self._leg_outcome(lid, outcome)
                self._hist(outcome)
                self.journal.write("BLOCK", _jr.blocked_row(
                    outcome=outcome, blocked_reason_detail=elig.detail,
                    decision_fields=fields))
                continue
            eligible[lid] = dec
            self.journal.write("DECISION", fields)
            self.leg_desires[lid] = dec.desired_units
        if not eligible:
            return

        # L4 netting over ALL legs' standing desires
        net = self.netting.net(dict(self.leg_desires))
        if net.tie_zero:
            for lid in eligible:
                self._leg_outcome(lid, "NETTED_TO_ZERO")
                self._hist("NETTED_TO_ZERO")
                self.journal.write("NETTED_TO_ZERO", _jr.blocked_row(
                    outcome="NETTED_TO_ZERO",
                    blocked_reason_detail=(
                        "L4 tie: nonzero votes net to 0 -> asset FLAT this "
                        "decision (no fill, no cash effect)"),
                    decision_fields=self._dec_fields(
                        self.leg_by_id[lid], eligible[lid], ts, on)))
            return

        # L5 cluster/asset caps
        clamped, cap_reason = self.caps.clamp(
            net.net_target_units,
            [self.leg_by_id[l].identity.cluster_id
             for l in self.leg_desires])
        target = int(clamped)
        delta = int(round(target - self.book_units))
        if delta == 0:
            return

        # L6 cost guard on the pre-commit estimate (decision-bar quotes)
        if m >= 0:
            bid_c, ask_c = float(day.bid.close[m]), float(day.ask.close[m])
        else:
            agg = self.prev_day_agg or {}
            c = agg.get("day_close", self.last_mid_close or 1.0)
            bid_c = agg.get("last_bid_close", c)
            ask_c = agg.get("last_ask_close", c)
        side = "buy" if delta > 0 else "sell"
        est = self.kernel.estimate_all_in(side, abs(delta), bid_c, ask_c)
        verdict = self.guard.evaluate(ts, int(self.book_units), target,
                                      est["est_total_usd"])
        if not verdict.allow:
            for lid in eligible:
                self._leg_outcome(lid, "DEFERRED_COST_GUARD")
                self._hist("DEFERRED_COST_GUARD")
                fields = self._dec_fields(self.leg_by_id[lid],
                                          eligible[lid], ts, on)
                fields.update({
                    "order_kind": "DEFER", "urgency": verdict.urgency,
                    "guard": {"window_days": self.guard.state.window_days,
                              "cap_usd": self.guard.state.cap_usd,
                              "trailing_spend_usd":
                                  verdict.trailing_spend_usd},
                    "estimate": est, "units_after": self.book_units,
                    "outcome": "DEFERRED_COST_GUARD",
                    "blocked_reason_detail": verdict.reason})
                self.journal.write("DEFER", fields)
                # ONOFF counterfactual twin (GROUPING_PROPOSAL 4.2): the
                # always-on twin WOULD have filled here; would-* costs are
                # journaled, never charged.
                fb = self._fill_bar_index(day, m)
                if fb is not None:
                    fq = self.kernel.price_ordinary_fill(
                        side, abs(delta), float(day.bid.open[fb]),
                        float(day.ask.open[fb]))
                    twin = _jr.twin_row(
                        twin_of_order_id=None,
                        would_fill_price=fq.fill_price,
                        would_spread_once_usd=fq.spread_once_usd,
                        would_slip_usd=fq.slip_beyond_halfspread_usd,
                        would_commission_usd=self.kernel.commission(
                            abs(delta), fq.fill_price),
                        decision_fields={k: v2 for k, v2 in fields.items()
                                         if k not in ("outcome",
                                                      "blocked_reason_detail",
                                                      "order_kind",
                                                      "urgency", "guard",
                                                      "estimate",
                                                      "units_after")})
                    self.journal.write("TWIN", twin)
            return
        if cap_reason:
            for lid in eligible:
                self._leg_outcome(lid, "BLOCKED_RISK_CAP")
                self._hist("BLOCKED_RISK_CAP")
                self.journal.write("BLOCK", _jr.blocked_row(
                    outcome="BLOCKED_RISK_CAP",
                    blocked_reason_detail=cap_reason,
                    decision_fields=self._dec_fields(
                        self.leg_by_id[lid], eligible[lid], ts, on)))
            return

        # fill at next-bar-open (forward search to the next decision)
        fb = self._fill_bar_index(day, m)
        if fb is None:
            for lid in eligible:
                self._leg_outcome(lid, "UNAVAILABLE_FILL_BAR")
                self._hist("UNAVAILABLE_FILL_BAR")
                self.journal.write("BLOCK", _jr.blocked_row(
                    outcome="BLOCKED_STALE",
                    blocked_reason_detail=(
                        "UNAVAILABLE_FILL_BAR: no fill bar before the next "
                        "decision (fail-closed, no cash effect)"),
                    decision_fields=self._dec_fields(
                        self.leg_by_id[lid], eligible[lid], ts, on)))
            return
        fq = self.kernel.price_ordinary_fill(side, abs(delta),
                                             float(day.bid.open[fb]),
                                             float(day.ask.open[fb]))
        commission = self.kernel.commission(abs(delta), fq.fill_price)
        spread_pips = (float(day.ask.open[fb]) - float(day.bid.open[fb])) \
            / self.kernel.pip
        w4 = _pol.w4_check({f"{self.symbol}_mid_range": fq.mid_at_fill,
                            "spread_pips_max": spread_pips})
        if w4 is not None:
            for lid in eligible:
                self._leg_outcome(lid, "KILLSWITCH_FLAT")
                self._hist("W4_UNSEEN_STRUCTURE")
                self.journal.write("BLOCK", _jr.blocked_row(
                    outcome="KILLSWITCH_FLAT",
                    blocked_reason_detail=w4.detail,
                    decision_fields=self._dec_fields(
                        self.leg_by_id[lid], eligible[lid], ts, on)))
            return

        ts_fill = dt.datetime.combine(ts.date(), dt.time(0, 0), tzinfo=UTC) \
            + dt.timedelta(minutes=fb)
        self.book_units += delta
        if delta > 0:
            self.cash -= delta * fq.fill_price + commission
        else:
            self.cash += (-delta) * fq.fill_price - commission
        self.order_seq += 1
        order_id = f"{self.symbol}-o{self.order_seq:05d}"
        cost_total = (fq.spread_once_usd
                      + fq.slip_beyond_halfspread_usd + commission)
        self.report["cost_bill_totals_usd"]["spread_once"] += \
            fq.spread_once_usd
        self.report["cost_bill_totals_usd"]["slip"] += \
            fq.slip_beyond_halfspread_usd
        self.report["cost_bill_totals_usd"]["commission"] += commission
        if fq.gap_excess_pips > 0:
            self.report["cost_bill_totals_usd"]["slip_gap_excess"] += \
                fq.gap_excess_pips * self.kernel.pip * abs(delta)
        self.guard.record_spend(ts, cost_total)
        for lid in eligible:
            self._leg_outcome(lid, "FILLED")
            self._hist("FILLED")
            st = self.leg_stats[lid]
            st.decision_events.append(ts)
            st.decision_count_trailing += 1
            st.cost_events.append((ts, cost_total * self._leg_share(lid)))
        contributing = [{"leg_id": lid, "vote": eligible[lid].vote,
                         "contribution_units": self.leg_desires.get(lid, 0)}
                        for lid in sorted(eligible)]
        self.journal.write("NET_ORDER", _jr.net_order_row(
            order_id=order_id,
            order_kind=eligible[next(iter(eligible))].order_kind or "OPEN",
            ts_fill_utc=_fmt_ts(ts_fill), symbol=self.symbol, side=side,
            delta_units=delta, fill_price=fq.fill_price,
            quoted_side=fq.quoted_side, mid_at_fill=fq.mid_at_fill,
            spread_once_usd=fq.spread_once_usd,
            slip_beyond_halfspread_usd=fq.slip_beyond_halfspread_usd,
            cross_cost_usd=fq.cross_cost_usd, commission_usd=commission,
            cell_id=fq.cell_id, u3_band_id="U3_NON_EVENT",
            venue_model="PANEL_DUKA", units_after=self.book_units,
            contributing_legs=contributing))

    # -- misc -----------------------------------------------------------------

    def _dec_fields(self, leg, decision: _legs.LegDecision, ts: dt.datetime,
                    elig: _pol.EligibilityVerdict) -> Dict:
        ident = leg.identity
        st = self.leg_stats[ident.candidate_id]
        return _jr.decision_row(
            ts_decision_utc=_fmt_ts(ts), fold_id=None,
            cycle_id=ident.cycle_id, sleeve_id=ident.sleeve_id,
            leg_id=ident.candidate_id, symbol=self.symbol,
            family_id=ident.family_id, mech_key=ident.mech_key,
            outcome_exposed_label=ident.outcome_exposed_label,
            cluster_id=ident.cluster_id, direction_vote=decision.vote,
            desired_risk_units=decision.desired_units,
            entry_reason_code=decision.reason_code,
            eligibility_state=elig.state + (f" ({elig.rule_id})"
                                            if elig.rule_id else ""),
            risk_rule_state="netting voter",
            portfolio_state={"n_eligible": len(self.legs)},
            feature_pit_snapshot=decision.feature_pit_snapshot,
            eligibility_rule_id=elig.rule_id,
            onoff_features={
                "decision_count_trailing": st.decision_count_trailing})

    def _leg_outcome(self, lid: str, outcome: str) -> None:
        d = self.report["legs"][lid]["fills_by_outcome"]
        d[outcome] = d.get(outcome, 0) + 1

    def _hist(self, key: str) -> None:
        h = self.report["blocked_reason_histogram"]
        h[key] = h.get(key, 0) + 1

    def _fill_bar_index(self, day: _panels.DayPanel, m: int) -> Optional[int]:
        """The [T, T+1) bar open prices a decision at T; forward search for
        the first available bar (FILL_ACCOUNTING_SPEC 4)."""
        tradable = day.tradable_mask()
        fb = m + 1
        while fb < _panels.RECORDS_PER_DAY:
            if tradable[fb] and day.bid.open[fb] > 0 \
                    and day.ask.open[fb] >= day.bid.open[fb]:
                return fb
            fb += 1
        return None

    def _last_tradable_at_or_before(self, day: _panels.DayPanel,
                                    minute: int) -> Optional[int]:
        tradable = day.tradable_mask()
        for m in range(minute, -1, -1):
            if tradable[m]:
                return m
        return None

    def _leg_share(self, lid: str) -> float:
        total = sum(abs(v) for v in self.leg_desires.values())
        if total == 0:
            return 0.0
        return abs(self.leg_desires.get(lid, 0)) / total

    def _maybe_freeze(self, date: dt.date) -> None:
        if not self.volprof_legs or len(self.day_buffer) < 20:
            return
        freeze_ts = dt.datetime.combine(date, dt.time(20, 0), tzinfo=UTC)
        buf = list(self.day_buffer)
        last = buf[-1]
        if last["date"] == date:
            # PIT: the freeze day is truncated at the 20:00 stamp
            t = last["tradable"][:FREEZE_MIN]
            bh = last["bid_high"][:FREEZE_MIN]
            bl = last["bid_low"][:FREEZE_MIN]
            mc = last["mid_close"][:FREEZE_MIN]
            sl = dict(last)
            sl["mid_close"] = mc
            sl["bid_vol"] = last["bid_vol"][:FREEZE_MIN]
            sl["bid_high"] = bh
            sl["bid_low"] = bl
            sl["tradable"] = t
            if int(t.sum()) >= 1:
                sl["day_high"] = float(bh[t].max())
                sl["day_low"] = float(bl[t].min())
                sl["day_close"] = float(mc[t][-1])
            buf[-1] = sl
        try:
            prof = _legs.build_profile(freeze_ts, buf)
        except _legs.LegError:
            return
        self.profile = prof
        for leg in self.volprof_legs:
            leg.on_profile(prof)

    def _update_prev_agg(self, date: dt.date) -> None:
        if self.day_buffer and self.day_buffer[-1]["date"] == date:
            b = self.day_buffer[-1]
            self.prev_day_agg = {
                "date": date, "high": b["day_high"], "low": b["day_low"],
                "day_close": b["day_close"],
                "last_bid_close": b["last_bid_close"],
                "last_ask_close": b["last_ask_close"],
                "available": dt.datetime.combine(
                    date, dt.time(0, 0), tzinfo=UTC) + dt.timedelta(days=1),
                "close": b["day_close"],
            }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _code_digest() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    lines = []
    for fn in sorted(os.listdir(here)):
        if fn.endswith(".py"):
            blob = open(os.path.join(here, fn), "rb").read()
            lines.append(f"{fn}|{len(blob)}|"
                         f"{hashlib.sha256(blob).hexdigest()}")
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def leak_scan(*texts: str) -> Dict:
    hits = set()
    for text in texts:
        low = text.lower()
        for key in FORBIDDEN_KEYS:
            if key in low:
                hits.add(key)
    return {"keys": sorted(hits), "clean": not hits}


def _dates_between(root: str, start: dt.date, end: dt.date) -> List[dt.date]:
    out = []
    d = start
    while d <= end:
        if os.path.exists(os.path.join(root, "BID", f"{d.isoformat()}.bi5")):
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="PC12A dry run (no PnL)")
    ap.add_argument("--legs", required=True,
                    help="directory of leg config JSONs")
    ap.add_argument("--window", required=True, help="start,end ISO dates")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--tier", type=float, default=1.0,
                    choices=[1.0, 1.5, 2.0])
    args = ap.parse_args(argv)

    t0 = time.time()
    s, e = args.window.split(",")
    args.window_start = dt.date.fromisoformat(s)
    args.window_end = dt.date.fromisoformat(e)
    if args.window_start > args.window_end:
        raise DryRunError("window start after end")

    cfgs = _legs.load_leg_configs(args.legs)
    by_symbol: Dict[str, List[Dict]] = {}
    for c in cfgs:
        by_symbol.setdefault(c["symbol"], []).append(c)

    os.makedirs(args.out, exist_ok=True)
    legs_digest = hashlib.sha256(
        json.dumps(cfgs, sort_keys=True).encode()).hexdigest()
    run_id = hashlib.sha256(
        f"{args.window}|{legs_digest}|{args.tier}".encode()).hexdigest()[:16]

    report: Dict = {
        "schema": REPORT_SCHEMA,
        "cycle_id": "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1",
        "run_id": run_id,
        "window": {"start": s, "end": e},
        "tier": args.tier,
        "legs": {},
        "cost_bill_totals_usd": {"spread_once": 0.0, "slip": 0.0,
                                 "slip_gap_excess": 0.0, "commission": 0.0,
                                 "swap": 0.0},
        "blocked_reason_histogram": {},
        "notes": [
            "cost basis: measured C1 cells + DECLARED U2/U3/U4-U5 bands; "
            "C2 Mon-Thu from the Lane D corrected cells (dual-source law)",
            "swap converted at the accrual-bar mid for JPY-quoted pairs",
            "counts and cost bills only; no performance metric of any "
            "kind is computed or reported (RGC-INC-1)",
        ],
    }
    for c in cfgs:
        lid = c.get("class_candidate_id") or c["corpus_gid"]
        report["legs"][lid] = {
            "decisions": 0, "votes": {}, "fills_by_outcome": {},
            "outcome_exposed_label": c["outcome_exposed_label"],
            "family_id": c["family_id"], "mech_key": c["mech_key"],
            "symbol": c["symbol"],
        }

    journal_path = os.path.join(args.out, "journal.jsonl")
    guard = _pol.CostGuard(_pol.CostGuardState())
    store = _panels.PanelStore()
    data_digests: Dict[str, str] = {}
    with _jr.JournalWriter(journal_path, run_id, meta={
            "window": {"start": s, "end": e}, "tier": args.tier,
            "legs_digest": legs_digest}) as journal:
        for symbol in sorted(by_symbol):
            eng = SymbolEngine(symbol, by_symbol[symbol], args, journal,
                               guard, report)
            eng.run(store)
            data_digests[symbol] = store.panel_digest(
                symbol, _dates_between(store.roots[symbol],
                                       eng._warmup_start(),
                                       args.window_end))
        report["journal_row_count"] = journal.n_rows

    report["code_digest"] = _code_digest()
    report["data_digests"] = data_digests
    report["elapsed_seconds"] = round(time.time() - t0, 3)
    journal_text = open(journal_path, encoding="utf-8").read()
    report["leak_scan"] = leak_scan(journal_text,
                                    json.dumps(report, sort_keys=True))
    with open(os.path.join(args.out, "DRY_RUN_REPORT.json"), "w",
              encoding="utf-8") as fh:
        json.dump(report, fh, sort_keys=True, indent=1)
        fh.write("\n")

    final_text = open(os.path.join(args.out, "DRY_RUN_REPORT.json"),
                      encoding="utf-8").read()
    scan2 = leak_scan(journal_text, final_text)
    if not scan2["clean"]:
        print(f"RGC-INC-1 VIOLATION: forbidden keys {scan2['keys']}",
              file=sys.stderr)
        return 2
    print(json.dumps({"out": args.out,
                      "journal_rows": report["journal_row_count"],
                      "leak_scan_clean": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
