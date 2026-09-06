#!/usr/bin/env python
"""FOREX-FREE-V6 I-lane tests: family_a4p1 + family_a6p2 + exec_driver_v6.

Hand-computed SYNTHETIC fixtures ONLY (no production-outcome pins, no
scored PnL anywhere, no network, no real-data arm execution): the
reaction-direction sign goldens, hold-k exit on known bars, the CA boundary
remap, cost-exactly-once-per-side at every ladder tier, cash-never-an-
instrument, the dual-book sign non-inversion check, fold-boundary handling
per family frozen semantics, sham/placebo schedule identifiability,
arm_config_digest verification (frozen match + mismatch refusal), dry-run
sanitization, scored-mode refusal probes, pairwise-distinct record ids and
deterministic double-generation.

Every expected number is written next to its hand arithmetic (the
inherited tests/assets/forex_free_v3/test_accounting.py convention).

Run ONLY this file:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest \\
      tests/assets/forex_free_v6/test_i_family_v6.py -q
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from research.assets.forex_free_v6 import exec_driver_v6 as D      # noqa: E402
from research.assets.forex_free_v6 import family_a4p1 as A         # noqa: E402
from research.assets.forex_free_v6 import family_a6p2 as G         # noqa: E402

UTC = timezone.utc
SHA_FILLER = "a" * 64  # valid 64-hex placeholder (synthetic fixture only)

WEEKDAY_SERIES_START = date(2018, 9, 3)   # Monday (documentation anchor)


def weekdays(start, n):
    """n consecutive weekdays from ``start``."""
    out = []
    day = start
    while len(out) < n:
        if day.weekday() < 5:
            out.append(day)
        day += timedelta(days=1)
    return out


# ------------------------------------------------------------------ #
# synthetic fixtures                                                  #
# ------------------------------------------------------------------ #
def write_price_dir(tmp, closes_by_pair):
    """Staged-style 1day snapshot files (daily bars stamped with their
    decision date) under tmp/data_raw."""
    price_dir = os.path.join(str(tmp), "data_raw")
    os.makedirs(price_dir, exist_ok=True)
    for pair, series in closes_by_pair.items():
        values = [{"datetime": d.isoformat(), "open": f"{c:.6f}",
                   "high": f"{c:.6f}", "low": f"{c:.6f}", "close": f"{c:.6f}"}
                  for d, c in sorted(series.items())]
        payload = {"meta": {"symbol": pair, "interval": "1day"},
                   "status": "ok", "values": values}
        name = f"{pair}_1day_fixture.json"
        with open(os.path.join(price_dir, name), "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
    return price_dir


def filler_dates():
    """Weekday decision dates strictly before the fixture's staged data
    start (the fillers fail closed on warmup, never inferred)."""
    return weekdays(date(2018, 4, 4), 110)  # 110 weekday slots, all pre-staged


def make_clocks_file(tmp, extra_rows):
    """A p3-shaped clocks authority: per-economy counts frozen at
    GB 88 / CA 105 / AU 23 / NZ 30 (total 246) with synthetic rows."""
    rows = []
    used = {e: set() for e in ("GB", "CA", "AU", "NZ")}
    for row in extra_rows:
        rows.append(row)
        used[row["economy"]].add(row["decision_date"])
    counts = {"GB": 88, "CA": 105, "AU": 23, "NZ": 30}
    idx = 0
    for economy, total in counts.items():
        have = sum(1 for r in rows if r["economy"] == economy)
        for _ in range(total - have):
            while filler_dates()[idx % len(filler_dates())].isoformat() \
                    in used[economy]:
                idx += 1
            day = filler_dates()[idx % len(filler_dates())]
            idx += 1
            used[economy].add(day.isoformat())
            if economy in ("GB", "AU"):
                precision = "DAY (synthetic filler)"
                stamp = f"{day.isoformat()}T23:59:59Z"
            elif economy == "CA":
                precision = "INSTANT (synthetic filler)"
                stamp = f"{day.isoformat()}T12:30:00Z"  # before 16:00-NY
            else:
                precision = "INSTANT (synthetic filler)"
                stamp = f"{day.isoformat()}T10:45:00+12:00"
            rows.append({
                "economy": economy, "decision_date": day.isoformat(),
                "available_time_utc": stamp, "precision": precision,
                "reference_period": "synthetic",
                "archive_sha256": SHA_FILLER,
            })
    payload = {
        "schema": "forex_free_v6_conditioning_clocks_v1",
        "S0_window": {"start": "2018-04-04", "end": "2025-07-24"},
        "per_economy_in_S0": counts,
        "total_clocks_published": 246,
        "clocks": rows,
    }
    path = os.path.join(str(tmp), "clocks.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    return path


def story_clocks():
    """The fixture story clocks: one conditionable clock per economy in the
    staged window, plus exactly 3 CA rows that fire the boundary remap
    (2 pre-staged + the in-window story row) per the frozen CA_BOUNDARY_
    COUNT == 3 gate."""
    return [
        # GB story: 16:00-NY decision of Wed 2018-09-12 (EDT -> 20:00Z)
        {"economy": "GB", "decision_date": "2018-09-12",
         "available_time_utc": "2018-09-12T23:59:59Z",
         "precision": "DAY (synthetic story)",
         "reference_period": "synthetic", "archive_sha256": SHA_FILLER},
        # CA story: scheduled 08:30-Toronto print, same-day conditionable
        {"economy": "CA", "decision_date": "2018-09-14",
         "available_time_utc": "2018-09-14T12:30:00Z",
         "precision": "INSTANT (synthetic story)",
         "reference_period": "synthetic", "archive_sha256": SHA_FILLER},
        # CA boundary story: stamp AFTER the decision instant -> the print
        # is conditionable ONLY at the published next-weekday afdd
        {"economy": "CA", "decision_date": "2018-09-26",
         "available_time_utc": "2018-09-26T22:00:00Z",
         "precision": "INSTANT (synthetic boundary story)",
         "reference_period": "synthetic", "archive_sha256": SHA_FILLER,
         "available_for_daily_decision_date": "2018-09-27"},
        # CA boundary fillers (pre-staged window; the remap fires and the
        # event then fails closed on warmup)
        {"economy": "CA", "decision_date": "2018-05-28",
         "available_time_utc": "2018-05-28T21:03:00Z",
         "precision": "INSTANT (synthetic boundary filler)",
         "reference_period": "synthetic", "archive_sha256": SHA_FILLER,
         "available_for_daily_decision_date": "2018-05-29"},
        {"economy": "CA", "decision_date": "2018-05-29",
         "available_time_utc": "2018-05-29T22:04:00Z",
         "precision": "INSTANT (synthetic boundary filler)",
         "reference_period": "synthetic", "archive_sha256": SHA_FILLER,
         "available_for_daily_decision_date": "2018-05-30"},
        # AU story: DAY precision, conditionable at its decision_date
        {"economy": "AU", "decision_date": "2018-09-25",
         "available_time_utc": "2018-09-25T23:59:59Z",
         "precision": "DAY (synthetic story)",
         "reference_period": "synthetic", "archive_sha256": SHA_FILLER},
        # NZ story: INSTANT +12:00 conservative LATER bound, still before
        # the 16:00-NY decision of its decision_date
        {"economy": "NZ", "decision_date": "2018-09-21",
         "available_time_utc": "2018-09-21T10:45:00+12:00",
         "precision": "INSTANT (synthetic story)",
         "reference_period": "synthetic", "archive_sha256": SHA_FILLER},
    ]


def p1_story_closes(n_days):
    """Hand-built weekday closes for the four P1 pairs.  Weekdays from
    2018-09-03; the story windows (hand arithmetic in the assertions):

      GB  D_prev 09-11 close 1.300000, D0 09-12 close 1.308000
          -> R = ln(1.308/1.300) > 0 -> side +1
          D1 09-13 close 1.310000 (entry); k=5 exit 09-20 close 1.322000
          k=10 exit 09-27 close 1.331000
          control: shifted D0 09-19 (close 1.318000) vs D_prev 09-18
          (close 1.314000) -> R > 0 -> side +1
      CA story Fri 09-14: D_prev 09-13 (1.300000), D0 09-14 (1.293500)
          -> R < 0 -> side -1; D1 = Mon 09-17, k=5 exit Mon 09-24
      CA boundary story: conditionable Tue 09-27 (afdd); D_prev 09-26
          (1.298000), D0 09-27 (1.301000) -> side +1; D1 09-28, k=5 exit
          Fri 10-05
      AU story Tue 09-25: D_prev 09-24 (0.720000), D0 09-25 (0.722880)
          -> side +1; D1 09-26, exit 10-03
      NZ story Fri 09-21: D_prev 09-20 (0.660000), D0 09-21 (0.656700)
          -> side -1; D1 09-24, exit 10-01
    """
    days = weekdays(WEEKDAY_SERIES_START, n_days)
    base = {d: 1.0 + 0.001 * i for i, d in enumerate(days)}
    gb = dict(base)
    gb.update({date(2018, 9, 11): 1.300000, date(2018, 9, 12): 1.308000,
               date(2018, 9, 13): 1.310000, date(2018, 9, 18): 1.314000,
               date(2018, 9, 19): 1.318000, date(2018, 9, 20): 1.322000,
               date(2018, 9, 27): 1.331000})
    cad = {d: 1.3000 - 0.0002 * i for i, d in enumerate(days)}
    cad.update({date(2018, 9, 13): 1.300000, date(2018, 9, 14): 1.293500,
                date(2018, 9, 17): 1.291000, date(2018, 9, 24): 1.288000,
                date(2018, 9, 26): 1.298000, date(2018, 9, 27): 1.301000,
                date(2018, 9, 28): 1.302000, date(2018, 10, 5): 1.305000})
    aud = {d: 0.7200 + 0.0001 * i for i, d in enumerate(days)}
    aud.update({date(2018, 9, 24): 0.720000, date(2018, 9, 25): 0.722880,
                date(2018, 9, 26): 0.723500, date(2018, 10, 3): 0.726000})
    nzd = {d: 0.6600 - 0.0001 * i for i, d in enumerate(days)}
    nzd.update({date(2018, 9, 20): 0.660000, date(2018, 9, 21): 0.656700,
                date(2018, 9, 24): 0.656000, date(2018, 10, 1): 0.653000})
    return {"GBPUSD": gb, "USDCAD": cad, "AUDUSD": aud, "NZDUSD": nzd}


def make_ledger(tmp):
    """Tiny evidenced financing ledger (accounting kernel input): baseline
    rows effective 2000-01-01 for every area the two universes need."""
    path = os.path.join(str(tmp), "financing_ledger.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for area, value in (("GB", 0.75), ("US", 2.50), ("CA", 1.75),
                            ("AU", 1.50), ("NZ", 1.75), ("EMU", 0.00),
                            ("CH", -0.75), ("JP", -0.10)):
            fh.write(json.dumps({
                "area": area,
                "announcement": {"operative_available_time_utc":
                                 "2000-01-01T00:00:00Z"},
                "effective_time_utc": "2000-01-01T00:00:00Z",
                "new_value": value,
            }) + "\n")
    return path


def make_manifest(tmp):
    path = os.path.join(str(tmp), "staged_manifest.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"schema": "synthetic", "digests_exec2": {}}, fh)
    return path


def make_fixture(tmp, end_days=560):
    """One synthetic snapshot serving both families: 7 staged pairs (the
    P1 four with hand-built story closes + the P2 three with a dominant
    common factor) over the SAME weekday span (so the 7-pair intersection
    grid spans the full fixture), the 246-row clocks authority with the
    story rows, the tiny financing ledger and a synthetic manifest."""
    days = weekdays(WEEKDAY_SERIES_START, end_days)
    closes = p1_story_closes(end_days)
    # P2 pairs: a dominant common factor plus small idiosyncratic noise
    # (sin + drift: deterministic, hand-auditable)
    for pair, phase in (("EURUSD", 0.0), ("USDCHF", 1.1), ("USDJPY", 2.2)):
        series = {}
        for i, d in enumerate(days):
            f = 1.0 + 0.0008 * (i % 37) + 0.004 * np.sin(i / 9.0 + phase)
            idio = 0.0002 * np.sin(i / 3.1 + phase * 2.0)
            series[d] = round(f + idio, 8) if pair.endswith("USD") \
                else round(100.0 / (f + idio) if pair == "USDJPY"
                           else 1.0 / (f + idio), 8)
        closes[pair] = series
    price_dir = write_price_dir(tmp, closes)
    clocks_path = make_clocks_file(tmp, story_clocks())
    ledger_path = make_ledger(tmp)
    manifest_path = make_manifest(tmp)
    return {
        "price_1day_dir": price_dir,
        "conditioning_clocks": clocks_path,
        "announcement_ledger": ledger_path,
        "staged_manifest": manifest_path,
        "verify_authority": False,
    }


@pytest.fixture()
def fixture(tmp_path):
    return make_fixture(tmp_path)


@pytest.fixture()
def tmp_ledger(tmp_path):
    """A temp ledger under the driver's dryrun_tmp/ (the driver refuses
    dry-run ledgers anywhere else); cleaned up by the caller."""
    d = os.path.join(D.ROOT, D.V6_CTL, D.DRYRUN_TMP_DIRNAME,
                     f"test_{os.getpid()}_{abs(hash(str(tmp_path))) % 99999}")
    os.makedirs(d, exist_ok=True)
    yield d
    shutil.rmtree(d, ignore_errors=True)


def read_ledger(path):
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


# ------------------------------------------------------------------ #
# family_a4p1: reaction direction + schedule mechanics                #
# ------------------------------------------------------------------ #
def test_reaction_direction_sign_hand_built():
    # R = ln(close(D0)/close(D_prev)); side = sign(R)
    import math
    assert A.reaction_direction(1.308000, 1.300000) == pytest.approx(
        math.log(1.308 / 1.300), abs=1e-12)
    assert A.direction_of(A.reaction_direction(1.308, 1.300)) == 1
    assert A.direction_of(A.reaction_direction(1.2935, 1.3000)) == -1
    # an EXACT zero is NO_TRADE (fail closed)
    assert A.reaction_direction(1.261, 1.261) == 0.0
    assert A.direction_of(0.0) == 0


def test_hold_k_exit_on_known_bars():
    days = weekdays(date(2018, 9, 3), 20)
    series = {d: 1.0 + 0.001 * i for i, d in enumerate(days)}
    series_days = sorted(series)
    # D0 = Wed 2018-09-12 (index 7); D_prev = Tue 09-11; D1 = Thu 09-13;
    # k=5 exit = 5 sessions after D1 -> Fri 2018-09-20
    reason, leg = A.resolve_schedule(date(2018, 9, 12), 5, series, series_days)
    assert reason is None
    assert leg["d_prev"] == date(2018, 9, 11)
    assert leg["d1"] == date(2018, 9, 13)
    assert leg["exit_day"] == date(2018, 9, 20)      # 14,17,18,19,20
    assert leg["entry_price"] == pytest.approx(series[date(2018, 9, 13)])
    assert leg["exit_price"] == pytest.approx(series[date(2018, 9, 20)])
    # the time exit is ISSUED at D1+k-1 (never a same-bar exit fill)
    assert leg["exit_decision_day"] == date(2018, 9, 19)
    # k=10 reaches Fri 2018-09-27 (one session per weekday, Mon-Fri)
    _, leg10 = A.resolve_schedule(date(2018, 9, 12), 10, series, series_days)
    assert leg10["exit_day"] == date(2018, 9, 27)
    # a weekend spans as missing weekdays: D0 Fri 09-14 -> D1 Mon 09-17
    reason2, leg2 = A.resolve_schedule(date(2018, 9, 14), 5, series,
                                       series_days)
    assert reason2 is None
    assert leg2["d1"] == date(2018, 9, 17)
    assert leg2["exit_day"] == date(2018, 9, 24)


def test_ca_boundary_remap_next_weekday():
    # a synthetic 22:00Z stamp (after the 20:00Z EDT decision instant) is
    # conditionable NEXT day at the published available_for_daily_decision_date
    def shaped(economy, decision_date, stamp, precision="INSTANT (synthetic)",
               afdd=None):
        return {"economy": economy, "decision_date": decision_date,
                "available": datetime.fromisoformat(
                    stamp.replace("Z", "+00:00")),
                "precision": precision,
                "available_for_daily_decision_date": afdd}
    clock = shaped("CA", "2018-09-26", "2018-09-26T22:00:00Z",
                   afdd="2018-09-27")
    cond, remap = A.conditionable_date(clock)
    assert (cond, remap) == (date(2018, 9, 27), True)
    # a scheduled 08:30-Toronto (12:30Z) print is same-day conditionable
    sched = shaped("CA", "2018-09-14", "2018-09-14T12:30:00Z",
                   afdd="2018-09-14")
    assert A.conditionable_date(sched) == (date(2018, 9, 14), False)
    # GB DAY precision: same day by the published convention
    gb = shaped("GB", "2018-09-12", "2018-09-12T23:59:59Z",
                precision="DAY (ONS bulletin Release date field)")
    assert A.conditionable_date(gb) == (date(2018, 9, 12), False)
    # NZ INSTANT (+12:00 conservative LATER bound) preceding the decision
    nz = shaped("NZ", "2018-09-21", "2018-09-21T10:45:00+12:00",
                precision="INSTANT (Stats NZ PublicationDate)")
    assert A.conditionable_date(nz) == (date(2018, 9, 21), False)
    # a contradictory CA stamp (post-decision instant, afdd not later)
    # is skipped fail closed
    bad = shaped("CA", "2018-09-26", "2018-09-26T22:00:00Z",
                 afdd="2018-09-26")
    assert A.conditionable_date(bad) == (None, False)


def test_warmup_requires_five_closes_ending_at_d_prev():
    days = weekdays(date(2018, 9, 3), 20)
    series = {d: 1.0 for d in days}
    series_days = sorted(series)
    # D0 09-06: D_prev 09-05 has only 3 prior closes (09-03, 09-04 + itself)
    # -> warmup skip (5 closes must END at close(D_prev))
    reason, _ = A.resolve_schedule(date(2018, 9, 6), 5, series, series_days)
    assert reason == A.REASON_WARMUP
    # D0 09-12: D_prev 09-11 has 6 prior closes -> warmup satisfied
    reason2, _ = A.resolve_schedule(date(2018, 9, 12), 5, series, series_days)
    assert reason2 is None
    # a D_prev outside the staged series fails closed (never inferred):
    # D0 = the series' first day -> D_prev = the prior Friday, absent
    reason3, _ = A.resolve_schedule(days[0], 5, series, series_days)
    assert reason3 == A.REASON_MISSING_PREV


def test_p1_run_arm_story_golden(fixture):
    """The hand-computed story trades on the synthetic fixture: DST-correct
    16:00-NY stamps, sides, fills and the k=5 vs k=10 single-axis
    difference; reconciliation and the CA boundary gate hold."""
    anchor = A.run_arm("anchor", fixture)["decisions"]
    gb = [d for d in anchor if d["economy"] == "GB"]
    assert len(gb) == 1
    t = gb[0]
    # side +1: R = ln(1.308/1.300) > 0 (hand arithmetic above)
    assert t["side"] == 1
    assert t["r_value"] == pytest.approx(__import__("math")
                                         .log(1.308 / 1.300), abs=1e-12)
    assert t["decision_ts"] == "2018-09-12T20:00:00+00:00"  # EDT: 16:00-NY
    assert t["entry_ts"] == "2018-09-13T20:00:00+00:00"
    assert t["exit_ts"] == "2018-09-20T20:00:00+00:00"
    assert t["entry_price"] == pytest.approx(1.310000)
    assert t["exit_price"] == pytest.approx(1.322000)
    assert t["k_hold"] == 5
    assert t["fold"] == "F1"   # D0 2018-09-12 inside F1
    assert t["span_boundary_purged"] is False
    assert t["archive_sha256"] == SHA_FILLER  # resolvable clock tuple
    # CA scheduled story: short reaction, Monday entry over the weekend
    ca = [d for d in anchor if d["economy"] == "CA"
          and d["clock_decision_date"] == "2018-09-14"]
    assert len(ca) == 1
    assert ca[0]["side"] == -1
    assert ca[0]["entry_ts"] == "2018-09-17T20:00:00+00:00"
    assert ca[0]["exit_ts"] == "2018-09-24T20:00:00+00:00"
    # CA boundary story: conditionable ONLY at the afdd (remap), +1 side
    cab = [d for d in anchor if d["ca_boundary_remap"]]
    assert len(cab) == 1
    assert cab[0]["decision_ts"] == "2018-09-27T20:00:00+00:00"
    assert cab[0]["side"] == 1
    # neighbour: identical trades except the hold axis (k=10)
    neigh = A.run_arm("neighbour", fixture)["decisions"]
    n_gb = [d for d in neigh if d["economy"] == "GB"]
    assert n_gb[0]["k_hold"] == 10
    assert n_gb[0]["decision_ts"] == t["decision_ts"]
    assert n_gb[0]["exit_ts"] == "2018-09-27T20:00:00+00:00"
    # control: the same rule on the +7d shifted calendar
    ctrl = A.run_arm("control", fixture)["decisions"]
    c_gb = [d for d in ctrl if d["economy"] == "GB"]
    assert len(c_gb) == 1
    # shifted D0 = 2018-09-19 (Wed), D_prev 09-18, side +1
    assert c_gb[0]["decision_ts"] == "2018-09-19T20:00:00+00:00"
    assert c_gb[0]["side"] == 1
    assert c_gb[0]["conditionable_date"] == "2018-09-19"   # shifted date
    assert c_gb[0]["published_conditionable_date"] == "2018-09-12"
    assert c_gb[0]["sham_shifted"] is True
    assert all(d["sham_shifted"] is False for d in anchor)
    # anchor vs control schedules differ (the sham is a different calendar)
    anchor_keys = {d["decision_ts"] for d in anchor}
    ctrl_keys = {d["decision_ts"] for d in ctrl}
    assert anchor_keys != ctrl_keys


def test_p1_meta_counts_reconcile(fixture):
    for arm in ("anchor", "neighbour", "control"):
        meta = A.run_arm(arm, fixture)["meta"]
        assert meta["ca_boundary_remap_events"] == 3
        per = meta["per_economy_schedule"]
        for economy, counts in per.items():
            skips = sum(v for kk, v in counts.items()
                        if kk in A.ALL_SKIPPED_REASONS)
            assert counts["trades"] + skips == counts["published_clocks"]
        assert meta["n_decisions"] + sum(meta["skipped_counts"].values()) == 246


def test_ca_boundary_count_gate_blocks_on_wrong_count(fixture, tmp_path):
    """CA_BOUNDARY_COUNT: a clocks authority where the remap rule does not
    fire exactly 3 times BLOCKS (implementation bug, never absorbed)."""
    rows = [r for r in story_clocks()
            if "available_for_daily_decision_date" not in r]
    clocks_path = make_clocks_file(tmp_path, rows)
    broken = dict(fixture, conditioning_clocks=clocks_path)
    with pytest.raises(A.DataBlocked, match="CA_BOUNDARY_COUNT"):
        A.run_arm("anchor", broken)


# ------------------------------------------------------------------ #
# family_a6p2: state machinery + fills + folds                        #
# ------------------------------------------------------------------ #
def test_state_share_series_bounds_and_degenerate():
    rng_days = weekdays(date(2018, 1, 1), 40)
    # one common factor + one idiosyncratic pair set -> share in (0, 1]
    closes = {}
    for i, d in enumerate(rng_days):
        pass
    grid = rng_days
    matrix = np.zeros((len(grid), 7))
    for i, d in enumerate(grid):
        f = float(np.sin(i / 5.0))
        for j in range(7):
            matrix[i, j] = 100.0 * (1.0 + 0.01 * f + 0.001 * ((i * 7 + j) % 3)
                                    / 3.0)
    shares, singular, returns = G.state_share_series(grid, matrix)
    assert singular == 0
    defined = [v for v in shares.values() if v is not None]
    assert len(defined) == len(grid) - G.STATE_WINDOW
    assert all(0.0 < v <= 1.0 + 1e-9 for v in defined)
    # a constant (zero-variance) pair column leaves the state UNDEFINED
    matrix2 = matrix.copy()
    matrix2[:, 3] = 100.0
    shares2, singular2, _ = G.state_share_series(grid, matrix2)
    assert singular2 == len(grid) - G.STATE_WINDOW


def test_p2_grid_and_fills_on_synthetic(fixture):
    """On the synthetic 7-pair grid: the intersection grid has all closes
    by construction, fills are never same-bar, entry is the first decision
    day after t, and the exit fill is exactly 5 decision days after the
    entry fill (5 close-to-close intervals)."""
    result = G.run_arm("anchor", fixture)
    meta, decisions = result["meta"], result["decisions"]
    assert meta["skipped_counts"]["state_undefined_days"] == 0
    assert meta["skipped_counts"]["leg_skips_end_of_data"] == 0
    # rebuild the grid to verify the fill geometry + the warmup anchor
    grid_days, _ = G.build_grid(fixture["price_1day_dir"])
    index = {d.isoformat(): i for i, d in enumerate(grid_days)}
    assert meta["first_eligible_decision_date"] == \
        grid_days[G.WARMUP_DECISION_DAYS].isoformat()  # grid index 272
    assert len(decisions) > 0
    for d in decisions:
        i = index[d["decision_ts"][:10]]
        e = index[d["entry_ts"][:10]]
        x = index[d["exit_ts"][:10]]
        assert e == i + 1                      # first decision day after t
        assert x == e + G.HOLD_DECISION_DAYS   # 5 sessions after the fill
        assert d["noise_floor_pass"] is True
        # fade direction: -sign(cum10)
        if d["cum10"] > 0:
            assert d["side"] == -1
        else:
            assert d["side"] == 1
        assert d["fold"] in ("F1", "F2", "F3")


def test_p2_exit_crossing_fold_boundary_dropped(fixture):
    """The frozen fold-boundary rule: any trade whose EXIT FILL crosses an
    internal fold boundary is dropped from both books and counted; every
    emitted trade stays inside one fold."""
    result = G.run_arm("neighbour", fixture)
    meta = result["meta"]
    dropped = meta["skipped_counts"]["boundary_crossing_dropped"]
    assert dropped > 0   # the fixture spans B1 = 2020-09-09 with daily states
    grid_days, _ = G.build_grid(fixture["price_1day_dir"])
    index = {d.isoformat(): i for i, d in enumerate(grid_days)}
    for d in result["decisions"]:
        assert G.fold_of_index(grid_days, index[d["decision_ts"][:10]]) \
            == G.fold_of_index(grid_days, index[d["exit_ts"][:10]])
    # and the emitted population + drops reconcile against the leg buckets
    sc = meta["skipped_counts"]
    legs = sum(sc[kk] for kk in ("leg_skips_noise_floor", "leg_skips_collision",
                                 "leg_skips_end_of_data",
                                 "boundary_crossing_dropped"))
    assert meta["n_decisions"] + legs == sc["state_days"] * 7


def test_p2_neighbour_is_complement_state(fixture):
    anchor = G.run_arm("anchor", fixture)["meta"]["skipped_counts"]
    neigh = G.run_arm("neighbour", fixture)["meta"]["skipped_counts"]
    # the complement state: state_days must sum to the scanned days
    assert anchor["state_days"] + neigh["state_days"] \
        == anchor["decision_days_scanned"]
    assert anchor["decision_days_scanned"] == neigh["decision_days_scanned"]


def test_p2_placebo_shifts_state_by_100_decision_days(fixture):
    """state_placebo_t = state_{t-100}: the placebo preserves the fade rule
    and the fills but sources its state 100 decision days back; the placebo
    schedule differs from the anchor's."""
    anchor = G.run_arm("anchor", fixture)
    ctrl = G.run_arm("control", fixture)
    grid_days, _ = G.build_grid(fixture["price_1day_dir"])
    index = {d.isoformat(): i for i, d in enumerate(grid_days)}
    assert len(ctrl["decisions"]) > 0
    for d in ctrl["decisions"]:
        src = d["placebo_source_date"]
        assert src is not None
        assert index[d["decision_ts"][:10]] - index[src] == 100
    anchor_keys = {d["decision_id"] for d in anchor["decisions"]}
    ctrl_keys = {d["decision_id"] for d in ctrl["decisions"]}
    assert anchor_keys != ctrl_keys   # the schedules differ


