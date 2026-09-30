# A7 TERMINAL AUDIT — ETHUSDT-OPEN-SEARCH-V2 (G9, fresh context, read-only)

Auditor: G9 A7 TERMINAL lane, independent fresh context. Scope per dispatch:
adjudicate the terminal close of STOP-1 (verdict
`ETHUSDT_OPEN_SEARCH_V2_NO_INCREMENTAL_VALUE`, G8 repro twin ALL_MATCH), with
central adjudication of the r1 remediation re-run. No repair performed; no
engine edits; no network; no git writes by this lane beyond these two audit
artifacts.

Audited state (measured, not trusted):

- Integration worktree `.worktrees/ethusdt-open-search-v2/integration` at HEAD
  `c70a4ab82179d429c9dd9c2bd29c09e4acee04d2`, branch
  `orca/ethusdt-open-search-v2-integration`, tree clean. Chain verified:
  `f672e01e` (gate set) → `d613786b` (GO record, additive-only, diff verified:
  exactly one new 28-line file) → `1908b075` (scored execution) → `c70a4ab8`
  (G8 twin report).
- Root checkout `main` at `a0f1519e` (one registry sync past the dispatch
  packet's stated `7f4ea422`; that sync only records the G8 landing + this
  audit in flight — expected bookkeeping, noted as INFO).
- Code-freeze digests re-measured on disk: `eosv2_engine.py`
  `cf1f36d5…`, `run_scored.py` `28f0ff88…` (r1-remediated), `stage_all.py`
  `5d96cad6…`, `test_fixtures.py` `c4307701…` — all equal to
  `freezes/eosv2_freeze.json` `code_freeze` (incl. r1 supersession).
  Pre-r1 `run_scored.py` at `f672e01e` re-hashed = `974111c5…` (matches the
  r1 record's `old_digest_run_scored_py`).

---

## 1. The r1 remediation re-run (central adjudication)

**Claim under audit**: attempt-1 crashed pre-publication
(`KeyError: 'all_pass'` at `run_scored.py:201`); the lane applied a one-token
fix (`g["all_pass"]` → `g.get("all_pass")`), superseded the runner digest in
the freeze via an additive `freeze_remediations.r1` record, and re-ran WITHOUT
a fresh A7 delta — deviating from V1's precedent (V1 deltas r2/r3, each
`AUTHORIZED_FOR_SCORED_RERUN`, confirmed present in git at `8196e3ea`).

**(a) The fix cannot alter PnL/gates/arms/verdict — PASS (verified by code
reading in full context).** The changed line sits in the aggregation loop of
`scored()` AFTER all compute (`run_all()`, tier table, `gates()` per cell)
and BEFORE the artifact is assembled:

- `gates()` (lines 132–172) always sets `all_pass` (True/False, line 166) for
  every computed cell, so `g.get("all_pass")` returns the identical boolean —
  no computed cell's membership can change.
- NOT_RUN_THIN cells are placeholder dicts `{"status", "reason"}` written at
  lines 197–198 without gate fields; they were never computed and can never be
  all-pass, so excluding them (via the falsy `.get` default) is exactly what a
  bug-free aggregation would do. Eligibility is governed independently by
  `eligible_arms()`/`feasibility.json`, untouched.
- The verdict expression (lines 214–216) depends only on whether the
  `all_pass` list is empty; arms/folds/tiers/cost law/PnL math live in
  `eosv2_engine.py`, whose digest is unchanged byte-exact across r1
  (re-verified: `cf1f36d5…` both sides of the diff).
- `git diff f672e01e 1908b075` on `run_scored.py` is exactly one hunk, one
  line, the described token change plus comment. The engine diff is empty.

**(b) The remediation record is truly additive — PASS.** The freeze diff
(`f672e01e` → `1908b075`) contains only: the `code_freeze.run_scored.py`
digest supersession (`974111c5…` → `28f0ff88…`) and the new
`freeze_remediations.r1` block. The old digest is preserved INSIDE the r1
record and the entire pre-r1 freeze remains recoverable at git `f672e01e` /
`05790ce7`. No gate text, arm spec, fold, ladder, or verdict-enum entry was
modified. Nothing was overwritten without trace.

**(c) Zero outcome exposure before the fix — PASS (three independent
evidences).**

1. Structural: the `KeyError` fires at line 201; the only publication paths
   (`dest.write_text` at line 219, `print` at line 220) are strictly after it.
   Attempt-1 could not have published by construction.
