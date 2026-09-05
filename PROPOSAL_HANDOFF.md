# PROPOSAL_HANDOFF — lane A4 (blind proposal lane, per-print CPI axis), cycle FOREX-FREE-V5

```yaml
agent: A4_FOREX_V5_BLIND_LANE_PER_PRINT_AXIS
lane: A4 (axis 1 — per-print CPI timing structure; blind outcome proposal lane)
cycle: FOREX-FREE-V5
branch: orca/forex-free-v5-d1-a4-proposals
base_sha: e2b7a0e1e29794ca8449625f271f9a67c302fcf2
commit_sha: SELF-REFERENTIAL — the single D1-A4 commit carrying the three files listed in
  changed_files on this branch; obtain with `git -C <worktree> rev-parse HEAD` after the
  commit lands (single-commit constraint prevents embedding its own SHA; V4-lane precedent)
changed_files:
  - PROPOSAL_FXFV5-A4-P1.json
  - PROPOSAL_FXFV5-A4-P2.json
  - PROPOSAL_HANDOFF.md
tests: none run — documentation-only lane (no backtest, no dry-run, no scored or PnL
  computation of any kind; the frozen suites under tests/assets/forex_free_v3/ are cited
  as convention authorities, not executed by this lane)
known_limitations:
  - PLAN_forex_v5.md is not in this worktree's base tree (added on main at 704c6a9, not an
    ancestor of e2b7a0e); it was read read-only from the shared main checkout
    /Users/hoangminhlong/my-quantitative/PLAN_forex_v5.md — no file outside the worktree was
    created or modified. Sections 1, 2 and 4 are the operative authorities used here.
  - Pair concentration is structural, not chosen — CA (105) + GB (88) are ~78% of the 246
    evidenced clocks; PAIR_CONCENTRATION_ABOVE_40PCT is a live disclosed risk in both packets.
  - P2 anchor decision-count risk — trades only on consecutive-print sign agreement; if the
    agreement rate lands below ~17% the book falls under the frozen 40-decision floor and
    records terminal SAMPLE_FLOOR_FAIL (disclosed, never tuned around).
  - AU conditioning is partial by evidence (23 clocks; documented archive gaps pre-Sep-2019
    and mid-2022); all AU decisions/sequences fail closed on unevidenced months.
  - GB/AU DAY-precision stamps (23:59:59Z) force a structural next-day availability lag on
    the daily 16:00-NY clock; CA/NZ INSTANT stamps allow same-NY-day decisions; all decisions
    are strictly after available_time_utc parsed with recorded offsets (NZ stamps carry
    +12:00/+13:00 offsets and fall on the previous UTC day).
  - Nearest forbidden ancestry is FXFV4-A6-P1 (event-basket shape, fixed hold); |rho| <= 0.20
    novelty vs ALL forbidden ancestry is accepted as a measured D2 adjudication, prose claims
    in the packets are not the test.
  - No print VALUES exist in the evidence (release-calendar timing only) — both mechanisms
    are deliberately timing-structure mechanisms; any surprise/value-conditioned variant is
    out of scope this cycle.
  - Literature rows carry [unverified]/[unverified-precision] flags where citation precision
    is from memory.
tree_clean: true
workers: 0
scored_outcome_seen: none exists — Phase P measured 0 PnL; outcome-blind attestation signed
  inside each proposal JSON and reaffirmed below
```

## One-line mechanism summaries

- **FXFV5-A4-P1 — `post_print_reaction_direction_drift`:** when a domestic CPI print becomes
  evidenced-available (246 clocks, GB/CA/AU/NZ), take the local pair in the sign of the
  availability-exact print-window reaction (first 16:00-NY close after availability vs last
  before), filled next bar, held H=5 (anchor) / H=10 (neighbour); control = identical rule at
  matched NON-print days — placebo reproduction falsifies.
