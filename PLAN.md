# V10R → V11 EXECUTION — DATA REMEDIATION (OPTION A), M01 SCORED, SECOND DISCOVERY

> **Fresh-context owner plan. Read completely before acting.**
>
> Owner directives recorded 2026-08-28:
>
> - **Option A** — re-stage data to cover the preregistered window end
>   `2026-08-21T00:00:00Z`; the window itself does NOT move.
> - **Clock: 24 hours** from go-live; no auto-extension.
> - **Second discovery wave: 2 families — 6 cells.** Together with M01 this
>   supersedes the V10 contract ceiling of 2 families/6 cells: the new
>   authorized maximum is **3 families / 9 scored cells total**, and the
>   multiple-testing cost is accepted (denominator grows accordingly; DSR/PBO
>   must count every scored cell).
>
> Measured terminal state inherited from sprint V10P-R (full record:
> `research/control/v10p_run/terminal_closeout_v10p.json`, integration
> `orca/v10-integration@86b7274`): terminal `V10_BLOCKED_PRELAUNCH`, budget
> **0/9 consumed**, denominator **117**, historical denominator floor holds.

## 1. Mission

1. **R** — Remediate the single HIGH blocker (`G05_COVERAGE_SHORTFALL`),
   re-freeze, pass a fresh independent A7 prelaunch audit, then run M01's
   three preregistered scored cells through the already-built adapter
   pipeline, reproduce them, and close the M01 family honestly.
2. **V11** — Immediately after M01's backtest completes, run one more
   discovery sprint of the same discipline as V10's (blinded proposals →
   novelty → rescue challenge → selection freeze → 3 cells per family),
   carrying forward the lessons of V1–V9 and V10P, selecting **2 new
   families**, and closing each honestly.

Scientific success is honest evidence. `REJECT_ALL`, `BLOCKED_PRELAUNCH`,
`INCOMPLETE_NOT_PROMOTABLE` remain valid outcomes at every stage. A profitable
but contaminated or unreproduced cell is not success.

## 2. Completed authority — do not repeat

Everything below is built, tested and frozen. Do not rebuild, do not redesign:

- **Generic adapter** `research/adapter_v10/` (contract:
  `research/control/v10p_run/adapter_contract_v10.json`): BG1–BG6 closed,
  dummy + M01 plugin reuse proven, exactly-once publish, 52-test acceptance +
  fault matrix. Blockers G15 (funding reconciliation), F2 (cache adopted on
  strict full-pipeline proof), G17 (one measured authority
  `final_cap=min(owner_ceiling=1, measured_safe_cap)`), H08 cases 12–20 are
  closed with evidence.
- **Fresh execution trees** `exec-v10-R1b`/`exec-v10-R2b` detached at
  `W2=d61a483`, staged data verified 47/47 manifest entries, byte-identical,
  read-only. Old `W=79fc883` + `exec-v10-R1/R2` are historical, never score
  from them.
- **M01** module, C1 field verification, signals/PIT tests; family
  `A8-V10-M01-AGGRESSOR-ABSORPTION-PANEL`; 3 preregistered cells: anchor,
  30-day-dispersion neighbor, C2 price-placebo. Window
  `2025-08-21T00:00:00Z→2026-08-21T00:00:00Z`, 3 chronological folds,
  strict-later fills, 5bp taker floor + adverse tick floor + native funding.
- **Data note**: `catalog/` extras and `funding_data/scan_2026/` are NOT
  git-tracked; fresh worktrees must copy them from root or old exec trees and
  re-verify against `research/control/v10_discovery_run/stage_manifest_R1.csv`.
- V9 closed `V9_REJECT_ALL_MULTI_FAMILY`; V9H
  `V9H_PASS_V10_AUTHORIZED`; V10P A7 recompute passed all gates except the
  one remediated in §3.

## 3. The blocker this plan remediates

`G05_COVERAGE_SHORTFALL` (HIGH, V10P A7): staged bars end
`2026-08-20T02:29:59.999Z` — 86 bars / 21.5 h before the preregistered window
end. Worse: `build_daily_closes` **silently synthesizes** the final daily
close from a 21.5 h-old bar instead of failing closed, and `coverage_report()`
reports counts without raising. Owner chose **Option A**: fetch the missing
data; the window stays frozen.

## 4. Phase R0 — data remediation (Option A)

