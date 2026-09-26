# A7 TERMINAL AUDIT — DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1

Independent terminal auditor, fresh context, no stake in the cycle passing.
Worktree `.worktrees/data-foundation-v1/lane-a7`, branch `orca/dfv1-lane-a7`,
HEAD verified `f05c1baf7c152db8061d38032f52b41da8593c76` (== the audited
integration HEAD lineage; parent `78c836bb3df79fc501277313fdaef40ffbf20359`).
All numbers below re-measured from bytes / committed artifacts this session,
2026-09-26. Read-only except this file; no `.env`, no sealed/holdout content
(metadata/name counting only); no network.

## VERDICT: AUTHORIZED_WITH_FINDINGS — CRITICAL 0 / HIGH 0 / MEDIUM 3 / LOW 3

The cycle's positive claims reproduce where they are checkable: every sha256
A7 re-measured matches (4 datasets incl. the mandatory PS1 probe), the status
tally is exact, the validator passes on the committed file, the D1 erratum
genuinely corrects a real premature-PASS, and no scored/PnL or credential
content exists in the cycle dir. The three MEDIUM findings are arithmetic/
definition inaccuracies in prose layers (exposure-map count, erratum violation
count, F1 READY tag) — none inflates the cycle's evidence and none blocks a
terminal close, but each must be corrected before its number is reused.

---

## Duty 1 — Recount of key numbers

| Claim | Claimed | A7 measured | Result |
|---|---|---|---|
| data_inventory.jsonl rows | 91 | 91 JSONL rows, all parse (0 parse failures) | MATCH |
| Status tally | 32/26/28/2/1/2 | AVAILABLE_VALIDATED 32, AVAILABLE_UNVALIDATED 26, NOT_RUN 28, BLOCKED_TRANSPORT 2, BLOCKED_LICENSE 1, BLOCKED_ACCOUNT 2 (sum 91) | MATCH (exact) |
| 5 lane handoffs exist + parse with schema `zcode_orch_v3_handoff@1` | 5 | 5/5 found (L-FX, L-CX, L-ST, L-PIT, L-COST), all parse, all declare `schema: zcode_orch_v3_handoff@1`, all `dispatch_sha == actual_start_sha` (40-hex each) | MATCH, with schema-field deviations (F-A7-5) |
| Exposure map: exposed rows | 30 table rows (21 outcome-exposed + 9 read-only) | **28** data rows counted across the 5 tables (FX 8 + FX-macro 2 + crypto 9 + stocks 7 + vol/commodities 2; 33 pipe-rows minus 5 header rows) | **MISMATCH — F-A7-1** |
| Exposure map: unopened classes | 5 | 5 (S1 everywhere; ERP1 sealed 2026-H1 AUDUSD/USDCAD; post-2026-09 prospective streams; all future windows; BNBUSDT pre-read plane) | MATCH |

Handoff deviations (F-A7-5, all 5 files): `recommended_next_action` absent;
`tests[]` carry `result` prose instead of the required `verdict`
(PASS/FAIL/NOT_RUN) + `log_digest`; `outputs[]` have no per-file `sha256`
(L-FX/L-PIT/L-ST are lists of path strings, L-COST/L-CX plain dicts);
`commit_sha` is `null` (L-CX, L-ST) or a prose string
"SELF_REFERENTIAL_SINGLE_COMMIT …" (L-COST, L-PIT) instead of 40-hex — only
L-FX carries a real sha; `authority_claims[]` is populated in all 5 with
data-ruling substance (reviewed: no scope-authority claim in the content;
lanes assert no authority over other lanes/ledgers). Integrity remains
traceable via the git commits they document.

## Duty 2 — Re-derived authority-row statuses (6 rows, 4 asset classes)