- **FXFV5-A4-P2 — `consecutive_print_sequence_confirmation_drift`:** trade only when two
  consecutive evidenced prints of the same economy produce same-sign reactions, in the common
  direction, held Q=15 (anchor) / Q=30 (neighbour) at the inter-print scale; control =
  cross-economy pseudo-sequences (donor map GB->CA->AU->NZ->GB) at identical decision instants —
  pseudo-sequence reproduction falsifies.

Both: evidence-dictated 4-pair universe (GBPUSD/USDCAD/AUDUSD/NZDUSD — the only pairs with an
evidenced non-US CPI leg; EURUSD/USDJPY/USDCHF excluded because EMU/JP/CH are unevidenced for
per-print timing), daily 16:00 America/New_York DST decision clock, next-bar fills, frozen cost
schedule 1.5 bps/side x {1.0, 1.5, 2.0} tiers with tier 2.0 primary on booked stress PnL,
dual-book financing under the frozen formula (zero rate content in the signals), exactly three
scored arms each, pre-registered falsification rules and expected-failure interpretations.

## Pre-registered classes — carry-forward, NOT proposed (per lane instruction)

- `real_differential` — **DATA_BLOCKED_VALID, carried forward as blocked, not selected**: needs
  both legs including the US CPI leg, which is UNAVAILABLE_FAIL_CLOSED (p0_verdict.json).
- `PPP_deviation` — **DATA_BLOCKED_VALID, carried forward as blocked, not selected**: needs both
  legs; equally blocked by the unevidenced US leg.

P1 is disclosed inside the packet as class-ADJACENT but honest within-bloc (per-print timing
structure only; no US leg, no CPI levels, no differentials) — it does not implement, proxy, or
rescue either blocked class.

## What was read (sanctioned packet only)

`PLAN_forex_v5.md` sections 1/2/4 (shared main checkout, see known_limitations);
`research/control/forex_free_v5_run/p0_verdict.json`, `p0a_cpi_availability_table.json`,
`p3_conditioning_clocks_v5.json` (246 clocks, counts verified GB 88 / CA 105 / AU 23 / NZ 30,
per-row archive_sha256), `p2_data_authority_v5.json`;
`research/control/forex_free_v4_run/forbidden_family_inventory.json` (cumulative ancestry);
`research/wayfinder/HYPOTHESIS_LEDGER.md` sections D and E.2 (read from the shared main
checkout — file not present in this worktree's base tree either; read-only);
`tests/assets/forex_free_v3/test_accounting.py` and `test_scored_runner.py` plus the frozen
`research/assets/forex_free_v3/scored_runner.py` constants (folds B0 2020-03-01 / 2022-05-01 /
2024-08-01, PURGE_DAYS 14, per-arm floor 40, gates, session gate, dual-book contract — cited,
not executed). No scored outcome file exists in this cycle; no other lane's worktree was
entered; no forbidden artifact (V3R records, SURVIVORS.md, published ledgers) was opened.

## Notes for A7-N / D2

- Measure |rho| for both anchors against FXFV4-A6-P1's event-basket books (nearest shape
  ancestor) and against generic same-horizon momentum; the packets accept the measured decision.
- If both families are selected, all six arms consume the cycle's full six-cell budget; P2's F5
  asks for material non-identity verification between the two anchors (decision-date overlap +
  rank correlation) as disclosed context.
- Both packets are self-falsifying by design (placebo / pseudo-sequence controls run to
  completion under evidenced semantics — the V3R refused-control failure mode is designed out).

## Outcome-blind attestation

Signed inside each proposal JSON and reaffirmed here: lane agent A4 has seen NO scored outcome
for any arm of either proposal — none exists (Phase P measured 0 PnL; S1 SEALED_UNTOUCHED; no
backtest, dry-run, or gate computation performed by this lane). All design constants were fixed
ex ante from the sanctioned evidence files and frozen conventions. Both packets would be
byte-identical if every cell in the program's history had scored zero.

signed: A4_FOREX_V5_BLIND_LANE_PER_PRINT_AXIS — 2026-09-05
