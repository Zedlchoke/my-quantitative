# DRYRUN_REPORT — FUTURES-ES-PB1-V1, gate 4 (exact-arm dry-run)

Lane **DRYRUN** · 2026-10-04 · worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep` (branch `prep/futures-es-reg-20261004`) · HEAD at start/end **`42885fafd991025499a4da15ed3c54316d9549a6`** (status clean at start; only untracked `research/control/FUTURES-ES-PB1-V1/{dryrun,dispatch}/**` added by this lane; no tracked file touched).

> **QUARANTINED DESCRIPTIVE-ONLY — NOT SCORED — ZERO DENOMINATOR CONSUMPTION — pre-GO rehearsal per registered plan §4 gate 4.**
> Every numeric output below and every file under `dryrun/quarantine/**` + `dryrun/quarantine_rerun/**` is a rehearsal artifact. Budget counters untouched; observed denominator NOT incremented; zero scored cells consumed; nothing here is a gate on PnL quality and nothing is publishable as a result. **NO GO exists or is implied** — the typed owner GO (`GO FUTURES-ES-PB1-V1 SCORED EXECUTION`, plan §5) remains the only key 2.

## 1. What ran

- Single-shot rehearsal of the **exact frozen 24-identity set** (`selection_freeze.json` identity_table, byte-exact) over the full chain span (held T-5 chain `es_chain_T5.parquet`, 4,204 sessions 2010-06-07..2026-10-01) at **×1.0 declared Variant-A costs** (plan §2, owner D3 "tôi chọn 2.25$"; embedded in the selection freeze; retired values 1.386/21.006/33.506/46.006 asserted absent).
- Data: pinned panel `es_1m_outright.parquet` (7,825,657 bars; sha `7ae6de2d…`, pin-verified pre-run) + held chain (sha `7b6179d2…`, pin-verified). Zero network; root `.venv` only; single-shot panel reads.
- Machinery: `dryrun/dryrun_builder.py` (sha `867946f3f1057049c7a1df7637494f15ac6dabaa4f801aa8abeea9f25878e3ee`) — every mechanic cites SPEC §1-§7 / plan §2 / PLAYBOOKS §1 in code comments and in every output record. Two independent full passes (each re-reads every input from disk) → `quarantine/` and `quarantine_rerun/` (byte-identical).
- Frozen surfaces applied unchanged: exclude_list.json (sha round-trip vs freeze embed PASS; 1,278 in-panel exclusions), fold structure (F1 2010-06..2012-12 · F2 2013-01..2017-12 · F3 2018-01..2021-12 · F4 2022-01..2026-09), per-fold 252-session positional warmup carve-outs, eval surface 2,926 sessions (375/950/711/890 — reproduced **exactly** from window−excluded, first/last dates matching the freeze).

## 2. Pass criteria (the gate's own pass — NOT PnL quality)

| criterion | result | evidence |
|---|---|---|
| **(a) Identity enumeration** — exactly the frozen 24, byte-exact, zero extras, zero missing | **PASS** | simulated id list == `selection_freeze.identity_table[].id` (order AND set equal; extras `[]`; missing `[]`); any unparseable id would abort |
| **(b) Cost recomputation** — 20 sampled trades recomputed by independent arithmetic vs Variant-A pinned table | **PASS** | 20/20 exact: side = fees(2.25; 2.24 in 2014-10-01..2017-12-31) + spread 6.25 + tier slippage (12.50/25.00/37.50); RT = ×2 (e.g. S2 normal RT 67.00; S2 window RT 66.98 on 2017-08-29); gross = dir×(exit−entry)×50 verified too. Sample rows in `dryrun_digest.json` |
| **(c) Determinism** — builder re-run yields identical outputs | **PASS** | trades-index sha256 identical across passes: `db728f5c13c09aa39e6e432daf1670706651fc8df101b46cf5b99e98aeed77fd`; all 24 per-identity JSONs byte-identical between `quarantine/` and `quarantine_rerun/` (held across three full runs total) |

**Gate 4 verdict: PASS** (a ∧ b ∧ c). Machine mirror: `dryrun/dryrun_digest.json` (sha `96aa2d849b8290159ad995d96567d898ffe5ad62633ad3274364774c0f7ca682`).

## 3. Per-identity trades (QUARANTINED descriptive counts — fold × identity)

| identity | F1 | F2 | F3 | F4 | total |
|---|---|---|---|---|---|
| FBES1-PB1-{CONT,REV}-UP-D0-S2 | 39 | 99 | 68 | 83 | 289 each |
| FBES1-PB1-{CONT,REV}-UP-D30-S2 | 39 | 99 | 68 | 83 | 289 each |
| FBES1-PB1-{CONT,REV}-DN-D0-S2 | 37 | 84 | 66 | 77 | 264 each |
| FBES1-PB1-{CONT,REV}-DN-D30-S2 | 37 | 84 | 67 | 77 | 265 each |
| FBES1-PB1-{CONT,REV}-UP-D0-S1 | 39 | 99 | 68 | 83 | 289 each |
| FBES1-PB1-{CONT,REV}-UP-D0-S3 | 39 | 99 | 68 | 83 | 289 each |
| FBES1-PB1-{CONT,REV}-DN-D0-S1 | 37 | 84 | 66 | 77 | 264 each |
| FBES1-PB1-{CONT,REV}-DN-D0-S3 | 37 | 84 | 66 | 77 | 264 each |
| FBES1-PB1-{CONT,REV}-UP-D0-S2-FOMCIN | 1 | 1 | 5 | 2 | 9 each |
| FBES1-PB1-{CONT,REV}-DN-D0-S2-FOMCIN | 0 | 2 | 0 | 0 | 2 each |
| FBES1-PLA-D0-S2 (C1) | 375 | 950 | 710 | 890 | 2,925 |
| FBES1-ALW-D0-S2 (C2) | 375 | 950 | 710 | 890 | 2,925 |
| FBES1-FLAT (C3) | 0 | 0 | 0 | 0 | 0 |
| FBES1-DOSE-D0-S2 (C4) | 369 | 934 | 705 | 882 | 2,890 |

Range: primaries 264-289; FOMCIN 2-9; C1/C2 2,925; C3 0; C4 2,890. q80 tail share 553/2,926 = **18.9%** (anatomy expectation ~20%). Full per-trade records (entry/exit ts, prices, cost application, skip counters) under `dryrun/quarantine/*.json` — **quarantined**.

## 4. Findings

**Ambiguities (law text quoted; none blocks gate 4; all MUST be pinned before scored execution gate 6 — a guessed parameter would be a new family definition, so they are declared pins here, not silent choices):**

- **D-A1 (q80 method)** — SPEC §3 L73-74: *"điều kiện |m| ≥ q80(|m|, trailing-252d, strict-past) — q80 từ anatomy (NQ dossier H4 refined spec; ES §8-H5), không tune"*. No interpolation method pinned in SPEC, ESNQ_HYPOTHESES, or the DEEPFOUR addenda. Pinned: `numpy.percentile(…, 80)` linear.
- **D-A2 (C2 direction)** — PLAYBOOKS L76: *"(C2) always-in-RTH baseline — CÓ PnL path ⇒ scored identity"*; L87 gives only "tier 2, cùng folds". Implemented: unconditional LONG, D0 entry, hold to era-correct close, no TP/SL (only reading consistent with "always-in").
- **D-A3 (C1 RNG)** — PLAYBOOKS L76: *"(seed cố định 20261002, sign-draw deterministic theo session)"*. Algorithm unstated. Pinned: `sha256("FBES1-PLA-D0-S2|seed=20261002|"+date)[0] < 0x80 → +1 else −1`.

**Implementation pins (declared, LOW):**

- **D-A4** — q80/SL windows chain-wide strict-past (not fold-fenced); trading fold-fenced. Corroboration: fold-fenced windows would leave F2-F4 eval heads trade-free for weeks, contradicting the frozen eval counts. **D-A5** — costs booked as USD lines at pinned table values; TP/SL levels derive from fill price.

**Facts:**

- **D-F1** — rehearsal caught a real FOMCIN defect in the first build: warmup-position FOMC days traded (6 of 15 CONT-UP trades, e.g. 2013-03-20, 2022-01-26) because FOMC_STATEMENT_DAY outranks WARMUP in the frozen list while the warmup carve-out is positional. Fixed (FOMCIN set requires date > fold `warmup_carve_out.last`); post-fix scan: **zero trades inside any warmup range across all 24 identities**. FOMCIN set 104 sessions.
- **D-F2** — single D0 fill-bar gap: 2020-03-16 (COVID limit-down open) lacks the 08:31 bar → deterministic no-fill skip, no imputation.
- **D-F3** — 7 eval sessions m-unavailable (2012-04-09, 2012-10-31, 2015-04-06, 2021-04-05, 2023-04-10, 2025-01-10, 2026-04-06; Easter-adjacent + 2025-01-10 mourning close) → no signal, E4-consistent.
- **D-F4** — 28 eval sessions with m == 0 exactly (open_0830 print-equal C_prev) → no direction (C4 skips; primaries tail=None).
- **D-F5 (LOW)** — C_prev last-RTH-print matches the baseline chain daily `close` on 4,142/4,204 sessions; the 51 differing sessions differ by exactly 1 tick (chain column uses a different final-print convention; the panel last print is the consumed law per freeze pin). RTH-open matches 4,193/4,204. Evaluation view only.
- **D-F6** — tail share 18.9% consistent with anatomy ~20%.
- **D-F7** — quarantine law honored end-to-end (see §5).

## 5. Lock record + zero-denominator statement

- Heavy-job lock: `researchctl.py locks inspect` at start → **`FREE_PROVEN`** ("no registry row and the lock file is not flocked"); re-inspected after the runs → **`FREE_PROVEN`**. No lock taken (single-shot reads per dispatch); no foreign worker touched; no conflict occurred.
- **Zero denominator consumption**: no ledger, counter, registry, or scored-cell write anywhere; the observed denominator was NOT incremented by anything in this lane; outputs exist only under `dryrun/quarantine*/**`; S1 SEALED_UNTOUCHED; zero network; root repo read-only.
- Write boundary: only `research/control/FUTURES-ES-PB1-V1/dryrun/**` + `research/control/FUTURES-ES-PB1-V1/dispatch/handoff_DRYRUN.json`.

## 6. Files

- `dryrun/dryrun_builder.py` — the machinery (sha `867946f3f1057049c7a1df7637494f15ac6dabaa4f801aa8abeea9f25878e3ee`)
- `dryrun/quarantine/` — pass-1 outputs: 24 per-identity JSONs + `summary.json` + `trades_index.json` (9.0 MB)
- `dryrun/quarantine_rerun/` — pass-2 outputs (byte-identical)
- `dryrun/dryrun_digest.json` — machine mirror (sha `96aa2d849b8290159ad995d96567d898ffe5ad62633ad3274364774c0f7ca682`)
- `dispatch/handoff_DRYRUN.json` — structured handoff `zcode_orch_v3_handoff@1`

## 7. Recommended next action

Controller: commit lane outputs by pathspec at the `42885faf…` lineage; route to **gate 5 — typed owner GO** (owner only, never delegated, canonical phrase per plan §5), carrying findings D-A1/D-A2/D-A3 as MUST-PIN-BEFORE-SCORED-G6 items for gate 6 scoping. No GO consumed or produced by this lane.

— End DRYRUN_REPORT.
