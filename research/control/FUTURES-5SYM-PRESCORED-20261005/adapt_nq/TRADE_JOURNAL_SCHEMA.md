# TRADE_JOURNAL_SCHEMA — NQ per-trade record + reconciliation contract (PROPOSED)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-NQ**, 2026-10-05.
- **STATUS: PROPOSED** — the schema the ADAPT-NQ adapters emit for intended ORDER INTENT on
  synthetic fixtures, and the reconciliation contract against the exec lane's ledger
  (`exec/scored_runner_v2.py` + `exec/RUNNER_SPEC_V2.md`, consumed READ-ONLY). This file
  authorizes no execution; the ledger below is quoted as the binding target shape for the
  later FREEZE-WIRING lane.

## 1. Adapter journal record (adapt_nq/trade_journal@1 — the `order_intent` output)

Every record is one intended trade (or an explicit NO-TRADE) for one draft identity on one
session. Pure data; no execution; labels carried on every row.

| field | type | law / provenance |
|---|---|---|
| `identity_id` | string | draft grammar `FBNQ1-<FAM>-<ARM>-<TAIL>-<DELAY>-<TIER>` (+ controls `SHDW/ALW/FLAT`); registered cycle ID replaces `FBNQ1` verbatim (`IDENTITY_BUDGET_NQ.md` §3) |
| `family` | enum | NQ-F1 / NQ-F2 / NQ-F3 / NQ-F4 |
| `status` | enum | `INTENT` \| `NO-TRADE` record shape (flag `no_trade: true`) |
| `no_trade_reason` | string \| null | exclusion flag join, `TAIL_MISMATCH`, `TRIGGER_FLAT`, `ROLL_CROSS_UNADJUSTED`, `CANCELED_CONTROL_STRATUM`, `ERA_GATED`, `ATR_WARMUP_INSUFFICIENT`, `HORIZON_BEYOND_PANEL`, `ENTRY_SESSION_NOT_KNOWABLE_AT_ASOF`, `FLAT_ANCHOR_ZERO_TRADES`, `ROLE_B_INTERACTION_GATE_NOT_EVIDENCED` (raised) |
| `session_date` | date | session key (chain sessionization consumed as carried data; DST fall-back absolute-24h quirk preserved-as-measured) |
| `ts_entry` / `ts_exit` | ISO-8601 CT (bar START, D5 schema law) | F1/F2: 1m bar starts (D0 = anchor+1m, D30 = anchor+31m; exit = touch bar or measured last bar); F3: session open/close sessions |
| session context | `session_context` | `era` (A/B, SESSION_SWITCH_DATE 2015-09-21), era-correct close (16:15/16:00 CT), measured `last_bar_ct` (era-A Fridays per-session, never asserted), RTH-core coverage (register value) |
| event context | `event_context` | F1: FOMC statement (14:00 ET anchor = 13:00 CT, trigger move); F2: BLS series + `vintage_known_by`; F3: k-run; F4: refused; controls: CLOCK_ONLY_SHADOW / ALWAYS_IN |
| `side` / `direction` / `quantity` | BUY\|SELL / ±1 / 1 | quote direction `long_base_sign = +1` (USD per index point; long profits when price rises) |
| `entry_ref_price` / `exit_ref_price` | float on 0.25 tick grid | conservative fill law: entry = next bar/session OPEN; exit = SL/TP touch level (same-bar TP/SL ⇒ **SL priority**) or measured session close |
| `sl_price` / `tp_price` / `atr20_points` | float on grid | SL = 1.0 x ATR(20) (prior 20 held sessions, strict past); TP = 2 x SL distance |
| cost components | `cost_preview` | **frozen cost shape** (see §2): `fee_all_in_usd`, `spread_half_turn_usd` ($16.25 = 3.25 ticks x $5.00, 6.5-tick close proxy half-turn, high-biased), `slippage_usd` (S1/S2/S3 = 5.00/10.00/15.00), `cost_per_side_usd`, `cost_rt_usd` = 2 x per-side, `stress` (1.0 gate / 1.5 / 2.0 disclosed), `variant` (A default basis-only while P5-NQ3 unsigned), `labels` = MODELED COST / UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN |
| `fold_id` | F1..F4 \| null | fold map F1 2010-06..2012-12 · F2 2013-01..2017-12 · F3 2018-01..2021-12 · F4 2022-01..2026-09; 2026-10-01 partial tail outside every fold |
| `era_view` | object | declared K-views K-V1..K-V6 (evaluation labels, never identity splits) |
| `exclusion_flags` | list | H1..H5 / FOMC_STANDING_OUTSIDE / EMERGENCY_TIMING / UNTIMED_DAY_LEVEL_ONLY / CANCELED strata (fail-closed ⇒ NO-TRADE) |
| `k3_stratum` | bool | 2020-03..04 concentration stratum (G6) |
| `decision_slot_dependencies` | list | `["P5-NQ1","P5-NQ2","P5-NQ3","P5-NQ5","P5-NQ6"]` — the owner-pending laws this row obeys |
| `contract` / `tick_size` / `multiplier` | — | bound from `exec/symbol_contracts.json` NQ row (0.25 / 20; $2.50 refuse-worthy, P5-NQ4) |
| `labels` | list | `SYNTHETIC FIXTURE`, `PROPOSED DRAFT`, `NO EXECUTION` |

F4 Role-B emits NO journal rows: `order_intent` raises `ROLE_B_INTERACTION_GATE_NOT_EVIDENCED`
(machinery-only). EXPWITCH-NQ emits NO rows: `EXPWITCH_DEAD_AT_GATE`.

## 2. Frozen cost-manifest binding (shape quoted from `exec/RUNNER_SPEC_V2.md` §5)

