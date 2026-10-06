# INTENT_SEAM_SPEC — the REAL intent-execution seam (wave-4 WIRING-FIX)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave 4, lane **WIRING-FIX**,
  2026-10-06. PREP-only; SYNTHETIC fixtures + sandbox authority only.
- Defect fixed (owner audit at `d938e9a5`, evidence
  `freeze_wiring/repro_mixed_direction/REPRO_FAIL.json`, committed
  `f1f69c8e` — kept untouched as history): the positional seam picked the
  runner arm from `intents[0]["direction"]` and made ONE positional trade
  per identity, silently dropping same-identity mixed-direction/extra legs;
  the positional `[signal, entry, filler, exit]` / `hold_bars=2` /
  `F-COMPILED` encoding was accounting-test-only, not a strategy timeline.

## 0. Implementation shape (owner-law decision)

**Chosen: (a) intent-mode extension of `exec/scored_runner_v2.py`.** A new
frozen packet schema `futures_5sym_prescored/intent_packet@1` is executed by
the SAME runner — same CLI, same authority gates, same lock lifecycle, same
reproduction twin, same append-only ledger idempotency, same publication and
finalization law. The existing `spec_packet@1` positional path is
byte-unchanged and the 42-test `exec/test_runner_v2` suite passes unmodified
(measured 2026-10-06).

Why (a) and not (b) (side executor importing accounting primitives): the
owner's test list requires the FULL gate set through the seam — missing
authority / wrong GO / registry mismatch / input drift refusals
pre-computation, twin-mismatch-never-success, publication-failure-keeps-
observed, finalization-fault-non-zero-exit (T-MD10) and retry idempotency
against a shared ledger (T-MD9). Those are ~500 lines of settled runner
law; a side executor would have to duplicate them (or route through the
runner anyway), and "accounting reuse" would need a reconciliation proof
per formula. With (a) the accounting reuse is an identity, not a proof: the
intent engine and the positional engine share the same formulas, cost law,
era law and rounding, and the production path a future registered cycle
calls is literally the same CLI (`scored_runner_v2.py --spec-packet
<intent_packet.json> ...`). Proof-by-parity on the single-trade case is
still asserted (test_intent_seam.py::test_tmd7: positional net ==
intent-seam net == independent SPEC arithmetic).

## 1. The seam contract

```
wired_intent@1 (adapter)  --wiring/intent_executor.build_intent_run-->
  intent_packet@1 + timeline fixture + cost manifest + input manifest
    --exec/scored_runner_v2.py (intent-mode dispatch)-->
  ledger TRIAL rows (one per identity, per-trade journal inside) + FOLD rows
  + published_summary + terminal handoff
```

Wiring entrypoint: `wiring/intent_executor.intent_and_run(groups,
session_bars, folds=..., warmup_bars=..., calendar_excluded_dates=...,
calibrated_era=..., ...)` — the function a future registered cycle calls
per identity group, with the canonical lock around it
(`CANONICAL_INTEGRATION.md`).

### 1.1 intent_packet@1 (frozen SPEC packet, schema
`futures_5sym_prescored/intent_packet@1`)

```json
{"schema": "futures_5sym_prescored/intent_packet@1",
 "encoding": "INTENT_TIMELINE_VERBATIM",
 "provenance": "SYNTHETIC",                       // PREP law; else refuse
 "warmup_bars": 252,
 "calendar_excluded_dates": ["YYYY-MM-DD", ...],  // SPEC exclusion law
 "identities": [
   {"identity_id": "<declared, verbatim>", "symbol": "NQ",
    "cost_tier": "S2", "stress": 1.0,
    "holding_horizon_bars": 2,
    "intents": [
      {"intent_seq": 0, "direction": 1,
       "signal_ts": "YYYY-MM-DD",     // decision timestamp, carried verbatim
       "entry_ts":  "YYYY-MM-DD",
       "exit_ts":   "YYYY-MM-DD",
       "entry_price": 15110.0, "exit_price": 15130.0,
       "exit_reason": "horizon|stop_loss|take_profit|session_close"}]}],
 "folds": [{"fold_id": "F1", "start_bar": 252, "end_bar": 276}, ...]}
```

