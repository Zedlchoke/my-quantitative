# PLAN — SOCCER-INTL-WC-EURO-PAPER-PREP-V1 (WC + Euro men's national-team paper intake PREP + read-only Synpath source evaluation; $0; zero scored cells)

- cycle_id: `SOCCER-INTL-WC-EURO-PAPER-PREP-V1` · asset: shared · budget 0/0 ·
  registered 2026-10-10 (owner round-4 instructions, this chat — two explicit
  instructions: (1) successor PREP to prepare FIFA World Cup and UEFA Euro
  MEN'S NATIONAL-TEAM matches for the shared paper wallet; (2) ADD a READ-ONLY
  lane evaluating Synpath as a SECONDARY market-data source (pre-match price
  discovery from Polymarket/Kalshi). Explicitly **NOT a typed GO**.
- GO phrase (REGISTERED_NOT_CONSUMED, typed ONLY by the owner, verbatim, fresh,
  at this cycle's own gate):
  **`GO SOCCER INTL WC EURO PAPER PREP V1 INTEGRATE`**

## Scope and hard scope exclusions

- IN: FIFA World Cup (men) GROUP STAGE; UEFA Euro (men) GROUP STAGE; FIFA World
  Cup QUALIFYING (ordinary group/league-stage matches); UEFA Euro QUALIFYING
  (ordinary group-stage matches). 90-minute results only.
- OUT (fail-closed NOT_RUN until a separate proof): any playoff / knockout /
  Final-Four / inter-confederation playoff match where extra time (or
  penalties) is possible; ALL club competitions; women's internationals; the
  already-live UEFA Nations League lane (EXEC-V1 keeps it; untouched here).

## Model law (measured 2026-10-10, never assumed)

- The CURRENT paper soccer model is **B1** (`soccer_b1_replay`, Elo/Davidson
  K=48, ν=0.6, HCA=65) — ledger `paper_ledger.jsonl` sha `c2975309…`, 17 rows,
  the only SOCCER FORECAST row carries `model_version_sha: soccer_b1_replay`.
- `SOCCER-INTL-B1R-PAPER-SWITCH-V1` exists, phase REGISTERED, go phrase
  `GO SOCCER INTL B1R PAPER SWITCH V1` **REGISTERED_NOT_CONSUMED** — the switch
  has NOT passed its own gate; it is NOT assumed, NOT pre-empted, NOT blocked
  here. This cycle makes no model decision: adapter drafts wire the engine
  exactly as the exec runner wires it (single wiring point), so whatever model
  is live in SPORTS-PAPERTRADE-EXEC-V1 at activation time is what the new
  competitions use. B1R stays TRAIN_INTERNAL_DIAGNOSTIC-only (90MIN-PREP R2).

## Inheritance (cite, never duplicate or modify; all READ-ONLY)

- `SPORTS-PAPERTRADE-EXEC-V1` (369d36bf): live one-wallet service; ledger
  genesis 100,000c; risk law 500c fixed stake / 10,000c open cap in-lock /
  EV≥5% c=0.02 / 10% drawdown pause / T-6h anchors / freshness row law;
  quota-guarded core client (`research/papertrade/odds_client.py` in the
  sports-papertrade-v1 worktree, key `~/.config/wnba-money-capture/
  odds_api_key`, fingerprint-journaled, HALT_KEY on 401/403); stage law is the
  committed `competition_law` table (fail-closed, window-checked,
  NOT_RUN_STAGE_LAW journaled); crosswalk extension CSV with per-pair evidence.
- `SOCCER-INTL-WINPROB-SCORED-V1` (TERMINAL 6d3e659): frozen arms, engine
  bytes, PIT_LAW_PROVEN_SAMEDAY_EXCLUSION; 2023+ PARTIALLY REVEALED (erratum)
  — never a clean holdout, never tuned on.
- `SOCCER-INTL-90MIN-PREP-V1` (683de135): 441/20-flip ET audit
  (RETROSPECTIVE_DIAGNOSTIC_POSTHOC); B1R draw-map pre-registration
  (`DRAW_CAL_MAP_FROZEN.json`); football-data.org measured 403 tier-blocked
  for EC/AC/CA under token (round 3, journal `probe3/`) — cited, no new calls.
- `SOCCER-EXPANSION-SURVEY_20261007` (EXEC control dir, sha'd snapshot):
  85-key census 2026-10-07 measured NO active key for WCQ, Euro/continental
  cups, or friendlies — `soccer_uefa_nations_league` was the ONLY men's
  international key. Re-measured by THIS cycle's census, never cited as
  current.
- `WSL-WINPROB-PROSPECTIVE-PAPER-PREP-V1` R3/R7 predmarket method: Polymarket
  Gamma + CLOB public APIs, walk-the-book ask-fill for the stake, mid/last/
  site-% never execution prices, never assume 3 asks sum to 100%, resolution
  rules verbatim, taker fee pinned from docs.

## Lanes

1. **L_STATE** — re-measure at round start (root HEAD, registry, worktrees,
   machine lock, ledger sha + row count, live-service heartbeat, quota state,
   B1-vs-B1R gate state). Written as an artifact; nothing assumed.
2. **L_SOURCES** — per group (WC-group, Euro-group, WC-qual, Euro-qual):
   re-run the 0-credit census (`GET /v4/sports`) against the CURRENT key and
   byte-pin the snapshot; enumerate candidate keys from the RESPONSE ONLY.
   For every candidate key: 0-credit `GET /v4/sports/{key}/events` — future
   fixtures with event_id, two teams, kickoff UTC, stage, venue/neutral,
   commence-time stability. Secondary fixture sources per group (ESPN public
   scoreboard; openfootball CC0 worldcup/euro pinned clones with `git
   ls-remote` re-pin check; fixturedownload) verified for rights + true UTC +
   change policy. A key in docs is NOT an active key; a page is NOT a market;
   zero fixtures is a valid measured outcome (calendar reality 2026-10:
   WC2026 finished July 2026; Euro 2028 undrawn; most 2030 qualifiers not
   launched) — record NOT_RUN_SOURCE with the measured reason and keep the
   watcher ready.
3. **L_ODDS_PROBE** — pre-registered hard cap: **credit-bearing requests ≤ 2
   TOTAL this cycle** (and only where a measured future fixture on an active
   key exists), else 0. Qualified quote law (inherited): Home/Draw/Away from
   ONE bookmaker (pinnacle) and ONE snapshot; source `update` timestamp ≤
   fetch timestamp < anchor; 90-minute h2h market; freshness row journaled.
   Missing any leg / unlisted ⇒ NOT_RUN_NO_QUALIFIED_ODDS. Quota precheck
   against the shared state; day/month caps re-measured, never redefined.
4. **L_CROSSWALK** — extend the provider↔corpus name crosswalk ONLY on
   measured per-pair evidence (provider payload bytes + corpus name);
   fail-closed for unresolved names (NOT_RUN, never fuzzy). 1:1 join
   fixture↔model on the mapped pair + UTC date. **Neutral-venue law**: WC
   group-stage matches are true-neutral except designated host sides; the
   adapter MUST pass the neutral flag through the frozen engine's own
   interface (interface verified against the pinned engine in this lane);
   host-nation matches and all qualifiers are home/away. No HCA is applied by
   default anywhere. No refit, no retune.
5. **L_STAGE_LAW** — draft `competition_law` windows per competition (JSON +
   evidence): GROUP_STAGE_90MIN (draws stand, no ET; bet-eligible-shaped,
   activation gated on the GO) vs KNOCKOUT_ET_POSSIBLE / PLAYOFF_ET_POSSIBLE
   (fail-closed NOT_RUN). Each entry states target-model semantics ↔ market
   1X2 90-minute ↔ settlement source alignment explicitly.
6. **L_ADAPTER** — candidate per-competition adapter + dashboard extension
   (per match: competition, teams, kickoff, model_id, p×3, odds×3, capture ts,
   EV, stake or precise NOT_RUN reason), reusing the shared wallet/stake/cap/
   risk gates verbatim. Delivered as CANDIDATE code + a PROPOSED config
   amendment (sport_keys + competition_law + crosswalk rows) in this cycle's
   worktree ONLY; the live service and its config are NOT touched; no real
   paper row is possible in this cycle.
7. **L_SYNPATH (READ-ONLY)** — evaluate Synpath as a SECONDARY market-data
   source for the four groups (price discovery Polymarket/Kalshi; a
   data-source evaluation, NOT order-integration):
   a. Read SDK code, docs, MIT license, hosted-API terms; pin version/commit
      sha. Public API or already-granted Owner read rights ONLY; NO account,
      NO key, NO purchase, NO credential fetch/print; **order-entry, router,
      trading-engine and any write endpoint are NEVER called** (fail-closed
      at the SDK boundary: only market-data functions).
   b. Market discovery per verified fixture, 1:1 (event ID, teams, kickoff
      UTC, stage, neutral). No market ⇒ NOT_RUN_NO_MARKET; no price inference
      from other matches.
   c. Three-leg 90-minute law: HOME/DRAW/AWAY must all exist for the SAME
      match under a 90-minute rule; where the venue splits YES/NO markets,
      join the three YES of the same match; NO(Home) is NOT Away. Resolution
      rules read VERBATIM (extra time, penalties, postponement, cancellation).
      Playoff/knockout or unclear-90-minute ⇒ NOT_RUN_RULES.
   d. For valid markets: walk-the-book ASK fill for the $5 stake (multi-level
      allowed), depth at that fill, spread, fees, data receipt timestamp,
      capture-before-anchor feasibility. Mid/last/percentages are NOT
      execution prices; never assume 3 asks = 100%. Raw response + URL +
      retrieval UTC + market/token IDs + sha256 + missing-data reason saved.
   e. Cross-check the SAME market against native Polymarket/Kalshi public
      APIs (IDs, rules, best ask, depth, timestamps, fees); every discrepancy
      reported. Synpath's cross-venue matching is a CANDIDATE only — side_map
      is never treated as evidence of identical settlement.
   f. Rights: MIT code license ≠ hosted data terms; snapshots for private
      research only; key-gated hosted history/matching ⇒ NOT_RUN_ACCOUNT
      (never self-register); historical data is PIT ONLY with proven
      coverage+timestamps for the exact market.
   g. Read-only test battery: missing draw leg, wrong stage, neutral venue,
      closed market, stale quote, depth<$5, data gap, same-name-different-
      rules market. Independent verifier re-derives Synpath vs native raw.
   Deliverable: per-fixture table (fixture source, market IDs, three legs,
   90-min law, ask/depth/fees, PIT, rights, verdict PASS/NOT_RUN) + the
   measured count of paper-eligible matches ADDED vs the current source (0 is
   a valid answer).
8. **L_BATTERY** — synthetic battery on pristine sandbox copies (no real p,
   no real odds, no real rows): neutral venue, reschedule/postpone, missing
   draw leg, un-crosswalkable team, same match on two competitions, stale
   quote, wrong stage, open-cap overflow, quota exhausted, idempotent re-run;
   PLUS the live ledger byte-unchanged proof (sha before == sha after; row
   count 17 frozen).
9. **L_PACKET** — per-competition decision packet: measured fixture/quote
   counts, data rights, expected quota cost, blockers, and SELF-ACTIVATION
   conditions for when each competition becomes listed; OWNER_GO_PACKET with
   the exact phrase and the single controller command after GO; A7 PRELAUNCH
   prepared (fresh-context audit before any GO).

## Boundaries (fail-closed)

PREP ONLY — stop before every GO. No new real paper rows, no scored OOS, no
backfill, no edits to old rows, no model refit/retune (B1 frozen; B1R has its
own unconsumed gate), no wallet/stake/cap/risk/cadence/dashboard-production/
ledger changes, no purchases/accounts/keys, no S1, no push/merge/rebase.
Live-service config untouched. Heavy compute takes the machine-wide lock; this
cycle's jobs are light quota-guarded probes + file authoring (90MIN-R3
precedent) — lock state journaled each probe batch, foreign workers never
touched. Missing evidence = NOT_RUN_*. Registry via researchctl CAS only.
Data under `~/.my-quantitative-data/soccer-intl-wc-euro-paper-prep-v1/`;
artifacts under `research/control/SOCCER-INTL-WC-EURO-PAPER-PREP-V1/`.
Worktree `.worktrees/soccer-intl-wc-euro-paper-prep-v1/integration`, branch
`orca/soccer-intl-wc-euro-paper-prep-v1-integration`. Key bytes never in
chat/log/git/argv.

## Terminal outcomes (negative-first)

**WC_EURO_PAPER_INTAKE_READY_PENDING_OWNER_GO** (all lanes delivered; per-group
NOT_RUN counts may be large — a measured zero-fixture calendar is a valid
outcome) | NOT_RUN_SOURCE_* | NOT_RUN_RESOURCE_CONFLICT | BLOCKED_<gate> |
TECHABORT_*. The GO phrase is never typed by a lane; an early/paraphrased GO
dies unconsumed.
