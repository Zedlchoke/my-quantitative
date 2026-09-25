# A7_tracka1_plan_audit_REPORT — independent fresh-context plan audit of ERP1-TRACKA-COHORT-1 (DRAFT)

- Auditor: A7, independent fresh context (quant-auditor). Read-only except this
  report and `HANDOFF_tracka1_a7_plan_audit.json`. No commits, no registry
  writes, no downloads, no backtests, no PnL computation, no touch of any
  running worker (FX-RANGEFADE-2M-SHADOW-V1 daemon source read statically
  only; process PID 79157 verified alive and untouched).
- Audited object: `plans/DRAFT_ERP1_TRACKA_COHORT_1.md` (DRAFT_FOR_OWNER_GO;
  registers nothing, executes nothing — re-verified: `grep TRACKA
  plans/CYCLE_REGISTRY.json` = 0 hits, 68 registered cycles scanned).
- Measured base: root `main` @ `69ddc60447d223249319f82b71b21e26ab941203`
  (`git rev-parse HEAD`, measured 2026-09-25; matches the draft's §2 snapshot
  and all three council lanes' recorded base).
- Live-state re-measure at audit time: heavy lock `FREE_PROVEN`
  (`research/researchctl.py locks inspect`); daemon PID 79157 alive;
  orchestrator v3 events idle (last `2026-09-19T00:32:40Z`,
  `ZCODE-ORCHESTRATION-V3 TASK_DISPATCHED`); umbrella
  `ECONOMIC-ROBUSTNESS-PROGRAM-V1` ACTIVE_LIGHT budget 0/0;
  `FX-RANGEFADE-2M-SHADOW-V1` ACTIVE_LIGHT workers=2; `EURUSD-DATA-
  QUALIFICATION-V1` BLOCKED (`BLOCKED_SOURCE_LICENSE` verified in
  `.worktrees/eurusd-data-qualification-v1/integration/research/control/
  eurusd_data_qualification_v1/CYCLE_VERDICT.md`). All consistent with the
  draft's §0/§2/§5.1 claims.

## VERDICT: PASS_WITH_CONDITIONS

The draft is internally coherent, faithfully inherits the umbrella law set,
correctly reports the code-authority facts (independently re-verified line by
line), ran a genuinely outcome-blind council whose D2 veto was applied as
written, and closes every false-PROMOTE path this audit hunted. Four
integration gaps remain (F1–F4, all MEDIUM). None is gate-leaky by itself, but
each is a binding pre-GO-1 item because three of them are cheap to close now
and expensive (or irreversible) to close later. No CRITICAL or HIGH defect
found.

---

## A. Umbrella inheritance — recompute results (all PASS unless noted)

| Umbrella element | Draft location | Verdict |
|---|---|---|
| §5.1 council composition + outcome-blindness law | §7.1; three signed lane disclosures (EXPLORER §5, SKEPTIC §7 + header, DATACOST §0) | Blindness PASS. **Composition gap: umbrella's "plus blind proposers" element omitted — F1 (MEDIUM)** |
| §5.2 ≤3 mechanisms | §7.2, appendix A.2 (M1+M2+M3; M2 vetoed at D2 → 2 frozen; slot dead, not banked) | PASS |
| §5.3 10-field proposal format + six-question frame | §7.3 (all 10 fields enumerated; six questions present); explorer fields 1–10 per mechanism | PASS |
| §5.4 Track A five binding conditions VERBATIM | §6 items 1–5 | PASS — all five present, none weakened; 2/4/5 tightened (unit-tested fixtures, fill-bar charging precision, PAYS-the-spread wording law). FOREX-NG8-closed and paper-tier cap carried verbatim |
| §5.5 pre-PnL falsification battery | §8 F-1..F-7 (ancestry rho, clock-placebo must MOVE with non-vacuity predicates, inverted runnable, DST/release geometry + S6 no-drift, F-6 nearest-window feasibility, F-5 cost ceiling) | PASS (F-5 source ambiguity → F4) |
| §5.6 child creation law, own GO, no pre-filled GO | §0 GO-1/GO-2 typed fresh at own gates; registration only via `researchctl` after owner GO | PASS |
| §5.7 trial freeze arm structure 1 anchor / ≤2 neighbours / 1 causal / 1 inverted / 1 baseline | §7.2 + A.2: M1 = R-ANCHOR; R-ORIG+R-NEIGH (2 neighbours); clock-placebo; inverted; baseline set = 6. M3 = anchor; N1+N2; spread-WIDE complement; inverted; baseline set = 6 | PASS (baseline "set" = FLAT + SHORT/LONG_ALWAYS counted as one composite arm is a stricter instantiation; the SHORT/LONG arms are the umbrella-mandated short-beta controls, C-FX-1 class) |
| §5.8 observed/published denominators | §0, §10; holdout looks count in observed (§9.1) | PASS |
| §5.9 chronological folds + no substitution | §9.1 (dev 2021-01-01..2025-12-31; holdout 2026-01-01..2026-06-30; F1..F6 chronological non-overlapping; force-flat at boundaries; no fold-window substitution after any PnL) | PASS |
| §5.10 S1 sealed | §0 `SEALED_UNTOUCHED`; §9.3 "never S1, never live" | PASS |
| §5.11 reproduction + fresh A7 | §11 (A7 fresh-context prelaunch before GO-2, terminal at close); §9.3 "reproduction exact" | PASS |
| §5.12 decision-count gates | N/A for a scored cohort (no shadow sleeve in this cycle); sub-power positives = `NOT_POWERED_CANDIDATE` consistent with "sub-power positives are INCONCLUSIVE, never PASS" | PASS (N/A noted) |
| §5.13 PROMOTE/KILL/TIME-STOP preregistered | §9.3 (exact inequality sets; TIME-STOP freeze+60 days → `BLOCKED_*` honest closure) | PASS |
| §5.14 evidence floors ≥ (never below) | G5 keeps ≥100 RT AND ≥6 months; G4 net>0 @×1.5 (stricter than umbrella non-negative); ×1.5/×2.0 both reported; G3 ≥4/6 folds; G6/G7/G8 ≤50%; DSR + PBO NOT_RUN fail-closed; baseline beaten + control not reproducing | PASS (smoke-floor-30 remark → F9 LOW) |
| §9 verdict vocabulary | §11 adopts umbrella §9 paper-tier bound; specializations (`NOT_SCORED_FALSIFIED`, `KILL_*`, `NOT_POWERED_CANDIDATE`) never grant more than paper-tier | PASS |
| §6 ancestry rho ≤0.20 + class vetoes | §3.4/F-1: pooled \|rho\| ≤ 0.20 vs `research/wayfinder/FAMILY_FAILURES.jsonl` + the exact six class vetoes, "umbrella §6, immovable" | PASS (representation-law pin missing → F2) |
| §7 PIT/license/timestamps | §5.1 license posture (`OWNER_DIRECTIVE_SOURCE_AUTHORIZATION` + `TCU_RISK_DISCLOSED`; EDQ1 `BLOCKED_SOURCE_LICENSE` on record, not re-litigated; three owner unblock paths); six-question Q4 separates event/effective/available | PASS |
| §8 measured-cost contract + FX ×2.0 frozen | §6 (measured components only; declared fee buffer verbatim no-number line; ×2.0 per-regime frozen pre-outcome; ×1.5/×2.0 reported; fill-bar charging spec; census-vs-executor reconcile) | PASS |

## B. Internal consistency — recomputed

- **Budget arithmetic: CORRECT.** Cap 24 = Task 1: 2 pairs × 6 arms = 12
  (R-ANCHOR, R-ORIG, R-NEIGH, causal, inverted, baseline-set-composite) +
  Task 2: 2 × 6 × 1 home pair = 12. Effective after the D2 veto of M2 =
  12 + 6 = 18 (M3 = anchor + N1 + N2 + causal + inverted + baseline = 6 on
  USDCAD only). §0 and §10 agree; holdout looks ledgered, not extra cells;
  TECHABORT re-runs consume observed budget.
- **Arm structure per mechanism matches §5.7 exactly** (see table above).
- **Fold/holdout windows consistent** across §3.3, §5.1, §5.2, §9.1
  (corpora 2021-01..2026-06; dev through 2025-12-31; holdout 2026-01..06-30;
  one look; new-pair holdout verified untouched against the registry before
  freeze; the shadow worktree's 2026-09-23 bridge is not in the cohort's
  download window).
- **Seam law (§9.4) mathematically well-defined**: book tier pinned (×1.0
  base); sign convention consistent (all three kill clauses fire when
  R-ORIG outperforms); `c_rt` logged with its actual number at freeze;
  `N_diff` computable pre-PnL from signal arrays. Units of `S` vs `c_rt` not
  explicitly named (engine books pips) and the (iii) "matched trips" pairing
  rule is implicit — **F8 (LOW)**.
- **Power coherence: RESOLVED correctly.** G5 floor ≥100 RT (umbrella floor
  preserved, never lowered); G2 PF ≥ 1.20; PROMOTE additionally requires
  ≥236 RT on union of dev folds OR preregistered bootstrap CI on PF
  excluding 1.0 at frozen seed; below that `NOT_POWERED_CANDIDATE` (never
  PROMOTE). The G2-at-n=100 draw-luck hole the skeptic identified is closed.
- **Kill bands coherent**: causal 0.5× + fold-residue clause; beta-kill ≤0
  and <0.5× margin; inversion ≥anchor + shadow-wins clause; G8
  hour-concentration ≤50%; no-vacuity predicates on F-3 and M3's complement
  control. TIME-STOP 60 days present.
- **Phase-0 snapshot claims re-measured TRUE** (lock FREE_PROVEN, PID 79157,
  orchestrator idle 2026-09-19, child absent from registry).

## C. Code-authority verification (fresh static read at the audit HEAD; worktree sources byte-read)

| Draft/skeptic claim | Fresh verification | Verdict |
|---|---|---|
| `f_rangeexp` at `v2_lib.py:265` | `def f_rangeexp(p, lo_q, hi_q, use_breakout):` at line 265 | **CONFIRMED** |
| `_prev_day_stats` `:66-79` accumulates day-d full-day highs/lows | def at :66, docstring "PIT helper" at :67, `hi[d]=max/lo[d]=min` over every non-skipped bar, return at :79 | **CONFIRMED** |
| `ranges[d][0]` = day d's OWN full-day range `:271` | `ranges[d] = (hi[d] - lo[d], hi[days[j-1]], lo[days[j-1]])` at :271 | **CONFIRMED** |
| `pct[d]` from own range, hist PIT-ordered `:274-281` | `pct[d] = float(np.searchsorted(sorted(hist), ranges[d][0]) / len(hist))` at :278; `hist.append` :279 AFTER the query; cap 60 :280-281 | **CONFIRMED** (only the query value leaks) |
| Consumed at day-d first bar `:291-301` | `if d != cur_day:` :291 → mode set from `pct[d]` :293-297; levels :298-299; else flat :300-301. Mode decided at 00:00 UTC from a range that completes ~20:00 UTC; first fill hour ≥7 (`fill_ok = tradable & (hour <= 18)`, H1Plane) | **CONFIRMED** |
| `pct>0` guard `:293` | `if d in pct and pct[d] > 0:` at line 293 | **CONFIRMED** |
| Deployed mapping (0.3, 0.7, False): pct==0→flat; 0<pct≤0.7→FADE; pct>0.7→FOLLOW | :297 `expand = narrow if use_breakout else wide` → expand=(pct>0.7); expand=True → breakout branch :305-310 (break above prev-high → long); expand=False → fade branch :311-320 (break above → short; middle-quarter exit :319-320) | **CONFIRMED** |
| Line `:296` dead code | `expand = narrow if use_breakout else (wide if not narrow else False)` at :296, overwritten by :297; values coincide under both flag settings (narrow ⇒ ¬wide at 0.3/0.7) | **CONFIRMED** (no behavior impact) |
| Daemon growing-panel partial-range mode `:225-228, 277-288` | `targets_from_df` calls `V.f_rangeexp(plane, 0.3, 0.7, False)` on the current panel at :225-228; `on_closed_bar` appends the closed bar and recomputes on the growing panel, consuming `tgt[-1]` (:280-283); `desired_now` :290-298 supplies it to the just-opened bar (≡ engine `want = target[i-1]`) | **CONFIRMED** — running partial-range percentile is a third law, PIT-legal in itself |
| Parity self-test same-function-same-panel blindness `:515-525`; `:284` hard-codes PASS | Self-test at :515-525 compares `targets_from_df(b.df)` vs `V.f_rangeexp(plane_from_df(b.df), 0.3, 0.7, False)` — both sides on `b.df`; structurally unable to see full-panel divergence. `self.parity = "PASS"` at :284, cosmetic | **CONFIRMED** |
| Engine signal shift | `want = int(target[i - 1])` at **engine.py:108** (skeptic cited :97-100 — line imprecision, substance right → F7) | **CONFIRMED** (corrected line) |
| Blocking port defect: `build_bars.py` hard-codes `PIP=1e-4`, EURUSD band `0.80<bid<1.35`; `engine.py` hard-codes `PIP=1e4` | `PIP = 1e-4` build_bars.py:32; band at :8/:75/:79; scale literal `o / 1e5` at :47 (the draft's "PRICE_SCALE=1e5" is a paraphrase of this literal — F7); `PIP = 1e4` engine.py:26 | **CONFIRMED** in substance |
| Spread fields only at `v2_lib.py:27-28`, no family consumes them | `df["s_open"]`/`df["s_close"]` at :27-28 (H1Plane constructor); no family function references them | **CONFIRMED** |

The draft's §4.2 council verdict is accurate in every particular, including
the two skeptic refinements (searchsorted-left tie rule; guard-shift
statement) and the D2.3 erratum pin. **No prose-vs-code inversion survives in
the draft as amended**: §4.1's prose ("in the not-extremely-wide regime, fade
breaks") matches the code; the voided §4.2 parenthetical is explicitly
voided by the code-authority clause.

## D. Council-process integrity

- **Signed outcome-blindness disclosures**: all three reports carry them
  (EXPLORER §5 signed block; SKEPTIC header + §7 signed block; DATACOST §0).
- **No outcome numbers**: scanned all three reports — no PnL, PF, win-rate,
  trade-count or adjudication result of any scored/shadow surface. DATACOST's
  numbers are data/cost facts (spread quantiles, file counts, gates) — the
  permitted class. Explorer cites two rho values from
  `FAMILY_FAILURES.jsonl` (0.3988, 0.997–1.000) — that ledger is the
  mandated F-1/§6 gate input (dead-family failure memory), not a banned
  outcome surface; class-consistent.
- **D2 veto of M2 applied V-4 as written**: the adjudication explicitly
  refuses the explorer's narrowing ("not an indicator blend *on one series*"
  adds a restriction V-4 does not contain); cross-pair gating of two
  PDHLOC-class ancestry observables is the enumerated V-4 form. Co-vetoes
  V-1/§7.4 recorded; disposition `NOT_SCORED_FALSIFIED`, slot closed, no
  reassignment/repair loop. **No loosening found.**
- **M3 admission conditions pre-registered and binding pre-PnL**: armed V-1
  rho>0.60 fixture (target-array representation), T-1 session-collapse
  tripwire (≥80% of gate-open bars in one ≤6h UTC window ⇒ V-3), T-2
  just-closed-bar PIT fixture, T-3 ≥2% mutation non-vacuity, F-5 arithmetic
  kill pre-declared (measured USDCAD stress RT ≥2.0 pips ⇒ forced kill),
  G8 + occupancy-matched F-3. All are kill conditions; none grants M3 any
  evidentiary slack. The D2 interpretation step is inherently post-slate;
  with zero PnL in existence anywhere, no outcome bias was possible, and the
  conditions bias against M3, not for it.
- **No mid-cohort replacement loophole**: §9.3 KILL "No replacement proposal
  enters mid-cohort"; skeptic D2.4 "the unused Task-2 slot is dead, not
  banked"; M2's veto text forecloses repair ("a cross-pair gate on a
  NON-ancestry observable may be a future-cohort proposal").
- **No outcome-exposure path for the proposer**: explorer's read set (draft,
  registry lifecycle fields, family ledger, EDQ1 license facts, code
  structure) contains no candidate-mechanism outcome; the only outcomes in
  the program are ancestry dead families, which are the mandated gate input.
  Council ran entirely pre-PnL (nothing has ever been scored in this cycle),
  so blindness was structurally enforceable, not just promised.

