# RUNBOOK — PM WATCHER (read-only Polymarket watch, exec cycle)

Owner authority: instruction 2026-10-10 Part B ("Theo dõi market Polymarket
bằng API gốc CHỈ ĐỌC…"). This watcher OBSERVES; it never switches the
production price source, never adds paper rows, never falls back, and never
consumes `GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER` or any other
phrase.

## What runs

    cd /Users/hoangminhlong/my-quantitative/.worktrees/sports-papertrade-exec-v1/integration
    /Users/hoangminhlong/my-quantitative/.venv/bin/python \
        research/control/SPORTS-PAPERTRADE-EXEC-V1/pm_watcher/pm_watcher.py
    # optional: --scopes NBA,SOCCER   (subset; default all seven scopes)

Cadence: DAILY automation fires at 09:15 local (Asia/Ho_Chi_Minh; 02:15Z) —
no collision with HCAL1 (13:00Z), Q1 (13:30Z), NFL (00:00 local), or the
exec service's own 30s local tick (the watcher shares nothing with the
service process). One run ≈ 100 s, 22 Gamma pages + ~45 ESPN GETs + CLOB
books only for joined events.

## Laws carried (inherited, never re-derived)

- Join/quote/fee/NO(Home) laws: `polymarket_source.py` of
  SPORTS-POLYMARKET-CUTOVER-PREP-V1 (see AMENDMENT_SOURCE_SWITCH_POLYMARKET
  §1–§5), imported READ-ONLY and sha-pinned
  (`PM_SOURCE_SHA256.txt` beside the watcher; drift refuses).
- Raw evidence: every Gamma/CLOB/ESPN GET journaled + append-only snapshot
  (url, retrieval UTC, bytes, sha256, event/market/token ids) in the
  cutover prep data plane (`~/.my-quantitative-data/
  sports-polymarket-cutover-prep-v1/live/` + `journal/`) — the single PM
  snapshot home (V10-probe precedent).
- Derived artifacts (this cycle's data plane):
  `~/.my-quantitative-data/sports-papertrade-exec-v1/pm_watcher/`
  — `state/watcher_state.json` (per-scope signature), `alerts.jsonl`
  (append-only; only on meaningful change), `reports/report_<ts>.json`
  (full per-fixture rows).
- Model p: read-only from the REAL ledger's chain-verified FORECAST rows
  via the pinned core (`forecast_index`: B1R preferred for soccer). No
  probabilities are computed here.
- Non-interference: the ledger/dashboard are read-only; the watcher holds
  no locks and is never imported by the service.

## Per-scope reading of a report

`n_fixtures` (future, teams known, kickoff parses), `n_candidate_events`
(distinct Gamma events joined), `n_joined_1to1` (fixtures with exactly one
joining event), `n_full_leg_quotes` (all legs filled at the $5 walk with
best ASK + vwap + depth + fee + book sha + retrieval UTC). Statuses are the
AMENDMENT §5 taxonomy (NOT_RUN_NO_MARKET, NOT_RUN_MARKET_MISMATCH,
NOT_RUN_RULES_MISMATCH, NOT_RUN_KICKOFF_MISMATCH, NO_QUOTE_DEPTH,
NOT_RUN_NO_RECORDED_FORECAST, NO_QUOTE, QUOTED_EV_COMPUTED). "Có market"
chưa đồng nghĩa "đủ điều kiện paper": EV/risk gates và BET_PAPER vẫn thuộc
shared core + các GO của từng cycle.

## Silence law

A scope whose signature (match_id, status, event_id set) is unchanged emits
no alert (`QUIET_UNCHANGED`); the state-file update is the record. On
`MARKET_STATE_CHANGED` the run writes `alerts.jsonl` and the automation
reports it (with new joined event ids) so a live-quote A7 can be prepared.
`BASELINE_RECORDED` is the first run's record.

## Boundaries

$0, public read-only GETs, no auth/keys/accounts/orders/router/wallet
endpoints, no Synpath (native Gamma/CLOB only), no purchases, no S1,
no push/merge, registry writes never happen here, the exec service and its
ledger are untouched, WC/Euro groups stay PREP-observation only (their
paper intake remains behind the WC/EURO cycle's own GO).
