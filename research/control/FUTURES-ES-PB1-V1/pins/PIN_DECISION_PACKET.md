# PIN_DECISION_PACKET — FUTURES-ES-PB1-V1, lane PIN-ADJUDICATION (gate-5 input, pre-GO)

- Adjudication lane (independent): prior-authority hunt + design-merit evaluation
  of the three dry-run ambiguity pins **D-A1 / D-A2 / D-A3**. Measured at
  worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`,
  branch `prep/futures-es-reg-20261004`, HEAD **`8324a8c0e414fb683d9bfa6f56734d0a17b9d40a`**
  (one bare `rev-parse` at start; `git status --porcelain` EMPTY at start —
  every artifact read below is therefore the committed corpus at this HEAD;
  one read-only `git show` history check performed and recorded in §5).
- **Outcome-blindness law honored**: NO quarantined rehearsal numeric was read
  or used as a decision input. Only the DRYRUN_REPORT's *pin declarations and
  findings text* were read (permitted). No option below is chosen because of
  any rehearsal output; per-pin notes carry design-merit reasoning only.
- **This packet ratifies nothing.** It is a signature menu for the typed owner
  gate (plan §5). Every classification below states what prior artifacts
  already freeze vs what genuinely needs an owner ruling.
- Machine mirror: `pins/pin_decisions.json` (same directory).

## 0. Executive classification

| pin | question | prior authority on the exact item | classification | dry-run recorded default |
|---|---|---|---|---|
| D-A1 | q80 percentile interpolation method | **NOT_FOUND** — method unstated in every authority | **OWNER_RATIFICATION_REQUIRED** | `numpy.percentile(…, 80)` linear |
| D-A2 | C2 always-on control direction | **NOT_FOUND** — direction unstated; C2's *role* IS frozen | **OWNER_RATIFICATION_REQUIRED** | unconditional LONG, D0, hold to era-correct close, no TP/SL |
| D-A3 | C1 placebo RNG algorithm | **PARTIAL** — seed value + per-session determinism + single-seed/single-delay constraints ARE frozen; algorithm NOT_FOUND | **OWNER_RATIFICATION_REQUIRED** (algorithm only; frozen seed law untouchable) | `sha256("FBES1-PLA-D0-S2|seed=20261002|"+date)[0] < 0x80 → +1 else −1` |

**Zero ALREADY_FROZEN pins** ⇒ no append-only closure is drafted by this lane;
**zero CRITICAL deviations** — for none of the three pins does the dry-run's
recorded default contradict any frozen law text (there is no frozen law on
these exact items; the defaults satisfy every frozen constraint they touch —
see §4 per-pin "constraint compliance"). The dry-run's own report correctly
declared all three as pins rather than silently guessing (DRYRUN_REPORT §4).

## 1. D-A1 — q80 percentile interpolation method

### 1.1 Prior-authority hunt (what IS frozen vs what is not)

Every authority that names the q80 was swept. All of them freeze the SAME
three facts and none of them names an interpolation method:

| artifact (sha256, prefix) | location | exact wording on q80 | method? |
|---|---|---|---|
| SPEC_PB1_ES r3 `445f7499…` | §3 L73-74 | "điều kiện \|m\| ≥ q80(\|m\|, trailing-252d, strict-past) — q80 từ anatomy (NQ dossier H4 refined spec; ES §8-H5), không tune" | NO |
| PLAYBOOKS_DRAFT r5 `7610ed3c…` | §1 Tín hiệu row (L65) | "[PROVISIONAL: q80 — chọn từ anatomy, không tune]" | NO |
| NQ_DEEP_v2 `d3cf621c…` | §H4 (L176) — the "NQ dossier H4 refined spec" SPEC cites | "condition = trailing-252d 80th percentile of \|overnight\| (strict past)" | NO |
| ES_DEEP_v2 `05f0874f…` | §8-H5 (L435-441) — the "ES §8-H5" SPEC cites | H5 refined spec "drafted in handoff"; the DEEP-ES handoff contains **zero** occurrences of "q80" | NO |
| ES_DEEPFOUR_V3_ADDENDUM `d18d5422…` | §9 signal row (L271) | "condition \|m\| ≥ q80(\|m\|, trailing-252d, strict-past) — q80 from anatomy, not tuned" | NO |
| NQ_DEEPFOUR_V3_ADDENDUM `e78548a6…` | §9 signal row (L292) | "\|m\| ≥ q80(\|m\|, trailing-252d, strict-past)" | NO |
| ESNQ_HYPOTHESES `9f9176e5…` | §0.5 (L104) | "q80-strict-past OVN tail" | NO |
| HYPOTHESES_ESNQ_R3 `9dfe7b12…` | §2 overlap disclosure (L267) | "(q80 OVN tails)" | NO |
| selection_freeze / identity_table_24 `6e391980…` / A7_PRELAUNCH `553c55a4…` | identity rows | carry the q80 condition by reference only | NO |

Grep coverage: `q80|quantile|percentile|interpolat|linear|nearest|midpoint`
across `research/` + `plans/` (md/json/py) — no ES-corpus hit pairs the q80
with any method keyword; the only `np.percentile` calls in the ES/NQ analysis
corpus are descriptive DTE p10/p90 tables (NQ_a3_term.py), not the PB1 tail
law. The anatomy that "q80 comes from" measured tail *share* descriptively; it
never fixed a computational convention for the scored threshold.

**Frozen by prior law (do not amend):** threshold level 80; window trailing
252d of |m|; strict-past; warmup 252; "không tune" (the level itself is not an
owner knob — only the interpolation *method* is open).

### 1.2 Admissible option space (design-merit only)

| option | one-line consequence | determinism / PIT | identity table |
|---|---|---|---|
| (a) Linear interpolation (numpy/pandas default, R type-7) | threshold is a convex combination of the two adjacent order statistics at the fractional position 0.8·(n−1) | deterministic; PIT-safe (window already strict-past); matches the toolchain default and the machinery already written | unchanged (24) |
| (b) Nearest-rank / empirical (R type-1) | threshold = smallest observed order statistic with rank ≥ ⌈0.8·n⌉ (n=252 ⇒ rank 203); threshold is an actual historical \|m\| | deterministic; PIT-safe; tie-handling explicit (equal values share rank) | unchanged (24) |
| (c) Midpoint of adjacent order statistics (R type-2) | average of the two order statistics bracketing the fractional position | deterministic; PIT-safe; least common in the repo toolchain | unchanged (24) |

Empirical scope of the difference: the three options differ **only** when the
0.8 position is fractional (n·0.8 non-integral; with a full 252-window it
always is), and then only by the gap between adjacent order statistics of the
trailing window — i.e. the choice can flip *borderline* sessions between armed
and not-armed. It never changes which identities exist, only membership of
trades inside the primary/FOMCIN arms. All three are equally deterministic and
equally PIT-legal; the choice is a scored-output convention that must be law
before gate 6 so the scored run is reproducible from text alone.

### 1.3 Decision text for the owner (no pre-selection)

> **D-A1**: "The q80 threshold for FBES1-PB1-* arms is computed from the
> trailing-252d strict-past |m| window using method ______ (option a/b/c),
> consistent with SPEC §3 ('q80 từ anatomy, không tune'). The dry-run's
> recorded `numpy.percentile(…, 80)` linear is the default currently recorded
> in rehearsal machinery — not yet law."

## 2. D-A2 — C2 always-on control direction

### 2.1 Prior-authority hunt

The corpus repeatedly freezes C2's **role** and **config**, never its
**direction**:

| artifact (sha256, prefix) | location | exact wording | direction? |
|---|---|---|---|
| SPEC_PB1_ES r3 `445f7499…` | §6 L128 | "C2 baseline \| `FBES1-ALW-D0-S2` \| 1" | NO |
| SPEC_PB1_ES r3 `445f7499…` | §8 G7 | "arm vượt C2 và C1 về after-cost expectancy tại S2 (không vượt ⇒ 'no conditioning information')" — the FROZEN ROLE | NO (role only) |
| PLAYBOOKS_DRAFT r5 `7610ed3c…` | §1 control row (L76) | "(C2) always-in-RTH baseline — **CÓ PnL path ⇒ scored identity**" | NO |
| PLAYBOOKS_DRAFT r5 `7610ed3c…` | identity row (L87) | "C2 always-in-RTH baseline \| **CÓ** \| tier 2, cùng folds \| 1" | NO |
| ES_DEEPFOUR_V3_ADDENDUM `d18d5422…` | §9 (L282, L334-335) | "C2 always-in-RTH + … = 4"; "**C2** always-in-RTH baseline (D0/S2, scored)" | NO |
| CYCLE_LAUNCH_DRAFT `bc2b6488…` | §5 (L176-179) | "**C2 always-on control** (signal ignored; an arm that does not beat C2 after cost ⇒ 'no conditioning information')" — the census role wording | NO (role only) |
| identity_table_24.json `6e391980…` | C2 row | "C2 baseline (always-on)" | NO |
| ESNQ_HYPOTHESES `9f9176e5…` | §6 (L192, sibling family F1) | "C2 always-in-RTH on event days" | NO |

Nearest direction-adjacent text in the whole corpus — and why it is NOT a
ruling: HYPOTHESES_ESNQ_R3 `9dfe7b12…` §4 veto row V10 (L423) says a rejected
pre-holiday candidate is "confounded with the always-on C2 baseline (calendar
long = clock family)". That phrase describes the *vetoed candidate* (a calendar
long); it presupposes overlap-with-C2 as the veto ground and pins no C2
direction law. Recorded here for completeness; **prior authority on D-A2:
NOT_FOUND.**

### 2.2 What prior law already constrains (do not amend)

- C2 is exactly `FBES1-ALW-D0-S2`, 1 scored identity with its own PnL path
  (PLAYBOOKS L76/L87; SPEC §6).
- Config: tier 2, same folds as primary (PLAYBOOKS L87).
- Role: the "no conditioning information" bar — an arm that does not beat C2
  (and C1) on after-cost expectancy at S2 gets that verdict (SPEC §8 G7;
  CYCLE_LAUNCH §5 "signal ignored").
- C2 must stay **distinct from C4** (`FBES1-DOSE-D0-S2` = sign(m) EVERY day,
  D0, tier 2 — PLAYBOOKS L76/L89). This is what makes "side-of-signal"
  inadmissible below.

### 2.3 Admissible option space (design-merit only)

| option | one-line consequence | identity table |
|---|---|---|
| (a) Unconditional LONG every RTH session, D0 fill, hold to era-correct close, no TP/SL (dry-run recorded) | the conventional "always-in" reading: pure market-exposure baseline carrying structural drift on the long side; deterministic | unchanged (24) |
| (b) Unconditional SHORT (same machinery, −1 sign) | measures the short-exposure baseline instead; equally role-preserving and deterministic; changes only which benchmark path G7 compares against | unchanged (24) |
| (c) Deterministic alternating side (e.g., parity of session index in the eval set) | drift-neutral exposure baseline; introduces a side-scheduling rule absent from every law text — a NEW design element, larger than a reading of "always-in" | unchanged (24) |
| (d) side-of-signal (enter sign(m) every day) | **INADMISSIBLE** — byte-level collapse into C4 dose-response (same entry clock, same rule, same tier/folds), voiding C2's independence and effectively deleting one control from the frozen design; a freeze amendment masquerading as a pin | VIOLATES the 24-table semantics ⇒ excluded |

Constraint compliance of the recorded default: option (a) satisfies every
frozen C2 constraint (1 identity; tier 2; same folds; own PnL path; distinct
from C4; role intact). No law text contradicts it; no law text selects it.

### 2.4 Decision text for the owner (no pre-selection)

> **D-A2**: "C2 `FBES1-ALW-D0-S2` holds direction ______ every scored RTH
> session (option a/b/c: long-only / short-only / deterministic alternating),
> D0 fill, hold to era-correct close, no TP/SL — keeping the frozen role
> (SPEC §8 G7 'no conditioning information' bar; PLAYBOOKS L76/L87 config).
> The dry-run's recorded long-only reading is the default currently recorded
> in rehearsal machinery — not yet law."

## 3. D-A3 — C1 placebo RNG algorithm

### 3.1 Prior-authority hunt — what is ALREADY FROZEN

The C1 placebo's seed law is one of the most-repeated frozen items in the
corpus. These elements are law and are NOT open:

| frozen element | authority (sha256, prefix) | quote |
|---|---|---|
| Seed value **20261002** | SPEC_PB1_ES r3 `445f7499…` §6 L127 | "C1 placebo \| `FBES1-PLA-D0-S2` (seed 20261002; đơn seed đơn delay …)" |
| Deterministic per-session sign draw | PLAYBOOKS_DRAFT r5 `7610ed3c…` L76 | "(seed cố định 20261002, sign-draw deterministic theo session)" |
| Single seed, single delay — published limitation, no permutation-robustness claim | PLAYBOOKS L76 + L95; ES_DEEPFOUR_V3_ADDENDUM `d18d5422…` §9 L348 ("A-r4's single-seed C1 (20261002, single delay) is a published [limitation]"); SHORTLIST_6SYM `1a6f56a7…` PB1 row | "giới hạn công bố — không claim permutation robustness" |
| Config: delay 0, tier 2, same fold/session set as primary, no arm/tail | PLAYBOOKS L86 | "seed 20261002, delay 0, tier 2, cùng fold/session set với primary; không áp arm/tail (hướng random)" |
| Identity id `FBES1-PLA-D0-S2` | identity_table_24 `6e391980…`; A7_PRELAUNCH Check 2 | — |

### 3.2 Prior-authority hunt — the ALGORITHM: NOT_FOUND

- No authority names a PRNG or a seed→sign map. PLAYBOOKS L76 stops at
  "sign-draw deterministic theo session"; SPEC §6 stops at the seed.
- Sibling-family convention confirms the gap is structural, not an oversight:
  FOMC-presser F1 (esnq_hypotheses.json, FUTURES-OVERNIGHT-PREP) reuses
  "C1-C4 pattern (new disclosed seed)" with "single-seed placebo limitation
  inherited"; run-family NC-4b "sign-shuffled run labels (own seed)" —
  convention = "disclosed seed", never "disclosed algorithm".
- SIX-SCORED-GATE-PREP: "placebo ≥100-seed ruling slot (CENSUS §5, still
  EMPTY)" — an owner slot about multi-seed *expansion* for future families,
  orthogonal to PB1's single-seed algorithm; confirms this register never
  carried a PB1 algorithm ruling.
- DAILY-EXPLORATORY-V1 (TERMINAL, forex, `e1872377…`): its A7 terminal audit
  records a "C2 clock-shadow random-dwell control" that was **NOT executed**
  and names no PRNG — no precedent.
- ECONOMIC-ROBUSTNESS-PROGRAM-V1 cohort lanes: "wide-mirror/ungated/shuffle
  causal controls", "sign-shuffle" — no named PRNG algorithm anywhere.
- sweep keywords: `random.?sign|sign.?draw|sign.?shuffle|PRNG|np\.random|
  default_rng|MT19937|PCG|hashlib` across `research/` + `plans/` — zero
  algorithm-pinning hit tied to any placebo seed.

**Prior authority on the D-A3 algorithm: NOT_FOUND. Classification:
OWNER_RATIFICATION_REQUIRED** — but scoped: the ratification covers ONLY the
seed→sign map; the seed law above is frozen and any option outside it
(different seed, multi-seed, non-deterministic draw) is out of bounds without
a freeze amendment.

### 3.3 Admissible option space (design-merit only; all embed seed 20261002, per-session deterministic, ±1)

| option | one-line consequence | reproducibility character | identity table |
|---|---|---|---|
| (a) Stateless cryptographic hash draw (dry-run recorded): `sign=+1 iff sha256("FBES1-PLA-D0-S2|seed=20261002|"+date)[0] < 0x80` | per-session uniform ±1; draw is a pure function of (id, frozen seed, date) | **law-text-complete**: no library state, no consumption order, no version pin needed | unchanged (24) |
| (b) Versioned PRNG stream (e.g., numpy PCG64 seeded 20261002, consumed in session order) | per-session draws from a seeded stream | requires pinning library version + enumeration order + stream-position discipline; more fragile across environments/rewrites | unchanged (24) |
| (c) Legacy PRNG stream (e.g., MT19937 via RandomState) | same as (b) with the legacy generator | same fragility class as (b) | unchanged (24) |
| (d) Arithmetic per-session hash (LCG/modular family) | deterministic and stateless like (a) but with weaker uniformity guarantees | law-text-complete but lower-quality randomness | unchanged (24) |

Constraint compliance of the recorded default: option (a) satisfies every
frozen C1 constraint (seed embedded verbatim; deterministic per session;
single draw/session; tier 2, D0, same session set). No law text contradicts
it; no law text selects it.

### 3.4 Decision text for the owner (no pre-selection)

> **D-A3**: "The C1 `FBES1-PLA-D0-S2` sign draw maps the FROZEN seed 20261002
> to a per-session ±1 via ______ (option a/b/c/d: sha256 hash draw / PCG64
> stream / MT19937 stream / arithmetic hash), under the frozen constraints
> (single seed, single delay, deterministic per session, tier 2, same
> fold/session set — PLAYBOOKS L76/L86; SPEC §6). The dry-run's recorded
> sha256 draw is the default currently recorded in rehearsal machinery —
> not yet law."

## 4. Consistency statement (M4) — the 24-identity enumeration is invariant

Under **every admissible option** of all three pins:

- D-A1 changes only threshold arithmetic inside the already-frozen q80
  condition; the 24 (id, arm, config) cells are untouched (only trade
  membership within primaries/FOMCIN can move).
- D-A2 changes only the sign/schedule of C2's single path; `FBES1-ALW-D0-S2`
  remains 1 identity with tier 2 and the same folds.
- D-A3 changes only the sign sequence of C1's single path;
  `FBES1-PLA-D0-S2` remains 1 identity (seed/config frozen).

Enumeration stays exactly the SPEC §6 A-r4 24 (P-A 8 + P-B 8 + FOMC 4 +
C1-C4 4; identity_table_24.json sha `6e391980…` byte-exact; A7 Check 2
PASS at `a33978b7` remains valid). The single option that WOULD disturb the
design — C2 side-of-signal collapsing into C4 — is excluded at §2.3 as
design-inadmissible; no freeze amendment is required for any admissible
option. **CRITICAL flag count: 0.**

Process consequence (not a deviation): if the owner ratifies any option
DIFFERENT from the dry-run's recorded default, the rehearsal machinery's
parameter must be amended and gate 4's determinism evidence re-generated at
the new builder sha before gate 6 (the dry-run is descriptive-only and
nothing scored consumed it, so this is a conditional re-run obligation, not
a CRITICAL finding). If the owner ratifies exactly the recorded defaults, no
re-run is needed.

## 5. Discipline record

- ONE bare `git -C <worktree> rev-parse HEAD` at start →
  `8324a8c0e414fb683d9bfa6f56734d0a17b9d40a` (matches dispatch SHA).
  `git status --porcelain` EMPTY at start (all read artifacts committed).
- One read-only `git show` history check (recorded): `git show
  HEAD:{SPEC_PB1_ES.md, DRYRUN_REPORT.md, dryrun_builder.py}` sha256s match
  worktree bytes (445f7499…, 97a4ff6a…, 867946f3…). No other git command.
- No commit/stage/push. Write boundary honored:
  `research/control/FUTURES-ES-PB1-V1/pins/**` +
  `research/control/FUTURES-ES-PB1-V1/dispatch/handoff_PIN-ADJUDICATION.json`.
- Root repo read-only (PLAN_futures_es_pb1_v1.md read, never written).
  Zero network. Root .venv untouched (no computation beyond sha256 hashing).
- Quarantine law: zero reads of `dryrun/quarantine*/**` trade numerics; the
  only dry-run artifacts read were DRYRUN_REPORT.md (pin declarations and
  findings text) and dryrun_builder.py (the recorded pin implementations —
  machinery text, not rehearsal output numbers). No option in this packet is
  justified by any rehearsal outcome.

— End PIN_DECISION_PACKET.
