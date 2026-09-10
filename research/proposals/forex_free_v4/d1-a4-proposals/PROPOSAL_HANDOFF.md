# PROPOSAL_HANDOFF — lane A4 (blind proposal lane, axis 1), cycle FOREX-FREE-V4

- lane: A4 (axis 1 — policy-rate / carry region, sanctioned confirmatory re-entry)
- branch: `orca/forex-free-v4-d1-a4-proposals`
- base/wave SHA: `3cf818b566d5de75e147585686a6288cac597f3a` (verified with `git rev-parse HEAD` before work)
- proposals: `PROPOSAL_FXFV4-A4-P1.json`, `PROPOSAL_FXFV4-A4-P2.json` (this directory)
- outcome-blind: yes — attestation signed inside each proposal JSON

## What was read (sanctioned packet only)

`PLAN_forex_v4.md` (sections 1/1.1, 2, 7, 12 primary), `research/control/forex_free_v4_run/forbidden_family_inventory.json`,
`research/control/forex_free_v4_run/p2_data_authority_v4.json`, `research/control/forex_free_v4_run/announcement_ledger.jsonl`
(v2 pin `ae5e1f2e…`, byte-read per row), `research/control/forex_free_v3_run/w3_freeze.json`, and the frozen
`research/assets/forex_free_v3/scored_runner.py` / `accounting.py` gate constants (machinery hashed in w3_freeze, no outcomes).
FORBIDDEN artifacts (V3R scored records/recompute/diff tables, SURVIVORS.md, other lanes' worktrees, V1/V2 published ledgers)
were never opened.

## Mechanism summaries

### FXFV4-A4-P1 — financing-budget-scaled differential carry (`financing_aware_position_sizing`)

Hold each pair in its evidenced policy-rate-differential direction with size linear in the carry-to-cost ratio:
`w = sign(Δr) · min(1, |Δr|/κ)` with `κ = 2 × 6 bps × 252/63 = 48 bps`, where the budget is defined by the
STRESS-TIER (2.0) round trip. Trades fire only when the evidenced differential moves the weight by ≥ 0.10 (hysteresis);
since Δr is a step function constant between pinned-ledger events, the fill count is event-bound by construction.
No volatility input anywhere. Cost survival is structural: re-pricing at doubled costs doubles κ and shrinks every
position instead of invalidating it. Control: cross-pair derangement (fixed cyclic signal remapping) — identical
dates/sizes/fill machinery, so it runs to completion under evidenced semantics by inheritance and cannot hit the
frozen validator abort (the V3R `ONE_EVENT_LAG_VIOLATION` failure mode is structurally impossible). Neighbour:
SAFETY=3 (κ=72 bps) — isolates the cost-budget channel.

### FXFV4-A4-P2 — event-anchored persistence hold with cost-stressed unwind (`event_anchored_persistence_hold_with_cost_stressed_unwind`)

Trade ONLY at evidenced differential updates: if |Δr| ≥ 48 bps at the first evidenced-readable clock, enter one
full-size position in the differential direction, hold a fixed 63 sessions; exit early only if the evidenced
differential collapses (< 24 bps or sign flip) or the pair enters a cost-stressed state (5-session vol > 2.5× its
63-session median on two consecutive clocks — the front door's "unwind rules that shorten exposure in cost-stressed
states", implemented literally); a lockout bars re-entry until the NEXT evidenced rate update, making churn
structurally impossible. Fills are bounded by the pinned ledger's event count. Control: mirrored-subset (direction
flipped on the preregistered 4 pairs {GBP/USD, NZD/USD, USD/CHF, USD/CAD}) — identical fill schedule (validator-clean
by inheritance), predicted ≤ 0 expectancy because the flip converts carry-receiving into carry-paying positions.
Neighbour: H=42 sessions — horizon-robustness of the post-event drift claim.

Both proposals: confirmatory re-entry of FXFV3-A6-P1 disclosed and flagged; PIT conditioning exclusively on the
pinned v2 announcement ledger (US 22/22 EVIDENCED INSTANT, AU 25/50 INSTANT via OFFICIAL_FIXED_SCHEDULE,
GB 21/22 / NZ 25/50 / CH 11/22 / JP 4/5 EVIDENCED DAY, CA 0/22 and EMU 0/19 conservative LATER-bound,
8 baselines conservative non-load-bearing); daily 16:00 America/New_York DST-aware decision clock; full 7-pair
universe; frozen costs 1.5 bps/side with ×1.5/×2.0 tiers on booked stress PnL and break-even bps reporting;
frozen kernel floors (per-arm 40 decisions, 30/fold populated, folds 2020-03-01/2022-05-01/2026-09-02 purge 14,
dropout 6-of-8, MDD 2500 USD, pair share 0.40, fold share 0.50, USD |corr| 0.30, control reject PF 1.10);
incremental alpha vs the naive differential-direction book via `per_trade_expectancy_difference_v1`.

## Margin-to-fail expectations (ex ante, summary)

Shared honest view of both families:
- **Design-level survival claimed (thin-to-margin pass):** STRESS_TIER_2.0 (primary) and STRESS_TIER_1.5 — the
  gate that killed the ancestor (-101.62, PF 0.9881) is the gate both constructions were built around
  (event-bound fills + budget/lockout). P2 claims the wider margin (lowest fill count).
- **Knife-edge passes:** fin-adj expectancy > 0; PF ≥ 1.10; ≥ 2/3 positive populated folds (with a disclosed
  fold-1 population risk: 2019-01..2020-03 is event-poor and may fall under the 30-trade populated floor,
  forcing 2-of-2); dropout 6-of-8 (dropping USD/JPY or USD/CHF plausibly kills either book).
- **Plausible FAIL gates, disclosed ex ante:** USD-drift |corr| ≤ 0.30 (the evidenced differential direction is
  structurally USD-long on this universe through most of the window — the mechanism cannot neutralize that without
  abandoning itself); price-only sign (FINANCING_MANUFACTURES_EDGE — carry PnL is partly financing by nature);
  fold-positive share ≤ 50% and pair concentration ≤ 40% (the 2022-05..2026-09 fold and the JPY/CHF legs plausibly
  dominate positive PnL); incremental alpha > 0 — the second most likely mechanistic failure, because the naive
  differential-direction book is itself event-anchored and low-turnover on this universe.
- **Expected clean passes:** control does-not-reproduce AND runs-to-completion (both controls inherit the anchor's
  validator-clean fill schedule); reproduction ALL_MATCH (deterministic, no inferred stamps); neighbour support.

## Notes for A7-N / A9-F / A8

- A7-N must measure anchor rank correlation against BOTH V3 family2 anchor variants (as-scored and
  evidenced-corrected books; 158 differing decisions, 19 sign flips per the inventory). Both families accept the
  D2 eligibility decision on those numbers; P1 has no volatility input anywhere and P2's volatility appears only
  in a one-way crash exit with lockout — but prose is not the test, the rho numbers are.
- Fold boundaries, purge, floors, cost ladder, dropout suite, control-reject rule: all inherited frozen
  (V3 scored_runner / accounting kernel, w3_freeze-hashed); nothing new introduced, no new data sources
  (only `policy_rates_bis_wscbpol` = EVIDENCED_CITABLE is cited; CPI is STAGED_NOT_CITABLE and unused).
- The `108/151` phrasing in p2_data_authority_v4.json's evidence string does not match the byte-read row census
  (108 evidenced of 212 rate-change rows + 8 baselines = 220 rows total). Proposals cite the per-row classes from
  their own byte-read; flagged here for the manifest owner, not resolved by this lane.
- Known limitations: fold-1 population risk (both families); event-bound samples give PF/alpha estimates with
  wide ex ante uncertainty; the USD-long structural tilt of the differential direction on a 7×USD universe.

## Outcome-blind attestation

Signed inside each proposal JSON and reaffirmed here: lane agent A4 has not read any scored outcome file
(V3 published scored ledger, V3R records/recompute/diff, SURVIVORS.md, V1/V2 published ledgers, other lanes'
worktrees). Ancestor numbers quoted come only from the sanctioned packet (PLAN §0/§1.1, forbidden inventory).
All design constants were fixed ex ante from frozen authorities.
