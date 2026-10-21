# HANDOVER ROUND-17 — PaperDesk completion pass (IMPLEMENT + REPAIR + VERIFY)

Owner instruction 2026-10-21 (VN): complete PaperDesk — PM executable-quote
production chain (NBA/WNBA 2-way, soccer/WSL 3-YES), per-candidate AI
research gate (KEEP/VETO/SWITCH/ABSTAIN), app/ops lifecycle, E2E sandbox
verification, independent A7 at the FINAL head. **NOT a typed GO** — no real
orders, no cutover activation, no AI authority activation.

## Final state (measured 2026-10-21)

- Lane: `.worktrees/sports-papertrade-exec-v1/integration` @ branch
  `orca/spt-exec-v1-integration`, HEAD **c4422f8de18b945c8f9073e7bae09e90168bffb0**
  = CYCLE_REGISTRY head (CAS-updated 2026-10-21T01:48:37Z).
- Round-17 commits: cef8412c (wiring + re-seal + containment) → a43130e1
  (STALE_CORPUS) → ef45e249 (PM join law vs real Gamma) → c4422f8d (A7
  remediation F-1 HIGH + 3 LOW). No push, no merge.
- GO states UNTOUCHED: cutover phrase `GO SPORTS PAPERTRADE EXEC V1
  POLYMARKET CUTOVER` = REGISTERED_NOT_CONSUMED; AI authority = NOT
  REGISTERED; `config.feature_gates` = both OFF (verified by A7 check 1).

## Per-league handover table (DoD-18)

