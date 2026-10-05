# T2 — BALLDONTLIE status update, adapter, and hoopR comparison (2026-10-05)

## 1. Status change (per owner directive 2026-10-05)

`BLOCKED_NO_KEY` → **`KEY_AVAILABLE_TO_OWNER_BUT_NOT_IN_RUNTIME`**.

The owner supplied an API key in the Codex chat on 2026-10-05. Per the owner's own
directive the key is a SECRET and must not be copied into prompts, source, commands,
logs, manifests, handoffs, or git. It is therefore NOT loaded into ZCode's runtime by
this lane. The owner must load it personally via env or Keychain (see §4).

SECURITY INCIDENT (handbook §29 class): the key transited a chat channel (Codex→owner→
this thread), which is an exposure surface. Recommendation recorded for the owner:
**rotate the key** in the balldontlie dashboard after loading the replacement via the
safe channel. ToS §5 (verified verbatim below) reinforces this: the owner is
"responsible for maintaining the confidentiality of your account credentials" and keys
"may not be shared, sold, transferred, or distributed to third parties".

## 2. Current docs/ToS re-verification (fetched 2026-10-05)

- Docs (docs.balldontlie.io): free tier = **Teams/Players/Games only**; box scores,
  player stats, injuries, lineups, odds, plays = paid. Rate limits: Free **5 req/min**,
  ALL-STAR 60 ($9.99/mo), GOAT 600 ($39.99/mo). Coverage: "The API contains data from
  1946-current"; advanced stats from 2015; quarter scores from 2023; odds/PBP/lineups
  from 2025. Games objects carry `date` (YYYY-MM-DD) AND `datetime` (ISO-8601 **UTC**)
  — tip-grain cross-checkable. Auth: plain `Authorization: <key>` header (not Bearer).
- ToS (Last Updated 2026-09-17): §6 grant — "use, copy, cache, store, archive, modify,
  combine, analyze," … publish/distribute/sublicense + derivative works; permitted
  purposes include analytics + AI/ML training; "No attribution … or additional
  permission … is required unless a separate written agreement" says otherwise.
  Restrictions: no competing products, no reselling raw data, no key sharing, no
  rate-limit circumvention, no implying league affiliation. §5 credential
  confidentiality quoted above.

## 3. BDL vs hoopR — comparison and division of labor ($0, no duplicate bulk loads)

| Dimension | hoopR/sportsdataverse releases (lane A) | balldontlie free tier |
|---|---|---|
| Data license | **CC BY 4.0 verbatim** on producer repos | Broad contractual grant (ToS §6); attribution not required |
| Auth | none (public release assets) | key required (owner-only runtime load) |
| Coverage (games/results) | schedules 2016–2026 downloaded; full release spans NBA history per README | 1946–current claimed; measured on first authorized pull |
| Tip timestamps | local-offset `game_date_time` (verified) | ISO-8601 UTC `datetime` (docs-verified) |
| Box/PBP | PBP sample 2026 pulled; full PBP available | **not on free tier** |
| Rate limits | none (static files) | **5 req/min** |
| Provenance | ESPN NBA API (declared) | not affiliated with NBA (ToS §1); underlying feeds not declared |

**Decision (this lane):** hoopR remains PRIMARY for NBA 2016+ (rights clearer, richer,
no rate limits, already downloaded). BDL = **CROSS-CHECK / secondary** only: (a)
independent results mirror for sample games across seasons (score/date/home-away
identity), (b) alternate tip-timestamp source for kickoff-grain law verification.
No bulk mirror of BDL games (owner: avoid duplicate downloads); targeted spot-check
queries only, budget ≤50 requests per verification session (10 min at 5/min).

## 4. Adapter (fail-closed) + owner load instructions

`bdl_adapter.py` in this lane: key resolution env `BALLDONTLIE_API_KEY` → macOS
Keychain (`security find-generic-password -s balldontlie -a winprob-ng -w`); every
call raises `BDLKeyUnavailable` BEFORE any network request when absent; key never in
errors/logs/repr; CLI `check` prints PRESENT/ABSENT + source only. Tests
(test_bdl_adapter.py) cover fail-closed, env source, keychain source, error-leak
guard, no-real-fragment-in-source. 5/5 PASS.

**Owner load instructions (do NOT paste the key in any chat again):**
```bash
# Option A — Keychain (recommended; prompts securely, never in shell history):
security add-generic-password -a winprob-ng -s balldontlie -w
# (paste when prompted; then optionally delete the chat-exposed key and issue a new one)

# Option B — env var in the owner's own shell profile:
export BALLDONTLIE_API_KEY='<paste locally, not in chat>'
```
Then: `python lanes/T2_BDL_ADAPTER/bdl_adapter.py` → expect `BDL key: PRESENT (source: …)`.

