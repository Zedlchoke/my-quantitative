"""A1-controls Phase I tests (amendment FX-RANGEFADE-2M-SHADOW-V1).

Covers the five fixtures the amendment §3 requires before ACTIVATION,
plus the golden no-diff law on the frozen strategy path:

(a) parity / strategy no-diff — sha-pinned frozen library files, frozen
    sleeve decision functions and the frozen main-loop sleeve block
    (captured BEFORE the A1 change-set), plus a behavioral golden: the
    SAME synthetic H1 bars through the REAL f_rangeexp + PairBook
    decision methods must produce the SAME signals/decisions as the
    pre-change capture;
(b) control-arm fixture — synthetic 3-day quote series (Fri/Sat/Mon)
    with hand-computed CTRL-SHORT-ALWAYS and CTRL-SHADOW-MATCHED PnL,
    including the weekend boundary and the missed-20:00 catch-up;
(c) cost-field fixture — one hand-computed fill with fee/slip/stress;
(d) schema fixture — old journal rows (no new fields) parse unchanged
    and report NOT_RUN_COST_FIELDS; never backfilled;
(e) session-bucket fixture — fills in different sessions get the right
    bucket median x2.0 from session_spread_curve.json.

LAW under test: the A1 additions are PARALLEL books + REPORTING only —
zero behavior diff on the live sleeves.
"""
import hashlib
import inspect
import json
import types

import numpy as np
import pandas as pd
import pytest

import fx_shadow_core as C
import shadow_daemon as D          # noqa: E402  (adds frozen lib to sys.path)
import engine as E                 # noqa: E402
import v2_lib as V                 # noqa: E402

GOLDEN = json.loads((D.ROOT / "tests" / "golden_a1_phase1.json").read_text())
COST_BOOK = C.CostBook.from_file(D.COST_CURVE)
PIPS = {p: m["pip"] for p, m in D.PAIRS.items()}


def sha_src(fn) -> str:
    return "sha256:" + hashlib.sha256(inspect.getsource(fn).encode()).hexdigest()


def resolve_frozen(name: str):
    """Golden keys are function names (optionally dotted); resolve against
    the two source modules without guessing the owner module."""
    parts = name.split(".")
    for mod in (C, D):
        obj = mod
        try:
            for part in parts:
                obj = getattr(obj, part)
            return obj
        except AttributeError:
            continue
    raise AssertionError(f"cannot resolve frozen symbol: {name}")


def frozen_block_text() -> str:
    lines = D.HERE.joinpath("shadow_daemon.py").read_text().split("\n")
    b = next(i for i, l in enumerate(lines) if "FROZEN-SLEEVE-BLOCK-BEGIN" in l)
    e = next(i for i, l in enumerate(lines) if "FROZEN-SLEEVE-BLOCK-END" in l)
    return "\n".join(lines[b + 1:e])


# ======================================================================
# (a) parity / strategy no-diff
# ======================================================================
def test_a_frozen_library_files_byte_identical():
    for name, sha in GOLDEN["frozen_files"].items():
        p = D.HERE.parent.parent / "EURUSD-OPEN-SEARCH-V2" / "scripts" / name
        assert "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest() == sha, \
            f"frozen library {name} changed — strategy law violated"


def test_a_frozen_decision_functions_byte_identical():
    for name, sha in GOLDEN["frozen_functions"].items():
        assert sha_src(resolve_frozen(name)) == sha, \
            f"frozen function {name} changed"


def test_a_frozen_main_loop_sleeve_block_byte_identical():
    blk = GOLDEN["frozen_main_loop_block"]
    text = frozen_block_text()
    assert len(text.split("\n")) == blk["n_lines"]
    assert "sha256:" + hashlib.sha256(text.encode()).hexdigest() == blk["sha256"], \
        "the frozen sleeve decision block was touched — A1 violation"


