# PLAN — NWSL-WINPROB-PREP-V1 (NWSL win-prob PREP: sources, join laws, baselines, design; $0, zero scored cells)

- cycle_id: `NWSL-WINPROB-PREP-V1` · asset: shared · ACTIVE_LIGHT ·
  budget **0/0 scored by law** (PREP only: source qualification + protocol
  design; no scored pass, no prospective ledger, no paper hookup in this
  cycle) · registered 2026-10-15 (owner instruction, this chat: open a NWSL
  PREP research round; PREP ONLY — stop at freeze/decision packet for owner
  review before any scored or prospective successor).
- No GO phrase exists for this cycle. Any successor's GO is typed only by
  the owner at that successor's own gate (P-8). Non-duplication: no
  registered cycle owns NWSL; SPORTS-WINPROB-DISCOVERY-PREP-V1 (TERMINAL
  23b81a26) holds NWSL only as an inventory-only `NOT_RUN_SOURCE` row
  (probe bytes 2016 + 2026, ESPN scoreboard, est ~530 dated requests) —
  this cycle consumes that row, never re-litigates it.

## Inheritance (frozen pins; re-measured at bootstrap)

- DISCOVERY row `usa.nwsl` (NOT_RUN_SOURCE, inventory-only) +
  `samples/usa.nwsl_20160416.json` sha256 `726dde33…` — byte-reproduced
  fresh at the 2026-10-15 owner-round survey (same sha) — and
  `usa.nwsl_20260912.json` sha256 `4afdf55f…`.
- Odds qualification law: WNBA-ODDS-DISCOVERY SOURCE_MATRIX §0 Class
  A/B/C definitions + anchor law (T0 − 6h10m default) — inherited
  verbatim; NWSL rows are graded under the same law.
- Paper program laws read-only: SPORTS-PAPERTRADE-V1 + CAPITAL-V3 (1%
  equity stake, $500 open cap + availability bound, EV gate
  `p·d_eff − 1 − 0.02 ≥ 0.05`, drawdown pause 10%, PIT anchors, quota,
  append-only shared ledger). NWSL is NOT in the watcher/paper scope;
  adding it is a separate owner decision + separate gate, never this
  cycle.
- Men's-league parameters (any K/ν/HCA grid value fitted on men's or
  other leagues' outcomes) are EXCLUDED by law (WSL scored-prep
  precedent): NWSL arms are fitted on NWSL outcomes only.

## Owner-round survey facts (2026-10-15, $0, no accounts, no purchases; bytes + sha256 in the data plane)

Raw bytes: `~/.my-quantitative-data/nwsl-winprob-prep-v1/survey_raw/`
(SHA256SUMS.txt pinned). Summary artifact:
`research/control/NWSL-WINPROB-PREP-V1/SURVEY_20261015.md`.

1. **ESPN public API `usa.nwsl` scoreboard** — LIVE for the 2026 season
   (season id 14024; e.g. 2026-10-17 Gillette Stadium fixture with UTC
   kickoff ISO8601); historical 2016-04-16 probe byte-reproduces the
   DISCOVERY pin. Fields: fixtures, kickoff UTC, venue + city, status,
   scores, season type. Historical odds field is empty (null) — never an
   odds source. Est. full harvest ≈530 dated requests ($0, unauthenticated).
2. **nwslR/nwsldata `matches.csv` (release `key_tables`)** — 1,170
   matches, seasons 2016–2024 (incl. Challenge Cup + 2020 Fall Series),
   columns incl. kickoff (naive local datetime), stadium, city,
   home/away score, **penalty scores + `won_on_penalties`** (direct
   extra-time/shootout signal for playoff rows). STALE: last data touch
   2024-04/2024-06 — 2025–2026 ABSENT. `nwslR/nwslR` HEAD 0dd4efe80768
   (2024-04-25), MIT-style LICENSE pin; `nwsldata` HEAD fcbb44b13279.
3. **SoccerStatsUS/nwsl_data** — HEAD 6a21eaeb2bd6 (2026-10-02, commit
   "License the data under CC BY 4.0"); WUSA/WPS/NWSL depth, actively
   maintained; legacy text-block format (date day-first, score,
   scorers/rosters) — parser + coverage audit is lane work; candidate
   backfill for pre-2016 seasons and the 2025–26 gap.
4. **NWSL official (nwslsoccer.com)** — live; robots.txt pinned (allows
   most paths; sitemaps listed). Terms-of-use text NOT captured in
   static HTML (SPA) ⇒ any bulk fetch of official property waits for a
   lane-pinned rendered ToU. No documented public stats API ⇒ Class C
   until evidence.