### 1.2 Trade journal (inside every TRIAL payload, per trade, in submission
order — also mirrored per fold)

```json
{"intent_seq": 0, "direction": 1,
 "signal_ts": "...", "entry_ts": "...", "exit_ts": "...",   // verbatim
 "entry_bar": 275, "exit_bar": 276,                          // timeline idx
 "entry_price": 15110.0, "exit_price": 15130.0,              // era-rounded
 "exit_reason": "session_close", "fold_id": "F1",
 "era": "NQ-era1", "tick_size": 0.25, "tick_value_usd": 5.0,
 "gross_pnl_usd": 400.0, "cost_usd": 57.0, "net_pnl_usd": 343.0}
```

## 2. Execution law: SPEC -> execution (all flow-controlled, none hardcoded)

| SPEC law | carrier | executor behavior |
|---|---|---|
| One trade per intent | packet intents[] | EVERY intent executes as its own trade; per-intent direction (Long AND Short in one identity both execute); submission order preserved (`intent_seq` 0..n-1 enforced); identity ids/table NEVER split or renamed |
| Fold membership | packet `folds` (never F-COMPILED) | entry bar index → the unique fold with `start_bar <= entry_bar < end_bar`; folds validated non-overlapping (a seam trade lands in EXACTLY one fold); an executable entry bar in no fold refuses (`REFUSED_SPEC_INVALID`) |
| Warmup | packet `warmup_bars` | entry bar `< warmup_bars` (or before the first fold) → recorded exclusion `excluded_intents[].reason="warmup"`, no trade, no silent drop |
| Session/event/calendar exclusions | packet `calendar_excluded_dates` | entry on an excluded date → recorded exclusion `reason="calendar_excluded"`, NO trade, run still succeeds; an entry date that is neither a bar date nor a declared exclusion refuses |
| Roll / cease-guard boundaries | identity table + intent dates | routing is DECLARED: the intent lands in the identity it was declared under (post-roll contract identity gets the roll-week trade; the pre-roll identity does not) — proven, not invented |
| Tick era | frozen `symbol_contracts.json` era table | era = LAST row with `effective_from <= ENTRY bar date` (6A: era-1 0.0001/$10.00, era-2 from 2020-11-23 0.00005/$5.00); one trade carries ONE era for both fills, grid rounding and cost conversion |
| Quote direction | contract `long_base_sign = +1` | same formula for every symbol; 6J (USD-per-JPY) long profits when the quoted number RISES (proven positive on a yen-strengthening move; short mirrors negative) |
| Cost regimes | frozen cost manifest (`fee_per_side_usd_by_tier`, `spread/slip_ticks_by_stress` at x1.0/x1.5/x2.0) | per side: `fee(tier) + (spread+slip ticks at stress) * tick_value_usd(ENTRY era)`; net = gross − 2×cost_side; money rounded 6dp. The manifest is encoded by the ONE USD→ticks implementation (`spec_compiler.compiled_cost_manifest`); `calibrated_era` mismatch with any intent entry era refuses (`REFUSED_COMPILE_COST_ERA_MISMATCH`, exit 41 — both directions) |
| SL-priority same-bar | intent `exit_reason="stop_loss"` | same-bar close legal (`exit_bar == entry_bar`); validated inside the holding window |
| Holding horizon | identity `holding_horizon_bars` | `horizon` reason requires `exit_bar == entry_bar + holding_horizon_bars` exactly; other reasons require `entry_bar <= exit_bar <= entry_bar + horizon` (SL/TP/session-close may close early/same-bar) |
| Session-close exits | intent `exit_reason="session_close"` | same-day close legal; carried verbatim into the journal |
| Zero-trade identities | identity with `intents: []` | spec-valid processed anchor: TRIAL row, executed count 0, folds present with n_trades 0, counts toward the observed denominator (processed — never not-run; denominator semantics unchanged) |

## 3. Accounting reuse proof

