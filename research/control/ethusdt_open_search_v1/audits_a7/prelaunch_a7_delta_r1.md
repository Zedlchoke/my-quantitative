# A7 PRELAUNCH DELTA AUDIT r1 — ETHUSDT-OPEN-SEARCH-V1 (fresh-context auditor, same rules)

- Scope: verification of ONLY the r1 blocking findings (F-1 HIGH, E-1 MEDIUM) + chain regression. The full A–H audit of 2026-09-24T15:19:34Z stands unchanged except as re-examined here.
- Remediation commit: `4d05374569da88bf75fb33bcf15480d24b483381` (branch `orca/ethusdt-open-search-v1-integration`); pre-audit HEAD was `c52e8eb1` (r1-era).
- Audited at: 2026-09-24 (delta), interpreter `/Users/hoangminhlong/my-quantitative/.venv/bin/python`, all recomputation from bytes.
- Verdict: **AUTHORIZED_FOR_STOP1**

---

## 1. F-1 (HIGH, G7 structural unpassability) — RESOLVED

Code read (`scripts/run_scored.py`, lines ~103-140 at HEAD 4d053745):

- `cost_roundtrip_bps(res, tier)` is now `(2 * E.TICK * tier / px) * 1e4` — the ES1-precedent
  EXECUTION semantics: 2 adverse ticks per round trip, in bps of the average raw fill price.
  The fee term is gone from the gate. Docstring states the rationale and that G7 is an
  execution-quality ceiling, not a second fee gate.
- Fees remain priced inside net PnL: the git diff of `eos1_engine.py` in 4d053745 touches ONLY
  `PriceAtSettlement` — `run_book`'s cost law (`fees = qty*entry_raw*fee + qty*px_raw*fee`
  booked in `close()`, tick on both legs, funding cashflow) is byte-unchanged, and fixtures 3/4/9
  (costs-once, funding sign, tier scaling) all still pass.
- **Structural passability recomputed from staged bytes** (all 58,440 ETHUSDT 1h closes:
  min 95.73, max 4932.84): worst-case gate value `(2*0.01*tier/95.73)*1e4` =
  **2.089 bps @1.0x, 3.134 bps @1.5x, 4.178 bps @2.0x — all ≤ 10**. At the actual price range
  the gate now binds only on execution slippage and the 10,000-fill cap, exactly as plan §6 G7's
  fills clause pairs with a cost clause that CAN pass. No longer structurally unpassable.

Plan text NOT modified — verified in git on the main checkout:
- `git diff 51250e22 8a5a06b4 -- plans/PLAN_ethusdt_open_search_v1.md` = the single allowed
  cross-reference fix (`symbol-swap law, §14.3` → `symbol-swap law, handbook §14.3`, commit
  8a5a06b4, matching my r1 LOW finding L-4).
- `git diff 8a5a06b4 HEAD -- plans/PLAN_ethusdt_open_search_v1.md` = EMPTY (plan untouched since).
- Current plan §6 line: `G7  fills @1.5× ≤ 10,000 AND measured cost/round-trip ≤ 10 bps` —
  byte-identical to the r1-audited text. No gate-text drift.

Verdict: **RESOLVED**.

## 2. E-1 (MEDIUM, settlement fallback future price) — RESOLVED

Code read (`scripts/eos1_engine.py PriceAtSettlement.price` at HEAD 4d053745):