## E. Ordering law

- §8: "data/PIT/cost audit and falsification run to completion BEFORE any
  PnL-bearing computation anywhere in the cycle"; F-PIT-1 freezes verdict +
  seam constants before the first PnL-bearing cell of ANY arm; data gate per
  pair before any outcome (§5.2); M-2 re-derivation bounded to one pre-PnL
  registered amendment inheriting the consumed look.
- No section contradicts the law with one exception: **F-5's "expected gross
  premium per holding period ... evaluated on the F-6 recent window" is
  ambiguous** between declared-hypothesis-band arithmetic (the reading the
  skeptic's D2.2 condition 5 forces) and a measured gross-expectancy
  backtest, which would itself be PnL-bearing executed before F-PIT-1
  freezes — **F4 (MEDIUM)**.
- F-3's control averages (entries/day, hours, holding duration) are
  signal-array quantities computable pre-PnL; R-DAEMON emulation is
  signal-level only. No other ordering violation found.

## F. GO law

- Two GO phrases (§0), each scoped, each "typed fresh" at its own gate;
  GO-2 additionally conditioned on A7 prelaunch PASS. The draft does not
  pre-consume GO-2 and registers/executes nothing (registry grep 0; ledger
  path not created).
- Boundaries vs the running FX shadow worker explicit three times (§0 shadow
  line, §2 Phase-0, owner decision D-D) plus the read-only-citation rule;
  this audit independently confirmed the daemon alive and untouched.

## G. Leak hunt (residual paths from weak positive to PROMOTE)

Closed paths verified: holdout control clause (§9.3); G8 hour concentration
with three-level exclusion zones (§9.2); DSR across full cohort history + PBO
NOT_RUN fail-closed (§9.3, §10); `SINGLE_SOURCE_PANEL` and
`FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK` mandatory labels + the full wording
ban list (§6); R-NEIGH never supports or flips any verdict (§4.2, skeptic
plug 3); M-2 re-derivation bounded once pre-PnL; pair substitution requires
owner amendment and is forbidden after any signal exists on the slate
(§9.3 TIME-STOP + A.1 spare rule); R-ORIG never selectable regardless of
outcome (§4.2, §9.4); holdout consumed only by dev-passing arms, one look,
failure final (§9.1); bootstrap alternative preregistered at frozen seed
(§9.3); unfundable-arm veto (§6). Residuals:

- **F3 (MEDIUM)**: §9.1 admits to the holdout any arm "that passed all dev
  gates". R-ORIG — a never-selectable diagnostic — can pass dev gates and
  consume the pair's one look; and nothing states that a mechanism killed at
  dev (e.g. `KILL_PIT_SEAM`, `KILL_CONTROL_REPRODUCED`) forfeits its
  remaining holdout looks. A consumed look is irreversible: the outcome-free
  window is this program's scarcest resource.
- **F2 (MEDIUM)**: F-1 lacks the skeptic's representation law (pooled |rho|
  on the exact scored target-array representation, frozen variant set,
  computed by the skeptic lane — proposer-friendly representations void).
  M3's pairwise V-1 fixture pins a representation only against R-ANCHOR.