| League | Label | Evidence |
|---|---|---|
| NBA | **WIRED_SANDBOX_PASS + LIVE_CASE_VERIFIED (2-way join+walk)** | Sandbox: PM seam chain forecast→quote→crosswalk→gates→AI→ledger (test_pm_cutover_ai_* 3 tests; E2E battery). Live read-only probe 2026-10-21 through the NEW wiring: PM event 1191461 "Hawks vs. Magic" joined by BOTH pinned names (AWAY-first short-form title), token map by NAME {Hawks:AWAY, Magic:HOME}, per-token CLOB walks at real 1000c stake (HOME vwap 0.5922 / AWAY 0.4423, fee 12c/leg), outcomePrices indicative-only — `PM_LIVE_PROBE_ROUND17_2026-10-21.json`. Production forecast live: 11 B1* rows (ledger FORECAST), decision trace below. |
| WNBA | **WIRED_SANDBOX_PASS (engine + shared PM 2-way law)** | Engine entry restored (`wnba-2026-remainder-v1` worktree at registry head f1c0e1b; predict.py pin 5fc6459c verified); battery: WNBA forecast→quote→decide→settle green; same 2-way PM code path as NBA (live-verified there). No live WNBA market case this round — season window; any future fixture flows through the identical gated chain; 2027+ gated NOT_RUN_FORECAST_GATE_2027 by plan law. |
| SOCCER (men's intl) | **WIRED_SANDBOX_PASS; live market = NOT_RUN_PM_MARKET_NOT_YET_LISTED (honest)** | Crosswalk chain RE-SEALED: prep seed grew 8→12 pairs upstream (cc7a3546) — extension re-anchored + 8 evidenced pairs (20 rows, 57354475); `soccer_extension_crosswalk` verifies (England→England … Türkiye→Turkey). 3-YES joiner (one event, exactly 3 YES/NO legs by name, partial-join reason surfaced) sandbox-tested. Live probe England–Croatia (UNL 2026-11-12): PM has NOT listed the match markets yet → joiner fails closed → production path would journal NOT_RUN_PM_QUOTE (owner DoD-9). 90-min stage law + B1R fail-closed law unchanged (battery green). |
| WSL | **LIVE_CASE_VERIFIED (pre-existing lane) + STALE_CORPUS health added** | Lane live since capital-V3 GO: 6/6 settled (+11280c); UMA clean-resolution settlement law unchanged (A7 check 9 PASS); D-1 provenance launchd `com.myquant.wslprov.d1` loaded, provenance index fresh; NEW `classify_open_bets` → AWAITING_KICKOFF / PENDING_UMA / STALE_CORPUS / IDENTITY_UNRESOLVED surfaced via incidents + `state/wsl_settle_health.json` — never inferred from UMA W/D/L. |

## Decision trace (fixture → ledger), production rows, real data

Match 401909088 Detroit Pistons vs Boston Celtics (2026-10-20):
1. FORECAST 12:01:51Z pre-anchor — B1* p {HOME 0.6401, AWAY 0.3599}, model
   sha nba26_predict@57f0c810f8cd.
2. MARKET_QUOTE 12:02:06Z — pinnacle h2h {HOME 2.04, AWAY 1.88}, payload sha
   ec54c7cc… (pre-cutover pinned source; the PM source replaces this only
   after the owner GO).
3. DECISION 12:02:12Z — BET_PAPER HOME, EV_net 0.285733 ≥ 0.05,
   stake 1135c = 1% of equity 113495c (v3-1pct), in-lock recheck + append.
Ledger: **82 rows, chain_ok=True** (GENESIS 1 / FORECAST 27 / QUOTE 17 /
DECISION 27 / SETTLEMENT 10); equity 113495c; open 13 bets (3 NBA + 4 WNBA +
6 WSL), open exposure 3405c ≤ 50000c cap; drawdown 1.49% < 10% pause.
Battery runs: live ledger 82 rows + sha unchanged before/after both runs
(non-interference).

## Tests (DoD-15/16) — two full passes, byte-repro

- pytest `tests/papertrade_exec/`: **147 passed / 0 failed**, two consecutive
  runs (run1 76.8s, run2 33.3s), exit 0 both. All 11 pre-existing failures
  resolved with named causes: 3× BLOCKED_PIN_DRIFT (crosswalk re-seal),
  3× engine-entry-absent (worktrees restored), capital-v3 stale stake assert,
  config 5-keys stale expect, PIT-law time-decay assert, 2× WSL seam
  containment (harness injection). No "baseline" hand-waving anywhere.
- Node batteries: ai-gate 17/17, ai-seam 43/43, lifecycle-safety 13/13,
  paper-policy 27/27 (exit 0).
- Adversarial coverage in-suite: swapped/ambiguous outcomes, unrelated names,
  3-YES incomplete/missing DRAW/wrong-fixture/closed/non-90min/empty-book/
  stale-after-anchor/depth-short, missing GO, tamper, duplicates, restart
  idempotence, AI ABSTAIN/VETO/KEEP/SWITCH + price/EV frozen, PM join
  failures ⇒ NOT_RUN_PM_QUOTE, no Odds API fallback in PM branch.

## Independent A7 (DoD-17) — final HEAD

- `A7_ROUND17/A7_VERDICT.json` (at ef45e249): FAIL → **F-1 HIGH**: the
  crosswalk re-seal had recorded a seed digest whose 52-char tail was NOT a
  measurement (my error; caught by A7, exactly what the discipline is for).
- Remediation c4422f8d: re-measured `shasum -a 256`, re-pinned the true
  digest, erratum recorded in the pin note; F-2 fee_total, F-3 env-seam
  real-mode raise, F-4a partial-join reason also fixed.
- `A7_ROUND17/A7_REAUDIT_VERDICT.json` (at c4422f8d): **PASS_WITH_FINDINGS**
  — 0 CRITICAL/HIGH/MED remaining; pin-honesty sweep independently recomputed
  ALL 20 direct-sha pins: 20/20 match (F-1's error class eliminated).
  Residual (non-blocking, recorded for next round): R-N1 LOW — no dedicated
  battery test for the AI-opinion env seam real-mode raise (code law measured
  PASS by A7); R-N2/R-N3 INFO — docstring drift, advisory head strings.

## Wiring (DoD-5..14) — summary of what changed this round

- `cmd_run_day` catches LaneBlock per-league (WSL) with the same hard-break
  law — a lane refusal never crashes the desk, a tamper/no-go/pin refusal
  never lands in a green report.
- PM cutover path: join by BOTH pinned team names (query variants against
  PM's real short-form AWAY-first titles; strict market-outcome identity
  unchanged); fixture id NEVER used as PM event id (crosswalk journaled:
  fixture↔event↔market↔tokens); 3-YES soccer joiner (one event, exactly
  HOME/DRAW/AWAY); REAL 1%-equity stake walk (old hardcoded 10000c probe
  removed); quote rows APPENDED to the ledger in both branches; executable
  odds = 1/VWAP (best_ask display-only — the old `odds=best_ask` would have
  broken EV math); AWAY never 1−HOME; NO Odds API fallback in the PM branch;
  sandbox-only seams (pm_probe / AI opinion) refused in real mode.
- AI boundary: single execution surface in `cmd_decide` AFTER
  `risk.evaluate_match`, BEFORE `append_decision`; flag OFF ⇒ DISABLED +
  byte-identical legacy behavior; ABSTAIN/missing/non-COMPLETED/post-deadline
  ⇒ NOT_PLACED_AI_GATE (terminal, evidence kept); KEEP/SWITCH regraded
  against frozen gates (SWITCH needs quote+depth on target); the AI supplies
  only action+proposed_leg — probabilities/prices/EV/stake/cap/drawdown come
  exclusively from the ledger snapshot; opinions read from
  `ai_review/opinions/` (provider openrouter, fail-closed mapping).
- App: untouched lifecycle (opslock single-runner, quit preserves ledger —
  A7 check 7 PASS); app batteries green; dashboard already renders
  equity/exposure/settlements/AI/incidents; STALE_CORPUS now journaled +
  persisted for both dashboards.

## Blockers / NOT_RUN (honest)

- WNBA live market case: no in-window fixture at audit time — the chain is
  sandbox-verified and the 2-way law is live-verified on NBA.
- SOCCER live PM case: match markets for the 2026-11-12 UNL window are not
  listed yet — NOT_RUN_PM_MARKET_NOT_YET_LISTED with the fail-closed probe
  evidence; re-probe at listing time (T-6h10m cadence will do it naturally).
- WSL AI boundary: the WSL lane's decider is its own module (wsl_lane);
  the AI boundary wired this round covers the NBA/WNBA/SOCCER decide path.
  A7 scope note recorded; wiring WSL decide into the same gate is a
  follow-up BEFORE any AI-authority GO (flag is OFF, so no live impact).

## What the Owner's GOs would do (unchanged, not typed)

- `GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER` → flips
  `pm_cutover_active`: production quotes switch to PM book-walks as the
  single decision source (fail-closed NOT_RUN when markets absent).
- AI authority GO (separate, not registered) → flips `ai_authority_active`.
- Nothing in this round consumed, typed, or rehearsed any GO in real mode.
