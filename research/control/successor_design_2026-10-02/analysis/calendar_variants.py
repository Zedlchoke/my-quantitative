#!/usr/bin/env python3
"""calendar_variants — corrected LEARN/validation calendar law for
successor_design_2026-10-02 (CALENDAR/EXPOSURE/SELECTION lane revision).

Read-only over dates; writes calendar_variants.json next to this file and
prints the table. Nothing here registers anything; every date is calendar
arithmetic under the conventions stated below, [derived] from cited anchors.

Anchors (all cited in the packet / prior artifacts):
- registration date (this packet's owner-review boundary): 2026-10-02.
- PC12A scored TEST folds: 2022-01-07 -> 2025-12-26
  (PC12A audits/A7_TERMINAL_AUDIT.md:84; RULE_SLATE status header).
- M1 panels of record end 2026-09-23 (poolB data_audit/audit_summary.json
  max_date; RULE_SLATE §6).
- DAILY-EXPLORATORY-V1 exploratory folds 2022-09-30 -> 2026-09-24, fold
  windows per battery/BATTERY_REPORT.md §2; fold-8 vehicle sessions end
  2026-09-23.
- Collector sessions through 2026-09-28
  (DATA-FOUNDATION-SIXSOURCE-V1/ibkr_fx/sessions_index.jsonl, metadata).

CONVENTIONS (stated, single source of truth for this file):
- All windows are end-inclusive calendar-date windows.
- A 26-week fold = 182 days end-inclusive: fold = [start, start + 181d].
- Folds are contiguous: fold k start = fold (k-1) end + 1 day.
- 6 contiguous 182-day folds span 1092 days end-inclusive:
  last fold end = fold-1 start + 1091 days.
- "final readable date" = last fold end + 1 day (the morning after the last
  bar closes; this is the convention RULE_SLATE §6 used: folds from
  2026-09-30 -> "fold 1 readable 2027-03-31"). Both last-fold-end and
  readable are reported.
- Embargo convention (dispatch): fold-1 start = LEARN end + 7 days.
- Warmup: 52 weeks = 364 days end-inclusive immediately before fold-1 start:
  [fold1_start - 364d, fold1_start - 1d].
- Engine cross-check: this convention must reproduce the DAILY battery fold
  table exactly (fold 1 2022-09-30..2023-03-30 ... fold 8
  2026-03-27..2026-09-24); verified below and asserted.

Lawful-source classes for warmup data: {pre-registration data, LEARN data}.
Anything else (embargo window, post-LEARN non-fold data) is flagged.
"""

from __future__ import annotations

import json
import math
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "calendar_variants.json"

D = date.fromisoformat

REGISTRATION = D("2026-10-02")
SCORED_FOLD_END = D("2025-12-26")          # PC12A last scored fold end
SCORED_FOLD_START = D("2022-01-07")        # PC12A first scored fold start
M1_PANEL_END = D("2026-09-23")             # poolB audit max_date
DAILY_FOLD1_START = D("2022-09-30")        # DAILY battery fold 1
DAILY_FOLDS = 8
LAST_SESSION_UTC = "2026-09-28T21:49:31Z"  # sessions_index.jsonl tail (metadata)

WEEK = timedelta(days=7)
FOLD_DAYS = 182          # 26 weeks, end-inclusive
FOLD_LEN = FOLD_DAYS - 1  # start->end day offset (181)
NFOLDS = 6
EMBARGO_DAYS = 7
WARMUP_WEEKS = 52

# Owner-typed sealed tail (SUCCESSOR_PLAN_DRAFT.md item 4, 2026-10-01):
# "the S1 sealed tail (2026-01-02→2026-06-26 — stays SEALED; no unseal is
# authorized)". The protocol draft §1 never pins the tail's dates and its
# 'last 26w of the segment' reading conflicts with this — recorded below.
SEALED_TAIL = (D("2026-01-02"), D("2026-06-26"))


def span_days(a: date, b: date) -> int:
    """End-inclusive day count of [a, b]."""
    return (b - a).days + 1


def weeks_of(days: int) -> float:
    return round(days / 7.0, 2)


def fold_window(start: date, k: int) -> tuple[date, date]:
    """Contiguous end-inclusive fold k (1-based) given fold-1 start."""
    s = start + timedelta(days=(k - 1) * FOLD_DAYS)
    return s, s + timedelta(days=FOLD_LEN)


def folds_table(fold1_start: date, n: int = NFOLDS) -> list[dict]:
    return [
        {"fold": k, "start": str(s), "end": str(e)}
        for k, (s, e) in ((k, fold_window(fold1_start, k)) for k in range(1, n + 1))
    ]


