# PLAN — SOCCER-INTL-EXPANSION-DISCOVERY-V1 (men's NT beyond UEFA NL: $0 source DISCOVERY, $0)

- cycle_id: `SOCCER-INTL-EXPANSION-DISCOVERY-V1` · asset: shared · budget
  0/0 (ZERO scored cells; no paper rows) · registered 2026-10-07.
- Owner authority 2026-10-07 (this chat): find $0 data sources to EXPAND
  SOCCER paper trade (SPORTS-PAPERTRADE-EXEC-V1 lane) to men's national-team
  matches BEYOND `soccer_uefa_nations_league`. This round is
  **DISCOVERY/PREP ONLY**: survey sources, measure coverage, rights/PIT
  check, one 1:1 join sample, decision packet. The running paper program is
  NOT modified (code frozen; exec worktree read-only for this cycle).
- Verified baseline this cycle inherits (measured 2026-10-07): The Odds API
  `/v4/sports` census snapshot (85 sports / 48 soccer keys) contains exactly
  ONE men's-NT key `soccer_uefa_nations_league`; the ~1,074 matches/year
  figure is HISTORICAL corpus volume (martj42 results.csv, CC0-1.0, sha256
  `df35268f…`), NOT a promise of paper-tradeable fixtures. Standing key law
  OWNER_DECISION_CAPTURE_2: key file `~/.config/wnba-money-capture/odds_api_key`
  (bytes never in chat/log/git); quota caps 4 credits/day + 120/month
  (measured today used 4/4 → **only 0-credit calls allowed today**).
- **No GO phrase, no scored execution, no paper bets, no ledger writes**:
  B1 join sample is plumbing-proof ONLY (≤3 real future fixtures), stored in
  THIS cycle's data dir, never in any ledger/exec artifact, never a bet.

## Scope (competitions surveyed; UEFA NL itself excluded — already covered)

Men's NT: FIFA World Cup qualifiers (all confederations, 2030 cycle), Euro
(qualifiers + finals), Copa América, AFCON (+qualifiers), AFC Asian Cup
(+qualifiers), CONCACAF Gold Cup, CONCACAF Nations League, friendlies.

## Lanes (parallel, light fetches; no heavy lock unless >10MB/slow)

- **A FIXTURES**: survey + MEASURE $0 no-account future-fixture sources
  (ESPN hidden API, api.fifa.com, TheSportsDB v1 free, fixturedownload.com,
  football-data.org docs-listed free tier [account → CONDITIONAL only],
  confederation/official feeds). Per source × competition: match ID, teams,
  competition, stage, venue/neutral flag, kickoff UTC provenance,
  postpone/cancel update semantics; measured future-fixture counts for the
  Oct 2026 / Nov 2026 / Jan–Feb 2027 windows. Evidence JSON + raw samples
  under this cycle's data dir.
- **B ODDS**: $0 real pre-match 1X2 (three 90-minute legs from ONE
  bookmaker, price, publish/update timestamp vs fetch time). The Odds API:
  0-credit census `GET /v4/sports?all=true` via standing key (key bytes
  never echoed; today's 4/day cap is exhausted → census-only), plus public
  docs pages (sports-odds-data list, quota cost model, ToS) — classify
  which non-NL men's-NT keys exist now or historically; quota math for a
  capture cadence. Others (football-data.co.uk = post-match → DISQUALIFIED
  as live odds by owner instruction; TheSportsDB odds v2 = paid;
  Oddspedia/OddsPortal/bookmaker scraping = ToS) — document rejection
  reasons honestly. No self-computed odds; no post-match site substitutes.
- **C RIGHTS/PIT**: verbatim license/ToS snippets + URLs + retrieval UTC
  for every A/B candidate (storage, attribution, redistribution, research
  use); PIT risk register: kickoff-timezone provenance, postponement
  semantics, odds-timestamp-vs-fetch, 90-minute vs incl-ET market
  definitions per source, knockout-stage result-definition risk (B1 target
  is 90-minute 3-way; ET/shootout comps without a proven 90' market
  definition = NOT_RUN per competition).
- **JOIN SAMPLE (controller)**: ≤3 REAL future fixtures from lane A →
  team-name crosswalk (seed `2132533b…` + extensions, evidence per row) →
  B1 replay (`soccer_b1_replay` port `22553f6b…` imported READ-ONLY,
  corpus sha-pinned) → odds leg from lane B (no key ⇒ record
  NOT_RUN_ODDS_NO_KEY honestly). Records 1:1 matches AND non-matches.
- **VERIFIER (fresh context)**: re-checks sources vs evidence, rights
  quotes vs live pages, join 1:1 + B1 simplex, coverage numbers, boundary
  compliance (no key bytes anywhere, no exec/ledger writes, no GO).

## Deliverable

`research/control/SOCCER-INTL-EXPANSION-DISCOVERY-V1/DECISION_PACKET.md`
(+ lane evidence JSONs): per-competition table (hist matches/yr from
results.csv by tournament; months with matches; MEASURED future fixtures;
% with pre-match 1X2; rights; $0 cost; PIT; verdict PASS/CONDITIONAL/
NOT_RUN + blocker), ≤2 recommended options with join schema, capture
cadence, quota forecast, anti-leak/anti-duplicate tests, and the MINIMAL
changes a successor integration cycle would need in SPORTS-PAPERTRADE-
EXEC-V1. If nothing qualifies → verdict NOT_RUN_SOURCE, no standard lowered.

## Boundaries

$0; no accounts/purchases/tier upgrades/quota evasion; no API keys read
from chat or echoed to log/git; standing key used ONLY for 0-credit census
while 4/day cap is exhausted; no S1; no push/merge/rebase; registry via
researchctl CAS; exec/NBA/WNBA/NFL worktrees + ledgers + models + EV
thresholds + 1,000 USD wallet UNTOUCHED; no GO typed; politeness (UA
string, sequential, ≤10 MB/source/run, backoff on 429/5xx). Data under
`~/.my-quantitative-data/soccer-intl-expansion-discovery-v1/`. Worktree/
branch: `.worktrees/soccer-intl-expansion-discovery-v1/integration` on
`orca/soccer-intl-expansion-discovery-v1-integration`. Terminal outcomes:
DECISION_PACKET_PENDING_OWNER | NOT_RUN_SOURCE | TECHABORT_*.
