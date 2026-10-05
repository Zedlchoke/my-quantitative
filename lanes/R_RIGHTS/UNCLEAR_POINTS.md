# UNCLEAR_POINTS — open questions requiring owner/legal decision before ANY publication
# or commercial use of derived player features

- Cycle: WINPROB-PLAYERDATA-PREP-V1 · Lane: R_RIGHTS · Date: 2026-10-05
- Framing: internal research documentation only. This file lists open questions; it is
  **not legal advice** and does not resolve any of them. Fail-closed rule: until an item
  is resolved by the owner (with competent advice where relevant), treat the affected use
  as NOT PERMITTED outside this workspace's private research.
- Evidence base: verbatim quotes in RIGHTS_MATRIX.md, all fetched 2026-10-05 with URLs +
  UTC timestamps (fetch_log.txt, fetches/).

## U1. Underlying league/ESPN data rights are NOT covered (or proven covered) by the repo licenses

- What is verified: hoopR-nba-data / hoopR-nba-stats-data / wehoop-wnba-data /
  wehoop-wnba-stats-data grant CC BY 4.0 over "the contents of this repository (data,
  code, and documentation)"; nflverse-data carries full CC BY 4.0 legalcode.
- What stays unclear: those grants come from the repo maintainers, not from ESPN, the NBA,
  the WNBA, or the NFL. None of the fetched LICENSE/README files quotes, links, or
  acknowledges the terms of service of ESPN APIs, stats.nba.com, stats.wnba.com, or
  NFL/GSIS feeds, and none contains a league-affiliation or "data property of" disclaimer
  (verified absent by grep across all fetched READMEs, 0 hits for
  terms-of-service/not-affiliated/disclaimer patterns).
- Open questions: (a) do ESPN/NBA/WNBA/NFL ToS permit this scraping-and-republishing
  pipeline at all; (b) does a CC BY 4.0 grant by a scrapist effectively transfer or
  license rights it does not own; (c) does the CC grant's "even commercially" reach
  league-derived statistics.
- Fail-closed consequence: the CC BY 4.0 attribution step is necessary but is NOT
  evidence that underlying rights are cleared. Any publication/commercial use needs an
  owner decision informed by the leagues'/ESPN's actual terms.

## U2. CC BY 4.0 attribution compliance in outputs is an unmet (future) obligation

- The deed requires (verbatim in RIGHTS_MATRIX.md §7): "appropriate credit ... a link to
  the license, and indicate if changes were made", plus creator/attribution-party names,
  copyright notice, license notice, disclaimer notice, and a link to the material where
  supplied; and "not in any way that suggests the licensor endorses you or your use".
- The workspace's internal feature tables currently carry provenance (sha256, URLs) but
  no publication-grade attribution/NOTICE layer. If any derived table were ever
  published or shared outside the workspace, attribution obligations attach.
- Open question: what exact attribution block per league/source the owner wants as the
  standard (proposed draft exists in the WNBA lane manifest, but it is lane-local, not
  owner-ratified).

## U3. Redistribution of derived tables (share-alike is absent, but scope of "Adapt" outputs is untested)

- CC BY 4.0 has no share-alike clause; adapted material may in principle be distributed
  under different terms **as long as** attribution and the no-additional-restrictions
  clause (cannot forbid others from doing what the license permits) are respected.
- Open question: whether publishing derived feature tables that embed substantial verbatim
  player-box content counts as redistribution of the licensed material (attribution
  mandatory) vs an unadapted copy (which must remain under CC BY 4.0). Edge: columns
  copied verbatim vs aggregate features. Owner/legal decision needed before any external
  release.

## U4. ToS of scraped endpoints (ESPN, stats.nba.com, stats.wnba.com, NFL feeds)

- Not fetched this cycle (out of lane scope; also these terms change). No lane may rely
  on "the repo did it, so it is fine". Any publication/commercial plan needs a fresh
  fetch + review of the current ToS of each upstream endpoint at that time.

## U5. balldontlie: Free tier excludes player stats; ToS and license of balldontlie data unexamined

- Verified (BALLDONTLIE_FREE.md): Free = Teams/Players/Games only; player stats endpoints
  paid. The vendor's ToS, acceptable-use policy, and the licensing status of any data
  obtained from balldontlie (can outputs be republished? at all? commercially?) were NOT
  fetched and remain UNCLEAR. The tier tables are marketing pages subject to change.
- Open question: if balldontlie is ever used (even for metadata), owner must review ToS;
  no assumption that paid tiers are affordable or permitted ($0 budget law).

## U6. Store-vs-producer license layering in sportsdataverse-data

- The store root LICENSE is MIT (store code) while the README badge is CC BY 4.0 (data)
  and each producer repo carries its own CC BY 4.0 LICENSE.md; there is NO NOTICE file
  (404) and the README does not enumerate per-tag licenses. The mapping release-tag →
  producing repo → license is documented in RIGHTS_MATRIX.md but relies on per-repo
  files, not on a single store-side statement.
- Open question: acceptable confidence for publication is an owner call; for internal
  PREP the per-producer CC BY 4.0 LICENSE.md files are the operative licenses.

## U7. nflfastR README carries no league disclaimer at HEAD; provenance of NFL player stats

- nflverse-data README is minimal and nflfastR README (HEAD, 2026-10-05) contains no
  "not affiliated with the NFL" language; the special-thanks section credits third-party
  sources (Nick Shoemaker's JSON pbp for 1999–2000; FTN Fantasy charting data). Whether
  FTN-derived fields (e.g. scramble marking) carry any additional restriction is
  UNCLEAR. nflverse weekly player stats (Lane C's target) sit in the same release store
  under CC BY 4.0, but per-release provenance (which fields trace to NFL GSIS vs charting
  vendors) is not documented repo-side.
- Open question: field-level provenance for NFL player stats before any external use.

## U8. Attribution for WNBA corpus already on disk

- The on-disk corpus (`~/.my-quantitative-data/wnba-prep-v1/`) was pulled from
  sportsdataverse-data release tags produced by wehoop-wnba-data (ESPN WNBA) /
  wehoop-wnba-stats-data (stats.wnba.com). License chain verified CC BY 4.0 upstream, but
  the ATTRIBUTION.md shipped with the corpus (if any) was authored by a prior lane, not
  ratified by the owner. If the corpus or derivatives leave the workspace, U2 applies.

## U9. No legal review has occurred anywhere in this chain

- Nothing in any fetched document constitutes authorization from ESPN, NBA, WNBA, NFL, or
  their teams. "CC BY 4.0" is a copyright license grant by the repo maintainers; it does
  not by itself answer trademark, database-rights, right-of-publicity (player names/
  images in commercial products), gambling/advertising-regulation, or contract-law
  questions. All of the above are outside this lane's scope and remain OPEN.

## Precedent to keep

The fail-closed pattern follows plan doctrine: what is not evidenced is NOT_RUN, never
inferred PASS. For rights: what is not cleared is UNCLEAR, never assumed permitted.
