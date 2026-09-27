# G3 IDENTITY FREEZE — EVENT-MECHANISMS-V1 (2026-09-27, outcome-blind)

Court: A1 + independent skeptic (G1 rulings applied; fences below are
binding). Two identities, both stocks, both keyed on the SAME new
information layer (EDGAR acceptance clock — the untested N2 axis; NG6's
dead event-forms were date-based, measured). No parameter sweeps: every
constant below is fixed a priori with a stated reason; neighbours probe
robustness, not optimization. Controls/baselines are re-evaluations, not
trials (EURUSD-OPEN-SEARCH budget_note precedent).

Shared control battery (both identities, one implementation):
1. **date-only control** — identical rule with acceptance-time strata
   removed (filing-date clock). If it reproduces the anchor's net expectancy
   within noise, the acceptance clock adds nothing → identity dies (E-class
   kill, preregistered).
2. **permuted-acceptance placebo** — acceptance stamps shuffled within
   issuer×form×year (moves the clock, keeps the event set; Q-11: a null
   must move the signal). Anchor must NOT be reproduced.
3. **clock-only shadow** (Q-7) — stratum conditioning with the event
   payload removed (random events on the same clock): isolates how much of
   the anchor is pure clock.
4. **ancestry rho battery** — representation-rho vs the named dead
   observables (A1: NG6 event-conditional forms incl. reversal_5d; A2:
   SFNG1 declared-plan cadence + amihud illiquidity level), bar 0.20
   immovable, measured pre-PnL on committed bytes.
5. **cost law (frozen, no new numbers)** — per-side cost = the
   STOCKS-AMIHUD-RETEST-V1 frozen band-cost contract (Q-2 conditional +
   L-SAMV1-3 X1/X2 fill-feasibility) applied unmodified; entries at session
   opens priced at the open band; stress ×1.5/×2.0 reported separately.
   PROXY-PRIOR label carried (stocks cost plane 0/10 measured).

Universe (shared): death-inclusive cohort — NG6 panel members (2,168
tickers archived, 1,769 dead included) joined to EODHD bars via the N4
dated identity map; events from form4_stream (A2) / cohort submissions
staging (A1). Window: 2015-01-05 .. 2026-06-30 (dev; S0 screening only).
Folds (fixed): F1 2015-2018, F2 2018-2021, F3 2021-2023, F4 2023-2026H1.
Floors (preregistered kill bars): ≥100 bookable events per fold and ≥400
total per anchor, else NOT_RUN_THIN; ≥2/3 folds net-positive after costs;
no single name >20% of book net; drop-one-name survival; PF bar 1.10 at
×1.0 cost (margin-to-fail reported; Q-12 exclusion zone stated).

---

## EMV1-A1 — filing-flow acceptance-clock drift book

- family_id `EMV1-A1-FILINGFLOW-ACC`; mechanism: slow diffusion of
  disclosure accepted OUTSIDE monitoring windows (attention-constrained
  payer; Q-7 clock law). Payer: participants conditioning on date-only
  information sets.
- events: 10-Q/10-K acceptances (forms frozen) per cohort issuer.
- strata (fixed by market clock, no tuning): S1 pre-open [00:00,09:30),
  S2 in-session [09:30,16:00), S3 after-close [16:00,20:00), S4 late
  [20:00,24:00) ET; weekend bucket separate.
- anchor: on acceptance in S1∪S3∪S4 (unmonitored windows — prediction:
  slower incorporation), direction = sign of first-post-acceptance session
  return (close−open), entry = NEXT session open, hold 5 sessions, exit
  close. Long/short symmetric by direction sign.
- neighbours: N1 hold 10 sessions; N2 identical rule restricted to S2
  (monitored window — prediction: net ≈ 0 or negative after costs; if S2
  matches S1∪S3∪S4, the clock story dies from the other side).
- falsifiers (in addition to shared battery): post-event |drift| spread
  between unmonitored vs monitored strata ≈ 0 after costs; PF < 1.10 at
  ×1.0; any fold floor miss.
- expected failure interpretation: if date-only control matches anchor,
  acceptance clock is redundant → identity dead, filing-flow closed on
  this axis (NOT a date-clock rescue — momentum/cadence classes stay
  ancestry-dead).

## EMV1-A2 — insider-flow acceptance-clock book

- family_id `EMV1-A2-INSIDERFLOW-ACC`; mechanism: officer/director
  open-market buys carry private-information advantage; the 2-business-day
  Form-4 deadline dates the event; slow outsiders pay the drift.
- events: issuer-days with net open-market BUY value ≥ $100,000
  (transactionCode 'P'; officers/directors; cluster = ≥2 distinct insiders
  same issuer-day recorded as a feature, not a gate) from form4_stream,
  original filings only (amendment arm DROPPED by G1 court — SFNG2 law).
- anchor: LONG at next-session open after acceptance, hold 10 sessions,
  exit close. Long-only (sell-side asymmetry excluded a priori).
- neighbours: N1 hold 20 sessions; N2 cluster-conditioned (≥2 insiders;
  prediction: stronger).
- identity fences: representation-rho vs SFNG1 declared-plan cadence
  observable < 0.20 (measured pre-PnL); illiquidity cross-check — anchor
  net on top-half-DV names must not be explained by amihud-level
  conditioning (rho vs ILLIQ-AMIHUD-28D/63D signals < 0.20).
- falsifiers: drift ≈ 0 after costs; value/date-matched no-event placebo
  reproduces; PF < 1.10 at ×1.0; fold floors.
- merge condition (G1 court, preregistered): if A2 anchor net is
  indistinguishable from A1's generic filing-flow drift (representation-rho
  of the two event-date indicator streams > 0.20), A2 collapses into A1 as
  a neighbour arm and the identity count drops to 1.

## Budget / trial identity

- arms: A1 {anchor, N1, N2} + A2 {anchor, N1, N2} = 6 scored cells max =
  registered budget 0/6. Controls/baselines/placebos = re-evaluations.
- each scored arm records: cycle_id, family_id, arm_id,
  arm_config_digest (sha256 of this freeze section), data_snapshot_digest
  (at staging), code_freeze_sha, cost_tier, fold contract. Exact-arm
  dry-run must show pairwise-distinct record IDs, zero PnL leakage.
- S1 remains SEALED; nothing here opens it.

## Gate status after this freeze

G4 battery / G5 independent implementation / G6 ceiling arithmetic /
G7 A7 prelaunch: **NOT_RUN — implementation lanes not yet dispatched**
(this session stops at the gate boundary per §25; dispatch packets below).
Scored execution: BLOCKED at owner GO gate by construction.
