# SKEPTIC_SUCCESSOR — fresh-context review of the successor prep objects (2026-10-01)

Scope: the four uncommitted objects in this directory (SUCCESSOR_PLAN_DRAFT.md,
OWNER_PACKET_SUCCESSOR.md, RULE_SLATE.md, GATING_VS_SIZING.md) against primary
evidence: PC12A ARMS journals/metrics (`…/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/
diagnostics/stagec/ARMS/{POLICY,B1_ALWAYS_ON}/`), the 3 symbol dockets,
DECISION_PACKET.md §2/§11, PASS_BARS_V2.md, BACKTEST_CAMPAIGN_DESIGN.md, poolB
`audit_summary.json`, SIXSOURCE `sessions_index.jsonl`, the data-lane worktree
`orca/pc12a-7asset-unblock-20261001 @8b8c24a5`, and `researchctl locks inspect`.
Method: read-only; all arithmetic re-executed with `.venv/bin/python` (Decimal),
including a full independent reimplementation of the weekly GATE/SIZE/PONLY/
CARRY decomposition from the raw journals. This file is the only write.

Severity classes: BLOCKING (must fix before commit), MINOR (fix or note at
registration), INFO (no action / disclosed).

---

## 1. DECOMP arithmetic (dispatch item 1)

**VERIFIED (exact).** Per-symbol and pooled harm reproduce to the cent from
`metrics.json per_symbol_fold_records` (Decimal): USDJPY −87,201.388806,
EURUSD +1,714.262345, GBPUSD +223.697010, pooled **−85,263.429451** — matches
GATING_VS_SIZING §2's ΔW row and DP §2.1/§2.2. Per-fold ΔW column (§4) matches
my recomputation on every fold (e.g. f2 −208,827.50, f5 +174,192.41). The
stated validation is real, not asserted:

- **V1 fold-cash identity:** my independent cumulative-cash prefix scan
  (Decimal, events = NET_ORDER fills − SWAP debits) reproduces all 48
  arm×symbol×fold segments with worst |Σjournal − (cash_end − cash_start)| =
  **7.7e-7** (claim: $0.000001). The scan correctly assigns weekend force-flats
  (e.g. USDJPY fold-7 boundary event 2025-12-28T22:04Z; EURUSD fold-0
  2022-07-03T21:04Z — the exact example DECOMP §1.1 cites).
- **V4 component identity:** my from-scratch weekly rebuild (mark chain =
  friday_equity with fold-end replaced by realized cash_end; cross-arm ts
  matching; implied P = (equity − cash)/units) closes
  GATE+SIZE+PONLY+CARRY ≡ ΔW to **7e-7 summed over all 624 symbol-weeks**,
  zero weeks above $1.
- **V3 known totals:** exact (above). 208 marks × 3 symbols = 624 ✓.

**VERIFIED (spot numbers, several exact).** Gate typing from the journals:
DEFER ×331 all USDJPY ("L6 cost guard: trailing 28d spend X >= cap Y",
`guard.cap_usd` 2836.97), BLOCK ×343 all `eligibility_rule_id=E1`
("E1: 0 decisions in trailing 26w < 3 -> NOT_RUN_THIN FLAT"), NETTED_TO_ZERO
×35 ("L4 tie"); **zero E-degradation/W-rule rows exist in either journal**
(only E1/L4/L6 strings occur). DP §2.3-a's citation row reproduces verbatim
(2023-05-16T16:00Z, "trailing 28d spend 2852.3954 >= cap 2836.97",
decision_count_trailing 503). L6 = −352,959.21 is **91.41%** of USDJPY gate
harm −386,130.32, **4.05×** net harm; L6 fold concentration f1+f2 =
−351,531 (99.6% of L6, "folds 1–2" claim ✓); E1 pooled +17,281.7 with f5
dominance (my rebuild: E1-by-fold f5 = +108,488 vs claimed +108,761);
worst L6 weeks 2022-08-05 −94,889 and 2024-10-04 −69,774 reproduce **to the
dollar**; EDGE weeks pooled **−105,525.42** and USDJPY **−105,654.60 exact**;
206/624 weeks |ΔW|>$100 = **33.0% exact**; census class counts sum to 624 and
ΣΔW = −85,263 ✓; n_force_flat 6 vs 11 and force-flat costs $6,925.86 vs
$7,114.83 exact; fold-0 arms identical to the cent. Worked example week
2024-11-08: ΔW = −114,124.85 **exact** in my rebuild.