2. Independent machine record: the machine-wide heavy-lock history
   (`~/.my-quantitative-governance/heavy_runtime/heavy_worker.history.jsonl`)
   holds a row pid 21026, started 2026-09-30T21:23:21Z, RELEASED **FAILED**
   21:23:36Z, whose release note preserves the stderr tail verbatim — the
   traceback names `run_scored.py", line 201, in scored … KeyError: 'all_pass'`
   and shows the PRE-FIX source text `g["all_pass"]`. This record is outside
   the lane's control files and was not authored by the lane.
3. Publication trail: `scored/` first enters git at `1908b075` (attempt-2's
   commit); events.jsonl records "scored/summary NOT written, stdout artifact
   empty"; the current `run_scored_stdout.json` (mtime 21:25:46Z) is
   attempt-2's verdict print. Freeze red line ("any change after scored PnL
   is visible = new experiment") not crossed: attempt-1's PnL existed only
   in-process, never written, never printed.

Timeline (all times UTC; reconstructed from lock history + events + mtimes,
coherent): GO consumed 21:20:00 → attempt-1 lock 21:23:21, FAILED release
21:23:36 (TECHABORT event + r1 record stamped 21:23:21) → freeze rewritten
with r1 21:25:13 (file mtime) → attempt-2 lock 21:25:31, pid 21182 →
summary + stdout written 21:25:46 → determinism + FINISHED release 21:26:06.

**(d) Ruling: LAWFUL remediation-with-disclosure. No verdict downgrade, no
condition on the scored result.** Reasoning:

- The experiment the GO authorizes is defined by the freeze (4 lane-B cells ×
  3 tiers × frozen engine × frozen corpus), not by a process count. A crashed
  invocation that published nothing consumed no observation; one experiment,
  one budget accounting (8/8), consistent.
- What a fresh pre-run A7 delta would have verified — that the fix is
  outcome-neutral — is now proven with STRONGER evidence than a pre-run audit
  could have had: independent code reading (a), the lock history's preserved
  pre-fix traceback (c.2), the digest chain, and the G8 detached-twin
  re-derivation at the remediated SHA reproducing every outcome byte
  (Section 6). Retrospective verification subsumes the delta's purpose here.
- Disclosure was complete at every layer (freeze r1 record, events.jsonl,
  scored report §2, STOP1_execution handoff, registry phase prose, state.json)
  and explicitly flagged to this gate.

The deviation from V1 precedent is real and is NOT blessed as a general
pattern — it is lawful here because the fix is provably outcome-neutral and
pre-publication. Condition 2 below codifies the path forward. Note (LOW): the
events.jsonl description writes the fix as `g.get("all_pass", False)` while
the applied code and freeze r1 record write `g.get("all_pass")` — functionally
identical (both falsy defaults); the code + freeze are the authority.

## 2. Verdict law — PASS (recomputed independently)

All gate calls recomputed from `scored/scored_summary.json` raw values:

- **G3 wall**: best cell B2 net@1.0× = 403,801.90 vs `BASE_ALWAYS_ON_LONG`
  1,653,470.33 → margin −1,249,668.43 (matches runner to the cent; B1/B3/B4
  margins −1,365,046.53 / −1,514,025.8x / −1,424,587.6x, rounding-consistent).
  Also below `BASE_TREND_LF` 472,864.82 for all four. G3 FAIL 4/4 (beats
  `REF_SHORT_ALWAYS` −1,656,451.03, but G3 requires strictly ALL three).
- **G10**: every cell's net@1.0× < TREND_LF (first conjunct fails alone);
  flip check independently recomputed: B2 F2 (trend +40,179.87 → −27,143.87),
  B3 F1 (+296,861.29 → −2,363.18), B4 F2 (+40,179.87 → −55,391.93) — matches
  the runner's flip lists; B1 no flips. G10 FAIL 4/4.
- **G5**: recomputed max-positive-fold shares: B1 0.6112 FAIL, B2 0.5795 FAIL,
  B3 0.4292 PASS, B4 0.6440 FAIL — matches.
- **Passes confirmed**: G1 (all four nets@1.0× > 0), G2 (all @1.5× > 0), G4
  (B1 4/4 folds positive; B2/B3/B4 3/4), G6 (shuffle 106,573.76/310,630.58/
  42,140.88/178,600.27 and inversion all negative — none out-earn their cell),
  G7 (fills@1.5× 516/450/380/236 ≤ 10,000; cost/rt 0.1197–0.1386 bps ≤ 10).
- `all_pass_cells == []` confirmed; with all four cells failing G3 and G10 the
  CANDIDATE branch is unreachable regardless of G5.
