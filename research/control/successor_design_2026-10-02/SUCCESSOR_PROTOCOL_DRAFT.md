# SUCCESSOR_PROTOCOL_DRAFT v3 — successor_design_2026-10-02 (NOT RUN; nothing registers today)

> **v3 (co-owner round 3, F1–F5):** two-freeze law (FREEZE-1 search space at
> registration / FREEZE-2 learned values after LEARN); GO-gated fold-1
> (dates ILLUSTRATIVE pending actual anchors); sealed-tail lineage verdicts
> by axis; warmup feasibility from corpus code/configs (no trimming);
> floor-causality INF/ECO law (design §1 + SAMPLE_FEASIBILITY_MATRIX.md);
> canonical budget via machine-verified arm manifest. All changes itemized
> in `ERRATUM_V3.md`.

## 1. Exposure lineage (per-axis verdicts; replaces v2 §1.1–§1.2)

### 1.1 What is proven, disproven, unproven `[M: lane audit, manifests/hashes/GO records only — no sealed bytes read]`

| axis | verdict | evidence |
|---|---|---|
| DAILY battery execution authorized | **PROVEN** | owner election "ĐI TIẾP KHÔNG CÓ SAO KÊ" + two-key GO 2026-10-01T08:36:23Z (`auth/GO_RECORDED.json`), frozen calendar A7-audited |
| Tail-range reads constituted an S1 unseal | **NOT_RUN_UNPROVEN** | no artifact in the DAILY chain names 2026-01-02→2026-06-26 in any election/GO; the GO record asserts the OPPOSITE. Missing artifact: an explicit owner election naming the tail (ratification) or an erratum correcting DAILY's "S1 SEALED" assertions |
| Tail statistically read/scored | **PROVEN — EXPOSED** | panels (4,184 sha-verified .bi5/pair, coverage → 2026-09-23) include all tail dates; DAILY journals contain tail-dated FILLED rows (USDJPY 2026-01-28, 2026-02-04; EURUSD 2026-04-07, 04-26, 06-10); G5 band derivation used the full 1,490-day window |
| Tail usable as untouched validation | **REFUTED** | same evidence — affirmatively disproven, not merely NOT_RUN |
| Same bytes vs same dates/different source | **PROVEN same bytes** at hash level | DAILY `datainputs.py` sha-verifies every .bi5 against the panel-local manifest; hashes identical to PC12A poolB `panel_hashes_*.jsonl` on tail dates; identical physical paths. Whether a physically separate "S1 store" exists besides this date-range access class: **NOT_RUN_UNPROVEN** (no artifact defines one) |

**Recorded lineage defect (disclosed, not silently fixed):** DAILY's own
committed authorization chain asserts what its journals disprove —
`GO_RECORDED.json` `"s1": "SEALED_UNTOUCHED"`, plan §0b "S1 sealed tail
untouched", `TERMINAL_DECISION.md` "S1 SEALED throughout" — while folds 7–8
filled on tail dates. The frozen DAILY artifacts are append-only and are
NOT edited; this section is the disclosure of record. **Owner action
needed:** ratify the tail-for-exploratory read retroactively, declare the
directive's scope, or file a DAILY-side APPEND-ONLY incident erratum
(proposed here, not executed); until then the tail's PERMISSION status
stays NOT_RUN_UNPROVEN even though its STATISTICAL EXPOSURE is proven (the
two axes are never merged).

**Standing-directive timeline `[M]`:** the "stays SEALED" directive was
typed 2026-10-01 ~04:31–05:39Z; DAILY's tail-opening fills executed ~09:24Z
the same morning — the directive predates the fills by ~4h and did not stop
them because nothing in the DAILY chain connected the two. **This packet
does NOT interpret the directive's intended scope and does NOT ratify the
historical read** — what it covers (successor use? all future reads?
retroactive?) is an OWNER question (D-1a: explicit ratification, a scoping
declaration, or a DAILY-side append-only incident erratum — proposed, not
executed; frozen artifacts and registry untouched). Two axes stay separate
everywhere: PERMISSION (who may read what — owner-decided only) vs
STATISTICAL EXPOSURE (what has been read — measured above).

**Sealed-tail length discrepancy (pin at registration):** CAM §3 says
"26-week sealed tail"; the owner-typed window 2026-01-02→2026-06-26 is 176
days = 25.1w end-inclusive. One of the two is authoritative — the
registration package must pin which.

### 1.2 Read-scope honesty (replaces the grep over-claim)

"No committed artifact in the three searched control trees
(successor_design_2026-10-02, terminal_review_2026-10-01,
DAILY-EXPLORATORY-V1) references M1 vehicle prices dated after 2026-09-23
as a data input. Unreadability outside those trees and outside committed
artifacts is NOT_RUN_UNPROVEN: no repo-wide read audit exists, and the
sixsource read-only collector streamed live post-09-23 FX ticks on
2026-09-28 by design (sanitized metadata + raw sha256 on file; index schema
has no producer-version field — disclosed gap). 'Unread' here means 'no
artifact-of-record consumes such bytes', not 'no process ever touched
them'."