The intent engine (`compute_intents`) and the positional engine
(`compute_all`) in `exec/scored_runner_v2.py` share the SAME accounting
surface: `era_for` (entry-era law), `round_to_tick` (fill grid),
`gross = direction*(exit-entry)*tick_value/tick_size`,
`cost_side = fee + (spread+slip)*tick_value`, `_r6` money rounding, and the
same `Ledger.append_trials` / twin / publication path. There is NO
reimplemented arithmetic anywhere in the wiring: the builder writes packets
and manifests only, and even the cost manifest and the era lookup are
imported from `spec_compiler` (one implementation of the USD→ticks law and
the C2/C3 gates). Independent parity is proven in
`test_intent_seam.py::test_tmd7`: for 7 covering cases (both directions,
both 6A eras, a 6J trade, an SL exit, a 6E case) the executor net equals a
contract-SPEC reference computed in the test from
`symbol_contracts.json` + the cost constants — NOT from executor code — and
on the single-trade case the positional and intent paths price identically.

## 4. The relabeled positional scope

`wiring/spec_compiler.py` is now labeled `POSITIONAL_ACCOUNTING_TEST_ONLY`
(module docstring; `encoding` field on every compiled spec packet and
compile record). It represents exactly ONE positionally-encoded trade:
groups with >1 intent or mixed directions REFUSE with
`REFUSED_POSITIONAL_SCOPE` (exit 46) — it can never again silently encode a
multi-intent identity. Legal remaining use: single-trade accounting proofs
(e.g. `test_wiring_e2e.py` positional-era proofs, PIT truncation). Real
multi-intent execution is `wiring/intent_executor.py` only.

## 5. Authority gates carried by the seam

- non-SYNTHETIC provenance refuses at the wiring layer
  (`REFUSED_COMPILE_INTENT_INVALID`) and AGAIN in the runner
  (`validate_intent_spec`: `REFUSED_SPEC_INVALID` on
  `provenance != "SYNTHETIC"`) — every real-data slot still refuses; every
  computed run is stamped `SYNTHETIC-SANDBOX`;
- GO / registry / authority / input-drift / lock / stale-marker gates are
  the runner's own, unchanged (the seam adds no bypass and no flag);
- twin (`compute_intents` run twice, faults never injected) blocks success
  on any diff; publication failure keeps the observed denominator and
  quarantines; release/handoff/final-status failures force non-zero exit
  (BUG1/BUG2-class law inherited unchanged);
- ledger reopen/retry: identity-ID idempotency (DUPLICATE_RETRY, never
  recomputed) applies to intent-mode TRIAL rows unchanged (T-MD9).

## 6. What remains owner-gated (unchanged, still NOT_RUN)

- ALL real-data execution (provenance gate; the sandbox stamp is on every
  artifact);
- GATE-0 authority matrix per symbol (NQ d9+ceiling, 6E/6B pb2+ceiling,
  6A pb3+d8+d9+ceiling, 6J 6j_ceiling+ceiling) — `freeze_builder.py`
  unchanged;
- 6A D8-era-aware per-era cost manifests (today ONE calibration era per
  run; a cross-era identity carries an explicitly DECLARED calibration era
  and the C3 gate refuses mismatches — per-era cost tables are the pending
  owner law carrier);
- canonical machine-wide lock integration (sandbox flock is NOT evidence —
  `CANONICAL_INTEGRATION.md` §0);
- budgets/ceilings/decisions D3/D8/D9, PB2/PB3 — untouched;
- registration, typed GO, S1, commits — none in this lane.

## 7. Test surface

`freeze_wiring/tests/test_intent_seam.py` (12 tests, T-MD1..T-MD10 +
validator unit + positional-scope relabel) — each owner-listed test asserts
journal + ledger + denominator state. Wave-3 suite adjustments are
documented in `test_wiring_e2e.py`'s module docstring and in
`dispatch/handoff_WIRING-FIX.json` (ALW denominator, positional PIT,
6A era-boundary; no assertion weakened). Repro:
`freeze_wiring/repro_mixed_direction/repro.py` now exits 0 with
`REPRO_FIXED.json` (verdict PASS: 2 trades, directions {1,-1}, 1 identity
row); `REPRO_FAIL.json` is untouched history.
