# A7 TERMINAL AUDIT — cycle FOREX-FREE-V2

- Role: independent terminal auditor (**audit-only; no repairs**)
- Measured (UTC): 2026-09-04T11:17:33Z (machine clock; see F3 on a ~1h stamp-skew note)
- Audited head: `a86e3f794a025e327b670c2c5fecc5e9abfd3431` (tip `orca/forex-free-v2-integration`; branch `orca/forex-free-v2-a7-terminal` created here)
- Cycle base: `bee64beaf2637ea51216cffc6be6393d545bf474` (FOREX-FREE-V1 terminal)
- Claimed W2: `a68764d8f1501b27d07840de6a8fce11ec8eaa5b`
- Method: everything recomputed from file bytes — ledger rows re-digested with the runner's own canonical recipe (`json.dumps(sort_keys, separators(',',':'), ensure_ascii=False)` → sha256), `stage_a_gates` re-implemented from the twin runner source and evaluated over each row's own fields, staged data re-hashed, all ledgers re-hashed and cross-compared. **No scoring was run.**

## Verdict

> **FOREX_FREE_V2_TERMINAL_AUDIT_PASS — terminal label `FOREX_FREE_V2_REJECT_ALL` CONFIRMED.**
> C1..C8 all PASS. Findings: 0 CRITICAL / 0 HIGH / **1 MEDIUM (F1)** / 3 LOW / 2 INFO — none verdict-changing.

## Per-check results

### C1 PIN CHAIN — PASS
- Both twins `git rev-parse HEAD` == `a68764d8f1501b27d07840de6a8fce11ec8eaa5b` == W2, both detached.
- `w2_freeze.json` byte-identical across e-exec-1 / r-reproduce / integration copies; all **30** code/spec hash checks (9 code + 6 spec × 2 twins) match the actual twin blobs — 0 mismatch.
- `staged_data_manifest.json`: **174 entries** per twin; independent re-hash replay **174/174 PASS in each twin**, 0 mismatch / 0 missing; manifest W2 == W2.
- Twins tracked-clean: all porcelain lines are `??` run artifacts (7 / 5); 0 tracked modifications.

### C2 LEDGER — PASS
- Committed `scored_ledger_published.jsonl`: exactly **6 rows**; every line is exactly canonical JSON bytes.
- All 6 digests recompute (strip `digest` → canonical bytes → sha256) == stored; **6 unique digests**.
- `cell_ids` == the six authorized in `w2_launch_verdict.json` (exact set).
- `event_log.jsonl`: 15 events; `SIX_CELLS_SCORED` **exactly once**, is the **last** event; 0 events after. (No per-digest events exist; once-only is enforced by the digest-presence check under `flock` in `publish_cell` — verified in source.)
- Ledger sha256 `1be279ef18d6baa2…707c906` == `reproduction_report.ledger_sha256_exec` == e-exec-1 local == r-reproduce local → **byte-identical ×3**; `REPRODUCTION_ALL_MATCH`, `all_digests_match=true`.

### C3 GATES/METRICS SANITY — PASS (with finding F1)
- `expectancy == round(total_pnl/trades,10)` for 6/6.
- Recomputed `stage_a_gates` reproduces `gates=False` and the stored `gate_reasons` **exactly** (list equality) for 6/6; `EXPECTANCY_NONPOSITIVE` present in all.
- MDD 5907.8–16090.5, all > 2500. `break_even_cost_bps` −0.8239…−0.0172, all ≤ 1.5 and all **negative** (gross edge negative before any cost).
- All 17 `w2_freeze.frozen_gates` items match the twin runner source constants (14 numeric + purge_days + folds + session-gate) — 0 mismatches.
- Stress deltas vs base: tier1.5 = 0.0 exactly ×6; tier2.0 = −0.070 / −0.045 / **+1.756** / +0.230 / +0.347 / −0.056 — all stress expectancies remain negative; every stress gate still FAILS.

### C4 RECONCILIATION — PASS
- `sched_trades = trades + weekend_gate_dropped + purged_trades` reconciles **exactly** against the pre-outcome (pre-W2, outcome-blind) A9-F/prelaunch schedule counts: family1 anchor `1541+151+16 = 1708` (prelaunch: "full 1708"); family2 anchor `3830+100+123 = 4053` (prelaunch: "anchor trades 4053").
- Note: `decisions` is go/no-go decision points incl. void entries (arm-invariant), not a schedule trade count (F6).
- Rows byte-identical across exec / repro / committed; `state.json` summary matches ledger for all 6 cells.
- `replay_summary.json`: mode scored, the 6 scored cells all `published_now=0`; `execution_summary.json` first pass `published_now=[1,1,1,1,1,1]` — publish once, replay zero-delta.

