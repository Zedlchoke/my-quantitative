# STOCKS-FREE-V3 Terminal Audit — A7T (independent, verify-only)

**Date (UTC):** first pass 2026-09-03T16:11:29Z @ `deba0838`; **re-audit 2026-09-03T16:20:20Z @ `3251554` (final)**
**Worktree:** `.worktrees/stocks-free-v3/r-a7-terminal` (branch `orca/stocks-free-v3-r-a7-terminal`)
**Interpreter:** `/Users/hoangminhlong/my-quantitative/.venv/bin/python` only. Read-only on r-reproduce / e-exec-1. No network. No S1 reads. Nothing repaired.

---

## TERMINAL VERDICT (final, after verified A1 remediation)

```
STOCKS_FREE_V3_REJECT_ALL_CONFIRMED
```

Supersedes the first-pass verdict `STOCKS_FREE_V3_INCOMPLETE_NOT_PROMOTABLE`, which documented blocker **A7T-B1** (ledger digest column). A1 applied the prescribed remedy at HEAD `3251554d3fb12d54c52bca661440fe38be74e8ec` (cherry-pick of `aa6e79c`, parent = the originally audited `deba0838`); the re-audit below verifies it. **Blockers: none.**

### Re-audit (measured_utc 2026-09-03T16:20:20Z, HEAD `3251554`)

- **A — ledger repin: PASS.** Six append-only `ARTIFACT_DIGEST_REPINNED` entries; each `artifact_sha256_of_published_bytes` equals the recomputed sha256 of the exact published file bytes — **6/6 match** (`c7fc474c…`, `238b220e…`, `f4a03e6b…`, `1faf15f1…`, `5e8e03a5…`, `168164f4…`). Prior rows untouched, proven byte-exact: the ledger's **first 24 entries are identical to the git `deba0838` version** (18 event rows + 6 old wrapper-digest publication rows, with `prior_publication_wrapper_digest` carrying each old value); repins are the last 6 entries in execution order; counters unchanged 6/6, six distinct published keys. A1's recorded root cause ("publish() recorded sha256(canonical_json(wrapper))") is consistent with A7T's original finding.
- **B — first-pass results stand.** The six `scored_cells/` files are **byte-identical** to what was audited (recomputed sha256 == the values recorded in `z9_a7_terminal.json`); the remediation diff touches only the five prescribed control files (event_log +1 append-only `A7T_B1_REMEDIATED` row, family_verdicts, heartbeat, ledger, state); scored cells, research code and staging trees untouched. ADJ-5 corrected figures now match A7T's derivations (TOM-A **4.884039**, TOM-N/C **4.856678**; IDIO kept at the correct 3-dp 4.241/4.104/3.967). Heartbeat label and `state.scored_cells[]` INFO fixes applied. Family verdicts (both REJECT), sprint `STOCKS_FREE_V3_REJECT_ALL`, zero survivors — all unchanged. T2–T11 evidence (bit-exact rebuilds, 90/90 gate truth, ADJ-5 arithmetic, fresh-process reproduction, S1 isolation, boundaries, counters, process scan) carries over unchanged since the scored bytes are identical. One INFO residual: a single prose parenthetical "PASS under ADJ-5 (4.886)" remains in the TOM gate summary — verdict-neutral (gate PASS correct under both figures; the authoritative corrected map in the same file carries 4.884039).
- **C — untracked paths:** `git status --porcelain` shows exactly the two A7T audit files, uncommitted.

---

## FIRST-PASS RECORD (2026-09-03T16:11:29Z @ `deba0838`) — verdict then: `STOCKS_FREE_V3_INCOMPLETE_NOT_PROMOTABLE`



## Per-task measured results

### T1 LEDGER — **FAIL (blocker A7T-B1, HIGH)**
- `observed=6`, `published=6`, six distinct published keys, exactly the six arms of `selection_freeze.json`; per-key event sequence `COMPUTE_RECORDED → digest+published_at → FIRST_PUBLICATION → REPLAY_ZERO_DELTA` correct (24 entries); serial order matches `scoring_contract.execution_order`; replays counter-neutral.
- **Digest recomputation: 0/6.** The six `artifact_digest` values in `research/control/stocks_free_v3_run/ledger.json` do **not** equal sha256 of the published artifact bytes (`research/audits/stocks_free_v3/scored_cells/<ARM>.json`). Example: ledger A1 `c6469123…` vs actual file `c7fc474c…`. I exhausted ~10 convention families (raw bytes ±newline; V2 `canonical_json`; run_utc-stripped via dict-pop and regex; indent/ensure_ascii variants; field removals; turnover halved/rounded; stdout-summary forms; jq -S -c). None match.
- `scoring_contract.json → publication.immutability` says *"sha256 recorded in the ledger entry"* — the recorded values pin nothing recoverable.
- **Mitigation (why this is confined to the ledger column):** `event_log.jsonl` cell-1 `artifact_sha256` **does** match the published bytes; e-exec-1 and r-reproduce `.staging/out` copies are byte-identical to the published artifacts modulo `run_utc`; and my own fresh rerun (T7) reproduces the published bytes exactly. The artifacts are almost certainly the true published bytes; the ledger digest column is the defect.
- **Remedy (for A1, not me):** re-derive the six digests as sha256 of the exact published bytes (or document+prove the convention actually used), then re-run this terminal audit.

