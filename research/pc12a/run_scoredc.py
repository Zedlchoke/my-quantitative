"""Stage-C SCORED EVALUATION — PC12A (TEST folds, GO-gated, heavy lock).

The campaign's scored evaluation: the frozen policy (POLICY_FROZEN.json,
policy_digest verified at entry) against the full baseline/robustness
battery of PASS_BARS_V2 (+ADDENDUM), evaluated on the 8 TEST folds
pooled per E-Law 2 (fold-edge force-flat, equity carries across folds,
one $100k book; per-symbol virtual sub-accounts per the frozen Stage-B
book law, portfolio equity = 100k + sum sub-PnL).

Laws implemented here (each cited at the point of enforcement):

- TEST-ONLY partition: the scored window is [fold0.test_start,
  fold7.test_end] = [2022-01-07, 2025-12-26]; warmup is indicator-only
  (no decisions) before the window; the sealed tail (2026-01-02+) is
  NEVER loaded and TRAIN folds are NEVER re-scored (asserted; the
  engine's PIT/truncation law is inherited frozen from the verification
  battery).
- E-Law 1 quantities: pooled netPnL (exact cash identity; folds are flat
  at both edges so fold net = cash delta), maxDD in USD on the weekly
  Friday-mark equity path of the pooled window (maxDD% reported,
  non-governing); P7's per-fold DD uses within-fold peaks (reset at fold
  start).
- E-Law 2 fold-edge force-flat: at each test fold's last decision day
  (the last processed day >= the fold's test_end... realized as: the
  first processed day d >= fold.test_end closes the fold) every open
  position is force-flatted; the exit fills at the FIRST tradable bar of
  the next session (typically the Sunday reopen; bar-quoted spread-once
  + commission, the frozen engine fill law), booked inside the CLOSING
  fold. Per-arm fold-edge force-flat cost totals are tracked (skeptic
  F-7 companion table).
- Baseline realization laws exactly per PASS_BARS_V2 §1 rows (B0..B8;
  see _ARMS below). B3 selection is TRAIN-only from the X2 diagnostics
  and is frozen to disk BEFORE any test arm runs (mode b3select).
- B4 = ONE identity: 128 seeded sub-runs, duty+turnover matched to the
  policy's TRAIN-realized eligibility path (per-leg two-state Markov
  chain with stationary duty pi and per-decision flip rate f; a=f/(2(1-
  pi)), b=f/(2 pi)); seed list frozen and digest-recorded.
- P6d pricing mode: every realized state change re-priced at the
  measured p90 of its applicable spread cell (C1 default, C2 windows,
  C3 reopen; fill = mid +/- (p90/2 + slip_band)); the L6 guard estimate
  stays the ordinary p50-labeled planning estimate (addendum A-3).
- Determinism: the policy arm re-run must be byte-identical (mode repro
  inside orchestrate); arm metrics JSONs are canonical (sort_keys,
  rounded).
- NO TUNING: bars fail as they fail; nothing downstream re-fits.

Usage (orchestrate runs everything under the machine-wide heavy lock):
    .venv/bin/python -m research.pc12a.run_scoredc --mode verify
    .venv/bin/python -m research.pc12a.run_scoredc --mode b3select
    .venv/bin/python -m research.pc12a.run_scoredc --mode trainextract
    .venv/bin/python -m research.pc12a.run_scoredc --mode arm --arm POLICY
    .venv/bin/python -m research.pc12a.run_scoredc --mode b4
    .venv/bin/python -m research.pc12a.run_scoredc --mode bars
    .venv/bin/python -m research.pc12a.run_scoredc --mode orchestrate
"""

from __future__ import annotations

import argparse
import bisect
import datetime as dt
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
import time
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

from . import calendar_service as cal
from . import cost_kernel as _ck
from . import journal as _jr
from . import legs as _legs
from . import panels as _panels
from . import policy as _pol
from . import run_diag as rd
from . import run_dry as _rd
from . import run_stageb as sb

UTC = dt.timezone.utc
CYCLE = "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1"
INITIAL_CASH = 100_000.0          # per-symbol virtual sub-account (book law)
LABEL = "SCORED-TEST"
SCHEMA_ARM = "pc12a_stagec_arm@1"
RESIDUAL_TOL = 1e-6
ROOT_CHECKOUT = "/Users/hoangminhlong/my-quantitative"
WORKTREE = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
            "portfolio-composite-12assets-100k-v1/integration")
CONTROL = os.path.join(WORKTREE, "research", "control", CYCLE)
LEDGER_PATH = os.path.join(CONTROL, "TRIAL_LEDGER.jsonl")
POLICY_PATH = os.path.join(CONTROL, "policy", "POLICY_FROZEN.json")
STAGEC_DIR = os.path.join(CONTROL, "diagnostics", "stagec")
ARMS_DIR = os.path.join(STAGEC_DIR, "ARMS")
LEGS_CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "legs_config")
GAMMA = 0.5772156649015329
EUL = 2.718281828459045
N_B4_SEEDS = 128
B4_SEED_BASE = 770_000            # frozen seed list: 770000..770127
B7_LAG_WEEKS = 26                 # one test fold = 26 weeks (P4c law)
B2_PER_LEG_CAP_UNITS = 100_000    # unit-space per-leg bound (architecture 5)
IDENTITY_CAP = 48                 # scored-identity budget cap (plan v2 4)
LEDGER_STOP_LINE = 1400           # of the 1500 cap
FILL_SEARCH_DAYS = 5              # forward fill-bar search window


def _dump(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, sort_keys=True, indent=1)
        fh.write("\n")


def _now() -> str:
    return dt.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _r6(x: float) -> float:
    return round(float(x), 6)


def _fmt(t: dt.datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _max_dd(equities: List[float]) -> float:
    peak = equities[0] if equities else 0.0
    dd = 0.0
    for e in equities:
        peak = max(peak, e)
        dd = max(dd, peak - e)
    return dd


# ---------------------------------------------------------------------------
# 0. Frozen policy load + digest verification (BLOCKED on mismatch)
# ---------------------------------------------------------------------------


def load_policy() -> Dict:
    pol = json.load(open(POLICY_PATH, encoding="utf-8"))
    claimed = pol["policy_digest"]
    body = dict(pol)
    body.pop("policy_digest")
    recomputed = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode()).hexdigest()
    if claimed != recomputed:
        raise RuntimeError(
            f"POLICY DIGEST MISMATCH: claimed {claimed} recomputed "
            f"{recomputed} — BLOCKED (no scored run on an unverified freeze)")
    if pol["variant_config"] != {"caps": "default", "eligibility": "base",
                                 "netting": "super", "variant_id": "V3"}:
        raise RuntimeError(f"unexpected winner config {pol['variant_config']}")
    return pol


def policy_engine_inputs(pol: Dict) -> Dict:
    """Reconstruct the engine inputs from POLICY_FROZEN (never hardcoded):
    slate cfgs by symbol, caps + cluster_symbols, variant, guard cap."""
    survivors = [leg["leg_id"] for leg in pol["slate"]]
    cfgs_all = {c.get("class_candidate_id") or c["corpus_gid"]: c
                for c in _legs.load_leg_configs(LEGS_CONFIG_DIR)}
    missing = [s for s in survivors if s not in cfgs_all]
    if missing:
        raise RuntimeError(f"slate legs missing configs: {missing}")
    caps_cfg = dict(pol["caps"])
    caps_cfg["cluster_symbols"] = {
        cid: sorted({cfgs_all[m]["symbol"] for m in members
                     if m in cfgs_all})
        for cid, members in pol["cluster_map"]["clusters"].items()}
    by_symbol: Dict[str, List[Dict]] = {}
    for lid in sorted(survivors):
        c = cfgs_all[lid]
        by_symbol.setdefault(c["symbol"], []).append(c)
    # freeze cross-check: every slate arm_config_digest must match the config
    for leg in pol["slate"]:
        ident = _legs.make_identity(cfgs_all[leg["leg_id"]])
        if ident.arm_config_digest != leg["arm_config_digest"]:
            raise RuntimeError(
                f"slate digest drift for {leg['leg_id']}: frozen "
                f"{leg['arm_config_digest']} vs config "
                f"{ident.arm_config_digest}")
    return {"survivors": survivors, "by_symbol": by_symbol,
            "caps_cfg": caps_cfg,
            "variant": dict(pol["variant_config"]),
            "guard_cap_usd": float(pol["guard"]["cap_usd"])}


# ---------------------------------------------------------------------------
# 1. Arm registry (baseline realization laws, PASS_BARS_V2 1)
# ---------------------------------------------------------------------------


class AlwaysOnEligibility:
    """B1/B2: eligibility (L2, E1-E5) pinned ON at every decision."""

    def __init__(self):
        self.base = _pol.Eligibility()

    def evaluate(self, leg_id, stats, pit_snapshot, now):
        return _pol.EligibilityVerdict("ON", None, "B1/B2 pinned ON")


class RecordingEligibility:
    """Policy mode: pure delegation + verdict recording (no behavior change)."""

    def __init__(self):
        self.base = _pol.Eligibility()
        self.timeline: Dict[str, List[Tuple[dt.datetime, bool]]] = {}

    def evaluate(self, leg_id, stats, pit_snapshot, now):
        v = self.base.evaluate(leg_id, stats, pit_snapshot, now)
        self.timeline.setdefault(leg_id, []).append((now, v.state == "ON"))
        return v


class ClockGateEligibility:
    """B5: deterministic clock, every k-th decision ON (phase 0),
    k = round_half_up(1/duty), duty = policy-realized TRAIN duty."""

    def __init__(self, duty: Dict[str, float]):
        self.duty = duty
        self.counts: Dict[str, int] = {}

    @staticmethod
    def k_of(duty: float) -> Optional[int]:
        if duty <= 0.0:
            return None                     # never ON
        k = int(math.floor(1.0 / duty + 0.5))  # half-up (documented)
        return max(k, 1)

    def evaluate(self, leg_id, stats, pit_snapshot, now):
        k = self.k_of(self.duty.get(leg_id, 0.0))
        n = self.counts.get(leg_id, 0)
        self.counts[leg_id] = n + 1
        if k is None:
            return _pol.EligibilityVerdict(
                "OFF", "B5", f"B5 clock: TRAIN duty 0 -> never ON")
        if n % k == 0:
            return _pol.EligibilityVerdict(
                "ON", None, f"B5 clock ON (decision {n} mod {k} == 0)")
        return _pol.EligibilityVerdict(
            "OFF", "B5", f"B5 clock OFF (decision {n} mod {k} != 0)")


class InvertedEligibility:
    """B6: binary complement of the policy's own eligibility decision
    (ON<->OFF); the policy has no PROBATION state, so the PROBATION clause
    of the realization law is vacuous (disclosed in the report)."""

    def __init__(self):
        self.base = _pol.Eligibility()

    def evaluate(self, leg_id, stats, pit_snapshot, now):
        v = self.base.evaluate(leg_id, stats, pit_snapshot, now)
        if v.state == "ON":
            return _pol.EligibilityVerdict(
                "OFF", "B6", f"B6 inverted: policy ON -> OFF")
        return _pol.EligibilityVerdict(
            "ON", None, f"B6 inverted: policy {v.state} ({v.rule_id}) -> ON")


class LaggedEligibility:
    """B7: the policy's own eligibility decision delayed by one fold
    (26w). Verdict timeline = TRAIN run (for the first test fold's lag
    window) + the POLICY test run; lookup = the policy verdict at the
    latest decision instant <= ts - 26w; none recorded -> fail-open ON
    (counted + disclosed)."""

    def __init__(self, timeline: Dict[str, Tuple[List[float],
                                                  List[bool]]]):
        self.timeline = timeline           # leg -> (epoch_ts[], on[])
        self.n_failopen = 0

    def evaluate(self, leg_id, stats, pit_snapshot, now):
        tgt = (now - dt.timedelta(weeks=B7_LAG_WEEKS)).timestamp()
        tss, ons = self.timeline.get(leg_id, ([], []))
        i = bisect.bisect_right(tss, tgt) - 1
        if i < 0:
            self.n_failopen += 1
            return _pol.EligibilityVerdict(
                "ON", None,
                "B7 lag: no recorded policy verdict before ts-26w -> "
                "fail-open ON (disclosed)")
        if ons[i]:
            return _pol.EligibilityVerdict("ON", None,
                                           f"B7 lag: policy ON at -26w")
        return _pol.EligibilityVerdict("OFF", "B7",
                                       "B7 lag: policy OFF at -26w")


class OracleEligibility:
    """B8: perfect next-fold eligibility, REPORTING ONLY — the admission
    set per fold = slate legs with positive always-on PAPER (sum-of-legs)
    net over that fold, measured from the B1 run's paper book."""

    def __init__(self, sets: Dict[int, List[str]]):
        self.sets = sets
        self.fold = 0

    def set_fold(self, fold_id: int) -> None:
        self.fold = fold_id

    def evaluate(self, leg_id, stats, pit_snapshot, now):
        if leg_id in self.sets.get(self.fold, []):
            return _pol.EligibilityVerdict(
                "ON", None, f"B8 oracle: leg in fold-{self.fold} winner set")
        return _pol.EligibilityVerdict(
            "OFF", "B8", f"B8 oracle: leg not in fold-{self.fold} winner set")


class MarkovEligibility:
    """B4 seed sub-run: per-leg two-state chain, stationary duty pi and
    per-decision flip rate f matched to the policy's TRAIN eligibility
    path (a=f/(2(1-pi)) OFF->ON, b=f/(2 pi) ON->OFF, clamped to [0,1];
    realized mismatch disclosed)."""

    def __init__(self, seed: int, duty: Dict[str, float],
                 flip: Dict[str, float]):
        self.seed_root = seed
        self.duty = duty
        self.flip = flip
        self.rngs: Dict[str, np.random.Generator] = {}
        self.state: Dict[str, bool] = {}
        self.leg_ix = {lid: i for i, lid in enumerate(sorted(duty))}

    def _chains(self, leg_id: str):
        pi = min(max(self.duty.get(leg_id, 0.0), 0.0), 1.0)
        f = min(max(self.flip.get(leg_id, 0.0), 0.0), 1.0)
        a = f / (2.0 * (1.0 - pi)) if pi < 1.0 else (1.0 if f > 0 else 0.0)
        b = f / (2.0 * pi) if pi > 0.0 else (1.0 if f > 0 else 0.0)
        return min(a, 1.0), min(b, 1.0)

    def evaluate(self, leg_id, stats, pit_snapshot, now):
        pi = min(max(self.duty.get(leg_id, 0.0), 0.0), 1.0)
        if leg_id not in self.rngs:
            self.rngs[leg_id] = np.random.default_rng(
                np.random.SeedSequence(entropy=self.seed_root,
                                       spawn_key=(self.leg_ix[leg_id],)))
            self.state[leg_id] = bool(self.rngs[leg_id].random() < pi)
        a, b = self._chains(leg_id)
        on = self.state[leg_id]
        p_flip = b if on else a
        if self.rngs[leg_id].random() < p_flip:
            on = not on
        self.state[leg_id] = on
        if on:
            return _pol.EligibilityVerdict("ON", None, "B4 random ON")
        return _pol.EligibilityVerdict("OFF", "B4", "B4 random OFF")


