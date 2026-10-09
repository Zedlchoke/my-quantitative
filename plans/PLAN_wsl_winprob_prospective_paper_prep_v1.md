# PLAN — WSL-WINPROB-PROSPECTIVE-PAPER-PREP-V1 (WSL prospective forecast + odds qualification + shared-paper adapter PREP; PAPER ONLY, $0; STOP before Owner GO)

- cycle_id: WSL-WINPROB-PROSPECTIVE-PAPER-PREP-V1 · asset: shared ·
  ACTIVE_LIGHT · **budget 0/0 scored by law** (prospective forecasting and
  paper rows are process recordings, never scored arms) · GO phrase
  registered, NOT typed:
  **`GO WSL WINPROB PROSPECTIVE PAPER V1 FIRST BATCH`** — typed ONLY by the
  owner, verbatim, fresh, in a separate message at this cycle's own gate
  after A7; authorizes EXACTLY the first future WSL batch (FORECAST rows
  pre-anchor + QUOTE/DECIDE via the shared ledger adapter if odds qualify)
  and nothing else.
- Owner authority 2026-10-09 (round 5, this chat): prepare and integrate WSL
  into the shared paper program (SPORTS-PAPERTRADE-EXEC-V1, live for
  WNBA/NBA/men's soccer). PAPER ONLY — no real bets, no purchases, no
  self-typed GO. The WSL scored GO (consumed 2026-10-09) authorizes NOTHING
  prospective or paper; this successor exists precisely because the scored
  freeze §7 requires "odds/live anything" in a NEW plan + NEW cycle.
- Inheritance (verbatim, from WSL-WINPROB-SCORED-PREP-V1 freeze
  `wsl_winprob_freeze@1` sha 80e429c4… and its A7 chain): forecast arm
  **B1 Elo/Davidson K=24.0, ν=0.55, HCA=40.0**, 3-way HOME/DRAW/AWAY, init
  1500, Davidson ν, HCA on home designation only; **B2 is NOT fielded**
  (byte-identical to B1 — never presented as a new mechanism); day-batch
  **D−1** (all date-D matches from the end-of-(D−1) snapshot; no same-day
  results even when kickoff order is known); identity = EWF `team_id`
  (renames fold; T-019-T Millwall→London City ONE lineage); awarded rows
  and data-quality anomalies EXCLUDED from targets and features;
  seed 20261009; corpus pins (ewf_matches eb043b03… etc.).
- Exposure law: WSL seasons 2023-24 + 2024-25 are EXPOSED (scored OOS
  consumed 2026-10-09); 2025-26/2026-27 were never scored — fresh for
  rating-state accumulation, but NO season is ever called a clean holdout
  and NO accuracy/LL number is ever evidence of betting edge.

## Lane 1 — results + fixtures source (forecast substrate)

Find, rights-check and PIN a legal source for (a) complete 2025-26 WSL
results, (b) 2026-27 WSL matches already FINAL, (c) future fixtures with
TRUE kickoff UTC (the pinned EWF corpus ends 2024-25 and has no kickoff
times). Per source: bytes pinned (clone/download HEAD + per-file sha256 +
retrieval UTC), rights quote (primary page), team-name → team_id crosswalk
EXTENSION (fail-closed: unmapped name = row refused, never guessed),
promotion/relegation identity, renamed teams, awarded/postponed handling.
Rating state evolves by the frozen D−1 day-batch law through the new
results; forecasts recorded BEFORE anchor AND kickoff per the shared paper
law (anchor = kickoff − 6h unless the source census proves a different
binding law); missed windows are NOT_RUN forever — NO backfill. Missing
link ⇒ NOT_RUN_<gap>; forecast lane may end NOT_RUN_SOURCE and the cycle
still delivers the odds + adapter lanes.

## Lane 2 — odds qualification (gate for any BET_PAPER)

1X2 pre-match with ALL THREE outcomes, **90-minute settlement**, quote
update timestamp + fetch timestamp, storage/research rights (primary
quote), 1:1 fixture join. Measure REAL coverage on the actual future WSL
fixtures. Leads to re-survey with evidence, not assumptions: The Odds API
(no WSL league key — documented round-1; re-verify against their current
league list page), Betfair Exchange (EXCHANGE pricing: if ever used, freeze
separate back-price/liquidity/commission selection rules FIRST — never
treated as bookmaker odds; account/app-key is OWNER-ONLY territory, out of
this round), API-Football (women's coverage + odds endpoint — rights
CONDITIONAL per V1R1-R3 chain; a WSL odds probe needs its OWN owner
authorization; the 12/11 Nations-League probe automation is out of scope
and untouched). Price-display websites never self-certify an API or storage
rights; no scraping against terms; no accounts; no out-of-scope keys; no
purchases. Missing draw leg, stale quote (quote_update not strictly before
anchor), team-name mismatch, kickoff change ⇒ NOT_RUN_<reason> per match.
No qualified source ⇒ **forecast-only mode: zero BET_PAPER rows** (NOT_RUN
recorded), the adapter still ships gated to NO_BET/NOT_RUN decisions.

## Lane 3 — shared-paper adapter (only after Lanes 1–2 gates)

Extend SPORTS-PAPERTRADE-EXEC-V1 with a WSL adapter using the SAME virtual
wallet ($1,000 start), stake $5/bet, open-exposure cap $100, and the
existing EV/cost/drawdown/quota/settlement gates verbatim — one flock, no
race that could exceed the shared cap (an eligible-bets scan must count
WSL + WNBA + NBA + soccer-men together). Per fixture the row sequence is
FORECAST → QUOTE (or journaled missing-quote reason) → DECIDE
(BET_PAPER/NO_BET/NOT_RUN) → SETTLE/REFUND on valid results only. The
dashboard shows every WSL fixture including no-bets, with 3-way
probabilities, real odds, EV, stake, reason, PnL and the SHARED equity. No
fabricated rows to fill the dashboard; proxy odds never pass as real odds;
existing append-only rows (all three leagues) are never edited or replayed.

## Verification (before the gate)

End-to-end SYNTHETIC battery: success path AND refusal paths — no GO;
wrong HEAD/pin; lookahead (forecast recorded after anchor/kickoff); quote
after anchor; missing draw leg; duplicate fixture; kickoff change;
awarded/postponed; key/quota failure; exposure on the 21st concurrent
command; drawdown gate; ledger tamper; settlement/refund. Byte-level
reproduction; independent A7 at the final HEAD. Before/after byte+hash
reconciliation of the WNBA/NBA/men's-soccer ledgers (paper 17 rows sha
c2975309…, NG 129 rows sha 7d9af286…, HCAL1 evidence); doctor clean for the
new cycle; registry CAS head-synced; heavy lock per law (never kill foreign
workers). $0; no S1; no push/merge.