def overlap(a1: date, a2: date, b1: date, b2: date) -> int:
    """End-inclusive overlap in days between windows [a1,a2] and [b1,b2]."""
    lo, hi = max(a1, b1), min(a2, b2)
    return max(0, span_days(lo, hi)) if lo <= hi else 0


def engine_convention_crosscheck() -> dict:
    """Reproduce the DAILY battery fold table (BATTERY_REPORT §2) under this
    file's conventions; assert equality. Evidence the convention matches the
    codebase's existing fold law rather than being invented here."""
    expected = [
        ("2022-09-30", "2023-03-30"), ("2023-03-31", "2023-09-28"),
        ("2023-09-29", "2024-03-28"), ("2024-03-29", "2024-09-26"),
        ("2024-09-27", "2025-03-27"), ("2025-03-28", "2025-09-25"),
        ("2025-09-26", "2026-03-26"), ("2026-03-27", "2026-09-24"),
    ]
    got = [(str(s), str(e)) for s, e in
           (fold_window(DAILY_FOLD1_START, k) for k in range(1, DAILY_FOLDS + 1))]
    ok = got == expected
    assert ok, f"fold convention mismatch: {got}"
    return {
        "reproduces_daily_battery_fold_table": ok,
        "note": ("182d end-inclusive contiguous folds reproduce all 8 DAILY "
                 "fold windows exactly (BATTERY_REPORT.md §2); the same law "
                 "is used for the successor variants below."),
    }


def anchors() -> dict:
    seg_start, seg_end = D("2025-12-27"), M1_PANEL_END
    seg_days = span_days(seg_start, seg_end)
    sealed_start = seg_end - timedelta(days=FOLD_LEN)  # last 26w of segment
    daily_f7 = (D("2025-09-26"), D("2026-03-26"))
    daily_f8 = (D("2026-03-27"), D("2026-09-24"))
    return {
        "registration_date": str(REGISTRATION),
        "pc12a_scored_folds": {
            "start": str(SCORED_FOLD_START), "end": str(SCORED_FOLD_END),
            "days": span_days(SCORED_FOLD_START, SCORED_FOLD_END),
            "weeks": weeks_of(span_days(SCORED_FOLD_START, SCORED_FOLD_END)),
        },
        "never_scored_m1_segment": {
            "start": str(seg_start), "end": str(seg_end),
            "days": seg_days, "weeks": weeks_of(seg_days),
            "days_exclusive_convention": seg_days - 1,
            "packet_claim_check": ("RULE_SLATE §6 / protocol §1 claim "
                                   "'270 days = 38.6w' uses the exclusive "
                                   "day-difference; end-inclusive counting "
                                   "gives 271d = 38.71w. Same fold count "
                                   "either way; no decision changes — "
                                   "convention noted, not a defect."),
            "folds_equivalent": round(seg_days / FOLD_DAYS, 2),
            "sealed_tail_owner_typed": {
                "window": f"{SEALED_TAIL[0]}..{SEALED_TAIL[1]}",
                "days": span_days(*SEALED_TAIL),
                "cite": ("SUCCESSOR_PLAN_DRAFT.md item 4 (2026-10-01): 'the "
                         "S1 sealed tail (2026-01-02→2026-06-26 — stays "
                         "SEALED; no unseal is authorized)'"),
                "conflict_note": ("SUCCESSOR_PROTOCOL_DRAFT §1 implies the "
                                  "tail is inside its 38.6w LEARN segment "
                                  "without pinning dates; a 'last 26w of the "
                                  "segment' reading would be "
                                  f"{sealed_start}..{seg_end} — the two "
                                  "documents disagree; the owner-typed "
                                  "window is used here"),
            },
            "sealed_tail_exposure_via_daily_folds": {
                "fold_7_overlap_days": overlap(*SEALED_TAIL, *daily_f7),
                "fold_8_overlap_days": overlap(*SEALED_TAIL, *daily_f8),
                "note": ("the ENTIRE owner-typed sealed tail lies inside DAILY "
                         "exploratory folds 7-8 (vehicles = the same "
                         "USDJPY/EURUSD M1 panels): sealed != unread — it is "
                         "exploratory-EXPOSED"),
            },
        },
        "daily_folds_covering_segment": {
            "fold_7": {"window": f"{daily_f7[0]}..{daily_f7[1]}",
                        "covers_segment_days":
                            overlap(seg_start, seg_end, *daily_f7)},
            "fold_8": {"window": f"{daily_f8[0]}..{daily_f8[1]}",
                        "covers_segment_days":
                            overlap(seg_start, seg_end, *daily_f8)},
            "conclusion": ("the never-scored M1 segment 2025-12-27->2026-09-23 "
                           "is fully inside DAILY exploratory folds 7-8 (PnL "
                           "computed on the same M1 vehicles, journals on "
                           "disk): exploratory-EXPOSED, not untouched"),
        },
        "standing_owner_directive_conflict": {
            "directive": ("SUCCESSOR_PLAN_DRAFT item 4 (2026-10-01): "
                          "'NO-UNSEAL OPERATIVE ... This supersedes RULE_SLATE "
                          "§4.5's fallback dates and the unseal variants "
                          "(DEAD by owner directive)'; OWNER_DECISION_TABLE "
                          "row SEALED-TAIL: 'ALREADY ANSWERED — stays SEALED'"),
            "conflict": ("SUCCESSOR_PROTOCOL_DRAFT §1 (2026-10-02) lists "
                         "variant A (unseal) as '(recommended)' without "
                         "recording that a standing owner directive marked "
                         "unseal variants DEAD one day earlier; the dispatch "
                         "for this revision nevertheless asks for A to be "
                         "computed — computed here with the conflict flagged "
                         "for owner resolution"),
        },
        "collector_last_session_utc": LAST_SESSION_UTC,
    }


