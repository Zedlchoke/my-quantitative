"""FOREX-FREE-V7 family FXFV7-A4-P1 — cross-economy release-sign spillover
continuation drift (frozen at selection_freeze_v7.json).

Verbatim from the frozen proposal + selection freeze:
- universe: NON-reporting pairs per calendar around GB/CA CPI prints
  (GB: EURUSD USDJPY USDCAD AUDUSD NZDUSD USDCHF; CA: EURUSD GBPUSD USDJPY
  AUDUSD NZDUSD USDCHF); 833 funded clocks (GB 395 + CA 438).
- anchor: position = sign(r_W) on the non-reporting pair at the funded
  16:00-NY decision instant; hold k=4 sessions.
- neighbour: SAME mechanism k=9.
- control: sham-calendar placebo at anchor params — event +7 calendar days
  (matched weekday by construction of +7d on weekday-dated events), the
  funded decision recomputed as the first 16:00-NY after the shifted window
  end; fail-closed dedupe vs true event dates (a shifted clock whose window
  contains a true evidenced event instant of the same economy is dropped).
- r_W = last 1h close / first 1h close inside the P0 reaction window W - 1
  (INSTANT windows for CA v3/NZ; DAY windows start next 00:00Z — inherited
  from the census semantics; both GB and CA are in scope here).
- decision-close series: 16:00 America/New_York completed bars derived from
  the staged H1 snapshot (house standard; the only evidenced decision-close
  instants). Holds are k sessions on that series.
- collision rule: max one open position per pair (entry may not precede a
  live position's exit).

Costs, financing and books are driver-owned (exec_driver_v7.py); this module
only produces decision records. No PnL here.
"""
from __future__ import annotations

import bisect
import glob
import json
import math
import os
from collections import OrderedDict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

__all__ = ["run_arm", "ARM_IDS", "K_HOLD", "SHAM_SHIFT_CALENDAR_DAYS"]

UTC = timezone.utc
NY_TZ = ZoneInfo("America/New_York")

CYCLE_ID = "FOREX-FREE-V7"
FAMILY_ID = "FXFV7-A4-P1"

ARM_IDS = OrderedDict((
    ("anchor", "anchor_spillover_drift_k4"),
    ("neighbour", "neighbour_spillover_drift_k9"),
    ("control", "control_sham_calendar_plus7_k4"),
))
K_HOLD = {"anchor": 4, "neighbour": 9, "control": 4}
SHAM_SHIFT_CALENDAR_DAYS = 7
ECONOMIES = ("GB", "CA")            # frozen: GB+CA clocks only
WARMUP_SESSIONS = 20                # sigma/series warmup floor

NONREP_PAIRS = {
    "GB": ("EURUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD", "USDCHF"),
    "CA": ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCHF"),
}
PAIR_AREAS = {   # financing attribution (driver bookkeeping input)
    "EURUSD": ("EMU", "US"), "GBPUSD": ("GB", "US"), "USDJPY": ("US", "JP"),
    "USDCAD": ("US", "CA"), "AUDUSD": ("AU", "US"), "NZDUSD": ("NZ", "US"),
    "USDCHF": ("US", "CH"),
}
EXPECTED_CLOCK_COUNT = 833           # GB 395 + CA 438 (P2 clocks file)


def ny_close_ts(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, 16, 0, tzinfo=NY_TZ).astimezone(UTC)


