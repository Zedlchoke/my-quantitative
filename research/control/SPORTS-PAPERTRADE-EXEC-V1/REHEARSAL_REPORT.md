# REHEARSAL_REPORT — SPORTS-PAPERTRADE-EXEC-V1 (Lane EXEC-RUNNER, pre-GO)

Built and verified **before** the GO. THE ONE GO
(`GO SPORTS PAPERTRADE EXEC V1 RUN ALL`) remains **REGISTERED_NOT_CONSUMED** —
typed by the owner alone. Zero real paper rows exist; zero real probabilities
and zero market odds are stored anywhere; every sandbox probability/odds byte
is labeled SYNTHETIC in its row. Raw evidence:
`research/control/SPORTS-PAPERTRADE-EXEC-V1/rehearsal/`
(`rehearsal_runs.json` = every command + exit code + output;
`rehearsal_row_census.json`; `rehearsal_results_sandbox.json`).

- Worktree: `.worktrees/sports-papertrade-exec-v1/integration`,
  branch `orca/spt-exec-v1-integration`, base `8e5c8f81aeecab13539d1d771d49c739100d5306`.
- Runner: `research/papertrade_exec/execute.py` (+ `adapters.py`, `pins.json`,
  `config.json`, `PINS.md`).
- Battery: `tests/papertrade_exec/test_exec_battery.py` — **36/36 PASS**
  after EXEC-NBA-REWIRE (28 pre-rewire + 8 NBA additions;
  `/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest
  tests/papertrade_exec/test_exec_battery.py`, exit 0, ~8 s, offline,
  deterministic, tmp-path sandboxes only). Sibling suites re-run read-only
  2026-10-07 (worktree trees clean after the runs): WNBA 79/79, SOCCER 94/94,
  NBA-prep 81/81.

## 1. Per-league wiring status (honest)

