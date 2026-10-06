# TRADE_JOURNAL_SCHEMA_6J_6A — order-intent journal schema for the ADAPT-FXJA lane (PROPOSED)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXJA**, 2026-10-05.
- **Alignment note (required by the dispatch):** `adapt_nq/TRADE_JOURNAL_SCHEMA.md`
  **does NOT exist** in this checkout (verified by file search this wave) — the
  ADAPT-NQ lane shipped per-family `adapter.py` intent records + a shared
  `nq_common` without a journal-schema doc. This document therefore AUTHORS
  the schema for 6J/6A from the two lawful anchors that DO exist and notes the
  **ALIGNMENT RISK**: a future NQ-side schema author should reconcile against
  this file (or vice versa) before any cross-symbol freeze; until then the
  field names below are PROPOSED, never a registered contract.
- Anchor 1: `exec/RUNNER_SPEC_V2.md` §6 ledger envelope
  `{"schema": "futures_5sym_prescored/ledger_row@1", "seq", "row_type",
  "counts_observed", "identity_id", "payload"}` (append-only; observed vs
  published separate counters; REFUSED rows carry `counts_observed=false`).
- Anchor 2: the intent dicts the adapters in this lane actually emit
  (`fx_common.intent_head` + per-family fields).
- 0 PnL, 0 scored runs: this schema journals **ORDER INTENTS on synthetic
  fixtures** (and, post-GO at a future cycle's own gate, scored intents); it
  never journals executions or PnL in this build.

## 1. Row envelope (consumed verbatim from RUNNER_SPEC_V2 §6)

```json
{"schema": "futures_5sym_prescored/ledger_row@1",
 "seq": 1,
 "row_type": "TRIAL | REFUSED | DUPLICATE_RETRY | FOLD | ABORT | PUBLICATION",
 "counts_observed": true,
 "identity_id": "FB6J1-JF1-DRIFT-UP-D1-S2",
 "payload": { ...intent record below... }}
```

REFUSED rows (slots, era-1, lag-law, K4, session-mask) carry the exception's
`record()` shape: `{"code", "slot_id"?, "detail"}` — a refusal is EVIDENCE,
never a silent default.

## 2. Intent payload — common head (all families)

| field | type | law |
|---|---|---|
| `family` | str | JF1/JF3/JF2/RMM6J/AF1/AF3/AF4/RMM6A |
| `identity_id` | str | draft grammar (FB6J1-* for 6J; C6A0-CONT-* PROPOSED shapes for 6A) |
| `status` | "INTENT" | never "EXECUTION" in this build |
| `session_date` | ISO date | carried data, never re-derived from ts |
| `symbol` | "6J" \| "6A" | |
| `fold_id` | F1..F4 \| null | SPEC_6J §8 map |
| `era` / era fields | see §3 | 6A only (era1/era2) |
| `warmup_ok` | bool | ATR law (daily or same-window per family) |
| `exclusion_flags` | [str] | non-empty ⇒ NO-TRADE row (fail-closed) |
| `decision_slot_dependencies` | [str] | the full P5-* block: P5-FXJA-D1..D5, P5-HYPO-OD2..OD4 |
| `tick_size`, `multiplier` | float/int | 6J: 5e-07/12,500,000; 6A: era-aware |
| `labels` | [str] | `["SYNTHETIC FIXTURE", "PROPOSED DRAFT", "NO EXECUTION"]` |
| `no_trade`, `no_trade_reason` | bool/str | the fail-closed audit trail |

## 3. Signal-family fields

| field | families | law |
|---|---|---|
| `window_move` / `trigger_close` | JF1/JF3/AF1/AF3 | **6J direction law**: in 6J PRICE terms — `6J UP = yen STRONG` (orientation proof `6j_orientation_recheck.json` sha `6ca0baeb…`). **`quote_direction` / `quote_direction_law` MUST be journaled on every 6J row** (`"USD_PER_JPY__6J_UP__JPY_STRONG"`) |
| `tail` | all | UP/DN in the symbol's own price terms |
| `direction` (+1/−1), `side` BUY/SELL | all | 6J long = long yen strength; 6A long = long AUD strength |
| `decision_time` | event families | the LAWFUL decision instant (window close / trigger close); BoJ minute stamps NEVER journaled (NOT_IN_CORPUS; P5-HYPO-OD2) |
| `regime_context` | JF2 | disclosure-lagged label + visible ops + K status; same-day op labels are REFUSED rows, never payloads |
| `event_context` | all | trigger law + event type + stratum (e.g. `REGIME_CHANGE_DESCRIPTIVE_ONLY`) |

## 4. 6A-era fields (the era law is load-bearing on every 6A row)

| field | law |
|---|---|
| `era` | `era1` (2020-01-02..2020-11-20, 1e-04 = $10.00/tick) \| `era2` (from 2020-11-23, 5e-05 = $5.00/tick); measured boundary, data-side PROVISIONAL pending D8 |
| `tick_value_usd` | era value actually used ($10.00 era-1 / $5.00 era-2) |
| `cost_preview.era` | the cost ladder chosen by the ENTRY session — **no-back-cast**: era-2 models never back-cast; era-1 trade intent is a REFUSED row (`REFUSED_ERA1_DESCRIPTIVE_ONLY`), never a priced intent |
| `cost_preview.notional_of_record_usd` | era-1 $69,120 · era-2 $66,960 · (6J $79,787.50) |
| `contingency` | `"CONTINGENCY-PB3-PARK — machinery, never activated"` on every 6A row |

## 5. Fill / exit fields (conservative fill law, D5)

`order_type` ("MARKET_NEXT_BAR_OPEN"), `ts_entry`, `entry_ref_price`,
`sl_price`, `tp_price` (tick-grid rounded; SL 1.0×ATR, TP 2×SL),
`ts_exit`, `exit_ref_price`, `exit_reason` (SL-priority on same-bar TP/SL;
SESSION_CLOSE / switch+K time exits), `exit_resolution`
(RESOLVED | PENDING_UPTO_ASOF), `atr20_points`/`atr20_window`.
BBO/queue/limit claims NEVER journal (`REFUSED_PENDING_OWNER_DECISION`
P5-FXJA-D3).

## 6. Cost fields (MODELED COST everywhere)

`cost_preview` = `fc.cost_per_side_usd(...)`: `{era, tier, slip, stress,
fee_usd, spread_proxy_usd, slippage_usd, session_floor_entry_usd,
cost_per_side_usd, cost_rt_usd, notional_of_record_usd, cost_rt_bp_of_notional,
labels: ["MODELED COST","UNDER REVIEW","VERIFIED_VS_ACCOUNT=NOT_RUN"],
fill_model, forbidden_words_respected}`. The words "measured cost"/"complete
cost" are FORBIDDEN in any journaled string; a request for a verified label
is a REFUSED row (P5-FXJA-D4).

## 7. Chain fields (RMM legs)

`guard_disclosure` (`fc.measure_and_disclose_guard_violations`:
violations, n, explicit_guard_mandatory, chain_sign_flip), `mode` (ABRUPT/
GRADUAL), `trigger` (`cease_guard_no_bars` | `k5_crossover`), `timing_law`
("decided at close t, effective t+1" verbatim), event-stacking exclusion
flags, extremal-stratum descriptive-only markers.

## 8. Provenance + prohibition block (every journal file)

Every journal MUST carry: `provenance: SYNTHETIC` for every consumed panel;
the base SHA + worktree; slot states (`fx_common.GUARDS` snapshot, all
unsigned); and the prohibition block: no real governance/registry/GO/ledger/
lock writes; no PnL; no scored-run claims; real-data adapter execution
NOT_RUN (P5-FXJA-D1 / P5-FXJA-D5).

## 9. ALIGNMENT RISK (restated)

`adapt_nq/TRADE_JOURNAL_SCHEMA.md` does not exist this wave. If the NQ lane
authors one later, the reconciliation duty (shared field names: `identity_id`,
`no_trade_reason`, `cost_preview`, `labels`, ledger envelope) is a
pre-registration A7 item for whichever cycle first runs both symbols. Until
then this schema is the 6J/6A-side PROPOSED reference.
