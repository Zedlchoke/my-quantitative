# FREEZE_BUILDER_SPEC_6E_6B — deterministic freeze builder per symbol (DRAFT; builder NOT_RUN today)

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **FXEB**, 2026-10-05. This document
  SPECIFIES a builder; **it does not run one.** Status: **NOT_RUN** (by design — the
  pre-freeze gate list below is unsigned, and the builder must hard-refuse).
- **CONDITIONAL-ON-PB2-LIFT DRAFT — PB2 HOLD (6E/6B) stands.** The builder is
  hard-refusing while ANY of the gate list is unsigned; PB2 lift is gate #1 and is NOT
  treated as given.

## 1. Committed inputs (located and hashed by this lane in THIS worktree; read-only
single-shot reads, locks FREE_PROVEN before/after)

### 1.1 6E inputs

| file | bytes | sha256 |
|---|---|---|
| `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/6E_cache/6e_annotated_1m.parquet` (3,054,311 rows per K6GATE §0.1) | 83,827,281 | `13ae3cd657bb140a05e73986838069d6e5ae197757ecfc1328c987305499077e` |
| `…/6E_cache/6e_outright_1m.parquet` | 79,396,559 | `fc9ca2a1f6e8a9b61f4b3352bfcd988738e65d808d9d7f28d71cdd0e989a70e2` |
| `…/6E_cache/held_calendar.parquet` (1,746 sessions) | 11,369 | `35aa5d0bb4e7943a7cc2a9a6a2fd2c4c89c71e412c4745b34f7d7f557a7a0231` |
| `…/6E_cache/contract_registry.json` | 34,516 | `0d5c577a21cd0b90ff63affa473d22e96ea703044443583525f9918c006148b6` |

### 1.2 6B inputs

| file | bytes | sha256 |
|---|---|---|
| `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/6B_cache/6b_annotated_1m.parquet` (2,549,633 rows per K6GATE §0.1) | 57,985,992 | `6133b0e7dec514b49de4c850585cb9c093bbbfca318f79b1db67a9b69166b322` |
| `…/6B_cache/6b_outright_1m.parquet` | 51,446,342 | `3e13a452e74d9770d1ce829a6bab94900ea4a839271c9db063dfd4aa7ff7f6dd` |
| `…/6B_cache/held_calendar.parquet` (1,746 sessions) | 11,369 | `dff43c4cab5f5419b07d9ac042480801b7ea7c039a037ecb9ea63aa8c179d09f` |
| `…/6B_cache/chain_calendar.parquet` | 134,805 | `9cc849c22d2c32e4cdc0b98d67c26b43918bf078036ce3ea34459c5eaf258801` |
| (registry) `…/6B_cache/contract_registry.json` | — | **NOT_OBTAINED** (6E-only artifact; official-calendar cross-ref substitutes) |

### 1.3 Calendar / cost authority inputs

Expiry JSON `FUTURES-SIX-READINESS-20261004/fx_eb/calendar/fx_eb_expiry_2023_2026.json`
sha256 `cf07d4e2…1ef07`; holiday JSON `…/holiday/holiday_deviation_6e_6b.json` sha256
`07d60a7e…c4821`; roll JSON `…/cost_roll_events/cost_roll_events_fxeb.json` sha256
`a99a6983…40052`; fee authority `FEES_CORRECTED.md` sha256 `006d6372…5d1bef` + A7
`A7_FEE_REAUDIT.md` sha256 `2c1095d6…211ad`; identity/ budget
`FUTURES-SIX-SCORED-GATE-PREP-20261004/budget/IDENTITY_TABLES.md` sha256 `750858ab…f6e6`.
(Full 64-hex values in `SPEC_6E.md`/`CALENDAR_PIT_POLICY_6E_6B.md`/handoff outputs.)

## 2. Builder spec (deterministic; one invocation per symbol)

- **Chain params**: held chain = `held_calendar.parquet` (session_date + held label);
  held-contract restriction ON (raw_symbol prefix == held label; K6GATE §0.7 law);
  roll switches = the 27 measured switch dates per symbol from the roll JSON (freeze
  re-reads and re-verifies them against the chain; drift ⇒ REFUSE); session mask =
  17:00 CT (D-1) → 16:00 CT + 60-min break, segment columns from the annotated parquets.