def _iso(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")


class DataBlocked(RuntimeError):
    pass


_H1_CACHE: dict = {}


def load_h1(price_dir: str, pair: str):
    """(sorted bar datetimes, {datetime: close}) from the staged 1h files."""
    key = (price_dir, pair)
    if key in _H1_CACHE:
        return _H1_CACHE[key]
    rows = []
    for fp in sorted(glob.glob(os.path.join(price_dir, f"{pair}_1h_*_a.json"))):
        d = json.load(open(fp))
        if d.get("status") != "ok":
            continue
        for v in d["values"]:
            rows.append((datetime.strptime(v["datetime"], "%Y-%m-%d %H:%M:%S")
                         .replace(tzinfo=UTC), float(v["close"])))
    if not rows:
        raise DataBlocked(f"NO_H1_DATA: {pair}")
    rows.sort()
    out = ([r[0] for r in rows], dict(rows))
    _H1_CACHE[key] = out
    return out


_DC_CACHE: dict = {}


def load_decision_closes(price_dir: str, pair: str):
    """16:00-NY completed weekday closes from the H1 snapshot (house series).

    Returns (sorted days, {day: close})."""
    key = (price_dir, pair)
    if key in _DC_CACHE:
        return _DC_CACHE[key]
    bars, closes = load_h1(price_dir, pair)
    inst = {}
    for ts in bars:
        loc = ts.astimezone(NY_TZ)
        if loc.hour == 16 and loc.minute == 0 and loc.weekday() < 5:
            want = ny_close_ts(loc.date())
            c = closes[ts]
            if loc.date() in inst and inst[loc.date()][1] != c:
                # conflicting 16:00 stamps (DST fold) — keep the earlier UTC
                if want < inst[loc.date()][0]:
                    inst[loc.date()] = (want, c)
            else:
                inst[loc.date()] = (want, c)
    days = sorted(inst)
    out = (days, {d: inst[d][1] for d in days})
    _DC_CACHE[key] = out
    return out


def load_clocks_v7(path: str, expected_count: int = EXPECTED_CLOCK_COUNT):
    rows = json.load(open(path))["clocks"]
    out = []
    for r in rows:
        if r["economy"] not in ECONOMIES:
            continue
        T = datetime.fromisoformat(r["event_available_time_utc"]
                                   .replace("Z", "+00:00")).astimezone(UTC)
        pc = r["precision_class"]
        w0 = T if pc.startswith("INSTANT") else \
            (T.replace(hour=0, minute=0, second=0) + timedelta(days=1))
        out.append({"clock_id": r["clock_id"], "economy": r["economy"],
                    "pair": r["nonrep_pair"],
                    "decision_date": date.fromisoformat(r["decision_date"]),
                    "w0": w0, "w1": w0 + timedelta(hours=24),
                    "event_instant": T,
                    "precision_class": pc})
    if len(out) != expected_count:
        raise DataBlocked(f"CLOCK_COUNT_MISMATCH: {len(out)} != {expected_count}")
    return out


def r_window_return(price_dir, pair, w0, w1):
    bars, closes = load_h1(price_dir, pair)
    i0 = bisect.bisect_left(bars, w0)
    if i0 >= len(bars) or bars[i0] > w1:
        return None
    i1 = bisect.bisect_right(bars, w1) - 1
    if i1 < i0:
        return None
    c0, c1 = closes.get(bars[i0]), closes.get(bars[i1])
    if not c0 or not c1:
        return None
    return c1 / c0 - 1.0


def _first_decision_after(instant: datetime) -> date:
    d = instant.astimezone(NY_TZ).date()
    for _ in range(5):
        cand = ny_close_ts(d)
        if cand >= instant:
            return d
        d += timedelta(days=1)
    raise DataBlocked("NO_DECISION_AFTER_WINDOW")


def fold_of(day: date, fold_starts) -> int:
    if day < fold_starts[1]:
        return 1
    if day < fold_starts[2]:
        return 2
    return 3


def run_arm(arm: str, data_paths: dict):
    """Produce the arm's decision records (no PnL anywhere)."""
    if arm not in ARM_IDS:
        raise ValueError(f"unknown arm {arm}")
    k = K_HOLD[arm]
    sham = arm == "control"
    price_dir = data_paths["price_dir"]
    clocks = load_clocks_v7(data_paths["clocks_path"],
                            data_paths.get("expected_clock_count",
                                           EXPECTED_CLOCK_COUNT))
    true_event_instants = sorted(c["event_instant"] for c in clocks)

    fold_starts = data_paths["fold_starts"]
    series = {p: load_decision_closes(price_dir, p) for p in
              sorted({p for e in ECONOMIES for p in NONREP_PAIRS[e]})}

    decisions = []
    counts = {"clocks": 0, "rw_unavailable": 0, "zero_signal": 0,
              "entry_not_in_series": 0, "warmup_short": 0,
              "exit_beyond_series": 0, "s0_exit_excluded": 0,
              "collision_skipped": 0, "sham_dropped_true_event_inside": 0}
    cur_exit_ts = {}

    for c in sorted(clocks, key=lambda x: (x["decision_date"], x["economy"], x["pair"])):
        counts["clocks"] += 1
        w0, w1 = c["w0"], c["w1"]
        if sham:
            w0 = w0 + timedelta(days=SHAM_SHIFT_CALENDAR_DAYS)
            w1 = w1 + timedelta(days=SHAM_SHIFT_CALENDAR_DAYS)
            if any(w0 < t < w1 for t in true_event_instants):
                counts["sham_dropped_true_event_inside"] += 1
                continue
        # funded-decision rule (F-A7-PL-1 remediation): EVERY arm enters at
        # the first 16:00-NY instant at/after the reaction-window end w1 —
        # the window is CLOSED before the decision; the carried
        # decision_date field is informational only.
        d_entry = _first_decision_after(w1)
        rw = r_window_return(price_dir, c["pair"], w0, w1)
        if rw is None:
            counts["rw_unavailable"] += 1
            continue
        if rw == 0:
            counts["zero_signal"] += 1
            continue
        side = 1 if rw > 0 else -1
        days, _ = series[c["pair"]]
        if d_entry not in set(days):
            counts["entry_not_in_series"] += 1
            continue
        ie = days.index(d_entry)
        if ie < WARMUP_SESSIONS:
            counts["warmup_short"] += 1
            continue
        if ie + k >= len(days):
            counts["exit_beyond_series"] += 1
            continue
        entry_ts = ny_close_ts(days[ie])
        exit_ts = ny_close_ts(days[ie + k])
        s0_end = data_paths["s0_end"]
        if exit_ts > ny_close_ts(s0_end):
            counts["s0_exit_excluded"] += 1
            continue
        if entry_ts < cur_exit_ts.get(c["pair"], datetime.min.replace(tzinfo=UTC)):
            counts["collision_skipped"] += 1
            continue
        cur_exit_ts[c["pair"]] = exit_ts
        decisions.append({
            "pair": c["pair"], "side": side,
            "entry_ts": _iso(entry_ts), "exit_ts": _iso(exit_ts),
            "entry_day": str(days[ie]), "exit_day": str(days[ie + k]),
            "entry_price": series[c["pair"]][1][days[ie]],
            "exit_price": series[c["pair"]][1][days[ie + k]],
            "fold": fold_of(days[ie], fold_starts),
            "clock_id": c["clock_id"], "economy": c["economy"],
            "r_W": rw,
            "areas": PAIR_AREAS[c["pair"]],
            "arm_config_digest": f"a4p1:{arm}:k{k}:signRW:833clk(GB+CA)",
        })
    meta = {
        "family_id": FAMILY_ID, "arm": arm, "arm_id": ARM_IDS[arm],
        "k_hold": k, "sham": sham,
        "n_clocks": counts["clocks"], "counts": counts,
        "n_decisions": len(decisions),
        "arm_config_digest": f"a4p1:{arm}:k{k}:signRW:833clk(GB+CA)",
        "folds": {str(f): sum(1 for d in decisions if d["fold"] == f)
                  for f in (1, 2, 3)},
    }
    return {"decisions": decisions, "meta": meta}
