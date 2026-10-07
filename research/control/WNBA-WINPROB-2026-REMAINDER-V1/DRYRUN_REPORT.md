# DRYRUN_REPORT — Lane W26, cycle WNBA-WINPROB-2026-REMAINDER-V1

SANDBOX DRY RUN — SYNTHETIC ONLY · ZERO REAL ROWS · NO GO TYPED
(No real-game probability exists anywhere in this cycle. Typed GO is the
owner's alone.)

## 1. What was run

Ported ledger: `research/papertrade_wnba26/wnba_2026_remainder_ledger.py`
(schema `wnba_2026_remainder_ledger@1`, provenance header inside). Tests run
from the worktree cwd with
`/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest`:

| suite | file | result |
|---|---|---|
| ported ledger unit suite (2027 PREP suite port) | `tests/papertrade_wnba26/test_wnba_2026_remainder_ledger.py` | **59 passed** (47 test functions; `test_10` ×6, `test_23` ×7 parametrized; source suite = 57 items green — all 46 source functions ported + new `test_15b` strict-anchor accept + `test_47` pin re-measure) |
| sandbox dry-run proofs D1–D7 | `tests/papertrade_wnba26/test_dryrun_2026_remainder.py` | **8 passed** |
| combined | `tests/papertrade_wnba26` | **67 passed** (final runs: `59 passed in 0.37s`, `8 passed in 0.17s`, `67 passed in 0.36s`) |

Sandbox bytes (SANDBOX ledger files + per-proof result JSON) live OUTSIDE git
under `~/.my-quantitative-data/wnba-2026-remainder-v1/sandbox/dryrun-*`
(latest complete run cited in the handoff). The frozen B1-WNBA engine was
imported READ-ONLY (pinned `arms.py`, sha re-measured in-suite:
`82263eab…`; `harness.py` `b9446f76…`); nothing under any other cycle's tree
was modified.

## 2. Proofs (all GREEN, synthetic 2026-style games only)

- **D1 append-before-anchor ACCEPTED** — full-slate ET-day-2026-10-07 batch
  (SYN tips 23:30Z + next-day 01:30Z) recorded 17:00:00Z/17:10:00Z (< anchor
  17:20:00Z) → 2 rows written, chain intact, scoring = 2× VALID_PROSPECTIVE.
- **D2 append-AT-anchor REFUSED** — a row stamped exactly at T0−6h10m
  (2026-10-07T17:20:00Z) refused; **append-AFTER-anchor REFUSED** —
  19:20:01Z refused. The anchor is an EXCLUSIVE deadline; refusals are
  atomic (nothing written).
- **D3 completed-only state law** — with the frozen engine's `run_stream`
  (K=32/HCA=50/γ=0.65), the rating state at the batch anchor includes ONLY
  games with `tip_utc < anchor` AND result present: `SYN-NORESULT` (tip <
  anchor, no result) and `SYN-POSTANCHOR` (tip ≥ anchor) are excluded;
  batch predictions from the engine's tip-batch snapshot equal the
  hand-computed logistic from the completed-only state (agreement < 1e-12).
- **D4 tamper detection** — bit-flip → `verify_chain` flags row 0, scoring
  raises fail-closed; competent re-hash tamper → chain-linkage break flagged
  at the successor row; true restore returns the walk to intact.
- **D5 batch snapshot law (ledger side)** — one batch per ET day; a second
  batch for the same `local_date` refused (no re-prediction, no backfill).
- **D6 partial-batch capture window (disclosed behavior)** — after the ET
  day's earliest anchor passed (17:20Z) but before a later game's own anchor
  (19:20Z), a first-and-only batch containing only the later game is
  ACCEPTED and permanently consumes the ET day: the earlier-tipped game can
  never be recorded → `not_run_games` census = the missed game, forever.
- **D7 boundary + pin guards** — window law (REG refused, season-locked
  2026) enforced in sandbox; engine + data sha pins re-measured.

## 3. Anchor-law reconciliation (binding interpretation)

The dispatch pins per-game anchors equal to each game's own
`tip_utc − 6h10m` (17:20:00Z for 401918297; 19:20:00Z for 401918298 —
reproduced exactly from the pinned schedule snapshot). The ledger's frozen
day-batch structure gates on the earliest tip among the batch's rows
(= the ET game-day's T0 when the full slate is batched). Both statements
hold together: a full-slate day batch must land strictly before the day's
earliest per-game anchor (17:20:00Z tonight); a game whose own anchor has
not passed remains capturable alone via a first-and-only partial batch
(D6), at the permanent cost of any same-ET-day game whose anchor already
passed. No reading of the laws allows backfill, re-prediction, or a row at
or after an anchor.

## 4. FEASIBILITY (mandatory) — per remaining game

Report instant: **2026-10-07T07:04Z**. A game is CAPTURABLE iff the owner
types this cycle's GO and the mechanical chain GO → freeze-packet genesis →
ledger creation → pre-tip batch append completes strictly before that
game's anchor. The chain is proven mechanical (dry-run above): minutes of
work, no human tuning, no data dependency beyond the already-pinned
snapshot. **Missed anchors are NOT_RUN forever (no backfill).**

| game | matchup | per-game anchor (UTC) | status at report | verdict |
|---|---|---|---|---|
| 401918297 | NY @ ATL (SF2) | 2026-10-07T17:20:00Z | ~10h16m ahead | **CAPTURABLE** if owner GO lands before 17:20:00Z today |
| 401918298 | LV @ GS (SF2) | 2026-10-07T19:20:00Z | ~12h16m ahead | **CAPTURABLE** — full-slate capture before 17:20:00Z; alone (D6 partial batch) until 19:20:00Z |
| 401918299 | ATL @ NY (SF3) | 2026-10-09T17:20:00Z | future | CAPTURABLE if GO before anchor |
| 401918300 | GS @ LV (SF3) | 2026-10-09T19:20:00Z | future | CAPTURABLE if GO before anchor |
| 401918302 | GS @ LV (SF4 if nec.) | 2026-10-10T21:50:00Z | future | CAPTURABLE if played and GO before anchor |
| 401918301 | ATL @ NY (SF4 if nec.) | 2026-10-11T11:50:00Z | future | CAPTURABLE if played and GO before anchor |
| 401918303 | NY @ ATL (SF5 if nec.) | 2026-10-13T21:50:00Z | future | CAPTURABLE if played and GO before anchor |
| 401918304 | LV @ GS (SF5 if nec.) | 2026-10-13T21:50:00Z | future | CAPTURABLE if played and GO before anchor |
| 401918305 | Finals G1 | 2026-10-17T13:20:00Z | future | CAPTURABLE if GO before anchor |
| 401918306 | Finals G2 | 2026-10-19T17:50:00Z | future | CAPTURABLE if GO before anchor |
| 401918307 | Finals G3 | 2026-10-22T17:50:00Z | future | CAPTURABLE if GO before anchor |
| 401918308 | Finals G4 | 2026-10-24T13:20:00Z | future | CAPTURABLE if GO before anchor |
| 401918309 | Finals G5 if nec. | 2026-10-26T17:50:00Z | future | CAPTURABLE if played and GO before anchor |
| 401918310 | Finals G6 if nec. | 2026-10-29T17:50:00Z | future | CAPTURABLE if played and GO before anchor |
| 401918311 | Finals G7 if nec. | 2026-10-31T17:50:00Z | future | CAPTURABLE if played and GO before anchor |

**SF1 verdict (the critical path): 401918297 (NY @ ATL, tip
2026-10-07T23:30:00Z) IS capturable — its anchor 2026-10-07T17:20:00Z is
~10h16m after this report. If the owner types the GO any time strictly
before that anchor, freeze + forecast record physically happen (tooling
proven, data pinned, engine frozen). After 17:20:00Z the game is NOT_RUN
forever; 401918298 remains capturable alone until 19:20:00Z (D6 path);
after 19:20:00Z both ET-day-2026-10-07 games are NOT_RUN forever.**
Series-contingent ("if necessary") games that are never played are simply
never recorded (cancellation notices available if formally cancelled);
they are not repairable retroactively either.

This cycle can NEVER reach MIN_VALID=300 (≤15 games): the remainder window
is a paper-trade operational proof, not a powered evaluation — stated, not
stretched (FREEZE_PACKET §4).

## 5. Boundary compliance

$0; no purchases; no accounts; no S1; no GO typed or simulated; zero real
forecast rows (sandbox ledgers carry SYN-* games only and live outside git);
no edits to any other cycle's files; heavy lock checked FREE_PROVEN before
any long job; all writes inside `research/papertrade_wnba26/**`,
`tests/papertrade_wnba26/**`, `research/control/WNBA-WINPROB-2026-REMAINDER-V1/**`
and `~/.my-quantitative-data/wnba-2026-remainder-v1/**`.
