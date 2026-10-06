"""PIT producer-prefix tests (R5 review-extra, round co-owner-review-fix-1).

Truncation/mutation tests must exercise the PRODUCER PREFIX — bars + roll
table + metadata + selection inputs — not just bars with a static roll table.

Producer channels mutated/truncated here:
  1. bars          – ContractData.daily_trades per contract
  2. roll table    – RollRow list REBUILT through RollEngine on truncated
                     contracts (never a statically-filtered copy)
  3. metadata      – per-session producer reference series consumed by the
                     strategy through a PIT wrapper
  4. selection     – nested TRAIN params chosen by a selector pinned at
                     train_end (futbt.walkforward.run_selection)

Positive laws: replaying on the truncated producer must reproduce every
already-emitted decision at sessions <= cutoff (prefix determinism), and
garbage in every post-cutoff channel must change nothing at or before the
cutoff (future-mutation invariance).

Counter-tests (teeth): deliberately LOOKAHEAD implementations that read
post-cutoff producer state (bars / roll rows / metadata / selection) DO
change decisions <= cutoff — the invariance helpers must catch them, which
proves the positive tests are not vacuous.
"""
import copy
import datetime as dt
import random
import unittest
from dataclasses import dataclass, replace

from futbt.calendarx import WeekdayCalendar
from futbt.costs import CostBook
from futbt.engine import BacktestEngine, Decision, EngineConfig
from futbt.journal import TradeJournal
from futbt.rawdata import ContractData, ContractIdentity
from futbt.roll import RollEngine, RollTable
from futbt.walkforward import (WalkForwardPlanner,
                               assert_future_mutation_invariance,
                               assert_prefix_determinism,
                               replay_deterministic)

from tests.helpers import make_bar

CAL_START = dt.date(2026, 1, 5)
CAL_END = dt.date(2026, 5, 29)
CUTOFF = dt.date(2026, 3, 31)          # after the Feb-27 roll, before Apr-30
MUT_SEED = 20261002
HORIZON, EMBARGO, N_FOLDS, TRAIN_FRAC = 3, 1, 4, 0.35
SYMBOL = "ES"

# rolls under the declared calendar rule: last session before day-1 of the
# expiry month -> ESH6 rolls 2026-02-27, ESM6 rolls 2026-04-30
_CONTRACT_SPECS = [
    ("ESH6", 101, dt.date(2026, 3, 18), 6000.0),
    ("ESM6", 102, dt.date(2026, 5, 20), 6050.0),
    ("ESU6", 103, dt.date(2026, 9, 18), 6100.0),
]


def build_calendar():
    return WeekdayCalendar(CAL_START, CAL_END)


def raw_contracts(sessions):
    out = []
    for ls, conid, ltd, base in _CONTRACT_SPECS:
        bars = [make_bar(s, base + 1.0 * i, base + 1.0 * i + 5.0,
                         base + 1.0 * i - 5.0, base + 1.0 * i, v=1000.0)
                for i, s in enumerate(sessions) if s <= ltd]
        out.append(ContractData(
            identity=ContractIdentity(symbol=SYMBOL, local_symbol=ls,
                                      conid=conid, last_trade_date=ltd),
            daily_trades=bars))
    return out


@dataclass
class ProducerState:
    """The full data-producer prefix surface decisions may depend on."""
    contracts: list            # channel 1: bars
    roll_rows: list            # channel 2: roll table rows
    rule_config: dict          # channel 2b: roll-rule metadata
    metadata: list             # channel 3: per-session producer metadata


class MetadataPIT:
    """PIT accessor: strategies may only read metadata entries at sessions
    <= their decision asof."""

    def __init__(self, entries):
        self.entries = sorted(entries, key=lambda e: e["session"])

    def latest_ref(self, asof: dt.date) -> float | None:
        ref = None
        for e in self.entries:
            if dt.date.fromisoformat(e["session"]) <= asof:
                ref = e["ref_px"]
        return ref

    def last_entry_overall(self) -> dict:
        """LEAK helper: the final entry, future included."""
        return self.entries[-1]


