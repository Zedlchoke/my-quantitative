"""COMMODITIES-NG1 D2 novelty measurement (P-12 two-commit law).

Task: commodities-ng1-d2-novelty (cycle COMMODITIES-NG1).

P-12 ORDER (this task)
----------------------
Commit-1 (BEFORE any rho exists): THIS file + feasibility_renote.json +
tests/test_commodities_ng1_d2.py -- measurement code, shadow-reconstruction
definitions, representation mapping, frozen default parameters.  NO measured
correlation value may appear in any commit-1 file (the only rho-family number
allowed is the DECLARED ceiling, which comes from the dispatch packet, not
from measurement).

Commit-2 (AFTER the run): d2_novelty_panel.json -- per-proposal x per-shadow
Spearman and Pearson decision-state correlations, pooled max, margin to the
0.20 ceiling, verdict ELIGIBLE / VETO / VETO_PENDING_UNMEASURABLE.

WHAT IS MEASURED (and what is not)
----------------------------------
Decision-STATE series correlation ONLY.  A decision state is the position a
rule family holds at a decision instant, in {-1, 0, +1}.  NO returns, NO PnL,
NO costs charged, NO scored outcomes, no expectancy anywhere in this task.

NOVELTY LAW (dispatch packet commodities-ng1-d2-novelty)
--------------------------------------------------------
For each of the 4 D1 proposals
(research/control/commodities_ng1_run/d1/proposals/*.json), reconstruct the
ancestry kill-shadows ON THE PROPOSAL'S OWN DECLARED REPRESENTATION (the
weekly CoT-release decision grid from the committed P2 census) and measure
decision-state correlation:

  (a) momentum_63s            -- trailing 63-session momentum sign on the
                                  ETP legs, weekly-decimated to the proposal
                                  grid;
  (b) generic_dow_tue         -- calendar-clock positions from
                                  release-weekday geometry;
  (c) v16_close_displace_fade -- short-horizon close-displacement reversal
                                  on the ETP legs;
  (d) PRICE_ONLY_SHADOW       -- the proposal's OWN tradeable rule family
                                  driven by price features alone (no
                                  positioning input); the plan section 1
                                  mandatory control, measured here as a
                                  veto.

Per shadow: Spearman AND Pearson vs the proposal's own decision-state
series (parameters FROZEN below, before any rho).  Pooled per shadow =
max(|spearman|, |pearson|) on the pooled (stacked across the 11 bookable
pairs, pairwise-complete) observation set.  Proposal pooled = max over
shadows.  pooled |rho| <= 0.20 = ELIGIBLE, else VETO.  Margin to 0.20
recorded per P-2.

FAIL-CLOSED (never-PASS-by-absence): a shadow that cannot be measured (fewer
than 2 pairwise-complete observations, or a zero-variance state series) is
UNMEASURABLE and forces verdict VETO_PENDING_UNMEASURABLE unless provably
inapplicable (documented in the panel).  Absence of evidence is never
evidence of absence.

REPRESENTATION MAPPING (identical for all 4 proposals; they declare the
same grid and the same 11-pair bookable set)
------------------------------------------------------------------------
- Pair universe: the 11 fully-costed bookable pairs declared by every
  proposal (the 9 transaction-only expense-fail-closed legs are excluded
  exactly as declared at D1; see feasibility_renote.json).
- Grid: per pair, the P2 counted window -- every measured weekly CoT
  report with release date >= 2018-01-01 minus the first 52 warmup
  instants, restricted to instants whose decision session exists (401 per
  pair).  The grid is re-derived here from the committed P2 code
  (research/assets/commodities_ng1/feasibility.py::census_pair_grid
  semantics) and asserted IDENTICAL to the p2_gate.json per_pair_census,
  fail-closed.
- Decision session: first MEASURED ETP session strictly after the release
  date (clock.next_session_after, imported, never re-derived).  Decision
  instant: that session's EOD close.
- CoT-side facts: reports visible at a decision instant are exactly the
  reports released at or before that grid row's release instant (PIT
  guard; the P0 release rule is imported via
  feasibility.release_instant_for_report, never re-derived).  State
  history chains run over the FULL measured substrate from 2016 (warmup
  for the trailing windows); the MEASURED set is only the P2 counted
  window.
- Price-side facts: RAW ETP closes (unadjusted; RAW is the declared
  decision surface).  The declared D1 convention (stricter than the
  kernel maximum): a price fact at a decision instant reads only bars
  whose close instant is STRICTLY BEFORE the decision instant, i.e.
  sessions strictly before the decision session; the freshest readable
  bar is the previous session.
- Sign conventions of the anchor families are frozen and documented below;
  pooled |rho| is invariant to a global flip of either series' sign, so
  the verdicts do not depend on the frozen sign choices.

PARAMETER FREEZE LAW
--------------------
Every family parameter below is the declared NEUTRAL/MEDIAN default,
frozen in this commit BEFORE any rho was computed, never moved afterwards
(P-12/P-2).  Rationales are attached to each parameter.
"""

from __future__ import annotations

import bisect
import csv
import hashlib
import json
import math
import os
import sys
from datetime import date, datetime, timezone

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from research.assets.commodities_ng1.clock import (  # noqa: E402
    ClockRefused,
    next_session_after,
)
from research.assets.commodities_ng1.feasibility import (  # noqa: E402
    WINDOW_START,
    WARMUP_WEEKS,
    release_instant_for_report,
)

SCHEMA = "commodities_ng1_run/d2_novelty@1"
SCHEMA_PANEL = "commodities_ng1_run/d2_novelty_panel@1"

RUN_DIR = os.path.join(_REPO_ROOT, "research", "control", "commodities_ng1_run")
D2_DIR = os.path.join(RUN_DIR, "d2")
P2_GATE_PATH = os.path.join(RUN_DIR, "p2_gate.json")
COT_CSV_PATH = os.path.join(RUN_DIR, "p0_cot_weekly_targets.csv")
PROPOSALS_DIR = os.path.join(RUN_DIR, "d1", "proposals")
ETP_DIR = os.path.join(RUN_DIR, "etp_eod")