| league | fixtures source | engine | status |
|---|---|---|---|
| **WNBA** | PINNED snapshot `wnba_schedule_2026.csv` (sha 0ed97faf…): 15 remaining 2026 playoff games, census + anchors reproduced from FREEZE_PACKET §5 (401918297→17:20:00Z, 401918298→19:20:00Z exact) | Lane B `wnba26_predict` (landed mid-build 2026-10-07; contract-compatible with the dispatch's `predict_matches(completed_rows, upcoming)` — both names accepted; B1-WNBA K=32/HCA=50/γ=0.65 replay, byte-pinned sha 5fc6459c…) | **WIRED_ENGINE_READY** — contract test replays 344 completed 2026 rows and predicts 401918299 in-memory (p_home∈(0,1), deterministic, 64-hex state_digest); NOTHING stored |
| **NBA** | PINNED payloads `espn_schedule_2026_27/` (composite 3d527b3c…, re-derived every verify; since EXEC-NBA-REWIRE verification also accepts the post-GO self-hashed `REFRESH_MANIFEST.jsonl` chain anchored at the frozen pin): opening-window 8 real fixtures 2026-10-20/21 (UTC tip dates), batch anchor T0−6h10m = 2026-10-20T12:50:00Z | **EXEC-NBA-REWIRE**: Lane D prospective PIT path `nba26_predict(upcoming, completed, anchor)` lazy-imported from the byte-pinned `nba26` package (`loader.py` 2679be80… + `predict.py` 57f0c810…, content commit 65ebefc4 / head 82542aa8) — frozen B1_STAR law (K=32/HCA=100/γ=0.75 quoted; warm-up R0=1500 carried pre-registration), frozen ESPN payloads ONLY, **never** the scored bind corpus (that path is DEAD — `ERRATUM_NBA_REWIRE.md`) | **WIRED_ENGINE_READY** — real engine path proven in-memory on the frozen snapshot: window 8/8 rows, completed=0 ⇒ every rating at R0=1500, p_home = 1/(1+10^(−100/400)) = 0.640065 for all, state_digest `f2d59f35…`, deterministic; NOTHING stored (see §7) |
| **SOCCER** | Post-GO: The Odds API events endpoint (0-credit) via the paper core `OddsClient`, sport key `soccer_uefa_nations_league` pinned in `config.json` (quota caps 4/day + 120/month enforced by the core client). Pre-GO rehearsal: labeled SYNTHETIC events | Lane C `soccer_b1_replay(fixtures, corpus_csv, asof_date)` (landed mid-build; pinned sha 22553f6b…; B1 Elo/Davidson K=48/ν=0.6/HCA=65, fail-closed provider crosswalk) | **WIRED_ENGINE_READY** — contract test replays the pinned corpus in-memory through the 8-pair seed crosswalk (USA/Czechia probe; three-way p sums to 1, deterministic); NOTHING stored |

Rehearsal LEDGER rows are SYNTHETIC for all three leagues by law
(zero real probabilities pre-GO): the `forecast` command always probes and
reports the engine status (`wiring` field) but writes only
`mode=SYNTHETIC, model_version_sha=SYNTHETIC_ADAPTER_NOT_ENGINE` rows in
sandbox mode. Post-GO first real run: WNBA/SOCCER/NBA all switch to
`mode=ENGINE` automatically (NBA via the rewired prospective PIT path —
§7 below; NBA additionally refreshes the payload corpus for the batch's
game-days first, post-GO only).

## 2. Success-path run log (SANDBOX; commands + exit codes)

Sandbox environment: `~/.my-quantitative-data/sports-papertrade-exec-v1/sandbox/`
with SANDBOX control copies (GO_TOKEN + registry copy clearly labeled
"REHEARSAL-SANDBOX-FABRICATION"; the REAL control dir and registry untouched).
Rehearsal clock `--now 2026-10-06T00:00:00Z` (sandbox-only hook; real mode
always wall-clock). Full log with outputs: `rehearsal/rehearsal_runs.json`.

| # | command (research.papertrade_exec.execute …) | exit | result |
|---|---|---|---|
| 1–3 | `plan --date 2026-10-09 / 2026-10-21 / 2026-10-12` (real mode, read-only) | 0 | WNBA: NY vs ATL tip 2026-10-09T23:30:00Z, anchor 17:20:00Z, eligible; NBA: 11 fixtures, anchor 16:50:00Z; SOCCER: post-GO source note |
| 4–6 | `--sandbox forecast/quote/decide --league WNBA --date 2026-10-09` | 0,0,0 | 1 real fixture; DECISION journaled |
| 7–9 | `--sandbox forecast/quote/decide --league NBA --date 2026-10-21` | 0,0,0 | 11 real fixtures → 4 BET_PAPER + 7 NO_EDGE |
| 10–12 | `--sandbox forecast/quote/decide --league SOCCER --date 2026-10-12` | 0,0,0 | 3 synthetic fixtures → journaled |
| 13 | `--sandbox run-day --date 2026-10-09` | 0 | chains NBA+WNBA+SOCCER; SANDBOX run reports are written under `<data-root>/sandbox/` (A7 F1 wording precision: the one file that exists under `<data-root>/runs/` is the REAL-mode pre-GO REFUSAL artifact from log entries 15/16 — a `BLOCKED_NO_GO` refusal JSON only, zero rows, itself evidence of the gate working; nothing else is ever written to `runs/` pre-GO) |
| 14 | `--sandbox settle --league NBA --date 2026-10-21 --results rehearsal_results_sandbox.json` | 0 | 401909091 WIN +3.82 USD; 401909836 POSTPONED_NO_RESCHEDULE → REFUND 0.00 USD (open exposure released) |
| 15 | `--sandbox dashboard` | 0 | `sandbox/dashboard/index.html` carries the SANDBOX banner ("SANDBOX LEDGER — SYNTHETIC FIXTURES ONLY … TEST ARTIFACT"); summary.json `sandbox:true chain_ok:true` |

Row census after the run (`rehearsal/rehearsal_row_census.json`):
GENESIS 1 · FORECAST 18 (1 WNBA real-fixture + 11 NBA real-fixture + 3 SOCCER
synthetic-fixture — all `mode=SYNTHETIC` probabilities) · MARKET_QUOTE 18
(`mode=SYNTHETIC`, bookmaker `SYNTHETIC_BOOK (rehearsal)`, key_fingerprint
`sandbox-synthetic-00` — never a real fingerprint) · DECISION 18 (6 BET_PAPER
+ 12 NO_EDGE) · SETTLEMENT 2 (1 WIN +3.82, 1 REFUND 0.00). Chain verify OK.

## 3. Adversarial matrix (test → expected → observed)

All in `tests/papertrade_exec/test_exec_battery.py`; observed = pytest result,
28/28 PASS.

| # | adversarial case | expected | observed |
|---|---|---|---|
| 1 | missing GO_TOKEN (sandbox control copy without token) | BLOCKED_NO_GO exit 3, zero rows written | PASS (`test_refuse_forecast_missing_go_token`) |
| 2 | wrong GO phrase (retired lane phrase in token) | BLOCKED_NO_GO, "verbatim" refusal; retired phrases accepted nowhere | PASS (`test_refuse_wrong_go_phrase`) |
| 3 | token present, registry phase without GO_CONSUMED | BLOCKED_NO_GO | PASS (`test_refuse_registry_not_consumed`) |
| 4 | REAL-mode mutation pre-GO (forecast, run-day) | BLOCKED_NO_GO; no real ledger dir created | PASS (`test_refuse_real_mode_mutation_prego`) |
| 5 | HEAD drift (`verify-pins --expect-head` wrong sha) | HEAD_DRIFT exit 6; correct sha → 0 | PASS (`test_refuse_head_drift`) |
| 6 | PIN drift (byte flipped in a pristine copy of the paper core, `--paper_core_root` override) | BLOCKED_PIN_DRIFT exit 7 naming `risk.py`, nothing written | PASS (`test_refuse_pin_drift`) |
| 7 | forecast exactly AT anchor / after anchor (WNBA 2026-10-09 anchor 17:20:00Z, exclusive) | BLOCKED_ANCHOR_PASSED exit 5, zero FORECAST rows (no partial batch) | PASS (`test_refuse_forecast_at_and_after_anchor`) |
| 8 | odds source updated after capture (`source_last_update > fetch_ts`) | DECISION STALE_PRICE journaled (ERRATUM_CAPTURE_1 E-2 row law) | PASS (`test_odds_updated_after_capture_stale_price`) |
| 9 | missing odds (forecast only, no quote) | DECISION NO_QUOTE journaled | PASS (`test_decide_missing_odds_no_quote`) |
| 10 | soccer quote missing the DRAW leg | NO_QUOTE, "missing required legs" (fail-loud) | PASS (`test_soccer_missing_draw_leg_refused`) |
| 11 | duplicate match (second decision draft for a decided match) | BLOCKED_DUPLICATE_SELECTION (core law); runner-level decide skips already-decided matches (idempotence) | PASS (`test_duplicate_match_second_decision_blocked` + `test_idempotent_rerun_no_duplicate_rows`) |
| 12 | 21st concurrent bet vs 100.00 USD open cap (core sandbox builder: 17 open after its settlements + 3 fillers = exactly 20 × 5.00) | 21st journaled BLOCKED_OPEN_EXPOSURE, stake 0, exposure unchanged at 10,000 cents, chain OK | PASS (`test_21st_bet_open_exposure_cap_in_lock`) |
| 13 | quota exhausted (core `QuotaSkip` precheck, no network by construction) | QUOTA_SKIP DECISION rows journaled per match, never silently skipped | PASS (`test_quota_exhausted_journals_quota_skip`) |
| 14 | key file missing / wrong mode (0644) | BLOCKED_KEY exit 4 (only the 12-hex fingerprint on success) | PASS (`test_key_missing_and_wrong_mode_blocked`) |
| 15 | ledger tamper (byte-level row edit) | decide AND dashboard refuse BLOCKED_TAMPER exit 8 | PASS (`test_ledger_tamper_refuses_decide_and_dashboard`) |
| 16 | postponement settlement | REFUND (pnl 0), exposure released, append-only chain intact | PASS (`test_settle_win_and_postpone_refund_then_dashboard_sandbox_banner`) |
| 17 | idempotent re-run (forecast/quote/decide twice) | no duplicate rows (row count unchanged; skips reported) | PASS (`test_idempotent_rerun_no_duplicate_rows`) |
| 18 | sandbox/real ledger cross-contamination | sandbox mode refuses a REAL ledger and vice versa (BLOCKED_SANDBOX_MISMATCH) | enforced in `open_ledger` (covered by mode isolation in 4) |
| 19 | no real probabilities stored pre-GO | every FORECAST row `mode=SYNTHETIC`, `model_version_sha=SYNTHETIC_ADAPTER_NOT_ENGINE` | PASS (asserted in success-path test) |
| 20 | dashboard NOT_RUN accounting | NO_QUOTE rows counted under `missing_or_invalid_odds` | PASS (`test_dashboard_never_lists_hidden_rows_and_counts_not_run`) |
| 21 | engine entry contracts (WNBA + SOCCER) deterministic, shape-conformant, nothing persisted | p∈(0,1), sums to 1, stable state_digest | PASS (`test_wnba_engine_entry_wired_contract`) |
| 22 | NBA engine replay via scored harness on SYNTHETIC inputs (season-boundary) | deterministic p_home∈(0,1) | PASS (`test_nba_engine_replay_via_scored_harness_synthetic_inputs`) |
| 23 | run-day chains all three leagues; hard refusal aborts | statuses OK per league; real-mode run-day BLOCKED_NO_GO | PASS (`test_run_day_chains_three_leagues_sandbox`, `test_run_day_refuses_hard_prego_real_mode`) |
| 24 | verify-pins reports optional entry files + data pins | data pins OK (WNBA sha, NBA composite); entries OK since pinned | PASS (`test_verify_pins_reports_optional_entries`) |

## 4. Pins

See `research/papertrade_exec/PINS.md` + machine-readable
`research/papertrade_exec/pins.json`. Byte-level sha256 is the binding
identity; worktree HEADs measured 2026-10-07 (advisory, sibling lanes
legitimately advanced): paper_core 8105e878 (dispatch said a752553f — pinned
files byte-identical), wnba26 4620… (d6ed119e + Lane B's entry commit),
nba_harness a76dadb1 (== dispatch), soccer 1ca5cd7d (24e5745f + Lane C's
entry commit). `verify-pins` exit 0 at rehearsal time; composite NBA pin
re-derived 208/208 OK.

## 5. What post-GO first real run does (exact behavior)

1. Owner types `GO SPORTS PAPERTRADE EXEC V1 RUN ALL` in chat; controller
   transcribes `GO_TOKEN.json` into
   `research/control/SPORTS-PAPERTRADE-EXEC-V1/` AND consumes it in
   `plans/CYCLE_REGISTRY.json` (phase records GO_CONSUMED for
   SPORTS-PAPERTRADE-EXEC-V1; the three absorbed lanes' own phrases die
   UNCONSUMED — accepted nowhere, enforced by the verbatim-phrase check).
2. `run-day --date <UTC day>` per league: `forecast` lazily imports the
   pinned engine (WNBA `wnba26_predict`, SOCCER `soccer_b1_replay`, NBA
   `nba26_predict` over the frozen ESPN payloads — §7), refuses at/after the
   batch anchor (T0−6h10m exclusive / soccer ko−6h strict), writes mode=ENGINE
   FORECAST rows into the REAL PaperLedger (genesis auto-created once with
   the key fingerprint, GEN-1). NBA additionally runs the post-GO incremental
   payload refresh for the batch's game-days BEFORE forecasting (bytes + .meta
   + self-hashed manifest chain; refuses BLOCKED_NO_GO without a consumed GO).
   `quote` captures pinnacle h2h via the core
   quota-guarded client (4/day + 120/month; QuotaSkip journaled as rows;
   HALT_KEY fail-closed). `decide` runs the crosswalk → EV → risk gates with
   the in-lock recheck and appends. `settle` applies results incl. refunds.
3. Cron automation only AFTER the GO (plan §1.5). Matches lacking schedule/
   forecast capacity/odds/crosswalk journal NOT_RUN-family rows — the GO
   cannot create rows for them.

## 6. Known limitations / incidents

- **BLOCKED_NBA_CORPUS_BIND — RETIRED by EXEC-NBA-REWIRE (history)**: the
  original NBA engine path routed real ratings through the SCORED cycle's
  harness corpus, whose outcome-bind law refused this cycle's GO (the bind
  token is mintable only by that cycle's own postgo gate; disclosed,
  fail-closed, never worked around). The rewire replaced it with the lawful
  prospective PIT path (§7) that never touches the scored corpus; the old
  code is kept as marked-DEAD history (`adapters.nba_real_corpus_read`,
  unreachable; `nba_harness` pins retained only for the battery's
  synthetic-inputs history replay). Full story:
  `ERRATUM_NBA_REWIRE.md`.
