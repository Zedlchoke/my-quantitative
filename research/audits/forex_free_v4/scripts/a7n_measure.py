#!/usr/bin/env python
"""A7-N novelty measurement, cycle FOREX-FREE-V4 (decision series only; NO PnL).

Reconstructs:
  (1) V3 family2 (FXFV3-A6-P1) anchor decision series, TWO variants:
      (a) as-scored asserted-bound vintages (V3 tree, frozen vintages)
      (b) evidenced-availability vintages (V3R tree)
      using the FROZEN family2 construction (imported read-only from the V3
      worktree).  A mirrored walk is certified against the frozen
      _schedule_pair trips exactly, then used to emit per-decision-clock
      direction states.
  (2) FXFV4-A4-P1 anchor series (financing-budget-scaled differential carry)
      per its packet spec over the P0a evidenced vintages (v2 ledger).
  (3) FXFV4-A4-P2 anchor series (event-anchored persistence hold with
      cost-stressed unwind) per its packet spec (ledger events + vintages +
      snapshot closes for the crash trigger).
  (4) FXFV4-A6-P2 anchor series (policy-change drift, H=10 NY-days) per its
      packet spec (ledger events + snapshot calendar).
Cross-checks:
  - decision_diff_table.json replicated row-exactly (n_diff, n_sign_flips).
  - v2 ledger sha256 pin; P0a evidenced vintage canonical sha256 manifest.
  - mirrored family2 walk trips == frozen _schedule_pair trips.
Measurements: decision-level Spearman rho (gating = active cells) per the
DECLARED BAR in A7_N_DECLARED_BAR.md (written before this script ran).

Read-only on every other worktree.  Writes only under
research/audits/forex_free_v4/ in the A7-N worktree.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

V3_ROOT = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v3/integration"
V3R_ROOT = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v3r/integration"
V4_ROOT = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v4/integration"
WT = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v4/d2-a7-novelty"
OUT_DIR = os.path.join(WT, "research/audits/forex_free_v4")

sys.path.insert(0, V3_ROOT)  # frozen code, read-only import
from research.assets.forex_free_v3 import family2 as F2  # noqa: E402
from research.assets.forex_free_v3.macro_reader import PolicyRateReader  # noqa: E402

NY = ZoneInfo("America/New_York")
AREAS = ("US", "EMU", "GB", "JP", "CH", "CA", "AU", "NZ")
PAIR_AREAS = {p: F2.PAIR_AREAS[p] for p in F2.PAIR_UNIVERSE}
PAIRS = F2.PAIR_UNIVERSE
GRID_START = date(2019, 1, 2)
GRID_END = date(2026, 9, 2)
V2_LEDGER_SHA = "ae5e1f2e64b8aa7c08472755bd73857543aa89b72ea81b70ad5c5d81e7cd6bd4"

CHECKS: dict = {}


def iso_utc(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def ny_grid(start: date, end: date) -> list:
    out = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            out.append(datetime(d.year, d.month, d.day, 16, 0, tzinfo=NY)
                       .astimezone(timezone.utc))
        d += timedelta(days=1)
    return out


# ---------------------------------------------------------------------------
# cached frozen reader wrapper (pure memoization; frozen semantics untouched)
# ---------------------------------------------------------------------------
class CachedReader:
    def __init__(self, vintage_dir: str, label: str):
        paths = {"macro_vintages": {a: os.path.join(vintage_dir, f"{a}.json")
                                    for a in AREAS}}
        self.reader = PolicyRateReader.from_data_paths(paths)
        self.label = label
        self._rate: dict = {}
        self._diff: dict = {}

    def policy_rate(self, area: str, ts) -> float | None:
        key = (area, ts if isinstance(ts, str) else iso_utc(ts))
        if key not in self._rate:
            self._rate[key] = self.reader.policy_rate(area, key[1])
        return self._rate[key]

    def differential(self, base: str, quote: str, ts) -> float | None:
        key = (base, quote, ts if isinstance(ts, str) else iso_utc(ts))
        if key not in self._diff:
            self._diff[key] = self.reader.differential(base, quote, key[2])
        return self._diff[key]


def sgn(x: float) -> int:
    return 1 if x > 0 else (-1 if x < 0 else 0)


# ---------------------------------------------------------------------------
# (1) family2 both variants
# ---------------------------------------------------------------------------
def walk_family2(series, direction_of):
    """Mirror of the frozen _schedule_pair holding law (anchor estimator),
    additionally recording the per-decision-clock direction state.  Trips
    must equal the frozen walk's trips exactly (certified by caller)."""
    stamps = series.stamps
    ff_days = F2._force_flat_day_indices(stamps)
    trips, state = [], {}
    pos = None
    for i, ts in enumerate(stamps):
        if not series.has_bar[i]:
            continue
        nb = series.next_bar_index(i)
        if i in ff_days and pos is not None:
            trips.append({"decision_i": pos["decision_i"], "entry_i": pos["fill_i"],
                          "exit_i": i, "side": pos["side"], "force_flat": True})
            pos = None
        if not series.state_evaluable(i):
            continue
        direction = direction_of(i)
        low = series.vol_state(i, "mean")
        if nb is None:
            # MISSING_NEXT_FILL_BAR path (frozen: skip, record only when a
            # new entry was attempted); no state recorded for this day
            continue
        if pos is not None:
            if low is False:
                trips.append({"decision_i": pos["decision_i"], "entry_i": pos["fill_i"],
                              "exit_i": nb, "side": pos["side"], "force_flat": False})
                pos = None
            elif direction is not None and direction != pos["side"]:
                trips.append({"decision_i": pos["decision_i"], "entry_i": pos["fill_i"],
                              "exit_i": nb, "side": pos["side"], "force_flat": False})
                pos = {"decision_i": i, "side": direction, "fill_i": nb}
        if pos is None and low is True and direction is not None:
            if nb in ff_days:
                pass  # FOLD_BOUNDARY_NO_ENTRY
            else:
                pos = {"decision_i": i, "side": direction, "fill_i": nb}
        state[i] = pos["side"] if pos is not None else 0
    return trips, state


