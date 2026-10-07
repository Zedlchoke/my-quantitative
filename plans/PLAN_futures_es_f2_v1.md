# PLAN — FUTURES-ES-F2-V1 (ES-F2 CPI/NFP macro-morning, F2-B family-pooled)

> Registration copy. Content identical to the round-draft at
> `research/control/FUTURES-NQFX-PACKET-PREP-20261007/registration/plan/PLAN_futures_es_f2_v1.md`
> on branch `prep/futures-nqfx-packet-prep-20261007` @ 0f9002d7 (round
> FUTURES-NQFX-PACKET-PREP-20261007). Authority chain: owner decision
> OWNER_DECISION_RECORDED.json (sentence sha256 01cca9eb…, JSON v2 @ b0b68f3a);
> verifier verdicts READY_TO_SIGN (wave 4), ACCEPT (VERIFY-A5PORT); PC-2
> closed 17/17 vintage-2026 pins; RB-1/RB-2 closed via the committed A5 port.
> Two-key GO phrase registered NOT consumed:
> `GO FUTURES-ES-F2-V1 SCORED EXECUTION`.

# PLAN_futures_es_f2_v1 — registration plan for cycle FUTURES-ES-F2-V1

- **Cycle:** `FUTURES-ES-F2-V1` — ES-F2 MACRO-0730 (CPI+NFP), option **F2-B**,
  vintage rule **348 strict decision-time-known (DTK)**, cost contract
  **Variant A**, D-1 resolved as **Reading A (narrow)** — all four frozen by the
  recorded owner decision
  (`research/control/FUTURES-NQFX-PACKET-PREP-20261007/auth/OWNER_DECISION_RECORDED.json`,
  `approved_sentence_sha256 = 01cca9eb36fbb3a3298e1e61b3afe86113023ce24b5efc744e31d36ff6ea7040`,
  recorded at commit `b0b68f3a81dd55ba73fc23cee485d14edea9b9e4`).
- **Status of this document:** COMPLETE registration plan (no TBD). Drafted in
  wave 5 of round FUTURES-NQFX-PACKET-PREP-20261007 by lane P1
  (`registration/plan/`); the controller commits it to
  `plans/PLAN_futures_es_f2_v1.md` at registration. Registration itself, the
  D2 run, and any GO remain separate authority acts.
- **Provenance header (parent evidence chain):**

| link | identity |
|---|---|
| Family spec (pre-PB1, no post-hoc mining) | `FUTURES-OVERNIGHT-PREP-20261003/hypo/es_nq/ESNQ_HYPOTHESES.md` §ES-F2 (committed 2026-10-03T22:40Z, before PB1 scored 2026-10-06) |
| ES-successor owner packet | `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-successor/prep` @ `fbc96b228b3ed34a2284a5308e0f4435a6d64465` — `research/control/successor_design_2026-10-02/es_f2_prep/` (ES_F2_CYCLE_PACKET.md sha256 `d47d115e5a45c786cb6f75aaf2660f6c215d5244da9e97ee434395c39cbce9e8`; IDENTITY_OPTIONS_F2.json; VINTAGE_2025_DISPOSITION.md sha256 `67e37005650992b948d73dd8cffbbc1f51ccd5eb1ff0b6c21a76a1770d6230bf`; D2_INTEGRATION.md sha256 `606efabdcba584527cb5f3c79ec67fa586e7f62eecfce014ebf5c24cda4045e4`) + `FUTURES-ES-SUCCESSOR-PREP-20261006/` (ANCESTRY_RULING.md sha256 `d6218b5ff3a611fedbd9f79db595703931a53a3b030f3e27d382558fdff503ca`, POWER_COST_DESIGN.md sha256 `694dea1033c21c237cc866463a3e45a1efad84a70213614f77df8fd150ad5b8c`, F2_DATA_VERIFICATION.md sha256 `d2c8060ceb043928be77c8bcf740523203f36528aead205d1f8aec1d781793f5`) |
| PB1 terminal (frozen) | `FUTURES-ES-PB1-V1` TERMINAL `FUTURES_ES_V1_REJECT_ALL` 24/24, registry worktree `futures-es-reg/prep` @ `935556cf5ec4914bc704b170ce4bab5045ca6027` (pass_a committed clean; byte-identical reproduction twin recorded at commit 8283f135) |
| Dead-sibling terminals | FUTURES-NQ-V1 + FUTURES-FX-V1 TERMINAL at root `a72b995715914915f88ada8e65bbae8cf33b09a5` (NQ ledger 33 rows sha256 `f90a60ab8fc874af9bacc99530e19da3eb16ad0e31e43f7e4e68e335aca42056`; FX ledger 85 rows sha256 `72e0a3ab9df6c72d08f350dbff78f74aefc27b2a8db2ea678547b0ee9d264ce7` — both re-hashed and matched this round) |
| Packet-prep round | round `FUTURES-NQFX-PACKET-PREP-20261007`, worktree `futures-nqfx-packet-prep/prep` branch `prep/futures-nqfx-packet-prep-20261007`; **actual_start_sha of this lane = `bce2468c5f1f79860290faade4186870e2b43bae`** (measured at lane start) |
| Owner decision | `OWNER_DECISION_RECORDED.json` @ b0b68f3a (verifier wave-4 verdict READY_TO_SIGN 10/10 MATCHES_CODE; byte round-trip identical) |
| D-1 resolution artifacts | `d1_resolution/addendum/D1_READING_A_ADDENDUM_V2.md` (predicate table P1–P9), `d1_resolution/comparator_census/` (COMPARATOR_CENSUS.md, comparator_census.json, R5_VERBATIM.md), `d1_resolution/prereg_conditions/PREREG_CONDITIONS.md`, `d1_resolution/d2_synthetic_test/d2_reference.py` (`d2-reference@1`), `lane_d_es/ES_F2_RECHECK.md` (ADDENDUM-D drafted, (d.3) finding) |
| M-2 control-semantics fix | `FUTURES-NQFX-SEARCH-PREP-20261006/w4_m2_fix/` (REPRO_M2.md + `adapter_fixed/`, prior round a630b326..cefa52fe; sandbox-only, no production rewrite) |

Evidence-label discipline: every load-bearing claim below is OBSERVED
(committed artifact, cited), INFERRED (derivation shown), or PROPOSED (design,
no data). Zero candidate PnL, expectancy, PF, conditional return, or measured
rho exists anywhere in PREP (prep zero-PnL law); D2 measurements run only
INSIDE the registered cycle.

---

## 1. Cycle identity, lineage and estimand

