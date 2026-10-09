# PLAN — SOCCER-1X2-SOURCE-PREP-V1 (legal-source qualification for (a) 90-minute results with ET info and (b) pre-match-timestamped 1X2 odds; $0; documentation-only)

- cycle_id: SOCCER-1X2-SOURCE-PREP-V1 · asset: shared · ACTIVE_LIGHT ·
  **budget 0/0 by law** (source discovery + qualification only; nothing
  scored, nothing purchased) · GO phrase registered, NOT typed:
  `GO SOCCER 1X2 SOURCE PREP V1 QUALIFIED RUN`.
- Owner authority 2026-10-09 (second round, this chat): open ONE DATA/SOURCE
  PREP to find legal sources for (a) men's-international **90-minute results
  with extra-time/shootout information** and (b) **1X2 odds with pre-match
  timestamp evidence**. Measure per source: coverage, usage rights, price,
  1:1 joinability, settlement definition. $0 sources first; **paid options
  go into the decision packet ONLY — no purchases, no paid-key use, no
  account creation**. Do not modify B1/V1 (frozen in the TERMINAL scored
  cycle); do not read 2023+ as a clean holdout; no PnL, no edge claims. Any
  missing link ⇒ **NOT_RUN with the specific reason**.

## Inheritance (cite, never duplicate or modify)

- `SOCCER-APIFOOTBALL-PREP-V1R3` (ACTIVE_LIGHT, 9c239ee): free-tier probe of
  API-Football `/odds` + `/fixtures` scheduled 2026-11-12 (≤3 requests, key
  law `~/.config/soccer-api-football/api_key`, never printed); its V1/V1R2
  findings: odds rows carry NO team names (join via fixture.timestamp),
  rights CONDITIONAL (resale forbidden, publication not granted,
  betting-adjacent gray), and **"Match Winner = 90 minutes" is NOT
  documented by the provider** (league phase = clean 90'; knockout =
  NOT_RUN until evidenced). This cycle READS those artifacts; it never uses
  that key, never runs that probe, never edits that cycle.
- `SOCCER-INTL-WINPROB-PROSPECTIVE-PREP-V1` (a8057a9): The Odds API
  0-credit events census — fixtures + stable `commence_time` VERIFIED;
  per-match 1X2 NOT_RUN_ODDS_UNVERIFIED.
- `WNBA-ODDS-DISCOVERY-PREP-V1` (68867f87): qualification law Class A/B/C
  (rights + row-level PIT `snapshot_time <= anchor` AND
  `line_update <= snapshot_time < tip` + same-book two-sidedness + certain
  join) and the day×credit cost-model precedent.
- `SOCCER-1X2-POSTHOC-ANALYSIS-V1` (d8e11d98): the 1,425
  NOT_RUN_TARGET_NO_ET_FLAG rows are the concrete (a)-gap this cycle aims to
  close prospectively; 2023+ partially revealed (ERRATUM) — never a clean
  holdout.

## Tasks (documentation-only; ZERO API calls, ZERO key reads)

1. SOURCE_MATRIX.md — per candidate source, per leg (a)/(b): international
   coverage, rights (primary-source quote + URL + retrieval time), price,
   machine access, **1:1 join keys** (what fields would anchor a join to the
   corpus/ledger), **settlement definition** (is "result" documented as
   90-minute? where is extra time encoded?). Candidates at minimum:
   API-Football (docs pages only), The Odds API (docs only; historical
   endpoint economics day×credits), Betfair Historical Data (official store
   terms/pricing), Pinnacle-via-B2B feeds, OddsPortal/BetExplorer
   (rights caveats), OpenFootball/open datasets, worldfootball/Soccerway/
   11v11-class archives (scrape-rights caveats), official competition
   sites (FIFA/UEFA — terms). Class A/B/C verdict per source per leg.
2. SETTLEMENT_LAW.md — what evidence would prove a provider's match result
   is the 90-minute result (status enums incl. AET/PEN, documented market
   rules, side-channel cross-checks); the API-Football status-enum question
   is the sharpest open item — formulate the EXACT probe question for
   V1R3's scheduled probe WITHOUT running anything.
3. JOIN_FEASIBILITY.md — for each qualifying candidate: the concrete join to
   (i) the frozen corpus (team-name/date) and (ii) a future prospective
   ledger (fixture id/timestamp), collision analysis (same-day internationals),
   and what identity/crosswalk work a successor would need.
4. DECISION_PACKET_SOURCES.md — $0-qualified sources (if any) with a lawful
   acquisition path; paid options with measured-day cost models (built from
   documentation, never from calls); recommended successor registration
   conditions per source; explicit NOT_RUN_<link> lines for whatever is
   missing.
5. Independent verifier re-derives the matrix's load-bearing claims from
   primary docs.

## Boundaries

$0; documentation-only web access; NO API calls of any kind (not even
0-credit), NO key reads (both standing keys out of scope), NO accounts, NO
purchases; no S1; no push/merge/rebase; registry via researchctl CAS;
B1/V1 and every other cycle read-only; calibration vocabulary only — no
edge claims; missing evidence = NOT_RUN_*. Worktree
`.worktrees/soccer-1x2-source-prep-v1/integration` on
`orca/soccer-1x2-source-prep-v1-integration`; artifacts under
`research/control/SOCCER-1X2-SOURCE-PREP-V1/`.

## Terminal outcomes (negative-first)

**SOURCE_QUALIFICATION_COMPLETE_<CLASS_A_COUNT>** (matrix + settlement law +
join feasibility + decision packet delivered; count may be ZERO — a
documented zero with reasons is a valid outcome) | NOT_RUN_* |
BLOCKED_* | TECHABORT_*. GO phrase stays unconsumed.