# ------------------------------------------------------------------ #
# exec_driver_v6: costs, books, validation                            #
# ------------------------------------------------------------------ #
def _hand_trade():
    # long 10000 GBPUSD from 1.3000 to 1.3100:
    #   gross = +1 * 10000 * (1.31/1.30 - 1) = +76.923077 USD
    return {"decision_id": "t1", "pair": "GBPUSD", "side": 1,
            "notional_usd": 10000.0, "entry_price": 1.30,
            "exit_price": 1.31}


cost_side = {1.0: 1.50, 1.5: 2.25, 2.0: 3.00}


def test_cost_charged_exactly_once_per_round_trip_each_tier():
    tr = _hand_trade()
    fin = {"t1": 0.0}
    gross = D.price_pnl_usd(tr)
    assert gross == pytest.approx(10000.0 * (1.31 / 1.30 - 1.0))
    # per-side cost = notional * 1.5bps * tier / 1e4, charged once per side:
    #   tier 1.0: 2 x 1.50 USD = 3.00   -> net 73.923077
    #   tier 1.5: 2 x 2.25 USD = 4.50   -> net 72.423077
    #   tier 2.0: 2 x 3.00 USD = 6.00   -> net 70.923077
    expected = {1.0: 3.00, 1.5: 4.50, 2.0: 6.00}
    for tier, cost in expected.items():
        pnls = D.book_trades([tr], tier, fin)
        assert pnls[0] == pytest.approx(gross - cost, abs=1e-9)
    # the kernel primitive agrees tier for tier
    for tier in (1.0, 1.5, 2.0):
        assert D.K.bps_cost(10000.0, tier) == pytest.approx(cost_side[tier])