FLOORS_NOTE = ("Calendar dates are outputs of calendar arithmetic plus the "
               "inherited decision floors (20/3/100 per leg per fold, CAM §3, "
               "plus per-rule docket floors). Thin folds type NOT_RUN_THIN and "
               "never widen silently; collector-quiet weeks type BLOCKED_STALE "
               "FLAT weeks and extend the calendar 1:1 (DAILY precedent: 73 "
               "BLOCKED_STALE rows). These dates are NOT absolute time law.")


def warmup_line(fold1_start: date, learn: tuple[date, date],
                sealed: tuple[date, date], label: str) -> dict:
    w_start = fold1_start - timedelta(days=WARMUP_WEEKS * 7)
    w_end = fold1_start - timedelta(days=1)
    pre_reg = overlap(w_start, w_end, D("2021-01-01"),
                      REGISTRATION - timedelta(days=1))
    post_reg = span_days(w_start, w_end) - pre_reg
    in_learn = overlap(w_start, w_end, *learn)
    in_sealed = overlap(w_start, w_end, *sealed)
    in_exposed = overlap(w_start, w_end, SCORED_FOLD_START, SCORED_FOLD_END)
    in_embargo = overlap(w_start, w_end,
                         learn[1] + timedelta(days=1),
                         fold1_start - timedelta(days=1))
    flags = []
    if post_reg > 0:
        classes = []
        if in_learn > 0:
            classes.append(f"{in_learn}d LEARN (lawful class)")
        if in_embargo > 0:
            classes.append(f"{in_embargo}d embargo (NEITHER pre-registration "
                           "NOR LEARN — outside the two lawful warmup classes; "
                           "trim warmup to LEARN end)")
        flags.append(
            f"needs {post_reg}d of POST-registration data at fold-1 time: "
            + "; ".join(classes))
    if in_sealed > 0:
        flags.append(
            f"{in_sealed}d of warmup lies inside the 26w sealed tail "
            f"[{sealed[0]}..{sealed[1]}]: reading it consumes the seal unless "
            "the owner's no-unseal declaration explicitly permits "
            "feature-input reads (feature values only, never outcomes/labels)")
    if in_exposed > 0:
        flags.append(
            f"{in_exposed}d of warmup lies inside the PC12A EXPOSED scored "
            f"window [{SCORED_FOLD_START}..{SCORED_FOLD_END}]: feature inputs "
            "only; any fold-outcome/label read is an exposure violation")
    if w_start <= M1_PANEL_END < w_end:
        flags.append(
            f"{span_days(M1_PANEL_END + timedelta(days=1), w_end)}d of warmup "
            f"({M1_PANEL_END + timedelta(days=1)}..{w_end}) postdate the "
            "frozen M1 panels (end 2026-09-23): D1/H1-derived features there "
            "require live collector-session aggregation (last indexed session "
            f"{LAST_SESSION_UTC}); panels do not exist yet for that slice")
    return {
        "variant": label,
        "window": f"{w_start}..{w_end}",
        "days": span_days(w_start, w_end),
        "weeks": weeks_of(span_days(w_start, w_end)),
        "pre_registration_days": pre_reg,
        "post_registration_days": post_reg,
        "of_which_learn_days": in_learn,
        "of_which_embargo_days": in_embargo,
        "of_which_sealed_tail_days": in_sealed,
        "of_which_exposed_scored_days": in_exposed,
        "classification": ("pre-registration data" if post_reg == 0
                           else "pre-registration + LEARN (post-registration "
                                "part lawful only under the 'or LEARN' clause)"),
        "flags": flags,
    }