5. **Polymarket Gamma (read-only public API)** — NWSL match events
   EXIST (slug pattern `nwsl-<away>-<home>-YYYY-MM-DD`), each event =
   three YES/NO markets (Home / Draw / Away) of ONE event — same shape
   as the qualified WSL lane; **draw market resolution pinned verbatim
   from bytes: "only … within the first 90 minutes of regular play plus
   stoppage time"**; futures (2026 Winner/Runner-Up) also present.
   Historical market census (seasons before 2026, per-event history
   via CLOB) is lane work; snapshot/PIT law follows the WSL paper
   pattern (append-only snapshots strictly pre-anchor).
6. **The Odds API** — `soccer_usa_nwsl` sport page NOT_FOUND at the
   guessed slug; sport enumeration requires the vendor key (account
   creation forbidden; standing-key use = quota decision, deferred to
   lane with owner visibility). Historical odds are paid regardless ⇒
   CANDIDATE_NOT_AUTHORIZED, never assumed coverage.
7. **Injuries/lineups** — no timestamped historical archive identified
   at $0 in this survey; default gate NOT_RUN_PIT unless a lane proves
   archived publish timestamps strictly pre-kickoff (H-STATUS WNBA
   precedent).

## Round tasks (this round: survey + plan + registration; lanes STOP before dispatch pending owner review)

1. Controller: commit plan → `researchctl cycle register` (CAS) →
   survey artifacts + manifest (DONE this round, documentation-only,
   $0, zero API-key use, zero quota burn).
2. L-ENGINE (next round, post-owner-review): B0-NWSL constant 3-way on
   train seasons only; B1-NWSL Elo/Davidson grid (NWSL-fitted only);
   market-implied de-vig 3-way arm when PIT snapshots exist; designed
   nulls (K=0 ≡ B0-mechanics; identity map) as CONTROL arms.
3. L-DATA (next round): ESPN dated-poll harvest 2016→2026 (~530
   requests, politeness caps, per-file sha256 + provenance) after the
   rendered ESPN ToU pin; nwslR/SoccerStatsUS cross-check + join-key
   audit; playoff marker law (regular season: draws stand; playoffs:
   ET/penalties — cross-verified against nwslR penalty fields and
   ESPN season-type); Polymarket NWSL census (seasons, three-leg
   completeness, 90-min rules per event).
4. L-PIT (next round): as-of law (day-batch D−1 where kickoff UTC
   coverage holes exist; strict kickoff-UTC batching where present);
   snapshot law for PM (fetch_ts < anchor; line_update ≤ snapshot);
   rights verdicts per Class A/B/C law.
5. L-A7 (next round): independent fresh-context audit; freeze packet;
   decision packet; STOP.

## Boundaries

$0; no purchases; no accounts; no S1; no push/merge/rebase; registry
writes only via researchctl CAS; heavy lock machine-wide (never kill
foreign workers); language law: calibration/forecasting vocabulary
only — no betting/edge claims from accuracy or log loss; no paper-trade
hookup, no watcher scope change, no ledger writes anywhere; other
cycles read-only (incl. the live NFL NG cadence, WSL/soccer BET_PAPER
lanes, NBA H-CAL1 recorder); missing evidence = NOT_RUN_*; handoff
JSON `zcode_orch_v3_handoff@1` at each handoff_path when lanes run.

## Worktrees / artifacts

Integration worktree + branch created at lane start:
`.worktrees/nwsl-winprob-prep-v1/integration` on
`orca/nwsl-winprob-prep-v1-integration`. Data plane:
`~/.my-quantitative-data/nwsl-winprob-prep-v1/`. Control artifacts:
`research/control/NWSL-WINPROB-PREP-V1/` (this round:
`SURVEY_20261015.md` + `SURVEY_MANIFEST.json`).

## Terminal outcomes (negative-first)

**PREP_COMPLETE_PENDING_OWNER_SUCCESSOR** (sources qualified/refused
honestly, join laws proven or NOT_RUN, baselines + design frozen, 0
scored) | PREP_PARTIAL_<gap> | NOT_RUN_SOURCE_<reason> |
NOT_RUN_ODDS_<reason> | NOT_RUN_PIT_<family> | BLOCKED_LICENSE |
NOT_RUN_RESOURCE_CONFLICT | TECHABORT_*. This cycle never scores, never
opens a prospective ledger, never writes a paper row.