def test_financing_adjustment_hand_computed(tmp_path):
    ledger = make_ledger(tmp_path)
    reader = D.financing_reader({"announcement_ledger": ledger})
    # long GBPUSD (GB/US): r_GB - r_US = 0.75 - 2.50 = -1.75%/yr;
    # held [d, d+3) = 3 calendar days:
    #   fin = +1 * 10000 * (-0.0175) * 3/365 = -1.438356 USD
    entry = datetime(2018, 9, 12, 20, 0, tzinfo=UTC)
    exit_ = datetime(2018, 9, 15, 20, 0, tzinfo=UTC)
    adj = D.financing_adjustment_usd(reader, "GBPUSD", 1, 10000.0, entry,
                                     exit_)
    assert adj == pytest.approx(10000.0 * (-0.0175) * 3 / 365.0, abs=1e-9)
    # short USDCAD (US/CA): r_US - r_CA = +0.75%/yr, side -1:
    #   fin = -10000 * 0.0075 * 1/365 = -0.205479 USD
    adj2 = D.financing_adjustment_usd(reader, "USDCAD", -1, 10000.0,
                                      entry, entry + timedelta(days=1))
    assert adj2 == pytest.approx(-10000.0 * 0.0075 / 365.0, abs=1e-9)


def test_cash_never_treated_as_instrument():
    tr = dict(_hand_trade(), pair="USD")
    with pytest.raises(ValueError, match="CASH_AS_INSTRUMENT"):
        D.validate_decisions([tr], "FXFV6-A4-P1")


