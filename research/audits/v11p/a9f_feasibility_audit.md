# A9-F Feasibility Audit (D2) — V11 proposal pool

- Producer: **D2-A9-F** (independent data / turnover / implementation feasibility auditor)
- Generated: see `generated_utc` in `a9f_feasibility_audit.json`
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/v11/d2-a9-feasibility`
- Branch: `orca/v11d-a9-feasibility` — bootstrap `903ed49529de5ee56ece7dc9fe896da32804a4f8` (verified before work; status clean)
- Scope: schedule-only. **No scored return / PnL was computed, exposed or persisted. Budget 0/12; denominators 119/120 untouched.**
- Data: staged snapshot `/Users/hoangminhlong/my-quantitative/catalog_live_crypto` + `/Users/hoangminhlong/my-quantitative/funding_data` — READ-ONLY, nothing written into them, nothing downloaded.

## 1. The decisive OI answer

**OI snapshot coverage per symbol is ZERO.** For all 20 staged symbols: count = 0, cadence = undefined, gaps = undefined. A schema census over all 43 catalog files found only 15m OHLCV bar parquets (23 parts) and static `CryptoPerpetual` instrument definitions (20, one row each). There is **no open-interest series anywhere in the staged snapshot**.

Per the fail-closed rule, missing = **UNAVAILABLE** for the OI_POSITIONING family — never an inferred PASS. All three OI-lane proposals (`a5_prop2`, `a6_prop2`, `a8_prop2`) are **UNAVAILABLE on data readiness**, by their own predeclared gates (a5_prop2: ≥1 snapshot/day per universe symbol; a6_prop2: ≥60d OI coverage; a8_prop2: P9 plausibility gate).

New-external-data need (FLAGGED ONLY, not fetched): PIT OI snapshot history for all 20 symbols, ≥1/day, ≥90d before formation, through 2026-08-21.

## 2. Field existence (PIT)

| Field | Coverage | Verdict |
|---|---|---|
| 15m bars (close/volume/quote_volume) | 20/20 symbols, 70,045–70,079 rows each, 2024-08-21..23 → 2026-08-23; only ETHUSDT has gaps (63 missing bars / 3 events, largest 57 bars 2025-08-20T23:59→2025-08-21T14:29 UTC); 0 zero-volume bars; 0 zero-dollar-volume days; staleness 0 at 2026-08-21T00:00Z | **PASS** |
| Instrument defs / tick size | 20/20 static snapshots: `price_increment`, min_notional, taker_fee 0.0005, onboardDate ≤ 2023-12 (no mid-window listings) | **PASS** (LOW caveat: single end-of-window def snapshot, not a PIT series) |
| Funding settlements | 20/20 (`scan_2026`): 2,190–4,636 rows, 2024-08-23T08:00Z → 2026-08-23, median cadence 8h (4h for ACE/BOME/ENA/ONG), max gap 8h, zero gaps >12h | **PASS** |
| Mark price series | Present **only** at funding settlement stamps; no continuous series (no scheduling-critical consumer) | **PASS w/ LOW flag** |
| OI snapshots | 0/20 symbols | **UNAVAILABLE (fail-closed)** |

`ts_event` is the exchange CLOSE stamp of each completed 15m bar (`research/panel.py` convention); PIT-correct for the daily-close construction through the window end.

## 3. Schedule-only feasibility (frozen A3 gate)

Method: each spec's decision schedule built over the candidate scored window 2025-08-22 → 2026-08-21 (weekly Monday 00:00Z; A6 monthly 28d cycle at 00:05Z; terminal FORCED_FLAT appended). Target books are **representative schedule proxies** (deterministic, price-independent pseudo-characteristic, gross 1.0 dollar-neutral bucket books) — documented as schedule proxies, **not scored results**. Fill prices are real staged 15m closes, cost inputs only. Cost model at frozen floors (taker 5bps = staged value = V10 contract floor; 1 adverse tick; per-symbol tick sizes from staged defs; stressed = fee×1.5/+2 ticks). Arithmetic reused verbatim from `research/v11/cost_feasibility.py` + `research/adapter_v10` — nothing forked.

| Family | Gate verdict | dec/365d | med hold (d) | base drag | stressed | max sym share |
|---|---|---|---|---|---|---|
| a5_prop1 (weekly quintile) | **PASS** (all 5 floors) | 52.6 | 21 | 2.48%/yr | 4.18%/yr | 16.7% |
| a8_prop1 (weekly quintile) | **PASS** | 52.6 | 21 | 2.48%/yr | 4.18%/yr | 16.7% |
| seed DEF-RESVOL (weekly) | **PASS** | 52.6 | 21 | 2.48%/yr | 4.18%/yr | 16.7% |
| seed LOT-RESMAX/SKEW (weekly) | **PASS** | 52.6 | 21 | 2.48%/yr | 4.18%/yr | 16.7% |
| a5_prop2 (OI weekly tercile) | **UNAVAILABLE_FAIL_CLOSED** (signal availability — OI absent) | 52.6 | 28 | 1.49%* | 2.53%* | 13.3% |
| a8_prop2 (OI weekly quintile) | **UNAVAILABLE_FAIL_CLOSED** (same) | 52.6 | 21 | 2.48%* | 4.18%* | 16.7% |
| a6_prop1 (monthly tercile) | **UNAVAILABLE_FAIL_CLOSED** (own min-6-names/leg rule unsatisfiable → empty books) | 14 | — | — | — | — |
| a6_prop2 (monthly + OI) | **UNAVAILABLE_FAIL_CLOSED** (breadth + OI) | 14 | — | — | — | — |

\* = counterfactual run with availability supplied (data absence neutralised) to show the schedule+cost floors themselves PASS; the only blocker for the OI weekly lane is the missing OI data.

Breadth-relaxed counterfactual for the A6 lane (min 1/leg — **not a waiver**): floors pass (base 1.22%, stressed 2.05%, medhold 29d). The blocker is breadth, not schedule.

## 4. Minimum eligible symbols per decision

PIT rule: exchange-listed (instrument `onboardDate`) + required history (60d A5/A8-weekly, 90d A6/seeds) + active (bar within 48h) + trailing-28d median daily dollar volume **strictly above** the cross-sectional PIT median.

- Active: **20/20** at every decision date. Above-median: **9** at every date (min = median = max = 9 across 52 weekly + 14 monthly dates). The DV-median floor structurally caps the universe near half the active names.
- Viable-breadth statement: quintile books run at **1 name per leg**, terciles at 3 per leg. A6's declared fail-closed minimum of 6 names/leg needs ≥18 eligible — **unsatisfiable here (9 < 18)** and on any ~20-symbol universe.
- HIGH flag (not a floor fail): weekly quintile families trade 2 scored names per side; Stage-A concentration gates are the binding downstream risk.

## 5. Compute / RAM / runtime (prewindow 2024-11-01 → 2025-08-21, 20 symbols, 8GiB arm64 host)

| Workload | Wall-clock | Peak RSS |
|---|---|---|
| Bar load, all 20 symbols (15m, 3 cols) | 1.93 s | — |
| 28d Amihud across symbols (ILLIQUIDITY group) | 0.07 s | — |
| 90d rolling BTC-beta residual + 28d resvol + 7d MAX + 30d skew (SEEDS group) | 0.17 s | — |
| OI growth (OI group) | **not computable — no data** | — |
| Whole-process peak | — | **≈137 MB of 8 GiB** |

**No stronger machine is needed** for D2/P1 feature generation at this universe size (the owner directive to move Phase E to a stronger machine is unrelated to this estimate).

## 6. Verdict matrix

| Family | Verdict |
|---|---|
| V11-SEED-DEFENSIVE-RESIDUAL-RISK | **PASS** (HIGH breadth caveat) |
| V11-SEED-LOTTERY-MAX-SKEW | **PASS** (HIGH breadth caveat) |
| V11-A5-ILLIQ-PREMIUM (a5_prop1) | **PASS** |
| A8-V11-ILLIQ-AMIHUD (a8_prop1) | **PASS** |
| V11-A6-ILLIQUIDITY-PREMIUM (a6_prop1) | **FAIL** — own min-6-names/leg rule unsatisfiable (9 eligible) |
| V11-A5-OI-HEDGEPRESSURE (a5_prop2) | **UNAVAILABLE** — zero OI coverage |
| V11-A6-POSITIONING-SATURATION (a6_prop2) | **UNAVAILABLE** — zero OI coverage + breadth fail |
| A8-V11-OILEVER-DELEV (a8_prop2) | **UNAVAILABLE** — zero OI coverage |

Groups: ILLIQUIDITY_PREMIUM **PASS (2/3)**; OI_POSITIONING **UNAVAILABLE (0/3)**; SEEDS **PASS (2/2)**.

## 7. Canonical recommendation (criteria: data readiness first, then schedule simplicity)

- **ILLIQUIDITY_PREMIUM → A8-V11-ILLIQ-AMIHUD (a8_prop1).** Data readiness equal to a5_prop1 (bars-only); schedule equally simple in cadence; a8_prop1's spec is simpler (single Amihud estimator for anchor+neighbour 28d/56d, plain quintile book; no winsorisation, no Roll estimator dependency). Runner-up: a5_prop1 — equally feasible, adds the Roll-spread estimator-consistency neighbour and the reversal-orthogonality diagnostic. PLAN D3 lexicographic tie-break applies if A1 needs it.
- **OI_POSITIONING → NONE.** Group is data-blocked. If the owner stages PIT OI snapshots later, the weekly lane's floor-passing counterfactuals (a8_prop2 / a5_prop2) already stand; a8_prop2 carries the most predeclared OI data-quality gates and would be the natural conditional candidate. a6 monthly variants stay breadth-blocked regardless.

## 8. Blockers and assumptions

Blockers: OI data absence (owner decision required to stage; fetching forbidden for this auditor); a6_prop1 breadth FAIL; HIGH breadth-concentration flag on weekly quintile families; LOW flag on static instrument defs.

Assumptions: candidate scored window 2025-08-22..2026-08-21 (no window declared yet in `research/control/v11_run/run_contract.json`); Monday 00:00Z / 28d-00:05Z decision instants per specs; books are schedule proxies; DV floor implemented from 15m `quote_volume` daily sums with strictly-above median; funding cadence from `scan_2026` (the `20240820_20260821` directory is a 7-symbol earlier partial capture); bar firsts are snapshot-coverage starts, so PIT listing used `onboardDate`.

Full machine-readable detail (per-symbol coverage tables with counts and gaps, per-decision eligibility, floor tables, hashes): `research/audits/v11p/a9f_feasibility_audit.json`.
