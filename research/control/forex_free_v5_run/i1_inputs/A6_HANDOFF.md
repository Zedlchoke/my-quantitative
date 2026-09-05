# PROPOSAL_HANDOFF — lane A6 (open axis), cycle FOREX-FREE-V5

```yaml
agent: A6
lane: A6 (blind proposal lane, open axis — any evidenced authority except the cumulative forbidden inventory)
cycle: FOREX-FREE-V5
base_sha: e2b7a0e1e29794ca8449625f271f9a67c302fcf2
commit_sha: self-referential by construction (this file is inside the single semantic commit it names); the parent records `git rev-parse HEAD` on this branch — exactly one commit on top of base_sha, message prefix "FOREX-FREE-V5 D1 lane A6:"
worktree: /Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v5/d1-a6-proposals
branch: orca/forex-free-v5-d1-a6-proposals
changed_files:
  - PROPOSAL_FXFV5-A6-P1.json
  - PROPOSAL_FXFV5-A6-P2.json
  - PROPOSAL_HANDOFF.md
tests: none run (documentation lane)
known_limitations:
  - "PLAN_forex_v5.md is not in this worktree's base tree; read via git object 704c6a9 (shared object database, same repo) — sections 1, 2, 4 as required"
  - "all turnover/MDD/margin numbers are schedule-level design priors from frozen constants, not measurements (no data loaded, none staged in this worktree)"
  - "P1 keys trade windows to EVIDENCED REALIZED release stamps while the real-time tradable object is the published forward schedule; schedule/realized coincidence assumed and flagged for D2 feasibility quantification (both arms share the property)"
  - "P1 trade-count margin over the 140-trade floor is THIN (est. 1.2-1.4x) and pair-concentration is a declared HIGH structural risk (CA holds ~43% of clocks vs the 0.40 ceiling) — no cherry-picking remedy permitted"
  - "P2's USD-drift diagnostic is declared the most likely single-gate failure (book is USD-directional on trigger days by construction; expected |corr| 0.15-0.45 vs the 0.30 ceiling) — retained deliberately as the preregistered dollar-momentum killer"
  - "P2's EUR-down trigger subset partially intersects V4 family1 (commodity-bloc risk-off) firing states on 3 of 6 legs — submitted to measured |rho| <= 0.20 vs BOTH scored variants of FXFV4-A6-P1 at D2; a measured failure kills P2 pre-scoring"
  - "P1/P2 dropout suites are family-side proportional adaptations of the kernel 8-scenario rule (5 and 7 scenarios respectively; leader-drop structurally vacuous in P2) — kernel definitions govern where labels differ"
  - "no literature metadata verified by network (network fetch forbidden in this lane); all citations marked recalled-canonical"
tree_clean: true (after commit; verified with git status --porcelain)
workers: 0
pushed: false
scored_cells_created: 0
outcome_blind: true (attestations inside both packets)
```

## P1 — FXFV5-A6-P1: pre-release position-avoidance window (evidenced CPI calendar)