- Lane B/C landed their entry files WHILE this lane was building (mid-run
  import error caught and adapted). Their bytes are now pinned; if they
  iterate further, pin drift surfaces as BLOCKED_PIN_DRIFT_ENTRY (probe) /
  BLOCKED_PIN_DRIFT (real mode) — re-pin deliberately, never silently.
- No network was used at any point ($0 held; the only The Odds API surface
  exercised is the 0-credit design path, quota-guarded, post-GO).
- The sandbox GO_TOKEN/CYCLE_REGISTRY copies live ONLY under
  `~/.my-quantitative-data/sports-papertrade-exec-v1/sandbox/control` and are
  labeled fabrications; the real control dir contains no GO_TOKEN and the
  real registry phase is untouched ("REGISTERED (planned)").

## 7. NBA SUCCESS-PATH rehearsal after EXEC-NBA-REWIRE (pre-GO)

Raw evidence: `rehearsal/exec_nba_rewire_rehearsal.json` (every command +
exit code, row census, engine-path evidence). The run used a PRISTINE sandbox
copy (fresh tmp data-root; the sandbox GO token/registry copies are labeled
fabrications; the real control dir untouched). Outcome-masked: no game result
was read anywhere; the settle step's two results are rehearsal-file entries
exercising the settlement LAW, not game outcomes. No network; the post-GO
payload refresh was NOT executed — the frozen snapshot (composite 3d527b3c…,
208/208 re-verified) is the only lawful PRE-GO corpus state.