# ---- behavioral golden: same bars in, same decisions out --------------
def _synth_df(days):
    rows = []
    base = 1.1000
    for di, day0 in enumerate(days):
        wide = (di % 2 == 1)
        for h in range(20):
            ts = day0 + h * 3600
            amp = 0.0090 if wide else 0.0015
            drift = (h / 19.0 - 0.5) * amp
            b_o = base + drift
            b_c = base + drift + (0.0004 if wide else 0.0002)
            b_h = max(b_o, b_c) + 0.0008 if wide else max(b_o, b_c) + 0.0002
            b_l = min(b_o, b_c) - 0.0008 if wide else min(b_o, b_c) - 0.0002
            spr = 0.0002
            rows.append({"ts": pd.Timestamp(ts, unit="s", tz="UTC"),
                         "b_o": b_o, "b_h": b_h, "b_l": b_l, "b_c": b_c,
                         "a_o": b_o + spr, "a_c": b_c + spr,
                         "s_open": spr, "s_close": spr})
    return pd.DataFrame(rows)


DAYS = [1757894400 + 86400 * i for i in range(6)]  # 2025-09-15 Mon .. Sat


class NullJournal:
    def log(self, *a, **k):
        return {}


def _fresh_book(seed_days):
    book = D.PairBook.__new__(D.PairBook)
    book.pair, book.pip = "EURUSD", 1e-4
    book.journal = NullJournal()
    book.df = _synth_df(seed_days)
    book.seed_last_ts = int(book.df["ts"].iloc[-1].timestamp())
    book.pos, book.entry_px, book.entry_ts = 0, None, None
    book.realized_usd, book.fills = 0.0, 0
    book.live_bar, book.last_target, book.parity = None, 0, None
    return book


def test_a_same_synth_bars_produce_golden_signals():
    df = _synth_df(DAYS)
    tgt = V.f_rangeexp(V.H1Plane(df), 0.3, 0.7, False)
    assert [int(x) for x in tgt] == GOLDEN["signal_synth"]["targets"]
    assert int(np.count_nonzero(tgt)) == GOLDEN["signal_synth"]["nonzero"] > 0


def test_a_same_synth_bars_produce_golden_decisions():
    """Old-vs-new decision logic: the pre-change capture drives the REAL
    frozen PairBook methods on synthetic bars; the post-change run must
    reproduce it trace-for-trace."""
    df = _synth_df(DAYS)
    book = _fresh_book(DAYS[:1])
    trace = []
    for di in range(1, 6):
        for h in range(20):
            row = df.iloc[di * 20 + h]
            bar = {"ts": int(row["ts"].timestamp()), "b_o": row["b_o"],
                   "b_h": row["b_h"], "b_l": row["b_l"], "b_c": row["b_c"],
                   "a_o": row["a_o"], "a_c": row["a_c"]}
            book.on_closed_bar(bar)
            trace.append([bar["ts"], int(book.last_target),
                          int(book.desired_now())])
    assert trace == GOLDEN["decision_trace"]


def test_a_daemon_signal_path_is_the_frozen_library():
    df = _synth_df(DAYS)
    tgt_daemon, plane = D.targets_from_df(df, 1e-4)
    assert np.array_equal(tgt_daemon, V.f_rangeexp(plane, 0.3, 0.7, False))


def test_a_short_beta_label_pinned():
    assert C.SHORT_BETA_LABEL == "SHORT_BETA_UNSEPARATED — NOT PROMOTABLE"


# ======================================================================
# (b) control-arm fixture: 3-day synthetic series, hand-computed PnL
# ======================================================================
FRI = 1767312000            # 2026-01-02 Fri 00:00 UTC
SAT, MON = FRI + 86400, FRI + 3 * 86400


class FakeBook:
    """Stand-in for the SLEEVE book in the observer loop: only the attrs
    a1_observe_iteration is allowed to READ."""

    def __init__(self, pos=0, entry_px=None, live_ts=None):
        self.pos = pos
        self.entry_px = entry_px
        self.live_bar = types.SimpleNamespace(ts=live_ts) if live_ts is not None else None


class SP:  # constant 2-pip spread quote
    @staticmethod
    def q(bid):
        return {"bid": bid, "ask": bid + 0.0002}


def _mark(h0, bid):
    m = SP.q(bid)
    m["ts"] = h0 + 60.0        # first poll inside the h0 bar
    return m


