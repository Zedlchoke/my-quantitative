#!/usr/bin/env python
"""FOREX-FREE-V6 scored execution driver (I1 lane): wires the two SELECTED
V6 families (FXFV6-A4-P1, FXFV6-A6-P2) into the frozen selection freeze and
produces one scored-ledger record per arm via
research.assets.forex_free_v6.ledger_row_v6 (F-TERM-4).

Architecture (inherits the V5 driver architecture,
research/assets/forex_free_v5/exec_driver_v5.py; the V3 accounting kernel
and the V5 financing reader are imported READ-ONLY and never modified):

    for family in (FXFV6-A4-P1, FXFV6-A6-P2):
        for arm in (anchor, neighbour, control):   # exactly 3 arms each
            decisions = family.run_arm(arm, data_paths)
            record    = arm_record(...)             # books, folds, gates
            record    = ledger_row_v6.build_scored_ledger_row(**record)
            publish   = ledger_row_v6.append_row(...)   # append-only

arm_config_digest (F-TERM-4, MANDATORY): recomputed at startup for EACH of
the 6 arms as
``ledger_row_v6.compute_arm_config_digest(selection_freeze.frozen_config)``
and VERIFIED against the frozen ``arm_config_digest`` recorded in
research/control/forex_free_v6_run/selection_freeze.json; ANY mismatch
refuses the whole run before any compute.  The proposal files and the
conditioning-clocks file are sha256-pinned the same way.

Modes
-----
dryrun  The SANITIZED dry-run (handbook discipline, V5 shape): the full
        decision pipeline runs end-to-end (books, folds, drop-one,
        diagnostics are computed internally) and then EVERY outcome field
        is zeroed/placeholders -- scored=false, real_pnl=false,
        published=false, dry_run=true -- before any record leaves the
        module; a recursive PnL-leak scan fails closed on any leak.
        Records go ONLY into a temporary ledger under
        research/control/forex_free_v6_run/dryrun_tmp/ (never the
        canonical ledger, never the scored budget) through the append-only
        ledger_row_v6.append_row (a replay run appends nothing: duplicate
        record ids are refused by the ledger and skipped).  Reveals no
        outcome: the run report carries COUNTS ONLY.
scored  IMPLEMENTED but REFUSES to run unless ALL of:
          1. research/control/forex_free_v6_run/run_contract.json exists
             with the launch-authorization fields (cycle id, launch
             authorized, S0 verdict FOREX_FREE_V6_S0_LAUNCH_AUTHORIZED,
             fresh owner GO phrase "GO FOREX V6 SCORED EXECUTION"),
          2. the ledger seed file named by the contract exists,
          3. budget: fewer than 6 scored cells consumed.
        The scored path is NOT exercised by the I1 lane (no scored
        computation anywhere in it).

Per-arm record contents (V5 baseline vocabulary + V6 identity additions):
dual books (price-only vs financing-adjusted at the base tier 1.0), the
frozen cost ladder 1.5 bps/side x {1.0, 1.5, 2.0} with stress multipliers
applied to BOOKED PnL (tier 2.0 PRIMARY), financing adjustment (inherited
V5 day-start as-of policy-rate differential formula over the pinned
V5-extension ledger -- accounting only, never a signal), 3 temporal folds
in S0 with the per-family frozen boundary semantics, drop-one
(leave-one-pair-out) diagnostics, the USD-drift diagnostic, break-even bps,
and the P-2 margin-to-fail scaffold with every frozen threshold.

Cash (USD) is never an instrument.  No wall clock enters any record.
Determinism: replaying the dry-run produces byte-identical records.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import subprocess
import sys
import time
from datetime import date, datetime, timedelta, timezone

from research.assets.forex_free_v3 import accounting as K            # read-only
from research.assets.forex_free_v5.family_a6p1 import (              # read-only
    LedgerVintageReader,
    dedupe_ledger_rows,
    load_ledger_rows,
)
from research.assets.forex_free_v6 import ledger_row_v6 as L

CYCLE_ID = "FOREX-FREE-V6"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
V6_CTL = os.path.join("research", "control", "forex_free_v6_run")
DRYRUN_TMP_DIRNAME = "dryrun_tmp"
FREEZE_PATH = os.path.join(V6_CTL, "selection_freeze.json")
RUN_CONTRACT_PATH = os.path.join(V6_CTL, "run_contract.json")
SCORED_LEDGER_DEFAULT = os.path.join(V6_CTL, "scored_ledger_published.jsonl")
STAGED_MANIFEST = os.path.join("research", "control", "forex_free_v1_run",
                               "staged_data_manifest.json")
V5_LEDGER = os.path.join("research", "control", "forex_free_v5_run",
                         "announcement_ledger_v5_extension.jsonl")
CLOCK_AUTHORITY = os.path.join(V6_CTL, "p3_conditioning_clocks_v6.json")

# inherited pins (state.json inherited_pins; verified fail closed at startup)
V5_LEDGER_SHA256 = ("cf1f01a7ec2d3d7506892c045139910937147df49d3742cc4ec72b36d"
                    "20fd902")

REPORT_SCHEMA = "forex_free_v6_dryrun_report_v1"
SCORED_REFUSAL_SCHEMA = "forex_free_v6_scored_refusal_v1"
OWNER_GO_PHRASE = "GO FOREX V6 SCORED EXECUTION"
S0_VERDICT = "FOREX_FREE_V6_S0_LAUNCH_AUTHORIZED"
PLANNED_SCORED_CELLS = 6            # exactly 2 families x 3 arms (freeze)
CODE_FREEZE_SHA_PLACEHOLDER = "PENDING_V6_CODE_FREEZE"

BASE_TIER = 1.0
STRESS_TIERS = (1.0, 1.5, 2.0)
PRIMARY_TIER = 2.0
CASH_CURRENCY = "USD"
MAX_FILL_LAG_DAYS = 4
MIN_PF = 1.10                       # V5 scaffold, carried by the V6 rubric
STRESS_MIN_PF = 1.00
MIN_POSITIVE_FOLDS = 2
FOLD_FLOOR = 30                     # rubric feasibility floor per arm/fold
MAX_PAIR_POS_SHARE = 0.40
BREAK_EVEN_FLOOR_BPS = 1.5
USD_CORR_CEILING = 0.30
USD_DIAG_MIN_DAYS = 60
FINANCING_FORMULA_ID = "fx5_day_start_asof_policy_rate_diff_v5ledger_v1"
FINANCING_FORMULA = (
    "financing_adjusted_pnl = price_only_pnl - costs + sign * notional_usd * "
    "(r_base - r_quote) * holding_days/365, accrued per calendar day at the "
    "day-start as-of policy-rate differential from the evidenced policy-rate "
    "vintages of the pinned V5-extension announcement ledger (sha256 "
    "cf1f01a7ec2d3d7506892c045139910937147df49d3742cc4ec72b36d20fd902); rows "
    "eligible only when available_time_utc <= the accrual instant AND "
    "effective_time_utc <= the accrual instant; accounting only, never a "
    "signal (inherited kernel formula, no new financing assumptions)")

FAMILIES = {
    "FXFV6-A4-P1": {
        "module": "research.assets.forex_free_v6.family_a4p1",
        "proposal": os.path.join(V6_CTL, "d1", "a4_postrelease",
                                 "proposal_P1.json"),
        "identifying_tier": 1.0,     # mean per-trade NET bps at 1.0x
        "usd_pairs": ("GBPUSD", "USDCAD", "AUDUSD", "NZDUSD"),
        "drop_one_fold_subsets": True,   # frozen "3 drop-one subsets"
    },
    "FXFV6-A6-P2": {
        "module": "research.assets.forex_free_v6.family_a6p2",
        "proposal": os.path.join(V6_CTL, "d1", "a6_open",
                                 "proposal_P2.json"),
        "identifying_tier": 2.0,     # pooled per-trade NET bps at 2.0x
        "usd_pairs": ("AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD",
                      "USDCHF", "USDJPY"),
        "drop_one_fold_subsets": False,
    },
}
ARMS = ("anchor", "neighbour", "control")

# USD-leg sign of a position: XXX/USD long is short USD (and conversely).
USD_LEG_SIGN = {p: (-1.0 if p.endswith("USD") and not p.startswith("USD")
                    else 1.0) for p in
                ("AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF",
                 "USDJPY")}
PAIR_AREAS = {
    "GBPUSD": ("GB", "US"), "USDCAD": ("US", "CA"), "AUDUSD": ("AU", "US"),
    "NZDUSD": ("NZ", "US"), "EURUSD": ("EMU", "US"), "USDCHF": ("US", "CH"),
    "USDJPY": ("US", "JP"),
}

# Implementing readings for proposal ambiguities at code fidelity (logged at
# runtime; every one is flagged in the I1 handoff to A1, never silent).
IMPLEMENTING_READINGS = (
    {"field": "a6p2_fold_boundaries", "reading":
        "the A6-P2 proposal freezes '3 contiguous temporal thirds of S0 by "
        "decision-day count; boundaries frozen by A1/A9 before any scored "
        "computation'; the only in-repo frozen-boundary evidence is the A9 "
        "measured thirds grid (d2/a9_feasibility/FXFV6-A6-P2.json "
        "sensitivity_fold_thirds_full_S0_grid): B1 2020-09-09, B2 2023-02-16 "
        "-- adopted as the frozen boundaries"},
    {"field": "a6p2_exit_fill_schedule", "reading":
        "exit fill at the decision close exactly 5 decision days after the "
        "entry fill; the exit DECISION is issued at the close 4 decision "
        "days after the entry fill (the proposal parenthetical) so the exit "
        "fill is never same-bar and exposure spans exactly 5 close-to-close "
        "intervals (the proposal holding_profile)"},
    {"field": "a6p2_financing_in_dual_book", "reading":
        "the driver applies the uniform financing-adjusted dual book to BOTH "
        "families per the implementation order; the A6-P2 proposal text "
        "defines its book A as net-of-costs only -- the financing "
        "adjustment is reported separately per record so the strict "
        "net-of-costs book is re-derivable (financing_adjustment_usd column)"},
    {"field": "a4p1_s0_cap_scope_for_sham", "reading":
        "the S0 window caps published clock decision_dates (enforced by the "
        "clocks loader); a control sham SHIFTED conditionable date is not a "
        "published clock date and carries no S0 cap -- its trades fail "
        "closed at staged-data end (A9 measured sham D0s beyond S0 end as "
        "qualified)"},
    {"field": "fold_boundary_semantics", "reading":
        "force-flat-at-boundaries is implemented per family frozen "
        "semantics: A4-P1 never truncates (the k-session hold is the "
        "mechanism); its hold-spanning trades are flagged and purged from "
        "drop-one computations (purge window 16 calendar days, frozen); "
        "A6-P2 exit-fill-crossing trades are DROPPED from both books and "
        "counted"},
    {"field": "percentile_method", "reading":
        "the preregistered 75th-percentile reference threshold uses linear "
        "interpolation between order statistics (the deterministic numpy "
        "default); the method is fixed, never fitted"},
    {"field": "financing_pre_2019_coverage", "reading":
        "the pinned V6 financing authority (V5-extension announcement "
        "ledger, sha cf1f01a7) has a first eligible vintage of 2019-01; a "
        "trade whose accrual window precedes it cannot be financed from "
        "evidence and SKIPS fail-closed, counted as "
        "financing_unavailable_skipped (the staged-data-start pattern, "
        "P-1: no invented rates) -- flagging in case A1 instead funds a "
        "deeper rate authority"},
)


# -------------------------------------------------------------------------- #
# small utilities                                                            #
# -------------------------------------------------------------------------- #
def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git_head(root=ROOT):
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:  # pragma: no cover - record-only
        return None


def _round10(x):
    return None if x is None else round(float(x), 10)


def build_default_data_paths(root=ROOT):
    """The staged V6 data authority: the byte-verified inherited snapshots,
    the P-3 conditioning clocks (A4-P1's ONLY conditioning authority) and
    the pinned V5-extension announcement ledger (financing input,
    accounting only)."""
    return {
        "price_1day_dir": os.path.join(root, "data_raw", "forex_free_v1"),
        "conditioning_clocks": os.path.join(root, CLOCK_AUTHORITY),
        "announcement_ledger": os.path.join(root, V5_LEDGER),
        "staged_manifest": os.path.join(root, STAGED_MANIFEST),
    }


def verify_staged_data(data_paths, root=ROOT):
    """Verify the staged data authority against its pins; fail closed on
    any mismatch.  Returns the evidence dict (hashes + counts only)."""
    manifest_path = (data_paths.get("staged_manifest")
                     or os.path.join(root, STAGED_MANIFEST))
    if not os.path.exists(manifest_path):
        raise RuntimeError(f"STAGED_MANIFEST_MISSING: {manifest_path}")
    manifest = json.load(open(manifest_path, encoding="utf-8"))
    digests = manifest["digests_exec2"]
    bad = []
    for rel, expected in sorted(digests.items()):
        full = os.path.join(root, rel)
        if not os.path.exists(full) or sha256_file(full) != expected:
            bad.append(rel)
    if bad:
        raise RuntimeError(f"STAGED_SNAPSHOT_MISMATCH: {bad[:5]} "
                           f"({len(bad)} bad of {len(digests)})")
    clocks_path = data_paths["conditioning_clocks"]
    clocks_sha = sha256_file(clocks_path)
    freeze = load_freeze(root)
    pinned_clocks = freeze["clocks_file_sha256"]
    if clocks_sha != pinned_clocks:
        raise RuntimeError("CLOCK_AUTHORITY_PIN_MISMATCH: "
                           f"{clocks_sha} != {pinned_clocks}")
    ledger_path = data_paths["announcement_ledger"]
    ledger_sha = sha256_file(ledger_path)
    if ledger_sha != V5_LEDGER_SHA256:
        raise RuntimeError("FINANCING_LEDGER_PIN_MISMATCH: "
                           f"{ledger_sha} != {V5_LEDGER_SHA256}")
    return {
        "staged_snapshot": {
            "manifest": os.path.relpath(manifest_path, root),
            "files_verified": len(digests),
            "mismatches": 0,
        },
        "conditioning_clocks": {
            "path": os.path.relpath(clocks_path, root),
            "sha256": clocks_sha,
            "pinned": pinned_clocks,
            "match": True,
        },
        "financing_ledger": {
            "path": os.path.relpath(ledger_path, root),
            "sha256": ledger_sha,
            "pinned": V5_LEDGER_SHA256,
            "match": True,
        },
    }


def load_freeze(root=ROOT):
    path = os.path.join(root, FREEZE_PATH) if not os.path.isabs(FREEZE_PATH) \
        else FREEZE_PATH
    if not os.path.exists(path):
        raise SystemExit(f"SELECTION_FREEZE_MISSING: {path}")
    return json.load(open(path, encoding="utf-8"))


# -------------------------------------------------------------------------- #
# freeze verification (digest table; refuse on ANY mismatch)                 #
# -------------------------------------------------------------------------- #
def verify_freeze(root=ROOT):
    """Verify the selection freeze against the materialized artifacts and
    recompute all 6 arm_config_digests.  Returns (arms_table, checks):
    arms_table rows {family_id, arm, proposal_sha256, recomputed_digest,
    frozen_digest, digest_match}; ANY mismatch raises SystemExit."""
    freeze = load_freeze(root)
    checks = []
    families = freeze["selected_families"]
    if len(families) != 2:
        raise SystemExit(f"FREEZE_FAMILY_COUNT_MISMATCH: {len(families)} != 2")
    proposal_pins = {}
    arms_table = []
    for fam in families:
        family_id = fam["family_id"]
        spec = FAMILIES.get(family_id)
        if spec is None:
            raise SystemExit(f"FREEZE_FAMILY_UNKNOWN: {family_id}")
        proposal_path = os.path.join(root, spec["proposal"])
        if not os.path.exists(proposal_path):
            raise SystemExit(f"PROPOSAL_PACKET_MISSING: {proposal_path}")
        actual = sha256_file(proposal_path)
        if actual != fam["proposal_sha256"]:
            raise SystemExit(f"PROPOSAL_SHA_MISMATCH: {proposal_path} "
                             f"{actual} != {fam['proposal_sha256']}")
        proposal_pins[family_id] = actual
        if sorted(fam["arms"]) != sorted(ARMS):
            raise SystemExit(f"FREEZE_ARM_COUNT_MISMATCH: {family_id} "
                             f"{sorted(fam['arms'])}")
        for arm in ARMS:
            arm_spec = fam["arms"][arm]
            frozen_cfg = arm_spec["frozen_config"]
            frozen_digest = arm_spec["arm_config_digest"]
            recomputed = L.compute_arm_config_digest(frozen_cfg)
            row = {
                "family_id": family_id,
                "arm": arm,
                "design_axis": arm_spec["design_axis"],
                "frozen_digest": frozen_digest,
                "recomputed_digest": recomputed,
                "digest_match": recomputed == frozen_digest,
            }
            if not row["digest_match"]:
                raise SystemExit(
                    f"ARM_CONFIG_DIGEST_MISMATCH: {family_id}/{arm} "
                    f"recomputed {recomputed} != frozen {frozen_digest} "
                    "-- refusing to run")
            arms_table.append(row)
            checks.append(f"{family_id}/{arm}")
    return arms_table, checks


def clocks_evidence_set(clocks_path):
    """The set of archive_sha256 values published in the clocks file (an
    A4-P1 decision citing a sha outside this set is an invented clock ->
    HARD_FAIL)."""
    payload = json.load(open(clocks_path, encoding="utf-8"))
    return {row["archive_sha256"] for row in payload["clocks"]}


# -------------------------------------------------------------------------- #
# decision-stream validation (fail closed)                                   #
# -------------------------------------------------------------------------- #
def _parse(ts, what):
    try:
        t = datetime.fromisoformat(str(ts))
    except ValueError as exc:
        raise ValueError(f"{what} is not an ISO-8601 instant: {ts!r}") from exc
    if t.tzinfo is None:
        raise ValueError(f"{what} is timezone-naive: {ts!r}")
    return t.astimezone(timezone.utc)


def _is_ny_1600(t):
    from zoneinfo import ZoneInfo
    ny = t.astimezone(ZoneInfo("America/New_York"))
    return ny.hour == 16 and ny.minute == 0


def validate_decisions(decisions, family_id, clocks_shas=None):
    """Frozen decision-stream rules; any violation fails the run closed."""
    seen = set()
    for d in decisions:
        did = d.get("decision_id")
        if not isinstance(did, str) or not did:
            raise ValueError(f"{family_id}: decision_id missing")
        if did in seen:
            raise ValueError(f"DUPLICATE_DECISION_ID: {did}")
        seen.add(did)
        if d.get("pair") == CASH_CURRENCY:
            # cash (USD) is never an instrument (kernel rule)
            raise ValueError(f"CASH_AS_INSTRUMENT: {did}")
        if d.get("side") not in (1, -1):
            raise ValueError(f"{did}: side must be +1/-1")
        if float(d.get("notional_usd", 0)) <= 0:
            raise ValueError(f"{did}: notional_usd must be > 0")
        dec = _parse(d.get("decision_ts"), f"{did}: decision_ts")
        entry = _parse(d.get("entry_ts"), f"{did}: entry_ts")
        exit_ = _parse(d.get("exit_ts"), f"{did}: exit_ts")
        for name, t in (("decision_ts", dec), ("entry_ts", entry),
                        ("exit_ts", exit_)):
            if not _is_ny_1600(t):
                raise ValueError(f"{did}: {name} {t.isoformat()} is not a "
                                 "completed 16:00 America/New_York daily bar")
        if not (entry > dec):
            raise ValueError(f"{did}: same-bar fill forbidden "
                             "(entry not strictly after the decision instant)")
        if entry - dec > timedelta(days=MAX_FILL_LAG_DAYS):
            raise ValueError(f"{did}: entry fill more than "
                             f"{MAX_FILL_LAG_DAYS} days after the decision")
        if not (exit_ > entry):
            raise ValueError(f"{did}: exit is not after entry")
        if clocks_shas is not None:
            sha = d.get("archive_sha256")
            if sha not in clocks_shas:
                raise ValueError(f"{did}: invented clock (archive_sha256 not "
                                 "resolvable to the clocks authority)")
    return seen


# -------------------------------------------------------------------------- #
# financing (inherited kernel formula; pinned ledger; accounting only)       #
# -------------------------------------------------------------------------- #
def financing_reader(data_paths):
    rows = load_ledger_rows(data_paths["announcement_ledger"])
    return LedgerVintageReader(dedupe_ledger_rows(rows))


def financing_adjustment_usd(reader, pair, side, notional, entry_ts, exit_ts,
                             strict=True):
    """sign * notional * sum(day-start as-of policy-rate differentials)/365
    over the calendar days [entry fill date, exit fill date).

    strict=True (booking): a missing eligible vintage at any accrual
    instant fails closed.  strict=False (eligibility pass): returns None
    when ANY accrual day lacks an eligible vintage -- the pinned V6
    financing authority's own data start (first eligible vintage
    2019-01); such trades skip fail-closed and are counted (the
    staged-data-start pattern), never financed with invented rates.
    """
    base_area, quote_area = PAIR_AREAS[pair]
    day = entry_ts.date()
    last = exit_ts.date()
    diffs = []
    while day < last:
        t = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        diff = reader.differential(base_area, quote_area, t)
        if diff is None:
            if strict:
                raise RuntimeError(
                    f"{pair}: no eligible policy-rate vintage for accrual at "
                    f"{t.isoformat()}")
            return None
        diffs.append(diff / 100.0)
        day = day + timedelta(days=1)
    return side * notional * math.fsum(diffs) / 365.0


# -------------------------------------------------------------------------- #
# booking (price-only book vs costed ladder; stress on BOOKED PnL)           #
# -------------------------------------------------------------------------- #
def price_pnl_usd(trade):
    """The frozen kernel USD-unit price identity:
    direction * notional * (exit/entry - 1)."""
    return trade["side"] * trade["notional_usd"] \
        * (trade["exit_price"] / trade["entry_price"] - 1.0)


def dual_book_inversions(trades, financing_by_id):
    """Tiers at which the costed book inverts the aggregate sign of the
    price-only book (an accounting HARD_FAIL flag, never a rescue)."""
    price_mean = (math.fsum(price_pnl_usd(t) for t in trades)
                  / len(trades)) if trades else 0.0
    inversions = []
    for tier in STRESS_TIERS:
        pnls = book_trades(trades, tier, financing_by_id)
        costed_mean = math.fsum(pnls) / len(pnls) if pnls else 0.0
        if (costed_mean > 0) != (price_mean > 0):
            inversions.append(f"tier{tier}")
    return inversions


def book_trades(trades, tier, financing_by_id):
    """Booked PnL at one ladder tier: price PnL - costs at the tier +
    financing.  The stress multiplier is applied to the BOOKED PnL (the
    whole round trip is re-booked at the tier), never scaled after the
    fact.  Costs: 1.5 bps per side x tier via the kernel primitive
    (charged exactly once per side)."""
    pnls = []
    for tr in trades:
        gross = price_pnl_usd(tr)
        cost = 2.0 * K.bps_cost(tr["notional_usd"], tier)
        net = gross - cost + financing_by_id[tr["decision_id"]]
        pnls.append(net)
    return pnls


def book_metrics(pnls):
    """V3 kernel metrics convention (same rounding / None-PF)."""
    return K.book_metrics(pnls)


def mdd_of(pnls):
    peak = trough = cum = mdd = 0.0
    for p in pnls:
        cum += p
        peak = max(peak, cum)
        mdd = max(mdd, peak - cum)
    return _round10(mdd)


def concentration(trades, pnls):
    """Share of gross positive PnL by pair (V3 convention; cash never
    appears)."""
    pos = [p for p in pnls if p > 0]
    gp = math.fsum(pos)
    if gp <= 0:
        return {}
    shares = {}
    for tr, p in zip(trades, pnls):
        if p <= 0 or tr["pair"] == CASH_CURRENCY:
            continue
        shares[tr["pair"]] = shares.get(tr["pair"], 0.0) + p
    return {kk: round(v / gp, 6) for kk, v in shares.items()}


def fold_positive_share(folds):
    gp = math.fsum(f["gross_positive"] for f in folds
                   if f["gross_positive"] > 0)
    if gp <= 0:
        return 0.0
    return round(max(f["gross_positive"] for f in folds) / gp, 6)


# -------------------------------------------------------------------------- #
# USD-drift diagnostic                                                       #
# -------------------------------------------------------------------------- #
def usd_index_daily_returns(data_paths, pairs):
    """Frozen equal-weight USD-leg return index from the staged 1day
    closes: XXX/USD contributes the NEGATIVE pair return, USD/XXX the
    positive pair return; keyed by the later bar's date."""
    from research.assets.forex_free_v6 import family_a6p2 as G
    per_pair = {}
    for pair in pairs:
        closes = G.load_daily_closes(data_paths["price_1day_dir"], pair)
        days = sorted(closes)
        steps = {}
        for d0, d1 in zip(days, days[1:]):
            r = math.log(closes[d1] / closes[d0])
            steps[d1.isoformat()] = USD_LEG_SIGN[pair] * r
        per_pair[pair] = steps
    all_days = sorted({d for steps in per_pair.values() for d in steps})
    return {d: math.fsum(s[d] for s in per_pair.values() if d in s)
            / sum(1 for s in per_pair.values() if d in s)
            for d in all_days}


