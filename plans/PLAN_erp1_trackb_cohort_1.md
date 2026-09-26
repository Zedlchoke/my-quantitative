# PLAN (DRAFT) — ERP1-TRACKB-COHORT-1 — BTCUSDT spot–perp delta-neutral basis/carry: cohort 1

> **Status: `DRAFT_FOR_OWNER_GO — NOT REGISTERED, NOT EXECUTED.** This file
> registers nothing, starts no worker, downloads no data, opens no S1, places
> no order, consumes no GO, and touches no running shadow worker/dashboard.
> Parent law: `plans/PLAN_economic_robustness_program_v1.md` (umbrella,
> ACTIVE_LIGHT) §5.4 Track B, §§5.1–5.15, §6–9; program layer
> `plans/PLAN_erp_trackb_program_v1.md` (ERP-TRACKB-PROGRAM-V1 charter).
> Registration only via `researchctl cycle register` after owner GO on this
> plan (proposed command in the owner packet). This child implements umbrella
> §10 item 6 (there named `ERP1-TRACKB-CARRY-DELTA-NEUTRAL-V2`; the id
> `ERP1-TRACKB-COHORT-1` is chosen for Track A/B symmetry — same object,
> disclosed).
>
> Authored 2026-09-26 by Lead from explicit owner instruction (verbatim
> intent: mở hướng BTCUSDT spot–perpetual delta-neutral basis/carry; lập kế
> hoạch + triển khai theo từng gate; KHÔNG phải GO vĩnh viễn cho scoring,
> sealed OOS, shadow hay giao dịch; vốn chung 100.000 USD không nhân đôi cho
> hai chân; dừng chờ owner tại gate bắt buộc).

## 0. Cycle identity

```text
cycle_id     ERP1-TRACKB-COHORT-1
class        MECHANISM COHORT (outcome-blind council -> pre-PnL
             falsification -> frozen scored trials under a paper-tier
             measured-cost book; verdict class bounded per program §4)
parent       ECONOMIC-ROBUSTNESS-PROGRAM-V1 (umbrella Track B) +
             ERP-TRACKB-PROGRAM-V1 (program layer)
asset        BTCUSDT spot (Binance) + BTCUSDT-PERP (USDⓈ-M, Binance fapi)
             — ONE pair, ONE venue; widening = new cohort + owner decision
budget       7 scored cells MAX (M1: 6 arm-classes + 1 diagnostic arm);
             observed/published denominators per umbrella §5.8; sealed
             prospective looks are ledgered, NOT extra cells
ledger       research/control/ERP1-TRACKB-COHORT-1/trial_ledger.jsonl
             (append-only, created at registration; council artifacts of
             THIS session live under the umbrella namespace
             ECONOMIC-ROBUSTNESS-PROGRAM-V1/trackb_cohort1/ per Track-A
             precedent)
S1           SEALED_UNTOUCHED (no S1 surface; S1 request law = umbrella
             §5.10)
orders       NONE — no broker/exchange order surface of any kind; the
             100,000 USDT book is a SIMULATION (program §5), never an
             account; prospective continuation is a separate owner-GO
             shadow surface
shadow       DOES NOT touch PROSPECTIVE-SHADOW-V1 sleeves/workers/ledgers
             (XSECT/BASISLV/ILLIQ/BANDRIDGE), FX-RANGEFADE-2M-SHADOW-V1,
             the A4-draft portfolio surfaces, or any dashboard (owner
             instruction 2026-09-26 nguyên văn)
GO-1 phrase  GO ERP1 TRACKB COHORT 1 REGISTER AND FREEZE
             (typed fresh at the registration gate; authorizes: cycle
             registration via researchctl, freezing this plan's council
             slate + hashes, the §5 data-gate downloads (bounded, heavy
             lock), PIT/cost censuses, the §8 falsification battery, trial
             freeze artifact — and STOPS)
GO-2 phrase  GO ERP1 TRACKB COHORT 1 SCORED
             (typed fresh at the scored gate only after A7 prelaunch PASS;
             authorizes the 7-cell cap only)
GO-3 phrase  GO ERP1 TRACKB COHORT 1 SEALED OOS AND REPLICATION
             (typed fresh only if any identity survives dev gates; ONE
             sealed prospective pass + independent reproduction; one-shot)