class Rig:
    """Drives a1_observe_iteration in the daemon's REAL per-poll order:
    (1) capture pre-state (pos + live-bar id), (2) let the simulated
    frozen sleeve block act and roll the H1 bar, (3) observe."""

    def __init__(self, journal, pairs=("EURUSD",)):
        self.journal = journal
        self.ctrl_sa = {p: C.CtrlShortAlwaysBook(p, PIPS[p]) for p in pairs}
        self.ctrl_sm = {p: C.CtrlShadowMatchedBook(p, PIPS[p]) for p in pairs}
        self.books = {p: FakeBook() for p in pairs}
        self.epochs = set()
        self.emitted = False

    def step(self, h0, bids, sleeve=None):
        """bids: {pair: bid}. `sleeve` mutates books (the frozen block's
        position effect) AFTER pre-state capture, like main() does."""
        pre = {p: (b.pos, b.live_bar.ts if b.live_bar is not None else None)
               for p, b in self.books.items()}
        if sleeve is not None:
            sleeve(self.books)
        marks = _mk_marks(h0, bids)
        for b in self.books.values():               # frozen block bar roll
            b.live_bar = types.SimpleNamespace(ts=h0)
        self.emitted = D.a1_observe_iteration(
            self.books, marks, pre, self.ctrl_sa, self.ctrl_sm,
            COST_BOOK, self.journal, self.epochs) or self.emitted


def _mk_marks(h0, bids, ts_off=60.0):
    out = {}
    for p, bid in bids.items():
        m = SP.q(bid)
        m["ts"] = h0 + ts_off
        out[p] = m
    return out


def test_b_ctrl_short_always_hand_computed_3day_with_weekend():
    jp = D.ROOT / "tests" / "_b_sa.jsonl"
    jp.unlink(missing_ok=True)               # no cross-run accumulation
    journal = D.CostJournal(jp, COST_BOOK, PIPS)
    rig = Rig(journal)

    bids = {}                                    # (day0, hour) -> bid
    def setq(day, h, bid):
        bids[(day, h)] = bid
    for h in range(24):
        setq(FRI, h, 1.1000)
    setq(FRI, 20, 1.0950)                        # Friday flat mark (20:00)
    for h in range(24):
        setq(SAT, h, 1.1000)                     # weekend: ignored
        setq(MON, h, 1.1010)
    setq(MON, 20, 1.1000)                        # Monday flat mark

    for day in (FRI, SAT, MON):
        for h in range(24):
            rig.step(day + h * 3600, {"EURUSD": bids[(day, h)]})

    sa = rig.ctrl_sa["EURUSD"]
    assert sa.fills == 2
    # Friday: short 1.1000 @01:00 open (first FILLABLE open after 00:00 —
    # the 00:00 open is NOT fillable under the sleeve law), flat @1.0952
    # (ask) at the 20:00 boundary -> +48 pips x $15 = +$720.00 gross.
    # Monday: short 1.1010 @01:00, flat @1.1002 -> +8 pips = +$120.00.
    assert sa.realized_gross_usd == pytest.approx(720.0 + 120.0, abs=0.01)
    fee_e = COST_BOOK.fee_usd(1.1000)            # 3.30
    fee_x = COST_BOOK.fee_usd(1.0952)            # 3.2856
    fee_m_e = COST_BOOK.fee_usd(1.1010)          # 3.303
    fee_m_x = COST_BOOK.fee_usd(1.1002)          # 3.3006
    slip = COST_BOOK.slip_usd(COST_BOOK.slip_pips)  # 1.50
    expected_net = ((720.0 - (fee_e + slip) - (fee_x + slip))
                    + (120.0 - (fee_m_e + slip) - (fee_m_x + slip)))
    assert sa.realized_net_usd == pytest.approx(expected_net, abs=0.02)
    assert sa.realized_net_usd == pytest.approx(820.81, abs=0.02)   # hand total
    # stress view: Asia (0.30 x2 -> $9.00/side) entries, NY exits, both days
    expected_stress = ((720.0 - (fee_e + 9.0) - (fee_x + 9.0))
                       + (120.0 - (fee_m_e + 9.0) - (fee_m_x + 9.0)))
    assert sa.realized_stress_usd == pytest.approx(expected_stress, abs=0.02)
    # weekend: book flat all Saturday/Sunday, NO new opens (fills stay 2)

    rows = [json.loads(l) for l in
            (D.ROOT / "tests" / "_b_sa.jsonl").read_text().splitlines() if l.strip()]
    sa_rows = [r for r in rows if r.get("arm") == C.CTRL_SHORT_ALWAYS]
    assert [r["event"] for r in sa_rows] == ["ctrl_open", "ctrl_close",
                                             "ctrl_open", "ctrl_close"]
    assert sa_rows[0]["entry_px"] == 1.1000 and sa_rows[0]["dir"] == -1
    assert sa_rows[0]["session_bucket"] == "Asia"
    assert sa_rows[1]["reason"] == "force_flat" and sa_rows[1]["exit_px"] == 1.0952
    assert sa_rows[1]["realized_net"] == pytest.approx(710.41, abs=0.01)
    assert sa_rows[1]["round_trip_id"] == sa_rows[0]["round_trip_id"]
    # 00:00 open is NOT fillable (sleeve fill law) — first open is 01:00
    assert sa_rows[0]["entry_ts"] == FRI + 3600
    # sleeve untouched: no fill_open/fill_close rows in this scenario
    assert not [r for r in rows if r["event"].startswith("fill")]
    journal.path.unlink()