# arm spec: name, tier, pricing, leg subset, eligibility mode, sizing mode
def _arm(name: str, tier: float = 1.0, pricing: str = "base",
         legs: Optional[List[str]] = None, elig: str = "policy",
         sizing: str = "policy", note: str = "") -> Dict:
    return {"arm": name, "tier": tier, "pricing": pricing,
            "legs": legs, "elig": elig, "sizing": sizing, "note": note}


def build_arm_specs(survivors: List[str]) -> List[Dict]:
    arms = [
        _arm("POLICY"),
        _arm("B1_ALWAYS_ON", elig="alwayson"),
        _arm("B2_EQUAL_WEIGHT", elig="alwayson", sizing="equal_split"),
        _arm("B3_BEST_SINGLE"),
        _arm("B5_CLOCK_GATE", elig="clock"),
        _arm("B6_INVERTED", elig="inverted"),
        _arm("B7_LAGGED", elig="lagged"),
        _arm("B8_ORACLE", elig="oracle"),
        # P6a governing x1.5 + P6b/P6c mandatory x2.0 reporting pair
        _arm("POLICY_X15", tier=1.5),
        _arm("B1_X15", tier=1.5, elig="alwayson"),
        _arm("POLICY_X20", tier=2.0),
        _arm("B1_X20", tier=2.0, elig="alwayson"),
        # P6d switch-p90 ladder
        _arm("POLICY_P90", pricing="p90"),
        _arm("B1_P90", pricing="p90", elig="alwayson"),
    ]
    for lid in survivors:                                  # P8 matrix
        arms.append(_arm(f"POLICY_MO_{lid}", legs=[lid]))
        arms.append(_arm(f"B1_MO_{lid}", legs=[lid], elig="alwayson"))
    return arms


def arm_config_digest(spec: Dict, pol_digest: str, extra: str = "") -> str:
    body = {"arm": spec["arm"], "tier": spec["tier"],
            "pricing": spec["pricing"], "legs": spec["legs"],
            "elig": spec["elig"], "sizing": spec["sizing"],
            "policy_digest": pol_digest, "extra": extra}
    return hashlib.sha256(
        json.dumps(body, sort_keys=True).encode()).hexdigest()


# ---------------------------------------------------------------------------
# 2. The scored engine (test window; frozen Stage-B decision path copied
#    with arm hooks; equivalence-tested against sb.PortfolioEngine)
# ---------------------------------------------------------------------------


class _TestArgs:
    def __init__(self, window_start: dt.date, window_end: dt.date,
                 tier: float):
        self.window_start = window_start
        self.window_end = window_end
        self.tier = tier


