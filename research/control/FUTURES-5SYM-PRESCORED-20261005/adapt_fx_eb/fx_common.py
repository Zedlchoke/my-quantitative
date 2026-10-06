"""fx_common — shared deterministic machinery for the ADAPT-FXEB lane (6E + 6B).

Round FUTURES-5SYM-PRESCORED-20261005, wave-3, lane ADAPT-FXEB. PREP-only.
PROPOSED / CONDITIONAL-ON-PB2-LIFT throughout — PB2 HOLD stands; nothing here
is an approved freeze; real-data execution is NOT_RUN.

BINDING LAWS CARRIED (every constant cites its committed source):
  - fx_eb/SPEC_6E.md s.1/s.3/s.4/s.5/s.6/s.7  (6E identity/tick, session+DST,
    calendar/roll, event PIT, cost, folds/warmup)
  - fx_eb/SPEC_6B.md s.1/s.3/s.4/s.5/s.6/s.7  (6B same; holiday grid 0/42
    structural absence; MPC minute-720 London anchor; 6B not-obtained quarters)
  - fx_eb/CALENDAR_PIT_POLICY_6E_6B.md s.1-s.5 (expiry tables, roll law-pending
    k=5+cease-guard, holiday fail-closed lists, D12 posture, vintage law)
  - fx_eb/COST_CONTRACT_6E_6B.md s.1-s.5      (fee layer, spread proxy,
    slippage tiers, RT ladders, dead-spot 3.0 bp fence, MODELED/UNDER REVIEW)
  - fx_eb/IDENTITY_BUDGET_6E_6B.md s.1-s.7    (CONV-D per-symbol decomposition,
    exact DRAFT ID strings, signature list, gates)
  - fx_eb/GAPS_AND_DECISIONS_6E_6B.md s.(b)   (owner slots P5-OD1..OD11 ->
    namespaced here as P5-FXEB-OD1..OD11, fail-closed while unsigned)
  - exec/symbol_contracts.json rows "6E"/"6B" (tick/tick_value/multiplier/quote
    direction; session_mask_spec.rth "07:20-14:00" is PLACEHOLDER-PENDING —
    CONTRACTS handoff F2 — never inherited; session law of record is the
    measured Globex 17:00->16:00 CT template, SPEC_6E s.3 / SPEC_6B s.3)
  - exec/RUNNER_SPEC_V2.md s.6                (ledger row envelope — consumed
    read-only for the trade-journal payload shape)
  - M2c erratum (FXEB_K6_GATES.md finding 1, binding on any future freeze):
    the family-doc baseline 0.3778% reopen-gap std was the 08:30-CT RTH-open
    gap; the true 17:00-CT reopen gaps are 2.3-5x smaller (ratio ~0.16).

OUTCOME-BLIND LAW: adapters compute SIGNALS and intended ORDER INTENT on
SYNTHETIC fixtures only. Any panel whose provenance is not SYNTHETIC raises
RefusedPendingOwnerDecision("P5-FXEB-OD1") — real-data adapter execution =
NOT_RUN (gated on PB2 lift + ceiling + fees + registration).

All functions are pure and deterministic: no randomness, no wall-clock reads,
no I/O beyond an optional read of the committed symbol_contracts.json.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

CT = ZoneInfo("America/Chicago")
LONDON = ZoneInfo("Europe/London")

# ------------------------------------------------------------------ symbols
# exec/symbol_contracts.json rows + SPEC_6E s.1 / SPEC_6B s.1 (identity tables).
# Fixed-point int-nano ticks from FXEB_K6_GATES s.0.5/s.4 (tick constancy
# CONSTANT at the 2020-11-23 boundary, both symbols).
SYMBOL_LAW: dict[str, dict] = {
    "6E": {
        "tick": 0.00005,                 # 0.00005 = $6.25/tick (SPEC_6E s.1)
        "tick_value_usd": 6.25,
        "multiplier": 125000,            # EUR 125,000 vs USD
        "quote": "USD per EUR",
        "base_ccy": "EUR",
        "long_base_sign": 1,
        "int_nano_tick": 50000,
        "primary_overlay": "FOMC",       # FX-F2 6E anchor: 13:00 CT, minute 780
        "secondary_overlay": "ECB",      # 14:15 CET/CEST decision stratum (x1.73)
        "f2_day_sets": ("fomc_dates", "ecb_dates"),
        "rt_bp_band": (3.6, 6.3),        # MODELED RT ladder (COST_CONTRACT s.3.1)
        "notional_band": (119400.0, 155363.0),   # px 0.9552-1.2429 measured
        "holiday_grid": "34/42 OBTAINED; fail-closed exclusion lists binding "
                        "(CALENDAR_PIT_POLICY s.3.1)",
        "not_obtained_quarters": ["2026-Q3", "2026-Q4"],  # ECU26/ECZ26 proven-absent
        "census_triggers": 1362,         # court census >=500 PASS (K6GATE M1)
        "mde_f1_bp": 3.5,                # power honesty (SPEC_6E s.9)
        "roll_switches": 27, "roll_lead_days": "13-19 where cells obtained",
        "rmm_mode_split": {"abrupt": 22, "gradual": 5},   # k6gate mode ledger
    },
    "6B": {
        "tick": 0.0001,                  # 0.0001 = $6.25/tick (SPEC_6B s.1)
        "tick_value_usd": 6.25,
        "multiplier": 62500,             # GBP 62,500 vs USD
        "quote": "USD per GBP",
        "base_ccy": "GBP",
        "long_base_sign": 1,
        "int_nano_tick": 100000,
        "primary_overlay": "MPC",        # FX-F2 6B anchor: 12:00 London, minute 720
        "secondary_overlay": "FOMC",     # 13:00 CT stratum on 6B (x9.5)
        "f2_day_sets": ("mpc_dates", "fomc_dates"),
        "rt_bp_band": (6.3, 11.2),       # MODELED RT ladder (COST_CONTRACT s.3.2)
        "notional_band": (64950.0, 88781.0),     # px 1.0392-1.4205; bp at 81250 ref
        "holiday_grid": "0/42 NOT_OBTAINED — documented structural absence; NO "
                        "holiday exclusion implementable; hole declared on every "
                        "6B result (CALENDAR_PIT_POLICY s.3.2)",
        "not_obtained_quarters": ["2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4",
                                  "2024-Q1", "2024-Q2"],  # BPH23..BPM24 structural
        "census_triggers": 1342,
        "mde_f1_bp": 4.2,                # 6B MDE sits BELOW its own cost floor
        "roll_switches": 27, "roll_lead_days": "17d 2024Q4->2026Q3; 14d into 2026Q4",
        "rmm_mode_split": {"abrupt": 23, "gradual": 4},
    },
}

SYMBOLS = ("6E", "6B")


def quarter_of(d: str | date) -> str:
    ds = _as_date(d)
    return f"{ds.year}-Q{(ds.month - 1) // 3 + 1}"


# ---------------------------------------------------------------- session law
# SPEC_6E s.3 / SPEC_6B s.3: Globex ~23h; session = 17:00 CT (D-1) -> 16:00 CT
# (D); 60-min maintenance break 16:00-17:00 CT. 348/1746 Sunday-evening opens.
# No verbatim weekly-hours spec capture exists for either symbol (structural
# NOT_OBTAINED) — session law rests on the measured template + deviation grids.
SESSION_OPEN_MIN = 17 * 60          # 17:00 CT (D-1)
SESSION_CLOSE_MIN = 16 * 60         # 16:00 CT (D)
MAINT_BREAK_MIN = (16 * 60, 17 * 60)
# session_date is consumed as carried panel data and NEVER re-derived from ts
# (DST-fall-back absolute-24h quirk preserved as measured).

# Held-contract-only law (SPEC_6E s.2 / SPEC_6B s.2): all masks/fills consume
# the held chain only; mixing contracts inside sessions inflates dispersion.

# ------------------------------------------------------------------ fold law
# SPEC_6E s.7 / SPEC_6B s.7 (DRAFT, binding only post-lift; re-fixed at any
# future registration freeze). S1 = SEALED_UNTOUCHED.
FOLDS: dict[str, tuple[str, str]] = {
    "F1": ("2020-01-01", "2021-12-31"),
    "F2": ("2022-01-01", "2023-12-31"),
    "F3": ("2024-01-01", "2025-06-30"),
    "F4": ("2025-07-01", "2026-09-30"),
}
PANEL_END = "2026-09-30"
# Two competing warmup laws (P5-FXEB-OD10):
#   FAMILY_60 — 60 held sessions at each fold head (FX_HYPOTHESES s.1.5 family
#               law; K6GATE s.0.2) — DRAFT DEFAULT recorded, never binding
#               without the signature.
#   ES_252    — 252-session ES precedent (CYCLE_LAUNCH_DRAFT s.4 six-adopt).
WARMUP_MODES: dict[str, int] = {"FAMILY_60": 60, "ES_252": 252}
DEFAULT_WARMUP_MODE = "FAMILY_60"


def fold_for_date(d: str | date) -> str | None:
    ds = _as_date(d)
    for fid, (a, b) in FOLDS.items():
        if date.fromisoformat(a) <= ds <= date.fromisoformat(b):
            return fid
    return None


def scoreable_sessions(sessions: list[str], fold_id: str,
                       warmup_mode: str = DEFAULT_WARMUP_MODE) -> list[str]:
    """Exclude the warmup head at each fold, per the selected warmup law.

    Both competing laws are implemented and switchable; while P5-FXEB-OD10 is
    unsigned NEITHER is binding — the default (FAMILY_60) is the recorded draft
    and bind_warmup_law() refuses to bind either without the signature.
    """
    if warmup_mode not in WARMUP_MODES:
        raise ValueError(f"unknown warmup mode {warmup_mode!r} "
                         f"(known: {sorted(WARMUP_MODES)})")
    inside = sorted(s for s in sessions if fold_for_date(s) == fold_id)
    return inside[WARMUP_MODES[warmup_mode]:]


# ------------------------------------------------------------- decision slots
# GAPS_AND_DECISIONS_6E_6B.md s.(b): owner decisions, namespaced P5-FXEB-OD1..11
# (this lane's rendering of the GAPS P5-OD* set; prior authorities PB2, D2/D3,
# e.1-e.4, D5, D12, DC s.1.3, ADOPT-D8/D9 are cited by their ORIGINAL ids and
# never renumbered). Fail-closed: None == UNSIGNED. No lane may sign.
GUARDS: dict[str, None | dict] = {
    "P5-FXEB-OD1": None,   # PB2 lift for 6E/6B (P5-OD1) — real-data gate
    "P5-FXEB-OD2": None,   # FX ceiling signature: CONV-D vs census-native,
                           # option FX-A/B/C, clock-shadow reading (a)/(b)
    "P5-FXEB-OD3": None,   # CONV-D core delay-slot assignment {D0,D1B} vs
                           # {D0,D30M}
    "P5-FXEB-OD4": None,   # placebo budget ruling (single-seed default)
    "P5-FXEB-OD5": None,   # RMM Role-B legality: owner DC s.1.3 boundary ruling
    "P5-FXEB-OD6": None,   # reg-basis on the FX tier (Variant-B 2.46 printed vs
                           # Variant-A 2.47 DERIVED) — consumes D3(=e.4)
    "P5-FXEB-OD7": None,   # e.1 FX-group fee alias corroboration (PARTIAL)
    "P5-FXEB-OD8": None,   # BBO/execution realism (reaffirm D5)
    "P5-FXEB-OD9": None,   # D12 residual-cell posture ratification for FX
    "P5-FXEB-OD10": None,  # FX fold/warmup law freeze (60 vs 252)
    "P5-FXEB-OD11": None,  # court s.b1.1 1m trigger-time anatomy commissioning
}


class RefusedPendingOwnerDecision(Exception):
    """Fail-closed gate: an owner-pending law was exercised unsigned."""

    code = "REFUSED_PENDING_OWNER_DECISION"

    def __init__(self, slot_id: str, detail: str = ""):
        self.slot_id = slot_id
        self.detail = detail
        super().__init__(f"[{slot_id}] unsigned owner decision — refused "
                         f"(fail-closed)" + (f": {detail}" if detail else ""))

    def record(self) -> dict:
        return {"code": self.code, "slot_id": self.slot_id, "detail": self.detail}


class RefusedPendingEvidence(Exception):
    """NEEDS_EVIDENCE family: a named missing measurement blocks the path."""

    code = "REFUSED_PENDING_EVIDENCE"

    def __init__(self, item: str, detail: str = ""):
        self.item = item
        self.detail = detail
        super().__init__(f"[{item}] missing evidence — refused (NEEDS_EVIDENCE)"
                         + (f": {detail}" if detail else ""))

    def record(self) -> dict:
        return {"code": self.code, "item": self.item, "detail": self.detail}


class PanelError(Exception):
    code = "REFUSED_PANEL_INVALID"


class RefusedSessionMismatch(Exception):
    code = "REFUSED_SESSION_MISMATCH"


def require_synthetic(panel: dict) -> None:
    """P5-FXEB-OD1 gate (PB2 lift, unsigned): real-chain consumption refuses.

    Any panel whose provenance is not SYNTHETIC raises. This is the adapter-side
    form of the law "real-data adapter execution = NOT_RUN" (PB2 + FX ceiling +
    fee basis + registration all gated; PB2 HOLD stands).
    """
    prov = panel.get("provenance")
    if prov != "SYNTHETIC":
        raise RefusedPendingOwnerDecision(
            "P5-FXEB-OD1",
            f"panel provenance {prov!r} is not SYNTHETIC: consuming any real "
            f"6E/6B chain requires the PB2 lift (P5-OD1; PB2_HOLD_RESTATE sha256 "
            f"88386aa3...5a75b — HOLD stands) + FX ceiling (P5-OD2) + fee basis "
            f"(P5-OD6/OD7) + registration; real-data adapter execution = NOT_RUN")


def bind_option(option_id: str) -> dict:
    """Bind an identity-budget option (FX-A 44 / FX-B 66 / FX-C 96 CONV-D) —
    P5-FXEB-OD2 gated. While unsigned NO option may bind; the DRAFT enumeration
    stays provisional and never constitutes a scored denominator. The signature
    payload must also name CONV-D vs census-native and the clock-shadow reading
    (a)/(b) (IDENTITY_BUDGET s.5 items 2/4)."""
    if option_id not in ("FX-A", "FX-B", "FX-C"):
        raise ValueError(f"unknown FX option {option_id!r}")
    if GUARDS["P5-FXEB-OD2"] is None:
        raise RefusedPendingOwnerDecision(
            "P5-FXEB-OD2",
            f"binding option {option_id} requires the FX ceiling signature "
            f"(CONV-D vs census-native, option letter, clock-shadow reading "
            f"(a)/(b) — CENSUS_FINAL s.4 'no cap exists'; IDENTITY_TABLES s.2.1/"
            f"s.6); unsigned -> nothing registers")
    return {"option_id": option_id, "bound_by": GUARDS["P5-FXEB-OD2"]}


# --------------------------------------------------------- identity budget
# IDENTITY_BUDGET_6E_6B.md s.4 — exact DRAFT ID strings (grammar
# FXF<n>-<SYM>-<ARM>-<TAIL>-<DELAY>-<TIER>[-<STRATUM>]; DRAFT naming, fixed at
# any future registration freeze). CONV-D per family per leg = 8 core S2
# (2 arms x 2 tails x 2 delays) + 3 scored controls = 11.
ARM_CODES = {
    "FX-F1": ("HC", "HD"),   # H-C continuation vs H-D fade
    "FX-F2": ("RC", "RD"),   # resolution-drift vs spike-reversal
    "FX-F3": ("SC", "SD"),   # spill continuation vs fade
    "FX-F4": ("GC", "GD"),   # reopen-gap continuation vs revert
}
CONTROL_IDS = ("C1-SHADOW", "C2-ALW", "C3-ANCHOR")
DELAY_SLOTS_DRAFT = ("D0", "D1B")     # P5-FXEB-OD3 draft default: spike-decay
                                      # detector pair (FX_HYPOTHESES s.2.5)
DELAY_SLOTS_ALT = ("D0", "D30M")      # ES P-A shape alternative


def bind_delay_slots(pair: tuple[str, str]) -> dict:
    """P5-FXEB-OD3 gated: the CONV-D signature must fix the core delay-slot
    assignment. Draft default {D0, D1B} is recorded but never binding."""
    if GUARDS["P5-FXEB-OD3"] is None:
        raise RefusedPendingOwnerDecision(
            "P5-FXEB-OD3",
            f"binding core delay slots {pair} requires the CONV-D convention "
            f"signature; draft default {DELAY_SLOTS_DRAFT} recorded, never "
            f"binding without it (GAPS s.(b) P5-OD3)")
    return {"delay_slots": list(pair), "bound_by": GUARDS["P5-FXEB-OD3"]}


def core_ids(family: str, sym: str,
             delay_slots: tuple[str, ...] = DELAY_SLOTS_DRAFT) -> list[str]:
    if family not in ARM_CODES:
        raise ValueError(f"unknown family {family!r}")
    if sym not in SYMBOLS:
        raise ValueError(f"unknown symbol {sym!r}")
    if delay_slots not in (DELAY_SLOTS_DRAFT, DELAY_SLOTS_ALT):
        raise ValueError("delay slots must be the draft default or the declared "
                         "alternative (binding requires P5-FXEB-OD3)")
    arms = ARM_CODES[family]
    fam_tag = family.split("-")[1]        # "F1" -> ID prefix "FXF1"
    return [f"FX{fam_tag}-{sym}-{arm}-{tail}-{delay}-S2"
            for arm in arms for tail in ("UP", "DN") for delay in delay_slots]


def control_ids(family: str, sym: str) -> list[str]:
    if family not in ARM_CODES or sym not in SYMBOLS:
        raise ValueError("unknown family/symbol")
    fam_tag = family.split("-")[1]
    return [f"FX{fam_tag}-{sym}-{c}" for c in CONTROL_IDS]


def family_identity_counts(family: str, sym: str) -> dict:
    return {"core": len(core_ids(family, sym)), "controls": len(control_ids(family, sym)),
            "conv_d_minimal": len(core_ids(family, sym)) + len(control_ids(family, sym))}


# ------------------------------------------------------------- cost contract
# COST_CONTRACT_6E_6B.md s.1-s.3. MODELED COST / UNDER REVIEW /
# VERIFIED_VS_ACCOUNT=NOT_RUN on every surface; "measured cost"/"complete cost"
# FORBIDDEN (A7 s.7 language law). Fee layer: commission 0.85 (IBKR Fixed T1),
# exchange CME "Forex Futures" group 1.60 (label alias PARTIAL — 6E/6B never
# printed verbatim, owner slot e.1 = P5-FXEB-OD7), reg Variant-B 0.01 (printed
# composition) vs Variant-A 0.02 (DERIVED for FX — not in any A7 s.8 dual-variant
# table, which tabulates ES/NQ only; owner reg-basis ruling P5-OD6 required).
FEE_COMPONENTS_USD = {"commission_t1": 0.85, "exchange_forex_group": 1.60,
                      "reg_variant_B_printed": 0.01, "reg_variant_A_derived": 0.02}
FEE_ALL_IN_PER_SIDE = {"B": 2.46, "A_derived": 2.47}
SPREAD_HALF_TURN_USD = 18.75          # 3 ticks x $6.25 close-proxy, HIGH-BIASED
                                      # (DC s.1.7; BBO NOT_RUN — D5)
SLIPPAGE_USD_PER_SIDE = {"S1": 6.25, "S2": 12.50, "S3": 18.75}  # {1,2,3} ticks
COST_LABELS = ["MODELED COST", "UNDER REVIEW", "VERIFIED_VS_ACCOUNT=NOT_RUN"]
DEAD_SPOT_FLOOR_BP = 3.0              # PB2 ancestry fence (court s.a/s.b4):
                                      # 6E 1.2-2.1x, 6B 2.1-3.7x the dead proxy


def cost_ladder_usd(sym: str, tier: str, stress: float = 1.0) -> dict:
    """Descriptive modeled-cost ladder row (COST_CONTRACT s.3 shape).

    gate_consumable is ALWAYS False while P5-FXEB-OD6 is unsigned: on FX both
    reg bases coexist and NO cost gate may consume either number (fail-closed
    GAPS P5-OD6 default). RT x1.0 is the gate number at any future freeze;
    x1.5/x2.0 are disclosed robustness views.
    """
    if sym not in SYMBOLS:
        raise ValueError(f"unknown symbol {sym!r}")
    if tier not in SLIPPAGE_USD_PER_SIDE:
        raise ValueError(f"unknown cost tier {tier!r}")
    if stress not in (1.0, 1.5, 2.0):
        raise ValueError("stress must be one of 1.0/1.5/2.0 (no double-stress law)")
    per_side_b = (FEE_ALL_IN_PER_SIDE["B"] + SPREAD_HALF_TURN_USD
                  + SLIPPAGE_USD_PER_SIDE[tier]) * stress
    per_side_a = (FEE_ALL_IN_PER_SIDE["A_derived"] + SPREAD_HALF_TURN_USD
                  + SLIPPAGE_USD_PER_SIDE[tier]) * stress
    lo, hi = SYMBOL_LAW[sym]["notional_band"]
    rt_b = 2.0 * per_side_b
    return {
        "symbol": sym, "tier": tier, "stress": stress,
        "fee_variant_B_printed": FEE_ALL_IN_PER_SIDE["B"],
        "fee_variant_A_derived": FEE_ALL_IN_PER_SIDE["A_derived"],
        "spread_half_turn_usd": SPREAD_HALF_TURN_USD,
        "slippage_usd_per_side": SLIPPAGE_USD_PER_SIDE[tier],
        "cost_per_side_usd_B": round(per_side_b, 6),
        "cost_per_side_usd_A_derived": round(per_side_a, 6),
        "cost_rt_usd_B": round(rt_b, 6),
        "cost_rt_usd_A_derived": round(2.0 * per_side_a, 6),
        "rt_bp_band_symbol": list(SYMBOL_LAW[sym]["rt_bp_band"]),
        "rt_bp_at_notional_low": round(rt_b / lo * 1e4, 4),
        "rt_bp_at_notional_high": round(rt_b / hi * 1e4, 4),
        "gate_consumable": False,
        "gate_blockers": ["P5-FXEB-OD6 (reg basis; consumes D3/e.4)",
                          "P5-FXEB-OD7 (e.1 FX fee alias corroboration)"],
        "labels": list(COST_LABELS),
        "forbidden_words_respected": True,
    }


def consumable_rt_cost(sym: str, tier: str, stress: float = 1.0,
                       basis: str | None = None) -> float:
    """A cost number a GATE may consume. Refuses while P5-FXEB-OD6 unsigned
    (both bases coexist; none consumable). Requesting basis="A" additionally
    refuses as DERIVED-not-tabulated even under a signed B ruling."""
    if basis == "A":
        raise RefusedPendingOwnerDecision(
            "P5-FXEB-OD6",
            "FX Variant-A composition (0.85+1.60+0.02=2.47) is DERIVED — not "
            "tabulated in A7 s.8 (ES/NQ only); requires the owner reg-basis "
            "ruling on its own terms")
    if GUARDS["P5-FXEB-OD6"] is None:
        raise RefusedPendingOwnerDecision(
            "P5-FXEB-OD6",
            "no cost gate may consume either FX reg basis while the owner "
            "ruling is unsigned (GAPS P5-OD6 fail-closed default); e.1 alias "
            "corroboration (P5-FXEB-OD7) is additionally outstanding")
    return cost_ladder_usd(sym, tier, stress)["cost_rt_usd_B"]


def rt_cost_bp(rt_usd: float, sym: str, notional: float | None = None) -> float:
    if notional is None:
        lo, hi = SYMBOL_LAW[sym]["notional_band"]
        notional = (lo + hi) / 2.0
    return rt_usd / notional * 1e4


def override_d12_posture(*_args, **_kwargs) -> None:
    """Documented P5-FXEB-OD9 bypass helper — ALWAYS refuses while unsigned.
    The D12 residual-cell posture stands: NOT_OBTAINED quarters/holiday windows
    stay out, affected sessions excluded fail-closed (CALENDAR_PIT_POLICY s.5)."""
    if GUARDS["P5-FXEB-OD9"] is None:
        raise RefusedPendingOwnerDecision(
            "P5-FXEB-OD9",
            "D12 residual-cell posture for FX (6E ECU26/ECZ26; 6B 2023Q1-24Q2 + "
            "0/42 holiday grid; 6E 8 aged-out windows): leave + fail-closed "
            "stands; funding further permitted-route attempts is owner-only")
    raise PanelError("P5-FXEB-OD9 signed path is outside ADAPT-FXEB scope")


def request_f1_scored_spec(sym: str) -> None:
    """P5-FXEB-OD11: court s.b1.1 1m trigger-time anatomy is NOT_RUN and is
    required BEFORE any scored F1 registration — regardless of a PB2 lift."""
    raise RefusedPendingOwnerDecision(
        "P5-FXEB-OD11",
        f"court s.b1.1 1m trigger-time anatomy NOT_RUN (K6GATE s.6 item 1): no "
        f"scored FX-F1 {sym} spec may be commissioned from PREP; commissioning "
        f"needs an explicit owner authorization (borders the unconditional-only "
        f"law)")


def bind_warmup_law(mode: str) -> dict:
    """P5-FXEB-OD10 gated: binding either warmup/fold law as THE law requires
    the owner signature (60-held-session family law vs 252-session ES precedent
    — the two committed laws differ for FX; GAPS P5-OD10)."""
    if mode not in WARMUP_MODES:
        raise ValueError(f"unknown warmup law {mode!r}")
    if GUARDS["P5-FXEB-OD10"] is None:
        raise RefusedPendingOwnerDecision(
            "P5-FXEB-OD10",
            f"binding warmup law {mode} requires the owner fold/warmup freeze "
            f"signature; draft default {DEFAULT_WARMUP_MODE} recorded, never "
            f"binding without it")
    return {"warmup_mode": mode, "bound_by": GUARDS["P5-FXEB-OD10"]}


def decision_slot_dependencies() -> list[str]:
    """Every adapter intent carries the full P5-FXEB-OD* dependency block."""
    return [f"P5-FXEB-OD{k}" for k in range(1, 12)]


# --------------------------------------------------------- instrument law
def load_fx_contract(sym: str, path: str | Path | None = None) -> dict:
    """Load + bind the 6E/6B contract row from exec/symbol_contracts.json.

    SPEC_6E s.1 / SPEC_6B s.1: 6E tick 0.00005 / $6.25 / 125000; 6B tick
    0.0001 / $6.25 / 62500; long_base_sign +1 (USD per unit of base ccy).
    Invariant tick_value/tick_size == multiplier statically asserted.
    NOTE: the row's session_mask_spec.rth "07:20-14:00" is a
    PLACEHOLDER-PENDING field with zero committed evidence (CONTRACTS handoff
    finding F2) — it is read for disclosure only and NEVER consumed as session
    law; the measured Globex 17:00->16:00 CT template is the law of record.
    """
    if path is None:
        path = Path(__file__).resolve().parents[1] / "exec" / "symbol_contracts.json"
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    c = data["contracts"][sym]
    tick, tval, mult = float(c["tick_size"]), float(c["tick_value_usd"]), float(c["multiplier"])
    expected = SYMBOL_LAW[sym]
    if (tick, tval, mult) != (expected["tick"], expected["tick_value_usd"],
                              expected["multiplier"]):
        raise PanelError(f"{sym} contract numbers diverge from the bound "
                         f"identity: tick {tick}, ${tval}/tick, mult {mult}")
    if abs(tval / tick - mult) > 1e-6:
        raise PanelError("tick_value/tick_size != multiplier invariant violated")
    if int(c["long_base_sign"]) != 1:
        raise PanelError(f"{sym} long_base_sign must be +1 (USD per {expected['base_ccy']})")
    return {
        "ticker": c["ticker"], "exchange": c["exchange"],
        "tick_size": tick, "tick_value_usd": tval, "multiplier": mult,
        "quote_ccy": c["quote_ccy"], "base_ccy": c["base_ccy"],
        "long_base_sign": int(c["long_base_sign"]),
        "session_mask_placeholder_disclosed": c.get("session_mask_spec", {}).get("rth"),
        "source": str(path),
        "verification_note": ("runner-side verification field is "
                              "PLACEHOLDER-PENDING-PER-SYMBOL-LANE (EXEC-lane "
                              "data law); adapter binds the SPEC_6E/SPEC_6B s.1 "
                              "identity tables and discloses the placeholder"),
    }


def round_to_tick(px: float, sym: str) -> float:
    tick = SYMBOL_LAW[sym]["tick"]
    return round(round(px / tick) * tick, 10)


def on_tick_grid(px: float, sym: str) -> bool:
    tick = SYMBOL_LAW[sym]["tick"]
    return abs(px / tick - round(px / tick)) < 1e-6


# ------------------------------------------------------------------ helpers
def _as_date(d: str | date) -> date:
    return d if isinstance(d, date) else date.fromisoformat(str(d)[:10])


def parse_ts(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        raise PanelError(f"bar ts must carry a tz offset (CT-stamped chain "
                         f"law): {ts!r}")
    return dt.astimezone(CT)


def ct_minutes(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


def in_session_minutes(dt: datetime) -> bool:
    """Globex 17:00 CT (D-1) -> 16:00 CT (D), 60-min maintenance break."""
    m = ct_minutes(dt)
    return m >= SESSION_OPEN_MIN or m < SESSION_CLOSE_MIN


def session_bars(panel: dict, session_date: str,
                 upto: str | datetime | None = None) -> list[dict]:
    a = upto if upto is None or isinstance(upto, datetime) else parse_ts(upto)
    out = []
    for b in panel["bars"]:
        if b["session_date"] != session_date:
            continue
        ts = parse_ts(b["ts"])
        if a is not None and ts > a:
            continue
        out.append({**b, "_dt": ts})
    out.sort(key=lambda b: b["_dt"])
    return out


def bars_upto(panel: dict, asof: str | datetime) -> list[dict]:
    """PIT read: only bars with ts <= asof. Every adapter read goes through this
    (or session_bars(..., upto=...))."""
    a = asof if isinstance(asof, datetime) else parse_ts(asof)
    return [b for b in panel["bars"] if parse_ts(b["ts"]) <= a]


def session_map(panel: dict) -> dict:
    return {s["session_date"]: s for s in panel["sessions"]}


def prior_sessions(panel: dict, session_date: str, n: int) -> list[str]:
    return sorted(s for s in session_map(panel) if s < session_date)[-n:]


def atr20_points(panel: dict, session_date: str, period: int = 20) -> float | None:
    """ATR(period) = mean daily range (high-low) of the prior `period` held
    sessions, strict past (never includes session_date itself), held-contract-
    only aggregates (SPEC_6E s.2 / SPEC_6B s.2 law). Numeric SL/TP levels are
    computed at freeze, never before (SPEC_6E s.10 item 12 posture); this
    helper is the deterministic ATR primitive those levels consume."""
    sm = session_map(panel)
    prior = sorted(s for s in sm if s < session_date)[-period:]
    if len(prior) < period:
        return None
    return sum(float(sm[s]["high"]) - float(sm[s]["low"]) for s in prior) / period


def validate_panel(panel: dict) -> None:
    sym = panel.get("symbol")
    if panel.get("schema") != "adapt_fx_eb/synthetic_panel@1":
        raise PanelError(f"panel schema must be adapt_fx_eb/synthetic_panel@1, "
                         f"got {panel.get('schema')!r}")
    if sym not in SYMBOLS:
        raise PanelError(f"panel symbol must be one of {SYMBOLS}, got {sym!r}")
    for key in ("contract", "sessions", "bars"):
        if key not in panel:
            raise PanelError(f"panel missing {key!r}")
    for bar in panel["bars"]:
        for k in ("ts", "open", "high", "low", "close", "volume", "session_date"):
            if k not in bar:
                raise PanelError(f"bar missing {k!r}")
        if not on_tick_grid(float(bar["open"]), sym) or \
           not on_tick_grid(float(bar["close"]), sym):
            raise PanelError(f"bar price off {sym} tick grid: {bar}")


# ----------------------------------------------------- day-set / exclusion law
def f2_event_day_set(sym: str, calendar: dict) -> set[str]:
    """FX-F2 day-sets per symbol (mutually exclusive vs F1's base —
    IDENTITY_BUDGET s.2 table): 6E = FOMC u ECB GC; 6B = MPC u FOMC.
    Vintage law (CALENDAR_PIT_POLICY s.4): calendars keyed as-of decision date;
    current-calendar inference FORBIDDEN — the injected rows must carry their
    vintage provenance; this function consumes them as carried data."""
    cal = calendar or {}
    out: set[str] = set()
    for key in SYMBOL_LAW[sym]["f2_day_sets"]:
        for row in cal.get(key, []):
            out.add(row if isinstance(row, str) else row["date"])
    return out


EVIDENCE_BASED_DEVIATION_6E = "2023-11-24"   # the single committed id-58
                                             # deviation exclusion (CALENDAR
                                             # s.3.1); hard-coded, cited.
AGED_OUT_WINDOWS_6E = ["2022-12-31", "2023-01-15", "2023-02-19", "2023-04-06",
                       "2023-05-28", "2023-06-18", "2023-07-03",
                       "2025-01-05"]        # 8 INCONCLUSIVE_AGED_OUT (never cells)


def holiday_exclusion_flags(sym: str, calendar: dict, session_date: str) -> list[str]:
    """Per-symbol holiday law (CALENDAR_PIT_POLICY s.3), fail-closed."""
    cal = calendar or {}
    flags: list[str] = []
    if sym == "6E":
        if session_date == EVIDENCE_BASED_DEVIATION_6E:
            flags.append("H6E_EVIDENCE_BASED_DEVIATION")
        if session_date in set(cal.get("holiday_neighborhood_6e", [])):
            flags.append("H6E_NEIGHBORHOOD_FAIL_CLOSED")   # 93 cells / 37 windows
        if session_date in set(cal.get("aged_out_neighborhood_6e",
                                       AGED_OUT_WINDOWS_6E)):
            flags.append("H6E_AGED_OUT_NEIGHBORHOOD")      # zero-grids from aged
                                                           # captures never clean
    else:  # 6B: 0/42 grid — NO exclusion implementable; the hole is DECLARED
        flags.append("HOL_GRID_ABSENT_0OF42_DECLARED")
    return flags


def roll_anchor_exclusions(sym: str, session_date: str) -> list[str]:
    """D12 posture: quarters whose official expiry cells are NOT_OBTAINED carry
    no official roll anchor -> fail-closed per-quarter exclusion at freeze."""
    if quarter_of(session_date) in SYMBOL_LAW[sym]["not_obtained_quarters"]:
        return ["QUARTER_NOT_OBTAINED_ROLL_ANCHOR"]
    return []


def apply_exclusions(sym: str, calendar: dict, panel: dict, *,
                     family: str, coverage_threshold: float = 0.80,
                     london_coverage: dict[str, float] | None = None) -> dict:
    """Family-scoped fail-closed exclusion pass over every session in the panel.

    Returns {session_date: [flag, ...]}; ANY flag means EXCLUDED (NO-TRADE).
    Flags that are posture DECLARATIONS on 6B (HOL_GRID_ABSENT_0OF42_DECLARED)
    are NOT exclusions — callers must treat only the documented exclusion-class
    flags as blocking (see EXCLUSION_FLAGS vs DECLARATION_FLAGS below).
    """
    out: dict[str, list[str]] = {}
    f2_days = f2_event_day_set(sym, calendar)
    rolls = set((calendar or {}).get("roll_switch_dates", []))
    for s in panel["sessions"]:
        sd = s["session_date"]
        flags: list[str] = []
        if family == "FX-F1" and sd in f2_days:
            flags.append("FXF2_EVENT_DAY_STANDING_OUTSIDE")
        if family == "FX-F4":
            if sd in rolls:
                flags.append("ROLL_SESSION")
            prev = sorted(session_map(panel))
            try:
                i = prev.index(sd)
                if i > 0 and prev[i - 1] in rolls:
                    flags.append("SESSION_AFTER_ROLL")
            except ValueError:
                pass
        flags += holiday_exclusion_flags(sym, calendar, sd)
        flags += roll_anchor_exclusions(sym, sd)
        if london_coverage and sd in london_coverage \
           and london_coverage[sd] < coverage_threshold:
            flags.append("LONDON_COVERAGE_LT_080")     # F1 census coverage gate
        if flags:
            out[sd] = flags
    return out


# Declared-posture flags (present, informational — never exclusions):
DECLARATION_FLAGS = {"HOL_GRID_ABSENT_0OF42_DECLARED"}
# Blocking exclusion flags produced by apply_exclusions:
EXCLUSION_FLAGS = {
    "FXF2_EVENT_DAY_STANDING_OUTSIDE", "ROLL_SESSION", "SESSION_AFTER_ROLL",
    "H6E_EVIDENCE_BASED_DEVIATION", "H6E_NEIGHBORHOOD_FAIL_CLOSED",
    "H6E_AGED_OUT_NEIGHBORHOOD", "QUARTER_NOT_OBTAINED_ROLL_ANCHOR",
    "LONDON_COVERAGE_LT_080",
}


def blocking_flags(flags: list[str]) -> list[str]:
    return [f for f in flags if f in EXCLUSION_FLAGS]


def is_blocked(flags: list[str]) -> bool:
    return bool(blocking_flags(flags))


def next_session(panel: dict, session_date: str, n: int = 1) -> str | None:
    dates = sorted(s["session_date"] for s in panel["sessions"])
    try:
        i = dates.index(session_date)
    except ValueError:
        return None
    j = i + n
    return dates[j] if j < len(dates) else None


# ------------------------------------------------------------ exit walk law
# Family exit law (CENSUS FX-F1/F2/F3 field 5, all intraday families):
# TP = entry +/- 2 x SL_distance; SL = entry -/+ 1.0 x ATR(20); same-bar TP/SL
# => SL-priority; otherwise mandatory flat at the 16:00 CT session close.
# Bars before the fill bar are never scanned.
EXIT_SESSION_CLOSE = 16 * 60


def exit_walk(panel: dict, session_date: str, fill_ts: str, sl: float, tp: float,
              direction: int) -> tuple[float, str]:
    """Deterministic exit resolution: SL-priority on touch, TP on touch, else
    the 16:00 CT bar close. Raises PanelError when the session has no 16:00 CT
    bar (refuse, never silently extend the horizon)."""
    close_bar = None
    for b in session_bars(panel, session_date):
        if b["ts"] < fill_ts:
            continue
        m = ct_minutes(b["_dt"])
        lo, hi = float(b["low"]), float(b["high"])
        hit_sl = (direction == 1 and lo <= sl) or (direction == -1 and hi >= sl)
        hit_tp = (direction == 1 and hi >= tp) or (direction == -1 and lo <= tp)
        if hit_sl:
            return sl, "SL_TOUCH"
        if hit_tp:
            return tp, "TP_TOUCH"
        if m == EXIT_SESSION_CLOSE:
            close_bar = b
    if close_bar is not None:
        return float(close_bar["close"]), "TIME_EXIT_1600CT"
    raise PanelError(f"no 16:00 CT close bar for time exit: {session_date}")
