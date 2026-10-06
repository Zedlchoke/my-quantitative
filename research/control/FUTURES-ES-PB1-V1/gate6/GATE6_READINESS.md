# GATE6_READINESS — FUTURES-ES-PB1-V1, lane DA45-GATE6 (Part B)

- 2026-10-05 · worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`,
  branch `prep/futures-es-reg-20261004`, HEAD `456dac6bc75f84ea860a977068568f9688053743`
  (one bare `rev-parse` at start; `git status --porcelain` clean at start;
  no other git command; nothing committed/staged/pushed by this lane).
- **Zero real-outcome PnL computed by this lane.** Part B built and
  SYNTHETIC-tested infrastructure only. Every smoke artifact lives under
  `gate6/smoke/` behind a SYNTHETIC banner and gates nothing.
- Heavy-lock law: `researchctl.py locks inspect` at lane start →
  **FREE_PROVEN** ("no registry row and the lock file is not flocked"),
  re-checked FREE_PROVEN before the smoke runs. No lock taken (no panel
  access at all — the smoke test reads NO parquet); no foreign worker
  touched; no `NOT_RUN_RESOURCE_CONFLICT`. Registry row (ROOT, read-only):
  `go_phrase_state: REGISTERED_NOT_CONSUMED`, `budget {used: 0, max: 24}` —
  untouched by this lane.

## Component status (honest PASS / NOT_RUN)

| # | component | status | evidence |
|---|---|---|---|
| 1 | `gate6/scored_runner_spec.md` — the exact execution contract (inputs, refusal gates R1-R5, heavy-lock acquire/release protocol, twin byte-match requirement, terminal A7 hook, write boundary) | **PASS (written)** | the spec; inputs pinned to freeze v-final (`selection_freeze_v2.json` `cf150e24…`, `exclude_list_v2.json` `67060c8c…` round-trip, repair auth `db0360fa…`, donor carryover `314ae947…`), machinery of record `dryrun_v2_1/dryrun_builder_v2_1.py` `00141bf0…`, panel `7ae6de2d…` / chain `7b6179d2…`, D-A4/D-A5 adjudication `pins2/**` |
| 2 | `gate6/trial_ledger.py` — REAL 24-slot ledger implementation: observed-counter law, statuses NOT_RUN/PASS/FAIL/REFUSED, append-only hash-chained JSONL, refusal-event rows, twin manifest/compare bookkeeping | **PASS (implemented; smoke-verified)** | 28/28 smoke checks; module computes no PnL, touches no panel |
| 3 | `gate6/synthetic_smoke_test.py` — run to completion on fabricated data | **PASS (28 pass / 0 fail — ALL GREEN)** | `gate6/smoke/smoke_digest.json` + section evidence below |
| 4 | Refusal-gate wiring against the REAL registry / a real typed GO / real lock state | **NOT_RUN (by law)** — no GO exists (`REGISTERED_NOT_CONSUMED`); the gate logic is synthetic-verified only; R1/R3 will consume real inputs only inside the GO-authorized run | registry read-only row; `smoke` V2 |
| 5 | The scored runner itself (executing the 24 identities on the real panel, post-GO) | **NOT_RUN (by law — pre-GO)** | plan §4 gate 6 requires the typed owner GO first |
| 6 | Reproduction twin on REAL scored outputs (G8) | **NOT_RUN (by law)** — synthetic twin bookkeeping PASS only | `smoke` V5 |
| 7 | Terminal A7 | **NOT_RUN (by law)** — hook specified in `scored_runner_spec.md` §3.7 | — |

## What the smoke test verified (SYNTHETIC; 28 checks, all PASS)

- **V1 24-slot law** — ledger initializes ONLY with the frozen 24 identity
  ids (runtime set-equality assert vs `selection_freeze_v2.identity_table.
  embedded.identities`; freeze order = slot order); 23-slot init refused;
  fresh ledger = 24 × NOT_RUN, observed 0.
- **V2 refusal triggers fire** (declarations simulated, fail-closed):
  `REFUSED_NO_GO` ×3 (paraphrased historical GO string / delegated GO /
  registry mismatch), `REFUSED_NO_AUTH` ×2 (missing A7; unresolved HIGH),
  **`NOT_RUN_RESOURCE_CONFLICT`** (lock-held simulation), plus
  `REFUSED_CONTROL_STATE_DRIFT` (bad lock state), `REFUSED_DRIFT`
  (freeze-sha mismatch), `REFUSED_PINS_UNRESOLVED` (owner-ordered variant);
  allow-path passes R1→R5 in order.
- **V3 append-only behavior** — double-terminal refused; unknown slot
  refused; disk re-read + hash-chain verify PASS; tampering a non-final row
  on a copy breaks the successor chain link (detected); whole-file sha256
  changes under any tamper (final-row law).
- **V4 observed-denominator accounting** — synthetic results 11 PASS /
  5 FAIL (one `published=False`: publication failure STILL counts) / 3
  REFUSED / 5 NOT_RUN ⇒ observed denominator exactly 16 = PASS+FAIL;
  REFUSED/NOT_RUN never counted; resolving the 5 NOT_RUN slots to REFUSED
  completes all 24 slots WITHOUT moving the denominator (still 16).
- **V5 reproduction-twin bookkeeping** — two identical synthetic runs
  (24 files each) byte-match; a one-byte-perturbed run FAILS with exactly
  one differing file.

## What the GO-authorized scored run will consume (per `scored_runner_spec.md`)

- **Freeze v-final (operative):** `repair/selection_freeze_v2.json`
  (+ `repair/exclude_list_v2.json`, eval surface **2,925** = F1 375 /
  F2 949 / F3 711 / F4 890; warmup carve-outs 4×252 positional; FOMCIN set
  104; owner-ratified pins D-A1/A2/A3 embedded verbatim) — the v1/v2/v2.1
  rehearsal artifacts remain HISTORY/quarantine, never consumed by scoring.
- **Machinery of record:** `dryrun_v2_1/dryrun_builder_v2_1.py`
  (`00141bf0…`) adapted to scored mode — mechanics unchanged, outputs to
  `gate6/scored/**` + ledger rows.
- **Correction laws:** DONOR_LAW_CARRYOVER (SL-donor exclusion set = v1's
  139 sessions on v1 class labels) and the D-A4/D-A5 adjudicated readings
  (`pins2/` — both AUTHORITY_EXISTS, SPEC-dispositive; any different
  variant = freeze amendment, refused by gate R5).
- **Cost contract:** Variant A (all-in/side 21.00/33.50/46.00, RT ×2,
  window −0.01; retired 1.386/21.006/33.506/46.006 asserted absent; MODELED
  COST; VERIFIED_VS_ACCOUNT NOT_RUN).
- **Gates:** R1 typed GO `GO FUTURES-ES-PB1-V1 SCORED EXECUTION` (owner
  only) → R2 A7 `AUTHORIZED_WITH_FINDINGS` 0 HIGH/CRITICAL (`a7_v2`,
  `24c2e38d…`) → R3 heavy lock (inspect → `heavy_lock.acquire(cycle_id=
  "FUTURES-ES-PB1-V1", role="SCORED-EXECUTION", …)` → heartbeat → release
  in `finally`; `LockBusyError` ⇒ `NOT_RUN_RESOURCE_CONFLICT`, never kill a
  foreign worker) → R4 input-sha drift gate → two-pass scored run → G8
  byte-match → 24-slot ledger → digest → terminal A7 hook (pre-decided
  terminal outcomes, SPEC §9).
- **Denominator law:** every computed scored result counts (publication
  failure included); REFUSED/NOT_RUN do not; rehearsal/quarantined passes
  never counted (registered plan §6; implemented and smoke-verified in
  `trial_ledger.py`).

## Residual obligations carried to the owner/controller (NOT new)

1. Owner acknowledgment of the D-A4/D-A5 adjudication one-liners
   (`pins2/DA45_DECISION_PACKET.md` §2.5/§3.3) — formal only; both pins
   already classified AUTHORITY_EXISTS.
2. The typed owner GO — key 2 of 2, never delegated, exact string.
3. `VERIFIED_VS_ACCOUNT` remains NOT_RUN (cost model stays MODELED COST).
4. Controller commits lane outputs by pathspec at the `456dac6b…` lineage.

— End GATE6_READINESS.