def test_dual_book_sign_non_inversion_check_fires():
    # gross +0.2308 USD round trip (multiplicative identity) vs 3.00 USD
    # tier-2 cost: the costed book inverts the positive price-only sign
    # -> the check FIRES
    tr = {"decision_id": "t1", "pair": "GBPUSD", "side": 1,
          "notional_usd": 10000.0, "entry_price": 1.30,
          "exit_price": 1.30003}
    assert D.price_pnl_usd(tr) == pytest.approx(
        10000.0 * (1.30003 / 1.30 - 1.0), abs=1e-9)
    inversions = D.dual_book_inversions([tr], {"t1": 0.0})
    assert inversions == ["tier1.0", "tier1.5", "tier2.0"]
    # a healthy gross out-earns every tier: no inversion
    healthy = dict(_hand_trade())
    assert D.dual_book_inversions([healthy], {"t1": 0.0}) == []


def test_validate_decisions_rejects_same_bar_and_bad_clock():
    good = {"decision_id": "d1", "pair": "GBPUSD", "side": 1,
            "notional_usd": 10000.0,
            "decision_ts": "2018-09-12T20:00:00+00:00",
            "entry_ts": "2018-09-13T20:00:00+00:00",
            "exit_ts": "2018-09-20T20:00:00+00:00",
            "archive_sha256": SHA_FILLER}
    D.validate_decisions([good], "FXFV6-A4-P1", clocks_shas={SHA_FILLER})
    # same-bar fill forbidden
    with pytest.raises(ValueError, match="same-bar"):
        D.validate_decisions([dict(good, entry_ts=good["decision_ts"])],
                             "FXFV6-A4-P1")
    # a non-16:00-NY stamp violates the decision clock
    with pytest.raises(ValueError, match="16:00"):
        D.validate_decisions([dict(good, decision_ts="2018-09-12T21:00:00"
                                   "+00:00")], "FXFV6-A4-P1")
    # an invented clock (sha not in the clocks authority) is a HARD_FAIL
    with pytest.raises(ValueError, match="invented clock"):
        D.validate_decisions([good], "FXFV6-A4-P1", clocks_shas={"b" * 64})