### T2 TOM-SETTLE-A science — **PASS (bit-exact)**
- `total_pnl = curve[last]−1 = 0.38516201458278565` — equals artifact exactly; PF 1.6202389056324922 and expectancy 0.002416822913650805 recompute exactly from `period_pnls`.
- Fold returns at the scored boundaries recompute exactly: F1 0.11008982300575965, F2 0.1526550204560293, F3 0.1035640412679324.
- **Independent rebuild from primary data** (staging root `r-reproduce/.staging`, manifest sha `4bc21789…` verified — file hash matches the driver pin and 51/51 listed files verify; `MANIFEST.json` sha `62ac324d…` equals the selection-freeze pin): `load_s0_snapshot_inputs → build_registry + schedule_entries → value_book @10bps → assert_reconciles` reproduces total_pnl, expectancy, PF, total_cost, n_periods (177), the full 1842-session equity curve and all period PnLs **bit-identically (diff 0.0)** — stronger than the 1e-12 requirement.
- Fold alphas rebuilt independently via `build_risk_matched_spy` (arm's frozen registry binding) + `compute_fold_alpha`: all three exact, including benchmark returns and series digests.

### T3 IDIO-A1 anchor — **PASS (bit-exact)**
Same rebuild path: total_pnl −0.20599603636907116, expectancy −0.0029621973384726477, PF 0.4264036223803547, total_cost 0.028264196060712093, n_periods 60, curves/PnLs bit-identical; all three fold alphas exact (F3 −0.1069701536240838).

### T4 GATE TRUTH — **PASS**
90 gate verdicts re-evaluated across the six artifacts against their own observed values and the frozen `scoring_contract` thresholds: **zero mis-statements** (verdicts and observed fields). `turnover_within_ceiling=FAIL` recorded in every artifact is arithmetically correct under the artifacts' doubled field. All six `arm_gates_all_pass=false`.

### T5 ADJ-5 TURNOVER — **PASS with 2 LOW findings**
- Confirmed: artifact `schedule_turnover_two_way_per_year` = **2 × (sum|delta|/yr)** (driver `one_way * 2.0 / n_years`; rebuild reproduced `sum|delta|/n_years = field/2` bit-exactly; note fill costs are equity-scaled, so `total_cost/bps ≠ sum|delta|`).
- Corrected figures under the frozen convention (recomputed): IDIO **4.241042 / 4.104235 / 3.967427**, TOM **4.884039 / 4.856678 / 4.856678** — **all six < 6.0**.
- Family verdicts are independent of this gate: flipping turnover to PASS leaves every arm failing ≥2 hard gates (TOM: `risk_matched_excess 1/3` and `overall_alpha ≤ 0`; IDIO: expectancy/PF/alpha/stress/drop-ones).
- LOW: ADJ-5's TOM-A corrected figure **4.886 vs derivable 4.884039** (0.002 off); TOM-C **4.856** vs TOM-N **4.857** — inconsistent rounding of the *identical* derivable 4.856678. Verdict-neutral.

### T6 VERDICT TRUTH — **PASS (both REJECT confirmed)**
- **TOM:** anchor alpha −0.125656 (1/3 folds positive < 2) fails the alpha gates despite +38.5% raw PnL, PF 1.620, 3/3 positive folds, passing stress/drop-ones. Control C alpha −0.241158: **same sign** as anchor and **|C| ≥ 0.5·|A|** (0.2412 ≥ 0.0628) → preregistered falsification rule 2 triggers. Per PLAN §16 raw PnL cannot override → `FAMILY_REJECT` is the only defensible verdict.
- **IDIO:** anchor alpha −0.251390, non-positive, 0/3 folds; control C1 −0.020701 with |C|/|A| = 0.082 < 0.5 — the sign-inverted falsification *form* holds, but the anchor itself is dead (expectancy −0.00296, PF 0.426, stress −0.230), nothing to rescue. Neighbour N1 −0.064748 (same sign; fails gates). → `FAMILY_REJECT` only defensible verdict.
- **Zero Stage-A survivors**, under both the recorded and the corrected turnover convention.

### T7 REPRODUCTION — **PASS**
- Driver sha in **both** detached trees = `48e95f21737c78bcfd17fd169e67a6522cb85da9534cf3d67d270e424fc9bd88` (matches claim).
- **My own fresh-process rerun** of `SFV3-A6-TOM-SETTLE-N` from r-reproduce at W1 (pins passed): output byte-identical to the published artifact after deleting **only** `run_utc`. All metrics agree.
- `z9_reproduction.json` verified: its `digest16` values equal `sha256(raw rerun bytes)[:16]` for all six cells, and published == rerun after run_utc-only normalization for all six → **6/6 EXACT_MATCH claim VERIFIED**.

### T8 S1 ISOLATION — **PASS**
Max period date 2025-07-29, max curve/session date 2025-07-31, max fold end 2025-07-24 across all six artifacts — nothing ≥ 2025-08-01. No S1 reads in `event_log.jsonl`; the only S1-era mention is P1's honest NOT_RUN note (2 split-provenance closes per split symbol, 2025-12-04/05 provenance facts, read during **P1 data revalidation** per the adjudicated V2 practice — no scored computation used post-S0 dates; my rebuild asserts every session < 2025-08-01). FD7 S1-isolation lineage carries from V2 control state and is restated sealed in all V3 control files.

### T9 BOUNDARIES — **PASS**
`main` tip = `e1c2b7c` (owner plan, matches run_contract pin) and is **not** in the lane's ancestry (merge-base `b8876ef`); **zero merge commits** in the lane after the fork. No `orca/stocks-free-v3-*` remote refs (`git for-each-ref refs/remotes`; `git ls-remote` not used per no-network rule). All 11 V3 worktrees present, including e-exec-1 and r-reproduce detached at `586f9fe` — no deletions. `/Users/hoangminhlong/my-quantitative/.v2c` holds only an 85-byte tooling pointer (`plugin_root`); no V3 research state there.

### T10 COUNTERS/BUDGET — **PASS**
state.json, heartbeat.json, ledger.json and family_verdicts.json all agree: V3 observed 6 / published 6, budget 6/6, historical 6/6, workers 0, `NO_PAPER_NO_LIVE_NO_ORDERS`, S1 sealed. Exactly six files in the tree carry the `stocks_free_v3/scored_cell@1` schema — no seventh scored metric. INFO: `heartbeat.verdict` label is stale (`PRELAUNCH_AUTHORIZED_NO_SCORED_CELL_RUN` vs completed_cells=6); `state.json.scored_cells[]` empty (ledger is authoritative).

### T11 PROCESS — **PASS**
`ps aux | grep -E "pytest|nautilus|backtest|cell_runner" | grep -v grep` → no matches. No interference with V3 trees.

---

## Blockers (first pass — all now resolved)

| ID | Sev | Finding | Status |
|----|-----|---------|--------|
| A7T-B1 | **HIGH** | `ledger.json` `artifact_digest` column (6/6) did not recompute as sha256 of the published artifact bytes, violating `scoring_contract.publication.immutability`; no recoverable convention reproduced the recorded values. Artifact immutability was independently corroborated (event-log cell-1 hash, exec-tree copies, T7 rerun), confining the defect to the ledger digest column — but the primary publication record was not self-verifying. | **REMEDIATED AND VERIFIED** at `3251554`: six append-only repins carry the exact published-bytes sha256 (6/6 match); prior 24 rows byte-identical to the pre-remediation ledger; counters 6/6 unchanged. |

## Objections

| ID | Sev | Finding | Status |
|----|-----|---------|--------|
| A7T-O1 | LOW | ADJ-5 corrected TOM-A turnover 4.886 vs derivable 4.884039; TOM-C 4.856 vs TOM-N 4.857 inconsistent rounding of the identical derivable 4.856678. Verdict-neutral. | **REMEDIATED** (map now 4.884039/4.856678/4.856678, resolution note present); one prose remnant "(4.886)" in the TOM gate summary noted as INFO, verdict-neutral. |

**Info:** stale heartbeat verdict label [fixed at `3251554` → `FAMILY_REJECT_BOTH_SPRINT_REJECT_ALL_PENDING_TERMINAL_A7`]; empty `state.scored_cells[]` [fixed at `3251554`, populated with the six arm ids]; "1.1% pnl" in the IDIO neighbour reading is ambiguous (artifact N1 total_pnl = −0.56%; the PF-1.10-below-gate part is correct at 1.0977); identical TOM-N/TOM-C turnover fields are legitimate (same 2-transitions-per-month gross-cycling structure).

## Bottom line

The scored science is sound and reproduced bit-exactly: **both families are correctly `STOCKS_FREE_V3_FAMILY_REJECT`, zero survivors, no promotable edge.** The sole blocker (A7T-B1) was remedied by A1 exactly as prescribed and re-verified 6/6 at HEAD `3251554`. The terminal signature is:

**`STOCKS_FREE_V3_REJECT_ALL_CONFIRMED`**

*Audit artifacts written and updated in place (uncommitted): `research/audits/stocks_free_v3/z9_a7_terminal.json`, `research/audits/stocks_free_v3/z9_a7_terminal_AUDIT_REPORT.md`. No other files touched; nothing staged or committed.*
