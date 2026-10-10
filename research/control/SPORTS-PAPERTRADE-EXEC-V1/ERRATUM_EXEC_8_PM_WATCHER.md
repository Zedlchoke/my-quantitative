# ERRATUM_EXEC_8 — READ-ONLY POLYMARKET WATCHER (owner round-11, 2026-10-10, Part B)

Adds market WATCHING for the Polymarket cutover prep. **No production
change**: the price source stays The Odds API / Pinnacle; no paper rows;
no fallback; no config change; `GO SPORTS PAPERTRADE EXEC V1 POLYMARKET
CUTOVER` remains REGISTERED_NOT_CONSUMED and is NOT typed here. Synpath is
not used anywhere (native Gamma + CLOB public GETs only).

## What landed (this dir + data planes)

- `pm_watcher/pm_watcher.py` — the watcher (exec-owned; NEVER imported by
  the service). `pm_watcher/RUNBOOK_PM_WATCHER.md` — operation + laws.
- PM module reuse is BYTE-PINNED: `pm_watcher/PM_SOURCE_SHA256.txt` pins
  the cutover prep cycle's `polymarket_source.py` (frozen join/book/fee
  laws); drift refuses before any network.
- Raw evidence: journaled GETs + append-only snapshots (url, retrieval
  UTC, bytes, sha256) continue in the cutover prep data plane (single PM
  snapshot home; V10-probe precedent). Derived state/alerts/reports live in
  `~/.my-quantitative-data/sports-papertrade-exec-v1/pm_watcher/`.
- Cadence: daily automation 09:15 Asia/Ho_Chi_Minh (02:15Z) — no collision
  with any existing automation (HCAL1 13:00Z, Q1 13:30Z, NFL 00:00 local).
  Silence law: unchanged signatures emit no alert; meaningful changes write
  `alerts.jsonl` and are reported for a live-quote A7.

## First scans (measured 2026-10-10)

Run 1 04:56:41Z (baseline) + run 2 05:01:25Z (silence-law check) — Gamma
2,100 open events / 22 pages both runs:

| scope | fixtures | candidate markets | joined 1:1 | full-leg quotes | NOT_RUN reason |
|---|---|---|---|---|---|
| NBA | 1214 | 0 | 0 | 0 | NOT_RUN_NO_MARKET ×1214 |
| WNBA | 11 | 0 | 0 | 0 | NOT_RUN_NO_MARKET ×11 |
| SOCCER (UNL) | 2 | 0 | 0 | 0 | NOT_RUN_NO_MARKET ×2 |
| WSL | 147 | 0 | 0 | 0 | NOT_RUN_NO_MARKET ×147 |
| WC_GROUP | 0 | — | — | — | no future fixtures (ESPN matrix 2027–2031, 0 HTTP failures) |
| EURO_GROUP | 0 | — | — | — | same |
| WCQ | 0 | — | — | — | same (6 confederations × 5 years) |
| EUROQ | 0 | — | — | — | same |

READY_LEAGUES_NONE stands — identical verdict to the cutover prep R2 probes
and the exec V10 re-probe (0/246); the fixture census now additionally
covers the full refreshed NBA payload corpus (1,214 future games) and the
four WC/Euro groups re-measured live each run. NOT_RUN_NO_MARKET status is
preserved everywhere; a future listing flips the signature and fires one
alert. Run 1 had exactly 1 ESPN transport error (journaled
`LIVE_HTTP_ERROR`, 89/90 snapshots); run 2 was clean.

## Non-interference (asserted)

Real ledger sha `13f65120550eba64d59e053897bfcb1161e9d3e0ce869c4716be2035
977d2ae1` (20 rows) unchanged across both watcher runs; dashboard untouched;
`config.json` untouched; the service (restarted healthy at 04:51Z under
ERRATUM_EXEC_7's B1R law) runs its own cadence throughout.

## Gates (Part B.4)

Nothing is consumed. The watcher is observation-only: when real candidate
markets appear, the alert carries event/market/token IDs + rules + ASK +
depth + fee evidence so a live-quote A7 can be prepared — activation still
requires the owner to type the cutover phrase (and, for WSL BET_PAPER, the
WSL cycle's split phrase). WC/Euro groups remain PREP observation: any
candidate they ever show is reported, never intake.
