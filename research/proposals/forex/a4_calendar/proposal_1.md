# FX2-A4-P1 — DST desynchronization of the London–New York overlap: a session-clock liquidity-provision premium

Lane: `forex-f2-a4-calendar` (A4 — sessions, holidays, DST, macro clocks). Outcome-blind hypothesis document.
The JSON file `proposal_1.json` is authoritative; this narrative restates the same content for humans.

## Mechanism

The deepest liquidity window of the 24/5 FX week is the London–New York overlap. BIS Triennial 2022:
UK 38% + US 19% of global turnover (top five centres 78%), USD on one side of 88% of trades.
But the two centres' wall-clock alignment is governed by two independent statutory DST calendars
(Europe/London: last Sunday March / last Sunday October; America/New_York: second Sunday March /
first Sunday November). In every year there are weeks where their UTC offsets differ from the
long-run aligned +5h:

- spring gap: `D = tz_offset(London) − tz_offset(NY) = +4h` (US switches ~2 weeks before Europe),
- autumn gap: `D = +6h` (Europe switches ~1 week before the US),
- otherwise aligned: `D = +5h`.

**Hypothesis.** During desynchronized weeks the overlap is shifted and effectively thinner for the
same client flow; dealer inventory-carrying risk per unit volume rises; liquidity providers demand
higher compensation. Testable signatures: (i) relative bid/ask spread widening inside the
preregistered New-York-morning window on desynchronized weeks; (ii) a spread-adjusted premium for
passive risk-takers standing in that window versus the identical window on adjacent synchronized
weeks. The claim is about *where in the clock* compensation accrues, not which currency wins.

**Expected counterparty.** Bank dealing desks and electronic market makers quoting the overlap
(inventory risk rises when the deepest window contracts/shifts), and fast-money flow migrating to
whichever centre is open.

## Signal fields and publication clock

- `dst_state_desync`: per-UTC-day label from pure tzdb arithmetic — desynchronized iff
  `tz_offset("Europe/London", t) − tz_offset("America/New_York", t) ≠ +5h`. No returns, volumes or
  spreads enter the definition; the label is computable before the date exists (no look-ahead).
- `overlap_window_utc`: `[08:00, 12:00] America/New_York` local wall time, converted to UTC via
  zoneinfo, preregistered before any outcome inspection.
- 1h bid/ask bars; midpoint for diagnostics only, never an executable fill.

The DST clock is **real in-repo** (zoneinfo; `research/assets/forex/sessions.py`,
`tests/assets/forex/test_sessions_dst.py`). The repo's session wall-time labels are
SYNTHETIC_TEST_ONLY defaults, so the 08:00–12:00 window boundary is a preregistered convention that
must be reconciled with the frozen provider's documented session convention at freeze, before scoring.
The clock is never derived from observed profitable hours; a session filter added after PnL
observation would be a new family/trial (PLAN_forex.md §7/A4).

## Formation / holding / rebalance

- **Form** at 08:00 America/New_York on each trading day with `D ∈ {+4h, +6h}`; equal risk weights.
- **Hold** four hours, to 12:00 America/New_York; always flat outside the window; **never held
  across the New York 17:00 rollover**, so swap/rollover accrual is zero by construction.
- **Rebalance:** none intrawindow; re-form next desynchronized day. ~15 round trips per pair per
  year (~10 trading days around the March gap, ~5 around the autumn gap), ~210/year across 7 pairs —
  low turnover inside the day's tightest-spread window.

## Universe and neutralization

All seven frozen pairs: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD. Predeclared
concentration expectations: EURUSD/GBPUSD strongest, USDCAD weakest. Neutralization is two-layer:
(1) anchor, neighbour and control hold the *identical basket*, differing only in active calendar
days, so anchor-minus-neighbour differences are currency- and USD-neutral by construction;
(2) per-pair/per-currency decompositions with the PLAN §13 gates (no pair >30%, no currency >40%,
positive result not explained solely by USD direction). No cross-currency bet is introduced.

## Expected costs

Tightest spreads of the week expected in-window, with relative widening on desynchronized weeks;
costs from measured side-specific bid/ask of the frozen provider, never a global pip; mandatory
spread ×1.5/×2 stresses. Rollover: zero by construction. Turnover: low, as above.

## Anchor / neighbour / negative control

| Arm | Definition | Why it validates/destroys |
|---|---|---|
| **Anchor** | Basket held only on desynchronized days (`D ∈ {+4h,+6h}`), window `[08:00,12:00]` NY | Only arm exposed to the structural change. Confirmation requires *both* spread widening and spread-adjusted premium; one without the other fails the mechanism. |
| **Neighbour** | Same basket/window on synchronized days (`D = +5h`) in the calendar weeks immediately adjacent to each gap | Shares every input except the DST state; isolates the causal variable. Mechanism predicts anchor > neighbour after costs; equality means generic time-of-day seasonality (Ranaldo 2009), not DST compensation — the specific claim dies. |
| **Negative control** | Placebo day-sets with the D-label shifted ±1 week (true state of every placebo day is known at freeze; fully specified ex ante) | A genuine mechanism must fail on mislabeled clocks. Anchor-like placebo performance destroys the mechanism: returns would track the label incorrectly, i.e. not the DST structure. |

