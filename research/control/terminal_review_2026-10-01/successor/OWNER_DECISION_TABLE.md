# OWNER_DECISION_TABLE — both-track preparation (2026-10-01, session 3)

Integrates DAILY_ADMISSION_MATRIX.md + M1_OPERATIVE_UPDATE.md into the
successor package (base `87e65f00`). Preparation only; both TERMINAL
cycles untouched; GOs DEAD; budgets never reused; sealed tail SEALED.

## What can be done NOW (preparation drafting only — some items still need owner input before they RUN)

1. DAILY-track preparation DRAFTS for the 4 spot/metals pairs + 7
   candidates + 2 EIA-signal legs (config drafts, daily-clock adapter
   spec, PIT-freeze drafts, ledger skeleton) — drafting needs no owner
   input; RUNNING any of it is inside a future registered cycle.
2. M1-track collection: the protocol is a DRAFT (M1_OPERATIVE §5) — it
   requires an owner-named free/keyless M1 source + registration before
   collection starts; nothing accumulates yet.
3. TB-LABELS as TRAIN-side diagnostics (no claim) + attribution-tagged
   rule priors preserved as EXPOSED-fold hypotheses — draft-ready.

## Exact owner-supplied evidence / declarations required

**Data items now follow the lane's OI-1..OI-6 checklist verbatim**
(OWNER_INPUT_CHECKLIST.md @d722f5d5 — one action per item; defaults
fail-closed). This table supersedes the earlier D-DAILY-* rows:

| id | decision | exact evidence/declaration |
|---|---|---|
| OI-1 | PIT availability law (4 spot/metals + energy signal) | (a) declare IBKR HMDS D1 panel-of-record, availability = same-evening closed bar (point-1 measured + point-2 PERSISTENCE_PRESENCE_MEASURED_2pts), labeled LAG_DECLARED_BY_OWNER; or (b) fund vintage/publish-timestamp measurement. Freeze σ-law thresholds (1σ/5σ/0.5σ tripwire) |
| OI-2 | IBKR Activity/Flex statement (all 4 spot/metals) | export to ~/.my-quantitative-data/ibkr_statement/ — the ONLY unmeasured cost component |
| OI-3 | XAU archive canonical pin | pin the forex-ng6 staging path (sha 49c2684e…, re-verified twice) or order a manifested copy |
| OI-4 | XAG independent archive | (a) owner downloads a silver daily CSV to the lane's owner_drop/ + "XAG archive dropped"; (b) declare IBKR panel-of-record under OI-1(a); (c) accept SLV proxy (weakest); (d) licensed feed (purchase authorization) |
| OI-5 | Certified futures chain + roll + entitlement (execution side only; signal side done) | name the certified source (licensed vendor / ICE/CME-direct / CONTFUT convention WITH synthetic disclosure) + enable IPE/NYMEX subscriptions if live quotes wanted; NATGAS: name AECO+TTF hub sources or drop those rows |
| OI-6 | Register the successor cycle | the lane's DRAFT_AMENDMENT_SUCCESSOR.md is the registration basis |
| M1-D | USDCAD/AUDUSD collector (M1-track item, unchanged) | recommended: accept permanent NOT_RUN this cycle; if wanted, option c (owner-named H1 source) dominates b |
| M1-CAL | M1 calendar variant election | N1 (recommended: LEARN 2026-06-27→2026-12-26, earliest eval 2029-12-29) vs N2 (2030-04-04) |
| SEALED-TAIL | ALREADY ANSWERED | stays SEALED — no-unseal operative in the plan |

## Earliest honest validation dates

| track | LEARN | fold 1 | earliest complete 6×26w evaluation |
|---|---|---|---|
| DAILY (4 pairs + EIA signals) | first 20% of 2020-10→2026-09 daily calendar | on registration | **on registration + 8 test folds** (feasible once OI-1/OI-2 land; TODAY it remains 0/7 fully admitted) |
| M1 (EUR/GBP/JPY slate) — NO-UNSEAL N1 (recommended) | 2026-06-27→2026-12-26 | 2027-01-02 | **2029-12-29** (2030-01-05 strict) |
| M1 — N2 (slate fallback, corrected) | 2026-09-24→2027-03-25 | 2027-04-08 | 2030-04-04 |
| USDCAD/AUDUSD | — | — | NOT_RUN (per D-4 recommendation) |
| Futures execution | — | — | BLOCKED until certified chain (3 legs measured FAIL + costs NOT_RUN_STATEMENT) |

## Next gate

Register the DAILY-track successor cycle (its plan draft is assembled
from DAILY_ADMISSION_MATRIX §5 + the existing plan skeleton; freeze →
A7 → its own GO). The M1-track registers when the owner elects its
calendar variant (N1 recommended) — no scored cell anywhere before a
new cycle's own freeze + A7 + GO.
