# B1R_FAIL_CLOSED_VERIFY — independent A7-style verification of c1d4f780

Verifier: fresh-context independent audit (owner-commissioned), 2026-10-10.
Object: commit `c1d4f7801ff5150ba8b0b47ea43114a1a8aa3d1e` on branch
`orca/spt-exec-v1-integration`, worktree
`.worktrees/sports-papertrade-exec-v1/integration`. Audit only — nothing
repaired, nothing consumed, nothing pushed, no tracked file modified, the
live ledger and the running service (pid 23029) untouched.

## VERDICT: VERIFY_PASS_WITH_FINDINGS

All seven audit items (A–G) PASS on re-measured evidence. The B1R fail-closed
guard is complete, byte-pinned, and adversarially probed (11/11 refusal paths
fire with the specific reason; the live England–Croatia B1R row is re-derived
BYTE-EXACT from the frozen map by the verifier's own implementation and is
ACCEPTed by the guard). 16/16 dedicated battery passed; the full-suite failure
set is exactly the 12 pre-existing sibling-entry-drift failures documented in
ERRATUM_EXEC_7 — nothing new. The real ledger sha256 was identical before,
during, and after every verifier run. Findings: 0 CRIT, 0 HIGH, 2 LOW, 3 INFO.

---

## A. Commit / branch / tree state — PASS

- `git rev-parse HEAD` → `c1d4f7801ff5150ba8b0b47ea43114a1a8aa3d1e`; branch
  `orca/spt-exec-v1-integration`. Confirmed.
- `git status --porcelain` (incl. `-uall`) → clean; the only untracked entry
  observed during the session was `research/control/SPORTS-PAPERTRADE-EXEC-V1/
  pm_watcher/` — another live session's directory (its process pid 23675 is
  running from it). Not the verifier's; ignored. This report file is the only
  file the verifier created and it is NOT git-added.
- Full diff of c1d4f780 read. 8 files: `plans/CYCLE_REGISTRY.json` (+628/−27,
  mirror refresh), `B1R_FAIL_CLOSED_REHEARSAL.json` (new, 50),
  `ERRATUM_EXEC_7.md` (new, 98), `research/papertrade_exec/execute.py`
  (+254/−few), `ops_service.py` (+18/−2), `pins.json` (+19/−3),
  `tests/papertrade_exec/test_b1r_fail_closed.py` (new, 530),
  `tests/papertrade_exec/test_exec_battery.py` (+55/−20). No other file
  touched — in particular `config.json`, `live_dashboard.py`, `results_fetch.py`,
  `adapters.py`, `__init__.py` and the GO_TOKEN are untouched by this commit.

## B. Guard completeness — PASS (code read + semantics independently re-derived)

`soccer_b1r_forecast` (execute.py:876–933) refuses, each with a specific
reason, journaled by the caller as terminal `NOT_RUN_NO_B1R_FORECAST`
(stake 0, chosen_leg None):
1. 0 B1R rows (B1-only ⇒ "CONTROL-ONLY") — verified;
2. >1 B1R rows ("ambiguous (duplicate law)") — verified;
3. `map_sha256 != 1f4a4c4f…953befd` — verified;
4. `model_version_sha != soccer_b1r_v1` — verified;
5. `control_ref_row_sha256` unresolvable — verified;
6. control row not a SOCCER FORECAST of the SAME fixture — verified;
7. control not B1 identity (`soccer_b1_replay` / `B1_SOCCER`; a self-referencing
   B1R control_ref is refused by this check) — verified;
8. `p_control_b1 != control.p` (T4) — verified;
9. B1R `p` != byte-exact frozen transform recomputed at decision time through
   the byte-pinned adapter's `b1r_transform` on the CONTROL's p (T4/T6) —
   verified;
10. `recorded_at_utc >= anchor_utc` (strict-before law), incl. missing/malformed
    timestamps — verified.

Verifier probe: 11 adversarial in-memory mutations of the live ledger rows
(map drift, version drift, dangling ref, self-ref, p_control tamper, p tamper,
recorded at/after anchor, missing timestamps, duplicate B1R, B1-only) — every
one refused with the exact reason; unmutated rows ACCEPTed. (Read-only probe;
no ledger written.)