**Block point:** until the owner loads the key AND (recommended) rotates the exposed
one, all BDL network verification is NOT_RUN_KEY_NOT_LOADED (fail closed by design).
Everything else in the program proceeds without BDL.

## T2b execution results (2026-10-05, 9/10 requests used, $0)

- **Base URL verified from docs**: `https://api.balldontlie.io/v1` (docs verbatim
  "GET https://api.balldontlie.io/v1/games"); adapter placeholder `.vn` corrected.
- **Auth: PASS** (Keychain key, HTTP 200 on /teams, 89 entries returned).
- **Free-tier /games endpoint: HTTP 400 on every `seasons=YYYY` attempt** (6 tries
  across 1946/2016/2017/2020/2023/2025/2026). Without the param (cursor-only) it
  returns 25 rows from 1946-11-01 — so the endpoint works but **does not support
  the seasons filter on free tier** (or requires a format the docs don't disclose
  for free tier). This makes targeted cross-check by season/date **impractical**
  within the ≤10-request budget: cursor pagination through ~75k games at 25/page
  ≈ 3,000 requests.
- **Cross-check verdict: NOT_RUN_PAGINATION_IMPRACTICAL** — hoopR stays the sole
  PRIMARY for NBA 2016+ (already CC BY 4.0 verified + downloaded); BDL free tier
  is demoted from "cross-check" to "not usable for targeted game verification
  under $0 constraints". Paid tiers (ALL-STAR $9.99+) would unlock it but are
  outside the $0 budget.
- **Cost: $0.** No bulk download. Key never in any artifact (sweep re-verified).

## T2b CORRECTION (owner-identified, 2026-10-05)

**Prior conclusion RETRACTED**: "free-tier /games does not support seasons filter"
was WRONG. The HTTP 400 responses were caused by **incorrect parameter syntax**
on my part: I sent `seasons=2024` (scalar) when the BDL API requires **array-style
`seasons[]=2024`** (per docs.balldontlie.io Get All Games section). The owner
identified this error.

**Corrected finding (verified with request 10/10, the last of this session)**:
`GET /games?seasons[]=2024` → HTTP 200, 25 rows per page, first game 2024-10-22
(2024-25 season tip-off). **Free tier DOES support season filtering.** The
NOT_RUN_PAGINATION_IMPRACTICAL verdict and the "~3,000 cursor pages" claim are
both retracted — the actual page count for a full season is ~50 pages at 25/page,
well within a reasonable rate-limited session.

**Current status**: BDL is restored as a **viable cross-check source** alongside
hoopR. The adapter has been fixed to emit array-style params. The targeted
cross-check (matching specific hoopR games to BDL by season+date) remains
**NOT_RUN_QUOTA_EXHAUSTED** — this session's 10-request budget is consumed.
Next session can execute it with ~6 requests (one per target season × 1 page).

## T2c CROSS-CHECK RESULTS (2026-10-05, 5/6 requests used, $0) — **5/5 MATCH**

Protocol (co-owner-reviewed): pick 5 finished hoopR games from widely-separated
seasons → query BDL by `dates[]=<local_date>` (array syntax) → match on
date + home team identity + away team identity + score + tip UTC.

| Date | Home | Away | hoopR score | BDL score | tip UTC | Verdict |
|---|---|---|---|---|---|---|
| 2016-01-23 | DEN | DET | 104-101 | 104-101 | 02:30Z ✓ | **MATCH** |
| 2018-01-17 | OKC | LAL | 114-90 | 114-90 | 01:00Z ✓ | **MATCH** |
| 2020-01-11 | BOS | NO | 140-105 | 140-105 | 00:00Z ✓ | **MATCH** |
| 2022-01-17 | LAL | UTAH | 101-95 | 101-95 | 03:30Z ✓ | **MATCH** |
| 2024-01-25 | MIA | BOS | 110-143 | 110-143 | 00:30Z ✓ | **MATCH** |

All five checks (date, home_team, away_team, score, tip_utc) PASS on all 5
targets — no mismatches, no unmatched games, no errors. BDL free-tier with
`dates[]` array syntax is a **fully viable targeted cross-check source**.
Prior T2b conclusions about pagination impracticality are definitively
retracted (they were based on a syntax error, corrected by owner).

Script: `bdl_t2c_crosscheck.py` (this lane); results: `BDL_T2C_CROSSCHECK.json`.
