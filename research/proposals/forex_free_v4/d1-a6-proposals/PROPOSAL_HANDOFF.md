# PROPOSAL_HANDOFF — lane A6 (open axis), cycle FOREX-FREE-V4

- Lane: A6 (blind proposal lane, axis 3 — open axis)
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v4/d1-a6-proposals`
- Branch: `orca/forex-free-v4-d1-a6-proposals`
- Base / wave SHA: `3cf818b566d5de75e147585686a6288cac597f3a` (verified with `git rev-parse HEAD` before any write)
- Files delivered (this directory only):
  - `PROPOSAL_FXFV4-A6-P1.json`
  - `PROPOSAL_FXFV4-A6-P2.json`
  - `PROPOSAL_HANDOFF.md`
- Proposal IDs: `FXFV4-A6-P1`, `FXFV4-A6-P2`
- Nothing outside `research/proposals/forex_free_v4/d1-a6-proposals/` was modified. No installs, no scored or heavy computation, no data loads.

## P1 — FXFV4-A6-P1: commodity-bloc risk-off event basket (price-only)

At each daily 16:00 America/New_York decision (DST-aware, 20:00Z/21:00Z), compute the
commodity-bloc strength `S_t = mean( r(AUD/USD), r(NZD/USD), −r(USD/CAD) )` from the
authorized H1 snapshot's daily 16:00-NY closes and standardize over the trailing 60
completed NY-days. On a risk-off event (`z_t <= −1.0`), enter a frozen 5-leg basket at the
next-session 16:00-NY bar open when flat — short AUD/USD, short NZD/USD, long USD/CAD,
short USD/JPY, short USD/CHF — and hold exactly 5 NY-days (fixed horizon, no refresh).
Causal claim: the cross-sectional response to a commodity-bloc risk-off day continues to
drift for days because the forced flows are gradual (vol-target/risk-parity deleveraging on
trailing risk, margin and carry-unwind cascades — Brunnermeier-Pedersen 2009; Brunnermeier-
Nagel-Pedersen 2009), while safe-haven currency behavior (Ranaldo-Söderlind 2010 RoF 14(3);
Habib-Stracca 2012 JIMF) and the commodity-currency identity of AUD/NZD/CAD
(Chen-Rogoff-Rossi 2010 QJE 125(3); Cashin-Céspedes-Sahay 2004 JDevEcon 75(1)) fix the
signed cross-section. Arms: anchor / neighbour (median instead of mean bloc estimator —
one presumption away) / placebo control (trigger read from the sham majors bloc
EUR/USD+GBP/USD, preregistered non-reproduction rule: control expectancy > 0 AND PF >= 1.10,
or control expectancy >= 0.5 x anchor -> family fails). Incremental benchmark: identical law
with the trigger read +10 NY-days stale (staleness exceeds the 5-day drift window).
EUR/USD and GBP/USD are excluded from the anchor precisely so they can serve as the sham
trigger bloc — an ex ante design-integrity exclusion, not a result-aware subset.

## P2 — FXFV4-A6-P2: policy-change underreaction drift with hike/cut asymmetry

Events are RATE_CHANGE rows of the pinned v2 announcement ledger
(sha256 `ae5e1f2e64b8aa7c08472755bd73857543aa89b72ea81b70ad5c5d81e7cd6bd4`; 220 rows =
212 RATE_CHANGE + 8 BASELINE_LEVEL, areas AU 50 / NZ 50 / CA 22 / CH 22 / GB 22 / US 22 /
EMU 19 / JP 5; 108 EVIDENCED, 104 conservative-LATER) — EVIDENCED_CITABLE per
`p2_data_authority_v4.json`. A change in area A is eligible at the first daily 16:00-NY
decision whose completion instant >= its `operative_available_time_utc` (never on the
effective date alone; no-stamp rows fail closed). Direction: the delta sign mapped to A's
own pair with frozen base/quote sign convention (A = US drives all 7 pairs long-USD on a
hike); hold 10 NY-days (anchor). Neighbour: hike hold 10 / cut hold 3 (asymmetric
persistence). Control: frozen +3 derangement over the area order
[US, EMU, GB, JP, CH, CA, AU, NZ] re-mapping every area's events to a different area's pair,
with disclosed leakage through USD legs and globally synchronized rate cycles. Incremental
benchmark: every availability instant shifted +180 calendar days (stale events).
Literature: Andersen-Bollerslev-Diebold-Vega 2003 AER 93(1) and Faust-Rogers-Wang-Wright
2007 JME 54(4) (event-time response; the claim under test is the residual multi-day drift,
not the instant jump); Molodtsova-Papell 2009 JIE 77(2); Rossi 2013 JEL 51(4) as the honest
counterweight; Cover 1992 QJE 107(4) and Bernanke-Kuttner 2005 JF 60(3) as asymmetry/
surprise analogs; Ehrmann-Fratzscher and Kearns-Manners cited for concept, marked
[unverified]. Sample honesty: est. 180-260 trades vs the 140 floor (thin, INDETERMINATE
risk declared); JP contributes only 5 events (drop-one near-vacuity for USD/JPY disclosed).

## Novelty comparison summary (vs every forbidden row — different information source AND different causal control)

| Forbidden row | P1 differs because | P2 differs because |
|---|---|---|
| V1 f1 London-open momentum continuation (intraday) | cross-pair bloc z-score observable, daily clock, fixed 5-day basket holds, sham-bloc control | evidenced policy-event ledger observable, daily clock, 10-day event holds, sham-derangement control |
| V1 f2 late-NY standardized-extension fade (intraday) | no extension observable, no fade — predicts multi-day CONTINUATION after a cross-sectional event; not a sign inversion (different observable/source/horizon) | no extension observable, no fade; event-drift from policy deltas, not price geometry |
| V2 f1 Tokyo compression -> London expansion | no session range or compression/expansion transition anywhere | no session structure anywhere |
| V2 f2 London-AM break + retest-hold | no break, no retest confirmation | no break, no retest confirmation |
| V3 f1 FXFV3-A5-P1 policy-divergence-gated daily trend | no policy input and no price-trend term; direction from a frozen cross-sectional event map | no price-trend term; conditioning is the point-event delta sign at availability time, not a differential path gate |
| V3 f2 FXFV3-A6-P1 vol-gated policy-differential carry (INVALIDATED) | no differential, no vol gate, no carry holding law; not the Section 1.1 front door and does not invoke it | differential LEVEL never a signal (only the event DELTA sign); no vol gate; not a re-grade or descendant of the invalidated row |

Blanket clauses respected: no sign inversions, no cost assumptions below the frozen
1.5 bps x {1.0, 1.5, 2.0} authority (F1-fixed, applied to booked stress PnL), no pair
cherry-picking (all subsets fixed ex ante with causal justification), no result-aware reuse
of earlier packets. Lane diversity: P1 is price-only (policy rates appear only inside the
frozen financing kernel — accounting, not signal); P2 uses policy rates in an
event-response role only (the controller's open-axis brief lists forward-guidance asymmetry
explicitly for this lane); neither touches A4's carry region or A5's inflation axis, and
CPI-class series (STAGED_NOT_CITABLE / NOT_FUNDED per P2 authority) are unused.

## Margin-to-fail expectations (ex ante, per Stage-A gate; from the packets)

- Both families expect the knife-edge class of gates to be PF >= 1.10 and the PRIMARY
  tier-2.0 stress gate (expected tier-2.0 PF 0.95-1.15 in both) — the same gate class that
  killed the V3 arc. Cost headroom is NOT the expected failure mode if a gross effect exists
  (expected gross 15-80 bps vs 6 bps RT tier-2.0 requirement).
- P1: F1 fold population is thin (est. 1.0-1.8x the 30-trade floor); trades margin over the
  140 floor est. 1.25-2.5x; incremental-alpha margin THIN-POSITIVE (stale-trigger overlap
  risk disclosed); sham-bloc control is a genuine falsification risk by design (EUR/GBP
  risk-factor leakage disclosed). USD-drift margin expected 0.10-0.25 (near-USD-neutral
  basket by construction).
- P2: USD-drift diagnostic is declared the most likely single-gate failure (US events are
  ~45% of pair-events; expected |corr| 0.2-0.5 vs the 0.3 ceiling; exclusion of US events
  was considered and rejected ex ante because it forces an INDETERMINATE below-floor book).
  Trades margin over the 140 floor est. 1.3-1.9x — thin, INDETERMINATE-by-rule risk
  declared. Concentration and fold-share knife-edge under event clustering (March 2020,
  2022-2023 waves).
- Both: below-floor cells are INDETERMINATE (never negative evidence); a firing control or
  failed incremental alpha is terminal regardless of the anchor's sign; no post-observation
  tuning of thresholds, horizons, maps, legs or clocks.

## Limitations

- Design estimates only: all turnover/MDD/margin numbers are schedule-level priors from the
  frozen constants, not measurements (no data was loaded in this lane).
- P1's falsification rests on a 6.3-year post-warmup span with a single global stress
  regime cluster (2020); regime coverage is what it is — declared, not engineered around.
- P2's evidence mix (108 EVIDENCED / 104 conservative-LATER rows) means part of the book is
  availability-conservative by construction; the P2 authority doc's "108/151" classification
  and the lane's raw 212-RATE_CHANGE count are both cited in the packet — the operative
  classification at implementation follows the P2 authority.
- P2 drop-one has a disclosed near-vacuous scenario (USD/JPY, 5 JP events).
- Unverified literature items are marked in-packet (Ehrmann-Fratzscher, Kearns-Manners,
  and recalled page numbers on canonical citations).

## Signed outcome-blind attestation

I, lane agent A6 (FOREX-FREE-V4, blind proposal lane, open axis), attest that both packets
above were designed and written BEFORE any V4 outcome exists and without access to any
scored artifact. I read only: the owner plan (PLAN_forex_v4.md sections 1, 2, 7, 12), the
cumulative forbidden-family inventory, the V4 P2 data authority catalog, the pinned v2
announcement ledger (availability evidence), the V4 P3 baseline-invariant gate constants,
the V3 w3 freeze (frozen cost/convention authority), the V3 data-authority dispositions,
and the V3 A5/A6 proposal PACKETS (format + novelty differentiation only). I did NOT open
`scored_ledger_published.jsonl`, `v3r_records.jsonl`, `v3r_recompute_report.json`,
`decision_diff_table.json`, `SURVIVORS.md`, any other V4 lane's worktree, or any per-arm
PnL/outcome/verdict file. I loaded no market data, fetched no series, ran no backtest or
simulation; every numeric claim is a frozen design constant, a schedule-level estimate, or
an evidence count. — A6, 2026-09-05.
