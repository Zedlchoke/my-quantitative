# CALENDAR_PIT_POLICY_6J_6A — calendar/PIT state and fail-closed exclusion law

- Lane FXJA, round FUTURES-5SYM-PRESCORED-20261005, PREP-only. This is a
  STATE-OF-EVIDENCE policy document: what is decision-time-knowable per
  symbol, what is proven absent, and what must be excluded fail-closed.
  0 PnL, 0 network this lane. Missing evidence = NOT_RUN / NOT_OBTAINED,
  **never inferred, never rule-derived** (IMM-rule expiry derivation
  FORBIDDEN; current-calendar inference FORBIDDEN).

## §1 Per-symbol expiry-cell states (68-cell grid 2010–2026)

| symbol | state | provenance of OBTAINED cells | NOT_OBTAINED remainder |
|---|---|---|---|
| **6J** | **62/68** (was 58/68; +4 dual-vintage 2026 quarters, CAL_JANQ) | 52 official FxCAL 2010–2022 + 6 Q5-capture rows (2024Q3–2025Q4) + J1H26 2026-03-16 / J1M26 2026-06-15 / J1U26 2026-09-14 / J1Z26 2026-12-14 (identical in re-verified Q5 XLS sha `09a85ef7…` and new Nov-2025 XLS sha `f4ed4513…`; own parsers, sha-verified inputs) | **6 cells: 2023Q1–Q4 + 2 cells whose identity is not determinable from captures** (dispatch said 10 missing; bounded scope 8; the other 2 flagged to the owner, NOT inferred). Absence evidence: `Future/69` CDX = 3 pre-span captures (2015/2017), `Download.xls?productId=69` = 2024-09-04 + 2025-11-04 only (post-expiry drop; no capture crawled 2017-07-28..2024-09-04) — `cal_janq/captures/cdx_future69.txt`, `cdx_dl69.txt` |
| **6A** | **66/68** (was 62/68; +4 single-vintage 2026 quarters, CAL_JANQ) | 52 official FxCAL 2010–2022 + 10 Q5-capture rows (2023Q3–2025Q4) + ADH26 16 Mar / ADM26 15 Jun / ADU26 14 Sep / ADZ26 14 Dec 2026 from the re-verified Sep-2023 capture `pcal_37_6a_20230916051415.json` (sha `dad89c31…`) | **exactly 2023Q1 (Mar) and 2023Q2 (Jun)**. Absence evidence: `Future/37` CDX = pre-span captures + 2023-09-16 (first row ADU23, post-expiry); `Download.xls?productId=37` = zero archived captures (0-byte CDX result, 2 attempts — transport law honored) — `captures/cdx_future37.txt`, `cdx_dl37.txt` |

Cell rule: every cell consumed at a future freeze carries provenance
**OBTAINED (file + sha256, or fetch-log line)** or **NOT_OBTAINED**; a
quarter whose roll/expiry status cannot be proven from cells + bar-side
validation is **EXCLUDED fail-closed, whole-quarter** (ES precedent E2).
All extracted official lastTrade dates ≥ observed last-bar session
(identity cross-check clean, both symbols).

## §2 Holiday grid states

| item | 6J | 6A |
|---|---|---|
| Measured data holes | 2023: exactly 2 missing weekdays — 2023-01-02 (New Year), 2023-12-25 (Christmas), both exchange holidays (`fx_ja/session_holes_2023.json` sha `58b4faa4…`) | Mar-2023: 23 traded weekday sessions; Jun-2023: 22; **zero missing weekdays** — the "Mar/Jun-2023 gap" is an expiry-pointer cell, not a data hole |
| Holiday session TIMES (early-close minutes) | **NOT_OBTAINED 2024–25**; in-corpus FXCAL per-family times 2017–2023 only | **NOT_IN_CORPUS for every year** (same open cell) |
| Product-code deviation windows | **0/42** (no archived trading-hours capture carries id 69) | **0/42** (id 37; `trading-hours-holiday-download` replays HTTP 403 at Wayback edge — BLOCKED_TRANSPORT, 2 attempts honored) |
| Standing exclusion law | holiday-shortened sessions EXCLUDED by deterministic bar-count/coverage rules (JF3: Tokyo window ≥80% of nominal bars else EXCLUDE); the exclusion list is script-generated at freeze, sha-pinned, never edited post-GO | same; partial 2026-10-01 tail (~2h) ends full-session statistics at 2026-09-30 on both symbols |

## §3 BoJ calendar law (6J) — what is decision-time-knowable

- **Knowable at decision time: the MPM DECISION DATES.** 54 decision dates
  2020–2026 measured from the in-corpus statement archive (156 statement
  files 2011-01-25..2026-09-18; 30 dated decisions 2023–2026; 17 mpmdeci
  index files; "day-2 statements" = decisions announced on day 2 of each
  2-day MPM). Titled regime-change labels: 4 measured + 2 v1-FACT
  (2026-06-16, 2026-09-18).
