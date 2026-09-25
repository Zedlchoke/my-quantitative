# DRAFT AMENDMENT A1 — FX-RANGEFADE-2M-SHADOW-V1 controls & cost observability

> **Status: DRAFT_FOR_OWNER_GO — NOT REGISTERED, NOT EXECUTED.** Owner
> decision D2 (2026-09-25) approved this at PLANNING LEVEL only. Nothing in
> this file is live law until the owner types the amendment's own GO phrase
> at its own gate, after independent review. No worker restart, no
> implementation, no scored cell, no S1, no order is authorized by this
> draft. Parent laws: plans/PLAN_fx_rangefade_2m_shadow_v1.md (frozen
> strategy law UNTOUCHED) + plans/PLAN_economic_robustness_program_v1.md
> §4.1 (C-FX-1..4).

## 0. Identity

```text
target cycle        FX-RANGEFADE-2M-SHADOW-V1 (ACTIVE_LIGHT, registry)
umbrella law        ECONOMIC-ROBUSTNESS-PROGRAM-V1 §4.1 (if registered;
                    cited as draft law otherwise)
amendment id        A1-controls
scope               measurement & control observability ONLY
strategy law        UNCHANGED — v2_lib.f_rangeexp(p, 0.3, 0.7), H1 closed
                    bar → next H1 open fill at opposite quote, force-flat
                    20:00 UTC, weekend flat, 1.5 lots/pair/signal fixed
GO phrase (draft)   GO FX RANGEFADE AMENDMENT A1 CONTROLS MOUNT
```

## 1. What this amendment adds (and what it must never touch)

Four additions, exactly as owner D2 specified. Parameters, signal, size,
timing, pairs and trading behavior of the live sleeves are FROZEN — any
diff that changes a live-sleeve decision, fill, size or force-flat
behavior is OUT OF SCOPE and rejects the amendment.

### 1.1 Short-beta control arm (C-FX-1)

Two parallel VIRTUAL books per pair (no orders, same paper class as the
sleeve), computed from the same TrueFX marks and the same H1 boundaries:

- **CTRL-SHORT-ALWAYS (day-session construct)**: short 1.5 lots from the
  first fillable H1 open after 00:00 UTC each weekday, force-flat at the
  sleeve's own 20:00 UTC flat boundary. Costed with the SAME cost book as
  the sleeve (§1.4). **Comparability note (binding):** this control is a
  DAY-SESSION short book; the ancestor's +314.0-pips SHORT_ALWAYS
  reference (EURUSD-OPEN-SEARCH-V2 commit `bf4f07f1`, holdout window) was
  a window-long construct — the two are NOT numerically comparable. The
  ancestor number is cited as the REASON a short-beta control is
  mandatory, not as a benchmark for this arm.
- **CTRL-SHADOW-MATCHED**: identical to the sleeve's decisions but with
  sign INVERTED at entry, exits identical (the inverted control of
  umbrella §5.7).

Reporting law: every sleeve PnL number is published TOGETHER with
`sleeve_minus_short_control` (excess over short-beta). Until the control
arm has emitted records, all sleeve PnL carries
`SHORT_BETA_UNSEPARATED — NOT PROMOTABLE` (umbrella §4.1 label).

### 1.2 Aggregate USD exposure report (C-FX-2)

Per H1 decision epoch, compute and record into the state/journal:
`usd_same_side_notional` (EURUSD+GBPUSD same-direction gross, in lots and
USD), `usd_net_notional`, per-pair direction. Display-only per owner D10 —
no capping, no behavior change.

### 1.3 Event-time stress-spread book (C-FX-3)

A PARALLEL cost view on every fill (reporting only; primary book
unchanged): charge the measured **session/rollover spread median for the
fill's session bucket** — from the sha-pinned Dukascopy spread census
(EURUSD-OPEN-SEARCH-V1/V2 + FX-MAJORS census artifacts) — multiplied by
**2.0** (lane-F frozen stress tier), refreshed only by preregistered
quarterly re-census (dated hash boundary, never in-place rewrite). The
session bucket of every fill is recorded. Rationale: range-edge fades fill
precisely when spreads widen; the global 0.3-pip median is not the
relevant cost (umbrella §5.4 Track-A condition 3).