BASE_SHA = "5cb5a010d1086bd9e672e5c2616360bf81ae21b0"
BRANCH = "orca/commodities-ng1-integration"
CYCLE_ID = "COMMODITIES-NG1"
TASK_ID = "commodities-ng1-d2-novelty"

#: The commit-1 file set (the negative "no rho numbers" law is enforced on
#: exactly these paths; the panel and handoff are commit-2 artifacts).
COMMIT1_FILES = (
    "research/control/commodities_ng1_run/d2/measure_novelty.py",
    "research/control/commodities_ng1_run/d2/feasibility_renote.json",
)

PROPOSAL_IDS = (
    "COMMNG1-A4-P1",
    "COMMNG1-A4-P2",
    "COMMNG1-A5-P1",
    "COMMNG1-A5-P2",
)

SHADOW_IDS = (
    "momentum_63s",
    "generic_dow_tue",
    "v16_close_displace_fade",
    "price_only_shadow",
)

VERDICT_ELIGIBLE = "ELIGIBLE"
VERDICT_VETO = "VETO"
VERDICT_VETO_PENDING = "VETO_PENDING_UNMEASURABLE"


class D2Refused(Exception):
    """Fail-closed D2 refusal (bad inputs, identity violations,
    insufficient data).  Never improvise, never drop silently."""


# ----------------------------------------------------------------------- #
# FROZEN PARAMETERS (commit-1; frozen BEFORE any rho; never moved)
# ----------------------------------------------------------------------- #

FROZEN_PARAMETERS = {
    "novelty_ceiling_abs_rho": {
        "value": 0.20,
        "rationale": "dispatch packet commodities-ng1-d2-novelty (P-2 "
                     "margin law; plan section 6 rubric); DECLARED, not "
                     "measured",
    },
    "percentile_window_weeks": {
        "value": 104,
        "rationale": "median of the standard weekly percentile-window "
                     "conventions {52, 104, 156} (1y/2y/3y); the rolling "
                     "window INCLUDES the current observation",
    },
    "tail_cut": {
        "value": 0.10,
        "rationale": "symmetric tails q_lo=0.10 / q_hi=0.90: median of the "
                     "common {0.05, 0.10, 0.20} tail conventions",
    },
    "holding_weeks_a4_reversal": {
        "value": 4,
        "rationale": "median of the common weekly holding conventions "
                     "{1, 2, 4, 8, 13} decision sessions",
    },
    "carry_bound_weeks_a4p2": {
        "value": 13,
        "rationale": "one quarter (13 weekly decision sessions): the "
                     "standard bound convention for a continuation family",
    },
    "trigger_tau_geometry": {
        "value": 0.02,
        "rationale": "weekly positioning flow of 2% of open interest "
                     "opposing the held side: a conventional non-trivial "
                     "weekly flow on the OI-normalized geometry scale",
    },
    "accel_window_weeks_a5p2": {
        "value": 4,
        "rationale": "median of the common acceleration windows {2, 4, 8} "
                     "weekly reports",
    },
    "holding_weeks_a5p2": {
        "value": 4,
        "rationale": "same median holding convention as lane A4",
    },
    "momentum_sessions": {
        "value": 63,
        "rationale": "the named shadow's own canonical definition "
                     "(momentum_63s): 63 trading sessions",
    },
    "v16_displace_sessions": {
        "value": 5,
        "rationale": "one trading week of sessions: the v16-class "
                     "short-horizon close displacement",
    },
    "tau_price_weekly_a4p2": {
        "value": 0.02,
        "rationale": "price analogue of the positioning trigger: opposing "
                     "1-week RAW displacement of 2%",
    },
}


def P(key):
    """Frozen parameter accessor (values only; no override path)."""
    return FROZEN_PARAMETERS[key]["value"]


# ----------------------------------------------------------------------- #
# Correlation core (hand-rolled; unit-tested against hand-computed values)
# ----------------------------------------------------------------------- #

def pearson(x, y):
    """Pearson correlation; None when either series has zero variance."""
    n = len(x)
    if n != len(y) or n == 0:
        raise D2Refused("pearson on mismatched/empty series")
    mx = math.fsum(x) / n
    my = math.fsum(y) / n
    sxy = math.fsum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = math.fsum((a - mx) ** 2 for a in x)
    syy = math.fsum((b - my) ** 2 for b in y)
    if sxx == 0.0 or syy == 0.0:
        return None
    return sxy / math.sqrt(sxx * syy)


def average_ranks(v):
    """Ranks 1..n with average ranks assigned to ties."""
    order = sorted(range(len(v)), key=lambda i: v[i])
    ranks = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(x, y):
    """Spearman correlation (Pearson on average ranks); None when the
    rank series is degenerate (zero variance)."""
    return pearson(average_ranks(x), average_ranks(y))


def correlation_pair(x, y):
    """(spearman, pearson); both None (UNMEASURABLE row) when fewer than 2
    observations or either series has zero variance."""
    if len(x) != len(y) or len(x) < 2:
        return None, None
    sp = spearman(x, y)
    pe = pearson(x, y)
    if sp is None or pe is None:
        return None, None
    return sp, pe


# ----------------------------------------------------------------------- #
# Small numeric helpers
# ----------------------------------------------------------------------- #

def sign(v):
    if v > 0:
        return 1.0
    if v < 0:
        return -1.0
    return 0.0


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def percentile_tail(values, i, window, cut):
    """Symmetric tail bucket of values[i] inside the trailing `window`
    observations ENDING at i (inclusive), by percentile rank:
    rank = (# window values <= x) / n.
    'lo' when rank <= cut; 'hi' when rank >= 1-cut; else None.
    Requires the full window.  (A unique window minimum has rank ~1/n ->
    'lo'; a unique maximum has rank 1.0 -> 'hi'; a tie cluster can satisfy
    both only when cut >= 0.5, refused as degenerate.)"""
    if i + 1 < window:
        return None
    w = values[i - window + 1:i + 1]
    x = values[i]
    n = len(w)
    rank = sum(1 for v in w if v <= x) / n
    lo = rank <= cut
    hi = rank >= (1.0 - cut)
    if lo and hi:
        return None
    if lo:
        return "lo"
    if hi:
        return "hi"
    return None


