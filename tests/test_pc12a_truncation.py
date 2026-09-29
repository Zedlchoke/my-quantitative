"""PC12A verification battery §8.1 -- no-lookahead truncation replay
(ERP-tracka law: decisions computed from a data prefix must not change
when data AFTER the cut is removed).

Pipeline level: a deterministic SYNTHETIC mini-panel (minted with the same
encoder the impl lane's panel tests use) drives the full dry pipeline over
window W for the 12 REAL leg configs; the same window is then re-run over
the panel TRUNCATED at t_cut (mid-window: the cut day's volume is zeroed
from the cut minute on, and every later day file is absent).  Every journal
row whose carried timestamps are all <= t_cut must be byte-identical to the
corresponding row of the full run, in order (the hash chain makes the
prefix identity byte-strong: row N depends only on rows < N).

Leg level: for each of the 12 real legs, a deterministic in-test decision
stream is replayed truncated at t_cut on a FRESH leg instance and the
(vote, desired_units, reason_code) sequence prefix must be identical -- this
covers legs that produce few or no rows on synthetic panels (e.g. the
252-day vol-percentile gate of EURUSD-S009).

NO PnL is asserted anywhere (counts and vote/digest identities only).
"""

import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess

import numpy as np
import pytest

from research.pc12a import journal as jr
from research.pc12a import legs as _legs
from research.pc12a import panels as _panels

UTC = dt.timezone.utc
SYMS = ("EURUSD", "GBPUSD", "USDJPY")
MID = {"EURUSD": 1.0850, "GBPUSD": 1.2700, "USDJPY": 155.50}

WORKTREE = pathlib.Path(__file__).resolve().parent.parent
PYTHON = "/Users/hoangminhlong/my-quantitative/.venv/bin/python"
REAL_LEGS_DIR = WORKTREE / "research" / "pc12a" / "legs_config"

WIN_START = dt.date(2024, 6, 5)
WIN_END = dt.date(2024, 6, 18)
TREE_START = dt.date(2024, 5, 1)          # VOLPROF warmup ~25 trading days
CUT_DATE = dt.date(2024, 6, 11)           # Tuesday, mid-window
CUT_MIN = 12 * 60                         # midday cut at 12:00 UTC
T_CUT = dt.datetime(2024, 6, 11, 12, 0, tzinfo=UTC)


def _build_day_files(root: pathlib.Path, sym: str, d: dt.date,
                     zero_vol_from: int = None) -> None:
    """Mint one deterministic synthetic pair-day (same encoder as the impl
    lane's tests).  ``zero_vol_from`` truncates the day AT the cut minute:
    OHLC bytes are preserved verbatim, volume is zeroed from that minute on
    so every later bar becomes untradable carry-forward."""
    seed = d.toordinal() * 10 + SYMS.index(sym)
    weekend = d.weekday() >= 5
    vol = np.zeros(_panels.RECORDS_PER_DAY) if weekend else None
    bid, ask = _panels.synthetic_day_bytes(
        sym, d, mid_level=MID[sym], vol_pattern=vol, seed=seed)
    if zero_vol_from is not None:
        bid = _zero_vol_from(bid, zero_vol_from)
        ask = _zero_vol_from(ask, zero_vol_from)
    (root / sym / "BID" / f"{d.isoformat()}.bi5").write_bytes(bid)
    (root / sym / "ASK" / f"{d.isoformat()}.bi5").write_bytes(ask)


def _zero_vol_from(compressed: bytes, minute: int) -> bytes:
    rec = _panels.decode_bi5(compressed)
    v = rec["v"].copy()                    # frombuffer view is read-only
    v[minute:] = 0.0
    return _panels.compress_bi5(_panels.encode_bi5(
        rec["t"], rec["o"], rec["c"], rec["l"], rec["h"], v))


def _build_full_tree(root: pathlib.Path) -> None:
    for sym in SYMS:
        for side in ("BID", "ASK"):
            (root / sym / side).mkdir(parents=True, exist_ok=True)
    d = TREE_START
    while d <= WIN_END:
        for sym in SYMS:
            _build_day_files(root, sym, d)
        d += dt.timedelta(days=1)


