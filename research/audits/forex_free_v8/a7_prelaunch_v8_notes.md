# A7 PRELAUNCH — FOREX-FREE-V8 (fresh-context)

Verdict: **FOREX_FREE_V8_S0_LAUNCH_AUTHORIZED** — 0 unresolved HIGH/CRITICAL.
Full evidence: `a7_prelaunch_v8_verdict.json` (schema `forex_free_v8_a7_prelaunch_v1`).

Audited HEAD `79ddeb5` on `orca/forex-free-v8-q-a7-prelaunch`, porcelain=0 throughout.
Everything recomputed from bytes; no recorded verdict trusted without re-verification;
nothing repaired; no gate flipped; scored execution attempted WITHOUT authorization
to prove the refusal (exit 2, refusal JSON, zero side effects).

## What was independently reproduced (not just read)

- V8 suite 47/47; inherited V6+V7 118/118.
- `validate_contract` -> PASS; my own `smoke_check_twin_rerun` in a fresh empty
  sandbox -> PASS (driver re-emitted every canon artifact, content-verified).
- Driver sanitized dry-run on real staged bytes -> exit 0; reproduces Q exactly
  (anchor 314 pooled / folds 70-133-111; usable 1640; first usable 2019-04-12);
  recursive leak scan of the report: clean (only `pnl_suppressed` flags).
- All three `arm_config_digest`s recomputed from code == `run_contract`.
- INC-V8-2: re-hashed 5/5 pause pins in working AND committed tree (the p3
  restore `5ca0bcea` IS in commit 79ddeb5) + 13/13 staged files vs manifest.
- Adjudication ruling 1 verified against V7 code bytes
  (`git show orca/forex-free-v7-integration:...exec_driver_v7.py` line 279:
  comparator `"<="`, margin = threshold - observed) and V6's ledger
  (BE 3.4750450694 -> margin -1.9750450694 exact). Ruling byte-true.
- Frozen-spec fidelity: all proposal-1.json mechanics found verbatim in code
  (arms z252/z504/DGS10-level, |z|>=1 entry, 0.5 hysteresis or 21bd exit,
  next-clock re-entry, one position per pair, 252 binding-clock warmup, 3 equal
  folds, 1.5bps/side x {1,1.5,2} tier-2.0 primary, dual books, gates 1..10 in
  frozen order with {gate_id,value,threshold,margin}, per-period series, R1..R4).
  AX2: as-of reconstruction only (`latest realtime_start <= decision date`);
  no current-vintage pull path exists; trailing history as-bound, never re-pulled.

## Findings (2 MEDIUM unresolved — disclosed obligations, not blockers)

- **F1 MEDIUM** — driver `_launch_gate_state()` reads top-level/`launch` keys;
  contract stores them under `launch_gate.*`. Fail-closed (refusal proven);
  must be reconciled by A1 BEFORE the owner GO is typed or the authorization
  step must write driver-visible keys.
- **F2 MEDIUM** — strict `margin > 0` means exactly-2/3 positive folds fails
  gate 3 although the frozen text says ">= 2 of 3" (gate 8 equality likewise).
  Conservative direction (can kill a survivor, never pass a false one); V6
  precedent documented the same class; ruling 3 covered only boolean gates.
  Owner to adjudicate before E-phase verdict interpretation. NOT repaired.
- F3 LOW (resolved): proposal's ~1655/~2019-04-04 usable estimate vs measured
  1640/2019-04-12 — binding-clock warmup semantics, folds split on actual grid.
- F4 LOW: main registry phase prose lags state.json (lifecycle/budget correct).
- F5 LOW (resolved, adjudicated ruling 3): boolean gate encoding deviation.

## Refusals and hygiene

- `scored` without authorization: exit 2, `missing_gates: [s0_launch_authorized,
  owner_fresh_go]`, no ledger, no artifacts dir, porcelain 0.
- No PnL anywhere in control dirs (only rule names and `pnl_anywhere:false`).
- Budget 0/6 (3 bound), S1 SEALED_UNTOUCHED, ledger 233/236, registry ACTIVE_LIGHT.
- Gitignored bytes (staged_vintaged, data_raw/forex_free_v1) copied from
  integration for runs only — never committed (porcelain stayed 0).
