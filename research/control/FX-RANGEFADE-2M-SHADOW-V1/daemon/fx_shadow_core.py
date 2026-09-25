"""Pure core for the RANGEFADE-2M shadow (no network, no I/O side effects
beyond what the caller passes in) — extracted so the self-tests exercise
the REAL restart/bar logic, not a function compared with itself.

Laws implemented here (PLAN_fx_rangefade_2m_shadow_v1.md + owner orders
2026-09-24):

- ONE shared $100,000 account for BOTH pairs; per-pair numbers are
  CONTRIBUTIONS (pnl, fills, gross exposure), never a second seed.
- Restart identity: shadow_journal.jsonl is the immutable source of
  truth — position, entry, realized PnL, fill count and the committed
  H1 bars (beyond the seed corpus) are REPLAYED from it, never
  invented, never double-counted (events carry seq; replay is
  idempotent under duplication of whole events).
- PIT H1 bars: a bar with hour floor h0 contains ONLY ticks with
  h0 <= ts < h0+3600; decisions are computed on CLOSED bars only;
  fills happen at the live opposite quote of the bar that just opened
  (long opens buy at ask, short opens sell at bid; closes symmetric).
- Fail-closed: marks older than STALE_SEC mean no decisions; PnL today
  = realized-since-UTC-midnight + unrealized NOW (book is always flat
  at UTC midnight by the 20:00 force-flat law, so the unrealized
  anchor at the day boundary is 0 BY CONSTRUCTION and this is stated
  in the state file rather than assumed silently).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

HOUR = 3600
LOTS = 1.5
SEED_EQUITY = 100_000.0
DOLLARS_PER_PIP_PER_LOT = 10.0


def floor_hour(ts: float) -> int:
    """PIT hour bucket of a unix timestamp (int seconds)."""
    return int(ts) // HOUR * HOUR


def pnl_of(pos: int, entry_px: float, exit_px: float, pip: float) -> float:
    """USD PnL for `pos` (+1/-1) units of 1.5 lots closing at exit_px."""
    return (exit_px - entry_px) * pos * LOTS / pip * DOLLARS_PER_PIP_PER_LOT


class LiveBar:
    """One forming H1 bar built from BID for b_* and ASK for a_*.

    b_h/b_l track the bid high/low only (the seed corpus' b_* columns
    are bid-derived); a_o/a_c carry the ask open/close. A tick belongs
    to the bar whose hour floor matches its OWN quote timestamp, never
    the receiver's wall clock.
    """

    __slots__ = ("ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_c")

    def __init__(self, ts: int, bid: float, ask: float):
        self.ts = int(ts)
        self.b_o = self.b_h = self.b_l = self.b_c = float(bid)
        self.a_o = self.a_c = float(ask)

    def update(self, bid: float, ask: float) -> None:
        self.b_h = max(self.b_h, float(bid))
        self.b_l = min(self.b_l, float(bid))
        self.b_c = float(bid)
        self.a_c = float(ask)

    def as_row(self) -> Dict[str, Any]:
        return {"ts": self.ts, "b_o": self.b_o, "b_h": self.b_h,
                "b_l": self.b_l, "b_c": self.b_c, "a_o": self.a_o,
                "a_c": self.a_c}


# ----------------------------------------------------------------------
# Journal replay — the restart identity mechanism
# ----------------------------------------------------------------------
def event_id(seq: int, ts: str, event: str, pair: str = "") -> str:
    raw = f"{seq}|{ts}|{event}|{pair}"
    return "fx" + hashlib.sha256(raw.encode()).hexdigest()[:12]


def replay_journal(
    lines: Iterable[str],
    seed_last_ts: Optional[Mapping[str, int]] = None,
) -> Dict[str, Any]:
    """Rebuild account state from journal bytes. Idempotent: repeated
    identical events collapse by (pair, event-kind, ts/entry_ts, px);
    unknown or malformed lines are skipped and counted, never fatal.

    Returns dict with:
      pairs: {pair: {pos, entry_px, entry_ts, realized_usd, fills,
                     bars: {ts: row}}}  (bars beyond seed_last_ts only)
      realized_usd: total across pairs
      realized_today_utc: {day_key: realized}
      bars_restored, events_read, events_bad, events_dup
    """
    seed_last_ts = dict(seed_last_ts or {})
    pairs: Dict[str, Dict[str, Any]] = {}
    seen: set = set()
    totals = {"realized_usd": 0.0, "events_read": 0, "events_bad": 0,
              "events_dup": 0, "bars_restored": 0}
    realized_today: Dict[str, float] = {}

    def pair_state(pair: str) -> Dict[str, Any]:
        return pairs.setdefault(pair, {
            "pos": 0, "entry_px": None, "entry_ts": None,
            "realized_usd": 0.0, "fills": 0, "bars": {},
        })

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        totals["events_read"] += 1
        try:
            rec = json.loads(line)
        except ValueError:
            totals["events_bad"] += 1
            continue
        if not isinstance(rec, Mapping):
            totals["events_bad"] += 1
            continue
        event = rec.get("event")
        ts = str(rec.get("ts") or "")
        if event in ("parity_selftest", "shadow_start", "boot_replay",
                     "day_roll", "day_anchor", "seq_probe"):
            continue
        pair = str(rec.get("pair") or "")
        if not pair:
            totals["events_bad"] += 1
            continue
        st = pair_state(pair)
        key = None
        if event == "fill_open":
            key = ("open", pair, rec.get("entry_ts"), rec.get("entry_px"))
        elif event in ("fill_close", "force_flat"):
            key = ("close", pair, ts, rec.get("exit_px"))
        elif event == "bar_closed":
            key = ("bar", pair, rec.get("bar_ts"))
        else:
            totals["events_bad"] += 1
            continue
        if key in seen:
            totals["events_dup"] += 1
            continue
        seen.add(key)

        if event == "fill_open":
            st["pos"] = int(rec.get("dir") or 0)
            st["entry_px"] = rec.get("entry_px")
            st["entry_ts"] = rec.get("entry_ts")
            st["fills"] += 1
        elif event in ("fill_close", "force_flat"):
            pnl = float(rec.get("pnl_usd") or 0.0)
            st["realized_usd"] += pnl
            totals["realized_usd"] += pnl
            day = ts[:10]
            realized_today[day] = realized_today.get(day, 0.0) + pnl
            st["pos"] = 0
            st["entry_px"] = None
            st["entry_ts"] = None
        elif event == "bar_closed":
            bar_ts = int(rec.get("bar_ts") or 0)
            last = seed_last_ts.get(pair)
            if bar_ts and (last is None or bar_ts > last):
                st["bars"][bar_ts] = {
                    "ts": bar_ts,
                    "b_o": rec.get("b_o"), "b_h": rec.get("b_h"),
                    "b_l": rec.get("b_l"), "b_c": rec.get("b_c"),
                    "a_o": rec.get("a_o"), "a_c": rec.get("a_c"),
                }
                totals["bars_restored"] += 1

    return {
        "pairs": pairs,
        "realized_usd": totals["realized_usd"],
        "realized_by_day_utc": dict(sorted(realized_today.items())),
        "bars_restored": totals["bars_restored"],
        "events_read": totals["events_read"],
        "events_bad": totals["events_bad"],
        "events_dup": totals["events_dup"],
    }


def account_block(
    realized_usd: float,
    unrealized_usd: float,
    realized_today: float,
    gross_exposure_usd: float,
    marks_fresh: bool,
) -> Dict[str, Any]:
    """THE single $100k account view; sleeves are contributions only."""
    equity = SEED_EQUITY + realized_usd + unrealized_usd
    return {
        "seed_equity": SEED_EQUITY,
        "equity": round(equity, 2) if marks_fresh else None,
        "pnl_total": round(realized_usd + unrealized_usd, 2),
        "pnl_total_pct": round((realized_usd + unrealized_usd) / SEED_EQUITY * 100, 3),
        "realized_usd": round(realized_usd, 2),
        "unrealized_usd": round(unrealized_usd, 2),
        # PnL hôm nay = realized since UTC midnight + unrealized NOW.
        # Anchor stated: the book is FLAT at every UTC midnight by the
        # 20:00 force-flat law, so the unrealized part of the anchor is
        # zero by construction (not silently assumed — disclosed here).
        "pnl_today_anchor_utc": "00:00 UTC, book flat by force-flat law",
        "pnl_today": round(realized_today + unrealized_usd, 2)
        if marks_fresh else None,
        "realized_today": round(realized_today, 2),
        "gross_exposure_usd": round(gross_exposure_usd, 2),
        "capital_in_use_pct": round(gross_exposure_usd / SEED_EQUITY * 100, 2),
    }


# ======================================================================
# A1-controls (amendment FX-RANGEFADE-2M-SHADOW-V1, owner GO consumed
# 2026-09-25T04:21:15Z) — PARALLEL books + reporting only.
#
# LAW (amendment §1/§3): the sleeve decision path (signal, fills, size,
# force-flat) is FROZEN; nothing below feeds back into it. Every function
# here is either an independent virtual book driven by OBSERVED sleeve
# state, or a reporting/cost view.
# ======================================================================

SESSION_BUCKETS_UTC = (  # SEED convention; replaced only with the census
    ("Asia", 0, 7), ("London", 7, 12), ("Overlap", 12, 16),
    ("NY", 16, 21), ("Rollover", 21, 24),
)
SHORT_BETA_LABEL = "SHORT_BETA_UNSEPARATED — NOT PROMOTABLE"
NOT_RUN_COST_FIELDS = "NOT_RUN_COST_FIELDS"

#: AMENDMENT A1 metadata patch (owner-approved preparation 2026-09-25;
#: restart NOT yet authorized): the activation milestone in state is
#: DERIVED, never a static placeholder. Authority order (owner law):
#: T_ctrl comes from A1_ACTIVATION.json (phase_a.t_ctrl_utc); the journal
#: cost_book row timestamp is CROSS-CHECK EVIDENCE ONLY and is never
#: silently substituted for T_ctrl. Missing / malformed / contradictory
#: artifact => FAIL-CLOSED (no ACTIVATED claim; label stays UNSEPARATED).
ACTIVATION_SKEW_TOLERANCE_S = 300.0

def derive_a1_activation(activation_artifact, journal_cost_book_ts):
    """Pure derivation of the a1_controls activation metadata block.

    activation_artifact: parsed A1_ACTIVATION.json dict (or None/missing).
    journal_cost_book_ts: ISO ts string of the boot cost_book journal row.
    Returns a dict with phase / T_ctrl / cross_check; deterministic and
    idempotent for identical inputs (restart-safe).
    """
    def fail(reason, detail=""):
        return {
            "phase": "ACTIVATION_UNVERIFIED_FAIL_CLOSED",
            "T_ctrl": None,
            "activation_source": "A1_ACTIVATION.json",
            "cross_check": {"reason": reason, "detail": detail,
                            "verdict": "FAIL_CLOSED"},
            "note": ("fail-closed: no ACTIVATED claim; sleeve label stays "
                     "SHORT_BETA_UNSEPARATED — NOT PROMOTABLE"),
        }

    if not isinstance(activation_artifact, dict):
        return fail("ARTIFACT_MISSING_OR_UNREADABLE")
    t_ctrl = (activation_artifact.get("phase_a") or {}).get("t_ctrl_utc")
    if not isinstance(t_ctrl, str) or not t_ctrl.endswith("Z"):
        return fail("ARTIFACT_MALFORMED_NO_T_CTRL", repr(t_ctrl)[:60])
    if not journal_cost_book_ts:
        return fail("JOURNAL_COST_BOOK_ROW_MISSING")
    import datetime as _dt
    def _p(x):
        return _dt.datetime.fromisoformat(str(x).replace("+00:00", "Z").replace("Z", "+00:00"))
    try:
        skew = (_p(journal_cost_book_ts) - _p(t_ctrl)).total_seconds()
    except Exception as exc:
        return fail("TIMESTAMP_PARSE_ERROR", str(exc)[:80])
    if skew < 0:
        return fail("JOURNAL_ROW_PRECEDES_ARTIFACT_T_CTRL",
                    f"cost_book {journal_cost_book_ts} < T_ctrl {t_ctrl}")
    if skew > ACTIVATION_SKEW_TOLERANCE_S:
        return fail("SKEW_EXCEEDS_TOLERANCE", f"skew {skew}s > {ACTIVATION_SKEW_TOLERANCE_S}s")
    return {
        "phase": "ACTIVATED",
        "T_ctrl": t_ctrl,
        "activation_source": "A1_ACTIVATION.json (authority; journal row is "
                             "cross-check evidence only, never substituted)",
        "cross_check": {"journal_cost_book_ts": journal_cost_book_ts,
                        "skew_s": skew, "verdict": "CONSISTENT"},
    }

def short_beta_label_for(ctrl_emitted, activation_block, first_ctrl_ts):
    """Label law: UNSEPARATED until control records exist AND activation
    is verified; then ACCRUING (never a victory claim — interpretation is
    gated on the preregistered decision-count law)."""
    if not ctrl_emitted:
        return SHORT_BETA_LABEL
    if not activation_block or activation_block.get("phase") != "ACTIVATED":
        return SHORT_BETA_LABEL  # fail-closed direction
    return ("SHORT_BETA_SEPARATION_ACCRUING (control records since "
            f"{first_ctrl_ts or "T_ctrl"}; interpretation gated on "
            "preregistered decision-count law — no FX-vs-control conclusion)")
COST_ROW_FIELDS = ("fee_bps", "slip_pips", "spread_at_fill", "session_bucket",
                   "cost_book_digest", "stress_fee", "stress_slip",
                   "round_trip_id", "realized_net")
COST_ROW_FIELDS_OPEN = COST_ROW_FIELDS[:-1]  # realized_net lands at close
COST_ROW_FIELDS_CLOSE = COST_ROW_FIELDS
CONTRACT_SIZE = 100_000.0  # notional USD per 1.0 lot (same book as sleeve)
CTRL_SHORT_ALWAYS = "ctrl_short_always"
CTRL_SHADOW_MATCHED = "ctrl_shadow_matched"
CTRL_EVENTS = ("ctrl_open", "ctrl_close")
EPOCH_REPORT_EVENT = "epoch_report"
# Journal event kinds that carry NO sleeve-accounting semantics: the boot
# replay FILTERS these out before replay_journal (which stays byte-frozen)
# so they neither pollute sleeve state nor count as events_bad.
A1_IGNORED_BY_SLEEVE_REPLAY = (EPOCH_REPORT_EVENT, "cost_book",
                               "short_beta_label") + CTRL_EVENTS


def session_bucket_of_hour(hour_utc: int) -> str:
    """Session bucket of a UTC hour (0..23). SEED convention, dated in
    session_spread_curve.json; replaced only with the sha-pinned census."""
    for name, h0, h1 in SESSION_BUCKETS_UTC:
        if h0 <= hour_utc < h1:
            return name
    raise ValueError(f"hour_utc out of range: {hour_utc!r}")


def session_bucket_of_epoch(epoch_s: int) -> str:
    return session_bucket_of_hour((int(epoch_s) // HOUR) % 24)


def is_weekday_utc(epoch_s: int) -> bool:
    """Mon..Fri UTC (epoch day 0 = 1970-01-01 = Thursday)."""
    return ((int(epoch_s) // 86400) + 3) % 7 < 5


def fill_allowed_open(new_bar_hour_utc: int) -> bool:
    """THE sleeve fill law, restated for the control arms (amendment:
    controls use the identical fill law). A fill may execute at the open of
    the bar that just opened only when the just-CLOSED bar's hour <= 18
    (shadow_daemon main loop + desired_now: no fills at closed hour >= 19,
    i.e. the 00:00 UTC open is NOT fillable, the last fillable open is the
    19:00 bar). Derived identity: closed hour = (new_bar_hour - 1) % 24."""
    return ((int(new_bar_hour_utc) - 1) % 24) <= 18


def cost_field_status(row: Mapping) -> str:
    """Append-only schema law (amendment §1.4): rows written before T_ctrl
    never gain the cost fields; their absence is NOT_RUN_COST_FIELDS,
    never zero, and old rows are never backfilled. Open rows require the
    per-fill fields; close/flat rows additionally carry the round-trip
    aggregate realized_net."""
    need = (COST_ROW_FIELDS_CLOSE if "exit_px" in row
            else COST_ROW_FIELDS_OPEN)
    return "OK" if all(k in row for k in need) else NOT_RUN_COST_FIELDS


class CostBook:
    """The single pinned cost book loaded from session_spread_curve.json
    (single source, digest-pinned; amendment §2). Measured components:
    spread-at-fill + session census curve (SEED until the sha-pinned
    census). Declared components: fee_bps/slip_pips, clearly labeled,
    never override the measured book (umbrella cost law)."""

    def __init__(self, cfg: Mapping, digest: str, path: str):
        self.cfg = dict(cfg)
        self.digest = digest
        self.path = str(path)
        sched = cfg["declared_fee_schedule"]
        self.fee_bps = float(sched["fee_bps_per_side"])
        self.slip_pips = float(sched["slip_pips_per_side"])
        self.stress_multiplier = float(cfg["stress_multiplier"])

    @classmethod
    def from_file(cls, path) -> "CostBook":
        raw = Path(path).read_bytes()
        digest = "sha256:" + hashlib.sha256(raw).hexdigest()[:16]
        return cls(json.loads(raw.decode()), digest, str(path))

    def median_pips(self, pair: str, bucket: str) -> float:
        return float(self.cfg["session_median_pips"][pair][bucket])

    def stress_pips(self, pair: str, bucket: str) -> float:
        """Stress-book spread for the fill's bucket (median x tier, lane-F
        frozen x2.0). Parallel reporting view ONLY — never primary PnL."""
        return self.median_pips(pair, bucket) * self.stress_multiplier

    def fee_usd(self, px: float, lots: float = LOTS) -> float:
        return px * lots * CONTRACT_SIZE * self.fee_bps / 1e4

    def slip_usd(self, pips: float, lots: float = LOTS) -> float:
        return pips * DOLLARS_PER_PIP_PER_LOT * lots

    def declared_side_cost_usd(self, px: float) -> float:
        return self.fee_usd(px) + self.slip_usd(self.slip_pips)

    def fill_cost_fields(self, pair: str, bucket: str, spread_pips: float,
                         px: float) -> Dict[str, Any]:
        """Per-fill cost row fields (amendment §1.4), same book for the
        sleeve and both control arms. stress_fee = the declared fee in USD
        (fees do not change under stress); stress_slip = the x2.0 session
        spread in USD for ONE side."""
        fee_usd = self.fee_usd(px)
        return {
            "fee_bps": self.fee_bps,
            "slip_pips": self.slip_pips,
            "spread_at_fill": round(float(spread_pips), 2),
            "session_bucket": bucket,
            "cost_book_digest": self.digest,
            "stress_fee": round(fee_usd, 2),
            "stress_slip": round(self.slip_usd(self.stress_pips(pair, bucket)), 2),
        }

    def summary(self) -> Dict[str, Any]:
        sched = self.cfg["declared_fee_schedule"]
        return {
            "path": self.path,
            "digest": self.digest,
            "status": self.cfg.get("status"),
            "stress_multiplier": self.stress_multiplier,
            "declared_fee_schedule": {
                "class": sched.get("class"),
                "fee_bps_per_side": self.fee_bps,
                "slip_pips_per_side": self.slip_pips,
            },
            "session_median_pips": self.cfg["session_median_pips"],
            "buckets_utc": {n: [h0, h1] for n, h0, h1 in SESSION_BUCKETS_UTC},
        }


def _rt_id(arm: str, pair: str, epoch: int, px: float) -> str:
    raw = f"{arm}|{pair}|{int(epoch)}|{px!r}"
    return "rt" + hashlib.sha256(raw.encode()).hexdigest()[:12]


class CtrlShortAlwaysBook:
    """C-FX-1 arm 1 — CTRL-SHORT-ALWAYS, the DAY-SESSION construct.

    Per pair, a parallel VIRTUAL book (paper class, NO orders): short LOTS
    from the first FILLABLE H1 open after 00:00 UTC each weekday (fillable
    = the sleeve's own fill law: opens at new-bar hours 01..19 UTC), force-
    flat at the sleeve's own 20:00 UTC boundary, weekends never open (the
    daily force-flat keeps the book flat across the weekend by
    construction). Costed with the SAME cost book and the SAME opposite-
    quote rule as the sleeve (short opens sell at bid, covers buy at ask).

    COMPARABILITY LAW (amendment §1.1, binding): this is a day-session
    book; the ancestor's +314.0-pips SHORT_ALWAYS reference (EURUSD-OPEN-
    SEARCH-V2 bf4f07f1, holdout) was a WINDOW-LONG construct — the two are
    NOT numerically comparable. The ancestor number is cited only as the
    REASON this control is mandatory.
    """

    arm = CTRL_SHORT_ALWAYS

    def __init__(self, pair: str, pip: float):
        self.pair, self.pip = pair, pip
        self.pos = 0                      # 0 or -1 (LOTS units sign)
        self.entry_px = None
        self.entry_epoch = None
        self.entry_bucket = None
        self.rt_id = None
        self.open_day = None              # UTC day number already opened
        self.realized_gross_usd = 0.0
        self.realized_net_usd = 0.0       # primary basis (declared costs)
        self.realized_stress_usd = 0.0    # parallel stress view
        self.fills = 0

    def on_h1_open(self, bar_open_epoch: int, bid: float, ask: float,
                   cost_book: CostBook, spread_pips: float) -> Optional[dict]:
        """Offer the open of the bar that just opened (observed, PIT)."""
        hour = (int(bar_open_epoch) // HOUR) % 24
        day = int(bar_open_epoch) // 86400
        if self.pos != 0 or self.open_day == day:
            return None
        if not is_weekday_utc(bar_open_epoch) or not fill_allowed_open(hour):
            return None
        px = float(bid)                   # short opens SELL at bid
        self.pos, self.entry_px, self.entry_epoch = -1, px, int(bar_open_epoch)
        self.entry_bucket = session_bucket_of_epoch(bar_open_epoch)
        self.open_day = day
        self.rt_id = _rt_id(self.arm, self.pair, bar_open_epoch, px)
        self.fills += 1
        ev = {"arm": self.arm, "pair": self.pair, "dir": self.pos,
              "entry_px": px, "entry_ts": int(bar_open_epoch), "lots": LOTS,
              "round_trip_id": self.rt_id}
        ev.update(cost_book.fill_cost_fields(
            self.pair, self.entry_bucket, spread_pips, px))
        return ev

    def force_flat(self, flat_epoch: int, bid: float, ask: float,
                   cost_book: CostBook, spread_pips: float) -> Optional[dict]:
        """Close at the sleeve's 20:00 UTC boundary (or a caught-up missed
        boundary): short covers BUY at ask — same opposite-quote rule."""
        if self.pos == 0:
            return None
        return self._close(float(ask), int(flat_epoch), cost_book,
                           spread_pips, reason="force_flat")

    def _close(self, px: float, epoch: int, cost_book: CostBook,
               spread_pips: float, reason: str) -> dict:
        gross = pnl_of(self.pos, self.entry_px, px, self.pip)
        entry_bucket = self.entry_bucket
        exit_bucket = session_bucket_of_epoch(epoch)
        fee_e = cost_book.fee_usd(self.entry_px)
        fee_x = cost_book.fee_usd(px)
        slip_e = cost_book.slip_usd(cost_book.slip_pips)
        slip_x = cost_book.slip_usd(cost_book.slip_pips)
        sst_e = cost_book.slip_usd(cost_book.stress_pips(self.pair, entry_bucket))
        sst_x = cost_book.slip_usd(cost_book.stress_pips(self.pair, exit_bucket))
        net = gross - fee_e - slip_e - fee_x - slip_x
        stress = gross - fee_e - sst_e - fee_x - sst_x
        self.realized_gross_usd += gross
        self.realized_net_usd += net
        self.realized_stress_usd += stress
        ev = {"arm": self.arm, "pair": self.pair, "dir": self.pos,
              "entry_px": self.entry_px, "exit_px": px, "exit_ts": epoch,
              "lots": LOTS, "reason": reason,
              "pnl_usd": round(gross, 2),
              "realized_net": round(net, 2),
              "realized_net_stress": round(stress, 2),
              "round_trip_id": self.rt_id,
              "realized_total_net": round(self.realized_net_usd, 2)}
        ev.update(cost_book.fill_cost_fields(self.pair, exit_bucket,
                                             spread_pips, px))
        self.pos, self.entry_px, self.entry_epoch = 0, None, None
        self.entry_bucket, self.rt_id = None, None
        return ev


class CtrlShadowMatchedBook:
    """C-FX-1 arm 2 — CTRL-SHADOW-MATCHED: the umbrella §5.7 inverted
    control. Decisions IDENTICAL to the sleeve's (same fill px, same
    timestamps, same exits) with the sign INVERTED at entry only; exits
    are applied as-is (not re-inverted). Pure mirror: the daemon OBSERVES
    sleeve transitions and replays them here inverted — the sleeve path
    itself is never touched."""

    arm = CTRL_SHADOW_MATCHED

    def __init__(self, pair: str, pip: float):
        self.pair, self.pip = pair, pip
        self.pos = 0
        self.entry_px = None
        self.entry_epoch = None
        self.entry_bucket = None
        self.rt_id = None
        self.realized_gross_usd = 0.0
        self.realized_net_usd = 0.0
        self.realized_stress_usd = 0.0
        self.fills = 0

    def on_sleeve_open(self, sleeve_dir: int, fill_px: float,
                       fill_epoch: int, cost_book: CostBook,
                       spread_pips: float) -> Optional[dict]:
        """Mirror the sleeve's open with the sign inverted at the SAME px."""
        if sleeve_dir == 0 or self.pos != 0:
            return None
        px = float(fill_px)
        self.pos = -int(sleeve_dir)
        self.entry_px, self.entry_epoch = px, int(fill_epoch)
        self.entry_bucket = session_bucket_of_epoch(fill_epoch)
        self.rt_id = _rt_id(self.arm, self.pair, fill_epoch, px)
        self.fills += 1
        ev = {"arm": self.arm, "pair": self.pair, "dir": self.pos,
              "mirrors_sleeve_dir": int(sleeve_dir),
              "entry_px": px, "entry_ts": int(fill_epoch), "lots": LOTS,
              "round_trip_id": self.rt_id}
        ev.update(cost_book.fill_cost_fields(
            self.pair, self.entry_bucket, spread_pips, px))
        return ev

    def on_sleeve_close(self, exit_px: float, exit_epoch: int,
                        cost_book: CostBook, spread_pips: float) -> Optional[dict]:
        """Mirror the sleeve's exit IDENTICALLY (same px, not re-inverted)."""
        if self.pos == 0:
            return None
        gross = pnl_of(self.pos, self.entry_px, float(exit_px), self.pip)
        entry_bucket, exit_bucket = self.entry_bucket, session_bucket_of_epoch(exit_epoch)
        fee_e, fee_x = cost_book.fee_usd(self.entry_px), cost_book.fee_usd(float(exit_px))
        slip_e = cost_book.slip_usd(cost_book.slip_pips)
        sst_e = cost_book.slip_usd(cost_book.stress_pips(self.pair, entry_bucket))
        sst_x = cost_book.slip_usd(cost_book.stress_pips(self.pair, exit_bucket))
        net = gross - fee_e - slip_e - fee_x - slip_e
        stress = gross - fee_e - sst_e - fee_x - sst_x
        self.realized_gross_usd += gross
        self.realized_net_usd += net
        self.realized_stress_usd += stress
        ev = {"arm": self.arm, "pair": self.pair, "dir": self.pos,
              "entry_px": self.entry_px, "exit_px": float(exit_px),
              "exit_ts": int(exit_epoch), "lots": LOTS, "reason": "signal",
              "pnl_usd": round(gross, 2),
              "realized_net": round(net, 2),
              "realized_net_stress": round(stress, 2),
              "round_trip_id": self.rt_id,
              "realized_total_net": round(self.realized_net_usd, 2)}
        ev.update(cost_book.fill_cost_fields(self.pair, exit_bucket,
                                             spread_pips, float(exit_px)))
        self.pos, self.entry_px, self.entry_epoch = 0, None, None
        self.entry_bucket, self.rt_id = None, None
        return ev