- **cycle_id:** `FUTURES-ES-F2-V1`.
- **Family:** ES-F2 `MACRO-0730` — scheduled US 08:30 ET data releases, CPI +
  NFP legs. Mechanisms (pre-registered, pre-PB1): `M-MS-CONT` (07:30-window
  move persists into RTH) and `M-MS-REV` (thin-book over-extension faded by
  RTH liquidity). Construction: arm conditions on the sign of the reaction
  window r = log(px 08:29 / px 07:29) CT on scheduled-release days; tails
  UP/DN; delays D0 = first 1m bar ≥ 08:30 CT, D30 = ≥ 09:00 CT; tier S2 core;
  fill = next-bar open, TP 2.0×SL, SL 1.0×ATR(20d RTH), SL-priority,
  era-correct measured close-time exit, warmup 252 sessions.
- **Registered estimand (from the packet's F2-B definition, quoted verbatim):**
  > "**F2-B** CPI+NFP family-pooled — **recommended** | 16 primaries (CPI 8 +
  > NFP core 8, same construction) + 3 shared controls = **19** | 19 | **38** |
  > The only estimand the committed power law clears with headroom: the
  > FAMILY-POOLED CPI+NFP question — the round-2/3 headline cell. NFP adds a
  > different macro object (payrolls vs price surprises) on disjoint days
  > (168+178=346, no double count) for +8 identities, controls shared."
  > (ES_F2_CYCLE_PACKET.md §2 table, row F2-B)
  and (IDENTITY_OPTIONS_F2.json options[1].power_honesty):
  > "family-pooled only; series split (CPI-only t=3.24 / NFP-only t=3.34) and
  > every era/fold cell are descriptive 0-cost views, never scored estimands;
  > pooled is the round-2/3 headline cell".
- **First-response scope:** the scored arms are the first-response delays D0
  and D30 only (first 1m bar at/after 08:30 CT / 09:00 CT). No other delay
  class enters the scored table.
- **Day sets (vintage 348):** MAIN n = 348 = CPI 169 + EMPSIT 179; folds
  F1–F4 and eras E1/E2/E3 are evaluation views only (§9); NC-2b canceled-day
  falsifier subset n=2 (CPI 2025-11-13, EMPSIT 2025-11-07) never scored as
  MAIN. The n-invariant §1.1 provenance repairs (CPI 2016-11-15→11-17 swap;
  CPI-2013 actual-vintage rows; EMPSIT 2013) ride the same written vintage
  rule at the freeze (PC-3).
- **Convention:** CONV-B (ESNQ census minimal: minimal-core primaries + 3
  scored controls). Conventions are never mixed; the census "full-grid 48"
  number is primaries-only and is never presented as an option total.

## 2. Identity table — the 19 scored identities of F2-B

Extracted verbatim from `IDENTITY_OPTIONS_F2.json` options[1]
(`scored_identities.primaries` / `.controls`), ES-successor packet @ fbc96b22.
Validator re-run at packet time: **exit 0** — "PASS — IDENTITY_OPTIONS_F2.json:
3 options (F2-A 11/22, F2-B 19/38, F2-C 27/54), counts 346=168+178,
RT 42/67/92, pooled t=4.65, exactly one recommended, d2_rows==scored_total,
non-options recorded" (ES_F2_RECHECK.md (b), re-verified this round).
**Verified: 19 scored + 19 D2 rows, zero F1/F3/F4 leakage** — every one of the
19 IDs is an FBES2* (CPI) or FBES2N* (NFP) construction or one of the three
shared controls; no FOMC-RES (F1), COT-CROWD (F3) or RUN-REV (F4) identity
appears (leakage arithmetic: 16 primaries = 8 CPI + 8 NFP; +3 controls = 19;
no other family contributes any row).

| # | id | family | arm | delay | direction | event set | role |
|---|---|---|---|---|---|---|---|
| 1 | FBES2-MS-CONT-UP-D0-S2 | ES-F2 CPI | M-MS-CONT | D0 | UP | CPI 168→169 | core |
| 2 | FBES2-MS-CONT-UP-D30-S2 | ES-F2 CPI | M-MS-CONT | D30 | UP | CPI | core |
| 3 | FBES2-MS-CONT-DN-D0-S2 | ES-F2 CPI | M-MS-CONT | D0 | DN | CPI | core |
| 4 | FBES2-MS-CONT-DN-D30-S2 | ES-F2 CPI | M-MS-CONT | D30 | DN | CPI | core |
| 5 | FBES2-MS-REV-UP-D0-S2 | ES-F2 CPI | M-MS-REV | D0 | UP | CPI | core |
| 6 | FBES2-MS-REV-UP-D30-S2 | ES-F2 CPI | M-MS-REV | D30 | UP | CPI | core |
| 7 | FBES2-MS-REV-DN-D0-S2 | ES-F2 CPI | M-MS-REV | D0 | DN | CPI | core |
| 8 | FBES2-MS-REV-DN-D30-S2 | ES-F2 CPI | M-MS-REV | D30 | DN | CPI | core |
| 9 | FBES2N-MS-CONT-UP-D0-S2 | ES-F2 NFP | M-MS-CONT | D0 | UP | EMPSIT 178→179 | core |
| 10 | FBES2N-MS-CONT-UP-D30-S2 | ES-F2 NFP | M-MS-CONT | D30 | UP | EMPSIT | core |
| 11 | FBES2N-MS-CONT-DN-D0-S2 | ES-F2 NFP | M-MS-CONT | D0 | DN | EMPSIT | core |
| 12 | FBES2N-MS-CONT-DN-D30-S2 | ES-F2 NFP | M-MS-CONT | D30 | DN | EMPSIT | core |
| 13 | FBES2N-MS-REV-UP-D0-S2 | ES-F2 NFP | M-MS-REV | D0 | UP | EMPSIT | core |
| 14 | FBES2N-MS-REV-UP-D30-S2 | ES-F2 NFP | M-MS-REV | D30 | UP | EMPSIT | core |
| 15 | FBES2N-MS-REV-DN-D0-S2 | ES-F2 NFP | M-MS-REV | D0 | DN | EMPSIT | core |
| 16 | FBES2N-MS-REV-DN-D30-S2 | ES-F2 NFP | M-MS-REV | D30 | DN | EMPSIT | core |
| 17 | FBES2-C1-PLA-0730-S2 | ES-F2 shared | C1 clock placebo | D0 (single-delay) | seeded random-sign | weekday-matched non-release 07:30 clock | control |
| 18 | FBES2-C2-ALW-S2 | ES-F2 shared | C2 always-in | — | long always-in RTH | event-day baseline (both series) | control |
| 19 | FBES2-NC2-NR-0730-S2 | ES-F2 shared | NC-2 negative control | D0 | sign-per-matched-day | weekday-matched non-release same-clock | control |

