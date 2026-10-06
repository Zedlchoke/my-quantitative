# HOLIDAY_CLOSURE — FUTURES-ES-PB1-V1 / lane HOLIDAY-CLOSURE (M3)

- Cycle: FUTURES-ES-PB1-V1. Lane: HOLIDAY-CLOSURE. Generated 2026-10-04.
- Measured at worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`,
  branch `prep/futures-es-reg-20261004`, HEAD
  **`8324a8c0e414fb683d9bfa6f56734d0a17b9d40a`** (single bare `rev-parse` at
  lane start; `git status --porcelain` EMPTY at start; no commit/stage/push).
- Subject: the prelaunch-A7 standing obligation (A7_PRELAUNCH.md finding
  F-A1, MEDIUM, adjudicated lawful non-blocking at HEAD a33978b7):
  **"2011-2016 per-day holiday enumeration NOT_RUN /
  HOLIDAY_UNCERTAIN fail-closed-pending."**
- Mission: machine-prove the exposure statement, hunt independent day-level
  evidence, and close the obligation — or block it formally.

---

## VERDICT: NOT_RUN — the obligation is a REAL, NAMED blocker. NOT closed.

One 2011-2016 session sits in the evaluation surface on a date that a
committed official CME artifact names as an equity-family early-close day,
while the pinned panel shows a complete, real-volume session and the frozen
freeze does not exclude the date:

| blocker date | panel (pinned parquet) | committed evidence naming the day | freeze status |
|---|---|---|---|
| **2015-07-02** | 390 RTH-core bars (coverage 1.0), held ESU5; volume forensics: 619 bars from 12:00 CT, 476,608 contracts, trading to 23:59 CT — real trading, not synthetic bars | `2015-4th-of-july-holiday-schedule.pdf`, "CME Group Equity Products": verbatim *"Thursday, July 2 — 1215 CT / 1315 ET / 1715 UTC – Early close"* (sha256 `2c8831c207c60a421d3d1ae283632b77959198de83a07d16db4b4bc713abbaeb`); corroborated by `cmecal_coverage.json` year-2015 note ("Settlement notices name early-close days Jul 2 and Sep 4 2015") | absent from `exclude_list.json` (survivor); inside fold F2 EVAL surface (warmup ends 2014-01-16, eval first 2014-01-17, n=950) |

This is an **evidence-vs-data conflict that this lane cannot resolve under
the fail-closed law** (SPEC_PB1_ES §2-E1): the session's holiday status is
simultaneously adjudicated-by-artifact (early close) and
contradicted-by-data (full session). Either the printed schedule was
amended/not implemented for equity products that day (the PDF footer
reserves "Dates and times are subject to change"), or the panel data is
wrong for that afternoon. Both readings require an owner-authorized action
this lane is forbidden to take (network fetch, or builder change).

**Consequence:** the A7 F-A1 closure attempt FAILS at the strict
candidate-overlap level. The standing obligation stays OPEN — now with a
named date and a concrete resolution path, replacing "fail-closed-pending
with (believed) empty exposure".

## What WAS proved (the A7 claim itself is TRUE)

`holiday/exposure_proof.py` → `holiday/exposure_proof_2011_2016.json`
(verdict field `NOT_RUN_BLOCKER`; 27/28 machine checks PASS; the single
FAIL is the recorded exposure discovery, non-fatal by design):

1. **Panel recompute (L1):** RTH-core bars re-derived from the pinned panel
   for ALL 4,204 sessions — 4,204/4,204 equal to the K6 session rows.
2. **Band census (L2/L3):** exact integer partition at 234 = 0.60 × 390
   over the 1,535 in-panel 2011-2016 sessions:
   - cov = 0: **4** sessions (2012-04-06 Good Friday; 2012-10-29,
     2012-10-30 Hurricane Sandy; 2015-04-03 Good Friday) — all excluded.
   - 0 < cov < 0.60: **40** sessions (bars 116-226; every Monday holiday,
     Thanksgiving Thu/Fri, Jul-3/Jul-4, Christmas Eve) — all excluded.
   - **0.60 ≤ cov < 1.0: 0 sessions — the band is EMPTY** (A7 F-A1's
     specific claim verified: margin 0.5795 below / 1.0 at-or-above).
   - cov = 1.0: **1,491** complete sessions; 1,084 eval-eligible
     (matches the A7 census exactly).
3. **The pending class covers nothing (L4b/L4c/L4d):** the frozen
   `HOLIDAY_UNCERTAIN` class emits 2017-2025 only — zero 2011-2016 rows in
   `exclude_list.json`; `HOLIDAY_FACT_EARLYCLOSE` likewise zero in-span.
4. **All other candidate behavior corroborates the freeze (L5b-L5e):**
   36 candidate dates that are sessions are ALL ≤226 bars (<0.60) and
   excluded by COVERAGE_LT60 regardless of holiday status; 22 candidate
   CLOSED dates are absent from the panel entirely (Good Fridays
   2011/2013/2014/2016, MLK 2014, Dec-25s, Jan-1s — nothing to exclude);
   all 1,491 full sessions are weekdays; 40 window-interior full sessions
   reviewed (context ranges only; none named as holiday days by any
   artifact).

The A7 exposure MODEL ("unadjudicated holiday ⇒ truncated session, and all
truncated sessions are <0.60") holds for every case EXCEPT the one named
blocker: 2015-07-02 shows that an officially-named early-close day can
carry a COMPLETE session. That third case was invisible to the A7 census
(it is a cov=1.0 session) and is exactly the scenario the fail-closed law
exists for.

## M2 — independent day-level evidence hunt (committed corpus, zero network)

**FOUND — the 2011-2015 day-level evidence EXISTS and is committed**, in a
corpus the A7 never opened:

- **53 official per-holiday CME Globex schedule PDFs, 2011-2015**, at
  `research/control/FUTURES-OVERNIGHT-PREP-20261003/cme_cal_gap/fx_comm/captures/`
  (catalogued by `fxcomm_gapfill_coverage.json` gap4: 43/45 cells OBTAINED).
  48/53 carry a **"CME Group Equity Products"** section — equity-family
  (ES-family) session-hours authority. (Family-authority note: CME
  publishes ONE venue-wide Globex holiday schedule; the 2010 38-page PDF
  parsed in DEEPFOUR `NQ_CALENDAR_EVIDENCE.md` shows no product carve-outs
  in equity sections. ES-specific transcription/adjudication itself remains
  NOT_RUN at this SHA.) The duplicate
  `FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/comm/2011-thanksgiving.pdf`
  is byte-identical (same sha256).
- Extraction (machine): `holiday/extract_equity_pdf_evidence.py` →
  `holiday/pdf_equity_evidence_2011_2015.json` — **56 candidate dates**
  (CLOSED 12 / HALT 27 / EARLY_CLOSE 17, 2011-01-17..2015-12-25), every
  HALT/EARLY_CLOSE truncation time ≤ 12:15 CT, **106 regular-adjudicated
  dates**, weekday of every parsed date re-computed (0 mismatches;
  5 documented anomalies = 2 one-pager normal-schedule PDFs, garbled
  2014-MLK [known NOT_TRANSCRIBED], 2 settlement-doc Veterans files).
- Window-level context: `cmecal_coverage.json` 2011-2016 notes + DEEPFOUR
  `NQ_CALENDAR_EVIDENCE.md` per-year verbatim windows (declared in
  `exposure_proof.py` WINDOWS with quotes).
- One settlement-tier candidate RESOLVED by the day-level evidence:
  **2015-09-04** is named early-close only by a settlement notice
  (`cmecal_coverage.json` note); the committed
  `2015-labor-day-holiday-schedule.pdf` equity section adjudicates
  *"Friday, Sep 4 — 1615 CT – Regular close"* and the panel agrees (390
  bars, regular 16:14 last bar) ⇒ regular, NOT an exposure.

**NOT FOUND (stays NOT_RUN_OBTAIN):** 2016 has no per-holiday PDF set in
any corpus (the `globex-holiday-calendar.pdf` naming family ends at 2010;
the eq-gapfill lane's 2011 404 probe and the CDX inventory
`captures/cdx_holiday_files.txt` are the evidence of absence). 2016
candidates rest on the calendar-page captures only (Good Friday Mar 25 and
Dec 26 closures; Nov 25 equities floor 12:15 with Globex equity times
NOT transcribed). No 2016-day-level fetch was attempted per lane law —
zero network.

## Resolution path (owner actions; none executable by this lane)

1. **Builder round (preferred, zero network):** owner authorizes a gate-2
   builder revision consuming `pdf_equity_evidence_2011_2015.json`:
   add a `HOLIDAY_DAYLEVEL_PDF` class for primary-tier candidate dates
   2011-2015 (excludes 2015-07-02 and the other 2014/2015 early-close
   days — all truncated-excluded already except the blocker), keep
   settlement-tier days regular where a PDF adjudicates REGULAR
   (2015-09-04). Re-run `exposure_proof.py`; expected outcome: zero
   blocker rows ⇒ verdict PASS, obligation closed at the new freeze.
2. **Fetch round (only if the data side is to be challenged):** owner
   authorizes network: retrieve CME's July-2015 amended holiday/trading
   notices (route: web.archive.org CDX for cmegroup.com holiday-calendar /
   notices pages and the `2015-4th-of-july*` file family, June-July 2015
   vintages; expected artifact: an amended schedule naming Thursday
   2015-07-02 equity session hours). If an amendment shows the printed
   12:15 early close was not in force, the PDF candidate is downgraded for
   2015-07-02 and the freeze needs no change.
3. Either way, re-run `exposure_proof.py` after any panel/refresh or
   builder change — the proof is deterministic and re-opens automatically.

## Data-version binding

This artifact and the proof are tied EXACTLY to:

| input | sha256 |
|---|---|
| pinned panel `es_1m_outright.parquet` | `7ae6de2d5896d9e150f70209f2709ca70b625f0b06bbdbfed348b1b0e0227b95` |
| session universe `session_dispersion_es.json` | `e56c4a53841983e02f5e643e60693581e2c9e096488a1f7491659a71bb7c43a4` |
| frozen `exclude_list.json` (builder output; generation HEAD `e7fc1d8db00e91af74683cee7e999620fa8ff361`, builder `build_exclude_and_freeze.py` measured sha `9b94372d5bd297f5d50ac5107fcb1c34dcee9c090f4d10eaf38f97d387116e69`) | `bc8a41b673eccb998017e704a9865d139e67438fe984906f7f522782f93b438a` |
| PDF evidence roll-up | `holiday/pdf_equity_evidence_2011_2015.json` (sha recorded inside `exposure_proof_2011_2016.json`) |

Any change to the panel, the session universe, or the exclude builder
invalidates this proof; `exposure_proof.py` re-run is mandatory and
verdict-bearing. This closure document closes NOTHING and authorizes
NOTHING: no GO is typed or endorsed; no PnL/signal computation was
performed; zero network was used.

## Boundary compliance

- ONE bare `git rev-parse HEAD` at start (`8324a8c0…`); start
  `git status --porcelain` EMPTY; end status re-checked in the lane
  handoff. No other git operations.
- Writes confined to `research/control/FUTURES-ES-PB1-V1/holiday/**` and
  `research/control/FUTURES-ES-PB1-V1/dispatch/handoff_HOLIDAY-CLOSURE.json`.
- Root repo read-only; FUTURES-BEHAVIOR (P3-QUARANTINED) NOT accessed;
  zero network (all evidence from committed bytes); Python = root .venv
  read-only, single-shot panel reads (one 2-column full read + one
  3-column verification read on the conflict date).

— End HOLIDAY_CLOSURE (FUTURES-ES-PB1-V1).
