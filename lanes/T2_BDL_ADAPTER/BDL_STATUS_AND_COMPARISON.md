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