- **F4 (MEDIUM)**: F-5 source ambiguity (see E).
- **F1 (MEDIUM)**: council composition gap (see A).
- LOW residuals: F5 (stale ancestry-disclosure item: draft §3.2 says the
  shadow journal has "no fee/slippage fields yet — amendment A1 pending its
  own GO"; the registry's latest write token records "Amendment A1 controls
  ACTIVATED T_ctrl=2026-09-25T05:35:03Z" — re-measure the disclosure at the
  child's own intake and correct at registration), F6 (explorer claims 127
  ledger entries; measured 126), F7 (citation imprecisions: engine.py:108
  not :97-100; `PRICE_SCALE=1e5` is the literal `o / 1e5` at
  build_bars.py:47), F8 (seam units + matched-trip pairing to be named at
  freeze), F9 (smoke floor 30 has no umbrella FX-intraday counterpart —
  harmless: G5 ≥100 and the 236-RT promote gate are preserved), F10 (Track A
  literal "replication targets EURUSD/GBPUSD/USDJPY" is re-scoped to new
  pairs only — the only reading compatible with the outcome-exposure and
  one-look laws; ratify explicitly in the owner packet under D-B), F11 (the
  council ran pre-registration under umbrella light authority and is frozen
  as appendix A — lawful drafting support per umbrella §2.2, hashes
  re-verified at GO-1; recorded, no action).

