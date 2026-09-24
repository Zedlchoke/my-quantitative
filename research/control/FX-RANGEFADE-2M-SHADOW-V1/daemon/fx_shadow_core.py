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
