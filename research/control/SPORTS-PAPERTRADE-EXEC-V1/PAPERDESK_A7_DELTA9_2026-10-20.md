# PAPERDESK A7 — DELTA-9 INDEPENDENT VERIFICATION (round-13+14 delta dispatch, 2026-10-20)

**Verifier:** A7 fresh-context subagent. Read-only except this artifact; nothing repaired, nothing pushed, no ledger/registry writes.

**Scope:** delta commit c20ea9c78f2841ebf5c0d8f58f0818148d26d225 ("PaperDesk round-13") on
branch `orca/spt-exec-v1-integration`, worktree
`/Users/hoangminhlong/my-quantitative/.worktrees/sports-papertrade-exec-v1/integration`.
Delta touches exactly 2 files: `research/papertrade_exec/decision_pipeline.py` (+5/−3) and
`research/papertrade_exec/pm_quote_source.py` (+145 new).

## VERDICT: **VERIFY_PASS** — 0 CRIT / 0 HIGH / 0 MED / 0 LOW / 2 INFO

Every dispatch claim re-measured and reproduced. No regression, no gate bypass, no wiring
of AI or post-cutover quote source into the live cadence, no ledger interference.

---

## 1. Claim table

| # | Claim | Result | Evidence |
|---|-------|--------|----------|
| 1a | KEEP PIT fix: `ok = all(g["pass"] for g in gates)` AFTER all pushes incl. G_PIT_KEEP | **PASS** | `decision_pipeline.py:167-177` — `push("G_EV_KEEP", …)` then `push("G_PIT_KEEP", …)` then `ok = all(g["pass"] for g in gates)` (:173); the pre-fix `ok` assignment from the EV push alone is gone (diff confirmed: old lines `ok = push("G_EV_KEEP", …)` removed) |
| 1b | PIT-failed KEEP returns NOT_PLACED, not PLACE | **PASS** | Functional check via pinned venv: EV=0.20 (passes G_EV_KEEP) + `anchor_passed=True` → decision **NOT_PLACED**, gates `{G_EV_KEEP: True, G_PIT_KEEP: False}`, reason `"AI KEEP — gates fail: G_PIT_KEEP"`. All-pass KEEP → PLACE. Exact bug shape (EV ok, PIT failed) can no longer PLACE |
| 2a | `pm_quote_source.py` exists; `QuoteSourceRouter` has `cutover_active` flag | **PASS** | 145-line module at `research/papertrade_exec/pm_quote_source.py`; `QuoteSourceRouter.__init__(*, cutover_active, data_root, sandbox=False)` (:125-129) |
| 2b | Pre-cutover returns None (caller falls back) | **PASS** | `:135-136` `if not self.cutover_active: return None`; functional check: router with `cutover_active=False` returns None for NBA and for WSL(3 market_ids) |
| 2c | Post-cutover dispatches 2-way (NBA/WNBA) or 3-YES (SOCCER/WSL) | **PASS** | `:137-140` NBA/WNBA → `quote_moneyline_2way` (via `pm_moneyline.probe_event_moneyline` book walk); `:141-144` SOCCER/WSL+`market_ids` → `quote_3yes` (Gamma event markets, YES-side prices, `all_present` only when 3/3, `len(legs)<2 → None`); unknown league → None |
| 2d | NOT wired into production cadence (grep execute.py + ops_service.py = zero hits) | **PASS** | `grep pm_quote_source` on `execute.py` → 0 hits; on `ops_service.py` → 0 hits; repo-wide: only the file itself (+ its own docstring). `execute.py` import block (:44-53) has no `decision_pipeline`, no `pm_quote_source` |
| 3a | pytest wsl_results + ui_control_seam → 19 passed | **PASS** | `19 passed in 33.70s` (11 wsl_results + 8 ui_control_seam) |
| 3b | node test_ai_gate.js → 17/17 | **PASS** | `ai gate: 17/17 pass` |
| 3c | node test_paper_policy.js → 27/27 | **PASS** | `paper policy: 27/27 pass` |
| 3d | node test_ai_seam.js /tmp/a7r13 → 43/43 | **PASS** | `ai seam: 43/43 pass` |
| 3e | node test_lifecycle_safety.js → 13/13 | **PASS** | `lifecycle safety: 13/13 pass` |
| 4a | Registry head == git rev-parse HEAD | **PASS** | ROOT `plans/CYCLE_REGISTRY.json` cycles[SPORTS-PAPERTRADE-EXEC-V1].head = `c20ea9c7…` == `git rev-parse HEAD`; root phase names "PAPERDESK.APP round-13 at c20ea9c7…" |
| 4b | Cutover REGISTERED_NOT_CONSUMED | **PASS** | cycles[SPORTS-POLYMARKET-CUTOVER-PREP-V1].`go_phrase_state` = "REGISTERED_NOT_CONSUMED (pointer, corrected 2026-10-10…)" for "GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER"; root exec-v1 phase: "cutover REGISTERED_NOT_CONSUMED untouched; AI authority NOT_REGISTERED" |
| 4c | GO_TOKEN unchanged | **PASS** | `GO_TOKEN.json` = "GO SPORTS PAPERTRADE EXEC V1 RUN ALL" typed 2026-10-07T11:08:47Z — byte-identical to delta-8 measurement |
| 4d | Pinned verifier True / 68 rows; 59→68 via live cadence, not this repo's work | **PASS** | `execute.load_pinned_core(roots={})` + `PaperLedger(~/.my-quantitative-data/sports-papertrade-exec-v1/ledger/paper_ledger.jsonl).load().verify_chain()` → **(True, [])**, 68 rows. Rows 60-68 = NBA 3×FORECAST (12:01:51Z) + 3×MARKET_QUOTE (12:02:06Z) + 3×DECISION (12:02:12Z), all recorded 2026-10-20 by the live runner; delta commit authored no ledger rows and is not imported by the cadence. Live service agrees: `/api/state` rows_count 68, chain.ok true, mode REAL |
| 4e | 2 open NBA bets | **PASS** | BET_PAPER decisions without SETTLEMENT = exactly 2: `401909088` Detroit–Boston HOME 1135c (kickoff 2026-10-20T19:00Z), `401909090` San Antonio–OKC HOME 1135c (kickoff 2026-10-21T01:30Z); third fixture `401909089` = NO_EDGE |
| 4f | Runner RUNNING | **PASS** | PaperDesk pid 9990 (+GPU/renderer/network helpers) from this worktree's build; `ops_service` pid 10000 `python -m research.papertrade_exec.ops_service --data-root …` LISTEN 127.0.0.1:8791; service tick_count 169, last tick 2026-10-20T13:28:29Z, drawdown_frac 0.0149 not paused, equity 113495c, open exposure 2270c ≤ cap 50000c |
| 5a | openrouter: zero hits in research/papertrade_exec/*.py | **PASS** | grep → 0 hits |
| 5b | ai_gate.js referenced ONLY from apps/paperdesk/ | **PASS** | `ai_gate.js` exists only at `apps/paperdesk/main/ai_gate.js` (+ Electron build bundle copy of same); sole requirer = `apps/paperdesk/test_ai_gate.js`. Zero references from `research/` |

## 2. Measured state summary

```
git rev-parse HEAD                        → c20ea9c78f2841ebf5c0d8f58f0818148d26d225 (branch orca/spt-exec-v1-integration)
git status --porcelain                    → clean (delta-8 F-3 untracked pm_stake_law.js now committed as 58ecec28)
pytest (2-file battery)                   → 19 passed
node ai_gate / policy / ai_seam / safety  → 17/17, 27/27, 43/43, 13/13
pinned core verify_chain(main)            → (True, []) 68 rows (1 GENESIS + 27 FORECAST + 14 MARKET_QUOTE + 16 DECISION + 10 SETTLEMENT)
open bets                                 → 2 NBA (401909088, 401909090), both HOME 1135c
live service 8791                         → chain.ok true; rows_count 68 (agrees with disk); mode REAL
root registry exec-v1 head                → c20ea9c7… == HEAD; phase "GO_CONSUMED CAPTURE_ACTIVE LIVE_SERVICE_ACTIVE | round-13…"
worktree registry mirror head             → 9a18a4f2 (lags root — see F-1)
GO_TOKEN.json                             → unchanged since 2026-10-07T11:08:47Z
```

## 3. Findings

- **F-1 (INFO, mirror lag — precedent)** — The **worktree copy** of
  `plans/CYCLE_REGISTRY.json` carries head `9a18a4f2` (the round-12-era "registry
  mirror: refresh from root" commit), not HEAD. The **root** registry — the authority
  per the mirror convention ("lane mirrors legitimately lag root events journal
  (precedent)", message of 9a18a4f2 itself) — equals HEAD exactly and its phase text
  already registers round-13 at `c20ea9c7` with the delta's own battery numbers. The
  dispatch claim holds against the root registry; no action needed beyond the standing
  convention that the next mirror commit syncs the lane copy.
- **F-2 (INFO, wiring prerequisites for the post-cutover round — not a current defect)** —
  Two approximations inside `pm_quote_source.py` must be closed before any cutover wiring:
  (a) the 2-way adapter's AWAY leg is `1 − HOME ask` labelled in-code "approx from HOME
  ask (2-outcome complement)" — display-only; the executable AWAY walk needs `tokens[1]`;
  and both legs are emitted with hardcoded `depth_ok: True` with no stake-sized walk on
  the AWAY side, while `quote_3yes` prices are top-of-book `outcomePrices` (no VWAP walk;
  its `stake_cents` parameter is accepted but unused). None of this is reachable today —
  the router returns None pre-cutover and nothing imports the module — but the G_DEPTH
  gate's "walk covers stake" semantics require real walks on every executable leg at
  cutover time.

## 4. Verdict rationale

All 17 dispatch claims were re-measured; all 17 reproduce exactly. The KEEP PIT fix is
correct in both code shape and behaviour (functionally probed: the exact pre-fix bug
shape — EV passing, PIT failing — now returns NOT_PLACED with the failing gate named in
the reason). The PM quote router is a self-contained, feature-gated reference
implementation with zero production-cadence references. AI remains fully in shadow:
no openrouter anywhere in the runner tree, ai_gate.js confined to apps/paperdesk,
decision_pipeline imported by nothing in the cadence, AI authority NOT_REGISTERED at
root. The live ledger verified True through the pinned core at 68 rows with the 59→68
growth being live-cadence NBA rows recorded by the runner process, untouched by this
delta. GO_TOKEN unchanged, cutover gate REGISTERED_NOT_CONSUMED, runner healthy with
2 open NBA bets and drawdown 1.49% (unpaused). No CRIT, no HIGH, no MED, no LOW.
**VERIFY_PASS.**