def hold_positions(arm, h):
    """Position held h consecutive instants from each arming; the LATEST
    arming inside the window wins."""
    n = len(arm)
    pos = [0.0] * n
    for i in range(n):
        for j in range(i, max(-1, i - h), -1):
            if arm[j] != 0.0:
                pos[i] = arm[j]
                break
    return pos


def _tail_arm(series, i, w, cut):
    """Arm value from the tail bucket of series[i] (None-safe)."""
    if i < 0 or i >= len(series) or series[i] is None:
        return None
    window_vals = series[i - w + 1:i + 1]
    if len(window_vals) < w or any(v is None for v in window_vals):
        return None
    return percentile_tail(window_vals, w - 1, w, cut)


# ----------------------------------------------------------------------- #
# Data loading (digest-verified; committed surfaces only; NO network)
# ----------------------------------------------------------------------- #

def load_p2_gate():
    with open(P2_GATE_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def load_cot_by_market():
    """contract_market_code -> report rows (structural P0 fields), sorted
    by report_date."""
    by_code = {}
    with open(COT_CSV_PATH, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            by_code.setdefault(row["contract_market_code"], []).append({
                "report_date": date.fromisoformat(row["report_date"]),
                "open_interest": float(row["open_interest"]),
                "noncomm_long": float(row["noncomm_long"]),
                "noncomm_short": float(row["noncomm_short"]),
                "noncomm_spreading": float(row["noncomm_spreading"]),
                "comm_long": float(row["comm_long"]),
                "comm_short": float(row["comm_short"]),
            })
    for code, rows in by_code.items():
        rows.sort(key=lambda r: r["report_date"])
        dates = [r["report_date"] for r in rows]
        if len(set(dates)) != len(dates):
            raise D2Refused(f"duplicate CoT report dates for market {code}")
    return by_code


def load_etp_series(symbol):
    """(session dates, RAW closes) for one ETP leg (RAW primary by law)."""
    path = os.path.join(ETP_DIR, f"{symbol}.csv")
    dates, closes = [], []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            dates.append(date.fromisoformat(row["date"]))
            closes.append(float(row["close"]))
    if len(set(dates)) != len(dates) or dates != sorted(dates):
        raise D2Refused(f"ETP session calendar malformed for {symbol}")
    return dates, closes


def load_proposals():
    proposals = {}
    for pid in PROPOSAL_IDS:
        path = os.path.join(PROPOSALS_DIR, f"{pid}.json")
        with open(path, encoding="utf-8") as fh:
            proposals[pid] = json.load(fh)
    return proposals


def bookable_pairs(proposals):
    """The common declared bookable pair set (fail-closed if the four
    proposals disagree)."""
    sets = {}
    for pid, prop in proposals.items():
        sets[pid] = list(
            prop["feasibility_citation"]["d1_bookable_set_declaration"]
            ["bookable_pairs"])
    ref = sets[PROPOSAL_IDS[0]]
    for pid in PROPOSAL_IDS[1:]:
        if sorted(sets[pid]) != sorted(ref):
            raise D2Refused(
                f"bookable-set disagreement between proposals at {pid}; "
                "fail closed")
    return sorted(ref)


# ----------------------------------------------------------------------- #
# Pair chain: the proposal's own representation, reconstructed + asserted
# ----------------------------------------------------------------------- #

def build_pair_chain(pair_id, cot_by_market, etp_dates, etp_closes):
    """Full weekly chain (2016+) for ONE bookable pair.

    Each row carries: report_date, release instant (P0 rule imported),
    release_date, decision_session (extended to pre-window reports for the
    warmup chains), the A4 geometry g, spec_net, comm_net, the A5-P2
    acceleration coordinate, cend_close (freshest RAW close readable
    strictly before the decision instant) and the counted flag (P2 counted
    window).  PIT law: CoT facts at row i come only from reports released
    at/before row i's release instant (the release-sorted prefix;
    monotonicity asserted fail-closed).
    """
    code, _symbol = pair_id.split("/")
    reports = cot_by_market[code]
    rows = []
    prev_release = None
    for r in reports:
        release, rule_source = release_instant_for_report(r["report_date"])
        if prev_release is not None and release < prev_release:
            raise D2Refused(
                f"release instants not monotone for market {code} at "
                f"{r['report_date'].isoformat()}; PIT prefix law broken")
        prev_release = release
        release_day = release.date()
        try:
            decision_session = next_session_after(release_day, etp_dates)
        except ClockRefused:
            decision_session = None
        g = ((r["noncomm_long"] - r["noncomm_short"])
             - (r["comm_long"] - r["comm_short"])) / r["open_interest"]
        cend_close = None
        if decision_session is not None:
            cut = bisect.bisect_left(etp_dates, decision_session)
            if cut > 0:
                cend_close = etp_closes[cut - 1]
        rows.append({
            "report_date": r["report_date"],
            "release_instant": release,
            "release_date": release_day,
            "rule_source": rule_source,
            "decision_session": decision_session,
            "g": g,
            "spec_net": r["noncomm_long"] - r["noncomm_short"],
            "comm_net": r["comm_long"] - r["comm_short"],
            "open_interest": r["open_interest"],
            "cend_close": cend_close,
        })

    # derived A5-P2 acceleration coordinate (needs 2w reports of history)
    w_acc = int(P("accel_window_weeks_a5p2"))
    for i, row in enumerate(rows):
        row["accel"] = None
        if i >= 2 * w_acc:
            cn = row["comm_net"]
            row["accel"] = (cn - 2.0 * rows[i - w_acc]["comm_net"]
                            + rows[i - 2 * w_acc]["comm_net"]) \
                / row["open_interest"]

    # P2 counted window flag (identity asserted by verify_pair_census)
    counted = [False] * len(rows)
    order = 0
    for i, row in enumerate(rows):
        if row["release_date"] >= WINDOW_START:
            if order >= WARMUP_WEEKS and row["decision_session"] is not None:
                counted[i] = True
            order += 1
    return rows, counted


def verify_pair_census(pair_id, rows, counted, p2_gate):
    """Fail-closed identity: the reconstructed grid MUST equal the
    committed P2 per-pair census.  The counted window is the post-warmup
    window (expected releases, mapped or not); grid-eligible instants are
    its mapped subset (the MEASURED set)."""
    ref = p2_gate["per_pair_census"].get(pair_id)
    if ref is None:
        raise D2Refused(f"pair {pair_id} absent from p2_gate per_pair_census")
    floor_ref = ref["floor_evaluation"]
    window_rows = [i for i, r in enumerate(rows)
                   if r["release_date"] >= WINDOW_START]
    counted_window = window_rows[WARMUP_WEEKS:]
    mapped = [i for i in counted_window
              if rows[i]["decision_session"] is not None]
    unmapped = [rows[i]["release_date"].isoformat()
                for i in counted_window
                if rows[i]["decision_session"] is None]
    if len(counted_window) != floor_ref["counted_expected_releases"]:
        raise D2Refused(
            f"pair {pair_id}: counted-window releases {len(counted_window)} "
            f"!= committed {floor_ref['counted_expected_releases']}")
    if len(mapped) != floor_ref["grid_eligible_instants"]:
        raise D2Refused(
            f"pair {pair_id}: grid-eligible instants {len(mapped)} != "
            f"committed {floor_ref['grid_eligible_instants']}")
    if sum(counted) != len(mapped):
        raise D2Refused(
            f"pair {pair_id}: measured mask {sum(counted)} != mapped "
            f"{len(mapped)}")
    first = rows[mapped[0]]["release_date"].isoformat()
    last = rows[counted_window[-1]]["release_date"].isoformat()
    if first != floor_ref["counted_first_release"] \
            or last != floor_ref["counted_last_release"]:
        raise D2Refused(
            f"pair {pair_id}: counted window [{first}..{last}] != committed "
            f"[{floor_ref['counted_first_release']}.."
            f"{floor_ref['counted_last_release']}]")
    if unmapped != floor_ref["unmapped_release_dates_counted"]:
        raise D2Refused(
            f"pair {pair_id}: unmapped counted releases {unmapped} != "
            f"committed {floor_ref['unmapped_release_dates_counted']}")
    return True


# ----------------------------------------------------------------------- #
# Anchor decision-state series (rule families with FROZEN parameters)
# ----------------------------------------------------------------------- #

def state_a4p1(chain):
    """COMMNG1-A4-P1 anchor: percentile-extreme forced-unwind REVERSAL.

    state(t) = tail bucket of g(r_t) over the frozen trailing window.
    Upper tail (crowded-long geometry) => -1, lower tail => +1 (opposing
    the crowded side; frozen symmetric convention).  Armed direction held
    for `holding_weeks_a4_reversal` grid instants; latest arming wins.
    """
    w = int(P("percentile_window_weeks"))
    cut = P("tail_cut")
    h = int(P("holding_weeks_a4_reversal"))
    g = [r["g"] for r in chain]
    arm = [0.0] * len(chain)
    for i in range(len(chain)):
        b = percentile_tail(g, i, w, cut)
        if b == "hi":
            arm[i] = -1.0
        elif b == "lo":
            arm[i] = +1.0
    return hold_positions(arm, h)


def state_a4p2(chain):
    """COMMNG1-A4-P2 anchor: crowd-carry persistence-until-trigger.

    Entry on a fresh TRANSITION into a tail bucket; direction = sign of
    the speculative net (the crowd side; frozen).  Exit on (a) an opposing
    weekly geometry flow (first difference of g) of magnitude >=
    `trigger_tau_geometry`, (b) leaving the entered tail, or (c) the
    `carry_bound_weeks_a4p2` bound.  Re-arm requires a fresh transition
    into a tail.  ("may flip under the same frozen convention" is frozen
    at NO flip: trigger terminates to flat -- the conservative reading.)
    """
    w = int(P("percentile_window_weeks"))
    cut = P("tail_cut")
    tau = P("trigger_tau_geometry")
    h_max = int(P("carry_bound_weeks_a4p2"))
    g = [r["g"] for r in chain]
    n = len(chain)
    pos = [0.0] * n
    held_d = 0.0
    entered_bucket = None
    entry_i = -1
    prev_bucket = None
    for i in range(n):
        b = percentile_tail(g, i, w, cut)
        if held_d != 0.0:
            f = g[i] - g[i - 1] if i > 0 else 0.0
            trigger = (sign(f) == -held_d) and abs(f) >= tau
            left_tail = (b != entered_bucket)
            bound = (i - entry_i) >= h_max
            if trigger or left_tail or bound:
                held_d = 0.0
            else:
                pos[i] = held_d
        if held_d == 0.0 and b is not None and b != prev_bucket:
            d = sign(chain[i]["spec_net"])
            if d != 0.0:
                held_d = d
                entered_bucket = b
                entry_i = i
                pos[i] = d
        prev_bucket = b
    return pos


def state_a5p1(chain):
    """COMMNG1-A5-P1 anchor: official-flow vs price-direction DISAGREEMENT.

    s_flow = sign of the weekly change in speculative net (the two newest
    PIT-visible reports); s_price = sign of the weekly RAW close-to-close
    direction over the decision week (grid-step close anchors, each read
    strictly before its decision instant).  ONLY the two disagreement
    cells arm; direction by the FLOW side (frozen); held 1 grid instant
    (h frozen at the weekly-refresh convention).
    """
    n = len(chain)
    pos = [None] * n
    for i in range(1, n):
        prev, cur = chain[i - 1], chain[i]
        if cur["cend_close"] is None or prev["cend_close"] is None:
            continue
        s_flow = sign(cur["spec_net"] - prev["spec_net"])
        s_price = sign(cur["cend_close"] - prev["cend_close"])
        if s_flow != 0.0 and s_price != 0.0 and s_flow != s_price:
            pos[i] = s_flow
        else:
            pos[i] = 0.0
    return pos


def state_a5p2(chain):
    """COMMNG1-A5-P2 anchor: commercial hedging-flow ACCELERATION tails.

    accel(r) = second difference of commercial net over
    `accel_window_weeks_a5p2` reports, OI-normalized.  Symmetric tail
    buckets of its trailing percentile: upper tail (shock spike) => +1,
    lower tail (saturation collapse) => -1 (frozen symmetric sign
    declaration); held `holding_weeks_a5p2` instants.
    """
    w = int(P("percentile_window_weeks"))
    cut = P("tail_cut")
    h = int(P("holding_weeks_a5p2"))
    accel = [r["accel"] for r in chain]
    n = len(chain)
    arm = [0.0] * n
    for i in range(n):
        b = _tail_arm(accel, i, w, cut)
        if b == "hi":
            arm[i] = +1.0
        elif b == "lo":
            arm[i] = -1.0
    return hold_positions(arm, h)


ANCHOR_STATE = {
    "COMMNG1-A4-P1": state_a4p1,
    "COMMNG1-A4-P2": state_a4p2,
    "COMMNG1-A5-P1": state_a5p1,
    "COMMNG1-A5-P2": state_a5p2,
}


# ----------------------------------------------------------------------- #
# Shadow decision-state series (mapped onto the proposal's own grid)
# ----------------------------------------------------------------------- #

def _readable_bar_index(etp_dates, decision_session):
    """Index of the freshest session STRICTLY before the decision session
    (the declared D1 readability convention), or None."""
    cut = bisect.bisect_left(etp_dates, decision_session)
    return cut - 1 if cut > 0 else None


def shadow_momentum_63s(chain, etp_dates, etp_closes):
    """(a) momentum_63s: sign of the RAW close displacement over 63
    sessions ending at the freshest bar readable strictly before the
    decision instant (weekly-decimated to the grid)."""
    k = int(P("momentum_sessions"))
    pos = [None] * len(chain)
    for i, row in enumerate(chain):
        ds = row["decision_session"]
        if ds is None:
            continue
        j = _readable_bar_index(etp_dates, ds)
        if j is None or j < k:
            continue
        pos[i] = sign(etp_closes[j] - etp_closes[j - k])
    return pos


def shadow_generic_dow_tue(chain):
    """(b) generic_dow_tue: the bare calendar clock on the proposal's
    release-weekday geometry, mapped onto the weekly grid.  The canonical
    post-Friday-release decision session is Monday => fixed +1 side;
    holiday-shifted decision sessions (the ONLY weekday variation the
    weekly grid admits) => -1.  A weekly-grid family that is only this
    clock is exactly the dead calendar family."""
    pos = [None] * len(chain)
    for i, row in enumerate(chain):
        ds = row["decision_session"]
        if ds is None:
            continue
        pos[i] = 1.0 if ds.weekday() == 0 else -1.0
    return pos


def shadow_v16_close_displace_fade(chain, etp_dates, etp_closes):
    """(c) v16_close_displace_fade: fade (negative sign) of the RAW close
    displacement over 5 sessions ending at the freshest readable bar."""
    k = int(P("v16_displace_sessions"))
    pos = [None] * len(chain)
    for i, row in enumerate(chain):
        ds = row["decision_session"]
        if ds is None:
            continue
        j = _readable_bar_index(etp_dates, ds)
        if j is None or j < k:
            continue
        pos[i] = -sign(etp_closes[j] - etp_closes[j - k])
    return pos


# -- price-only analogues (the proposal's own family, price features only) #

def _grid_cend_series(chain):
    """Close anchors (cend) as a chain-aligned series (None preserved)."""
    return [r["cend_close"] for r in chain]


def _weekly_displacement(cend, w):
    """Displacement over w grid steps, relative (scale-free); None-safe."""
    n = len(cend)
    disp = [None] * n
    for i in range(w, n):
        if cend[i] is None or cend[i - w] is None or cend[i - w] == 0.0:
            continue
        disp[i] = cend[i] / cend[i - w] - 1.0
    return disp


def shadow_price_a4p1(chain):
    """(d) A4-P1 price-only shadow: the SAME percentile-tail reversal
    family with the positioning coordinate replaced by trailing ETP price
    displacement over the same frozen window; upper tail => -1, lower tail
    => +1 (mirror of the anchor convention); same holding window."""
    w = int(P("percentile_window_weeks"))
    cut = P("tail_cut")
    h = int(P("holding_weeks_a4_reversal"))
    disp = _weekly_displacement(_grid_cend_series(chain), w)
    arm = [0.0] * len(chain)
    for i in range(len(chain)):
        b = _tail_arm(disp, i, w, cut)
        if b == "hi":
            arm[i] = -1.0
        elif b == "lo":
            arm[i] = +1.0
    return hold_positions(arm, h)


def shadow_price_a4p2(chain):
    """(d) A4-P2 price-only shadow: the SAME persistence-until-trigger
    family on price alone.  Persistence state = displacement-percentile
    tail (upper => carry +1, lower => -1); trigger = opposing 1-week RAW
    displacement of magnitude >= `tau_price_weekly_a4p2`; same bound;
    identical transition entry/exit law to the anchor."""
    w = int(P("percentile_window_weeks"))
    cut = P("tail_cut")
    tau = P("tau_price_weekly_a4p2")
    h_max = int(P("carry_bound_weeks_a4p2"))
    cend = _grid_cend_series(chain)
    disp = _weekly_displacement(cend, w)
    n = len(chain)
    week = [None] * n
    for i in range(1, n):
        if cend[i] is None or cend[i - 1] is None or cend[i - 1] == 0.0:
            continue
        week[i] = cend[i] / cend[i - 1] - 1.0
    pos = [0.0] * n
    held_d = 0.0
    entered_bucket = None
    entry_i = -1
    prev_bucket = None
    for i in range(n):
        b = _tail_arm(disp, i, w, cut)
        if held_d != 0.0:
            f = week[i] if week[i] is not None else 0.0
            trigger = (sign(f) == -held_d) and abs(f) >= tau
            left_tail = (b != entered_bucket)
            bound = (i - entry_i) >= h_max
            if trigger or left_tail or bound:
                held_d = 0.0
            else:
                pos[i] = held_d
        if held_d == 0.0 and b is not None and b != prev_bucket:
            held_d = 1.0 if b == "hi" else -1.0
            entered_bucket = b
            entry_i = i
            pos[i] = held_d
        prev_bucket = b
    return pos


def shadow_price_a5p1(chain):
    """(d) A5-P1 price-only shadow: the SAME 2x2 joint-state cell family
    with BOTH marginals replaced by price analogues: s_now = weekly
    direction sign, s_prev = prior week's direction sign; only the two
    disagreement cells arm; direction by the more recent side (frozen)."""
    cend = _grid_cend_series(chain)
    n = len(chain)
    pos = [None] * n
    for i in range(2, n):
        c0, c1, c2 = cend[i], cend[i - 1], cend[i - 2]
        if None in (c0, c1, c2):
            continue
        s_now = sign(c0 - c1)
        s_prev = sign(c1 - c2)
        if s_now != 0.0 and s_prev != 0.0 and s_now != s_prev:
            pos[i] = s_now
        else:
            pos[i] = 0.0
    return pos


def shadow_price_a5p2(chain):
    """(d) A5-P2 price-only shadow: the SAME acceleration-tail family with
    the coordinate replaced by the scale-free price analogue: second
    difference of the RAW close over the frozen window, relative to the
    close; identical tail/hold law to the anchor."""
    w = int(P("percentile_window_weeks"))
    w_acc = int(P("accel_window_weeks_a5p2"))
    cut = P("tail_cut")
    h = int(P("holding_weeks_a5p2"))
    cend = _grid_cend_series(chain)
    n = len(chain)
    accel = [None] * n
    for i in range(2 * w_acc, n):
        c0, c1, c2 = cend[i], cend[i - w_acc], cend[i - 2 * w_acc]
        if None in (c0, c1, c2) or c0 == 0.0:
            continue
        accel[i] = (c0 - 2.0 * c1 + c2) / c0
    arm = [0.0] * n
    for i in range(n):
        b = _tail_arm(accel, i, w, cut)
        if b == "hi":
            arm[i] = +1.0
        elif b == "lo":
            arm[i] = -1.0
    return hold_positions(arm, h)


PRICE_ONLY_SHADOW = {
    "COMMNG1-A4-P1": shadow_price_a4p1,
    "COMMNG1-A4-P2": shadow_price_a4p2,
    "COMMNG1-A5-P1": shadow_price_a5p1,
    "COMMNG1-A5-P2": shadow_price_a5p2,
}


# ----------------------------------------------------------------------- #
# Measurement assembly
# ----------------------------------------------------------------------- #

def pair_observations(anchor_states, shadow_states, counted):
    """Pairwise-complete measured observations for ONE (pair, shadow):
    (anchor_state, shadow_state) at every counted instant where both are
    computable."""
    return [(a, s) for a, s, c in zip(anchor_states, shadow_states, counted)
            if c and a is not None and s is not None]


def evaluate_shadow(anchor_by_pair, shadow_by_pair, counted_by_pair):
    """Full shadow evaluation: per-pair rows + pooled (stacked across
    pairs) Spearman/Pearson; pooled_abs_rho = max(|spearman|, |pearson|).
    UNMEASURABLE when the pooled observation set is degenerate (fewer than
    2 observations or zero variance).  Per-pair degeneracy is recorded and
    disclosed -- never silently dropped."""
    per_pair = []
    pooled_a, pooled_s = [], []
    n_degenerate_pairs = 0
    for pair_id in sorted(anchor_by_pair):
        obs = pair_observations(
            anchor_by_pair[pair_id], shadow_by_pair[pair_id],
            counted_by_pair[pair_id])
        sp, pe = correlation_pair([a for a, _ in obs], [s for _, s in obs])
        if sp is None:
            n_degenerate_pairs += 1
        per_pair.append({
            "pair": pair_id,
            "n_obs": len(obs),
            "pair_measurable": sp is not None,
            "spearman": None if sp is None else round(sp, 12),
            "pearson": None if pe is None else round(pe, 12),
        })
        for av, sv in obs:
            pooled_a.append(av)
            pooled_s.append(sv)
    sp_p, pe_p = correlation_pair(pooled_a, pooled_s)
    if sp_p is None:
        return {
            "status": "UNMEASURABLE",
            "status_reason": "pooled observation set empty or zero-variance "
                             "(fail-closed: never-PASS-by-absence)",
            "n_obs_total": len(pooled_a),
            "n_degenerate_pairs": n_degenerate_pairs,
            "spearman_pooled": None,
            "pearson_pooled": None,
            "pooled_abs_rho": None,
            "per_pair": per_pair,
        }
    worst = max(
        per_pair,
        key=lambda r: max(
            abs(r["spearman"]) if r["spearman"] is not None else 0.0,
            abs(r["pearson"]) if r["pearson"] is not None else 0.0))
    return {
        "status": "MEASURED",
        "n_obs_total": len(pooled_a),
        "n_degenerate_pairs": n_degenerate_pairs,
        "spearman_pooled": round(sp_p, 12),
        "pearson_pooled": round(pe_p, 12),
        "pooled_abs_rho": round(max(abs(sp_p), abs(pe_p)), 12),
        "per_pair": per_pair,
        "worst_pair_disclosure": {
            "pair": worst["pair"],
            "max_abs": round(max(
                abs(worst["spearman"]) if worst["spearman"] is not None else 0.0,
                abs(worst["pearson"]) if worst["pearson"] is not None else 0.0),
                12),
            "note": "disclosure only; the verdict follows the pooled formula",
        },
    }


def verdict_from_shadows(shadows):
    """The packet verdict law, applied to a {shadow_id: row} map:
    any UNMEASURABLE shadow => VETO_PENDING_UNMEASURABLE (fail-closed,
    never-PASS-by-absence); else proposal pooled = max over shadows of
    pooled_abs_rho; ELIGIBLE iff pooled <= ceiling.  Margin to the
    ceiling recorded per P-2."""
    ceiling = P("novelty_ceiling_abs_rho")
    unmeasurable = [sid for sid in SHADOW_IDS
                    if shadows[sid]["status"] != "MEASURED"]
    measured = [sid for sid in SHADOW_IDS if sid not in unmeasurable]
    if unmeasurable:
        return {
            "verdict": VERDICT_VETO_PENDING,
            "proposal_pooled_abs_rho": None,
            "driving_shadow": None,
            "margin_to_ceiling": None,
            "unmeasurable_shadows": unmeasurable,
        }
    pooled = max(shadows[sid]["pooled_abs_rho"] for sid in measured)
    driving = max(measured, key=lambda s: shadows[s]["pooled_abs_rho"])
    return {
        "verdict": VERDICT_ELIGIBLE if pooled <= ceiling else VERDICT_VETO,
        "proposal_pooled_abs_rho": pooled,
        "driving_shadow": driving,
        "margin_to_ceiling": round(ceiling - pooled, 12),
        "unmeasurable_shadows": [],
    }


def evaluate_proposal(pid, proposals, pair_chains, counted_by_pair):
    """Measure all 4 shadows for ONE proposal; verdict per the packet
    formula.  Fail-closed: any UNMEASURABLE shadow =>
    VETO_PENDING_UNMEASURABLE (never-PASS-by-absence)."""
    anchor_by_pair = {}
    for pair_id, (chain, _counted, _dates, _closes) in pair_chains.items():
        anchor_by_pair[pair_id] = ANCHOR_STATE[pid](chain)
    shadow_rows = {sid: {} for sid in SHADOW_IDS}
    for pair_id, (chain, _c, dates, closes) in pair_chains.items():
        shadow_rows["momentum_63s"][pair_id] = \
            shadow_momentum_63s(chain, dates, closes)
        shadow_rows["generic_dow_tue"][pair_id] = \
            shadow_generic_dow_tue(chain)
        shadow_rows["v16_close_displace_fade"][pair_id] = \
            shadow_v16_close_displace_fade(chain, dates, closes)
        shadow_rows["price_only_shadow"][pair_id] = \
            PRICE_ONLY_SHADOW[pid](chain)

    shadows = {sid: evaluate_shadow(anchor_by_pair, shadow_rows[sid],
                                    counted_by_pair)
               for sid in SHADOW_IDS}

    ceiling = P("novelty_ceiling_abs_rho")
    verdict_row = verdict_from_shadows(shadows)
    detail = {
        "proposal_id": pid,
        "lane": proposals[pid]["lane"],
        "shadows": {},
        "unmeasurable_shadows": verdict_row["unmeasurable_shadows"],
        "proposal_pooled_abs_rho": verdict_row["proposal_pooled_abs_rho"],
        "driving_shadow": verdict_row["driving_shadow"],
        "novelty_ceiling_abs_rho": ceiling,
        "margin_to_ceiling": verdict_row["margin_to_ceiling"],
        "verdict": verdict_row["verdict"],
        "verdict_law": "pooled |rho| <= 0.20 = ELIGIBLE else VETO; any "
                       "UNMEASURABLE shadow => VETO_PENDING_UNMEASURABLE "
                       "(fail-closed, never-PASS-by-absence)",
    }
    for sid in SHADOW_IDS:
        row = dict(shadows[sid])
        row["margin_to_ceiling"] = (
            None if row["pooled_abs_rho"] is None
            else round(ceiling - row["pooled_abs_rho"], 12))
        detail["shadows"][sid] = row
    return detail


# ----------------------------------------------------------------------- #
# Feasibility re-note (P2 per-pair census citations; NO rho)
# ----------------------------------------------------------------------- #

def build_feasibility_renote():
    """Emit d2/feasibility_renote.json (commit-1 artifact): per-proposal
    feasibility re-note citing the P2 per-pair census.  Cost constants are
    cited, not re-measured; NO outcome content, NO correlation values."""
    p2 = load_p2_gate()
    proposals = load_proposals()
    pairs = bookable_pairs(proposals)
    p2_sha = sha256_file(P2_GATE_PATH)
    per_proposal = {}
    for pid in PROPOSAL_IDS:
        decl = proposals[pid]["feasibility_citation"]["d1_bookable_set_declaration"]
        per_proposal[pid] = {
            "lane": proposals[pid]["lane"],
            "bookable_pair_count": decl["bookable_pair_count"],
            "bookable_pairs": sorted(decl["bookable_pairs"]),
            "excluded_pairs": sorted(decl["excluded_pairs"]),
            "exclusion_reason": decl["exclusion_reason"],
            "per_pair_p2_census": {
                pair: {
                    "grid_eligible_instants":
                        p2["per_pair_census"][pair]["floor_evaluation"]
                        ["grid_eligible_instants"],
                    "release_to_session_coverage":
                        p2["per_pair_census"][pair]["floor_evaluation"]
                        ["release_to_session_coverage"],
                    "floor_a_instants":
                        p2["per_pair_census"][pair]["floor_evaluation"]
                        ["floor_a_instants"],
                    "floor_b_coverage":
                        p2["per_pair_census"][pair]["floor_evaluation"]
                        ["floor_b_coverage"],
                    "counted_first_release":
                        p2["per_pair_census"][pair]["floor_evaluation"]
                        ["counted_first_release"],
                    "counted_last_release":
                        p2["per_pair_census"][pair]["floor_evaluation"]
                        ["counted_last_release"],
                    "purity": p2["per_pair_census"][pair]["purity"],
                }
                for pair in sorted(decl["bookable_pairs"])},
            "p2_census_source": {
                "path": "research/control/commodities_ng1_run/p2_gate.json",
                "sha256": p2_sha,
                "final_verdict": p2["final_verdict"],
            },
            "re_note": "D2 re-note: the P2 Q-6 feasibility verdict is "
                       "re-affirmed on the declared bookable set; every "
                       "retained pair individually meets both frozen "
                       "floors (>=300 counted grid-eligible instants, "
                       "coverage >=0.9); cost ceilings are cited from the "
                       "frozen P1 tier-2.0 contract, not re-measured; no "
                       "PnL, no outcome content.",
        }
    renote = {
        "schema": "commodities_ng1_run/d2_feasibility_renote@1",
        "cycle_id": CYCLE_ID,
        "task_id": TASK_ID,
        "base_sha": BASE_SHA,
        "authored_phase": "D2 commit-1 (before any rho; P-12)",
        "p2_final_verdict": p2["final_verdict"],
        "p2_qualifying_pairs": len(p2["per_pair_census"]),
        "per_proposal": per_proposal,
    }
    os.makedirs(D2_DIR, exist_ok=True)
    out = os.path.join(D2_DIR, "feasibility_renote.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(renote, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return out


# ----------------------------------------------------------------------- #
# Runner (commit-2 artifact: the panel)
# ----------------------------------------------------------------------- #

def run(out_path=None):
    """Execute the D2 novelty measurement and write the panel JSON."""
    proposals = load_proposals()
    p2 = load_p2_gate()
    pairs = bookable_pairs(proposals)

    # digest verification of every consumed substrate surface
    cot_sha = sha256_file(COT_CSV_PATH)
    if cot_sha != p2["substrate_pins"]["cot_weekly_targets_csv_sha256"]:
        raise D2Refused("CoT weekly targets digest != committed pin")
    etp_shas = {}
    for pair_id in pairs:
        sym = pair_id.split("/")[1]
        if sym in etp_shas:
            continue
        pin = p2["substrate_pins"]["etp_eod_sha256"][sym]
        actual = sha256_file(os.path.join(ETP_DIR, f"{sym}.csv"))
        if actual != pin:
            raise D2Refused(f"ETP EOD digest mismatch for {sym}")
        etp_shas[sym] = actual

    cot = load_cot_by_market()
    pair_chains = {}
    counted_by_pair = {}
    for pair_id in pairs:
        code, sym = pair_id.split("/")
        dates, closes = load_etp_series(sym)
        chain, counted = build_pair_chain(pair_id, cot, dates, closes)
        verify_pair_census(pair_id, chain, counted, p2)
        pair_chains[pair_id] = (chain, counted, dates, closes)
        counted_by_pair[pair_id] = counted

    results = {}
    for pid in PROPOSAL_IDS:
        results[pid] = evaluate_proposal(
            pid, proposals, pair_chains, counted_by_pair)

    panel = {
        "schema": SCHEMA_PANEL,
        "cycle_id": CYCLE_ID,
        "task_id": TASK_ID,
        "measured_utc": datetime.now(timezone.utc).isoformat(),
        "base_sha": BASE_SHA,
        "branch": BRANCH,
        "law": "decision-STATE correlation only; NO returns, NO PnL, NO "
               "scored outcomes anywhere in this panel",
        "ceiling": {
            "abs_rho_ceiling": P("novelty_ceiling_abs_rho"),
            "source": FROZEN_PARAMETERS["novelty_ceiling_abs_rho"]["rationale"],
        },
        "frozen_parameters": {k: v["value"]
                              for k, v in FROZEN_PARAMETERS.items()},
        "frozen_parameter_rationales": {
            k: v["rationale"] for k, v in FROZEN_PARAMETERS.items()},
        "pooling_definition": "per shadow: Spearman and Pearson of the "
                              "anchor vs shadow decision-state series on the "
                              "pooled pairwise-complete observation set "
                              "stacked across the 11 bookable pairs (P2 "
                              "counted window, 401 instants per pair); "
                              "pooled_abs_rho = max(|spearman|, |pearson|); "
                              "proposal_pooled_abs_rho = max over shadows; "
                              "margin_to_ceiling = ceiling - pooled",
        "representation_mapping": {
            "grid": "P2 counted weekly decision grid (release >= 2018-01-01, "
                    "52-instant warmup carve-out, mapped decision sessions "
                    "only); identity with p2_gate per_pair_census asserted "
                    "fail-closed per pair",
            "warmup_chains": "state history runs over the full measured "
                             "substrate from 2016; the MEASURED set is only "
                             "the P2 counted window",
            "price_readability": "RAW ETP closes; bars strictly before the "
                                 "decision session (declared D1 convention)",
            "pit": "CoT facts only from reports visible at the row's "
                   "release instant (P0 rule imported, never re-derived)",
            "sign_conventions": "anchor family sign conventions frozen and "
                                "documented in measure_novelty.py; pooled "
                                "|rho| is invariant to a global sign flip "
                                "of either series, so verdicts do not "
                                "depend on them",
        },
        "inputs": {
            "p2_gate_sha256": sha256_file(P2_GATE_PATH),
            "cot_weekly_targets_sha256": cot_sha,
            "etp_eod_sha256": etp_shas,
            "proposal_sha256": {
                pid: sha256_file(os.path.join(PROPOSALS_DIR, f"{pid}.json"))
                for pid in PROPOSAL_IDS},
            "commit1_code_sha256": {
                rel: sha256_file(os.path.join(_REPO_ROOT, rel))
                for rel in COMMIT1_FILES},
        },
        "pair_universe": pairs,
        "proposals": results,
    }
    if out_path is None:
        out_path = os.path.join(D2_DIR, "d2_novelty_panel.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(panel, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return out_path, panel


def main(argv):
    out = argv[1] if len(argv) > 1 else None
    path, _panel = run(out)
    print(f"panel written: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