1. Use the repo's existing download/ingest infrastructure (`data/download.py`,
   `research/download_derivatives.py`, `research/download_funding.py` — read
   them first; do not invent a new pipeline) to extend staged 15-minute bars
   for the full staged symbol set through `2026-08-21T00:00:00Z` **plus the
   warmup margin the M01 prewindow requires** (`2025-07-22` onwards is already
   covered; only the tail is missing).
2. Verify funding staged data (`funding_data/scan_2026/`) covers through the
   window end with the same freshness; if short, extend it by the same
   method. Fail-closed if any symbol cannot be completed.
3. Fix the silent-synthesis defect: `build_daily_closes` and
   `coverage_report` must **raise** (`DataUnavailable`-class) when the last
   covered bar is older than the boundary being emitted. Add a regression
   test that pins exactly the V10P failure mode (a stale tail must never
   produce a boundary close).
4. Rebuild stage manifests (CSV sha256+size+path, same format), stage into
   two NEW detached trees, byte-verify R↔R identical, read-only.
5. Do NOT touch `W2`/`exec-v10-R1b`/`exec-v10-R2b` or any historical tree.

## 5. Phase R1 — new freeze W3

Only after R0 verifies clean:

1. Full test suite, run alone, on the integration tree: expected ≥1275
   passed, plus the new regression tests.
2. Freeze `W3` = final code-bearing SHA. Create detached `exec-v10-R1c` and
   `exec-v10-R2c` exactly at W3; stage data read-only; verify byte-identity.
3. Record all hashes (code, data, funding, spec, adapter, cost, stress,
   benchmark, cache, resource, ledger) in a new worktree manifest under
   `research/control/v10r_run/`.

## 6. Phase R2 — A7 prelaunch re-audit (fresh, on W3)

A new independent A7 agent recomputes, never reads old verdicts: ETH/loader
coverage at the NEW window tail (the previously failing point, explicitly),
window/folds pins, BG1–BG6, G15, F2 (fresh probe or explicit
UNAVAILABLE_FAIL_CLOSED), G17 (fresh measured cap), H08 12–20, W3/R1c/R2c
identity, budget purity (0 consumed, no scored metrics), full suite, zero
unresolved HIGH/CRITICAL.

Launch gates (ALL required before any scored cell):

- A7 verdict `V10_LAUNCH_AUTHORIZED` (or explicitly scoped M01 equivalent);
- fresh resource probe allowing ≥1 heavy worker (`measured_safe_cap ≥ 1`);
- ≥120 minutes remaining on the clock;
- budget still 0/9, ledger clean.

## 7. Phase R3 — M01: exactly three scored cells (serial, heavy=1)

1. Anchor; 2. 30-day-dispersion neighbor; 3. C2 price-placebo control.

Per cell: verify preflight pins → 3 chronological folds with warmup outside
score → costs + native funding → baseline + fee×1.5 / +2 ticks / +1 event
delay / drop-one-symbol / drop-one-fold stress → deterministic artifacts
(metrics, trades, holdings, cashflows, fold reports, benchmark/context,
provenance, terminal row) → publish trial + denominator exactly once, only
after a valid score. Never inspect one cell to modify another. Technical
abort before any scored metric does not consume the slot (forensic proof
required); once a score is published the slot is consumed, no replacement.

## 8. Phase R4 — reproduction and M01 terminal science

Reproduce all three cells from clean `exec-v10-R2c` fresh processes; require
`all_match` on artifacts/trades/metrics/hashes. Denominator = 117 + valid
publications. DSR/PBO if valid, else `UNAVAILABLE_FAIL_CLOSED` with zero
credit. Apply the frozen Stage-A hard gates (after-cost expectancy >0,
PF≥1.10, ≥2/3 folds positive, no populated fold PF<0.80, positive-fold
contribution ≤50%, MDD≤10%, symbol contribution ≤40%, trade floor, no
drop-one dependency, stressed PnL>0 and PF≥1.00, neighbor supports anchor,
C2 demonstrates incremental flow information, reproduction all-match, zero
unresolved HIGH/CRITICAL). Outcomes limited to: family REJECT /
`STAGE_A_SURVIVOR_LOCKED_FOR_FUTURE_S1` (locked only; S1 is never opened) /
BLOCKED / INCOMPLETE. Record the family's lessons into the V11 lessons
register before touching the next wave.