forbidden    parameter grids; indicator blending; sign-flip renames;
             maker-fill assumptions in any cost number; fee reductions
             without a dated venue change; timeframe/rescue swaps of dead
             families; reading ancestry PnL into proposer packets; S1;
             orders; shadow/dashboard touch; registry edits outside
             researchctl; push/merge; editing TERMINAL verdicts; levered or
             borrow-based variants (BLOCKED per Track B law (e))
```

## 1. Objective and non-objectives

### 1.1 Objective

Freeze and falsify ONE admitted mechanism class (skeptic F-0 court verdict
2026-09-26: exactly one class admissible — funding-level-gated low-turnover
cash-and-carry with breakeven-horizon entry law), under the measured-cost
100k shared-capital simulation, with: the six economic questions answered
pre-PnL (program §3.3), the falsifier battery to completion before any
PnL-bearing computation, dev evidence labeled `ANCESTRY_EXPOSED_DEV`
(kill + engineer only), and the only promotion-grade evidence being the
sealed post-freeze prospective one-look.

### 1.2 Non-objectives

- No promotion beyond `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION`
  (SINGLE_VENUE, PAPER_TIER). Program §4.3: replication limb (iii)
  (independent surface) is BLOCKED-unauthorized today; the word
  "replicated" is unavailable to this cohort by construction.
- No rescue of CARRY/BASISLV/BAB/OITD/FUNDCROWD/XSECT/FOREX-V4-carry by
  rename, parameter change, timeframe change, maker-fill assumption, or fee
  reduction (owner instruction 2026-09-26, nguyên văn; umbrella §6; Q-3).
- No live-readiness claim (umbrella §1.3). `NO_ELIGIBLE_PROPOSAL` /
  `REJECT_ALL` / `NO_CANDIDATE` are valid, expected outcomes (skeptic
  prior of pre-PnL death: 0.70–0.80).

## 2. Authority, Phase-0, boundaries

- Authority order: owner instruction > this child plan (once registered) >
  program plan > umbrella plan > CLAUDE.md + handbook v2. Stricter wins.
- Phase-0 gate re-measured at this child's own intake before any dispatch
  (umbrella §3). Snapshot at drafting (2026-09-26, root checkout): registry
  reconciled; root `main` @ `e4e3b915…`; heavy lock `FREE_PROVEN` (last
  history row: a FAILED cohort-2 build worker, released); owner untracked
  changes present and PRESERVED (`.zcode/`, `plan_at.md`,
  `plans/DRAFT_amendment_PSCTV1_A4_*`, SHARED-PORTFOLIO-100K-V1/,
  SANDBOX-OVERFIT-3ASSETS/, d2_curiosity_v1_sources/, ERP1 new files —
  never staged by lanes, P0-4); pre-existing doctor HIGHs = accepted-
  historical TERMINAL class (P0-3). Two sibling ACTIVE_LIGHT surfaces exist
  and are NOT touched: CRYPTO-HISTORICAL-REPLICATION-3F-V1 (scored
  execution in flight per its registry phase — re-measure at GO-1; heavy
  lock law applies machine-wide) and ETHUSDT-OPEN-SEARCH-V2 (STOP-1
  awaiting its own owner GO — unrelated surface, no interaction).
- One live Lead session; bounded heavy jobs (data staging/censuses) under
  the machine-wide lock only; council/plan work under umbrella light
  authority (Track-A precedent).
- Implementation lanes only in this cycle's own worktree
  (`.worktrees/erp1-trackb-cohort-1/...`, created at registration).

## 3. Ancestry disclosure and the outcome-exposed window map (binding)

Every artifact of this cycle carries this block. **The entire measurable
BTCUSDT funding/basis history is outcome-exposed ancestry** (measured from
the registry + FAMILY_FAILURES, 2026-09-26):

| Window | Status | Evidence (axis exposed) |
|---|---|---|
| ≤ 2019-09-09 | OUT_OF_REACH | vision funding panel starts 2019-09-10; fapi floor 2020-07-18; basis endpoint empty 2019-11 (CHR3F `p0_feasibility_table.md` §2) |
| 2019-09-10 .. 2020-07-17 | vision-only; below fapi floor | single-source prefix; EXCLUDED from scoring (exclusion-not-merge law, PITDATA §1) |
| 2020-07-18 .. 2024-08-19 | `ANCESTRY_EXPOSED_DEV` | V6 CARRY-1D/3D/7D funding-carry windows (fold 51.66% kill); V12 BAB-LOWBETA; V13 OITD; V14 BASISLV (fold 0.5110); BTC-H4 ×4 price-axis cycles 2020–2026 |
| 2024-08-20 .. 2026-08-21 | `ANCESTRY_EXPOSED_DEV` (densest) | CHR3F staged + scored S0 window (non-overlap law V12 A3); BTC-H4 EDGE/BAND windows to 2026-08-21 |
| 2026-08-22 .. 2026-09-13 | `SEAM_CONSISTENCY_ONLY` | PIT/parity/consistency checks ONLY — no selection, no headline numbers; verify against registry + FAMILY_FAILURES/MAP at GO-1 |
| 2026-09-14 .. freeze date | `ANCESTRY_EXPOSED_SEAM` (A7 F2 relabel) | PSV1 sleeves live from 2026-09-14 book funding-axis decisions whose books read BTCUSDT (XSECT benchmark leg; BASISLV basis panel) — NOT outcome-free; seam-consistency use only, never selection evidence |
| post-freeze | **SEALED prospective accrual** | the ONLY promotion-grade window; one look (GO-3) at preregistered decision-count gates |

Consequences (frozen): (1) dev-window PnL can KILL and engineer, never
promote — every dev row carries `ANCESTRY_EXPOSED_DEV`; (2) the per-window
verification above is re-run against `CYCLE_REGISTRY.json` **+
`research/wayfinder/FAMILY_FAILURES.jsonl` + MAP closed bullets** at GO-1
(A7 M-disposition: the V6/V12/V13/V14 window authorities live there, not
all in registry rows) and hash-pinned in the freeze artifact; (3) no
fold-window substitution after
any PnL is seen; (4) ancestry chain labels pinned: CARRY-1D/3D/7D (V6
SCIENTIFIC_REJECTION), BAB-LOWBETA (V12, COST_DOMINATED), OITD (V13),
BASISLV-PREMFADE-28D (V14; price-only clause marks its edge as funding
credit), FUNDCROWD-MR (SPRINT), XSECT-FUND-CARRY-7D (PSV1 sleeve 3,
RETIRE pending, live cost:carry 77:1), FOREX-V4 carry class (rho
0.997–1.000, cross-asset class precedent).

## 4. Data authority (authority: PITDATA_cohort1_REPORT.md — its §1–§6 are this cycle's data law)

- **Funding PIT contract** (PITDATA §1, binding): a settlement is
  consumable only when `fundingTime ≤ T`; no forward-fill; fapi
  premium-index next-interval rate = `funding_predicted` — structurally
  quarantined from `funding_settled`, never a signal input; fapi serves
  `{symbol, fundingTime, fundingRate}` only (no fundingCount field —
  counts are census-derived); panel-truncation replay must be
  byte-identical (P-18) — this is fixture M-5 of §8.
- **Alignment contract** (PITDATA §2): catalog perp bars are close-stamped
  LAST-price vs open-stamped vision klines — a 15-minute join shift if
  unnormalized; basis = synchronized spot-vs-perp LAST bars; funding
  premium (mark/index) is a SEPARATE channel; basis observable on 1h
  synchronized bars.
- **Coverage/census gates** (PITDATA §3): funding settlement count vs
  3/day UTC with enumerated gaps; spot + perp bar coverage floors;
  DST-free UTC calendar fixtures; duplicates/out-of-order fail-closed;
  `.001`-stamp residue minute-quantization check; single-symbol surface —
  survivorship N/A, P-7 channel canaries apply per CHANNEL (spot klines /
  perp klines / funding / bookTicker each licensed separately).
- **License posture** (PITDATA §4): fapi endpoints + data.binance.vision
  (spot klines, funding zips, bookTicker/aggTrades) each run
  DOCUMENTED_CANDIDATE → AUTHORIZED_INTERNAL_RESEARCH via the gate;
  Binance-public-archive posture per crypto-cycle precedent (P-25 noted).
- **BLOCKED today** (PITDATA §5): liquidation tape; borrow/spot-margin
  terms; queue-position/maker fills; second-venue funding; replay-vs-fill
  slippage. Each with its single unblocking owner action. No BLOCKED
  component may enter any number (declared bands only, stress-covered).
- **GO-1 data-gate checklist** = PITDATA §6 items 1–14, each
  PASS/FAIL/BLOCKED with evidence path; verdict + sha chain recorded
  before any signal computation. Spot BTCUSDT bars are staged nowhere
  today (measured) — staging them is GO-1 work, bounded heavy job.

## 5. Cost authority and the 100,000 USDT shared-capital simulation contract

Authority: COSTEXEC_cohort1_REPORT.md (its §1–§6 are this cycle's cost law).
Evidence classes measured at intake: 5 MEASURED-path, 4 DECLARED-required,
3 BLOCKED.

1. **One book, never doubled**: opening equity 100,000 USDT; sizing law
   frozen at freeze-artifact: spot notional N and perp margin M with
   N + M ≤ 100,000; cost auditor's preregistered proposal (pending venue
   tier validation at GO-1): N = 65,000 / M = 35,000 (perp short notional
   = N, 1:1 delta hedge; leverage on the perp leg ≈ 1.86× against its own
   margin — unlevered at BOOK level, margin-managed at leg level; if venue
   tier validation at GO-1 contradicts the 35% band, the sizing law is
   re-pinned ONCE pre-PnL with a dated freeze note, never after PnL).
2. **Cost book**: taker-only; both legs' fill-hour conditional spread
   distributions (per-(leg, utc_hour, month) histograms, persisted counts,
   LOW_SAMPLE_BUCKET/EXCLUDED_BUCKET flags — COSTEXEC §2); venue fee
   schedules = DECLARED until validated; slippage = replay-vs-fill if
   evidence exists else DECLARED + stress; funding received/paid from the
   SETTLED series (measured); hedge drift booked per bar (measured);
   margin/liquidation = DECLARED model from venue-published tiers; outage
   = DECLARED band (miss N settlements + adverse gap reopen).
3. **Stress law**: ×1.5 and ×2.0 on EVERY component + funding-path stress
   on the measured settlement distribution (COSTEXEC §2: E[3-negative-
   settlement run] ≈ 1.9 per 42-day hold at p=24.7%; worst-path
   5×30 bps ≈ 1.0% of book — PnL drag, not a solvency event at 1:1 with
   the 35% margin band).
4. **F-5 cost-ceiling law (KILL_COST_CEILING)**: the operative
   preregistered ceiling = all-in ×2.0-stressed fill-conditioned round
   trip + declared outage band ≈ **45–60 bps of N**; entry-premium band
   must measurably exceed it on the RECENT window (Q-6: never the
   2020–2026 archive mean of 3.23 bps/day). Anchor arithmetic verified by
   the cost auditor: breakeven 12.4–15.5 days (mean carry, ×2.0), 18–23
   days (downtrend carry, ×1.0), 27–34 (×1.5), 36–45 (×2.0); **erratum
   recorded** — one −0.30%/8h settlement = 30 bps ≈ 1.2–1.5 full RTs (the
   umbrella's "2.5 fee round-trips" used a fee-only unit); the umbrella
   text stands as evidence of the past, this plan's number governs.
   Honest ceiling verdict at intake (COSTEXEC §4): the book clears the
   ceiling ONLY for ≥6–8 week positive-funding-regime holds; in-downtrend
   conditional carry sits AT the ceiling (knife-edge, P-2) — the ceiling
   stays armed.
5. **Comparison set (mandatory, same cost book)**: cash (0%); long BTC
   spot; perp-only unlevered funding structure IF scoreable under law (e)
   (else recorded BLOCKED with reason); plus the arm-level controls of §7.
6. **Accounting labels (every row)**: `SINGLE_VENUE_PANEL`, `PAPER_TIER`,
   `FUNDING_PATH_STRESSED`, `LIQUIDATION_MODEL_DECLARED`,
   `FILL_QUALITY_CLASS_<measured|declared>`; gross / declared-cost net /
   measured-cost net / funding-received / funding-paid / fees / slippage /
   drift reported as separate named fields, never merged (Q-14).

## 6. Mechanism freeze (council slate — FROZEN from the 2026-09-26 outcome-blind council)

Council artifacts (authorities): `research/control/ECONOMIC-ROBUSTNESS-
PROGRAM-V1/trackb_cohort1/{PROPOSER,PITDATA,SKEPTIC,COSTEXEC}_cohort1_
REPORT.md` + four `HANDOFF_trackb1_*.json` (`zcode_orch_v3_handoff@1`).
All lanes measured base `main` @ `e4e3b915…`. Slate hash-pinned at GO-1.

**Cross-lane adjudication by Lead (tracka-1 §11 law: tổng hợp bất đồng,
không bỏ phiếu ghi đè):** the proposer offered 2 mechanisms + 1 empty
slot; the skeptic's F-0 court admits exactly ONE class (A:
funding-level-gated low-turnover cash-and-carry, breakeven-horizon entry
law) and rules the honest variants of A are holding-period neighbours —
"a cohort freezing 3 mechanisms here would be freezing 3
parameterizations of one mechanism." This plan therefore freezes **ONE
mechanism (M1)** with the proposer's second candidate (DTX exit-gate)
demoted to a pre-registered DIAGNOSTIC arm inside M1 (never
anchor-selectable), preserving both lanes' findings verbatim:

### M1 — TB1-DN-CARRY-CTG (cost-gated fixed-horizon cash-and-carry)

- **Mechanism** (proposer §C1, admitted class A): enter only when expected
  carry over the intended hold ≥ the ×2.0 all-in RT bill (45 bps anchor;
  45–60 bps band per §5.4), computed from the recent-window settled-funding
  distribution; hold a fixed horizon; weekly decision clock (Friday 00:00
  UTC bar close); no funding-window prediction, no basis-level signal —
  the gate is a feasibility inequality, not a forecast.
- **Payer**: leveraged USDⓈ-M perpetual longs (leverage demand, not
  delta); they cannot arbitrage the funding away without surrendering the
  leverage or holding spot inventory they do not want.
- **Risk transferred** (skeptic §3 verbatim list): venue counterparty
  (both legs, one venue); short-leg margin path on pumps; funding sign
  flips inside the hold; entry-basis blowout at signal peaks; forced
  unwind; hedge drift; outage (declared). Price-only clause (law c):
  the premium is funding credit — carry harvest, not information alpha;
  every verdict says so.
- **Arms (frozen)**:
  - **ANCHOR**: 35-day hold (105 settlements), ×2.0 gate.
  - **N1 / N2 (≤2 neighbours, holding-period support only)**: 28d / 42d,
    same gate.
  - **CAUSAL control**: entry-timing permutation (same holding
    distribution, entry ticks shuffled within matched funding-state
    marginals — removes gate-timing information, keeps exposure shape;
    must MOVE the result, Q-11; non-vacuity predicates frozen at GO-1:
    ≥90% round trips differ from anchor, both states present, occupancy
    band 10–40%).
  - **INVERTED control**: hold the same book exactly during gate-EXCLUDED
    states (expected carry < bill — the class-F book as control, skeptic
    §4/F); must not out-earn the anchor.
  - **BASELINE set** (one composite arm): cash 0% + long BTC spot +
    perp-only-if-scoreable.
  - **DIAGNOSTIC arm DTX (pre-registered, NEVER anchor-selectable)**:
    negative-run exit gate (exit iff 21-settlement-day realized run-rate
    implies E[remaining funding] < −exit RT); its own causal null =
    funding SIGN-SCRAMBLE (signs permuted within level-matched marginals);
    DTX dies if the sign-scramble reproduces its improvement or if
    fixed-hold beats it net of exit costs. **Tension on record (skeptic
    F-0 information test: sign/run transforms of funding risk the class-C
    collision, V17 FUNDJUMP rho 0.2439 precedent)**: the skeptic's GO-1
    F-0 ruling on the DTX arm is a NAMED PRECONDITION — if ruled a re-gated
    dead observable, the DTX arm empties pre-PnL (SLOT-style) without
    touching M1.
- **Slot 3: EMPTY (SLOT_LEFT_EMPTY)** — basis-prepaid entry rejected
  pre-proposal by both lanes (BASISLV re-tune; premium-fade class veto
  −0.418/−0.515).

### F-0 court standing rulings (skeptic §4, binding on this cohort)

ADMIT: class A only (with the five binding conditions of skeptic §4/A).
VETO regardless of rho: basis-level entry (B); funding-momentum/
sign-persistence as an ENTRY class (C); vol-of-funding gate (D);
calendar/session conditioning (E); cross-sectional/percentile (G);
OI/term-structure (H); post-cascade entry (I). STRUCTURAL: negative-funding
inverse = the inverted control, not a mechanism (F).

## 7. Trial freeze contract (umbrella §5.7, concretized)

Frozen fields at GO-1 freeze artifact (sha-pinned, P-19 hygiene): hypothesis
ID + arm IDs + `arm_config_digest` per arm; universe (BTCUSDT spot+perp,
one venue); decision clock (weekly Friday 00:00 UTC); warmup (28d settled
funding + bar alignment warmup); entry/exit/fill laws (same-bar fills both
legs at opposite quotes, one crossing per side per leg, COSTEXEC §5);
hedge-drift rebalance band (COSTEXEC's concrete threshold candidates frozen
at GO-1); the §5 sizing law (N/M); fold contract (§9.1); cost tiers ×1.0/
×1.5/×2.0 + funding-path stress; seeds (permutation + bootstrap + scramble,
numeric, stored in the freeze JSON); D-gates for the sealed pass; exact-arm
dry-run non-vacuous + leak-scanned before any scored cell.

## 8. Pre-PnL falsification battery (gate BEFORE any scored cell; order is law)

- **F-0 mechanism-class court** (done at council for the class space;
  re-runs at GO-1 as the named DTX precondition + any late amendment).
- **F-1 ancestry rho (one-shot, skeptic lane)**: pooled Spearman |rho| on
  the exact decision-state representation (skeptic §2: state series on the
  8h settled grid + synchronized 1h basis grid where read; values enter
  only at available time; truncation proofs BEFORE rho) vs CARRY-1D/3D/7D
  funding-level state, CARRY-BAB proxy, XSECT single-symbol projection,
  FUNDCROWD percentile state, BASISLV basis-level state. Bar ≤ 0.20
  immovable; computed ONCE; class vetoes apply regardless of rho.
  Skeptic calibration on record: class A's state is monotone in funding
  level — expect a breach (V16 cleared by 0.0073; V17 measured 0.2439);
  if it breaches, the cohort closes with 0 scored cells and that is a
  first-class outcome.
- **F-2 PIT battery (M-class, P-18)**: M-1 shift/independent-impl
  equivalence of the gate computation; M-2 non-vacuity of every state
  variable (≥2% of decision epochs must move under a one-index shift);
  M-3 panel-truncation replay byte-identical (settled-funding only; the
  predicted-rate quarantine is a build-failing fixture); M-4 seam
  disclosure (close-stamped vs open-stamped bars; funding-premium channel
  vs basis channel); M-5 no same-bar statistic at decision time.
- **F-3 clock-placebo**: time-only entries at the anchor's occupancy and
  fill-hour marginals, direction/exposure shape identical; must not
  reach ≥0.5× anchor net (KILL_CONTROL_REPRODUCED).
- **F-4 baseline/beta**: anchor vs long-BTC baseline and vs cash on
  identical windows/folds, per-fold tables; a carry book that underperforms
  cash after measured costs at ×1.0 is dead on arrival (G1).
- **F-5 cost-survivability ceiling** (§5.4): DECLARED-band arithmetic
  replaced by the MEASURED fill-hour conditional book at GO-1 (P-27 law);
  negative recent-window ceiling = KILL_COST_CEILING pre-PnL; compression
  scenario (post-entry funding halves → breakeven doubles to 12–46d) is a
  mandatory reported stress, not optional.
- **F-6 feasibility nearest-window** (Q-6): recent 6 months — gate-fire
  counts, fill-hour census populations, hold populations vs power floors;
  NOT the archive mean (3.23 bps/day is inadmissible for gating).
- **F-7 concentration pre-check** (Q-12): exclusion zones at fold, hold,
  and settlement-period level; declared concentration statistic frozen
  pre-outcome (carry concentrates in mania folds — V6/V14 precedent).

Ordering law: data gate (§4) + falsification to completion BEFORE any
PnL-bearing computation anywhere in the cycle. A mechanism/arm failing F-1..
F-7 is `NOT_SCORED_FALSIFIED`; no replacement enters mid-cohort.

## 9. Folds, gates, kill laws, sealed pass

### 9.1 Dev window + folds

Dev = the `ANCESTRY_EXPOSED_DEV` window 2020-07-18..2026-08-21 (labels per
§3); chronological non-overlapping folds F1..F6 by the ancestry convention;
force-flat at fold boundaries; `SEAM_CONSISTENCY_ONLY` window 2026-08-22..
freeze used for parity/consistency fixtures only.

### 9.2 Dev gates (per arm; margins-to-fail mandatory, P-2)

- G1 net > 0 @ measured cost ×1.0 (net = funding received − funding paid −
  fees − spreads − slippage − drift, per the §5 named fields);
- G2 PF ≥ 1.20 on the per-hold distribution;
- G3 ≥ 4/6 folds net > 0;
- G4 net > 0 @ ×1.5 (funding-path stress included);
- G5 population floors: ≥52 valid weekly decision epochs AND ≥40 closed
  holds AND a preregistered bootstrap CI on per-hold net excluding 0 at the
  frozen seed (power note: ~64 non-overlapping holds exist archive-wide —
  thin by construction; sub-power positives are `INCONCLUSIVE`, never
  PASS; this floor SET is the child's power analysis and is ≥ the umbrella
  weekly floor in decision-epoch terms — any lowering requires an umbrella
  amendment, not this plan);
- G6 top-fold share ≤ 50% of positive net;
- G7 top-5-holds share ≤ 50% of positive net;
- G8 top single funding-episode (contiguous same-sign settlement run)
  share ≤ 50% of positive net.

### 9.3 PROMOTE / KILL / TIME-STOP (preregistered)

- **PROMOTE (= paper-tier candidate eligibility, nothing more)**: all G1–G8
  PASS at dev, AND the causal control fails to reproduce, AND inverted
  strictly below, AND baselines beaten net at ×1.0 and ×1.5, AND DSR
  reported across the cohort + program trial history, AND reproduction
  exact — then and only then the identity MAY request the GO-3 sealed
  prospective pass. Dev PASS alone never promotes (ANCESTRY_EXPOSED_DEV
  law); the sealed pass is where promotion-grade evidence lives.
- **KILL (terminal for the identity)**: any G-gate FAIL at dev;
  KILL_COST_CEILING (F-5); KILL_INVERSION; KILL_CONTROL_REPRODUCED (F-3
  or DTX's sign-scramble for the DTX arm); KILL_BETA_EXPLAINED (long-BTC
  or cash baseline explains ≥ half the net); KILL_PIT_SEAM (any M-fixture
  failure); concentration breach; ancestry rho breach at F-1 (kills the
  class pre-PnL). No rescue by rename/param/timeframe/maker-assumption/
  fee-reduction (owner list, nguyên văn); a killed arm never re-enters.
- **TIME-STOP**: if by freeze+60 days the data gate or falsifiers are
  incomplete, the cohort closes `BLOCKED_*` honestly; if the whole cohort
  cannot reach G5 populations, closes `REJECT_ALL`/`NO_ELIGIBLE_PROPOSAL`.
- **Sealed prospective pass (GO-3, one-shot)**: post-freeze accrual on the
  frozen identity; D-gates D13/D26/D52 mapped to weekly decision epochs
  (umbrella §5.12); membership artifact sha256'd before the pass; dead
  arms take NO look; failure is final. **Membership PINNED at freeze
  (A7 F7 disposition, binding): the one sealed pass covers the M1 ANCHOR
  only, plus — computed in the same single pass as companions, never as
  independent consumers — its preregistered causal control, inverted
  control and baseline books (tracka-1 §9.1 one-look law). N1/N2 take NO
  look regardless of dev survival; the DTX diagnostic arm NEVER looks,
  regardless of outcome.** Independent reproduction (detached twin + A7
  recompute from raw settlement bytes, engine rewritten not imported)
  precedes any GO-3 request.

## 10. Trial budget, ledger, denominators

- Cap: **7 scored cells** = M1's 6 arm-classes (anchor, N1, N2, causal,
  inverted, baseline-composite) + 1 diagnostic arm (DTX). Re-runs after
  TECHABORT consume budget (observed counter always). Sealed looks
  ledgered separately.
- Ledger row per cell/look (append-only; a bad row is corrected by a later
  row referencing it): `cycle_id, mechanism_id, arm_id, arm_config_digest,
  window_tag/fold, cost_tier, funding_received, funding_paid, fees,
  spreads, slippage, drift, net_pnl_measured, net_pnl_declared,
  gates_with_margins_to_fail, verdict, exclusion_zones, labels[],
  sha_chain{code_freeze, data_manifest, selection_digest}`. Labels per
  §5.6. Observed/published split per umbrella §5.8; DSR across ALL cohort
  trials (per-period series persisted — P-11); PBO = NOT_RUN (<8 configs,
  fail-closed).

## 11. A7 arc, reproduction, decisions, close

- A7 fresh-context plan-audit of THIS draft (run under umbrella light
  authority before the owner packet — report at
  `ECONOMIC-ROBUSTNESS-PROGRAM-V1/trackb_cohort1/A7_trackb1_plan_audit_