class PinnedCloses:
    """Selection view pinned at `asof` (leaky=False). leaky=True reads all
    bars regardless of asof — the lookahead counter-test."""

    def __init__(self, contracts, sessions, asof, leaky=False):
        limit = sessions[-1] if leaky else asof
        vals = sorted(b.c for cd in contracts for b in cd.daily_trades
                      if b.t <= limit)
        self.median = vals[len(vals) // 2] if vals else None

    def median_close(self):
        return self.median


def make_selector(leaky: bool = False):
    def selector(view):
        med = view.median_close()
        return {"tp_add": 20.0 if (med or 0.0) > 6050.0 else 10.0}
    return selector


def build_producer(contracts, cal) -> ProducerState:
    sessions = cal.sessions()
    re = RollEngine(SYMBOL, contracts, cal)
    table = re.build_roll_table()
    held = re.held_contract_index_by_session(table)
    close_maps = [cd.close_map() for cd in contracts]
    metadata = []
    for i, s in enumerate(sessions):
        hi = held.get(s, 0)
        ref = close_maps[hi].get(sessions[i - 1]) if i > 0 else None
        metadata.append({"session": s.isoformat(), "ref_px": ref,
                         "note": f"held={contracts[hi].identity.local_symbol}"})
    return ProducerState(contracts=list(contracts),
                         roll_rows=list(table.rows),
                         rule_config=copy.deepcopy(table.rule_config),
                         metadata=metadata)


def truncate_producer(producer: ProducerState, cal) -> ProducerState:
    """Producer prefix at CUTOFF: every channel restricted to data the
    producer could have emitted by then. The roll table is REBUILT through
    RollEngine on the truncated bars — not statically filtered."""
    truncated_contracts = []
    for cd in producer.contracts:
        truncated_contracts.append(ContractData(
            identity=cd.identity,
            daily_trades=[b for b in cd.daily_trades if b.t <= CUTOFF]))
    rebuilt = RollEngine(SYMBOL, truncated_contracts, cal).build_roll_table()
    prefix_rows = [r for r in rebuilt.rows if r.decision_session <= CUTOFF]
    return ProducerState(
        contracts=truncated_contracts,
        roll_rows=prefix_rows,
        rule_config=copy.deepcopy(producer.rule_config),
        metadata=[e for e in producer.metadata
                  if dt.date.fromisoformat(e["session"]) <= CUTOFF])


def mutate_producer(producer: ProducerState) -> ProducerState:
    """Garbage in EVERY post-cutoff producer channel, deterministically.
    Garbage prices/volumes are dyadic rationals (exact in binary) and sit
    at a ~5300 level: clearly wrong for a ~6000-6200 market (so every leak
    detector fires) yet above every stop floor used by the strategies, so
    the engine's exact cash reconciliation stays meaningful on mutated
    data (a base-engine property this file must not disturb)."""
    rng = random.Random(MUT_SEED)
    garbage_px = [5250.0, 5300.0, 5312.5, 5350.0, 5375.0]
    garbage_vol = [0.5, 2.0, 8.0, 32.0]
    mut_contracts = []
    for cd in producer.contracts:
        bars = []
        for b in cd.daily_trades:
            if b.t <= CUTOFF:
                bars.append(b)
            else:
                g = rng.choice(garbage_px)
                bars.append(make_bar(b.t, g, g + 2.0, g - 2.0, g,
                                     v=rng.choice(garbage_vol)))
        mut_contracts.append(ContractData(identity=cd.identity,
                                          daily_trades=bars))
    mut_rows = []
    for r in producer.roll_rows:
        if r.decision_session <= CUTOFF:
            mut_rows.append(r)
        else:
            mut_rows.append(replace(
                r, raw_price_gap=250.0, adjustment_additive=250.0,
                adjustment_ratio=1.05,
                old_close_at_decision=rng.choice(garbage_px),
                new_close_at_decision=rng.choice(garbage_px),
                old_volume_at_decision=rng.choice(garbage_vol),
                new_volume_at_decision=rng.choice(garbage_vol),
                decision_inputs={"leaked": "garbage-after-cutoff"}))
    mut_metadata = []
    for e in producer.metadata:
        if dt.date.fromisoformat(e["session"]) <= CUTOFF:
            mut_metadata.append(e)
        else:
            mut_metadata.append({"session": e["session"],
                                 "ref_px": rng.choice(garbage_px),
                                 "note": "GARBAGE"})
    return ProducerState(contracts=mut_contracts, roll_rows=mut_rows,
                         rule_config=copy.deepcopy(producer.rule_config),
                         metadata=mut_metadata)


# --------------------------------------------------------------------- #
# strategies
def strategy_pit(params, md: MetadataPIT):
    """Honest strategy: bars via ctx.view (PIT-guarded), metadata via the
    PIT wrapper, tp from TRAIN-selected params."""
    tp_add = params["tp_add"]

    def strat(ctx):
        if ctx.position is not None:
            return Decision(action="none")
        closes = ctx.view.closes(ctx.asof, 6)
        if len(closes) < 6 or closes[-1] <= sum(closes[:-1]) / 5.0 + 0.05:
            return Decision(action="none")
        ref = md.latest_ref(ctx.asof)
        tp, sl = closes[-1] + tp_add, ref - 250.0
        return Decision(action="enter_long", tp_price=tp, sl_price=sl,
                        time_exit_sessions=3, reason="mom",
                        features={"tp": (tp, ctx.asof),
                                  "sl": (sl, ctx.asof),
                                  "tp_add": (tp_add, ctx.asof),
                                  "md_ref": (ref, ctx.asof)})
    return strat


def strategy_leak_bars(producer: ProducerState):
    """LOOKAHEAD: entry threshold uses the mean of ALL bars (future ones
    included) straight off the producer, bypassing the PIT view."""
    allc = [b.c for cd in producer.contracts for b in cd.daily_trades]
    mean_all = sum(allc) / len(allc)

    def strat(ctx):
        if ctx.position is not None:
            return Decision(action="none")
        c = ctx.view.close(ctx.asof)
        if c >= mean_all:
            return Decision(action="none")
        tp, sl = c + 20.0, c - 250.0
        return Decision(action="enter_long", tp_price=tp, sl_price=sl,
                        time_exit_sessions=3, reason="leak_bars",
                        features={"tp": (tp, ctx.asof), "sl": (sl, ctx.asof),
                                  "leak_mean": (mean_all, ctx.asof)})
    return strat


def strategy_leak_roll(producer: ProducerState):
    """LOOKAHEAD: tp offset from the max |raw gap| across the FULL roll
    table, including roll rows decided after the decision session."""
    gap = max(abs(r.raw_price_gap or 0.0) for r in producer.roll_rows)

    def strat(ctx):
        if ctx.position is not None:
            return Decision(action="none")
        closes = ctx.view.closes(ctx.asof, 6)
        if len(closes) < 6 or closes[-1] <= sum(closes[:-1]) / 5.0 + 0.05:
            return Decision(action="none")
        tp, sl = closes[-1] + gap, 5000.0
        return Decision(action="enter_long", tp_price=tp, sl_price=sl,
                        time_exit_sessions=3, reason="leak_roll",
                        features={"tp": (tp, ctx.asof), "sl": (sl, ctx.asof),
                                  "leak_gap": (gap, ctx.asof)})
    return strat


def strategy_leak_metadata(md_all: MetadataPIT):
    """LOOKAHEAD: sl from the FINAL metadata entry (future session)."""
    last = md_all.last_entry_overall()

    def strat(ctx):
        if ctx.position is not None:
            return Decision(action="none")
        closes = ctx.view.closes(ctx.asof, 6)
        if len(closes) < 6 or closes[-1] <= sum(closes[:-1]) / 5.0 + 0.05:
            return Decision(action="none")
        tp, sl = closes[-1] + 20.0, last["ref_px"] - 5000.0
        return Decision(action="enter_long", tp_price=tp, sl_price=sl,
                        time_exit_sessions=3, reason="leak_metadata",
                        features={"tp": (tp, ctx.asof),
                                  "sl": (sl, ctx.asof),
                                  "leak_ref": (last["ref_px"], ctx.asof)})
    return strat


# --------------------------------------------------------------------- #
def extract_decisions(journal, lo: dt.date, hi: dt.date) -> list[dict]:
    out = []
    for r in journal.records:
        if lo <= r.decision_session <= hi:
            fs = r.feature_snapshot or {}
            out.append({
                "session": r.decision_session.isoformat(),
                "reason": r.entry_decision_reason,
                "dir": r.direction,
                "veto": r.veto_reason,
                "exit": r.exit_type,
                "qty": r.qty,
                "tp": fs.get("tp"),
                "sl": fs.get("sl"),
                "tp_add": fs.get("tp_add"),
            })
    return out


def wf_replay(producer: ProducerState, cal, strategy_factory=None,
              leaky_selection: bool = False, n_folds: int = N_FOLDS) -> dict:
    """Walk-forward replay over the producer's fold windows: nested TRAIN
    selection per fold (PIT view pinned at train_end), then TEST replay
    with the frozen params. Returns the emitted decisions per fold."""
    sessions = cal.sessions()
    planner = WalkForwardPlanner(sessions, true_horizon_sessions=HORIZON,
                                 embargo_sessions=EMBARGO)
    folds = planner.plan(n_folds=n_folds, train_frac=TRAIN_FRAC)
    table = RollTable(symbol=SYMBOL, rule_config=dict(producer.rule_config),
                      rows=list(producer.roll_rows))
    engine = BacktestEngine(SYMBOL, RollEngine(SYMBOL, producer.contracts, cal),
                            table, CostBook.for_symbol(SYMBOL), EngineConfig())
    md = MetadataPIT(producer.metadata)
    factory = strategy_factory or (lambda params, m: strategy_pit(params, m))
    selector = make_selector(leaky_selection)

    def runner(fold, phase, seed):
        view = PinnedCloses(producer.contracts, sessions, fold.train_end,
                            leaky=leaky_selection)
        params = planner.run_selection(fold, selector, view)
        strat = factory(params, md)
        if phase == "test":
            lo, hi = fold.test_start, fold.test_end
        else:
            lo, hi = fold.train_start, fold.train_end
        journal = engine.run(strat, TradeJournal(0.0), cutoff=hi)
        return extract_decisions(journal, lo, hi)

    out = replay_deterministic(folds, runner, seed=7)
    decisions = [d for rec in out for d in rec["test"]]
    return {"decisions": decisions,
            "folds": [f.to_dict() for f in folds]}


class ProducerPrefixFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cal = build_calendar()
        cls.sessions = cls.cal.sessions()
        cls.full = build_producer(raw_contracts(cls.sessions), cls.cal)
        cls.truncated = truncate_producer(cls.full, cls.cal)
        cls.mutated = mutate_producer(cls.full)

    def prefix(self, output):
        """Decisions at or before CUTOFF with the R5 label-maturity law
        applied at the evaluation layer: a record whose label window
        (decision session + HORIZON sessions) extends past the boundary is
        CENSORED — its outcome is compared as LABEL_CENSORED, never as a
        resolved exit computed on data past the boundary (that would be
        evaluating an immature label on truncated/future data)."""
        idx = {s: i for i, s in enumerate(self.sessions)}
        b = idx[CUTOFF]
        out = []
        for d in output["decisions"]:
            if d["session"] > CUTOFF.isoformat():
                continue
            di = idx[dt.date.fromisoformat(d["session"])]
            if d["veto"] is None and di + HORIZON > b:
                out.append(dict(d, exit="LABEL_CENSORED"))
            else:
                out.append(d)
        return out


class TestProducerPrefixChannels(ProducerPrefixFixture):
    def test_fixture_shape(self):
        # 104 weekday sessions; two roll rows: Feb 27 and Apr 30
        self.assertEqual(len(self.sessions), 105)
        self.assertEqual([r.decision_session for r in self.full.roll_rows],
                         [dt.date(2026, 2, 27), dt.date(2026, 4, 30)])
        self.assertEqual(self.full.metadata[0]["session"],
                         CAL_START.isoformat())

    def test_roll_table_channel_rebuilt_not_static(self):
        # rebuilt from truncated BARS via RollEngine; prefix rows identical
        rebuilt = RollEngine(
            SYMBOL, self.truncated.contracts, self.cal).build_roll_table()
        rebuilt = [r for r in rebuilt.rows if r.decision_session <= CUTOFF]
        self.assertEqual([r.decision_session for r in rebuilt],
                         [dt.date(2026, 2, 27)])
        self.assertEqual(rebuilt[0].to_dict(),
                         self.full.roll_rows[0].to_dict())
        # the truncated producer carries NO post-cutoff roll rows
        self.assertTrue(all(r.decision_session <= CUTOFF
                            for r in self.truncated.roll_rows))

    def test_metadata_channel_is_a_prefix(self):
        full_prefix = [e for e in self.full.metadata
                       if dt.date.fromisoformat(e["session"]) <= CUTOFF]
        self.assertEqual(self.truncated.metadata, full_prefix)
        self.assertTrue(all(
            dt.date.fromisoformat(e["session"]) <= CUTOFF
            for e in self.truncated.metadata))

    def test_selection_channel_pinned_at_train_end(self):
        planner = WalkForwardPlanner(self.sessions,
                                     true_horizon_sessions=HORIZON,
                                     embargo_sessions=EMBARGO)
        folds = planner.plan(n_folds=N_FOLDS, train_frac=TRAIN_FRAC)
        for f in folds:
            if f.train_end > CUTOFF:
                continue
            v_full = PinnedCloses(self.full.contracts, self.sessions,
                                  f.train_end)
            v_trunc = PinnedCloses(self.truncated.contracts, self.sessions,
                                   f.train_end)
            params = planner.run_selection(f, make_selector(), v_full)
            self.assertEqual(params,
                             make_selector()(v_trunc))
            self.assertEqual(f.selection_asof, f.train_end)
            self.assertIn("frozen at train_end", f.selection_note)


class TestPrefixDeterminism(ProducerPrefixFixture):
    def test_replay_on_truncated_producer_reproduces_prefix(self):
        base = {"decisions": self.prefix(wf_replay(self.full, self.cal))}
        trunc = {"decisions": self.prefix(
            wf_replay(self.truncated, self.cal))}
        self.assertTrue(base["decisions"],
                        "vacuous test: no decisions at or before cutoff")
        # the label-maturity censoring path is genuinely exercised: at least
        # one decision near the boundary has an immature label, and both
        # runs censor exactly the same decision sessions
        c_base = [d for d in base["decisions"] if d["exit"] == "LABEL_CENSORED"]
        c_trunc = [d for d in trunc["decisions"] if d["exit"] == "LABEL_CENSORED"]
        self.assertTrue(c_base)
        self.assertEqual([d["session"] for d in c_base],
                         [d["session"] for d in c_trunc])
        assert_prefix_determinism(base, trunc, CUTOFF)

    def test_post_decision_producer_mutation_changes_nothing(self):
        base = {"decisions": self.prefix(wf_replay(self.full, self.cal))}
        mut = {"decisions": self.prefix(wf_replay(self.mutated, self.cal))}
        self.assertTrue(base["decisions"])
        # the mutation is real: every post-cutoff channel actually differs
        self.assertNotEqual(
            [b.c for cd in self.full.contracts for b in cd.daily_trades
             if b.t > CUTOFF],
            [b.c for cd in self.mutated.contracts for b in cd.daily_trades
             if b.t > CUTOFF])
        self.assertNotEqual(self.full.roll_rows[1].to_dict(),
                            self.mutated.roll_rows[1].to_dict())
        self.assertNotEqual(
            [e for e in self.full.metadata
             if dt.date.fromisoformat(e["session"]) > CUTOFF],
            [e for e in self.mutated.metadata
             if dt.date.fromisoformat(e["session"]) > CUTOFF])
        assert_future_mutation_invariance(base, mut, CUTOFF)


class TestCounterLookaheadTeeth(ProducerPrefixFixture):
    """A lookahead implementation WOULD change already-emitted decisions —
    the invariance helper must catch each leak channel, proving the
    positive tests above have teeth."""

    def test_leaky_bar_reader_is_detected(self):
        base = {"decisions": self.prefix(wf_replay(
            self.full, self.cal,
            strategy_factory=lambda p, m: strategy_leak_bars(self.full)))}
        mut = {"decisions": self.prefix(wf_replay(
            self.mutated, self.cal,
            strategy_factory=lambda p, m: strategy_leak_bars(self.mutated)))}
        self.assertTrue(base["decisions"])
        with self.assertRaises(AssertionError):
            assert_future_mutation_invariance(base, mut, CUTOFF)

    def test_leaky_roll_table_reader_is_detected(self):
        # n_folds=2: enough folds for pre-cutoff records in fold 1 while
        # keeping the replay small; the mutated roll row (post-cutoff,
        # gap 250) is read by THIS strategy through the leak, and never
        # needs to execute a roll to prove the detection
        base = {"decisions": self.prefix(wf_replay(
            self.full, self.cal, n_folds=2,
            strategy_factory=lambda p, m: strategy_leak_roll(self.full)))}
        mut = {"decisions": self.prefix(wf_replay(
            self.mutated, self.cal, n_folds=2,
            strategy_factory=lambda p, m: strategy_leak_roll(self.mutated)))}
        self.assertTrue(base["decisions"])
        with self.assertRaises(AssertionError):
            assert_future_mutation_invariance(base, mut, CUTOFF)

    def test_leaky_metadata_reader_is_detected(self):
        base = {"decisions": self.prefix(wf_replay(
            self.full, self.cal, strategy_factory=lambda p, m:
            strategy_leak_metadata(MetadataPIT(self.full.metadata))))}
        mut = {"decisions": self.prefix(wf_replay(
            self.mutated, self.cal, strategy_factory=lambda p, m:
            strategy_leak_metadata(MetadataPIT(self.mutated.metadata))))}
        self.assertTrue(base["decisions"])
        with self.assertRaises(AssertionError):
            assert_future_mutation_invariance(base, mut, CUTOFF)

    def test_leaky_selection_changes_params(self):
        # PIT selection is stable under post-train-end mutation; a leaking
        # selector is not — that difference is what pins the law.
        for f_train_end in (dt.date(2026, 2, 24), dt.date(2026, 3, 19)):
            honest_full = make_selector()(
                PinnedCloses(self.full.contracts, self.sessions, f_train_end))
            honest_mut = make_selector()(
                PinnedCloses(self.mutated.contracts, self.sessions,
                             f_train_end))
            self.assertEqual(honest_full, honest_mut)
            leaky_full = make_selector(leaky=True)(
                PinnedCloses(self.full.contracts, self.sessions, f_train_end,
                             leaky=True))
            leaky_mut = make_selector(leaky=True)(
                PinnedCloses(self.mutated.contracts, self.sessions,
                             f_train_end, leaky=True))
            self.assertNotEqual(leaky_full, leaky_mut)


if __name__ == "__main__":
    unittest.main()