def test_usd_drift_diagnostic_signs():
    # long GBPUSD is SHORT the USD leg; long USDJPY is LONG the USD leg:
    # one of each over disjoint days -> mean exposure 0 and +/-1 days
    trades = [
        {"pair": "GBPUSD", "side": 1, "notional_usd": 10000.0,
         "entry_ts": "2018-09-12T20:00:00+00:00",
         "exit_ts": "2018-09-13T20:00:00+00:00"},
        {"pair": "USDJPY", "side": 1, "notional_usd": 10000.0,
         "entry_ts": "2018-09-14T20:00:00+00:00",
         "exit_ts": "2018-09-15T20:00:00+00:00"},
    ]
    diag = D.usd_drift_diagnostic(trades, [-1.0, 1.0], [[]], {})
    assert diag["evaluated"] is False
    assert diag["mean_usd_leg_exposure"] == 0.0
    assert diag["n_days"] == 2


# ------------------------------------------------------------------ #
# arm_config_digest verification (frozen match + mismatch refusal)    #
# ------------------------------------------------------------------ #
def test_all_six_frozen_arm_config_digests_verify():
    table, checks = D.verify_freeze(D.ROOT)
    assert len(table) == 6
    assert len(checks) == 6
    for row in table:
        assert row["digest_match"] is True
        assert row["recomputed_digest"] == row["frozen_digest"]
    arms = {(r["family_id"], r["arm"]) for r in table}
    assert arms == {(f, a) for f in D.FAMILIES for a in D.ARMS}


