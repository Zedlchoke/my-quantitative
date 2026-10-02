# ERRATUM_V2 — corrections to successor_design_2026-10-02 v1 (co-owner follow-up, 2026-10-02)

v1 committed as `b707e0c0`/`bbbee10a`. The co-owner review found five
defect classes; two parallel lanes (budget/accounting;
calendar/exposure/selection) verified each and produced corrected content,
which the controller integrated into the packet files. **No historical
evidence file was edited to hide an error — v1 text is preserved in git at
`b707e0c0`, and this erratum itemizes every change.** No sealed-tail data
was accessed: calendar work is date arithmetic over committed metadata
only.

## 1. BUDGET (COMPOSITE_POLICY_DESIGN §6 — replaced)

v1 claimed "29 identities, ≤140 rows". Both numbers fail:

- 29 identities minus B0 (1 identity, **0 rows** by PB2 §1 law) = 28
  row-writing identities × 6 folds = **168 minimum scored rows**; the
  co-owner's 174 is the 29×6 reading that counts B0's zero rows. Even with
  every optional branch struck and the most permissive conventions, the
  floor is 150 rows > 140.
- v1's table OMITTED four mandatory classes: the crossed LORO×LOL arms
  mandated by A-H1 (2 identities/12 rows: (SLATE+guard)∖S003, ∖S023 —
  crossing with S026 dedups to LOL∖S026; crossing S014 is not mandated);
  HN-5 ×{×1.0, ×1.5} (2/12); the J3 cap-multiplier grid on LEARN (+3 rows,
  "≈9" → 12); and the contingency reserve as 3 identities/18 rows under
  E-Law 8 (v1 had it as row-headroom only). The ≤32 identity cap was also
  self-inconsistent (34–36 needed).
