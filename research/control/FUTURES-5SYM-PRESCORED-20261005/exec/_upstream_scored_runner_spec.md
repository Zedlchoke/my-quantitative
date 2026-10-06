# ============================================================================
# [EXTRACT/PROVENANCE] _upstream_scored_runner_spec.md
# Verbatim byte-exact extraction (blob sha256 932425c7c1104588b4b4ba265686663f4bc85afdf63300bac2812111340d257f) of
#   research/control/FUTURES-ES-PB1-V1/gate6/scored_runner_spec.md
# from branch prep/futures-es-reg-20261004 (FUTURES-ES-PB1-V1), commit a855dab809be73c4b6eef60ab8c41566532febcd.
# Branch-tip revision; upstream v1 execution contract (HISTORY) — design
# lineage for RUNNER_SPEC_V2.md.
# Extracted 2026-10-05 by LANE-EXEC, cycle FUTURES-5SYM-PRESCORED-20261005,
# via `git show prep/futures-es-reg-20261004:<path>` — read-only evidence extraction; the
# futures-es-reg worktree was NEVER written. Evidence only; not executable
# authority for the PRESCORED cycle.
# ============================================================================

# scored_runner_spec — FUTURES-ES-PB1-V1 gate 6 execution contract (v1, written pre-GO)