class ScoredEngine(rd.DiagEngine):
    """PortfolioEngine over the pooled TEST folds with fold-edge
    force-flat, arm eligibility/sizing hooks, full journaling and (for
    P6d) p90 cell pricing. The decision path in _apply_decisions_scored
    is a copy of sb.PortfolioEngine._apply_decisions_stageb (frozen);
    test_pc12a_stageC pins behavioral equivalence on synthetic panels."""

    def __init__(self, symbol: str, cfgs: List[Dict], store, folds,
                 tier: float, variant: Dict, caps_cfg: Dict,
                 guard: _pol.CostGuard, journal, arm: Dict,
                 elig_builder: Callable[[], object],
                 heat_lookup: Optional[Callable[[dt.datetime], float]] = None,
                 verdict_recorder=None, paper_out: Optional[Dict] = None):
        report = {"legs": {},
                  "cost_bill_totals_usd": {"spread_once": 0.0, "slip": 0.0,
                                           "slip_gap_excess": 0.0,
                                           "commission": 0.0, "swap": 0.0},
                  "blocked_reason_histogram": {}}
        for c in cfgs:
            lid = c.get("class_candidate_id") or c["corpus_gid"]
            report["legs"][lid] = {"decisions": 0, "votes": {},
                                   "fills_by_outcome": {}}
        args = _TestArgs(folds[0].test_start, folds[-1].test_end, tier)
        _rd.SymbolEngine.__init__(self, symbol, cfgs, args, journal, guard,
                                  report)
        self.journal.engine = self
        self.diag_window_end = folds[-1].test_end
        self.diag_store = store
        self.folds = sorted(folds, key=lambda f: f.test_end)
        self.fold_by_end = {}               # disable stageb TRAIN snapshots
        self.snapshots = {}
        self._fold_by_id = {f.fold_id: f for f in folds}
        self._friday_equity: Dict[dt.date, float] = {}
        self._now_ts: Optional[dt.datetime] = None
        self._swap_ts: Optional[dt.datetime] = None
        self.variant = variant
        self.caps_cfg = caps_cfg
        self.netting = (sb.SupermajorityNetting()
                        if variant["netting"] == "super" else _pol.Netting())
        self.arm = arm
        self.eligibility = elig_builder()
        self._heat_lookup = heat_lookup
        self._verdict_recorder = verdict_recorder
        self._paper_out = paper_out
        self._prev_desires = {lid: 0 for lid in self.leg_desires}
        self._paper_mark_prev: Optional[float] = None
        self._paper_fold_net: Dict[str, Dict[int, float]] = {
            lid: {} for lid in self.leg_desires}
        self._current_fold_idx = 0
        self.fold_records: Dict[int, Dict] = {}
        self._fold_fills: List[Dict] = []
        self._fold_swaps: List[Dict] = []
        self._fold_fridays: Dict[dt.date, float] = {}
        self.force_flat_costs: List[Dict] = []
        self._edge_cash = INITIAL_CASH
        self._prev_edge_ts: Optional[dt.datetime] = None
        self.n_force_flat = 0
        self.turnover_usd = 0.0
        self.heat_events: List[Tuple[dt.datetime, float]] = []
        self.n_decisions_total = 0
        self.all_fills: List[Dict] = []
        # kernel capture (staged-fill discipline as wave 2 / Stage-B)
        orig_fill = self.kernel.price_ordinary_fill
        orig_swap = self.kernel.swap_usd
        self._orig_fill = orig_fill
        self._staged_fills: List[Dict] = []
        self._captured_fills: List[Dict] = []
        self._captured_swaps: List[Dict] = []

        def cap_fill(side, delta_units, bid_open, ask_open):
            fq = orig_fill(side, delta_units, bid_open, ask_open)
            signed = delta_units if side == "buy" else -delta_units
            self._staged_fills.append({
                "ts": self._now_ts, "delta": signed, "fq": fq,
                "commission": self.kernel.commission(
                    delta_units, fq.fill_price)})
            return fq

        def cap_swap(units_abs, mult, mid):
            usd = orig_swap(units_abs, mult, mid)
            if units_abs:
                self._captured_swaps.append({"ts": self._swap_ts,
                                             "usd": usd})
            return usd

        self.kernel.price_ordinary_fill = cap_fill
        self.kernel.swap_usd = cap_swap

    # -- day loop / fold edges ----------------------------------------------

    def _fold_idx_at(self, date: dt.date) -> int:
        for f in self.folds:
            if date <= f.test_end:
                return f.fold_id
        return self.folds[-1].fold_id

    def run(self, store):
        d = self._warmup_start()
        closed = -1
        sealed_start = cal.sealed_tail()[0]
        while d <= self.window_end:
            try:
                day = store.load_day(self.symbol, d)
            except (FileNotFoundError, _panels.PanelError):
                d += dt.timedelta(days=1)
                continue
            self._process_day(day, d)
            while closed + 1 < len(self.folds) \
                    and d >= self.folds[closed + 1].test_end:
                closed += 1
                self._close_fold(self.folds[closed], store, d,
                                 sealed_start)
            d += dt.timedelta(days=1)
        while closed + 1 < len(self.folds):    # fold-end data-gap safety
            closed += 1
            self._close_fold(self.folds[closed], store, self.window_end,
                             sealed_start)
        if self.book_units != 0.0:
            raise RuntimeError(
                f"{self.symbol}: non-flat book {self.book_units} after the "
                f"last fold edge (force-flat law violated)")
        return {"data_days": 0}

    def _process_day(self, day, date):
        self._swap_ts = dt.datetime.combine(date, dt.time(22, 0), tzinfo=UTC)
        self._current_fold_idx = self._fold_idx_at(date)
        if hasattr(self.eligibility, "set_fold"):
            self.eligibility.set_fold(self._current_fold_idx)
        _rd.SymbolEngine._process_day(self, day, date)
        mark = self.last_mid_close
        if (mark is not None and date.strftime("%a") == "Fri"
                and self.window_start <= date <= self.window_end):
            eq = self.cash + self.book_units * float(mark)
            self._friday_equity[date] = eq
            self._fold_fridays[date] = eq
            if self._paper_mark_prev is not None:
                fk = self._current_fold_idx
                for lid, des in self.leg_desires.items():
                    net = self._paper_fold_net[lid].get(fk, 0.0) \
                        + des * (float(mark) - self._paper_mark_prev)
                    self._paper_fold_net[lid][fk] = net
            self._paper_mark_prev = float(mark)

    def _close_fold(self, fold, store, last_day, sealed_start):
        """Fold-edge force-flat (E-Law 2): flatten at the next session's
        first tradable bar, full kernel charged, booked to the CLOSING
        fold; then seal the fold record. The fill-bar search NEVER reaches
        the sealed tail (fail-closed)."""
        fill_ts = None
        pre_edge_cash = self.cash
        pre_edge_units = int(self.book_units)
        if self.book_units != 0.0:
            fill = self._force_flat_fill(store, last_day, sealed_start)
            if fill is not None:
                fq, commission, ts_fill = fill
                delta = -int(self.book_units)
                side = "buy" if delta > 0 else "sell"
                if delta > 0:
                    self.cash -= delta * fq.fill_price + commission
                else:
                    self.cash += (-delta) * fq.fill_price - commission
                self.book_units += delta
                self.turnover_usd += abs(delta) * fq.fill_price
                cost = (fq.spread_once_usd
                        + fq.slip_beyond_halfspread_usd + commission)
                self.report["cost_bill_totals_usd"]["spread_once"] += \
                    fq.spread_once_usd
                self.report["cost_bill_totals_usd"]["slip"] += \
                    fq.slip_beyond_halfspread_usd
                self.report["cost_bill_totals_usd"]["commission"] += commission
                self.guard.record_spend(ts_fill, cost)
                self.n_force_flat += 1
                self.force_flat_costs.append({
                    "fold_id": fold.fold_id, "symbol": self.symbol,
                    "ts_fill_utc": _fmt(ts_fill), "delta_units": delta,
                    "spread_once_usd": _r6(fq.spread_once_usd),
                    "slip_beyond_halfspread_usd":
                        _r6(fq.slip_beyond_halfspread_usd),
                    "commission_usd": _r6(commission),
                    "cost_total_usd": _r6(cost)})
                self._fold_fills.append({
                    "ts": ts_fill, "delta": delta, "fq": fq,
                    "commission": commission, "force_flat": True})
                self.all_fills.append({
                    "ts": ts_fill, "delta": delta,
                    "price": fq.fill_price, "force_flat": True})
                fill_ts = ts_fill
                self.journal.write("NET_ORDER", _jr.net_order_row(
                    order_id=f"{self.symbol}-ff{self.n_force_flat:03d}",
                    order_kind="CLOSE",
                    ts_fill_utc=_fmt(ts_fill), symbol=self.symbol,
                    side=side, delta_units=delta, fill_price=fq.fill_price,
                    quoted_side=fq.quoted_side, mid_at_fill=fq.mid_at_fill,
                    spread_once_usd=fq.spread_once_usd,
                    slip_beyond_halfspread_usd=fq.slip_beyond_halfspread_usd,
                    cross_cost_usd=fq.cross_cost_usd,
                    commission_usd=commission, cell_id=fq.cell_id,
                    u3_band_id="U3_NON_EVENT", venue_model="PANEL_DUKA",
                    units_after=self.book_units, contributing_legs=[],
                    cash_delta_usd=(-(delta * fq.fill_price + commission)
                                    if delta > 0
                                    else ((-delta) * fq.fill_price
                                          - commission))))
        edge_equity = self.cash                    # flat by law here
        cutoff = fill_ts or dt.datetime.combine(last_day, dt.time(23, 59,
                                                                  59),
                                                tzinfo=UTC)
        fills = list(self._fold_fills)
        swaps = [s for s in self._captured_swaps
                 if (self._prev_edge_ts is None
                     or s["ts"] > self._prev_edge_ts) and s["ts"] <= cutoff]
        self._prev_edge_ts = cutoff
        start_cash = self._edge_cash
        self.fold_records[fold.fold_id] = {
            "fold_id": fold.fold_id,
            "test_window": [fold.test_start.isoformat(),
                            fold.test_end.isoformat()],
            "cash_start": _r6(start_cash),
            "cash_end": _r6(self.cash),
            "pre_edge_cash": _r6(pre_edge_cash),
            "pre_edge_units": pre_edge_units,
            "net_pnl_usd": _r6(self.cash - start_cash),
            "friday_equity": {d.isoformat(): _r6(v) for d, v in
                              sorted(self._fold_fridays.items())},
            "edge_equity_usd": _r6(edge_equity),
            "n_fills": len(fills),
            "n_entries": sum(1 for f in fills
                             if f.get("entry", False)),
            "force_flat_cost_usd": _r6(sum(
                c["cost_total_usd"] for c in self.force_flat_costs
                if c["fold_id"] == fold.fold_id)),
            "cost_bill_usd": {
                "spread_once": _r6(sum(f["fq"].spread_once_usd
                                       for f in fills)),
                "slip": _r6(sum(f["fq"].slip_beyond_halfspread_usd
                                for f in fills)),
                "commission": _r6(sum(f["commission"] for f in fills)),
                "swap": _r6(sum(s["usd"] for s in swaps))}}
        self._edge_cash = self.cash
        self._fold_fills = []
        self._fold_fridays = {}
        if self._paper_out is not None:
            for lid in sorted(self._paper_fold_net):
                self._paper_out.setdefault(lid, {})[fold.fold_id] = \
                    _r6(self._paper_fold_net[lid].get(fold.fold_id, 0.0))

    def _force_flat_fill(self, store, last_day, sealed_start):
        """Price the force-flat at the first tradable bar of the next
        session after `last_day` (forward search, never reaching the
        sealed tail; bar-quoted spread-once, the frozen engine fill law;
        p90 cells in P6d mode)."""
        d = last_day + dt.timedelta(days=1)
        while d < sealed_start:
            try:
                day = store.load_day(self.symbol, d)
            except (FileNotFoundError, _panels.PanelError):
                d += dt.timedelta(days=1)
                continue
            tradable = day.tradable_mask()
            for m in range(_panels.RECORDS_PER_DAY):
                if tradable[m] and day.bid.open[m] > 0 \
                        and day.ask.open[m] >= day.bid.open[m]:
                    side = "sell" if self.book_units > 0 else "buy"
                    units = abs(int(self.book_units))
                    ts_fill = dt.datetime.combine(
                        d, dt.time(0, 0), tzinfo=UTC) \
                        + dt.timedelta(minutes=m)
                    fq = self._price_fill(side, units, day, m, ts_fill)
                    commission = self.kernel.commission(units,
                                                        fq.fill_price)
                    return fq, commission, ts_fill
            d += dt.timedelta(days=1)
        raise RuntimeError(
            f"{self.symbol}: no fill bar before the sealed tail "
            f"({sealed_start}) after {last_day} for the fold-edge "
            f"force-flat (fail-closed; sealed tail untouched)")

    def _price_fill(self, side, units, day, m, ts_fill):
        """Fill pricing dispatch: base = bar-quoted spread-once (frozen
        law); p90 = measured p90 of the applicable cell (P6d)."""
        bid_o, ask_o = float(day.bid.open[m]), float(day.ask.open[m])
        if self.arm.get("pricing") != "p90":
            return self.kernel.price_ordinary_fill(side, units, bid_o, ask_o)
        cell = _ck.MEASURED_CELLS["C1"][self.symbol]
        event = False
        if cal.is_sunday_reopen(ts_fill):
            cell = _ck.MEASURED_CELLS["C3"][self.symbol]
            event = True
        elif cal.is_in_roll_charge_window(ts_fill):
            wd = ts_fill.strftime("%a")
            cell = _ck.MEASURED_CELLS[
                "C2_FRI" if wd == "Fri" else "C2_MON_THU"][self.symbol]
            event = True
        s_eff = max(cell["p90"],
                    _ck.MEASURED_CELLS["C1"][self.symbol]["p90"]) \
            * self.kernel.tier
        mid = (bid_o + ask_o) / 2.0
        half = s_eff / 2.0 * self.kernel.pip
        slip = self.kernel.slip(event_window=event)
        quoted = mid + half if side == "buy" else mid - half
        fill = quoted + slip if side == "buy" else quoted - slip
        return _ck.FillQuote(
            side=side, delta_units=units, fill_price=fill,
            quoted_side=quoted, mid_at_fill=mid,
            spread_once_pips=half / self.kernel.pip,
            slip_pips=slip / self.kernel.pip, cell_id="P90",
            slip_band_pips=slip / self.kernel.pip)

    # -- decisions (frozen copy of the Stage-B path + arm hooks) ----------

    def _apply_decisions(self, decisions, ts, day, m):
        self._now_ts = ts
        try:
            self._apply_decisions_scored(decisions, ts, day, m)
        finally:
            if decisions:
                self.n_decisions_total += 1
                # post-decision heat event (B2's frozen input series)
                self.heat_events.append((ts, abs(self.book_units)))
            self._paper_charge_switching(day, m)
            self._staged_fills.clear()

    def _leg_share(self, lid: str) -> float:
        total = sum(abs(v) for v in self.leg_desires.values())
        if total == 0:
            return 0.0
        return abs(self.leg_desires.get(lid, 0)) / total

    def _paper_charge_switching(self, day, m) -> None:
        if day is None:
            return
        bid_c = ask_c = None
        if m is not None and m >= 0:
            bid_c, ask_c = float(day.bid.close[m]), float(day.ask.close[m])
        else:
            tradable = day.tradable_mask()
            for mm in range(len(tradable)):
                if tradable[mm] and day.bid.open[mm] > 0:
                    bid_c, ask_c = (float(day.bid.open[mm]),
                                    float(day.ask.open[mm]))
                    break
        if bid_c is None:
            return
        fk = self._current_fold_idx
        for lid, des in self.leg_desires.items():
            delta = des - self._prev_desires[lid]
            if delta != 0:
                side = "buy" if delta > 0 else "sell"
                est = self.kernel.estimate_all_in(side, abs(delta),
                                                  bid_c, ask_c)
                self._paper_fold_net[lid][fk] = \
                    self._paper_fold_net[lid].get(fk, 0.0) \
                    - est["est_total_usd"]
            self._prev_desires[lid] = des

    def _b2_resize(self, heat: float) -> None:
        """B2: replace L3 sizes with an equal split of the policy's
        realized per-decision TOTAL HEAT TARGET (frozen schedule), each
        leg keeping its own sign, capped per leg (PASS_BARS_V2 1)."""
        active = [l for l, d in self.leg_desires.items() if d != 0]
        if heat > 0.0 and active:
            share = heat / len(active)
            for l in active:
                d = self.leg_desires[l]
                self.leg_desires[l] = int(
                    math.copysign(min(share, B2_PER_LEG_CAP_UNITS), d))

    def _apply_decisions_scored(self, decisions, ts, day, m) -> None:
        """FROZEN COPY of sb.PortfolioEngine._apply_decisions_stageb with:
        full journal rows, arm eligibility hook (self.eligibility), B2
        equal-split sizing, p90 pricing dispatch, heat/verdict recorders.
        Behavioral equivalence with the Stage-B engine is pinned by
        tests/test_pc12a_stageC.py (policy mode on synthetic panels)."""
        if self.first_decision_ts is None:
            for st in self.leg_stats.values():
                st.leg_start_ts = ts
            self.first_decision_ts = ts
        eligible: Dict = {}
        for lid in sorted(decisions):
            dec = decisions[lid]
            st = self.leg_stats[lid]
            st.decisions_total += 1
            self.report["legs"][lid]["decisions"] += 1
            v = self.report["legs"][lid]["votes"]
            v[str(dec.vote)] = v.get(str(dec.vote), 0) + 1
            elig = self.eligibility.evaluate(lid, st,
                                             dec.feature_pit_snapshot, ts)
            if self._verdict_recorder is not None:
                self._verdict_recorder(lid, ts, elig.state == "ON")
            base_fields = self._scored_dec_fields(lid, dec, ts, elig)
            if elig.state != "ON":
                outcome = {"E1": "BLOCKED_FLOOR", "E3": "BLOCKED_STALE",
                           "E4": "BLOCKED_COST_BUDGET"}.get(
                               elig.rule_id or "", "BLOCKED_FLOOR")
                self._leg_outcome(lid, outcome)
                self._hist(outcome)
                self.journal.write("BLOCK", _jr.blocked_row(
                    outcome=outcome,
                    blocked_reason_detail=elig.detail,
                    decision_fields=base_fields))
                continue
            eligible[lid] = dec
            self.leg_desires[lid] = dec.desired_units
            self.journal.write("DECISION", base_fields)
        if not decisions:
            return
        if not eligible:
            return                          # frozen engine law (run_dry)

        if self.arm.get("sizing") == "equal_split":
            heat = self._heat_lookup(ts) if self._heat_lookup else 0.0
            self._b2_resize(heat)

        net = self.netting.net(dict(self.leg_desires))
        block_reason = None
        if net.tie_zero:
            block_reason = "L4 tie: nonzero votes net to 0 -> asset FLAT"
            for lid in eligible:
                self._leg_outcome(lid, "NETTED_TO_ZERO")
                self._hist("NETTED_TO_ZERO")
                self.journal.write("NETTED_TO_ZERO", _jr.blocked_row(
                    outcome="NETTED_TO_ZERO",
                    blocked_reason_detail=block_reason,
                    decision_fields=self._scored_dec_fields(
                        lid, eligible[lid], ts, _pol.EligibilityVerdict(
                            "ON", None, "eligible"))))
        elif (self.variant["netting"] == "super"
              and net.net_target_units == 0
              and any(dv != 0 for dv in self.leg_desires.values())):
            block_reason = ("L4 supermajority: agreeing share < 2/3 -> "
                            "asset FLAT this decision")
            for lid in eligible:
                self._leg_outcome(lid, "SUPERMAJORITY_BLOCK")
                self._hist("SUPERMAJORITY_BLOCK")
        target = int(net.net_target_units)

        clamped, cap_reason = sb.clamp_l5(target, self.symbol, self.caps_cfg)
        if clamped != target:
            for lid in eligible:
                self._leg_outcome(lid, "BLOCKED_RISK_CAP")
                self._hist("BLOCKED_RISK_CAP")
        target = int(clamped)
        delta = int(round(target - self.book_units))
        if delta == 0:
            return

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
                fields = self._scored_dec_fields(
                    lid, eligible[lid], ts,
                    _pol.EligibilityVerdict("ON", None, "eligible"))
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
            return

        fb = self._fill_bar_index(day, m)
        if fb is None:
            for lid in eligible:
                self._leg_outcome(lid, "UNAVAILABLE_FILL_BAR")
                self._hist("UNAVAILABLE_FILL_BAR")
            return
        ts_fill = dt.datetime.combine(ts.date(), dt.time(0, 0), tzinfo=UTC) \
            + dt.timedelta(minutes=fb)
        fq = self._price_fill(side, abs(delta), day, fb, ts_fill)
        commission = self.kernel.commission(abs(delta), fq.fill_price)
        spread_pips = (float(day.ask.open[fb])
                       - float(day.bid.open[fb])) / self.kernel.pip
        w4 = _pol.w4_check({f"{self.symbol}_mid_range": fq.mid_at_fill,
                            "spread_pips_max": spread_pips})
        if w4 is not None:
            for lid in eligible:
                self._leg_outcome(lid, "KILLSWITCH_FLAT")
                self._hist("W4_UNSEEN_STRUCTURE")
            return
        self.book_units += delta
        self.turnover_usd += abs(delta) * fq.fill_price
        if delta > 0:
            self.cash -= delta * fq.fill_price + commission
        else:
            self.cash += (-delta) * fq.fill_price - commission
        self.order_seq += 1
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
        self._commit_staged_fill()
        self._fold_fills.append({
            "ts": ts_fill, "delta": delta, "fq": fq,
            "commission": commission, "force_flat": False})
        self.all_fills.append({
            "ts": ts_fill, "delta": delta, "price": fq.fill_price,
            "force_flat": False})
        for lid in sorted(eligible):
            self._leg_outcome(lid, "FILLED")
            st = self.leg_stats[lid]
            st.decision_events.append(ts)
            st.decision_count_trailing += 1
            st.cost_events.append((ts, cost_total * self._leg_share(lid)))
        cash_delta = (-(delta * fq.fill_price + commission) if delta > 0
                      else ((-delta) * fq.fill_price - commission))
        self.journal.write("NET_ORDER", _jr.net_order_row(
            order_id=f"{self.symbol}-o{self.order_seq:05d}",
            order_kind=(eligible[min(eligible)].order_kind or "OPEN"),
            ts_fill_utc=_fmt(ts_fill), symbol=self.symbol, side=side,
            delta_units=delta, fill_price=fq.fill_price,
            quoted_side=fq.quoted_side, mid_at_fill=fq.mid_at_fill,
            spread_once_usd=fq.spread_once_usd,
            slip_beyond_halfspread_usd=fq.slip_beyond_halfspread_usd,
            cross_cost_usd=fq.cross_cost_usd, commission_usd=commission,
            cell_id=fq.cell_id, u3_band_id="U3_NON_EVENT",
            venue_model="PANEL_DUKA", units_after=self.book_units,
            contributing_legs=[{"leg_id": l, "vote": eligible[l].vote,
                                "contribution_units":
                                    self.leg_desires.get(l, 0)}
                               for l in sorted(eligible)],
            cash_delta_usd=cash_delta))

    def _commit_staged_fill(self) -> None:
        if self._staged_fills:
            self._captured_fills.append(self._staged_fills[-1])
            self._staged_fills.clear()

    def _scored_dec_fields(self, lid, dec, ts, elig) -> Dict:
        leg = self.leg_by_id[lid]
        ident = leg.identity
        st = self.leg_stats[lid]
        row = _jr.decision_row(
            ts_decision_utc=_fmt(ts), fold_id=self._current_fold_idx,
            cycle_id=ident.cycle_id, sleeve_id=ident.sleeve_id,
            leg_id=ident.candidate_id, symbol=self.symbol,
            family_id=ident.family_id, mech_key=ident.mech_key,
            outcome_exposed_label=ident.outcome_exposed_label,
            cluster_id=ident.cluster_id, direction_vote=dec.vote,
            desired_risk_units=dec.desired_units,
            entry_reason_code=dec.reason_code,
            eligibility_state=elig.state + (f" ({elig.rule_id})"
                                            if elig.rule_id else ""),
            risk_rule_state="netting voter",
            portfolio_state={"n_eligible": len(self.leg_desires)},
            feature_pit_snapshot=dec.feature_pit_snapshot,
            eligibility_rule_id=elig.rule_id,
            onoff_features={
                "decision_count_trailing": st.decision_count_trailing})
        row["label"] = LABEL
        return row

    def _leg_outcome(self, lid: str, outcome: str) -> None:
        d = self.report["legs"][lid]["fills_by_outcome"]
        d[outcome] = d.get(outcome, 0) + 1

    def _hist(self, key: str) -> None:
        h = self.report["blocked_reason_histogram"]
        h[key] = h.get(key, 0) + 1



# ---------------------------------------------------------------------------
# 3. Portfolio arm runner (per-symbol engines, shared guard, one journal)
# ---------------------------------------------------------------------------


def _arm_output_dir(name: str) -> str:
    return os.path.join(ARMS_DIR, name)


_POLICY_CACHE: Optional[Dict] = None


def _policy() -> Dict:
    global _POLICY_CACHE
    if _POLICY_CACHE is None:
        _POLICY_CACHE = load_policy()
    return _POLICY_CACHE


def _heat_lookup_from_schedule(sched: Dict):
    ts_epoch = sched["heat_ts_epoch"]
    heat = sched["heat_total"]

    def look(ts: dt.datetime) -> float:
        i = bisect.bisect_right(ts_epoch, ts.timestamp()) - 1
        return heat[i] if i >= 0 else 0.0
    return look


def _verdict_timeline(sched: Dict):
    """leg -> (epoch_ts[], on[]) over TRAIN then TEST policy verdicts."""
    out: Dict[str, Tuple[List[float], List[bool]]] = {}
    for src in ("train", "test"):
        for lid, recs in sched["verdicts"].get(src, {}).items():
            tss, ons = out.setdefault(lid, ([], []))
            for ts_epoch, on in recs:
                tss.append(ts_epoch)
                ons.append(on)
    return out


def _eligibility_factory(spec: Dict):
    mode = spec["elig"]
    if mode == "policy":
        rec = RecordingEligibility()
        return (lambda: rec), rec
    if mode == "alwayson":
        box = AlwaysOnEligibility()
        return (lambda: box), box
    if mode == "clock":
        duty = json.load(open(os.path.join(STAGEC_DIR, "TRAIN_EXTRACT.json"),
                              encoding="utf-8"))["duty"]
        box = ClockGateEligibility(duty)
        return (lambda: box), box
    if mode == "inverted":
        box = InvertedEligibility()
        return (lambda: box), box
    if mode == "lagged":
        sched = json.load(open(os.path.join(STAGEC_DIR,
                                            "POLICY_SCHEDULES.json"),
                               encoding="utf-8"))
        box = LaggedEligibility(_verdict_timeline(sched))
        return (lambda: box), box
    if mode == "oracle":
        body = json.load(open(os.path.join(STAGEC_DIR, "B8_SETS.json"),
                              encoding="utf-8"))
        box = OracleEligibility({int(k): v for k, v in
                                 body["admission_sets"].items()})
        return (lambda: box), box
    raise RuntimeError(f"unknown eligibility mode {mode}")