def usd_drift_diagnostic(trades, pnls, folds_held_days, usd_index):
    """Aggregate net USD-leg exposure drift: mean daily signed USD-leg
    exposure over every held calendar day, its per-fold dispersion, and
    the Pearson correlation of daily aggregate PnL vs the USD index daily
    return (evaluated only over >= USD_DIAG_MIN_DAYS trade days)."""
    daily_exp = {}
    daily_pnl = {}
    for tr, p in zip(trades, pnls):
        sign = USD_LEG_SIGN[tr["pair"]] * tr["side"]
        day = tr["entry_ts"][:10]
        last = tr["exit_ts"][:10]
        d = date.fromisoformat(day)
        end = date.fromisoformat(last)
        while d < end:
            key = d.isoformat()
            daily_exp[key] = daily_exp.get(key, 0.0) + sign
            daily_pnl[key] = daily_pnl.get(key, 0.0) + p
            d = d + timedelta(days=1)
    days = sorted(daily_exp)
    mean_exp = (math.fsum(daily_exp[d] for d in days) / len(days)) if days \
        else 0.0
    fold_disp = None
    if folds_held_days:
        fold_means = []
        for day_list in folds_held_days:
            vals = [daily_exp[d] for d in day_list if d in daily_exp]
            if vals:
                fold_means.append(math.fsum(vals) / len(vals))
        if len(fold_means) >= 2:
            mu = math.fsum(fold_means) / len(fold_means)
            fold_disp = math.sqrt(
                math.fsum((v - mu) ** 2 for v in fold_means)
                / len(fold_means))
    corr = None
    xs, ys = [], []
    for d in days:
        r = usd_index.get(d)
        if r is not None:
            xs.append(float(r))
            ys.append(daily_pnl.get(d, 0.0))
    evaluated = False
    if len(xs) >= USD_DIAG_MIN_DAYS:
        mx, my = math.fsum(xs) / len(xs), math.fsum(ys) / len(ys)
        cov = math.fsum((x - mx) * (y - my) for x, y in zip(xs, ys))
        vx = math.fsum((x - mx) ** 2 for x in xs)
        vy = math.fsum((y - my) ** 2 for y in ys)
        corr = _round10(cov / math.sqrt(vx * vy)) if vx > 0 and vy > 0 else 0.0
        evaluated = True
    return {
        "mean_usd_leg_exposure": _round10(mean_exp),
        "fold_dispersion_usd_leg_exposure": _round10(fold_disp),
        "corr": corr,
        "n_days": len(days),
        "evaluated": evaluated,
    }