## Findings register

| ID | Severity | Finding | Evidence | Required disposition |
|---|---|---|---|---|
| F1 | MEDIUM | Umbrella §5.1 composition element "plus blind proposers" omitted; explorer is sole proposer; omission not disclosed as a deviation | umbrella plan :343-346 vs draft :346-354 | Owner ratifies the 3-lane composition in the D-A decision packet before GO-1 (blindness was maintained and signed; this is a composition-form deviation, not a blindness breach) |
| F2 | MEDIUM | F-1 representation law not integrated into the plan text | SKEPTIC report §2 F-1 bullet; draft :402-403 (F-1 terse); appendix A.3 integrated list :664-671 lacks it | Pin in the plan pre-GO-1: pooled \|rho\| computed on the exact scored target-array representation, frozen variant set, by the skeptic lane; proposer-computed rho void |
| F3 | MEDIUM | Holdout-consumption scope open to never-selectable (R-ORIG) and dev-killed arms; irreversible burn of outcome-free windows | draft :474-477 (§9.1) | Pin pre-GO-1: arms of mechanisms dead at dev take no holdout look; R-ORIG takes none in any case |
| F4 | MEDIUM | F-5 "expected gross premium ... evaluated on the recent window" ambiguous between declared-band arithmetic and a measured gross backtest (the latter would breach the §8 ordering law pre-PIT-freeze) | draft :446-451; ordering law :459-463; SKEPTIC D2.2 cond. 5 :170 | Pin pre-GO-1: F-5 = declared hypothesis band vs measured ×2.0-stressed conditional cost, arithmetic only; no gross-expectancy backtest before F-PIT-1 freezes |
| F5 | LOW | Ancestry-disclosure item may be stale (shadow amendment A1 activation in registry write token vs draft "pending its own GO") | draft :120; `plans/CYCLE_REGISTRY.json` write_token + `updated_at_utc` 2026-09-25T05:36:15Z | Re-measure at the child's own intake; correct the disclosure block at registration |
| F6 | LOW | Explorer authority claim "127 entries" vs measured 126 JSONL entries | EXPLORER :43, handoff authority_claims; `wc`/parse of `research/wayfinder/FAMILY_FAILURES.jsonl` | Correct the count in the registration packet; no gate impact |
| F7 | LOW | Line-citation imprecisions (engine.py:108 not :97-100; `PRICE_SCALE=1e5` is the literal `o / 1e5` at build_bars.py:47) | SKEPTIC :28; engine.py:108; build_bars.py:47 | Record corrected line numbers in the freeze's semantic-diff table |
| F8 | LOW | Seam-law units not named (pips vs USD) and (iii) matched-trip pairing rule implicit | draft :527-536 | Name the unit (engine books pips) and the pairing rule at freeze alongside `c_rt` |
| F9 | LOW | Smoke floor 30 (eligibility only) has no umbrella FX-intraday counterpart | draft :483-484 vs umbrella §5.14 | Record as child specialization; adjudication floor ≥100 and promote gate ≥236 preserved (fail-safe as written) |
| F10 | LOW | Track A literal replication targets (EURUSD/GBPUSD/USDJPY) re-scoped to new pairs only | umbrella :413-414 vs draft §3.3/§1.1 | Acknowledge the re-scope explicitly in the owner packet (D-B); it is the only reading compatible with the outcome-exposure and one-look laws |
| F11 | LOW | Council ran pre-registration under umbrella light authority; slate frozen as appendix A, hash-verified at GO-1 | draft :353-355, :579-587; umbrella §2.2 | No action; recorded for the owner's D-A file |

