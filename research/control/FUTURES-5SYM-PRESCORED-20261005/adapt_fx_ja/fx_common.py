"""fx_common — shared deterministic machinery for the ADAPT-FXJA lane (6J/6A).

Round FUTURES-5SYM-PRESCORED-20261005, wave-3, lane ADAPT-FXJA. PREP-only.

BINDING LAWS CARRIED (every constant cites its committed source):
  - fx_ja/SPEC_6J.md s.1-9   (instrument identity, QUOTE-DIRECTION LAW s.2, session
    law s.3, calendar law s.4, roll/cease-guard s.5, BoJ/MOF event law s.6, costs s.7,
    folds s.8, baselines s.9)
  - fx_ja/SPEC_6A_CONTINGENCY.md s.1-8 (tick-era law s.1-2, chain laws s.3, AF
    family bindings s.4-5, frozen 26-ID table s.6)
  - fx_ja/CALENDAR_PIT_POLICY_6J_6A.md s.1-5 (expiry cells, holiday grid, BoJ
    knowable/NOT-knowable, RBA date-granularity, fail-closed exclusion inventory)
  - fx_ja/COST_CONTRACT_6J_6A.md s.1-4 (modeled ladders; fee-invariant stress law)
  - fx_ja/IDENTITY_BUDGET_6J.md + .json (J-A/J-B/J-C draft enumeration; FB6J1 token)
  - hypo/CENSUS_5SYM.md family dossiers (JF1/JF2/JF3/RMM/AF1/AF3/AF4 rows)
  - hypo/HYPO_GAPS.md (P5-HYPO-OD2/OD3/OD4 owner slots)
  - fx_ja/GAPS_AND_DECISIONS_6J_6A.md (P5-FXJA-D1..D5 owner slots)
  - exec/symbol_contracts.json "6J"/"6A" rows (consumed read-only; rows carry
    PLACEHOLDER-PENDING-PER-SYMBOL-LANE markers -> adapter binding re-asserts the
    committed identity numbers from SPEC_6J s.1 / SPEC_6A s.1 and refuses drift)

OUTCOME-BLIND LAW: adapters compute SIGNALS and intended ORDER INTENT on SYNTHETIC
fixtures only. Real-data consumption raises RefusedPendingOwnerDecision:
  6J  -> P5-FXJA-D1 (owner 6J ceiling; no cap exists anywhere - CENSUS_FINAL s.4)
  6A  -> P5-FXJA-D5 (PB3 lift + ADOPT-D8 + ADOPT-D9 + D2 + calendar chain)
Real-data adapter execution = NOT_RUN on both symbols.

All functions are pure and deterministic: no randomness, no wall-clock reads,
no I/O beyond an optional read of the committed symbol_contracts.json.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

CT = ZoneInfo("America/Chicago")
JST = ZoneInfo("Asia/Tokyo")            # 6J Tokyo-side windows (SPEC_6J s.3 clock law)
SYD = ZoneInfo("Australia/Sydney")      # 6A AF1/AF3 hosts (SPEC_6A s.4)
SHA = ZoneInfo("Asia/Shanghai")         # AF3 K4 China-window boundary

# ----------------------------------------------------- quote-direction law (6J)
# SPEC_6J s.2 QUOTE-DIRECTION LAW (load-bearing for every sign in any 6J arm):
# 6J is quoted USD per JPY. When the yen STRENGTHENS against the US dollar, the
# 6J price RISES. Every drift/reversal sign, every window-move sign, every
# continuation-arm convention is expressed IN 6J PRICE TERMS
# (yen-strong = positive 6J return). No arm may re-express signals in USDJPY
# terms without an explicit sign inversion declared in its identity table.
#
# ORIENTATION PROOF (own raw slice, not vendor docs):
# fx_ja/6j_orientation_recheck.json (sha256 6ca0baebe85abc7df9204f70252da44e72e
# 0e396751a5114561640a25331ae54) - 2024-07-11 MOF intervention day, front 6JU4:
# session open 0.0062485 -> close 0.0063565 (+1.73% CT-trade-date convention)
# while implied USDJPY fell 160.04 -> 157.32 (yen stronger, 6J price UP).
# Burst minute: 12:41->12:42 UTC close 0.0062800 -> 0.0063325 = +105 ticks/min,
# 12:42Z volume 17,448 lots (bit-identical to 6J_DEEP_v2.md s.5).
QUOTE_DIRECTION_6J = "USD_PER_JPY__6J_UP__JPY_STRONG"
SIXJ_ORIENTATION_PROOF = (
    "fx_ja/6j_orientation_recheck.json sha256 6ca0baeb...: 2024-07-11 front 6JU4 "
    "open 0.0062485 -> close 0.0063565 (+1.73%) while implied USDJPY 160.04 -> 157.32"
)


def usdjpy_to_6j(usdjpy: float) -> float:
    """Orientation helper for TESTS ONLY: implied 6J price from a USDJPY level
    (1/USDJPY, unit-scale). Never a data path; exists so the direction law can be
    exercised end-to-end (yen stronger => smaller USDJPY => LARGER 6J price)."""
    return 1.0 / usdjpy


# ------------------------------------------------------------ instrument law
# SPEC_6J s.1: tick 5e-07 USD/JPY = $6.25/contract; multiplier 12,500,000 JPY.
# SPEC_6A s.1: multiplier 100,000 AUD; ERA LAW tick 1e-04 = $10.00 (era 1,
# 2020-01-02..2020-11-20) vs 5e-05 = $5.00 (era 2, from 2020-11-23); the break
# sits in the 2020-11-20 -> 2020-11-23 weekend (CME FX tick-halving window).
SIXJ_TICK = 5e-07
SIXJ_TICK_VALUE_USD = 6.25
SIXJ_MULTIPLIER = 12_500_000
SIXA_MULTIPLIER = 100_000
SIXA_ERA1_TICK = 1e-04
SIXA_ERA1_TICK_VALUE_USD = 10.00
SIXA_ERA2_TICK = 5e-05
SIXA_ERA2_TICK_VALUE_USD = 5.00
# SPEC_6A s.1-2 (6a_tick_adjudication.json, sha 06367e67...; aud_d2_tickera.json
# sha 14426cfb...): measured boundary, data-side PROVISIONAL pending D8.
SIXA_ERA_BOUNDARY_LAST_ERA1 = date(2020, 11, 20)
SIXA_ERA_BOUNDARY_FIRST_ERA2 = date(2020, 11, 23)


def load_fx_contract(symbol: str, path: str | Path | None = None) -> dict:
    """Load + bind the 6J/6A contract row from exec/symbol_contracts.json.

    The runner-side rows carry VERIFICATION: PLACEHOLDER-PENDING-PER-SYMBOL-LANE
    (EXEC-lane data law). The adapter binding RE-ASSERTS the committed identity
    numbers from SPEC_6J s.1 / SPEC_6A s.1 and refuses drift; the 6A era table
    must carry exactly two rows with the measured boundary.
    """
    if symbol not in ("6J", "6A"):
        raise ValueError(f"unknown symbol {symbol!r}")
    if path is None:
        path = Path(__file__).resolve().parents[1] / "exec" / "symbol_contracts.json"
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    c = data["contracts"][symbol]
    eras = c["era_table"]
    if symbol == "6J":
        if len(eras) != 1:
            raise PanelError("6J must carry exactly one era row (constant tick regime)")
        tick, tval, mult = float(eras[0]["tick_size"]), float(eras[0]["tick_value_usd"]), float(eras[0]["multiplier"])
        if (tick, tval, mult) != (SIXJ_TICK, SIXJ_TICK_VALUE_USD, SIXJ_MULTIPLIER):
            raise PanelError(
                f"6J contract numbers diverge from the bound identity (SPEC_6J s.1): "
                f"tick {tick}, ${tval}/tick, mult {mult}")
        if abs(tval / tick - mult) > 1e-6:
            raise PanelError("6J tick_value/tick_size != multiplier invariant violated")
        return {"symbol": "6J", "tick_size": tick, "tick_value_usd": tval,
                "multiplier": mult, "quote_ccy": "USD", "base_ccy": "JPY",
                "long_base_sign": 1, "quote_direction": QUOTE_DIRECTION_6J,
                "source": str(path)}
    if len(eras) != 2:
        raise PanelError("6A must carry exactly two era rows (tick-era law, SPEC_6A s.1)")
    e1, e2 = eras[0], eras[1]
    got1 = (float(e1["tick_size"]), float(e1["tick_value_usd"]), float(e1["multiplier"]))
    got2 = (float(e2["tick_size"]), float(e2["tick_value_usd"]), float(e2["multiplier"]))
    if got1 != (SIXA_ERA1_TICK, SIXA_ERA1_TICK_VALUE_USD, SIXA_MULTIPLIER):
        raise PanelError(f"6A era-1 row diverges from the measured law: {got1}")
    if got2 != (SIXA_ERA2_TICK, SIXA_ERA2_TICK_VALUE_USD, SIXA_MULTIPLIER):
        raise PanelError(f"6A era-2 row diverges from the measured law: {got2}")
    if date.fromisoformat(e2["effective_from"]) != SIXA_ERA_BOUNDARY_FIRST_ERA2:
        raise PanelError("6A era-2 effective_from must be the measured 2020-11-23 boundary")
    return {"symbol": "6A", "tick_size": got2[0], "tick_value_usd": got2[1],
            "multiplier": got2[2], "quote_ccy": "USD", "base_ccy": "AUD",
            "long_base_sign": 1, "era_table": {"era1": got1, "era2": got2},
            "source": str(path)}


def sixa_era_for_date(d: str | date) -> str:
    """Era label deterministic from the MEASURED 2020-11-20/23 boundary
    (conventional anchor, disclosed; data-side PROVISIONAL pending D8).
    Era 1 = 2020-01-02..2020-11-20 (231 sessions); era 2 = from 2020-11-23."""
    ds = _as_date(d)
    if ds <= SIXA_ERA_BOUNDARY_LAST_ERA1:
        return "era1"
    return "era2"


def sixa_tick(d: str | date) -> float:
    return SIXA_ERA1_TICK if sixa_era_for_date(d) == "era1" else SIXA_ERA2_TICK


def sixa_tick_value_usd(d: str | date) -> float:
    return SIXA_ERA1_TICK_VALUE_USD if sixa_era_for_date(d) == "era1" else SIXA_ERA2_TICK_VALUE_USD


def round_to_tick(px: float, tick: float) -> float:
    return round(round(px / tick) * tick, 10)


def on_tick_grid(px: float, tick: float) -> bool:
    return abs(px / tick - round(px / tick)) < 1e-6


# --------------------------------------------------------- decision slots
# GAPS_AND_DECISIONS_6J_6A.md s.(b) mints P5-FXJA-D1..D5; HYPO_GAPS.md mints
# P5-HYPO-OD2/OD3/OD4. Fail-closed: None == UNSIGNED. No lane may sign; the
# FREEZE-WIRING lane wires the owner-signature path later.
GUARDS: dict[str, None | dict] = {
    "P5-FXJA-D1": None,    # 6J ceiling + clock-shadow reading (no cap exists)
    "P5-FXJA-D2": None,    # DC s.1.3 boundary ruling (RMM Role-B legality, iff J-C)
    "P5-FXJA-D3": None,    # 6J BBO/fill ruling (BBO NOT_RUN per D5 law binds)
    "P5-FXJA-D4": None,    # 6J/6A fee A7 posture (MODELED COST binds until ruled)
    "P5-FXJA-D5": None,    # 6A activation chain: PB3 lift -> D8 -> D9 -> D2 -> calendar
    "P5-HYPO-OD2": None,   # BoJ intraday decision-stamp acquisition (upgrade path only)
    "P5-HYPO-OD3": None,   # ABS + China release-calendar acquisition (AF3 K4 boundary)
    "P5-HYPO-OD4": None,   # JF2 zone-threshold constant (PARAM-GAP, 6J_DEEP s.7-H5)
}

SLOT_DEPENDENCIES = [
    "P5-FXJA-D1", "P5-FXJA-D2", "P5-FXJA-D3", "P5-FXJA-D4", "P5-FXJA-D5",
    "P5-HYPO-OD2", "P5-HYPO-OD3", "P5-HYPO-OD4",
]


class RefusedPendingOwnerDecision(Exception):
    """Fail-closed gate: an owner-pending law was exercised unsigned."""

    code = "REFUSED_PENDING_OWNER_DECISION"

    def __init__(self, slot_id: str, detail: str = ""):
        self.slot_id = slot_id
        self.detail = detail
        super().__init__(f"[{slot_id}] unsigned owner decision — refused (fail-closed)"
                         + (f": {detail}" if detail else ""))

    def record(self) -> dict:
        return {"code": self.code, "slot_id": self.slot_id, "detail": self.detail}


class RefusedBojStampNotInCorpus(Exception):
    """CALENDAR_PIT_POLICY s.3: no minute-level BoJ release stamp exists in
    corpus. JF1 stays WINDOW-CONVENTION-ONLY; any minute-stamped claim is
    PIT-illegal on this corpus. Upgrade path = P5-HYPO-OD2 (owner acquisition)."""

    code = "REFUSED_BOJ_STAMP_NOT_IN_CORPUS"

    def __init__(self, detail: str = ""):
        self.detail = detail
        super().__init__("BoJ intraday stamps NOT_IN_CORPUS (window-convention law)"
                         + (f": {detail}" if detail else ""))

    def record(self) -> dict:
        return {"code": self.code, "detail": self.detail}


class RefusedEra1NoTradeIntent(Exception):
    """SPEC_6A s.2 NO-BACK-CAST LAW + wave-3 dispatch law: era-1 (2020-01-02..
    2020-11-20) windows are descriptive-only for era-2-calibrated cost models;
    the adapter REFUSES to produce trade intent there (refusal code, not a
    warning). Era-1 trade intent with an era-1 cost model additionally sits
    behind the full P5-FXJA-D5 chain and never activates in this build."""

    code = "REFUSED_ERA1_DESCRIPTIVE_ONLY"

    def __init__(self, detail: str = ""):
        self.detail = detail
        super().__init__("6A era-1 stratum is descriptive-only (no-back-cast law)"
                         + (f": {detail}" if detail else ""))

    def record(self) -> dict:
        return {"code": self.code, "detail": self.detail}


class RefusedMofLagLawViolation(Exception):
    """DC s.1.4 lag law: MOF op amounts publish ~1 month (monthly) / quarterly
    (daily detail) after the fact. Same-day intervention signals are FORBIDDEN;
    JF2 labels are built on the DISCLOSURE date, never the op date."""

    code = "REFUSED_MOF_LAG_LAW_VIOLATION"

    def __init__(self, detail: str = ""):
        self.detail = detail
        super().__init__("MOF same-day op knowledge is PIT-illegal (lag law)"
                         + (f": {detail}" if detail else ""))

    def record(self) -> dict:
        return {"code": self.code, "detail": self.detail}


class RefusedRbaTimeNotCarried(Exception):
    """CALENDAR_PIT_POLICY s.4: the RBA table carries DATES, not decision TIME.
    The 14:30-Sydney anchor stays a DECLARED convention (6A_DEEP s.4.1); any
    verified-release-minute claim refuses."""

    code = "REFUSED_RBA_DECISION_TIME_NOT_CARRIED"

    def __init__(self, detail: str = ""):
        self.detail = detail
        super().__init__("RBA decision time not carried by the source table "
                         "(declared 14:30-Sydney convention only)"
                         + (f": {detail}" if detail else ""))

    def record(self) -> dict:
        return {"code": self.code, "detail": self.detail}


class RefusedChinaCalendarNotRun(Exception):
    """AF3 K4 (SPEC_6A s.4-5): China Caixin/NBS calendars NOT_RUN; a trigger
    landing inside the Shanghai data window is a contamination boundary and the
    base spec refuses rather than trades an unclassifiable event."""

    code = "REFUSED_CHINA_CALENDAR_NOT_RUN"

    def __init__(self, detail: str = ""):
        self.detail = detail
        super().__init__("China release calendars NOT_RUN (AF3 K4 boundary; "
                         "P5-HYPO-OD3 acquisition class)"
                         + (f": {detail}" if detail else ""))

    def record(self) -> dict:
        return {"code": self.code, "detail": self.detail}


class RefusedAf4NoStandaloneIntent(Exception):
    """AF4 overlay law (SPEC_6A s.5; CENSUS AF4 s.5): AF4 has 0 standalone
    identities; NO entry is ever defined from the tick era."""

    code = "REFUSED_AF4_NO_ENTRY_FROM_TICK_ERA"

    def __init__(self, detail: str = ""):
        self.detail = detail
        super().__init__("AF4 is a T3 conditioning overlay with 0 standalone "
                         "identities; no entry is ever defined from the tick era"
                         + (f": {detail}" if detail else ""))

    def record(self) -> dict:
        return {"code": self.code, "detail": self.detail}


class PanelError(Exception):
    code = "REFUSED_PANEL_INVALID"


def require_synthetic(panel: dict, symbol: str) -> None:
    """Real-data consumption gate, symbol-specific:
      6J -> P5-FXJA-D1 (owner 6J ceiling; builder refuses BLOCKED_NO_CEILING),
      6A -> P5-FXJA-D5 (PB3 lift + D8 + D9 + D2 chain; BLOCKED_PB3_PARK /
            BLOCKED_D8_UNRATIFIED). Any panel whose provenance is not SYNTHETIC
            refuses. Real-data adapter execution = NOT_RUN (both symbols)."""
    prov = panel.get("provenance")
    if prov == "SYNTHETIC":
        return
    if symbol == "6J":
        raise RefusedPendingOwnerDecision(
            "P5-FXJA-D1",
            f"panel provenance {prov!r} is not SYNTHETIC: consuming any real 6J "
            f"chain requires the owner 6J ceiling signature (no cap exists, "
            f"CENSUS_FINAL s.4) + BBO ruling (P5-FXJA-D3) + fee A7 posture "
            f"(P5-FXJA-D4) + registration; real-data adapter execution = NOT_RUN")
    raise RefusedPendingOwnerDecision(
        "P5-FXJA-D5",
        f"panel provenance {prov!r} is not SYNTHETIC: any 6A real-data path is "
        f"gated on the activation chain PB3 lift -> ADOPT-D8 ratification -> "
        f"ADOPT-D9 cease-guard standard -> D2 fee A7 -> ABS/China calendar "
        f"ruling (P5-FXJA-D5); 6A stays PB3 PARK "
        f"(BLOCKED_PB3_PARK / BLOCKED_D8_UNRATIFIED)")


def bind_option_6j(option_id: str) -> dict:
    """Bind a 6J identity-budget option (J-A / J-B / J-C) — P5-FXJA-D1 gated,
    J-C additionally P5-FXJA-D2 gated. While unsigned, NO option may bind: the
    draft enumeration stays PROPOSED DRAFT and never constitutes a scored
    denominator (IDENTITY_BUDGET_6J s.0-1)."""
    if option_id not in ("J-A", "J-B", "J-C"):
        raise ValueError(f"unknown 6J option {option_id!r}")
    if GUARDS["P5-FXJA-D1"] is None:
        raise RefusedPendingOwnerDecision(
            "P5-FXJA-D1",
            f"binding option {option_id} requires the owner 6J ceiling signature "
            f"naming the option AND the clock-shadow reading (a)/(b); unsigned -> "
            f"no 6J registration is lawful (BLOCKED_NO_CEILING)")
    if option_id == "J-C" and GUARDS["P5-FXJA-D2"] is None:
        raise RefusedPendingOwnerDecision(
            "P5-FXJA-D2",
            "J-C carries the RMM Role-B 6J leg; legality requires the owner DC "
            "s.1.3 boundary ruling (never self-ratified)")
    return {"option_id": option_id, "bound_by": {k: v for k, v in GUARDS.items()
                                                 if v is not None}}


def consume_boj_intraday_stamp(*_args, **_kwargs) -> None:
    """Documented always-refusing helper: BoJ minute-stamp refinement of JF1 is
    NOT A FAMILY — a data acquisition (P5-HYPO-OD2). The window convention is
    the lawful anchor today (K3 ANCHOR_INSENSITIVE_AT_45MIN delivered)."""
    raise RefusedBojStampNotInCorpus(
        "minute-stamp refinement of JF1 is a P5-HYPO-OD2 owner acquisition, "
        "never a lane inference; K3 anchor law governs")


def jf2_zone_threshold(*_args, **_kwargs) -> float:
    """JF2 zone-threshold constant ('distance-to-highest-USDJPY-acted-upon'
    zone) — PARAM-GAP the owner must fix a priori (P5-HYPO-OD4). Unsigned ->
    the JF2 zone label cannot be computed and the block cannot freeze."""
    raise RefusedPendingOwnerDecision(
        "P5-HYPO-OD4",
        "JF2 zone-threshold constant must be fixed a priori by the owner "
        "(PARAM-GAP, 6J_DEEP s.7-H5); unsigned -> JF2 block cannot freeze")


def verified_cost_label(*_args, **_kwargs) -> dict:
    """Any request for a VERIFIED_VS_ACCOUNT / 'measured cost' / 'complete cost'
    surface refuses while the fee A7 posture (P5-FXJA-D4) is unsigned. All
    cells stay MODELED COST / UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN."""
    raise RefusedPendingOwnerDecision(
        "P5-FXJA-D4",
        "VERIFIED_VS_ACCOUNT requires the owner-authorized fee A7 (D2 posture) "
        "to run clean; until ruled all cells stay MODELED COST / UNDER REVIEW")


def non_conservative_fill_model(*_args, **_kwargs) -> dict:
    """BBO/limit/queue fill claims refuse while P5-FXJA-D3 is unsigned: BBO is
    NOT_RUN (D5 law) and the conservative fill law (fill = next-bar open,
    close-proxy spread, SL-priority) is the only lawful fill model."""
    raise RefusedPendingOwnerDecision(
        "P5-FXJA-D3",
        "BBO NOT_RUN (D5 law); the conservative fill law is the only lawful "
        "fill model until the owner BBO/fill ruling signs")


# ------------------------------------------------------------- cost contract
# COST_CONTRACT_6J_6A.md s.1-4. Labels binding on EVERY cell: MODELED COST /
# UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN. "measured cost"/"complete cost"
# FORBIDDEN. Stress x1.5/x2.0 apply to (spread + declared slippage) ONLY — the
# fee layer is invariant (s.0 stress law).
FEE_USD_PER_SIDE = {"T1": 2.46, "T2": 2.26, "T3": 2.06, "T4": 1.86}
SIXJ_SPREAD_USD_PER_SIDE = 25.00        # 4 ticks x $6.25 close proxy, HIGH-BIASED
SIXJ_SLIPPAGE_USD = {"S1": 6.25, "S2": 12.50, "S3": 18.75}
SIXJ_NOTIONAL_OF_RECORD = 79_787.50     # 12,500,000 x 0.006383 (re-measured 2026 tail)
SIXA_ERA2_SPREAD_USD_PER_SIDE = 20.00   # 4 ticks x $5.00 post-break
SIXA_ERA2_SLIPPAGE_USD = {"S1": 5.00, "S2": 10.00, "S3": 15.00}
SIXA_ERA2_NOTIONAL_OF_RECORD = 66_960.00   # 100,000 x 0.6696
SIXA_ERA1_SPREAD_USD_PER_SIDE = 40.00   # 4 ticks x $10.00 (D-2 doubling law)
SIXA_ERA1_SLIPPAGE_USD = {"S1": 10.00, "S2": 20.00, "S3": 30.00}
SIXA_ERA1_NOTIONAL_OF_RECORD = 69_120.00   # 100,000 x 0.6912 median era-1 close
COST_LABELS = ["MODELED COST", "UNDER REVIEW", "VERIFIED_VS_ACCOUNT=NOT_RUN"]
SESSION_FLOOR_NOTE = ("session-of-day floor PROVISIONAL (JF1-7/JF3-8/AF3-8): "
                      "Tokyo/Sydney-window entry fills carry +1 tick additional "
                      "entry-side slippage assumption; declared, never measured")


def cost_per_side_usd(symbol: str, session_date: str | date, tier: str = "T1",
                      slip: str = "S1", stress: float = 1.0,
                      session_floor: bool = False) -> dict:
    """Per-side all-in cost per COST_CONTRACT_6J_6A s.1-3 (era-aware for 6A;
    the era is chosen by the ENTRY session — no-back-cast law).

    per_side = fee + stress x (spread + slippage) [+ entry-side session floor]
    Requesting anything but the conservative model (BBO/queue) refuses at
    non_conservative_fill_model(); requesting a verified label refuses at
    verified_cost_label().
    """
    if tier not in FEE_USD_PER_SIDE:
        raise ValueError(f"unknown fee tier {tier!r}")
    if stress not in (1.0, 1.5, 2.0):
        raise ValueError("stress must be one of 1.0/1.5/2.0 (no double-stress law)")
    if symbol == "6J":
        spread, slip_tab, notional, era = (SIXJ_SPREAD_USD_PER_SIDE,
                                           SIXJ_SLIPPAGE_USD,
                                           SIXJ_NOTIONAL_OF_RECORD, "constant")
    elif symbol == "6A":
        era = sixa_era_for_date(session_date)
        if era == "era1":
            spread, slip_tab, notional = (SIXA_ERA1_SPREAD_USD_PER_SIDE,
                                          SIXA_ERA1_SLIPPAGE_USD,
                                          SIXA_ERA1_NOTIONAL_OF_RECORD)
        else:
            spread, slip_tab, notional = (SIXA_ERA2_SPREAD_USD_PER_SIDE,
                                          SIXA_ERA2_SLIPPAGE_USD,
                                          SIXA_ERA2_NOTIONAL_OF_RECORD)
    else:
        raise ValueError(f"unknown symbol {symbol!r}")
    if slip not in slip_tab:
        raise ValueError(f"unknown slippage tier {slip!r}")
    fee = FEE_USD_PER_SIDE[tier]
    slippage = slip_tab[slip]
    per_side = fee + stress * (spread + slippage)
    floor_usd = 0.0
    if session_floor:
        floor_usd = SIXJ_TICK_VALUE_USD if symbol == "6J" else sixa_tick_value_usd(session_date)
    rt = 2.0 * per_side + floor_usd
    return {
        "symbol": symbol, "era": era, "tier": tier, "slip": slip, "stress": stress,
        "fee_usd": fee, "spread_proxy_usd": spread, "slippage_usd": slippage,
        "session_floor_entry_usd": floor_usd, "session_floor_law": SESSION_FLOOR_NOTE,
        "cost_per_side_usd": round(per_side, 6),
        "cost_rt_usd": round(rt, 6),
        "notional_of_record_usd": notional,
        "cost_rt_bp_of_notional": round(rt / notional * 1e4, 4),
        "labels": list(COST_LABELS),
        "fill_model": "CONSERVATIVE (next-bar open; close-proxy spread; SL-priority; BBO NOT_RUN D5)",
        "forbidden_words_respected": True,
    }


# ------------------------------------------------------------------ fold law
# SPEC_6J s.8 (DRAFT — final boundaries fixed at registration freeze):
# 4 folds mapped to the measured span 2020-01-02..2026-09-30, yearly sequential,
# 252-session warmup carve-out excluded from scoring at each fold head.
FOLDS_6J = {
    "F1": ("2020-01-01", "2021-12-31"),
    "F2": ("2022-01-01", "2023-12-31"),
    "F3": ("2024-01-01", "2025-12-31"),
    "F4": ("2026-01-01", "2026-09-30"),
}
PANEL_END = "2026-09-30"       # full-session statistics end (2026-10-01 partial tail)
WARMUP_HELD_SESSIONS = 252     # SPEC_6J s.8 (ES precedent), excluded at each fold head


def fold_for_date(d: str | date) -> str | None:
    ds = _as_date(d)
    for fid, (a, b) in FOLDS_6J.items():
        if date.fromisoformat(a) <= ds <= date.fromisoformat(b):
            return fid
    return None


def scoreable_sessions(sessions: list[str], fold_id: str,
                       warmup: int | None = None) -> list[str]:
    """Fold-head warmup exclusion (SPEC_6J s.8). Warmup = 252 held sessions."""
    if warmup is None:
        warmup = WARMUP_HELD_SESSIONS
    inside = sorted(s for s in sessions if fold_for_date(s) == fold_id)
    return inside[warmup:]


# ------------------------------------------------------------- panel helpers
def _as_date(d: str | date) -> date:
    return d if isinstance(d, date) else date.fromisoformat(str(d)[:10])


def parse_ts(ts: str) -> datetime:
    """All fixture bars are UTC-stamped (ISO, +00:00). Window membership is
    resolved in the LOCAL law clock (JST for 6J Tokyo windows, SYD for 6A) via
    zoneinfo — the DST-correct bucketing law (SPEC_6J s.3 / SPEC_6A s.4)."""
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        raise PanelError(f"bar ts must carry a tz offset (UTC-stamped law): {ts!r}")
    return dt.astimezone(ZoneInfo("UTC"))


def local_hhmm(dt_utc: datetime, tz: ZoneInfo) -> tuple[int, int]:
    loc = dt_utc.astimezone(tz)
    return loc.hour, loc.minute


def local_minutes(dt_utc: datetime, tz: ZoneInfo) -> int:
    h, m = local_hhmm(dt_utc, tz)
    return h * 60 + m


def at_local(d: str | date, hh: int, mm: int, tz: ZoneInfo) -> datetime:
    """Local-wall-clock timestamp in `tz` converted to UTC — the ONLY lawful
    way decision times and fixture bars are stamped (DST-correct bucketing
    law, SPEC_6J s.3 / SPEC_6A s.4)."""
    ds = _as_date(d)
    loc = datetime(ds.year, ds.month, ds.day, hh, mm, tzinfo=tz)
    return loc.astimezone(ZoneInfo("UTC"))


def validate_panel(panel: dict, symbol: str) -> None:
    """Structural validation + era-aware tick-grid assertion (6A)."""
    if panel.get("schema") != "adapt_fx_ja/synthetic_panel@1":
        raise PanelError(f"panel schema must be adapt_fx_ja/synthetic_panel@1, got "
                         f"{panel.get('schema')!r}")
    if panel.get("symbol") != symbol:
        raise PanelError(f"panel symbol {panel.get('symbol')!r} != {symbol!r}")
    for key in ("contract", "sessions", "bars"):
        if key not in panel:
            raise PanelError(f"panel missing {key!r}")
    tick_6j = SIXJ_TICK
    for bar in panel["bars"]:
        for k in ("ts", "open", "high", "low", "close", "volume", "session_date"):
            if k not in bar:
                raise PanelError(f"bar missing {k!r}")
        tick = tick_6j if symbol == "6J" else sixa_tick(bar["session_date"])
        if not on_tick_grid(float(bar["open"]), tick) or not on_tick_grid(float(bar["close"]), tick):
            raise PanelError(f"bar price off the {symbol} tick grid: {bar}")


def bars_upto(panel: dict, asof: str | datetime) -> list[dict]:
    """PIT read: only bars with ts <= asof. Every adapter read goes through
    this (no-future-data law)."""
    a = asof if isinstance(asof, datetime) else parse_ts(asof)
    return [b for b in panel["bars"] if parse_ts(b["ts"]) <= a]


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


def session_map(panel: dict) -> dict:
    return {s["session_date"]: s for s in panel["sessions"]}


def session_last_dt(panel: dict, session_date: str) -> datetime | None:
    agg = session_map(panel).get(session_date)
    if agg is None or agg.get("last_bar_utc") is None:
        return None
    return parse_ts(agg["last_bar_utc"])


def atr20_points(panel: dict, session_date: str, period: int = 20) -> float | None:
    """ATR(period) = mean daily range (high-low) of the prior `period` held
    sessions, strict past (never includes session_date itself); None when
    fewer than `period` prior sessions exist (insufficient warmup -> NO-TRADE)."""
    sm = session_map(panel)
    prior = sorted(s for s in sm if s < session_date)[-period:]
    if len(prior) < period:
        return None
    return sum(float(sm[s]["high"]) - float(sm[s]["low"]) for s in prior) / period


def window_atr20(panel: dict, event_dates: list[str], session_date: str,
                 window_key: str = "window_range") -> float | None:
    """Same-window ATR(20): mean of the event-window ranges over the prior 20
    EVENT sessions, strict past (JF1/AF1 'ATR(20 same-window)' law). The
    per-event window ranges are carried in the session aggregates under
    `window_ranges[window_key]`; None when fewer than 20 prior events exist."""
    sm = session_map(panel)
    prior = sorted(d for d in event_dates if d < session_date and d in sm)[-20:]
    if len(prior) < 20:
        return None
    total = 0.0
    for d in prior:
        wr = sm[d].get("window_ranges", {}).get(window_key)
        if wr is None:
            return None
        total += float(wr)
    return total / 20.0


def window_bars(panel: dict, session_date: str, tz: ZoneInfo,
                start_min: int, end_min: int,
                upto: str | datetime | None = None) -> list[dict]:
    """1m bars of `session_date` whose START local-minute (in `tz`) lies in
    [start_min, end_min) — the DST-correct local-clock bucketing law."""
    out = []
    for b in session_bars(panel, session_date, upto=upto):
        lm = local_minutes(b["_dt"], tz)
        if start_min <= lm < end_min:
            out.append(b)
    return out


def window_coverage(panel: dict, session_date: str, tz: ZoneInfo,
                    start_min: int, end_min: int) -> float | None:
    """Minutes-with-bar share of the nominal [start_min, end_min) window in
    local tz (the >=80% coverage EXCLUDE rule, JF3/AF3 law)."""
    nominal = end_min - start_min
    have = {local_minutes(b["_dt"], tz)
            for b in session_bars(panel, session_date)
            if start_min <= local_minutes(b["_dt"], tz) < end_min}
    return len(have) / nominal if nominal > 0 else None


def first_close_outside(bars: list[dict], lo: float, hi: float) -> dict | None:
    """First 1m bar whose CLOSE is strictly outside [lo, hi]."""
    for b in bars:
        c = float(b["close"])
        if c > hi or c < lo:
            return b
    return None


# --------------------------------------------------------- exclusion engine
# CALENDAR_PIT_POLICY_6J_6A s.5 fail-closed inventory + per-family excludes
# (census JF1 s.6 / JF3 s.6 / AF1 s.6 / AF3 s.6). ANY flag => NO-TRADE.
PARTIAL_TAIL_DATE = "2026-10-01"   # ~2h partial tail ends full-session stats


def apply_fx_exclusions(calendar: dict, panel: dict, symbol: str,
                        *, coverage_windows: list[tuple[ZoneInfo, int, int]] | None = None,
                        exclude_boj_mpm: bool = False,
                        exclude_mof_disclosure: bool = False,
                        exclude_fomc: bool = False) -> dict:
    """Deterministic fail-closed exclusion pass over every panel session.

    Returns {session_date: [flag, ...]}; non-empty means EXCLUDED (NO-TRADE).
    Laws:
      H_QUARTER_UNPROVEN          — whole-quarter exclusions (6J 2023Q1-Q4 + 2
                                    unidentified cells; 6A 2023Q1/Q2) injected
                                    as calendar['quarters_unproven'] (CALENDAR
                                    s.5 item 1; derivation FORBIDDEN)
      H_HOLIDAY_TIMES_NOT_OBTAINED — holiday-shortened sessions whose FX times
                                    cannot be proven (calendar[
                                    'early_close_times_not_obtained']) (s.5 item 2)
      H_WINDOW_COVERAGE_LT_080    — injected-window coverage < 0.80 (s.5 item 3)
      H_PARTIAL_TAIL              — 2026-10-01 partial tail (s.5 item 3)
      X_BOJ_MPM_DAY               — BoJ MPM day excludes for host families
      X_MOF_DISCLOSURE_DAY        — MOF disclosure-date excludes (JF3; op days
                                    for JF1 arrive via calendar['mof_op_days'])
      X_MOF_OP_DAY                — MOF op-day excludes (JF1 universe law; the
                                    op list is a committed ex-post universe
                                    cut, never a decision-time input)
      X_FOMC_DAY / X_FOMC_SPILLOVER — AF1 base excludes (the measured US
                                    common factor on 6A is LARGER than RBA's)
      X_ROLL_CEASE_GUARD          — held-dead sessions under the baseline chain
                                    (6J 2022-09-20 law case; 6A 2024-12-17 /
                                    2026-06-16) injected as calendar[
                                    'roll_guard_flagged_days'] (s.5 item 6)
    """
    out: dict[str, list[str]] = {}
    quarters = set(calendar.get("quarters_unproven", []))
    early = set(calendar.get("early_close_times_not_obtained", []))
    boj = set(calendar.get("boj_mpm_dates", []))
    mof_disc = set(calendar.get("mof_disclosure_dates", []))
    mof_ops = set(calendar.get("mof_op_days", []))
    fomc = set(calendar.get("fomc_statement_days", []))
    fomc_spill = {next_session_date(d) for d in fomc}
    roll_flagged = set(calendar.get("roll_guard_flagged_days", []))
    for s in panel["sessions"]:
        sd = s["session_date"]
        flags: list[str] = []
        dsd = _as_date(sd)
        q = f"{dsd.year}-Q{(dsd.month - 1) // 3 + 1}"
        if q in quarters:
            flags.append("H_QUARTER_UNPROVEN")
        if sd in early:
            flags.append("H_HOLIDAY_TIMES_NOT_OBTAINED")
        if sd == PARTIAL_TAIL_DATE:
            flags.append("H_PARTIAL_TAIL")
        for (tz, a, b) in (coverage_windows or []):
            cov = window_coverage(panel, sd, tz, a, b)
            if cov is not None and cov < 0.80:
                flags.append("H_WINDOW_COVERAGE_LT_080")
                break
        if exclude_boj_mpm and sd in boj:
            flags.append("X_BOJ_MPM_DAY")
        if exclude_mof_disclosure and sd in mof_disc:
            flags.append("X_MOF_DISCLOSURE_DAY")
        if sd in mof_ops:
            flags.append("X_MOF_OP_DAY")
        if exclude_fomc:
            if sd in fomc:
                flags.append("X_FOMC_DAY")
            elif sd in fomc_spill:
                flags.append("X_FOMC_SPILLOVER_NEXT_DAY")
        if sd in roll_flagged:
            flags.append("X_ROLL_CEASE_GUARD")
        if flags:
            out[sd] = sorted(set(flags))
    return out


def next_session_date(d: str | date) -> str:
    ds = _as_date(d) + timedelta(days=1)
    while ds.weekday() >= 5:   # skip weekend for the spillover label [DRAFT-CODE]
        ds += timedelta(days=1)
    return ds.isoformat()


def decision_slot_dependencies() -> list[str]:
    """Every adapter intent carries the full P5-* dependency block it obeys."""
    return list(SLOT_DEPENDENCIES)


# ------------------------------------------------------- MOF disclosure-lag law
# DC s.1.4: op amounts publish ~1 month (monthly) / quarterly (daily detail)
# after the fact; JF2 labels are built on the DISCLOSURE date, never the op
# date; same-day signals FORBIDDEN.
JF2_K_TRAILING_SESSIONS = 63   # [PROVISIONAL] census JF2 s.4
JF2_NULL_ERA = ("2020-01-01", "2022-08-31")   # ZERO in-window ops (C3'' check)


def mof_regime_label(ops: list[dict], session_date: str, asof: str | datetime,
                     held_sessions: list[str] | None = None,
                     k: int = JF2_K_TRAILING_SESSIONS) -> dict:
    """Disclosure-lagged MOF regime state for `session_date` evaluated at
    `asof` (PIT). Only ops with disclosure_date <= asof are visible. Regime =
    REGIME when a visible op's op_date falls within the trailing K held
    sessions of `session_date` (K=63 PROVISIONAL); else NON_REGIME.

    Same-day leak guard: an op whose disclosure_date > asof is INVISIBLE here —
    a caller attempting to read it anyway must go through the refusing
    require_same_day_op_visibility() gate. The pre-2022 null era
    (2020-01..2022-08) must read NON_REGIME throughout (C3'' construction-bug
    check; census JF2 s.6)."""
    # asof is UTC-stamped (fixture law); the knowledge date is its UTC date.
    a_date = asof.date() if isinstance(asof, datetime) else _as_date(str(asof))
    a_date = _as_date(a_date)
    visible = [o for o in ops if _as_date(o["disclosure_date"]) <= a_date]
    if held_sessions is None:
        held_sessions = [session_date]
    held_sorted = sorted(set(held_sessions) | {session_date})
    try:
        i = held_sorted.index(session_date)
    except ValueError:
        i = len(held_sorted)
    window_start_idx = max(0, i - k)
    window_dates = set(held_sorted[window_start_idx:i + 1])
    in_window = [o for o in visible
                 if o["op_date"] in window_dates and _as_date(o["op_date"]) <= a_date]
    label = "REGIME" if in_window else "NON_REGIME"
    return {
        "session_date": session_date, "asof": a_date.isoformat(),
        "regime_label": label,
        "visible_ops": sorted({o["op_date"] for o in visible}),
        "in_window_op_dates": sorted({o["op_date"] for o in in_window}),
        "k_trailing_sessions": k, "k_status": "PROVISIONAL",
        "lag_law": "labels on DISCLOSURE date only (DC s.1.4); same-day signals FORBIDDEN",
    }


def require_same_day_op_visibility(*_args, **_kwargs) -> dict:
    """Documented always-refusing helper: reading a same-day MOF op label at
    decision time violates the DC s.1.4 lag law. K2 (the lag-law violation
    probe) is an evaluation VIEW, never a lawful signal path."""
    raise RefusedMofLagLawViolation(
        "same-day op labels are FORBIDDEN (publish lag ~1 month / quarterly); "
        "JF2 labels are built on the DISCLOSURE date only")


def jf2_null_era_check(ops: list[dict]) -> dict:
    """C3'' construction-bug check: the label must read non-regime throughout
    2020-01..2022-08 (zero in-window ops). Returns the audit record."""
    a, b = (date.fromisoformat(x) for x in JF2_NULL_ERA)
    bad = [o["op_date"] for o in ops
           if a <= _as_date(o["op_date"]) <= b]
    return {"era": list(JF2_NULL_ERA), "ops_in_era": sorted(bad),
            "clean": len(bad) == 0,
            "law": "census JF2 s.6: any op inside the era is a construction bug"}


# ------------------------------------------------------- roll / cease-guard law
# SPEC_6J s.5 + SPEC_6A s.3 (DC s.1.3 timing law): baseline k=5 trailing-5-
# session-volume-crossover chain; cease-guard = if the held contract ceases
# trading (<25% bars or ~0 volume of the session) while the rule has not
# switched, force-switch at that session's close; "decided at close t,
# effective t+1" verbatim; chain choice must not flip any sign (RMM K6(a)).
CEASE_BAR_FRACTION = 0.25


def build_roll_chain(roll_rows: list[dict]) -> dict:
    """Classify each injected roll row and produce both chain variants.

    Each roll_rows entry: {switch_date, old_contract, new_contract,
    held_bars, session_bars_total, held_volume, new_volume, trigger_hint}.
    Classification: cease_guard_no_bars -> ABRUPT; k5_crossover -> GRADUAL.
    Baseline variant keeps a held-dead row (the 6J 2022-09-20 law case: the
    baseline held-MAP keeps the row but the bar-level chain drops the session);
    the explicit cease-guard variant force-switches at that session's close,
    effective the NEXT session (decided close t, effective t+1).
    6A law (SPEC_6A s.3): the baseline k=5 has 2 violations (2024-12-17,
    2026-06-16) => the explicit cease-guard variant is the MANDATORY
    chain-builder (law-pending ADOPT-D9 until ratified).
    """
    baseline, explicit = [], []
    for r in roll_rows:
        frac = (float(r["held_bars"]) / float(r["session_bars_total"])
                if float(r["session_bars_total"]) > 0 else 0.0)
        dead = (frac < CEASE_BAR_FRACTION) or float(r["held_volume"]) <= 0.0
        if dead:
            mode = "ABRUPT"
            trigger = "cease_guard_no_bars"
        else:
            mode = "GRADUAL"
            trigger = "k5_crossover"
        baseline.append({**r, "mode": mode, "trigger": trigger,
                         "held_contract_effective": r["old_contract"],
                         "held_dead_session_dropped": dead,
                         "timing_law": "decided at close t, effective t+1"})
        explicit.append({**r, "mode": mode, "trigger": trigger,
                         "held_contract_effective": (
                             r["new_contract"] if dead else r["old_contract"]),
                         "cease_guard_forced_switch": dead,
                         "effective_session_law": "next session after the close-t decision",
                         "timing_law": "decided at close t, effective t+1"})
    return {"baseline_k5": baseline, "explicit_cease_guard": explicit,
            "baseline_violations": [b["switch_date"] for b in baseline
                                    if b["held_dead_session_dropped"]],
            "sign_flip_check": {"law": "RMM K6(a): chain choice must not flip any sign",
                                "old_to_new_order_identical": all(
                                    b["old_contract"] == e["old_contract"]
                                    and b["new_contract"] == e["new_contract"]
                                    for b, e in zip(baseline, explicit))},
            "mode_counts": {
                "abrupt": sum(1 for b in baseline if b["mode"] == "ABRUPT"),
                "gradual": sum(1 for b in baseline if b["mode"] == "GRADUAL")},
            }


def measure_and_disclose_guard_violations(chain: dict) -> dict:
    """ADOPT-D9 law-pending default (SPEC_6A s.3; CYCLE_LAUNCH_DRAFT D9):
    until D9 is ratified, any builder must MEASURE AND DISCLOSE guard
    violations first. Returns the disclosure record; consumers must attach it
    to any chain-consumed intent."""
    return {"violations": chain["baseline_violations"],
            "n_violations": len(chain["baseline_violations"]),
            "explicit_guard_mandatory": len(chain["baseline_violations"]) >= 2,
            "mandatory_law": ("SPEC_6A s.3: baseline-code k=5 with 2 violations "
                              "=> explicit cease-guard variant mandatory "
                              "(law-pending ADOPT-D9)"),
            "chain_sign_flip": chain["sign_flip_check"]["old_to_new_order_identical"]}


# -------------------------------------------------------------- identity layer
# IDENTITY_BUDGET_6J.md s.2 (+ .json machine mirror): draft token FB6J1;
# grammar FB6J1-<FAM>-<ARM>-<TAIL>-<DELAY>-S2 for cores; controls literal.
DRAFT_TOKEN_6J = "FB6J1"
# 6A contingency token: the frozen 26-ID table carries COUNTS, not ID strings
# (SPEC_6A s.6, sha 1a96b8ea...); the C6A0 skeletons below are PROPOSED
# CONTINGENCY-PB3-PARK shapes and never a scored denominator.
CONTINGENCY_TOKEN_6A = "C6A0"


def jf_core_ids(family: str, arms: tuple[str, str]) -> list[str]:
    return [f"{DRAFT_TOKEN_6J}-{family}-{arm}-{tail}-{delay}-S2"
            for arm in arms for tail in ("UP", "DN") for delay in ("D1", "D30M")]


def jf_control_ids(family: str) -> list[str]:
    return [f"{DRAFT_TOKEN_6J}-PLA-{family}", f"{DRAFT_TOKEN_6J}-ALW-{family}",
            f"{DRAFT_TOKEN_6J}-CLK-{family}"]


def jf1_core_ids() -> list[str]:
    return jf_core_ids("JF1", ("DRIFT", "REV"))


def jf3_core_ids() -> list[str]:
    return jf_core_ids("JF3", ("CONT", "FADE"))


def jf2_core_ids() -> list[str]:
    """JF2 REG identities = regime-state condition on the host grid @ S2:
    FB6J1-JF2-{DRIFT|CONT,REV|FADE}-{UP,DN}-REG-S2 (4 per host)."""
    return [f"{DRAFT_TOKEN_6J}-JF2-{arm}-{tail}-REG-S2"
            for arm in ("DRIFT", "REV") for tail in ("UP", "DN")]


def rmm6j_ids() -> list[str]:
    return [f"{DRAFT_TOKEN_6J}-RMM-MCOMPRESS-{arm}-{delay}"
            for arm in ("REV", "CONT") for delay in ("D1", "D30M")]


def contingency_6a_ids(family: str) -> list[str]:
    """PROPOSED CONTINGENCY-PB3-PARK skeletons. AF1/AF3: 8 cores + 3 controls
    (CONV-B shape); RMM-6A: 4. The FROZEN object is the 26-count table —
    these strings freeze only post-PB3-lift and are never a denominator."""
    if family in ("AF1", "AF3"):
        arm_pair = ("DRIFT", "REV") if family == "AF1" else ("ROT", "ABS")
        cores = [f"{CONTINGENCY_TOKEN_6A}-CONT-{family}-{arm}-{tail}-{delay}-S2"
                 for arm in arm_pair for tail in ("UP", "DN") for delay in ("D1", "D30M")]
        controls = [f"{CONTINGENCY_TOKEN_6A}-CONT-PLA-{family}",
                    f"{CONTINGENCY_TOKEN_6A}-CONT-ALW-{family}",
                    f"{CONTINGENCY_TOKEN_6A}-CONT-CLK-{family}"]
        return cores + controls
    if family == "RMM6A":
        return [f"{CONTINGENCY_TOKEN_6A}-CONT-RMM-MCOMPRESS-{arm}-{delay}"
                for arm in ("REV", "CONT") for delay in ("D1", "D30M")]
    raise ValueError(f"unknown 6A contingency family {family!r}")


def frozen_6a_table_citation() -> dict:
    """The frozen 26-ID contingency table of record (carried VERBATIM in
    SPEC_6A_CONTINGENCY s.6; never expanded): FUTURES-SIX-SCORED-GATE-PREP-
    20261004/budget/identity_tables.json (sha256 1a96b8eafcc80c9ec549a34e06cb
    704db4a240af80bb6488ab2bbc46e6e9246a), symbol entry '6A'."""
    return {
        "source": "FUTURES-SIX-SCORED-GATE-PREP-20261004/budget/identity_tables.json",
        "sha256": "1a96b8eafcc80c9ec549a34e06cb704db4a240af80bb6488ab2bbc46e6e9246a",
        "cap_status": ("PB3 PARK => 0 budget; contingency lines only, all zero "
                       "until PB3 lift + D8"),
        "total": 0, "total_if_ever_lifted": 26,
        "identities_by_category": {
            "AF1_minimal_core": 8, "AF1_controls": 3,
            "AF2_differential_overlay": 0,
            "AF3_minimal_core": 8, "AF3_controls": 3,
            "AF4_tick_regime_overlay": 0, "RMM_6A_contingency": 4,
        },
        "signatures_required": ["owner PB3 lift + D8 (precondition for ANY nonzero count)"],
    }


# -------------------------------------------------- K0/K3 fold-floor helpers
def fold_floor_check(n_events: int, n_folds: int = 4, floor: int = 5) -> dict:
    """Pre-registered >=5-per-fold floor (AF1 K0 thin-n kill; AF4 K3; JF1
    regime-change subset; RMM extremal stratum). Returns the audit record."""
    per_fold = n_events / n_folds if n_folds else 0.0
    return {"n_events": n_events, "n_folds": n_folds, "floor": floor,
            "per_fold_mean": round(per_fold, 2),
            "passes": per_fold >= floor,
            "law": ">=5 events per fold floor; failing strata are DESCRIPTIVE "
                   "FOREVER (pre-declared), never scored"}


# ------------------------------------------------------- C3'' clock-law probe
def dst_mismatch_falsifier(window_minute_delta: int = 60) -> dict:
    """JF3/AF3 C3'' clock-law falsifier: a +/-(1h) CT-side shift of a
    Tokyo/Sydney-anchored effect is a clock bug => family kill. This helper
    returns the DECLARED falsifier law; the empirical probe is an evaluation
    view computed at freeze (0 IDs), never a selectable identity."""
    return {"falsifier": "C3p_DST_MISMATCH",
            "law": ("a +/-1h shift of a Tokyo/Sydney-anchored window effect = "
                    "clock-law bug => family kill (SPEC_6J s.3; census JF3 s.3 "
                    "K3 / AF3 s.3 K3)"),
            "shift_minutes_ct": window_minute_delta,
            "view_status": "evaluation view, 0 identities"}


# ------------------------------------------------------------ C1 shadow law
C1_SEED = 20261002   # ES-precedent single-seed/single-delay law (reading (a))


def shadow_direction(session_date: str, seed: int = C1_SEED) -> int:
    """C1-class clock-only shadow: deterministic sign from (seed, session
    ordinal) at identical window times on matched non-event days. Single-seed/
    single-delay publication law binds (>=100-seed expansions are separate
    owner rulings — the placebo slot is EMPTY, IDENTITY_BUDGET_6J s.0.3)."""
    d = _as_date(session_date)
    return 1 if (seed + d.toordinal()) % 2 == 0 else -1


# ------------------------------------------------------- shared exit resolver
def resolve_exit(bars_after_entry: list[dict], entry_px: float, sl_px: float,
                 tp_px: float, tick: float, session_complete: bool) -> dict:
    """Shared TP/SL/time-exit resolution (conservative fill law, D5):
    scan bars from entry onward; same-bar TP/SL -> SL PRIORITY; otherwise
    mandatory flat at the session's measured last bar close. When the panel is
    truncated (PIT asof before the session end) the exit stays PENDING."""
    exit_px = exit_ts = exit_reason = None
    for b in bars_after_entry:
        lo, hi = float(b["low"]), float(b["high"])
        if lo <= sl_px <= hi:
            return {"exit_ref_price": round_to_tick(sl_px, tick),
                    "exit_ts": b["_dt"].isoformat(), "exit_reason": "SL",
                    "exit_resolution": "RESOLVED"}
        if lo <= tp_px <= hi:
            return {"exit_ref_price": round_to_tick(tp_px, tick),
                    "exit_ts": b["_dt"].isoformat(), "exit_reason": "TP",
                    "exit_resolution": "RESOLVED"}
    if session_complete and bars_after_entry:
        last = bars_after_entry[-1]
        return {"exit_ref_price": round_to_tick(float(last["close"]), tick),
                "exit_ts": last["_dt"].isoformat(), "exit_reason": "SESSION_CLOSE",
                "exit_resolution": "RESOLVED"}
    return {"exit_ref_price": None, "exit_ts": None, "exit_reason": None,
            "exit_resolution": "PENDING_UPTO_ASOF"}


def intent_head(family: str, identity_id: str, session_date: str, panel: dict,
                extra: dict | None = None) -> dict:
    return {"identity_id": identity_id, "family": family,
            "status": "INTENT", "session_date": session_date,
            "fold_id": fold_for_date(session_date),
            "exclusion_flags": [], "warmup_ok": True,
            "decision_slot_dependencies": decision_slot_dependencies(),
            "symbol": panel.get("symbol"),
            "labels": ["SYNTHETIC FIXTURE", "PROPOSED DRAFT", "NO EXECUTION"],
            **(extra or {})}


def no_trade(head: dict, reason: str) -> dict:
    return {**head, "no_trade": True, "no_trade_reason": reason}