- Typed verdict `ETHUSDT_OPEN_SEARCH_V2_NO_INCREMENTAL_VALUE` is a member of
  the frozen `verdict_enum` and is the correct member for an empty all-pass
  list. Lane-A cells are lawful `NOT_RUN_THIN` placeholders (feasibility kill:
  F1 populations 28/0/0/0 < floor 100 — reconfirmed in
  `freezes/feasibility.json`; prelaunch A7 check C independently recomputed
  them).

## 3. References / V1 reproduction — PASS (zero drift)

Compared V2 `scored_summary.json` references against V1's terminal scored
summary (baseline: the byte-identical repro-twin copy of V1's
`eos1.scored_run@1` at V1 commit 8196e3ea; V1 registry prose independently
corroborates 1,653,470 / 472,865): 4 references × 3 tiers × + 4 references ×
4 folds = **28/28 values equal to the cent, zero drift**. ALWAYS_ON
1,653,470.33 / TREND_LF 472,864.82 / SHORT_ALWAYS −1,656,451.03 / CASH 0.00,
fold nets included. The plan §4 "material divergence = STOP" clause was never
triggered; the restaged corpus is byte-equivalent to V1 on the shared plane,
exactly as the census V1 cross-check (80/80×3) predicted.

## 4. Authorization chain — PASS (lawful under the delegation as recorded)

- `auth/GO_RECORDED_STOP1_COWNER.json`: owner delegation recorded verbatim
  (Vietnamese, 2026-09-30): "Bạn cứ thoải mái ra lệnh GO hay gì đó. Bạn là
  co-owner và thay tôi làm việc tới 8 giờ sáng mai. Mọi quyền của tôi giao
  cho bạn." plus the embedded scope clause (research GOs only after verifying
  gates/freeze/A7/registry/budget/lock at the correct gate; record evidence;
  no double consumption). Time-boxed to 2026-10-01 08:00 Vietnam
  (= 2026-10-01 01:00Z); transmission 2026-09-30T21:20:00Z is inside the box.
- Two-key complete: key 1 = A7 prelaunch `AUTHORIZED_FOR_STOP1` (0 blocking;
  9 checks, 8 PASS + H NO_VETO), with the audited-head additivity verified by
  me (`05790ce7` → `f672e01e` additive only: A7 report, charter, .gitignore,
  state/events; engine/freeze/data untouched); key 2 = the transmitted GO
  phrase, `match: EXACT` against the registered phrase.
- No double consumption: registry `go_phrase_state` was
  `REGISTERED_NOT_CONSUMED` from registration (2026-09-25) through the
  consumption commit `6b650cb1`; the only consumption is 21:20:00Z; worktree
  `state.json` records `CONSUMED`; worktree `audits_a7/go_authorization.json`
  written at execution and the frozen runner refuses scored mode without it
  (code lines 176–183 verified).
- Gate verification at consumption recorded (registry state, worktree/branch
  clean, heavy lock FREE_PROVEN, workers 0, S1 SEALED_UNTOUCHED).

Ruling: the co-owner transmission is lawful under the delegation AS RECORDED
— owner instruction is the top authority in this workspace; the delegation's
own embedded conditions were all satisfied at transmission and are evidenced.
Chat-layer provenance is outside this audit's boundary; the record is
internally consistent and corroborated by the registry commit chain
(`6b650cb1` → `d53b6b03`).

## 5. Budget / denominators — PASS

- 8/8 consumed, recorded conservatively; both countings disclosed: dispatch
  accounting 4 arms + 4 references = 8 of the 8-cell cap; plan §4 would read
  references as NOT cells (4/8). The conservative 8/8 is what `state.json`
  records, so no later lane can infer spare budget.
- Runner denominator verified inside `scored_summary.json`:
  `scored_cells 4, computations 12, controls 24, references 12` = 48 books,
  matching the P3 dry-run's `expected_computations 48 / actual 48 / pass`.
- Observed == published: the four scored cells' engine values appear once, in
  the frozen artifact; the report transcribes verbatim (spot-checked).
- Zero additional cells post-verdict: nothing new under `scored/` after
  `1908b075` except documentation (`G8_REPRO_TWIN.md`); G8 re-derived the
  already-counted artifacts at the same SHA — zero budget, denominator
  reproduced identically. Budget is exhausted; no scored re-run is possible
  or required.

## 6. G8 repro twin — PASS (no over-claim)