Engine path (REAL, in-memory ONLY): Lane D `loader.load_completed /
load_upcoming` + `predict.nba26_predict` lazy-imported from the byte-pinned
`nba26` package over the frozen ESPN payloads.

- Window: opening window 2026-10-20/21 (UTC tip dates) = **8 forecast rows**
  (BOS@DET 19:00Z, PHI@NY 23:00Z, OKC@SA 01:30Z, ATL@ORL 23:00Z, MIL@WSH
  23:00Z, MIN@MIA 23:30Z, CHA@BKN 23:30Z, CHI@TOR 23:30Z — all real frozen
  tips/teams; competition regular-season).
- Batch anchor: T0 − 6h10m with T0 = 2026-10-20T19:00:00Z ⇒
  **2026-10-20T12:50:00Z** (exclusive; forecast at/after it refuses —
  battery-pinned).
- **completed = 0** (zero FINAL games in the frozen snapshot) ⇒ every team
  enters at **R0 = 1500** (warm-up carried pre-registration) — the lawfully
  correct opening-night state, NOT a data gap.
- Probabilities: all eight p_home = 1/(1+10^(−100/400)) = **0.640065**
  (frozen HCA=100 prediction-only law); state_digest over the rating table
  `f2d59f35befbb1ffbbb6302fbac62804d51a39cab618ccc836b122f92722c8c5`;
  deterministic (byte-identical on re-run).
