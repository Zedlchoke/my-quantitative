# A7 Independent Audit Log — MARKET-DATA-PLANE-V2R1

- Auditor: A7 (independent adversarial auditor)
- Date: 2026-09-10
- Worktree: /Users/hoangminhlong/my-quantitative/.worktrees/market-data-plane-v2r1/a7-audit
- Branch: orca/v2r1-a7-audit (single commit at end of audit)
- Audited candidate: 9aa9fd9b0bb7f7242b80354852f4d57aa343a43b
- Diff base (MDP-V2 terminal tip): 597e74c085e29fa5dd4632c942a0291ecccd25d1
- Python: /Users/hoangminhlong/my-quantitative/.venv/bin/python (cwd = worktree for pytest)
- Heavy lock: NOT acquired, NOT waited on. No network. Full tests/ battery NOT run.
- Verdict: **A7_AUTHORIZE_V2R1_CLOSURE** (high/critical count = 0; 1 MEDIUM + 5 LOW findings, all dispositioned no-block)

## What I ran, in order

### C1 — diff inventory
- `git -C <wt> diff --name-status 597e74c..9aa9fd9b` → 73 files. All within claimed ownership
  (plans cycle infra + own PLAN; research/control/market_data_plane_v2r1_run/**; 5 governance
  modules; 3 scripts; 6 test files; tests/fixtures/**). Zero touches to strategy/, ledger,
  survivors, S1, other cycles' plans, research/market_data_plane/**, research/data_fusion/**,
  provider payloads, secrets.

### C2 — historical immutability
- `git diff 597e74c..9aa9fd9b -- research/control/market_data_plane_v2_run/ research/audits/market_data_plane_v2/ research/control/market_data_plane_v1_run/` → EMPTY.
- Same diff for data/v9_manifests/universe_selection_v9.json, data/v8x_manifests/crypto_universe_selection.json,
  research/audits/v9p/{data_audit_v9,t02_gate_v9}.json, scripts/v8x_crypto_universe_selection.py → EMPTY.
- `shasum -a 256 scripts/v8x_crypto_universe_selection.py` → 709b40c229d733aa08df867a3e207da46d5c86a111c54c0d502d2b809beda406 (exact).
- v8x manifest sha prefix e73c703f confirmed.

### C3 — fixture authority
- `validate_fixture_manifest(<worktree>)` → 0 problems (canonical manifest 4 entries + fragment fixture_entries.json 50 entries).
- Independent sha256 recompute over all 54 entries → all match; contains_real_provider_payload/contains_secret exactly false everywhere.
- Class histogram: 50 SYNTHETIC_HAND_COMPUTED + 4 SCHEMA_MINIMAL. No REDISTRIBUTABLE_PINNED / DERIVED_NON_REVERSIBLE.
- Byte inspection (pyarrow): bars = constant round volumes (250.5/290.5/500.5), 96 rows/file, ns stamps at −0.1 ms before slot close;
  funding = constant rates at exact 8h spacing; instruments = hand-written filter blocks; legacy fixtures = placeholder heads
  ("5555…5", "dddd…d", prose). Regex secret scan over all fixture text files → no hits. BTCUSDT appears only as a symbol label.

### C4 — hermeticity
- `pytest tests/test_legacy_adapters.py tests/test_fixture_manifest.py tests/test_v9_universe_audit.py tests/test_terminal_identity.py tests/test_terminal_consistency.py tests/test_cycle_registry.py -q`
  → **145 passed, 21.52s** (13/8/27/45/30/22), 0 skips.
- Absence probes: catalog_live_crypto and funding_data/scan_2026 ABSENT; forex-free-v8/stocks-free-v12 worktrees are empty husks
  (no cycle_state, no .git) so declared legacy sources absent; CRYPTO-V17 state present but never read by suites.
- Code inspection: remediated tests touch only committed fixtures + tmp_path.
- `cd /tmp && pytest <wt>/tests/test_legacy_adapters.py -q --rootdir=<wt>` → 8 failed / 5 passed.
  Root cause (pre-existing at base): normalize_legacy_state → main_repo_root() → `git rev-parse --git-common-dir` fails outside a repo.
  Prescribed fallback: PYTHONHASHSEED=7 vs 123 from the worktree → 40 passed == 40 passed. Recorded as finding F3 (LOW).

### C5 — assertion-strength mutations (all reverted; tree clean afterwards)
- C5a: tampered one digest in a tmp COPY of the manifest → validator reports `sha256 mismatch` (caught).
- C5b: (i) injected a byte-mutating write into build_registry_from_legacy → suite 1 failed
  (test_real_legacy_files_are_read_without_byte_mutation) — assertion bites; (ii) removed the
  `assert before == after` line, re-injected the same bug → 13 passed — the assertion was the sole guard;
  (iii) reverted production + test, `git checkout -- tests/fixtures/legacy_adapters/` (my experiment's side effect),
  re-ran → 13 passed, porcelain clean.
- C5c: `pytest tests/test_v9_universe_audit.py -v -k "mutation or invariant"` → 5 passed, 0 skipped
  (btc-into-selected, removed bar→gap, missing settlement, altered pinned volume, cwd/hashseed invariance).
- C5d novel mutations (tmp copies, engine run via load_inputs/run_audit_from_bundle):
  - M1 swap two funding rows → PASS (engine sorts timestamps; order carries no semantics) → F5 LOW.
  - M2 duplicate a scored-window bar row → PASS (completeness audit; extra rows outside scope) → F4 LOW.
  - M3b duplicate EVERY pre-window bar of EEEUSDT → PASS. Root-caused to a PRE-EXISTING zip-truncation bug in the
    immutable v8x script (`slot_opens_from_ts_event` returns `np.unique` opens; `zip(opens, qv)` truncates):
    median stays '24048.0' with doubled rows → drift gate blind to injected rows (altered values ARE caught) → F1 MEDIUM (pre-existing, no-block).

### C6 — Tier-R truthfulness
- `python scripts/legacy_state_tier_r_check.py` → verdict NOT_RUN_DATA_UNAVAILABLE, EXIT=3; census {expected 3, present 1, absent 2};
  zero-mutation proof for the present CRYPTO-V17 source (sha 43ceb158… before==after); offline_no_secret assertion.
- `python scripts/v9_universe_audit_tier_r.py` → verdict NOT_RUN_DATA_UNAVAILABLE, EXIT=3; availability artifact with
  expected inputs (catalog_live_crypto, funding_data/scan_2026 — both absent), census zeros, network_access_used=false.
  (The CLI wrote research/audits/v9_tier_r/ — inspected for evidence, then DELETED before committing; nothing outside
  my audit dir was committed.)
- `grep tier_r tests/` → no imports (only fixture-manifest consumer-declaration strings).

### C7 — V9 semantics + gate authenticity
- AST comparison base vs new test file: 0 of 20 old tests dropped, 0 old assertions lost (assert count 71 → 126; 7 tests added).
  Real-data constant (gaps_found_total == 57) replaced by hand-computed fixture constants with STRICTER per-symbol + btc-totals asserts.
  BTC exclusion incl. benchmark-context role fields, gap-class allowlist, funding f1/f2/f3 + corroboration, window containment,
  byte-identical rerun, reproduce-committed-artifacts, gate shape/unique ids/PASS — all still asserted.
- Gate assembly read line-by-line: checks derive from computed values (drifts, btc_in_selected, unexplained_total, failed_ages,
  funding_all_complete, pit flags) with typed FAIL_* status tags; the two structural ok:True entries are enforced upstream
  (load_inputs refuses wrong-sha inputs; test_load_pinned_selection_rejects_wrong_sha proves it).
- Authenticity: A7 re-ran the engine over the COMMITTED bundle → manifest.json / audit.json / gate.json byte-identical to expected/.

### C8 — legacy semantics
- AST comparison: all 9 old tests present, no assertion lost; 4 typed-error/determinism tests added.
- Warning wordings byte-identical to base: stale-head, prose-head, "drift recorded-not-normalized per sec2".
- Behavioral: `build_registry_from_legacy(...)` with source_paths=None on this host → typed
  `LegacySourceUnavailable: FOREX-FREE-V8: legacy source unavailable at <exact path>` (fail-closed default preserved).

### C9 — adversarial terminal identity matrix (synthetic repos in /tmp/a7_matrix)
23 initial + 5 corrected checks (two of my own scenario bugs corrected and re-run clean):
- PASS anchor==tip (zero findings); branch_tip always surfaced.
- PASS control addendum; PASS registry-surface commit.
- FAIL(as intended) code change / test change / PLAN_*.md edit / HYPOTHESIS_LEDGER.md edit → TERMINAL_IDENTITY_FORBIDDEN_PATH HIGH.
- Event log: append PASS; delete FAIL; reorder FAIL; canonical journal rewrite FAIL (non-vacuous base).
- Orphan tip → NOT_ANCESTOR HIGH; malformed sha → HIGH; head≠anchor → ROW_MALFORMED HIGH.
- Undeclared TERMINAL row → exactly one visible TERMINAL_IDENTITY_UNDECLARED MEDIUM (never silent).
- CAS: wrong prev_sha → ControlStateDrift; non-TERMINAL row → ValueError; head mismatch → ValueError;
  correct prev_sha applies; identical re-declare no-op write; different re-declaration raises (immutable).
- Idempotency (the core anti-self-reference property): double validation at an evidence-only tip → zero findings both runs,
  tip byte-stable, NO repin commit.
- New edge found: EVENT_LOG_REWRITTEN vacuous when the log is absent at the anchor → F2 LOW (real anchors predate the logs; verified).

### C10 — real-history repin detection
- `validate_terminal_identity` on my worktree with the real MDP-V2 row:
  undeclared → [TERMINAL_IDENTITY_UNDECLARED/MEDIUM], branch_tip surfaced (9aa9fd9b).
- Hypothetical declared row (terminal_anchor_sha=41bf9b1…) at branch_tip=597e74c → ZERO findings;
  descendants exactly [98a1b780…, 597e74c…]; `git diff --name-status 41bf9b1..597e74c` shows ONLY
  plans/ACTIVE_CYCLES.json + plans/CYCLE_REGISTRY.events.jsonl + plans/CYCLE_REGISTRY.json (+ the V2 cycle event_log at
  intermediate commits); journal 39→43 lines, anchor version a strict byte-prefix (`cmp` verified); cycle event_log 14→15, same.
- Against the current candidate tip the same hypothetical V2 row correctly flags the V2R1 cycle's own new paths as
  FORBIDDEN for the V2 row — strict scoping works; V2 closure re-validation belongs to its own lane (plan G9).

### C11 — allowlist breadth
- default_allowlist = cycle control/** + cycle audits/** + exactly the 3 registry surfaces.
- Code/tests/plans-docs/ledgers/research results NOT allowlisted (proven by C9 HIGH failures).
- Legacy/ACTIVE rows keep head==tip in terminal_consistency (hook is additive; identity_result=None → historical behavior).
- Live branch tip surfaced in every result.

### Gate evidence scrutiny
- research/control/market_data_plane_v2r1_run/: state.json is TRUTHFUL — phase R0_BOOTSTRAP, completed_gates={},
  open_gates G0..G9, verdict None. Event log has 2 lines (R0_INTAKE_MEASURED, R0_BOOTSTRAP). G0/G1 gate JSONs carry verdict PASS
  while the ledger still lists them open → F6 LOW (bookkeeping reconciliation, no false closure claim; plan G6 awaits this A7 verdict).
- p0_first_report.json inspected (host, root 8f5ee9c + owner dirty classification, residual signature) — consistent with its claims.

## Findings (all dispositioned no-block)
- F1 MEDIUM (pre-existing, out of scope): v8x zip-truncation blinds the pinned-volume drift gate to injected duplicate bar rows.
- F2 LOW: terminal_identity event-log rewrite check vacuous when the log is absent at the anchor.
- F3 LOW (pre-existing): legacy suites not strictly cwd-independent (git rev-parse from non-repo cwd); hashseed invariance holds.
- F4 LOW: scored-window duplicate bar row outside the audit's completeness semantics.
- F5 LOW: funding-row reorder is by-design order-independence.
- F6 LOW: controller gate ledger not yet reconciled with G0/G1 evidence files (verdict None is truthful).

## Independence / zero-repair confirmation
A7 authored zero implementation changes. All mutations were throwaway, in-tree edits or /tmp sandboxes, fully reverted
(fixture bytes restored via git checkout and re-verified with 13 passed). The Tier-R CLI's stray artifact directory was
deleted before committing. This branch contains ONLY research/audits/market_data_plane_v2r1/**. Heavy lock never acquired.

---

# A7-r2 — DELTA re-audit of the terminal-identity scope fix (2026-09-10)

Scope: ONLY commit 011ef81e (cherry-picked identically as 85f39c3, tree b5cfb79f both —
empty diff verified), the A4-r2 remediation of the G9 FAIL_TERMINAL_IDENTITY_CONTRACT
refusal at d2416c3 (background read from bytes: gates/V2R1-G9_terminal_identity_FAIL_r1.json
+ the G9_FAIL_R1 event_log.jsonl line). The prior A7 sections above are untouched.

## Delta checklist results (full evidence in a7_delta_verdict_r2.json)

- **D1 diff inventory — PASS.** Exactly the 5 claimed files (2 governance + 3 tests),
  748+/73−. Zero other files.
- **D2 semantic preservation vs the prior C9 matrix — PASS.** Anchor grammar/missing/
  ancestry/branch-missing, head!=anchor, row-shape malformations, report mismatch,
  event-log delete/reorder (cycle log AND canonical journal) vs append, undeclared
  legacy row (exactly one visible MEDIUM) — all unchanged; identity/consistency/registry
  suites 104 passed. Intended semantic delta: foreign-scope successor changes above an
  old anchor are LISTED (foreign_scope_paths) not HIGH — that is the §12.2 semantics the
  G9 ruling prescribed for the 86/139 false HIGHs, not a defang.
- **D3 scoped-path worst case — PASS.** Own control/audit evidence appends pass (G9
  audits-dir defect fixed; pattern covers a7_verdict.json/audit_log.md/nested);
  own-scope paths fire FORBIDDEN_PATH HIGH under a non-sanctioning explicit allowlist;
  HYPOTHESIS_LEDGER.md fires HIGH with default AND ['**'] override (protected
  classification is first and allowlist-independent); foreign code is not a finding and
  is listed.
- **D4 protected-global carve-out abuse — PASS_WITH_FINDING.** Fail-closed proven: no
  successor declaration → HIGH; only-malformed successors → HIGH; corrupt/missing
  registry → HIGH; non-ancestor (orphan) successor with no other cover → HIGH.
  F-R2-1 (LOW): a forged successor row in the canonical registry (working tree or
  committed) anchored ≥ the tamper suppresses the ledger HIGH for every row — registry
  content is the contract's trust root, so this is an authority-forgery boundary, not a
  classification bug; uncovered tampering always fires.
- **D5 redeclare abuse — PASS 11/11.** Backward / unrelated-orphan / nonexistent /
  malformed new anchors all refused with registry+journal bytes unchanged; undeclared,
  non-TERMINAL, and head!=anchor rows raise; identical redeclare is a no-op; forward
  migration moves head+terminal_anchor_sha together, touches nothing else, appends
  TERMINAL_IDENTITY_REDECLARED (from/to anchors). Repin loops structurally impossible:
  terminal_identity.py contains zero writer calls; a 3× validation loop at a moved tip
  left tip/journal/registry bytes byte-identical. Real precondition: 9aa9fd9b IS an
  ancestor of 85f39c3 — the sanctioned migration is forward-legal.
- **D6 audits-dir convention — PASS.** default_allowlist(V2R1) == exactly
  {control/market_data_plane_v2r1_run/**, audits/market_data_plane_v2r1/**, 3 registry
  surfaces}; V2 pair likewise; explicit audit_dir= wins; real research/audits/ carries
  no *_run directory; no pattern beyond the §12.2 minimal list.
- **D7 real history at tip 85f39c3 — PASS.** The 3 declared rows (V2R1@9aa9fd9b,
  V2@41bf9b1, V1@917b8749): ZERO findings each; foreign counts 5 / 90 / 143 (G9's 86/139
  HIGHs now informational; +4 explained by the two commits after d2416c3); V2R1's foreign
  list is exactly the 5 delta files; event-log prefix property holds on all three ranges;
  idempotent re-run identical.
- **D8 regression — PASS.** Six suites 152 passed / 0 failed (legacy_adapters 13,
  fixture_manifest 8, v9_universe_audit 27, terminal_identity 45, terminal_consistency 31,
  cycle_registry 28).
- **D9 historical immutability — PASS.** git diff 597e74c..HEAD restricted to
  research/control/market_data_plane_v2_run/, research/control/market_data_plane_v1_run/,
  research/audits/market_data_plane_v2/ is EMPTY.

## Findings

- F-R2-1 LOW (NO-BLOCK): forged-successor-row suppression of the protected-global guard
  (see D4); recommendation: resolve successor anchors from a pinned committed revision.
- F-R2-2 LOW (NO-BLOCK, pre-fix-identical): own-scope pattern set == default allowlist
  set, so under the default the own-scope HIGH can only surface via an explicit narrower
  allowlist param (as the shipped test does).
- F-R2-3 INFO (NO-BLOCK, prescribed): §12.3 "code change → FAIL HIGH" now holds through
  scoped ownership; enforcement of the new-anchor-after-A7 rule for foreign changes is
  procedural (this audit + the one forward-only redeclare).

## Verdict

**A7_AUTHORIZE_ANCHOR_MIGRATION** — high/critical count 0. The delta faithfully implements
the G9-prescribed contract, preserves every previously-catching HIGH, and authorizes the
single forward-only migration 9aa9fd9b → 85f39c3 via
cycle_registry.redeclare_terminal_identity, recorded as TERMINAL_IDENTITY_REDECLARED in
the canonical journal.

## Independence

A7-r2 wrote only research/audits/market_data_plane_v2r1/** (this section + the verdict
JSON). All attacks ran in /tmp/a7r2_delta synthetic repos; no network; no full tests/
run; heavy lock never acquired; worktree clean except this audit dir at commit.
