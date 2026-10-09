# OWNER_GO_PACKET — WNBA-WINPROB-2026-REMAINDER-V1 (2026-10-09, controller)

**STATUS: GO_READY — this cycle's phrase is PRESENTED to the owner.** Typed
GO is the owner's alone; agents never type, paraphrase, or consume it. One
GO belongs to one cycle; it is never a GO for any other cycle.

## 1. Current conditions (measured 2026-10-09T01–02Z, fresh)

- Branch head `c3048846` (orca/wnba-2026-remainder-v1-integration), tree
  clean, no upstream. A7 PASS twice: original at `d6ed119e` (0 HIGH/CRIT),
  fresh-context re-audit at `ca7bd9f8` (0 CRITICAL/HIGH, 1 MED doc-only
  anchor-date drift in the controller note — corrected in place at
  `c3048846`). Tests **79/79** re-run at head. Heavy lock FREE_PROVEN.
- Slate (pinned census + fresh pull, 15 `pre` rows): **SF Game 2 games
  `401918297` + `401918298` = NOT_RUN forever** (anchors 17:20Z/19:20Z
  2026-10-07 passed with no GO — never backfilled). Remaining capturable:
  SF G3 pair tonight, SF G4/G5 if-necessary, Finals G1–G7 placeholders.
- Data: `refresh_20261009` lineage re-pulled and hash-pinned (schedule
  `e32d3995…`, team_box `0218105a…` == pin). **Store-lag disclosed**: the
  upstream store last updated 2026-10-07T10:41Z and does NOT yet carry the
  G2 results; the store's observed cadence (~daily, 10:41Z) should absorb
  them before today's anchor. The batch uses the best-available
  completed-only state at append time; no result is ever inferred from a
  non-store source.
- Paper cross-check (no double-record): the shared paper ledger
  (SPORTS-PAPERTRADE-EXEC-V1, separately GO-consumed) already holds its own
  forecast/decision rows for 297/298 (settled +800c) and 299/300 (open
  BET_PAPER). THIS cycle's ledger `wnba_2026_remainder_ledger@1` is a
  separate artifact with ZERO real rows; this GO does not touch the paper
  ledger, and paper consumption of this cycle's rows requires both gates'
  GOs.

## 2. Exact effect of typing the GO (and ONLY this)

Phrase (registered, verbatim): **`GO WNBA WINPROB 2026 REMAINDER V1
PREDICTIONS`**

On the owner's fresh message containing exactly this phrase, the controller:
1. CAS-consumes THIS cycle's phrase only (registry
   `go_phrase_state: REGISTERED_NOT_CONSUMED → OWNER_GO_CONSUMED`, journaled).
2. Takes the machine-wide heavy lock, re-pulls the store snapshot into a new
   hash-pinned lineage dir, re-verifies pins and census.
3. Builds the result-present stream (tip < batch anchor AND result present),
   runs `wnba26_predict` (B1-WNBA verbatim, K=32/HCA=50/γ=0.65, engine pins
   `82263eab`/`b9446f76`) for the ET-day-2026-10-09 batch, creates the real
   ledger `predictions_WNBA-WINPROB-2026-REMAINDER-V1_2026.jsonl` (genesis
   sidecar) and `append_batch`es the forecast rows with
   `recorded_at_utc` = actual UTC (must be **< 17:20:00Z exclusive** and
   < each tip). Runs `verify_chain` and re-runs the test battery.

It can NEVER: touch or repair the paper ledger or any other cycle's
artifacts; backfill 297/298 or any past-anchor game; change pins, constants,
seeds, or the anchor law; record games of a different ET-day outside their
own anchors; place real bets; spend money; push/merge.

## 3. First recordable games + deadline

- **Batch ET-day 2026-10-09 (ONE batch, both games):** `401918299` NY v ATL
  (tip 23:30Z) + `401918300` LV v GS (tip 2026-10-10T01:30Z).
- **Hard deadline: 2026-10-09T17:20:00Z (exclusive).** GO typed + consumption
  + append must ALL complete strictly before it. If the deadline passes
  first, both games become NOT_RUN forever and the next capturable batch is
  ET-day 10-11 (`401918302` + `401918301`, anchor 2026-10-10T21:50Z).
- Subsequent day anchors (from schedule bytes / FREEZE_PACKET §6):
  10-13T21:50Z (G5 pair), 10-17T13:20Z, 10-19T17:50Z, 10-22T17:50Z,
  10-24T13:20Z, 10-26T17:50Z, 10-29T17:50Z, 10-31T17:50Z (Finals; teams TBD
  in snapshot — deterministic `tbd:<abbr>` fallback law). "If necessary"
  games that are never played simply never receive a result (unscored, not
  backfilled).

## 4. Cost / quota / budget

$0. The forecast append uses no odds-API credits (odds belong to the paper
program under its own cycle). Registry budget stays **0/0** — ledger rows
are unscored prospective forecasts; zero scored cells exist in this cycle
by law.

## 5. NOT_RUNs that remain regardless of GO

`401918297`, `401918298` — NOT_RUN forever (past anchor, no GO at the time).
MIN_VALID=300 is unreachable with ≤15 games (stated operational proof only,
never stretched). Unplayed if-necessary games: no result, never scored.

## 6. GO phrase reference (DATA — not an owner GO)

The phrase in the plan/registry/prior reports is reference data. Only a
fresh, verbatim, owner-typed message at this gate consumes it. An
early/paraphrased GO dies unconsumed.