def _build_truncated_tree(full: pathlib.Path, trunc: pathlib.Path) -> None:
    """Copy every day STRICTLY BEFORE the cut; re-mint the cut day with
    volume zeroed from the cut minute; NO day after the cut exists."""
    for sym in SYMS:
        for side in ("BID", "ASK"):
            (trunc / sym / side).mkdir(parents=True, exist_ok=True)
    d = TREE_START
    while d < CUT_DATE:
        for sym in SYMS:
            for side in ("BID", "ASK"):
                shutil.copyfile(full / sym / side / f"{d.isoformat()}.bi5",
                                trunc / sym / side / f"{d.isoformat()}.bi5")
        d += dt.timedelta(days=1)
    for sym in SYMS:
        _build_day_files(trunc, sym, CUT_DATE, zero_vol_from=CUT_MIN)


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    """Full + truncated dry runs of the 12 REAL leg configs on the
    synthetic tree (one CLI subprocess each, like the impl dry-run tests)."""
    base = tmp_path_factory.mktemp("pc12a_trunc")
    full_tree = base / "panels_full"
    trunc_tree = base / "panels_trunc"
    _build_full_tree(full_tree)
    _build_truncated_tree(full_tree, trunc_tree)

    def _cli(tree: pathlib.Path, out: pathlib.Path) -> None:
        env = dict(os.environ)
        env["PC12A_PANEL_ROOTS"] = json.dumps(
            {s: str(tree / s) for s in SYMS})
        r = subprocess.run(
            [PYTHON, "-m", "research.pc12a.run_dry",
             "--legs", str(REAL_LEGS_DIR),
             "--window", f"{WIN_START.isoformat()},{WIN_END.isoformat()}",
             "--out", str(out)],
            cwd=str(WORKTREE), env=env, capture_output=True, text=True,
            timeout=540)
        assert r.returncode == 0, r.stderr[-3000:]

    out_full = base / "out_full"
    out_trunc = base / "out_trunc"
    _cli(full_tree, out_full)
    _cli(trunc_tree, out_trunc)
    return {"full": out_full, "trunc": out_trunc,
            "full_tree": full_tree, "trunc_tree": trunc_tree, "base": base}


# ---------------------------------------------------------------------------
# Pipeline-level prefix identity
# ---------------------------------------------------------------------------


def _parse(stamp: str) -> dt.datetime:
    return dt.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=UTC)


def _row_max_ts(row: dict):
    """Latest instant carried by a row across its timestamp fields (None
    for the HEADER, which roots the chain and always compares equal)."""
    stamps = [row[k] for k in ("ts_decision_utc", "ts_fill_utc", "ts_utc")
              if isinstance(row.get(k), str)]
    return max(_parse(s) for s in stamps) if stamps else None


_CHAIN_FIELDS = ("seq", "prev_row_sha256", "row_sha256")


def _content(row: dict) -> str:
    """Canonical JSON of a row minus the hash-chain bookkeeping fields.

    The chain fields depend on the row's POSITION in the interleaved file;
    main() streams symbol engines sequentially (EURUSD block, then GBPUSD,
    then USDJPY), so post-cut rows of an EARLIER symbol legitimately shift
    the seq/chain of later symbols' rows.  Decision CONTENT must not shift.
    """
    return json.dumps({k: v for k, v in row.items()
                       if k not in _CHAIN_FIELDS},
                      sort_keys=True, separators=(",", ":"))


def _symbol_prefix(journal_path: pathlib.Path, symbol: str) -> list:
    """Content-canonical rows of one symbol whose every carried timestamp
    is <= t_cut (the row's full lifecycle completed inside truncated data),
    in journal order."""
    out = []
    for line in journal_path.read_text().splitlines():
        if not line:
            continue
        row = json.loads(line)
        if row.get("symbol") != symbol:
            continue
        mx = _row_max_ts(row)
        if mx is None or mx <= T_CUT:
            out.append(_content(row))
    return out


def test_truncated_run_prefix_identical_to_full_run(runs):
    jp_full = runs["full"] / "journal.jsonl"
    jp_trunc = runs["trunc"] / "journal.jsonl"
    both_chains_ok = all(jr.verify_chain(str(p))["ok"]
                         for p in (jp_full, jp_trunc))
    assert both_chains_ok

    # (a) per-symbol decision-content prefix identity: every row whose
    # lifecycle completed inside data <= t_cut is IDENTICAL (field for
    # field, except chain bookkeeping) to the full run's row.
    total_decisions = 0
    for sym in SYMS:
        a = _symbol_prefix(jp_full, sym)
        b = _symbol_prefix(jp_trunc, sym)
        assert len(a) == len(b), f"{sym}: prefix length differs"
        assert a == b, (
            f"{sym}: truncated replay diverged from the full run inside "
            f"data <= t_cut (ERP-tracka prefix law)")
        total_decisions += sum(1 for x in a if '"row_kind":"DECISION"' in x)
    # non-vacuous: real decision traffic was compared
    assert total_decisions >= 3, (
        f"prefix too thin to prove anything ({total_decisions} decisions)")

    # (b) BYTE-prefix where the file layout permits it: the first symbol
    # block (EURUSD, processed first by main()) is a contiguous file prefix
    # in both runs; the hash chain makes this comparison sensitive to ANY
    # byte of ANY earlier row.
    full_lines = [x for x in jp_full.read_text().splitlines() if x]
    trunc_lines = [x for x in jp_trunc.read_text().splitlines() if x]
    k = 0
    while k < len(full_lines):
        row = json.loads(full_lines[k])
        mx = _row_max_ts(row)
        if mx is not None and mx > T_CUT:
            break
        k += 1
    assert k > 20, "byte-prefix compared too few rows to prove anything"
    assert full_lines[:k] == trunc_lines[:k], (
        "byte-identical prefix law violated: the truncated run's leading "
        "rows differ from the full run's")


