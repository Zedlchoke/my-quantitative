# DATA_READINESS_ES — 8-dimension data-readiness dossier

Round **FUTURES-SIX-READINESS-20261004**, lane **ES-READINESS**. 2026-10-04 UTC.
Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep`,
branch `codex/futures-six-readiness-20261004`, HEAD measured `d7fc62312947b2613523dd401d44c9ec1a8d166b`
(== dispatch base; resolved by reading gitdir files — this lane ran NO git commands).

Scope law honored: re-verification from existing artifacts only; **no PnL, no scored
cells, no S1 access, no new hypotheses, no network access**. Missing evidence is
NOT_RUN, never inferred PASS. Every number below traces to an artifact this lane
actually read, or to a re-derivation script committed under `es/`.

## Verdict table

| # | Dimension | Verdict | Evidence pointer (this lane unless noted) |
|---|---|---|---|
| 1 | identity/tick | **PASS** | `es_readiness.json` dim 1; ES mult 50, tick 0.25 = $12.50, CME Globex (ES_DEEPFOUR_V3_ADDENDUM §1 FACT rows; SPEC_PB1_ES §1 binding); 7,825,657-bar panel re-measured, exact |
| 2 | O1M coverage + holes | **PASS** | `es/es_o1m_roll_recheck.json`; 4,204 sessions, span 2010-06-06..2026-10-01, era coverage ~97%→100%, 0 OHLC violations; residuals: minute-gap 0.03-0.90%/era, 24,653 residual maintenance-window prints (disclosed) |
| 3 | roll/expiry | **PASS** | `es/es_expiry_recheck.json` — **68/68 re-derived** (37 D3 product + 26 DEEPFOUR family + 5 OVERNIGHT gap; 0 conflicts); 67× 3rd-Friday + ESM6 Juneteenth 2026-06-18; spacing 84-98d; 66/66 data-side expiries match; 5 gap-quarter dates byte-grepped in archived captures (G1a all 5, G1b 4/5, NQ 5/5); roll rule **OBSERVED** |
| 4 | session/holiday | **PASS** | `es/es_session_holiday.json` — 17/17 year windows authority-backed (D3); era-correct closes OBSERVED (16:30/16:15/16:00 CT); **2026 weekly + 11 deviation windows OBTAINED_PERMITTED and independently verified from Q5 raw bytes** (15/15 present captures sha256-match, 23/23 claimed cells reproduced); 161 date + 36 event-row legality checks all legal; 2011-2025 unproven product days EXCLUDE fail-closed per SPEC §2-E1 (A7 R5) |
| 5 | event PIT (BLS/FOMC) | **PASS** | CLOSED-PREP: BLS 204+204 all-08:30 PASS_EVIDENCED + 2025 vintage law (11 CPI/10 EMPSIT; 2 canceled-day falsifiers) `FUTURES-OVERNIGHT-PREP-20261003/bls_vintage/`; FOMC 132-day law, 92 timed minute-level 2016+; surprise NOT_RUN (disclosed) |
| 6 | fee/spread/slippage/BBO | **BLOCKED** | `es/es_fee_status.json` — corrected tier-1 all-in **2.24 USD/side MODELED COST** UPHELD (P0 erratum UPHELD in full); **VERIFIED_VS_ACCOUNT=NOT_RUN** (owner decision D2 open); SPEC §5 21.006/33.506/46.006 **UNDER-REVIEW-erratum**; **$0.01/side reg-basis divergence open** (NFA timeline vs IBKR capture basis); fee A7 re-audit **READY-NOT-RUN**; BBO NOT_RUN program-wide |
| 7 | trial budget | **BLOCKED** | `es/es_trial_census.json` — ES minimal recount **36** (F1 11 + F2 11 + F3 7 + F4 7) vs frozen cap **24** (SPEC_PB1_ES r3 §6 A-r4 list; all 24 IDs enumerated), **headroom 0**, every new ES family **BLOCKED_TRIAL_BUDGET**; no new trials run |
| 8 | reproduction/A7 | **PASS** | This lane reproduced, in this worktree, from cache bytes: panel rows exact, sessions exact, **66/66 crossovers recomputed from `es_contract_daily.parquet`**, |T-5−crossover|≤3 66/66, sign-match **61/66** reproduced, 68/68 union reproduced, 23/23 Q5 cells re-extracted; A7-SPEC verdict FREEZE_READY_WITH_ERRATA (0 BLOCKER/0 MAJOR) on file; S1 SEALED_UNTOUCHED |

**Closing line: "data-ready ≠ scored-authorized".** Dims 1-5 and 8 are
evidence-complete at the data-readiness level. The dims that still block scored
use are **dim 7 — trial budget (36 > 24 frozen, headroom 0,
BLOCKED_TRIAL_BUDGET)** and **dim 6 — fee account verification (D2 NOT_RUN,
SPEC §5 UNDER-REVIEW-erratum, $0.01/side reg-basis divergence open, fee A7
READY-not-run)**. NO_GO_REGISTER · NO_GO_SCORE · NO_GO_ORDER stand.

## What this lane independently re-verified (methods + outputs)

1. **Expiry 68/68** (`es/verify_expiry.py` → `es/es_expiry_recheck.json`): union of
   the three baseline sources rebuilt in this worktree; machine checks on all 68
   dates; data-side cross-check vs `ES_cache/es_roll_table.json` (66/66 match);
   byte-grep spot legs on the captures physically present here — G1a
   `es_pcal_20100528164817.html` contains all five gap dates (2 hits each), G1b
   `es_pcal_20100418154051.html` four (Sep-2011 absent exactly as the baseline
   documents), and `nq_pcal_20110305184630.html` carries the same-quarter NQ dates
   5/5 with verbatim row extraction (`SEP 2011 | NQU11 | 06/18/2010 | 09/16/2011 |
   09/16/2011`). G1a/G1b sha256 recomputed and match the baseline's published
   digests. Capture-byte legs for D3 C10/C11 and DEEPFOUR R4 bytes are
   NOT_RUN_IN_THIS_WORKTREE (files absent here) — pointer + data-side legs all
   match; nothing inferred.
2. **Q5 permitted captures** (`es/q5_independent_verify/verify_q5_captures.py`,
   own parser written against the raw capture structure — no Q5 code reused):
   15 present captures sha256-match both the coverage JSON and Q5's own
   SHA256SUMS.txt; the ES weekly Globex string was re-extracted from raw bytes of
   `cspecs_133_20260405234659.json` and equals the claimed verbatim (venue-prefix
   semantics); all 23 claimed 2026 deviation cells were re-extracted from raw
   bytes and match (1 cell carries claim-side duplicate events — same values,
   merge artifact noted). **Verdict VERIFIED_WITH_RESIDUALS**; per owner law the
   Q5 values are therefore usable in this dossier, and only via this
   verification chain.
3. **Session/holiday** (`es/verify_session_holiday.py` →
   `es/es_session_holiday.json`): era template table (authority + data-side
   corroboration), 2017→2026 windows verbatim from D3, 2026 grid from the
   verified Q5 extraction; legality: every holiday observance date is a real
   weekday (Sunday Q5 eventDates are Globex session-start days, documented);
   every 'closed' minute sits inside the standing session span with a later
   reopen on file; CT/ET offset constant 1h, no DST-transition Sunday in the
   grid. NOT_OBTAINED register carried forward (2011-2025 product-level times
   NOT_TRANSCRIBED → SPEC §2-E1 fail-closed EXCLUDE; P3#2 ClearPort
   PENDING_ADJUDICATION — **nothing was extracted from any P3-lane capture;
   only Q5 captures, after verification**).
4. **Fee cell** (`es/verify_fee_and_census.py` → `es/es_fee_status.json`):
   restatement only — web captures NOT re-derived (per brief); 15 cited baseline
   artifacts sha256-pinned in the JSON.
5. **Trial census** (same script → `es/es_trial_census.json`): 24 frozen IDs
   enumerated from SPEC §6 patterns and counted (8+8+4+4); ESNQ minimal recount
   11+11+7+7 = 36 vs cap 24, headroom 0.
6. **O1M + roll** (`es/verify_o1m_roll.py` → `es/es_o1m_roll_recheck.json`):
   parquet re-read (pyarrow, local); 66/66 volume crossovers recomputed under the
   disclosed rule (last-25-sessions pre-expiry window; a whole-history search
   fires on far-forward thin-volume noise and is not the lane's measured
   quantity); T-5 switch recomputed 66/66 within 0..-2 sessions of crossover
   (0 violations >3); 61/66 sign-match reproduced exactly from the artifact's own
   spread/DFF-proxy columns.

## Contradictions and residuals found (reported, not smoothed)

1. **8 of 23 Q5-listed ES deviation captures are missing from disk AND absent
   from Q5's own fetch_log** while `cal_permitted_coverage.json` lists them with
   sha256 (over-claim). None of the claimed 23 cells depends on them — all cells
   reproduce from the 15 present files. Owner may want the coverage JSON
   annotated. (Incident note in Q5's lane doc about deleting "0-byte leftovers"
   does not cover these — they are 7 named files + 1, none in the log.)
2. **Brief said "13 sha-pinned captures"; the coverage JSON lists 23** for the
   ES 2026 cell-group (1 weekly + 22 deviation entries incl. alternate-timestamp
   duals). Count discrepancy recorded; verification covered every listed file.
3. **D3 prose verdict "36 of 68" vs its own 37-row master table** — already
   recorded by DEEPFOUR as a D3 counting slip; this lane counts from rows (37)
   and says so in `es_expiry_recheck.json`.
4. **2010 PDF "regular close 15:15 CT" vs quality-ledger era "Globex day ends
   16:30 CT"** — not a data conflict: different roles (RTH settlement close vs
   full-session end); pre-2016 16:00-16:30 tail lives in the BRK bucket and is
   excluded from RTH/ON aggregates. Both annotations carried in
   `es_session_holiday.json` with citations.
5. **2026 ES-specific Globex times were NOT_OBTAINED at baseline** and are used
   in this dossier ONLY through the independently verified Q5 chain above; the
   P3#2 ClearPort row remains PENDING_ADJUDICATION and was not touched.
6. Roll-crossover recompute required an explicit pre-expiry search window
   (disclosed in the script header); whole-history search is degenerate on
   far-forward zero/low-volume sessions. Recorded as method note, not a defect.

## NOT_RUN register (unchanged by this round)

- VERIFIED_VS_ACCOUNT (fee) — NOT_RUN, owner decision D2 open.
- A7 FEE re-audit — READY-NOT-RUN.
- BBO/depth — NOT_RUN program-wide (D5 law).
- PIT consensus/surprise archive — NOT_RUN (H3); publish-latency NOT_RUN.
- Capture-byte spot legs for D3 C10/C11 and DEEPFOUR R4 — NOT_RUN_IN_THIS_WORKTREE
  (bytes absent here; authority-claim vs data-side legs all matched).
- ES product-level Globex early-close times 2011-2025 — NOT_TRANSCRIBED;
  unproven days EXCLUDE fail-closed (frozen law, A7 R5).

— End of DATA_READINESS_ES.md. Companion machine file: `es_readiness.json`.
