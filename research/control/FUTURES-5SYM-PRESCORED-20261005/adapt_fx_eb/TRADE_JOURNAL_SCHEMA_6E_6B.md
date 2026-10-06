# TRADE_JOURNAL_SCHEMA_6E_6B — intended-order-intent journal row (PROPOSED)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXEB**, 2026-10-05.
- **STATUS: PROPOSED / CONDITIONAL-ON-PB2-LIFT.** This is the payload shape every
  `order_intent(...)` in `adapt_fx_eb/` emits per intended order. It is a SIGNAL/INTENT
  journal, not a fill record: nothing here transmits, fills, or scores; BBO NOT_RUN;
  real-data execution NOT_RUN (P5-FXEB-OD1).
- **Alignment note for the controller**: `adapt_nq/TRADE_JOURNAL_SCHEMA.md` does **not
  exist** in this worktree (the ADAPT-NQ lane ships `nq_common.py` + per-family adapters
  without a schema doc), so this document is AUTHORED HERE and cites the one committed
  ledger shape law, `exec/RUNNER_SPEC_V2.md` §6. **RISK**: when the NQ lane authors its
  own journal schema, the two must be reconciled field-for-field before any shared
  freeze-builder consumes both; until then this schema is FXEB-local PROPOSED.

## 1. Envelope (RUNNER_SPEC_V2 §6, consumed read-only)

Runner ledger rows are:
`{"schema": "futures_5sym_prescored/ledger_row@1", "seq", "row_type", "counts_observed",
"identity_id", "payload"}` — append-only, never truncated, `seq = max(existing)+1`;
`row_type ∈ {REFUSED, TRIAL, DUPLICATE_RETRY, FOLD, ABORT, PUBLICATION}`; TRIAL rows
carry `counts_observed=true`. The FXEB journal payload below is the **per-order intent
content** that a future TRIAL payload would embed per identity per session; it is NOT
itself a ledger row and the adapter never writes a ledger.

## 2. Payload fields (adapt_fx_eb intent row; emitted by every family's order_intent)

| field | type | law / source |
|---|---|---|
| `identity_id` | str | DRAFT grammar `FXF<n>-<SYM>-<ARM>-<TAIL>-<DELAY>-<TIER>[-<STRATUM>]` (IDENTITY_BUDGET_6E_6B §4); RMM `FXRMM-<SYM>-RB<k>`; minting OD2/OD5-gated |
| `session_date` | str | carried panel session_date (never re-derived from ts) |
| `family` / `symbol` | str | FX-F1..F4, RMM / 6E or 6B (fx_common.SYMBOL_LAW) |
| `arm` / `tail` | str | per-family arm pair (HC/HD, RC/RD, SC/SD, GC/GD); tail UP/DN |
| `delay_slot` / `tier` | str | {D0, D1B} draft default (P5-FXEB-OD3) / S2 (CONV-D core) |
| `strata` | list | descriptive stratum labels (MPC_CHANGE/MPC_HOLD, KNOWN_CPI, WEEKDAY/SUNDAY_REOPEN, …) — never base-pool splits |
| `status` | str | `ORDER_INTENT` or `NO_TRADE` (with `flags` + `blocking`) |
| `side` | enum | BUY / SELL from (arm, tail) with `long_base_sign = +1` (symbol_contracts) |
| `entry_ts_intent` / `entry_px_intent` | str / float | conservative next-bar-open fill at the family's fill instant; on the symbol tick grid (asserted) |
| `fill_law` | str | constant disclosure: CONSERVATIVE_NEXT_BAR_OPEN; BBO NOT_RUN (D5; P5-FXEB-OD8); family-specific addenda (T+60s ≥1min post-release for F2; T+5m auction-minute exclusion for F4; latency NOT_RUN for F3; 17:00 thin-window spread-bias hazard for F4) |
| `sl_level` / `tp_level` / `same_bar_priority` | float/float/const | SL = entry ∓ 1.0×ATR(20); TP = entry ± 2×SL_distance; `SL` priority (family exit law); tick-grid rounded |
| `exit_px_model` / `exit_rule` | float/str | deterministic exit walk: SL_TOUCH / TP_TOUCH / TIME_EXIT_1600CT (F1/F2/F3) or TIME_EXIT_0900CT_PROVISIONAL (F4); `NOT_RESOLVED_AT_DECISION_INSTANT` on the PIT-truncated read |
| `horizon` | str | intraday, same session; mandatory flat at the family's time exit |
| `window` | str | F4 only: `WINDOW_A_REOPEN_1700_PRIMARY` (M2c erratum; WINDOW_B is measurement-only and never appears as a signal source) |
| `cost_model` | object | `fx_common.cost_ladder_usd(sym, tier, stress)` row: fee B 2.46 / A-derived 2.47, spread half-turn 18.75, slippage tier, RT USD, bp at notional band, **`gate_consumable: false`** (P5-FXEB-OD6/OD7), `labels: [MODELED COST, UNDER REVIEW, VERIFIED_VS_ACCOUNT=NOT_RUN]` |
| `cost_gate_consumable` | bool | always false while the fee/reg-basis slots are unsigned |
| `k_views` | object | declared evaluation-era labels (K5 era split, DST-mismatch, BLS-2025 regime, …) — never identity splits |
| `provenance` | str | must be `SYNTHETIC` (require_synthetic gate) |
| `pit_asof` | str | the decision/fill instant the row is PIT-consistent with |
| `proposed` | str | constant: PROPOSED — conditional on PB2 lift; no order transmission; no scored consumption |
| `decision_slot_dependencies` | list | `P5-FXEB-OD1..OD11` (the full block the row obeys) |

## 3. NO_TRADE rows

Excluded/structural non-trades emit `{identity_id, status: "NO_TRADE", flags[],
session_date}` (+ `blocking[]` where the flags block). 6B carries
`HOL_GRID_ABSENT_0OF42_DECLARED` as a DECLARATION on every session — it appears in
`flags` but NEVER in `blocking` (declaration ≠ exclusion; the hole is declared on every
6B result).

## 4. Language law (binding on any rendering of these rows)

The words "measured cost" / "complete cost" are FORBIDDEN on any output (A7 §7);
cost surfaces carry MODELED COST / UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN. No row
asserts a fill, a queue position, or a profit. A null at program-feasible n is the
pre-registered death of a family, never evidence of absence (court §c3).

— End TRADE_JOURNAL_SCHEMA_6E_6B (PROPOSED; FXEB-local until reconciled with any NQ schema).