## 2. Two-freeze law and stage sequence (replaces v2 §2–§3.1)

```text
(1) DRAFT/ADMISSION  this packet; owner review; NOTHING runs
(2) REGISTRATION = FREEZE-1  owner elects: calendar variant, unseal
    ratification (if any), tail-as-warmup (if any), S014/S017 membership,
    aggregate-floor reading, warmup-unpinned-constant pins (S009 277td,
    S023 142td, VC2 profile window), risk caps, budget, floors law
    (INF/ECO), full grid NODE LISTS + selection objective + deterministic
    LEARN-only algorithm + NOT_RUN_GRID_THIN collapse law
(3) IMPLEMENTATION   engine prerequisites (design §0) + INF/ECO +
    truncation/mutation harnesses; HN-6 TB-LABELS TRAIN-side
(4) LEARN            runs the FROZEN algorithm on LEARN data only
(5) FREEZE-2         learned VALUES (hour sets, f-ratio, J3 multiplier,
    B3S leg) + engine code SHA + data manifests + selection audit trail
(6) A7 PRELAUNCH     independent audit (two-key 1; includes T1–T4 pass)
(7) OWNER GO         fresh GO at this cycle's own gate (two-key 2)
(8) EXECUTION        validation folds — fold-1's first session starts
    strictly AFTER max(FREEZE-2, A7 completion, GO). No part of any
    validation fold may predate GO. Interim typed readings; NO threshold/
    composition changes (amendments clarify execution law only)
(9) TERMINAL         full battery + stress + mandatory two-sided tables;
    A7 terminal; two-half close; negative close first-class
```

**Selection law (unchanged core, corrected timing):** FREEZE-1 freezes the
search space and the rules of the game; FREEZE-2 freezes the learned
values. Composition/membership changes discovered on validation require a
NEW registered cycle; validation-fold LOL/LORO are fixed diagnostics that
TYPE hypotheses, never selectors. LEARN cannot decide S014/S017
(expected-count arithmetic, §4 row 4/6 of SAMPLE_FEASIBILITY_MATRIX.md).

**Purge/embargo basis (per family; overall = max of elected options):**
HN-1 gates 0d (decision-time predicates; LEARN-end force-flat makes labels
LEARN-only); retires 0d; E2/HN-2 counters 26w feature-warm from LEARN
(TRAIN-side, lawful); J3 guard 28d trailing-spend state — cold-start or
LEARN-warm elected at FREEZE-1; multimonth legs via LEARN-end force-flat
(else that leg's purge = its own max holding time — calendar extends,
never shortens). Default: 7d embargo + LEARN-end force-flat + J3 election.

## 3. Calendar variants (ILLUSTRATIVE — pending actual registration_ts / go_ts)

Anchor semantics: `registration_ts` and `go_ts` are PENDING (nothing is
registered; the 2026-10-02 anchor is assumed). Gating law:
`fold1_start = max(learn_end + 1 + purge_days, go_date + 1)`. End-inclusive
26w folds; 6 folds span 1,091 days; conventions validated against the 8
executed DAILY fold windows (`analysis/calendar_variants.py`).

| variant | LEARN | fold-1 = max(LEARN+1+purge, GO+1) | fold-6 end (readable +1) |
|---|---|---|---|
| A (tail-consuming; needs unseal ratification + FREEZE-1 election) | 2025-12-27→2026-10-01 (on file) | GO+1 (δ after registration) | `end_A(δ) = R + δ + 1092d`: δ=1w → **2029-10-05 (10-06)**; δ=4w → **2029-10-26 (10-27)**. δ=0 (v2's 2029-09-27) is UNLAWFUL — fold 1 would predate GO |
| B (no unseal) | registration → +181d (2026-10-02→2027-04-01 illustrative; accumulates) | max(GO+1, LEARN+7) | `end_B(δ) = max(L+δ+1, L+7) + 1091d`: δ=1w → **2030-04-04 (04-05)**; δ=4w → **2030-04-25 (04-26)** |
| ~~A′~~ | WITHDRAWN (v2; double-use) | — | — |

**Warmup feasibility (from corpus code/configs — no trimming):** per-leg
warmup `[M: legs_config + leg_rules.py]`: S002-JPY 230td (≈46w) · S003 290td
(≈58w) · S014 230td (≈46w) · S009 277td code-derived (≈55.4w; config omits
the field — pin at FREEZE-1) · S023 142td code / 140 config (pin) · S026
20td · S013 45td · S046 50td · GBP-S002 20td · S017 15td · VC2 ~1 session
(profile window unpinned — pin). Under variant B, four legs (S002-JPY,
S003, S014, S009) reach back into the owner-typed tail at fold-1 start
(37–121d of tail) → NOT ADMISSIBLE at fold 1 unless the owner elects
**(i)** tail-as-warmup for FEATURE inputs only; else **(ii)** those legs
admit from fold 2 (fold-1 rows typed `NOT_RUN_WARMUP`, FLAT
deterministically); or **(iii)** NOT ADMISSIBLE this cycle. **Nothing is
trimmed** — v2's "trim warmup to 26w" is repealed (it silently starved
4 legs and was itself the arbitrary trim the law forbids; S003's 58w reach
exceeds even an untrimmed 52w window). Variant A has no fold-1 warmup
problem (LEARN covers the reach-backs).

