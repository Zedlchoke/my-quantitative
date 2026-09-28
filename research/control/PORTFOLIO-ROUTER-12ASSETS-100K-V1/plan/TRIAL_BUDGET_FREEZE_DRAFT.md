# TRIAL_BUDGET_FREEZE_DRAFT — PORTFOLIO-ROUTER-12ASSETS-100K-V1 (2026-09-28)

Freezes the trial-accounting caps proposed to the owner at registration. Rationale
for the sizes (not just the numbers):

1. **Ledger rows ≤ 220.** Composition: state-engine grid 54 nodes (3×3×3×2,
   TRAIN-only, preregistered — no other grid exists); sleeve admissions ≤10
   sleeves × ≤4 pre-registered config variants = 40; baseline arms B0–B8 = 9
   arms × ≤10 folds counted once per fold-set execution = up to 90; kill-switch
   constants + allocation constants ≤ 6 preregistered trials; robustness
   variants ≤ 30 (×1.5/×2 costs, 12 LOAO, 5 LOCO, 3 corruption levels, ladder).
   Headroom ≈ 0 — the caps are the budget, not a floor.
2. **Scored test-fold arm-executions ≤ 64** (the expensive, exposure-creating
   class): router selected-config ≤ 10 (one per fold), B0–B8 ≤ 27 (9 arms pooled
   + per-fold where the protocol requires per-fold comparison), robustness
   ≤ 27. Any unused cap expires at close — it is not transferable.
3. **Why small vs 1,200:** DSR/PBO credibility. PBO at 64 candidate trials is
   interpretable; at 1,200 it is a foregone conclusion (~1.0) and every
   "survivor" would be arithmetically dead on arrival. The 548 dead-family
   variants and 554 data-blocked/unfalsifiable rows never consume budget by
   construction (never admitted).
4. **Denominators:** observed (every computed outcome, incl. publication
   failures and TECHABORTs with exposure) vs published — tracked separately in
   every report (P-9). Budget consumed = observed, not published.
5. **Overflow law:** hitting any cap ⇒ HARD STOP ⇒ owner decision packet
   (option A: close at current state; option B: preregistered amendment with a
   new identity for the增量). No silent growth; no "exploratory doesn't count".
6. **Zero-cell closes are valid:** `NOT_RUN_PIT_GATE_FAILED`,
   `NOT_RUN_INSUFFICIENT_CALENDAR`, `ROUTER_STATES_THIN` and
   `ROUTER_TABLE_UNINFORMATIVE` all close at 0 scored cells — cheaper than any
   survivor would be worth if the bars are unmeetable (P-27/P-28 doctrine).
