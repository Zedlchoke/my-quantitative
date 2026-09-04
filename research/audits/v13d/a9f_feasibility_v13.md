# A9-F feasibility audit — CRYPTO-V13 Phase D2 (schedule-only)

Artifact: `research/audits/v13d/a9f_feasibility_v13.json` (companion MD) |
Producer: A9-F | Generated: 2026-09-04T11:54:06Z |
Worktree `orca/v13-d2-a9f-feasibility` @ d0be533

**Scope discipline.** Schedule-only feasibility on the real snapshot. NO PnL,
returns, backtests or scored series were computed; all data access was
read-only; no S1; no proposal or code under audit was modified. Reference
marks were read ONLY as cost inputs (the `markPrice` field of funding
settlement rows — the same cost-input concept as the V11 gate's `fill_prices`);
no return series was ever formed.

**Verdict summary.** All six proposals are **FEASIBLE (schedule-only)**;
0 INFEASIBLE. The caveats below are documentation/engineering pins; none
weakens a frozen floor or requires proposal redesign.

| Proposal | 1 Data | 2 Schedule | 3 Cost | 4 Cap | 5 Control | 6 Sample | Overall | Impl. risk |
|---|---|---|---|---|---|---|---|---|
| A13-V13-A5-EXITCAP | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE* | FEASIBLE | MED |
| A13-V13-A5-LIQEPIS | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE* | FEASIBLE | LOW |
| A13-V13-A6-CAPVEL | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE | MED |
| A13-V13-A6-LIQPRO | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE | LOW |
| A13-V13-A8-OITD | FEASIBLE | FEASIBLE† | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE | MED |
| A13-V13-A8-TCH | FEASIBLE | FEASIBLE† | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE | FEASIBLE | LOW |

\* frozen floors met; the proposal's self-declared ">= 52 decisions in the
screen window" is unmet at 51 (see off-by-one caveat).
† FEASIBLE with the slot-open fill-reference semantics caveat.

## 1. Window, clock and folds (measured)

- Blind-S0 window 2025-08-22..2026-08-21 contains **52 Mondays**
  (2025-08-25..2026-08-17), but **Monday 2026-04-20 lies inside the frozen F1
  1-day purge zone [2026-04-20, 2026-04-21)** → **51 discretionary decisions**,
  gate-normalized **52.15/365d ≤ 60** (frozen floor).
- Fold decision counts from the frozen V12 fold contract
  (F0 2025-08-22..2025-12-21, F1 2025-12-22..2026-04-21, F2 2026-04-22..2026-08-21,
  1-day purge): **F0 = 17, F1 = 17, F2 = 17** — all ≥ the proposals' own
  ≥ 15-per-fold floor; non-degenerate; 51 ≥ the a8 30-decision publication floor.
- Median intended holding: 7d for all six (weekly cadence; a8 hysteresis spans
  ≥ 7d by construction) ≥ 3d floor.

## 2. Data identifiability (measured, read-only)

- **15m bars (20/20):** 0 missing slots in the blind-S0 window
  (34,944 slots/symbol), 0 missing slots in the 90d/56d/28d warmup regions
  before the first stamp 2025-08-25. The ~2–3-day head gap vs the outer window
  start is the frozen V12 ILLIQ finding, outside blind-S0 and outside every
  warmup need. LIQEPIS's every-slot-complete rule therefore never fires.
- **Open interest (20/20):** daily snapshots 2025-07-01..2026-08-20/21, **0 gap
  days**, stamped ~23:55Z (available at Monday 00:00Z). At the first stamp:
  OITD "7 stamps within trailing 10d" satisfiable 20/20; CAPVEL counts
  ≥ 26 (28d) / ≥ 52 (56d) met with margins **+2 / +3** at stamp 1 (full
  coverage from stamp 2). **OI does not exist before 2025-07-01** — any
  post-hoc OI lookback beyond ~54d before 2025-08-25 would be infeasible.
- **Mark price:** no dedicated root; staged as the `markPrice` field of funding
  settlement rows (present on **every** row, all 20 symbols; max staleness 8h).
  EXITCAP's and OITD's declared 24h pairing tolerances are satisfiable at every
  stamp; consumers must document that mark stamps coincide with settlement stamps.
- **Funding:** scan_2026 primary (20/20, P2 hashes OK), 1,092 settlements per
  symbol in blind-S0, max internal gap 8.0h; cadence 8h for 16 symbols, mixed
  finer for ACE (1h/4h), BOME (4h), ENA (4h), ONG (1h/4h).
- **Instrument metadata (20/20):** positive tick sizes for all symbols.

## 3. Cost / turnover arithmetic (schedule-only, frozen schedule)

Frozen arithmetic (V10 adapter via `research/v11/cost_feasibility.py`):
taker **5.0 bps/side** + **1 adverse tick** base; stress = **fee ×1.5 + 3
ticks total**; drag annualized ×365/357 over 51 stamps. Measured tick/price
over the 19 tradables: mean 1.366e-4, median 9.34e-5, max 5.76e-4 (NEARUSDT).
Funding enters the floor arithmetic as settlement **event counts only** (frozen
gate precedent; rates applied once at score time): ~21 events per held symbol
per 7d at 8h cadence → ~252/week for 12-slot books, ~105/week for 5-slot books.

| Churn per stamp (one-way Σ\|Δw\|) | Base drag | Stressed drag |
|---|---|---|
| 2.0 — adversarial ceiling (never-exceedable) | 6.64% | **12.09%** |
| 1.0 — high churn | 3.32% | 6.05% |
| 0.6 — typical tercile/quintile weekly | 1.99% | 3.63% |
| 0.3 — low churn | 1.00% | 1.81% |
| 0.2 — hysteresis (a8) | 0.66% | 1.21% |

- **Base ≤ 8%/yr of gross: holds for all six even at the never-exceedable
  ceiling (6.64%).**
- **Stressed ≤ 12%: holds at all plausible churn (≤ 6.05% at 1.0/stamp;
  ~3.6% typical; ≤ 3.03% for the a8 hysteresis books).** It is exceeded
  (12.09%) **only** at the adversarial ceiling of replacing the entire book
  every week for 51 weeks at average tick rates — a corner the frozen
  realized-schedule gate would fail closed at score time. a8's own claim that
  the hysteresis book keeps churn inside the floors is arithmetically
  supported (widest margin of the six).

## 4. Cap / construction (by construction)

- a5 terciles / a8 hysteresis (6 per side): max |w| = 1/12 = 0.0833 ≤ 0.30;
  a6 quintiles: 0.20 ≤ 0.30; gross = 1.0 (a8: w = min(0.5/n_side, 0.30),
  gross ≤ 1.0, cash fallback at n_side < 2). All satisfy the caps by
  construction, including a8's fail-closed rebalance skip at side membership < 4.
- **Per-symbol turnover share:** expected share by symmetry = 8.3% (12-slot
  books) and 20% (5-slot books), both ≤ 25%. The 5-slot books have only a 5pp
  symmetric margin and no structural bound if churn concentrates in one slot —
  correctly framed by CAPVEL itself as "detected by the frozen feasibility
  floor, never relaxed".
- **Drop-one:** a8 fully declares "HELD symbol with maximum |weight|
  (tie-break: ascending symbol name)" — best-specified of the six. a5 declares
  the ascending-symbol tie-break for the book but not in the drop-one rule, and
  its "renormalize the remaining side to 5 symbols per side (1/10)" sentence is
  ambiguous (one symbol total vs one per side). a6 does not declare a drop-one
  tie-break (all held weights tie at 0.20). All are identifiable as held
  max-|w| selections once the tie-break/renormalization sentences are pinned.

## 5. Control identifiability (from definitions)

- **EXITCAP STATIC-SCALE:** testable and distinct (frozen pre-screen 90d median
  turnover denominator; zero capacity dynamics); would detect the stated
  confound class (edge persisting without capacity updating ⇒ placebo passes ⇒
  family rejected). Note: it ranks OI_now / frozen_capacity_i — capacity-
  relative with a frozen denominator, **not literal raw OI scale** as the
  attribution sentence claims; detection works, the label is imprecise.
- **LIQEPIS SIGN-INV:** factory-standard inverted-ordering control; detects a
  generic tilt/ordering artifact; preregistered, never promotable.
- **CAPVEL VOLLEVEL-28D:** directly detects the size/liquidity-level rival
  (removes the OI denominator); precise preregistered reproduction rule.
- **LIQPRO VOLREG-28D:** detects the vol-level rival (the documented vol-level
  sorting shadow); realized vol confined to the control seat.
- **OITD CTL-FLOW-ONLY:** retains the anchor's turnover-level exposure and
  deletes the OI stock; detects the DNR-style flow confound precisely.
- **TCH CTL-VOLLEVEL:** detects the vol-level shadow (low-H co-moves with low
  realized vol); anchor signal contains no returns.
- All six controls are distinct from their anchors, testable under the frozen
  gates, and none is promotable to a family.

## 6. Sample floors

Frozen floors met by all six: 52.15 decisions/365d ≤ 60; 17/17/17 per fold
≥ 15; 51 ≥ 30 (a8 publication floor); books always-invested by construction so
the zero-position refusal cannot trigger. a8's "per-side membership ≥ 4 at
≥ 95% of stamps" and "signal availability ≥ 95%" depend on the realized signal
and are deferred to the W1 `cost_feasibility` gate (score-time-only checks).
**Off-by-one:** the proposals' nominal "52 decisions" is 51 effective (one
Monday purged); a5's self-declared "≥ 52 in the screen window" is strictly
unmet — documentation correction in W1, not a redesign.