Conditioning objects are the 246 evidenced CPI clocks of
`research/control/forex_free_v5_run/p3_conditioning_clocks_v5.json` (GB 88 / CA 105 / AU 23 /
NZ 30, per-row archive_sha256, S0 window 2018-04-04..2025-07-24), mapped to the four
evidenced non-US pairs (GBP/USD, USD/CAD, AUD/USD, NZD/USD). For each clock: decision at the
second-to-last completed 16:00-NY bar strictly before `available_time_utc`, fill at the last
bar before it, exit at the first bar after it — the holding window mechanically spans the
release instant and never holds a post-release session. Direction = −sign of the trailing
10-NY-day return sum (anchor) / 5-day (neighbour): the claim is that extended positioning is
UNWOUND into evidenced scheduled gap risk (position avoidance), so the pre-release window is
counter-trend regardless of the print's outcome — no print value is ever read. Arms: anchor /
neighbour (5-day sum) / sham-calendar control (identical reversal law anchored to +7-day
shifted windows containing no evidenced release; preregistered non-reproduction rule kills the
family if generic multi-day reversal explains the book). Incremental benchmark: stale calendar
(each trade anchored to the same economy's previous clock). Prices per
`p2_data_authority_v5.json` (byte-verified); financing kernel input is the V5-extension ledger
(sha `cf1f01a7…`), accounting only.

## P2 — FXFV5-A6-P2: dollar-board diffusion (cross-pair information leadership)

Price-only. Leader EUR/USD (never traded): trigger iff |z| >= 2.0 where z is the leader's
one-session daily log return over its trailing 120-NY-day sigma, at the completed daily
16:00-NY bar. All six other authorized pairs act as followers in the EUR direction vs USD
(EUR-up: long GBP/AUD/NZD, short JPY/CHF/CAD vs USD; mirrored on EUR-down), entered next
session (one-event lag), held exactly 1 NY-day. Mechanism: EUR/USD is the dollar board's
pricing anchor (~57.6% of DXY); inventory-constrained dealers re-center stale follower quotes
over more than one session (Ho-Stoll; Evans-Lyons; Lyons; LRV 2011 factor structure) — the
claim under test is the t+1 -> t+2 slow tail. Arms: anchor / neighbour (2-day cumulative
trigger) / sign-shuffled control (frozen SHA-256 hash-parity ~50% direction flip on the same
trigger days; kills direction-irrelevant exposure forms). Incremental benchmark: leader read
at t−10. The inherited USD-drift diagnostic is declared a preregistered live killer of the
dollar-momentum explanation. Six legs keep the 0.40 pair-concentration gate structurally
passable (2-3 leg designs violate it by arithmetic).

## Material difference between the two packets

Different information source (evidenced statistical-release calendar vs cross-pair leader
return) AND different causal control (sham-calendar vs sign-shuffled leader). Neither uses
policy-rate signals, realized-vol state gates, print values/surprises, session geometry, or
post-release/post-decision holding windows.

## Forbidden entries checked (all rows read; both packets carry per-row distinctness + rho submission)

1. V1 family1 — session-open (London-open) momentum continuation, intraday
2. V1 family2 — late-NY standardized-extension fade, intraday
3. V2 family1 (FXFV2-A4-P1) — Tokyo-range compression -> London-morning expansion
4. V2 family2 (FXFV2-A4-P2) — London-AM range break with retest-hold
5. V3 family1 (FXFV3-A5-P1) — policy-divergence-gated daily trend (EXPECTANCY_NONPOSITIVE)
6. V3 family2 (FXFV3-A6-P1) — realized-vol-gated policy-rate-differential carry
   (DATA_AUTHORITY_INVALIDATED) + the CLOSED carry region (V4-measured rho 0.997-1.000)
7. V4 family1 (FXFV4-A6-P1) — commodity-bloc risk-off event conditioning (every
   threshold/window variant)
8. V4 family2 (FXFV4-A6-P2) — post-policy-decision drift (REJECT)
9. Blanket clauses (sign inversions, cost softening below 1.5 bps x {1.0,1.5,2.0}, pair
   cherry-picking, re-grading, result-aware reuse, control forgiveness/stress exemptions)
10. E.2 falsification-by-control cluster (9 instances) — both controls designed so a generic
    exposure form that reproduces the anchor fires the preregistered kill, and neither control
    can rescue; P2 additionally front-loads the USD-drift killer

## E.2-conscious control design

- P1: the sham-calendar control RETAINS the whole reversal law and removes only the evidenced
  release timing — plain reversal exposure reproduces it and dies (the V2-family2 failure mode
  is the preregistered death, not an unanticipated one).
- P2: two killers for two confound classes — sign-shuffle (direction-irrelevant exposure) and
  the USD-drift gate (dollar momentum, declared expected-failure gate).
- Neither control can validate the anchor; controls only falsify. Both controls run to
  completion under evidenced semantics (V3R ONE_EVENT_LAG lesson respected).
```