def test_truncated_run_has_no_rows_after_the_cut(runs):
    """The truncated panel physically cannot produce decisions past t_cut
    (no data exists there).  The ONLY tolerated exception is the SWAP
    accrual at the declared 22:00 UTC boundary ON the cut date itself: a
    modeling-calendar event valued from the last tradable bar <= the cut,
    not fabricated future data.  Nothing may reference a later date."""
    for row in jr.read_rows(str(runs["trunc"] / "journal.jsonl")):
        mx = _row_max_ts(row)
        if mx is None or mx <= T_CUT + dt.timedelta(minutes=1):
            continue
        if row.get("row_kind") == "SWAP":
            assert mx.date() == CUT_DATE and mx == dt.datetime(
                CUT_DATE.year, CUT_DATE.month, CUT_DATE.day, 22, 0,
                tzinfo=UTC), f"unexpected post-cut SWAP row: {row}"
            continue
        raise AssertionError(
            f"row past the cut fabricated from absent data: {row}")


def test_truncated_data_preserves_pre_cut_bytes(runs):
    """The truncation itself is surgical: pre-cut days are byte-copies and
    the cut day's OHLC payload is unchanged (only volume was zeroed)."""
    for sym in SYMS:
        d = TREE_START
        while d < CUT_DATE:
            for side in ("BID", "ASK"):
                a = (runs["full_tree"] / sym / side
                     / f"{d.isoformat()}.bi5").read_bytes()
                b = (runs["trunc_tree"] / sym / side
                     / f"{d.isoformat()}.bi5").read_bytes()
                assert a == b
            d += dt.timedelta(days=1)
        for side in ("BID", "ASK"):
            full = _panels.decode_bi5(
                (runs["full_tree"] / sym / side
                 / f"{CUT_DATE.isoformat()}.bi5").read_bytes())
            trunc = _panels.decode_bi5(
                (runs["trunc_tree"] / sym / side
                 / f"{CUT_DATE.isoformat()}.bi5").read_bytes())
            for f in ("t", "o", "c", "l", "h"):
                assert np.array_equal(full[f], trunc[f]), (
                    f"OHLC mutated by truncation: {sym} {side} {f}")
            assert (trunc["v"][CUT_MIN:] == 0).all()
            assert np.array_equal(full["v"][:CUT_MIN], trunc["v"][:CUT_MIN])
    # and no day file exists after the cut in the truncated tree
    assert not (runs["trunc_tree"] / "EURUSD" / "BID"
                / "2024-06-12.bi5").exists()


def test_full_run_reports_all_twelve_real_legs(runs):
    report = json.loads(
        (runs["full"] / "DRY_RUN_REPORT.json").read_text())
    assert len(report["legs"]) == 12
    on_disk = {p.stem for p in REAL_LEGS_DIR.glob("*.json")}
    assert set(report["legs"]) == on_disk


# ---------------------------------------------------------------------------
# Leg-level vote-sequence prefix identity (fresh instance per replay)
# ---------------------------------------------------------------------------


def _day_buffer(n_days=20, start=dt.date(2024, 5, 3)):
    """Hand-checkable 20-weekday buffer with three activity plateaus (the
    impl lane's profile construction fixture pattern)."""
    buf = []
    day = start
    while len(buf) < n_days:
        if day.weekday() < 5:
            mids = np.array([1.0800 if i % 3 == 0 else
                             (1.0850 if i % 3 == 1 else 1.0900)
                             for i in range(480)])
            vols = np.array([5.0 if i % 3 == 1 else 3.0
                             for i in range(480)])
            buf.append({
                "date": day, "mid_close": mids, "bid_vol": vols,
                "bid_high": mids + 1e-5, "bid_low": mids - 1e-5,
                "tradable": np.ones(480, dtype=bool),
                "day_high": float(mids.max() + 1e-5),
                "day_low": float(mids.min() - 1e-5),
                "day_close": float(mids[-1]),
                "last_bid_close": float(mids[-1]),
                "last_ask_close": float(mids[-1] + 2e-5),
            })
        day += dt.timedelta(days=1)
    return buf