## 7. Host resources (measured 2026-09-04T11:50Z)

- CPU: Apple M1, 8 cores. RAM: 8 GB total, ~50% free (≈ 4.0 GB); swap
  7,168 MB total with 5,551 MB used (elevated memory pressure).
- Disk: 48 GB available (228 GB volume, 75% used). Authorized data footprint:
  bars 129 MB, OI consolidated 160 KB — per-family in-memory working sets
  (rolling 90d windows, 19 symbols) are far below 1 GB.
- Strong-host E0 formula: `measured_safe_cap = min(3, floor((free_gb − 1.5)/2.0))`
  → **cap = 1**: serialized single scored cell at a time (consistent with the
  serial-arm plan and the P1 single-writer-per-ledger policy); 12-hour clock
  and <120min/<45min rules apply; swap pressure warrants modest per-process
  memory and no parallel cells.
- Implementation risk per family: **MED** — EXITCAP, CAPVEL, OITD
  (cross-dataset PIT joins: OI + funding-row marks + bars, pairing/fail-closed
  stamp rules; OITD additionally needs the slot-open fill-reference
  convention). **LOW** — LIQEPIS, LIQPRO, TCH (bars-only signals; the slot
  completeness census is already verified clean).

## Caveats register (full detail in the JSON)

1. Off-by-one stamps (52 Mondays − 1 purged = 51); fix the proposals' "≥ 52"
   documentation in W1.
2. a8 slot-open fill reference (available 00:30Z, fill at 00:15Z): economically
   realizable, no decision-time look-ahead, but needs an explicit engine
   convention; the a5/a6 close-fill convention avoids it.
3. Stressed-cost margin is thin only at the adversarial churn ceiling (12.09%);
   plausible churn passes with wide margin; the score-time gate fail-closes.
4. a6 quintile turnover share: 20% expected vs 25% floor — symmetric margin
   only; detected (never relaxed) by the frozen gate.
5. Mark price granularity = funding settlement stamps (≤ 8h staleness);
   pairing tolerances satisfiable; document the coincidence of stamps.
6. OI history starts 2025-07-01: all declared OI warmups satisfiable; longer
   OI lookbacks would need an owner data-authority decision.
7. Drop-one wording pins needed (a5 renormalization ambiguity + tie-breaks;
   a6 tie-break).
8. EXITCAP control attribution label imprecise ("raw positioning scale" vs
   frozen-capacity normalization); detection logic sound.

## Attestation

Schedule-only audit. No PnL, returns, PF, Sharpe or rankings were computed; no
backtest was run; no scored outcome series was emitted; data access was
read-only; no S1 access; no artifact under audit was modified. Audit artifacts
only: this file and its JSON companion.
