# A7-1 Pre-API Audit — JEV-REGIME-ROUTER-V1

- Auditor: A7 (independent, fresh context; artifacts-only; no implementation touched)
- Date: 2026-09-22 (audit performed 04:12Z)
- Worktree: `.worktrees/jev-regime-router-v1/integration` — branch `orca/jev-regime-router-v1-integration`, HEAD `7c83d563d34f6b8c65fed0922eed560e5bcd1ded`
- Machine-checked companion: `a7_1_pre_api_audit.json` (`jrv1_a7_1_pre_api_audit@1`)

## Verdict: REFUSED_WITH_ACTIONS

Zero-unresolved-HIGH/CRITICAL is **not** met: 1 CRITICAL + 2 HIGH findings are
unresolved. A7-1 does **not** authorize the STOP-1 report yet. Every finding
below is concrete, evidence-backed, and cheap to fix; none requires re-running
the freezes or the plan.

| Severity | Count |
|---|---|
| CRITICAL | 1 |
| HIGH | 2 |
| MEDIUM | 1 |
| LOW | 4 |

## What was audited and how

Every checklist item was verified by reading code and recomputing from bytes —
not by trusting names, docstrings, or green tests. I re-ran both suites
(pytest 95 passed / 0 failed; adapter `tsc --noEmit` clean + `node --test`
57 pass / 0 fail), re-measured the data census from the parquet bytes
(35,039 rows, 0 interior 15m gaps, 8,759 complete H1 hours, 2 partial edge
hours — equal to the freeze), recomputed SPY fold decision counts from the
frozen cache bytes (688/688/688/687 = 2,751 = 2,943 − 192), re-verified the
12-file freeze sha chain (all MATCH), byte-compared the embedded regime-label
contract in `freeze_digests.ts` against the on-disk freeze (identical), and
ran my own cross-language digest experiment on the 25 real prepared request
lines.

Checklist verdicts: A FAIL (one sub-item), B PASS, C PASS, D PASS, E PASS,
F PASS, G PASS, H PASS-with-finding, I NOT-CONTAMINATED, J PASS, K FAIL
(same sub-item as A).

## The three findings that block

### F1 (CRITICAL, before bulk): Python and TypeScript compute different `input_digest` for the same state

`adapter_contract.json` §5a requires `input_digest =
sha256(canonical_json(state) || requested_model)` to be computed identically
on both sides of the boundary. It is not. Python's `canonical_json`
(`json.dumps`, sorted keys) renders doubles `< 1e-4` in exponent form
(`-8.779711216487518e-05`); TypeScript's `canonicalJson` (`JSON.stringify`)
renders the same double as `-0.00008779711216487518` (and exponent formats
differ again above `1e-7`: Python `1e-07` vs JS `1e-7`).

Measured on the 25 real prepared request lines in
`runtime/requests_btcusdt.jsonl`: **10 of 25 (40%) digests differ** between
`jrv1/freezes.py:canonical_json` and `adapter/src/contract.ts:canonicalJson`.
Real BTC H1 features land in the divergence window constantly
(`ema_slope_fast/slow`, small `r1`).

Consequence at bulk: every such state's response carries the TS-side digest;
Python's `validate_response_line` flags `input_digest_mismatch` →
`SCHEMA_ERROR` → `TRANSITION_UNKNOWN` — **after the billable call was made**.
Roughly 40% of an ~11,318-call budget would be converted into forced-UNKNOWN
decisions. Nothing crashes; nothing is scientifically corrupted (fail-closed by
design) — the money is simply burned. The existing test suites cannot catch
this: every TS test vector uses values ≥ 1e-4.

Required action (before bulk; recommended before the STOP-1 GO request):
pin canonicalization to a single authority. Cleanest options: (a) quantize
`feature_vector` to a fixed decimal grid in the payload before digesting on
both sides, or (b) carry the Python-computed `input_digest` in the request
line and have the adapter echo/compare instead of recompute. Add a
cross-language round-trip golden test using real-magnitude values (< 1e-4).
This is a payload-shape change — it must land before any live call so the
canary budget (≤ 100) measures the final request format.

### F2 (HIGH, before bulk): the `prior_regime` (f17) chicken-and-egg has no implemented bulk mechanism