1. **`ofr_stfm` (shared, AVAILABLE_VALIDATED) — CONFIRMED.** Evidence: "sha256
   of all 6 on-disk files vs committed ofr_stfm_v1r1_manifest.json -> 6/6
   match". A7 re-fetched the manifest from `orca/free-data-frontier-v1r1-integration`
   (`research/control/free_data_frontier_v1r1_run/manifests/ofr_stfm_v1r1_manifest.json`)
   and re-hashed all 6 files under
   `~/.my-quantitative-data/free-data-frontier-v1r1/raw/ofr_stfm/`:
   **6/6 sha256 MATCH**, byte sizes == manifest `content_length`.
2. **`td_xauusd_1day` (commodities, AVAILABLE_VALIDATED) — CONFIRMED.**
   Evidence: "full re-hash shasum -a256 XAUUSD_1day_full.json ==
   49c2684ebb… == p0_census_verdict.json declared sha; rows==12268 counted
   from bytes; first 1979-12-26, last 2026-09-16". A7 re-hashed the staging
   file on `forex-ng6` integration: sha256
   `49c2684ebb045302acf0c452b5aa9a3b96dff73eb3bc6f5add1801d6817fb33d` EXACT;
   `values` list len = **12,268**; first datetime `1979-12-26`, last
   `2026-09-16`. The declared sha is present inside the committed
   `p0_census_verdict.json`. Evidence fully supports the status.
3. **`sec_nport_2026q2_qqq` (stocks, AVAILABLE_VALIDATED) — CONFIRMED (sha).**
   Evidence: "2026q2_nport.zip re-hashed EXACTLY 077cc836… MATCH committed
   sec_nport_manifest entry; holdings row count 102 measured from bytes".
   A7 re-hash of the 440,699,889-byte zip:
   `077cc836a978a593b29012219395fbe9c303d5e930f5be3b5f4353c3b02296fc` —
   matches the cited prefix.
4. **`dukascopy_m1_eurusd_eosv2` (forex, AVAILABLE_VALIDATED) — CONFIRMED
   (counts/endpoints).** Evidence: "find count 4014 == manifest 4014 (BID
   2007 + ASK 2007); first ASK/2021-01-01.bi5, last BID/2026-06-30.bi5".
   A7 counted names only under
   `.worktrees/eurusd-open-search-v2/…/data_local/duka/M1/`: BID 2007 +
   ASK 2007 = **4,014**; last `BID/2026-06-30.bi5`; first `ASK/2021-01-01.bi5`.
5. **`forex_intra_bidask_canary` (forex, BLOCKED_TRANSPORT) — CONFIRMED.**
   Evidence: "committed A7 terminal audit … (verdict CONFIRM_WITH_FINDINGS,
   terminal_claim BLOCKED_TRANSPORT) read from branch orca/fibv1-integration;
   2 DoH artifacts on disk (8.0K du…)". A7 read
   `orca/fibv1-integration:research/control/forex_intra_bidask_v1/audits/a7_terminal_forex_intra_bidask_v1.json`:
   `verdict: CONFIRM_WITH_FINDINGS`, `terminal_claim: BLOCKED_TRANSPORT`;
   `~/.my-quantitative-data/forex-intra-bidask-v1/` measures **8.0K**. BLOCKED
   status supported, not understated.
6. **`finra_daily_short_sale_volume_cns` (stocks, BLOCKED_LICENSE) —
   CONFIRMED (existence/provenance).** Evidence cites
   `research/control/stocks_ng4_run/audits/evidence/finra_terms_snapshot_2026-09-15.txt`
   + plan §3 P-25. File exists (9,636 bytes); header reads "A7 PLAN-AUDIT
   RAW-WEB EVIDENCE SNAPSHOT — FINRA SHORT SALE VOLUME TERMS + CANARIES,
   snapshot_utc 2026-09-15T11:06:32Z". Reopen condition (owner procures FINRA
   data license) recorded in-row. BLOCKED status supported.

No row's status was found overstated relative to its cited evidence.

## Duty 3 — Independent re-hash (4 datasets; requirement ≥3)