- `cmd_decide` (execute.py:1321–1385): already-decided matches skip FIRST
  (line 1336–1338, terminal, never re-decided); real-mode stage-law safety net
  runs first (sandbox exempt from stage law by pre-existing design); the B1R
  guard then runs for `league == "SOCCER"` UNCONDITIONALLY of sandbox mode
  (line 1356–1368), BEFORE `crosswalk_ok`/`risk.evaluate_match`; a refused
  match journals NOT_RUN and `continue`s. Sandbox and real mode both apply
  the guard. Lawful BET_PAPER/NO_EDGE soccer rows additionally cite
  `decision_forecast_row_sha256` + `map_sha256` + `control_ref_row_sha256`
  (line 1375–1380).
- `cmd_forecast` (SOCCER): `b1r_switch_ts_verified` then
  `emit_b1r_forecasts` after the write pass (line 748–756). Emission is
  idempotent (any existing B1R row for the match ⇒ skip, never a second row),
  anchor-gated (now >= anchor ⇒ skip — no backfill; the command-level
  `check_anchor` refusal already fired before ANY write), refuses duplicate B1
  controls (`BLOCKED_B1R_CONTROL_AMBIGUOUS`), skips decided matches, refuses
  adapter-level failures (`BLOCKED_B1R_EMISSION`), and builds rows ONLY via
  `ad.build_forecast_rows(b1, m)` — no hand-built B1R payload anywhere.
- `b1r_switch_ts_verified` (line 847–873): requires the B1R cycle's registry
  `go_phrase_state` to start with `OWNER_GO_TYPED_LIVE` with second token ==
  pinned `2026-10-10T02:20:20Z`, else `BLOCKED_B1R_SWITCH_TS_UNVERIFIED`
  (fail-loud; soccer commands only). Verified against the root registry:
  state is `OWNER_GO_TYPED_LIVE 2026-10-10T02:20:20Z at head 153fc3c1…` —
  pins verified.
- Byte-pin of the adapter: `pins.json → packages.b1r_switch.files.
  b1r_adapter.py.sha256 = 815884affff5d2972a213341c7b416356b7360fe8f87a8dbd
  275d890eb5cac39` == verifier-measured `sha256` of
  `.worktrees/soccer-intl-b1r-paper-switch-v1/integration/research/control/
  SOCCER-INTL-B1R-PAPER-SWITCH-V1/lanes/L_SWITCH/code/b1r_adapter.py`.
  `required: true` ⇒ enforced by `verify_pins` at EVERY mutation command;
  the pkg has no CLI root-override seam (only the five PINNED_ROOTS keys are
  exposed as flags). Adapter source read: frozen law as planned (PAV map on
  p_D, proportional H/A residual, file+inner sha `load_map_verified`).
- Map pins re-measured by the verifier: map file sha256
  `b72a1151…48e64a7` == pin; inner `map_sha256` recomputed independently
  (json payload minus the declared field, sort_keys, utf-8) ==
  `1f4a4c4f…953befd`; 18 pools. `BLOCKED_B1R_MAP_PIN` carries
  `EXIT_PIN_DRIFT` (=7) which is a HARD break in `cmd_run_day`.
- B1 cannot reach a soccer decision: `risk.evaluate_match` has exactly ONE
  caller in the tree (execute.py:1370). For SOCCER, the `forecast=` argument
  is `fc_row`, which after line 1360 can only be a fully validated B1R row —
  every refusal path `continue`s before it. `forecast_index` (which retains
  the E-1 preference structure) is consumed by `cmd_decide` only for
  NBA/WNBA; its SOCCER uses are `cmd_forecast` idempotency-skip and
  `cmd_plan` display (`forecast_present`), both non-decisional.

## C. Test batteries re-run by the verifier — PASS

- `pytest tests/papertrade_exec/test_b1r_fail_closed.py -q`
  → **16 passed** in 5.24s. The battery asserts the REAL ledger sha unchanged
  around every test (`real_ledger_untouched` fixture) and resets the guard
  caches per test.
- `pytest tests/papertrade_exec/ -q`
  → **12 failed, 71 passed**. Failure list is EXACTLY the ERRATUM_EXEC_7
  list (all in `test_exec_battery.py`): wnba_engine_entry_wired_contract,
  forecast_reports_wiring_status, plan_is_readonly_with_real_tips,
  nba_engine_replay_via_scored_harness_synthetic_inputs,
  nba_prospective_engine_success_opening_window,
  nba_outcome_leak_injected_completed_row_ignored,
  nba_adapter_refuses_tampered_payload_dir, nba_adapter_pin_drift_blocked,
  nba_window_success_chain_sandbox, soccer_extension_crosswalk_laws,
  soccer_forecast_real_engine_in_memory_only,
  soccer_stage_law_blocks_engine_before_crosswalk. Visible cause (e.g.
  `BLOCKED_SOCCER_ENTRY: Lane C replay entry absent`) = sibling-worktree
  environment drift, untouched by this diff. Nothing new.