All dates extend (never shorten) if floors bind, folds go thin, or the
collector goes quiet. The 2029/2030 dates are FULL-BATTERY dates — see §5
for what can proceed before them.

## 4. Owner decision menu (each ONE action; nothing runs before it)

| id | decision | consequence |
|---|---|---|
| D-1 | elect calendar variant A / B (+ δ expectations) | sets the fold-1 gate per §3 |
| D-1a | A only: ratify the tail-for-exploratory read (retroactive) AND elect tail-as-LEARN for the successor | resolves the NOT_RUN_UNPROVEN authorization axis; without ratification the lineage defect stands and A is unavailable |
| D-1b | B only: elect tail-as-warmup (feature-only) for the 4 reach-back legs, or accept their fold-2 admission, or drop them | per §3 warmup law |
| D-2 | export IBKR Activity/Flex statement (optional) | upgrades ONLY commission + swap/accrual attribution where valid; never slippage/spread-beyond-cells/capacity/history; DECLARED + stress remain for exploratory |
| D-3 | approve registration (FREEZE-1 package: budget per arm manifest, floors law incl. INF/ECO + aggregate reading, membership elections, warmup pins, risk caps, grids) | opens the cycle at stage 2 |
| D-4 | (separate track) PIT declarations daily-cohort; futures chain naming | opens OTHER calendars |
| D-5 | (null) reject every hypothesis | program FLAT; cost authority + cohort unlocks remain |

## 5. The two tracks (what can start NOW vs what waits for dates)

**Track 1 — HISTORICAL EXPLORATORY RESEARCH (start immediately from exposed
journals; every new scored computation still needs its own small registered
cycle + gates + GO; results are hypothesis-generating and NEVER independent
validation):**
1. **HN-6 TB-LABELS producer** over the committed M1 panels (TRAIN-side +
   EXPOSED-labeled): unlocks exit-geometry questions (S013 2.8σ ordering,
   S017 1-minute stop-outs, S002 ±2-pip vs ±3, MAE/MFE W/L separation).
2. **Journal forensics extensions** (analysis-only): extend the census with
   the guard spend-band histogram (row-5 input), session/DST alignment of
   the NY/handover buckets, blocked-set two-sided tables.
3. **Full-path LOL/LORO replay on the EXPOSED folds** as a registered
   exploratory identity: re-run the whole netting/caps/cost path
   portfolio-minus-leg — this is the ONLY lawful way to price leg surgery
   (per-leg PnL arithmetic is banned); results type priors for the next
   registration, never validate.
4. **Cost/mechanism checks** under DECLARED + stress bands (no after-cost
   claims).

**Track 2 — PROSPECTIVE EVIDENCE COLLECTION + VALIDATION (starts only after
FREEZE-2 + A7 + GO per §2):** the 6×26w battery with pre-declared sample
milestones (SAMPLE_FEASIBILITY_MATRIX.md), interim typed diagnostics after
each fold (allowed and expected), acceptance bars unchanged.

**Recommended priority (with reasons):** Track 1 items 1–2 FIRST (TB-LABELS
is the single highest-leverage unlock — it feeds exit-geometry hypotheses,
HN-6, and the successor engine's MAE/MFE fields; forensics item 2 produces
the J3 spend-band input the register needs BEFORE registration), then
Track 1 item 3 (exploratory LOL/LORO replay — prerequisite evidence for the
S014/S017/S002 membership elections at FREEZE-1), with Track 2's
registration (D-3) proceeding whenever the owner is ready — nothing in
Track 1 blocks on 2029/2030, and nothing in Track 2's acceptance bars is
relaxed to produce results sooner.

## 6. Boundaries held

No scored run, no S1 read, no sealed-tail byte access (this revision used
manifests/hashes/GO records only), no orders/paper/live, no GO, no closed-
budget reuse, no registry write. Frozen DAILY artifacts untouched
(append-only); the lineage defect is disclosed here, not papered over.
Push/merge forbidden; this packet lands on root main by pathspec.

— end protocol draft v3 —