def test_digest_mismatch_refuses(tmp_path):
    """A tampered frozen_config (or recorded digest) refuses the run
    before any compute."""
    root = os.path.join(str(tmp_path), "repo")
    os.makedirs(os.path.join(root, D.V6_CTL, "d1", "a4_postrelease"),
                exist_ok=True)
    os.makedirs(os.path.join(root, D.V6_CTL, "d1", "a6_open"), exist_ok=True)
    for family_id, spec in D.FAMILIES.items():
        shutil.copy(os.path.join(D.ROOT, spec["proposal"]),
                    os.path.join(root, spec["proposal"]))
    freeze = json.load(open(os.path.join(D.ROOT, D.FREEZE_PATH),
                            encoding="utf-8"))
    # tamper ONE frozen config value (content change -> digest change)
    freeze["selected_families"][0]["arms"]["anchor"]["frozen_config"]\
        ["k_hold"] = 6
    with open(os.path.join(root, D.FREEZE_PATH), "w", encoding="utf-8") as fh:
        json.dump(freeze, fh)
    with pytest.raises(SystemExit, match="ARM_CONFIG_DIGEST_MISMATCH"):
        D.verify_freeze(root)


def test_proposal_sha_mismatch_refuses(tmp_path):
    root = os.path.join(str(tmp_path), "repo")
    os.makedirs(os.path.join(root, D.V6_CTL, "d1", "a4_postrelease"),
                exist_ok=True)
    os.makedirs(os.path.join(root, D.V6_CTL, "d1", "a6_open"), exist_ok=True)
    for family_id, spec in D.FAMILIES.items():
        shutil.copy(os.path.join(D.ROOT, spec["proposal"]),
                    os.path.join(root, spec["proposal"]))
    freeze = json.load(open(os.path.join(D.ROOT, D.FREEZE_PATH),
                            encoding="utf-8"))
    freeze["selected_families"][0]["proposal_sha256"] = "0" * 64
    with open(os.path.join(root, D.FREEZE_PATH), "w", encoding="utf-8") as fh:
        json.dump(freeze, fh)
    with pytest.raises(SystemExit, match="PROPOSAL_SHA_MISMATCH"):
        D.verify_freeze(root)