def build_variant_A() -> dict:
    learn = (D("2025-12-27"), D("2026-10-01"))
    sealed = SEALED_TAIL  # owner-typed window (SUCCESSOR_PLAN_DRAFT item 4)
    fold1 = REGISTRATION  # dispatch law: fold counting starts at registration
    folds = folds_table(fold1)
    last_end = D(folds[-1]["end"])
    na_folds = folds_table(D("2026-09-24"))
    na_last_end = D(na_folds[-1]["end"])
    primary = {
        "id": "A",
        "status": "COMPUTED (dispatch-specified primary reading)",
        "learn_window": f"{learn[0]}..{learn[1]}",
        "learn_days": span_days(*learn), "learn_weeks": weeks_of(span_days(*learn)),
        "learn_content": ("never-scored M1 segment (2025-12-27..2026-09-23, "
                          "270d, exploratory-EXPOSED via DAILY folds 7-8, "
                          "declared) + fresh collector accumulation "
                          "2026-09-24..2026-10-01 (8d, panels pending)"),
        "embargo": "none specified (dispatch primary); inherited RULE_SLATE "
                   "§4 item-3 1-week-embargo law would push fold 1 to "
                   "2026-10-08 — see variant A_embargoed_1w",
        "fold_1_start": str(fold1),
        "folds": folds,
        "final_readable_date": str(last_end),          # task: readable = last fold end
        "last_fold_end": str(last_end),
        "readable_morning_after": str(last_end + timedelta(days=1)),
        "total_weeks": weeks_of(span_days(learn[0], last_end)),
        "total_days": span_days(learn[0], last_end),
        "validation_weeks": NFOLDS * 26,
        "floors_note": FLOORS_NOTE,
        "warmup_52w_pre_fold_1": warmup_line(fold1, learn, sealed, "A"),
        "dependency": ("owner declaration unsealing the sealed tail as "
                       "LEARN/TRAIN (it can then NEVER count toward "
                       "validation) + collector aggregation for the "
                       "2026-09-24..2026-10-01 LEARN slice. CONFLICT FLAGGED: "
                       "SUCCESSOR_PLAN_DRAFT item 4 (2026-10-01) records the "
                       "sealed tail as 'stays SEALED; no unseal is "
                       "authorized' with unseal variants 'DEAD by owner "
                       "directive' — electing A requires the owner to "
                       "explicitly supersede that directive."),
    }
    no_adjust = {
        "id": "A_no_adjustment",
        "description": ("the reading the current SUCCESSOR_PROTOCOL_DRAFT §1 "
                        "variant-A row implies: fold 1 = 2026-09-24 (the day "
                        "after M1 panel end), ignoring that registration is "
                        "2026-10-02 and fold counting must start at "
                        "registration"),
        "fold_1_start": "2026-09-24",
        "folds": na_folds,
        "last_fold_end": str(na_last_end),
        "readable_morning_after": str(na_last_end + timedelta(days=1)),
        "coowner_figure_check": {
            "coowner_claim": "2026-09-24 + 156w = 2029-09-20",
            "script_result": (f"2026-09-24 + 1091d (6 contiguous end-inclusive "
                              f"folds) = {na_last_end}; readable (end+1) = "
                              f"{na_last_end + timedelta(days=1)}"),
            "verdict": (f"the co-owner's 2029-09-20 equals this file's "
                        f"readable date (last fold end + 1 day) — the "
                        f"ARITHMETIC is right, but the anchor is unlawful: "
                        f"fold 1 cannot start 2026-09-24 because the cycle "
                        f"does not exist before registration 2026-10-02; the "
                        f"8 days 2026-09-24..2026-10-01 are LEARN (or "
                        f"embargo), never fold-1 validation data. Corrected "
                        f"final: {last_end} (readable "
                        f"{last_end + timedelta(days=1)}), 8 days later."),
        },
    }
    return primary | {
        "no_adjustment_reading": no_adjust,
        "draft_table_claim_check": {
            "draft_claim": "A: fold 1 starts 2026-09-24 ... 6 folds complete "
                           "≈ 2029-09-26",
            "verdict": ("internally inconsistent twice: (i) fold-1 start "
                        "predates registration (violates the draft's own "
                        "'fold counting starts at registration' sentence); "
                        "(ii) ≈2029-09-26 is the RULE_SLATE §6 figure for "
                        "fold 1 = 2026-09-30 — with the draft's own fold-1 "
                        "anchor 2026-09-24 the arithmetic gives "
                        f"{na_last_end}/{na_last_end + timedelta(days=1)}, "
                        "and under the registration anchor it gives "
                        f"{last_end}/{last_end + timedelta(days=1)}. The "
                        "quoted completion date follows from neither."),
        },
    }