def test_b_ctrl_shadow_matched_hand_computed_inverted():
    jp = D.ROOT / "tests" / "_b_sm.jsonl"
    jp.unlink(missing_ok=True)               # no cross-run accumulation
    journal = D.CostJournal(jp, COST_BOOK, PIPS)
    rig = Rig(journal)

    # 10:00 roll: sleeve opens LONG 1.5 @1.1000 (its fill px = the ask)
    def sleeve_open_long(books):
        books["EURUSD"].pos, books["EURUSD"].entry_px = 1, 1.1000

    # 14:00 roll: sleeve closes @1.1050 (its close px = the bid)
    def sleeve_close(books):
        books["EURUSD"].pos, books["EURUSD"].entry_px = 0, None

    rig.step(FRI + 9 * 3600, {"EURUSD": 1.0998})             # warm-up bar
    rig.step(FRI + 10 * 3600, {"EURUSD": 1.0998}, sleeve_open_long)
    rig.step(FRI + 14 * 3600, {"EURUSD": 1.1050}, sleeve_close)

    sm = rig.ctrl_sm["EURUSD"]
    assert sm.pos == 0 and sm.fills == 1
    # exits identical, entry sign-inverted: ctrl short 1.1000 -> 1.1050
    assert sm.realized_gross_usd == pytest.approx(-750.0, abs=0.01)
    fee_e, fee_x = COST_BOOK.fee_usd(1.1000), COST_BOOK.fee_usd(1.1050)
    slip = COST_BOOK.slip_usd(COST_BOOK.slip_pips)
    assert sm.realized_net_usd == pytest.approx(
        -750.0 - (fee_e + slip) - (fee_x + slip), abs=0.01)
    assert sm.realized_net_usd == pytest.approx(-759.615, abs=0.01)
    # stress: London entry + Overlap exit, 0.30 x2 = 0.6 pip -> $9.00/side
    assert sm.realized_stress_usd == pytest.approx(
        -750.0 - (fee_e + 9.0) - (fee_x + 9.0), abs=0.01)

    rows = [json.loads(l) for l in
            (D.ROOT / "tests" / "_b_sm.jsonl").read_text().splitlines() if l.strip()]
    sm_rows = [r for r in rows if r.get("arm") == C.CTRL_SHADOW_MATCHED]
    o = next(r for r in sm_rows if r["event"] == "ctrl_open")
    cl = next(r for r in sm_rows if r["event"] == "ctrl_close")
    assert o["dir"] == -1 and o["mirrors_sleeve_dir"] == 1 and o["entry_px"] == 1.1000
    assert cl["exit_px"] == 1.1050 and cl["round_trip_id"] == o["round_trip_id"]
    assert cl["realized_net"] == pytest.approx(-759.615, abs=0.01)
    journal.path.unlink()


