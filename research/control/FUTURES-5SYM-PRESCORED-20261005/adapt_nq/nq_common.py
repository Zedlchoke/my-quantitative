"""nq_common — shared deterministic machinery for the ADAPT-NQ lane.

Round FUTURES-5SYM-PRESCORED-20261005, wave-3, lane ADAPT-NQ. PREP-only.

BINDING LAWS CARRIED (every constant cites its committed source):
  - SPEC_NQ.md s.1/§3/§4/§6  (instrument identity, session law, event PIT, folds/K-views)
  - CALENDAR_PIT_POLICY_NQ.md s.1-6 (session mask, DST quirk, H1..H5 fail-closed exclusions,
    FOMC standing-outside, BLS vintage law, D5 pin)
  - COST_CONTRACT_NQ.md s.1-6 (modeled cost ladders; never-consumable list)
  - IDENTITY_BUDGET_NQ.md (+ .json) s.1-4 (draft identity grammar/enumeration, options, gates)
  - exec/symbol_contracts.json "NQ" (tick 0.25 / $5.00 / mult 20 / long_base_sign +1)
  - exec/RUNNER_SPEC_V2.md (tick rounding, ledger shape — CONSUMED read-only)

OUTCOME-BLIND LAW: adapters compute SIGNALS and intended ORDER INTENT on SYNTHETIC
fixtures only. Real-data consumption raises RefusedPendingOwnerDecision("P5-NQ1"):
real-data adapter execution = NOT_RUN (D9 + ceiling + D3 + registration gated).

All functions are pure and deterministic: no randomness, no wall-clock reads,
no I/O beyond an optional read of the committed symbol_contracts.json.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

CT = ZoneInfo("America/Chicago")

# ---------------------------------------------------------------- session law
# SPEC_NQ.md s.1 / CALENDAR_PIT_POLICY_NQ.md s.1: era-A close 16:15 CT through
# 2015-09-18; era-B close 16:00 CT from 2015-09-21 (SESSION_SWITCH_DATE).
SESSION_SWITCH_DATE = date(2015, 9, 21)
RTH_START_MIN = 8 * 60 + 30          # 08:30 CT
ERA_A_CLOSE_MIN = 16 * 60 + 15       # 16:15 CT
ERA_B_CLOSE_MIN = 16 * 60            # 16:00 CT
MAINT_BREAK_MIN = (16 * 60, 17 * 60)  # 16:00-17:00 CT era-B maintenance (documented)

# Held-contract-only law: every fill consumes the held chain only (RC-2.5).
# DST fall-back absolute-24h quirk PRESERVED AS MEASURED (CALENDAR s.2): adapters
# NEVER re-derive session_date from ts — session_date is consumed as carried data.

# ------------------------------------------------------------------ fold law
# SPEC_NQ.md s.6: 4 folds, ES-precedent shape, mapped to cache_v3 era.
FOLDS = {
    "F1": ("2010-06-01", "2012-12-31"),
    "F2": ("2013-01-01", "2017-12-31"),
    "F3": ("2018-01-01", "2021-12-31"),
    "F4": ("2022-01-01", "2026-09-30"),
}
WARMUP_HELD_SESSIONS = 252  # SPEC_NQ.md s.6 (ES precedent), excluded at each fold head
PANEL_END = "2026-09-30"    # scoring coverage end; 2026-10-01 partial tail excluded


def fold_for_date(d: str | date) -> str | None:
    """RC-5.1 fold map. Returns None outside every fold (unscoreable tail)."""
    ds = _as_date(d)
    for fid, (a, b) in FOLDS.items():
        if date.fromisoformat(a) <= ds <= date.fromisoformat(b):
            return fid
    return None


def scoreable_sessions(sessions: list[str], fold_id: str, warmup: int | None = None) -> list[str]:
    """RC-5.2: exclude `warmup` held sessions at the fold head (default law = 252).

    Fold boundaries themselves are enforced by fold_for_date upstream; this
    function applies only the head-warmup exclusion, deterministically.
    """
    if warmup is None:
        warmup = WARMUP_HELD_SESSIONS
    inside = [s for s in sessions if fold_for_date(s) == fold_id]
    inside.sort()
    return inside[warmup:]


# ------------------------------------------------------------------ K-views
# SPEC_NQ.md s.6: declared evaluation era views (never fold cuts, never identities).
def k_views(d: str | date) -> dict:
    ds = _as_date(d)
    y = ds.year
    kv1 = "A" if ds < SESSION_SWITCH_DATE else "B"
    kv2 = "2010-16" if y <= 2016 else ("2017-21" if y <= 2021 else "2022-26")
    kv3 = ("PRE-2016" if y < 2016 else
           "2016-19" if y <= 2019 else
           "2020-22" if y <= 2022 else "2023-26")
    return {
        "K-V1": kv1,
        "K-V2": kv2,
        "K-V3": kv3,
        "K-V4_covid_window": date(2020, 3, 1) <= ds <= date(2020, 4, 30),
        "K-V5_alias_region": date(2018, 8, 1) <= ds <= date(2020, 6, 30),
        "K-V6_reg_window": date(2014, 10, 1) <= ds <= date(2017, 12, 31),
    }


# ------------------------------------------------------------- cost contract
# COST_CONTRACT_NQ.md s.1-4. All numbers MODELED / UNDER REVIEW /
# VERIFIED_VS_ACCOUNT=NOT_RUN. Never-consumable list (s.6): 1.386, 21.006-class,
# $2.50/tick — none may be produced by this module (refused at the loader).
FEE_ALL_IN_PER_SIDE = {"A": 2.25, "B": 2.24}       # USD/side (A: NFA basis; B: IBKR offset)
SPREAD_HALF_TURN_USD = 16.25                        # 6.5-tick close proxy, high-biased
SLIPPAGE_USD_PER_SIDE = {"S1": 5.00, "S2": 10.00, "S3": 15.00}  # {1,2,3} ticks x $5.00 (D1)
COST_LABELS = ["MODELED COST", "UNDER REVIEW", "VERIFIED_VS_ACCOUNT=NOT_RUN"]
REG_WINDOW_A_EQUALS_B = (date(2014, 10, 1), date(2017, 12, 31))


def cost_per_side_usd(tier: str, stress: float = 1.0, variant: str | None = None) -> dict:
    """Per-side all-in cost, COST_CONTRACT_NQ.md s.3/s.4 shape.

    variant=None (fail-closed default while P5-NQ3/D3 is unsigned): Variant A,
    basis only. Requesting Variant B while P5-NQ3 is unsigned raises
    RefusedPendingOwnerDecision("P5-NQ3").
    """
    if tier not in SLIPPAGE_USD_PER_SIDE:
        raise ValueError(f"unknown cost tier {tier!r}")
    if stress not in (1.0, 1.5, 2.0):
        raise ValueError("stress must be one of 1.0/1.5/2.0 (no double-stress law)")
    if variant is None:
        variant = "A"
        d3 = "OPEN — Variant A basis-only default (COST_CONTRACT_NQ.md s.1)"
    else:
        if variant not in ("A", "B"):
            raise ValueError("variant must be 'A' or 'B'")
        if variant == "B" and GUARDS["P5-NQ3"] is None:
            raise RefusedPendingOwnerDecision(
                "P5-NQ3", "Variant B (IBKR offset basis 2.24/side) requires the D3 "
                          "regulatory-basis ruling; unsigned -> Variant A basis-only default")
        d3 = "RULED" if GUARDS["P5-NQ3"] is not None else "OPEN — Variant A basis-only default"
    per_side = (FEE_ALL_IN_PER_SIDE[variant] + SPREAD_HALF_TURN_USD
                + SLIPPAGE_USD_PER_SIDE[tier]) * stress
    return {
        "variant": variant,
        "d3_status": d3,
        "tier": tier,
        "stress": stress,
        "fee_all_in_usd": FEE_ALL_IN_PER_SIDE[variant],
        "spread_half_turn_usd": SPREAD_HALF_TURN_USD,
        "slippage_usd": SLIPPAGE_USD_PER_SIDE[tier],
        "cost_per_side_usd": round(per_side, 6),
        "cost_rt_usd": round(2.0 * per_side, 6),
        "labels": list(COST_LABELS),
        "forbidden_words_respected": True,
    }


# ------------------------------------------------------------ decision slots
# GAPS_AND_DECISIONS_NQ.md s.(b): owner decisions are namespaced P5-NQ*.
# Fail-closed: None == UNSIGNED. No lane may sign; the FREEZE-WIRING lane wires
# the owner-signature path later. Slots consulted here:
#   P5-NQ1  ADOPT-D9 Option A (chain of record) — real-data consumption gate
#   P5-NQ2  NQ identity ceiling + clock-shadow reading — option-binding gate
#   P5-NQ3  D3 regulatory basis — Variant-B cost gate (A basis-only default)
#   P5-NQ5  EXPWITCH leg disposition — consulted by the refusal stub record only
#           (the leg stays DEAD-AT-GATE: the stub refuses regardless of any state)
#   P5-NQ6  calendar-2026 posture — consulted only by the documented bypass helper
#           unexclude_2026(); the fail-closed exclusions stand while unsigned
GUARDS: dict[str, None | dict] = {
    "P5-NQ1": None,
    "P5-NQ2": None,
    "P5-NQ3": None,
    "P5-NQ5": None,
    "P5-NQ6": None,
}


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


class RefusedD5PinMissing(Exception):
    """RC-3.4: a 2026-window F2 evaluation without the D5 CPI pin (2026-02-13)."""

    code = "REFUSED_D5_PIN_MISSING"

    def __init__(self, detail: str = ""):
        self.detail = detail
        super().__init__("D5 pin absent from the BLS vintage table for a 2026 evaluation"
                         + (f": {detail}" if detail else ""))

    def record(self) -> dict:
        return {"code": self.code, "detail": self.detail}


class RefusedSessionMaskMismatch(Exception):
    """RC-2.1: session mask vs measured last-minute disagreement -> refuse."""

    code = "REFUSED_SESSION_MASK_MISMATCH"

    def __init__(self, detail: str = ""):
        self.detail = detail
        super().__init__("session-mask mismatch" + (f": {detail}" if detail else ""))

    def record(self) -> dict:
        return {"code": self.code, "detail": self.detail}


class PanelError(Exception):
    code = "REFUSED_PANEL_INVALID"


def require_synthetic(panel: dict) -> None:
    """P5-NQ1 gate: real-chain consumption requires ADOPT-D9 Option A (unsigned).

    Any panel whose provenance is not SYNTHETIC refuses. This is the adapter-side
    form of the law "real-data adapter execution = NOT_RUN".
    """
    prov = panel.get("provenance")
    if prov != "SYNTHETIC":
        raise RefusedPendingOwnerDecision(
            "P5-NQ1",
            f"panel provenance {prov!r} is not SYNTHETIC: consuming any real chain "
            f"(cache_v3) requires ADOPT-D9 Option A (P5-NQ1) + ceiling (P5-NQ2) + "
            f"D3 (P5-NQ3) + registration; real-data adapter execution = NOT_RUN")


def bind_option(option_id: str) -> dict:
    """Bind an identity-budget option (NQ-A/B/C) — P5-NQ2 gated.

    NQ-D is refused unconditionally (EXPWITCH leg DEAD-AT-GATE — SPEC_NQ.md s.8.1).
    While P5-NQ2 is unsigned, NO option may bind: the draft enumeration stays
    provisional DRAFT-CODE and never constitutes a scored denominator.
    """
    if option_id == "NQ-D":
        from expwitch_refusal import ExpwitchDeadAtGate
        raise ExpwitchDeadAtGate(
            "option NQ-D has no lawful path: EXPWITCH-NQ leg DEAD-AT-GATE "
            "(SPEC_NQ.md s.8.1; P5-NQ5 is the owner's data-plane route)")
    if option_id not in ("NQ-A", "NQ-B", "NQ-C"):
        raise ValueError(f"unknown option {option_id!r}")
    if GUARDS["P5-NQ2"] is None:
        raise RefusedPendingOwnerDecision(
            "P5-NQ2",
            f"binding option {option_id} requires the owner NQ ceiling signature + "
            f"clock-shadow reading (a)/(b); unsigned -> no registration is lawful")
    return {"option_id": option_id, "bound_by": GUARDS["P5-NQ2"]}


def unexclude_2026(*_args, **_kwargs) -> None:
    """Documented P5-NQ6 bypass helper — ALWAYS refuses while unsigned.

    The 2026 dubious-day fail-closed exclusions (CALENDAR_PIT_POLICY_NQ.md s.3
    H2/H3) stand unless the owner rules the bounded permitted-route extension.
    """
    if GUARDS["P5-NQ6"] is None:
        raise RefusedPendingOwnerDecision(
            "P5-NQ6", "2026 calendar residual posture: fail-closed exclusions stand; "
                      "a permitted-route extension is owner-only (D12 posture applied to NQ)")
    raise PanelError("P5-NQ6 signed path is outside ADAPT-NQ scope (FREEZE-WIRING lane)")


# --------------------------------------------------------- identity budget
# IDENTITY_BUDGET_NQ.md s.3 / identity_budget_nq.json — DRAFT grammar
# FBNQ1-<FAM>-<ARM>-<TAIL>-<DELAY>-<TIER>; DRAFT cycle token FBNQ1 (registered
# cycle ID replaces it verbatim). Tiers all S2 (CONV-B core).
CONVENTION = "CONV-B"
DRAFT_TOKEN = "FBNQ1"


def core_ids(family: str) -> list[str]:
    if family == "NQ-F1":
        arms_tails = [(a, t) for a in ("CONT", "REV") for t in ("UP", "DN")]
        return [f"{DRAFT_TOKEN}-F1-{a}-{t}-{d}-S2"
                for (a, t) in arms_tails for d in ("D0", "D30")]
    if family == "NQ-F2":
        arms_tails = [(a, t) for a in ("CONT", "REV") for t in ("UP", "DN")]
        return [f"{DRAFT_TOKEN}-F2-{a}-{t}-{d}-S2"
                for (a, t) in arms_tails for d in ("D0", "D30")]
    if family == "NQ-F3":
        return [f"{DRAFT_TOKEN}-F3-{a}-{t}-D0-S2"
                for a in ("CONT", "REV") for t in ("UP", "DN")]
    if family == "NQ-F4":
        return [f"{DRAFT_TOKEN}-F4-{a}-{t}-D0-S2"
                for a in ("CONT", "REV") for t in ("UP", "DN")]
    raise ValueError(f"unknown family {family!r}")


def control_ids(family: str) -> list[str]:
    if family not in ("NQ-F1", "NQ-F2", "NQ-F3", "NQ-F4"):
        raise ValueError(f"unknown family {family!r}")
    f = family.split("-")[1]
    return [f"{DRAFT_TOKEN}-{f}-SHDW-D0-S2", f"{DRAFT_TOKEN}-{f}-ALW-D0-S2",
            f"{DRAFT_TOKEN}-{f}-FLAT"]


def family_identity_counts() -> dict:
    return {f: {"core": len(core_ids(f)), "controls": 3,
                "minimal_total": len(core_ids(f)) + 3}
            for f in ("NQ-F1", "NQ-F2", "NQ-F3", "NQ-F4")}


# ------------------------------------------------------------- instrument law
def load_nq_contract(path: str | Path | None = None) -> dict:
    """Load + bind the NQ contract row from exec/symbol_contracts.json.

    RC-1.1/1.2: tick 0.25 pt, $5.00/tick, multiplier 20, long_base_sign +1.
    A $2.50/tick configuration is refuse-worthy (P5-NQ4 defect guard, RC-1.1).
    The invariant tick_value/tick_size == multiplier is statically asserted.
    """
    if path is None:
        path = Path(__file__).resolve().parents[1] / "exec" / "symbol_contracts.json"
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    c = data["contracts"]["NQ"]
    tick, tval, mult = float(c["tick_size"]), float(c["tick_value_usd"]), float(c["multiplier"])
    if tval == 2.5:
        raise PanelError("NQ $2.50/tick configuration is refuse-worthy (P5-NQ4 defect guard)")
    if (tick, tval, mult) != (0.25, 5.0, 20.0):
        raise PanelError(f"NQ contract numbers diverge from the bound identity: "
                         f"tick {tick}, ${tval}/tick, mult {mult}")
    if abs(tval / tick - mult) > 1e-9:
        raise PanelError("tick_value/tick_size != multiplier invariant violated")
    if int(c["long_base_sign"]) != 1:
        raise PanelError("NQ long_base_sign must be +1 (USD per index point)")
    return {
        "ticker": c["ticker"], "exchange": c["exchange"],
        "tick_size": tick, "tick_value_usd": tval, "multiplier": mult,
        "quote_ccy": c["quote_ccy"], "base_ccy": c["base_ccy"],
        "long_base_sign": int(c["long_base_sign"]),
        "source": str(path),
        "verification_note": ("lane-bound numbers per SPEC_NQ.md s.1 "
                              "(PASS_ARITHMETIC_TRIANGULATED; direct vendor capture NOT_RUN, "
                              "P5-NQ4-adjacent); runner-side PLACEHOLDER markers are "
                              "EXEC-lane data law and do not block adapter binding"),
    }


NQ_TICK = 0.25


def round_to_tick(px: float, tick: float = NQ_TICK) -> float:
    """Identical arithmetic to exec/scored_runner_v2.py::round_to_tick."""
    return round(round(px / tick) * tick, 10)


def on_tick_grid(px: float, tick: float = NQ_TICK) -> bool:
    return abs(px / tick - round(px / tick)) < 1e-9


# ------------------------------------------------------------------ helpers
def _as_date(d: str | date) -> date:
    return d if isinstance(d, date) else date.fromisoformat(str(d)[:10])


def _nth_weekday(y: int, month: int, weekday: int, n: int) -> date:
    d = date(y, month, 1)
    delta = (weekday - d.weekday()) % 7
    return d + timedelta(days=delta + 7 * (n - 1))


def ct_offset_str(d: str | date) -> str:
    """America/Chicago UTC offset for a date (CDT -05:00 Mar->Nov, CST -06:00).
    DST law: second Sunday March -> first Sunday November. Used to STAMP
    synthetic fixture bars; the adapter never re-derives session semantics
    from it (DST quirk preserved-as-measured law, CALENDAR s.2)."""
    d = _as_date(d)
    if _nth_weekday(d.year, 3, 6, 2) <= d < _nth_weekday(d.year, 11, 6, 1):
        return "-05:00"
    return "-06:00"


def parse_ts(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        raise PanelError(f"bar ts must carry a tz offset (CT-stamped chain law): {ts!r}")
    return dt.astimezone(CT)


def ct_minutes(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


def era_for_date(d: str | date) -> str:
    return "A" if _as_date(d) < SESSION_SWITCH_DATE else "B"


def era_close_min(d: str | date) -> int:
    """Era-correct regular close (CALENDAR s.1). Era-A Fridays are NOT asserted
    here: their close is handled per-session by the measured last minute (RC-2.2)."""
    return ERA_A_CLOSE_MIN if era_for_date(d) == "A" else ERA_B_CLOSE_MIN


def validate_panel(panel: dict) -> None:
    """Minimal structural validation; provenance gate (P5-NQ1) enforced by
    require_synthetic() at every adapter entry point."""
    if panel.get("schema") != "adapt_nq/synthetic_panel@1":
        raise PanelError(f"panel schema must be adapt_nq/synthetic_panel@1, got "
                         f"{panel.get('schema')!r}")
    for key in ("contract", "sessions", "bars"):
        if key not in panel:
            raise PanelError(f"panel missing {key!r}")
    for bar in panel["bars"]:
        for k in ("ts", "open", "high", "low", "close", "volume", "session_date"):
            if k not in bar:
                raise PanelError(f"bar missing {k!r}")
        if not on_tick_grid(float(bar["open"])) or not on_tick_grid(float(bar["close"])):
            raise PanelError(f"bar price off tick grid: {bar}")


def bars_upto(panel: dict, asof: str | datetime) -> list[dict]:
    """PIT read: only bars with ts <= asof. Every adapter read goes through this."""
    a = asof if isinstance(asof, datetime) else parse_ts(asof)
    return [b for b in panel["bars"] if parse_ts(b["ts"]) <= a]


def session_bars(panel: dict, session_date: str, upto: str | datetime | None = None) -> list[dict]:
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


def rth_core_coverage(panel: dict, session_date: str) -> float | None:
    """RC-2.4 coverage law: minutes-with-bar share of [08:30 CT, era-correct close).

    Consumed from the panel's per-session coverage register (the chain's own
    v3_qc-class property — a SESSION-level disposition). Deliberately NOT
    recomputed from (possibly truncated) 1m bars in any decision path: coverage
    is knowable only at session end, and the decision path must be
    truncation-stable. Bars-derived recomputation lives in
    audit_coverage_from_bars() (verification only).
    """
    sm = session_map(panel).get(session_date)
    if sm is None:
        return None
    cov = sm.get("rth_core_coverage")
    return None if cov is None else float(cov)


def audit_coverage_from_bars(panel: dict, session_date: str) -> float | None:
    """Verification-only recomputation of the coverage share from 1m bars.
    Never used by any decision path (see rth_core_coverage)."""
    bars = [b for b in panel["bars"] if b["session_date"] == session_date]
    if not bars:
        return None
    total = era_close_min(session_date) - RTH_START_MIN
    have = {ct_minutes(parse_ts(b["ts"])) for b in bars}
    return len([m for m in have
                if RTH_START_MIN <= m < era_close_min(session_date)]) / total


def atr20_points(panel: dict, session_date: str, period: int = 20) -> float | None:
    """ATR(period) = mean daily range of the prior `period` held sessions,
    strict past (never includes session_date itself). Daily ranges come from the
    held-session aggregates (chain law: held-contract-only). Returns None when
    fewer than `period` prior sessions exist (insufficient warmup -> NO-TRADE)."""
    sm = session_map(panel)
    prior = sorted(s for s in sm if s < session_date)[-period:]
    if len(prior) < period:
        return None
    return sum(float(sm[s]["high"]) - float(sm[s]["low"]) for s in prior) / period


def fomc_day_set(calendar: dict) -> set[str]:
    """Day-level FOMC statement set (standing-outside law). Untimed 2011-2015
    statements are included at DAY level (time-safe; minute anatomy NOT_RUN)."""
    return {r["date"] for r in calendar.get("fomc_statements", [])}


def fomcin_inverse_include(calendar: dict, all_sessions: list[str]) -> list[str]:
    """FOMCIN-class arms use the inverse include set (SPEC_NQ.md s.4):
    the sessions with NO base-FOMC statement."""
    fomc = fomc_day_set(calendar)
    return sorted(s for s in all_sessions if s not in fomc)


def timed_fomc_events(calendar: dict) -> list[dict]:
    """Timed-14:00-ET event class (the minute-anchored base universe of NQ-F1).
    n=85 on cache_v3 (RC-3.2) — runner-side check; here the injected stamps are
    filtered by class: time_et == '14:00'. Other timed stamps route to the
    EMERGENCY_TIMING sensitivity stratum (excluded from the base universe);
    untimed stamps route to UNTIMED_DAY_LEVEL_ONLY."""
    timed, emergency, untimed = [], [], []
    for r in calendar.get("fomc_statements", []):
        t = r.get("time_et")
        if t is None:
            untimed.append({**r, "stratum": "UNTIMED_DAY_LEVEL_ONLY"})
        elif t == "14:00":
            timed.append({**r, "stratum": "TIMED_1400ET", "anchor_ct": "13:00"})
        else:
            emergency.append({**r, "stratum": "EMERGENCY_TIMING"})
    return timed


def bls_rows_for(calendar: dict, series: str) -> list[dict]:
    return [r for r in calendar.get("bls_vintage", []) if r.get("series") == series]


def require_d5_pin(calendar: dict) -> None:
    """RC-3.4 + CALENDAR s.5: any 2026-window evaluation requires the D5 CPI pin
    (CPI January-2026 release Friday 2026-02-13, embargo 08:30 a.m. ET)."""
    for r in bls_rows_for(calendar, "CPI"):
        if r.get("scheduled_date") == "2026-02-13" and r.get("status", "scheduled") == "scheduled":
            return
    raise RefusedD5PinMissing(
        "CPI 2026-02-13 (D5 pin: pre-release schedule snapshot + release document, "
        "CAL_CLOSE_REPORT.md s.1/s.6-T4) not found in the injected vintage table")


def calendar_2026_dubious_days() -> list[str]:
    """H2/H3 named 2026 suspect windows visible in this cycle-family's captures
    (CALENDAR_PIT_POLICY_NQ.md s.3): EXCLUDE fail-closed for NQ while P5-NQ6 is
    unsigned. The full per-day register is injected calendar data; this constant
    is the named minimum that must never be traded."""
    return ["2026-01-19", "2026-04-03", "2026-07-03"]


def apply_calendar_exclusions(calendar: dict, sessions: list[str],
                              include_fomc: bool = True) -> dict:
    """H2/H3/H4/H5 (+ optionally the FOMC standing-outside day-level law),
    applied deterministically.

    include_fomc=True is the cross-family default (base arms exclude every
    statement day). NQ-F1 (whose UNIVERSE is the timed statement days) calls
    with include_fomc=False and layers its own stratum flags.
    Returns {session_date: [flag, ...]} — non-empty means EXCLUDED (fail-closed
    = NO-TRADE).
    """
    out: dict[str, list[str]] = {}
    fomc = fomc_day_set(calendar) if include_fomc else set()
    early_nt = set(calendar.get("early_close_not_transcribed", []))
    quarters = set(calendar.get("quarters_unproven", []))
    for s in sessions:
        flags: list[str] = []
        if s in fomc:
            flags.append("FOMC_STANDING_OUTSIDE")
        if s in calendar_2026_dubious_days():
            flags.append("H2_H3_2026_DUBIOUS")
        if s in early_nt:
            flags.append("H4_EARLY_CLOSE_NOT_TRANSCRIBED")
        sd = _as_date(s)
        q = f"{sd.year}-Q{(sd.month - 1) // 3 + 1}"
        if q in quarters:
            flags.append("H5_QUARTER_UNPROVEN")
        if flags:
            out[s] = flags
    return out


def apply_exclusions_with_panel(calendar: dict, panel: dict,
                                coverage_threshold: float = 0.60,
                                include_fomc: bool = True) -> dict:
    """Full exclusion pass (H1..H5 + optional FOMC standing-outside)."""
    out = apply_calendar_exclusions(calendar, [s["session_date"] for s in panel["sessions"]],
                                    include_fomc=include_fomc)
    for s in panel["sessions"]:
        sd = s["session_date"]
        cov = rth_core_coverage(panel, sd)
        if cov is not None and cov < coverage_threshold:
            out.setdefault(sd, []).append("H1_RTH_COVERAGE_LT_060")
    return {k: sorted(set(v)) for k, v in out.items()}


def next_session(panel: dict, session_date: str, n: int = 1) -> str | None:
    dates = sorted(s["session_date"] for s in panel["sessions"])
    try:
        i = dates.index(session_date)
    except ValueError:
        return None
    j = i + n
    return dates[j] if j < len(dates) else None


def decision_slot_dependencies() -> list[str]:
    """Every adapter intent carries the full P5-NQ* dependency block it obeys."""
    return ["P5-NQ1", "P5-NQ2", "P5-NQ3", "P5-NQ5", "P5-NQ6"]