- Conventions were undeclared: C2 fold rows (RULE_SLATE: inside the row
  budget; DAILY: outside — stricter adopted, alternative disclosed); ×2.0
  identity classification; seed sub-runs write NO per-fold scored rows
  (PC12A's B4 never executed; DAILY's C2 wrote zero rows — the "128/128
  random beats policy" figure is a DP diagnostic, not a scored battery).

Corrected §6: **Option A 33 committed / 36 max identities, 192/210 scored
rows, 204/222 total, ≤128 seed sub-runs on their own line; Option B (LOL
scoped to the 6 live legs) 27/30 identities with HN-5 (25/28 without),
156/174 scored rows, 168/186 total.** Option B's deferred LOL legs are
typed `NOT_RUN_LOL_DEFERRED` — nothing silently dropped. Disclosed
degeneracies: LORO(J3)≡SLATE under guard-removed (realized as guard-IN
arm); LOL∖S017≡SLATE after G1 retire (declared-LOL-over-11 saves 1/−6);
crossed(J3)∖S026≡LOL∖S026. **Controller correction of the lane:** the lane's
Option B prose said 29/168 with-HN-5; table-consistent arithmetic is
27/156 — the packet carries the corrected numbers and this note.

## 2. CALENDAR / EXPOSURE (SUCCESSOR_PROTOCOL_DRAFT §1 — rewritten)

- **v1's dates were pasted, not computed.** "A ≈2029-09-26" follows from no
  anchor; "B ≈2029-10-01" is wrong under every convention (own anchor →
  2030-03-26/27; corrected anchor → 2030-04-03/04). The co-owner's figures
  verified: "2026-09-24 + 156w = 2029-09-20" reproduces exactly (an unlawful
  pre-registration anchor, kept in the JSON for transparency);
  "2027-03-31 + 156w = 2030-03-27" is right arithmetically but its anchor
  is the stale RULE_SLATE fallback.
- **All dates are now script outputs** (`analysis/calendar_variants.py` →
  `.json`; end-inclusive; conventions assert-validated against all 8
  executed DAILY fold windows): **A** LEARN 2025-12-27→2026-10-01, fold 1
  2026-10-02 (registration anchor), fold-6 end **2029-09-27** (readable
  09-28); **A_emb** (inherited 1w embargo) end **2029-10-03**; **B** LEARN
  2026-10-02→2027-04-01 (fully post-registration), fold 1 2027-04-08, end
  **2030-04-03**. Dates extend if floors bind or the collector goes quiet —
  they are arithmetic + floors, never absolute time law.
- **A′ WITHDRAWN**: it double-used the same tail as LEARN and as folds
  1–1.5, and relabeled DAILY exploratory exposure as validation; no
  independent partition exists (271d < 6×182d regardless).
- **Exposure truth (v1 hid it):** the "never-scored M1 segment"
  2025-12-27→2026-09-23 sits INSIDE DAILY exploratory folds 7–8
  (2025-09-26..2026-03-26, 2026-03-27..2026-09-24; vehicle sessions end
  09-23) — exploratory-scored, not untouched. Unscored ≠ untouched. Raw M1
  prices 2026-09-24→ are unread (grep across all three control trees: no
  artifact cites M1 vehicle prices past 2026-09-23). Full ledger in
  protocol §1.1 (sources, producers, last-read dates, kinds; the collector
  index schema has NO producer-version field — disclosed gap).
- **Standing owner directive conflict (v1 omitted it):**
  `SUCCESSOR_PLAN_DRAFT` item 4 (2026-10-01) pins the sealed tail
  2026-01-02→2026-06-26 "stays SEALED; no unseal is authorized", unseal
  variants "DEAD by owner directive". v1's "A (recommended)" conflicted with
  this standing directive. v2: A/A_emb are CONDITIONAL on a fresh owner
  election superseding it; the packet recommends nothing that requires an
  unseal. Warmup audit added: B's 52w warmup would read 79d of the
  owner-typed tail → B's warmup is trimmed to LEARN length (26w) or the
  owner declares tail-as-warmup lawful.
- **Stage law corrected (v1 put A7+GO inside the registration gate):**
  draft/admission → registration → implementation → LEARN → freeze → A7
  prelaunch → owner GO → execution → terminal (protocol §2).

## 3. SELECTION LAW (protocol §3 + register HN-3/A-H4/B-H-E3/B-H-G1)

v1 let validation-fold LOL/LORO measurements CHOOSE composition ("decide
S014's fate by the leave-one-leg arm on the fresh calendar") — selecting on
the same data later called validation. Corrected law: composition and rule
nodes freeze at registration; LEARN-side data only for anything learned;
validation-fold LOL/LORO are fixed diagnostics that TYPE hypotheses at
terminal and never select; a refutation can only close negative (never
restore a retired leg in-cycle); any composition change discovered on
validation requires a new registered cycle; v1's "mid-cycle rule edit via
amendment" sentence deleted (amendments clarify execution law only).
Expected-count honesty added: S014 ≈3–6 and S017 ≈3.5–7.5 expected entries
on any 26–40w LEARN vs floors ≥20/≥50 ⇒ **LEARN cannot decide them** —
membership frozen by owner election at registration; the ≥20/≥50 floors are
validation-window floors. B-H-E3's "re-entry on first fresh-fold review"
retimed to the NEXT cycle's registration review.

## 4. CLAIMS (design law + failure map + register)

- "Every portfolio-level participation gate ever measured destroyed value"
  scoped to the measured set (7 terminal overlay programs + B5/B6/B7/B8/B2
  controls) on this calendar — a prior, not a proof over all possible
  gates; re-opening the class requires a new mechanism + explicit
  multiple-testing budget. Same scoping applied in COMPLEMENTARITY §6/F1
  and the register's dead-list.
- HN-1's shared London→NY mechanism is labeled POST_OUTCOME hypothesis
  everywhere; DST/session alignment added to the trigger law (session marks
  from the calendar's London-close event time, never hardcoded UTC); the
  placebo-session + clock-shadow controls are named as what can promote or
  kill the causal claim — none is pre-asserted.
- Guard removal, S017 retire, clock floors: phrased as frozen
  hypotheses/elections to be measured, never as improvements.
- Hard risk caps (per-symbol max position, heat ceiling, maxDD kill-switch,
  fold-edge force-flat) made an explicit frozen-at-registration RISK LAW,
  binding every arm identically and independent of any economic
  gate/eligibility selection (design §4).

## 5. COSTS (design §0-4 + protocol D-2)

The owner has elected to continue EXPLORATORY research without a statement
— the statement's absence is NOT an absolute blocker for exploratory work,
and v1's "until the owner statement lands" phrasing rebuilt OI-2 as one.
Corrected to component-wise law: spread cells C1–C3 measured from panels;
commission/slippage/swap DECLARED with labels; a statement, if it lands,
upgrades ONLY commission + swap/interest-accrual attribution where valid —
it measures neither slippage, nor spread-beyond-cells, nor capacity, nor
unwitnessed history. DECLARED bands + ×1.5/×2.0 stress remain in force for
exploratory results; no exploratory number becomes an "after-cost PASS" or
"measured edge" via a partial statement.

## Verification status

Two lanes verified independently; a fresh-context skeptic then audited the
REVISED packet against this erratum (verdict in `SKEPTIC_REVIEW_V2.md`).
All lane arithmetic re-verified by the controller (one lane prose error
caught and corrected, §1). Boundaries: 0 scored runs, 0 S1/sealed-tail
reads, 0 registrations, 0 closed-budget reuse; owner dirty tree and the
futures lane untouched; this erratum and the revised files land by pathspec
on root main (the packet's own surface, terminal-review precedent).

— end erratum v2 —