def family2_anchor(reader: CachedReader, h1_dir: str, label: str):
    panels, trip_report = {}, {}
    for pair in PAIRS:
        bars = F2.load_h1_bars(h1_dir, pair)
        series = F2.PairSeries(pair, bars)
        b, q = PAIR_AREAS[pair]

        def direction_of(i, _s=series, _b=b, _q=q):
            return F2._sign_or_none(reader.differential(_b, _q, _s.stamps[i]))

        frozen_trips, _skipped, _counts = F2._schedule_pair(series, "anchor", direction_of)
        my_trips, state = walk_family2(series, direction_of)
        if json.dumps(my_trips, sort_keys=True) != json.dumps(frozen_trips, sort_keys=True):
            trip_report[pair] = "MISMATCH"
        else:
            trip_report[pair] = f"OK({len(frozen_trips)} trips)"
        panels[pair] = {iso_utc(series.stamps[i]): int(state[i]) for i in state}
    CHECKS[f"family2_trips_frozen_equivalence_{label}"] = trip_report
    return panels


def replicate_diff_table(old: CachedReader, new: CachedReader):
    rows = []
    d = date(2019, 1, 1)
    end = date(2026, 9, 2)
    while d <= end:
        inst = datetime(d.year, d.month, d.day, 16, 0, tzinfo=NY)\
            .astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        for pair, (b, q) in PAIR_AREAS.items():
            r_old = old.differential(b, q, inst)
            r_new = new.differential(b, q, inst)
            if r_old != r_new:
                rows.append({"pair": pair, "decision_ts_utc": inst,
                             "sign_flip": bool(r_old is None or r_new is None
                                               or (r_old > 0) != (r_new > 0))})
        d += timedelta(days=1)
    return rows