### C5 DIRECTION/CONTROL — PASS
- family1: anchor −3.8040, control −4.6478 → control < anchor (coherent control, no rescue) ✔
- family2: anchor −3.0925, control −3.0344 → |Δ| = 0.058 ≤ 0.5 (placebo parity ⇒ mechanism not distinct) ✔
- Neighbours −4.2973 / −3.4172, both negative (do not support) ✔
- USD |corr|: 0.021 / 0.047 / 0.038 / 0.018 / 0.069 / 0.072 — max 0.0723 ≤ 0.30 for all six ✔ (event log "≤ 0.072" matches at rounding)

### C6 DENOMINATOR — PASS
- V1 ledger: exactly 6 rows, sha256 `066db4337e31139d…77eecd7`, **byte-identical to `bee64be`'s version**; zero diff on `research/control/forex_free_v1_run/` across the cycle.
- V2 adds exactly 6. Historical forex denominator 12 = V1 6 + V2 6 as claimed.

### C7 BOUNDARIES — PASS
- 60 changed paths `bee64be..a86e3f7`: research/control(21), proposals(12), tests(9), assets(8), audits(6), plans(2), dry-run reports(2). **No** `research/control/forex_run/` path, **no** S1-named path, **no** data_raw in diff; `git ls-files | grep data_raw` empty repo-wide.
- No credentials: 0 hits for api_key/secret/passphrase/bearer in V2 assets+control; only `AUTHORIZATION_TOKEN = "GO FOREX V2 SCORED EXECUTION"` (W2-gating phrase, allowed).
- **0 merge commits** in the cycle; `a86e3f7` and every cycle commit unreachable from main (main tip `b6d9790`); 0 `origin/*forex-free-v2*` refs; 0 scoring workers in `ps`; integration and r-a7-terminal trees clean.

### C8 VERDICT LABEL — PASS
6/6 gates FAIL with EXPECTANCY_NONPOSITIVE (recomputed), 0 survivors, evidence complete and committed (replay zero-delta, reproduction ALL_MATCH byte-identical) → BLOCKED/INCOMPLETE inapplicable, no survivor label applicable, super-family merge caveat moot. Strongest allowed label: **`FOREX_FREE_V2_REJECT_ALL`** — confirmed.

## Findings

| ID | Severity | Finding | Verdict impact |
|----|----------|---------|----------------|
| F1 | **MEDIUM** | **Stress-tier cost multipliers never applied to booked PnL.** Family trade dicts carry no `cost_tier`; the runner books every trade via `tr.get("cost_tier", 1.0)`. Numeric proof from the ledger: implied per-side cost = exactly 1.500 bps in base AND tier1.5 groups of all 6 rows; tier1.5 metrics byte-identical to base ×6. So `stress.tier1.5` duplicates base and `stress.tier2.0` measures the frozen one-event delay at base costs — the frozen 2.25/3.00 bps cost stresses were never exercised in published PnL. | **None.** All cells fail base expectancy; break-even bps negative for all 6 ⇒ higher cost tiers are strictly worse; no gate can flip. REJECT_ALL robust a fortiori. |
| F2 | LOW | family1:control tier2.0 stress expectancy +1.7564 vs base (delay re-timing; still −2.8915, total_pnl −6557.86, pf 0.744 → stress gate still FAIL). Consequence of F1 semantics. | None |
| F3 | LOW | Self-reported control-artifact UTC stamps (12:10–12:15Z) lead machine-verifiable UTC (commit 11:06:03Z; audit clock 11:17:33Z) by ~1h; unresolvable internally. All evidence verified from bytes, timestamp-independent. | None |
| F4 | LOW | Ledger rows carry static `"published": false` (set pre-publication in `compute_cell`; never flipped in the published record). Publication evidenced by 5 independent signals. | None |
| F5 | INFO | Event-log narrative "173 files/tree" vs operative staged manifest 174 (replayed 174/174 ×2). Manifest authoritative. | None |
| F6 | INFO | `decisions` = decision points incl. void, not schedule trade count (2767 / 11765, arm-invariant). | None |

## Attestation

**audit-only; no repairs.** All figures above were independently recomputed from file bytes (ledger re-digestion, gates re-implemented from runner source, staged data re-hashed, ledgers cross-compared byte-for-byte). No scoring was run; no file outside `research/audits/forex_free_v2/terminal/` was modified.