**F-1 [MINOR] — headline components are marking-convention-dependent (disclosed,
but quoted downstream without the caveat).** My rebuild's split differs from
the declared §2 table while closing the same identity: GATE −449,597.50 /
SIZE −18,541.04 / PONLY +71,214.97 / CARRY +311,660.13 vs declared
−385,499.62 / −7,306.56 / +65,677.59 / +241,865.16. Signs, ordering
(GATE ≫ SIZE), the ~79% CARRY+PONLY offset and every identity are stable; the
dollar split moves exactly as DECOMP §5/§8.3 disclose ("totals exact, split
convention-sensitive [NR]"). E1-typing under my conventions: USDJPY +16,773.81
**exact**, GBPUSD +221.70 **exact**, L6 −338,114 (96% of declared). The
successor PLAN §2 and OWNER_PACKET (1) quote "−$385.5k vs −$7.3k (2%)" flatly;
under my convention the size share is 4.1%. The qualitative conclusion
(participation ≫ sizing) survives any convention tested; the precise figures
should carry the DECOMP's own caveat when quoted.

**F-2 [MINOR] — display-rounding nits inside DECOMP tables.** §2 Σ-row SIZE
−7,306.56 vs its own per-symbol sum (−7,580.27+273.72 = −7,306.55) and §4
per-fold sum (−7,306.55); CARRY 241,865.16 vs 241,865.15; USDJPY component
identity sums to −87,201.38 vs ΔW −87,201.39; §3 E1 pooled 17,281.73 vs
16,773.81+286.23+221.70 = 17,281.74; §2 note "CARRY offsets 62.3%" — actual
62.24% (rounds to 62.2%). All sub-cent/rounding level; the underlying
full-precision identities are exact (verified above).

**F-3 [INFO] — fallback-mark honesty is warranted and, if anything,
understated.** My census of weeks with both arms flat at the mark anchor =
343/624 (55%) vs the declared 291/624 (46.6%) — the count depends on the
fallback's exact definition; under any definition the split-vs-totals
sensitivity is material and the DECOMP's §5/§8.3 disclosure of it is honest.

**F-4 [INFO] — SUPERMAJORITY counts reconciled.** DECOMP §3 "P 659 vs B1 1,021"
(pooled) vs docket A §6 "B1 998" (USDJPY-only): both correct — metrics show
B1 USDJPY 998 + EURUSD 23 = 1,021; POLICY 659 is USDJPY-only. No contradiction;
scopes differ.

**F-5 [INFO] — E1-floor narrative tension (both conventions disclosed,
resolved by the slate).** DECOMP §9.3 "E1 floor did not hurt on net (+$17.3k
pooled)" vs docket A H3 "E-floor removed legs worth +428.7k paper / +187.1k
realized-entry" — different attribution conventions (week-marked same-week
B1-only fills vs paper-book / excursion-entry attribution). RULE_SLATE benches
A-H3 (row 8, HIGH-RISK, paper-book dependence) and scopes the floor rule to
SIG-exit-only legs where docket B measured it helpful (R-E1 ≈ +$504) — the
lawful resolution. The successor objects never state the two numbers side by
side; one sentence would preempt owner confusion.

## 2. SLATE integrity (dispatch item 2)

**VERIFIED — ranking axis is explicitly not PnL/magnitude.** RULE_SLATE §1:
"Axis definitions (per dispatch; ranking is on these, NOT exposed PnL)" and
row 5 (A-H1/J3 — the largest measured harm) says outright: "Large measured
leakage (+274.6k journal units) but the weakest evidence base of the top six;
enters the slate only with a grid + strict anti-hypothesis." The DECOMP-says-
largest / slate-ranks-fifth tension is therefore explicitly resolved by the
declared mechanistic/coverage/overfit axis, as the dispatch required. DP §11.3
uses its own ranking but likewise declares "ranked by MECHANISTIC plausibility
not exposed PnL".

