# PLAN — SOCCER-APIFOOTBALL-PREP-V1 (API-Football as fixture + $0 1X2 odds source for men's international NT soccer; PREP only, $0)

- cycle_id: `SOCCER-APIFOOTBALL-PREP-V1` · asset: shared · budget 0 scored
  cells · no paper rows · registered 2026-10-08 (owner instruction, this chat).
- Owner authority 2026-10-08: re-open the closed question "no other $0 odds
  source exists" from SOCCER-INTL-EXPANSION-DISCOVERY-V1
  (DECISION_PACKET_PENDING_OWNER, fe030a8e): API-Football advertises a free
  tier (100 requests/day) with fixtures and pre-match odds, but neither real
  odds coverage nor storage rights for paper trade are proven. This round
  verifies via official docs and — if a valid key exists — real responses.
- Hard stop at PREP: **no GO, no paper bet, no ledger/cadence/model/EV/
  wallet(1,000 USD) change, no account creation or purchase on the owner's
  behalf, no push/merge, key bytes never in chat/log/git.** If the probe
  cannot prove real odds + suitable rights → verdict NOT_RUN, source stays
  OUT of paper.

## Measured at registration (2026-10-08)

- main HEAD `6eb31cd2`; lock FREE_PROVEN; running cycles untouched:
  SPORTS-PAPERTRADE-EXEC-V1 (6553427), SPORTS-PAPERTRADE-V1 (8105e87),
  SOCCER-INTL-EXPANSION-DISCOVERY-V1 (fe030a8, decision packet read).
- API-Football key: **ABSENT** (only `~/.config/wnba-money-capture/odds_api_key`
  = The Odds API exists; using it for this service is FORBIDDEN by owner).
  Therefore this round completes the DOCS + SYNTHETIC-HARNESS portion and
  records `NEED_OWNER_FREE_ACCOUNT_KEY`; the owner will create the free
  account and store the key OUTSIDE chat/git.

## Scope

Men's international NT competitions (same families as the discovery cycle):
friendlies, FIFA World Cup (+qualifiers, all confederations), Euro
(+qualifiers), Copa América, AFCON (+qualifiers), AFC Asian Cup
(+qualifiers), CONCACAF Gold Cup, CONCACAF Nations League, UEFA Nations
League (reference). Verify per competition: presence in API-Football
coverage catalogue vs REAL future fixture with kickoff UTC + fixture id +
stage + pre-match "Match Winner" odds carrying all three legs HOME/DRAW/AWAY.

## Work items

1. **DOCS** — fetch and snapshot (public pages, UA-polite, $0): pricing,
   coverage, terms, and endpoint docs for `/fixtures`, `/leagues`, `/odds`
   (https://www.api-football.com/pricing/ , /coverage/ , /terms/ , API docs
   page). Extract verbatim: free-tier request cap + reset, which plans include
   odds, bookmakers listed, odds update cadence, odds market definition
   (90-minute vs incl-ET), response structure (`response[].bookmakers[].
   bets[].values[]`), storage/redistribution/research clauses, account/key
   mechanics. Raw snapshots sha256-journaled.
2. **HARNESS (synthetic, key-absent)** — `probe_api_football.py` in this
   worktree: request journal (count, endpoint, ts, sha256 of response body,
   status), hard cap 10 API requests/run, key read ONLY from a file outside
   git (`~/.config/api-football/api_football_key` convention, bytes never
   echoed), dry-run mode emitting the exact request plan without network.
   Budgeted probe plan (≤10 requests total, $0): (1) `/leagues?type=league`
   filtered men's-NT families [or league-by-id spot checks]; (2) `/fixtures`
   for 2–3 named leagues within a future window; (3) `/odds?fixture=<id>`
   for ≤3 fixtures checking Match Winner 3-leg presence + bookmaker +
   update timestamp. Any result = journaled; fabrication forbidden.
3. **JOIN SAMPLE (dry-run, honest)** — reuse the discovery cycle's proven
   join plumbing pattern (fixture → crosswalk EXTENDED_CROSSWALK.csv →
   martj42 corpus entity → B1 K=48/ν=0.6/HCA=65). With no key: record
   NOT_RUN per missing leg with the exact reason (NOT_RUN_NO_KEY /
   NOT_RUN_NO_FIXTURE / NOT_RUN_NO_ODDS / NOT_RUN_NO_TIMESTAMP /
   NOT_RUN_CROSSWALK_MISS / NOT_RUN_90MIN_UNDEF). No synthetic odds ever
   presented as real.
4. **RIGHTS/PIT** — verbatim terms quotes (retrieval UTC): storage for
   internal research allowed or not; attribution; redistribution; cache
   limits; "display-only" restrictions if any. PIT register: odds
   `update` timestamp vs fetch time; kickoff timezone provenance
   (fixture `date` UTC-ness); 90-minute settlement definition for Match
   Winner — knockout/extra-time competitions (Euro finals KO, Copa KO,
   AFCON KO, Asian Cup KO, Gold Cup KO, WC KO, WCQ playoffs) stay
   NOT_RUN_KNOCKOUT_90MIN_UNPROVEN until the market definition is proven;
   league/group-format competitions are 90'-clean by competition rules.
5. **VERIFIER (fresh context)** — re-checks docs quotes vs live pages,
   harness cap logic (≤10 requests), key-absence handling, join honesty,
   boundary compliance (no exec/ledger writes, no GO, no TOA key use,
   $0 spent, no key bytes anywhere).
6. **DELIVERABLE** — `research/control/SOCCER-APIFOOTBALL-PREP-V1/
   DECISION_PACKET.md`: per-competition table (catalogue-listed vs REAL
   fixture vs REAL 3-leg odds; PASS/CONDITIONAL/NOT_RUN + blocker),
   rights verdict, free-tier quota math for a paper cadence, minimal
   integration changes a successor would need in SPORTS-PAPERTRADE-EXEC-V1
   (incl. whether the Pinnacle bookmaker rule would need an OWNER decision),
   and the `NEED_OWNER_FREE_ACCOUNT_KEY` hand-off if the key is still
   absent. Terminal outcomes: DECISION_PACKET_PENDING_OWNER |
   NEED_OWNER_FREE_ACCOUNT_KEY | NOT_RUN_SOURCE | TECHABORT_*.

## Boundaries

$0; ≤10 API requests TOTAL this round (docs pages are not API requests);
no accounts/purchases; The Odds API key NEVER used for this service; no S1;
no push/merge/rebase; registry via researchctl CAS; exec/NBA/WNBA/NFL/
discovery worktrees + ledgers + models + EV thresholds + 1,000 USD wallet
UNTOUCHED; no GO typed; politeness (UA string, sequential, backoff on
429/5xx). Data under `~/.my-quantitative-data/soccer-apifootball-prep-v1/`.
Worktree/branch: `.worktrees/soccer-apifootball-prep-v1/integration` on
`orca/soccer-apifootball-prep-v1-integration`.