def run_arm(spec: Dict, out_dir: Optional[str] = None) -> Dict:
    """Run ONE scored arm over the pooled TEST folds; writes
    journal.jsonl + metrics.json under ARMS/<name> (or out_dir)."""
    pol = _policy()
    inputs = policy_engine_inputs(pol)
    folds = cal.fold_calendar()
    name = spec["arm"]
    out = out_dir or _arm_output_dir(name)
    metrics_path = os.path.join(out, "metrics.json")
    if os.path.exists(metrics_path):
        raise RuntimeError(f"arm {name} already scored at {metrics_path} "
                           f"(append-only law; refusing to re-run)")
    if spec["arm"] == "B3_BEST_SINGLE":
        # legs come from the TRAIN-only selection frozen PRE-test
        sel = json.load(open(os.path.join(STAGEC_DIR,
                                          "B3_SELECTION.json"),
                             encoding="utf-8"))
        spec = dict(spec)
        spec["legs"] = [sel["selected_leg"]]
    digest = arm_config_digest(spec, pol["policy_digest"])
    keep = set(spec["legs"]) if spec["legs"] else set(inputs["survivors"])
    by_symbol = {s: [c for c in cfgs
                     if (c.get("class_candidate_id") or c["corpus_gid"])
                     in keep]
                 for s, cfgs in inputs["by_symbol"].items()}
    by_symbol = {s: v for s, v in by_symbol.items() if v}
    if not by_symbol:
        raise RuntimeError(f"arm {name}: empty leg set")
    heat_lookup = None
    if spec["sizing"] == "equal_split":
        sched = json.load(open(os.path.join(STAGEC_DIR,
                                            "POLICY_SCHEDULES.json"),
                               encoding="utf-8"))
        heat_lookup = _heat_lookup_from_schedule(sched)
    elig_factory, _elig_box = _eligibility_factory(spec)
    guard = _pol.CostGuard(_pol.CostGuardState(
        cap_usd=inputs["guard_cap_usd"]))
    paper_out: Dict = {} if name == "B1_ALWAYS_ON" else None
    run_id = digest[:16]
    per_symbol: Dict[str, Dict] = {}
    digests: Dict[str, str] = {}
    heat_events: Dict[str, List] = {}
    verdicts_test: Dict[str, Dict] = {}
    journal_path = os.path.join(out, "journal.jsonl")
    with _jr.JournalWriter(journal_path, run_id, meta={
            "arm": name, "tier": spec["tier"], "pricing": spec["pricing"],
            "legs": sorted(keep), "policy_digest": pol["policy_digest"],
            "label": LABEL,
            "window": [folds[0].test_start.isoformat(),
                       folds[-1].test_end.isoformat()]}) as journal:
        for symbol in sorted(by_symbol):
            store = _panels.PanelStore()
            digests[symbol] = rd._symbol_digest(store, symbol, folds)
            eng = ScoredEngine(symbol, by_symbol[symbol], store, folds,
                               spec["tier"], inputs["variant"],
                               inputs["caps_cfg"], guard, journal, spec,
                               elig_factory, heat_lookup=heat_lookup,
                               paper_out=paper_out)
            eng.run(store)
            per_symbol[symbol] = {
                "fold_records": eng.fold_records,
                "cost_bill_totals_usd": {
                    k: _r6(v) for k, v in
                    eng.report["cost_bill_totals_usd"].items()},
                "blocked_reason_histogram":
                    dict(eng.report["blocked_reason_histogram"]),
                "legs": {lid: {"decisions": v["decisions"],
                               "votes": v["votes"],
                               "fills_by_outcome": v["fills_by_outcome"]}
                         for lid, v in eng.report["legs"].items()},
                "n_force_flat": eng.n_force_flat,
                "turnover_usd": _r6(eng.turnover_usd),
                "n_decisions": eng.n_decisions_total}
            heat_events[symbol] = [[t.timestamp(), u] for t, u in
                                   eng.heat_events]
            if spec["elig"] == "policy":
                verdicts_test[symbol] = {
                    lid: [[t.timestamp(), on] for t, on in recs]
                    for lid, recs in eng.eligibility.timeline.items()}
    metrics = _assemble_metrics(spec, pol, folds, per_symbol, digests,
                                digest)
    if spec["elig"] == "policy":
        metrics["heat_events_by_symbol"] = heat_events
        metrics["verdicts_test_by_symbol"] = verdicts_test
    if paper_out is not None:
        metrics["paper_fold_net_by_leg"] = paper_out
    _dump(metrics_path, metrics)
    return metrics


# ---------------------------------------------------------------------------
# 4. Portfolio metrics assembly (E-Law 1/2 quantities)
# ---------------------------------------------------------------------------


def _portfolio_weekly(per_symbol: Dict[str, Dict]) -> Dict[str, float]:
    """Merged portfolio weekly equity: 100k + sum of per-symbol sub-PnL,
    each symbol forward-filled from its own last mark (Stage-B book law).
    The fold-end Friday mark is the post-force-flat edge equity (the
    fold-edge realization is attributed to the closing fold)."""
    series: Dict[str, Dict[str, Dict[str, float]]] = {}
    for symbol, d in per_symbol.items():
        fr: Dict[str, float] = {}
        for fk in sorted(d["fold_records"]):
            rec = d["fold_records"][fk]
            for day, v in rec["friday_equity"].items():
                fr[day] = v
            fr[rec["test_window"][1]] = rec["edge_equity_usd"]
        series[symbol] = fr
    dates = sorted(set().union(*[set(v) for v in series.values()]))
    out: Dict[str, float] = {}
    last = {s: INITIAL_CASH for s in series}
    for d in dates:
        eq = INITIAL_CASH
        for s in sorted(series):
            if d in series[s]:
                last[s] = series[s][d]
            eq += last[s] - INITIAL_CASH
        out[d] = eq
    return out


def _assemble_metrics(spec: Dict, pol: Dict, folds, per_symbol: Dict,
                      digests: Dict, digest: str) -> Dict:
    weekly = _portfolio_weekly(per_symbol)
    dates = sorted(weekly)
    eq = [INITIAL_CASH] + [weekly[d] for d in dates]
    rets = [eq[i] - eq[i - 1] for i in range(1, len(eq))]
    net_pnl = sum(d["fold_records"][fk]["net_pnl_usd"]
                  for d in per_symbol.values()
                  for fk in d["fold_records"])
    # cash identity cross-check (folds flat at both edges)
    cash_net = sum(d["fold_records"][max(d["fold_records"])]["cash_end"]
                   - INITIAL_CASH for d in per_symbol.values())
    if abs(net_pnl - cash_net) > 1e-4:
        raise RuntimeError(f"arm {spec['arm']}: fold-net sum {net_pnl} != "
                           f"cash identity {cash_net} (integrity)")
    maxdd = _max_dd(eq)
    run_peak = -float("inf")
    dd_pct = 0.0
    for e in eq:
        run_peak = max(run_peak, e)
        if run_peak > 0:
            dd_pct = max(dd_pct, (run_peak - e) / run_peak)
    maxdd_pct = dd_pct
    # portfolio fold-edge equity per fold (all symbols flat at edges)
    edge_eq = {}
    for f in folds:
        edge_eq[f.fold_id] = INITIAL_CASH + sum(
            per_symbol[s]["fold_records"][f.fold_id]["edge_equity_usd"]
            - INITIAL_CASH for s in per_symbol)
    per_fold = []
    for f in folds:
        pnl = _r6(sum(d["fold_records"][f.fold_id]["net_pnl_usd"]
                      for d in per_symbol.values()))
        # per-fold DD: within-fold weekly path, peak resets at the fold
        # start = the PREVIOUS fold's edge equity (P7 law)
        feq = ([edge_eq[f.fold_id - 1]] if f.fold_id > 0
               else [INITIAL_CASH])
        for d in dates:
            if f.test_start.isoformat() <= d <= f.test_end.isoformat():
                feq.append(weekly[d])
            elif d > f.test_end.isoformat():
                break
        dd_f = _max_dd(feq) if feq else 0.0
        per_fold.append({
            "fold_id": f.fold_id,
            "test_window": [f.test_start.isoformat(),
                            f.test_end.isoformat()],
            "net_pnl_usd": pnl,
            "max_dd_usd": _r6(dd_f),
            "force_flat_cost_usd": _r6(sum(
                d["fold_records"][f.fold_id]["force_flat_cost_usd"]
                for d in per_symbol.values())),
            "n_fills": sum(d["fold_records"][f.fold_id]["n_fills"]
                           for d in per_symbol.values()),
            "cost_bill_usd": {
                k: _r6(sum(d["fold_records"][f.fold_id]["cost_bill_usd"][k]
                           for d in per_symbol.values()))
                for k in ("spread_once", "slip", "commission", "swap")}})
    hist: Dict[str, int] = {}
    for d in per_symbol.values():
        for k, v in d["blocked_reason_histogram"].items():
            hist[k] = hist.get(k, 0) + v
    n_weeks = len(rets)
    mean_r = statistics.fmean(rets) if rets else 0.0
    std_r = statistics.pstdev(rets) if n_weeks >= 2 else 0.0
    sr_hat = mean_r / std_r if std_r > 0 else 0.0
    # frozen Stage-B objective formula applied to THIS arm's pooled TEST
    # weekly series (P3's obj; SR0 frozen at the Stage-B freeze value)
    sr0 = pol["sr0_inputs"]["sr0"]
    obj_test = net_pnl - n_weeks * sr0 * std_r - maxdd
    return {
        "objective_test_usd": _r6(obj_test),
        "objective_law": ("obj = netPnL - W*SR0*sigma_w - maxDD on the "
                          "pooled TEST weekly path (the frozen Stage-B "
                          "formula, never re-fit; SR0 frozen at Stage-B)"),
        "schema": SCHEMA_ARM, "label": LABEL, "arm": spec["arm"],
        "arm_config": {k: spec[k] for k in
                       ("arm", "tier", "pricing", "legs", "elig",
                        "sizing")},
        "arm_config_digest": digest,
        "policy_digest": pol["policy_digest"],
        "tier": spec["tier"], "pricing": spec["pricing"],
        "window": [folds[0].test_start.isoformat(),
                   folds[-1].test_end.isoformat()],
        "net_pnl_pooled_usd": _r6(net_pnl),
        "max_dd_pooled_usd": _r6(maxdd),
        "max_dd_pooled_pct": _r6(maxdd_pct),
        "n_weekly_returns": n_weeks,
        "weekly_mean_usd": _r6(mean_r), "weekly_std_usd": _r6(std_r),
        "sr_hat_weekly": _r6(sr_hat),
        "per_fold": per_fold,
        "fold_edge_force_flat_cost_total_usd": _r6(sum(
            pf["force_flat_cost_usd"] for pf in per_fold)),
        "n_fills_total": sum(pf["n_fills"] for pf in per_fold),
        "n_force_flat": sum(d["n_force_flat"]
                            for d in per_symbol.values()),
        "turnover_usd": _r6(sum(d["turnover_usd"]
                                 for d in per_symbol.values())),
        "n_decisions_total": sum(d["n_decisions"]
                                  for d in per_symbol.values()),
        "blocked_reason_histogram": hist,
        "cost_bill_totals_usd": {
            k: _r6(sum(d["cost_bill_totals_usd"][k]
                       for d in per_symbol.values()))
            for k in ("spread_once", "slip", "slip_gap_excess",
                      "commission", "swap")},
        "weekly_equity": {d: _r6(v) for d, v in weekly.items()},
        "per_symbol": {s: {k: v for k, v in d.items()
                           if k != "fold_records"}
                       for s, d in per_symbol.items()},
        "per_symbol_fold_records": {
            s: {str(fk): d["fold_records"][fk]
                for fk in sorted(d["fold_records"])}
            for s, d in per_symbol.items()},
        "data_digests": digests,
        "code_digest": _rd._code_digest()}


def b0_metrics(pol: Dict, folds) -> Dict:
    """B0 FLAT: no orders ever; equity constant (P1-B0 sub-bar law)."""
    weekly = {}
    d = folds[0].test_start
    while d <= folds[-1].test_end:
        weekly[d.isoformat()] = INITIAL_CASH
        d += dt.timedelta(days=7)
    return {
        "schema": SCHEMA_ARM, "label": LABEL, "arm": "B0_FLAT",
        "arm_config": {"arm": "B0_FLAT", "tier": 1.0, "pricing": "base",
                       "legs": None, "elig": "none", "sizing": "none"},
        "arm_config_digest": arm_config_digest(
            {"arm": "B0_FLAT", "tier": 1.0, "pricing": "base", "legs":
             None, "elig": "none", "sizing": "none"}, pol["policy_digest"]),
        "policy_digest": pol["policy_digest"], "tier": 1.0,
        "pricing": "base",
        "window": [folds[0].test_start.isoformat(),
                   folds[-1].test_end.isoformat()],
        "net_pnl_pooled_usd": 0.0, "max_dd_pooled_usd": 0.0,
        "max_dd_pooled_pct": 0.0, "n_weekly_returns": 207,
        "weekly_mean_usd": 0.0, "weekly_std_usd": 0.0,
        "sr_hat_weekly": 0.0,
        "per_fold": [{"fold_id": f.fold_id,
                      "test_window": [f.test_start.isoformat(),
                                      f.test_end.isoformat()],
                      "net_pnl_usd": 0.0, "max_dd_usd": 0.0,
                      "force_flat_cost_usd": 0.0, "n_fills": 0,
                      "cost_bill_usd": {"spread_once": 0.0, "slip": 0.0,
                                        "commission": 0.0, "swap": 0.0}}
                     for f in folds],
        "fold_edge_force_flat_cost_total_usd": 0.0, "n_fills_total": 0,
        "n_force_flat": 0, "turnover_usd": 0.0, "n_decisions_total": 0,
        "blocked_reason_histogram": {},
        "cost_bill_totals_usd": {"spread_once": 0.0, "slip": 0.0,
                                 "slip_gap_excess": 0.0, "commission": 0.0,
                                 "swap": 0.0},
        "weekly_equity": weekly, "per_symbol": {},
        "per_symbol_fold_records": {}, "data_digests": {},
        "code_digest": _rd._code_digest(),
        "note": "B0 FLAT by construction: no orders, equity constant "
                "100k; netPnL=0, maxDD=0 (PASS_BARS_V2 1)"}


# ---------------------------------------------------------------------------
# 5. B3 BEST_SINGLE selection (TRAIN-only, frozen BEFORE any test run)
# ---------------------------------------------------------------------------


