# PLAN — FUTURES-FX-V1 (6E/6B/6J scored cycle, pre-GO registration)

Registered per owner decision 2026-10-05 (PB2 lift following the dependency
chain, FX-A 44 + J-A 29; **NOT a typed GO**). Scored/PnL/S1/paper/live/
purchases/push/merge remain forbidden until the owner types the GO phrase.

- Branch/worktree: `prep/futures-5sym-prescored-20261005` @ `6f7819df…`
  (wave-5a). Evidence under `research/control/FUTURES-5SYM-PRESCORED-20261005/`.
- Scope: **73 identities** = 6E 22 + 6B 22 (FX-A CONV-D: F2 Policy-Decision +
  F3 US-8:30, delays {D0,D1B}, tier S2, reading (a); F1 excluded by FX-A
  composition, F4 POWER-DEAD owner-ratified exclusion, F5 NEEDS_EVIDENCE
  vintage-as-of) + 6J 29 (J-A: JF1 11 + JF3 11 EXECUTABLE; JF2 7
  REGISTERED-BLOCKED threshold, carried inside 29, never dropped — dry-run/
  scored MUST refuse those rows until owner unblocks P5-OD-4). Tables:
  `prego/fx_eb/IDENTITY_TABLE_FX_A_6E_22.json`, `..._6B_22.json`,
  `prego/fx_ja/IDENTITY_TABLE_J_A_29.json`; budget-max **73**.
- Chains: measured k=5 + cease-guard per SPECs; freeze bundles
  `prego/fx_eb/freeze_6e/` (stamp ed4288a9), `freeze_6b/` (c8f30511),
  `prego/fx_ja/freeze_6j/` (6c21a1b7) — GATE-0/1 passed, zero drift.
- Cost: D3 Variant A; FX group fee 2.47/side carried **DERIVED** (A7-tabulated
  nowhere; e.1 alias PARTIAL permanent per auth/fee_audit/); 6J RT $67.42 =
  8.4499bp T1 modeled; MODELED / VERIFIED_VS_ACCOUNT=NOT_RUN; BBO NOT_RUN.
- Laws: 6E/6B fold warmup = 60 held sessions (family law, strict-past); 6J =
  its own 252-session law; Globex template session law; fail-closed calendar
  exclusions; BoJ stamps NOT_IN_CORPUS; conservative fill + SL-priority.
- Gate sequence: registration → prelaunch A7 (0 HIGH/CRITICAL unresolved;
  must flag the DERIVED fee table + JF2 blocked rows) → exact-arm dry-run
  (quarantined; JF2 rows refuse) → **owner typed GO:
  `GO FUTURES-FX-V1 SCORED EXECUTION`** → scored under canonical lock → twin
  → terminal A7.