REPORT.md`); findings dispositioned into this text before GO-1.
- A7 prelaunch before GO-2 (hashes chain, exact-arm identity, PIT/cost
  audits, dry-run hygiene, S1 sealed, denominator seed, zero unresolved
  HIGH/CRITICAL); independent reproducer lane (engine rewritten from the
  frozen spec, never importing the implementer's engine — program §6);
  A7 terminal at close; two-half close per handbook §32 (registry, P-9
  ledger, FAMILY_FAILURES/MAP/LESSONS, errata bundle P-19).
- Terminal vocabulary: umbrella §9 + program §9. `NO_ELIGIBLE_PROPOSAL` /
  `REJECT_ALL` / `NO_CANDIDATE` are first-class closes.
- **Owner decisions carried in the packet (this plan STOPS at GO-1)**:
  (D-B1) approve the charter + this child plan and type GO-1; (D-B2) the
  7-cell budget; (D-B3) acknowledge the structural limits — single venue,
  ANCESTRY_EXPOSED_DEV dev evidence, sealed promotion path = prospective
  accrual (weeks-to-months wall clock after GO-2 survival), replication
  limb (iii) BLOCKED; (D-B4) any data-source unblock (second venue /
  bookTicker depth history) is explicitly NOT granted by this plan.

## Appendix A — Council slate summary (hash-pinned at GO-1)

- Proposer (blind): 2 candidates + SLOT_LEFT_EMPTY (basis-prepaid rejected
  as BASISLV re-tune); honest count 2, nested-book framing for DTX.
- Skeptic (VETO): 1 class ADMIT conditional (A) with 5 binding conditions;
  7 classes VETOED/STRUCTURAL; modal pre-PnL killer = F-1 rho; prior of
  pre-PnL death 0.70–0.80.
- PIT/data auditor: gate FEASIBLE as specified; 14-item GO-1 checklist;
  settlement-timing + alignment + coverage are the three top risks; spot
  staging absent (bounded work, not research risk); 5 BLOCKED components.
- Cost/execution auditor (BLOCKED): 5 measured-path / 4 declared / 3
  blocked; operative ceiling 45–60 bps all-in at ×2.0; ceiling clears only
  for ≥6–8 week positive-regime holds; downtrend carry AT the ceiling
  (knife-edge); erratum on the 2.5-RT anchor recorded (§5.4).
- Honest cohort summary for the owner: ONE mechanism, 7 cells, three GO
  gates, and the stated expectation of the council that F-1 ancestry rho
  and F-5 cost arithmetic are the modal killers — a 0-scored-cell close is
  a fully valid outcome.
