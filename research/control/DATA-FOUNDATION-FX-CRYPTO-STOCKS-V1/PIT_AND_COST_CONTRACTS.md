# PIT_AND_COST_CONTRACTS — DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1 (deliverable D4)

Frozen at integration. This file BINDS the following already-committed
artifacts as the program's data contracts; each is authoritative for its
layer and any change requires a new preregistered amendment.

## 1. Authority-row schema (every dataset, no exceptions)

- Schema: `pit_license/authority_row_schema.json` (`dfv1_authority_row@1`)
  — plan §5 fields incl. event_time / available_at / ingested_at /
  revision, timezone + DST evidence, missingness, manifest verification,
  acquisition/storage costs, reproducibility, and the status enum
  (AVAILABLE_VALIDATED / AVAILABLE_UNVALIDATED / BLOCKED_LICENSE /
  BLOCKED_ACCOUNT / BLOCKED_COST / BLOCKED_STORAGE / [BLOCKED_TRANSPORT ≡
  BLOCKED-cause-transport superset] / NOT_RUN).
- Validator: `pit_license/validate_rows.py` (stdlib-only; MUST return VALID
  before any inventory is cited).
- Standing law: **file existence never implies AVAILABLE_VALIDATED**; the
  status requires this-cycle re-measurement recorded in `status_evidence`.
  Live-owner datasets are `INHERITED_NOT_REHASHED_LIVE_OWNER`, sealed bytes
  are manifest-metadata only.

## 2. Pipeline contract (raw → replay)

`pit_license/PIPELINE_CONTRACT_DRAFT.md` is adopted as the frozen design
contract: raw immutable (write-once, sha manifests, machine-local, never in
Git) → normalized+provenance (source_id, normalizer_version, row lineage) →
PIT/quality gates (fail-closed) → cost book (measured, stress tiers) →
query/replay read-only (deterministic point-in-time reads). Its
EXISTS/PARTIAL/DESIGN-ONLY inventory of current machinery (CADS,
market_data_plane reason codes, data_fusion PIT/identity/conflict,
calendar_engine, QueryPlane, ERP1 pit_battery2, EURUSD truncation fixtures)
is the honest build map: **no layer is invented as existing**.
Clause C-CX-1 (verbatim, binding): "Không suy ra order book hay forced flow
từ nến" — no order book or forced flow may be inferred from candles; named
fixture F-CX-NOBOOK-1 enforces it.

## 3. Fixture battery (the tests a dataset must pass before backtest use)

`pit_license/FIXTURE_BATTERY_CONTRACT.md` (11 named fixtures; 6 EXIST, 5
PARTIAL): future-leak truncation replay; revision/restatement detection;
DST boundary; symbol/identity change; duplicate/missing bar; quote
crossed/stale; source disagreement; stamp-scale migration (assert
first/last stamp within one bar of declared window end — L-TRACKB1-1);
spread non-positive rejection; volume-0 unfillable (L-SAMV1-3); reverse-
split adjustment (L-SAMV1-1). A dataset entering any scored cycle runs the
applicable subset, and only fixtures marked EXISTS may be cited as already
proven — PARTIAL/DESIGN-ONLY must be built first.

## 4. Cost book contract (measured beats stated — Q-8)

`cost_execution/COST_AUTHORITY_TABLE.md` + `.json` are the frozen cost
authority: per asset × 10 components (spread, commission, min size, tick,
swap/financing, triple-swap, margin, slippage/latency, FX conversion, API
fees) with evidence class MEASURED_FROM_BYTES / DECLARED / STATED_VENDOR /
UNMEASURED + 2 frozen extras (stress multiplier 2.0 PRIMARY; P3-A
0.41-pip threshold). Current state: FX 2/10 measured, crypto 3/10 (+2
declared), stocks 0/10, XAU 2/10.

### Evidence standard: "backtestable after costs" per asset

An asset's data plane may host a SCORED cycle only when, for the exact
instruments and cadence of the proposal:

1. **FX**: spread measured at the order clock (session/rollover-resolved)
   from a tradables-grade source OR the Dukascopy census with the
   indicative-quote disclosure + financing band per pair (swap long/short,
   triple-swap day) measured or BLOCKED-declared with a ≥2.0× stress on
   the declared value; commission explicit per lot.
2. **Crypto**: settled funding re-verified floor-exact (8h), fee tier
   measured or DECLARED with stress, spread census measured for the symbol
   (SOL-class census; BTC/ETH currently declared — flagged), and no
   order-book/forced-flow observable inferred from candles (C-CX-1).
3. **Stocks**: fills only on volume>0 bars with participation caps
   (L-SAMV1-3 X1/X2), adjusted-price state rebuilt from action-date tables
   (not vendor adjusted_close), identity joins via dated mapping, and a
   cost book that is at minimum a declared bps ladder with stress — a
   measured book does not exist today (0/10) and any equities net-of-cost
   claim must disclose that.

### Missing-evidence defaults

Missing component ⇒ UNMEASURED (fail-closed) with the named owner action
(runbook); DECLARED/STATED values carry the frozen 2.0× stress and can
never be silently upgraded to measured (P-21/Q-8).

## 5. Outcome-exposure separation (research vs confirmation data)

`pit_license/OUTCOME_EXPOSURE_MAP.md` is binding: 21 outcome-exposed
family windows vs 5 UNOPENED classes (S1 everywhere; ERP1 sealed 2026-H1
AUDUSD+USDCAD; post-2026-09 prospective streams; future windows; BNBUSDT
pre-read plane). UNOPENED data is readable only by an owner-authorized
confirmation plan; prospective collectors are never replayed into
research; sealed bytes get manifest-metadata treatment only (F8).