def build_variant_A_embargoed() -> dict:
    learn = (D("2025-12-27"), D("2026-10-01"))
    sealed = SEALED_TAIL  # owner-typed window (SUCCESSOR_PLAN_DRAFT item 4)
    fold1 = learn[1] + timedelta(days=EMBARGO_DAYS)
    folds = folds_table(fold1)
    last_end = D(folds[-1]["end"])
    return {
        "id": "A_embargoed_1w",
        "status": "COMPUTED (alternative reading, flagged)",
        "why": ("RULE_SLATE §4 item 3 (inherited law) requires a 1-week "
                "embargo between LEARN and fold 1; the dispatch's primary A "
                "starts folds at registration +0. If the owner applies the "
                "embargo law to variant A, this is the calendar. The conflict "
                "is flagged for owner resolution, not silently resolved."),
        "learn_window": f"{learn[0]}..{learn[1]}",
        "learn_days": span_days(*learn), "learn_weeks": weeks_of(span_days(*learn)),
        "embargo_window": f"{learn[1] + timedelta(days=1)}..{fold1 - timedelta(days=1)} "
                          f"({EMBARGO_DAYS - 1}d gap; fold 1 = LEARN end + {EMBARGO_DAYS}d)",
        "fold_1_start": str(fold1),
        "folds": folds,
        "final_readable_date": str(last_end),
        "last_fold_end": str(last_end),
        "readable_morning_after": str(last_end + timedelta(days=1)),
        "total_days": span_days(learn[0], last_end),
        "total_weeks": weeks_of(span_days(learn[0], last_end)),
        "validation_weeks": NFOLDS * 26,
        "floors_note": FLOORS_NOTE,
        "warmup_52w_pre_fold_1": warmup_line(fold1, learn, sealed, "A_embargoed_1w"),
        "dependency": "same as A, plus the embargo election",
    }


def build_variant_A_prime_withdrawn() -> dict:
    return {
        "id": "A_prime",
        "status": "WITHDRAWN — documented, NOT computed as an option",
        "draft_row": ("A′ (max credit) | same LEARN | tail credited as folds "
                      "1–1.5 | ≈ 2028-12-23 | owner accepts 38.6w of "
                      "exposure-adjacent-but-unscored M1 as 1.5 folds"),
        "withdrawal_reasons": [
            "DOUBLE-USE: variant A's own dependency sentence declares the "
            "sealed tail unsealed as TRAIN/LEARN and states it can 'then "
            "NEVER count toward validation'; A′ credits the same 26 weeks as "
            "validation folds 1–1.5. The same data cannot be both the LEARN "
            "window ('same LEARN' per the draft row) and folds 1–1.5.",
            "RELABELING EXPOSURE: the 2025-12-27→2026-09-23 segment lies "
            "inside DAILY-EXPLORATORY-V1 exploratory folds 7–8 (fold 7 "
            "2025-09-26..2026-03-26, fold 8 2026-03-27..2026-09-24; PnL "
            "computed on the same USDJPY/EURUSD M1 vehicles, journals on "
            "disk). Crediting it as validation folds relabels "
            "exploratory-exposed outcomes as validation — the exact maneuver "
            "§1's own law forbids ('the exposed 2021–2025 folds can never be "
            "relabeled validation'; folds 7–8 are 2025-09→2026-09 "
            "exposure-adjacent).",
            "INCOHERENT PARTIAL FOLDS: 'folds 1–1.5' is not a fold boundary "
            "under any end-inclusive arithmetic; a mid-fold credit cannot be "
            "floored (20/3/100 per leg per fold), so the credited material "
            "is unfalsifiable as validation.",
        ],
        "disposition": ("withdrawn from the owner decision menu; if maximal "
                        "credit is wanted, it must be argued as a NEW owner "
                        "declaration in a registered cycle, not as an entry "
                        "in this packet's variant table"),
    }