# -------------------------------------------------------------------------- #
# drop-one diagnostics (leave-one-pair-out; A4-P1 also drops each fold)      #
# -------------------------------------------------------------------------- #
def mean_bps(pnls, trades):
    if not pnls:
        return None
    return _round10(math.fsum(p / t["notional_usd"] * 10000.0
                              for p, t in zip(pnls, trades)) / len(pnls))


def drop_one_diagnostics(trades, tier, financing_by_id, family_spec,
                         full_sign):
    """Leave-one-pair-out: each subset's pooled mean net bps at the
    family's identifying tier must share the full-sample sign (P1 subsets
    purge hold-spanning trades per the frozen purge rule).  A4-P1
    additionally evaluates the 3 frozen drop-one-FOLD subsets."""
    scenarios = []
    lopo_means = {}
    pairs = sorted({t["pair"] for t in trades})
    for excl in pairs:
        sub_t = [t for t in trades if t["pair"] != excl]
        sub_t = [t for t in sub_t if not t.get("span_boundary_purged")]
        sub_p = book_trades(sub_t, tier, financing_by_id)
        m = mean_bps(sub_p, sub_t)
        lopo_means[excl] = m
        scenarios.append({"scenario": f"drop_pair:{excl}", "expectancy_bps": m,
                          "survived": (m is not None and full_sign != 0
                                       and (m > 0) == (full_sign > 0))})
    if family_spec.get("drop_one_fold_subsets"):
        for fold in ("F1", "F2", "F3"):
            sub_t = [t for t in trades
                     if t.get("fold") != fold
                     and not t.get("span_boundary_purged")]
            sub_p = book_trades(sub_t, tier, financing_by_id)
            m = mean_bps(sub_p, sub_t)
            scenarios.append({"scenario": f"drop_fold:{fold}",
                              "expectancy_bps": m,
                              "survived": (m is not None and full_sign != 0
                                           and (m > 0) == (full_sign > 0))})
    return lopo_means, scenarios