- New law: `floor_ts = (ts // 3600_000) * 3600_000`; if the floor-hour bar exists → return its
  **OPEN** (a price forming AT the floor instant; odd-ms stamps counted as fallbacks). If the
  floor-hour bar is missing → **close of the last bar ENDING at or before floor_ts**
  (`bisect_right(ts_sorted, floor_ts - 3600_000)`, close finalizes at ts'+1h ≤ floor_ts ≤ ts).
  `i == 0` → None (fail-closed, event skipped).
- Adversarial finalize-time proof: case 1 finalizes at floor_ts ≤ ts; case 2 finalizes at
  ts'+1h ≤ floor_ts ≤ ts; no code path can return a price finalized after the stamp instant.
- A7 probe on real staged bytes across **all 7,305 funding stamps**: 0 law violations (no wrong
  price, no finalize-after-stamp). Odd-ms example `2020-01-02T00:00:00.002Z` → 130.63
  (floor OPEN) instead of the r1 behavior (130.60, that bar's future close). Missing-floor
  branch exercised on real data (floor bar removed, bar ending exactly 2020-01-02T00:00Z used).
- Fixture 10 (`test_settlement_pricing_pit`) asserts all three cases with hand-computed values:
  exact stamp → floor open (130.0); odd-ms (+2 ms) → floor OPEN **not** close (130.0 ≠ 150.0);
  missing floor bar → previous bar's close (110.0). Present in `main()` and executed.
- Full fixture suite re-run: **exit 0, final line `ALL FIXTURES PASS`** (groups 1–10, including
  the r1 PIT/cost/fold goldens — confirms the remediation regressed nothing in the kernel).

Verdict: **RESOLVED**.

## 3. Regression: freeze chain + dry-run — PASS

- `freezes/eos1_freeze.v1_SUPERSEDED_BLOCKED.json` sha256 `90d5dcdb647c3ad9…af90ff5` equals the
  git blob of `freezes/eos1_freeze.json` at r1-era commit `c52e8eb1` → the r1 freeze is preserved
  **byte-untouched** as the blocked pre-remediation record.
- New `freezes/eos1_freeze.json` (frozen_utc 2026-09-24T15:25:13Z): all 8 code/evidence hashes
  re-verified against current bytes — **8/8 MATCH** (engine 4728850b…, runner 738a09f3…, stager
  unchanged c9ef1c8…, fixtures 20a1ec10…; census/dry_run/feasibility/staged_manifest all match).
  The freeze carries `remediation_r1` and `supersedes` records naming both A7 findings.
- `census.json` / `feasibility.json` diffs vs r1 are `built_utc`-only (data byte-identical —
  verified in the commit diff).
- Dry-run re-executed per instruction: `run_scored.py dryrun` → **exit 0**,
  `dry_run_pass: true`, **84/84** computations, `record_ids_pairwise_distinct: true`, leak scan
  clean (15 substrings, none leaked), `denominator_delta: 0`, all non-BASE_CASH books
  non-vacuous, BASE_CASH all-zero. The fresh output is semantically identical to the committed
  `dry_run.json` with `built_utc` the ONLY differing field; the committed bytes were restored
  exactly after the check (post-restore sha256 `fd616f62…169e3f` == freeze evidence hash →
  chain intact). No freeze file was left modified by this audit.

Verdict: **PASS**.

## 4. Scored-mode absence + budget — PASS

- `scored/` directory exists and is EMPTY — no `scored_summary.json`.
- `audits_a7/go_authorization.json` does NOT exist.
- Registry (`plans/CYCLE_REGISTRY.json` + `researchctl cycle list`): `ACTIVE_LIGHT`,
  `budget {used: 0, max: 8}`, `go_phrase_state: REGISTERED_NOT_CONSUMED`, plan path
  `plans/PLAN_ethusdt_open_search_v1.md`.
- `events.jsonl` records the r1 verdict (`A7_PRELAUNCH_R1_REMEDIATION_REQUIRED`) and the
  remediation (`REMEDIATION_R1_APPLIED`) — no scored-run event anywhere.

Verdict: **PASS**.

## 5. r1 LOW findings implemented as declared — CONFIRMED

- **G6 tie semantics**: now `(not shuf > net_total) and (not inv > net_total)` — a control
  out-earning still kills; an exact tie no longer kills. Matches plan §6 G6 ("must NOT
  out-earn; out-earn ⇒ kill").
- **Per-book fallback counter**: runner captures `px_settle.fallbacks` delta around each
  book/tier run and emits `settlement_price_fallbacks_this_book` (WHITELIST updated). Verified
  equal across the three tiers of every book (e.g. E1-A1 = 1616 at 1.0/1.5/2.0) — per-book
  semantics, no cumulative artifact.

Verdict: **CONFIRMED**.

---

## Verdict

**AUTHORIZED_FOR_STOP1.** Both r1 blocking findings are remediated exactly as specified and
verified from bytes: F-1's G7 is now the ES1-precedent execution-cost semantics with the plan
gate text untouched and a recomputed worst case of 3.134 bps @1.5x (≤ 10, passable); E-1's
settlement pricing can no longer use any price finalized after the stamp instant (0 violations
over all 7,305 real stamps, fixture 10 asserts both branches, full suite exit 0). The chain
regressed nothing: r1 freeze preserved byte-untouched, v2 freeze hashes match 8/8 current files,
dry-run re-run is 84/84 clean with the committed bytes restored exactly, no scored mode was
entered, no GO authorization exists, and the budget remains 0/8 REGISTERED_NOT_CONSUMED. The
prelaunch gate is clean for the owner to type the GO phrase.