def build_variant_B() -> dict:
    learn = (D("2026-10-02"), D("2027-04-01"))
    sealed = SEALED_TAIL  # owner-typed window (SUCCESSOR_PLAN_DRAFT item 4)
    assert span_days(*learn) == FOLD_DAYS  # exactly 26w end-inclusive
    fold1 = learn[1] + timedelta(days=EMBARGO_DAYS)
    folds = folds_table(fold1)
    last_end = D(folds[-1]["end"])
    co_fold1 = D("2027-03-31")
    co_folds = folds_table(co_fold1)
    co_end = D(co_folds[-1]["end"])
    return {
        "id": "B",
        "status": "COMPUTED",
        "learn_window": f"{learn[0]}..{learn[1]}",
        "learn_days": span_days(*learn), "learn_weeks": weeks_of(span_days(*learn)),
        "learn_content": ("live forward M1 accumulation from registration; "
                          "sealed tail stays sealed (no unseal)"),
        "embargo_window": f"{learn[1] + timedelta(days=1)}..{fold1 - timedelta(days=1)} "
                          f"({EMBARGO_DAYS - 1}d gap; fold 1 = LEARN end + {EMBARGO_DAYS}d "
                          "= 2027-04-08 as specified)",
        "fold_1_start": str(fold1),
        "folds": folds,
        "final_readable_date": str(last_end),
        "last_fold_end": str(last_end),
        "readable_morning_after": str(last_end + timedelta(days=1)),
        "total_weeks": weeks_of(span_days(learn[0], last_end)),
        "total_days": span_days(learn[0], last_end),
        "validation_weeks": NFOLDS * 26,
        "floors_note": FLOORS_NOTE,
        "warmup_52w_pre_fold_1": warmup_line(fold1, learn, sealed, "B"),
        "dependency": ("collector continuity only (HMDS M1 backfill remains "
                       "NOT_RUN_SIZE_CAP; forward accumulation is the only "
                       "source)"),
        "coowner_claim_check": {
            "coowner_claim": "B: 2027-03-31 + 156w = 2030-03-27",
            "script_result_under_claim_anchor": (
                f"fold 1 = {co_fold1}: 6 contiguous end-inclusive folds end "
                f"{co_end}; readable (end+1) = {co_end + timedelta(days=1)}"),
            "verdict": ("the arithmetic is right under this file's "
                        "conventions — 2027-03-31 + 1091d = "
                        f"{co_end} last fold end, and the co-owner's "
                        "2030-03-27 is the readable (end+1) date. But the "
                        "fold-1 anchor 2027-03-31 is the STALE RULE_SLATE "
                        "§4-item-5 fallback (LEARN 2026-09-24→2027-03-24), "
                        "already corrected by SKEPTIC_SUCCESSOR F-7 and "
                        "OWNER_DECISION_TABLE row N2 (fold 1 2027-04-08, "
                        "battery 2030-04-04): that LEARN starts "
                        "pre-registration (2026-09-24 < 2026-10-02). Under "
                        "the registration-anchored variant B (LEARN "
                        "2026-10-02→2027-04-01, embargo, fold 1 2027-04-08) "
                        f"the battery completes {last_end} (readable "
                        f"{last_end + timedelta(days=1)}), 8 days after the "
                        "co-owner's figure."),
        },
        "draft_table_claim_check": {
            "draft_claim": "B: LEARN 2026-09-24→2027-03-24 | fold 1 2027-03-31 "
                           "| 6 folds complete ≈ 2029-10-01",
            "verdict": ("three errors: (i) LEARN starts 2026-09-24, "
                        "pre-registration — under the registration anchor "
                        "LEARN = 2026-10-02→2027-04-01; (ii) fold 1 2027-03-31 "
                        "is inconsistent with the inherited 1-week-embargo law "
                        "for that LEARN end (LEARN end + 7d = 2027-03-31 only "
                        "if the embargo is counted from 2027-03-24, but the "
                        "corrected convention is fold 1 = LEARN end + 7d); "
                        "(iii) '≈ 2029-10-01' follows from NO convention: with "
                        "the row's own fold-1 anchor 2027-03-31, 6 folds end "
                        f"{co_end} (readable {co_end + timedelta(days=1)}) — "
                        "the row understates its own calendar by ~7 months; "
                        "under the corrected anchor it is "
                        f"{last_end} (readable {last_end + timedelta(days=1)})."),
        },
    }


