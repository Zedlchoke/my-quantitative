#!/usr/bin/env python3
"""STOCKS-SEARCH-V1 D1 — frozen search-space manifest builder (deterministic, outcome-blind).

Cycle:   STOCKS-SEARCH-V1 (orchestration label ZCODE-ORCHESTRATION-V3)
Task:    ssearch-d1
Plan:    plans/PLAN_stocks_search_v1.md  §5 (as amended by §3b)
Base:    5be14a6d6771df8ec3c23ebc70f0044e9b87ec6e (branch orca/stocks-search-v1-integration)

Builds   research/control/stocks_search_v1_run/d1/search_space_manifest.json
         enumerating ALL 47 configurations (EVENT-UNWIND 9, GAP 12, 52W-HIGH 6,
         CLV-RANGE 4, DVOL-SHOCK 8, VOL-REGIME 8; grid cap 120).

Laws enforced by construction:
  - OUTCOME-BLIND: no returns, PnL, PF, Sharpe, expectancy, drawdown or any
    performance statistic anywhere (the --selfcheck key-scan bans
    performance-field keys; a violation is a build failure).
  - DETERMINISTIC: output depends ONLY on the committed p0 artifacts + this
    file; no clock, no randomness. Byte-identical rebuild from the same base.
  - FAIL-CLOSED: any mismatch vs p0 artifacts (counts, IDs, definitions) is
    an INPUT_MISMATCH build failure, never a silent repair.

Usage:
  build_d1_manifest.py              # build (writes search_space_manifest.json)
  build_d1_manifest.py --selfcheck  # build, then verify the frozen manifest
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parent                      # research/control/stocks_search_v1_run
P0 = RUN / "p0"
ROOT = HERE.parents[3]                 # worktree root
PLAN = "plans/PLAN_stocks_search_v1.md"
FFL = ROOT / "research" / "wayfinder" / "FAMILY_FAILURES.jsonl"
MANIFEST_PATH = HERE / "search_space_manifest.json"

BASE_SHA = "5be14a6d6771df8ec3c23ebc70f0044e9b87ec6e"
SCHEMA = "stocks_search_v1_d1_search_space_manifest@1"
CYCLE_ID = "STOCKS-SEARCH-V1"
TASK_ID = "ssearch-d1"
GRID_CAP = 120
FOLDS = ["F1", "F2", "F3"]             # chronological; F3 = most recent fold
SELECTION_FOLD = "F3"                  # §3b tier: "the most recent fold"

# ---------------------------------------------------------------------------
# canonical hashing convention
#   self_sha256 = sha256(canonical_json(manifest)) where canonical_json is
#   UTF-8, sort_keys=True, separators=(",",":"), ensure_ascii=False, computed
#   with the manifest's own "self_sha256" field set to the EMPTY STRING "".
#   The committed file is pretty-printed; the hash binds content, not
#   formatting.
# ---------------------------------------------------------------------------


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canon_sha256(obj) -> str:
    return hashlib.sha256(canon(obj)).hexdigest()


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class BuildError(RuntimeError):
    """INPUT_MISMATCH / freeze-contract violation — fail-closed."""


# ---------------------------------------------------------------------------
# §5 frozen parameter sub-grids (plan §5 verbatim grid; all parameters declared
# from construction logic, never tuned). param order in IDs is stable.
# ---------------------------------------------------------------------------

FAMILIES = {
    "EVENT-UNWIND": {
        "grid_text": "K in {21, 63, 252} x hold H in {5, 10, 20} (plan §5 family 1; NG6 anchor construction, grid-extended)",
        "param_key": "K",
        "h_key": "H",
        "combos": [(k, h) for k in (21, 63, 252) for h in (5, 10, 20)],
        "cfg_id": lambda p: f"SSS-EVENT-UNWIND-K{p[0]}-H{p[1]}",
        "params": lambda p: {"K": p[0], "H": p[1]},
        "components": {
            "1_BREAK": "adj_low_t < min(adj_low_{t-K..t-1})",
            "2_RECLAIM": "adj_close_t > that prior K-session low",
            "3_RANGE": "(close_t - low_t)/(high_t - low_t) >= 0.5 (zero-range law: high == low NOT FIRED)",
            "4_PARTICIPATION": "dollar_volume_t >= 1.5x trailing 60-session median",
            "membership": "ALL FOUR components required to fire (conjunction, plan §5)",
        },
        "sign_frozen": "long-only: long on the fired break-reclaim decision, flat otherwise; no short leg (no borrow-cost authority — plan §5 long-only law)",
    },
    "GAP": {
        "grid_text": "gap threshold at {25th, 50th, 75th} percentile of the trailing 252-session gap distribution x direction {fade, confirm} x H in {1, 5} (plan §5 family 2)",
        "param_key": "pctl",
        "h_key": "H",
        "combos": [(q, d, h) for q in (25, 50, 75) for d in ("FADE", "CONFIRM") for h in (1, 5)],
        "cfg_id": lambda p: f"SSS-GAP-P{p[0]}-{p[1]}-H{p[2]}",
        "params": lambda p: {"pctl": p[0], "direction": p[1].lower(), "H": p[2]},
        "components": {
            "conditioning": "gap_t = open_t/close_{t-1} - 1 on the adjusted series; threshold = p-th percentile (linear) of the trailing 252-session gap history ending at and including t",
            "trigger": "directional side: fade FIRED iff gap_t <= threshold; confirm FIRED iff gap_t >= threshold (long-only)",
        },
        "sign_frozen": {
            "FADE": "long-only: long on the fired fade-side gap (gap_t <= threshold), flat otherwise; no short leg",
            "CONFIRM": "long-only: long on the fired confirm-side gap (gap_t >= threshold), flat otherwise; no short leg",
        },
    },
    "52W-HIGH": {
        "grid_text": "band in {2%, 5%, 10%} below the 252-session high x H in {5, 20} (plan §5 family 3)",
        "param_key": "band",
        "h_key": "H",
        "combos": [(b, h) for b in (2, 5, 10) for h in (5, 20)],
        "cfg_id": lambda p: f"SSS-52W-HIGH-B{p[0]}-H{p[1]}",
        "params": lambda p: {"band_pct": p[0], "H": p[1]},
        "components": {
            "conditioning": "high_t = rolling 252-session max of adjusted close (the SAME adjusted series as returns), ending at and including t",
            "trigger": "proximity_t = (high_t - close_t)/high_t <= band/100",
            "history_law": "non-positive adjusted high leaves the state UNDEFINED — NEVER fires, bar censused (same fail-closed family as the §5 zero-range law; commit 127e7f26)",
        },
        "sign_frozen": "long inside the band, flat outside; sign frozen from construction (plan §5 verbatim); long-only, no short leg",
    },
    "CLV-RANGE": {
        "grid_text": "slope window k in {5, 10} x H in {5, 10} on the 20-session CLV accumulation state (plan §5 family 4; CLV formula per FOREX-NG7 §5 FNG7-A2-P1-ABSORB, cross-plane adaptation to equities DISCLOSED)",
        "param_key": "k",
        "h_key": "H",
        "combos": [(k, h) for k in (5, 10) for h in (5, 10)],
        "cfg_id": lambda p: f"SSS-CLV-RANGE-K{p[0]}-H{p[1]}",
        "params": lambda p: {"k": p[0], "H": p[1]},
        "components": {
            "clv_formula": "CLV_t = ((C-L)-(H-C))/(H-L); zero-range law: a high == low bar makes CLV undefined and NOT FIRED (fail-closed, never imputed)",
            "conditioning": "P_t = sum of CLV over the trailing 20 completed bars (undefined if ANY bar in the window is degenerate — fail-closed)",
            "trigger": "slope = P_t - P_{t-k}; FIRED iff slope > 0 (strict)",
        },
        "sign_frozen": "long-only: long on positive CLV-accumulation slope (slope > 0 strict), flat otherwise; sign frozen from construction; no short leg",
    },
    "DVOL-SHOCK": {
        "grid_text": "dollar-volume ratio in {1.5x, 3.0x} vs trailing 60-session median x direction {fade, confirm} x H in {1, 5} (plan §5 family 5)",
        "param_key": "ratio",
        "h_key": "H",
        "combos": [(r, d, h) for r in (1.5, 3.0) for d in ("FADE", "CONFIRM") for h in (1, 5)],
        "cfg_id": lambda p: f"SSS-DVOL-SHOCK-R{p[0]}x-{p[1]}-H{p[2]}",
        "params": lambda p: {"ratio": p[0], "direction": p[1].lower(), "H": p[2]},
        "components": {
            "conditioning": "ratio_t = dvol_t / median(dvol over trailing 60 sessions ending at t-1); shock present iff ratio_t >= ratio threshold",
            "trigger": "directional side on ret_t = close_t/close_{t-1} - 1 (adjusted series): confirm FIRED iff shock AND ret_t > 0; fade FIRED iff shock AND ret_t < 0 (ret_t == 0 NOT FIRED, fail-closed neutral)",
        },
        "sign_frozen": {
            "FADE": "long-only: long on a fired shock with ret_t < 0, flat otherwise; no short leg",
            "CONFIRM": "long-only: long on a fired shock with ret_t > 0, flat otherwise; no short leg",
        },
    },
    "VOL-REGIME": {
        "grid_text": "lookback L in {21, 63} x H in {5, 20} x direction {long-LOW, long-HIGH} = 8 configs, BOTH directions enumerated as distinct configurations inside the cap, signs frozen at D1 from the enumeration (plan §5 family 6)",
        "param_key": "L",
        "h_key": "H",
        "combos": [(l, d, h) for l in (21, 63) for d in ("LOW", "HIGH") for h in (5, 20)],
        "cfg_id": lambda p: f"SSS-VOL-REGIME-L{p[0]}-{p[1]}-H{p[2]}",
        "params": lambda p: {"L": p[0], "direction": p[1].lower(), "H": p[2]},
        "components": {
            "estimator": "sigma_j = close-to-close log-return sample std (ddof=1) over the trailing L returns ending at and including j",
            "boundaries": "1/3 and 2/3 quantiles (linear interpolation) of sigma over the trailing 252-session window ending at and including t, refreshed daily, same-bar assignment — NEVER full-sample (causal, pinned)",
            "trigger": "long-LOW FIRED iff sigma_t <= q1; long-HIGH FIRED iff sigma_t >= q2 (middle tercile flat)",
        },
        "sign_frozen": {
            "LOW": "long-only: long in the LOWEST vol tercile (sigma_t <= q1), flat otherwise; direction enumerated as a distinct configuration (plan §5); no short leg",
            "HIGH": "long-only: long in the HIGHEST vol tercile (sigma_t >= q2), flat otherwise; direction enumerated as a distinct configuration (plan §5); no short leg",
        },
    },
}

FAMILY_COUNTS_PLAN = {"EVENT-UNWIND": 9, "GAP": 12, "52W-HIGH": 6,
                      "CLV-RANGE": 4, "DVOL-SHOCK": 8, "VOL-REGIME": 8}

# ---------------------------------------------------------------------------
# §6 controls declared ex ante per family (C-COMPLEMENT; R5 component-only).
# Declared BEFORE any measurement; outcome-blind definitions only.
# ---------------------------------------------------------------------------

C_COMPLEMENT = {
    "EVENT-UNWIND": "raw breakdown without reclaim (plan §6 example): FIRED iff BREAK AND RANGE AND PARTICIPATION; the RECLAIM component is removed — same grid, causal placebo",
    "GAP": "gap state without direction (plan §6 example): FIRED iff gap_t <= threshold OR gap_t >= threshold — threshold-state presence with the fade/confirm split removed",
    "52W-HIGH": "proximity complement region: FIRED iff high_t defined AND proximity_t > band/100 — the candidate's flat (outside-band) region under the same construction",
    "CLV-RANGE": "range-state without direction (plan §6 example): FIRED iff P_t is defined (complete 20-bar CLV window under the zero-range law) with the slope-sign trigger removed — any slope",
    "DVOL-SHOCK": "shock state without direction: FIRED iff ratio_t >= ratio threshold — shock presence with the ret-sign split removed",
    "VOL-REGIME": "tercile-state complement: FIRED iff q1 < sigma_t < q2 — the middle tercile under the same causal machinery, extremal direction removed",
}

R5_COMPONENT_ONLY = {
    "EVENT-UNWIND": "range+participation filter-only (plan §6 R5 example): FIRED iff RANGE AND PARTICIPATION — BREAK and RECLAIM removed (conditioning filter WITHOUT the directional/trigger component)",
    "GAP": "threshold-state-only (plan §6 R5 example): FIRED iff the percentile threshold is crossed on either side — conditioning state without any directional/trigger component",
    "52W-HIGH": "high-window-only: FIRED iff the rolling 252-session high is defined — proximity condition removed",
    "CLV-RANGE": "P_t-defined-only: FIRED iff the 20-bar CLV window is complete (zero-range law) — slope trigger removed",
    "DVOL-SHOCK": "ratio-state-only: FIRED iff ratio_t is defined (trailing-60 median available) — shock threshold and ret-sign trigger removed",
    "VOL-REGIME": "tercile-assigned-only: FIRED iff sigma_t is assigned to any tercile (boundaries defined) — extremal selection removed",
}
# every family admits a component-only analog -> R5 adjudicable for all six;
# the plan's NOT_ADJUDICABLE branch (§6 R5) is unused in this grid (disclosed).

EXPECTED_DOA = {
    "EVENT-UNWIND": "expected-DOA: reversal-shadow territory — the event-conditional 5d/21d return and drawdown-depth short-term-reversal shadows are BINDING (§6 inventory); survives only through construction distance (§6 R0 convention). EX-ANTE construction-based disclosure ONLY — R0 is NOT_RUN this cycle (D2 skipped per §3b); never a measured verdict",
    "GAP": "expected-DOA: the overnight-gap state IS a listed §6 R0 shadow class (prior-session close-to-open gap, fade/confirm direction classes). EX-ANTE disclosure ONLY — R0 NOT_RUN (D2 skipped per §3b)",
    "52W-HIGH": "expected-DOA: the 52-week-high proximity generic IS a listed §6 R0 shadow AND a candidate here — both roles hashed (§6). EX-ANTE disclosure ONLY — R0 NOT_RUN (D2 skipped per §3b)",
    "CLV-RANGE": "carries its own-class shadow in the inventory (R0S-CLV-20-ACCU, adapted from FOREX-NG7 §5 with the cross-plane adaptation disclosed); expected-DOA or survives only through construction distance (§6 R0 convention). EX-ANTE disclosure ONLY — R0 NOT_RUN (D2 skipped per §3b)",
    "DVOL-SHOCK": "expected-DOA: the dollar-volume-shock state IS a listed §6 R0 shadow (event-conditional, tagged). EX-ANTE disclosure ONLY — R0 NOT_RUN (D2 skipped per §3b)",
    "VOL-REGIME": "expected-DOA: realized-vol LEVEL + semivariance share states ARE listed §6 R0 shadows (event-conditional vol-tercile + vol-restricted shadows BINDING). EX-ANTE disclosure ONLY — R0 NOT_RUN (D2 skipped per §3b)",
}

# per-family ancestry-search basis: grep record against FAMILY_FAILURES.jsonl
# (patterns fixed ex ante; the builder runs the grep at build time and embeds
# the result verbatim — reproducible at the frozen base).
ANCESTRY_GREP = {
    "EVENT-UNWIND": ["event-unwind", "reclaim", "breakdown", "reversal"],
    "GAP": ["overnight", "gap"],
    "52W-HIGH": ["52w", "week-high", "52"],
    "CLV-RANGE": ["clv", "close-location"],
    "DVOL-SHOCK": ["dvol", "dollar-volume"],
    "VOL-REGIME": ["vol-regime", "tercile", "semivariance"],
}

ANCESTRY_BASIS_TEXT = {
    "EVENT-UNWIND": "no dead STOCKS break-reclaim/event-unwind class found; the reversal class carries dead crypto ancestry (CRYPTO-V8 H-XSECT-REVERSAL-v2, STOCKS-FREE-V3 SFV3-A5-IDIO-SHOCK-REVERSAL) and the C-REVERSAL-PLAIN kill is re-inherited BINDING at R4 — reversal-shadow territory per §6",
    "GAP": "no dead stocks overnight-gap class found in FAMILY_FAILURES.jsonl / the ledger (plan §6 verbatim ancestry-search basis for the GAP family); 'gap' hits are diagnostic-contract-gap usages, not strategy classes",
    "52W-HIGH": "no dead stocks 52-week-high class found; literal '52' hits are session-window counts, not strategy classes",
    "CLV-RANGE": "no dead stocks CLV / close-location-value class found; the class is a cross-plane adaptation of FOREX-NG7 §5 FNG7-A2-P1-ABSORB (forex lineage, disclosed)",
    "DVOL-SHOCK": "dead dollar-volume-shock ancestry EXISTS: CRYPTO-V9 XSECT-VOLSHK-S15 (SELECTION_REJECTION), CRYPTO-NG1 generic_dvol_shock ancestry kill, CRYPTO-V17 dvol_shock proxies, STOCKS-FREE-V4 SFV4-A5-H1-PARTICIPATION-SHIFT (control-out-earned SCIENTIFIC_REJECTION) — consistent with the expected-DOA disclosure",
    "VOL-REGIME": "no dead stocks vol-regime/tercile class found; the vol-shape neighbourhood has one dead stocks ancestor (STOCKS-FREE-V4 SFV4-A4-H1-SEMIVARIANCE-SHARE, SCIENTIFIC_REJECTION)",
}

# ---------------------------------------------------------------------------
# §6 R0 shadow inventory — enumerated EX ACTO from plan §6, hashed here.
# R0 is NOT_RUN this cycle (D2 skipped per §3b): the inventory is frozen and
# hashed for the record; NO rho is computed or claimed.
# ---------------------------------------------------------------------------

R0_INVENTORY = [
    {"shadow_id": "R0S-MOMENTUM-63S", "plan_item": "momentum_63s generic", "binding": False},
    {"shadow_id": "R0S-TSMOM-12-1MO", "plan_item": "12-1mo cross-sectional momentum", "binding": False},
    {"shadow_id": "R0S-STR-5D", "plan_item": "event-conditional 5d return short-term-reversal state", "binding": True},
    {"shadow_id": "R0S-STR-21D", "plan_item": "event-conditional 21d return short-term-reversal state", "binding": True},
    {"shadow_id": "R0S-STR-DDDEPTH", "plan_item": "drawdown-depth short-term-reversal state", "binding": True},
    {"shadow_id": "R0S-DVOL-SHOCK", "plan_item": "dollar-volume-shock state (event-conditional, tagged)", "binding": False},
    {"shadow_id": "R0S-RVOL-LEVEL", "plan_item": "realized-vol LEVEL state (event-conditional vol-tercile + vol-restricted shadows BINDING)", "binding": True},
    {"shadow_id": "R0S-SEMIVAR-SHARE", "plan_item": "semivariance share state (event-conditional vol-tercile + vol-restricted shadows BINDING)", "binding": True},
    {"shadow_id": "R0S-ROLLING-BETA", "plan_item": "rolling-beta state", "binding": False},
    {"shadow_id": "R0S-DGS10-LEVEL", "plan_item": "DGS10-LEVEL state", "binding": False,
     "disposition": "NG6 recorded DGS10 UNMEASURABLE on this plane; no DGS10 authority is pinned at P0 -> NOT_ADJUDICABLE, disclosed, never an inferred PASS; a P0 authority pass may activate it control-only (plan §6 disposition, pinned)"},
    {"shadow_id": "R0S-EVENT-CAL-GEOM", "plan_item": "event-calendar geometry (P-24 class)", "binding": False},
    {"shadow_id": "R0S-V13-DEATH-PROX", "plan_item": "V13 death-event proximity", "binding": False},
    {"shadow_id": "R0S-NG5-REL-BREADTH", "plan_item": "STOCKS-NG5 relative-breadth rotation state", "binding": False},
    {"shadow_id": "R0S-DIV-DECOMP-DIVERGENCE", "plan_item": "dividend-decomposition divergence (non-scored, fail-closed if distribution-dominated)", "binding": False},
    {"shadow_id": "R0S-52W-HIGH-PROX", "plan_item": "52-week-high proximity generic — this grid makes it a candidate AND a shadow for other families; both roles hashed", "binding": False},
    {"shadow_id": "R0S-OVERNIGHT-GAP", "plan_item": "overnight-gap state (prior-session close-to-open gap, fade/confirm direction classes — added for the GAP family)", "binding": False},
    {"shadow_id": "R0S-CLV-20-ACCU", "plan_item": "close-location-value 20-bar accumulation state (own-class shadow for CLV-RANGE, adapted from FOREX-NG7 §5 with the cross-plane adaptation disclosed)", "binding": False},
]

# BANNED performance-field KEYS for the --selfcheck key-scan (OUTCOME-BLIND law).
BANNED_KEY_SUBSTRINGS = [
    "pnl", "sharpe", "profit", "expectancy", "drawdown", "mdd", "alpha",
    "pbo", "pf", "return", "survivor_score", "hit_rate", "win_rate",
]


# ---------------------------------------------------------------------------
# build helpers
# ---------------------------------------------------------------------------


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def grep_ffl(patterns):
    """Deterministic grep record against FAMILY_FAILURES.jsonl (case-insensitive)."""
    lines = FFL.read_text(encoding="utf-8").splitlines()
    record = {}
    for pat in patterns:
        hits = []
        for i, line in enumerate(lines, start=1):
            if pat.lower() in line.lower():
                try:
                    obj = json.loads(line)
                    ident = f"{obj.get('cycle_id', '?')}:{obj.get('family_id', '?')}"
                except json.JSONDecodeError:
                    ident = "<unparsed-line>"
                hits.append({"line": i, "cycle:family": ident})
        record[pat] = {"n_hits": len(hits), "hits": hits}
    return record


def generate_configs(census_cfg_list):
    """Generate the 47 configs from the frozen §5 grids; cross-check IDs
    against the P0 census target list (INPUT_MISMATCH on any drift)."""
    by_id = {c["config_id"]: c for c in census_cfg_list}
    out = []
    for fam in sorted(FAMILIES):
        spec = FAMILIES[fam]
        for combo in spec["combos"]:
            cid = spec["cfg_id"](combo)
            if cid not in by_id:
                raise BuildError(f"INPUT_MISMATCH: generated config {cid} absent from p0/census_configs.json")
            src = by_id[cid]
            if src["family"] != fam:
                raise BuildError(f"INPUT_MISMATCH: family drift for {cid}")
            params = spec["params"](combo)
            if src["params"] != params:
                raise BuildError(f"INPUT_MISMATCH: params drift for {cid}: {src['params']} != {params}")
            sign = spec["sign_frozen"]
            if isinstance(sign, dict):
                dkey = combo[1]
                sign = sign[dkey]
            out.append({
                "config_id": cid,
                "family": fam,
                "params": params,
                "construction_verbatim": src["state"],
                "construction_source": "p0/census_configs.json state field (frozen at P0, gate F8) — plan §5 grid",
                "components": spec["components"],
                "sign_frozen_from_construction": sign,
                "warmup_need_sessions": src["warmup_need"],
                "first_eligible_decision": (
                    f"no earlier than the {src['warmup_need'] + 1}-th served session of the name "
                    f"(0-based index >= {src['warmup_need']}); base warmup law (§4 F4): 252 served "
                    f"sessions, first eligible decision never earlier than the 253rd served session; "
                    f"a longer construction need wins; warmup attrition censused (F4)"
                ),
            })
    return out, by_id


def build_family_blocks(rows_by_cfg):
    """Family blocks: totals per fold (fired + bookable) and the §3b selection
    tier basis (sum of fired decisions over the most recent fold F3)."""
    fams = {}
    for fam in sorted(FAMILIES):
        per_fold = {f: {"fired": 0, "bookable_fired": 0} for f in FOLDS}
        cfgs = [cid for cid in rows_by_cfg if rows_by_cfg[cid]["F1"]["family"] == fam]
        for cid in cfgs:
            for f in FOLDS:
                row = rows_by_cfg[cid][f]
                per_fold[f]["fired"] += row["fired"]
                per_fold[f]["bookable_fired"] += row["bookable_fired"]
        fams[fam] = {
            "n_configs": len(cfgs),
            "grid_text": FAMILIES[fam]["grid_text"],
            "fired_totals_per_fold": {f: per_fold[f]["fired"] for f in FOLDS},
            "bookable_fired_totals_per_fold": {f: per_fold[f]["bookable_fired"] for f in FOLDS},
            "selection_tier_basis_f3_fired_total": per_fold[SELECTION_FOLD]["fired"],
            "c_complement": C_COMPLEMENT[fam],
            "r5_component_only": R5_COMPONENT_ONLY[fam],
            "r5_adjudicable": True,
            "expected_doa": EXPECTED_DOA[fam],
            "ancestry_search_basis": {
                "source": "research/wayfinder/FAMILY_FAILURES.jsonl (grep record, read-only; ledger corroboration via HYPOTHESIS_LEDGER.md rows quoted in the hits)",
                "grep": grep_ffl(ANCESTRY_GREP[fam]),
                "basis": ANCESTRY_BASIS_TEXT[fam],
            },
        }
        if len(cfgs) != FAMILY_COUNTS_PLAN[fam]:
            raise BuildError(f"INPUT_MISMATCH: family {fam} count {len(cfgs)} != plan count {FAMILY_COUNTS_PLAN[fam]}")
    return fams


def selection_tier(rows_by_cfg, fam_blocks):
    """§3b selection tier: (i) families DESCENDING by P0 fired-population
    census (F3 sum of fired), ties lexicographic; (ii) within family, configs
    DESCENDING by F3 fired, tie-break lexicographic config ID; (iii)
    family-stratified round-robin, <= 2 cells/family, until 3 cells."""
    fam_order = sorted(
        fam_blocks,
        key=lambda f: (-fam_blocks[f]["selection_tier_basis_f3_fired_total"], f),
    )
    cfg_order = {}
    for fam in fam_order:
        cfg_order[fam] = [
            cid for cid in sorted(
                (cid for cid in rows_by_cfg if rows_by_cfg[cid]["F1"]["family"] == fam),
                key=lambda c: (-rows_by_cfg[c][SELECTION_FOLD]["fired"], c),
            )
        ]
    # round-robin: one config per family per round, max 2 per family, 3 cells
    picks, taken = [], {f: 0 for f in fam_order}
    rnd = 0
    while len(picks) < 3:
        picked_this_round = 0
        rnd += 1
        for fam in fam_order:
            if len(picks) >= 3:
                break
            if taken[fam] >= 2 or taken[fam] >= len(cfg_order[fam]):
                continue
            picks.append({"round": rnd, "family": fam,
                          "config_id": cfg_order[fam][taken[fam]]})
            taken[fam] += 1
            picked_this_round += 1
        if picked_this_round == 0:
            break  # unreachable with 6 families; defensive
    return {
        "amendment_3b_verbatim": (
            "Owner amendment §3b (2026-09-17 #2): the D2 phase is NOT dispatched; the R0 "
            "ancestry battery is NOT MEASURED (NOT_RUN — never an inferred PASS); §5 "
            "selection tier (i) is replaced by the P0 fired-population census and tier (ii) "
            "loses its W_c term (both non-performance, outcome-blind properties retained); "
            "T_F/W_c are NOT COMPUTED (never an inferred PASS). The fired census and "
            "feasibility floors are measured at P0 as a pure data census (fired counts only "
            "— no candidate returns, no PnL, no PF); P-20 books-distinct at S is UNCHANGED."
        ),
        "tier_i": "families DESCENDING by P0 fired-population census (family-level sum of fired decisions over the most recent fold, F3); ties break by lexicographic family name",
        "tier_ii": "within a family, configurations DESCENDING by P0 fired-population census (config-level, most recent fold F3), tie-break lexicographic config ID",
        "tier_iii": "selection is FAMILY-STRATIFIED round-robin over the tier-ordered families — one configuration per family per round, at most 2 scored cells per family, until 3 cells are filled (breadth is the point)",
        "p20_books_distinct_at_S": (
            "P-20 books-distinct at S: a candidate whose pooled |rho| vs any higher-ranked "
            "already-selected candidate exceeds 0.98 is SELF-SUBSUMED, skipped, and the next "
            "candidate by the frozen order is taken; an unmeasurable pairwise rho makes the "
            "slot NOT_ADJUDICABLE, fail-closed — never an inferred PASS. NOT COMPUTED AT D1 "
            "(adjudicated at S; no rho exists in this manifest)."
        ),
        "tf_wc_status": "T_F/W_c NOT COMPUTED — D2 skipped per §3b; never an inferred PASS",
        "selection_fold": SELECTION_FOLD,
        "family_ranking_f3_fired_desc": fam_order,
        "family_ranking_values_f3_fired": {
            f: fam_blocks[f]["selection_tier_basis_f3_fired_total"] for f in fam_order
        },
        "per_family_config_order_f3_fired_desc": cfg_order,
        "round_robin_census_order": picks,
        "round_robin_note": (
            "deterministic census-based ORDER (round 1 fills all 3 cells, one per family, "
            "max 2/family satisfied); this is an ORDER, not a selection — pending P-20 "
            "books-distinct at S and the exact-arm hash freeze"
        ),
        "outcome_blindness": (
            "NO return, expectancy, PF, Sharpe or any performance statistic enters this "
            "tier; the ranking consumes ONLY P0 fired counts (§5 ban carried verbatim; a "
            "performance-based narrowing is a BLOCKED_METHOD_CONTRACT incident)"
        ),
    }


def sparse_book_convention():
    return {
        "verbatim_plan_§5": (
            "SPARSE-BOOK CONVENTION (pinned): the primary pooled_rho aligns the candidate's "
            "daily book-return series (zero on non-fired days) against each shadow's daily "
            "series over the full S0 window; ADDITIONALLY, for any family whose fired-day "
            "share is below 30%, a fired-day-conditioned rho against the shadow's "
            "fired-day returns is computed (A4 sparse-book lesson: cohort-wide rho "
            "understates a sparse event book); the veto statistic consumes the MAX of the "
            "two |rho| values per shadow — fail-closed direction; the convention is a "
            "required D1-manifest field."
        ),
        "cumulative_binding_note_verbatim": (
            "The §6 event-conditional BINDING shadows are measured for every event-type "
            "family REGARDLESS of fired-day share; the §5 30% sparse-book trigger ADDS the "
            "fired-day-conditioned rho on top — both apply cumulatively, neither "
            "substitutes for the other."
        ),
        "status": (
            "carried for the record as a REQUIRED D1 field; R0 measurement is NOT_RUN this "
            "cycle (D2 skipped per §3b) — no rho of either kind is computed here"
        ),
        "trigger_threshold_fired_day_share": 0.30,
    }


def r0_block():
    inv = sorted(R0_INVENTORY, key=lambda s: s["shadow_id"])
    return {
        "r0_status": "NOT_RUN",
        "law": (
            "the R0 ancestry battery is NOT MEASURED this cycle (D2 skipped by owner "
            "amendment §3b) — NOT_RUN, never an inferred PASS; the inventory below is "
            "frozen and hashed for the record (plan §5 requires the R0 shadow "
            "inventory's own hash in this manifest); NO rho is computed or claimed"
        ),
        "floor_standing": 0.20,
        "floor_owner_relaxed": 0.30,
        "veto_law": "veto is STRICTLY > 0.30 (equality passes), measured to 6 decimal places; the 0.20 standing value is printed alongside (§6 R0)",
        "inventory": inv,
        "inventory_hash": canon_sha256(inv),
        "inventory_hash_convention": "sha256 of the canonical JSON (sort_keys, compact separators, UTF-8) of the sorted inventory list above",
        "own_family_convention": (
            "every configuration is tested against the FULL frozen inventory INCLUDING its "
            "own family's shadow class — no exemptions; the own-class rho is computed and "
            "REPORTED separately as disclosure, never carved out (§6 R0 conventions)"
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selfcheck", action="store_true",
                    help="build, then verify the frozen manifest in place")
    args = ap.parse_args()

    # --- load committed p0 artifacts (read-only) ---------------------------
    paths = {
        "p0_gate": P0 / "p0_gate.json",
        "p0_census": P0 / "p0_census.json",
        "census_configs": P0 / "census_configs.json",
        "fold_freeze": P0 / "fold_freeze.json",
        "cost_bands": P0 / "cost_bands.json",
        "clock_contract": P0 / "clock_contract.json",
    }
    src = {k: load_json(p) for k, p in paths.items()}
    src_sha = {k: sha256_file(p) for k, p in paths.items()}

    gate = src["p0_gate"]
    if gate.get("overall_verdict") != "PASS":
        raise BuildError(f"INPUT_MISMATCH: p0_gate overall_verdict {gate.get('overall_verdict')!r} != PASS")
    census = src["p0_census"]
    cc = src["census_configs"]

    # --- census rows: per-config per-fold, verbatim ------------------------
    rows_by_cfg = {}
    for row in census["per_config_per_fold"]:
        rows_by_cfg.setdefault(row["config_id"], {})[row["fold"]] = row

    # --- configs from the frozen §5 grids ----------------------------------
    configs, _cc_by_id = generate_configs(cc["configs"])
    if len(configs) != 47:
        raise BuildError(f"INPUT_MISMATCH: {len(configs)} configs != 47")
    for c in configs:
        folds_present = sorted(rows_by_cfg.get(c["config_id"], {}))
        if folds_present != sorted(FOLDS):
            raise BuildError(f"INPUT_MISMATCH: census folds {folds_present} for {c['config_id']}")
        c["p0_census_per_fold_verbatim"] = rows_by_cfg[c["config_id"]]

    fam_blocks = build_family_blocks(rows_by_cfg)
    tier = selection_tier(rows_by_cfg, fam_blocks)

    ff = src["fold_freeze"]
    cb = src["cost_bands"]
    ck = src["clock_contract"]

    manifest = {
        "schema": SCHEMA,
        "cycle_id": CYCLE_ID,
        "task_id": TASK_ID,
        "plan": PLAN,
        "phase": "D1 — frozen search-space manifest (plan §5; the cycle's A2-equivalent dossier IS this manifest)",
        "base_sha": BASE_SHA,
        "authority": {
            "plan_section": "plans/PLAN_stocks_search_v1.md §5 as amended by §3b (owner amendment 2026-09-17 #2)",
            "p0_gate_schema": gate["schema"],
            "p0_gate_overall_verdict": gate["overall_verdict"],
            "m0_lineage": "M0 PASS re-inherited BYTE-EXACT (commit ce057f39) — precondition for D1 (plan §9)",
            "source_artifacts": {
                k: {"path": str(paths[k]).replace(str(ROOT) + "/", ""), "sha256": src_sha[k]}
                for k in paths
            },
        },
        "outcome_blindness_law": (
            "OUTCOME-BLIND freeze: NO returns, PnL, PF, Sharpe, drawdown, expectancy or "
            "any performance statistic may be computed for ANY configuration before the S "
            "freeze (plan §5; the D2 ancestry rho, feasibility floors and fired-population "
            "censuses are NON-SCORED diagnostics explicitly carved out of this ban — and D2 "
            "is itself SKIPPED this cycle per §3b). A key-scan in --selfcheck bans "
            "performance-field keys."
        ),
        "grid": {
            "cap": GRID_CAP,
            "n_configs": len(configs),
            "family_counts": {f: FAMILY_COUNTS_PLAN[f] for f in sorted(FAMILY_COUNTS_PLAN)},
            "id_law": "SSS-<FAMILY>-<PARAMKEY>, stable, lexicographic (config list is stored sorted by config_id)",
            "long_only_law": "no short leg (no borrow-cost authority — FOREX-NG6 F4 class); direction falsification by R1 + inversion-SUBSTITUTE controls, honestly labelled",
            "within_cap": len(configs) <= GRID_CAP,
        },
        "amendment_3b": {
            "r0_status": "NOT_RUN",
            "d2_status": "SKIPPED_BY_OWNER_AMENDMENT_3B",
            "p0_gate_amendment_verbatim": gate["amendment_3b"],
            "r0_not_run_note": (
                "R0_NOT_RUN: the D2 phase is NOT dispatched in this cycle; the R0 ancestry "
                "battery is NOT MEASURED (NOT_RUN — never an inferred PASS); the §9 chain's "
                "D2 row reads SKIPPED; terminal survivor outcome names and §10 language "
                "carry R0_NOT_RUN alongside the standing 0.20/0.30 disclosure (§3b verbatim "
                "effect)"
            ),
        },
        "relaxation_axes_verbatim": {
            "r0_ancestry_veto_floor": {"standing": "pooled |rho| <= 0.20", "this_program": "<= 0.30 (owner)"},
            "dsr_deflation_set_N": {"standing": "program-cumulative ~260 (P-9)", "this_program": "frozen grid size (<= 120, §5; measured 47)"},
            "dsr_significance_level": {"standing": "alpha 0.05", "this_program": "alpha 0.10"},
            "search_breadth": {"standing": "1 family + 1 neighbour", "this_program": "<= 120 enumerated configurations (measured 47)"},
            "print_law": "every result artifact prints BOTH the standing and relaxed values (§3)",
        },
        "representation_and_conventions": {
            "p12_representation": cc["conventions"]["representation"],
            "percentile_method": cc["conventions"]["percentile_method"],
            "percentile_interpolation_required_field": "linear",
            "percentile_interpolation_note": "plan §5 required manifest field: 'the percentile interpolation method (linear)' — carried verbatim as 'linear'",
            "quantile_use_sites": [
                "GAP: threshold percentile of the trailing 252-session gap distribution",
                "VOL-REGIME: 1/3 and 2/3 tercile boundaries over the trailing 252-session sigma window",
            ],
            "warmup_law": cc["conventions"]["warmup_law"],
            "warmup_first_eligible": "252/253 law: 252 served sessions warmup; first eligible decision no earlier than the 253rd served session per name; longer construction need wins (VOL-REGIME L21: 272, L63: 314 — per-config warmup_need_sessions)",
            "zero_range_law_plan_§5": "a bar with high == low makes RANGE (component 3) and CLV undefined — the state is NOT FIRED on that bar (fail-closed, never imputed); degenerate bars are counted in a P0 census",
            "zero_range_law_census": census["zero_range_law"],
            "hold_invariance": cc["conventions"]["hold_invariance"],
            "bookability_floors": cc["conventions"]["bookability_floors"],
            "bookability_floors_note": "$1.00 adjusted close / $2M trailing 60-session median dollar volume, declared ex ante (§4 F4); SUBFLOOR/UNRESOLVED law in cost_bands.json",
            "decision_clock": ck,
            "sparse_book_convention": sparse_book_convention(),
        },
        "folds": {
            "window": ff["window"],
            "boundaries": ff["boundaries"],
            "folds": ff["folds"],
            "rule": ff["rule"],
            "regime_law": ff["regime_law"],
            "f8_floor": ff["q6_floor"],
            "f8_floor_law": ">= 30 bookable fired decisions per fold, fail-closed kill recorded, never silently dropped; measured at P0: ALL 141 cells pass (min cell 5,729, EVENT-UNWIND)",
            "sha256_fold_freeze": src_sha["fold_freeze"],
        },
        "costs": {
            "schedule": cb["schedule"],
            "band_keys": cb["band_keys"],
            "worst_case_ceiling_bps_round_trip": 100,
            "worst_case_ceiling_derivation": "25 bps x 2 fills x 2.0 stress = 100 bps/round trip (P-21)",
            "stress_tier": "STRESS TIER 2.0 PRIMARY",
            "law_verbatim": cb["law"],
            "subfloor_law_verbatim": cb["subfloor_law"],
            "sha256_cost_bands": src_sha["cost_bands"],
        },
        "controls_identifiability": {
            "per_state_per_fold_floor": 10,
            "per_state_per_fold_floor_law": (
                "PINNED at D1: any control or state book (C-COMPLEMENT, R5 component-only, "
                "C-CAL-HIST bucket, any R0 shadow book) with fewer than 10 fired decisions "
                "in a fold is NOT_ADJUDICABLE for that fold — disclosed, never silently "
                "skipped, never an inferred PASS (§6 disposition rule, numeric floor pinned "
                "at D1)"
            ),
            "c_cal_hist_bucket_rule_verbatim": (
                "C-CAL-HIST: deterministic calendar book matched to the fired-date "
                "distribution on day-of-week x month-position buckets (bucket = (weekday, "
                "{first-half, second-half of month})); deterministic rule declared ex ante "
                "BEFORE any measurement; minimum twin population 10 fired decisions per "
                "bucket per fold — a sub-floor bucket is NOT_ADJUDICABLE and disclosed, "
                "never silently skipped; must NOT out-earn the candidate (the R6 clock rule "
                "extends to it)"
            ),
            "unpopulated_control_law": "a control that is unpopulated or has an invalid null is NOT_ADJUDICABLE, never silently skipped (§6)",
        },
        "c_complement_and_r5_law": {
            "c_complement_law": "the family's own causal placebo — declared ex ante per family here, consumes no scored slot (§6)",
            "r5_law": (
                "component-only book: the conditioning filter applied WITHOUT the "
                "directional/trigger component, declared per family here; reproduces >= 0.5x "
                "same-sign in >= 2/3 folds -> REJECT; where a family admits no such analog, "
                "R5 is NOT_ADJUDICABLE for that family, disclosed, never an inferred PASS "
                "(§6 R5). In this grid every family admits an analog — the NOT_ADJUDICABLE "
                "branch is unused (disclosed)."
            ),
        },
        "families": fam_blocks,
        "configs": sorted(configs, key=lambda c: c["config_id"]),
        "selection_tier_3b": tier,
        "r0_shadow_inventory": r0_block(),
        "s0_window": {
            "start": ff["window"][0],
            "end": ff["window"][1],
            "source": "p0/fold_freeze.json window (the S0 window is the P0-frozen full window; folds F1/F2/F3 partition it; the full-S0-window daily series of the sparse-book convention is defined over this extent)",
            "sha256_fold_freeze": src_sha["fold_freeze"],
        },
        "relaxation_disclosure_verbatim": gate["relaxation_disclosure"],
        "result_language_law_§10": (
            "any result language must carry verbatim: \"accepted under owner-relaxed "
            "acceptance battery (R0 0.30 / DSR alpha 0.10 at N = grid) | PBO NOT_RUN "
            "fail-closed (<=3 cells, d0992d17 class) | R0 NOT_RUN (D2 skipped by owner "
            "amendment §3b)\""
        ),
        "determinism": {
            "law": "this manifest is produced by build_d1_manifest.py deterministically from the committed p0 artifacts listed in authority.source_artifacts; no clock, no randomness; a byte-identical rebuild from the same base reproduces the same self_sha256",
            "hash_convention": (
                "self_sha256 = sha256 of the canonical JSON (UTF-8, sort_keys=true, "
                "separators ',' ':', ensure_ascii=false) of this manifest computed with the "
                "field self_sha256 set to the EMPTY STRING \"\" (empty-field convention); "
                "the committed file is pretty-printed — the hash binds content, not "
                "formatting"
            ),
        },
        "self_sha256": "",
    }
    manifest["self_sha256"] = canon_sha256(manifest)

    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {MANIFEST_PATH}")
    print(f"self_sha256 = {manifest['self_sha256']}")

    if args.selfcheck:
        return selfcheck(src, src_sha)
    return 0


# ---------------------------------------------------------------------------
# selfcheck
# ---------------------------------------------------------------------------


def iter_keys(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield f"{prefix}.{k}" if prefix else k
            yield from iter_keys(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_keys(v, prefix)


def selfcheck(src, src_sha) -> int:
    m = load_json(MANIFEST_PATH)
    checks = []

    def check(name, ok, detail=""):
        checks.append((name, bool(ok), detail))
        if not ok:
            print(f"FAIL  {name}  {detail}")

    # 1. parses — implicit in load_json above
    check("manifest_parses", True)

    # 2. 47 configs
    cfgs = m["configs"]
    check("n_configs_is_47", len(cfgs) == 47, f"got {len(cfgs)}")

    # 3. IDs unique + lexicographic
    ids = [c["config_id"] for c in cfgs]
    check("config_ids_unique", len(set(ids)) == len(ids))
    check("config_ids_lexicographic", ids == sorted(ids))
    check("ids_match_sss_pattern", all(i.startswith("SSS-") for i in ids))

    # 4. counts match p0_census.json (every copied field, every config, every fold)
    census_rows = {}
    for row in src["p0_census"]["per_config_per_fold"]:
        census_rows.setdefault(row["config_id"], {})[row["fold"]] = row
    ok_counts, bad = True, ""
    for c in cfgs:
        for f in FOLDS:
            if c["p0_census_per_fold_verbatim"][f] != census_rows[c["config_id"]][f]:
                ok_counts, bad = False, f"{c['config_id']}/{f}"
                break
    check("census_rows_match_p0_census", ok_counts and
          len(census_rows) == 47 and
          src["p0_census"]["n_configs"] == 47, bad)
    check("census_n_configs_field", m["grid"]["n_configs"] == src["p0_census"]["n_configs"] == 47)
    check("family_counts_match_plan_grid", m["grid"]["family_counts"] == {
        "52W-HIGH": 6, "CLV-RANGE": 4, "DVOL-SHOCK": 8,
        "EVENT-UNWIND": 9, "GAP": 12, "VOL-REGIME": 8})

    # 5. family totals match a fresh recomputation
    fam_f3 = {}
    for cid, folds in census_rows.items():
        fam = folds["F3"]["family"]
        fam_f3[fam] = fam_f3.get(fam, 0) + folds["F3"]["fired"]
    ok_tot = all(
        m["families"][f]["selection_tier_basis_f3_fired_total"] == fam_f3.get(f, 0)
        for f in m["families"]
    )
    check("family_totals_match_recompute", ok_tot)
    order = sorted(fam_f3, key=lambda f: (-fam_f3[f], f))
    check("family_ranking_desc_by_f3_fired",
          m["selection_tier_3b"]["family_ranking_f3_fired_desc"] == order)

    # 6. floors pinned
    ci = m["controls_identifiability"]
    check("per_state_per_fold_floor_pinned_10", ci["per_state_per_fold_floor"] == 10)
    check("c_cal_hist_min_10_per_bucket_per_fold_pinned",
          "minimum twin population 10 fired decisions per bucket per fold"
          in ci["c_cal_hist_bucket_rule_verbatim"])
    check("f8_floor_pinned_30", m["folds"]["f8_floor"]["floor"] == 30)

    # 7. pins verbatim vs source artifacts
    check("cost_bands_pin_verbatim",
          m["costs"]["schedule"] == src["cost_bands"]["schedule"] and
          m["costs"]["band_keys"] == src["cost_bands"]["band_keys"] and
          m["costs"]["law_verbatim"] == src["cost_bands"]["law"] and
          m["costs"]["worst_case_ceiling_bps_round_trip"] == 100)
    sched = m["costs"]["schedule"]
    check("cost_band_values_10_15_25", sched["band_bps"] == {"A": 10, "B": 15, "C": 25} and
          sched["bands_def"] == {"A": 50000000.0, "B": 10000000.0, "C": 2000000.0})
    check("clock_contract_pin_verbatim", m["representation_and_conventions"]["decision_clock"] == src["clock_contract"])
    check("fold_boundaries_pin_verbatim",
          m["folds"]["window"] == src["fold_freeze"]["window"] and
          m["folds"]["boundaries"] == src["fold_freeze"]["boundaries"] and
          m["folds"]["folds"] == src["fold_freeze"]["folds"])
    check("sparse_book_convention_present",
          m["representation_and_conventions"]["sparse_book_convention"]["trigger_threshold_fired_day_share"] == 0.30 and
          "MAX of the two |rho| values per shadow" in
          m["representation_and_conventions"]["sparse_book_convention"]["verbatim_plan_§5"])
    check("amendment_3b_r0_not_run_present",
          m["amendment_3b"]["r0_status"] == "NOT_RUN" and
          m["amendment_3b"]["d2_status"] == "SKIPPED_BY_OWNER_AMENDMENT_3B" and
          m["amendment_3b"]["p0_gate_amendment_verbatim"] == src["p0_gate"]["amendment_3b"])
    check("tf_wc_not_computed_disclosed",
          "NOT COMPUTED" in m["selection_tier_3b"]["tf_wc_status"])
    check("r0_inventory_hash_present_and_verifies",
          m["r0_shadow_inventory"]["inventory_hash"] ==
          canon_sha256(m["r0_shadow_inventory"]["inventory"]))
    check("s0_window_pin", m["s0_window"]["start"] == src["fold_freeze"]["window"][0] and
          m["s0_window"]["end"] == src["fold_freeze"]["window"][1])
    check("percentile_linear_pin",
          m["representation_and_conventions"]["percentile_method"] == "linear" and
          m["representation_and_conventions"]["percentile_interpolation_required_field"] == "linear")
    check("warmup_252_253_pin",
          "252 served sessions" in m["representation_and_conventions"]["warmup_law"] and
          "253rd served session" in m["representation_and_conventions"]["warmup_first_eligible"])
    check("construction_verbatim_matches_census_configs",
          all(c["construction_verbatim"] == next(
              s["state"] for s in src["census_configs"]["configs"]
              if s["config_id"] == c["config_id"]) for c in cfgs))
    check("signs_frozen_on_every_config",
          all(c.get("sign_frozen_from_construction") for c in cfgs))
    check("expected_doa_on_every_family",
          all("expected_doa" in m["families"][f] for f in m["families"]) and len(m["families"]) == 6)
    check("ancestry_basis_on_every_family",
          all("grep" in m["families"][f]["ancestry_search_basis"] and
              "basis" in m["families"][f]["ancestry_search_basis"] for f in m["families"]))
    check("zero_range_law_carried",
          m["representation_and_conventions"]["zero_range_law_census"] == src["p0_census"]["zero_range_law"])
    check("long_only_everywhere", m["grid"]["long_only_law"] != "" and
          all("long" in c["sign_frozen_from_construction"].lower() for c in cfgs))
    check("selection_round_robin_shape",
          len(m["selection_tier_3b"]["round_robin_census_order"]) == 3 and
          len({p["family"] for p in m["selection_tier_3b"]["round_robin_census_order"]}) == 3)
    check("grid_cap_within_120", m["grid"]["n_configs"] <= m["grid"]["cap"] == 120)

    # 8. OUTCOME-BLIND: no performance-field keys anywhere
    banned_hits = []
    for key in iter_keys(m):
        lk = key.lower()
        for b in BANNED_KEY_SUBSTRINGS:
            if b in lk:
                banned_hits.append((key, b))
    check("no_performance_field_keys", not banned_hits, str(banned_hits[:5]))

    # 9. self-sha verifies (empty-field convention)
    claimed = m["self_sha256"]
    m["self_sha256"] = ""
    recomputed = canon_sha256(m)
    check("self_sha256_verifies", claimed == recomputed, f"claimed {claimed} != {recomputed}")

    failures = [c for c in checks if not c[1]]
    print(f"selfcheck: {len(checks) - len(failures)}/{len(checks)} checks PASS")
    for name, _, _ in failures:
        print(f"  FAILED: {name}")
    return 0 if not failures else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BuildError as e:
        print(f"INPUT_MISMATCH: {e}", file=sys.stderr)
        sys.exit(2)
