# A7-1 Round-r1 DELTA re-audit — JEV-REGIME-ROUTER-V1

- Auditor: ROLE A7, independent fresh context (no lane context reused).
- Date: 2026-09-22T05:06:28Z
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/jev-regime-router-v1/integration`
- Branch: `orca/jev-regime-router-v1-integration`
- Audited HEAD: `ea09f1de09a1d81a7a811a96887d7e4f2d0385b9`
- Round-1 baseline: `873634dc` (verdict REFUSED_WITH_ACTIONS, findings F1 CRITICAL / F2 HIGH / F3 HIGH / F4 MEDIUM / F5-F8 LOW)
- Remediation: `1a779f19` (content-identical cherry-pick of `orca/jrv1-remediation-r1` `b8fcd6e1` — `git diff b8fcd6e1 1a779f19` EMPTY, verified); handoff landing `ea09f1de` adds only `handoffs/remediation_r1_handoff.json`.
- Machine-readable artifact: `audits/a7_1_r1_delta_audit.json` (schema `jrv1_a7_1_r1_delta_audit@1`)

## VERDICT: AUTHORIZED_FOR_STOP1_REPORT

All four blocking findings REMEDIATED with independent evidence; zero unresolved
CRITICAL/HIGH; the four round-1 LOW findings remain open and non-blocking. No new
issues introduced by the remediation.

## Per-finding

### F1 (CRITICAL → REMEDIATED) cross-language input_digest divergence

- `freezes/adapter_contract.json` now carries `amendment_1` (dated
  2026-09-22T04:30:09Z): input_digest is computed ONLY by the Python producer and
  echoed verbatim by the TS adapter; the adapter MUST NOT recompute.
- SHA chain verified independently: `old_sha256 334515b7…` recomputed from the
  873634dc blob = exact; `new_sha256 a1893fde…` recomputed from HEAD bytes = exact;
  preserved in the manifest's append-only `amended` list.
- Code: `computeInputDigest` removed from the adapter's production import; every
  response path (mock / OK / SCHEMA_ERROR / provider-error / LOCAL_INVALID) echoes
  the request digest; cache key derives from the echo; `validateRequestLine`
  requires 64-lowercase-hex (missing, uppercase, short, typo → refused, no call,
  no cache entry). The legacy function survives only for golden tests.
- Golden file re-run standalone: 3/3 pass; its 3 Python-side constants
  (canonical strings + sha256) independently reproduced by the Python producer
  authority: 3/3 exact.
- **Auditor's own fresh check** (not lane vectors): 30 random feature vectors
  (seed 20260922) with magnitudes forced into the exponent-notation divergence
  window, request lines built with producer digests, `node src/adapter.ts --mock`:
  **30/30 echo-match** on Python recompute from stored states, **0 ingest
  violations** via `validate_response_line`, **30/30 cache entries** echo- and
  key-correct. Teeth: the same 30 states under the LEGACY TS recompute mismatch
  **30/30** — every vector sits in the old divergence window and the echo law
  carries all of them.

### F2 (HIGH → REMEDIATED) no legal bulk mechanism for sequential states

- `jrv1/replay.py` read end-to-end: strict in-order state iteration;
  prior_regime = persisted regime recomputed after EVERY merged response; one
  request line (with producer digest) and one adapter subprocess per state;
  cache-first resume with re-validation against the current recomputed digest
  (stale line → incident, fail-closed); hard fail on adapter non-zero exit and on
  wrong response-line count; decision store append-only.
- `prepare-requests` bulk mode REFUSED (reproduced live; error names A7-1 F2 and
  points to `replay`); `--fixtures-only` emits exactly 5 producer-digested canary
  lines (FIX6 null vector never serialized).
- **Auditor's own run**: `replay --asset spy --limit 25 --mock` from a clean
  runtime — run 1: 25/25 sent, 0 incidents, 0 digest mismatches, bar indices
  strictly increasing from 192, prior chain exact (each prior == previous
  persisted_after). Run 2 (resume): **0 new adapter calls**, 25/25 cached, 0
  incidents, 0 mismatches, identical persisted/status sequence. 25 adapter cache
  entries, 25 decision lines on disk.

### F3 (HIGH → REMEDIATED) fold gaps / boundary-spanning positions / non-reconciling attribution

- Engine: contiguous exec-bar partition; entry fills and signals refused on
  unassigned bars; hard in-loop assertion (no position open on an unassigned
  bar); post-run invariants — every invested bar carries a fold, every trade
  inside its fold's range, `sum(fold_net_pnl) == totals.net_pnl` within 1e-9;
  `fold_partition_invariants` wired into `build_context`.
- **Independent recomputation on BOTH real datasets** (partition/labeling only;
  no arms, no PnL):
  - BTCUSDT (35039 exec bars): `[0,774,9341],[1,9342,17909],[2,17910,26477],[3,26478,35038]`
    — exact-once coverage from the first post-warmup exec bar (774) through the
    final bar; the 13 previously-unassigned bars (4 per boundary ×3 + final bar)
    are now owned by the preceding fold.
  - SPY (2943): `[0,193,880],[1,881,1568],[2,1569,2256],[3,2257,2942]` —
    exact-once; first post-warmup exec bar 194 covered; the 3 previously-unassigned
    sessions now owned by the preceding fold.
  - Fold STARTS (decision boundaries) are IDENTICAL old-vs-new on both assets —
    only ownership of the gap bars changed.
- `freezes/fold_contract.json` bytes UNCHANGED: sha256 `ac658c50…` recomputed at
  both 873634dc and HEAD; frozen decision counts intact (BTC 8567 = 2142+2142+2142+2141;
  SPY 2751 = 688+688+688+687).
- Reconciliation identity test exists and is honest:
  `test_f3_gap_pattern_reconciliation_and_no_span` uses SYNTHETIC rising bars
  (BTC-like multi-bar gaps and SPY-like single-session gaps), asserts
  reconciliation ≤1e-9 + no-span + full assignment, and proves the OLD gapped
  partition now hard-fails the partition invariant. No real-data PnL involved.

### F4 (MEDIUM → REMEDIATED) plan §9 projection arithmetic

- §9 now quotes the frozen exact numbers: BTCUSDT 8,567 + SPY 2,751 = 11,318
  (arithmetic checked; addends match `fold_contract.json` `evaluable_decisions`
  re-read at HEAD) plus the amendment sentence. `git diff 873634dc..HEAD -- plans/`
  contains exactly this one hunk.

### F5–F8 (LOW → OPEN, non-blocking)

- F5: engine docstring still says BUY_HOLD "enters … at the first exec bar open";
  actual fill is the next open after the fold-start close signal. Open LOW.
- F6: BTC funding reference-price approximation still undisclosed in
  `cost_contract.json` (file untouched). Open LOW.
- F7: adapter cache-hit replay still does not re-check `response.model == pin`
  (Python re-enforces at scoring; replay re-validates digest+pin). Open LOW.
- F8: ddof=0 convention still not pinned in `feature_contract.json`. Open LOW.
- The remediation handoff explicitly declares these out of scope; per dispatch
  they do not block.

## Scope-creep review (full diff 873634dc..HEAD, 17 files, +1470/−69)

No out-of-scope change. Nothing touches strategies, mapping, persistence params,
features, cost, or fold bytes. Allowed changes only: `adapter_contract.json`
(amendment_1) + `freeze_manifest.json` (digest + amended list); plan §9 hunk;
F1/F2/F3 code + tests; new `jrv1/replay.py`; handoff artifact. TS freeze gate
(`freeze_digests.ts`) unchanged and passing. Verify-freezes 12/12.

Observation (disclosed, protocol-consistent, not a new issue): the remediation
lane ran real-data smoke (arm D, BTC+SPY) post-freeze to confirm 0 incidents
after the fold-law change — kill-only namespace (P-15), counts-only disclosure
consistent with INCIDENT-JRV1-1 (OBSERVED counter); no PnL in any committed
artifact and none quoted here.

## Tests recounted by the auditor at HEAD

| Check | Result |
|---|---|
| pytest tests_py | 110 passed / 0 failed / 6 warnings (degenerate-fixture numpy warnings, same profile as round 1) |
| adapter node --test | 63 pass / 0 fail; tsc --noEmit clean |
| golden digest file standalone | 3/3 pass |
| verify-freezes | 12/12 MATCH; mapping digest asserted; security scan 0 findings |
| census BTC | 35039 rows / 0 interior gaps / 8759 complete H1 / 2 partial edge — unchanged |
| census SPY | 2943 sessions — unchanged |
| own 30-vector cross-language check | 30/30 echo, 0 incidents; legacy recompute diverges 30/30 |
| own 25-state replay ×2 | run1 25 sent / 0 incidents; run2 0 new calls / identical sequence |
| own partition check, both assets | contiguous, exact-once, boundaries preserved, freeze bytes sha-equal |

## Constraints

No real-data arm backtest was executed; the backtest subcommand was not invoked
(quarantined). Mock-only executions (adapter `--mock`, replay `--mock`) plus
partition/labeling computations on real exec bars. No PnL numbers are quoted in
this artifact — counts and invariants only. Auditor writes confined to
`research/control/jev_regime_router_v1/audits/`.
