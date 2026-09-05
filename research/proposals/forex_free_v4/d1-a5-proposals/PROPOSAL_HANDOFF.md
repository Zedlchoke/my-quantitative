# PROPOSAL_HANDOFF — lane A5, cycle FOREX-FREE-V4, D1 blind proposal wave

- lane: A5 (blind proposal lane, axis 2 — inflation and real-rate structure)
- branch: `orca/forex-free-v4-d1-a5-proposals`
- base/wave SHA: `3cf818b566d5de75e147585686a6288cac597f3a` (verified `git rev-parse HEAD` at lane start)
- commit: the single focused commit carrying the three files in this directory (SHA in the lane's final report / `git log`)
- written_before_scoring_utc: 2026-09-05T04:11:57Z

## Files

| file | content |
|---|---|
| `PROPOSAL_FXFV4-A5-P1.json` | family FXFV4-A5-P1 — real-differential class, **DATA_BLOCKED** |
| `PROPOSAL_FXFV4-A5-P2.json` | family FXFV4-A5-P2 — PPP-deviation class, **DATA_BLOCKED** |
| `PROPOSAL_HANDOFF.md` | this handoff |

## Axis-2 determination (why both packets are DATA_BLOCKED, and why none is a runnable packet)

`research/control/forex_free_v4_run/p2_data_authority_v4.json` records:

- `cpi_bis_ws_long_cpi`: **STAGED_NOT_CITABLE** — the series body is fetchable (probe M.AU, 92 monthly obs, keyless sdmx-json v2), but per-print availability evidence is **NOT WIRED**; any assumed publication lag is `AGENT_ASSUMPTION_UNAUTHORIZED` (P-1). Consequence line: "NOT citable by V4 D1 proposals".
- `cpi_ecb_icp`: **NOT_FUNDED** (partner areas uncovered).
- `policy_rates_bis_wscbpol`: **EVIDENCED_CITABLE** (pinned ledger `ae5e1f2e`, 220 rows, 108 EVIDENCED).

Option (a) — a runnable full packet — was evaluated and **rejected as mechanism-dishonest**: with policy rates the only citable macro series, any runnable conditioning is nominal-rate-only. A "real rate" without an inflation term is definitionally a nominal differential; a runnable axis-2 packet would therefore be a carry-class mechanism (axis-1 trespass) and potentially ancestry-tainted against V3 family2 (DATA_AUTHORITY_INVALIDATED). Per the lane instruction ("two (a) proposals that quietly dodge the CPI dependency by being carry mechanisms in disguise are FORBIDDEN — honesty over volume"), the lane outputs **two (b) DATA_BLOCKED memos**, one per named axis-2 class in PLAN section 2.

Both memos are complete pre-registrations: mechanism, falsifiable prediction, literature, PIT observables with per-row evidence classes, 7-pair universe, warmup, holding, entry/exit, next-session fill convention inside the 4-day validator constraint, anchor + neighbour + placebo-style causal control (all designed to RUN TO COMPLETION under evidenced semantics once unblocked), incremental test with a frozen benchmark treatment, frozen cost authority (1.5 bps per fill, tiers x1.5/x2.0 on booked stress PnL, tier-2.0 primary), turnover/sample floors, 3-fold force-flat plan, 8-scenario drop-one (>= 6/8 inherited binding), failure interpretation, source-to-test map, ex-ante margin-to-fail expectations per Stage-A gate, and a signed outcome-blind attestation.

## FXFV4-A5-P1 — real-rate differential median-cross drift (DATA_BLOCKED)

Mechanism: r_real(area,t) = evidenced BIS WS_CBPOL effective rate minus the latest-available evidenced YoY CPI print. Trade the pair when the base-vs-quote real differential is >= 0.25 pp beyond its trailing 252-session median (long the high-real-rate currency; Frankel/Fisher-open class), 20-session holding, daily 16:00 America/New_York decision clock (DST-aware). Causal placebo: inflation-term sign inversion (`D + 2*(pi_b - pi_q)`), which keeps the policy-rate leg and flips the inflation channel — a control that reproduces the anchor with >= 90% decision overlap fails the family. Not a carry relabel: the signal is `sign((i_b - i_q) - (pi_b - pi_q))`, which flips against carry in identifiable states (e.g. US vs JP 2022-24); A7-N is asked to measure rank correlation vs BOTH V3 family2 anchor variants (as-scored and evidenced-corrected). Blocker: CPI per-print availability rows (national statistical agency release calendars / official static pages, precision INSTANT or DAY, archive-hashed, append-only ledger extension, re-pin, vintage regeneration with only-availability-differs invariant, P2 re-gate).

## FXFV4-A5-P2 — real-exchange-rate (PPP-deviation) band reversion (DATA_BLOCKED)

Mechanism: q = log s − (log P_base − log P_quote); when q is >= 2% above its trailing 756-session mean, short the real-overvalued base; >= 2% below, long it; 21-session holding; MONTHLY decision clock (first post-print session, 16:00 NY, one-event-lag rule) — daily-or-slower satisfied. Zero interest-rate inputs by construction (no axis-1 overlap possible). Causal placebo: quote-area price level deliberately read 12 months stale (PIT-legal, so the control always runs); reproduction of the anchor's gate status with >= 90% overlap means the price-level leg is inert and the family fails. Honest effect-size disclosure included: at Rogoff-consensus half-lives (3-5 y) the expected per-month drift is 2-12 bps against 3.0 bps base round-trip cost — the packet pre-states its own high prior probability of gate failure. Blocker: identical CPI evidence wiring as P1.

## Margin-to-fail expectations (ex ante, frozen)

Per-gate priors are in each JSON (`margin_to_fail_expectations`). Shared headline:

- **STRESS_TIER_2.0 (primary)** and **expectancy > 0 (fin-adj)** are the most probable kill gates for both families: documented axis-2 effects are small and slow; base-tier margins of 0-5 bps per trade against 3.0/4.5/6.0 bps cost tiers imply doubled-loss tier books flip negative.
- **Incremental alpha > 0** is second-most at risk (2022-23 USD-cycle confounding, absorbed only partially by the USD-drift benchmark).
- Concentration/drop-one moderate risk (US appears in 7/7 area maps in P1; wide real deviations may concentrate P2 entries).
- MDD, USD-drift, neighbour-support, reproduction-ALL_MATCH (self-consistency only, P-4) LOW risk.
- A base-tier knife-edge pass, if it occurs, must be recorded as such with per-gate margins (P-2). The modal ex-ante outcome is a scored negative or a tier kill — a correct negative is a successful result (P-6).

## Limitations (stated honestly)

1. Both families are UNRUNNABLE this cycle; neither contributed a scored candidate. The lane's output is two preregistrations plus blocker specifications — the sanctioned `FOREX_FREE_V4_BLOCKED_DATA_OR_SELECTION` path.
2. Expected decision counts (P1: 42-98 trades; P2: 160-280 pair-months) are bands conditioned on the unwired CPI path; realized counts below the frozen floors record `SAMPLE_FLOOR_FAIL`, not a rescore.
3. Literature confidence: Frankel 1979, Fisher 1930, Meese-Rogoff 1983, Mark 1995, Engel-West 2005, Rogoff 1996, Lothian-Taylor 1996, Froot-Rogoff 1995, Mussa 1986 stated as confidently existing; Cheung-Chinn-Pascual 2005 volume/page precision marked `[unverified-precision]` in-packet.
4. The blocker requires official per-print CPI release evidence from national statistical agencies; the packet deliberately does NOT assert those agencies' release times (that would itself violate P-1) — the evidence must be collected and archived before any read is legal.
5. P1 shares its policy-rate machinery with axis-1 by construction; the packet discloses this and delegates the measured rho decision to A7-N. P2 has zero rate inputs and is immune to that contamination.

## Outcome-blind attestation

I, lane agent A5 (blind proposal lane, axis 2), designed both packets before any FOREX-FREE-V4 outcome exists. I have not opened `scored_ledger_published.jsonl`, `v3r_records.jsonl`, `v3r_recompute_report.json`, `decision_diff_table.json`, `research/wayfinder/SURVIVORS.md`, or any sibling lane worktree (d1-a4, d1-a6). No per-arm outcome data was consulted; every margin statement is an ex-ante prior. Both packets would be byte-identical if every cell in the program's history had scored zero.

signed: A5_FOREX_V4_BLIND_LANE_AXIS2 — 2026-09-05T04:11:57Z