def learn_window_decision_counts() -> dict:
    """Expected S014/S017 decision counts on a 26-40w LEARN, from the journal
    census (JOURNAL_CENSUS_AND_RECONCILIATION.md; RULE_SLATE §2 floors).
    S014 entries: trig excursions n=24 (POLICY) / n=29 (B1) over the 4y scored
    window. S017 trades: 28 (POLICY) / 39 (B1). Floors: HN-3 / SU-RS-J2
    >=20/window (S014); B-H-G1 / SU-RS-G1 >=50 per arm book (S017);
    SU-RS-J2 >=3 per fold."""
    scored_days = span_days(SCORED_FOLD_START, SCORED_FOLD_END)
    out = {"scored_window_days": scored_days,
           "scored_window_weeks": weeks_of(scored_days),
           "sources": {
               "S014_entries_per_4y": {"POLICY_trig": 24, "B1_trig": 29,
                                        "cite": "RULE_SLATE §2 SU-RS-J2 measured prior; HN-3"},
               "S017_trades_per_4y": {"POLICY": 28, "B1": 39,
                                       "cite": "RULE_SLATE §2 SU-RS-G1; register B-H-G1"},
           },
           "floors": {"S014_window_floor": 20, "S014_per_fold_floor": 3,
                       "S017_arm_book_floor": 50}}
    for label, days in (("variant_A_LEARN_279d", 279), ("variant_B_LEARN_182d", 182)):
        # NB: variant-A LEARN days recomputed below from the real windows to avoid drift
        out[label] = {}
        for leg, (lo, hi) in {"S014_expected_entries": (24, 29),
                               "S017_expected_trades": (28, 39)}.items():
            out[label][leg] = {
                "low": round(lo * days / scored_days, 1),
                "high": round(hi * days / scored_days, 1)}
    # recompute with exact windows
    a_days = span_days(D("2025-12-27"), D("2026-10-01"))
    b_days = span_days(D("2026-10-02"), D("2027-04-01"))
    for label, days in (("variant_A_LEARN", a_days), ("variant_B_LEARN", b_days)):
        out[label] = {"days": days, "weeks": weeks_of(days)}
        for leg, (lo, hi) in {"S014_expected_entries": (24, 29),
                               "S017_expected_trades": (28, 39)}.items():
            out[label][leg] = {"low": round(lo * days / scored_days, 1),
                                "high": round(hi * days / scored_days, 1)}
    out.pop("variant_A_LEARN_279d"); out.pop("variant_B_LEARN_182d")
    lam = 29 * FOLD_DAYS / scored_days  # S014 per-fold expectation (B1 rate)
    out["S014_per_fold_expectation_B1_rate"] = round(lam, 2)
    out["S014_poisson_P_fewer_than_3_per_fold"] = round(
        math.exp(-lam) * (1 + lam + lam * lam / 2), 3)
    out["honest_implication"] = (
        "LEARN (26-40w) expects ~3.6-5.6 S014 entries and ~3.5-7.5 S017 "
        "trades — an order of magnitude below the >=20/window (S014) and "
        ">=50/arm (S017) floors, and S014 sits at ~3.6 per 26w fold, at the "
        ">=3/fold bar (Poisson P(n<3)≈"
        f"{round(math.exp(-lam) * (1 + lam + lam * lam / 2), 2)} per fold, so "
        "NOT_RUN_THIN folds will be routine). LEARN cannot DECIDE anything "
        "about S014/S017 composition; under the corrected selection law "
        "these are preregistered fixed diagnostics on validation folds, "
        "never LEARN- or validation-decided composition changes.")
    return out


