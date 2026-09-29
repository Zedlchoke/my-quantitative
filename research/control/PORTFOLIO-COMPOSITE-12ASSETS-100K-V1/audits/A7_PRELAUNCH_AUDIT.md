# A7_PRELAUNCH_AUDIT — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (2026-09-29)

Independent, fresh-context, read-only prelaunch audit of the frozen state
(registry phase "AWAITING A7 PRELAUNCH"). The auditor has never seen this
cycle's work before this session. Write scope (ONLY): this file +
`handoffs/A7_prelaunch.json`. No git operations, no network, no S1, no PnL
computation or estimation by the auditor. Read-only commands used: git
log/show/diff (both repos), pytest (root `.venv`), sha256/hash-chain
re-derivation, panel-manifest digest recomputation, disk spot-checks,
`researchctl.py locks inspect`.

Measured bases:
- ROOT `main @ b19723cd1714875a404d16c79b43426a09be3946` (dirty tree =
  owner's own SLEEVE-FX5/SANDBOX/SIXSOURCE paths only; NO file under this
  cycle's control dir is dirty — owner tree untouched).
- WORKTREE `.worktrees/portfolio-composite-12assets-100k-v1/integration`,
  branch `orca/portfolio-composite-12assets-100k-v1-integration` @
  `317d0838a756f08a1098d4fd32c9a897c0f58264`, tree clean, **no upstream
  configured** (no push ever possible from this branch as-is).

---

## D1 — AUTHORITY CHAIN: **PASS**

- Registration receipt
  (`plan/REGISTRATION_RECEIPT.md`, root control dir): owner GO
  `GO PORTFOLIO COMPOSITE 12ASSETS 100K V1 REGISTER PLAN …` consumed at
  `2026-09-29T10:56:39Z`; **A1 phrase ruling recorded** (typed form = full
  command head; plan-path suffix names a repo-unique object; both forms
  recorded). Scored GO separately REGISTERED_NOT_CONSUMED behind this audit
  (two-key, P-8). Receipt cross-checks against root `main` history:
  `65381730` (evidence, 44 files) → `013dda25` (registry write via
  researchctl, registry_sha256 `5a2ac29b…`) → `1ab53df0` (receipt) →
  `1c443d3b` → `b19723cd` — all present, control-plane-only files in the
  registry commits.
- Registry row (CYCLE_REGISTRY.json) vs measured reality:
  head `317d0838…` == measured worktree HEAD ✓; branch ✓;
  budget `{used:0, max:48}` ✓; `go_phrase_state: REGISTERED_NOT_CONSUMED` ✓;
  `s1: SEALED_UNTOUCHED` ✓; lifecycle ACTIVE_LIGHT ✓. The scored GO phrase
  string occurs ONLY in the plan and FREEZE (registered text), never as a
  consumed key.
- Plan registered copy vs control-dir draft: `diff` **byte-identical**
  (`plans/PLAN_portfolio_composite_12assets_100k_v1.md` ==
  `…/plan/PLAN_…_DRAFT.md`). Worktree control dir == root control dir for
  all shared files (diff -r: only worktree-only FREEZE/dry_run/IMPL/VERIFY
  and root-only REGISTRATION_RECEIPT differ by presence — consistent with
  the worktree branching at `65381730`, pre-receipt).
- Amendment recorded verbatim (Vietnamese owner text quoted) in
  `plan/AMENDMENT_OWNER_DIRECTIVE_2026-09-29.md`; its v2 ladder table (292)
  is superseded by ladder v2.1 (294) with the transition documented
  (LADDER_V1_APPENDIX.md + SESSION_REPORT) — audited chain, not a silent
  edit.
- No push/merge: branch has no upstream (`git rev-parse --abbrev-ref
  @{upstream}` fails); no merge commits in the lane chain; lane commits are
  additive on the registered base.
- One-Lead-session (P-17): claimed in FREEZE.md and receipt; not
  independently measurable from artifacts — recorded as disclosed, not
  verified (INFO-1).

## D2 — FREEZE INTEGRITY: **PASS** (one MEDIUM finding, F-1 below)

- Chain: FREEZE.md's `65381730` → `1b6e19dc` → `bfa51c2f` →
  `317d0838` == `git log` (full SHAs verified:
  `65381730b4689759…`, `1b6e19dc26de1a63…`, `bfa51c2f720156c1…`,
  `317d0838a756f08a…`). FREEZE commit carries exactly FREEZE.md +
  `dry_run/full_window/` (3 files, 35,808 insertions — journal is 35,504
  lines).
- Runtime pins: measured `tzdata 2026.3`, `python 3.12.14` in root
  `.venv` — matches FREEZE.md.
- Panel digests (independently recomputed, not taken on trust): per-pair
  aggregates rebuilt from `poolB/data_audit/panel_hashes_*.jsonl` using the
  audit script's exact recipe (`SIDE:date|bytes|sha256`, sorted, joined)
  reproduce `964abbac52132489…` / `9ffb0e4ba747de0c…` / `57b77f770b29690d…`
  and overall `d8d9807f…` **exactly**; 8 random files per pair re-hashed on
  disk == manifest (24/24 OK); panel roots (prior cycles' worktrees) exist
  and are read-only consumers. 12,552 files hashed ✓.
- Full-window journal: `sha256 = a6bde2cedc9de6202ef2d88b4ef9fca4
  404e734a5bd8083525181bdd6d6f49453` == FREEZE.md ✓; 35,504 rows ✓;
  hash-chain independently re-verified (see D3).
- SELECTION_FREEZE: 12 configs in `research/pc12a/legs_config/` ==
  FREEZE slate (9 VOLPROF VC1/VC2/VC3 × 3 pairs + USDJPY-S001 /
  GBPUSD-S027 / EURUSD-S009); `test_pc12a_arm_distinctness.py` enforces
  disk==in-code-defaults, 12/12 pairwise-distinct digests, digest purity,
  (family,mech,symbol) uniqueness, labels+cluster_ids, cluster map
  resolution (battery green).
- Fold calendar: `calendar_service.py` implements 286 = 52 + 8×26 + 26
  sealed with a hard guard that test folds cannot intrude the sealed tail
  (`fold_calendar()`, `SEALED_TAIL_WEEKS`); embargo is train-side
  (`train_end = fridays[test_start_idx-1-EMBARGO_WEEKS]`), swept in
  `test_pc12a_pit_joins.py` for all 8 folds incl. the Friday-20:00
  last-freeze bound.

## D3 — LEAK LAW (RGC-INC-1): **PASS**

Auditor's own scans (not the engine's claim):
- `dry_run/full_window/DRY_RUN_REPORT.json`: field-by-field read — only
  counts (decisions, votes, fills_by_outcome, blocked histogram), cost-bill
  totals (commission/slip/spread_once/swap — costs, not outcomes), digests,
  run metadata. No PnL/returns/equity/PF/Sharpe/drawdown field or value.
- `dry_run/full_window/journal.jsonl` (35,504 rows): key census over every
  row (76 distinct keys, all decision/fill/cost-bookkeeping) + regex scan
  for `pnl|profit|loss|return|equity|sharpe|drawdown|win_rate|expectancy|
  payoff|net_|gross_|performance|cagr|roi|mtm|…` → **0 hits**; raw-text
  grep → **0 hits**. Row kinds: HEADER 1 · DECISION 18,041 · NET_ORDER
  10,107 · SWAP 3,012 · NETTED_TO_ZERO 3,250 · BLOCK 367 · DEFER 363 ·
  TWIN 363 = 35,504 ✓. TWIN counterfactuals carry `would_*` **costs only**
  (no would-PnL) per GROUPING §4.2.
- Internal consistency: outcome histogram sum 14,087 == outcome-bearing
  rows (NET_ORDER 10,107 + NETTED 3,250 + BLOCK 367 + DEFER 363) exactly;
  per-leg decisions sum 18,408 == DECISION + BLOCK rows exactly; every
  per-leg/per-outcome count in the report matches the journal census. Note:
  the histogram deliberately does NOT equal `journal_row_count` (decision,
  swap, header rows are not outcomes) — the correct identity holds.
- Hash chain independently re-implemented and verified for BOTH journals
  (full-window 35,504 and smoke 965): every row self-hash and prev-link OK,
  including the hardened HEADER self-hash.
- Smoke journal (the superseded pre-fix artifact) also scans clean (chain
  OK, 0 leak hits) — matches the counter-test control
  (`test_committed_smoke_artifacts_scan_clean`).

## D4 — VERIFICATION BATTERY: **PASS**

- Ran myself, worktree, root `.venv`: `pytest tests/ -q -k pc12a` →
  **150 passed** (0 failed), matching FREEZE/VERIFY claims exactly.
- Full worktree suite: **2057 passed / 7 failed / 1 skipped (105s)** —
  matches the disclosed number; the 7 failures are all
  `tests/test_family_failures.py` registry-parsing tests, reproduced
  identically by me on ROOT `main @ b19723cd` (pre-existing at this base,
  untouched by this cycle).
- Truncation-replay test (`test_pc12a_truncation.py`): **substantive, not
  vacuous**. Real CLI runs over a full vs physically-truncated synthetic
  panel (OHLC preserved, volume zeroed from the cut minute, later days
  absent); per-symbol content-prefix identity for every row with lifecycle
  ≤ t_cut; raw BYTE-prefix over the leading contiguous block (>20 rows
  enforced); no-fabricated-rows proof tolerating ONLY the cut-day 22:00
  SWAP event; surgical-truncation byte proof; leg-level vote-prefix replay
  on fresh instances for all 12 real configs; non-vacuity floors (≥3
  decisions). The byte-prefix limitation (sequential symbol blocks) is
  honestly disclosed in VERIFY_battery known_limitations.
- PIT test (`test_pc12a_pit_joins.py`): **substantive**. Fold-embargo
  arithmetic all 8 folds; tzdata sweep across 14 DST seam dates 2021–2026
  with both regimes per year; 90s staleness at 89/90/91/3600s; poisoned
  FUTURE bar fails closed at BOTH layers (leg `on_bar` returns None;
  Eligibility returns OFF/E3 for future AND unparseable
  `available_time_utc`); FEATURES_BLACKLIST 18/18 with one poison per
  pattern AND a monkeypatch proof the gate runs inside every
  `Eligibility.evaluate`; swap-calendar sweep (≥250 weeks, Sun..Thu 22:00
  only, multiplier sum 7, Wed ×3, no Fri/Sat event); Friday-20:00 profile
  freeze truncation with poisoned post-20:00 prices.
- Bug fixes (read in code, each with a regression/counter test):
  1. `run_dry.py _process_day` — TR deque now advances bar-by-bar inside
     the decision loop (decision at minute m sees bars ≤ m); whole-day
     pre-pass retained only on warmup days where nothing is journaled.
     Correct and minimal; matches the disclosed root cause.
  2. `policy.py CostGuard.evaluate` — trailing window bounded
     `wstart < t <= now`; regression test proves a future-dated spend is
     invisible until time reaches it.
  3. `policy.py FROZEN_CLUSTER_MAP_PLACEHOLDER` — keys aligned to the
     frozen configs' cluster_id spelling (caps unchanged at 100,000);
     resolution test added.
  4. `journal.py verify_chain` — HEADER self-hash recomputed; header-tamper
     counter-test added.
  5. `legs.py VolprofLeg.on_bar` + `policy.py Eligibility` — symmetric
     fail-closed on future-dated data (two layers).
- Same-class sampling around the fixes (auditor's own review):
  - F-2 (LOW): `journal.py:121` `fields.setdefault("cash_delta_usd", 0.0)`
    injects a ZERO cash delta into BLOCK/DEFER/NETTED_TO_ZERO rows (TWIN
    inherits via the engine's DEFER fields), directly contradicting
    FILL_ACCOUNTING_SPEC §8 ("Fill fields are NULL (absent), never zero";
    `cash_delta_usd` is in `NULL_FILL_FIELDS`) and §7 (cash deltas belong
    on NET_ORDER rows — which do NOT carry the field). No leak and no
    accounting error in the dry run, but the letter of the law is inverted;
    must be fixed before scored per-bar reconciliation.
  - F-3 (LOW): `run_dry.py:441` writes outcome `"UNAVAILABLE_FILL_BAR"`,
    which is NOT in the frozen `OUTCOME_ENUM` — if that fail-closed path
    ever fires, `journal.write` raises instead of journaling the blocked
    row the spec requires (crash-closed, not journaled-closed).
  - INFO-2: `test_pc12a_pit_joins.py:235` asserts a dict literal it just
    built (`{"E3": "BLOCKED_STALE"}["E3"] == "BLOCKED_STALE"`) —
    decorative; the real mapping lives in `run_dry.py:334` (verified by
    code read).
  - INFO-3: FREEZE.md and the registry phase text say "3 lookahead/
    integrity bugs"; VERIFY_battery counts 5 defects (all disclosed
    per-file there). Understatement, not concealment.

## D5 — PIT/COST CONFORMANCE: **PASS**

- `cost_kernel.py` cells vs authorities (both read by auditor):
  C1 0.3/0.5 · 0.8/1.3 · 0.5/0.9 == COST_AUTHORITY_TABLE C1 (n=286/286 ×3,
  reproduced exactly by Lane D audit §D(ii)); C2_FRI 0.5/1.1 · 1.2/2.3 ·
  0.8/1.8 == table AND audit (exact); C3 5.9/9.0 · 13.4/23.8 · 11.0/22.0 ==
  table (audit §D(iv) corroboration); **C2_MON_THU 1.2/3.7 · 2.8/7.8 ·
  2.1/7.4 == the audit's CORRECTED (21:00,22:00] cells (n=65,109 / 65,274 /
  64,892)**, with the table's wrong-hour column (0.6/2.7, 1.4/5.8, 1.0/4.9)
  explicitly REFUSED in code comments + `dual_source_c2_doc()`. Dual-source
  law implemented as specified (erratum I-4).
- Spread-once law in code: ordinary fill = mid ± τ·(half-spread + slip
  band); the two attribution lines (spread_once_usd = |quoted−mid|·|Δ|,
  slip = |fill−quoted|·|Δ|) sum to |fill−mid|·|Δ| exactly at every tier;
  graded worst-fill keeps the measured spread and books excess inside the
  slip line; window fills use S_eff = max(cell p90, C1 p90) × τ + 1.0-pip
  event slip. Counter-tests trip on tampered cost fields via chain AND the
  identity.
- Swap calendar: Sun–Thu 22:00 UTC events only, Wed ×3, Fri/Sat none
  (code + ≥250-week sweep test); accrual valued at the last tradable bar
  ≤ 22:00 (PIT); charged against, never income; JPY pip value converted at
  the accrual-bar mid (disclosed in report notes).
- Fold calendar arithmetic: 286 = 52 + 8×26 + 26 sealed, verified in code
  with guards and in tests (see D2).

## D6 — PROTOCOL CONFORMANCE: **PASS** (INFO notes)

- Journal vs JOURNAL_SCHEMA.md: decision-time block fields present on all
  22,384 decision-family rows (ts/fold/cycle/sleeve/leg ids,
  feature_pit_snapshot with input_id/available_time_utc/value_digest/
  max_age_ok, direction_vote, desired_risk_units, entry_reason_code,
  eligibility/risk/portfolio state, GROUPING §4.2 additions); frozen
  outcome enum matches the schema; blocked rows carry decision-state only.
  INFO-4: rows use `leg_id` where the schema names `corpus_gid`/
  `class_candidate_id` (identity preserved — leg_id IS the gid/candidate
  id); no `fx_conversion` field (JPY conversion disclosed as a note);
  NET_ORDER lacks the §7 cash-delta field (folded into F-2).
- FEATURES_BLACKLIST (18 regexes) covers all six GROUPING §3.6 forbidden
  categories with one poison per pattern and a live-gate proof; INFO-5:
  patterns are anchored — mid-string evasions (e.g. `x_forecast_y`) would
  slip past the regexes; enforcement today is pattern + review.
- Policy skeleton: L1–L7 implemented per PORTFOLIO_POLICY_ARCHITECTURE §1
  layer map (pool/eligibility/targets/netting/risk-budget/execution/
  standing-out); L5 cluster caps, L6 guard/E4 caps are declared frozen
  PLACEHOLDERS to be re-frozen at Stage-B — disclosed in code, FREEZE and
  IMPL handoff.
- Leg configs: all 12 carry non-empty `outcome_exposed_label` +
  `cluster_id` (amended labeling duty), verified by schema test and
  spot-read (e.g. EURUSD-S009 `F0_INDIVIDUAL_REJECT`,
  VC1-VAEDGE-USDJPY `CLASS_CANDIDATE_ANCESTRY_RHO_LABELLED`).

## D7 — BUDGET/DENOMINATOR: **PASS**

- Registry `budget {used:0, max:48}`; 48 = Stage-C scored IDENTITY cap;
  B4 random battery (≤128 seeded sub-runs, ONE identity) on its own
  disclosed line per PASS_BARS_V2 **E-Law 8** (§Budget counting unit) and
  plan §4 table and the registration receipt. Counting-unit law verified
  in the policy doc read.
- Scored-artifact sweep (worktree + both control dirs): no TRIAL_LEDGER,
  no scored/discovery output, no PnL-bearing artifact of this cycle
  anywhere. The only PnL-adjacent content: (a) `journal/fixtures/fx*.json`
  hand-computed SPEC vectors on synthetic paths (pre-GO design evidence,
  skeptic- and A7-prereview-verified at 1e-9/1e-12) — not scored
  computation; (b) `research/pc12a/books.py` computes `net_pnl_usd` as the
  fixture-replay/accounting library — it is imported ONLY by tests;
  `run_dry.py` does not import it and the dry-run outputs are leak-clean.
  0 scored cells; S1 SEALED_UNTOUCHED; heavy lock FREE_PROVEN (measured).

## D8 — HONEST DISCLOSURE: **PASS** (F-1 filed)

- The caught defects are disclosed per-file with reasons/consequences
  (`VERIFY_battery.json changed_paths.engine_edits_disclosure`, 5 entries)
  plus incidents and known limitations (byte-prefix scope; tolerated
  cut-day SWAP row; macro joins NOT_RUN with negative assertion; leg-level
  replay thinness for rare-trigger legs).
- Superseded smoke: disclosed in VERIFY_battery known_limitations (pre-fix
  ATR semantics, scans clean, must not be treated as reproducible) and
  used as the clean control in counter-tests. BUT see F-1: FREEZE.md's
  smoke paragraph describes a POST-FIX smoke ("863 journal rows … two runs
  byte-identical") whose artifacts are NOT committed anywhere, and the
  FREEZE commit message claims "Superseded pre-fix smoke artifacts
  removed" while they remain at HEAD (`research/pc12a/smoke_dry_run/`,
  965 rows, byte-identical to `1b6e19dc`). The determinism LAW is still
  separately covered by the green `test_dry_run_deterministic_and_clean`.
- VC1 zero-fire: visible in the committed report (VC1 decisions 0/2/0
  across the three pairs) and called out in FREEZE as a Stage-A floors
  question, not a tuning invitation ✓. Honest feasibility counts also
  visible (USDJPY-S001: 3 decisions in 5.5y — will fail the 20-decision
  floor at Stage-A as designed).
- Open items disclosed: L5/L6 Stage-B freezes (placeholders named in code),
  H1 panels not consumed by slate v0 with their entry path, per-bar
  reconciliation + reproduction twin assigned to the scored stage.
- Commit inventory audit (git show --stat of all four lane commits): no
  surprise files — evidence commit = 44 control-dir/plan files; impl = 8
  engine modules + 12 configs + 8 test files + smoke; verification = 4
  test files + 4 minimal engine diffs + handoff; freeze = FREEZE.md +
  dry_run artifacts.
- Pre-existing 7 test failures disclosed and independently reproduced at
  base (root main) — not this cycle's.

---

## Findings (severity, evidence, remediation)

**F-1 (MEDIUM — evidence traceability of the freeze smoke).**
FREEZE.md §"Sanitized exact-arm dry-run" states "Smoke (8w, post-fix): 863
journal rows, leak-scan clean, two runs byte-identical (determinism proven
post-fix)" — no such artifact exists in the tree (the only committed smoke
is `research/pc12a/smoke_dry_run/journal.jsonl`, 965 rows, sha256
`41e1202be3cce8528ce462051657d1d5a51724a0d5b8acd02bb0a6841d403e3a`,
byte-identical to impl commit `1b6e19dc`, i.e. PRE-fix). The FREEZE commit
message further claims "Superseded pre-fix smoke artifacts removed" —
measured false (still present at HEAD `317d0838`). No integrity impact
(artifact scans clean; supersession honestly disclosed in
VERIFY_battery.json known_limitations[3]; determinism law separately
tested green) — but a freeze document must not describe unpinned evidence
nor claim a removal that did not happen.
Remediation (before owner GO #2, cheap): either commit the post-fix smoke
into a clearly named directory (e.g. `smoke_dry_run_postfix/`) and pin its
sha256 + row count in a FREEZE addendum, or issue a FREEZE erratum
correcting the smoke paragraph and the commit-message claim; delete or
rename the superseded pre-fix artifacts so the tree matches the words.

**F-2 (LOW — letter violation of FILL_ACCOUNTING_SPEC §7/§8 on cash
deltas).** `research/pc12a/journal.py:121`
(`fields.setdefault("cash_delta_usd", 0.0)`) makes BLOCK/DEFER/
NETTED_TO_ZERO (and, via the engine's DEFER fields, TWIN) rows carry
`cash_delta_usd: 0.0` — the committed journal census confirms 4,343 such
rows — while the spec requires fill fields "NULL (absent), never zero" on
those rows and requires cash deltas on NET_ORDER rows (which have none).
Remediation: before any scored run (per-bar reconciliation law), remove
the setdefault (emit absent/None) and add the cash/position deltas to
`net_order_row` per §7, or write a spec erratum if 0.0 is intentional.

**F-3 (LOW — unreachable journaled outcome).** `run_dry.py:441` uses
outcome `UNAVAILABLE_FILL_BAR`, absent from the frozen `OUTCOME_ENUM`
(`journal.py:38-47`) — that fail-closed path would raise `JournalError`
instead of journaling the blocked row the spec (FILL_ACCOUNTING_SPEC §4)
requires. Never fired in the full window (no such outcome in the
histogram). Remediation: add the value to the enum (or map the path to
`BLOCKED_STALE` with detail `UNAVAILABLE_FILL_BAR`) with a test.

**INFO-1** One-Lead-session (P-17) and "no S1 reads" are claims, not
independently measurable from artifacts; everything cross-checkable does
check out. **INFO-2** decorative tautology at
`tests/test_pc12a_pit_joins.py:235`. **INFO-3** "3 bugs" (FREEZE/
registry) vs 5 defects (VERIFY handoff) — understatement, all disclosed.
**INFO-4** `leg_id` vs schema's `corpus_gid`/`class_candidate_id` naming;
no `fx_conversion` field. **INFO-5** blacklist regexes are anchored
(mid-string evasion possible; enforcement is pattern + review).
**INFO-6** `audit_summary.json` digest method-string documents the
OVERALL line format for the per-pair aggregates too (per-pair lines omit
the pair prefix per `audit_scripts.py:336-342`); recomputation with the
code recipe matches exactly.

## Severity counts

CRITICAL 0 · HIGH 0 · MEDIUM 1 · LOW 2 · INFO 6

D-checklist: D1 PASS · D2 PASS · D3 PASS · D4 PASS · D5 PASS · D6 PASS ·
D7 PASS · D8 PASS (with F-1 filed). No dimension FAIL, no NOT_RUN except
the explicitly claimed-only items in INFO-1.

The scored GO remains REGISTERED_NOT_CONSUMED; if the owner issues it, it
is typed fresh at the scored gate after this verdict (two-key, P-8).

A7_PRELAUNCH_VERDICT: AUTHORIZED_WITH_FINDINGS