- The 2 deliberately-updated law-affected battery tests
  (`test_soccer_missing_draw_leg_refused`, `test_dashboard_never_lists_…`)
  carry explicit in-test comments stating the law change.
- Real-ledger sha immediately before and after BOTH runs:
  `13f65120550eba64d59e053897bfcb1161e9d3e0ce869c4716be2035977d2ae1`.

## D. Independent byte-exact transform re-derivation — PASS

Live ledger read-only: B1 control row `efea6160…` (match
`8a1174de9079b530bd6612e3fde6e2fa`, England–Croatia 2026-11-12T19:45Z, p =
H 0.6287766185639486 / D 0.1980108815138186 / A 0.1732124999222328) and B1R
row `dadbec715ba50d2b25dda4adf71d0ac0b6727a07ebc8af7948f2c5cd87177727`
(recorded 2026-10-10T02:22:43Z — after the GO, before its anchor
2026-11-12T13:45Z). The verifier implemented the transform DIRECTLY from the
plan text (`p_D' = g(p_D)` via the map pools; `p_H' = p_H·(1−p_D')/(1−p_D)`;
`p_A' = p_A·(1−p_D')/(1−p_D)`), NOT via the adapter:
- recomputed p = H 0.5877857143838626 / D 0.2502937720329025 /
  A 0.16192051358323492 — **BYTE-EXACT `==` to the row's p**;