- **Disclosure (mirrors the earlier lanes):** engine probabilities exist
  IN-MEMORY ONLY for this proof; every PERSISTED row is `mode=SYNTHETIC`
  with `model_version_sha=SYNTHETIC_ADAPTER_NOT_ENGINE` and synthetic p, and
  every quote is `SYNTHETIC_BOOK (rehearsal)` with key_fingerprint
  `sandbox-synthetic-00`. Zero real probabilities and zero real odds are
  stored anywhere pre-GO.

SANDBOX chain (all exit 0):

| # | command | result |
|---|---|---|
| 1 | `plan --league NBA --date 2026-10-20 --to-date 2026-10-21` (real mode, read-only) | 8 fixtures, anchor 12:50:00Z, all eligible |
| 2–4 | `--sandbox forecast / quote / decide` (window) | 8 FORECAST + 8 MARKET_QUOTE (SYNTHETIC) + 8 DECISION: 2 BET_PAPER (401909091, 401909836) + 6 NO_EDGE; wiring probe `WIRED_ENGINE_READY` |
| 5 | `--sandbox decide` again (duplicate-bet law) | full no-op: 8 skipped "already decided", journaled [] |
| 6 | `--sandbox settle --date 2026-10-21` (rehearsal results file) | 401909091 WIN +3.82 USD; 401909836 POSTPONED_NO_RESCHEDULE → REFUND 0.00 USD |
| 7 | `--sandbox dashboard` | SANDBOX banner present ("SANDBOX LEDGER … TEST ARTIFACT"); `sandbox:true chain_ok:true` |

Row census after the run: GENESIS 1 · FORECAST 8 · MARKET_QUOTE 8 ·
DECISION 8 (2 BET_PAPER + 6 NO_EDGE) · SETTLEMENT 2 (1 WIN +382 ¢, 1 REFUND
0 ¢). Chain verify OK.

Battery additions covering this section (36/36 PASS total):
`test_nba_prospective_engine_success_opening_window`,
`test_nba_outcome_leak_injected_completed_row_ignored` (injected FINAL row
with tip > anchor and tip == anchor moves neither digest nor p),
`test_nba_adapter_refuses_tampered_payload_dir` (bytes≠meta ⇒
BLOCKED_NBA_PAYLOAD_TAMPER), `test_nba_adapter_pin_drift_blocked`
(BLOCKED_PIN_DRIFT_ENTRY probe / BLOCKED_PIN_DRIFT real mode, before any
corpus touch), `test_nba_refresh_prego_refused_and_postgo_manifest_chain`
(no network: fake fetch), `test_nba_window_forecast_stale_after_anchor`,
`test_nba_window_success_chain_sandbox`, `test_nba_real_mode_refuses_prego_exit3`.