def _synthetic_bar_stream(n_bars=400,
                          t0=dt.datetime(2024, 6, 10, 7, 0, tzinfo=UTC)):
    """Deterministic M1 decision contexts oscillating across the fixture
    profile's VA edges (drives VC1/VC2/VC3 entries, exits, cooldowns)."""
    rng = np.random.default_rng(42)
    levels = np.concatenate([
        rng.choice([1.0788, 1.0851, 1.0882, 1.0833, 1.0800], size=n_bars)])
    out = []
    for i, lvl in enumerate(levels):
        ts = t0 + dt.timedelta(minutes=i)
        prev = float(levels[i - 1]) if i else 1.0850
        out.append((ts, float(lvl), prev))
    return out


def _drive_volprof(leg: _legs.BaseLeg, profile, stream, cut: dt.datetime):
    """Feed the bar stream to a VOLPROF leg; stop at the cut."""
    votes = []
    for ts, lvl, prev in stream:
        if ts > cut:
            break
        ctx = _legs.BarContext(
            ts=ts, symbol=leg.identity.symbol, mid_close=lvl,
            mid_close_prev=prev, bid_open=lvl - 2e-5, ask_open=lvl + 2e-5,
            bid_close=lvl - 2e-5, ask_close=lvl + 2e-5,
            bid_low=lvl - 3e-5, ask_high=lvl + 3e-5, atr60=0.0005,
            in_entry_window=True, is_flat_instant=False, day=ts.date(),
            profile=profile, last_data_ts=ts)
        d = leg.on_bar(ctx)
        votes.append(None if d is None else
                     (d.vote, d.desired_units, d.reason_code))
    return votes


def _drive_daily(leg: _legs.BaseLeg, bars, cut: dt.datetime):
    votes = []
    for bar in bars:
        if bar["available"] > cut:
            break
        d = leg.on_daily_bar(bar)
        votes.append(None if d is None else
                     (d.vote, d.desired_units, d.reason_code))
    return votes


def _daily_bars(n=60, start=dt.date(2024, 3, 4)):
    """Deterministic daily aggregates with trend breaks (drives Donchian,
    weekday-gate and MACD-leg decisions)."""
    rng = np.random.default_rng(7)
    bars = []
    px = 1.0850
    day = start
    for i in range(n):
        while day.weekday() >= 5:
            day += dt.timedelta(days=1)
        drift = 0.004 if (i // 7) % 2 == 0 else -0.003
        px = px + drift + float(rng.normal(0, 0.0015))
        hi, lo = px + 0.002, px - 0.002
        bars.append({
            "date": day, "high": hi, "low": lo, "close": px,
            "day_close": px, "last_bid_close": px - 1e-5,
            "last_ask_close": px + 1e-5,
            "available": dt.datetime.combine(
                day, dt.time(0, 0), tzinfo=UTC) + dt.timedelta(days=1),
        })
        day += dt.timedelta(days=1)
    return bars


def test_leg_level_vote_prefix_identity_all_twelve_real_configs():
    cfgs = _legs.load_leg_configs(str(REAL_LEGS_DIR))
    assert len(cfgs) == 12
    profile = _legs.build_profile(
        dt.datetime(2024, 6, 7, 20, 0, tzinfo=UTC), _day_buffer())
    stream = _synthetic_bar_stream()
    bars = _daily_bars()
    leg_cut = dt.datetime(2024, 6, 10, 7, 0, tzinfo=UTC) \
        + dt.timedelta(minutes=200)
    bar_cut = bars[37]["available"]
    decisions_seen = 0
    for cfg in cfgs:
        ident = _legs.make_identity(cfg)
        leg = _legs.build_leg(cfg)
        if isinstance(leg, _legs.VolprofLeg):
            leg.on_profile(profile)
            full = _drive_volprof(leg, profile, stream, stream[-1][0])
            repl = _drive_volprof(_legs.build_leg(cfg), profile, stream,
                                  leg_cut)
        else:
            full = _drive_daily(leg, bars, bars[-1]["available"])
            repl = _drive_daily(_legs.build_leg(cfg), bars, bar_cut)
        # the replayed sequence is a true PREFIX of the full sequence --
        # no vote past data the truncated leg cannot have seen
        assert repl == full[:len(repl)], (
            f"{ident.candidate_id}: truncated replay diverged at decision "
            f"{len(repl)} (ERP-tracka prefix law)")
        decisions_seen += sum(1 for v in full if v is not None)
    assert decisions_seen >= 3, (
        "synthetic streams produced too few leg decisions to prove the "
        f"prefix law ({decisions_seen} nonzero decisions across 12 legs)")