**VERIFIED — triggers name real journal fields.** Grepped in the journals:
`onoff_features.decision_count_trailing` (DECISION/BLOCK rows, integer),
`direction_vote` (±1/0), `leg_id`/`cluster_id`/`family_id` (e.g.
"USDJPY-S026", "meanrev_daily"), `blocked_reason_detail` L6 pattern (exact
string family, with `guard.{trailing_spend_usd, cap_usd, window_days}` object
alongside), `eligibility_rule_id="E1"` + "NOT_RUN_THIN FLAT" detail, fold_id,
contributing_legs with per-leg votes (for the C6/vote-0 accounting). Hour
semantics are derivable from `ts_decision_utc` (UTC ISO) ✓. `exit_class ==
SIG_ONLY` is declared a corpus-identity field (TB inventory), not a journal
field — correctly sourced to docket B §1. **F-6 [MINOR]:** the §2 preamble
claims the journal carries "`ts`" — the real fields are `ts_decision_utc` /
`ts_fill_utc`; the successor spec should name them exactly.

**VERIFIED — HIGH-RISK flags honest.** Three named in §1's restatement
(B-H-E2 hours scanned on scored journals; A-H3 exemption list = exposed
blocked set; A-H1 cap multiple + 29-trade matched set post-hoc), matching the
table's bolded HIGH-RISK/HIGH cells; milder disclosures for A-H2's long-only
split and B-H-E3's pair choice. Two of the three flagged rules are in the
slate only with preregistered grids re-learned on fresh TRAIN (§4); the third
(A-H3) is benched. OWNER_PACKET's "3 flagged HIGH-RISK" is consistent.

**VERIFIED — anti-hypotheses falsifiable, fresh-fold-bound.** Every slate rule
carries explicit REFUTED conditions evaluated "on fresh folds" plus sample
floors; failure is a typed kill (NOT_RUN_THIN / ledger row, no rescue);
benched rules re-enter only as amendments, never mid-cycle (§2 benched,
PLAN §5). No rescue path found.

**VERIFIED — budget arithmetic sums from its own components.** §5: identities
1+1+6+1+1+2+2 = **14 ≤ 24**; rows 6+6+36+6+6+12+12 = **84**; +18 LEARN grid
rows (3 gridded rules × 3 nodes × 2 sub-folds) = **102 ≤ ~120**; headroom 10
identities explicitly earmarked (C7 inverted+lagged = 2, contingency 8). C5/C6
add zero rows (analysis-side). PLAN §3.3's "≤24 / ≤120 (84 + 18 + margin)"
matches. Counting unit follows PASS_BARS_V2 E-Law 8 (verified in PB2: seeds
are sub-runs on a separate line; B4 ≤128 precedent).

## 3. Calendar math (dispatch item 3)

**VERIFIED (exact).** 6×26w = 156w = **1,092 days**. Never-scored M1 segment
2025-12-27→2026-09-23 = **270 days = 38.57w ≈ 38.6w = 1.48 folds** (panels end
2026-09-23 — poolB audit min/max 2021-01-01/2026-09-23 verified; live sessions
through 2026-09-28T21:49Z in sessions_index.jsonl ✓). Scored window ends
2025-12-26 ✓ (journal HEADER window). Earliest dates: **2028-12-23** max-credit
= panel end + (1,092−270) = 2026-09-23 + 822d **exact**; **2029-09-26**
recommended = folds 2026-09-30 + 1,092d **exact** (fold 1 end 2027-03-31
exact; LEARN→fold-1 gap = 7 days = the 1w embargo); **2029-09-27** zero-credit
= 2026-10-01 + 1,092d exact; mid-2027 unattainable ✓ (stock at 2027-06-30 =
78.6w = 3.02 folds < 6 → NOT_RUN_INSUFFICIENT_CALENDAR); daily cohort
2020-10-02→2026-09-30 = 312.7w − 52w warmup = **10.03 folds** ✓; H1 pairs
from-zero ≈ 2029-09/10 ✓.

