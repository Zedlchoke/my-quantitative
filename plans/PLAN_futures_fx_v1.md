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


## ADDENDUM (2026-10-06, LANE-FX-PREGO2 via controller): freeze-stamp supersession wave-6b

The freeze stamps cited above in the launch-freeze section — `prego/fx_eb/freeze_6e/` (stamp ed4288a9), `freeze_6b/` (c8f30511) — are HISTORICAL (pre-wave-6b). They are superseded at HEAD by the wave-6b re-freeze (lane WAVE6B; delta-verified by A7-DELTA-VERIFY): `freeze_6e` content stamp `d6a0c07e`, manifest file sha `8abeb37b`; `freeze_6b` content stamp `7d931c1c`, manifest file sha `f18790d2`. Cause of change: each FX freeze manifest grew exactly 4 dated-calendar input pins (`bls_dates.json` ad41d2a7, `ecb_decisions.json` 09eb980e, `mpc_decisions.json` e2df4de5, `collisions.json` 8e57e29d — ECB/MPC dated tables + BLS vintage artifact + pinned collision lists); re-freeze epoch `2026-10-06T12:00:00Z`. Identity tables (`c309d011` 6E / `23647771` 6B) and exclusion calendars (`2c76203b` 6E / `f709fe85` 6B) are BYTE-IDENTICAL to the bundles this plan originally pinned — no registered identity, budget, cost or scientific artifact changed. 6J (`6c21a1b7` / manifest `16b40279`) and NQ (`15ecbb6f` / manifest `3f33b42d`) are UNCHANGED. The operative pin set for FUTURES-FX-V1 execution is the NEW set; it is the set `dryrun_impl/dryrun_exec.py` BUNDLES pinned and the set the gate-3 exact-arm dry-run (`dryrun/quarantine/FUTURES-FX-V1/20261006T092238Z_31112`) consumed with `VERIFIED_NO_DRIFT`. Evidence: `calfix/w6b/W6B_REPORT.md` §2, `a7_prelaunch/delta6/`, `prego2/fx/PIN_SUPERSESSION_ADDENDUM.json` (re-hashed at prego2, HEAD b0be48c4).