# ------------------------------------------------------------------ #
# scored-mode refusal probes (tmp paths; fail closed)                 #
# ------------------------------------------------------------------ #
def test_scored_mode_refuses_without_contract(tmp_path):
    report = os.path.join(str(tmp_path), "refusal.json")
    with pytest.raises(SystemExit):
        D.run_scored({"price_1day_dir": str(tmp_path)}, report,
                     root=str(tmp_path))
    refusal = json.load(open(report, encoding="utf-8"))
    assert refusal["refused"] is True
    assert refusal["schema"] == D.SCORED_REFUSAL_SCHEMA
    assert refusal["gates"]["run_contract"]["ok"] is False
    assert "missing" in refusal["gates"]["run_contract"]["detail"]


def test_scored_mode_refuses_without_seed(tmp_path):
    root = str(tmp_path)
    seed = os.path.join(root, "scored_ledger.jsonl")
    ctl = os.path.join(root, "research", "control", "forex_free_v6_run")
    os.makedirs(ctl, exist_ok=True)
    contract = {
        "schema": "forex_free_v6_run_contract_v1",
        "cycle_id": "FOREX-FREE-V6",
        "launch_authorized": True,
        "s0_launch_authorized_verdict": D.S0_VERDICT,
        "owner_go_phrase": D.OWNER_GO_PHRASE,
        "owner_go_fresh": True,
        "ledger_seed_path": seed,
    }
    with open(os.path.join(ctl, "run_contract.json"), "w",
              encoding="utf-8") as fh:
        json.dump(contract, fh)
    report = os.path.join(root, "refusal.json")
    with pytest.raises(SystemExit):
        D.run_scored({"price_1day_dir": root}, report, root=root)
    refusal = json.load(open(report, encoding="utf-8"))
    assert refusal["refused"] is True
    assert refusal["gates"]["run_contract"]["ok"] is True
    assert refusal["gates"]["ledger_seed"]["ok"] is False


