# PIT AUDIT — NBA 2016+ candidate features — Lane A, NBA-WINPROB-NG-PREP-V1

Cycle NBA-WINPROB-NG-PREP-V1 · lane A_DATA · 2026-10-05 (UTC).
Scope: pre-game knowability (PIT) verdicts for every candidate feature class
named in the plan, plus the input-freeze law. AUDIT ONLY — no features were
computed, no outcomes scored (budget 0 scored).

PIT bar used throughout: a feature is PIT-legal for game *g* iff **every input
record it consumes was determined strictly before `tip_utc(g)`** and is
deterministically reconstructible from archived bytes. Where a source exposes
only per-FILE publish times (daily release assets), the guaranteed freeze point
is the file's publish instant, not the record's event time — the audit states
which bar each class can actually meet.

## Input-freeze law (general)

- Freeze state at `tip_utc(g)` − ε: only games with `tip_utc < tip_utc(g)`
  may feed any prior-derived aggregate. Strict inequality on the canonical
  `tip_utc` of GAME_UNIVERSE_SPEC_NBA_2016PLUS.md §2 (never `game_date`).
- Excluded games (All-Star family, postponed listings) contribute NOTHING to
  any prior state — they were never played. Postponed makeups enter the state
  at the MAKEUP's tip, not the original slot.
- Flagged Cup final rows enter as normal played results if a mechanism elects
  to consume results from them (they did occur); their separate flag must be
  preserved so the protocol lane can report them separately. Design decision
  delegated to lanes B/C — not decided in this audit.

## Verdicts by feature class

| # | Feature class | Verdict | One-line reason |
|---|---|---|---|
| 1 | Results-derived rolling ratings (Elo family; B1* K=32/HCA=100) | **PIT_PASS (conditional)** | Rating state = fold over strictly-earlier tips; knowable by construction from the corpus itself |
| 2 | Schedule-derived rest / travel / tz (b2b, 3in4, travel bucket, tz shift) | **PIT_PASS (conditional)** | Fixture list (dates, venues, tips) is published ahead of play; prior games known |
| 3 | Box/pbp-derived priors (train-only aggregates, F8 pace/efficiency init) | **PIT_PASS (conditional)** | Aggregates must close their window strictly before current tip; current-game pbp is leakage |
| 4 | Spread line (`game_spread` / `home_favorite` / `home_team_spread`) | **UNVERIFIED_PIT** | Line rides in the FINAL game payload; opening/closing/snapshot semantics and freeze instant undocumented upstream |
| 5 | Injury / roster availability | **NOT_RUN_PIT** | No rights-verified archive with per-record publish timestamps ≤ tip − cadence exists among $0 sources (candidates failed below) |

## 1. Results-derived ratings — PIT_PASS (conditional)

Conditions (all enforceable from the spec):
- Update only on games with `tip_utc` strictly earlier than the current tip.
- Consume only the deduped played universe (§4 of the spec): exhibitions and
  postponed listings never update state; the 3 Cup finals are flagged (see
  input-freeze law).
- Baseline constants: NBA B1* = K=32, HCA=100, pooled RS LL 0.5987 vs B0
  0.6769 (n=8369) — FROZEN from NBA-WINPROB-SCORED-V1
  (`scored_summary.json`, re-read this session; arms B0, B1-a..d, B2-a..d).
  Never re-tuned; any new mechanism must beat B1*, not B0.
- Negative control: time-shuffled twin (same games, shuffled order) must
  degrade the mechanism — a mechanism insensitive to shuffling is not using
  genuine pre-game information.

## 2. Schedule-derived rest / travel — PIT_PASS (conditional)

- Inputs are the fixture attributes of the current game (venue, tip, home/away)
  plus the team's strictly-prior played games — all knowable at tip.
- Rest = current `tip_utc` − max prior own-team `tip_utc`; b2b / 3in4 derived
  by counting games in the trailing window; travel/tz from venue change
  between consecutive games. Neutral-site globals (London/Mexico/Paris, 19
  rows 2016–2026) are real RS games and carry legitimate travel attributes.
- Postponement rule: the original slot must be treated as NOT PLAYED for rest
  accumulation (67 listings); the makeup slot re-enters at its own tip.
- Condition: use the corpus's own schedule bytes only; no live fetches.

## 3. Box/pbp-derived priors — PIT_PASS (conditional)

- Window law: aggregates (pace, efficiency, usage, rotations) over games with
  `tip_utc < tip_utc(g)` only. The current game's rows live in the same pbp
  parquet — any "same-season expanding" implementation must exclude it
  explicitly; a date-keyed (not tip-keyed) window leaks same-night late games.
- pbp holes documented in spec §5 (14 played games without pbp, ERRATUM R1 /
  defect D1: 2016×3, 2018×4, 2020×6, 2026×1 — full game-id list in spec §5)
  must be tolerated by feature code (smaller initial windows), never
  imputed silently.
- Same negative-control requirement as class 1.

## 4. Spread line — UNVERIFIED_PIT (do not advance as a mechanism)

Measured facts: `game_spread`, `home_favorite`, `home_team_spread` are
100% populated in the pbp release for every season 2016–2026 (spec §6) —
coverage is not the problem. The PIT problem: the columns are carried in the
FINAL game payload; upstream (sportsdataverse/ESPN) documents no field-level
timestamp saying whether the value is the opening line, the closing line, or
an intra-week snapshot. Therefore the value cannot be proven knowable at
`tip_utc(g) − cadence` from archived bytes. Verdict **UNVERIFIED_PIT**:
- NOT eligible as a hypothesis mechanism in the successor protocol (plan also
  bans closing/market odds as mechanisms).
- May serve only as an owner-approved DIAGNOSTIC reference with the
  unverified-timing caveat carried verbatim, never as a PIT feature.

## 5. Injury / roster — NOT_RUN_PIT

Bar (plan): rights-verified archive with per-record publish timestamps
≤ tip − cadence, proven on a spot sample. Candidates examined, all FAIL:

| Candidate | Failure reason |
|---|---|
| balldontlie free tier | Endpoints = Teams/Players/Games only (docs-verified prior lane; re-confirmed working this session). No injuries/roster-snapshot endpoint; games carry no per-record publish timestamp. |
| hoopR/sportsdataverse releases | team/player box + pbp are post-game artifacts; per-FILE `updated_at` only (daily); absence-from-boxscore is inference, not a published pre-game report. Supports "did not play" facts post-hoc — that is class-1/3 material, not an injury-report feature. |
| ESPN injury API / NBA.com injury reports | Live, unauthenticated, no archival snapshot store with per-record timestamps; no open license; scraping not exercised this cycle. Rights + provenance both unproven. |
| Paid providers (Sportradar et al.) | Purchases banned ($0 cycle). |

Consequence: injury/roster availability may NOT be a feature in the successor
protocol draft unless a successor cycle first proves an archive against the
bar above (spot sample: N≥20 report records across ≥2 seasons, each with a
publish instant ≤ its game's tip − cadence, rights memo verbatim).

## Audit coverage statement

This audit is a DESK verdict over source schemas and release semantics
measured this session (spec + DOWNLOAD_MANIFEST) plus the prior lane's
license verifications. No injury/report endpoint was fetched (nothing to
fetch on the free tier); no spread-timing probe exists to fetch. Both
limitations are inherent to the $0/PREP constraints, not skipped work.
