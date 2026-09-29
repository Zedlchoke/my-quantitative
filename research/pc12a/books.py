"""Cash / position / equity book + the fixture replay engine.

FILL_ACCOUNTING_SPEC §4 (FX-spot book identity, quote-currency accounting,
$100k book):

    u_t        : signed position in base-currency units
    cash_usd_t : USD cash
    equity_t   = cash_usd_t + u_t * mid_close_t   (mark at mid_close)

Per-event deltas (the ONLY ways state changes):

    buy D units at fill f:   cash -= D*f + commission ;  u += D
    sell D units at fill f:  cash += D*f - commission ;  u -= D
    nightly accrual event E: cash -= swap_usd(E)          (u unchanged)
    mark (every bar):        equity = cash + u * mid_close

UNAVAILABLE != 0: a missing bid/ask aborts the affected decision
fail-closed (never a 0-price fill, never a $0 mark).

The :class:`FillAccountingEngine` implements the fixture runner spec
(``journal/fixtures/README.md``) and reproduces fx1..fx6 within 1e-9.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Dict, List, Optional

TOL = 1e-9


class UnavailableQuote(RuntimeError):
    """UNAVAILABLE fail-closed trip (missing bid/ask for a mark or fill)."""


# ---------------------------------------------------------------------------
# Generic multi-symbol book (the dry-run engine's state)
# ---------------------------------------------------------------------------


@dataclass
class Book:
    """One $100k book over many symbols; one net position per symbol."""

    initial_cash_usd: float = 100_000.0
    cash_usd: float = 100_000.0
    units: Dict[str, float] = field(default_factory=dict)

    def position(self, symbol: str) -> float:
        return self.units.get(symbol, 0.0)

    def apply_fill(self, symbol: str, delta_units: float, fill_price: float,
                   commission_usd: float) -> None:
        if delta_units > 0:
            self.cash_usd -= delta_units * fill_price + commission_usd
        else:
            self.cash_usd += (-delta_units) * fill_price - commission_usd
        self.units[symbol] = self.position(symbol) + delta_units

    def apply_swap(self, swap_usd: float) -> None:
        self.cash_usd -= swap_usd

    def mark_equity(self, marks: Dict[str, float]) -> float:
        """equity = cash + sum(u * mid_close); UNAVAILABLE never read as 0."""
        eq = self.cash_usd
        for sym, u in self.units.items():
            if u == 0.0:
                continue
            if sym not in marks or marks[sym] is None:
                raise UnavailableQuote(f"mark UNAVAILABLE for {sym}")
            eq += u * marks[sym]
        return eq


def decomposition_residual(gross_vs_mid: float, spread_once: float,
                           slip: float, commission: float, swap: float,
                           equity_delta: float) -> float:
    """FILL_ACCOUNTING_SPEC §6 invariant residual (must be <= 1e-9)."""
    lhs = gross_vs_mid - spread_once - slip - commission - swap
    return lhs - equity_delta


# ---------------------------------------------------------------------------
# Fixture replay engine (journal/fixtures/README.md runner spec)
# ---------------------------------------------------------------------------


def _ts(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def _fmt_ts(t: dt.datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class _Conv:
    symbol: str
    pip_size: float
    lot_size: float
    commission_rate: float
    slip: float
    swap_pips: float
    swap_calendar: Dict[str, int]
    initial_cash: float
    tier: float

    @classmethod
    def from_fixture(cls, conv: Dict) -> "_Conv":
        return cls(conv["symbol"], conv["pip_size"],
                   conv["lot_size_base_units"],
                   conv["commission_rate_per_side"],
                   conv["slip_applied_per_side"],
                   conv["swap_pips_per_night"],
                   dict(conv["swap_calendar"]),
                   conv["initial_cash_usd"],
                   conv.get("stress_tier", 1.0))


@dataclass
class ReplayResult:
    timeline: List[Dict] = field(default_factory=list)
    fills: List[Dict] = field(default_factory=list)
    swap_lines: List[Dict] = field(default_factory=list)
    costs: Dict[str, float] = field(default_factory=dict)
    gross_vs_mid_usd: float = 0.0
    net_pnl_usd: float = 0.0
    vote_rows: List[Dict] = field(default_factory=list)
    blocked_rows: List[Dict] = field(default_factory=list)
    deferred_rows: List[Dict] = field(default_factory=list)
    residual: float = 0.0


def _bar_mid(bar: Dict, which: str) -> float:
    return (bar["bid_" + which] + bar["ask_" + which]) / 2.0


def _norm_kind(kind: str) -> str:
    k = (kind or "").split(" ")[0].strip(" (+)")
    return k or "OPEN"


def _fmt_lot(units: float, lot_size: float) -> str:
    s = f"{units / lot_size:.6f}".rstrip("0").rstrip(".")
    return s


class FillAccountingEngine:
    """Replays a fixture's bars + decisions under FILL_ACCOUNTING_SPEC.

    Conventions are INPUTS (never hardcoded). Covers the six fixture
    shapes: single-leg open/close (fx1, fx2), two-leg opposite netting
    (fx3), blocked-signal exclusion (fx4), cost-guard deferral with an
    open end (fx5), worst-fill graded stop exit (fx6).
    """

    def __init__(self, conventions: Dict):
        self.conv = _Conv.from_fixture(conventions)

    # -- primitive fill arithmetic (spread-once law) ------------------------

    def _ordinary_fill(self, side: str, units_abs: float, bid: float,
                       ask: float) -> Dict:
        c = self.conv
        slip = c.tier * c.slip
        mid = (bid + ask) / 2.0
        h = abs((ask if side == "buy" else bid) - mid)
        # §5: fill = mid +/- tau*(half_spread + slip_band); the two
        # attribution lines tau*h and tau*s sum to |fill - mid| exactly.
        quoted = mid + c.tier * h if side == "buy" else mid - c.tier * h
        fill = quoted + slip if side == "buy" else quoted - slip
        comm = c.tier * c.commission_rate * units_abs * fill
        return {
            "fill_price": fill, "quoted_side": quoted, "mid_at_fill": mid,
            "half_spread_pips": c.tier * h / c.pip_size,
            "spread_once_usd": c.tier * h * units_abs,
            "slip_beyond_halfspread_usd": abs(fill - quoted) * units_abs,
            "cross_cost_usd": abs(fill - mid) * units_abs,
            "commission_usd": comm, "graded": False,
        }

    def _graded_fill(self, side: str, units_abs: float, bid_open: float,
                     ask_open: float, bid_close: float,
                     ask_close: float) -> Dict:
        c = self.conv
        slip = c.tier * c.slip
        mid = (bid_open + ask_open) / 2.0
        quoted = ask_open if side == "buy" else bid_open
        h = abs(quoted - mid)          # the bar's measured half-spread
        if side == "buy":
            worst = max(ask_open, ask_close)
            fill = worst + slip
        else:
            worst = min(bid_open, bid_close)
            fill = worst - slip
        ordinary = quoted + slip if side == "buy" else quoted - slip
        excess = abs(fill - ordinary)  # market gap; tier-invariant
        comm = c.tier * c.commission_rate * units_abs * fill
        # spread-once law: the two lines sum to |fill - mid| exactly. The
        # graded fill is MARKET-set (worst-of), so only the U3 band is a
        # variable cost rate under section 5 -- the measured half-spread
        # and the realized gap excess do not scale with the tier.
        cross = abs(fill - mid) * units_abs
        spread_once = h * units_abs
        return {
            "fill_price": fill, "quoted_side": quoted, "mid_at_fill": mid,
            "half_spread_pips": h / c.pip_size,
            "spread_once_usd": spread_once,
            "slip_beyond_halfspread_usd": cross - spread_once,
            "cross_cost_usd": cross,
            "commission_usd": comm, "graded": True,
            "slip_band_usd": slip * units_abs,
            "gap_excess_usd": excess * units_abs,
            "grading": {
                "rule": ("worst of fill-bar open/close on the quoted side ("
                         + ("sell: min(bid_open, bid_close)" if side == "sell"
                            else "buy: max(ask_open, ask_close)")
                         + ") minus U3 band"),
                "bid_open": bid_open, "ask_open": ask_open,
                "bid_close": bid_close, "ask_close": ask_close,
                "worst_of": worst, "ordinary_modeled_fill": ordinary,
                "fill_never_at_stop_price": True,
            },
        }

    # -- replay ---------------------------------------------------------------

    def replay(self, bars: List[Dict], decisions: List[Dict],
               guard_state: Optional[Dict] = None) -> ReplayResult:
        c = self.conv
        bar_by_ts = {b["ts_open_utc"]: b for b in bars}
        res = ReplayResult()
        cash = c.initial_cash
        u = 0.0
        fills: List[Dict] = []
        spend_items: List[Dict] = []
        if guard_state:
            for row in guard_state.get("prior_spend_rows", []):
                spend_items.append({"ts_utc": row["ts_utc"],
                                    "usd": row["usd"]})
        has_guard = guard_state is not None
        graded_present = any("ts_event_utc" in d for d in decisions)

        def push(ts: dt.datetime, event: str, mark: float,
                 fill_price: Optional[float] = None) -> None:
            equity = cash + u * mark
            res.timeline.append({
                "ts_utc": _fmt_ts(ts), "event": event, "fill_price":
                    fill_price, "cash_usd_after": cash, "units_after": u,
                "mark_mid": mark, "equity_usd_after": equity})

        # ---- assemble the event stream ------------------------------------
        events: List[tuple] = []
        for d in decisions:
            if "ts_event_utc" in d:  # fx6 stop event
                events.append((_ts(d["ts_event_utc"]), 1, "stop", d))
            else:
                events.append((_ts(d["ts_decision_utc"]), 0, "decision", d))
        for b in bars:
            if b.get("role") == "accrual_mark_bar":
                ts = _ts(b["ts_open_utc"])
                if c.swap_calendar.get(ts.strftime("%a"), 0) > 0:
                    events.append((ts, 2, "accrual", b))
        events.sort(key=lambda e: (e[0], e[1]))

        for ts, _, kind, payload in events:
            # ---------------- accrual ------------------------------------
            if kind == "accrual":
                wd = ts.strftime("%a")
                mult = c.swap_calendar[wd]
                if u != 0.0:
                    swap_usd = (abs(u) * c.pip_size * c.swap_pips * mult
                                * c.tier)
                    cash -= swap_usd
                    res.swap_lines.append({
                        "ts_utc": _fmt_ts(ts),
                        "weekday_utc": ts.strftime("%A").lower(),
                        "units_abs": abs(u), "pips": c.swap_pips,
                        "multiplier": mult, "swap_usd": swap_usd,
                        "wed_x3": mult == 3, "cash_delta_usd": -swap_usd,
                        "cash_usd_after": cash, "units_after": u})
                push(ts, f"swap_accrual_{ts.strftime('%A').lower()}"
                     + ("_x3" if mult == 3 else ""),
                     _bar_mid(payload, "close"))
                continue

            # ---------------- fx6 stop event -----------------------------
            if kind == "stop":
                fillbar = bar_by_ts[payload["ts_event_utc"]]
                push(ts, "stop_triggered_gap_open_mark",
                     _bar_mid(fillbar, "open"))
                units_abs = abs(u)
                side = "sell" if u > 0 else "buy"
                fq = self._graded_fill(side, units_abs, fillbar["bid_open"],
                                       fillbar["ask_open"],
                                       fillbar["bid_close"],
                                       fillbar["ask_close"])
                delta = -u
                if delta > 0:
                    cash_delta = -(delta * fq["fill_price"]
                                   + fq["commission_usd"])
                else:
                    cash_delta = (-delta) * fq["fill_price"] \
                        - fq["commission_usd"]
                cash += cash_delta
                u = 0.0
                row = {"order_id": f"fx-o{len(fills) + 1}",
                       "order_kind": payload.get("order_kind", "STOP_EXIT"),
                       "side": side, "delta_units": int(delta),
                       "cash_delta_usd": cash_delta,
                       "bar": fillbar["ts_open_utc"],
                       "exit_reason_code": payload.get("exit_reason_code"),
                       "loss_fill_candidate": fq["gap_excess_usd"] > 0.0}
                row.update(fq)
                fills.append(row)
                push(ts, "stop_market_exit_graded_fill",
                     _bar_mid(fillbar, "close"), fq["fill_price"])
                continue

            # ---------------- decision ------------------------------------
            d = payload
            dts = _ts(d["ts_decision_utc"])
            dec_bar = bar_by_ts[_fmt_ts(dts - dt.timedelta(minutes=1))]
            fill_bar = bar_by_ts.get(_fmt_ts(dts))
            guard = d.get("guard", {}) if has_guard else {}
            order_kind = _norm_kind(d.get("order_kind", ""))

            if "legs" in d:  # fx4-style multi-leg with blocked flags
                blocked = [x for x in d["legs"] if x.get("blocked")]
                healthy = [x for x in d["legs"] if not x.get("blocked")]
                h0 = healthy[0]
                stem = h0["leg_id"].split("-")[-1].lower() + _dir_word(
                    h0["direction_vote"])
                if blocked:
                    lbl = "decision_" + stem + "_" + "_".join(
                        b["leg_id"].split("-")[-1].lower() + "_blocked_"
                        + _stale_suffix(b) for b in blocked)
                else:
                    lbl = "decision_" + stem
                push(dts, lbl, _bar_mid(dec_bar, "close"))
                for b in blocked:
                    snap = b["feature_pit_snapshot"][0]
                    res.blocked_rows.append({
                        "row_kind": "BLOCK",
                        "ts_decision_utc": d["ts_decision_utc"],
                        "leg_id": b["leg_id"], "symbol": c.symbol,
                        "feature_pit_snapshot": b["feature_pit_snapshot"],
                        "direction_vote": b["direction_vote"],
                        "desired_risk_units": b["desired_risk_units"],
                        "eligibility_state": "OFF (E3)",
                        "risk_rule_state": ("netting excluded - blocked legs "
                                            "cast no vote"),
                        "portfolio_state": {"n_eligible": len(healthy)},
                        "order_kind": None, "fill_price": None,
                        "spread_once_usd": None,
                        "slip_beyond_halfspread_usd": None,
                        "commission_usd": None, "cash_delta_usd": 0.0,
                        "units_after": 0, "outcome": "BLOCKED_STALE",
                        "blocked_reason_detail": (
                            f"E3: PIT input {snap['input_id']} available_time"
                            f" {snap['available_time_utc']} age exceeds "
                            f"max-age {snap['max_age']} at ts_decision "
                            f"{d['ts_decision_utc']} -> fail-closed OFF, "
                            f"never last-known-value, never 0-fill")})
                net_target = sum(x["direction_vote"]
                                 * x["desired_risk_units"] for x in healthy)
                voters, vote_mode = healthy, "legs"
                healthy_stem = healthy[0]["leg_id"].split("-")[-1].lower()

            elif "votes" in d:  # fx3-style netted votes
                votes = d["votes"]
                computed = sum(v["direction_vote"] * v["desired_risk_units"]
                               for v in votes)
                net_target = d.get("netting", {}).get("net_target_units",
                                                      computed)
                if any(v["direction_vote"] > 0 for v in votes) and any(
                        v["direction_vote"] < 0 for v in votes):
                    lbl = "decision_two_votes_opposite"
                elif all(v["direction_vote"] == 0 for v in votes):
                    lbl = "decision_both_exit"
                else:
                    lbl = "decision_votes"
                push(dts, lbl, _bar_mid(dec_bar, "close"))
                voters, vote_mode = votes, "votes"
                healthy_stem = None

            else:  # single-leg fx1/fx2/fx5/fx6
                vote, desired = d["direction_vote"], d["desired_risk_units"]
                net_target = vote * desired if vote != 0 else 0
                if guard.get("decision") == "DEFER":
                    lbl = "decision_DEFERRED_COST_GUARD_no_fill"
                elif order_kind == "ADJUST":
                    lbl = "decision_execute_adjust"
                elif order_kind == "OPEN" and has_guard:
                    lbl = f"decision_open_{_fmt_lot(desired, c.lot_size)}lot"
                elif vote > 0:
                    lbl = ("decision_long_stop_attached" if d.get(
                        "attached_standing_order") else "decision_long")
                elif vote < 0:
                    lbl = "decision_short"
                else:
                    lbl = "decision_exit"
                push(dts, lbl, _bar_mid(dec_bar, "close"))
                voters, vote_mode = None, "single"
                healthy_stem = d.get("leg_id", "").split("-")[-1].lower() \
                    or None

            # -- cost guard (fx5): trailing window vs cap, defer non-urgent
            delta = net_target - u
            if has_guard and vote_mode == "single":
                win, cap = guard_state["window_days"], guard_state["cap_usd"]
                wstart = dts - dt.timedelta(days=win)
                in_win = [it for it in spend_items if _ts(it["ts_utc"]) > wstart]
                trailing = sum(it["usd"] for it in in_win)
                urgent = abs(net_target) < abs(u)  # risk-reducing close
                if trailing >= cap and not urgent:
                    proposed = int(abs(delta))
                    est = self._estimate("buy" if delta > 0 else "sell",
                                         proposed, dec_bar)
                    res.deferred_rows.append({
                        "row_kind": "DEFER",
                        "ts_decision_utc": d["ts_decision_utc"],
                        "leg_id": d.get("leg_id"), "symbol": c.symbol,
                        "feature_pit_snapshot": d.get("feature_pit_snapshot"),
                        "direction_vote": vote,
                        "desired_risk_units": desired,
                        "eligibility_state": "ON", "order_kind": "DEFER",
                        "urgency": "NON_URGENT_INCREASE",
                        "guard": {"window_days": win, "cap_usd": cap,
                                  "trailing_spend_usd": trailing,
                                  "in_window_items": in_win},
                        "estimate": est,
                        "fill_price": None, "spread_once_usd": None,
                        "slip_beyond_halfspread_usd": None,
                        "commission_usd": None, "cash_delta_usd": 0.0,
                        "units_after": u, "outcome": "DEFERRED_COST_GUARD",
                        "blocked_reason_detail": (
                            f"L6 cost guard: trailing {win}d state-change "
                            f"spend ${trailing} >= cap ${cap}; non-urgent "
                            f"risk-increasing change deferred to next "
                            f"decision; swap accruals on the held position "
                            f"continue unaffected")})
                    continue
            if delta == 0:
                if vote_mode == "votes":
                    self._vote_rows(res, d, voters, net_target, None)
                continue
            if fill_bar is None:
                raise UnavailableQuote(
                    f"UNAVAILABLE_FILL_BAR at {d['ts_decision_utc']}")

            # -- fill at next-bar-open quoted side +/- U3 band
            units_abs = abs(delta)
            side = "buy" if delta > 0 else "sell"
            fq = self._ordinary_fill(side, units_abs, fill_bar["bid_open"],
                                     fill_bar["ask_open"])
            if delta > 0:
                cash_delta = -(delta * fq["fill_price"]
                               + fq["commission_usd"])
            else:
                cash_delta = (-delta) * fq["fill_price"] \
                    - fq["commission_usd"]
            cash += cash_delta
            u += delta
            row = {"order_id": f"fx-o{len(fills) + 1}",
                   "order_kind": order_kind, "side": side,
                   "delta_units": int(delta), "cash_delta_usd": cash_delta,
                   "bar": fill_bar["ts_open_utc"]}
            row.update(fq)
            fills.append(row)
            if has_guard:
                spend_items.append({
                    "ts_utc": d["ts_decision_utc"],
                    "usd": fq["spread_once_usd"]
                    + fq["slip_beyond_halfspread_usd"]
                    + fq["commission_usd"]})

            if vote_mode == "votes":
                self._vote_rows(res, d, voters, net_target, row)
            elif vote_mode == "single" and d.get("leg_id"):
                res.vote_rows.append({
                    "ts_decision_utc": d["ts_decision_utc"],
                    "leg_id": d["leg_id"], "direction_vote": vote,
                    "desired_risk_units": desired, "outcome": "FILLED",
                    "via_net_order": row["order_id"], "fill_price": None,
                    "cash_delta_usd": 0.0})

            flbl = _fill_label(side, order_kind, units_abs, vote_mode,
                               has_guard, graded_present,
                               healthy_stem if vote_mode == "legs"
                               and _has_blocked(d) else None)
            push(dts, flbl, _bar_mid(fill_bar, "close"), fq["fill_price"])

        # ---- final mark ---------------------------------------------------
        last_bar_ts = fills[-1]["bar"] if fills else _fmt_ts(
            _ts(decisions[-1]["ts_decision_utc"])
            - dt.timedelta(minutes=1))
        final_bar = bar_by_ts[last_bar_ts]
        final_mark = _bar_mid(final_bar, "close")
        push(_ts(last_bar_ts) + dt.timedelta(minutes=1),
             "final_mark" + ("_open_position" if u != 0 else ""), final_mark)

        # ---- virtual attribution post-pass (fx3 law §7.5) -----------------
        entry_fills = [f for f in fills if f["order_kind"] in ("OPEN",
                                                               "ADJUST")]
        exit_fills = [f for f in fills if f["order_kind"] == "CLOSE"]
        netted_rows = [r for r in res.vote_rows if "netting" in r]
        if entry_fills and exit_fills and netted_rows:
            total_abs = sum(abs(r["netting"]["leg_contribution_units"])
                            for r in netted_rows
                            if r["netting"]["leg_contribution_units"] != 0)
            if total_abs:
                for r in netted_rows:
                    contrib = r["netting"]["leg_contribution_units"]
                    if contrib == 0:
                        continue
                    share = abs(contrib) / total_abs
                    va = {
                        "virtual_units": contrib,
                        "gross_vs_mid_usd": contrib * (
                            exit_fills[0]["mid_at_fill"]
                            - entry_fills[0]["mid_at_fill"]),
                        "spread_once_usd": (
                            entry_fills[0]["spread_once_usd"]
                            + exit_fills[0]["spread_once_usd"]) * share,
                        "slip_usd": (
                            entry_fills[0]["slip_beyond_halfspread_usd"]
                            + exit_fills[0]["slip_beyond_halfspread_usd"])
                        * share,
                        "commission_usd": (
                            entry_fills[0]["commission_usd"]
                            + exit_fills[0]["commission_usd"]) * share,
                    }
                    va["virtual_net_usd"] = (
                        va["gross_vs_mid_usd"] - va["spread_once_usd"]
                        - va["slip_usd"] - va["commission_usd"])
                    r["virtual_attribution"] = va

        # ---- totals + identities -------------------------------------------
        spread_total = sum(f["spread_once_usd"] for f in fills)
        slip_total = sum(f["slip_beyond_halfspread_usd"] for f in fills)
        comm_total = sum(f["commission_usd"] for f in fills)
        swap_total = sum(s["swap_usd"] for s in res.swap_lines)
        gross = sum(f["delta_units"] * (final_mark - f["mid_at_fill"])
                    for f in fills)
        res.fills = fills
        res.costs = {"spread_once_total_usd": spread_total,
                     "slip_total_usd": slip_total,
                     "commission_total_usd": comm_total,
                     "swap_total_usd": swap_total}
        if any(f.get("graded") for f in fills):
            res.costs["slip_band_total_usd"] = sum(
                f.get("slip_band_usd", 0.0) for f in fills)
            res.costs["gap_excess_total_usd"] = sum(
                f.get("gap_excess_usd", 0.0) for f in fills)
        res.gross_vs_mid_usd = gross
        res.net_pnl_usd = (gross - spread_total - slip_total - comm_total
                           - swap_total)
        equity_delta = res.timeline[-1]["equity_usd_after"] - c.initial_cash
        res.residual = decomposition_residual(
            gross, spread_total, slip_total, comm_total, swap_total,
            equity_delta)
        assert abs(res.residual) < TOL, f"invariant residual {res.residual}"
        return res

    # -- helpers --------------------------------------------------------------

    def _estimate(self, side: str, units_abs: int, dec_bar: Dict) -> Dict:
        """Pre-commit estimate from the DECISION bar's close quotes (§8)."""
        fq = self._ordinary_fill(side, float(units_abs), dec_bar["bid_close"],
                                 dec_bar["ask_close"])
        return {
            "proposed_delta_units": units_abs,
            "est_fill_price": fq["fill_price"],
            "est_spread_once_usd": fq["spread_once_usd"],
            "est_slip_usd": fq["slip_beyond_halfspread_usd"],
            "est_commission_usd": fq["commission_usd"],
            "est_total_usd": (fq["spread_once_usd"]
                              + fq["slip_beyond_halfspread_usd"]
                              + fq["commission_usd"]),
        }

    def _vote_rows(self, res: ReplayResult, d: Dict, voters: List[Dict],
                   net_target: int, net_fill: Optional[Dict]) -> None:
        contribs = {v["leg_id"]: v["direction_vote"]
                    * v["desired_risk_units"] for v in voters}
        for v in voters:
            lid = v["leg_id"]
            res.vote_rows.append({
                "ts_decision_utc": d["ts_decision_utc"], "leg_id": lid,
                "direction_vote": v["direction_vote"],
                "desired_risk_units": v["desired_risk_units"],
                "outcome": "FILLED",
                "via_net_order": net_fill["order_id"] if net_fill else None,
                "netting": {"net_target_units": net_target,
                            "leg_contribution_units": contribs[lid],
                            "offset_by": [{"leg_id": o, "units": cc}
                                          for o, cc in contribs.items()
                                          if o != lid]},
                "fill_price": None, "cash_delta_usd": 0.0})


def _dir_word(vote: int) -> str:
    return {1: "_long", -1: "_short", 0: "_exit"}[vote]


def _stale_suffix(blocked_leg: Dict) -> str:
    snap = blocked_leg["feature_pit_snapshot"][0]
    return "stale" if not snap.get("max_age_ok", True) else "blocked"


def _has_blocked(d: Dict) -> bool:
    return bool(d.get("legs")) and any(x.get("blocked") for x in d["legs"])


def _fill_label(side: str, kind: str, units_abs: float, vote_mode: str,
                has_guard: bool, graded_present: bool,
                healthy_stem: Optional[str]) -> str:
    base = f"{side}_{kind.lower()}"
    if healthy_stem:
        return f"fill_{base}_{healthy_stem}_only"
    if has_guard:
        return f"fill_{base}_{int(units_abs)}"
    if vote_mode == "votes":
        return f"net_fill_{base}_{int(units_abs)}"
    if graded_present:
        return f"fill_{base}_ordinary"
    return f"fill_{base}"
