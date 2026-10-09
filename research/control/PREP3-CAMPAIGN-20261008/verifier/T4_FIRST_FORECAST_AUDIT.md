# T4 — FIRST REAL PROSPECTIVE FORECAST AUDIT (independent fresh context)

- Cycle: `PREP-FUTURES-Q1Q2Q3-20261007` (campaign `PREP3-CAMPAIGN-20261008`), task `Q1-FIRST-FORECAST-AUDIT`, role AUDITOR, lane AUDIT-T4.
- Date of audit: 2026-10-09 (14:06–14:20Z). Auditor repaired nothing, deleted nothing, pushed nothing; single read-only TWS historical re-read (clientId 9417) for the G3 root cause.

## OVERALL VERDICT: **PASS_WITH_FINDINGS**

All nine audit checks PASS on their lawful criteria. The first real forecast rows are valid evidence: ledger chain intact, timestamps lawful, inputs legal, pins intact, features and forecasts reproduce EXACTLY from saved bytes and pinned constants. Findings F1/F6 are operational (no row invalidity); F2/F3/F4/F5 are LOW.

Re-measured baseline: lane worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-q1q2q3-prep/prep`, branch `prep/futures-q1q2q3-prep-20261007`, HEAD `12854f32a2a51859c44c35008db195124dbbb3eb` (matches dispatch; porcelain-clean). Root main at audit start `4c545247e604c262dcb182c03d66d816377b6e33`.

---

## Check 1 — Ledger: PASS

`prospective/ledger_q1_prospective.jsonl` (lane worktree): exactly **2 lines**, both `record_type=forecast`, `session_date=2026-10-09`, symbols **ES + NQ**, both `status=FORECAST_ISSUED`. File sha256 `02204cc0…3df5`.

Per-line shas (bytes + trailing newline, the collector's own convention):
- line 1 (ES): `218d4fd501bd40035ffb47ed1c09fc9f20b7ffa9a05a807b8336f7aede255db2`
- line 2 (NQ): `c5616cf18119fb2f89379a5f7a8ec112d4308cf9136799ee306657f75e15b5fb`

Both match the `ledger_line_sha256` values in the `FORECAST_ISSUED` ops entry. Append-only chain: row 1 `prev_line_sha256=null` (first row, lawful); row 2 `prev_line_sha256 == sha256(line1 bytes + "\n") = 218d4fd5…` — VERIFIED, line 1 unmodified. No other prospective ledger exists (root checkout has no such dir).

## Check 2 — Timestamps (core check): PASS

| quantity (UTC) | ES | NQ |
|---|---|---|
| `bar_completed_at` | **2026-10-09T14:00:00Z** (exact) | **2026-10-09T14:00:00Z** (exact) |
| `data_arrival_at` | 2026-10-09T14:03:12Z | 2026-10-09T14:03:16Z |
| `forecast_made_at` | 2026-10-09T14:03:16Z | 2026-10-09T14:03:16Z |
| issue deadline | 2026-10-09T10:05:00-04:00 = 14:05:00Z | same |

Inequalities, stated explicitly (both symbols):
1. `bar_completed_at == 14:00:00Z` exactly — TRUE.
2. `14:00:00Z < data_arrival_at < 14:05:00Z` — TRUE (ES 14:03:12Z; NQ 14:03:16Z).
3. `14:00:00Z < forecast_made_at < 14:05:00Z` — TRUE (14:03:16Z).
4. `forecast_made_at >= data_arrival_at(ES)` — TRUE (14:03:16 ≥ 14:03:12).
5. `forecast_made_at >= data_arrival_at(NQ)` — TRUE (14:03:16 ≥ 14:03:16, equal; the write follows the second fetch return in the same second).

Raw `fetched_utc` equals each row's `data_arrival_at` (14:03:12Z ES / 14:03:16Z NQ). Today's ops events (refusals 14:01:02Z, 14:02:54Z; issue 14:03:16Z = 10:03:16 ET) are all inside the approved window `[10:00:00, 10:05:00)` ET (amendment 34, owner auth 36 = commit `df212b28`).

## Check 3 — Input legality: PASS

Recomputed sha256 of the saved raw files vs the rows' recorded `raw_sha256`:
- ES `raw/2026-10-09/ES_Z6_2026-10-09_m1.json`: `fdd4e0ec54d45feffcb4f3bd599535089ef62d3d29827bb25bec6f9d081296d8` — MATCH.
- NQ `raw/2026-10-09/NQ_Z6_2026-10-09_m1.json`: `3657679843c65e9afbbc9da2527cae75e567e2c2512764fc87552551c33f5ff8` — MATCH.

Max bar-start in the saved input: **2026-10-09T13:52:00Z (09:52 ET)** for BOTH symbols — **no bar with start ≥ 2026-10-09T14:00:00Z exists** (epoch-ns check vs cutoff 1791554400000000000: TRUE for both). Both symbols present. Bars are 23 contiguous 1-min bar-starts 09:30–09:52 ET, zero non-60 s gaps, all closes > 0. Recorded request: `endDateTime 20261009-14:00:00` (UTC-dash form, lane-H fix), `3600 S`, `1 min`, `TRADES`, `useRTH=false`. The `cut_input_window` cutoff refusal (any bar ≥ 10:00:00 ET) is enforced in code and was not violated. Manifest: 2 entries, per-file shas correct (chain field inert — F3).

## Check 4 — Pin integrity at HEAD: PASS

| pin | measured | expected | match |
|---|---|---|---|
| `17_null_calibration_raw_v2.json` | `e0dc703e2139a03170e863ee0800c0087db6b245613644ced5e1f3a228aba192` | same | YES |
| `es_expiry_coverage.json` | `8e2b98c59263458a960adc65efa0001d182089feb4e917faa6d6a3f02d1f3cb4` | same | YES |
| `bls_dates.json` | `ad41d2a76708229b9eef4a02bf62cd6df44eb023455f2c98d2d21cb5b1363009` | same | YES |
| `04_Q1_VOL_PANEL.json` | `12dc7fbef954155373d3a5fd2173823e1b7297c7b47633a55e19351555d5a76f` | pinned | YES |
| `lane_q1.py` | `82d1b8e6dc9dd25927dc35ec3c53a9f5da8bd0ece8ac465e55ac16d589d242c4` | pinned | YES |

Restored-vs-nested: the restored files at the original pinned path (`/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep/research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/{cme_cal/nq_es/es_expiry_coverage.json, events_bbo_coverage/bls_dates.json}`, mtime Oct 9 21:03 +0700) are **byte-identical** to the nested legacy copies inside the Q1 worktree (`…/prep/.worktrees/futures-es-reg/prep/…`) — identical sha256 on both pairs. The collector that actually ran is `3451d380…` (Lane K, blob at `325c4030` == HEAD); `COLLECTOR_STATE.script_sha256` still shows the Lane-H value `ca5d0b96…` (stale bookkeeping, F2, pre-declared in auth 36).

## Check 5 — Features and forecast recompute: PASS (exact)

Independent reimplementation (`T4_recompute.py`) of the collector's documented semantics (keep-first dedupe; pairs = gap exactly 60 s and closes > 0; log-return anchored at the LATER bar-start; `fsum` of ret² over later starts 09:31–09:34 = RV5, 09:31–09:59 = RV30; yhat = pinned betas applied to features — arithmetic on pinned constants, NOT a fit):

| quantity | ES row / recomputed | rel dev | NQ row / recomputed | rel dev |
|---|---|---|---|---|
| rv5 | 4.657410140769833e-07 / same | 0.0 | 1.1349560989570497e-06 / same | 0.0 |
| rv30 | 2.5287812547164097e-06 / same | 0.0 | 1.0114997722498044e-05 / same | 0.0 |
| yhat_reduced | -8.80608156859919 / same | 0.0 | -8.600014871719196 / same | 0.0 |
| yhat_full | -10.093635719093943 / same | 0.0 | -9.227703471312667 / same | 0.0 |

Tolerance 1e-12 rel — achieved exactly. `pins_applied` betas in each row equal the calibration file's `pinned_coefficients` for that symbol. lag1/trail20 equal the pinned panel TRAIN-tail warmup (last entry 2018-12-31), as expected for the first prospective session.

## Check 6 — G3 investigation: PASS (guard lawful; root cause identified)

- Rows: `g3_open_ok=false`, `n_pairs_open_valid=22` of expected 29.
- Raw bars in [09:30,10:00) ET: **ES 23, NQ 23** — contiguous 09:30–09:52; **missing 09:53, 09:54, 09:55, 09:56, 09:57, 09:58, 09:59 in BOTH symbols** (7 later-starts impossible → 22/29; no intra-window gaps; all closes > 0).
- **Root cause: transient IBKR paper-feed historical-store publication lag.** Proof: an auditor read-only re-request of the IDENTICAL window (`endDateTime 20261009-14:00:00`, `3600 S`, 1-min TRADES, `useRTH=false`, clientId 9417) at **2026-10-09T14:14:52Z returns 60/60 bars for ES and NQ with the 13:53–13:59Z minutes present** (`T4_g3_tws_probe.json`). The 09:53–09:59 bars exist; they were published to the store in the ~11 minutes after the 10:03:12–16Z fetch. Not an exchange halt (identical-shape tail gap on both symbols; bars exist), not collector error, not tampering.
- The 14 September parity captures show 30/30 open bars, but all were look-backs captured 2026-10-08T09:38Z, days after their sessions — they do not contradict same-moment lag.
- **Scoring consequence per the observe-step law** (`q1_collector.py:1146–1150`, priority g1→g3→g2): at observe_close the outcome rows for BOTH symbols will be `status=EXCLUDED_GUARD_FAIL`, `exclusion_cause=g3_open_window_incomplete`. The rows remain **COLLECTED** (forecast issued, guard flags recorded) but are **EXCLUDED** from scoring/evaluation. The code path has no override and none was applied.

## Check 7 — Refusal forensics: PASS

`ops/ops_log.jsonl` (11 entries): today's two lawful fail-closed refusals —
- `2026-10-09T14:01:02Z` `NOT_RUN_PIN_DRIFT` exit 4 (pinned `es_expiry_coverage.json` missing at the futures-es-reg path after the mass worktree cleanup);
- `2026-10-09T14:02:54Z` `NOT_RUN_PIN_DRIFT` exit 4 (same, after an incomplete restore).

Both are pre-market-access (pin verification precedes any fetch) and **wrote no ledger rows and no raw files** — the ledger/raw manifest contain only artifacts of the successful run. The successful run's `FORECAST_ISSUED` entry (14:03:16Z) is present and byte-consistent with the ledger (per-row line shas verified in Check 1). Prior-day fail-closed history (TWS unavailable, BLOCKED_BY_FINDING, BEFORE_AUTH_WINDOW, INPUT_WINDOW_STALE) is intact.

## Check 8 — Hygiene (nested stray tree): PASS with findings

`/Users/hoangminhlong/my-quantitative/.worktrees/futures-q1q2q3-prep/prep/.worktrees/…` is **NOT tracked in git** (`git ls-files` count 0; no commit ever added `.worktrees/*`; ignored by `.gitignore` line 3 `/.worktrees/`). It is, however, a **REGISTERED worktree nested inside the Q1 lane worktree**: `prep/.worktrees/futures-es-reg/prep @ 935556cf` on branch `prep/futures-es-reg-20261004`. The restored original path `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg` is **not** a registered worktree — an unregistered plain directory inside the root repo's gitignored `/.worktrees/` zone holding (at least) the two restored pin files. Nothing deleted by the auditor. See F4.

## Check 9 — No overclaim: PASS

No profitability/edge/alpha claims anywhere in today's evidence; the only "edge" mentions are explicit disclaimers (protocol 28: risk forecast, "không phải edge giao dịch"; auth 36 verbatim: "Q1 là dự báo biến động, chưa phải edge giao dịch"). Forecast rows log values with complete guard flags including `g3_open_ok=false / n_pairs_open_valid=22`; the commit message records G3 22/29 as a guard flag with eligibility at scoring. Disclosure duty (NQ parity divergence) pending at report level — F5.

---

## Findings

- **F1 (MEDIUM, operational — no violation):** Same-moment fetch at ~10:03 ET loses the input tail (7 min) to paper-feed store lag; the amendment-34 window ends 10:05 ET so an ~11-minute publication lag cannot be waited out inside the window. If it recurs, every session will be COLLECTED then EXCLUDED (`g3_open_window_incomplete`) — the campaign accumulates zero evaluable rows. Owner decision required for any timing change; auditor changed nothing. Interim state is lawful and honestly flagged.
- **F6 (MEDIUM, adjacent compliance gap):** The owner-declared-MISSED 2026-10-08 bookkeeping mandated by auth 36 §3 and the T3 gate ("observe-close tonight writes 2 MISSED rows") never ran: no observe ops entries exist between 2026-10-08T11:30:23Z and 2026-10-09T14:01:02Z, and the ledger has zero `session_missed` rows. The lawful observe window for 2026-10-08 (16:15 ET Oct 8 → 06:00 ET Oct 9) has lapsed, so those rows can no longer be lawfully appended (observe would refuse `NOT_RUN_OBSERVE_TOO_LATE`). Does NOT affect the 2026-10-09 rows verified here; the miss should be recorded explicitly (ops/incident or owner ledger), never backfilled.
- **F2 (LOW):** `COLLECTOR_STATE.json` stale `script_sha256` (`ca5d0b96…` Lane-H) vs executed collector `3451d380…` (Lane K == HEAD) and `ledger_rows: 0` vs actual 2 — `update_state_next_fire` refreshes only `next_fire`/`updated_utc`. Pre-declared as bookkeeping in auth 36; ledger sha-chain independently verified.
- **F3 (LOW):** Raw-manifest sha-chain is inert: `write_raw` reads key `sha256_of_line` from the previous persisted line, but persisted lines only carry `sha256`, so `prev_sha256_of_line` is always null (both of today's entries). Per-file sha256 correct; raw files committed at HEAD (git tamper-evidence) — today's evidence unaffected; law-9 chain intent not realized for future sessions.
- **F4 (LOW, hygiene):** Pinned dependencies live outside version control: restored originals in an unregistered plain dir in the gitignored `/.worktrees/` zone, plus a stray registered worktree nested inside the Q1 lane worktree (byte-identical, hash-verified today). This single-point-of-failure already caused 2 lawful refusals today; recommend pin artifacts inside the tracked tree or a sha-verified vault, and untangling the nested registration (owner/lane decision).
- **F5 (LOW):** Auth 36 option-1 disclosure duty (NQ RV30 Databento divergence ~1.05e-05–2.1e-05 rel > 1e-6 pin; 14-session/one-contract parity limitation) must appear in every prospective report; carried by auth doc 36 but not restated in the forecast commit message or rows.

## Auditor actions / scope

Read-only everywhere; one read-only TWS historical re-read (clientId 9417) for the G3 root cause; recompute script `T4_recompute.py` committed alongside this report. No repairs, deletions, pushes, merges, or orders.