| Dataset | Claimed | A7 measured | Result |
|---|---|---|---|
| **PS1 probe** `~/.my-quantitative-data/data-foundation-v1/ps1/BTCUSDT-pik-1h-2026-07.zip` | sha256 `448beab06b0f…f8443` == vendor CHECKSUM | sha256 `448beab06b0f7268d39520e71fea0420cf15d67cb3415cf53efaa28e106f8443`; vendor `.CHECKSUM` file contains the identical digest; stat 16,397 bytes; uncompressed **745 lines** == PS1_REPORT "745 hourly rows"; ps1 dir du 1.2M | EXACT MATCH |
| SEC N-PORT 2026q2 zip (440,699,889 B) | `077cc836…` | `077cc836a978a593b29012219395fbe9c303d5e930f5be3b5f4353c3b02296fc` (2.45 s wall) | EXACT MATCH |
| OFR STFM corpus (6 files) | 6/6 vs committed manifest | 6/6 EXACT (sizes 10,045 / 47,760 / 59,589 / 59,677 / 47,848 / 47,756 B) | EXACT MATCH |
| TD XAUUSD 1day full (1,347,055 B) | `49c2684e…`, 12,268 rows | EXACT + row count + endpoints | EXACT MATCH |

## Duty 4 — Re-measured coverage claims (3 claims; requirement ≥2)

| Claim | A7 measurement (names/ls/find only) | Result |
|---|---|---|
| FTD archive 434 zips, first 2009-07, last 2026-08 | `sec_ftd_archive/`: **434 .zip** files (436 dir entries incl. 2 non-zip inventory files) = 412 `cnsfails*` + 22 `cnsp*`; first `cnsfails200907a.zip`, last `cnsfails202608b.zip` | MATCH |
| Dukascopy EURUSD eosv2 = 4,014 files ending 2026-06-30 | BID 2007 + ASK 2007 = **4,014**; last `2026-06-30.bi5` | MATCH |
| eosv1 = 3,652; rangeexp duplicate = 4,014 | eosv1: 1,826 + 1,826 = **3,652**; rangeexp: 2,007 + 2,007 = **4,014** | MATCH |

## Duty 5 — Validator actually passes

Run from the audited worktree with the mandated interpreter:

```
.venv/bin/python research/control/DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1/pit_license/validate_rows.py \
  research/control/DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1/data_inventory.jsonl
→ VALID: 91 row(s) conform to dfv1_authority_row@1, exit 0
```

Also passes on the 16-row L-PIT subset (`pit_license/inventory_rows.jsonl`,
exit 0). PASS.

## Duty 6 — D1 erratum arc is honestly recorded

- **Premature PASS in parent 78c836bb — CONFIRMED** by the parent's own
  message: "PIT_AND_COST_CONTRACTS (frozen: schema+validator PASS …)" and
  "DATA_INVENTORY (93 rows, 33 AVAILABLE_VALIDATED)" while the consolidated
  file it shipped does NOT pass.
- **Erratum in f05c1baf — CONFIRMED**: message records the premature claim,
  the cause ("lanes other than L-PIT never ran validate_rows.py"), the fix
  (93→91 rows, dup dedup nyfed/fred, 1 R1 downgrade, bytes measured, enum
  mappings conservative, owner-action strings for BLOCKED_*), and
  DATA_INVENTORY.md line 11 carries the erratum note. Diff scope of the
  erratum commit is exactly the two D1 files (data_inventory.jsonl,
  DATA_INVENTORY.md) — nothing else touched.
- **A7 reproduced the failure**: `git show 78c836bb:…data_inventory.jsonl`
  (93 rows) against the same validator → `INVALID: 93 row(s), 265
  violation(s)` (93 unknown-field + 62 enum + 39 bytes-type + 27 enum +
  13 SAMPLED + 13 R4 + 7 R3 + 5 R2 + 4 R1 + 2 R6). `pit_license/` is
  byte-identical between the two commits, so the validator did not change.
  **The cited "109 violations" does not reproduce (A7 measures 265)** —
  F-A7-2. Direction is conservative (the original failure was worse than
  stated); the correction itself is genuine.

## Duty 7 — Gates G0–G7, probe ledger, disk floor

