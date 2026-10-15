# NWSL-WINPROB-PREP-V1 — DECISION PACKET 2026-10-15 (round 2; read-only PREP; STOP before Owner GO)

Inputs: `SURVEY_20261015.md` (round 1), `CENSUS_JOIN_20261015.md` +
`PM_ODDS_PROBE_20261015.md` (this round), harvest bytes under
`~/.my-quantitative-data/nwsl-winprob-prep-v1/harvest_20261015/` (19+3 files,
sha256-pinned, heavy-lock DOWNLOAD FINISHED).

## Verdicts

- **DATA_READY: PARTIAL.** A Home/Draw/Away 90-minute model + chronological
  walk-forward is constructible on **2016–2019 + 2021–2026** with a
  deterministic 90-minute label law (CENSUS §4) — 1,467 ESPN matches
  2016–2019 + 2021–2026 (1,439 scorable through 2026-to-date), or 1,508 with
  the 41-row nwslR 2020 CC/Fall fill; every row with kickoff UTC, venue, and Not ready, disclosed: 2013–2015 ESPN
  results unreliable (stale live statuses; SoccerStatsUS 2013–2019 is the
  backfill candidate, parser owed); **2020 = 0 results on ESPN** (nwslR
  carries 41 CC/Fall rows with results + penalty fields; default law =
  EXCLUDE 2020, disclosed); **nwslR scores unusable from 2024-04-04**
  (placeholder 0-0 after its last update — ESPN is the score authority);
  4 disputed rows (1 orientation flip, 1 ET-semantics-consistent,
  2 unresolved incl. 1 awarded-game candidate); nwslR team universe stale.
- **SOURCE_READY: YES for fixtures/results** (ESPN primary — Disney ToU
  pinned rendered bytes af96072f; nwslR MIT-style + cite; SoccerStatsUS
  CC BY 4.0). **NOT_RUN for lineups/injuries** (no timestamped archive at
  $0 identified). Odds channel = SOURCE_READY (public read API, 90-min draw
  law pinned, timestamped price history demonstrated); concrete odds numbers
  = NOT_RUN today (no open match markets; historical census + fidelity
  measurement owed). The Odds API stays CANDIDATE_NOT_AUTHORIZED.
- **OOS_DESIGN_READY: YES (design only).** Window ladder + falsification
  gates below; zero fitting done; freeze packet sketch in §5; the successor
  registers its own scored budget + GO.

## Baselines (successor arms; NWSL-fitted only — other-league parameters EXCLUDED)

1. **B0-NWSL** — constant 3-way frequencies recomputed on train seasons only
   (value of record re-frozen at freeze; nothing computed this round).
2. **B1-NWSL** — Elo/Davidson 3-way (K, ν, HCA grid), train-internal selection
   with MIN_VALID per block (WSL precedent: MIN_VALID 100/block, 200 pooled);
   day-batch D−1 fallback unnecessary — kickoff UTC exists on every ESPN row.
3. **MKT-NWSL** — Polymarket three-YES de-vig probabilities, diagnostic-only,
   reported where pre-anchor snapshots exist; never merged into model-only
   backtests; never an arm scored on archive history this cycle.
