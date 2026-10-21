# A7 ROUND 17 — INDEPENDENT VERIFIER NOTES

- Verifier: independent A7 audit-only agent. Audit only; repaired nothing; no
  commits/pushes; no writes to any ledger, registry, or app state. The only
  writes made are the two artifacts in this directory.
- Measured HEAD: `ef45e2495188ccdeb89dabde015f1abdf6b7144c` on
  `orca/spt-exec-v1-integration` (`git rev-parse HEAD`, re-verified after the
  coordinator re-anchor). Dispatch originally pinned `cef8412c`; the lane added
  `a43130e1` (WSL settle-health STALE_CORPUS) and `ef45e249` (PM public-search
  join law vs real Gamma shape) mid-audit; per coordinator instruction the
  verdict is for `ef45e249` and the deltas are audited under checks 2/3/9.
- Python: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`; all pytest
  runs from the worktree cwd.

## Check 1 — FEATURE GATES OFF  ⇒ PASS

- `research/papertrade_exec/config.json` L144-148:
  `"feature_gates": {"pm_cutover_active": false, "ai_authority_active": false,
  "law": "owner 2026-10-20: production gates stay OFF until typed GO; ..."}`
- `execute.papertrade_flags` (execute.py L1173-1184) reads config.json inside
  the module dir and returns `bool(fg.get("pm_cutover_active", False))` /
  `bool(fg.get("ai_authority_active", False))` — absent key or unreadable
  config ⇒ both False. `test_feature_gates_default_off` (test_pm_cutover_wiring
  L69-72) asserts exactly this and is green.
- Gates only flip behavior at execute.py L1349/L1389 (quote) and L1866
  (decide). Nothing else reads them.

## Check 2 — PM CUTOVER PATH LAWS  ⇒ PASS

- **2a BOTH-names join, fixture-id never the event id.**
  `pm_moneyline.discover_and_join` (ef45e249 shape): query variants
  `_search_variants` (full names, then single-word short forms); the title
  pre-filter requires `_team_name_hit(home, title) AND _team_name_hit(away,
  title)` — BOTH teams, order never trusted. Identity is then the strict
  market-outcome law: `_is_moneyline` (market outcomes normalized ==
  the two pinned names, bidirectional containment, derivatives refused) and,
  downstream, `map_outcomes_to_legs` by outcome NAME (ambiguity ⇒
  NOT_RUN_MARKET_MISMATCH). In `pm_quote_rows_for_fixtures` (execute.py
  L1236-1256) the fixture id travels only as `crosswalk["fixture_id"]`; the
  quote's `event_id` is `str(ev.get("id"))` from the joined Gamma event.
  Live-verified claim (event 1191461 'Hawks vs. Magic') is consistent with the
  short-form/AWAY-first law; battery asserts `pm_crosswalk.fixture_id ==
  "401918299"` while `pm_walk.event_id == "PM-EV-1"`.
- **2b SOCCER exactly 3 YES/NO markets of ONE event, fail-closed.**
  `discover_and_join_3yes` (ef45e249 `_join_3yes_in_event`): only 2-outcome
  YES/NO markets; leg attribution needs the question to hit that leg uniquely
  (`in_home XOR in_away`, or draw); complete set {HOME,DRAW,AWAY} from ONE
  event required, else None ⇒ execute.py raises
  `BlockError("NOT_RUN_PM_QUOTE")` (L1277-1281); a walk with
  `all_present != True` ⇒ NOT_RUN_PM_QUOTE (L1290-1293); odds set !=
  {HOME,DRAW,AWAY} ⇒ NOT_RUN_PM_QUOTE (L1298-1302).
- **2c per-leg own-token walks; AWAY never 1−HOME; outcomePrices never in
  math.** 2-way: `probe_event_moneyline` walks `tokens[i]` per leg via
  `walk_ask`; 3-YES: `quote_3yes` walks the YES token chosen by outcome NAME
  (`yes_idx`). Grep `outcomePrices|indicative`: only pm_moneyline L277-286
  (`indicative_prices` — "NEVER used as a quote") and pm_quote_source L133-152
  (`indicative_outcome_prices` — "display-only"); zero hits in execute.py /
  decision_pipeline.py math. Grep `1 - HOME` style inference: none; the only
  `1.0 /` division is the odds law below.
- **2d odds = 1 / vwap_ask; best_ask evidence-only.**
  execute.py L1266-1267 and L1295-1297: `odds = {leg: round(1.0 /
  l["vwap_ask"], 6) ...}`. best_ask appears only as a presence filter (L1297),
  in the `depth_walked` context booleans (L1788), and in dashboard display.
  decision_pipeline consumes `odds`/`ev_net_by_leg` from the row — no
  best_ask hits. `walk_ask` builds vwap from the full ask walk INCLUDING the
  taker fee in spend (pm_moneyline L196-209).
- **2e real stake.** execute.py L1228:
  `stake = core.stake_for_decision(led.equity_cents())`; `stake <= 0` ⇒
  NOT_RUN_PM_QUOTE. Grep `10000` in execute.py / pm_moneyline.py /
  pm_quote_source.py: zero hits. Battery asserts `stake_walk_cents == 1000  #
  REAL 1% stake, never 10000` and `stake_cents == 1000 and stake_law ==
  'v3-1pct'` on the decision row.
- **2f append in both PM branches of cmd_quote.** Sandbox seam branch:
  rows appended L1356-1357 (`mode PM_CUTOVER_SANDBOX_SEAM`); real cutover
  branch: rows appended L1400-1401 (`mode PM_CUTOVER`), rerun-safe
  (never-quoted/never-decided only).
- **2g no Odds API fallback.** The PM branch (L1389-1406) and
  `pm_quote_rows_for_fixtures` call only pm_moneyline/pm_quote_source, which
  speak directly to gamma-api/clob.polymarket via urllib. Grep
  `odds_client|OddsClient|get_odds` in both pm files: no matches. The
  quota-guarded OddsClient path (L1407+) is the PRE-cutover branch, reached
  only when the flag is off. PM failure ⇒ NOT_RUN_PM_QUOTE (test
  `test_pm_cutover_path_no_fallback`).
- **2h seams refused in real mode.** `args.pm_probe` /
  `PAPERTRADE_PM_PROBE_JSON`: `_pm_probe_seam` raises
  `BLOCKED_TEST_HOOK_IN_REAL_MODE` when either is present without sandbox
  (L1193-1197), re-checked inside `pm_quote_rows_for_fixtures` (L1223-1227);
  test `test_pm_probe_seam_refused_in_real_mode` green. `args.ai_opinion`
  raises the same code in real mode (L1737-1741). `PAPERTRADE_AI_OPINION_JSON`
  in real mode is not read at all (sandbox-guarded at L1735) — inert, fail-safe,
  but no block code raised; recorded as LOW finding F-3. Both seams are active
  only under sandbox=True; both exercised in the battery via monkeypatched env
  with sandbox env fixtures.
- **Delta audit (ef45e249).** Diff cef8412c..ef45e249 on pm_moneyline.py adds
  `_team_name_hit` (candidate retrieval only: full name OR last-word short
  form len>=4), `_search_variants`, a User-Agent header (public-search 403
  without it), and the 3-YES response scanner. The strict identity layers
  (`_is_moneyline` outcome law, `map_outcomes_to_legs` NAME law, 3-YES
  question-uniqueness, single-event completeness) are unchanged. Ambiguity
  spot-checks: two-word pinned names produce distinct short forms; a
  3-char single word (e.g. "USA") never uses the short-form path (len>=4
  guard); swapped/ambiguous outcomes still fail closed
  (`test_mapping_adversarial_swapped_names_mismatch`,
  `test_probe_refuses_on_mapping_mismatch` green).

## Check 3 — AI BOUNDARY  ⇒ PASS

- **3a placement.** cmd_decide: `risk.evaluate_match` (L1848-1852) ⇒ flags +
  `dec.status == "BET_PAPER"` guard (L1865-1866) ⇒ `load_ai_opinion` +
  `ai_boundary_review` (L1867-1874) ⇒ `led.append_decision` (L1890-1893).
  Flag OFF: the guard never enters; `ai_boundary_review` itself returns
  `{"action": "DISABLED"}` (L1667-1668) — and is not even called. Legacy
  behavior byte-identical (also asserted by `test_ai_boundary_disabled_when_flag_off`).
- **3b fail-closed opinions.** `_map_ai_opinion` L1690-1725: status !=
  COMPLETED ⇒ ABSTAIN; completedAt > deadline ⇒ ABSTAIN; VETO (verdict or
  recommendedAction) ⇒ VETO; CHALLENGE/ALTERNATIVE+leg or SWITCH+leg ⇒
  SWITCH; KEEP ⇒ KEEP; anything else (incl. literal "None" strings) ⇒ ABSTAIN.
  load: missing opinion ⇒ ABSTAIN (L1746-1748); read error ⇒ ABSTAIN
  (L1756-1758). `evaluate_ai_gate`: VETO ⇒ NOT_PLACED (L163-165);
  ABSTAIN/None/"" ⇒ NOT_PLACED G_ABSTAIN (L167-174); unknown ⇒ G_UNKNOWN_ACTION
  fail ⇒ NOT_PLACED (L219-220). Demotion (L1885-1889): status
  `NOT_PLACED_AI_GATE`, `stake_cents=0`, `chosen_leg=None`,
  `candidate_chosen_leg` + full `ai_gate` record (action, proposed_leg,
  opinion why/file/sha256, gates_failed) retained. Battery
  `test_pm_cutover_ai_abstain...` asserts all of this end-to-end.
- **3c regrade scope.** KEEP ⇒ G_EV_KEEP (frozen EV >= 0.05) + G_PIT_KEEP;
  the round-15 KEEP-PIT fix asserted (anchor passed ⇒ NOT_PLACED). SWITCH ⇒
  invalid/same target ⇒ G_SWITCH_TARGET fail; otherwise full per-leg set:
  G_EV_SWITCH, G_QUOTE_SWITCH, G_DEPTH_SWITCH (missing depth ⇒ NOT_PLACED,
  `test_switch_gate_needs_depth_on_target_leg`), G_PIT_SWITCH,
  G_STAKE_SWITCH, G_CAP_SWITCH, G_DRAWDOWN_SWITCH, G_ONE_SELECTION. The FULL
  frozen set for the actual placement is enforced by `risk.evaluate_match`
  (ran before the boundary on the standing leg) and `risk.in_lock_recheck`
  (runs at append regardless of AI action); the AI gate is an additional
  fail-closed demotion layer, never a bypass. Documented as F-4(b).
- **3d no AI-supplied numbers.** `ai_gate_context` (L1761-1791) sources:
  chosen_leg/p_frozen/odds_frozen/ev_net_by_leg/stake_cents from the decision
  row; equity/open_exposure/drawdown from the ledger; cap from the pinned
  core. The opinion record contributes only `action` + `proposed_leg`
  (candidate dict L1869-1870). `evaluate_ai_gate` uses the AI leg only to
  INDEX frozen numbers. Battery asserts frozen p/odds unchanged when the AI
  says KEEP ("fabricated AI EV ignored" in both node batteries too).
- **3e VETO/unknown.** See 3b — VETO returns NOT_PLACED before any gate can
  pass; only `decision == "PLACE"` preserves BET_PAPER (L1885); any other
  decision demotes. No bypass path found.

## Check 4 — RUN-DAY CONTAINMENT  ⇒ PASS

- cmd_run_day (execute.py L1902-1936): per-league try block; `except
  _LaneBlock` (wsl_lane.LaneBlock) reported per-league and the loop continues;
  hard-break tuple `(EXIT_BLOCKED_NO_GO, EXIT_BLOCKED_KEY, EXIT_BLOCKED_TAMPER, 7)`
  is byte-identical in the BlockError branch (L1918-1921) and the LaneBlock
  branch (L1929-1932). Constants measured: 3 / 4 / 8 / 7 (EXIT_PIN_DRIFT=7).
  Report is written (write_run_report) before re-raising `hard`. A
  non-safety LaneBlock (e.g. exit 9 lane refusal) never crashes the batch.

## Check 5 — TESTS  ⇒ PASS

- `pytest tests/papertrade_exec/ -q` at ef45e249: **147 passed, 0 failed**,
  exit 0. Reconciliation of the dispatch's "146": cef8412c's own commit
  message says "battery 146/146 x2 byte-repro"; delta a43130e1 adds exactly
  one test function to test_wsl_results.py (verified via
  `git show a43130e1 | grep -c '^+def test_'` = 1); 146 + 1 = 147, and both
  delta commit messages state "battery 147/147". Count drift fully explained;
  not a finding.
- Node batteries (apps/paperdesk, all exit 0):
  - `node test_ai_gate.js` → "ai gate: 17/17 pass", EXIT=0
  - `node test_ai_seam.js` → "ai seam: 43/43 pass", EXIT=0
  - `node test_lifecycle_safety.js` → "lifecycle safety: 13/13 pass", EXIT=0
  - `node test_paper_policy.js` → "paper policy: 27/27 pass", EXIT=0
- WSL subset re-run for check 9: test_wsl_lane.py + test_wsl_results.py =
  29 passed.

## Check 6 — LEDGER NON-INTERFERENCE + INTEGRITY  ⇒ PASS (read-only)

- File: `/Users/hoangminhlong/.my-quantitative-data/sports-papertrade-exec-v1/
  ledger/paper_ledger.jsonl` — 82 rows (wc -l), 79619 bytes.
- Verification method: read-only load through the pinned core
  (`research/papertrade.ledger.PaperLedger(...).load()` +
  `verify_chain()`) — no append calls anywhere; confirmed mtime identical
  before/after.
- Result: `chain_ok=True, errors=[]`. Row types: GENESIS 1, FORECAST 27,
  MARKET_QUOTE 17, DECISION 27, SETTLEMENT 10; all 82 rows carry row_sha256.
- mtime = Oct 20 23:51:50 2026 — predates this audit session (Oct 21), so no
  sandbox/test run (including my pytest runs, which use tmp env fixtures)
  wrote to the live ledger.

## Check 7 — APP LIFECYCLE  ⇒ PASS (code inspection; live pid untouched)

- Single instance: `helpers/opslock.py` takes `flock(LOCK_EX|LOCK_NB)` for the
  child's lifetime; already-held ⇒ prints `{"blocked":"SINGLE_INSTANCE"}`,
  exit 3. runner.js attach-before-spawn: healthy verified heartbeat ⇒ attach,
  never a second spawn; flock held without a healthy runner ⇒
  SPAWN_REFUSED_LOCK_HELD (probe only). Identity binding = command +
  --data-root (+ --sandbox) + lstart; lstart mismatch ⇒ PID-reuse refused,
  state drops to detached, PID_REUSE_REFUSED journaled (all asserted by the
  13/13 lifecycle battery).
- Quit: main.js `before-quit` → confirmation dialog → `gracefulStopRunner
  ('app-quit')` → quits only when the stop is verified clean AND the flock is
  released; otherwise QUIT_BLOCKED, app stays open. gracefulStopRunner is
  fail-closed: identity-lost ⇒ no signal; unexplained held lock ⇒ stop
  refused; launchd bootout failure ⇒ runner left RUNNING, stop aborted. Stop
  is SIGTERM (SIGKILL only while identity is still verified). No rm/unlink in
  the quit path; open bets stay open (dialog states it; settle code only
  appends settlement rows). Ledger/settlement files untouched by quit.

## Check 8 — PINS + SOCCER RE-SEAL  ⇒ FAIL (F-1)

- `python -m research.papertrade_exec.execute verify-pins` at ef45e249:
  **exit 0**, top-level `drift: []`, `missing_optional: []`.
  - Extension (data pin, required): OK — measured
    `57354475350bf12a0b80c6df7fe949419dddb1f8c39bb095dbacee1b719366a3` ==
    pin. Direct `shasum -a 256` agrees.
  - Extension byte-prefix law: verified on raw bytes —
    `ext.startswith(seed) == True` (2531 seed bytes + 1580 appended bytes;
    8 appended identity pairs, each evidence-tagged with capturing snapshot
    sha + event ids).
  - **Seed sub-assertion FAILS.** Pin:
    `f5b85fb9ea2b9219b80c150564e20d4c0d0aa1e97b07a7d59de25c46d1ce5f77`.
    Actual file (prep worktree @ a8057a95, git-clean; last modified by
    cc7a3546, the very commit the re-seal note cites):
    `f5b85fb9ea2baa083c4c8cdc34a2462d6f5fa4bc0c4fbe2f17c183b734d03441`.
    verify-pins itself reports `status: DRIFT` for the file (visible in the
    JSON), but the entry is `required:false` so it neither raises
    BLOCKED_PIN_DRIFT nor populates `drift[]`.
  - Forensics: the two digests share exactly the first 12 hex chars — the
    abbreviated form used in the commit message and notes ("f5b85fb9"). The
    true full digest IS on record upstream:
    `soccer-intl-winprob-prospective-prep-v1/.../SOCCER-INTL-WINPROB-
    PROSPECTIVE-PREP-V1/CONTROLLER_CROSSWALK_20261009.md` line 35 records
    `f5b85fb9ea2baa08...`. No normalization variant of the seed (raw,
    no-trailing-newline, CRLF, whitespace-stripped) hashes to the pinned
    value — the pin tail corresponds to no measurement of the file. The
    re-seal committed in cef8412c (and carried into ef45e249, pins.json
    untouched by the deltas) therefore recorded an unmeasured digest.
  - Blast radius: NONE at runtime today — production loads the extension
    through `adapters.soccer_crosswalk_load` (required pin, fail-closed
    BLOCKED_PIN_DRIFT) and binds it to the seed FILE bytes via a live
    `startswith` check (adapters.py L787-793); the seed pin string is never
    consulted. It is an evidence-integrity defect in the seal record, not a
    decision-path corruption. Gates are OFF; no real run trusted the pin.

## Check 9 — WSL LANE LAWS  ⇒ PASS

- Code spot-check (wsl_lane.py): three-YES same-event join law (join_fixture_to_event;
  >1 joined event ⇒ NOT_RUN_MARKET_MISMATCH "ambiguous joins refused"; 0 ⇒
  NOT_RUN_NO_MARKET; "the old source is never auto-fallback"); 90-min stage
  law with exact-key equivalence {LEAGUE_90MIN → LEAGUE_PHASE_HOME_AWAY},
  everything else fail-closed NOT_RUN_RULES; pre-anchor snapshot law strict
  (`snapshot_law_ok`: fetch_ts < anchor; == anchor is stale);
  in-lock phrase gate: `wsl_phrase_state` reads FRESH registry bytes inside
  the ledger flock; requires BOTH the WSL row and the SPORTS-PAPERTRADE-
  CAPITAL-V3 row to record go_phrase_state starting with
  OWNER_GO_TYPED_LIVE, plus the §7 ordering law; missing either ⇒
  BLOCKED_NO_GO in-lock. Full-stake depth law: stake never shrunk to fit
  depth (zero depth ⇒ NO_QUOTE_DEPTH).
- Delta a43130e1: `classify_open_bets` is a pure read-only classifier over
  ledger rows already in memory (statuses from kickoff time + the bet's own
  quote-row PM identity; grace 2h; never reads UMA W/D/L partials, indicative
  prices, or standings — nothing is fabricated). ops_service.settle_pass
  journals the STALE_CORPUS incident to the ops incident journal and
  atomically writes `state/wsl_settle_health.json`; ledger access remains
  `_ledger_state()` = chain-verified, fail-closed TAMPER. The ledger is
  written only by the pre-existing settle path.
- Tests: WSL battery subset 29 passed; full battery 147 green (above).

## Findings summary

- **F-1 (HIGH)** — soccer seed pin ≠ actual seed file; digest tail after the
  correct 12-char abbreviation was never measured (see check 8). Repair:
  re-pin to `f5b85fb9ea2baa083c4c8cdc34a2462d6f5fa4bc0c4fbe2f17c183b734d03441`
  with erratum; make the builder print the seed sha; consider probing this
  optional pin by default.
- **F-2 (LOW)** — 2-way legs evidence `fee_total` always None (walk_ask emits
  `fee_cents`); display-only; fee law itself is inside vwap.
- **F-3 (LOW)** — `PAPERTRADE_AI_OPINION_JSON` in real mode is inert (env not
  read) instead of raising BLOCKED_TEST_HOOK_IN_REAL_MODE; pm_probe raises on
  env. Symmetry repair suggested.
- **F-4 (LOW)** — (a) 3-YES joiner failure detail coarsened at ef45e249
  (fail-closed preserved); (b) KEEP-branch regrade is EV+PIT, full frozen set
  enforced by evaluate_match + in-lock recheck — document so the law text is
  read as aggregate enforcement.

## Verdict

FAIL — driven solely by check 8 / F-1 (HIGH): the audited HEAD's own seal
record contains a seed pin that does not match the bytes it claims to pin.
All execution-path laws (checks 1-7, 9) pass at ef45e249; the production
surface is not corrupted and the repair is a one-line disclosed re-pin. Per
the severity discipline ("do not soften failures") the round verdict is FAIL
until the re-seal erratum lands.