## Expected regimes and falsification

Strongest in the March gap (1-hour offset error for ~2 weeks), milder in autumn (~1 week);
concentrated in EURUSD/GBPUSD; corroborated by spread widening, not USD direction. Falsified by:
anchor ≤ neighbour after costs; no anchor-window spread widening; placebo performance ≈ anchor;
single-pair/single-fold/single-episode concentration (drop-one gates); disappearance under spread
×1.5/×2 stress; result explained solely by USD direction. Any failed criterion retires the family;
no post-score re-specification.

## External validity risks

DST abolition legislation (EU proposals, US debates) — the two-gap structure is a policy artifact;
repo wall-time labels are SYNTHETIC_TEST_ONLY (provider-convention reconciliation required; a
fixed-offset provider timestamps fails closed); the March gap contains moving Easter holidays and
holiday tables are SYNTHETIC_TEST_ONLY (blocked until an authoritative holiday source exists);
findings are feed-scoped, never "the global FX market" (§2); electronic/voice mix drift over 8
years; contested DST-switch-week anomalies exist in the literature — neutralized by neighbour and
placebo design.

## Trial count

Exactly **3** primary scored trials, serial: anchor → neighbour → negative control. Plan-mandated
stresses and context reports (spread ×1.5/×2, DST-boundary/weekend-gap subsets, drop-one-pair/
currency/fold, session context reports) recompute the same preregistered arms; every computed cell
increments the observed denominator exactly once. No post-score replacement.

## PIT fields and availability (measured repo facts)

| Field | Source | Availability |
|---|---|---|
| 1h bid/ask history ≥8y, 7 pairs, UTC stamps | owner-authorized provider (§2) | **UNAVAILABLE** — 0/7 pairs, fail-closed; **feasibility-blocked at selection unless the owner authorizes data** |
| IANA tzdb DST rules (London, New York) | repo zoneinfo (implemented, tested) | **AVAILABLE** — the only load-bearing field that exists today |
| Provider session wall-time convention | frozen provider docs | UNAVAILABLE pending provider freeze; in-repo defaults SYNTHETIC_TEST_ONLY |
| Authoritative holiday tables | authoritative per-currency source | SYNTHETIC_TEST_ONLY — blocked for scoring use |
| Rollover/swap schedule | provider/broker schedule | UNAVAILABLE — not required by primary arms (never cross the rollover); overnight variants blocked |
| PIT macro vintages | not used | UNAVAILABLE, and deliberately not required — signal is pure calendar arithmetic |

## Literature (all retrieved 2026-09-02T23:57:41Z)

1. BIS (2022), *Triennial Central Bank Survey of FX and OTC Derivatives Markets in 2022*,
   https://www.bis.org/statistics/rpfx22_fx.htm — UK 38%/US 19% turnover, USD on 88% of trades.
   [VERIFIED]
2. Ranaldo, A. (2009), *Segmentation and Time-of-Day Patterns in Foreign Exchange Markets*,
   Journal of Banking and Finance 33, 2199–2206; SNB WP 2007-3,
   https://ideas.repec.org/p/snb/snbwpa/2007-03.html — significant time-of-day patterns; domestic
   hours appreciation. [VERIFIED]
3. Kamstra, M., Kramer, L., Levi, M. (2000), *Losing Sleep at the Market: The Daylight Saving
   Anomaly*, American Economic Review 90(4), 1005–1011, DOI 10.1257/aer.90.4.1005 — DST switch days
   are market-relevant; motivation only, not the mechanism; contested replications declared as risk.
   [VERIFIED]
4. Andersen, T., Bollerslev, T., Diebold, F., Vega, C. (2003), *Micro Effects of Macro Announcements*,
   American Economic Review 93(1), 38–62, DOI 10.1257/000282803321455151 — background: intraday FX
   clocks and announcement concentration. [VERIFIED]

## Prohibited shortcuts

None apply: no RSI/EMA grids (single preregistered window/label from mechanism; no grid search
authorized); no provider volume treated as global volume (volume never used); no carry from today's
rates (no rates anywhere; arms never cross rollover); session windows fixed from named-zone tzdb
rules, never from observed profitable hours; midpoint never labeled executable.

## Ancestry

First-generation proposal; no previously rejected or scored FX family exists in this repo, so this
is not a rescue. Declarative ancestry: extends Ranaldo (2009) session segmentation and BIS turnover
geography with a question neither answers — whether the overlap premium changes when statutory DST
calendars desynchronize the two dominant centres; distinct from equity DST-behavioral anomalies,
which it uses as motivation only and neutralizes via its controls.

## Honesty statement

Feasibility-blocked at selection absent owner authorization: real FX bid/ask UNAVAILABLE (0/7,
fail-closed), holiday tables SYNTHETIC_TEST_ONLY, provider conventions unfrozen. The DST clock is
real and implemented. No claim is made that the required market data exists.