- Lane: DA45-GATE6 (Part B) · 2026-10-05 · worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`,
  branch `prep/futures-es-reg-20261004`, HEAD at spec-writing
  `456dac6bc75f84ea860a977068568f9688053743`.
- **This spec authorizes nothing.** It is the execution contract the
  GO-authorized scored runner must satisfy. Every refusal below is a
  fail-closed gate: the runner REFUSES (`NOT_RUN`, zero denominator
  consumption) rather than approximating.
- Authority order for the runner: (1) typed owner GO; (2) registered plan
  `plans/PLAN_futures_es_pb1_v1.md` (ROOT); (3) SPEC_PB1_ES r3 + freeze
  v-final + correction laws; (4) this spec. CLAUDE.md/HANDBOOK discipline
  (no push/merge/S1/orders; write boundary; heavy-lock law) applies
  throughout.

## 1. Refusal gates (fail-closed; checked in order; ANY failure ⇒ REFUSED, nothing written outside `gate6/refusal_record.json`)

| # | gate | pass condition | refusal verdict on failure |
|---|---|---|---|
| R1 | **NO_GO** | a GO record exists containing the EXACT typed phrase `GO FUTURES-ES-PB1-V1 SCORED EXECUTION` (registered plan §5 law; REGISTRATION_PACKET §5 F-A5 resolution — no aliases, no paraphrase), typed fresh by the OWNER (never delegated) at this cycle's own gate, and the registry row (`plans/CYCLE_REGISTRY.json`, ROOT) for `FUTURES-ES-PB1-V1` carries `go_phrase` exactly equal to that string. A paraphrase, early GO, or a GO in any prompt/chat is intent only and dies unconsumed ⇒ refuse. | `REFUSED_NO_GO` |
| R2 | **NO_AUTH (A7)** | prelaunch A7 (key 1 of 2) verdict exists and is `AUTHORIZED_WITH_FINDINGS` with **0 HIGH / 0 CRITICAL unresolved** — currently `a7_v2/A7_PRELAUNCH_V2.md` (sha `24c2e38d…`). If the operative surface changed after that audit, a fresh A7 must exist for the changed surface. | `REFUSED_NO_AUTH` |
| R3 | **LOCK** | `researchctl.py locks inspect` ⇒ `FREE_PROVEN`, immediately followed in the same orchestration step by `governance.heavy_lock.acquire(cycle_id="FUTURES-ES-PB1-V1", role="SCORED-EXECUTION", worktree=<this worktree>, command=<runner argv>, expected_artifacts=<§4 outputs>)`. `LockBusyError` ⇒ **`NOT_RUN_RESOURCE_CONFLICT`** — never wait, never kill, never touch the foreign worker; one heavy job machine-wide. `HeavyLockError` (registry malformed / CONTROL_STATE_DRIFT) ⇒ refuse fail-closed, file preserved, report to controller. | `NOT_RUN_RESOURCE_CONFLICT` / `REFUSED_CONTROL_STATE_DRIFT` |
| R4 | **DRIFT (input gate)** | every §3 input re-hashed pre-run and matched against its pin (table below); freeze round-trips (`selection_freeze_v2.exclude_list.sha256` == sha256(`exclude_list_v2.json`); identity_table sha `6e391980…`; Variant-A cost arithmetic asserts + retired-value ban `1.386/21.006/33.506/46.006` absent). ANY mismatch ⇒ abort pre-write. | `REFUSED_DRIFT` |
| R5 | **ADJUDICATION CLOSURE** | the two remaining implementation pins D-A4/D-A5 are either (a) owner-acknowledged per `pins2/DA45_DECISION_PACKET.md` §2.5/§3.3 one-liners, or (b) standing as adjudicated (both classified AUTHORITY_EXISTS — SPEC-text dispositive). The scored run consumes the adjudicated readings verbatim; any DIFFERENT choice is a freeze amendment (with gate re-runs), not a runner option. | `REFUSED_PINS_UNRESOLVED` (only if owner ordered a non-adjudicated variant) |

## 2. Inputs (all re-verified at R4 before any compute)

| input | path | sha256 pin |
|---|---|---|
| SPEC of record | `research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md` | `445f7499…` |
| **Freeze v-final (operative)** | `research/control/FUTURES-ES-PB1-V1/repair/selection_freeze_v2.json` | `cf150e24…` |
| Exclude list v2 | `research/control/FUTURES-ES-PB1-V1/repair/exclude_list_v2.json` | `67060c8c…` (round-trip vs freeze field) |
| Repair authority | `research/control/FUTURES-ES-PB1-V1/auth/PREGO_REPAIR_RECORDED.json` | `db0360fa…` |
| Holiday evidence | `research/control/FUTURES-ES-PB1-V1/holiday/pdf_equity_evidence_2011_2015.json` | `f3a8b4d4…` |
| Donor correction law | `research/control/FUTURES-ES-PB1-V1/repair/DONOR_LAW_CARRYOVER.md` | `314ae947…` |
| **Machinery of record** | `research/control/FUTURES-ES-PB1-V1/dryrun_v2_1/dryrun_builder_v2_1.py` (scored adaptation: outputs under `gate6/scored/**` + ledger rows; all mechanics UNCHANGED) | `00141bf0…` |
| Pinned panel | `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache/es_1m_outright.parquet` (7,825,657 bars) | `7ae6de2d…` |
| Held chain | `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache/es_chain_T5.parquet` (4,204 sessions) | `7b6179d2…` |
| D-A4/D-A5 adjudication | `research/control/FUTURES-ES-PB1-V1/pins2/DA45_DECISION_PACKET.md` + `da45_decisions.json` | `3acc6e9d…` / `76fd46c0…` |
| Trial ledger | `research/control/FUTURES-ES-PB1-V1/gate6/trial_ledger.py` (this package) | re-hashed at run time |

Panel/chain are accessed as **single-shot reads under the held heavy lock**;
no other panel/parquet access anywhere in the runner.

## 3. Execution sequence (post-refusal-gates)

1. **Twin pass 1** — full scored run of the frozen 24 identities from the
   freeze bytes over the single-shot panel read; per-identity results to
   `gate6/scored/pass1/<identity>.json` + `trades_index.json`.
2. **Twin pass 2** — independent full pass (re-reads EVERY input from disk);
   outputs to `gate6/scored/pass2/**`.
3. **G8 byte-match** — per-identity JSONs byte-identical across passes AND
   identical trades-index sha256; mismatch ⇒ `FAIL` on G8, results quarantined
   as non-publishable (identity still counted OBSERVED — computed).
4. **Ledger writing** — one terminal row per identity into the 24-slot
   append-only ledger (`gate6/ledger/trial_ledger.jsonl`): status `PASS`/`FAIL`
   per the pre-declared gate set (SPEC §8 G1-G9 mechanics evaluated by the
   digest module — NOT by PnL quality judgments of this spec), `observed`
   incremented for every computed scored result (publication failure still
   counts; REFUSED/NOT_RUN do not — registered plan §6 denominator law).
5. **Digest + manifest** — `gate6/scored/scored_digest.json` (machine mirror:
   pass criteria, lock record with acquire/release timestamps, input sha
   table, twin verdict, ledger sha).
6. **Release heavy lock** in `finally` (`FINISHED`, or `FAILED` + stderr tail).
7. **Terminal A7 hook (A7-TERM)** — hand the digest + ledger + twin manifests
   to a fresh-context terminal audit; terminal outcome is pre-decided from
   SPEC §9 (`FUTURES_ES_V1_REJECT_ALL` · `…_NO_ELIGIBLE_IDENTITY` ·
   `…_SURVIVOR_PENDING_S1` · `…_BLOCKED_<reason>`). The runner itself never
   selects the terminal outcome and never publishes.

## 4. Outputs (write boundary: `research/control/FUTURES-ES-PB1-V1/gate6/**` + `dispatch/handoff_SCORED-*.json` ONLY)

```
gate6/scored/pass1/<24 identity JSONs> + trades_index.json
gate6/scored/pass2/<… byte-identical …>
gate6/scored/scored_digest.json
gate6/ledger/trial_ledger.jsonl          (append-only, 24 terminal slots)
gate6/refusal_record.json                (written even on REFUSED paths)
gate6/GATE6_SCORED_REPORT.md             (post-run report lane)
```

`expected_artifacts` passed to `heavy_lock.acquire` = the seven paths above.
Nothing else is written; no registry write except the lock registry rows the
governance module itself maintains; budget counter updates happen ONLY
through the cycle registry's own tooling by the controller — the runner
records `observed` counts in the ledger and the digest, never edits
`CYCLE_REGISTRY.json`.

## 5. Invariants the runner must preserve (from the adjudicated pins + ratified laws)

- Identity enumeration: EXACTLY the frozen 24 (`selection_freeze_v2.identity_table`,
  byte-exact, order and set); any extra/missing/unparseable id ⇒ abort.
- D-A4 (adjudicated AUTHORITY_EXISTS): q80/SL donor windows CHAIN-WIDE
  strict-past; trading fold-fenced via frozen eval windows + per-fold-head
  positional warmup carve-outs. D-A5 (adjudicated AUTHORITY_EXISTS): costs
  booked as USD lines per side at the pinned Variant-A table; fill prices
  unadjusted; TP/SL levels from the fill price (R=2).
- Cost contract: Variant A only (all-in/side 21.00/33.50/46.00; RT ×2;
  window rows −0.01; retired values 1.386/21.006/33.506/46.006 asserted
  absent); labels MODELED COST / VERIFIED_VS_ACCOUNT NOT_RUN (never upgraded).
- Outcome-blindness up to this gate: no quarantined rehearsal numeric may be
  consumed by the runner; the scored run is the FIRST PnL computation.
- Determinism: fixed `generated_utc` constant; no wall-clock inside compute
  paths; two-pass byte-match is the evidence.
- No S1, no network, no orders, no push/merge, no `git add -A`; root
  read-only; Python = ROOT `.venv`.

## 6. What remains NOT_RUN in this lane (honesty)

This spec is a contract, not the runner. The GO-authorized run will consume
exactly §2 + §3. The synthetic smoke test (`gate6/synthetic_smoke_test.py`)
verifies the ledger/refusal/twin BOOKKEEPING infrastructure only, on
fabricated SYNTHETIC data — it computes zero real-outcome PnL and is not a
gate on anything.

— End scored_runner_spec.
