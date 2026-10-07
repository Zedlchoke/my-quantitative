# A7 FINAL VERDICT — SPORTS-PAPERTRADE-EXEC-V1 (post-rewire HEAD)

A7-role, fresh context, audit-only. Audited at the post-rewire HEAD; attempted to
REJECT. Nothing repaired.

- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/sports-papertrade-exec-v1/integration`
- Branch: `orca/spt-exec-v1-integration`
- Measured HEAD: `551bf17c39b4eed9bf449e92cc436104ee48e0ba` == claimed; tree clean
  before and after all my runs; no upstream (`branch -vv`).
- Heavy lock at audit time: `FREE_PROVEN` (researchctl locks inspect).

## VERDICT: **PASS_WITH_FINDINGS** (0 CRITICAL / 0 HIGH / 1 MEDIUM / 1 LOW / 2 INFO)

The one owner GO `GO SPORTS PAPERTRADE EXEC V1 RUN ALL` lawfully opens NBA +
WNBA-2026-remainder + SOCCER paper capture at this HEAD, with one MEDIUM
operational finding (F1) on which registry copy the GO consumption must reach —
fail-closed in every direction, disclosed below.

---

## 1. NBA unblock — VERIFIED

- **Lazy import**: `adapters.nba_engine_predict` → `nba_engine_modules`
  spec-loads `research/papertrade_nba/loader.py` then `predict.py` from the
  pinned `nba26` root at call time; no module-level import of the nba26 package
  anywhere. Entry/drift checks (BLOCKED_NBA_ENTRY / BLOCKED_PIN_DRIFT) run
  BEFORE any corpus touch (battery-enforced).
- **Bytes re-hashed by me** (shasum -a 256) at the NBA-prep worktree measured
  HEAD `82542aa8e97206b88f7eb777f4461b09054e9b09` (branch
  `orca/nba-winprob-prospective-prep-v1-integration`, clean):
  `loader.py` = `2679be80f1fb7f7d9862f76b65e546708aac3df6654fa7e8d866aedecd6461c8`,
  `predict.py` = `57f0c810f8cd1a12d78bcb68881ca49b6d8bdb16a4a0f61a11dfcc7987c6d81c`
  — equal to pins.json and to the dispatch claim. verify-pins at HEAD: drift []
  , self_head == 551bf17c…, all 16 file pins + 3 data pins OK, exit 0.
- **Bind path DEAD**: `adapters.nba_real_corpus_read` (adapters.py:616) has
  zero callers — worktree-wide grep finds it only at its definition and in
  docs/handoffs/erratum. `real_loader`/`outcome_bind`/`load_oos_corpus`
  references on the real path: none. `nba_engine_replay_synthetic` is called
  only from `tests/papertrade_exec/test_exec_battery.py` on `SYN-*` inputs
  (zero real outcomes); the `nba_harness` pins are annotated
  RETAINED-FOR-BATTERY-ONLY. The scored worktree
  (nba-winprob-ng-scored-v1) is CLEAN — its bind law untouched.
- **Rehearsal** (`rehearsal/exec_nba_rewire_rehearsal.json`): 8 REAL fixtures
  for tip-UTC window 2026-10-20..21 — I independently re-ran the read-only
  window loader and got the same 8 match_ids (401909088/89/90/91,
  401909834/35/36/37, earliest tip 2026-10-20T19:00:00Z → batch anchor
  `2026-10-20T12:50:00Z` = T0−6h10m). All persisted rows `mode=SYNTHETIC`,
  `model_version_sha=SYNTHETIC_ADAPTER_NOT_ENGINE`; engine p (0.640065 =
  1/(1+10^(−100/400)), completed=0 ⇒ R0=1500) IN-MEMORY ONLY; census
  GENESIS 1 / FORECAST 8 / MARKET_QUOTE 8 / DECISION 8 (2 BET_PAPER + 6
  NO_EDGE) / SETTLEMENT 2; dashboard SANDBOX banner + `chain_ok: true`;
  refresh step NOT executed pre-GO (frozen snapshot verified 208/208).

## 2. Battery + sibling suites — VERIFIED (counts: 36/79/94/81, total 290)

| Suite | Where | Result |
|---|---|---|
| tests/papertrade_exec | EXEC worktree | **36 passed** (9.34s) |
| tests/papertrade_wnba26 | wnba-2026-remainder-v1 | **79 passed** (0.60s) |
| tests/papertrade_soccer | soccer-intl-winprob-prospective-prep-v1 | **94 passed** (3.23s) |
| tests/papertrade_nba | nba-winprob-prospective-prep-v1 | **81 passed** (0.65s) |

`git status --porcelain` EMPTY on all five worktrees (EXEC + 4 siblings)
after my runs.

## 3. One-GO law — VERIFIED (with F1)

- Single live phrase: `GO_PHRASE = "GO SPORTS PAPERTRADE EXEC V1 RUN ALL"`
  (`__init__.py:22`) is the only phrase constant in
  execute.py/adapters.py/__init__.py; `exec_go_state` enforces VERBATIM
  equality (`!=` refuses). Retired lane phrases are accepted nowhere —
  battery `test_refuse_wrong_go_phrase` uses a retired phrase and expects
  exit 3; registry holds the three siblings' own phrases
  REGISTERED_NOT_CONSUMED at their own (untouched) gates.
- Two-key gate: token (`go_phrase_typed_by_owner` == phrase + provenance
  fields) AND registry row phase containing GO_CONSUMED. **My own tmp
  rehearsal** (fresh tmp dirs): real-mode `run-day` → **exit 3**
  BLOCKED_NO_GO "GO_TOKEN.json absent"; sandbox matrix — retired phrase +
  consumed registry → 3; right phrase + unconsumed registry → 3; no token +
  consumed registry → 3; both keys → 0 (two-key accept proven).
- Registry (read-only): ROOT `plans/CYCLE_REGISTRY.json` EXEC row head ==
  `551bf17c39b4eed9bf449e92cc436104ee48e0ba`, `go_phrase_state`
  REGISTERED_NOT_CONSUMED, phase READY_PENDING_ONE_OWNER_GO pending final A7
  (NBA rewired…). **Zero rows with GO_CONSUMED among all 115 cycles.**
  Sibling heads measured == registered, exact:
  sports-papertrade-v1 `8105e878ec6c…`, wnba-2026-remainder-v1
  `46200b30c0db…`, nba-winprob-prospective-prep-v1 `82542aa8e972…`,
  soccer-intl-winprob-prospective-prep-v1 `1ca5cd7ded19…`.

## 4. Data-contract legality — VERIFIED

- **ESPN-only**: loader.py header + code read ONLY
  `scoreboard_*.json` under `~/.my-quantitative-data/nba-winprob-prospective-prep-v1/espn_schedule_2026_27/`
  (208 payloads + 208 .meta, no REFRESH_MANIFEST.jsonl pre-GO — pristine
  frozen state; composite pin 3d527b3c… verified by verify-pins at HEAD via
  the manifest-aware `nba_payload_verdict`).
- **Refresh refuses pre-GO**: `nba_incremental_refresh` raises
  BLOCKED_NO_GO unless `go_ok` (defense-in-depth behind the gate) and
  refuses a corpus that does not verify BEFORE refreshing;
  battery `test_nba_refresh_prego_refused_and_postgo_manifest_chain` covers
  both plus the self-hashed chain on a fake fetch (no network).
- **Completed-only carry law, two layers**: loader `load_completed` = FINAL
  only, tip STRICTLY < anchor; `replay_completed` re-filters tip >= anchor
  defensively; battery injects FINAL rows with tip > anchor AND tip ==
  anchor into a resealed copy and asserts neither `p` nor `state_digest`
  moves (`test_nba_outcome_leak_injected_completed_row_ignored`).
- **Warm-up carried**: R0=1500 = "2016-17 season-start value, carried from
  the successor packet pre-registration"; the packet quote exists —
  NBA-prep `FREEZE_ADDENDUM_PIT_LOADER.md` line 55: "WARM-UP (streams run,
  never scored): NBA seasons 2016, 2017."
- **Slope disclosure verbatim**: "pooled OOS F1–F5 2022–2026 LL 0.639953,
  Brier 0.223545, n=6,605; calibration slope 0.8107 BELOW [0.85,1.15] —
  overconfidence sign; NO recalibration on viewed OOS" present in
  ERRATUM_NBA_REWIRE.md §4 (this worktree) and in NBA-prep
  FREEZE_PACKET.md §2 + FREEZE_ADDENDUM_PIT_LOADER.md §7.
- **No refit**: grep for fit/optimize/calibrat/recalibr over EXEC package and
  nba26 package returns only "NEVER re-fit" comments — zero fitting code.

## 5. Zero real rows pre-GO — VERIFIED

No GO_TOKEN.json anywhere in the worktree (find: zero hits); the only
GO_TOKEN is the labeled SANDBOX fabrication under
`~/.my-quantitative-data/sports-papertrade-exec-v1/sandbox/control/`. The
only ledger file is `sandbox/sandbox_ledger.jsonl` (57 rows, GENESIS
sandbox=True, all 36 FORECAST/MARKET_QUOTE rows mode=SYNTHETIC, zero
ENGINE/REAL rows). No `ledger/` dir exists. `runs/` holds exactly one file:
the REAL-mode pre-GO refusal record (BLOCKED_NO_GO JSON, zero rows) — gate
evidence, not data. Real-mode mutation refuses pre-GO (rehearsed by me,
exit 3). No real GENESIS ledger anywhere.

## 6. Boundary + lock — VERIFIED

`git log bc391b0c..HEAD` = exactly 2 commits (01e8bc1a, 551bf17c); name-only
file list: `research/papertrade_exec/*` (5), `tests/papertrade_exec/*` (1),
`research/control/SPORTS-PAPERTRADE-EXEC-V1/*` (4) — nothing else. Branch
`-vv`: no upstream. Locks FREE_PROVEN before and after.

---

## Findings

- **F1 MEDIUM (GO mechanics — which registry copy):** the real-mode gate
  reads THIS worktree's mirror of `plans/CYCLE_REGISTRY.json`
  (`REGISTRY_PATH` in `__init__.py`, frozen at the branch point, EXEC row
  phase "REGISTERED (planned)", head 000000000000). I demonstrated
  (read-only, tmp token copy + real worktree registry path):
  `exec_go_state` refuses with "registry phase 'REGISTERED (planned)' does
  not record GO_CONSUMED" even with a verbatim-correct token present.
  GO consumption via the canonical ROOT researchctl updates only the root
  copy; the packet's step 1 (`researchctl cycle update --phase …`) does not
  say which copy, and AGENTS.md documents researchctl from the ROOT. Until
  the registry copy the gate reads records GO_CONSUMED, `run-day` refuses
  (exit 3) with a self-explanatory message. Fail-closed in every direction —
  no unlawful opening is possible; zero data risk; hence MEDIUM, not HIGH.
  Remediation (one line, owner/controller side, not this audit): the GO
  consumption step must update the registry copy the gate reads (run
  researchctl from the worktree, or sync the root copy into
  `<wt>/plans/`), or the gate's real-mode registry read should point at the
  canonical root path. OWNER_GO_PACKET.md step 1 should say which.
- **F2 INFO (advisory head drift):** pins.json records lane-time dispatch
  heads for the four siblings; all four worktrees have legitimately
  advanced since. `matches_dispatch_head=False` in verify-pins is by design
  ("binding identity is the file bytes") and all 16 byte pins + 3 data pins
  verify OK; the ROOT registry is reconciled to the measured heads, exact.
- **F3 INFO (`--worktree` flag inert):** the runner parses `--worktree` but
  CONTROL_DIR/REGISTRY_PATH are module constants derived from `__file__`;
  the flag changes nothing.
- **F4 LOW (stale packet row):** OWNER_GO_PACKET.md's NOT_RUN table still
  says NBA = BLOCKED_NBA_CORPUS_BIND "NOT fixable by this GO" — written
  pre-rewire (commit bc391b0c) and not updated by the rewire lane (its
  pathspec allowed it). It contradicts the same packet's cadence bullet
  (NBA first eligible 2026-10-20) and is superseded by
  ERRATUM_NBA_REWIRE.md + the root registry phase. Fail-safe direction
  (understates capability; cannot cause capture). Should be corrected
  before the GO is typed so the Owner reading list matches the wired
  reality.

## Final statements (dispatch-mandated)

**(a) ONE GO truly opens all three league paths lawfully — AFFIRMED.**
Single phrase, two-key gate, byte-pinned fail-closed wiring for all three
leagues (NBA ESPN-PIT, WNBA Lane B entry, SOCCER Lane C entry), zero
GO_CONSUMED anywhere pre-GO, zero real rows. Lawfulness is unconditional;
F1 means the controller chain must update the registry copy the gate reads
or the gate stays closed (refusal, never an opening).

**(b) NBA BLOCKED_NBA_CORPUS_BIND is RESOLVED — AFFIRMED.** The bind path is
dead and unreachable (no caller; battery-only synthetic replay retained and
inert on the real path); the NBA real path reads only the frozen ESPN
payloads under the nba26 pins; the scored cycle's bind law and worktree are
untouched; gates untouched.

**(c) WNBA-2027 remains OUTSIDE this GO — AFFIRMED.** WNBA-WINPROB-PROSPECTIVE-PREP-V1
keeps its own untouched phrase `GO WNBA WINPROB PROSPECTIVE V1 PREDICTIONS`
REGISTERED_NOT_CONSUMED at its own gate; the EXEC gate accepts only the one
phrase (refusal test-enforced and rehearsed by me).

**(d) Soccer missing-1X2 = per-match NOT_RUN — AFFIRMED.** A quote without
the DRAW leg journals the match NO_QUOTE "missing required legs"
(battery test) — a data gap decision, not an engine blocker (Lane C entry
WIRED_ENGINE_READY, 94/94).

**(e) Missed WNBA anchors = NOT_RUN forever — AFFIRMED.** `check_anchor`
refuses the whole batch at/after the anchor ("NOT_RUN forever, no
backfill"), nothing written.

**(f) Zero real paper rows — AFFIRMED.** Evidence in §5.

**(g) No technical step remains for Owner after typing the phrase —
AFFIRMED with F1 disclosed.** The Owner only types the phrase; the
controller chain (transcribe token, consume GO in the registry, run the
cadence) is pre-built and rehearsed. F1 is a controller-chain
under-specification (which registry copy to consume), not an Owner step.

## Decision

A7 FINAL: **PASS_WITH_FINDINGS**. No unresolved HIGH/CRITICAL. The cycle is
lawful to open with the ONE GO at this HEAD; resolve F1 (one-line packet
clarification or equivalent controller instruction) and F4 (packet row
refresh) in the owner/controller plane — audit-only, not repaired here.