## Gate + stopping rule

Everything technical completes BEFORE the Owner GO. Then STOP with
DECISION_PACKET_WSL_PAPER.md stating: the exact phrase
(`GO WSL WINPROB PROSPECTIVE PAPER V1 FIRST BATCH`), precisely what a typed
GO authorizes (first future WSL batch only: FORECAST rows pre-anchor +
QUOTE/DECIDE via the qualified path; SETTLE when results land) and what it
can never do (no re-forecast, no backfill, no parameter change, no second
batch without its own gate), plus every remaining NOT_RUN. No self-typed
GO. After a valid separate-message GO: run the first batch, then audit
row-by-row.

## Worktrees / artifacts

Integration `.worktrees/wsl-winprob-prospective-paper-prep-v1/integration`
on `orca/wsl-winprob-paper-prep-v1-integration`; the shared program's
worktree (sports-papertrade-exec-v1 @ 369d36b) is restored/verified as a
dependency, not owned by this cycle. Data plane
`~/.my-quantitative-data/wsl-winprob-paper-prep-v1/`. Artifacts under
`research/control/WSL-WINPROB-PROSPECTIVE-PAPER-PREP-V1/`.

## Terminal outcomes (negative-first)

**PRELAUNCH_READY_PENDING_OWNER_GO** (lanes + battery + A7 PASS; GO not
typed) | **FORECAST_ONLY_READY_ODDS_NOT_RUN** (valid: adapter ships
NO_BET/NOT_RUN-gated) | PRELAUNCH_BLOCKED_<gate> | NOT_RUN_SOURCE |
BLOCKED_* | TECHABORT_*. An early/paraphrased GO dies unconsumed.