# ---------------------------------------------------------------------------
# (2) A4-P1: financing-budget-scaled differential carry
# ---------------------------------------------------------------------------
def walk_a4p1(reader: CachedReader, kappa: float = 0.0048, band: float = 0.10):
    grid = ny_grid(GRID_START, GRID_END)
    panels = {}
    for pair in PAIRS:
        b, q = PAIR_AREAS[pair]
        w_booked = None
        panel = {}
        for t in grid:
            diff = reader.differential(b, q, t)
            key = iso_utc(t)
            if diff is None:
                panel[key] = None
                continue
            w_target = sgn(diff) * min(1.0, abs(diff) / kappa)
            if w_booked is None:
                w_booked = w_target          # warmup seed, no fill (packet)
            elif w_target == 0.0 and w_booked != 0.0:
                w_booked = 0.0               # forced unwind (exit rule)
            elif w_booked != 0.0 and sgn(w_target) != sgn(w_booked):
                w_booked = 0.0               # sign-flip unwind (exit rule)
            elif abs(w_target - w_booked) >= band:
                w_booked = w_target          # hysteresis act (entry/re-size)
            panel[key] = sgn(w_booked)
        panels[pair] = panel
    return panels


# ---------------------------------------------------------------------------
# ledger rows: dedupe (area, effective_date) LAST-ROW-WINS (v2 upgrades)
# ---------------------------------------------------------------------------
def load_v2_ledger():
    path = os.path.join(WT, "research/control/forex_free_v4_run/announcement_ledger.jsonl")
    raw = open(path, "rb").read()
    CHECKS["v2_ledger_sha256"] = hashlib.sha256(raw).hexdigest()
    CHECKS["v2_ledger_sha256_matches_pin"] = \
        CHECKS["v2_ledger_sha256"] == V2_LEDGER_SHA
    rows = [json.loads(l) for l in raw.decode().splitlines() if l.strip()]
    dedup = {}
    for r in rows:  # file order; last wins
        dedup[(r["area"], r["effective_date"])] = r
    return rows, dedup


