# DATA_MANIFEST — NBA-WINPROB-PREP-V1 (seeded by controller; lane B extends with audit)

- dataset_id: nba-538-v1
- raw_path (outside git): ~/.my-quantitative-data/nba-538-v1/raw/nbaallelo.csv
- source_url: https://raw.githubusercontent.com/fivethirtyeight/data/master/nba-elo/nbaallelo.csv
- retrieved_at: 2026-10-04 (local) by controller (curl), under owner conditional grant
  2026-10-04 + lane A CONDITIONAL-YES (RIGHTS_MEMO_NBA.md §6)
- sha256: d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc (MATCHES lane A observed)
- size_bytes: 18173265
- license: CC BY 4.0 (data) — attribution + internal-research-only conditions in
  ~/.my-quantitative-data/nba-538-v1/raw/ATTRIBUTION.md
- controller first observations (to be verified by lane B, not authority):
  header has 23 columns incl. seasongame (not in README list); first data row
  gameorder=1, game_id=194611010TRH, date 11/1/1946 (BAA era, lg_id col present);
  tail row gameorder=63157, 2015-06-16 GSW@CLE — chronological end of file MUST be
  censused by lane B (hypothesis: this "Complete History" file ends ~2015, later
  seasons may live in other 538 files — DO NOT ASSUME, MEASURE).
- lane B outputs: DATASET_AUDIT.md (this dir) + handoff_B.json

## Lane B audit (2026-10-04) — extends this manifest; controller-seeded provenance above unchanged

Audit authority: `lanes/B_dataset/DATASET_AUDIT.md` (+ `audit_script.py`,
`DATASET_SCHEMA.md`, `handoff_B.json` in this dir). All numbers measured by
lane B code on the file above (sha256 re-verified MATCH before audit).

- rows/games/seasons: 126,314 rows; 63,157 games (exactly 2 rows each); seasons
  year_id 1947..2015; dates 1946-11-01..2015-06-16; 0 rows after 2015-07-01
  (controller tail hypothesis CONFIRMED — file ends with 2014-15 season).
- integrity: 0 mirror violations across both rows of all 63,157 games; 0 nulls
  except notes; 0 duplicate games; 0 seasons deviating >10% from era expectation.
- identity: 104 team_id -> 53 fran_id; every fran_id is one connected on-court
  lineage; fran_id adopted as lineage key (naming traps documented in audit §4).
- frozen split proposal (lane C placeholder rule): TEST = year_id 2009..2015
  (8,956 games), TRAIN = year_id 1947..2008 (54,201 games) — pending
  controller landing, then frozen.
- 538 priors (cross-check only): expansion cold start elo 1300.0; season-boundary
  reversion median 0.7542 toward 1500.
- COVID/bubble audit: NOT_APPLICABLE (no post-2015 data in this file).