f17 = persisted regime in force at t−1, which depends on prior decisions,
which depend on the calls. The only implemented bulk-preparation path
(`run.py prepare-requests`) walks the timeline in non-strict mode against an
empty cache, so the request lines carry **provisional priors** (measured: the
25-line file is `null` then `TRANSITION_UNKNOWN` throughout). At scoring,
`sequential_timeline(strict=True)` recomputes priors from the cache; wherever
the true prior differs from the sent prior, the digest changes and the cached
(billable) decision fail-closes to UNKNOWN. A naive batch bulk therefore
scores ≈ all-UNKNOWN.

The obvious fixpoint loop (re-prepare after ingest, re-call changed states) is
**impossible** with the current store: `DecisionStore` and
`ingest-responses` refuse any second line for an existing `state_id`
(duplicate incident), so a changed-digest line can never be scored — and
re-calling would violate one-call-per-state anyway.

The remaining correct design is a strict sequential per-state loop (prepare 1
state → call → ingest → next), which nothing implements or tests. Required
action (before bulk): implement + golden-test the sequential replay loop and
demonstrate end-to-end digest identity on a mock pass. Note F1 must be fixed
first or the sequential loop still mismatches 40% of digests.

### F3 (HIGH, before scored phase E): positions can span fold boundaries — the §2.4 embargo law is violated

Frozen fold boundaries are non-adjacent (BTC: fold 1 ends 09:00Z, fold 2
starts 10:00Z; SPY: end date d, next start d_next). `folds_from_regime_ts`
uses `a < ts_open <= b`, so each boundary leaves BTC 4 exec bars / SPY 1
session in **no fold** (verified on the frozen calendar: sessions 2018-07-02,
2021-03-26, 2023-12-19 belong to no fold). `targets_from_regime` computes
targets for ALL exec bars without fold gating, and the engine will happily
open a position from the fold-end bar's close signal into a gap bar — which
then spans into the next fold with no boundary event.

Proven at audit with an in-memory synthetic run (no real data, no arm
outcomes): trade entered at gap bar 11, exited at fold-1 end bar 25
(`fold_flat`, `fold_id=1`); `sum(fold_net_pnl) = −60.0601` while
`totals.net_pnl = −19.9600` — **fold attribution does not reconcile with
totals whenever gap trading occurs**. Per-fold series feed the concentration
kill (≤ 0.50), margin-to-fail (P-2) and DSR/PBO, so this silently corrupts
exactly the metrics the gates depend on.

Required action (before phase E; recommended before STOP-1 since it changes
the runner): fold-gate the engine (no entry/exit/holding on exec bars outside
a fold; suppress entry signals at fold-end bars; gap bars forced FLAT) and add
a runner assertion `sum(fold_net_pnl) == totals.net_pnl`.

## MEDIUM and LOW findings

- **F4 (MEDIUM, before STOP-1):** plan §9 prose says "≈8,568 H1 states − 192
  ≈ 8,376; total ≈ 11,100", contradicting the frozen fold contract
  (8,567 + 2,751 = **11,318**, both recomputed from primary bytes at audit).
  The STOP-1 report must quote the freeze numbers; the plan prose understates
  the bulk by ~2%. (Token estimate: a real state line is 386 bytes ≈ 96
  tokens; prompt ≈ 255 tokens with definitions repeated in instructions and
  options → ~430 input tokens/call; the plan's 1,200–1,800 is a consistent
  conservative ceiling.)
- **F5 (LOW):** arm A enters at the second exec bar open of each fold, not
  the first as the `engine.py` docstring claims (signal at fold-start close,
  fill next open). Causal and conservative; fix the docstring or timing.
- **F6 (LOW):** BTC funding at 8h boundaries uses the latest bar close as
  reference price, not the boundary price; deterministic and arm-symmetric,
  but undisclosed in `cost_contract.json` — disclose.
- **F7 (LOW):** adapter cache hits replay without re-checking
  `response.model == pin`; Python re-validates fail-closed at scoring, but a
  pin change would silently void cached billable decisions. Note in the bulk
  runbook.
- **F8 (LOW):** `rv24`/`vol_z` use population std (ddof=0); the contract is
  silent on the convention. Consistent across arms; record or disclose.

## Checklist summary

- **A Plan conformance — FAIL (one sub-item).** Clocks, warmup 192, 4
  chronological folds, decision/PIT semantics, stale-decision FLAT and SPY
  adjusted-series law all verified in code and against re-measured data.
  Fail: "no position spans folds" (F3).
