# FIRST REPORT — A1 STOCKS-FREE-V11 (PLAN_stocks_v11 §5)

measured_at_utc: 2026-09-07T01:13:18Z

## 1. Checkout (measured)

```
root        /Users/hoangminhlong/my-quantitative
branch      main
HEAD        d2b0f925a47a69947f85c06d7b95c25aa95a83a2
porcelain   clean (empty)
worktrees   no stocks-free-v11 worktree existed before bootstrap (measured)
branches    no orca/stocks-free-v11* branch existed before bootstrap (measured)
V10 branch  orca/stocks-free-v10-integration @ bec559ca3782140cd8558aff4c935c1706e90dac
workers     active_research_workers: [] (intake snapshot)
python      .venv/bin/python 3.12.14
```

Bootstrap (pwd measured immediately before `git worktree add`):

```
.worktrees/stocks-free-v11/integration
branch orca/stocks-free-v11-integration
HEAD   d2b0f925a47a69947f85c06d7b95c25aa95a83a2   (= root main; contains the
        V10 terminal chain bec559c AND the live plan PLAN_stocks_v11.md at
        its frozen commit 3bc1bce)
porcelain clean
```

## 2. V10 terminal + A7 CONFIRM chain — VERIFIED

- terminal commit bec559ca3782140cd8558aff4c935c1706e90dac is HEAD of
  `orca/stocks-free-v10-integration` (merge-base check: terminal is
  HEAD-or-ancestor, exit 0); its commit message records
  `STOCKS_FREE_V10_REJECT_ALL`, A7 CONFIRMED 8/8, budget 6/6,
  stocks 36/36, S1 sealed, workers 0, no push.
- terminal_report.json (in the V10 integration worktree): verdict
  `STOCKS_FREE_V10_REJECT_ALL`, closed 2026-09-06T06:50:00Z; reproduction
  `REPRODUCTION_ALL_MATCH` (detached twin @5b40d486507551b10d9c427ab70ad2a30079e818,
  present as a worktree; family_verdicts.json byte-equal, one by-design
  provenance leaf = INC-V10-1, adjudicated outcome-neutral).
- audits/a7_terminal_v10.json: verdict `STOCKS_FREE_V10_REJECT_ALL_CONFIRMED`;
  items 8/8 PASS (1_CHAIN, 2_REPRODUCTION_AND_INC_V10_1, 3_VERDICTS_FROM_BYTES,
  4_TWO_KEY_ARC, 5_DENOMINATORS, 6_BOUNDARIES, 7_POST_RUN_STATE,
  8_LABEL_ADJUDICATION); findings 5, unresolved HIGH/CRITICAL = 0
  (F-1 MEDIUM RESOLVED_DISCLOSED = INC-V10-1; F-2 MEDIUM OPEN_VERDICT_NEUTRAL
  timestamp drift; F-3..F-5 LOW). Two-key P-8 arc verified in-chain
  (a7_prelaunch_v1 REFUSED @… → remediation afad4b1 → v2 AUTHORIZED @6f72357
  → owner exact GO).

## 3. Denominators (ledger authority per P-9)

```
stocks program    36 observed / 36 published (V10 +6/6)
program wide      206 published / 209 observed logical post-V10 close
                  (HYPOTHESIS_LEDGER.md header; crypto 143/146, forex 27/27)
survivors         0
V11 budget        0/6 used of 6 planned scored cells (fresh cycle; unused
                  slots never reassigned; V9's 3 dead slots stay dead)
S1                SEALED_UNTOUCHED (terminal_report.s1; A7 item 6/7 verified)
veto set          ELEVEN entries (RULES.md §5): momentum, semivariance,
                  vol-level, WC-stock intensity, Goodwill/bloat,
                  F1-accrual-flow, depletion interaction, cash-level,
                  sector-exposure form, V10 deseasonalized-timing
                  characteristic form, V10 revision-correction
                  direction/breadth form
```

## 4. Cohort / panel / observable-layer hashes — re-verified from bytes

| asset | measured sha256 (2026-09-07) | pin | verdict |
|---|---|---|---|
| multivintage_panel.jsonl (V9 staging; 10,073,069 rows) | 67591464ee49acc159886143a379bda5890b1df602818b600d7938df92af1447 | p0_v10_observable_manifest.panel_sha256_pin | MATCH |
| cohort_v9.json | 6a95401ff84bff2144ac3c0b9426a6fa86daf3dde8d478195666249e3fa2aa62 | p0_v10_observable_manifest.cohort_sha256 | MATCH |
| v10_timing_observables.jsonl (5,453,478 rows; wc -l measured) | b1477ea39b8b794b7f32162cb349ff53fdd1a37b9a64d0ee20e77412ae802337 | p0_v10_observable_manifest.outputs.timing_sha256 | MATCH |
| v10_revision_observables.jsonl (1,667,422 rows; wc -l measured) | 7110cbf010ae6d3f414a1a45eec1e504aff5e94464755991e98605e4795657c2 | p0_v10_observable_manifest.outputs.revision_sha256 | MATCH |
| EOD price store spot-check | 12/12 sampled files re-hashed vs p0d_v9_price_manifest (2,190 files incl. benchmarks SPY + 11 SPDR sectors) | p0d_v9_price_manifest | MATCH |

## 5. Event-book + amendment-chain coverage pre-check (fundable clocks)

Method: one streaming pass over the hash-verified timing layer
(b1477ea3…) + a 31-entity sample spanning the event-count distribution
(02/10/25/50/75/90/98th percentile + 24 random), post-arrival windows
measured against each entity's own EOD price file. Counting only — no
proposal, no PnL. Evidence: /tmp/v11_precheck_events.json (mirrored into
the P0 manifest when published).

```
EVENT-BOOK AXIS (mandatory lane)
  distinct cohort entities in timing layer      2,162
  entities with an EOD price file               2,161  (99.95%)
  distinct filer-events (cik, first_avail)     74,931
  filer-events on priced entities              74,862  (99.9%)
  events per entity (median)                       33
  entities with >=20 filer-events               1,523
  sampled filer-events                          1,083
    with >=5 post-arrival price bars            1,025  (94.6%)
    with >=20 post-arrival price bars           1,019  (94.1%)
  (window truncation concentrates in dead legs
   near termination — expected on a
   death-inclusive cohort; dead-leg coverage is
   the P0 census's explicit deliverable)

AMENDMENT-PROCESS AXIS
  chain groups with depth >= 2              1,667,422  (matches pin census)
  entities with >=1 chain group                 2,156
  entities with >=5 chain groups                2,156
  entities with >=20 chain groups               2,153
  depth histogram head: 1x3,786,056 | 2x621,430 | 3x187,896 |
                        4x128,203 | 5x604,376 | 6x68,975
```

Verdict: **both V11 axes FUNDABLE** on the death-inclusive cohort — the
plan's `BLOCKED_DATA` branch does not trigger at pre-check. Amendment-chain
depth and cadence conditioners have deep, broad support; the filing-event
lane's 74.9k arrival events with post-arrival price windows dwarf any
conditioning-clock requirement V11's three arms can carry.

## 6. GO/NO_GO for P0

**GO.** All §5 items pass with margin. Heavy cap 1 honored (hashes and the
timing-layer stream serialized; no other heavy job on this machine).
Incidents: two harmless A1 tooling missteps during measurement (a wrong
relative path in a read attempt; an interpreter fallback attempt caught
before execution) — no artifact affected, recorded in incidents.md per the
"record even harmless" rule. V10's F-2 timestamp-drift finding is inherited
context, not an incident of this cycle.