def _skew_kurt(rs: List[float]) -> Tuple[float, float]:
    n = len(rs)
    m = statistics.fmean(rs)
    sd = statistics.pstdev(rs)
    if sd == 0 or n < 3:
        return 0.0, 3.0
    m2 = sum((x - m) ** 2 for x in rs) / n
    m3 = sum((x - m) ** 3 for x in rs) / n
    m4 = sum((x - m) ** 4 for x in rs) / n
    return m3 / m2 ** 1.5, m4 / m2 ** 2


def dsr(returns: List[float], sr0: float) -> Dict:
    """Bailey & Lopez de Prado DSR (PASS_BARS_V2 5). Sharpe uses the
    population stdev (the frozen Stage-B objective arithmetic)."""
    n = len(returns)
    if n < 2:
        return {"n": n, "sr_hat": 0.0, "dsr": 0.5, "psr": 0.5,
                "sr0": sr0, "skew": 0.0, "kurt": 3.0,
                "degenerate": True}
    sd = statistics.pstdev(returns)
    mean = statistics.fmean(returns)
    sr = mean / sd if sd > 0 else 0.0
    g3, g4 = _skew_kurt(returns)
    nd = statistics.NormalDist()

    def _phi(z):
        denom = 1 - g3 * sr + ((g4 - 1) / 4.0) * sr * sr
        if denom <= 0:
            return 0.5
        return nd.cdf(z * math.sqrt(n - 1) / math.sqrt(denom))
    return {"n": n, "sr_hat": _r6(sr), "sr0": sr0,
            "skew": _r6(g3), "kurt": _r6(g4),
            "dsr": _r6(_phi(sr - sr0)), "psr": _r6(_phi(sr)),
            "degenerate": sd == 0.0}


def mode_b3select() -> Dict:
    """obj_B3(leg) = DSR_T of the leg's TRAIN weekly NET returns at cost
    tier x2.0 (full kernel), SR0/N_eff from the full ledger EXACTLY as in
    P5 (the Stage-B freeze values). Selection + tie-break recorded; the
    artifact is written BEFORE any test arm runs (dispatch law)."""
    pol = _policy()
    slate = [leg["leg_id"] for leg in pol["slate"]]
    sr0 = pol["sr0_inputs"]["sr0"]
    diag_dir = os.path.join(CONTROL, "diagnostics")
    cands = []
    for fn in sorted(os.listdir(diag_dir)):
        if not (fn.startswith("DIAG_X2_") and fn.endswith(".json")):
            continue
        body = json.load(open(os.path.join(diag_dir, fn), encoding="utf-8"))
        assert body["tier"] == 2.0
        for leg in body["legs"]:
            if leg["leg_id"] not in slate:
                continue
            fe = leg["folds"][0]["friday_equity"]
            ks = sorted(fe)
            rs = [fe[ks[i]] - fe[ks[i - 1]] for i in range(1, len(ks))]
            dd = _max_dd([fe[k] for k in ks])
            d = dsr(rs, sr0)
            cands.append({
                "leg_id": leg["leg_id"], "obj_b3_dsr": d["dsr"],
                "dsr_detail": d,
                "train_net_x2_usd": leg["folds"][0]["net_pnl_usd"],
                "train_maxdd_x2_usd": _r6(dd),
                "train_turnover_x2_usd": None,   # not in the X2 artifact;
                # only needed on an exact DSR tie (tie-break step 3)
                "n_trades_x2": leg["folds"][0]["n_entries"]})
    if len(cands) != len(slate):
        raise RuntimeError(f"B3 candidates {len(cands)} != slate "
                           f"{len(slate)} (X2 diagnostics incomplete)")
    ranked = sorted(cands, key=lambda c: (-c["obj_b3_dsr"],
                                          -c["train_net_x2_usd"],
                                          c["train_maxdd_x2_usd"],
                                          c["leg_id"]))
    sel = {
        "schema": "pc12a_stagec_b3_selection@1", "label": "TRAIN-ONLY",
        "frozen_utc": _now(), "law": (
            "PASS_BARS_V2 1 B3: obj_B3 = DSR_T of the leg's TRAIN "
            "decision-cycle NET returns at tier x2.0 (full kernel), SR0/"
            "N_eff from the full discovery ledger exactly as in P5; "
            "tie-break (frozen): (1) higher TRAIN net at x2.0, (2) lower "
            "TRAIN maxDD USD, (3) lower TRAIN turnover USD, (4) earlier "
            "trial-ledger row id"),
        "sr0_source": "POLICY_FROZEN.json sr0_inputs (ledger as of the "
                      "Stage-B freeze, 805 rows)",
        "sr0": sr0,
        "candidates": ranked,
        "selected_leg": ranked[0]["leg_id"],
        "tie_break_fired": (len(ranked) > 1
                            and ranked[0]["obj_b3_dsr"]
                            == ranked[1]["obj_b3_dsr"]),
        "written_before_any_test_arm": True}
    _dump(os.path.join(STAGEC_DIR, "B3_SELECTION.json"), sel)
    print(json.dumps({"mode": "b3select",
                      "selected": sel["selected_leg"],
                      "dsr": ranked[0]["obj_b3_dsr"],
                      "tie": sel["tie_break_fired"]}))
    return sel


# ---------------------------------------------------------------------------
# 6. TRAIN extraction (B5 duty / B4 duty+flip) via instrumented V3 re-run
# ---------------------------------------------------------------------------


class _TrainRecorder:
    """Wraps the TRAIN V3 re-run: records per-leg eligibility verdicts;
    pure delegation (determinism asserted vs the frozen objective)."""

    def __init__(self):
        self.base = _pol.Eligibility()
        self.timeline: Dict[str, List[Tuple[dt.datetime, bool]]] = {}

    def evaluate(self, leg_id, stats, pit_snapshot, now):
        v = self.base.evaluate(leg_id, stats, pit_snapshot, now)
        self.timeline.setdefault(leg_id, []).append((now, v.state == "ON"))
        return v


def _duty_flip(timeline: Dict[str, List[Tuple[dt.datetime, bool]]]):
    out = {}
    for lid, recs in sorted(timeline.items()):
        ons = [on for _, on in recs]
        n = len(ons)
        duty = sum(ons) / n if n else 0.0
        flips = sum(1 for i in range(1, n) if ons[i] != ons[i - 1])
        flip = flips / (n - 1) if n > 1 else 0.0
        out[lid] = {"duty": _r6(duty), "flip_rate": _r6(flip),
                    "n_decisions_train": n, "n_on_train": int(sum(ons))}
    return out


def mode_trainextract() -> Dict:
    """Re-run the frozen V3 over the TRAIN prefix with the recorder; the
    objective must reproduce the frozen selection statistic byte-value
    (determinism guard); duty/flip feed B5/B4 (TRAIN-realized). ONE pass
    per symbol with a fresh shared guard (the frozen Stage-B order)."""
    pol = _policy()
    inputs = policy_engine_inputs(pol)
    folds = cal.fold_calendar()
    by_symbol = inputs["by_symbol"]
    timelines: Dict[str, List] = {}
    weekly: Dict[str, Dict[str, float]] = {}
    guard = _pol.CostGuard(_pol.CostGuardState(
        cap_usd=inputs["guard_cap_usd"]))
    for symbol in sorted(by_symbol):
        rec = _TrainRecorder()
        store = _panels.PanelStore()
        eng = sb.PortfolioEngine(symbol, by_symbol[symbol], store, folds,
                                 1.0, inputs["variant"],
                                 inputs["caps_cfg"], guard)
        eng.eligibility = rec
        eng.run(store)
        for lid, tl in rec.timeline.items():
            timelines[lid] = [[t.timestamp(), on] for t, on in tl]
        fe = eng.snapshots[folds[-1].fold_id].friday_equity
        weekly[symbol] = {d.isoformat(): v for d, v in fe.items()}
    duty_flip = _duty_flip({lid: [(dt.datetime.fromtimestamp(e, UTC), on)
                                  for e, on in recs]
                            for lid, recs in timelines.items()})
    pf_weekly = sb._portfolio_weekly({
        s: {"friday_equity_fold7": weekly[s]} for s in weekly})
    obj = sb.train_objective(pf_weekly, pol["sr0_inputs"]["sr0"])
    frozen = pol["selection_statistic"]
    for k in ("net_pnl_usd", "max_dd_usd", "sr_hat", "objective_usd"):
        if abs(obj[k] - frozen[k]) > 1e-4:
            raise RuntimeError(
                f"TRAIN re-run determinism guard FAILED on {k}: "
                f"{obj[k]} vs frozen {frozen[k]} (STOP-3)")
    out = {
        "schema": "pc12a_stagec_train_extract@1", "label": "TRAIN-ONLY",
        "frozen_utc": _now(),
        "law": ("duty = share of the leg's TRAIN decision events with "
                "L2-ON under the frozen policy; flip_rate = share of "
                "consecutive-decision state changes (B4 turnover match)"),
        "duty": {lid: v["duty"] for lid, v in duty_flip.items()},
        "flip_rate": {lid: v["flip_rate"] for lid, v in duty_flip.items()},
        "per_leg": duty_flip,
        "verdicts_train": timelines,
        "determinism_guard": {
            "rerun_objective": obj, "frozen_objective":
                {k: frozen[k] for k in ("net_pnl_usd", "max_dd_usd",
                                        "sr_hat", "objective_usd")},
            "match": True}}
    _dump(os.path.join(STAGEC_DIR, "TRAIN_EXTRACT.json"), out)
    print(json.dumps({"mode": "trainextract",
                      "legs": len(duty_flip),
                      "duty_range": [min(v["duty"] for v in
                                         duty_flip.values()),
                                     max(v["duty"] for v in
                                         duty_flip.values())]}))
    return out


# ---------------------------------------------------------------------------
# 7. POLICY schedules (B2 heat series; B7 verdicts) + B8 admission sets
# ---------------------------------------------------------------------------


def mode_schedules() -> Dict:
    """Assemble the frozen cross-arm inputs from the completed POLICY and
    B1 arms: (a) the policy's per-decision TOTAL HEAT TARGET step series
    (B2's frozen input); (b) the policy verdict timelines TRAIN+TEST (B7's
    frozen input); (c) B8 oracle admission sets from B1's paper book."""
    pol = _policy()
    pol_m = json.load(open(os.path.join(_arm_output_dir("POLICY"),
                                       "metrics.json"), encoding="utf-8"))
    # (a) heat step series: merge per-symbol post-decision |units| series
    events = []          # (epoch, symbol, units)
    for symbol, evs in pol_m["heat_events_by_symbol"].items():
        for e, u in evs:
            events.append((e, symbol, u))
    events.sort(key=lambda x: (x[0], x[1]))
    cur: Dict[str, float] = {}
    ts_epoch: List[float] = []
    heat: List[float] = []
    for e, symbol, u in events:
        cur[symbol] = u
        ts_epoch.append(e)
        heat.append(sum(cur.values()))
    # (b) verdict timelines
    tr = json.load(open(os.path.join(STAGEC_DIR, "TRAIN_EXTRACT.json"),
                        encoding="utf-8"))["verdicts_train"]
    vt = pol_m["verdicts_test_by_symbol"]
    verdicts = {"train": {}, "test": {}}
    for lid, recs in tr.items():        # TRAIN extract: leg -> [[epoch,on]]
        verdicts["train"][lid] = recs
    for sym, legs in vt.items():        # POLICY test run: symbol -> leg -> [[...]]
        for lid, recs in legs.items():
            verdicts["test"][lid] = recs
    # (c) B8 admission sets from B1's paper fold nets
    b1_m = json.load(open(os.path.join(_arm_output_dir("B1_ALWAYS_ON"),
                                      "metrics.json"), encoding="utf-8"))
    paper = b1_m["paper_fold_net_by_leg"]
    sets: Dict[str, List[str]] = {}
    detail = {}
    for fk in range(8):
        winners = sorted(lid for lid, folds in paper.items()
                         if folds.get(str(fk), 0.0) > 0.0)
        sets[str(fk)] = winners
        detail[str(fk)] = {lid: folds.get(str(fk), 0.0)
                           for lid, folds in sorted(paper.items())}
    out = {
        "schema": "pc12a_stagec_schedules@1", "label": LABEL,
        "frozen_utc": _now(),
        "law": {
            "heat": ("B2 reads the policy's realized per-decision TOTAL "
                     "HEAT TARGET (gross units across symbols, step "
                     "series at every decision instant; frozen input, "
                     "never re-fit)"),
            "verdicts": ("B7 uses the policy's own eligibility verdict "
                         "at the latest decision instant <= ts-26w (TRAIN "
                         "timeline for the first test fold's lag window)"),
            "b8": ("B8 oracle admits, per fold, the slate legs with "
                   "positive always-on PAPER (sum-of-legs) net for that "
                   "fold, from the B1 run's paper book; REPORTING ONLY")},
        "heat_ts_epoch": ts_epoch, "heat_total": [_r6(h) for h in heat],
        "verdicts": verdicts,
        "b8_admission_detail": detail}
    _dump(os.path.join(STAGEC_DIR, "POLICY_SCHEDULES.json"), out)
    _dump(os.path.join(STAGEC_DIR, "B8_SETS.json"), {
        "schema": "pc12a_stagec_b8_sets@1", "label": LABEL,
        "admission_sets": sets, "paper_fold_net_by_leg": paper,
        "law": out["law"]["b8"]})
    print(json.dumps({"mode": "schedules", "heat_events": len(ts_epoch),
                      "n_folds_with_winners":
                          sum(1 for v in sets.values() if v)}))
    return out


# ---------------------------------------------------------------------------
# 8. B4 RANDOM-GATE battery (ONE identity, 128 seeded sub-runs)
# ---------------------------------------------------------------------------


def run_b4_seed(seed: int, duty: Dict[str, float],
                flip: Dict[str, float], out_dir: str) -> Dict:
    """One seeded B4 sub-run (duty+turnover-matched random gating)."""
    pol = _policy()
    inputs = policy_engine_inputs(pol)
    folds = cal.fold_calendar()
    spec = _arm(f"B4_SEED{seed}", elig="markov")
    digest = arm_config_digest(spec, pol["policy_digest"],
                               extra=f"seed={seed}")
    guard = _pol.CostGuard(_pol.CostGuardState(
        cap_usd=inputs["guard_cap_usd"]))
    per_symbol = {}
    with _jr.JournalWriter(os.path.join(out_dir, "journal.jsonl"),
                           digest[:16], meta={
                               "arm": spec["arm"], "seed": seed,
                               "tier": 1.0, "policy_digest":
                                   pol["policy_digest"],
                               "label": LABEL}) as journal:
        for symbol in sorted(inputs["by_symbol"]):
            store = _panels.PanelStore()
            mk = (lambda s=seed: MarkovEligibility(s, duty, flip))
            eng = ScoredEngine(symbol, inputs["by_symbol"][symbol], store,
                               folds, 1.0, inputs["variant"],
                               inputs["caps_cfg"], guard, journal, spec,
                               mk)
            eng.run(store)
            per_symbol[symbol] = {
                "fold_records": eng.fold_records,
                "cost_bill_totals_usd": eng.report["cost_bill_totals_usd"],
                "blocked_reason_histogram":
                    dict(eng.report["blocked_reason_histogram"]),
                "legs": eng.report["legs"],
                "n_force_flat": eng.n_force_flat,
                "turnover_usd": eng.turnover_usd,
                "n_decisions": eng.n_decisions_total}
    metrics = _assemble_metrics(spec, pol, folds, per_symbol, {},
                                digest)
    metrics["seed"] = seed
    _dump(os.path.join(out_dir, "metrics.json"), metrics)
    return metrics


