# BALLDONTLIE_FREE — Free-tier endpoint evidence (PUBLIC docs only, no key, no signup)

- Cycle: WINPROB-PLAYERDATA-PREP-V1 · Lane: R_RIGHTS · Date: 2026-10-05
- Method constraint honored: only public documentation pages were fetched. No API key was
  obtained, no account created, no API request made against `api.balldontlie.io`. $0.
- Bottom line for the workspace: **the balldontlie FREE tier does NOT include player stats,
  player box scores, or season averages on any sport.** Free = Teams / Players / Games
  metadata only. The workspace MUST NOT assume Free provides player stats — this file is
  the evidence.

## Fetch register (HTTP status + UTC)

| page | URL | HTTP | retrieved UTC | bytes |
|---|---|---|---|---|
| NBA docs root (docs site) | https://docs.balldontlie.io/ | 200 | 2026-10-05T07:20:47Z | 457,047 |
| "pricing" path (probe) | https://balldontlie.io/pricing | **404** | 2026-10-05T07:20:47Z | 10,722 |
| homepage | https://balldontlie.io/ | 200 | 2026-10-05T07:20:48Z | 43,169 |
| NFL product/docs page | https://nfl.balldontlie.io/ | 200 | 2026-10-05T07:22:10Z | 925,695 |
| WNBA product/docs page | https://wnba.balldontlie.io/ | 200 | 2026-10-05T07:22:11Z | 188,668 |

Note: `balldontlie.io/pricing` does not exist (404). The tier delimitation lives in the
"Account Tiers" section of each sport's docs page, quoted verbatim below.

## 1. NBA — https://docs.balldontlie.io/ ("Account Tiers" section, verbatim)

The page contains exactly one Account Tiers section (verified: 3 occurrences of the string,
all TOC/sidebar/heading of the same section). Intro paragraphs verbatim:

```
Account Tiers

There are three different account tiers which provide you access to different types of
data. Visit our website to create an account for free.

Paid tiers do not apply across sports. The tier you purchase for NBA will not
automatically be applied to other sports. You can purchase the ALL-ACCESS ($299.99/mo)
tier to get access to every endpoint for every sport.

Read the table below to see the breakdown.
```

Endpoint availability table verbatim (Endpoint | Free | ALL-STAR | GOAT):

```
Teams                      | Yes | Yes | Yes
Players                    | Yes | Yes | Yes
Games                      | Yes | Yes | Yes
Game Player Stats          | No  | Yes | Yes
Active Players             | No  | Yes | Yes
Player Injuries            | No  | Yes | Yes
Season Averages            | No  | No  | Yes
Team Season Averages       | No  | No  | Yes
Game Advanced Stats        | No  | No  | Yes
Box Scores                 | No  | No  | Yes
Lineups                    | No  | No  | Yes
Team Standings             | No  | No  | Yes
Leaders                    | No  | No  | Yes
Betting Odds               | No  | No  | Yes
Player Props               | No  | No  | Yes
Daily Fantasy Sports       | No  | No  | Yes
Team Contracts             | No  | No  | Yes
Player Contracts           | No  | No  | Yes
Player Contract Aggregates | No  | No  | Yes
Plays                      | No  | No  | Yes
```

Tier pricing table verbatim (Tier | Requests / Min | $USD / mo.):

```
GOAT      | 600 | 39.99
ALL-STAR  | 60  | 9.99
Free      | 5   | 0
```

48-hour trial section verbatim (recorded because it delimits free-vs-paid mechanics;
the workspace does NOT use trials — payment method required):

```
48-hour free trial

Every paid sport offers a 48-hour trial of the GOAT tier (all endpoints, 5 req/min
during the trial). ALL-ACCESS is also available as a 48-hour trial with the same
5 req/min trial limit. A payment method is required at signup; there is no charge
until the trial ends, and you can cancel anytime from your dashboard. One trial per
sport per account. Existing ALL-STAR subscribers may trial the GOAT upgrade for
their sports.
```