The runner binds ONE cost manifest carried in the freeze: keys
`fee_per_side_usd_by_tier`, `spread_ticks_by_stress`, `slip_ticks_by_stress` at x1.0/x1.5/x2.0
(RC-4.1; no runtime re-derivation; RC-4.2 stale-print refusal: `1.386` and the 21.006-class
ladder are never consumable). The ADAPT-NQ adapters carry the DERIVED per-side ladder of
`nq/COST_CONTRACT_NQ.md` §3/§4 instead — **A 23.50/28.50/33.50 · B 23.49/28.49/33.49 per side**
(fee all-in + $16.25 spread half-turn + {1,2,3}-tick slippage), RT = 2 x per-side, stress
multipliers x1.0 (gate) / x1.5 / x2.0. The exact mapping adapter-ladder → runner-manifest keys
is the FREEZE-WIRING lane's binding responsibility (flagged, not resolved here); at a future
freeze the manifest must reproduce the ladder exactly and any config containing $2.50/tick or
a stale print must refuse.

## 3. Reconciliation contract (vs `exec/scored_runner_v2.py` ledger)

Runner ledger law (`RUNNER_SPEC_V2.md` §6, quoted): append-only JSONL, reopened never
truncated; row envelope
`{"schema": "futures_5sym_prescored/ledger_row@1", "seq", "row_type", "counts_observed",
"identity_id", "payload"}`; row types `REFUSED | TRIAL | DUPLICATE_RETRY | FOLD | ABORT |
PUBLICATION`; `seq = max(existing)+1`.

TRIAL payload (one per identity, per-fold sub-records + totals + provenance shas inside;
`counts_observed = true`), fields consumed from the source:

```
record_type, identity_id, symbol, arm, cost_tier, stress, hold_bars,
folds: [{fold_id, n_trades, n_skipped_no_exit, gross_pnl_usd, cost_usd, net_pnl_usd,
         trades: [{i_signal, i_entry, i_exit, entry_ts, exit_ts, entry_price, exit_price,
                   direction, era, tick_size, tick_value_usd,
                   gross_pnl_usd, cost_usd, net_pnl_usd}]}],
totals: {n_trades, gross_pnl_usd, cost_usd, net_pnl_usd}, engine_version   ("runner_v2@1")
```

Reconciliation checks (all must hold at any future scored run; the dry-run proves them with
counters untouched):

1. **Per-identity vs identity table**: every `identity_id` with a TRIAL row resolves against
   the frozen identity-table enumeration byte-exactly (`RC-6.1`; probe R1/R2 precedent);
   unknown IDs refuse; FLAT anchors carry `n_trades = 0`; every instantiated identity
   incremented the observed scored denominator exactly once (`RC-6.4`, P-9 law); dry-runs and
   this lane's synthetic runs touch zero counters.
2. **Sum-of-trades vs fold aggregates**: within each identity-fold, `Σ trades[].{gross,cost,net}`
   == the fold record (money rounded to 6 dp, identical arithmetic to
   `scored_runner_v2._r6`); per-identity `totals` == Σ over folds; per-fold `FOLD` records ==
   Σ over identities (`by_identity` map, `identity_count` == distinct identities in the fold).
   Folds multiply evaluation views only — identity count invariant across folds (`RC-5.3`).
3. **Observed vs published**: observed = distinct TRIAL identity ids (true at append time);
   success writes `published_summary.json` with published == observed; a publication failure
   keeps observed rows, withholds the summary, writes `PUBLICATION_QUARANTINE.json`, exits 3
   (`FAILED_PUBLICATION`) — the denominator is never lost and never double-counted
   (`DUPLICATE_RETRY` rows never recompute, `counts_observed = false`).
4. **Reopen/retry no-loss-no-double**: ledger append refuses on a torn line (integrity pass
   even with `--resume-with-recovery-check`); identity-ID dedupe on recovery (T20 class).
5. **Twin (G8)**: a second engine pass over the SAME frozen inputs must match structurally;
   any diff ⇒ `FAILED_TWIN_MISMATCH` exit 3 + `reconciliation_report.json` (`match: false`).
   Adapter-side determinism (byte-identical intents across calls; truncation-stable PIT) is
   proven per family and is a precondition for twin success.
6. **Refusals are rows, never passes**: any `REFUSED_*` writes a REFUSED row
   (`counts_observed = false`), `FINAL_STATUS.json` with a non-zero exit code, and a
   `refusal_record.json`; the adapter-side refusal records (P5-NQ* slots, D5 pin, session
   mask, EXPWITCH) map onto the same posture — a refusal is the only artifact and is advisory,
   never a gate pass.
7. **Success-token law**: `EXECUTION_COMPLETE` appears in outputs only when EVERY mandatory
   step (incl. lock release, publication, ledger summary, handoff write) measured done.

Adapter annotations (`era_view`, `exclusion_flags`, `k3_stratum`, `decision_slot_dependencies`,
`event_context`) are carried in the TRIAL provenance/`adapt_nq` annotation block; they are
non-authoritative for PnL arithmetic and must never alter ledger reconciliation arithmetic.

## 4. Why no PnL appears in this lane

Outcome-blind law: adapters emit SIGNALS and intended ORDER INTENT on synthetic fixtures.
`gross_pnl_usd / cost_usd / net_pnl_usd` above are RUNNER fields at a future registered,
lock-held, twin-verified run — never produced here. Synthetic-fixture `gross_synthetic_usd`
sanity numbers in the EXPECTED_MANIFESTs are arithmetic checks of direction/price/fill laws
(`direction x (exit-entry) x $20/pt`), labeled SYNTHETIC-ARITHMETIC, never a PnL claim.

— End TRADE_JOURNAL_SCHEMA (PROPOSED).