**VERIFIED — the sealed-tail handling is lawful and consistently gated.** Repo
law traced: CAM §3 ("remaining 26-week sealed tail = SEALED (S1-class,
untouched)"; common calendar ends 2026-06-26; M1 tail beyond NOT used,
extension = owner amendment), TERMINAL_DECISION ("sealed 26w tail never
loaded"), DP §5 (calendar burned for new scored claims; sealed tail = 1 fold <
the 6-fold floor ⇒ can never be validation), AGENTS.md NEVER-list ("S1 access"
only with the cycle's gate + owner). So: the sealed 26w [2025-12-27→2026-06-26]
is **reserved-as-sealed, owner-gated for any use, and categorically barred
from validation** (too short + burned-calendar law). The files' choice —
RULE_SLATE §4: LEARN = the full never-scored 38.6w **including** the sealed
tail, requiring "an explicit owner declaration", never countable toward the
≥6 folds, with a no-unseal fallback (LEARN 2026-09-24→ 26w, fold 1 2027-03-31,
battery ≈2030-03) — is the lawful handling. The 38.6w stock is counted **from
2025-12-27** (never-scored segment start) in both credit variants; 2026-09-24
appears only as the fallback LEARN start. No variant counts from 2026-06-27 —
correct, since the post-seal segment alone (12.6w) was never a defined
calendar unit and a partial-credit hybrid would add nothing lawful.

**F-7 [MINOR] — fallback dates off by one day.** 2026-09-24 + 26w =
2027-03-25 (file: 2027-03-24); +1w embargo → fold 1 = 2027-04-01 (file:
2027-03-31); battery 2030-03-27 ("≈2030-03" ok).

**F-8 [MINOR] — PLAN §3.2 garbles the LEARN window (see F-11 edit).** "the
first 38.6w of never-scored M1, 2026-09-24→" conflates the slate's primary
LEARN (2025-12-27→2026-09-23, sealed tail owner-gated) with the fallback
(2026-09-24→, 26w). Read literally it contradicts RULE_SLATE §4 AND the plan's
own §3.4 ("LEARN consumes the 38.6w stock"; folds 2026-09-30→2029-09-26). A
literal 2026-09-24 38.6w LEARN would complete the battery ~2029-01,
invalidating §3.4's dates.

## 4. PLAN conformance (dispatch item 4)

**VERIFIED — PASS_BARS_V2 inheritance accurate.** PB2 confirmed at
`…/policy/PASS_BARS_V2.md`: AND-only STRICT semantics, ties FAIL (E-Law 4);
pooled quantities (E-Law 2); comparability (E-Law 3); ≥6 executed folds or
NOT_RUN (E-Law 5); book-integrity precondition (E-Law 6); ordering (E-Law 7);
identity-vs-seed budget counting, B4 ≤128 seeds own line (E-Law 8); B1
ALWAYS_ON = eligibility pinned ON (slate's B1S mapping correct); B5 clock-gate
duty-matched phase-0 (slate C3 ✓); B6 inverted / B7 lagged (slate C7 ✓); P6a
×1.5 governing with baseline re-run at same tier, P6b ×2.0 reporting with the
`POLICY_COST_DOMINATED` sign-flip trigger (§6); P7 fold concentration ≤50% PnL
share / ≤2× pro-rata DD; P8 leave-one-leg with exactly-one break →
`POLICY_ONE_LEG_CARRIER`. The slate's P8R (rules replacing legs) and B4S/B5S
mappings are declared adaptations, not misquotes. CAM §3 floors 20/3/100 and
§4 stress tiers verified as cited.

**VERIFIED — P-MW/P-FA well-formed; LEARN cannot leak.** P-MW: strict
inequalities (avoided-loser net > suppressed-winner net pooled AND Δ(r) > 0),
winner column mandatory with `NOT_RUN_INTEGRITY` on omission; P-FA: admitted
set net > 0 AND worst single admitted loser < pooled admitted gain, ≥50%
concentration disclosure. Freeze-before-fold-1, 1-week embargo (verified 7
days), immutable selected node, `NOT_RUN_GRID_THIN` collapse on LEARN floor
failure. PLAN §3.8 restates both bars consistently.

**VERIFIED — no GO consumable; expansion path matches statuses.** No GO phrase
exists in any object; §3.7 registers it at registration. Expansion: M1-track
2029+ for EUR/GBP/JPY; USDCAD/AUDUSD collector-or-permanent-NOT_RUN (docket C
✓); daily-track for the 7 blocked assets incl. energy — EIA dailies
2020-10-01..2026-09-29 verified in the data lane's GATE_UPDATE_7ASSETS.md;
FRED FX ends 2026-09-25 ✓; roll/chain gates open ✓ (OWNER_PACKET row correct).
**F-9 [INFO]:** OWNER_PACKET item (5) "its own GO phrase lives in the draft
plan §3.7" is loose — the draft contains the phrase-registration RULE, not a
phrase; recommend "to be set at registration (draft §3.7)".

**F-10 [MINOR] — PLAN §1 paraphrases of anti-hypotheses diverge from the
frozen slate text.** Plan §1's "e.g." summaries are non-binding but state
conditions that do not exist in RULE_SLATE §2 (e.g. J3 "refuted if
guard-relaxed book DD exceeds guard-active book DD on ≥3 fresh folds" vs the
slate's three clauses (i)–(iii); J1 "≥3 folds" vs the slate's pooled/(ii) ≥2
folds). The plan does defer ("per RULE_SLATE §2"), but at registration the
slate's clauses must be the sole binding text — say so explicitly (see edit 4).

## 5. OWNER packet (dispatch item 5)

**VERIFIED.** Per-symbol table matches dockets: USDJPY YES 703 trades (393+310
✓); EURUSD/GBPUSD YES ✓; USDCAD/AUDUSD TRAIN-only + NOT_RUN no lawful H1/M1
calendar ✓ (docket C: H1 panels frozen read-only 2021-01-03→2026-06-30, no
collector, HMDS M1 NOT_RUN_SIZE_CAP); daily cohort ≈10 folds conditional ✓;
BRENT/WTI/NATGAS same-track + roll/chain open ✓. Data lane read-only state
verified: worktree `.worktrees/pc12a-7asset-unblock-20261001` on branch
`orca/pc12a-7asset-unblock-20261001` @ **8b8c24a5**, clean status;
GATE_UPDATE_7ASSETS.md / OWNER_PACKET.md present; D-1..D-7 exist in the lane's
packet. Heavy lock **FREE_PROVEN** (researchctl locks inspect, re-run this
session) ✓. No overclaim language: scan for validate/edge/proven/guarantee
finds only lawful uses ("never serve as validation", "cannot be lawfully
validated before late 2028", "proven engine" = lineage). Boundaries section
accurate vs DP §1/§10 and git status (only successor/ + owner dirty files).
Decision list: items 1/3/4/5 are single actions; **F-9b [INFO]** item 2 ("Data
lane decisions D-1..D-7") is a referral to the lane's own 7-decision packet,
not itself one action — acceptable as a pointer, slightly off the banner.

## 6. Cross-file consistency (dispatch item 6)

**VERIFIED.** All numbers quoted in PLAN §2 / OWNER_PACKET (1) match their
sources exactly: −$385.5k / −$7.3k / 2% / −$352,959 / 91.4% / +$17.3k /
W-rules never fired / ties $0 (DECOMP §2/§3/§9); every slate rule's measured
prior matches dockets A/B to the cent (J1: −281,460.12 n=91 / −83,683.91 n=74 /
50 losers −795,805.74 / 38 winners +514,369.07 / DD −412,208.31→−359,621.76 /
13-5-9-12-9-15-15-13; J2: −222,300.73/−319,603.73, family −470,441.67 n=33,
cluster −541,904.46 n=53; J3: 331 defers (S026 299), 29 filled +274,572.47
16W/13L, DD −378,482.09→−501,493.31; E-hour-gate: −495.9/57 and −1,037.1/59,
DD 878→387 / 2,277→977; E-floor: S009 −587.8/50, missed −504.0/49, +683.8
c-winners; G1: −47.6/28, −212.9/39, 20 SL:6 TP, 15/28 ≤1 min, DD 676→502).
128/128 B4 precedent ✓ (DP §2.3). 13 hypotheses / 12 on/off + H-G2 exit-law ✓.

**F-11 [BLOCKING] — SU-RS-E1/SU-RS-E2 rule-ID swap between PLAN §1 and
RULE_SLATE §2.** RULE_SLATE: SU-RS-E1 = EURUSD entry-hour gate {12,16}
(source B §7-H-E2 / DP §11.3-4, gridded); SU-RS-E2 = E1 activity floor for
SIG-exit-only legs (source B §7-H-E1 / DP §11.3-2, constants frozen).
SUCCESSOR_PLAN_DRAFT §1 assigns the IDs the other way: its SU-RS-E1 is the
floor ("codified E1", decision_count_trailing < 3/26w) and its SU-RS-E2 is the
hour gate. Consequences if registered as-is: (a) PLAN §3.1's "SU-H1..H6 = the
6 slate rules" binds hypothesis IDs to the crossed table; (b) the two rules'
frozen anti-hypotheses (hour-gate: suppressed-hour book > 0 pooled, ≥40-trade
floor; floor: $200 tripwire, ≥30-decision floor) would mis-attach; (c) the
P-FA mirror in RULE_SLATE §7 ("mirror-applied to SU-RS-E2's kept-floor
reading") would land on the hour gate under the plan's IDs; (d) the plan's
SU-RS-E1 symbol scope "EURUSD+GBPUSD" is wrong for the floor — the corpus has
exactly one SIG-exit-only leg (EURUSD-S009; GBPUSD legs are SL+TIME / TP+SL
per docket B §1); the slate correctly says "EURUSD-S009 (+ any successor leg
of that exit class)". Same rule set, crossed wiring — a registration-integrity
defect in a preregistration artifact. Fix = edit 1 below.

**F-12 [MINOR] — PLAN §1 SU-RS-J3 leg scope "all legs" vs RULE_SLATE §2
"USDJPY-S026 only"** (the L6 guard condition fired on S026 in 299/331 cases;
slate's trigger is explicitly S026-only). Also plan J3's "re-fit cap on LEARN"
wording vs the slate's frozen multiplier grid {1.5, 2.0, ∞} on the frozen cap
— the slate is the authority; align the word "re-fit".

---

## Verdict

The measurement layer is sound: every checkable identity closes (many to the
cent or the micro-dollar), the validations claimed in GATING_VS_SIZING are
real and independently reproducible, the calendar arithmetic is exact, the
sealed-tail handling is lawful under traced repo law, PASS_BARS_V2 inheritance
is accurate, and no overclaim language exists. The one thing that must not
reach registration is the crossed rule-ID wiring between the plan and the
slate (plus the plan's LEARN-window garble and two smaller alignment nits).

VERDICT: FIX_THEN_COMMIT

Exact minimal edits (all in SUCCESSOR_PLAN_DRAFT.md unless noted; RULE_SLATE
and GATING_VS_SIZING commit unchanged):

1. **§1 table — swap the SU-RS-E1/SU-RS-E2 rows' IDs to match RULE_SLATE §2**,
   and fix the floor rule's scope. After the SU-RS-J3 row, the two rows should
   read:
   `| SU-RS-E1 | EURUSD | all legs' entries | entry-hour UTC ∈ {12,16} [HIGH-RISK: shaped on exposed folds — grid re-learned on LEARN to honest ±adjacent hours] | OFF entry |`
   `| SU-RS-E2 | EURUSD (SIG-exit-only class; today EURUSD-S009) | signal-exit-only legs | onoff_features.decision_count_trailing < 3 in trailing 26w (constants frozen) | OFF (codified PC12A E1 floor) |`
   (this also removes "EURUSD+GBPUSD" and the "floor(3/26w)" notation).
2. **§3.2 — replace the LEARN parenthesis** "(the first 38.6w of never-scored
   M1, 2026-09-24→, or the first 20% of the daily-cohort calendar if that
   track is chosen)" with "(the never-scored M1 segment 2025-12-27→2026-09-23
   incl. the owner-declared sealed tail, per RULE_SLATE §4; fallback
   2026-09-24→2027-03-25 if the owner declines to unseal; or the first 20% of
   the daily-cohort calendar if that track is chosen)".
3. **§1 table — SU-RS-J3 scope**: "all legs" → "USDJPY-S026 only"; and "re-fit
   cap on LEARN window" → "cap-multiplier grid {1.5, 2.0, removed} learned on
   LEARN" (matches RULE_SLATE §2/§4).
4. **§1 anti-hypothesis note — append one sentence**: "Where this table's
   paraphrases differ in any particular from RULE_SLATE §2's frozen
   REFUTED/floor clauses, the slate text is binding."
5. *(optional, RULE_SLATE.md §7 item 1)*: fix typo "netPnQ(B1S)" →
   "netPnL(B1S)".

Non-blocking notes for the owner session (no edit required): DECOMP §2's
"62.3%" → 62.2%; the ±1-cent Σ-row displays (F-2); the fallback-variant date
nits (F-7); "ts" field naming (F-6); the E1-floor convention tension deserves
one cross-reference sentence (F-5); GO-phrase wording in OWNER_PACKET item 5
(F-9).

— end of skeptic file. Objects untouched; no commits made; this is the only
file written. —