def test_scored_mode_refuses_on_wrong_go_phrase_or_flag(tmp_path):
    root = str(tmp_path)
    seed = os.path.join(root, "scored_ledger.jsonl")
    with open(seed, "w", encoding="utf-8") as fh:
        fh.write("{}\n")
    for bad in ({"owner_go_phrase": "GO STOCKS V10 SCORED EXECUTION"},
                {"launch_authorized": False},
                {"s0_launch_authorized_verdict": "SOME_OTHER_VERDICT"},
                {"owner_go_fresh": False}):
        contract = {
            "schema": "forex_free_v6_run_contract_v1",
            "cycle_id": "FOREX-FREE-V6",
            "launch_authorized": True,
            "s0_launch_authorized_verdict": D.S0_VERDICT,
            "owner_go_phrase": D.OWNER_GO_PHRASE,
            "owner_go_fresh": True,
            "ledger_seed_path": seed,
        }
        contract.update(bad)
        with open(os.path.join(root, "run_contract.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(contract, fh)
        ok, gates = D.evaluate_launch_gates(root)
        assert ok is False, bad


# ------------------------------------------------------------------ #
# dry-run sanitization, pairwise ids, determinism                     #
# ------------------------------------------------------------------ #
def test_dryrun_sanitized_pairwise_ids_and_digest_table(fixture, tmp_ledger,
                                                        tmp_path):
    ledger = os.path.join(tmp_ledger, "dryrun_ledger.jsonl")
    report_path = os.path.join(str(tmp_path), "dryrun_report.json")
    report = D.run_dryrun(fixture, ledger, report_path,
                          verify_data=False)
    assert report["scored"] is False and report["real_pnl"] is False
    assert len(report["arms"]) == 6
    assert report["pairwise_distinct_ids"] is True
    ids = [a["record_id"] for a in report["arms"]]
    trials = [a["trial_id"] for a in report["arms"]]
    digests = [a["arm_config_digest"] for a in report["arms"]]
    assert len(set(ids)) == 6 and len(set(trials)) == 6 \
        and len(set(digests)) == 6
    # the digest verification table: all 6 frozen digests matched
    table = report["digest_verification_table"]
    assert len(table) == 6 and all(r["digest_match"] for r in table)
    # the run report's per-arm block carries COUNTS ONLY: no booked PnL
    # and no metric values of any kind
    arms_blob = json.dumps(report["arms"])
    for banned in ("total_pnl", "expectancy", "break_even", "mdd",
                   "gross_positive"):
        assert banned not in arms_blob
    for arm in report["arms"]:
        assert arm["outcome_fields"] == "zeroed_and_labelled_not_evidence"
        assert arm["leak_scan"] == "clean"
    # per-record flags + zeroed outcome fields + labels
    records = read_ledger(ledger)
    assert len(records) == 6
    for rec in records:
        assert rec["dry_run"] is True and rec["scored"] is False
        assert rec["real_pnl"] is False and rec["published"] is False
        for key in D._MONETARY_BOOK_KEYS:
            assert rec[key] == 0.0
        assert rec["break_even_cost_bps"] is None
        assert rec["mdd_usd"] == 0.0
        assert rec["pair_concentration"] == {}
        assert rec["base"]["pf"] is None
        assert rec["base"]["total_pnl"] == 0.0
        assert rec["dryrun_gate_scaffold"]["evaluated_on"] == \
            "sanitized_placeholders_not_evidence"
        assert rec["dryrun_gate_check"]["note"].startswith("not evidence")
        assert rec["dryrun_structure"]["n_decisions_returned"] == \
            rec["n_decisions"]


def test_dryrun_deterministic_double_generation(fixture, tmp_ledger,
                                                tmp_path):
    """Same inputs -> byte-identical dry-run records; a replay run appends
    nothing (once-only publication via duplicate-record-id refusal)."""
    ledger1 = os.path.join(tmp_ledger, "run1.jsonl")
    ledger2 = os.path.join(tmp_ledger, "run2.jsonl")
    D.run_dryrun(fixture, ledger1, os.path.join(str(tmp_path), "r1.json"),
                 verify_data=False)
    assert sum(1 for line in open(ledger1) if line.strip()) == 6
    # replay into the SAME ledger appends nothing
    D.run_dryrun(fixture, ledger1, os.path.join(str(tmp_path), "r1b.json"),
                 verify_data=False)
    assert sum(1 for line in open(ledger1) if line.strip()) == 6
    # a fresh ledger receives byte-identical lines
    D.run_dryrun(fixture, ledger2, os.path.join(str(tmp_path), "r2.json"),
                 verify_data=False)
    with open(ledger1, "rb") as fh:
        b1 = fh.read()
    with open(ledger2, "rb") as fh:
        b2 = fh.read()
    assert b1 == b2


def test_dryrun_ledger_must_be_temporary(fixture, tmp_path):
    outside = os.path.join(str(tmp_path), "outside.jsonl")
    with pytest.raises(SystemExit, match="DRYRUN_LEDGER_MUST_BE_TEMPORARY"):
        D.run_dryrun(fixture, outside, os.path.join(str(tmp_path), "r.json"),
                     verify_data=False)


def test_recursive_leak_scan_finds_leak():
    clean = {"scored": False, "real_pnl": False, "published": False,
             "dry_run": True, "base": {"total_pnl": 0.0, "pf": None}}
    findings, _ = D.recursive_leak_scan(clean)
    assert findings == []
    leaky = {"scored": False, "real_pnl": False, "published": False,
             "dry_run": True, "base": {"total_pnl": 12.5, "pf": None}}
    findings2, _ = D.recursive_leak_scan(leaky)
    assert any("total_pnl" in f for f in findings2)
    flag = {"scored": True, "real_pnl": False, "published": False,
            "dry_run": True, "base": {"total_pnl": 0.0, "pf": None}}
    findings3, _ = D.recursive_leak_scan(flag)
    assert any("scored" in f for f in findings3)


def test_implementing_readings_logged():
    """Every flagged ambiguity reading is carried by the driver and logged
    at runtime (never silent)."""
    fields = {r["field"] for r in D.IMPLEMENTING_READINGS}
    assert {"a6p2_fold_boundaries", "a6p2_exit_fill_schedule",
            "a6p2_financing_in_dual_book", "a4p1_s0_cap_scope_for_sham",
            "fold_boundary_semantics", "percentile_method"} <= fields