def ctrl_book_state(book) -> Dict[str, Any]:
    """Serializable state of a control book (state file + replay)."""
    return {"arm": book.arm, "pair": book.pair, "pos": book.pos,
            "entry_px": book.entry_px, "entry_epoch": book.entry_epoch,
            "open_day": getattr(book, "open_day", None),
            "realized_gross_usd": round(book.realized_gross_usd, 2),
            "realized_net_usd": round(book.realized_net_usd, 2),
            "realized_stress_usd": round(book.realized_stress_usd, 2),
            "fills": book.fills}


def restore_ctrl_book(book, st: Mapping) -> None:
    book.pos = int(st.get("pos") or 0)
    book.entry_px = st.get("entry_px")
    book.entry_epoch = st.get("entry_epoch")
    book.entry_bucket = st.get("entry_bucket")
    book.rt_id = st.get("rt_id")
    if hasattr(book, "open_day"):
        book.open_day = st.get("open_day")
    book.realized_gross_usd = float(st.get("realized_gross_usd") or 0.0)
    book.realized_net_usd = float(st.get("realized_net_usd") or 0.0)
    book.realized_stress_usd = float(st.get("realized_stress_usd") or 0.0)
    book.fills = int(st.get("fills") or 0)


def replay_control_events(lines: Iterable[str]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Restart identity for the CONTROL books, WITHOUT touching the frozen
    sleeve replay: scans only ctrl_open/ctrl_close rows (idempotent under
    duplication by the same collapse rule as replay_journal). Returns
    {arm: {pair: {pos, entry_px, entry_epoch, entry_bucket, rt_id,
                  open_day, realized_gross_usd, realized_net_usd,
                  realized_stress_usd, fills}}}."""
    books: Dict[str, Dict[str, Dict[str, Any]]] = {}
    seen: set = set()

    def st(arm: str, pair: str) -> Dict[str, Any]:
        return books.setdefault(arm, {}).setdefault(pair, {
            "pos": 0, "entry_px": None, "entry_epoch": None,
            "entry_bucket": None, "rt_id": None, "open_day": None,
            "realized_gross_usd": 0.0, "realized_net_usd": 0.0,
            "realized_stress_usd": 0.0, "fills": 0})

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if not isinstance(rec, Mapping):
            continue
        event = rec.get("event")
        if event not in CTRL_EVENTS:
            continue
        arm = str(rec.get("arm") or "")
        pair = str(rec.get("pair") or "")
        if arm not in (CTRL_SHORT_ALWAYS, CTRL_SHADOW_MATCHED) or not pair:
            continue
        s = st(arm, pair)
        if event == "ctrl_open":
            key = ("o", arm, pair, rec.get("entry_ts"), rec.get("entry_px"))
        else:
            key = ("c", arm, pair, rec.get("exit_ts"), rec.get("exit_px"))
        if key in seen:
            continue
        seen.add(key)
        if event == "ctrl_open":
            s["pos"] = int(rec.get("dir") or 0)
            s["entry_px"] = rec.get("entry_px")
            s["entry_epoch"] = rec.get("entry_ts")
            s["entry_bucket"] = rec.get("session_bucket")
            s["rt_id"] = rec.get("round_trip_id")
            if arm == CTRL_SHORT_ALWAYS and rec.get("entry_ts") is not None:
                s["open_day"] = int(rec["entry_ts"]) // 86400
            s["fills"] += 1
        else:
            for k_dst, k_rec in (("realized_gross_usd", "pnl_usd"),
                                 ("realized_net_usd", "realized_net"),
                                 ("realized_stress_usd", "realized_net_stress")):
                if rec.get(k_rec) is not None:
                    s[k_dst] += float(rec[k_rec])
            s["pos"], s["entry_px"], s["entry_epoch"] = 0, None, None
            s["entry_bucket"], s["rt_id"] = None, None
            s["fills"] += 1
    for arm in books:
        for pair, s in books[arm].items():
            for k in ("realized_gross_usd", "realized_net_usd",
                      "realized_stress_usd"):
                s[k] = round(s[k], 2)
    return books


def usd_exposure_block(dirs: Mapping[str, int],
                       mids: Mapping[str, Optional[float]]) -> Dict[str, Any]:
    """C-FX-2 — aggregate USD exposure per H1 decision epoch (DISPLAY-ONLY
    per owner D10: no capping, no behavior change).

    usd_same_side_notional: when EVERY pair carrying a position shares ONE
    direction, the same-direction gross notional (lots + USD); otherwise 0
    (nothing is fully same-side). usd_net_notional: signed sum, long + /
    short -."""
    per = {}
    for p, d in dirs.items():
        d = int(d)
        mid = mids.get(p)
        usd = d * LOTS * float(mid) * CONTRACT_SIZE if (d and mid) else 0.0
        per[p] = {"dir": d,
                  "lots": LOTS * abs(d) if d else 0.0,
                  "signed_lots": LOTS * d,
                  "usd": round(usd, 2)}
    open_p = [v for v in per.values() if v["dir"] != 0]
    same_dir = len({v["dir"] for v in open_p}) == 1 if open_p else False
    return {
        "per_pair_direction": {p: v["dir"] for p, v in per.items()},
        "usd_same_side_notional_lots": LOTS * len(open_p) if same_dir else 0.0,
        "usd_same_side_notional_usd": round(
            sum(abs(v["usd"]) for v in open_p), 2) if same_dir else 0.0,
        "usd_net_notional_lots": round(sum(v["signed_lots"] for v in per.values()), 3),
        "usd_net_notional_usd": round(sum(v["usd"] for v in per.values()), 2),
    }
