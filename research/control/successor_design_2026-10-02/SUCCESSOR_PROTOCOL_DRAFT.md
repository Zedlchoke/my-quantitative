# SUCCESSOR_PROTOCOL_DRAFT — successor_design_2026-10-02 (NOT RUN; nothing registers today)

Operating protocol for the successor cycle that would test
COMPOSITE_POLICY_DESIGN. Inherits: RULE_SLATE §4/§6/§7 (LEARN law,
calendar arithmetic, PASS bars), DAILY's prospective-surface law, PB2
E-Laws, P-35. This draft stops at the reviewable packet boundary —
registration/GO are owner actions in a NEW cycle (no closed budget reuse).

## 1. Calendar law (measured arithmetic, 2026-10-02)

Fresh-data stock on the M1 pairs (poolB audit + live collector
`sessions_index.jsonl`, sessions through 2026-09-28):
- Scored folds end 2025-12-26 ⇒ never-scored M1 segment
  **2025-12-27 → 2026-09-23 = 270 days = 38.6 weeks = 1.48 folds** (includes
  the 26-week sealed tail).
- ≥6 × 26w validation floor = 156 weeks.

| variant | LEARN window | fold 1 starts | 6 folds complete | dependency |
|---|---|---|---|---|
| **A (recommended)** | 2025-12-27→2026-09-23 (38.6w, consumes the sealed tail) | 2026-09-24 live accumulation | **≈ 2029-09-26** | owner declaration unsealing the tail as TRAIN (it can then NEVER count toward validation) |
| A′ (max credit) | same LEARN | tail credited as folds 1–1.5 | **≈ 2028-12-23** | owner accepts 38.6w of exposure-adjacent-but-unscored M1 as 1.5 folds — weakest evidence, NOT recommended |
| B (no unseal) | first 26w of live accumulation (2026-09-24→2027-03-24) | 2027-03-31 | **≈ 2029-10-01** | none beyond collector continuity |

All three variants are honest; the dispatch's law applies — the exposed
2021-2025 folds can never be relabeled validation. **Everything before fold
1 is exploratory/LEARN; every claim needs ≥6 future folds.** No advantage is
promised and no variant is assumed to be waiting for a specific historical
date of the old plan — fold counting starts at registration under whichever
variant the owner elects.

Dependency risk (measured): forward M1 accumulation depends on the live
IBKR read-only collector staying healthy (HMDS M1 history remains
NOT_RUN_SIZE_CAP — backfill is NOT available); collector-quiet weeks become
`BLOCKED_STALE`-typed FLAT weeks and EXTEND the calendar 1:1. This is the
same law DAILY exercised (73 BLOCKED_STALE rows).

## 2. Registration gate (all conditions; none exist today)

1. Owner elects calendar variant (A / A′ / B) and unseals or seals the tail
   accordingly — one decision, recorded in the plan.
2. Engine prerequisites implemented and tested (COMPOSITE_POLICY_DESIGN §0):
   quote-CCY ledger (exists in DAILY lineage), per-leg exposure + MAE/MFE
   journal fields (new), per-fill quoted-spread capture (new), DECLARED-cost
   labels (exists).
3. HN-6 TB-LABELS producer run TRAIN-side + EXPOSED-labeled (analysis-only;
   no rule may consume a test-fold label).
4. Hypothesis register frozen (this packet's Part 1/2 with owner edits);
   grids, floors, anti-hypotheses frozen verbatim.
5. Budget frozen (COMPOSITE_POLICY_DESIGN §6 or owner-amended); STOP-at-cap.
6. A7 prelaunch two-key per P-8; fresh GO at the successor's own gate.

## 3. Sequence (one lawful path)

```text
owner decisions (calendar variant, optional OI-2 statement export)
→ plan write + register cycle (fresh budget)
→ LEARN freeze: HN-1 hour-sets + HN-2 f-ratio learned; B3S chosen; nodes frozen
→ fold k arrives (26w) → SLATE + baselines + LORO/LOL run on fold k only
→ interim typed reading after EVERY fold (budget/identity/floor checks;
  NO threshold changes after this point — violation = STOP-3)
→ after fold 6: full battery read (PASS bars §7 of the design)
→ stress ×1.5/×2.0 re-priced; P-MW/P-FA/P-LOL tables mandatory
→ A7 terminal; two-half close; negative close first-class
```

Interim readings are typed (`NOT_RUN_THIN`, `B0_DOMINANCE`, …) and NEVER
restart the battery. Any mid-cycle rule edit requires a registered
amendment BEFORE the next fold opens.

## 4. Owner decision menu (each ONE action; nothing runs before it)

| id | decision | consequence |
|---|---|---|
| D-1 | elect calendar variant A / A′ / B | sets fold-1 date and the unseal declaration |
| D-2 | export IBKR Activity/Flex statement to `~/.my-quantitative-data/ibkr_statement/` (OI-2) | upgrades DECLARED→measured costs; re-anchors any spend cap to capacity; unlocks C-H-C2 analysis; does NOT unblock validation by itself |
| D-3 | approve successor registration (name/budget per design §6) | opens the cycle; A7 prelaunch follows |
| D-4 | (optional, separate track) PIT declarations for the daily cohort; futures chain-source naming | opens OTHER calendars; does not accelerate the M1 track |
| D-5 | (null action) reject every register hypothesis | the honest default: program stays FLAT; cost authority + cohort unlocks remain the only live paths |

## 5. Boundaries held by this draft

No scored run, no S1 read, no orders/paper/live, no GO, no reuse of
PC12A/DAILY budgets, no registry write. The 8 PC12A folds and 8 DAILY folds
stay exposed forever. The sealed tail stays sealed until an owner sentence
unseals it. Push/merge forbidden; this packet lands on root main by pathspec
only (terminal-review precedent).

— end protocol draft —