- **NOT knowable at decision time: the intraday release stamp.**
  **NOT_IN_CORPUS — no minute-level release timestamp exists for any BoJ
  statement.** Owner decision owns stamps. Consequences (binding):
  1. JF1 uses the **12:00–15:30 JST window convention** as anchor — declared,
     never claimed as a release time; signal evaluation at window close;
  2. the K3 anchor-robustness law substitutes for minute anchoring
     (descriptive anatomy delivered: ANCHOR_INSENSITIVE_AT_45MIN,
     W0 lead −9.78 pp on MPM range share, n=54);
  3. **no arm may condition on "the minute BoJ spoke"** — any such claim is
     PIT-illegal on this corpus.
- mpmdeci TITLES coverage 2018→2026-01 only; the two 2026 titles are
  v1-FACT (boj.or.jp 2026-10-02), not in the archive PDFs. Surprise
  classification NOT_RUN (buildable $0; no consensus series in corpus).
- MOF (JF2): 386 daily ops 1991-05-13..2026-05-06 (regenerated tidy
  verified; 81-row `.bak` forbidden). **Publish-lag law: op amounts ~1 month
  (monthly) / quarterly (daily detail) after the fact. Decision-time-knowable
  = nothing about a same-day op; JF2 labels are built on DISCLOSURE dates
  only.** The 2026-07-30 window is NOT MOF-verified (price anatomy only).
- US-side DFF: 16 year-end vintages (2010–2024 + 2026-09-30; **no 2025
  vintage**). Vintage law: `available_time = vintage(decision_date)`;
  current-calendar inference FORBIDDEN. BLS 2025-vintage law (BLSV) applies
  if US macro ever conditions a 6J arm.

## §4 RBA calendar law (6A) — AF1 conditioning

- **Knowable: 395 dated RBA cash-rate decisions 1990-08-02..2026-09-30**
  (`rba/cash_rate_gate.html`, sha-verified in the readiness lane); 2023–2026
  = 33 dated decisions (11/8/8/6), 12 changes; 2026 remaining (v1-FACT):
  Nov 3, Dec 8.
- **NOT carried by the file: the decision TIME.** The **14:30 Sydney anchor
  stays a DECLARED convention** (6A_DEEP §4.1): anchor = 14:30 Sydney on
  effective_date − 1 AU business day; the single off-Tuesday case
  (2020-03-19 COVID emergency cut) is flagged and the rule still lands
  correctly. AF1 may use decision dates as PIT facts; it may NOT claim a
  verified release minute.
- Surprise classification NOT_RUN (change-vs-hold weak proxy measured:
  59 vs 29 ticks). FOMC statement days (147 archived, 2011-01→2026-09) are
  AF1 base-EXCLUDES — the measured US common factor on 6A (±5' 8.2× volume)
  is LARGER than RBA's.
- **NOT_RUN (standing, blocks AF3 K4):** ABS CPI/Labour-Force historical
  release dates; China Caixin/NBS calendars — the AF3 base spec's own K4
  kills it without a China calendar; no acquisition proposed by this lane.

## §5 Fail-closed exclusion inventory (per-symbol, generated at freeze)

Every item below is EXCLUDED unless the calendar proves otherwise; the
freeze-time script emits the explicit dated list + reason per entry and
sha-pins it (ES E1–E5 shape):

1. Quarters with any unproven expiry/roll cell (whole-quarter): **6J
   2023Q1–Q4 + 2 unidentified cells; 6A 2023Q1/Q2** — until cells are
   obtained from a permitted route (never derived).
2. Holiday-shortened / early-close sessions whose FX session times cannot
   be proven (all years until obtained; 2024–25 explicitly NOT_OBTAINED).
3. Sessions failing bar-count/coverage floors (JF3 Tokyo-window <80%; the
   session-level coverage rule), incl. the 2026-10-01 partial tail.
4. BoJ MPM dates for JF3/JF2-host excludes; MOF disclosure dates per the
   lag law; FOMC statement days for AF1 (59 in panel per AF1 f5 — day-level,
   safe-in-time).
5. 6A: `6BU5` contaminant bars (1,584) and instrument-7084 strays (914) —
   excluded at panel level by documented rule (not calendar, listed here for
   completeness of the exclusion surface).
6. Roll-boundary artifacts: 6J 2022-09-20 held-dead session (baseline chain)
   and 6A 2024-12-17 / 2026-06-16 vanished sessions enter NO held-bar
   statistic under the baseline chains; the cease-guard variant eliminates
   them — chain choice disclosed, never silently normalized (RMM K6(c)).
7. Calendar-uncertain dates anywhere ⇒ EXCLUDE/NOT_RUN (DC §1.2), never
   imputed, never patched by inference.

— End CALENDAR_PIT_POLICY_6J_6A. 0 PnL; no fetches this lane; all citations
to committed artifacts (sha256 where load-bearing).