def parse_z(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# snapshot sessions/closes (shared by A4-P2 and A6-P2)
# ---------------------------------------------------------------------------
def pair_sessions(h1_dir: str):
    """Per pair: ordered session stamps (16:00-NY bars present, Mon-Fri) and
    closes.  Mirrors family2's enumerate_decision_days/has_bar convention."""
    out = {}
    for pair in PAIRS:
        bars = F2.load_h1_bars(h1_dir, pair)
        series = F2.PairSeries(pair, bars)
        stamps = [series.stamps[i] for i in range(len(series.stamps))
                  if series.has_bar[i]]
        closes = [bars[s][3] for s in stamps]
        out[pair] = {"stamps": stamps, "closes": closes}
    return out


def vol5_series(closes: list) -> list:
    """5-session realized vol (sample std, ddof=1, of the 5 daily log
    returns ending at each session); None until 5 returns exist."""
    rets = [None] + [math.log(closes[i] / closes[i - 1])
                     for i in range(1, len(closes))]
    out = []
    for i in range(len(closes)):
        window = rets[i - 4:i + 1]
        if i < 5 or any(r is None for r in window):
            out.append(None)
            continue
        m = sum(window) / 5.0
        var = sum((r - m) ** 2 for r in window) / 4.0
        out.append(math.sqrt(var))
    return out


# ---------------------------------------------------------------------------
# (3) A4-P2: event-anchored persistence hold + cost-stressed unwind
# ---------------------------------------------------------------------------
def walk_a4p2(reader: CachedReader, sessions: dict, deduped_rows: list,
              kappa: float = 0.0048, event_floor: float = 0.0024,
              H: int = 63, crash_mult: float = 2.5, crash_med_n: int = 63,
              crash_consec: int = 2):
    # pair events: rows whose area is one of the pair's legs, gated at
    # first_readable_decision_utc
    events = {}
    for r in deduped_rows:
        if r["row_type"] != "RATE_CHANGE":
            continue
        fr = parse_z(r["first_readable_decision_utc"])
        for pair in PAIRS:
            if r["area"] in PAIR_AREAS[pair]:
                events.setdefault(pair, []).append(fr)
    for pair in events:
        events[pair].sort()
    panels = {}
    diag = {}
    for pair in PAIRS:
        stamps = sessions[pair]["stamps"]
        v5 = vol5_series(sessions[pair]["closes"])
        ev = events.get(pair, [])
        ei = 0
        pos_side = 0
        entry_s = None
        locked = False
        fired_run = 0
        pending_update = False
        panel = {}
        n_entries = n_horizon = n_event_exit = n_crash = 0
        for s, t in enumerate(stamps):
            key = iso_utc(t)
            # 1) consume event crossings at/before this clock
            crossed = False
            while ei < len(ev) and ev[ei] <= t:
                ei += 1
                crossed = True
            if crossed:
                pending_update = True
                locked = False
            # window-open initial evidenced state
            if s == 0:
                pending_update = True
            # crash trigger state (needs warmup 63+5)
            fired = False
            if s >= 68:
                cur = v5[s]
                hist = [v5[j] for j in range(s - crash_med_n, s)]
                if cur is not None and all(h is not None for h in hist):
                    sh = sorted(hist)
                    med = sh[crash_med_n // 2]  # odd count -> middle element
                    fired = cur > crash_mult * med
            fired_run = fired_run + 1 if fired else 0
            diff = reader.differential(*PAIR_AREAS[pair], t)
            # 2) exits (decided this clock)
            if pos_side != 0:
                if entry_s is not None and s == entry_s + H:
                    pos_side = 0
                    entry_s = None
                    n_horizon += 1
                elif pending_update and (diff is None or diff == 0
                                         or sgn(diff) != pos_side
                                         or abs(diff) < event_floor):
                    pos_side = 0
                    entry_s = None
                    n_event_exit += 1
                elif fired_run >= crash_consec:
                    pos_side = 0
                    entry_s = None
                    locked = True
                    n_crash += 1
            # 3) entries (first clock at/after an evidenced update)
            if pos_side == 0 and not locked and pending_update \
                    and diff is not None and abs(diff) >= kappa:
                pos_side = sgn(diff)
                entry_s = s + 1   # fills next session; horizon counts from fill
                n_entries += 1
            pending_update = False
            panel[key] = pos_side
        panels[pair] = panel
        diag[pair] = {"entries": n_entries, "horizon_exits": n_horizon,
                      "event_exits": n_event_exit, "crash_exits": n_crash,
                      "sessions": len(stamps)}
    CHECKS["a4p2_walk_diagonal"] = diag
    return panels


# ---------------------------------------------------------------------------
# (4) A6-P2: policy-change drift, H=10 NY-days
# ---------------------------------------------------------------------------
def walk_a6p2(sessions: dict, deduped_rows: list, H: int = 10,
              first_ok: datetime = None):
    if first_ok is None:
        first_ok = datetime(2020, 2, 11, tzinfo=timezone.utc)
    # build per-pair event list: (decision stamp T, availability a, side)
    events = {p: [] for p in PAIRS}
    for r in deduped_rows:
        if r["row_type"] != "RATE_CHANGE":
            continue
        delta = r["new_value"] - r["old_value"]
        if delta == 0:
            continue
        a = parse_z(r["announcement"]["operative_available_time_utc"])
        area = r["area"]
        if area == "US":
            tgt = [("EUR/USD", -1), ("GBP/USD", -1), ("AUD/USD", -1),
                   ("NZD/USD", -1), ("USD/JPY", 1), ("USD/CHF", 1),
                   ("USD/CAD", 1)]
            tgt = [(p, m * sgn(delta)) for p, m in tgt]
        else:
            for pair in PAIRS:
                b, q = PAIR_AREAS[pair]
                if b == area:
                    tgt = [(pair, sgn(delta))]
                    break
                if q == area:
                    tgt = [(pair, -sgn(delta))]
                    break
        for pair, side in tgt:
            stamps = sessions[pair]["stamps"]
            T = None
            for t in stamps:  # first session stamp >= a
                if t >= a:
                    T = t
                    break
            if T is None or T < first_ok:
                continue  # NO_EVAL fail-closed (packet)
            events[pair].append((T, a, side))
    for pair in events:
        events[pair].sort(key=lambda x: (x[0], x[1]))  # tie-break: earlier a
    panels = {}
    diag = {}
    for pair in PAIRS:
        stamps = sessions[pair]["stamps"]
        idx_of = {t: i for i, t in enumerate(stamps)}
        ev = events[pair]
        ei = 0
        pos_side = 0
        entry_s = None
        panel = {}
        n_entries = n_ignored = n_exits = 0
        for s, t in enumerate(stamps):
            if pos_side != 0 and entry_s is not None and s == entry_s + H:
                pos_side = 0
                entry_s = None
                n_exits += 1
            while ei < len(ev) and ev[ei][0] <= t:
                T, a, side = ev[ei]
                ei += 1
                if pos_side == 0:
                    pos_side = side
                    entry_s = idx_of[T] + 1  # fills next session
                    n_entries += 1
                else:
                    n_ignored += 1
            panel[iso_utc(t)] = pos_side
        panels[pair] = panel
        diag[pair] = {"entries": n_entries, "exits": n_exits,
                      "ignored_while_positioned": n_ignored}
    CHECKS["a6p2_walk_diagonal"] = diag
    return panels


# ---------------------------------------------------------------------------
# rho machinery (declared bar: gating = ACTIVE cells)
# ---------------------------------------------------------------------------
def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    rx, ry = ranks(xs), ranks(ys)
    mx = sum(rx) / n
    my = sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = sum((a - mx) ** 2 for a in rx)
    dy = sum((b - my) ** 2 for b in ry)
    if dx == 0.0 or dy == 0.0:
        return None
    return num / math.sqrt(dx * dy)


def compare(panel_a: dict, panel_b: dict, label: str):
    cells_total, cells_active = [], []
    for pair in PAIRS:
        pa = panel_a.get(pair, {})
        pb = panel_b.get(pair, {})
        for key in sorted(set(pa) & set(pb)):
            va, vb = pa[key], pb[key]
            if va is None or vb is None:
                continue
            cells_total.append((va, vb))
            if va != 0 and vb != 0:
                cells_active.append((va, vb))
    xs_t = [c[0] for c in cells_total]
    ys_t = [c[1] for c in cells_total]
    xs_a = [c[0] for c in cells_active]
    ys_a = [c[1] for c in cells_active]
    agree_a = (sum(1 for a, b in cells_active if a == b) / len(cells_active)) \
        if cells_active else None
    nz_a = sum(1 for a in xs_a if a != 0)
    nz_b = sum(1 for b in ys_a if b != 0)
    return {
        "comparison": label,
        "n_shared_total": len(cells_total),
        "n_shared_active": len(cells_active),
        "rho_full": spearman(xs_t, ys_t),
        "rho_gating_active": spearman(xs_a, ys_a),
        "active_agreement_rate": agree_a,
        "active_cells_a_nonzero": nz_a,
        "active_cells_b_nonzero": nz_b,
    }


def apply_bar(r: dict):
    rho = r["rho_gating_active"]
    n = r["n_shared_active"]
    if rho is None or n < 30:
        r["bar_verdict"] = "INDETERMINATE_INSUFFICIENT_SHARED_ACTIVE_CELLS"
        return r
    a = abs(rho)
    if a > 0.7:
        r["bar_verdict"] = "REJECT_RE_GRADE"
    elif a >= 0.5:
        r["bar_verdict"] = "CONDITIONAL"
    else:
        r["bar_verdict"] = "NOVELTY_PASS"
    return r


# ---------------------------------------------------------------------------
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    h1_v3 = os.path.join(V3_ROOT, "data_raw/forex_free_v1")
    h1_v4 = os.path.join(V4_ROOT, "data_raw/forex_free_v1")

    rows, deduped = load_v2_ledger()
    deduped_rows = list(deduped.values())

    # vintage hash checks (P0a manifest)
    man = json.load(open(os.path.join(
        V4_ROOT, "data_raw/forex_free_v4_macro_evidenced/evidenced_vintages_manifest.json")))
    p0a = json.load(open(os.path.join(
        WT, "research/control/forex_free_v4_run/p0a_evidenced_vintages_manifest.json")))
    hash_ok = {}
    for area in AREAS:
        recs = json.load(open(os.path.join(
            V4_ROOT, f"data_raw/forex_free_v4_macro_evidenced/{area}.json")))
        digest = hashlib.sha256(json.dumps(
            recs, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False).encode("utf-8")).hexdigest()
        hash_ok[area] = {
            "computed": digest,
            "matches_tree_manifest": digest == man["per_area"][area]["evidenced_sha256_canonical"],
            "matches_p0a_manifest": digest == p0a["per_area"][area]["evidenced_sha256_canonical"],
        }
    CHECKS["v4_evidenced_vintage_hashes"] = hash_ok

    readers = {
        "a": CachedReader(os.path.join(V3_ROOT, "data_raw/forex_free_v3_macro"), "as-scored"),
        "b": CachedReader(os.path.join(V3R_ROOT, "data_raw/forex_free_v3r_macro_evidenced"), "evidenced"),
        "v4": CachedReader(os.path.join(V4_ROOT, "data_raw/forex_free_v4_macro_evidenced"), "v4-v2pin"),
    }

    print("reconstructing family2 variants ...", flush=True)
    f2a = family2_anchor(readers["a"], h1_v3, "a_as_scored")
    f2b = family2_anchor(readers["b"], h1_v3, "b_evidenced")

    print("replicating decision_diff_table ...", flush=True)
    my_rows = replicate_diff_table(readers["a"], readers["b"])
    stored = json.load(open(os.path.join(
        V3R_ROOT, "research/control/forex_free_v3r_run/decision_diff_table.json")))
    stored_keys = {(r["pair"], r["decision_ts_utc"]) for r in stored["rows"]}
    my_keys = {(r["pair"], r["decision_ts_utc"]) for r in my_rows}
    CHECKS["diff_table_replication"] = {
        "n_diff_mine": len(my_rows),
        "n_diff_stored": stored["n_diff_decisions"],
        "n_sign_flips_mine": sum(1 for r in my_rows if r["sign_flip"]),
        "n_sign_flips_stored": stored["n_sign_flips"],
        "row_set_equal": stored_keys == my_keys,
    }

    print("walking A4-P1 ...", flush=True)
    a4p1 = walk_a4p1(readers["v4"])
    print("walking A4-P2 ...", flush=True)
    sessions_v4 = pair_sessions(h1_v4)
    a4p2 = walk_a4p2(readers["v4"], sessions_v4, deduped_rows)
    print("walking A6-P2 ...", flush=True)
    a6p2 = walk_a6p2(sessions_v4, deduped_rows)

    comparisons = []
    for label, panel in (("FXFV4-A4-P1", a4p1), ("FXFV4-A4-P2", a4p2),
                         ("FXFV4-A6-P2", a6p2)):
        for var, f2p in (("a_as_scored", f2a), ("b_evidenced", f2b)):
            comparisons.append(apply_bar(
                compare(panel, f2p, f"{label}_vs_FXFV3-A6-P1_{var}")))
    # ancestry-variant internal check
    comparisons.append(apply_bar(
        compare(f2a, f2b, "FXFV3-A6-P1_a_as_scored_vs_b_evidenced")))

    out = {
        "schema": "forex_free_v4_a7n_measurements_raw_v1",
        "audit_utc": datetime.now(timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "auditor": "A7-N",
        "declared_bar_file": "A7_N_DECLARED_BAR.md",
        "checks": CHECKS,
        "comparisons": comparisons,
        "panel_notes": {
            "family2": "state = side held after each evaluable decision "
                       "clock (220-valid-NY-day warmup), frozen walk trips "
                       "certified equal to frozen _schedule_pair",
            "a4p1": "state = sign(w_booked) after each daily decision clock "
                    "(kappa=48bps, hysteresis 0.10, exit-on-flip/zero); "
                    "macro grid 2019-01-02..2026-09-02",
            "a4p2": "state per snapshot session (event entries >= 48bps, "
                    "H=63, event-exit < 24bps/flip, crash 2.5x/63-median "
                    "x2 clocks + lockout, window-open baseline)",
            "a6p2": "state per snapshot session (ledger RATE_CHANGE events "
                    "delta!=0, deduped last-row-wins, T = first session "
                    "stamp >= operative_available, H=10, first_ok "
                    "2020-02-11, US drives all 7 long-USD on hike)",
        },
    }
    path = os.path.join(OUT_DIR, "a7_n_measurements_raw.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print(json.dumps({"written": path,
                      "comparisons": comparisons,
                      "checks": CHECKS}, indent=1, default=str))


if __name__ == "__main__":
    main()