| Gate | Verdict | Evidence |
|---|---|---|
| G0 intake/plan/review | PASS | Plan committed `939d426e`; `audits/A7_PLAN_REVIEW_r1.md` AUTHORIZED_WITH_FINDINGS (0C/1H/5M/5L) with F1 (HIGH) closure condition; §14 amendment `189c6d23` records F1–F11 remediation as binding before G1 |
| G1 dispatch/worktrees | PASS | `G1_BOOTSTRAP_EVIDENCE.md`: 6 worktrees verified at base `189c6d23`, 148M each (du ledger 7.7→6.8 GiB), registered before dispatch, packets `af7b1c3c`; A7 verified all 5 handoffs `dispatch_sha == actual_start_sha` |
| G2 per-asset inventory complete | PASS | 91 rows; every family has a §5 row with status + evidence; validator R-rules force explicit NOT_RUN reasons; recount exact (Duty 1) |
| G3 validation within budget, no inferred PASS | PASS | Validator VALID; per-row re-measurement evidence; A7 independently re-derived 6 statuses + 4 sha re-hashes, all MATCH; no row found upgraded from existence |
| G4 gap matrix + runbook + contracts + exposure map | PASS with F-A7-1 | All four artifacts exist; gap matrix N1–N10 + O1–O7; runbook R1–R8; exposure map present, headline count wrong by 2 |
| G5 probes within §8 budgets; manifests ALL_MATCH | PASS | Ledger `dfv1_probe_ledger@1`: PS1 EXECUTED_COMPLETE 11 requests / 1,204,511 B (caps 20 per set / 600 cycle / ≤2 sets); PS2 NOT_RUN_LOW_VALUE with reason; PS1 sha == vendor CHECKSUM (A7 re-verified); sampled manifests A7-spot-checked ALL_MATCH |
| G6 A7 terminal audit 0 HIGH/CRITICAL blocking | PASS (this document) | 0 CRITICAL / 0 HIGH / 3 MEDIUM / 3 LOW |
| G7 two-half close | NOT_RUN at audit time | Registry TERMINAL / ledger row / MAP bullet are the close steps that follow this audit; correctly not pre-claimed |

Probe ledger caps: 11/600 cycle requests, 11/20 PS1 set — well within frozen
caps. Disk: **6.11 GiB free** at audit time (df 6,411,964 KiB) vs 5.0 GiB hard
floor and 6.0 GiB abort line — floor respected, but only ~118 MiB above the
abort line; 9 foreign ACTIVE_LIGHT cycles were already writing at G1 and the
drawdown from 6.8→6.11 GiB is concurrent activity A7 does not attribute to
this cycle without evidence (this cycle's recorded footprint: 888 MB
worktrees + 1.2 MB probe, within the 2.0 GB cap). See F-A7-6.

## Duty 8 — Scope, no scored/PnL, no credentials

- **6 owner deliverables present**: DATA_INVENTORY.md, DATA_GAP_MATRIX.md,
  PIT_AND_COST_CONTRACTS.md, OWNER_ACQUISITION_RUNBOOK.md,
  NEXT_RESEARCH_FRONTIER.md, PS1_REPORT.md (+ probe_ledger.json).
- **Stop conditions**: 3 asset classes covered with census rows — forex 26 /
  crypto 25 / stocks 20 (+ shared 13, commodities 4, rates 2, vol 1);
  remaining gates carry runbook entries R1–R8 (verified present).
- **No scored/PnL artifact**: full-cycle grep for sharpe/pnl/equity_curve/
  total_return/win_rate/profit_factor/CAGR returns only proscriptive or
  cost-ceiling contexts ("không phải cycle săn PnL", "pre-PnL",
  "0 outcome views, 0 PnL", CEILING_NEGATIVE_VETO). No result tables, no
  equity curves, no performance numbers anywhere in the cycle dir.
