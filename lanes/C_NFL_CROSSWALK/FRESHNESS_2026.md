# FRESHNESS 2026 — Lane C_NFL_CROSSWALK · WINPROB-PLAYERFEAT-PREP-V1

Measured 2026-10-05 from bytes; release build taken: **2026-10-04T15:06:29Z**
(`timestamp.json`/`timestamp.txt` both = `{"last_updated":"2026-10-04 11:06:29 EDT"}`;
GitHub API asset `updated_at` 2026-10-04T15:06:30Z agrees). Evidence:
`logs/freshness_qb_checks.json`, `logs/schema_audit_raw.json`.

## 1. Release timestamp

`players` release is a rolling re-cut store (published 2022-06-19, asset rewritten each
build). This lane's snapshot = build 2026-10-04T15:06:29Z, i.e. **T-1 day** vs the
predecessor stats build (2026-10-05T05:30:28Z). Frozen sha256
`485b1980…304885e2` is the evidence anchor; in-season re-pulls will differ by design.

## 2. Team domain & current rosters

- `latest_team`: 0 nulls, **all 32 teams present** (no pseudo-teams like FA/RET in the domain).
- Current-season roster proxy: `status=="ACT"` AND `last_season==2026` = **1,731 players
  across all 32 teams, 52–55 per team** — consistent with 53-man active rosters at the
  build date.

## 3. Named-starter crosswalk spot checks (top QBs by 2026 passing yards, weekly stats wk1–4)

| GSIS | stats name | pass yds | crosswalk name | pos | latest_team | status | pfr_id | last_season |
|---|---|---|---|---|---|---|---|---|
| 00-0039150 | Bryce Young | 1,268 | Bryce Young | QB | CAR | ACT | YounBr01 | 2026 |
| 00-0033106 | Jared Goff | 1,214 | Jared Goff | QB | DET | ACT | GoffJa00 | 2026 |
| 00-0026498 | Matthew Stafford | 1,189 | Matthew Stafford | QB | LA | ACT | StafMa00 | 2026 |
| 00-0036442 | Joe Burrow | 1,171 | Joe Burrow | QB | CIN | ACT | BurrJo01 | 2026 |
| 00-0039163 | C.J. Stroud | 1,141 | C.J. Stroud | QB | HOU | ACT | StroCJ00 | 2026 |
| 00-0033077 | Dak Prescott | 1,065 | Dak Prescott | QB | DAL | ACT | PresDa01 | 2026 |
| 00-0036264 | Jordan Love | 1,041 | Jordan Love | QB | GB | ACT | LoveJo03 | 2026 |
| 00-0034857 | Josh Allen | 1,039 | Josh Allen | QB | BUF | ACT | AlleJo02 | 2026 |

8/8 present with **both** GSIS and PFR ids, ACT status, current team. Cross-source identity
confirmed (names in weekly stats == crosswalk display names).

## 4. Roster-move lag risk (named, quantified where measurable)

- `last_season == 2026` = 2,586 players — file carries the current season's universe
  including post-cut players; in-season **trades/waiver claims update only at the next
  release build** (T-1 day observed here; worst case = time since last build, unbounded
  within the week). Any team-attribution feature must read team from the **weekly-stats
  per-game `team`/`opponent_team` columns (week-of-record), not from `latest_team`** —
  this is the same mid-season-trade law the predecessor documented for stats.
- 2026 rookie class coverage: 488 in file, 477 (97.75%) with pfr_id; 11 rookies pfr-null
  (incl. Peter Woods, gsis 00-0041545, DT KC — ACT, appears in 2026 weekly stats, snap-join
  blocked for him specifically).
- pfr-null cohort is structurally spread across all veteran classes (2,165 total; only 27
  with last_season 2026) — it is a **PFR-coverage gap on fringe players, not staleness**.