# -------------------------------------------------------------------------- #
# per-arm record assembly                                                    #
# -------------------------------------------------------------------------- #
def fold_split(trades, pnls, family_id):
    """Per-fold metrics; trades assign by the family's frozen rule (A4-P1:
    event D0; A6-P2: entry decision date t) -- both families carry the
    fold id on the trade.  Populated floor: FOLD_FLOOR trades."""
    out = []
    for fold in ("F1", "F2", "F3"):
        idx = [i for i, t in enumerate(trades) if t.get("fold") == fold]
        fp = [pnls[i] for i in idx]
        m = book_metrics(fp)
        m["fold"] = fold
        m["populated"] = m["trades"] >= FOLD_FLOOR
        out.append(m)
    return out


def arm_record(family_id, arm, family_result, spec, digest, reader,
               data_paths, root=ROOT):
    """Compute the FULL arm record (books, folds, drop-one, diagnostics,
    gate scaffold).  The dry-run sanitizes this record afterwards; the
    scored path would publish it as-is (never exercised by this lane)."""
    module = importlib.import_module(spec["module"])
    trades = family_result["decisions"]
    meta = family_result["meta"]
    clocks_shas = None
    if family_id == "FXFV6-A4-P1":
        clocks_shas = clocks_evidence_set(data_paths["conditioning_clocks"])
    validate_decisions(trades, family_id, clocks_shas)

    # financing events (accounting only): exactly one per BOOKED decision.
    # A trade whose accrual window precedes the pinned financing
    # authority's first eligible vintage skips fail-closed and is counted
    # (financing_unavailable_skipped -- the staged-data-start pattern;
    # never financed with invented rates).
    financing_by_id = {}
    financing_skipped = []
    for tr in trades:
        adj = financing_adjustment_usd(
            reader, tr["pair"], tr["side"], tr["notional_usd"],
            _parse(tr["entry_ts"], "entry_ts"),
            _parse(tr["exit_ts"], "exit_ts"), strict=False)
        if adj is None:
            financing_skipped.append(tr["decision_id"])
            continue
        financing_by_id[tr["decision_id"]] = adj
    booked_trades = [t for t in trades
                     if t["decision_id"] in financing_by_id]
    pnls_base = book_trades(booked_trades, BASE_TIER, financing_by_id)
    pnls_price = [price_pnl_usd(t) for t in booked_trades]
    metrics_base = book_metrics(pnls_base)
    metrics_price = book_metrics(pnls_price)

    # dual-book invariant: sign(price_only mean) must equal sign(costed
    # mean) at every tier; any inversion is an accounting HARD_FAIL flag,
    # never a rescue
    inversions = dual_book_inversions(booked_trades, financing_by_id)
    dual_book_ok = not inversions

    folds = fold_split(booked_trades, pnls_base, family_id)
    stress = {}
    for tier in STRESS_TIERS:
        stress[f"tier{tier}"] = book_metrics(
            book_trades(booked_trades, tier, financing_by_id))

    identifying_tier = spec["identifying_tier"]
    id_pnls = book_trades(booked_trades, identifying_tier, financing_by_id)
    id_mean_bps = mean_bps(id_pnls, booked_trades)
    full_sign = 0 if id_mean_bps is None else (1 if id_mean_bps > 0 else -1)
    lopo_means, scenarios = drop_one_diagnostics(
        booked_trades, identifying_tier, financing_by_id, spec, full_sign)
    n_lopo = sum(1 for s in scenarios if s["scenario"].startswith("drop_pair:"))
    lopo_share = round(sum(1 for s in scenarios
                           if s["scenario"].startswith("drop_pair:")
                           and s["survived"]) / n_lopo, 6) if n_lopo else None

    # break-even bps: per-side = |mean gross per-trade bps| / 2 (frozen
    # P-2 convention), reported against the 1.5 bps floor
    gross_bps = [p / t["notional_usd"] * 10000.0 for p, t in
                 zip(pnls_price, booked_trades)]
    break_even_bps = (_round10(abs(math.fsum(gross_bps) / len(gross_bps)) / 2.0)
                      if gross_bps else None)

    usd_index = usd_index_daily_returns(data_paths, spec["usd_pairs"])
    folds_held_days = []
    for fold in ("F1", "F2", "F3"):
        day_list = sorted({t["entry_ts"][:10] for t in booked_trades
                           if t.get("fold") == fold})
        folds_held_days.append(day_list)
    usd_diag = usd_drift_diagnostic(booked_trades, pnls_base,
                                    folds_held_days, usd_index)

    # per-pair and USD-base-vs-USD-quote splits (A4-P1 usd_drift_diag
    # reporting requirement; reported for both families)
    per_pair_mean = {}
    for pair in sorted({t["pair"] for t in booked_trades}):
        sub_t = [t for t in booked_trades if t["pair"] == pair]
        sub_p = book_trades(sub_t, identifying_tier, financing_by_id)
        per_pair_mean[pair] = mean_bps(sub_p, sub_t)
    base_pairs = [p for p in per_pair_mean if not p.startswith("USD")]
    quote_pairs = [p for p in per_pair_mean if p.startswith("USD")]

    n_dec = len(trades)
    purged = sum(1 for t in trades if t.get("span_boundary_purged"))
    boundary_dropped = int(meta.get("skipped_counts", {})
                           .get("boundary_crossing_dropped", 0))

    record = {
        # identity (V6 additions + baseline identity)
        "cycle_id": CYCLE_ID,
        "family_id": family_id,
        "arm": arm,
        "proposal_id": family_id,
        "arm_config_digest": digest,
        "code_freeze_sha": CODE_FREEZE_SHA_PLACEHOLDER,
        "data_snapshot_digest": sha256_file(data_paths["staged_manifest"]),
        "cell_id": f"{family_id}:{arm}@tier{PRIMARY_TIER}",
        "record_id": f"{CYCLE_ID}-{family_id}-{arm}-{digest[:12]}",
        "trial_id": f"{CYCLE_ID}/{family_id}/{arm}/{digest[:12]}",
        "cost_tier": PRIMARY_TIER,
        "decision_clock": meta["decision_clock"],
        # books (V5 baseline vocabulary)
        "base": metrics_base,
        "base_price_only": metrics_price,
        "gross_price_pnl_usd": _round10(math.fsum(pnls_price)) if pnls_price
        else 0.0,
        "price_only_pnl_usd": _round10(math.fsum(pnls_price)) if pnls_price
        else 0.0,
        "financing_adjusted_pnl_usd": metrics_base["total_pnl"],
        "financing_adjustment_usd": _round10(
            math.fsum(financing_by_id.values())) if financing_by_id else 0.0,
        "financing_formula": FINANCING_FORMULA,
        "financing_formula_id": FINANCING_FORMULA_ID,
        "mdd_usd": mdd_of(pnls_base),
        "folds": folds,
        "folds_declared": 3,
        "fold_positive_share": fold_positive_share(folds),
        "pair_concentration": concentration(booked_trades, pnls_base),
        "stress": stress,
        "break_even_cost_bps": break_even_bps,
        "drop_one_expectancy": lopo_means,
        "dropout_scenarios": scenarios,
        "incremental_alpha": None,
        "incremental_alpha_definition": (
            "none_declared_v6_exactly_three_arms_no_benchmark"),
        "benchmark_treatment": None,
        "delay_stress": None,
        "usd_drift_diag": dict(usd_diag,
                               per_pair_mean_bps=per_pair_mean,
                               usd_base_pairs_mean_bps=_round10(
                                   math.fsum([per_pair_mean[p] for p in
                                              base_pairs]) / len(base_pairs))
                               if base_pairs else None,
                               usd_quote_pairs_mean_bps=_round10(
                                   math.fsum([per_pair_mean[p] for p in
                                              quote_pairs]) / len(quote_pairs))
                               if quote_pairs else None),
        "usd_index_pairs": list(spec["usd_pairs"]),
        "usd_index_source": "staged_1day_equal_weight_usd_leg_v1",
        # counts
        "n_decisions": n_dec,
        "n_trades": n_dec,
        "n_trades_kept": len(booked_trades),
        "financing_unavailable_skipped": len(financing_skipped),
        "purge_days": module_meta(module, "PURGE_DAYS", None),
        "purged_trades": purged,
        "boundary_crossing_dropped": boundary_dropped,
        "weekend_gate_dropped": 0,
        # gates
        "gates": False,           # set below
        "gate_reasons": [],
        "dual_book_inversion_tiers": inversions,
        "dual_book_ok": dual_book_ok,
        "identifying_tier": identifying_tier,
        "identifying_metric_bps": id_mean_bps,
        "lopo_sign_robustness_share": lopo_share,
        # flags (dry-run sanitize flips these; scored leaves them)
        "dry_run": False,
        "scored": True,
        "real_pnl": True,
        "published": False,
    }
    scaffold = gate_scaffold(record)
    record["dryrun_gate_scaffold"] = {
        "evaluated_on": "booked_scored_book",
        "gates": scaffold,
    }
    ok, reasons = evaluate_gates(scaffold, record)
    record["gates"] = ok
    record["gate_reasons"] = reasons
    return record