## Binding pre-GO-1 conditions (from the MEDIUM findings)

1. **C1 (=F1):** Owner decision packet (D-A) explicitly ratifies the
   three-lane council composition as the cohort's specialization of umbrella
   §5.1, or adds blind proposers. No GO-1 without it.
2. **C2 (=F2):** Plan text pins the F-1 representation law (scored
   target-array representation, frozen variant set, skeptic-lane-computed)
   before GO-1.
3. **C3 (=F3):** Plan text pins holdout-consumption scope: mechanisms dead at
   dev (including seam and control kills) take no holdout look; R-ORIG never
   takes one. Before GO-1.
4. **C4 (=F4):** Plan text pins F-5 as declared-band-vs-measured-cost
   arithmetic, with an explicit no-gross-backtest-before-F-PIT-1-freeze
   clause. Before GO-1.

LOW items F5–F10 are recorded dispositions, not GO blockers; F5's
re-measurement is already mandated by the draft's own intake law and this
audit's registry observation makes it concretely due at registration.

— A7 quant-auditor, tracka-cohort1-a7, 2026-09-25, at root main
`69ddc60447d223249319f82b71b21e26ab941203`. Fresh context: this lane read no
other A7 artifact of any cycle and no ancestry outcome file beyond the
permitted set.

---

