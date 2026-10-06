# FREEZE_BUILDER_SPEC_6J_6A — chain/builder contract for a future 6J/6A freeze (DRAFT)

- Lane FXJA, round FUTURES-5SYM-PRESCORED-20261005, PREP-only. This spec
  defines WHAT a future freeze builder must consume, build, hash and prove —
  it does not run today. **Status: NOT_RUN (builder not executed; hard-refuse
  conditions below are all currently armed).** 0 PnL, 0 scored runs.

## §1 Panels of record in THIS worktree (hash-verified 2026-10-05)

All paths worktree-relative; sha256 + size measured this lane from the
committed bytes:

**6J — committed annotated cache:**

| file | sha256 | bytes |
|---|---|---|
| `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/6J_cache/6j_annotated_1m.parquet` | `b8bae2b2540eaff92db71bcf51e26fd28b79d59e9a601864f7f94103c2b067ef` | 81,996,669 |
| `.../6J_cache/6j_outright_1m.parquet` | `e00d4f107c1ede078f93e89298cf45695e54f7ab00b9eaeee83a0833cbd50956` | 57,607,876 |
| `.../6J_cache/held_volume_k5.parquet` (baseline k=5 chain of record, 1,745 sessions) | `1da2923a649591f312b8dd1a5e77bda7f3b341f9fb9e6d2bf9b6af39fbdabdba` | 11,368 |
| `.../6J_cache/held_calendar_q.parquet` | `728f852f27a08fdc77bc736f942d84977ba25832bd8673da3e53fc7a155adf76` | 11,369 |
| `.../6J_cache/6j_sessions.parquet` | `39c405233ffc8e1c3cb31cc94cbfbd459e149bab363b4a1bca33a6512d8ff48b` | 885,115 |
| `.../6J_cache/6j_held_daily.parquet` | `d3976eb514ac55ed38e8a7128963c6fda2598794a1daebe86c76a1b785f1c3ee` | 125,445 |
| `.../6J_cache/contract_registry.json` | `676e56e778f8cfe0e0ec74989535e6c13d579797aa8e585384260daacd79677f` | 26,023 |

**6A — committed cache (no annotated 6A cache exists; the K6GATE lane
consumed the raw vendor roots):**

| file | sha256 | bytes |
|---|---|---|
| `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/6A_cache/outright_1m.parquet` (2,703,211 bars post-exclusion) | `801833c3e67adc8768df1feb3d71ff2e029388df9b30b777951f82b1c06bb595` | 76,487,923 |
| `.../6A_cache/registry.parquet` (instrument_id map) | `53c874a319d7f8101ddde2cf9965e81a0f3c538f0229b90f39cd573bcbdd4f85` | 16,478 |
| `.../6A_cache/chain_daily.parquet` | `689b5de383001f3b96e885061f4cc0f87170782e2447541bb101827ddd77a7c2` | 167,265 |
| `.../6A_cache/session_contract.parquet` | `e08f9113b69ad40bab85573c40a8e727d329f3b3c32f3029734dde6f696b949a` | 585,458 |
| `.../6A_cache/build_report.json` | `401b384d6c1f0c74fd643470cae5576cfe894bbc35ccdcd32ccc9e144ba66137` | 1,992 |
| raw vendor roots (read-only, outside repo): `/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet/{AV1B-O1M-6A-BACKFILL2, AV1R-O1M-6A-BACKFILL, AV1T-O1M-6A}` and the AV1*-O1M-6J twins | (hashed at freeze if consumed) | — |

**Evidence companions consumed by the builder:**
`dossiers_v2/6J_DEEP_v2.md` sha `ef95ad8d…` (39,094 B), `dossiers_v2/6A_DEEP_v2.md`
sha `76d32f1c…` (32,248 B); event/session JSONs `6J_a4_events.json`
`8dab9318…`, `6J_a2_sessions.json` `f1a70575…`, `6A_a4_events.json`
`429f6032…`, `6A_a3_term.json` `c20b90c7…`, `6A_a2_sessions.json` `d93995b5…`;
readiness lane artifacts in
`research/control/FUTURES-SIX-READINESS-20261004/fx_ja/` (sha256 list in
SPEC_6J/SPEC_6A_CONTINGENCY and the handoff).

**Pinning law (CYCLE_LAUNCH_DRAFT §1): the chain of record consumed by a
cycle must be re-hashed into the selection freeze at registration; any drift
vs these pins ⇒ BLOCKED, never silent reuse.**

## §2 Chain parameters

**6J:**
- Algorithm: PIT k=5 trailing-5-session volume crossover, decided at close
  t, effective t+1 (DC §1.3).
- **Cease-guard MANDATORY in the builder**: force-switch at the close of the
  first session where the held contract ceases (<25% bars or ≈0 volume)
  while the rule has not switched. The baseline k=5 chain of record
  (`held_volume_k5.parquet`) is committed WITH the known 2022-09-20
  held-dead artifact (U2 zero bars, dropped session); the builder must
  either (i) consume the baseline and carry the artifact as the flagged
  exception it is (the session enters no held-bar statistic), or (ii) run
  the explicit cease-guard variant — **ADOPT-D9, if ratified, makes (ii)
  the standing chain-builder; until D9 lands the default is (i) + measured
  + disclosed guard violations (fail-closed)**.