def test_b_missed_20k_boundary_catches_up_and_reopens():
    """Daemon down across the Friday 20:00 flat: on the next observed
    fillable open (Monday 01:00) the book must catch-up-flat at THAT mark,
    then reopen for the new day."""
    sa = C.CtrlShortAlwaysBook("EURUSD", PIPS["EURUSD"])
    assert sa.on_h1_open(FRI + 3600, 1.1000, 1.1002, COST_BOOK, 2.0)
    # ...daemon down... resumes at the Monday 01:00 bar open:
    h0 = MON + 3600
    ev_flat = sa.force_flat(h0, 1.1010, 1.1012, COST_BOOK, 2.0)
    assert ev_flat["reason"] == "force_flat"
    assert ev_flat["pnl_usd"] == pytest.approx(-180.0, abs=0.01)  # -12 pips x $15
    assert ev_flat["realized_net"] == pytest.approx(
        -180.0 - (COST_BOOK.fee_usd(1.1000) + 1.5) - (COST_BOOK.fee_usd(1.1012) + 1.5),
        abs=0.01)
    ev_open = sa.on_h1_open(h0, 1.1010, 1.1012, COST_BOOK, 2.0)
    assert ev_open is not None and ev_open["dir"] == -1
    assert sa.pos == -1 and sa.entry_px == 1.1010


def test_b_weekend_never_opens_and_epoch_events_recorded():
    jp = D.ROOT / "tests" / "_b_we.jsonl"
    jp.unlink(missing_ok=True)               # no cross-run accumulation
    journal = D.CostJournal(jp, COST_BOOK, PIPS)
    rig = Rig(journal, pairs=("EURUSD", "GBPUSD"))
    for h in range(24):                          # all Saturday
        rig.step(SAT + h * 3600, {"EURUSD": 1.1000, "GBPUSD": 1.2700})
    for sa in rig.ctrl_sa.values():
        assert sa.fills == 0 and sa.pos == 0 and sa.realized_gross_usd == 0.0
    rows = [json.loads(l) for l in
            (D.ROOT / "tests" / "_b_we.jsonl").read_text().splitlines() if l.strip()]
    assert not [r for r in rows if r["event"].startswith("ctrl_")]
    # per-epoch USD exposure rows still recorded on the weekend
    epochs = [r for r in rows if r["event"] == C.EPOCH_REPORT_EVENT]
    assert epochs and all(r["usd_net_notional_usd"] == 0.0 for r in epochs)
    journal.path.unlink()


def test_b_usd_exposure_hand_computed():
    mids = {"EURUSD": 1.1000, "GBPUSD": 1.3000}
    blk = C.usd_exposure_block({"EURUSD": 1, "GBPUSD": 1}, mids)
    assert blk["usd_same_side_notional_lots"] == 3.0
    assert blk["usd_same_side_notional_usd"] == pytest.approx(360000.0)
    assert blk["usd_net_notional_usd"] == pytest.approx(360000.0)
    assert blk["per_pair_direction"] == {"EURUSD": 1, "GBPUSD": 1}
    blk = C.usd_exposure_block({"EURUSD": 1, "GBPUSD": -1}, mids)
    assert blk["usd_same_side_notional_lots"] == 0.0      # nothing fully same-side
    assert blk["usd_net_notional_lots"] == 0.0
    assert blk["usd_net_notional_usd"] == pytest.approx(1.1 * 1.5 * 1e5 - 1.3 * 1.5 * 1e5)
    blk = C.usd_exposure_block({"EURUSD": -1, "GBPUSD": -1}, mids)
    assert blk["usd_same_side_notional_usd"] == pytest.approx(360000.0)
    assert blk["usd_net_notional_usd"] == pytest.approx(-360000.0)
    blk = C.usd_exposure_block({"EURUSD": 1, "GBPUSD": 0}, mids)
    assert blk["usd_same_side_notional_lots"] == 1.5
    assert blk["usd_net_notional_usd"] == pytest.approx(165000.0)