Reading of the NBA table: Free gets Teams/Players/Games ONLY.
- "Game Player Stats" (player box scores) = **No on Free** (ALL-STAR and above).
- "Season Averages" = **No on Free AND No on ALL-STAR — GOAT only** ($39.99/mo).
- "Box Scores" (incl. live box scores) = **GOAT only**.

## 2. NFL — https://nfl.balldontlie.io/ ("Account Tiers" section, verbatim)

```
Account Tiers

There are three different account tiers which provide you access to different types of
data. Visit our website to create an account for free.

Paid tiers do not apply across sports. The tier you purchase for NFL will not
automatically be applied to other sports. You can purchase the ALL-ACCESS ($299.99/mo)
tier to get access to every endpoint for every sport.

Read the table below to see the breakdown.
```

```
Teams                   | Yes | Yes | Yes
Players                 | Yes | Yes | Yes
Games                   | Yes | Yes | Yes
Player Injuries         | No  | Yes | Yes
Active Players          | No  | Yes | Yes
Team Standings          | No  | Yes | Yes
Stats                   | No  | Yes | Yes
Season Stats            | No  | Yes | Yes
Team Stats              | No  | Yes | Yes
Team Season Stats       | No  | Yes | Yes
Advanced Rushing Stats  | No  | No  | Yes
Advanced Passing Stats  | No  | No  | Yes
Advanced Receiving Stats| No  | No  | Yes
Plays                   | No  | No  | Yes
Betting Odds            | No  | No  | Yes
Player Props            | No  | No  | Yes
Daily Fantasy Sports    | No  | No  | Yes
Fantasy Football        | No  | No  | Yes
Player Designations     | No  | No  | Yes
Team Roster             | No  | No  | Yes
```

Tier pricing table identical to NBA (GOAT 600/$39.99, ALL-STAR 60/$9.99, Free 5/$0).

Reading: NFL Free = Teams/Players/Games ONLY. "Stats" (weekly player stats) and
"Season Stats" = **No on Free** (ALL-STAR+). Advanced stat groups and plays = GOAT only.

## 3. WNBA — https://wnba.balldontlie.io/ ("Account Tiers" section, verbatim)

```
Account Tiers

There are three different account tiers which provide you access to different types of
data. Visit our website to create an account for free.

Paid tiers do not apply across sports. The tier you purchase for NBA will not
automatically be applied to other sports. You can purchase the ALL-ACCESS ($299.99/mo)
tier to get access to every endpoint for every sport.

Read the table below to see the breakdown.
```

```
Teams               | Yes | Yes | Yes
Players             | Yes | Yes | Yes
Games               | Yes | Yes | Yes
Active Players      | No  | Yes | Yes
Player Injuries     | No  | Yes | Yes
Standings           | No  | Yes | Yes
Play-by-Play        | No  | Yes | Yes
Player Stats        | No  | No  | Yes
Team Stats          | No  | No  | Yes
Player Season Stats | No  | No  | Yes
Team Season Stats   | No  | No  | Yes
Betting Odds        | No  | No  | Yes
Player Props        | No  | No  | Yes
```

Tier pricing table identical to the other sports.

Reading: WNBA Free = Teams/Players/Games ONLY; "Player Stats" and "Player Season Stats"
are **GOAT-only** (No even on ALL-STAR). (Copy quirk preserved verbatim: the WNBA page's
cross-sports paragraph still says "the tier you purchase for NBA".)

## Consequence for this cycle

- balldontlie can serve, at most, **Teams / Players / Games metadata** on the Free tier,
  at 5 requests/min, and only if the owner ever decides to register an account (out of
  scope here — no keys, no signups this cycle).
- Any assumption that Free provides player box scores, weekly player stats, season
  averages, or injuries is CONTRADICTED by the vendor's own tier tables above. Prior-cycle
  caution ("do NOT assume Free player stats") is confirmed with verbatim evidence.
- Tier definitions are vendor marketing pages subject to change without notice; re-verify
  before any future use, and treat any usage as also subject to the vendor's ToS (which
  this cycle did not fetch beyond these docs pages — see UNCLEAR_POINTS.md).