### 1.4 Fee/slippage ledger fields (C-FX-4)

Journal fill rows gain fields: `fee_bps`, `slip_pips`, `spread_at_fill`,
`session_bucket`, `cost_book_digest`, `stress_fee`, `stress_slip`,
`round_trip_id`, `realized_net`. Schema is append-only: existing rows are
NEVER backfilled; absence of the fields in old rows is reported as
`NOT_RUN_COST_FIELDS`, not as zero. Round-trip realized win-rate becomes
computable from new rows onward.

## 2. Accounting contract

- Primary book (pinned at implementation gate, before any new row is
  written): declared fee schedule + measured spread-at-fill — today's
  journal is GROSS-ONLY (no cost fields exist yet, explorer 2026-09-25);
  the exact fee schedule values and their provenance (declared-class,
  per data-cost critic Track-A condition 4) are frozen as part of the
  implementation freeze and recorded in `cost_book_digest`.
- Control arms use the identical cost book and fill law as the sleeve
  (same H1 open, same opposite-quote rule) so sleeve-minus-control is a
  clean information comparison, not a cost artifact.
- The stress book is reported alongside, never merged into primary PnL.
- Every daily/weekly report states which basis each number uses
  (umbrella §4.7 vocabulary).

## 3. Implementation boundary (for the owner-GO'd implementation cycle)

- Home: the FX-RANGEFADE-2M-SHADOW-V1 worktree
  (`.worktrees/fx-rangefade-2m-shadow-v1`), one bounded change-set:
  control-arm calculator + journal/state fields + USD aggregation +
  stress-cost calculator + parity tests. The frozen strategy module
  (`v2_lib` + signal/execution path) must show ZERO diff.
- Restart discipline: worker restart belongs to Phase A only (below),
  via the cycle's normal procedure, with restart-idempotence proof (no
  duplicate journal event_ids; journal is append-only). The GO phrase
  alone restarts nothing.
- Tests required before ACTIVATION (Phase V — the GO cannot waive them):
  (a) parity self-test unchanged and passing; (b) control-arm fixture —
  synthetic 3-day quote series with hand-computed CTRL-SHORT-ALWAYS and
  CTRL-SHADOW-MATCHED PnL; (c) cost-field fixture — one hand-computed
  fill with fee/slip/stress; (d) schema fixture — old rows parse without
  the new fields and report NOT_RUN_COST_FIELDS; (e) no-diff proof on the
  strategy module (git diff empty over the frozen paths).

## 4. Lifecycle phases + GO gate (where this draft stops)

**Lifecycle (binding).** Phase G: the GO phrase authorizes ONE thing —
the implementation cycle may write the change-set. Phase I: code written,
daemon untouched. Phase V: fixtures (a)–(e) + A7 prelaunch AUTHORIZED.
Phase A: **activation** — the daemon is restarted per the cycle's
procedure and the activation moment `T_ctrl` is recorded to the second
(UTC) in an activation artifact. The control arms, cost fields, USD
exposure rows and stress book begin emitting at `T_ctrl`; before it, the
journal stays in its old shape (`TRANSITION_OLD_LAW`, no backfill — cost
fields/control data never backfilled onto old rows), and the sleeve's
PnL keeps the `SHORT_BETA_UNSEPARATED — NOT PROMOTABLE` label until the
control arm has emitted records. A typed GO is never evidence the daemon
changed.

1. Independent fresh-context review of this draft (verdict artifact under
   `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/plan_review/`).
2. Owner reviews the review, then types at this amendment's own gate:
   `GO FX RANGEFADE AMENDMENT A1 CONTROLS MOUNT` (exact, fresh; typed
   early = intent only, dies unconsumed per P-8).
3. Only then does an implementation cycle open (umbrella §5.6 law),
   running Phases I → V → A as above.

## 5. Non-objectives

No parameter change; no pair addition; no sizing change; no promotion
claim; no broker/live surface; no S1; no scored cells; no heavy jobs.