def main() -> None:
    result = {
        "schema": "successor_calendar_variants@1",
        "generated_for": "successor_design_2026-10-02 CALENDAR/EXPOSURE/SELECTION lane revision",
        "authority": "calendar arithmetic only; registration/GO are owner actions; nothing here runs",
        "anchor_status_v3": {
            "registration_ts": "PENDING (2026-10-02 anchor ASSUMED — nothing is registered)",
            "go_ts": "PENDING",
            "all_dates": "ILLUSTRATIVE until actual anchors exist",
            "go_gate_law": "fold1_start = max(learn_end + 1 + purge_days, go_date + 1); no validation fold may predate GO",
            "delta_tables": {
                "A": "end_A(delta) = R + delta + 1092d -> delta=1w: 2029-10-05 (read 10-06); delta=4w: 2029-10-26 (read 10-27); delta=0 (2029-09-27) UNLAWFUL: fold 1 would predate GO",
                "B": "end_B(delta) = max(L+delta+1, L+7) + 1091d -> delta=1w: 2030-04-04 (read 04-05); delta=4w: 2030-04-25 (read 04-26)",
            },
            "variant_A_delta0_note": "the committed A/A_emb variant rows below were computed at delta=0 (fold1 = registration day) and are retained as arithmetic reference only; the GO gate above supersedes them",
        },
        "conventions": {
            "windows": "end-inclusive calendar dates (python datetime.date)",
            "fold": "26w = 182 days end-inclusive: [start, start+181d]",
            "contiguity": "fold k start = fold (k-1) end + 1 day",
            "six_fold_span": "last fold end = fold-1 start + 1091 days",
            "final_readable_date": "last fold end (readable_morning_after = end+1 also reported)",
            "embargo": "fold-1 start = LEARN end + 7 days",
            "warmup": "52w = 364 days end-inclusive ending fold1_start - 1",
        },
        "engine_convention_crosscheck": engine_convention_crosscheck(),
        "anchors": anchors(),
        "variants": {
            "A": build_variant_A(),
            "A_embargoed_1w": build_variant_A_embargoed(),
            "A_prime_WITHDRAWN": build_variant_A_prime_withdrawn(),
            "B": build_variant_B(),
        },
        "learn_window_decision_counts": learn_window_decision_counts(),
    }
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")

    print(f"wrote {OUT}\n")
    print("SUCCESSOR CALENDAR VARIANTS (end-inclusive; registration 2026-10-02)")
    print("=" * 100)
    for vid in ("A", "A_embargoed_1w", "A_prime_WITHDRAWN", "B"):
        v = result["variants"][vid]
        print(f"\n[{vid}] status: {v['status']}")
        if vid == "A_prime_WITHDRAWN":
            for r in v["withdrawal_reasons"]:
                print(f"  WITHDRAWN BECAUSE: {r}")
            continue
        print(f"  LEARN            : {v['learn_window']}  ({v['learn_days']}d = {v['learn_weeks']}w)")
        if "embargo_window" in v:
            print(f"  embargo          : {v['embargo_window']}")
        print(f"  fold 1 start     : {v['fold_1_start']}")
        for f in v["folds"]:
            print(f"    fold {f['fold']}: {f['start']} .. {f['end']}")
        print(f"  last fold end    : {v['last_fold_end']}   (readable morning after: {v['readable_morning_after']})")
        print(f"  total            : {v['total_days']}d = {v['total_weeks']}w (LEARN->fold 6 end); validation 156w")
        w = v["warmup_52w_pre_fold_1"]
        print(f"  warmup 52w       : {w['window']}  pre-reg {w['pre_registration_days']}d / "
              f"post-reg {w['post_registration_days']}d (LEARN {w['of_which_learn_days']}d, "
              f"embargo {w['of_which_embargo_days']}d)")
        for fl in w["flags"]:
            print(f"    warmup FLAG: {fl}")
    a = result["variants"]["A"]
    print("\nNO-ADJUSTMENT READING (draft's implied fold 1 = 2026-09-24):")
    na = a["no_adjustment_reading"]
    print(f"  folds end {na['last_fold_end']} / readable {na['readable_morning_after']} "
          f"— co-owner 2029-09-20 = readable date; arithmetic right, anchor "
          f"unlawful (pre-registration fold 1)")
    b = result["variants"]["B"]
    print("\nCO-OWNER CLAIM CHECKS:")
    print(f"  A: 2026-09-24+156w -> {na['readable_morning_after']} readable (co-owner 2029-09-20: arithmetic OK, anchor unlawful)")
    cb = b["coowner_claim_check"]
    print(f"  B: 2027-03-31+156w -> {cb['script_result_under_claim_anchor']}")
    print(f"     verdict: {cb['verdict'][:200]}...")
    dc = result["learn_window_decision_counts"]
    print("\nLEARN-WINDOW DECISION COUNTS (S014/S017 expected):")
    for k in ("variant_A_LEARN", "variant_B_LEARN"):
        print(f"  {k}: {dc[k]['days']}d = {dc[k]['weeks']}w -> "
              f"S014 {dc[k]['S014_expected_entries']['low']}-{dc[k]['S014_expected_entries']['high']} entries "
              f"(floor >=20/window), S017 {dc[k]['S017_expected_trades']['low']}-{dc[k]['S017_expected_trades']['high']} "
              f"trades (floor >=50/arm)")
    print(f"\n  {dc['honest_implication']}")


if __name__ == "__main__":
    main()