## ROUND 2 — DELTA REVIEW

Second-session delta audit, 2026-09-25, fresh re-measurement: root `main` @
`69ddc60447d223249319f82b71b21e26ab941203` (unchanged from round 1 — no lane
committed; last commit remains the pre-existing 2026-09-25T05:36Z registry
landing). Re-verified live: registry grep `TRACKA` = 0 (still unregistered);
heavy lock `FREE_PROVEN`; FX daemon PID 79157 alive, untouched. Full detail in
`A7_tracka1_delta_review_REPORT.md` (the round-2 authority).

**Round-1 conditions — all four verifiably IN the current plan text:**

- **C1 (F1) RESOLVED.** §7.1 records composition completed per owner decision
  D-E: blind proposer lanes P1+P2 ran under the same blindness law; owner's
  binding law "NO additional mechanism slots, M2 stays dead" is in §7.1 and
  §11; proposals recorded as FUTURE-COHORT candidates only (A.3, with the
  RECLAIM-ABSORB vs explorer retest-class self-veto cross-lane tension
  explicitly flagged for a future D2). PROPOSER1/PROPOSER2 reports + handoffs:
  schema `zcode_orch_v3_handoff@1`, signed outcome-blindness disclosures,
  zero outcome numbers (all figures are declared bands / clock arithmetic /
  plan-internal citations / failure-class labels), zero slot claims, lanes
  mutually independent (each read no other lane's output).
- **C2 (F2) RESOLVED.** F-1 (§8) now carries the representation law verbatim
  in strength: pooled |rho| ≤ 0.20 on the EXACT scored target-array
  representation, frozen variant set, BY THE SKEPTIC LANE, proposer-computed
  rho void.
- **C3 (F3) RESOLVED and extended.** §9.1 one-look law: holdout consumed by
  EXACTLY ONE preregistered evaluation PASS with frozen membership; anchor
  arms only; R-ORIG/R-NEIGH and all dev-killed mechanisms take NO look;
  extended per proposer P2 — causal, INVERTED and baseline books are
  companions computed in the same single pass (closing the inversion-on-
  holdout hole P2 found) at zero additional look cost. Strictly strengthens.
- **C4 (F4) RESOLVED.** F-5 (§8) pinned as DECLARED-BAND ARITHMETIC with the
  explicit clause "NO backtest, no measured gross return — the premium side
  stays the proposal's declared hypothesis until the scored phase."

**Session-2 additions audited (all clean):**

- `INCIDENT_RANGEFADE_PIT_SEAM_2026-09-25.md` — evidence invalidation
  correctly scoped: ancestor scored results remain append-only historical
  facts about R-ORIG semantics and are NOT evidence for the daemon law or
  R-ANCHOR; "parity PASS" citation ban restated; nothing executed, repaired,
  restarted or re-scored; cross-referenced as binding citation law in plan §6.
  Handbook §26 (Incident transparency, :842) exists — format reference valid.
- `PROPOSAL_SHADOW_CLASSIFICATION_FX-RANGEFADE-2M_2026-09-25.md` — verified
  proposal-only: no execution, no promotion, no $100k-account action, no
  parameter/restart/re-registration proposal; fail-closed default ("no
  change"); both exit conditions owner-gated (new amendment + GO; successor
  law per umbrella §5.6 with new strategy ID). Consistent with the untouched
  daemon (PID 79157, continuous etime) and the registry's amendment-A1
  activation-in-progress token.
- Four integrated design findings verified strictly strengthening: F-3
  mode-sham signal test (explicitly "signal-level, no scored arm, no new
  slot"); §9.1 inverted holdout companion; M3/all-controls gross+net
  decomposition with kill bands explicitly unchanged (NET); F-4
  beta-composition disclosure with the no-post-PnL-retrofit law.
- Ledger contract §10 frozen: append-only row schema with mandatory
  `SINGLE_SOURCE_PANEL` / `FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK` /
  `PAPER_TIER` labels + control gross/net decomposition (owner D-C/D-E
  reflected). §5.3 carries the D-C lock; §11 carries D-B/D-C/D-E as LOCKED
  and records the round-1 A7 arc accurately; owner packet rev 2 decision
  table consistent (D-A = the GO-1 gate, OPEN; D-F OPEN, proposal-only).
  GO-1/GO-2 phrases byte-identical between §0 and the packet.

**Round-2 findings (new):**

- **D1 (MEDIUM — binding GO-1 freeze-artifact content, non-blocking for
  typing GO-1):** freeze-completeness bundle: (i) numeric value + storage
  location for the PROMOTE bootstrap seed and the mode-sham shuffle seed
  (both texts say "frozen seed" without a number or named artifact); (ii) the
  §9.1 single-pass membership preregistration artifact + sha (where "frozen
  before the pass" is recorded); (iii) the mode-sham's firing consequence and
  verdict label (sham in the R-ORIG role of the §9.4 machinery — firing must
  be a kill, name it); (iv) two-pair close semantics (partial-replication vs
  REJECT_ALL composition rule at cycle close); (v) minimum evaluability floor
  for seam limb (iii) (`N_diff`/matched-pair count below which the limb is
  NOT_EVALUABLE and escalation is to (i)/(ii)) — recommended by BOTH
  proposers, not yet in the text. Disposition: all five belong in the GO-1
  freeze artifact (registration packet); A7 prelaunch verifies; none may be
  added post-PnL. Not GO-1-blocking because they are content OF the freeze
  that GO-1 authorizes, and the prelaunch gate (§11, incl. denominator seed)
  re-audits them before GO-2.
- **D2 (LOW):** F-5 cross-reference typo — "from its §5.3 field 2" should
  read "§7.3 field 2" (the 10-field proposal format lives in §7.3).
- **D3 (LOW):** §5.3's residual "If the owner completes an unblock path
  before GO-2…" upgrade bullet is dead text under the LOCKED D-C — annotate
  as superseded so it cannot read as a live option (fail-safe as is: any
  activation still requires owner amendment + new GO).
- **D4 (LOW):** §5.2/A.1 not annotated with the D-B lock (slate still reads
  "Council proposes … frozen at GO-1"; the USDCHF spare remains owner-
  amendment-only — consistent, but the lock state is understated where the
  slate is defined).
- **D5 (LOW):** §9.4(iii) pairing multiplicity unpinned (whether one
  R-ANCHOR-only trip may anchor multiple R-ORIG-only pairings); the
  same-day nearest-pair rule is otherwise well-defined and fail-safe.
- **D6 (LOW):** P2's mode-day-restricted beta decomposition table
  (computable from already-scored baseline cells, no new cell) was not
  mandated — the F-4 disclosure is carried and the no-retrofit law forbids
  gaming; add the table as a freeze reporting item (report-only).

**Round-2 verdict: PASS.** Zero CRITICAL / zero HIGH. All four round-1
conditions are integrated verbatim-in-strength; every session-2 addition is
correct, evidence-scoped and leak-tight; no arm-count drift (M1 = 6/pair,
M3 = 6, budget 24/18 unchanged in §0/§10/A.4); no GO-phrase drift. Remaining
items are D1 (freeze-content bundle, MEDIUM, binds the GO-1 freeze artifact)
and D2–D6 (LOW, recorded dispositions). None blocks the registration gate.

**GO-1 READY: YES** — with D1 as binding content of the freeze artifact that
GO-1 itself authorizes (verified by A7 prelaunch before GO-2).
