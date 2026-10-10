# PLAN — SPORTS-POLYMARKET-CUTOVER-PREP-V1 (prepare the shared paper program's source switch to Polymarket primary for NBA/WNBA/soccer-men/WSL; PAPER ONLY, $0; STOP before the shared Owner GO)

- cycle_id: SPORTS-POLYMARKET-CUTOVER-PREP-V1 · asset: shared ·
  ACTIVE_LIGHT · **budget 0/0 scored by law** · GO phrase: none of its own —
  the ACTIVATION gate is the shared program's standing phrase
  **`GO SPORTS PAPERTRADE EXEC V1 RUN ALL`** (REGISTERED_NOT_CONSUMED on
  SPORTS-PAPERTRADE-EXEC-V1), which this cycle's decision packet presents to
  the owner with the per-league readiness table. WSL BET_PAPER additionally
  requires the split gate `GO WSL WINPROB PROSPECTIVE PAPER V1 BET_PAPER`
  (registered on WSL-WINPROB-PROSPECTIVE-PAPER-PREP-V1) — recorded, never
  bypassed.
- Owner authority 2026-10-10 (round 9): prepare the switch of the shared
  paper program's primary price source to Polymarket's native public API for
  NBA/WNBA/soccer-men/WSL. NOT Synpath. PAPER ONLY — no real orders, no
  purchases, no accounts, no push/merge, no credentials in chat/log/git.
- Frozen-draft parent: SPORTS-PAPERTRADE-EXEC-V1
  AMENDMENT_SOURCE_SWITCH_POLYMARKET.md (db53d8dc) — config@3 laws, join
  laws, one-decision-per-fixture, no-fallback, NOT_RUN taxonomy, fee-once +
  c-relation, dashboard real-ledger law, gate structure.

## Tasks

1. **L-BUILD:** implement `polymarket_source/` in this cycle (never editing
   the live program pre-GO): Gamma open-events joiner per league (NBA/WNBA
   moneyline single-binary pairs; soccer/WSL 3-YES-binaries-of-one-event
   with same-event proof + kickoff ≤3600s + verbatim 90-min rules; NO
   futures/handicap/props/knockout-mismatch), CLOB read-only book-walk $5,
   fee 0.05·p·(1−p) once-in-denominator + c=0.02 generic, config@3
   source_map (frozen draft), one-decision-per-fixture law, no-fallback
   law, NOT_RUN taxonomy, dashboard real-ledger rendering (sandbox labeled).
2. **L-BATTERY:** offline battery: wrong market / wrong kickoff or stage /
   missing leg / empty book / stale quote / price change / no liquidity /
   duplicate / 21st command over shared cap / postpone-cancel / ledger
   tamper / NO(Home)-as-AWAY refusal / futures-and-props exclusion ×2 runs
   byte-identical. Real ledger + dashboard untouched (assert shas).
3. **L-PROBE:** read-only live probes per league on real Polymarket markets
   (NBA/WNBA preseason/offseason reality; UNL November window; WSL round-7
   listing watch) — append-only snapshots; per-match tables for all four
   leagues: fixture, model p, market/token ids, payout rules, ASK + $5
   execution depth, fee, EV, decision or NOT_RUN + reason, dashboard update
   time.
4. **Counts + decision packet:** matches-with-market, matches-with-quote,
   matches-passing-EV/risk-gate, BET_PAPER rows possible (expected 0 pre-
   listing) — per league. Decision packet: the shared gate phrase, the WSL
   split phrase, exact remaining conditions per league, runbook for the
   post-GO first batch, STOP.

## Boundaries

$0; public read-only endpoints only; no accounts/keys beyond the program's
existing law; no purchases; no S1; no push/merge; registry via CAS; heavy
lock per law (foreign workers never killed); the three live cadences and
every other cycle untouched; calibration vocabulary only — no edge claims.
Worktree `.worktrees/sports-polymarket-cutover-prep-v1/integration` on
`orca/sports-polymarket-cutover-prep-v1-integration`. Artifacts under
`research/control/SPORTS-POLYMARKET-CUTOVER-PREP-V1/`.

## Terminal outcomes (negative-first)

**CUTOVER_PREP_READY_PENDING_SHARED_GO** (per-league readiness table
delivered; ready leagues named; A7 PASS) |
**READY_LEAGUES_NONE** (valid: no league quotable today; tables + packet
still delivered) | BLOCKED_* | NOT_RUN_* | TECHABORT_*. The shared phrase
and the WSL split phrase stay unconsumed by this cycle.