# ======================================================================
# (c) cost-field fixture: one hand-computed fill
# ======================================================================
def test_c_fill_row_carries_hand_computed_cost_fields(tmp_path):
    jp = tmp_path / "c.jsonl"
    j = D.CostJournal(jp, COST_BOOK, PIPS)
    j.marks_ref = {"EURUSD": _mark(FRI + 6 * 3600, 1.09975)}   # 06:59 Asia
    j.log("fill_open", pair="EURUSD", dir=1, entry_px=1.1000, lots=1.5,
          quote_ts=FRI + 6 * 3600 + 60.0, spread=0.00025, mark="test")
    row = json.loads(jp.read_text().splitlines()[-1])
    assert C.cost_field_status(row) == "OK"
    assert row["fee_bps"] == 0.2 and row["slip_pips"] == 0.1
    assert row["spread_at_fill"] == pytest.approx(2.5)         # 0.00025 / 1e-4
    assert row["session_bucket"] == "Asia"
    assert row["cost_book_digest"] == COST_BOOK.digest
    assert row["stress_fee"] == pytest.approx(3.30, abs=0.005)   # 1.1000x150k x0.2bp
    assert row["stress_slip"] == pytest.approx(9.0, abs=0.005)   # 0.6 pip x $15
    rt = row["round_trip_id"]

    j.marks_ref = {"EURUSD": _mark(FRI + 14 * 3600, 1.1050)}   # Overlap
    j.log("fill_close", pair="EURUSD", dir=1, entry_px=1.1000,
          exit_px=1.1050, pnl_usd=750.0, lots=1.5, reason="signal")
    row = json.loads(jp.read_text().splitlines()[-1])
    assert row["round_trip_id"] == rt
    fee_e, fee_x = 3.30, 3.315
    assert row["realized_net"] == pytest.approx(750.0 - (fee_e + 1.5) - (fee_x + 1.5), abs=0.01)
    assert row["realized_net"] == pytest.approx(740.385, abs=0.01)   # HAND-COMPUTED
    # stress parallel view: +9.00 (Asia) and +9.00 (Overlap) spread instead of 1.5
    assert row["realized_net_stress"] == pytest.approx(750.0 - 12.30 - 12.315, abs=0.01)
    assert row["session_bucket"] == "Overlap"


def test_c_restored_position_close_discloses_missing_entry_ctx(tmp_path):
    jp = tmp_path / "c2.jsonl"
    j = D.CostJournal(jp, COST_BOOK, PIPS)
    j.marks_ref = {"EURUSD": _mark(FRI + 13 * 3600, 1.1050)}
    j.log("force_flat", pair="EURUSD", dir=1, entry_px=1.1000, exit_px=1.1050,
          pnl_usd=750.0, lots=1.5, reason="force_flat")
    row = json.loads(jp.read_text().splitlines()[-1])
    assert row["round_trip_id"] is None
    assert row["rt_note"] == "entry_cost_ctx_missing_restored_position"
    # only the EXIT-side declared cost is charged; disclosed, not zeroed
    assert row["realized_net"] == pytest.approx(
        750.0 - (COST_BOOK.fee_usd(1.1050) + 1.5), abs=0.01)


# ======================================================================
# (d) schema fixture: old rows parse unchanged; never backfilled
# ======================================================================
def _legacy_rows():
    return [
        {"seq": 1, "event_id": "fxaaa", "ts": "2026-09-24T01:05:00+00:00",
         "event": "fill_open", "pair": "EURUSD", "dir": 1, "entry_px": 1.1000,
         "entry_ts": 1767000000, "lots": 1.5, "spread": 3e-05,
         "mark": "truefx_indicative"},
        {"seq": 2, "event_id": "fxbbb", "ts": "2026-09-24T02:05:00+00:00",
         "event": "fill_close", "pair": "EURUSD", "dir": 1, "entry_px": 1.1000,
         "exit_px": 1.1050, "pnl_usd": 750.0, "lots": 1.5,
         "realized_total": 750.0, "reason": "signal"},
    ]


def test_d_old_rows_replay_unchanged_and_report_not_run_cost_fields():
    legacy = _legacy_rows()
    lines = [json.dumps(r) for r in legacy]
    rep = C.replay_journal(lines, seed_last_ts={"EURUSD": 0, "GBPUSD": 0})
    assert rep["realized_usd"] == pytest.approx(750.0)
    assert rep["events_bad"] == 0
    for r in legacy:
        assert C.cost_field_status(r) == C.NOT_RUN_COST_FIELDS
        assert all(k not in r for k in C.COST_ROW_FIELDS), "old row backfilled?!"
    newish = dict(legacy[0], **{k: 1 for k in C.COST_ROW_FIELDS})
    assert C.cost_field_status(newish) == "OK"