**Controls law — M-2-fixed semantics (binding design requirement):** the
M-2 defect (FXEB adapter made C1-SHADOW, C2-ALW and C3-ANCHOR execute the
identical always-on fill) was reproduced and fixed in sandbox
(`FUTURES-NQFX-SEARCH-PREP-20261006/w4_m2_fix/REPRO_M2.md` + `adapter_fixed/`,
prior round a630b326..cefa52fe). Any control-semantics code in this cycle:

- **C1 (`FBES2-C1-PLA-0730-S2`)** — clock-only shadow, **SEEDED random-sign**:
  per the PB1 C1 law (`SPEC_PB1_ES` §6; reference implementation
  `fx_common.py` L982-992: `C1_SEED = 20261002`;
  `shadow_direction(session_date) = 1 if (seed + d.toordinal()) % 2 == 0
  else -1`), **distinct from C2** and **deterministic given the registered
  seed**. Single-seed/single-delay; the concrete seed for THIS cycle is fixed
  and disclosed in writing at the freeze (seed-20261002 is precedent, not a
  default; ≥100-seed expansion is a separate owner ruling, never folded into
  this table).
- **C2 (`FBES2-C2-ALW-S2`)** — always-on (always-in-RTH event-day baseline);
  the beat-law target of G7.
- **C3 FLAT (zero-trade)** — the flat anchor is a **0-cost evaluation view**
  in F2-B (not one of the 19 scored): it must carry the M-2-fixed FLAT
  semantics — zero trades over the whole history, zero-trade by construction
  — whenever materialized (as in PB1 `FBES1-FLAT`, n_trades=0, trades=[]).
  C4 dose-response likewise 0-cost view.
- **NC-2** — weekday-matched non-release negative control; must show nothing
  beyond C2 ⇒ F2-K5.
- ID strings are draft labels; the binding object is each identity's
  DEFINITION in the cited spec (IDENTITY_OPTIONS_F2.json lineage note);
  renames at freeze do not change arithmetic.

## 3. Budget and trial accounting

- **Maximum observed rows: 38 = 19 D2 + 19 scored.** D2 ancestry rows count
  into the denominator (owner-fixed fail-closed accounting, D2_INTEGRATION §4;
  ANCESTRY_RULING R2-6). Branches: (i) D2 kills ⇒ the cycle records exactly
  the 19 D2 rows and 0 scored rows; (ii) D2 passes ⇒ 19 + 19 = 38.
- **Every scientifically computed cell counts even if publication fails** —
  per CLAUDE.md trial-accounting law, DSR is computed at the cycle terminal
  over the CUMULATIVE program trial count, including this cycle's observed
  rows regardless of verdict, publication status, or gating outcome. ES scored
  trials to date = 24 (PB1 terminal; corrected per VERIFIER_REPORT_R2 R2F-3).
