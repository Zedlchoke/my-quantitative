# SKEPTIC F-0 COURT REPORT — PWS-CX-SOLUSDT-C1 — verdict on P2-1

- **Lane:** economic-skeptic (outcome-blind, pre-PnL, VETO power). Authored 2026-09-26.
- **Worktree / branch:** `/Users/hoangminhlong/my-quantitative/.worktrees/pws-cx-solusdt-c1/integration`
  @ `orca/pws-cx-solusdt-c1-integration`.
- **Base (dispatch) sha:** `5aadae7a515962feb85f523e73410d30ae907296` (= HEAD at lane start, verified).
- **Input under judgment:** exactly ONE submitted proposal — `council/P2_PROPOSALS.md`
  §1, **P2-1 TAILPAYER-RUN-REGIME CAPTURE** (read in full). P1 submitted zero
  (`council/P1_PROPOSALS.md`, read as context for what is already dead).
- **Outcome-blindness held:** no scored outcome file opened; no PnL exists for this
  cycle. Representation math was computed **on the funding plane only** (settled
  funding series — cost-book class, explicitly authorized by the dispatch: "you may
  compute REPRESENTATIONS on the funding/kline planes … representation math, not
  outcome PnL"). The 1h kline plane was NOT consumed; no return series of any
  strategy was computed; every statistic below is a gate-state / episode-count /
  cross-representation correlation on the settlement grid.
- **Authority read:** master `plans/PLAN_pws_program_v1.md` §2.2–2.3 (F-0 court,
  anti-variant law), §6.4 (kill rules); child `plans/PLAN_pws_cx_solusdt_c1.md`
  §2–§3 (C3); `research/wayfinder/FAMILY_FAILURES.jsonl` crypto rows (CARRY-1D/3D/7D,
  TRACKB1-CLASSA, H-FUNDCROWD-MR-v2, V17-A6-P1-FUNDJUMP, SRLVCX1-M1-SETTLE-RESOLVE,
  A6-V16-F2 RUNPERSIST, CNG2-A5-P1); `research/wayfinder/LESSONS.md` P-27/P-28;
  `research/wayfinder/MAP.md`; `research/control/SRLV-PROGRAM-V1/OUTCOME_EXPOSURE_MAP.md` §4.

---

## 0. Verdict (up front)

> **P2-1: `VETOED_SAME_FAMILY` (K-F0 pre-PnL, zero scored cells).**
>
> Independent supporting pre-kills on the measured SOL distribution:
> (i) **ceiling×power empty intersection** — the proposal's own F-5 ceiling law
> (`r̄_run × 3 ≥ RT_stress`) and the ≥100-closed-RT power floor are **jointly
> unsatisfiable at every K tested** (0–1 episodes at ceiling vs ≥100 floor)
> ⇒ K-COST/K-THIN certain (advisory — cost auditor owns the verdict);
> (ii) **K-CONC arithmetic** — 59.1% of the entire 6-year negative-payment mass
> is 2022 and 42.2% sits inside the 9-day FTX anomaly window; the 4 deepest
> single settlements (−200 bps each) are 13.8% of that mass and **cannot be
> harvested by any ≥K-run persistence gate** — the mechanism targets exactly the
> mass its gate excludes, and the mass its gate includes cannot pay the bill.

The VETO is the F-0 same-family kill (skeleton test, §2 below), corroborated by a
**measured** ancestry representation: at every gate setting with viable episode
count, the P2-1 frozen representation correlates **rho 0.31–0.61** with the dead
funding-LEVEL window carry shadows — 1.5–3× above the immovable 0.20 bar,
reproducing and exceeding the V17 FUNDJUMP precedent (0.2439) on SOL-specific data.

---

## 1. Representation-math disclosure (inputs, definitions, reproducibility)

- Funding series: `data_local/funding/fapi_scan2026_H1_SOLUSDT.json` (sha256
  `3dcac8d8…332c0`) + `fapi_scan2026a_H2_SOLUSDT.json` (sha256 `3c5366…3c1cb1c`),
  sha-verified against `C1_machine_FUNDING_STATS_SOLUSDT.json` before use; boundary
  duplicate dropped on `fundingTime`; **n = 6,580 reproduced exactly**; mean
  +0.0138 bps/settlement, median +0.858, neg share 28.62%, 1 zero-rate settlement —
  all four reproduce the C1 census file.
- Run definition as the proposal pins it (field 3): maximal stretches of same-sign
  settlements (zeros break runs), counted in settlements, requiring wall-clock span
  ≥ K×6h to constitute one regime (FTX-week cadence robust). Entry observable =
  mean of the FIRST K settlements (what a PIT book can know at the K-th settlement).
  1,234 maximal runs; 484 with len ≥ 3; 258 with len ≥ 5; 153 with len ≥ 8.
- Cost book for the ceiling: fee 10 bps RT (DECLARED, CHR3F) + full spread crossed
  once per RT from the (new, data-gate-lane) spread census pooled p50 = 0.469 bps
  ⇒ RT_base 10.47 bps; ×1.5 = 15.70; ×2.0 = 20.94. Ceiling θ_min = RT/H_min =
  3.49 / 5.23 / 6.98 bps/settlement. Sensitivity: with spread = 0 and no stress
  (fee-only floor, θ_min = 3.33) the conclusion below does not change.
- Ancestry shadows (dead-family reconstructions on the same grid): trailing-window
  **funding-LEVEL receiver** states at W ∈ {3, 9, 21, 90} settlements (1D/3D/7D/30D
  at nominal 8h — the CARRY-1D/3D/7D / always-hold-receiver class), an
  **unconditional receiver** state, and a **V17-FUNDJUMP-style event** shadow
  (|Δannounced rate| ≥ its p90 → hold receiver 3 settlements). Pooled Spearman on
  all 6,580 grid points, gate state vs shadow state (representation rho, not a
  returns rho — the formal F-1 one-shot on the frozen representation remains the
  implementer's, but §3 makes a pass implausible).
- Repro: the two scripts are one-file python, stdlib + numpy/pandas only; commands
  and outputs recorded in `handoffs/HANDOFF_skeptic_f0.json` → `tests`.

## 2. F-0 test 1 — SKELETON TEST: **FAIL** (the load-bearing kill)

Strip the run-gate observable; keep trigger/direction/exit shape: "hold the
RECEIVING side of the funding stream; exit when the funding sign regime ends."
That is verbatim the skeleton of the recorded dead families:

- `CARRY-1D/3D/7D` (SCIENTIFIC_REJECTION — cross-sectional funding carry, cost-
  dominated; XSECT sleeve 77:1 cost:carry at 0.62×/day turnover), and the
  **unconditional always-hold-receiver form** the proposal itself measures at
  +0.91% gross / 6 years.
- `TRACKB1-CLASSA-FUNDING-LEVEL-GATED-CARRY` (SELECTION_REJECTION) — whose
  recorded reopening condition closes the funding-level surface against "ALL
  funding-level-derived gates — **window/percentile/change/run transforms alike**"
  (identity rho 1.0 on BTC; the run transform is named inside the closed class).
- `V17-A6-P1-FUNDJUMP` (SELECTION_REJECTION) — the CHANGE transform of the same
  series died at pooled rho 0.2439 vs the level proxy: "the event form still
  carries the forbidden level."
- Blind convergence: P1's independent W1 autopsy had already enumerated
  "level-gated / **persistence-gated / sign-run** / squeeze-mirror /
  clamp-conditional" as ONE funding-carry family. Two outcome-blind lanes drew
  the same family boundary; the skeptic concurs with both.

The proposal's own §1.2 self-court concedes the stripped skeleton is the dead
carry skeleton and stakes the identity on **gate incrementality**. Measured, the
gate does not deliver incrementality where the book is alive:

| gate (K=3 anchor, span≥18h) | episodes | occupancy | rho vs W=3 (1D) | vs W=9 (3D) | vs W=21 (7D) | vs W=90 (30D) | vs uncond. receiver |
|---|---|---|---|---|---|---|---|
| θ = 0.50 bps | 147 | 48.5% | **+0.607** | **+0.540** | **+0.493** | **+0.353** | **+0.615** |
| θ = 1.00 bps | 48 | 26.7% | **+0.377** | **+0.333** | **+0.310** | **+0.203** | **+0.383** |
| θ = 1.50 bps | 8 | 3.9% | +0.123 | +0.100 | +0.102 | −0.026 | +0.128 |
| θ = 2.00 bps | 3 | 1.9% | +0.084 | +0.077 | +0.059 | +0.013 | +0.087 |
| θ = 3.49 (base-book ceiling) | 1 | 0.2% | +0.016 | −0.018 | −0.060 | −0.060 | +0.025 |

Also: rho vs the V17-FUNDJUMP-style event shadow = **+0.319** at θ = 1.0. The
fence is |rho| ≤ 0.20, immovable (master §6.4 K-ANC; crypto-ng 11/11 died at this
bar). **At every gate with ≥48 episodes, rho = 0.31–0.61 — the gate is cosmetic,
not incremental.** The mechanism is structural: SOL funding sign is highly
persistent (rate autocorr lag-1 **+0.853**, lag-2 +0.780, lag-3 +0.731, lag-6
+0.527; P(next settlement same sign) **0.812**), so a sign-run state IS the
trailing level's sign, smoothed. A persistence gate cannot decorrelate from the
level family because the thing persisting is the level itself.

Under master §2.3 (anti-variant law): vs the dead carry family, P2-1 differs in
**risk shape** (directional single-pair vs delta-neutral basket) = 1 of the 3
required axes; **payer is the same** (contractual funding counterparty — P2
concedes this; P1's W1 scored payer PASS); **information layer is the same
settled funding series** (a run statistic is a transform of it, per P-27 "adding
an observable is not a new mechanism" and the TRACKB1 closing language). 1 of 3
⇒ ONE identity ⇒ `VETO_VARIANT_SAME_FAMILY`.

The low-turnover defense is examined and rejected as the gate's incrementality
claim, not accepted as a new risk shape: turnover-reduction via an entry gate on
the same series is precisely the "adding/binding a filter-gate observable while
trigger/direction/exit shape and payer are the same" clause of §2.3. The XSECT
ancestor died on cost:carry, and §4 shows the gate does not rescue the ceiling
either — it vacates the book.

## 3. F-0 test 2 — PAYER TEST: **PASS** (with two honesty flags, not vetoes)

The payer is identifiable and contractually forced: the levered crowd on the
losing-crowding side pays funding at every settlement it remains positioned; the
payer's existence and persistence are evidenced by the measured signed series
(1,883 negative settlements). No fictional counterparty — this is the clean payer
of the space (P1 W1 concurs: payer PASS). Self-arbitrage (unwind) exists and is
observable as the regime end; the exit is the crowd's own unwind.

Flags for the record (C4 matters, not F-0 vetoes):

1. **Exit-into-forced-flow:** the exit trigger (settled sign flip) is the
   unwinding crowd's own flow moment; the book crosses the spread against it.
   Spread census p99 in stressed hours reaches 2.3–5 bps — second-order vs the
   fee bill but the freeze must pin settlement-hour fill treatment.
2. **Price-only spec clause is a near-certain C4 spec-fail as designed:** an
   unlevered 1x directional hold of 1–3 weeks carries price PnL that dwarfs
   1–30 bps/settlement credits; "net edge = funding credit only" requires episode
   price PnL ≈ 0. P2 pre-declared this honestly as a spec check (price-driven
   edge = MIS-SPECIFIED = kill). Any future revival must keep that
   pre-registration; it is the correct falsifier for this payer story.

## 4. F-0 test 3 — INFORMATION TEST: **PASS on construction** (pins demanded, moot)

The run statistic is genuinely PIT-constructible from settled data only: state
uses rates known AT their `fundingTime`; entry executes on the 1h bar AFTER the
K-th confirming settlement; no predicted-rate input. The wall-clock span pin
(≥K×6h) makes the definition cadence-robust — measured on the actual anomaly:
despite 101 spacings of 1–4h in 2022-11-09..11-18, **no ≥K-run with entry-observable
mean ≥ 4 bps/settlement exists anywhere in the 6,580-settlement series**
(theta sweep: θ≥1 → 56 runs; θ≥2 → 3; θ≥3 → 2; θ≥4 → 0). The FTX windfall is
single settlements (four −200 bps prints), not runs — the pinned definition
correctly refuses to let cadence stacking manufacture a regime. Q-7: the
crowding-state observable is real information not contained in clock/trend/spread;
the unconditional premium being ≈ 0 confirms the information lives in the
conditioning. The test passes as a matter of construction — the failure is that
this information is **not new relative to the dead funding-LEVEL family** (§2),
and there is almost none of it above the cost floor (§5).

Pinning demands had this survived (moot, but on record): (a) T_max = 42 is
denominated in settlements while the entry gate is wall-clock normalized — 42
settlements ≈ 14 days nominal but ≈ 4 days at FTX cadence; pin T_max in
wall-clock or justify the asymmetry; (b) θ_renew has no numeric value in the
proposal — pin it at freeze; (c) pin the single zero-rate settlement as a
run-breaker; (d) pin the force-flat/truncation rule for the 2026-08-21..08-31
funding tail (10.3 days uncovered).

## 5. COST-CEILING PRE-SCREEN (advisory — cost auditor owns the verdict)

Episodes passing the proposal's own ceiling law `r̄_run × H_min(3) ≥ RT_stress`
(entry-observable first-K mean, span ≥ K×6h), measured:

| K | θ (bps) | book | episodes | settlements covered |
|---|---|---|---|---|
| 3 | 5.23 (×1.5) | stress | **0** | 0 |
| 3 | 6.98 (×2.0) | stress | **0** | 0 |
| 5 | 5.23 (×1.5) | stress | **1** | 12 |
| 5 | 6.98 (×2.0) | stress | **0** | 0 |
| 8 | 5.23 (×1.5) | stress | **1** | 12 |
| 8 | 6.98 (×2.0) | stress | **1** | 12 |

Ex-post upper bound (full-run mean — not entry-observable, i.e., lookahead):
θ = 5.23 → 5 runs; θ = 6.98 → 2. Power floor ≥100 closed RT is missed by
**two orders of magnitude** in every reading. Structural check: scanning the full
(θ, K) grid, **no setting satisfies the ceiling law (×1.5) AND ≥100 episodes —
the feasible set is EMPTY** for K ∈ {3,5,8}; even the base book (no stress,
θ = 3.49) yields 1–2 episodes. The only paper region that re-opens episodes
(θ ≈ 0.7, H_min ≥ ~22 settlements) is closed twice: rho 0.38–0.61 there (§2),
and H_min is a ceiling *assumption*, not an exit — stretching it to make the
inequality pass is tuning against the measured distribution (P-27/Q-2: the gate
selecting cheap states does not make the executor's charge cheap).

New fact for the cost auditor: the spread census now EXISTS
(`C1_machine_SPREAD_CENSUS_SOLUSDT.json`, generated 2026-09-26T11:46Z, after P2
authored its NOT_RUN claim) — pooled p50 spread 0.469 bps, but measurable **only
2023-05..2024-04** from keyless archives (2020-09..2023-04 and 2024-05..2026-08
UNMEASURABLE) — coverage remains fail-closed for their lane. My verdict is robust
to it: with spread = 0 and no stress multiplier (fee-only θ_min = 3.33), the
theta sweep still yields ≤2 episodes.

**K-CONC arithmetic (independent pre-kill if either gate were somehow passed):**
total negative-payment mass 7,252.5 bps-sum over 6 years; **2022 = 59.1%**;
**FTX window 2022-11-09..18 = 42.2%**; the 4 deepest single settlements
(−200 bps each, all in that window) = **13.8%**. Every plausibly qualifying
episode lives in one regime/one window ⇒ the 0.50 fold bar is structurally
unreachable — the third occurrence pattern (CARRY-7D 51.7%, H-FUNDCROWD 68–81%).

## 6. Why VETO, not CONDITIONAL-PASS

A conditional pass demands binding freeze conditions; no condition can repair a
distribution fact. The identity requires simultaneously: (a) ≥100 episodes
(power), (b) ceiling law satisfied per episode (its own construction), (c)
|rho| ≤ 0.20 vs dead shadows (ancestry). On the measured SOL funding series the
feasible set of (K, θ) satisfying (a)∧(b) is EMPTY, and at every (a)-viable θ,
(c) fails by 1.5–3×. This is not a marginal near-miss to condition on; it is the
same family measured again on a new pair. The correct disposition is a pre-PnL
kill at zero scored cells — exactly the "cheap kill the owner note prescribes",
and the outcome P2 itself ranked most likely (its §5 modal outcome #1).

## 7. Revival conditions (family law — what would reopen this surface)

Per the TRACKB1 reopening language, adapted and measured here on SOL:

1. **A non-funding-level PIT axis** (OI history / liquidation tape / L2 — all
   BLOCKED today): a payer or state not derived from the funding level. Owner
   data-authority action required.
2. **A dated measured cost-regime break** (taker-fee structure change or legal
   maker execution): re-run §5's arithmetic on new fee bytes.
3. **A dated distribution break:** the SOL funding series developing ≥100
   same-sign runs with entry-observable means ≥ RT_stress/H_min — i.e., this
   exact representation math re-run on future settlements. Until then,
   re-clock / re-label / re-window / re-threshold / pair-swap / sign-flip
   variants remain pre-vetoed (master §2.3, P-27, P-28).

## 8. Incidents / limitations

- Incidents: none. One data-plane note: the spread census artifact appeared
  mid-flight (untracked data-gate-lane file; consumed read-only for §5; not
  modified, not committed by this lane).
- Limitations: (i) representation rho is a state-series correlation, not the
  formal F-1 returns rho — the implementer's one-shot on the frozen
  representation is still the binding test, but at 2–3× the bar on every
  power-viable gate a pass is not plausible; (ii) episode definition bracketed
  both ways (entry-observable first-K mean and ex-post full-run mean); (iii) the
  kline plane was not consumed — no fill/vol conditioning was measured (not
  needed for this verdict); (iv) single-source fapi funding (Vision cross-check
  NOT_RUN, inherited disclosed item) — affects level placement, not the
  order-of-magnitude episode arithmetic.

— ECONOMIC SKEPTIC lane, PWS-CX-SOLUSDT-C1, F-0 court