def mode_b4(parallel: int = 6) -> Dict:
    tr = json.load(open(os.path.join(STAGEC_DIR, "TRAIN_EXTRACT.json"),
                        encoding="utf-8"))
    duty, flip = tr["duty"], tr["flip_rate"]
    seeds = [B4_SEED_BASE + k for k in range(N_B4_SEEDS)]
    seed_list_digest = hashlib.sha256(
        json.dumps(seeds).encode()).hexdigest()
    root = os.path.join(STAGEC_DIR, "B4")
    results = []
    t0 = time.time()
    from concurrent.futures import ProcessPoolExecutor
    jobs = []
    for s in seeds:
        od = os.path.join(root, f"SEED{s}")
        if not os.path.exists(os.path.join(od, "metrics.json")):
            jpath = os.path.join(od, "journal.jsonl")
            if os.path.exists(jpath):
                # incomplete sub-run from a killed job: journal without
                # metrics is not evidence -- remove and re-run (disclosed)
                os.remove(jpath)
            jobs.append((s, duty, flip, od))
    if jobs:
        with ProcessPoolExecutor(max_workers=parallel) as ex:
            futs = [ex.submit(run_b4_seed, s, d, f, od)
                    for s, d, f, od in jobs]
            for fu in futs:
                fu.result()
    for s in seeds:
        results.append(json.load(open(
            os.path.join(root, f"SEED{s}", "metrics.json"),
            encoding="utf-8")))
    nets = sorted(r["net_pnl_pooled_usd"] for r in results)
    dds = sorted(r["max_dd_pooled_usd"] for r in results)
    med_n = statistics.median(nets)
    med_d = statistics.median(dds)
    battery = {
        "schema": "pc12a_stagec_b4_battery@1", "label": LABEL,
        "law": ("PASS_BARS_V2 1 B4 + E-Law 8: ONE baseline identity "
                "executed as 128 seeded duty+turnover-matched sub-runs "
                "(own budget line); per-leg two-state chain, stationary "
                "duty = TRAIN policy duty, per-decision flip rate = TRAIN "
                "policy flip rate; seed list frozen below"),
        "n_seeds": len(seeds), "seed_list": seeds,
        "seed_list_digest": seed_list_digest,
        "duty": duty, "flip_rate": flip,
        "median_net_pnl_usd": _r6(med_n),
        "median_max_dd_usd": _r6(med_d),
        "net_pnl_min_usd": _r6(nets[0]), "net_pnl_max_usd": _r6(nets[-1]),
        "max_dd_min_usd": _r6(dds[0]), "max_dd_max_usd": _r6(dds[-1]),
        "elapsed_seconds": round(time.time() - t0, 1),
        "per_seed": [{"seed": r["seed"],
                      "net_pnl_pooled_usd": r["net_pnl_pooled_usd"],
                      "max_dd_pooled_usd": r["max_dd_pooled_usd"],
                      "objective_test_usd":
                          r.get("objective_test_usd")}
                     for r in sorted(results, key=lambda x: x["seed"])]}
    _dump(os.path.join(STAGEC_DIR, "B4_BATTERY.json"), battery)
    print(json.dumps({"mode": "b4", "seeds": len(seeds),
                      "median_net": battery["median_net_pnl_usd"],
                      "median_dd": battery["median_max_dd_usd"]}))
    return battery


# ---------------------------------------------------------------------------
# 9. P5 discovery-ledger inputs (N / N_eff / V / CSCV matrix)
# ---------------------------------------------------------------------------


