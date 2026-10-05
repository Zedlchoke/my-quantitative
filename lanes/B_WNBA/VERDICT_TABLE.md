# VERDICT TABLE — Lane B (WNBA PLAYER DATA) · cycle WINPROB-PLAYERDATA-PREP-V1 · 2026-10-05

Legend: PASS = measured evidence recorded (command + numbers in this lane's files);
FAIL = measured and failed; NOT_RUN / NOT_RUN_PIT = no evidence, not inferred.

## 1. Checks × data type

| # | check | data type | verdict | evidence |
|---|---|---|---|---|
| 1 | corpus integrity: 50/50 files re-hashed vs prior-cycle manifest sha256 | on-disk bytes | **PASS** | 50 match / 0 mismatch / 0 missing / 86,572,091 B (`measure_b.py` part 1, `measurements_b.json:integrity`) |
| 2 | files downloaded this session | — | **none (by design)** | expected none; corpus pre-existing, EXTEND-ONLY respected; 0 downloads, $0 |
| 3 | ESPN-side game universe re-derivation | schedules | **PASS** | 5,988 re-derived = prior cycle exactly; forfeit 401018942 + postponed 401507167/401857072 + 21 ASG rows re-dropped |
| 4 | player_box join vs universe (ESPN game_id) | player_box | **PASS** | 5,624/5,988 = 93.92% overall; 100% every season 2013+; backfill holes 2002 (5.9%), 2003 (76.1%), 2004 (90.3%) enumerated |
| 5 | game_rosters join vs universe | game_rosters | **PASS** | 5,983/5,988 = 99.92%; 5 universe games ever missing rosters (2002/2006×2/2008/2016) |
| 6 | both teams present per game | player_box | **PASS** | team_id-per-game == 2 in 5,643/5,643 games (0 violations) |
| 7 | duplicates (game_id, athlete_id) | player_box | **PASS** (1 explained artifact) | exactly 1 key ever: 250521017/athlete 30 double-listed HOU+SAS (2005 trade artifact); guard still mandatory |
| 8 | players-per-game distribution | player_box | **PASS** | median 22–25, p95 23–27, min 14–21 across all seasons; no pathology |
| 9 | starters = 5 per team-game | game_rosters | **PASS** (with measured exceptions) | 11,969/12,005 = 99.70% exactly 5; 33 team-games with 0 starter flags (2002–2018, enumerated); 3 anomalies (6/4/4, 2016/2017/2020); 2021–2026 perfect |
| 10 | DNP / non-player handling pb vs rosters | both | **PASS** | non-players appear in player_box (null minutes all eras; DNP flag 2012+); pb keys ⊆ rosters keys in all 25 seasons; `active` NOT an availability flag; `reason` defaulted (`COACH'S DECISION` incl. 100% of 2013 starters) |
| 11 | schema drift | player_box | **PASS** | 3 eras: 35 cols (2002, short names, string stats, minutes 100% null), 56 (2003–2011), 57 (2012+, +`reason`); rosters 22 cols identical 2002–2026 |
| 12 | era gap quantified vs 7,017 union | universe | **PASS** | player-level max coverable = 5,988/7,017 = 85.3%; 1,022 pre-2002 games + 7 stats-only 2002–2004 rows unkeyable; store publishes no pre-2002 player box/rosters |
| 13 | forfeit/postponed/ASG/ESPN-only/Cup-finals handling | both | **PASS** | forfeit: rosters-only (no pb); postponed: absent both; ASG: present in files, excluded by universe law; 3 ESPN-only regular rows + 6 Cup finals present in player_box |
| 14 | rights verified from official sources (verbatim + timestamps) | rights | **PASS** | RIGHTS.md: CC BY 4.0 README badge + MIT root LICENSE quoted verbatim; wehoop docs; underlying ESPN/WNBA rights NOT granted by any held license (fail-closed §4) |
| 15 | prior-games aggregates as-of join (tip time) | PIT | **PASS_CONSTRUCTIBLE** | worked example: CON 2013 game 400445816 (tip 2013-07-06T23:00Z), prior-5 by strict tip, minutes 199–202/game, per-player extraction clean |
| 16 | target-game starter/active/DNP/reason as pre-game feature | PIT | **NOT_RUN_PIT** | no pre-game publish timestamp evidenced (snapshot assets); `active`/`reason` also quality-barred |
| 17 | opening-roster variant v1 (all-season use) | PIT | **NOT_RUN_PIT** | PIT_AUDIT §3; v2 (from game 2 onward) = PASS by construction, design-level |
| 18 | injury/availability dated feed | PIT | **NOT_RUN_PIT** | no dated archive exists in the rights-cleared corpus |
| 19 | win-prob / scored computation on real outcomes | — | **NOT_RUN** | out of scope by plan; 0 scored consumed |
| 20 | expansion/2020-COVID risk documented | corpus | **PASS** | 2020 = 147 games real; expansion GSV 2025, TOR/PDX 2026 sparse — carried into FEATURE_PROPOSALS risks |

## 2. Actually-downloaded-this-session list

**None.** Expected per dispatch ("corpus pre-existing — verify hashes instead"): all 50 files
were verified by re-hash against `download_manifest_r2.json`. Data dirs written this session:
none (corpus untouched, read-only). Git artifacts: only `lanes/B_WNBA/**` +
`lanes/DISPATCH/handoff_B_WNBA.json`, uncommitted.

## 3. Remaining blockers (for a FEATURE-PREP successor, none for this PREP cycle)

1. **B1 (data)** player_box backfill holes: 2002 (16-game stub, minutes 100% null) and 2003
   (76.1% coverage). A successor building frozen tables must set a season floor (recommend:
   game-level features 2004+, minutes-quality features 2013+) or pull the release assets
   again only if the store re-publishes deeper history (asset `updated_at` 2026-07-16
   suggests active backfilling — re-check upstream before assuming 2002–2003 are final).
2. **B2 (PIT)** no publish timestamps on any asset → target-game availability features are
   permanently out unless a dated feed source is found and rights-cleared; opening-roster
   use restricted to v2 (game 2 onward).
3. **B3 (semantics)** `active` and `reason` are not availability fields (measured); any
   successor must encode availability only via prior-game null-minutes / `did_not_play`.
4. **B4 (rights)** CC BY 4.0 is a README badge with an MIT root LICENSE; maintainer
   confirmation needed before any external redistribution/commercial use. Internal research
   unaffected.
5. **B5 (schema)** era guards at 2002|2003 and 2011|2012 mandatory for any player_box consumer.

## 4. Cost

Actual spend: **$0** (no downloads, no accounts, no API keys; only public GitHub README/LICENSE
fetches and local compute).

## 5. Recommendation (PREP-level, NOT a scored GO)

**READY — recommend the owner authorize a FEATURE-PREP successor step** (building frozen
player-feature tables under the PIT laws above, WNBA-only), with scope conditions:
seasons with ≥90% player_box coverage (2004+; minutes/DNP-quality features 2013+),
franchise-lineage keys, W-H2 v2 as-of law, era guards, and the W-H1/W-H2 comparison
machinery already drafted in the prior cycle. **No scored GO is implied or requested**;
any scored successor additionally needs its own registration, data/code freeze, A7
prelaunch and owner typed GO at its own gate.
