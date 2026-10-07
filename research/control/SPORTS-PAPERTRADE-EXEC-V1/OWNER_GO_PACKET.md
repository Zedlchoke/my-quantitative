# OWNER GO PACKET — SPORTS-PAPERTRADE-EXEC-V1 · READY_PENDING_ONE_OWNER_GO

Measured 2026-10-07 (A7 verdict `A7_PRELAUNCH_VERDICT.md` PASS_WITH_FINDINGS at
audit commit b72c14da; runner HEAD 1ae71433). No real paper row exists. $0 spent.

## THE ONE PHRASE (typed by Owner, verbatim, fresh, nowhere else)

**`GO SPORTS PAPERTRADE EXEC V1 RUN ALL`**

## What happens next (the ONE controller command chain, no further Owner input)

1. Controller transcribes the phrase to
   `.worktrees/sports-papertrade-exec-v1/integration/research/control/
   SPORTS-PAPERTRADE-EXEC-V1/GO_TOKEN.json` and consumes it in the registry
   (`researchctl cycle update --phase "GO_CONSUMED …"`), journaling the verbatim
   phrase + timestamp. The three absorbed cycles (WNBA-2026-REMAINDER,
   NBA-PROSPECTIVE, SOCCER-PROSPECTIVE) get `EXEC_GO_CONSUMED_VIA …` phase notes;
   their own phrases die UNCONSUMED. WNBA-2027's separate phrase is NOT touched.
2. Controller runs, per league per game-day (cadence below):
   `python -m research.papertrade_exec.execute run-day --date <UTC date> --worktree <wt>`
   — chain: fixtures → forecast (engine, frozen pins re-hashed; refuses at/after
   anchor) → odds (quota-guarded Pinnacle) → crosswalk 1:1 → EV/risk decision
   (in-lock cap check) → ledger append → dashboard rebuild → settlements after
   results. Automation (cron) is scheduled only after the GO.

## Cadence (frozen anchors; missed anchor = NOT_RUN forever, no backfill)

- WNBA-2026: per ET game-day at T0−6h10m (SF1 17:20:00Z, SF2 19:20:00Z TODAY;
  then SF3 10-09 17:20Z, SF4 10-11, SF5 10-14, Finals 10-17→11-01 per census).
- NBA: per ET game-day at T0−6h10m (first eligible date 2026-10-20).
- SOCCER: kickoff−6h strict, batch per UTC date at min-kickoff−6h10m; runs only
  when a fixture has live 1X2 prices (three legs, one bookmaker, one snapshot).

## NOT_RUN lists at packet time + auto-transition conditions

| Scope | Status now | Becomes eligible when |
|---|---|---|
| WNBA semifinals 1–2 | capturable (anchors 17:20Z / 19:20Z today) | GO typed before each anchor |
| WNBA slate (13 more games) | scheduled, capturable later | their anchors (census in FREEZE_PACKET §5) |
| NBA | **BLOCKED_NBA_CORPUS_BIND** (fail-closed: the scored cycle's outcome-bind token cannot be minted by this gate) | a NEW owner-authorized remediation plan that re-binds the frozen NBA law under a fresh freeze + A7 — NOT fixable by this GO; rows journal NOT_RUN until then |
| SOCCER | WIRED, **NOT_RUN_ODDS_UNVERIFIED** | first matchday-window probe shows three-leg 1X2 from the pinned book (e.g. UEFA Nations League mid-November) |
| WNBA season ≥2027 | NOT_RUN_FORECAST_GATE_2027 | the separate untouched phrase `GO WNBA WINPROB PROSPECTIVE V1 PREDICTIONS` at the 2027-frozen cycle's gate |

## What the GO cannot do

It cannot create a row for any match lacking a real schedule entry, a pre-anchor
forecast slot, a qualifying pre-anchor quote, a 1:1 crosswalk, or risk-gate
headroom — such matches are journaled NOT_RUN/BLOCKED with reasons. It cannot
open WNBA-2027, real money, purchases, quota changes, or S1. Paper laws stay:
one 1,000.00 USD wallet, 5.00 USD fixed stake, 100.00 USD open cap (in-lock,
21st bet journaled BLOCKED_OPEN_EXPOSURE), EV≥5% on listed odds (c=0.02 frozen
assumption), 10% drawdown pause, refund settlement, PAPER-only.

## Evidence index (Owner reading list)

`A7_PRELAUNCH_VERDICT.md` (this cycle) · `REHEARSAL_REPORT.md` + raw JSONs
(success path 18F/18Q/18D/2S, all SYNTHETIC-mode) · 28/28 adversarial battery ·
W26 `REALPATH_PROOF.md` (state_digest SF1 8bdf1515159c) · soccer
`REPLAY_WIRING.md` · pins `PINS.md`/`pins.json` · dashboard prototype (SANDBOX
banner): `~/.my-quantitative-data/sports-papertrade-v1/dashboard/index.html`.