def module_meta(module, name, default):
    return getattr(module, name, default)


# -------------------------------------------------------------------------- #
# P-2 margin-to-fail scaffold (frozen thresholds; signed margins)            #
# -------------------------------------------------------------------------- #
def gate_scaffold(rec):
    """{gate, threshold, comparator, observed, margin} for every frozen
    gate; margin is signed in the PASS direction (margin > 0 passes;
    None when the observed value is not evaluable)."""

    def _margin(gate, threshold, comparator, observed):
        if observed is None:
            margin = None
        elif comparator in (">", ">="):
            margin = _round10(observed - threshold)
        else:
            margin = _round10(threshold - observed)
        return {"gate": gate, "threshold": threshold,
                "comparator": comparator, "observed": observed,
                "margin": margin}

    base = rec["base"]
    folds = rec["folds"]
    pop = [f for f in folds if f["trades"] > 0]
    pos_folds = [f for f in pop if f["expectancy"] is not None
                 and f["expectancy"] > 0]
    tier2 = rec["stress"]["tier2.0"]
    conc = max(rec["pair_concentration"].values()) \
        if rec["pair_concentration"] else None
    usd = rec["usd_drift_diag"]
    lopo_share = rec["lopo_sign_robustness_share"]
    rows = [
        _margin("fin_adj_expectancy_gt_0", 0.0, ">", base["expectancy"]),
        _margin("pf_ge_1.10", MIN_PF, ">=", base["pf"]),
        _margin("fold_nonvacuity_ge_30_per_arm_per_fold", float(FOLD_FLOOR),
                ">=", float(min((f["trades"] for f in pop), default=0))
                if pop else 0.0),
        _margin("positive_populated_folds_ge_2", float(MIN_POSITIVE_FOLDS),
                ">=", float(len(pos_folds))),
        _margin("pair_concentration_le_0.40", MAX_PAIR_POS_SHARE, "<=", conc),
        _margin("stress_tier2.0_primary_total_pnl_gt_0", 0.0, ">",
                tier2["total_pnl"]),
        _margin("stress_tier2.0_primary_pf_ge_1.00", STRESS_MIN_PF, ">=",
                tier2["pf"]),
        _margin("break_even_bps_le_1.5_floor", BREAK_EVEN_FLOOR_BPS, "<=",
                rec["break_even_cost_bps"]),
        _margin("dual_book_sign_non_inversion", 1.0, ">=",
                1.0 if rec["dual_book_ok"] else 0.0),
        _margin("lopo_sign_robustness_all_subsets", 1.0, ">=", lopo_share),
        _margin("usd_drift_corr_abs_le_0.30", USD_CORR_CEILING, "<=",
                abs(usd["corr"]) if usd["evaluated"]
                and usd["corr"] is not None else None),
    ]
    return rows


def evaluate_gates(scaffold, rec):
    """Gate verdict on the scaffold margins (all evaluable margins must be
    positive).  Returns (ok, reasons)."""
    reasons = []
    ok = True
    for row in scaffold:
        if row["margin"] is None:
            ok = False
            reasons.append(f"{row['gate']}: NOT_EVALUABLE")
        elif row["margin"] <= 0:
            ok = False
            reasons.append(f"{row['gate']}: margin {row['margin']}")
    if rec["purged_trades"] or rec["boundary_crossing_dropped"]:
        reasons.append(
            f"boundary_handling: purged={rec['purged_trades']} "
            f"dropped={rec['boundary_crossing_dropped']} (reported, "
            "frozen semantics)")
    return ok, reasons