- No rescue: a NOT-PASSING D2 or any K-gate kill publishes its verdict and
  stops; no parameter re-run may re-enter the same cycle (K2 no-re-param law;
  owner delegation: "no parameter rescue; NOT-PASSING publishes verdict and
  stops").
- A candidate-PnL computation outside a registered cycle is a trial by the
  fail-closed default (EURUSD-OPEN-SEARCH precedent); inside this cycle the
  accounting statement above is fixed in advance by the owner decision.

## 4. D2 ancestry protocol (frozen; Reading A approved)

**Ordering (P-12).** D2's first act, BEFORE any rho: commit (a) the enumerated
comparator list with per-member status, (b) the live-side representation code,
and (c) the materialized proxy artifacts per §5. `validate_exclusion_list`
executes BEFORE any `evaluate_member`; any tamper (trading book, missing
artifact, unknown name, duplicate) raises `ExclusionListTamperError` and fails
the run closed (`d2-reference@1`, run_d2 L432–459).

**Candidate side.** For EACH of the 19 identities: the daily PnL series in
USD, computed by the frozen family spec's own entry/exit law on the pinned
panel. Construction = **per-event-date PnL aggregation with session-date
calendar alignment**: each identity trades at most once per armed event day
(D0 or D30 entry, TP/SL/time exit), and the daily series maps each trade's
realized PnL to its session date (PB1 D2 precedent: pass_a one-trade-per-
session-session_date aggregation; §R5-2 "series = daily PnL (not per-trade),
sign as booked; alignment date = session_date"). GROSS and NET (S1/S2) views
are computed for every identity; **S2-net is the binding cell; gross/S1 are
robustness views of the same identity, not new rows** (d2_accounting,
IDENTITY_OPTIONS_F2.json).

**Dead side — 57 comparator books (census-verified, `comparator_census.json`):
**
- 24 PB1 pass_a books (§6 series derivation), incl. the two excluded FLAT
  books below;
- 11 NQ-F2 MACRO-0730 books (DEAD_K2 terminal, ledger rows seq 12–22);
- 11 FXF3-6E-F3 books + 11 FXF3-6B-F3 books (DEAD_K2 terminal, FX ledger rows
  seq 12–22 and 38–48) — the ADDENDUM-D dead-sibling extension, whose
  57-book denominator and extraction law the owner decision embeds ("the
  remaining 55 comparator books … participate under §R5-4 unchanged …
  denominators are 57 comparator books and 38 D2 rows, unchanged").

**Dead side — 18 court-cluster proxies:** enumerated per §5 (full per-row
specification in `PROXY_SPEC_18.json`, this plan's companion machine record).
Enumeration-as-books + materialization freeze as D2's first act (P-12;
D2_INTEGRATION §2-2: "PREP does not invent the proxy enumeration — it
inherits §R5's reference and freezes the enumeration as D2's first act").

**PRE-LOCKED EXCLUSION LIST (Reading A, owner-approved):** exactly
`{FBES1-FLAT, FUTURES-NQ-V1-F2-FLAT}`, validated BEFORE any rho. Eligibility
evidence (census, primary bytes): FBES1-FLAT — pass_a file sha256
`343de07fd1c329b2f7a3360e95de3ff99751967cfaece405b1ed8868f0af10f2`,
`"identity_id":"FBES1-FLAT"`, `"arm_class":"C3"`,
`"totals":{"n_trades":0,...}`, `"trades":[]`; FUTURES-NQ-V1-F2-FLAT — NQ-V1
ledger row, journal empty, n_trades=0. Both are excluded ONLY under the
d2-reference@1 predicates, quoted verbatim from the approved sentence and
OWNER_DECISION_D1_V2.json code_exact_predicates:

> "the pre-locked exclusion list is exactly {FBES1-FLAT,
> FUTURES-NQ-V1-F2-FLAT}, each eligible only because its terminal artifact
> shows n_trades=0 over its whole history AND its daily chain is identically
> 0.0 (exact equality, no epsilon); exclusion is validated BEFORE any rho and
> any tamper fails the run closed"

Predicate table (code-exact, D1_READING_A_ADDENDUM_V2 §1):

| # | predicate | exact semantics |
|---|---|---|
| P1 | Exclusion eligibility (`DailySeries.is_zero_chain`, L163–173) | every daily value `== 0.0` exactly, whole series; **no epsilon** |
| P2 | Exclusion evidence (R1 census, primary bytes) | `n_trades == 0` over the book's whole history in its terminal artifact |
| P3 | Zero variance on aligned sample (`evaluate_member` L379–382) | `max(x) == min(x)` **exactly**, BOTH candidate and comparator sides; each side its own reason |
| P4 | Small-n / overlap (L384–390) | aligned `n < 30` or `(n / candidate_days) < 0.20` ⇒ NOT_EVALUABLE |
| P5 | Kill rule (`kill_decision` L255–262) | worst member dead iff `\|rho\| > 0.20` **STRICT**; `\|rho\| == 0.2000` exactly survives |
| P6 | Missing artifact (L363–368) | `Comparator.series is None` ⇒ member **BLOCKED_DATA**; family BLOCKED_DATA (precedence 1) — never a silent exclusion |
| P7 | Family precedence (L461–473) | **BLOCKED_DATA > NOT_PASSING_DEAD_WORST_MEMBER > NOT_PASSING_NOT_EVALUABLE > PASS** |
| P8 | Exclusion timing (`run_d2` L432–459) | `validate_exclusion_list` BEFORE any `evaluate_member`; tamper fails closed |
| P9 | Not-evaluable = NOT-PASSING | any NOT_EVALUABLE member (candidate- or comparator-side) makes the family NOT-PASSING — never an inferred PASS |

**Alignment and statistics (§R5 quoted via R5_VERBATIM.md):** pooled Pearson
(binding) + Spearman (robustness) on the UNION calendar of both books'
trading days; non-trading days for one book EXCLUDED pairwise (no zero-fill —
forbidden); alignment date = session_date; USD both sides; margin to bar
reported (P-2); rho computed against EVERY comparison-set member, veto fires
on the WORST member, no averaging, no favorable-comparator selection (§R5-5).
No epsilon anywhere; any tolerance proposal is a separate re-frozen,
re-validated change BEFORE any real rho.

**Consequence of a kill:** worst-member \|rho\| > 0.20 ⇒ F2 family dead
(K2-class), zero scored identities execute, cycle records the 19 D2 rows and
stops. A measured \|rho\| ≤ 0.20 against any or all sibling books never
validates ES-F2 and never resurrects a dead family (ADDENDUM-D (5)
interpretation guard).

## 5. The 18 court-cluster proxies — full definition

**Source of record:** `ANCESTRY_COURT_INFRA` §S2 ("Macro/release-instant &
release-window reactions, 24 rows", sha256
`4f33851c3a065b754fc010bce417d2dd967f19ad0712162edb643a7a1bf8f0a6`) declares
"rho declared against rows 62–65/76–95" of
`/Users/hoangminhlong/my-quantitative/research/wayfinder/FAMILY_FAILURES.jsonl`
(173 rows; sha256
`4bc78a46e93173dbe21bb2649168b549811fe8fcc3871ab380917e95fe033264`,
re-hashed byte-identical this round). The **18 rho-target rows** (4+2+2+4+2+4
= 18), re-extracted this round by 1-based file line:

| line | family_id | source cycle | mechanism (one line) |
|---|---|---|---|
| 62 | FXFV9-A4-P1 | FOREX-FREE-V9 | realized-inflation event structure P1 (monthly vintaged-CPI decision calendar, GBPUSD-class majors) |
| 63 | FXFV9-A4-P2 | FOREX-FREE-V9 | realized-inflation event structure P2 (second parameterization) |
| 64 | FXFV9-A5-P1 | FOREX-FREE-V9 | realized-inflation PPP-deviation misalignment anchor (real-rate deviation from vintaged CPI index levels) |
| 65 | FXFV9-A5-P2 | FOREX-FREE-V9 | PPP-deviation misalignment P2 (second parameterization) |
| 76 | CNG1-A4-P1 | CRYPTO-NG1 | FOMC-instant drained-liquidity under-reaction (3-symbol perp, 8 PIT-evidenced instants) |
| 77 | CNG1-A4-P2 | CRYPTO-NG1 | forced pre-completion realization drift (pre-instant capped taker pressure) |
| 82 | FXNG1-A5-P1 | FOREX-NG1 | opening-follower print drift (early-economy release-order rollout, 16:00-NY grid) |
| 83 | FXNG1-A4-P2 | FOREX-NG1 | trailing-YoY CPI acceleration late-window drift (vintaged surprise vs frozen trend prior) |
| 84 | FXNG3-A4-P1 | FOREX-NG3 | CA revision sign drift (USDCAD, restricted first-print stream) |
| 85 | FXNG3-A4-P2 | FOREX-NG3 | CA revision magnitude regime (material-tail polarity) |
| 86 | FXNG3-A5-P1 | FOREX-NG3 | CA differential sign conditioning (USDCAD) |
| 87 | FXNG3-A5-P2 | FOREX-NG3 | CA-leg bilateral revision transfer (GBPUSD/AUDUSD/NZDUSD) |
| 88 | CNG2-A4-P1 | CRYPTO-NG2 | CPI-instant inflation reaction-sign continuation (H1 3-symbol) |
| 89 | CNG2-A4-P2 | CRYPTO-NG2 | NFP-instant labor flow-imbalance continuation |
| 92 | FXNG4-A4-P1 | FOREX-NG4 | EZ seasonal-naive print-deviation on EURUSD (restricted 37 events) |
| 93 | FXNG4-A4-P2 | FOREX-NG4 | EZ trailing-YoY print-deviation continuation |
| 94 | FXNG4-A5-P1 | FOREX-NG4 | EZ-US sign-opposition revision differential |
| 95 | FXNG4-A5-P2 | FOREX-NG4 | EZ-US magnitude-diff regime |

(The full S2 cluster additionally holds rows 38/40/49/51/56/59 — FXFV4–V8/V17
— which are NOT rho-targets and are not enumerated here.)

**Per-row daily-series derivation (materialization classes).** The dead-side
extraction law is as-scored / frozen-representation, "no re-run, no re-clock"
(§R5-1) for every proxy that HAS as-scored records; for never-scored proxies
(all six source families died pre-score, 0 cells, budget 0/6, except FOREX-NG1
which was scored 6/6) the frozen representation identity committed at the
proxy's own D2 IS the book — reconstructing it (same committed code, same
sha-pinned inputs, same committed decision dates, no new parameter) is
representation recovery, not re-clocking. Any deviation, any unrecoverable
pinned byte, any decision-date mismatch ⇒ **BLOCKED_DATA for that proxy ⇒
family BLOCKED_DATA by precedence P7** — never dropped silently, never
inferred, never self-excluded (owner-approved: "a missing artifact is
BLOCKED_DATA and never a silent exclusion").

- **Class A — as-scored committed daily series (2 rows: 82, 83).** Source
  artifacts (git objects at terminal commit `ea5721a2`, FOREX-NG1 E scored
  execution): `research/control/forex_ng1_run/e/cell_FXNG1-A5-P1-ANCHOR.json`
  and `cell_FXNG1-A4-P2-ANCHOR.json`. Each carries `series.series[]` =
  `{day, gross_usd, net_tier2_usd, cum_gross_usd, cum_net_tier2_usd}` with the
  artifact's own convention: "per-trade PnL realized at the exit grid day;
  cumulative curves over the full 1842-day grid (zero days omitted …); for
  the future DSR P-11 pass" — plus `per_trade_records[]` (37 rows A5-P1) with
  `entry_grid_day/exit_grid_day/gross_usd/net_usd_tier*/fold`. Derivation:
  map `day → net_tier2_usd` (net view) and `day → gross_usd` (gross view);
  as-scored, no re-run, no re-clock. **FULLY SPECIFIED.**
- **Class B — committed signed-cell maps + frozen identity (2 rows: 62, 63).**
  Source artifact (git object at `5f0527aa`, FOREX-FREE-V9 D2 r2):
  `research/control/forex_free_v9_run/d2/evidence/schedule_cells_proposals_v9_r2.json`
  keys `FXFV9-A4-P1-anchor` / `FXFV9-A4-P2-anchor` = per-decision signed-cell
  maps (`{date|pair → ±1}`; A4-P1 n=84, 2021-05-15..2025-07-15). The r2
  measurement ran on the frozen runner representation with the port script
  committed per P-12 remediation (FAMILY_FAILURES row 62 secondary_failures:
  "A1 r1/r2 port script committed per P-12 remediation"). Derivation: expand
  each committed decision cell over its committed holding span using the
  committed port-script span law and the pinned spot bytes
  (run_contract.json `data_pins.spot_reacquired` =
  `data_raw/forex_free_v9_spot/`, TD daily 5000 bars ×4 pairs, sha-pinned).
  Cross-check the materialized decision dates against the committed cell map;
  any mismatch or unrecoverable pinned byte ⇒ BLOCKED_DATA. **SPECIFIED
  (materialization at D2's first act).**
- **Class C — frozen representation identity + committed decision grid;
  materialize from committed code on sha-pinned inputs (12 rows: 76, 77,
  84–87, 88, 89, 92–95).** For each row the proxy's own D2 novelty-panel
  artifact (git objects at the cycle terminals: CNG1 `0cfb9acf`, FXNG3
  `b3786a2d`, CNG2 `71a29b15`, FXNG4 `a4ca6596`) commits (i) the decision
  grid — e.g. CNG1 `grid.decision_dates` = the 8 PIT-evidenced FOMC instants'
  dates; FXNG3/NG4 `representation_identity` (grid geometry "daily 16:00
  America/New_York common weekday grid, 1842 days 2018-04-04..2025-04-30",
  cells law "signed exposure date|pair, entry i..i+H-1, netting sign-of-sum",
  entry-clock and differential formulas verbatim); (ii) the construction
  proposal file with sha256 (`proposal_A4_P1.json` etc.);
  (iii) the representation/measurement code with sha256 (e.g. FXNG3:
  `research/assets/forex_ng3/d2/books.py` `992e3a24…`, `d2_run.py`
  `ac474eaf…`; CNG1: `measure.py` `6dc21748…`, `run_d2_measurement.py`
  `29852cb6…`); and (iv) the input-data pins with sha256 (panel CSVs
  CADS-addressed e.g. `111c1a2d…`; oi_series `f26a61e4…`; census/spot
  manifests sha-pinned). Derivation: re-execute the committed representation
  code on the recovered pinned input bytes, produce the per-decision series
  on exactly the committed decision grid, and CROSS-CHECK the materialized
  date set against the committed `decision_dates`/grid — equality is a
  release condition for the proxy; any unrecoverable byte, sha mismatch, or
  date mismatch ⇒ BLOCKED_DATA. **SPECIFIED (materialization at D2's first
  act; input-byte recovery verified at D2, never assumed).**
- **Class INCOMPLETE — derivation NOT specifiable from committed evidence
  (2 rows: 64, 65 → REGISTRATION BLOCKERS, see §12).** For FXFV9-A5-P1 and
  FXFV9-A5-P2 the ONLY committed A5 cell map
  (`schedule_cells_proposals_v9_r2.json` keys `FXFV9-A5-P1-anchor` n=3041
  spanning `1949-01..2026-07`, `FXFV9-A5-P2-anchor` n=3162 spanning
  `1922-04..2026-07`, month-keyed) is **the forbidden monthly-grid
  representation that A7 prelaunch REFUSED** (commit `67229fa9`:
  "the recorded PASSes 0.1062/0.0580 were measured on undisclosed
  monthly-grid 1917..2026 state maps, not the frozen representation"); the
  frozen daily 16:00-NY decision-grid books of the A7 recompute have no
  committed series bytes, and the recompute port "was not committed
  (irreproducible)" (FAMILY_FAILURES row 64 secondary_failures; A7 commit
  MEDIUM: "D2 numbers non-reproducible from committed cells"). Marked
  **PROXY_SPEC_INCOMPLETE**; exactly what is missing is enumerated in
  `REGISTRATION_BLOCKERS.json`.

**Proxy artifact format (all 18 rows, uniform):** each materialized proxy is
committed as D2's first act in the exact schema

```json
{"proxy_id": "<family_id>", "source_family": "<cycle_id>",
 "series_dates": ["YYYY-MM-DD", ...],
 "series_values": [<daily net PnL-or-return float>, ...],
 "sha256_of_source": "<sha256 of the source artifact bytes>",
 "extraction_status": "EXTRACTED | MATERIALIZED | BLOCKED_DATA | PROXY_SPEC_INCOMPLETE"}
```

disclosed sha'd and tamper-evident BEFORE any rho is cited (P-12; §R5-7),
worst-member veto applies to every kept row (§R5-5), margin-to-bar reported
(§R5-3), A7 prelaunch recomputes (§R5-7). Machine record:
`PROXY_SPEC_18.json` (companion file, this dir).

**Keep/drop ruling:** the court keeps all 18 (the owner decision's approved
sentence: "the remaining 55 comparator books and the 18 court-cluster proxies
participate under §R5-4 unchanged"). There is no drop path other than the
predicate table (P1–P9); in particular NO proxy is excludable for
inconvenience, and the exclusion list of §4 is closed at exactly two books
(append-only law; adding any name is a new owner decision).

## 6. The 55 trading books — daily-series derivation

All 55 books' series are derivable at D2 from committed terminal artifacts,
as-scored (R5-1 / ADDENDUM-D (2) extraction law; census verified
0 ARTIFACT_MISSING, 0 ARTIFACT_CORRUPT across all sources).

- **24 PB1 ES books** — source: pass_a per-trade arrays,
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep/research/control/FUTURES-ES-PB1-V1/gate6/ledger/runs/go_run_1/pass_a/FBES1-*.json`
  (24 files + summary.json sha256 `0f56a57be80c668f1e5f40964b29d991b09e6566828da14eea002cd937895d61`
  + trades_index.json sha256 `9734cfdee5d9b6801863139b16b0fdf9934a483fdad68a039467bec1543b573d`),
  committed clean at es-reg HEAD `935556cf5ec4914bc704b170ce4bab5045ca6027`
  (pass_a==pass_b byte-identical twin at 8283f135). Each file carries
  per-trade records with `session_date`, `net_pnl_usd`, `gross_pnl_usd`,
  `fold` (key set verified from file bytes). **Derivation rule:** daily
  series = aggregate `net_pnl_usd` by `session_date` (net binding; `gross_pnl_usd`
  by `session_date` = gross robustness view); in every trading book the
  distinct `session_date` count equals `n_trades` (one trade per signal
  session, flat by close) so the series has exactly `n_trades` rows. The two
  FLAT books (FBES1-FLAT; and in the sibling set FUTURES-NQ-V1-F2-FLAT) are
  the pre-locked exclusions of §4 — their zero chains are proven by bytes.
- **11 NQ-F2 books** — source: `FUTURES-NQ-V1/ledger/TRIAL_LEDGER.jsonl`
  (33 rows, sha256 `f90a60ab…2056`, re-hashed match this round), rows seq
  12–22, worktree `futures-5sym-prescored/prep` (frozen terminal, read-only).
  Each row's `payload.journal` carries per-trade records with `exit_ts`,
  `net_pnl_usd`, `fold_id`. **Derivation rule:** daily series = aggregate
  `net_pnl_usd` by the as-recorded calendar date of `exit_ts` (date component
  as stored — **no timezone re-clocking**); era confinement verified from
  journal bytes (all trading NQ-F2 books folds == {F4}, dates inside
  2023-01..2026-09).
- **22 FXF3 books (6E rows seq 12–22; 6B rows seq 38–48)** — source:
  `FUTURES-FX-V1/ledger/TRIAL_LEDGER.jsonl` (85 rows, sha256 `72e0a3ab…4ce7`,
  re-hashed match this round), same worktree. Same journal anatomy
  (`exit_ts`, `net_pnl_usd`, `fold_id`); folds F1–F4 as censused. **Derivation
  rule:** identical to NQ-F2 (aggregate `net_pnl_usd` by as-recorded
  `exit_ts` date; no re-clock).

No book's derivation has a gap: every enumerated artifact parsed, every
`totals.n_trades == len(trades)` equality asserted per PB1 book, cross-checks
match the terminal facts (NQ-F2 CONT pooled 65 / REV 73; 6E SC 40 / SD 38;
6B SC 22 / SD 20). **BLOCKERS: none.**

## 7. Cost contract — Variant A (frozen values; freeze re-signed at the F2 freeze)

- **Variant A (NFA basis), ES all-in per side: 21.00 / 33.50 / 46.00
  (S1/S2/S3) ⇒ RT 42.00 / 67.00 / 92.00.** Components: commission 0.85 +
  exchange 1.38 (CME, evidence-settled) + regulatory 0.02 default / 0.01
  inside the NFA window 2014-10-01..2017-12-31 (date-aware; window rows
  20.99 / 33.49 / 45.99) + spread half-turn proxy 6.25 (1-tick close-proxy;
  BBO true spread NOT_RUN) + slippage 12.50 / 25.00 / 37.50 per side.
- **Stale glued-superscript prints `1.386 / 21.006 / 33.506 / 46.006` are
  NEVER consumable** (COST_FREEZE_ERRATUM §2 of record; banned-value scan
  `1.386|21.006|33.506|46.006` over code+ledgers at load; Decimal recompute
  cell-match 18/18; window-aware builder consumption test — POWER_COST §4.2-4.3).
- Chain of record: COST_FREEZE_ERRATUM.md (sha `cf83bc2d…9ae8`) → owner
  `D3_RECORDED.json` (`f54610eb…e355`, D3-VARIANT-A-20261004) → CODE_AUDIT_B2
  §3 Decimal recompute 18/18 → POWER_COST_DESIGN §4 (sha `694dea10…5b8c`).
  Independent recompute re-verified to the cent this round (PREREG_CONDITIONS §2;
  ES_F2_RECHECK (c)). No open eratum against Variant A's values.
- **Labels binding: MODELED COST; fee values UNDER REVIEW until an A7-class
  re-audit (fresh IBKR/CME/NFA schedule re-pull at the freeze);
  VERIFIED_VS_ACCOUNT = NOT_RUN.** The successor's own D3-class owner cost
  record lands at the F2 freeze, before any scored run.
- Stress axis: the tier triple S1/S2/S3 (×1.0/×1.5/×2.0 of the 1-tick basis)
  is the ONLY sensitivity axis; no ad-hoc event-day surcharge (double-stress
  law).

## 8. Vintage 348 discipline (strict decision-time-known)

- **Law (committed, verbatim):** "for a historical decision date D, the
  correct expected-release calendar is the schedule vintage as known at D —
  pinned by a dated capture — never the current calendar"
  (BLS_VINTAGE_INVESTIGATION §5, quoted in VINTAGE_2025_DISPOSITION §1).
- **Rule 348:** every MAIN day is one on which a release was genuinely
  expected as-known at its decision date (dated capture). Removes the two
  known-before-day phantoms (CPI 2025-10-15, EMPSIT 2025-12-05); adds the
  four genuinely-announced revised days (CPI 2025-10-24, 12-18; EMPSIT
  2025-11-20, 12-16); keeps EMPSIT 2025-10-03 (announced 11-14, after the day
  ⇒ valid as-known expected/non-arrival day); canceled pair (CPI 2025-11-13,
  EMPSIT 2025-11-07) stays NC-2b falsifier-only. MAIN n = 348 = CPI 169 +
  EMPSIT 179. §1.1 n-invariant provenance repairs ride the same written rule.
- **Calendar of record:** `bls_dates.json` sha256
  `ad41d2a76708229b9eef4a02bf62cd6df44eb023455f2c98d2d21cb5b1363009`
  (204 CPI + 204 EMPSIT scheduled dates, `all_0830` stamp, official Eastern-Time
  chain).
- **2026 handling (PC-2):** 24 scheduled 2026 dates, of which 17 are eligible
  in-panel MAIN days (CPI 9 + EMPSIT 8; panel ends 2026-09-30; EMPSIT 04-03
  Good Friday excluded) and 6 are Q4 out-of-panel with future decision dates.
  Zero `wb_2026*` page captures were archived locally at packet time; the
  pinned CDX indexes show ≥1 pre-decision-time wayback snapshot for EVERY
  eligible 2026 date, and the keyless replay route is probe-proven
  (PREREG_CONDITIONS §1.3-1.4). **Fetch-at-registration (owner-directed):**
  the per-decision-date dated captures are fetched and pinned under
  `registration/vintage_2026/` (lane P2 pin location,
  `d1_resolution/prereg_conditions/` is the law of record). **Fail-closed
  rule: any eligible decision date WITHOUT a pinned pre-decision-time archive
  at D2 time is EXCLUDED from MAIN — never inferred, never substituted by the
  current calendar.** Q4-2026 dates enter only if the panel ever extends past
  2026-09-30 (written forward-capture rule per VINTAGE §4.1) — out of scope
  for this cycle's scored cells.
- No vintage-parameter rescue: the rule is frozen before any scored cell; the
  only 2026-lapse-class handling is the pinned-capture rule above.

## 9. Gates (G-matrix) + K2, and power honesty

**Per-identity gates** (mirroring SPEC_PB1_ES §8; freeze at registration):

- **G1** — after-modeled-cost expectancy > 0 at S2 (and S1);
- **G2** — PF ≥ 1.10 at S2;
- **G3** — ≥ 2/4 folds positive at S2;
- **G4** — K1 era-sign stable;
- **G6** — 2020-03..04 contribution < 80%;
- **G7** — arm beats C2 AND C1 on after-cost expectancy at S2, else
  "no conditioning information" (G7-class verdict);
- **G8** — reproduction byte-match;
- **G9** — A7 prelaunch (fresh context) with 0 HIGH/CRITICAL unresolved.

**Family kills (pre-registered in the corpus spec, §(7)):** F2-K1 era
instability across eras where the 07:30 anatomy reproduced; **F2-K2 both arms
below the S1 RT floor ⇒ family DEAD (K2-class; no re-param)** — same shape as
the NQ-V1 DEAD_K2 (29/29 NO_ELIGIBLE_IDENTITY) and FX-V1 DEAD_K2 (73/73
REJECT_ALL) terminals: family death publishes, closes the cycle, and admits
no parameter rescue; F2-K3 2020-03..04 concentration ≥ 80%; F2-K4 delay flip
D0 vs D30 ⇒ cash-open-push artifact; F2-K5 NC-2/NC-2b reproduction ⇒ kill;
F2-K6 per-era 07:30 anatomy gate — already PASSED (3.416 / 2.504 / 2.955, all
eras ≥ 2.0; PREP_GATE_MATRIX row 2) and carried. (Boundary: the K6 ES T3
1.220 < 1.25 finding belongs to the ESNQ-F5 EXPWITCH family and does NOT bind
ES-F2.)

**D2 gate:** §4 above — worst-member \|rho\| > 0.20 STRICT veto; precedence
BLOCKED_DATA > dead > not-evaluable > PASS; NOT_EVALUABLE = NOT-PASSING; a
D2 kill fires K2-class family death with zero scored identities.

**Power honesty (carried verbatim from the committed numbers):** pooled
family t(0.25σ) = **4.65** at n=346 (348-rule n=348 → 4.664; MDE −0.29%);
MDE_t3 $186.92 (D0) / $172.04 (D30) = 4.5× S1 / 1.9× S3 RT — the ONLY cell
the committed power law clears with real headroom (COST-CLEARABLE-IF-REAL).
CPI-only t = **3.24** and NFP-only t = **3.34** are marginal (n≥144 floor
margins 24/34 days). **Every era cell (127/111/108), every fold cell
(37/110/91/108), and every series×era/fold cell is UNDERPOWERED-at-0.25σ** —
era/fold must never be a scored estimand; they are 0-cost evaluation views
(F2_DATA_VERIFICATION §7: "only family-pooled and series-pooled questions are
live"). In every cell MDE_t3 exceeds all RT hurdles; a 0.25σ edge is
plausibility-shaped; no effect is claimed.

## 10. Ancestry / leakage boundaries

- **F1 (`FOMC-RES`) UNDERPOWERED — excluded:** n=91 closed universe, pooled
  t(0.25σ) = 2.38 < 3; break-even f* = 0.335–0.377σ; MDE_t3 $609.76/$656.25 ≫
  RT 42/67/92; fold F1 empty; era-E1 n=8. A null at n=91 is a REGISTERED
  DEATH; F1 may enter a future cycle only as an owner-accepted
  recorded-UNDERPOWERED rider, never mixed into an F2 package.
- **F3 (`COT-CROWD`) / F4 (`RUN-REV`) excluded:** their armed-day counts were
  never power-measured (NOT_RUN); buying their scoring legs now = ungated
  families mixed into the denominator. Zero leakage arithmetic: the 19 scored
  IDs and the 19 D2 rows contain no F1/F3/F4 identity (16 = 8 CPI + 8 NFP;
  +3 shared controls), and the 38-row budget contains no other family's cell.
- **Macro-morning fence law (no revival):** "any NQ/6E/6B/6J macro-morning
  CPI/NFP question is the ES-F2 family, not a new mechanism"
  (funnel/RESEARCH_FUNNEL.md L41-42; funnel.json L50). The dead siblings'
  terminals (NQ-F2 DEAD_K2, 6E-F3/6B-F3 DEAD_K2 at a72b9957) enter this cycle
  ONLY as dead-side comparators (ADDENDUM-D); **no revival by relabel or
  parameter; any sibling revival is an owner adjudication, never a relabel
  (owner amendment X-2); K2 is per-cycle, per-instrument; a measured
  \|rho\| ≤ 0.20 never resurrects a dead family.** NQ-F1 (FOMC 13:00-CT
  clock), ECB-day 6E-F2/6B-F2, and the 6J families are NOT comparators here
  (different information source or clock — ADDENDUM-D (4)).
- **ES-NQ cross out of scope:** stays MECHANISM_GAP / CROSS-lane honest zero
  (correlation is not a mechanism); not part of this cycle.
- **End-of-session (MIM-ES) out of scope:** stays in the survey branch;
  cost-bound; ancestry NOT_RUN_BLOCKED_AUTHORITY there.

## 11. Two-key GO, A7 prelaunch, S1

- **Typed-GO phrase (registered now, consumed only by the owner):**
  `GO FUTURES-ES-F2-V1 SCORED EXECUTION`. The phrase is registered as part of
  this plan and is **NOT consumed** by registration, by D2, or by any
  controller/lane act. Scored execution stays sealed until the owner types
  the phrase (owner decision `typed_go: NOT GRANTED`).
- **A7 prelaunch (fresh context) is REQUIRED** before any scored identity:
  re-verifies pins, representation, gates, cost labels, and RECOMPUTES the
  D2 verdict on the frozen representation by default (§R5-7 / P-12 law);
  0 HIGH/CRITICAL unresolved is gate G9.
- **S1 SEALED:** no orders, no live routing, no keys, no push/merge; the
  owner decision records `s1_orders_push_merge: NOT GRANTED`.
- Registration proceeds only via the official CAS registry path (owner
  delegation `registration: AUTHORIZED — conditional on all registration
  conditions verified`).

## 12. Open items at registration

1. **PC-2 / vintage-2026 archives (fetch-at-registration, owner-directed):**
   dated pre-decision-time captures for the 17 eligible 2026 days pinned into
   `registration/vintage_2026/` (lane P2 runs in parallel; the fail-closed
   exclusion rule of §8 applies at D2 regardless).
2. **Proxy enumeration as D2's first act (P-12):** the §5 table +
   `PROXY_SPEC_18.json` is the registered definition; the materialized
   per-proxy artifacts (exact schema of §5) are committed, sha'd and verified
   (decision-date cross-checks) BEFORE any rho; any BLOCKED_DATA proxy is
   recorded and propagates family BLOCKED_DATA by precedence.
3. **C1 seed disclosure at the freeze:** the concrete registered seed for
   `FBES2-C1-PLA-0730-S2` is fixed and disclosed in writing at the freeze
   (owner act, per packet §9 item 5); deterministic-given-seed semantics per
   §2.
4. **REGISTRATION BLOCKERS (must be resolved before registration proceeds):**
   - **RB-1 — FXFV9-A5-P1 (line 64):** PROXY_SPEC_INCOMPLETE. Missing:
     (a) committed construction code for the FROZEN daily 16:00-NY
     decision-grid A5 books (the A7 recompute port was never committed —
     "irreproducible", FAMILY_FAILURES row 64); (b) committed series bytes or
     a deterministic materialization path for those books — the only
     committed A5 cell map is the FORBIDDEN monthly-grid representation
     (1949-01..2026-07 month keys, A7-refused); (c) the PIT-correct
     construction consumes the mandated vintaged CPI channel, recorded
     unused at the A7 prelaunch (HIGH finding) — the vintaged-channel A5
     book has no committed implementation. Lawful fallback if unresolved at
     D2: the proxy is BLOCKED_DATA ⇒ family BLOCKED_DATA ⇒ D2 cannot PASS
     while it stands.
   - **RB-2 — FXFV9-A5-P2 (line 65):** PROXY_SPEC_INCOMPLETE — same three
     missing items as RB-1 (same construction family, second
     parameterization; the committed `FXFV9-A5-P2-anchor` cell map is the
     same forbidden monthly-grid class, 1922-04..2026-07).
   - Resolution path (either): a PREP/registration-time act commits the
     daily-grid A5 book construction over the staged vintaged channel
     (`fred_vintaged_manifest_v9.json` + data pins of
     `forex_free_v9_run/run_contract.json`) and the resulting series bytes,
     restoring derivability per §5 Class B/C — or the owner explicitly
     accepts the lawful BLOCKED_DATA consequence in writing at registration
     (which would predetermine D2 NOT-PASSING and is recorded as such, never
     papered over). No third path exists: these two proxies cannot be
     dropped, excluded, or inferred (§4, §5 laws).

Everything else is complete: the 55 trading books' derivations are fully
specified from committed artifacts (§6, no gaps), the 16 Class A/B/C proxies
are specified, the budget/ancestry law is frozen by the owner decision, and
the G/K matrix is pre-registered. Upon resolution (or owner-accepted written
consequence) of RB-1/RB-2, registration may proceed via the official CAS
registry path.

— End PLAN_futures_es_f2_v1.md (drafted by lane P1, wave 5,
FUTURES-NQFX-PACKET-PREP-20261007; zero PnL, zero rho, zero registration, zero GO).

---

## AMENDMENT A (2026-10-07, owner option (a)) — RB-1/RB-2 RESOLVED via the A5 daily-grid port

- Owner approved option (a) verbatim: FXFV9-A5-P1/P2 resolved via a LAWFUL
  daily-grid representation from frozen vintage inputs; no monthly-grid reuse
  (A7-refused); no dropping; no threshold/comparison-set change. Recorded at
  `FUTURES-NQFX-PACKET-PREP-20261007/auth/OWNER_DECISION_RECORDED.json`
  (sentence sha256 01cca9eb…).
- Construction path COMMITTED + VERIFIER-ACCEPTED:
  `FUTURES-NQFX-PACKET-PREP-20261007/registration/a5_port/` (a5_daily_grid,
  8 stdlib modules; 60/60 synthetic tests exit 0; machinery witness P1 anchor
  config digest == committed ff6c8247 byte-for-byte; VERIFY-A5PORT ACCEPT,
  19 CONFIRMED / 0 MISMATCH). Law conformance line-for-line vs the committed
  runners at 6e9f6069 with the single intentional delta = the AX2-C1
  vintaged-channel re-wire (the A7 F-HIGH-1 repair).
- D2 FIRST ACT (binding order): stage the 9 pinned-but-unrecoverable byte sets
  per `registration/a5_port/A5_PORT_APPENDIX.md` §6 (TD spot ×4 + ALFRED
  vintaged ×4 via keyed owner-entitlement channels — keys env-only, never
  echoed; NZ Infoshare tail; CA/GB official tails already staged keyless),
  verify pins byte-exact, run preflight to CONSTRUCTION_DETERMINATE,
  materialize + byte-pin FXFV9-A5-P1.json / FXFV9-A5-P2.json under
  `research/control/FUTURES-ES-F2-V1/d2/comparators/proxies/`, grid witness
  1903/2018-04-04/2025-07-24. ANY pin mismatch, missing print, or
  non-reproducible series => that proxy BLOCKED_DATA (never re-presented,
  never dropped); family precedence per §R5-4/approved Reading A applies.
- All other 16 proxies + 55 books materialize per PROXY_SPEC_18.json; the
  exclusion list {FBES1-FLAT, FUTURES-NQ-V1-F2-FLAT} stays pre-locked; kill
  rule strict |rho|>0.20; denominators 57 books / 38 D2 rows unchanged.
- Registration blockers RB-1/RB-2: CLOSED by this amendment (registration
  conditions genuinely met; controller executes CAS registration).