- **No credentials/sealed content committed**: grep for api_key/secret/
  token/bearer patterns returns policy statements only (directive: owner is
  not asked for passwords/API secrets; runbook: tokens go to `.env`, never
  chat; `LICENSE_RULINGS_VERIFIED.md` records `FRED_API_KEY` by NAME only,
  "values never read"; stocks LANE_REPORT mentions "the living token" with
  no value). ERP1 sealed 2026-H1 rows are metadata-only (F8) — A7 confirms
  rows 06–09 carry name-count/manifest-pin evidence with zero content reads.
  Cycle-dir git history (12 commits, `939d426e`→`f05c1baf`) is clean of
  secret-shaped content.

## Duty 9 — Adversarial sweep (overstatement hunt)

- **NEXT_RESEARCH_FRONTIER**: F2 (READY) enabling set is genuinely
  AVAILABLE_VALIDATED (rows 23/26/30/84) with honest dead-set fences —
  stands. F3 (BLOCKED) correctly blocked on R1. **F1 (READY) partially
  overstated against the doc's own definition** — F-A7-3.
- **DATA_INVENTORY.md**: status prose matches the machine file on the
  tallies A7 checked; section-header arithmetic errors found — F-A7-4.
  The "no PASS inferred from file existence" claim is supported: every
  AVAILABLE_VALIDATED row A7 examined carries this-cycle measurement, and
  validator R1 would reject otherwise.
- **OWNER_ACQUISITION_RUNBOOK**: no step asks for secrets in chat; token
  handling explicitly routed to `.env`; reopening conditions for BLOCKED_*
  rows are named (R2 license capture, R3 disk, R4 vendor decision, R8 FINRA
  license). Clean.
- **PS1_REPORT.md**: consistent with the ledger and with A7's independent
  re-hash (sha, 745 rows, 11 req / ~1.2 MB, 0 credentials). No
  overstatement found.

---

## Findings table

| id | severity | quote | why it matters | required fix |
|---|---|---|---|---|
| F-A7-1 | MEDIUM | OUTCOME_EXPOSURE_MAP.md: "Exposed-window count (table rows above): 30 instrument×window×cycle families, of which 21 … and 9 …" (repeated in commit c24747bd and DATA_INVENTORY.md "21 outcome-exposed family windows") | A7 counts **28** data rows in the five tables (33 pipe-rows − 5 headers). 30 is not reproducible as "table rows"; if the two "AUDUSD + USDCAD" rows are meant to count as 2 instruments each, that rule is nowhere stated. Headline counts of a separation-law deliverable must be recomputable. | Fix the count line to 28 rows (or state the per-instrument counting rule and re-derive 21/9 under it); correct the two echoing documents. |
| F-A7-2 | MEDIUM | f05c1baf + DATA_INVENTORY.md: "the file then failed with 109 violations" | With `pit_license/` byte-identical across the two commits, the parent's committed 93-row file yields **INVALID: 93 rows, 265 violations** under the same validator. The erratum's number is not reproducible. Direction is conservative (original failure understated) and the correction itself is verified genuine (current file VALID: 91). | Amend the erratum note to 265 violations (or document the exact measurement that produced 109). |
| F-A7-3 | MEDIUM | NEXT_RESEARCH_FRONTIER.md: "\"READY\" means the enabling data is AVAILABLE_VALIDATED this cycle" + F1 (READY) "Enabled by validated bytes: Form-4 substrate (345,150 XMLs, digest `5d351623…` EXACT), … EODHD div/splits (2,168+2,168 entitled files)" and "filing-flow observables with acceptance datetimes (EDGAR gives them free … gap N2)" | Under F1's own definition, READY requires AVAILABLE_VALIDATED enabling data, but Form-4 XML substrate (row 49), 4/A corpus (row 51) and the EODHD umbrella incl. div/splits (row 44) are AVAILABLE_UNVALIDATED (digest-pinned, not full-corpus), and the acceptance-datetime surface needs acquisition (N2) that has not run. Mitigations: form4_stream (row 50), FTD archive (row 52) and amihud (46/47) are genuinely VALIDATED, and every frontier still faces its falsification battery — so nothing scores unlawfully today. | Re-tag F1 "READY (partial: core planes VALIDATED; Form-4 XML/4-A/div-splits AUV until full-corpus re-hash; acceptance datetimes gated on N2)" or promote those rows to VALIDATED with byte evidence first. |
| F-A7-4 | LOW | DATA_INVENTORY.md: "SHARED / RATES / VOL / COMMODITIES (17 rows: 15 shared + 2 rates + 1 vol + 4 commodities)"; "STOCKS (20 rows)" then lists OFR/NY Fed under "Validated (9)" | Measured: shared 13 + rates 2 + vol 1 + commodities 4 = **20** rows (header says 17; its own components sum to 22); the stocks "Validated (9)" includes 2 rows whose `asset_class` is `shared`. Machine file is correct and validator-clean; only prose headers drift. | Correct the header to "20 rows: 13 shared + 2 rates + 1 vol + 4 commodities" and mark the OFR/NYFed cross-listing as shared-class. |
| F-A7-5 | LOW | All 5 HANDOFF_*.json: `recommended_next_action` absent; `tests[].result` prose; `outputs[]` without `sha256`; `commit_sha` null/prose in 4/5; `authority_claims[]` populated | Deviations from `zcode_orch_v3_handoff@1` required fields (verdict enum, log_digest, sha-pinned outputs, 40-hex commit_sha, empty authority_claims). Content reviewed: no scope-authority claim; dispatch==actual_start everywhere; integrity still traceable via git. Future validators/store checks may hard-fail on these. | For future cycles: emit the schema-exact fields (or get the schema amended); this cycle needs no rework. |
| F-A7-6 | LOW (observation) | df at audit: 6.11 GiB free vs §14 abort line 6.0 GiB / hard floor 5.0 GiB | Headroom above the abort line is ~118 MiB with 9 foreign ACTIVE_LIGHT cycles writing concurrently. This cycle's own footprint (888 MB + 1.2 MB) is within its 2.0 GB cap and cannot be blamed for the drawdown from 6.8 GiB at G1. | None for this cycle. Advisory for the close and the next cycle: re-measure df before any further byte creation; R3 (free 25–40 GB) is the structural fix. |