- **B Feature causality — PASS.** Every window strictly trailing
  (`close[t-w+1:t+1]`, `rv24[t-168:t]` exclusive); indicators recursive/SMA-
  seeded causal; warmup exactly 192; non-finite → LOCAL_INVALID never sent;
  mutation test confirms perturbing t+1.. never moves features at t; no
  counterexample found.
- **C Anonymization — PASS.** Payload is exactly
  `{feature_vector[16], prior_regime}` on both sides (TS validator enforces
  the shape); state_id = sha256(salt||bar_ts)[:16] opaque; real request lines
  contain no symbol/date/price/event; tests assert it.
- **D Regime definitions — PASS.** On-disk label contract sha ==
  manifest == embedded digest; embedded text verbatim-equal; 5 labels exact;
  free-text → SCHEMA_ERROR → UNKNOWN; definitions outcome-blind; prompt built
  from the embedded copy only.
- **E Pins — PASS.** `@typesafe-ai/sdk` exact `0.6.0` (package.json +
  package-lock single occurrence); `jev-latest`/missing pin → exit 3 unless
  `--mock`; response model == pin both sides; `maxRetries: 0` and
  `timeout: 10000` on client + the single `systemOne` call site (retry-scan
  re-run); `models_probe` writes the list, selects nothing;
  `model_pin.json` is `CANDIDATE_UNVERIFIED`.
- **F Credential safety — PASS.** Name-only env checks; SDK env fallback;
  redaction + credential tests pass; sentinel/dummy literals only in tests;
  key currently UNSET; no key material anywhere in the namespace.
- **G Fixtures — PASS.** 6 fixtures with frozen acceptable sets; frozen in
  4377c700 (09:41+07) which predates every runtime artifact (earliest
  10:53+07); zero live-mode cache entries; mock canary labels re-derived by
  hand match the frozen sets; FIX6 LOCAL_INVALID never sent.
- **H Cost/call — PASS with finding.** 8,567 + 2,751 = 11,318 billable states
  (freeze authority; plan prose inconsistent, F4); token estimate ~430/call,
  plan's 1,200–1,800 a consistent ceiling.
- **I Incident-JRV1-1 — NOT-CONTAMINATED.** The five ungated computations ran
  10:53–10:55+07, strictly after the last commit touching any freeze, prompt,
  mapping, persistence or feature file (≤ 10:52:42); `git diff 255fcc7c..HEAD`
  = `INCIDENTS.md` only; `git diff 4377c700..HEAD` over `freezes/` is empty;
  manifest re-verified 12/12. Contamination was chronologically impossible.
  The process breach stands as disclosed; the 12 scored cells remain
  uncomputed; smoke namespace stays kill-only.
- **J Tests — PASS.** 95 pytest + 57 node, all green. Three golden tests
  re-derived independently: (1) persistence switch at bar 7 (dwell 7 ≥ 6,
  streak 2 ≥ 2) and cooldown bars 8–10 / eligible 11 match `step()`;
  (2) cost-once round trip hand-computed (fees 113.235294, slip 22.647059,
  net 26,334.705882, equity 126,334.705882) matches the engine accounting;
  (3) rv_pctile 168/168 hand case equals the implementation.
- **K Dishonesty scan — FAIL (F3).** Otherwise clean: next-open fills, stop
  on post-entry bars only, costs once per fill (1e-12 equity identity),
  funding signed correctly (longs pay / shorts receive, once per boundary),
  SPY short unreachable (mapping-freeze long-only), S1 denial tested, no
  broker/order surface, degenerate metrics return NaN/None not 0, seeds are
  constants, arm F Q-11 failure is disclosed (`null_invalid_flag`), not
  hidden.

## Required actions before proceeding

1. (CRITICAL, before bulk — ideally before STOP-1 GO) Fix cross-language
   digest canonicalization (F1) + cross-language golden test.
2. (HIGH, before bulk) Implement and test the sequential per-state bulk
   replay loop so f17 priors and digests are exact (F2).
3. (HIGH, before scored) Fold-gate the engine; add
   `sum(fold_net_pnl) == totals.net_pnl` reconciliation (F3).
4. (MEDIUM, before STOP-1) Quote the frozen 11,318-state projection in the
   STOP-1 report; disclose the plan-prose discrepancy (F4).
5. LOW items F5–F8: fix or disclose at the phases indicated in the JSON.

After 1–4 land, a delta re-audit (A7-1-r1) can authorize the STOP-1 report.