def test_d_mixed_journal_replay_via_daemon_filter(tmp_path):
    """The daemon filters A1 rows before the frozen replay: sleeve state
    stays exact, control books rebuild, events_bad stays 0."""
    lines = [json.dumps(r) for r in _legacy_rows()]
    lines.append(json.dumps({"seq": 3, "event": "ctrl_open", "arm": "ctrl_short_always",
                             "pair": "GBPUSD", "dir": -1, "entry_px": 1.3000,
                             "entry_ts": 1767000000, "lots": 1.5,
                             "session_bucket": "Asia", "round_trip_id": "rtx"}))
    lines.append(json.dumps({"seq": 4, "event": "epoch_report", "epoch_ts": 1767000000,
                             "usd_net_notional_usd": 0.0}))
    raw = (tmp_path / "m.jsonl")
    raw.write_text("\n".join(lines) + "\n")
    replay_lines, a1_lines = [], []
    for ln in raw.read_text().splitlines():
        ev = json.loads(ln).get("event") if ln.strip() else None
        (a1_lines if ev in C.A1_IGNORED_BY_SLEEVE_REPLAY else replay_lines).append(ln)
    rep = C.replay_journal(replay_lines, seed_last_ts={"EURUSD": 0, "GBPUSD": 0})
    assert rep["realized_usd"] == pytest.approx(750.0) and rep["events_bad"] == 0
    ctrl = C.replay_control_events(a1_lines)
    sa = ctrl["ctrl_short_always"]["GBPUSD"]
    assert sa["pos"] == -1 and sa["entry_px"] == 1.3000 and sa["fills"] == 1
    # idempotent under duplication (restart identity, same rule as sleeve)
    dup = C.replay_control_events(a1_lines + a1_lines)
    assert dup == ctrl


def test_d_live_journal_old_rows_are_not_backfilled():
    jl = D.ROOT / "shadow_journal.jsonl"
    if not jl.is_file():
        pytest.skip("no live journal in this checkout")
    legacy_fill_rows = 0
    for line in jl.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("event") in ("fill_open", "fill_close", "force_flat") \
                and "cost_book_digest" not in row:
            legacy_fill_rows += 1
            assert C.cost_field_status(row) == C.NOT_RUN_COST_FIELDS
    assert legacy_fill_rows > 0, "expected pre-T_ctrl gross-only rows"


# ======================================================================
# (e) session-bucket fixture
# ======================================================================
def test_e_every_bucket_present_with_stress_median_x2():
    cfg = COST_BOOK.cfg
    for pair in ("EURUSD", "GBPUSD"):
        assert set(cfg["session_median_pips"][pair]) == {
            "Asia", "London", "Overlap", "NY", "Rollover"}
        for bucket in ("Asia", "London", "Overlap", "NY", "Rollover"):
            med = COST_BOOK.median_pips(pair, bucket)
            assert COST_BOOK.stress_pips(pair, bucket) == pytest.approx(med * 2.0)
    assert COST_BOOK.stress_multiplier == 2.0


@pytest.mark.parametrize("hour,bucket", [(3, "Asia"), (8, "London"), (13, "Overlap"),
                                         (17, "NY"), (22, "Rollover")])
def test_e_fills_land_in_the_right_bucket_with_x2_charge(hour, bucket):
    epoch = FRI + hour * 3600 + 60
    px = 1.1000
    for pair, base_med in (("EURUSD", 0.30), ("GBPUSD", 0.80)):
        f = COST_BOOK.fill_cost_fields(pair, C.session_bucket_of_epoch(epoch),
                                       2.0, px)
        assert f["session_bucket"] == bucket
        assert f["stress_slip"] == pytest.approx(base_med * 2.0 * 15.0, abs=0.005)
        assert f["stress_fee"] == pytest.approx(COST_BOOK.fee_usd(px), abs=0.005)
        assert f["fee_bps"] == 0.2 and f["slip_pips"] == 0.1


def test_e_seed_status_disclosed_and_digest_pinned():
    cfg = COST_BOOK.cfg
    assert "SEED" in cfg["status"]
    assert "census" in cfg["seed_disclosure"].lower()
    raw = D.COST_CURVE.read_bytes()
    assert COST_BOOK.digest == "sha256:" + hashlib.sha256(raw).hexdigest()[:16]
