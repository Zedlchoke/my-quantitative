#!/usr/bin/env python
"""producer_skeleton.py -- TB-LABELS offline producer SKELETON (HN-6 prep).

THIS FILE IS A SKELETON. It contains imports, CLI, dataclasses and function
signatures with docstrings that ENCODE the execution laws of
``TB_LABELS_EXECUTION_PREP.md`` (same directory). No barrier evaluation,
no panel decoding beyond type stubs, no journal reads, no writes.

Running this file does NOTHING except print a usage banner and exit 1.
Every compute path raises ``NotImplementedError`` with an explicit
NOT_IMPLEMENTED marker. Implementation may happen ONLY inside a registered,
owner-reviewed cycle (prep section 8 gating law).

Laws encoded here (section numbers = TB_LABELS_EXECUTION_PREP.md):
  - Section 2  feature-label separation firewall (POST_OUTCOME by
    construction; never a feature/eligibility/policy/sizing/arm input).
  - Section 4  AMBIGUOUS_ORDER law: same-M1-bar double-touch => the label
    is AMBIGUOUS_ORDER, never a guessed order; SL-first exists ONLY as the
    frozen uniform resolved_order derived field (TBD INVENTORY_AND_DESIGN
    section 4 'SL-first ambiguous law', lines 373-379); ambiguity counting
    is a first-class output stat reported BEFORE any downstream use.
  - Section 5  quote-side law (long exits at BID, short exits at ASK),
    same-bar spread, fill-lag tagging (NEXT_BAR_OPEN / TOUCH_BAR_QUOTED_SIDE
    / FX6_WORST_FILL / C2C3_CELL per FILL_ACCOUNTING_SPEC sections 1.3,
    1.5, 3), entry-bar evaluation + censoring for the S017 <=1-min class.
  - Section 6  DST-aware sessions via zoneinfo IANA zones (Europe/London),
    holiday calendar = the frozen panels' own recorded sessions
    (DECLARED-PANEL-CALENDAR@1 precedent); NO hardcoded UTC bounds; tzdata
    version pinned in the run manifest.
  - Section 7  MAE/MFE within holding only; CENSORED_FF /
    CENSORED_PANEL_END right-censoring; swap nights journaled, never
    affecting path labels.
  - Section 8  analysis-only identity, 0 scored rows, NOT-a-claim header on
    every output; window allowlist TRAIN/EXPOSED only; sealed tail
    (post campaign end 2026-06-26, panel end 2026-09-23) REFUSED.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import sys
from typing import Dict, Iterable, List, Literal, NoReturn, Optional, Sequence, Tuple

BANNER = "SKELETON NOT FOR EXECUTION"
SPEC_PATH = "research/control/successor_design_2026-10-02/tblabels/TB_LABELS_EXECUTION_PREP.md"
NOT_A_CLAIM_HEADER = (
    "TB-LABELS ANALYSIS-ONLY - POST_OUTCOME BY CONSTRUCTION - "
    "NOT A FEATURE, NOT AN ELIGIBILITY/POLICY/SIZING/ARM INPUT - NO CLAIM"
)

NOT_IMPLEMENTED = (
    "NOT_IMPLEMENTED: skeleton only. The labeling law is specified in "
    f"{SPEC_PATH} and may be implemented only inside a registered, "
    "owner-reviewed cycle (prep section 8 gating)."
)

# Frozen window law (prep section 8): campaign window is the default
# allowlist; anything after campaign end is PC12A sealed-tail class and the
# producer must REFUSE it. Panel coverage ends 2026-09-23 (audit_summary).
CAMPAIGN_START = dt.date(2021, 1, 8)
CAMPAIGN_END = dt.date(2026, 6, 26)  # last decision Friday (calendar_service.py)
PANEL_END = dt.date(2026, 9, 23)

WindowClass = Literal["TRAIN", "EXPOSED"]
ExitClass = Literal[
    "TP", "SL", "TIME", "SIG", "TRAIL", "TIMEOUT",
    "AMBIGUOUS_ORDER",  # prep section 4: same-bar double-touch, never guessed
    "CENSORED_FF", "CENSORED_PANEL_END", "BORN_THROUGH_BARRIER",
]
BarrierOrder = Literal["TP_FIRST", "SL_FIRST", "AMBIGUOUS_ORDER"]
Censoring = Literal["NONE", "CENSORED_FF", "CENSORED_PANEL_END"]
CostLabel = Literal[
    "NEXT_BAR_OPEN",          # decision-basis exits (SIG/TIME) - FILL_ACCOUNTING_SPEC 1.3
    "TOUCH_BAR_QUOTED_SIDE",  # touch-basis barrier exits - TBD 2b/6 spread-once
    "FX6_WORST_FILL",         # gap-through-barrier bars - FILL_ACCOUNTING_SPEC 1.5
    "C2C3_CELL",              # rollover / Sunday-reopen bars - FILL_ACCOUNTING_SPEC 3
]

# Dukascopy M1 record law (panels.py:8-21): 24 bytes, >u4 x5 + >f4,
# field order (sec_offset, open, close, low, high, volume_f32);
# 1440 records/day/side; divisors 1e5 (EURUSD/GBPUSD) and 1e3 (USDJPY).
M1_RECORD_FIELDS = ("sec_offset", "open", "close", "low", "high", "volume")
PRICE_DIVISORS: Dict[str, float] = {"EURUSD": 1e5, "GBPUSD": 1e5, "USDJPY": 1e3}
PIP_SIZES: Dict[str, float] = {"EURUSD": 0.0001, "GBPUSD": 0.0001, "USDJPY": 0.01}

# DST law (prep section 6): IANA zones via zoneinfo, no hardcoded UTC.
LONDON_TZ = "Europe/London"   # engine law: calendar_service.py:33
NEWYORK_TZ = "America/New_York"
HOLIDAY_CALENDAR_NAME = (
    "DECLARED-PANEL-CALENDAR@1 (weekend-skip + each frozen panel's own "
    "recorded sessions; no synthetic holiday model)"
)

# AMBIGUITY GATE (prep section 4 / TBD INVENTORY_AND_DESIGN section 4):
# >20% ambiguous bars => comparability kill; the labels analog types the
# affected leg's forensic reads with a NOT_RUN_TOUCH_RESOLUTION-analog
# qualifier. Reported per symbol x leg BEFORE any downstream use.
AMBIGUOUS_FRACTION_GATE = 0.20


@dataclasses.dataclass(frozen=True)
class M1Bar:
    """One M1 bar on ONE quoted side (bid or ask).

    Panels are per-minute OHLC per side (b_o/b_h/b_l/b_c + ask side);
    bid and ask for the same minute MUST come from the same bar index on
    both side files. A minute is tradable iff vol>0 and ask>=bid>0 (the
    D1_SESSION_1700ET@1 validity rule; weekend flat-carry bars are NOT
    tradable and never contribute to barrier paths - prep section 9.4).
    """

    ts_utc: dt.datetime
    side: str                 # "BID" | "ASK"
    open: float
    high: float
    low: float
    close: float
    volume: float

    @property
    def tradable(self) -> bool:
        raise NotImplementedError(NOT_IMPLEMENTED)


@dataclasses.dataclass(frozen=True)
class BarrierSpec:
    """Entry-information-only barrier set, frozen at the entry fill (prep 3).

    Geometry is either GENERIC (k_U=k_L=1.0 x ATR20_entry on the leg's own
    decision clock, H = realized holding - TBD 2a frozen form) or LEG_OWN
    (the implemented leg's own TP/SL/TIME levels, frozen at entry; where
    corpus intent and implementation diverge, the implementation governs
    and the divergence is carried as a note).
    """

    leg_id: str
    geometry: str             # "GENERIC_1ATR" | "LEG_OWN" | "HYPOTHESIS_BHG2_ONLY"
    tp_level: Optional[float]
    sl_level: Optional[float]
    horizon: Optional[dt.datetime]
    window_mask: Optional[Tuple[str, int, int]]  # (IANA zone, start_min, end_min)
    note: str = ""


@dataclasses.dataclass(frozen=True)
class LabelRow:
    """One output row (schema tb_label_v2@DRAFT superset of tb_label@1).

    Every field group maps 1:1 onto prep sections 4-8. The NOT-a-claim
    header is written at the top of every output file, not per row.
    """

    trade_id: str
    journal_order_id: str
    leg: str
    fold_id: str
    window_class: WindowClass
    direction: int
    entry_ts: dt.datetime
    entry_fill: float
    barriers: BarrierSpec
    exit_ts: Optional[dt.datetime]
    exit_class: ExitClass
    barrier_order: BarrierOrder
    resolved_order: Optional[BarrierOrder]  # uniform SL_FIRST only, prep 4.2
    ambiguous_flag: bool
    mae_pips: Optional[float]               # within holding only (prep 7)
    mfe_pips: Optional[float]
    censoring: Censoring
    cost_label: CostLabel
    entry_bar_touch: bool
    swap_nights: int
    hit_ts: Optional[dt.datetime]


# ---------------------------------------------------------------------------
# Panel + calendar layer (prep sections 5-6)
# ---------------------------------------------------------------------------

def load_m1_day(panel_root: str, symbol: str, day: dt.date) -> Tuple[List[M1Bar], List[M1Bar]]:
    """Decode one day's BID and ASK M1 panels.

    Laws: record struct (sec_offset, open, close, low, high, volume_f32),
    1440 records, 60s grid, price divisor per symbol, coverage assertions
    enforced fail-closed (panels.py). Files are READ-ONLY; the producer
    never writes to panel trees.
    """
    raise NotImplementedError(NOT_IMPLEMENTED)


def session_minutes(ts_utc: dt.datetime, zone_name: str) -> int:
    """Minutes-of-day of ts_utc in the named IANA zone (DST-aware).

    Law (prep 6): zoneinfo IANA zones only (Europe/London etc.); NO
    hardcoded UTC offsets - the S002 16:00 London exit and the S017
    15:30-18:30 window shift in UTC across DST and are derived per-day,
    exactly as the engine does (calendar_service.py / leg_rules.py tz law).
    The tzdata version is pinned in the run manifest.
    """
    raise NotImplementedError(NOT_IMPLEMENTED)


def window_class_of(ts_utc: dt.datetime) -> WindowClass:
    """TRAIN or EXPOSED tag for a timestamp inside the campaign window.

    Law (prep 8): default allowlist = campaign window
    [CAMPAIGN_START, CAMPAIGN_END]; every row is tagged with its class; any
    date in (CAMPAIGN_END, PANEL_END] is PC12A sealed-tail class and MUST
    be refused by the caller (SEALED_TAIL_REFUSED), never labeled.
    """
    raise NotImplementedError(NOT_IMPLEMENTED)


def refuse_sealed_tail(ts_utc: dt.datetime) -> None:
    """Fail-closed refusal for sealed-tail dates (prep 8/9.7)."""
    raise NotImplementedError(NOT_IMPLEMENTED)


# ---------------------------------------------------------------------------
# Barrier construction + evaluation (prep sections 3-5)
# ---------------------------------------------------------------------------

def resolve_barriers_at_entry(leg_id: str, entry_fill: float, entry_ts: dt.datetime,
                              panel_prefix: Iterable[M1Bar]) -> BarrierSpec:
    """Freeze the barrier set from ENTRY-TIME information only (prep 3).

    GENERIC form: U/L = fill +/- 1.0 x ATR20_entry on the leg's own
    decision clock (D1 legs ATR20(D1); H1/H4 legs ATR(20) of the aggregate
    clock; M1 session legs ATR(60 M1)); H = realized holding. LEG_OWN
    form: the implemented leg's levels per the section-3 table (S013
    m+/-2.8sigma, S017 VWAP/1sigma window-masked, S002 range-edge +/-2pip
    + 16:00 London flat, S026 0.5xATR(H1) + 1xATR(D1) ratchet, VC2
    POC/1xATR60 T-QUOTE + tmax 240 + 19:55, S014 1xATR(H4) + RSI2->50 +
    8 bars). Nothing post-entry may enter (TBD 3 leak law).
    """
    raise NotImplementedError(NOT_IMPLEMENTED)


def evaluate_barriers(spec: BarrierSpec, direction: int,
                      path: Sequence[Tuple[M1Bar, M1Bar]]) -> LabelRow:
    """Walk the M1 two-sided path from fill to the trade's actual close.

    Laws (prep 5): quoted-side evaluation only - long TP on bid_high,
    long SL on bid_low, short TP on ask_low, short SL on ask_high (TBD 2b
    four touch cases); spread from the SAME bar's two-sided quotes; the
    ENTRY bar IS evaluated (fill is at its open - FILL_ACCOUNTING_SPEC
    1.3) so the S017 <=1-minute stop-out class is captured, with
    entry_bar_touch=True; a fill bar whose OPEN is already beyond the SL
    is BORN_THROUGH_BARRIER (order determinable - open is first); bars
    outside the leg's window mask (e.g. S017 15:30-18:30 London) are NOT
    evaluated; cost_label tags which campaign fill law prices the exit.
    """
    raise NotImplementedError(NOT_IMPLEMENTED)


def resolve_ambiguous_order(bar: Tuple[M1Bar, M1Bar], spec: BarrierSpec,
                            direction: int) -> NoReturn:
    """AMBIGUOUS_ORDER stub - MUST NEVER guess an intrabar order (prep 4).

    If BOTH barrier levels lie inside the same M1 bar's quoted-side range
    (long: bid_low <= SL < TP <= bid_high; shorts mirrored on ask), the
    intrabar order is UNKNOWN. The label is AMBIGUOUS_ORDER with
    ambiguous_flag=True. The frozen SL-first default (TBD
    INVENTORY_AND_DESIGN section 4 'SL-first ambiguous law', lines
    373-379; DECISION_PACKET.md line 171) exists ONLY as the uniform
    derived field resolved_order=SL_FIRST for consumers that need a
    resolved order, with the ambiguous fraction disclosed alongside.
    This function intentionally has NO implementation beyond the refusal:
    there is nothing to compute.
    """
    raise NotImplementedError(
        NOT_IMPLEMENTED
        + " AMBIGUOUS_ORDER is a recorded state, not a computation: "
        "same-bar double-touch => barrier_order=AMBIGUOUS_ORDER, "
        "ambiguous_flag=True, resolved_order=SL_FIRST (uniform frozen "
        "default), and the bar is counted in the run's ambiguity stats."
    )


def compute_mae_mfe(entry_fill: float, direction: int,
                    held_path: Sequence[Tuple[M1Bar, M1Bar]]) -> Tuple[float, float]:
    """MAE/MFE in pips on the exit-side quoted path, WITHIN holding only.

    Law (prep 7): measured entry->exit only, inside the trade's own
    window/session masks; force-flat and panel-end exits right-censor
    (CENSORED_FF / CENSORED_PANEL_END) but MAE/MFE remain valid up to the
    censor bar; swap-charged nights never affect path labels (journaled
    separately as swap_nights).
    """
    raise NotImplementedError(NOT_IMPLEMENTED)


def cost_label_for_exit(exit_class: ExitClass, exit_bar: Tuple[M1Bar, M1Bar]) -> CostLabel:
    """Tag which campaign fill law prices this exit (prep 5; no pricing here).

    SIG/TIME -> NEXT_BAR_OPEN (FILL_ACCOUNTING_SPEC 1.3: decision at T
    fills at the open of bar [T, T+1min)); TP/SL/TRAIL quoted-side touch
    -> TOUCH_BAR_QUOTED_SIDE (TBD 2b/6 spread-once at the touch bar);
    gap-through-barrier bars -> FX6_WORST_FILL (worst of touch-bar
    open/close on the quoted side, never the barrier price - FAS 1.5);
    rollover-window / Sunday-reopen bars -> C2C3_CELL (FAS 3, corrected
    Mon-Thu cells govern).
    """
    raise NotImplementedError(NOT_IMPLEMENTED)


# ---------------------------------------------------------------------------
# Ambiguity accounting (prep section 4 - first-class output stat)
# ---------------------------------------------------------------------------

def ambiguity_stats(rows: Sequence[LabelRow]) -> Dict[str, float]:
    """Per symbol x leg ambiguity fractions, reported BEFORE downstream use.

    Must emit: ambiguous_trades, ambiguous_fraction_of_labeled_trades,
    ambiguous_bars/evaluated_bars (TBD section 4's own denominator), and
    the same restricted to entry-bar touches (the S017 hazard class). A
    leg over AMBIGUOUS_FRACTION_GATE (20%) carries the
    NOT_RUN_TOUCH_RESOLUTION-analog qualifier on every forensic read.
    The first real run's report is a gating artifact; no estimate of it
    exists today (this prep ran over no data).
    """
    raise NotImplementedError(NOT_IMPLEMENTED)


# ---------------------------------------------------------------------------
# Orchestration (prep section 8) - gated, refuses sealed tail
# ---------------------------------------------------------------------------

def run(panel_root: str, symbol: str, legs: Sequence[str], window: str,
        dry_run: bool) -> NoReturn:
    """Produce labels for one symbol x legs over an approved window.

    Laws: analysis-only identity (0 scored rows, NOT-a-claim header on
    every output file, run manifest with input hashes + tzdata version +
    spec sha); window allowlist TRAIN/EXPOSED only (sealed tail refused
    fail-closed); outputs = label jsonl/parquet per symbol x leg with the
    LabelRow schema + run_manifest.json with ambiguity_stats; every run
    is one ledger row.
    """
    raise NotImplementedError(NOT_IMPLEMENTED)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="producer_skeleton.py",
        description=(
            "TB-LABELS offline producer (HN-6) - SKELETON. Spec: " + SPEC_PATH
        ),
    )
    parser.add_argument("--panel-root", required=False,
                        help="read-only M1 panel root (absolute path; "
                             "default roots are the audited frozen paths)")
    parser.add_argument("--symbol", required=False,
                        choices=sorted(PRICE_DIVISORS),
                        help="one of EURUSD/GBPUSD/USDJPY (the 3 staged pairs)")
    parser.add_argument("--legs", required=False, nargs="*",
                        help="leg ids (e.g. GBPUSD-S017 EURUSD-S013 VC2-LVNFAIL-GBPUSD)")
    parser.add_argument("--window", required=False,
                        help="window spec: TRAIN | EXPOSED | campaign-dated allowlist; "
                             "sealed tail (post %s) is refused" % CAMPAIGN_END)
    parser.add_argument("--dry-run", action="store_true",
                        help="accepted for interface compatibility; the skeleton "
                             "still performs nothing")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    print("=" * 72)
    print(BANNER)
    print("=" * 72)
    print("TB-LABELS offline producer SKELETON (HN-6 prep lane).")
    print("Spec (read before any implementation):")
    print("  " + SPEC_PATH)
    print(NOT_A_CLAIM_HEADER)
    print(f"parsed args (NOT executed): {vars(args)}")
    print("This skeleton performs no panel read, no journal read, no labeling,")
    print("and no write. Implementation is gated on owner review of the prep")
    print("(prep section 8) inside a registered cycle.")
    print(BANNER)
    return 1


if __name__ == "__main__":
    sys.exit(main())
