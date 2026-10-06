# SYMBOL_COMPAT_MATRIX — per-symbol proof status for scored_runner_v2

Cycle `FUTURES-5SYM-PRESCORED-20261005`, EXEC lane, 2026-10-05.
The runner consumes contract numbers as DATA from
`exec/symbol_contracts.json`. **Every contract-number row is
`VERIFICATION: PLACEHOLDER-PENDING-PER-SYMBOL-LANE`** — OPEN until the
per-symbol lanes (`nq/`, `fx_eb/`, `fx_ja/`) re-derive them against
committed exchange-spec evidence and the VERIFY lane re-checks at a pinned
SHA. Nothing here verifies a contract number; it proves the runner APPLIES
the declared numbers on the real CLI path.

| symbol | contract file era rows | runner path exercised by | era-switch proof | sign/direction proof | cost-law proof | verification status |
|--------|------------------------|--------------------------|------------------|----------------------|----------------|---------------------|
| NQ  | NQ-era1 (0.25 / $5.00 / x20) | T1 (L1 long + S1 short, 2 folds), test_per_symbol_symbols_all_exercised_in_T1_shape | n/a (single era) | gross = dir*move*20 asserted for every trade (T1 invariant) | fee + (spread+slip)*tick_value per side (all T1 trades) | **OPEN — PLACEHOLDER-PENDING-PER-SYMBOL-LANE** |
| 6E  | 6E-era1 (0.00005 / $6.25 / x125000) | T1 (both arms), test_per_symbol_symbols_all_exercised_in_T1_shape | n/a | same invariant, multiplier 125000 | same | **OPEN — PLACEHOLDER-PENDING-PER-SYMBOL-LANE** |
| 6B  | 6B-era1 (0.0001 / $6.25 / x62500) | T1 (both arms), test_per_symbol_symbols_all_exercised_in_T1_shape | n/a | same invariant, multiplier 62500 | same | **OPEN — PLACEHOLDER-PENDING-PER-SYMBOL-LANE** |
| 6J  | 6J-era1 (0.0000005 / $6.25 / x12500000) | T1 + dedicated T18 (test_symbol_laws.py) | n/a | **T18**: USD-per-JPY quote convention; long on rising quote => POSITIVE gross; inverted (JPY-per-USD) misread would flip every sign — explicitly asserted | T18 cost = 2*(fee+(spread+slip)*6.25) | **OPEN — PLACEHOLDER-PENDING-PER-SYMBOL-LANE** (quote-direction NOTE itself re-checked by fx_ja lane) |
| 6A  | 6A-era1 (0.0001 / $10) + 6A-era2 from 2020-11-23 (0.00005 / $5) | T1 + dedicated T17 (test_symbol_laws.py) | **T17**: fixture straddling 2020-11-23 yields BOTH eras; era chosen by ENTRY-bar date; era-1 vs era-2 cost rows differ exactly per tick value; per-price-unit gross factor 100000 in both eras | standard +1 law (T1 invariant) | T17 explicit cost formulas ($35.00 vs $20.00 round-trip at t1/x1.0) | **OPEN — PLACEHOLDER-PENDING-PER-SYMBOL-LANE** (era BOUNDARY date itself also pending per-symbol-lane verification) |
| ES  | ES-era1 (0.25 / $12.50 / x50) — COMPATIBILITY ONLY | static consistency test (test_static_contract_table_internal_consistency) + runnable via any sandbox spec | n/a | invariant covers it | same | **OPEN — carried unverified from the upstream ES cycle as data** |

Static invariants proven for ALL rows of ALL contracts
(test_symbol_laws.py::test_static_contract_table_internal_consistency):
`tick_value_usd / tick_size == multiplier` for every era;
`long_base_sign == +1`; `PLACEHOLDER-PENDING-PER-SYMBOL-LANE` present in
every contract's verification field.

Runner-compat notes for the per-symbol lanes:

1. Fixture contract: CSV `ts,open,high,low,close`; `ts` = trade date
   (ISO date); bars consumed as a plain ordered series — the
   `session_mask_spec` in the contracts file is descriptive only in this
   build (PLACEHOLDER), so session/PIT filtering remains a lane
   deliverable before any real freeze.
2. Identities are declared per symbol in the SPEC packet; the runner
   supports exactly the two deterministic arms (`long-if-bar-up`,
   `short-if-bar-down`) + `hold_bars >= 1` + tier/stress references.
   Richer per-symbol arms are a future-cycle SPEC question, not a runner
   gap.
3. 6A era boundary selection is by ENTRY bar date; folds never change the
   era of a trade. If a lane's freeze needs per-side eras (fill-level),
   that is a SPEC change and must come with new tests.
4. A symbol sandbox may carry a SUBSET of the 5 fixtures (T17/T18 run
   single-symbol); `validate_spec` requires only that every identity's
   symbol has fixture bars with enough length for every fold.
