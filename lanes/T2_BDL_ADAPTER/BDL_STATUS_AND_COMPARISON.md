# T2 — BALLDONTLIE status, adapter, and hoopR comparison (2026-10-05)

## CURRENT STATUS (supersedes all historical sections below)

- **Key**: loaded by owner into macOS Keychain (`balldontlie`/`winprob-ng`) on 2026-10-05.
  Adapter verified PRESENT via `bdl_adapter.py` check. Value never printed.
- **Cross-check**: **5/5 MATCH** (T2c, 2026-10-05) — see §7 below for full table.
- **BDL verdict**: **VIABLE CROSS-CHECK SOURCE** alongside hoopR (PRIMARY).
- **Base URL**: `https://api.balldontlie.io/v1` (docs-verified).
- **Free tier**: Teams/Players/Games, 5 req/min; supports `dates[]=YYYY-MM-DD`
  and `seasons[]=YYYY` array-syntax filtering.
- **hoopR**: remains PRIMARY for NBA 2016+ (CC BY 4.0, no rate limit, full PBP).

## 1. [HISTORICAL] Initial status (superseded — key now loaded)

`BLOCKED_NO_KEY` → `KEY_AVAILABLE_TO_OWNER_BUT_NOT_IN_RUNTIME` → **KEY_LOADED**.

The owner supplied an API key in the Codex chat on 2026-10-05. Per the owner's
directive the key is a SECRET and was not copied into any artifact. The owner
then loaded it into Keychain per the instructions in §4 below.

SECURITY INCIDENT (handbook §29 class): the key transited a chat channel. The
owner was advised to **rotate the key**. ToS §5 (verified verbatim below):
the owner is "responsible for maintaining the confidentiality of your account
credentials."

## 2. Docs/ToS re-verification (fetched 2026-10-05)

- Docs (docs.balldontlie.io): free tier = **Teams/Players/Games only**; rate
  limit **5 req/min**. Coverage: "The API contains data from 1946-current."
  Games objects carry `date` (YYYY-MM-DD) AND `datetime` (ISO-8601 UTC).
  Auth: plain `Authorization: <key>` header.
  **Param syntax**: array-style — `seasons[]=2024`, `dates[]=2024-01-25`,
  `start_date=`, `end_date=` (NOT scalar `seasons=2024`).
- ToS (Last Updated 2026-09-17): §6 broad grant for research/AI-ML;
  §5 credential confidentiality; restrictions: no competing products,
  no reselling raw data, no key sharing.

## 3. BDL vs hoopR — comparison and division of labor

| Dimension | hoopR/sportsdataverse (PRIMARY) | BDL free tier (CROSS-CHECK) |
|---|---|---|
| Data license | CC BY 4.0 verbatim | Broad ToS §6 grant |
| Auth | none | Keychain key (owner-loaded) |
| Coverage (games/results) | 2016–2026 downloaded | 1946–current (docs claim) |
| Tip timestamps | local-offset ✓ | ISO-UTC ✓ (verified match) |
| Rate limits | none | **5 req/min** |
| Season/date filter | N/A (static files) | `dates[]=` ✓ / `seasons[]=` ✓ |
| Cross-check status | — | **5/5 MATCH** (T2c §7 below) |
| PBP/box | sample 2026 pulled | **not on free tier** |

**Decision**: hoopR PRIMARY; BDL CROSS-CHECK only (targeted `dates[]` queries,
no bulk download).

## 4. Adapter + owner load instructions

`bdl_adapter.py`: reads key from env `BALLDONTLIE_API_KEY` → Keychain
(`balldontlie`/`winprob-ng`); fails closed when absent; key never in errors/
logs/repr; CLI `check` prints PRESENT/ABSENT only. Tests 5/5 PASS.

```bash
# Keychain (recommended):
security add-generic-password -a winprob-ng -s balldontlie -w
# Check: python lanes/T2_BDL_ADAPTER/bdl_adapter.py → PRESENT
```

## 5. [HISTORICAL — RETRACTED] T2b execution results

> **RETRACTED**: The conclusions in this section were based on a parameter
> syntax error (`seasons=YYYY` scalar instead of `seasons[]=YYYY` array).
> They are kept as historical record only. The correct findings are in §7.

~~Base URL placeholder `.vn`~~ → corrected to `.io`. Auth PASS (HTTP 200,
teams=89). ~~Free-tier `/games` does not support seasons filter~~ → **WRONG**;
the `seasons[]` array syntax works (verified in T2c §7). ~~NOT_RUN_PAGINATION_
IMPRACTICAL~~ → **RETRACTED**; `dates[]` enables targeted per-game lookup.
~~BDL demoted / tier upgrade needed~~ → **RETRACTED**; BDL is a viable
cross-check source on the free tier.

## 6. [HISTORICAL — SUPERSEDED] T2b correction (partial)

Owner identified the syntax error. Request 10/10 confirmed `seasons[]=2024`
returns HTTP 200. Conclusions retracted. Script `bdl_t2b_crosscheck.py` is
now **OBSOLETE** — use `bdl_t2c_crosscheck.py` instead.

## 7. T2c CROSS-CHECK RESULTS (2026-10-05, 5/6 requests, $0) — **CURRENT**

**5/5 MATCH** — all five checks (date, home_team, away_team, score, tip_utc)
PASS on all 5 targets across seasons 2016/2018/2020/2022/2024:

| Date | Home | Away | Score | Tip UTC |
|---|---|---|---|---|
| 2016-01-23 | DEN | DET | 104-101 | 02:30Z ✓ |
| 2018-01-17 | OKC | LAL | 114-90 | 01:00Z ✓ |
| 2020-01-11 | BOS | NO | 140-105 | 00:00Z ✓ |
| 2022-01-17 | LAL | UTAH | 101-95 | 03:30Z ✓ |
| 2024-01-25 | MIA | BOS | 110-143 | 00:30Z ✓ |

Script: `bdl_t2c_crosscheck.py`; results: `BDL_T2C_CROSSCHECK.json`.