Finding counts: CRITICAL 0, HIGH 0, MEDIUM 3, LOW 3.

---

## Terminal labels A7 can authorize (plan §9; per-asset)

Both labels co-occur, per asset:

- **FOREX — BLOCKED_WITH_ACQUISITION_RUNBOOK** for every after-cost family
  (cost floor 3.6/4.4-pip RT measured; financing bands UNMEASURED; unblock =
  R1/R2), **plus** FOUNDATION_READY_FOR_NARROW_RESEARCH on the indicative
  price plane (5 Dukascopy M1 corpora + TD dailies, all A7-re-verified).
- **CRYPTO — FOUNDATION_READY_FOR_NARROW_RESEARCH** on the measured-cost
  plane (Vision panels + settled funding + SOL spread census + funding
  census, all VALIDATED and sampled-verified), with the runbook carrying
  OI/L2 history (R4) and BTC/ETH spread disk-gate (R3). High dead-set fences
  in F2 are honest and carried.
- **STOCKS — FOUNDATION_READY_FOR_NARROW_RESEARCH** on the VALIDATED panels
  (amihud ×2, form4_stream, FTD archive, N-PORT, Form-15, FTD posting-bound
  machinery), with F-A7-3's caveat binding: AUV substrates (Form-4 XML,
  4/A, div/splits) must be promoted to VALIDATED — and N2/N4 landed — before
  any scored use of F1-class families; runbook covers cost/earnings/borrow
  (R1/R5/R6/R8).

Strongest single label: **AUTHORIZED_WITH_FINDINGS terminal close, with
FOUNDATION_READY_FOR_NARROW_RESEARCH + BLOCKED_WITH_ACQUISITION_RUNBOOK
co-occurring per the per-asset split above.** No finding blocks the close;
F-A7-1..3 must be corrected in the documents before their numbers are
reused by any successor cycle.

— A7, terminal audit, 2026-09-26 (branch orca/dfv1-lane-a7 @ f05c1baf)