- Δp_draw `0.052282890519083886` == the row's `draw_delta_b1r_minus_b1`;
- `p_control_b1 == control.p`; `map_sha256` == inner pin; recorded < anchor.
Values also equal the GO packet's pre-GO T6 byte-repro. `execute.
soccer_b1r_forecast` run read-only against a loaded ledger + Fixture-shaped
object → **ACCEPT** ("valid B1R decision forecast", row dadbec71…).

## E. Real-ledger non-interference — PASS

`/Users/hoangminhlong/.my-quantitative-data/sports-papertrade-exec-v1/ledger/
paper_ledger.jsonl`:
- BEFORE any verifier run: `13f65120550eba64d59e053897bfcb1161e9d3e0ce869c
  4716be2035977d2ae1` (20 rows);
- re-checked immediately before AND after each of the two pytest runs: same;
- AFTER all verifier activity (incl. probes): same. **Zero verifier-induced
  change.** No diffing needed — the sha never moved (the row-20 SETTLEMENT
  append at 04:31:14Z happened before the verifier's first capture and is the
  live service's own lawful write, per the rehearsal evidence).

## F. GO states untouched — PASS

Root registry `plans/CYCLE_REGISTRY.json` (sha `b6e39040…`):
- SPORTS-PAPERTRADE-EXEC-V1: phase `GO_CONSUMED CAPTURE_ACTIVE
  LIVE_SERVICE_ACTIVE` (RUN ALL consumed 2026-10-07, proven R10); active
  phrase `GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER` =
  REGISTERED_NOT_CONSUMED. Confirmed.
- SOCCER-INTL-B1R-PAPER-SWITCH-V1: `OWNER_GO_TYPED_LIVE 2026-10-10T02:20:20Z`
  (row updated 02:38:25Z — BEFORE the commit). Confirmed.
- SOCCER-INTL-WC-EURO-PAPER-PREP-V1: phrase `GO SOCCER INTL WC EURO PAPER
  PREP V1 INTEGRATE` = REGISTERED_NOT_CONSUMED. Confirmed.
- c1d4f780 consumed NONE: the commit's registry change is the worktree MIRROR
  only (the stale 2026-10-07 mirror refreshed); the committed mirror bytes ==
  root bytes (`b6e39040…` both), every go_phrase_state line in the mirror
  diff carries a root state that pre-exists the commit (all registry
  updated_at stamps predate the commit time 04:50:38Z). GO_TOKEN.json not
  touched by the commit. No GO typed or consumed by the verifier.

## G. Bypass hunt — PASS (none found)

- Writers of soccer DECISION rows: only `execute.py` (stage-law,
  crosswalk-miss, NO_QUOTE, QUOTA_SKIP, NOT_RUN_NO_B1R_FORECAST journals and
  the guarded `evaluate_match` path — all stake 0 except the guarded
  BET_PAPER/NO_EDGE). `ops_service.settle_pass` → SETTLEMENT rows only (via
  `cmd_settle`, BET_PAPER decisions only). `live_dashboard.py`: display-only
  (list ops + one HTTP `wfile.write`; no ledger writes).
  `results_fetch.py`: reads DECISION BET_PAPER rows; writes results JSON
  files only. `risk.evaluate_match`: one caller (see B).
- `config.json` `sport_keys.SOCCER = ["soccer_uefa_nations_league"]` —
  UNCHANGED by the commit (file not in the diff). The four WC/Euro keys are
  NOT armed anywhere in the diff; "WC/Euro" strings in the registry-mirror
  portion of the diff are historical cycle rows / evidence prose only. The
  guard is key-agnostic (applies to every SOCCER fixture regardless of sport
  key), so arming keys later inherits the same law.
- Service: pid 23029 started 2026-10-10 11:51:01 +0700 — 23 seconds AFTER the
  commit (11:50:38 +0700) — so the running supervisor imported the GUARDED
  code (module-level `_B1R_SWITCH_VERIFIED` cache semantics per finding F-1
  below).

## FINDINGS

- **F-1 (LOW) — switch-ts re-verification is process-cached in the long-lived
  service.** `b1r_switch_ts_verified` memoizes `_B1R_SWITCH_VERIFIED` at
  module level. Each CLI command is a fresh process (claim "re-verified on
  every soccer command" holds for CLI), but `ops_service` calls
  `cmd_forecast`/`cmd_decide` IN-PROCESS across cadence ticks, so the
  registry file is re-read only on the first soccer command after service
  start. A later registry-side change (e.g. the B1R row CASed away) would not
  be noticed until a restart. Fail-safe direction: the cache can only
  suppress a BLOCKED, and per-decision B1R row validation (transform, pins,
  anchor) is unaffected. Suggest resetting the flag per cmd_* invocation.
- **F-2 (LOW) — map-pin check is lazy in decide on a B1-only ledger.**
  `soccer_b1r_forecast` reaches `b1r_map()` only after the row-level checks
  pass; on a ledger where the match has B1 rows but no B1R rows, a DRIFTED
  map file surfaces as per-match NOT_RUN_NO_B1R_FORECAST journals rather than
  the loud `BLOCKED_B1R_MAP_PIN` promised by `b1r_map`'s own docstring. Safe
  (nothing decides; stake 0) and the service chain blocks earlier at
  cmd_forecast's eager `b1r_map()`, but a standalone `decide` under map drift
  journals TERMINAL NOT_RUN rows that a hard block would have left undecided.
- **F-3 (INFO) — cmd_forecast write ordering.** `b1r_switch_ts_verified` and
  emission run AFTER the lawful B1 forecast rows + NOT_RUN miss journals are
  appended. Those writes are lawful under the standing EXEC GO regardless of
  switch state, so no unlawful write is possible; noted for the record.
- **F-4 (INFO) — `forecast_index` shape retained.** The E-1
  setdefault-first/B1R-overwrite structure remains, but `cmd_decide` no
  longer consumes it for SOCCER; remaining consumers are non-decisional
  (idempotency skip, plan display).
- **F-5 (INFO) — running service is on the new code.** pid 23029 start time
  post-dates the commit by 23s (see G).

## What this verification did NOT check

- The pinned paper_core (`spt_core`) internals — `risk.evaluate_match`,
  `ledger.append/append_decision`, `in_lock_recheck`, `settle` — out of
  scope; their bytes are pin-verified (`__init__.py a37a55ae…` re-seal) and
  the re-seal is documented in pins.json.
- The 12 pre-existing failures were NOT re-run at parent b6459892 by this
  verifier (a stash/checkout would mutate the audited worktree); identity of
  the failure LIST with ERRATUM_EXEC_7's documented list was verified
  name-by-name, and visible failure causes are sibling-worktree drift.
- No live-network behavior (odds/events API), key hygiene probe, dashboard
  HTTP serving, or quota ledger behavior was exercised.
- The root registry's CAS machinery was not audited; root registry states
  were read as bytes.
- The live ledger's hash chain was not re-walked row-by-row by the verifier
  (chain verification is owned by the pinned core and ran inside every
  ledger open during the batteries; the boundary rows were spot-read).
- pm_watcher (pid 23675, another session) was not audited.