# -------------------------------------------------------------------------- #
# dry-run sanitization + recursive PnL-leak scan (V5 discipline)             #
# -------------------------------------------------------------------------- #
_MONETARY_BOOK_KEYS = ("gross_price_pnl_usd", "price_only_pnl_usd",
                       "financing_adjustment_usd",
                       "financing_adjusted_pnl_usd")


def _zero_metrics(metrics):
    out = dict(metrics)
    for key in ("total_pnl", "expectancy", "gross_positive"):
        if key in out:
            out[key] = 0.0
    if "pf" in out:
        out["pf"] = None
    return out


def sanitize_dry_run(record):
    """Zero/placeholder EVERY booked monetary metric so no outcome
    information can leave the module; counts and frozen constants survive;
    flags flipped to the sanitized posture."""
    for key in _MONETARY_BOOK_KEYS:
        record[key] = 0.0
    record["base"] = _zero_metrics(record["base"])
    record["base_price_only"] = _zero_metrics(record["base_price_only"])
    record["folds"] = [_zero_metrics(f) for f in record["folds"]]
    record["stress"] = {tier: _zero_metrics(m)
                        for tier, m in record["stress"].items()}
    record["break_even_cost_bps"] = None
    record["mdd_usd"] = 0.0
    record["fold_positive_share"] = 0.0
    record["pair_concentration"] = {}
    record["drop_one_expectancy"] = {p: None
                                     for p in record["drop_one_expectancy"]}
    record["dropout_scenarios"] = [
        {"scenario": s["scenario"], "expectancy_bps": None, "survived": None}
        for s in record["dropout_scenarios"]]
    record["identifying_metric_bps"] = None
    record["lopo_sign_robustness_share"] = None
    record["dual_book_inversion_tiers"] = []
    usd = record["usd_drift_diag"]
    record["usd_drift_diag"] = {
        "mean_usd_leg_exposure": 0.0,
        "fold_dispersion_usd_leg_exposure": 0.0,
        "corr": None,
        "n_days": usd["n_days"],
        "evaluated": False,
        "per_pair_mean_bps": {p: None for p in usd.get("per_pair_mean_bps",
                                                       {})},
        "usd_base_pairs_mean_bps": None,
        "usd_quote_pairs_mean_bps": None,
    }
    record["dry_run"] = True
    record["real_pnl"] = False
    record["scored"] = False
    record["published"] = False
    scaffold = gate_scaffold(record)
    record["dryrun_gate_scaffold"] = {
        "evaluated_on": "sanitized_placeholders_not_evidence",
        "gates": scaffold,
    }
    ok, reasons = evaluate_gates(scaffold, record)
    record["gates"] = ok
    record["gate_reasons"] = list(reasons)
    record["dryrun_gate_check"] = {
        "evaluated_on": "sanitized_placeholders_not_evidence",
        "note": "not evidence: every observed value is a zeroed placeholder",
        "gate_pass": bool(ok),
        "gate_reasons": list(reasons),
    }
    return record


# dry-run structural allowlist (extends the V5 allowlist with the V6
# identity/structure keys; pair names under per-pair parents)
FIELD_ALLOWLIST = frozenset({
    # V5 baseline row columns
    "schema", "record_id", "cost_tier", "n_trades", "n_decisions",
    "gross_price_pnl_usd", "price_only_pnl_usd", "financing_adjustment_usd",
    "financing_adjusted_pnl_usd", "dry_run", "real_pnl", "published",
    "cell_id", "family_id", "arm", "proposal_id", "decision_clock",
    "financing_formula", "financing_formula_id", "scored", "n_trades_kept", "weekend_gate_dropped",
    "purged_trades", "folds_declared", "purge_days", "base",
    "base_price_only", "folds", "mdd_usd", "fold_positive_share",
    "pair_concentration", "drop_one_expectancy", "dropout_scenarios",
    "break_even_cost_bps", "usd_drift_diag", "usd_index_source",
    "usd_index_pairs", "stress", "delay_stress", "incremental_alpha",
    "incremental_alpha_definition", "benchmark_treatment",
    "gate_reasons", "gates", "trial_id",
    # V6 identity additions
    "arm_config_digest", "cycle_id", "code_freeze_sha",
    "data_snapshot_digest",
    # metrics keys (zeroed placeholders in a sanitized record)
    "trades", "total_pnl", "expectancy", "pf", "gross_positive",
    # fold metrics
    "fold", "populated",
    # driver structural block (counts only)
    "dryrun_structure", "dryrun_gate_check", "dryrun_gate_scaffold",
    "evaluated_on", "gate_pass", "note",
    "structure_family", "structure_arm", "schedule_totals",
    "skipped_reason_counts", "economy_clock_counts", "frozen_constants",
    "ca_boundary_remap_published", "ca_boundary_remap_in_schedule",
    "ca_boundary_remap_qualified", "grid_days", "grid_first_date",
    "grid_last_date", "first_eligible_decision_date",
    "singular_or_degenerate_correlation", "fold_contract",
    "fold_boundaries", "fold_boundary_evidence", "published_clocks",
    "trades_and_skips_reconciled", "dual_book_ok",
    "dual_book_inversion_tiers", "identifying_tier",
    "identifying_metric_bps", "lopo_sign_robustness_share",
    "boundary_crossing_dropped", "zero_positions",
    "would_refuse_publication", "refusal_code",
    "implementing_readings", "field", "reading",
    "financing_unavailable_skipped",
    # dropout scenario rows + P-2 scaffold rows (all placeholders in a
    # sanitized record)
    "scenario", "survived", "expectancy_bps",
    "gate", "threshold", "comparator", "observed", "margin",
    # per-pair / per-economy keyed parents
})
PAIR_KEY_PARENTS = frozenset({
    "drop_one_expectancy", "pair_concentration", "per_pair_mean_bps",
    "schedule_totals", "economy_clock_counts", "clocks_pair_map",
})
PAIR_NAMES = frozenset({"GBPUSD", "USDCAD", "AUDUSD", "NZDUSD", "EURUSD",
                        "USDCHF", "USDJPY", "GB", "CA", "AU", "NZ"})
REASON_KEY_PARENTS = frozenset({"skipped_reason_counts"})
FOLD_KEY_PARENTS = frozenset({"folds"})
TIER_KEY_PARENTS = frozenset({"stress"})
TIER_KEYS = frozenset({"tier1.0", "tier1.5", "tier2.0"})
# structural containers whose child keys are frozen/structural vocabulary
# (the outcome-suspect VALUE rule below still applies to every child)
STRUCTURE_KEY_PARENTS = frozenset({
    "frozen_constants", "fold_contract", "dryrun_structure",
    "dryrun_gate_check", "dryrun_gate_scaffold", "usd_drift_diag",
    "zero_positions", "s0_window",
})
OUTCOME_LABEL_KEYS = frozenset({
    "incremental_alpha_definition", "percentile_method",
})
OUTCOME_VALUE_RE = __import__("re").compile(
    r"(pnl|profit|expectancy|pf|mdd|break_even|alpha|concentration|"
    r"survived|gross|share|corr)")
LEAK_SCAN_NOTE = (
    "recursive scan over every dict/list leaf of every sanitized record; "
    "key allowlist (FIELD_ALLOWLIST; pair/economy names under per-pair "
    "parents; frozen skip-reason identifiers under skipped_reason_counts) + "
    "forced-placeholder rule for every key matching "
    "pnl|profit|expectancy|pf|mdd|break_even|alpha|concentration|survived|"
    "gross|share|corr (exceptions: incremental_alpha_definition is a frozen "
    "identifier label) + flags scored=false real_pnl=false published=false "
    "dry_run=true")