Independently re-verified by this audit, frozen side:
`run_scored_stdout.json` sha256 `5a4df6a2…`, `determinism_b1.json`
`955a8248…`, `scored_summary.json` `b18c3c7f…`, `STOP1_SCORED_REPORT.md`
`8f84b6db…` — all four equal the G8 table. I reproduced the canonical
equality myself: normalizing `built_utc` to a constant and canonicalizing
(json.dumps indent=1 sort_keys + newline) yields sha256
`bd8875aea83fc8fc5f5851ba20d099eb48e570e674e155435a91a160406323ea` —
byte-equal to the digest G8 reports for BOTH sides. The single-field root
cause is source-provable, not inferred: `run_scored.py` line 35
`now()` stamped at line 203 `"built_utc": now()` — a by-construction
wall-clock journal field. The report discloses the raw differing sha256s
rather than smoothing them, scope-limits the twin (detached, digests
pre-verified incl. the r1-remediated runner, frozen artifacts copied aside
and removed in the twin only, same invocation path), and does not claim
byte-equality for `STOP1_SCORED_REPORT.md` (correctly marked not re-runnable).
ALL_MATCH is an accurate claim for the deterministic outcomes. No over-claim
found.

## 7. Partition / PIT — PASS

STOP-1 ran on the staged V2 corpus (7 series, 551 zips, sha-pinned in
`staged_manifest.json`; census BUILD_PASS; V1 cross-check 80/80×3) with the
frozen engine (`cf1f36d5…`, kernel byte-inherited from V1 terminal 8196e3ea
per prelaunch check A: 19/22 blocks byte-identical, 3 differing confined to
allowed deltas) and the r1-remediated frozen runner (`28f0ff88…` in freeze
incl. r1) — all digests re-measured on disk by this audit. Lane-A exclusion
is a pre-PnL feasibility kill (zero denominator, never computed). S1
SEALED_UNTOUCHED per registry and `state.json`; no evidence anywhere of S1
access. `state.json` `orders: NONE`; no paper/live/order artifacts exist in
the cycle's evidence tree; the delegation itself carved trading out of scope.

## 8. Close readiness + plan §8 gates-NO branch

Plan §8 (root checkout, verbatim): "NO candidate ⇒ standing directive
authorizes tranche V3 ONLY with new lawful tuples; if A7 vetoes both lanes
here, the posthoc open space on keyless data is EXHAUSTED and the campaign
parks at an owner-redirection decision (asset change / new data authority /
wall-redesign successor — each an owner decision per §34.5, not
agent-derivable)."

Ruling on the branch the evidence supports:

- The verdict is gates-NO (`NO_INCREMENTAL_VALUE`, not a lane veto).
- A7 prelaunch adjudicated lane B genuinely novel with **NO_VETO**; lane A
  was killed by feasibility, not vetoed. This terminal audit issues **no
  lane veto** either (its findings are recording defects, none touching lane
  quality or outcome integrity).
- Therefore the operative branch is the FIRST clause: the standing directive
  authorizes **tranche V3 only with new lawful tuples**. The exhaustion /
  owner-redirection clause is NOT triggered by this cycle's evidence.
- However, V3 is not dispatchable without owner input, on three grounds:
  1. Any V3 GO needs fresh two-key authorization — the co-owner delegation
     expired 2026-10-01 08:00 Vietnam; no standing delegation remains.
  2. "New lawful tuples" on the CURRENT data authority are nearly exhausted:
     V1 consumed the BTC-price-state and ETHBTC-ratio families (killed),
     V2 consumed BTC-rvol (feasibility-dead on this corpus: 2020-01 data
     floor + 395d warmup > F1 end — more history is a data decision) and
     alt-breadth (scored dead). Genuinely new state-constructor families on
     the same 7 keyless series would have to survive P2 feasibility + lane
     novelty — possible in principle, thin in practice.
  3. The binding constraint is structural: the G3 ALWAYS_ON wall (+1.65M raw
     net, F1-2020/21 beta) is unbeatable by any posthoc long/flat book on
     this window — it killed V1 and V2 identically, and the charter itself
     preregistered it. "Wall-redesign successor" is expressly an owner
     decision per §34.5.

**The decision the owner faces** (P6 close should record it exactly): accept
this terminal, then choose among (a) register tranche V3 with genuinely new
lawful tuples from the existing data authority (owner GO required; agent may
propose families but they must clear feasibility and lane novelty; expect the
same G3 wall unless the wall itself is redesigned), (b) redirect: new asset /
new data authority (new series, new data classes, window extension) /
wall-redesign successor — each solely an owner decision, or (c) end the
campaign with this terminal. The evidence does NOT support the "exhausted →
park at owner-redirection" clause as the automatic outcome; it supports
"standing directive V3-with-new-tuples" as the default, with the honest
caveat that every credible continuation path runs through an owner decision.