## 9. Phase V11 — second discovery wave (2 families, 6 cells)

Same discipline as V10's discovery, sharpened by the lessons register
(§11):

1. **Blinded proposals** — independent agents each propose mechanisms from
   the S0-screened window; blind to each other and to M01's scored results'
   PnL (mechanism-level lessons only).
2. **Novelty matrix + independent rescue-risk challenge** of all candidates
   (including M01-family-adjacent ideas, which must show material deltas).
3. **Selection freeze** — exactly **2 families**; each with anchor +
   predeclared neighbor + negative control (3 cells each). Tie-break by
   hypothesis id. After selection: no grids, no replacement slots.
4. **Implementation through the existing adapter** (the V10P deliverable —
   new strategies must plug in, not fork the pipeline). C1-style field
   verification per family before any scored run.
5. **Prelaunch audit per freeze** (fresh A7, same gate set, fresh resource
   probe).
6. **3 serial scored cells per family** + R2c-style reproduction `all_match`
   + per-family terminal verdict under the same hard gates.

If the 24 h clock runs out mid-wave: close the wave
`V11_INCOMPLETE_NOT_PROMOTABLE`; never improvise scoring glue to fit the
clock.

## 10. Hard boundaries (unchanged unless owner speaks again)

- No hypothesis tuning or rescue on observed PnL of any scored cell; no
  peeking across cells; no replacement slots.
- Old W/R1/R2/R1b/R2b trees are historical; never score from them; never
  delete them.
- No S1; no equity scored runs; no paper/testnet/live; no real orders; no
  credentials; no destructive reset.
- Remote push only on explicit owner instruction (standing owner grant
  2026-08-28 for repo sync is noted; each bulk push still announced).
- Missing evidence is `UNAVAILABLE_FAIL_CLOSED`, never inferred PASS.
- Heavy scored workers: max 1, `final_cap=min(owner_ceiling=1,
  measured_safe_cap)`; full pytest runs alone; light agents ≤3 + A1.

## 11. Lessons register (must be applied, not relearned)

From V1–V9: multiple-testing honesty (every scored attempt enters the
denominator); concentration gates (top-fold/symbol) are what killed V6/V9
survivors, so stress + drop-one must run on every cell; negative controls are
mandatory, not decoration.

From V10P (new): (a) data coverage must be **fail-closed at the window tail**
— silent synthesis is the defect class that cost this sprint; (b) run the
resource probe **before** freezing the launch decision and respect
`final_cap=0`; (c) compute the `<120 min` launch-window arithmetic at intake,
not at launch time; (d) test fixtures must obey production invariants
(MIN_ELIGIBLE, per-symbol funding attribution) — align fixtures, never
weaken assertions; (e) exactly-once publication belongs in the adapter, not
the ledger; (f) cache adoption requires a preregistered raw-read budget on
the full pipeline or stays disabled; (g) one resource authority only, frozen
and monotone.

## 12. Deadline

24 hours from go-live (recorded in `research/control/v10r_run/heartbeat.json`
at start). Thresholds: <120 min → start no new scored cell; <45 min → stop
owned process groups, reconcile, close honestly. Do not skip tests/A7 to fit
the clock. Do not extend automatically.

## 13. Definition of Done

- R0–R2 complete with fresh A7 verdict explicit.
- If authorized: M01 3/3 cells executed, stressed, reproduced `all_match`,
  family verdict honest.
- V11: 2 families selected and frozen, implemented through the adapter,
  prelaunch-audited, cells executed/reproduced/verdicted — or an honest
  `V11_INCOMPLETE_NOT_PROMOTABLE` at the clock boundary.
- Denominator and budget accounting exact (each scored cell counted once).
- Master reports `.json`+`.md`, challenge memo, A7 audits per freeze.
- Integration clean; controller-owned workers 0; `PLAN.md`,
  `CONTINUE.md`, Wayfinder synchronized.

## 14. Mandatory checkpoints

1. go-live: clock + measured state; 2. R0 data verification; 3. W3/R1c/R2c
pins; 4. A7 R-verdict; 5. each M01 cell; 6. M01 terminal; 7. V11 selection
freeze; 8. each V11 family close; 9. final budget/denominator/workers report.

A1 continues through safe local non-destructive steps without repeated GO and
stops only at gate/deadline/permission failures or boundaries needing
push/deletion/S1/live authority.