- Cross-checks (hard): derived chain == `held_volume_k5.parquet` transitions
  27/27 (dates + pairs); the 2022-09-20 exemplar reproduces (cease-guard
  trigger, Z2 125,303 lots vs stale mean 92,857.8 > 88,234.0, switch 09-21);
  mode split 19 abrupt / 8 gradual matches `rmm_mode_ledger.json`.
- Expectations: 27 rolls 2020–2026, 1,745 held sessions (baseline) /
  1,746 with the guard (the 09-20 session restored to the new contract).

**6A:**
- **Explicit cease-guard variant is the MANDATORY builder chain** (2 baseline
  violations measured — 2024-12-17 dead 6AZ4 while 6AH5 traded 55,675 lots;
  2026-06-16 dead 6AM6 while 6AU6 traded 55,533): 27 rolls, 0 violations,
  1,746 held sessions; switch dates == committed cease-guard dates 27/27;
  21 abrupt / 6 gradual triggers reproduced from raw.
- The declared-calendar rule chain (27 rolls, dates ~9–15d earlier) is a
  disclosed SENSITIVITY view, never silently substituted (RMM K6(c)).
- Identity via `6A_cache/registry.parquet` instrument_id map (2020–21
  identity by instrument_id + delivery-frame; definitions begin 2023-10).
- Exclusions: 1,584 `6BU5` contaminant bars; 914 instrument-7084 strays;
  calendar-spread rows never enter price stats.

## §3 Era-split parameters (6A; none for 6J)

- Era boundary: **era-1 = sessions ≤ 2020-11-20 (231 held sessions); era-2 =
  sessions ≥ 2020-11-23 (1,515)**; label from
  `6a_tick_adjudication.json:tick_break_locator` (count matches 231/231).
- Era-1 = **descriptive-only stratum forever** (K3-thin law: any fold fails
  the ≥5-per-fold floor) — the builder tags every output row with its era
  and refuses to emit pooled era-1+era-2 cost or tick-denominated statistics
  without an explicit era split column.
- Tick/cost branch: era-1 $10.00/tick (RT T1/1-tick $104.92 = 15.1794 bp);
  era-2 $5.00/tick ($54.92 = 8.2019 bp); no-back-cast law enforced at build
  time (builder error, not warning, if an era-2 cost constant touches an
  era-1 row).
- 6J has NO era split (tick measured constant across sampled eras: GCD 500
  int-nano in 2020-03 / 2023-01 / 2026-07 windows) — the AF4 6J same-date
  placebo relies on exactly this.

## §4 Builder outputs + twin contract

Outputs (deterministic, no conditional-on-signal statistics):
1. `chain_manifest.json` — per symbol: consumed files + sha256, algorithm
   params, roll table (27 rows: switch date, from/to, trigger, mode), held
   session count, guard-violation register (must be empty for 6A-guard;
   6J baseline carries the 1 flagged artifact).
2. `sessions.parquet` — held-chain session table (per-session bar count,
   volume shares, era tag for 6A).
3. `exclusions.json` — the fail-closed exclusion list (CALENDAR_PIT_POLICY
   §5) with per-entry reason + calendar provenance.
4. `cost_binding.json` — the consumed cost table (COST_CONTRACT ladders,
   ×1.0 gate column) + its source shas.
**Twin contract**: a detached reproduction twin re-derives 1–3 from raw
bytes and must match byte/logical (G8 shape); chain re-derivation digests
must equal the pinned §1 digests; any mismatch ⇒ BLOCKED, back to freeze,
never a mid-flight repair.

## §5 Pre-freeze gates — builder HARD-REFUSES while unsigned (draft refusal logic, NOT_RUN today)

The builder's gate check runs BEFORE any byte is read, in this order:

1. **6J gates (ALL required):**
   - **Owner 6J ceiling signature** (P5-D1) naming option J-A/J-B/J-C AND
     clock-shadow reading (a)/(b) — no cap exists; absence ⇒ REFUSE
     (`BLOCKED_NO_CEILING`).
   - **BBO/fill ruling** (P5-D3): conservative fill law accepted as fill
     model of record — absence ⇒ REFUSE (`BLOCKED_NO_FILL_LAW`).
   - **Cost posture**: fee A7 (D2) run clean, 0 HIGH/CRITICAL unresolved —
     absence ⇒ REFUSE any cost-bearing build (`BLOCKED_COST_FREEZE`, the
     COST_FREEZE_ERRATUM posture).
2. **6A gates (ALL required):**
   - **PB3 lift signature** (P5-D5 bundle) — absence ⇒ REFUSE everything
     (`BLOCKED_PB3_PARK`). Today armed.
   - **D8 ratification** (era-aware tick/cost law: Option A ratify measured
     boundary / Option B demand exchange document) — absence ⇒ REFUSE
     (`BLOCKED_D8_UNRATIFIED`). Today armed.
   - D9 cease-guard standing law + fee A7 (D2) for any cost-bearing build.
3. **Both:** registration freeze at the cycle's own gate (freeze set: spec
   sha + exclusion-list sha + identity-table sha + §1 chain digests + cost
   digest + calendar provenance manifest), then prelaunch A7, exact-arm
   dry-run, typed owner GO — in that order (CYCLE_LAUNCH_DRAFT §6).

**Today all 6J and 6A refuse conditions are armed: the builder is a draft.
Executing it would be NOT_RUN_RESOURCE-LAWFUL but AUTHORITY-ILLEGAL; nothing
was executed.**

— End FREEZE_BUILDER_SPEC_6J_6A. 0 PnL; hashes measured from committed
bytes 2026-10-05; no builder run; write surface confined to this lane.