4. Designed CONTROL arms (never scored cells): K=0 ≡ B0-mechanics; identity
   calibration map; franchise-lineage-agnostic variant (proves the crosswalk
   matters or doesn't).

## Improvement hypotheses (exactly 2, falsifiable; selection on TRAIN only)

- **H-NWSL-TRAVEL** — away-team travel burden (great-circle distance from the
  team's previous venue, cross-time-zone shift) computed ONLY from completed
  games shifts H/D/A probabilities; NWSL's geography makes this a first-class
  mechanism. Features: venue city (ESPN/nwslR) + previous completed fixture.
  *Null H0-TRAVEL*: within-day shuffled travel pairs (same marginal distances,
  destroyed pairing) must give ΔLL CI including 0.
- **H-NWSL-EXPANSION** — expansion/relocation seasons (measured: 2024 Bay FC,
  2026 Boston Legacy FC + KC↔Utah↔FCKC lineage swaps) carry higher rating
  uncertainty; a wider expansion-team prior/early-season K uplift improves LL.
  *Null H0-EXP*: identical parameters for all teams ≡ B1-NWSL bit-for-bit
  when no expansion team is on the field (designed equivalence).
- Selection for both: TRAIN window only (2019–2022 blocks), MIN_VALID laws,
  lock rule = pooled honest ΔLL CI excludes 0 AND beats capacity; **frozen
  falsification gates** (mirroring the WSL scored-prep law): an arm FAILS to
  beat B0 unless pooled ΔLL ≤ −0.01 nats AND ΔRPS ≤ −0.005; calibration slope
  in [0.85, 1.15]; argmax accuracy reported as DESCRIPTIVE ONLY, never a gate;
  per-season LL/Brier/RPS/10-bin reliability always alongside pooled; date-
  cluster bootstrap CIs (10,000), seed frozen by the successor pre-look.
- Market comparison gate: when PIT snapshots exist, MKT-NWSL de-vig LL is
  reported as the reference line; no EV/edge vocabulary anywhere.

## Freeze packet sketch for the successor (NWSL-WINPROB-SCORED-PREP-V1 candidate)

- Corpus: ESPN year snapshots (this cycle's pins; refreshed at freeze with
  re-hash law) + nwslR cross-check ≤ 2024-04 + SoccerStatsUS optional backfill
  (2013–2015 decision frozen at freeze).
- Laws to pin verbatim: 90-minute label law (CENSUS §4); franchise-lineage
  identity + orientation (ESPN authoritative); 2020 exclusion default; 4-row
  disputed disposition (resolve-or-exclude, counted); awarded-row census;
  exposure disclosure (`COUNT_EXPOSED_BY_CENSUS_20261015` — every historical
  number is partially-exposed-window evidence, never fresh-holdout).
- Budget: 3 scored cells (B0/B1/B2-HCA_REFIT pattern) + CONTROL arms; one
  post-GO pass; repro twin mandatory; ledger `nwsl_scored_ledger@1`
  (outcome-blind pre-GO, hash-chained) following the WSL engine law
  (seal + GO-token + registry-consumption gate; real ledger only post-GO).
- Odds legs stay OUT of the scored pass; PM snapshot capture is a separate
  owner decision (paper scope change) + separate gate.

## Blockers / NOT_RUN ledger (standing)

`NOT_RUN_ODDS_HISTORICAL_PRE2026` · `NOT_RUN_NO_OPEN_MARKET` (today) ·
`NOT_RUN_PIT_LINEUPS_INJURIES` · `NOT_RUN_SOURCE_NWSL_OFFICIAL` (ToU pinned
for ESPN; nwslsoccer.com still unpinned/undocumented) ·
`NOT_RUN_AUTHORIZED_TOA_ENUMERATION` · `NOT_RUN_NWSL_PAPER_HOOKUP` ·
`NOT_RUN_CENSUS_COMPLETE` (Gamma full pagination) · 2020 results hole ·
nwslR post-2024-04 defect · 4 disputed rows.

## Next steps (in order, each behind its own gate)

1. Owner reviews this packet. If approved: successor PREP cycle
   (freeze-packet lanes per the sketch) — no scored cell before ITS GO.
2. Optional parallel lanes: Gamma full census + per-market fidelity
   measurement ($0 read-only); SoccerStatsUS parser (2013–2015 backfill
   decision input); secondary-source resolution for the 2 unresolved rows.
3. When NWSL match markets list on Polymarket: snapshot-capture pilot can be
   prepared in the successor ($0 read-only capture), while adding NWSL to the
   paper scope remains a separate owner decision + separate gate, permanently
   outside this cycle.

**Nothing scored, nothing fitted, no odds captured, no paper-scope change, no
GO, no push/merge.** Other programs (NBA/WNBA/WSL/soccer/NFL, paper service,
cadence, ledger) untouched — verified: only this cycle's control dir + data
plane were written.