def recursive_leak_scan(record):
    """Walk EVERY dict/list leaf of ``record``; return (findings, scanned).
    A finding is a key outside the allowlist, a non-placeholder value under
    an outcome-suspect key, or a broken dry-run flag."""
    findings = []
    scanned = 0

    def _zero_ok(value):
        if isinstance(value, dict):
            return all(_zero_ok(v) for v in value.values())
        if isinstance(value, list):
            return all(_zero_ok(v) for v in value)
        if isinstance(value, bool):
            return value is False
        if isinstance(value, (int, float)):
            return value == 0
        return value is None

    def _walk(node, path, parent_key):
        nonlocal scanned
        if isinstance(node, dict):
            for key, value in node.items():
                scanned += 1
                if not isinstance(key, str):
                    findings.append(f"{path}: non-string key {key!r}")
                    continue
                if parent_key in PAIR_KEY_PARENTS:
                    if key not in PAIR_NAMES:
                        findings.append(f"{path}.{key}: key not a pair name")
                elif parent_key in REASON_KEY_PARENTS:
                    if not key:
                        findings.append(f"{path}.{key}: empty reason id")
                elif parent_key in FOLD_KEY_PARENTS:
                    pass  # list of fold metric dicts (walked below)
                elif parent_key in TIER_KEY_PARENTS:
                    if key not in TIER_KEYS:
                        findings.append(f"{path}.{key}: not a tier label")
                elif parent_key in STRUCTURE_KEY_PARENTS:
                    pass  # structural container: frozen constants, gate
                          # scaffold rows, the USD diagnostic block
                elif key not in FIELD_ALLOWLIST:
                    findings.append(f"{path}.{key}: key outside allowlist")
                if isinstance(key, str) and OUTCOME_VALUE_RE.search(key):
                    if key in OUTCOME_LABEL_KEYS:
                        if not isinstance(value, (str, type(None))):
                            findings.append(
                                f"{path}.{key}: label key carries non-string")
                    elif not _zero_ok(value):
                        findings.append(
                            f"{path}.{key}: outcome-suspect key carries "
                            f"non-placeholder value {value!r}")
                _walk(value, f"{path}.{key}", key)
        elif isinstance(node, list):
            for i, value in enumerate(node):
                scanned += 1
                _walk(value, f"{path}[{i}]", parent_key)

    _walk(record, "$", None)
    for flag, expected in (("scored", False), ("real_pnl", False),
                           ("published", False), ("dry_run", True)):
        if record.get(flag) is not expected:
            findings.append(f"$.{flag}: expected {expected}, "
                            f"got {record.get(flag)!r}")
    return findings, scanned


# -------------------------------------------------------------------------- #
# scored-mode launch gates (refusal probes; fail closed)                     #
# -------------------------------------------------------------------------- #
def evaluate_launch_gates(root=ROOT, scored_ledger_path=None):
    """The V6 scored launch gates: the run contract must exist with its
    launch-authorization fields AND the ledger seed file must exist AND
    the budget must have free cells."""
    gates = {}

    def _check(name, ok, detail):
        gates[name] = {"ok": bool(ok), "detail": str(detail)}

    contract_path = os.path.join(root, RUN_CONTRACT_PATH)
    contract = None
    if not os.path.exists(contract_path):
        _check("run_contract", False,
               f"missing {RUN_CONTRACT_PATH} (no launch authorization)")
    else:
        try:
            contract = json.load(open(contract_path, encoding="utf-8"))
        except (OSError, ValueError) as exc:
            contract = None
            _check("run_contract", False, f"unreadable run contract: {exc}")
    if contract is not None:
        problems = []
        if contract.get("cycle_id") != CYCLE_ID:
            problems.append(f"cycle_id {contract.get('cycle_id')!r}")
        if contract.get("launch_authorized") is not True:
            problems.append("launch_authorized is not true")
        if contract.get("s0_launch_authorized_verdict") != S0_VERDICT:
            problems.append("s0_launch_authorized_verdict mismatch")
        if contract.get("owner_go_phrase") != OWNER_GO_PHRASE:
            problems.append("owner_go_phrase mismatch")
        if contract.get("owner_go_fresh") is not True:
            problems.append("owner_go_fresh is not true")
        _check("run_contract", not problems,
               "all launch-authorization fields present" if not problems
               else "; ".join(problems))

    seed = (contract or {}).get("ledger_seed_path") or SCORED_LEDGER_DEFAULT
    seed_path = seed if os.path.isabs(seed) else os.path.join(root, seed)
    if os.path.exists(seed_path):
        with open(seed_path, "r", encoding="utf-8") as handle:
            consumed = sum(1 for line in handle if line.strip())
        _check("ledger_seed", consumed < PLANNED_SCORED_CELLS,
               f"{consumed}/{PLANNED_SCORED_CELLS} scored cells consumed in "
               "the seeded ledger")
    else:
        _check("ledger_seed", False,
               f"ledger seed file missing: {seed} (scored publication "
               "requires the seeded append-only ledger)")
    return all(g["ok"] for g in gates.values()), gates


# -------------------------------------------------------------------------- #
# the 6-arm driver                                                           #
# -------------------------------------------------------------------------- #
def _register_families(root=ROOT):
    modules = {}
    for family_id, spec in FAMILIES.items():
        modules[family_id] = importlib.import_module(spec["module"])
    return modules


def _structure_summary(family_id, result):
    """Counts-only projection of one family run (never prices, never PnL)."""
    meta = result["meta"]
    summary = {
        "structure_family": family_id,
        "structure_arm": meta["arm"],
        "n_decisions_returned": len(result["decisions"]),
        "skipped_reason_counts": dict(meta.get("skipped_counts", {})),
    }
    if "economy_clock_counts" in meta:
        summary["economy_clock_counts"] = dict(meta["economy_clock_counts"])
    if "per_economy_schedule" in meta:
        summary["schedule_totals"] = {
            e: int(counts.get("trades", 0))
            for e, counts in meta["per_economy_schedule"].items()}
    if "frozen_constants" in meta:
        summary["frozen_constants"] = dict(meta["frozen_constants"])
    if "fold_boundaries" in meta:
        summary["fold_boundaries"] = list(meta["fold_boundaries"])
    if "fold_contract" in meta:
        summary["fold_contract"] = [dict(f) for f in meta["fold_contract"]]
    for key in ("ca_boundary_remap_published", "ca_boundary_remap_in_schedule",
                "ca_boundary_remap_qualified", "grid_days", "grid_first_date",
                "grid_last_date", "first_eligible_decision_date",
                "singular_or_degenerate_correlation"):
        if key in meta:
            summary[key] = meta[key]
    summary["trades_and_skips_reconciled"] = True  # family raises otherwise
    return summary