def _dedupe_ledger(rows: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """F-11/A-2 dedup: identical arm_config_digest AND data_snapshot_digest
    count as ONE trial (keep first, list duplicates)."""
    seen = set()
    keep, dups = [], []
    for r in rows:
        key = (r.get("arm_config_digest"),
               r.get("data_snapshot_digest"))
        if key in seen:
            dups.append(r)
        else:
            seen.add(key)
            keep.append(r)
    return keep, dups


def sr0_from_ledger(ledger_path: str = LEDGER_PATH) -> Dict:
    """N / N_eff / V per the frozen Stage-B formula over the FULL ledger
    at Stage-C (P5 law: every Stage-A try, Stage-B node, Stage-C arm)."""
    rows = [json.loads(l) for l in open(ledger_path, encoding="utf-8")]
    dedup, dups = _dedupe_ledger(rows)
    n = len(dedup)
    # N_eff per the FROZEN Stage-B formula (sb.freeze_sr0): distinct
    # (sleeve, cluster) families over the ledger's rows. Row-level dedup
    # cannot merge families (a kept screening row may lack cluster_id --
    # deduping on it would UNDERSTATE the family count and shrink SR0;
    # the frozen raw-row count is the conservative direction).
    n_eff = len({(r.get("sleeve_id"), r.get("cluster_id"))
                 for r in rows}) + 1
    series = sb._solo_series(os.path.join(CONTROL, "diagnostics"))
    sharpes = []
    for leg, fe in sorted(series.items()):
        rs = sb._weekly_pnl(fe)
        if len(rs) >= 3 and statistics.pstdev(rs) > 0:
            sharpes.append(statistics.fmean(rs) / statistics.pstdev(rs))
    v = statistics.pvariance(sharpes)
    nd = statistics.NormalDist()
    e_max = ((1 - GAMMA) * nd.inv_cdf(1 - 1 / n_eff)
             + GAMMA * nd.inv_cdf(1 - 1 / (n_eff * EUL)))
    sr0 = math.sqrt(v) * e_max
    return {"n_ledger_rows": len(rows), "n": n, "n_dupes": len(dups),
            "n_eff": n_eff, "n_sharpe_legs": len(sharpes),
            "v_trial_sharpes": v, "e_max_null": e_max, "sr0": sr0,
            "sr0_raw_n": math.sqrt(v) * (
                (1 - GAMMA) * nd.inv_cdf(1 - 1 / n)
                + GAMMA * nd.inv_cdf(1 - 1 / (n * EUL)))}


def cscv_matrix() -> Dict:
    """The N x T discovery-side trial-return matrix: the 62 diag legs'
    fold-7 TRAIN weekly return series (solo MAIN pass) + the 8 Stage-B
    variants' TRAIN weekly series; zero-variance trials keep Sharpe 0.0
    (deterministic, disclosed; never excluded silently)."""
    legs = sb._solo_series(os.path.join(CONTROL, "diagnostics"))
    names, series = [], []
    for lid in sorted(legs):
        fe = legs[lid]
        ks = sorted(fe)
        rs = [fe[ks[i]] - fe[ks[i - 1]] for i in range(1, len(ks))]
        names.append(lid)
        series.append(rs)
    for vid in [v["variant_id"] for v in sb.VARIANT_GRID]:
        body = json.load(open(os.path.join(
            CONTROL, "diagnostics", "stageb", f"VARIANT_{vid}.json"),
            encoding="utf-8"))
        we = body["weekly_equity_fold7"]
        ks = sorted(we)
        rs = [we[ks[i]] - we[ks[i - 1]] for i in range(1, len(ks))]
        names.append(f"BV:{vid}")
        series.append(rs)
    t = min(len(s) for s in series)
    mat = np.array([s[:t] for s in series], dtype=float)
    return {"names": names, "matrix": mat}


def cscv_pbo(blocks: int = 16) -> Dict:
    """PBO = fraction of C(16,8) combinations where the TRAIN-best trial
    ranks below the OOS median (lambda_c < 0); pure core in
    pbo_from_matrix (unit-tested on synthetic matrices)."""
    body = cscv_matrix()
    out = pbo_from_matrix(body["matrix"], blocks)
    out["pbo"] = _r6(out["pbo"])
    out["names"] = body["names"]
    out["zero_variance_policy"] = ("constant series score Sharpe 0.0 "
                                   "(deterministic; exclusions counted "
                                   "as 0)")
    return out


# ---------------------------------------------------------------------------
# 10. Bars evaluation (P1-P8; every bar PASS/FAIL/NOT_RUN with numbers)
# ---------------------------------------------------------------------------


def _load_metrics(name: str) -> Dict:
    return json.load(open(os.path.join(_arm_output_dir(name),
                                       "metrics.json"), encoding="utf-8"))


def _strict(gt: Optional[float], lt: Optional[float]) -> bool:
    return bool(gt) if gt is not None else bool(lt)


def p_and(p_net: float, b_net: float, p_dd: float,
          b_dd: float) -> Dict:
    """E-Law 4 strict AND-semantics: net strictly higher AND maxDD
    strictly lower; ties FAIL."""
    ok_pnl = p_net > b_net
    ok_dd = p_dd < b_dd
    return {"pnl_leg": ok_pnl, "dd_leg": ok_dd, "pass": ok_pnl and ok_dd}


def p3_clause1(obj_p: float, seed_objs: List[float]) -> Dict:
    n = len(seed_objs)
    below = sum(1 for o in seed_objs if obj_p > o)   # ties NOT below
    return {"n_seeds": n, "seeds_below": below,
            "threshold": 0.95 * n, "pass": below >= 0.95 * n}


def p7_check(per_fold: List[Dict], pooled_net: float, pooled_dd: float,
             durations: Optional[List[float]] = None) -> Dict:
    """P7: every fold net <= 50% of pooled net AND every fold DD <= 2x
    the pro-rata pooled DD (equal folds -> pooled/8)."""
    nf = len(per_fold)
    durs = durations or [1.0] * nf
    share = [d / sum(durs) for d in durs]
    offenders = []
    for pf in per_fold:
        f = pf["fold_id"]
        if pf["net_pnl_usd"] > 0.50 * pooled_net:
            offenders.append({"fold": f, "kind": "P7_PNL_SHARE",
                              "share": pf["net_pnl_usd"] / pooled_net})
        if pf["max_dd_usd"] > 2.0 * pooled_dd * share[f]:
            offenders.append({"fold": f, "kind": "P7_DD_SHARE",
                              "ratio": pf["max_dd_usd"]
                              / (pooled_dd * share[f])})
    return {"pass": not offenders, "offenders": offenders}


def p8_check(pairs: List[Dict]) -> Dict:
    """P8 close-code law: exactly one break -> POLICY_ONE_LEG_CARRIER;
    two or more -> POLICY_NO_INCREMENTAL_VALUE (P8_COALITION)."""
    breaks = [p for p in pairs if not p["ok"]]
    if not breaks:
        code, sub = None, None
    elif len(breaks) == 1:
        code, sub = "POLICY_ONE_LEG_CARRIER", None
    else:
        code, sub = "POLICY_NO_INCREMENTAL_VALUE", "P8_COALITION"
    return {"n_breaks": len(breaks), "close_code": code, "sub_tag": sub,
            "breaks": breaks, "pass": not breaks}


def pbo_from_matrix(mat: "np.ndarray", blocks: int = 16) -> Dict:
    """PBO pure core: 16 contiguous blocks (leading trim), C(16,8)
    combinations, train-best's OOS rank fraction, lambda = logit."""
    n_trials, t_all = mat.shape
    t = (t_all // blocks) * blocks
    dropped = t_all - t
    mat = mat[:, t_all - t:]                    # drop LEADING periods
    bl = mat.reshape(n_trials, blocks, -1)
    s1 = bl.sum(axis=2)
    s2 = (bl ** 2).sum(axis=2)
    cnt = bl.shape[2]
    from itertools import combinations
    comb = list(combinations(range(blocks), blocks // 2))
    n_below = 0
    for train_idx in comb:
        mask = np.zeros(blocks, dtype=bool)
        mask[list(train_idx)] = True

        def _sharpe(m):
            c = cnt * m.sum()
            m1 = s1[:, m].sum(axis=1)
            m2 = s2[:, m].sum(axis=1)
            mean = m1 / c
            var = np.maximum(m2 / c - mean ** 2, 0.0)
            sd = np.sqrt(var)
            return np.where(sd > 0, mean / np.where(sd > 0, sd, 1.0),
                            0.0)
        tr = _sharpe(mask)
        te = _sharpe(~mask)
        best = int(np.argmax(tr))
        order = np.argsort(te)
        rank = int(np.where(order == best)[0][0])
        omega = rank / (n_trials - 1) if n_trials > 1 else 0.5
        lam = (math.inf if omega >= 1.0 else
               (-math.inf if omega <= 0.0 else
                math.log(omega / (1.0 - omega))))
        if lam < 0:
            n_below += 1
    return {"n_trials": n_trials, "t_weeks_used": t,
            "t_weeks_dropped_leading": dropped, "blocks": blocks,
            "n_combinations": len(comb), "pbo": n_below / len(comb)}


def evaluate_bars(sr0_inputs: Optional[Dict] = None) -> Dict:
    pol = _policy()
    folds = cal.fold_calendar()
    m = {n: _load_metrics(n) for n in [
        "POLICY", "B1_ALWAYS_ON", "B2_EQUAL_WEIGHT", "B3_BEST_SINGLE",
        "B5_CLOCK_GATE", "B6_INVERTED", "B7_LAGGED", "B8_ORACLE",
        "POLICY_X15", "B1_X15", "POLICY_X20", "B1_X20",
        "POLICY_P90", "B1_P90"]}
    for lid in [leg["leg_id"] for leg in pol["slate"]]:
        m[f"POLICY_MO_{lid}"] = _load_metrics(f"POLICY_MO_{lid}")
        m[f"B1_MO_{lid}"] = _load_metrics(f"B1_MO_{lid}")
    b0 = b0_metrics(pol, folds)
    b4 = json.load(open(os.path.join(STAGEC_DIR, "B4_BATTERY.json"),
                        encoding="utf-8"))
    P = m["POLICY"]
    B1 = m["B1_ALWAYS_ON"]

    def net(x):
        return x["net_pnl_pooled_usd"]

    def dd(x):
        return x["max_dd_pooled_usd"]

    bars: Dict[str, Dict] = {}

    def bar(bar_id, status, **kw):
        bars[bar_id] = {"status": status, **kw}

    # P1 ------------------------------------------------------------------
    p1b0 = net(P) > 0.0
    bar("P1-B0", "PASS" if p1b0 else "FAIL",
        policy_net=net(P), law="netPnL(P) > 0 pooled test folds",
        close_code=None if p1b0 else "POLICY_NO_INCREMENTAL_VALUE",
        sub_tag=None if p1b0 else "P1_B0_ABSOLUTE")
    p1_pnl = net(P) > net(B1)
    p1_dd = dd(P) < dd(B1)
    p1 = p1b0 and p1_pnl and p1_dd
    bar("P1", "PASS" if p1 else "FAIL",
        policy_net=net(P), b1_net=net(B1),
        policy_dd=dd(P), b1_dd=dd(B1),
        pnl_leg=p1_pnl, dd_leg=p1_dd,
        close_code=None if p1 else "POLICY_NO_INCREMENTAL_VALUE",
        sub_tag=None if p1 else ("P1_B1_PNL" if not p1_pnl else
                                 "P1_B1_DD"))
    # P2 ------------------------------------------------------------------
    p2a = net(P) > net(m["B2_EQUAL_WEIGHT"]) and \
        dd(P) < dd(m["B2_EQUAL_WEIGHT"])
    p2b = net(P) > net(m["B3_BEST_SINGLE"]) and \
        dd(P) < dd(m["B3_BEST_SINGLE"])
    bar("P2a", "PASS" if p2a else "FAIL",
        policy_net=net(P), b2_net=net(m["B2_EQUAL_WEIGHT"]),
        policy_dd=dd(P), b2_dd=dd(m["B2_EQUAL_WEIGHT"]))
    bar("P2b", "PASS" if p2b else "FAIL",
        policy_net=net(P), b3_net=net(m["B3_BEST_SINGLE"]),
        policy_dd=dd(P), b3_dd=dd(m["B3_BEST_SINGLE"]))
    bar("P2", "PASS" if (p2a and p2b) else "FAIL")
    # P3 ------------------------------------------------------------------
    seed_objs = [s["objective_test_usd"] for s in b4["per_seed"]]
    obj_p = P["objective_test_usd"]
    n_below = sum(1 for o in seed_objs if obj_p > o)
    clause1 = n_below >= 0.95 * b4["n_seeds"]
    med_n = b4["median_net_pnl_usd"]
    med_d = b4["median_max_dd_usd"]
    clause2 = net(P) > med_n and dd(P) < med_d
    bar("P3-clause-1", "PASS" if clause1 else "FAIL",
        obj_policy=obj_p, seeds_below=n_below, seeds=b4["n_seeds"],
        threshold=0.95 * b4["n_seeds"])
    bar("P3-clause-2", "PASS" if clause2 else "FAIL",
        policy_net=net(P), median_seed_net=med_n,
        policy_dd=dd(P), median_seed_dd=med_d)
    bar("P3", "PASS" if (clause1 and clause2) else "FAIL",
        close_code=None if (clause1 and clause2)
        else "POLICY_NO_INCREMENTAL_VALUE",
        sub_tag=None if (clause1 and clause2) else "P3_B4_RANDOM")
    # P4 ------------------------------------------------------------------
    for bar_id, arm, tag in (("P4a", "B5_CLOCK_GATE", "P4_B5_CLOCK"),
                             ("P4b", "B6_INVERTED", "P4_B6_INVERTED"),
                             ("P4c", "B7_LAGGED", "P4_B7_LAGGED")):
        ok = net(P) > net(m[arm]) and dd(P) < dd(m[arm])
        bar(bar_id, "PASS" if ok else "FAIL",
            policy_net=net(P), baseline_net=net(m[arm]),
            policy_dd=dd(P), baseline_dd=dd(m[arm]))
    p4 = all(bars[f"P4{x}"]["status"] == "PASS" for x in "abc")
    bar("P4", "PASS" if p4 else "FAIL")
    # P5 ------------------------------------------------------------------
    sr0 = sr0_inputs or sr0_from_ledger()
    rets = [P["weekly_equity"][d] for d in
            sorted(P["weekly_equity"])]
    rets = [rets[i] - rets[i - 1] for i in range(1, len(rets))]
    d_neff = dsr(rets, sr0["sr0"])
    d_rawn = dsr(rets, sr0["sr0_raw_n"])
    p5a = d_neff["dsr"] > 0.95
    bar("P5a", "PASS" if p5a else "FAIL",
        dsr=d_neff["dsr"], threshold=0.95, sr_hat=d_neff["sr_hat"],
        sr0=sr0["sr0"], n=sr0["n"], n_eff=sr0["n_eff"],
        v=sr0["v_trial_sharpes"], psr=d_neff["psr"],
        dsr_raw_n=d_rawn["dsr"], sr0_raw_n=sr0["sr0_raw_n"],
        close_code=None if p5a else "POLICY_DEFLATION_FAIL")
    pbo = cscv_pbo()
    p5b = pbo["pbo"] <= 0.5
    bar("P5b", "PASS" if p5b else "FAIL", pbo=pbo["pbo"],
        threshold=0.5, n_trials=pbo["n_trials"],
        n_combinations=pbo["n_combinations"],
        close_code=None if p5b else "POLICY_OVERFIT_SUSPECT")
    bar("P5", "PASS" if (p5a and p5b) else "FAIL")
    # P6 ------------------------------------------------------------------
    p6a = net(m["POLICY_X15"]) > net(m["B1_X15"]) and \
        dd(m["POLICY_X15"]) < dd(m["B1_X15"])
    bar("P6a", "PASS" if p6a else "FAIL",
        policy_x15_net=net(m["POLICY_X15"]), b1_x15_net=net(m["B1_X15"]),
        policy_x15_dd=dd(m["POLICY_X15"]), b1_x15_dd=dd(m["B1_X15"]),
        close_code=None if p6a else "POLICY_COST_DOMINATED",
        sub_tag=None if p6a else "P6A_STRESS_1_5")
    bar("P6b", "REPORTING",
        delta_pnl_x20=_r6(net(m["POLICY_X20"]) - net(m["B1_X20"])),
        delta_dd_x20=_r6(dd(m["B1_X20"]) - dd(m["POLICY_X20"])),
        policy_x20_net=net(m["POLICY_X20"]), b1_x20_net=net(m["B1_X20"]))
    p6c_label = net(m["POLICY_X20"]) < 0
    bar("P6c", "LABEL_ATTACHED" if p6c_label else "NO_LABEL",
        policy_x20_net=net(m["POLICY_X20"]),
        label="POLICY_COST_DOMINATED" if p6c_label else None)
    p6d = net(m["POLICY_P90"]) > net(m["B1_P90"]) and \
        dd(m["POLICY_P90"]) < dd(m["B1_P90"])
    bar("P6d", "PASS" if p6d else "FAIL",
        policy_p90_net=net(m["POLICY_P90"]), b1_p90_net=net(m["B1_P90"]),
        policy_p90_dd=dd(m["POLICY_P90"]), b1_p90_dd=dd(m["B1_P90"]),
        close_code=None if p6d else "POLICY_COST_DOMINATED",
        sub_tag=None if p6d else "P6D_SWITCH_P90")
    bar("P6", "PASS" if (p6a and p6d) else "FAIL")
    # P7 ------------------------------------------------------------------
    if net(P) <= 0:
        bar("P7", "NOT_RUN", reason="NOT_RUN_P7_NO_POSITIVE_PNL")
    else:
        pnl_ok, dd_ok = True, True
        offenders = []
        dur = [1.0] * len(folds)            # equal folds (26w each)
        dur_share = [d / sum(dur) for d in dur]
        for pf in P["per_fold"]:
            f = pf["fold_id"]
            if pf["net_pnl_usd"] > 0.50 * net(P):
                pnl_ok = False
                offenders.append({"fold": f, "kind": "P7_PNL_SHARE",
                                  "share": _r6(pf["net_pnl_usd"] / net(P))})
            if pf["max_dd_usd"] > 2.0 * dd(P) * dur_share[f]:
                dd_ok = False
                offenders.append({"fold": f, "kind": "P7_DD_SHARE",
                                  "ratio": _r6(pf["max_dd_usd"] /
                                               (dd(P) * dur_share[f]))})
        p7 = pnl_ok and dd_ok
        bar("P7", "PASS" if p7 else "FAIL", offenders=offenders,
            per_fold=[{"fold": pf["fold_id"],
                       "net": pf["net_pnl_usd"],
                       "share_of_pooled": _r6(pf["net_pnl_usd"] / net(P)),
                       "dd_f": pf["max_dd_usd"],
                       "dd_cap": _r6(2.0 * dd(P) * dur_share[pf["fold_id"]])}
                      for pf in P["per_fold"]],
            close_code=None if p7 else "POLICY_FOLD_CONCENTRATION")
    # P8 ------------------------------------------------------------------
    breaks = []
    for lid in [leg["leg_id"] for leg in pol["slate"]]:
        pm = m[f"POLICY_MO_{lid}"]
        bm = m[f"B1_MO_{lid}"]
        ok = net(pm) > net(bm) and dd(pm) < dd(bm)
        if not ok:
            breaks.append({"leg": lid,
                           "p_net": net(pm), "b_net": net(bm),
                           "p_dd": dd(pm), "b_dd": dd(bm)})
    if len(breaks) == 0:
        p8, code = "PASS", None
    elif len(breaks) == 1:
        p8, code = "FAIL", "POLICY_ONE_LEG_CARRIER"
    else:
        p8, code = "FAIL", "POLICY_NO_INCREMENTAL_VALUE"
    bar("P8", p8, breaks=breaks, close_code=code,
        sub_tag=None if len(breaks) <= 1 else "P8_COALITION")
    # verdict per plan 7 (E-Law 7: every governing bar must PASS)
    governing = [b for b in ("P1-B0", "P1", "P2", "P3", "P4", "P5",
                             "P6", "P7", "P8")]
    failed = [b for b in governing if bars[b]["status"] == "FAIL"]
    if not failed:
        verdict = "PASS_ALL_BARS"
    elif "P1-B0" in failed or "P1" in failed:
        verdict = "POLICY_NO_INCREMENTAL_VALUE"    # P1 is PRIMARY (E-Law 7)
    elif len(breaks) == 1 and "P8" in failed:
        verdict = "POLICY_ONE_LEG_CARRIER"
    elif "P5a" in failed:
        verdict = "POLICY_DEFLATION_FAIL"
    elif "P5b" in failed:
        verdict = "POLICY_OVERFIT_SUSPECT"
    elif "P6a" in failed or "P6d" in failed:
        verdict = "POLICY_COST_DOMINATED"
    else:
        verdict = "POLICY_NO_INCREMENTAL_VALUE"
    out = {
        "schema": "pc12a_stagec_bars@1", "label": LABEL,
        "frozen_utc": _now(),
        "policy_digest": pol["policy_digest"],
        "sr0_inputs": sr0, "bars": bars, "verdict": verdict,
        "failed_governing_bars": failed,
        "p6c_label_attached": p6c_label,
        "b0": {k: b0[k] for k in ("net_pnl_pooled_usd",
                                  "max_dd_pooled_usd")},
        "b8_reporting": {"policy_net": net(P),
                         "oracle_net": net(m["B8_ORACLE"]),
                         "policy_dd": dd(P),
                         "oracle_dd": dd(m["B8_ORACLE"])}}
    _dump(os.path.join(STAGEC_DIR, "BARS.json"), out)
    print(json.dumps({"mode": "bars", "verdict": verdict,
                      "failed": failed}))
    return out


# ---------------------------------------------------------------------------
# 11. Ledger (C-SCORED rows) + budget accounting
# ---------------------------------------------------------------------------


def append_stagec_rows(bars: Dict, ledger_path: str = LEDGER_PATH,
                       stop_at: int = LEDGER_STOP_LINE) -> Dict:
    pol = _policy()
    folds = cal.fold_calendar()
    test_window = [folds[0].test_start.isoformat(),
                   folds[-1].test_end.isoformat()]
    rows: List[Dict] = []
    have = rd._ledger_len(ledger_path)
    now = _now()
    identity_names: List[str] = []

    def _row(base: Dict) -> Dict:
        out = dict(base)
        out["row_id"] = f"CSCD-W1-{have + 1 + len(rows):04d}"
        out.setdefault("cycle_id", CYCLE)
        out.setdefault("stage", "C-SCORED")
        out.setdefault("fold_scope", "TEST_ONLY")
        out.setdefault("label", LABEL)
        out.setdefault("sleeve_id", "PORTFOLIO_POLICY")
        out.setdefault("cluster_id", "portfolio")
        out.setdefault("fold_id", 7)
        out.setdefault("test_window", test_window)
        out.setdefault("tier", 1.0)
        out.setdefault("outcome_exposed_label", "SCORED_TEST")
        out["recorded_utc"] = now
        return out

    def _arm_row(name: str, result: str, detail: str,
                 tier: float = 1.0) -> Dict:
        m_ = _load_metrics(name)
        identity_names.append(name)
        return _row({
            "corpus_gid": f"C-{name}", "pass_tag": name,
            "arm_config_digest": m_["arm_config_digest"],
            "result": result, "tier": tier,
            "net_pnl_usd": m_["net_pnl_pooled_usd"],
            "max_dd_usd": m_["max_dd_pooled_usd"],
            "n_trades": m_["n_fills_total"],
            "turnover_usd": m_["turnover_usd"],
            "objective_usd": m_.get("objective_test_usd"),
            "detail": detail})

    rows.append(_arm_row(
        "POLICY", "POLICY_SCORED",
        "frozen policy V3 on the 8 pooled TEST folds 2022-01-07.."
        "2025-12-26, tier x1.0, fold-edge force-flat law"))
    rows.append(_row({
        "corpus_gid": "C-B0_FLAT", "pass_tag": "B0_FLAT",
        "arm_config_digest": b0_metrics(pol, folds)["arm_config_digest"],
        "result": "BASELINE_BY_CONSTRUCTION",
        "detail": "B0 FLAT: no orders; netPnL=0 maxDD=0 by construction "
                  "(PASS_BARS_V2 1)"}))
    identity_names.append("B0_FLAT")
    b1 = _load_metrics("B1_ALWAYS_ON")
    rows.append(_row({
        "corpus_gid": "C-B1_ALWAYS_ON", "pass_tag": "B1_ALWAYS_ON",
        "arm_config_digest": b1["arm_config_digest"],
        "result": "BASELINE_SCORED",
        "net_pnl_usd": b1["net_pnl_pooled_usd"],
        "max_dd_usd": b1["max_dd_pooled_usd"],
        "n_trades": b1["n_fills_total"], "turnover_usd": b1["turnover_usd"],
        "detail": "B1 ALWAYS_ON: eligibility pinned ON, L3-L6 identical"}))
    identity_names.append("B1_ALWAYS_ON")
    for name, law in (
            ("B2_EQUAL_WEIGHT",
             "B2 EQUAL_WEIGHT: eligibility ON + equal split of the "
             "policy's realized per-decision total heat target (frozen "
             "schedule), per-leg cap 100k, L4-L6 identical"),
            ("B3_BEST_SINGLE",
             None), ("B5_CLOCK_GATE",
                     "B5 CLOCK-GATE: every k-th decision ON, k=round(1/"
                     "TRAIN duty), phase 0"),
            ("B6_INVERTED",
             "B6 INVERTED: binary complement of the policy eligibility"),
            ("B7_LAGGED",
             "B7 LAGGED: policy eligibility delayed one fold (26w); "
             "first test fold lags the TRAIN timeline"),
            ("B8_ORACLE",
             "B8 ORACLE-legs: perfect next-fold eligibility from B1 "
             "paper fold nets; REPORTING ONLY")):
        m_ = _load_metrics(name)
        if name == "B3_BEST_SINGLE":
            sel = json.load(open(os.path.join(STAGEC_DIR,
                                              "B3_SELECTION.json"),
                                 encoding="utf-8"))
            law = (f"B3 BEST_SINGLE: leg {sel['selected_leg']} alone "
                   f"through L2-L6; obj_B3 = DSR_T of TRAIN x2.0 weekly "
                   f"returns ({sel['candidates'][0]['obj_b3_dsr']}); "
                   f"TRAIN-only selection frozen before any test run "
                   f"(tie_break_fired={sel['tie_break_fired']})")
        rows.append(_row({
            "corpus_gid": f"C-{name}", "pass_tag": name,
            "arm_config_digest": m_["arm_config_digest"],
            "result": "BASELINE_SCORED" if name != "B8_ORACLE"
            else "REPORTING_ONLY",
            "net_pnl_usd": m_["net_pnl_pooled_usd"],
            "max_dd_usd": m_["max_dd_pooled_usd"],
            "n_trades": m_["n_fills_total"],
            "turnover_usd": m_["turnover_usd"],
            "detail": law}))
        identity_names.append(name)
    for name, tag in (("POLICY_X15", "P6a policy @ x1.5"),
                      ("B1_X15", "P6a B1 @ x1.5"),
                      ("POLICY_X20", "P6b/P6c policy @ x2.0"),
                      ("B1_X20", "P6b B1 @ x2.0"),
                      ("POLICY_P90", "P6d policy @ switch-p90"),
                      ("B1_P90", "P6d B1 @ switch-p90")):
        m_ = _load_metrics(name)
        rows.append(_row({
            "corpus_gid": f"C-{name}", "pass_tag": name,
            "arm_config_digest": m_["arm_config_digest"],
            "result": "ROBUSTNESS_SCORED",
            "tier": m_["tier"],
            "net_pnl_usd": m_["net_pnl_pooled_usd"],
            "max_dd_usd": m_["max_dd_pooled_usd"],
            "n_trades": m_["n_fills_total"],
            "turnover_usd": m_["turnover_usd"],
            "detail": tag}))
        identity_names.append(name)
    for leg in pol["slate"]:
        lid = leg["leg_id"]
        for name in (f"POLICY_MO_{lid}", f"B1_MO_{lid}"):
            m_ = _load_metrics(name)
            rows.append(_row({
                "corpus_gid": f"C-{name}", "pass_tag": name,
                "arm_config_digest": m_["arm_config_digest"],
                "result": "ROBUSTNESS_SCORED",
                "net_pnl_usd": m_["net_pnl_pooled_usd"],
                "max_dd_usd": m_["max_dd_pooled_usd"],
                "n_trades": m_["n_fills_total"],
                "turnover_usd": m_["turnover_usd"],
                "detail": f"P8 leave-one-leg ({'policy' if name.startswith('POLICY') else 'B1'} -{lid})"}))
            identity_names.append(name)
    b4 = json.load(open(os.path.join(STAGEC_DIR, "B4_BATTERY.json"),
                        encoding="utf-8"))
    b4_spec = _arm("B4_RANDOM_GATE", elig="markov")
    rows.append(_row({
        "corpus_gid": "C-B4_RANDOM_GATE", "pass_tag": "B4_RANDOM_GATE",
        "arm_config_digest": arm_config_digest(
            b4_spec, pol["policy_digest"],
            extra=f"seeds={b4['seed_list_digest']}"),
        "result": "BASELINE_BATTERY_SCORED",
        "net_pnl_usd": b4["median_net_pnl_usd"],
        "max_dd_usd": b4["median_max_dd_usd"],
        "detail": (f"B4 battery: ONE identity, {b4['n_seeds']} seeded "
                   f"sub-runs (duty+turnover-matched; seed list digest "
                   f"{b4['seed_list_digest']}); median net "
                   f"{b4['median_net_pnl_usd']} USD, median DD "
                   f"{b4['median_max_dd_usd']} USD; sub-runs disclosed on "
                   f"their own budget line (E-Law 8)")}))
    identity_names.append("B4_RANDOM_GATE")
    rows.append(_row({
        "corpus_gid": "C-VERDICT", "pass_tag": "BARS_VERDICT",
        "arm_config_digest": pol["policy_digest"],
        "result": bars["verdict"],
        "detail": ("typed provisional verdict per plan 7; failed "
                   "governing bars: "
                   + str(bars["failed_governing_bars"] or "none")
                   + "; P6c label attached: "
                   + str(bars["p6c_label_attached"]))}))
    n_ids = len(identity_names)
    if n_ids > IDENTITY_CAP:
        raise RuntimeError(f"identity budget overflow: {n_ids} > "
                           f"{IDENTITY_CAP} (STOP-2 law)")
    if have + len(rows) > stop_at:
        raise rd.LedgerBudgetExceeded(
            f"append of {len(rows)} would take the ledger from {have} "
            f"past stop line {stop_at}")
    with open(ledger_path, "a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return {"rows_appended": len(rows), "ledger_total": have + len(rows),
            "identities": n_ids, "identity_names": identity_names}


# ---------------------------------------------------------------------------
# 12. CLI + orchestration (heavy lock held end-to-end)
# ---------------------------------------------------------------------------


def _take_lock(command: List[str]):
    gov = os.path.join(ROOT_CHECKOUT, "research")
    if gov not in sys.path:
        sys.path.insert(0, gov)
    from governance import heavy_lock
    return heavy_lock.acquire(
        cycle_id=CYCLE, role="stage-c-scored-evaluation",
        worktree=WORKTREE, command=command,
        expected_artifacts=[
            "research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/"
            "diagnostics/stagec/BARS.json"])


PY = [os.path.join(ROOT_CHECKOUT, ".venv", "bin", "python"), "-m",
      "research.pc12a.run_scoredc"]


def _spawn(cmd: List[str], log_path: str) -> subprocess.Popen:
    log = open(log_path, "a", encoding="utf-8")
    log.write(f"\n=== {' '.join(cmd)} @{_now()}\n")
    log.flush()
    return subprocess.Popen(cmd, stdout=log, stderr=log, cwd=WORKTREE)


def _run_sync(cmd: List[str], log_path: str) -> int:
    return _spawn(cmd, log_path).wait()


def _fanout(cmds: List[List[str]], log_dir: str, parallel: int) -> None:
    running: Dict[str, subprocess.Popen] = {}
    queue = list(cmds)
    codes: Dict[str, int] = {}
    while queue or running:
        while queue and len(running) < parallel:
            cmd = queue.pop(0)
            tag = cmd[cmd.index("--arm") + 1] if "--arm" in cmd else \
                f"job{len(codes) + len(running)}"
            running[tag] = _spawn(cmd, os.path.join(
                log_dir, f"{tag}.log"))
        time.sleep(5)
        for tag in list(running):
            rc = running[tag].poll()
            if rc is not None:
                codes[tag] = rc
                del running[tag]
    failed = {t: c for t, c in codes.items() if c != 0}
    if failed:
        raise RuntimeError(f"fanout failures: {failed}")


def mode_orchestrate(parallel: int = 6) -> None:
    os.makedirs(STAGEC_DIR, exist_ok=True)
    log = os.path.join(STAGEC_DIR, "ORCHESTRATOR_LOG.txt")
    lock = _take_lock(PY + ["--mode", "orchestrate"])
    t0 = time.time()
    try:
        # phase 0-2: verify, B3 freeze (pre-test), TRAIN extract
        for step in (["--mode", "verify"], ["--mode", "b3select"],
                     ["--mode", "trainextract"]):
            marker = {"verify": "VERIFY.json", "b3select":
                      "B3_SELECTION.json", "trainextract":
                      "TRAIN_EXTRACT.json"}[step[1]]
            if os.path.exists(os.path.join(STAGEC_DIR, marker)):
                continue
            rc = _run_sync(PY + step, log)
            if rc != 0:
                raise RuntimeError(f"step {step} failed rc={rc}")
        # phase 3: POLICY (serial; schedules input) + repro determinism
        if not os.path.exists(os.path.join(_arm_output_dir("POLICY"),
                                           "metrics.json")):
            rc = _run_sync(PY + ["--mode", "arm", "--arm", "POLICY"],
                           log)
            if rc != 0:
                raise RuntimeError("POLICY failed rc={rc}")
        if not os.path.exists(os.path.join(STAGEC_DIR,
                                           "REPRO_CHECK.json")):
            rc = _run_sync(PY + ["--mode", "repro"], log)
            if rc != 0:
                raise RuntimeError("repro failed rc={rc}")
        # phase 4: B1 (serial; B8 paper input) then schedules
        if not os.path.exists(os.path.join(_arm_output_dir("B1_ALWAYS_ON"),
                                           "metrics.json")):
            rc = _run_sync(PY + ["--mode", "arm", "--arm",
                                 "B1_ALWAYS_ON"], log)
            if rc != 0:
                raise RuntimeError("B1 failed rc={rc}")
        rc = _run_sync(PY + ["--mode", "schedules"], log)
        if rc != 0:
            raise RuntimeError("schedules failed rc={rc}")
        # phase 5: all remaining arms in parallel
        pol = load_policy()
        survivors = [leg["leg_id"] for leg in pol["slate"]]
        remaining = [a for a in build_arm_specs(survivors)
                     if a["arm"] not in ("POLICY", "B1_ALWAYS_ON")
                     and not os.path.exists(os.path.join(
                         _arm_output_dir(a["arm"]), "metrics.json"))]
        cmds = [PY + ["--mode", "arm", "--arm", a["arm"]]
                for a in remaining]
        _fanout(cmds, STAGEC_DIR, parallel)
        # phase 6: B4 battery (its own parallelism)
        rc = _run_sync(PY + ["--mode", "b4", "--parallel",
                             str(parallel)], log)
        if rc != 0:
            raise RuntimeError(f"b4 failed rc={rc}")
        # phase 7: bars + ledger + report
        for step in (["--mode", "bars"], ["--mode", "ledger"],
                     ["--mode", "report"]):
            rc = _run_sync(PY + step, log)
            if rc != 0:
                raise RuntimeError(f"step {step} failed rc={rc}")
        print(json.dumps({"mode": "orchestrate", "done": True,
                          "elapsed": round(time.time() - t0, 1)}))
    except BaseException:
        if lock is not None:
            lock.release(status="FAILED", note="stage-c orchestrate")
            lock = None
        raise
    finally:
        if lock is not None:
            lock.release(status="FINISHED", note="stage-c orchestrate")


def mode_verify() -> Dict:
    pol = load_policy()
    folds = cal.fold_calendar()
    inputs = policy_engine_inputs(pol)
    out = {
        "schema": "pc12a_stagec_verify@1", "frozen_utc": _now(),
        "policy_digest": pol["policy_digest"], "digest_match": True,
        "winner": pol["variant_id"],
        "window": [folds[0].test_start.isoformat(),
                   folds[-1].test_end.isoformat()],
        "sealed_tail": [cal.sealed_tail()[0].isoformat(),
                        cal.sealed_tail()[1].isoformat()],
        "survivors": len(inputs["survivors"]),
        "guard_cap_usd": inputs["guard_cap_usd"],
        "ledger_rows": rd._ledger_len(LEDGER_PATH),
        "identities_used_before_stage_c": 0,
        "arm_specs": len(build_arm_specs(inputs["survivors"]))}
    _dump(os.path.join(STAGEC_DIR, "VERIFY.json"), out)
    print(json.dumps({"mode": "verify", "digest_match": True,
                      "window": out["window"], "arms": out["arm_specs"]}))
    return out


def mode_repro() -> Dict:
    """Determinism check: re-run the POLICY arm into a REPRO dir; the
    journal and metrics must be byte-identical (documented determinism
    re-run; same identity, deduped per PASS_BARS F-11)."""
    pol = load_policy()
    repro_dir = os.path.join(STAGEC_DIR, "REPRO")
    metrics_path = os.path.join(repro_dir, "metrics.json")
    if os.path.exists(metrics_path):
        os.remove(metrics_path)
    if os.path.exists(os.path.join(repro_dir, "journal.jsonl")):
        os.remove(os.path.join(repro_dir, "journal.jsonl"))
    spec = _arm("POLICY")
    run_arm(spec, out_dir=repro_dir)
    a = open(os.path.join(_arm_output_dir("POLICY"), "journal.jsonl"),
             "rb").read()
    b = open(os.path.join(repro_dir, "journal.jsonl"), "rb").read()
    ma = open(os.path.join(_arm_output_dir("POLICY"), "metrics.json"),
              "rb").read()
    mb = open(metrics_path, "rb").read()
    out = {"journal_byte_identical": a == b,
           "metrics_byte_identical": ma == mb}
    _dump(os.path.join(STAGEC_DIR, "REPRO_CHECK.json"), out)
    print(json.dumps({"mode": "repro", **out}))
    if not (out["journal_byte_identical"]
            and out["metrics_byte_identical"]):
        raise RuntimeError("POLICY determinism check FAILED (STOP-3)")
    return out


def mode_ledger() -> Dict:
    bars = json.load(open(os.path.join(STAGEC_DIR, "BARS.json"),
                          encoding="utf-8"))
    out = append_stagec_rows(bars)
    print(json.dumps({"mode": "ledger", **{k: v for k, v in
                                           out.items()}}))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="PC12A Stage-C scored eval")
    ap.add_argument("--mode", required=True,
                    choices=["verify", "b3select", "trainextract", "arm",
                             "schedules", "b4", "bars", "ledger",
                             "report", "repro", "orchestrate"])
    ap.add_argument("--arm", default=None)
    ap.add_argument("--parallel", type=int, default=6)
    args = ap.parse_args(argv)
    if args.mode == "verify":
        mode_verify()
    elif args.mode == "b3select":
        mode_b3select()
    elif args.mode == "trainextract":
        mode_trainextract()
    elif args.mode == "arm":
        pol = load_policy()
        survivors = [leg["leg_id"] for leg in pol["slate"]]
        spec = next(a for a in build_arm_specs(survivors)
                    if a["arm"] == args.arm)
        run_arm(spec)
        print(json.dumps({"mode": "arm", "arm": args.arm, "done": True}))
    elif args.mode == "schedules":
        mode_schedules()
    elif args.mode == "b4":
        mode_b4(parallel=args.parallel)
    elif args.mode == "bars":
        evaluate_bars()
    elif args.mode == "ledger":
        mode_ledger()
    elif args.mode == "repro":
        mode_repro()
    elif args.mode == "report":
        from . import stagec_report
        stagec_report.write_report()
    elif args.mode == "orchestrate":
        mode_orchestrate(parallel=args.parallel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