Close readiness: G8 ALL_MATCH verified (§6), G9 = this audit (0 unresolved
HIGH/CRITICAL → G9 PASSES with MEDIUM carried as conditions), verdict and
budget reconcile, references reproduce V1, authorization chain lawful. The
cycle is ready for the P6 two-half close subject to the conditions below.

## 9. Verdict

```
A7_TERMINAL_VERDICT: CONFIRM_WITH_CONDITIONS
CRITICAL: 0   HIGH: 0   MEDIUM: 1   LOW: 1   INFO: 2
```

Findings:

- **M-1 (MEDIUM, non-blocking)** — Registry structured fields desynced from
  recorded facts at every sync since consumption: at `6b650cb1`, `d53b6b03`,
  `7f4ea422` and current HEAD `a0f1519e`, the ETHUSDT-OPEN-SEARCH-V2 row's
  machine-readable `budget.used` stayed `0/8` and `go_phrase_state` stayed
  `REGISTERED_NOT_CONSUMED` while the same row's `phase` prose correctly
  recorded GO consumed and 8/8. CYCLE_REGISTRY.json is the ONLY writable
  cycle authority; a future automated reader could infer an available scored
  GO / spare budget. (Same defect exists in the V1 terminal row — recurring.)
  Consumption was in truth single and fully evidenced (auth record + prose +
  worktree state), so no integrity breach.
- **L-1 (LOW)** — r1 disclosure text mismatch: `events.jsonl` describes the
  fix as `g.get("all_pass", False)`; the applied code and the freeze r1
  record say `g.get("all_pass")`. Functionally identical (both falsy
  defaults); code + freeze are the authority.
- **I-1 (INFO)** — r1 record's `utc` (21:23:21Z) is the TECHABORT event
  time; the freeze file edit completed 21:25:13Z (mtime), before attempt-2's
  lock take 21:25:31Z. Timeline coherent; the record does not state the
  freeze-write time separately.
- **I-2 (INFO)** — Root registry HEAD (`a0f1519e`) is one sync ahead of the
  dispatch packet's stated `7f4ea422`; the extra sync only records the G8
  landing and this audit in flight. Expected mid-flight bookkeeping.

Carried (not re-counted; already dispositioned by the authorized prelaunch
record): 2 MEDIUM + 2 LOW + 2 INFO from `prelaunch_a7.json` (incl. 552 raw
zips committed vs plan §9 — .gitignore added for future adds, history
untouched; freeze additive records not byte-reproducible from committed
builder).

Conditions (recording obligations ONLY — no scored re-runs; budget is
exhausted 8/8):

1. At the P6 two-half close registry write, reconcile the
   ETHUSDT-OPEN-SEARCH-V2 row's structured fields with the recorded facts:
   `budget.used` 8/8, `go_phrase_state` CONSUMED → DEAD per P-8, lifecycle
   TERMINAL with the typed verdict; and record a one-line reconciliation
   note for the same defect in the ETHUSDT-OPEN-SEARCH-V1 terminal row.
2. Codify the remediation path for future scored-phase pre-publication
   TECHABORTs: either obtain a fresh A7 delta (V1 precedent) or record an
   explicit skip carrying the r1 disclosure fields (trigger, old/new digests,
   pre-outcome proof, scope guarantee) — make the disclosed-skip a named
   lawful path rather than an ad-hoc deviation (plan §10 amendments log or
   campaign lessons at close).
3. Record in the P6 close: the operative §8 branch is the standing-directive
   tranche-V3 clause (no lane veto by prelaunch or this terminal); a V3 GO
   requires fresh owner two-key authorization (the 2026-09-30 co-owner
   delegation expired 2026-10-01 08:00 Vietnam); and record the family
   dispositions per the V1 close precedent (EOSV2-A rvol family
   feasibility-dead on this corpus; EOSV2-B breadth family scored-dead
   against the G3 wall) in the campaign's family-failure record.

The typed verdict `ETHUSDT_OPEN_SEARCH_V2_NO_INCREMENTAL_VALUE` STANDS
CONFIRMED. Nothing in this audit affects any outcome value; G9 gate = PASS
(0 unresolved HIGH/CRITICAL) with the MEDIUM carried as conditions above.
