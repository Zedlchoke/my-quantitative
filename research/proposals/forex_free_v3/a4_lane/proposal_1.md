# FXFV3-A4-P1 — Rationale: Post-availability drift in the direction of a policy-rate change

Lane A4, cycle FOREX-FREE-V3. Outcome-blind; written 2026-09-04. Companion to
`proposal_1.json` (authoritative for every frozen constant).

## Why this mechanism belongs in V3

Both prior cycles died on **intraday session-structure** mechanisms: V1 to costs,
V2 before costs (negative gross edge), with session-structure information in free
G10 data judged exhausted at intraday frequencies (12 mechanisms, 0 survivors).
V3 therefore moves the *information source* — from session price geometry to
**monetary-policy vintage data** adopted through Data Fusion (BIS WS_CBPOL
policy rates, availability-gated) — and the *clock* to daily-or-slower, both
chosen ex ante by the frozen invariants, not in response to any V3 outcome.

The economic claim is the smallest honest one available on authorized data:
high-frequency event studies document large, aligned immediate FX reactions to
monetary policy surprises with imperfect absorption; this proposal tests whether
an **availability-gated** daily entry after a policy-rate change earns a residual
5–30 bps drift over 10 sessions after costs. That drift may simply not exist — a
correct REJECT_ALL is a successful run.

## Design choices frozen ex ante

- **Decision rule is event-driven on the daily clock.** A decision exists only
  when a policy-rate vintage change first satisfies `available_time_utc <= T`.
  Because BIS availability is strictly later than effectiveness (never eligible
  on its own effective date) and date-only evidence yields the end-of-UTC-day
  upper bound, a same-day change is first tradeable at the next 16:00-NY bar.
  No same-day backdated carry is possible by construction (upstream P0 pin).
- **Three arms.** Anchor: hold 10 sessions in the direction of the change.
  Neighbour: 5 sessions (nearby variant that must preserve the sign if the
  mechanism is real). Control: exact sign-flip of the conditioning on identical
  dates/fills/horizons — preregistered to NOT reproduce the anchor if the
  surprise-aligned continuation is the operative ingredient.
- **Incremental benchmark.** Same schedule with direction replaced by the pair's
  own trailing 10-session price trend and zero macro reads: this isolates the
  macro conditioning, which is the only thing V3 can add over prior cycles.
- **Dual book.** Financing uses the frozen policy-rate-differential formula;
  the financing term is a PnL adjustment, never the signal, so the
  "financing manufactures the edge" failure mode is structurally unlikely but
  still gated (price-only sign non-inversion).
- **Costs.** 1.5 bps/side x {1.0, 1.5, 2.0} with the F1-fixed booking through
  `book_stress` / `assert_stress_rows_distinct` (3.00/4.50/6.00 USD round-trip
  cost at the 10k unit notional); one-event delay stress carried unblended.

## Known honest weaknesses

- USD-area events move all 7 pairs, so the schedule is USD-heavy by
  construction; the frozen USD-drift, concentration and drop-one gates carry
  the burden of deciding whether that is exposure or edge.
- Post-announcement drift at daily horizons is an extrapolation, not a
  documented daily-frequency result; magnitude class may not clear 2x the
  break-even round trip, in which case the stress gate fails honestly.
- BIS live-fetch warmup coverage is NOT_PROVEN_ON_LIVE_FETCH per
  `data_authority_v3.json`; the P3/Q data-hash gate must prove it or the
  proposal is BLOCKED_DATA_OR_SELECTION.
