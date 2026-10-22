# ERRATUM EXEC-4 — SOCCER expansion survey: source offers no second men's-international key; stage/venue law committed (2026-10-07, post-GO)

Owner instruction 2026-10-07: expand SOCCER beyond `soccer_uefa_nations_league`
to men's international football the frozen B1 model can identify; no club
competitions; same-90-minute-result law for odds; fail-closed when unsure.

## 1. Survey result (real data, 0 credits spent)

`get_sports` (0-credit, snapshot bytes + sha256 fe60ea5b0e60faec… persisted at
`<data-root>/data/sports_snapshot.json`) enumerates the WHOLE source: 85 keys,
48 active soccer keys, ZERO inactive soccer keys. The ONLY men's-international
soccer key on this source today is `soccer_uefa_nations_league`. There is NO
World-Cup-qualifier key (any confederation), NO continental-cup key (Euro /
Copa América / AFCON / Asian Cup / Gold Cup — the only "uefa/euro" soccer keys
are the club competitions), and NO international-friendly key, active or
inactive. **Nothing qualifies to be added to `sport_keys.SOCCER`; the config's
sport-key list is unchanged by this erratum.** The survey table with per-
category verdicts (ALREADY_ENABLED / NOT_RUN_SOURCE_ABSENT / OUT_OF_SCOPE) is
`SOCCER_EXPANSION_SURVEY_20261007.json`. When the source lists a seasonal
international key (WCQ / continental / friendly windows), the same survey runs
first; only then a config commit.

## 2. Same-result law now enforced (owner item 4)

The frozen B1 target is 3-way FULL-TIME 90/120 minutes with shootouts never
flipping it (`soccer_b1_replay.make_target`: "Shootout fields NEVER flip it"),
while Pinnacle soccer 1X2 settles on 90 minutes. Therefore any match where
extra time is possible carries DIFFERENT model and market semantics and must
never be bet. Venue adds the same discipline: the frozen adapter passes
`neutral=False` (home advantage to the listed home side), so only formats that
guarantee true home-and-away are modelable.

`config.json` (schema v2) now carries a committed `competition_law` table:
- `soccer_uefa_nations_league` 2026-09-01..2026-11-30 →
  `LEAGUE_PHASE_HOME_AWAY`, bet-ELIGIBLE (league phase double-headers, 90-
  minute regulation, true home/away — evidence in the config entry). This
  retro-validates the existing England-Croatia FORECAST row (2026-11-12).
- `soccer_uefa_nations_league` 2027-03-01..2027-06-30 →
  `KNOCKOUT_ET_POSSIBLE`, NOT_RUN (QF ties + March/June Final Four: extra
  time/penalties possible, single-venue finals possibly neutral).
- ANY other key or uncovered kickoff date → `UNKNOWN_STAGE`, NOT_RUN
  (fail-closed, never guessed).

Wiring: `soccer_stage_law()` runs BEFORE the crosswalk/engine in real
`forecast` (non-eligible fixtures are journaled `NOT_RUN_STAGE_LAW` with the
specific stage reason and never reach the engine) and again as a safety net in
real `decide` (covers matches forecasted before a law window landed). `plan`
now reports `stage_bet_eligible` and factors it into `eligible_now`.

## 3. Cross-key integrity + visibility

- Cross-key duplicate protection: two registered sport keys listing the same
  real match (same (commence_time, team-set) slot, different event ids) now
  refuse with `BLOCKED_FIXTURES_DUPLICATE` naming both keys — no duplicate
  fixtures/bets across keys is possible.
- Per-competition visibility (owner item 6): the pinned dashboard is byte-
  frozen, so the runner now writes an exec-owned supplement
  `soccer_by_competition.json` next to every dashboard build with per-
  competition BET / NO_BET / NOT_RUN counts; the CLI `dashboard` output
  includes the same block.

## 4. Gate reading (owner item 7)

No new Owner GO is required by the plan for this change: the config law
("grows only by an explicit config commit") covers sport-key and config
growth; this change adds ONLY fail-closed restrictions (stage/venue law,
cross-key refusal) and no new spend (0 credits this session), no model,
threshold, odds-proxy, or timing change. The frozen B1 model, paper law
(1,000 USD wallet, 5 USD stake, 100 USD open cap, EV/cost/drawdown, PIT,
quota, key handling) are untouched; the pinned core diff is empty.

## 5. State after this erratum

Battery 51/51 (46 + 5 new: stage classification, engine blocking, terminal
journal, cross-key collision/union, per-competition report). Ledger still
exactly 8 rows (all prior rows preserved; nothing written this session).
Quota day 4/4 (spent yesterday's window), month 4/120, provider 492. The
scheduled one-shot capture (2026-10-08 00:10Z) proceeds unchanged for the
England-Croatia 1X2 verification.