- **Expiry binding**: official last-trade dates ONLY from the expiry JSON OBTAINED
  cells; NOT_OBTAINED quarters (6E: ECU26/ECZ26; 6B: 2023Q1–2024Q2) ⇒ per-quarter
  EXCLUDE (fail-closed). No IMM/rule derivation anywhere.
- **Exclusion list synthesis** (deterministic, from CALENDAR_PIT_POLICY §3): 6E — the
  2023-11-24 early-close session + 93 fail-closed neighborhood cells + aged-out-window
  neighborhoods; 6B — empty exclusion list WITH the 0/42 hole declared verbatim in the
  manifest. Exclude-list sha recorded; not editable post-GO.
- **Outputs** (per symbol, one JSON + one binary manifest):
  1. `freeze_manifest_<SYM>.json` — input digests (§1), chain params, roll switch table,
     exclusion list + sha256, cost-table digest (COST_CONTRACT §3 row for that symbol),
     identity-table sha (signed CONV-D option slice), fold boundaries + warmup + K-views,
     verdict-criteria digest (SPEC §9), PB2-lift + ceiling + CONV-D + reading + placebo
     ruling reference IDs and their recorded signatures.
  2. `freeze_selection_<SYM>.parquet` — the exact evaluable session index per symbol
     (post-exclusion), with fold assignment.
- **Twin contract**: a detached twin process re-derives 1–2 from the committed inputs and
  must produce byte-identical manifests (chain re-derivation digests equal the pinned
  §1 digests); mismatch ⇒ BLOCKED (G8-class).
- Determinism law: no wall-clock, no network, no RNG in the builder (any C1 seed is
  consumed by the runner, not the builder; the single lawful seed 20261002 is recorded
  as a constant in the manifest).

## 3. Pre-freeze gate list (ALL required; ordered)

1. **PB2 lift** (owner; PB2_ANCESTRY_COURT_DRAFT §d consumption order; today HOLD).
2. **FX ceiling signature** naming CONV-D vs census-native + option (FX-A/B/C) +
   clock-shadow reading (a)/(b).
3. **CONV-D convention signature** incl. core delay slots (P5-OD3).
4. **Fee layer complete**: clean A7 against the account (today NOT_RUN) + reg-basis
   ruling (P5-OD7) + e.1 alias corroboration.
5. Calendar posture acknowledged: 6E fail-closed lists; 6B 0/42 + expiry gaps (D12).
6. FX-C only: DC §1.3 RMM ruling; placebo-budget ruling (if any expansion).
7. Court §b1.1 1m trigger-time anatomy (F1 families) — NOT_RUN today.

## 4. Draft refusal (the exact hard-refuse the builder emits while unsigned)

```
FREEZE REFUSED — FUTURES-5SYM-PRESCORED-20261005 / FXEB / <SYM>
refusal_id: P5-FREEZE-REFUSAL
reasons:
  [G1] PB2 HOLD stands (6E/6B) — owner lift absent. NOTHING may freeze.
  [G2] FX ceiling signature absent (no cap exists; CONV-D/census-native unnamed).
  [G3] CONV-D convention + delay slots unsigned (P5-OD3).
  [G4] Fee layer incomplete: VERIFIED_VS_ACCOUNT=NOT_RUN; reg basis unruled (P5-OD7).
  [G7] Court b1.1 1m trigger-time anatomy NOT_RUN (F1 families).
action: ZERO files written; freeze_builder_status = NOT_RUN; no retry scheduled.
law: PB2_HOLD_RESTATE.md sha256 88386aa3...5a75b; dispatch interpretation_law 2026-10-05.
```

Current status of this builder: **NOT_RUN — refused-by-design today.** No invocation is
scheduled; the refusal draft above is what any premature invocation must print.

— End FREEZE_BUILDER_SPEC_6E_6B.md. Conditional-on-PB2-lift; 0 files frozen.
