# OUTCOME_EXPOSURE_MAP — PORTFOLIO-ROUTER-12ASSETS-100K-V1 (DRAFT 2026-09-28)

Maps every planned outcome of the cycle to (a) the evidence artifacts it
produces, (b) the outcome-data exposure it creates (what PnL-shaped numbers
become visible, to whom, at which stage), and (c) the terminal action bound to
it. Exposure discipline: numbers seen pre-authorization may KILL (selection-
phase / smoke law P-15) but never select or rescue; every exposure is
disclosed at terminal.

| Stage / outcome | Evidence produced | Exposure created | Bound terminal action |
|---|---|---|---|
| Census (DONE, pre-GO) | CENSUS_1200.tsv + counts + shortlist | NONE — zero outcome-shaped numbers; sorting rubric frozen pre-PnL | n/a (research artifact) |
| State-engine census (post-GO, pre-PnL) | episodes/dwell/occupancy/margin-to-floor per state per train fold | state occupancy statistics only — no PnL | any floor fail ⇒ NOT_RUN_THIN rows (permanent FLAT); ≥2 states fail ⇒ close `ROUTER_STATES_THIN` |
| Representation-rho battery | rho tables vs RGC-G2 / FXFV3-A6 / drawdown-hysteresis / FXFV8-A5 observables | correlation numbers (no PnL) | any |rho|>0.20 ⇒ that variable's state layer dead — no substitution |
| Sleeve admissions | per-sleeve F-0 + PIT + ×2.0 after-cost TRAIN books | TRAIN-fold expectancy/PF per sleeve (exposed to admission court ONLY; kill-capable, not rescue-capable) | fail ⇒ SLOT_LEFT_EMPTY; pass ⇒ sleeve frozen into slate |
| Inverted-router kill (pre-tuning) | inverted-table TRAIN run | TRAIN PnL-shaped (kill use only, disclosed as SMOKE-class) | inverted ≈ primary ⇒ close `ROUTER_TABLE_UNINFORMATIVE` at 0 test folds |
| Scored test folds (post A7 + GO) | per-fold books, baselines B0–B8, ledger rows | FULL PnL exposure — the cycle's irreversible information spend | PASS bars P1–P7 evaluated verbatim; no re-tune (freeze law) |
| Robustness battery | stress/LOAO/LOCO/corruption/DSR/PBO artifacts | same books under perturbation | binding per protocol §7 |
| Reproduction twin | byte-compare ALL_MATCH report | none new (self-consistency only — P-4 caveat recorded) | mismatch ⇒ TECHABORT + incident |
| Terminal A7 + two-half close | audit + ledger + FAMILY_FAILURES/MAP/LESSONS rows | verdict + denominators published | whichever typed outcome the bars produce; reopening condition stated once |

Sequencing invariant: nothing in rows 2–5 may run before registration; nothing
in row 6 may run before A7 prelaunch AUTHORIZED + fresh owner GO at the scored
gate (two-key). Any accidental early exposure ⇒ `DIAGNOSTIC_OUTCOME_EXPOSED`
label + incident + owner notification, and the exposed configuration is never
selected (ERP1-TRACKA-1 law).
