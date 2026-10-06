# RUNNER_COMPAT_6E_6B — scored-runner requirements per symbol + acceptance checks (DRAFT)

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **FXEB**, 2026-10-05. PREP-only:
  no runner is modified or executed here; this is the compatibility contract the EXEC
  lane's symbol-parameterized runner v2 must satisfy for 6E/6B **if and after** the
  pre-freeze gate list (FREEZE_BUILDER_SPEC §3) is signed.
- **CONDITIONAL-ON-PB2-LIFT DRAFT — PB2 HOLD (6E/6B) stands.**

## 1. Contract spec the runner must carry (per symbol)

| requirement | 6E | 6B |
|---|---|---|
| Contract size / quote | EUR 125,000; USD per EUR | GBP 62,500; USD per GBP |
| **PnL semantics** | **USD-quoted ⇒ PnL in USD directly**: `pnl_usd = (p_sell − p_buy) × 125,000`; NO currency conversion of PnL, no quote-currency bookkeeping | **USD-quoted ⇒ PnL in USD directly**: `pnl_usd = (p_sell − p_buy) × 62,500`; same law |
| Tick value | 0.00005 = $6.25/tick (50,000 int-nano; GCD-verified) | 0.0001 = $6.25/tick (100,000 int-nano; GCD-verified) |
| Settlement-currency note | deliverable FX contract; settlement differs from quote currency — **irrelevant to this program: time exit 16:00 CT and roll lead ≥13 observed days mean no position ever approaches delivery; delivery terms verbatim NOT_RUN (sizing facts only)** | same note, GBP settlement |
| Price fixed point | 1e-9 int-nano; no float prices anywhere in fills/accounting | same |
| Spread/dash filter | `raw_symbol` containing `-` excluded; held-contract restriction ON (prefix == held label) | same; NO contract_registry artifact (registry cross-check NOT computable; official-calendar cross-ref) |
| Session masks | 17:00 CT (D-1) → 16:00 CT + 60-min break; `6E_deep_lib.SEGMENTS` CT-minute partition; DST via zoneinfo | same template; `6B_deep_lib.CITY_SEGMENTS` tz-aware labels; London local clock for bucketing (minute-720 anchor law) |
| Event stamp injection | FOMC 58 in-panel stamps (13:00 CT anchor; 2020 emergency EXCLUDED from base) + ECB 55 (14:15 CET/CEST stratum) + BLS CPI/EMPSIT 07:30 CT (vintage table as-of-D) | MPC 56 in-panel stamps (12:00 London, minute-720; change/hold split 22/34 descriptive) + FOMC 58 + BLS same. All keyed to vintage as-of decision date; current-calendar inference FORBIDDEN |
| Cost binding | COST_CONTRACT §3.1 ladder exactly (S1/S2/S3 ×1.0 gate, ×1.5/×2.0 views; 2.46 USD/side fee layer; $18.75 spread proxy; A/B reg variant per P5-OD7 ruling) | COST_CONTRACT §3.2 ladder exactly (same USD fee/spread/slip; 6B bp larger by notional) |
| Roll routing | 27 measured switch dates; T-5 + cease-guard DRAFT law; NOT_OBTAINED quarters excluded per-quarter | 27 measured switch dates; k=5 + cease-guard carried; 2023Q1–24Q2 quarters excluded per-quarter |
| Fold routing | 4 folds + K-views per SPEC_6E §7; folds multiply evaluation never identities; S1 SEALED_UNTOUCHED | same per SPEC_6B §7, with 6B London-drift split as mandatory view |
| Holiday posture | evidence-based 2023-11-24 exclusion + 93 fail-closed cells + aged-out neighborhoods (CALENDAR §3.1) | **NO exclusion implementable; 0/42 hole declared verbatim in every output** (CALENDAR §3.2) |

## 2. Acceptance checks (each must PASS with command + artifact before any scored run)

- **A1 row counts**: annotated parquet rows == 3,054,311 (6E) / 2,549,633 (6B); sha256
  equality with §1 pins of FREEZE_BUILDER_SPEC.
- **A2 held chain**: held sessions == 1,746 (2020-01-02..2026-10-01) both symbols;
  held_calendar sha equality.
- **A3 tick grid**: close-on-grid share on the declared grid == 1.0 in the 5 K6GATE
  sample windows per symbol (GCD 50,000 / 100,000 int-nano).
- **A4 session bounds**: every held session's first bar 17:00 CT ± maintenance-break
  handling; last bar ≤ 16:00 CT; segment column values ⊆ declared partition tables.
- **A5 stamp injection**: count of injected event stamps == 58 FOMC (both) + 55 ECB (6E)
  + 56 MPC (6B) + CPI/EMPSIT in-window rows; each stamp carries its as-of vintage key;
  zero stamps derived from current calendars.
- **A6 cost binding**: runner's recomputed all-in ladder == COST_CONTRACT tables
  (27.46/33.71/39.96 per side; RT 54.92/67.42/79.92 ×1.0; ×1.5/×2.0 views) to the cent.
- **A7 exclusion replay**: 6E exclusion list replay == 1 evidence-based + 93
  fail-closed cells; 6B prints the 0/42 hole verbatim; NOT_OBTAINED quarters excluded.
- **A8 fold routing**: fold boundaries == SPEC §7 draft; fold count == 4; warmup
  carve-out == 60 held sessions at each fold head; K-views emitted as views.
- **A9 identity enumeration**: byte-exact against the signed CONV-D slice
  (IDENTITY_BUDGET §4 string set) — nothing outside the signed table may instantiate.
- **A10 held-contract discipline**: any fill/trade series references only held-contract
  bars (spot-check mirrors K6GATE §0.7 re-derivation: 6E 0.3773% RTH-gap reproduction).

## 3. Explicitly OUT of runner scope until owner signatures land

PB2 consumption, ceiling consumption, any scored cell, any dry-run that computes
strategy outcomes (dispatch absolute: record NOT_RUN and put in the authorization packet
instead), any ledger/registry write, any parameter tuning. Missing evidence = NOT_RUN,
never PASS.

— End RUNNER_COMPAT_6E_6B.md. Conditional-on-PB2-lift draft.
