# SUCCESSOR_PROTOCOL_DRAFT v2 — successor_design_2026-10-02 (NOT RUN; nothing registers today)

> **v2 (2026-10-02, co-owner follow-up):** v1's calendar dates, variant set,
> stage sequence and selection law were defective and are corrected here;
> every change is itemized in `ERRATUM_V2.md`. Dates below are OUTPUTS of
> `analysis/calendar_variants.py` (end-inclusive, conventions validated
> against the 8 executed DAILY fold windows) — calendar arithmetic plus
> floors, never an absolute time law. Thin folds type `NOT_RUN_THIN`;
> collector-quiet weeks type `BLOCKED_STALE` FLAT and extend the calendar
> 1:1.

Operating protocol for the successor cycle that would test
COMPOSITE_POLICY_DESIGN v2. Inherits: RULE_SLATE §4/§7 (LEARN law, PASS
bars), PB2 E-Laws, P-35, DAILY's prospective-surface law. This draft stops
at the reviewable packet boundary — registration/GO are owner actions in a
NEW cycle (no closed budget reuse).

## 1. Calendar law (script-computed; `analysis/calendar_variants.json`)

### 1.1 Exposure state first (what the data actually is)

| source | last read | by what | kind |
|---|---|---|---|
| M1 panels EUR/GBP/JPY → 2025-12-26 | 2025-12-26 | PC12A 38 Stage-C arms | **scored, EXPOSED forever** |
| M1 panels 2025-12-27 → 2026-09-23 | 2026-09-23 | DAILY exploratory folds 7 (2025-09-26..2026-03-26) & 8 (2026-03-27..2026-09-24, vehicle sessions end 09-23) | **exploratory-scored** — the "never-scored segment" is EXPOSED, not untouched; it contains the whole owner-typed sealed tail |
| AUD/CAD D1 (G6 pull) | 2026-09-30 (10-01 forming bar excluded) | DAILY input side | exploratory-scored (inputs) |
| NZD/USDCHF/XAU/XAG D1 | 2026-09-30 | identity freeze / admission matrix | metadata-only |
| Live M1 collector raw (index has NO producer-version field — schema gap disclosed) | session metadata through 2026-09-28T21:49:31Z | this packet + RULE_SLATE (liveness) | metadata-only |
| Raw M1 prices 2026-09-24 → | none | grep across successor_design + terminal_review + DAILY control dirs: every post-09-23 date hit is a calendar label, D1 input, or collector metadata — **no artifact reads M1 vehicle prices past 2026-09-23** | **unread** |

Law: **unscored ≠ untouched.** Pre-registration data counts as independent
only with seal/unread evidence AND selection frozen before access. The
2025-12-27→2026-09-23 segment fails the untouched test (DAILY folds 7–8
computed exploratory PnL on it, journals on disk); it is lawful ONLY as
LEARN/TRAIN material, never as validation.

### 1.2 Standing owner directive (recorded conflict — v1 omitted this)

`SUCCESSOR_PLAN_DRAFT` item 4 (2026-10-01) pins the owner-typed sealed tail
as **2026-01-02 → 2026-06-26 — "stays SEALED; no unseal is authorized"**,
unseal variants "**DEAD by owner directive**" (`OWNER_DECISION_TABLE`:
"SEALED-TAIL | ALREADY ANSWERED"). v1 of this draft recommended a variant
that consumes that tail without recording this directive — a conflict. v2
resolves it by making every tail-consuming variant CONDITIONAL on a fresh,
explicit owner election that supersedes the standing directive; the packet
itself recommends nothing that requires an unseal.

### 1.3 Variants (computed; registration anchor 2026-10-02)

| variant | LEARN | embargo | fold 1 | last fold end (readable +1) | dependency |
|---|---|---|---|---|---|
| **A** (tail-consuming) | 2025-12-27→2026-10-01 (279d = 39.86w; includes the DAILY-exposed segment AND the owner-typed sealed tail) | 0d | 2026-10-02 | **2029-09-27 (2029-09-28)** | fresh owner election superseding the 2026-10-01 "stays SEALED" directive; the consumed tail can NEVER count toward validation |
| A_emb (A + inherited 1w embargo, RULE_SLATE §4-3) | same | 6d | 2026-10-08 | **2029-10-03 (2029-10-04)** | same + embargo law election |
| **B** (no unseal; fully post-registration LEARN) | 2026-10-02→2027-04-01 (182d = 26w) | 6d | 2027-04-08 | **2030-04-03 (2030-04-04)** | none beyond collector continuity |
| ~~A′~~ | **WITHDRAWN** — v1's "credit the tail as folds 1–1.5" double-used the same data as both LEARN and validation and relabeled DAILY exploratory exposure; no independent partition exists (271d tail < 6×182d folds regardless) | | | | |

- v1's "≈2029-09-26" (A) and "≈2029-10-01" (B) were pasted from other
  documents and follow from no anchor; the co-owner's "2026-09-24 + 156w =
  2029-09-20" reproduces exactly under the no-adjustment reading (fold 1
  predating registration — unlawful anchor, shown in the JSON for
  transparency only). Corrected B end 2030-04-03 matches
  OWNER_DECISION_TABLE N2.