def run_dryrun(data_paths, ledger_path, report_path, root=ROOT,
               verify_data=True):
    """The six-arm SANITIZED dry-run.  Records go ONLY to a temporary
    ledger under dryrun_tmp/; nothing is scored, published or budgeted.
    Replay-safe: a second run appends nothing and produces byte-identical
    records.  The run report carries COUNTS ONLY (no PnL, no metrics)."""
    tmp_dir = os.path.join(root, V6_CTL, DRYRUN_TMP_DIRNAME)
    abs_ledger = os.path.abspath(ledger_path)
    abs_tmp = os.path.abspath(tmp_dir)
    if os.path.commonpath([abs_ledger, abs_tmp]) != abs_tmp:
        raise SystemExit(
            f"DRYRUN_LEDGER_MUST_BE_TEMPORARY: {abs_ledger} is not under "
            f"{abs_tmp} (dry-run records never enter any canonical ledger)")
    os.makedirs(abs_tmp, exist_ok=True)

    t0 = time.time()
    freeze_table, freeze_checks = verify_freeze(root)
    data_verification = verify_staged_data(data_paths, root) \
        if verify_data else {"skipped": "synthetic fixture run"}
    modules = _register_families(root)
    reader = financing_reader(data_paths)

    arms_out = []
    records_by_id = {}
    head_pin = None
    leak_fields_total = 0
    schedule_files = {}
    for family_id in FAMILIES:
        spec = FAMILIES[family_id]
        module = modules[family_id]
        for arm in ARMS:
            result = module.run_arm(arm, data_paths)
            digest_row = next(r for r in freeze_table
                              if r["family_id"] == family_id
                              and r["arm"] == arm)
            record = arm_record(family_id, arm, result, spec,
                                digest_row["recomputed_digest"], reader,
                                data_paths, root)
            structure = _structure_summary(family_id, result)
            n_kept = int(record["n_trades_kept"])
            structure["zero_positions"] = {
                "n_trades_kept": n_kept,
                "would_refuse_publication": n_kept == 0,
                "refusal_code": "EMPTY_TRADE_SET" if n_kept == 0 else None,
            }
            record["dryrun_structure"] = structure
            record = sanitize_dry_run(record)
            findings, scanned = recursive_leak_scan(record)
            if findings:
                raise RuntimeError(f"PNL_LEAK_SCAN_FAILED {family_id}:{arm}: "
                                   f"{findings[:10]}")
            leak_fields_total += scanned
            # dry-run decision trace (counts + frozen inputs only) goes to
            # the temporary schedule artifact next to the temp ledger
            sched_path = os.path.join(
                abs_tmp, f"schedule_{family_id}_{arm}.json")
            with open(sched_path, "w", encoding="utf-8") as handle:
                json.dump({
                    "family_id": family_id, "arm": arm,
                    "n_decisions": len(result["decisions"]),
                    "decision_ids": [d["decision_id"]
                                     for d in result["decisions"]],
                }, handle, sort_keys=True)
            schedule_files[f"{family_id}:{arm}"] = sched_path
            # append-only publication into the TEMP ledger (replay: the
            # ledger refuses a duplicate record id and the run skips it)
            published_now = False
            try:
                evidence = L.append_row(abs_ledger, record,
                                        expected_head_sha256=head_pin)
                head_pin = evidence["head_sha256_after"]
                published_now = True
            except L.LedgerRowError as exc:
                if exc.code != "DUPLICATE_RECORD_ID":
                    raise
            records_by_id[record["record_id"]] = record
            arms_out.append({
                "family": family_id,
                "arm": arm,
                "arm_id": module.ARM_IDS[arm],
                "record_id": record["record_id"],
                "trial_id": record["trial_id"],
                "arm_config_digest": record["arm_config_digest"],
                "digest_match": digest_row["digest_match"],
                "n_decisions": record["n_decisions"],
                "n_trades_kept": record["n_trades_kept"],
                "purged_trades": record["purged_trades"],
                "boundary_crossing_dropped":
                    record["boundary_crossing_dropped"],
                "skipped_reason_counts":
                    record["dryrun_structure"]["skipped_reason_counts"],
                "zero_positions": record["dryrun_structure"]["zero_positions"],
                "dry_run": record["dry_run"],
                "scored": record["scored"],
                "real_pnl": record["real_pnl"],
                "published": record["published"],
                "published_now_to_temp_ledger": published_now,
                "leak_scan": "clean",
                "outcome_fields": "zeroed_and_labelled_not_evidence",
            })
            print(json.dumps({
                "arm": record["record_id"],
                "n_decisions": record["n_decisions"],
                "leak_scan": "clean",
                "published_now_to_temp_ledger": published_now}), flush=True)

    pairwise_ids = (
        len({a["record_id"] for a in arms_out}) == len(arms_out)
        and len({a["trial_id"] for a in arms_out}) == len(arms_out)
        and len({a["arm_config_digest"] for a in arms_out})
        == len(arms_out))
    if not pairwise_ids:
        raise RuntimeError("PAIRWISE_ID_VIOLATION: record/trial/digest ids "
                           "collide across the 6 arms")

    report = {
        "schema": REPORT_SCHEMA,
        "mode": "dryrun",
        "cycle_id": CYCLE_ID,
        "families": sorted(FAMILIES),
        "scored": False, "real_pnl": False, "published": False,
        "dryrun_utc": _utc_now_iso(),
        "stamp_source": "machine_date_u",
        "base_head": git_head(root),
        "code_freeze_sha": CODE_FREEZE_SHA_PLACEHOLDER,
        "digest_verification_table": freeze_table,
        "digest_checks": freeze_checks,
        "data_verification": data_verification,
        "arms": arms_out,
        "arm_record_counts": {a["record_id"]: a["n_decisions"]
                              for a in arms_out},
        "pairwise_distinct_ids": pairwise_ids,
        "recursive_leak_scan": {
            "records_scanned": len(arms_out),
            "fields_scanned": leak_fields_total,
            "leaks_found": [],
            "rule": LEAK_SCAN_NOTE,
        },
        "temporary_ledger": os.path.relpath(abs_ledger, root),
        "schedule_artifacts": {kk: os.path.relpath(v, root)
                               for kk, v in schedule_files.items()},
        "denominator_note": "dry-run records never enter the scored budget; "
                            "the temp-ledger line count is not a denominator",
        "implementing_readings": [dict(r) for r in IMPLEMENTING_READINGS],
        "limitations": [
            "dry-run only: every booked monetary metric is a zeroed "
            "placeholder; records carry counts and frozen constants, never "
            "outcomes",
            "dry-run gates and the P-2 margin scaffold are evaluated ON "
            "zeroed placeholders and are explicitly not evidence",
            "scored mode is implemented but refuses without the run "
            "contract launch-authorization fields and the seeded ledger",
        ],
        "note": "SANITIZED DRY-RUN: scored=false, real_pnl=false, "
                "published=false; book values are zeroed placeholders and "
                "carry no outcome information. This report carries COUNTS "
                "ONLY.",
        "elapsed_s": round(time.time() - t0, 1),
    }
    os.makedirs(os.path.dirname(os.path.abspath(report_path)), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    print(json.dumps({"mode": "dryrun", "arms": len(arms_out),
                      "pairwise_distinct_ids": pairwise_ids,
                      "leaks": 0, "report": report_path}), flush=True)
    return report


def run_scored(data_paths, report_path, root=ROOT):
    """The SCORED path.  REFUSES (SystemExit 2, refusal report written)
    unless the run-contract launch gates and the ledger seed hold; never
    invoked by the I1 lane."""
    ok, gates = evaluate_launch_gates(root)
    if not ok:
        refusal = {
            "schema": SCORED_REFUSAL_SCHEMA,
            "mode": "scored", "cycle_id": CYCLE_ID,
            "refused_utc": _utc_now_iso(),
            "stamp_source": "machine_date_u",
            "refused": True,
            "gates": gates,
            "note": "LAUNCH GATES NOT SATISFIED: no cell computed, nothing "
                    "booked, nothing published. Two-key protocol: fresh-"
                    f"context S0 artifact {S0_VERDICT}, then the owner "
                    f"types, fresh: '{OWNER_GO_PHRASE}'.",
        }
        os.makedirs(os.path.dirname(os.path.abspath(report_path)),
                    exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(refusal, handle, indent=1, sort_keys=True)
        print(json.dumps({"mode": "scored", "refused": True,
                          "failed_gates": [kk for kk, v in gates.items()
                                           if not v["ok"]],
                          "report": report_path}), flush=True)
        raise SystemExit(2)

    # Gates satisfied: scored books, appended to the seeded ledger.
    freeze_table, _ = verify_freeze(root)
    verify_staged_data(data_paths, root)
    modules = _register_families(root)
    reader = financing_reader(data_paths)
    contract = json.load(open(os.path.join(root, RUN_CONTRACT_PATH),
                              encoding="utf-8"))
    seed = contract.get("ledger_seed_path") or SCORED_LEDGER_DEFAULT
    ledger_path = seed if os.path.isabs(seed) else os.path.join(root, seed)
    head_pin = None
    if os.path.exists(ledger_path) and os.path.getsize(ledger_path) > 0:
        head_pin = sha256_file(ledger_path)
    cells = []
    for family_id in FAMILIES:
        spec = FAMILIES[family_id]
        module = modules[family_id]
        for arm in ARMS:
            result = module.run_arm(arm, data_paths)
            digest_row = next(r for r in freeze_table
                              if r["family_id"] == family_id
                              and r["arm"] == arm)
            record = arm_record(family_id, arm, result, spec,
                                digest_row["recomputed_digest"], reader,
                                data_paths, root)
            record["published"] = True   # the append below is the publication
            evidence = L.append_row(ledger_path, record,
                                    expected_head_sha256=head_pin)
            head_pin = evidence["head_sha256_after"]
            cells.append({"cell_id": record["record_id"],
                          "arm_config_digest": record["arm_config_digest"],
                          "gates_pass": record["gates"],
                          "gate_reasons": record["gate_reasons"],
                          "published": True})
            print(json.dumps({"cell": record["record_id"],
                              "gates_pass": record["gates"]}), flush=True)
    report = {"schema": "forex_free_v6_scored_report_v1", "mode": "scored",
              "cycle_id": CYCLE_ID, "cells": cells,
              "dryrun_utc": _utc_now_iso(),
              "stamp_source": "machine_date_u"}
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mode", choices=("dryrun", "scored"), required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--ledger", default=None,
                    help="dry-run mode: temp ledger path (must be under "
                         "dryrun_tmp/)")
    ap.add_argument("--data-paths", default=None,
                    help="JSON file with the data_paths dict; default: the "
                         "staged V6 data authority (verified fail-closed)")
    args = ap.parse_args(argv)

    data_paths = build_default_data_paths()
    verify = True
    if args.data_paths:
        data_paths = json.load(open(args.data_paths, encoding="utf-8"))
        verify = bool(data_paths.get("verify_authority", True))

    if args.mode == "dryrun":
        ledger = args.ledger or os.path.join(
            ROOT, V6_CTL, DRYRUN_TMP_DIRNAME, "dryrun_ledger.jsonl")
        return run_dryrun(data_paths, ledger, args.report, verify_data=verify)
    return run_scored(data_paths, args.report)


if __name__ == "__main__":  # pragma: no cover
    main()