- **Warmup audit (52w pre-fold-1):** A's warmup = 2025-10-03→2026-10-01,
  100% pre-registration (but 85d inside the PC12A scored window as feature
  inputs, 176d inside the tail, 8d past the frozen panels needing collector
  aggregation). B's 52w warmup would read 79d of the owner-typed sealed
  tail and 6d of embargo gap — **B's warmup must be trimmed to LEARN length
  (26w) or the owner declares tail-as-warmup lawful**; the JSON flags this.
- Fold-count arithmetic: 6 × 26w = fold-1 start + 1091d end-inclusive. All
  dates above are script outputs; if floors bind or the collector goes
  quiet, the readable date extends — never shortened.

## 2. Stage law (v1 had A7+GO inside the registration gate — impossible; corrected)

```text
(1) DRAFT/ADMISSION   this packet; owner review; NOTHING runs
(2) REGISTRATION      owner D-3: cycle + fresh budget + calendar-variant election
                      (incl. any unseal election superseding the standing directive)
                      + COMPOSITION/RULE-NODE FREEZE LIST named
(3) IMPLEMENTATION    engine prerequisites (design §0); HN-6 TB-LABELS TRAIN-side
(4) LEARN             hour-sets, f-ratio, J3 multiplier, B3S choice — LEARN data only
(5) FREEZE            composition + rule nodes + embargo + budgets frozen verbatim
(6) A7 PRELAUNCH      independent audit; two-key first (P-8)
(7) OWNER GO          fresh GO at this cycle's own gate — two-key second
(8) EXECUTION         folds 1–6 as data accumulates; interim typed readings;
                      NO threshold/composition changes (see selection law §3)
(9) TERMINAL          full battery + stress re-price + P-MW/P-FA/P-LOL tables;
                      A7 terminal; two-half close; negative close first-class
```

Registration-gate conditions (all before stage 2 completes): plan written;
calendar variant elected; budget frozen (design §6 v2); register frozen;
exposure ledger §1.1 re-measured and committed; engine prerequisites
specced. A7 prelaunch and GO are stages 6–7, AFTER registration and freeze.

## 3. Selection law (v1 let validation-fold LOL choose composition — repealed)

1. **Composition and rule nodes freeze at registration** (stage 2) and again
   verbatim at stage 5: leg list, S014/S017 membership, VC2 admission,
   guard default, HN-1 hour sets, HN-2 f-ratio, J3 multiplier, B3S choice.
   Everything learned is learned on LEARN-side data only.
2. **LOL/LORO arms on validation folds are fixed diagnostic comparisons**,
   preregistered with windows and floors. Their outputs TYPE hypotheses
   (REFUTED / NOT REFUTED / `NOT_RUN_THIN`) at terminal. They are **never
   selectors**: no validation-fold measurement may add, remove, restore, or
   re-parameterize a leg, rule, or node.
3. A refutation may close a claim negative; it may never restore a retired
   leg in-cycle. **Any composition change discovered on validation requires
   a new registered cycle.** (v1's "any mid-cycle rule edit requires a
   registered amendment before the next fold opens" is DELETED — amendments
   may only clarify execution law, never composition or thresholds.)
4. **LEARN cannot decide S014/S017** — expected-count arithmetic: S014 ≈
   3.0–5.6 entries and S017 ≈ 3.5–7.5 trades on a 26–40w LEARN window (vs
   floors ≥20/window, ≥50/arm-book; S014 at ~3.6/fold ⇒ ~30% of folds type
   thin). Their membership is therefore frozen at registration by owner
   election on prior evidence, and the LOL arms report as diagnostics. The
   register's HN-3/B-H-G1 floors are VALIDATION-window floors, not LEARN
   decisions.

## 4. Owner decision menu (each ONE action; nothing runs before it)

| id | decision | consequence |
|---|---|---|
| D-1 | elect calendar variant A / A_emb / B — A and A_emb additionally require a fresh unseal election superseding the 2026-10-01 "stays SEALED" directive (recorded conflict §1.2) | sets fold-1 date per §1.3; B needs no unseal (warmup trimmed to 26w) |
| D-2 | export IBKR Activity/Flex statement to `~/.my-quantitative-data/ibkr_statement/` (optional) | upgrades the DECLARED **commission + swap/accrual** components to measured where attribution is valid; does NOT measure slippage, spread-beyond-cells, or capacity, and rewrites no history; DECLARED bands + ×1.5/×2.0 stress REMAIN for exploratory work; never converts an exploratory number into an after-cost PASS |
| D-3 | approve successor registration (name/budget per design §6 v2; variant + freeze list) | opens the cycle at stage 2; A7 prelaunch and GO come later (stages 6–7) |
| D-4 | (optional, separate track) PIT declarations for the daily cohort; futures chain-source naming | opens OTHER calendars; does not accelerate the M1 track |
| D-5 | (null action) reject every register hypothesis | program stays FLAT; cost authority + cohort unlocks remain the only live paths |

## 5. Boundaries held by this draft

No scored run, no S1 read, no sealed-tail access (this revision did NOT
read any M1 price data — calendar work is date arithmetic over committed
metadata), no orders/paper/live, no GO, no reuse of PC12A/DAILY budgets, no
registry write. The 8 PC12A folds and 8 DAILY folds stay exposed forever.
Push/merge forbidden; this packet lands on root main by pathspec only.

— end protocol draft v2 —
