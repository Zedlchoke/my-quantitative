# A7 TERMINAL AUDIT — PWS-CX-BNBUSDT-C1 — independent recompute

- Lane: `a7-terminal` (independent terminal auditor, fresh context; writes audit
  artifacts only, repairs nothing).
- Date: 2026-09-26 (evening, +07). Worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/pws-cx-bnbusdt-c1/integration`,
  branch `orca/pws-cx-bnbusdt-c1-integration`.
- **Actual start sha (measured): `acdd464951384dc8e83a848318350a30dac13850`** —
  matches the dispatch expectation; `git status` clean except untracked
  `data_local/` (raw staging, never touched/staged by this lane).
- Method: every claimed number recomputed by this lane from **raw bytes**
  (`data_local/funding/fapi_scan_BNBUSDT_2026-09-26.json`,
  `data_local/vision/klines_um_BNBUSDT_1h/*.zip`) with this lane's own
  stdlib-only script in `/tmp` (`/tmp/a7_recompute.py`; logic fully inlined in
  §2 below), run under `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.
  No implementer output was trusted without re-derivation.

## 0. Scope

Audit the terminal close claim `NO_ELIGIBLE_PROPOSAL` for PWS-CX-BNBUSDT-C1:
(1) artifact integrity; (2) independent recompute of the funding census, kline
census, and the three skeptic spot-check families (sign persistence,
representation rho vs level-window shadows, ceiling×power episodes); (3) gate
consistency (registry, identity registry, GO record/authority chain, absence of
scored artifacts, disk evidence); (4) findings; (5) verdict.

## 1. Artifact inventory + sha256 (recomputed by this lane)

| Artifact | exists | sha256 (measured) |
|---|---|---|
| C0_control_plane.md | yes | `17f51bdd89b0833119652cd5009b3cf762b0845419c112b128f97b63b476630f` |
| C1_data_gate_REPORT.md | yes | `cbd3917e99411e0295511e29bd0f4898f2e3c7fc090e7199c9d4f6f02088b26e` |
| C1_machine_KLINE_CENSUS_BNBUSDT.json | yes | `463d3083108c055c8b0a1f8e7f1e969c2dfbb0183ce3d567a96fd4c873d5e259` |
| C1_machine_FUNDING_STATS_BNBUSDT.json | yes | `853b4f4453290af46f1e3ac5dbb25365d9d084eea42042a58d60ed9d9a5c0e9d` |
| C2_EXPOSURE_VERIFICATION.md | yes | `7feeb2e7110381a857c863c1663afb4c62021877d72c5502b5434a6da34da869` |
| C3_council_synthesis_and_freeze.md | yes | `8e5ace3122303533e1a5f07632394b08fc06016a802bed524a02898f532caaf7` |
| CYCLE_VERDICT.md | yes | `9c6d34da270ab0baf8092c7abfd62e57b6a743fa5256bba752b7d0498902f444` |
| council/P1_PROPOSALS_BNBUSDT.md | yes | `ffda9c75903644e5b693a481892f9a26f97c670f0d8b817e3fe50f1fda07bd22` |
| council/SKEPTIC_VERIFY_REPORT.md | yes | `9ec42813ea83119fdd0113b7d2607177eb18c2679b69d284053ef8d3016725ff` |
| handoffs/HANDOFF_council_P1.json | yes | `c929b2d1903636137d7160bc4444795bfeec276232d8aa0d5686c154d1dd7dbc` |
| handoffs/HANDOFF_c1c2_data_pit.json | yes | `4e0fd31633cd8bdfd1945077e995007721e80783eca5e155264ea53c865e1f76` |
| handoffs/HANDOFF_skeptic_verify.json | yes | `72ad0541e6459203046975a5845b464c7ee1d876bd966510baf19e059df4407a` |
| trial_ledger.jsonl | **ABSENT** | — (see Finding F-1) |

Cross-checks inside implementer artifacts, re-verified by this lane:
raw scan sha `464da8832d53bf0454f286d8ef3566a357a69d93336de5aa5d2835876c0dc893`
(recomputed — matches C1 §2/§7, the machine funding file `sources`, and the
skeptic report); `data_local/INVENTORY.md` = `20616dd2f3…` and manifest
`a9b3ec9b8c…` match the C1 §7 table; Binance Vision ToU pdf exists at the
SOLUSDT child path with sha `94d6f61a39b5f821ef1d38f968aea1f2aa136e374f2061a2131db9a6af96bc3b`
exactly as cited. All three handoff JSONs parse under schema
`zcode_orch_v3_handoff@1`, workers=0, branch correct.

## 2. Independent recompute vs expected

### 2a. Funding (raw fapi scan, dedupe on fundingTime + sort)

Implementation: dict-dedupe on `fundingTime`, sort, bps = rate×1e4; spacings
diffed pairwise (1 s ms-offset tolerance); runs = maximal same-sign spans
(zeros break); Spearman by average-rank; gate state on the **full settlement
grid** (±1 while positioned on a qualifying episode's live span
((K+1)-th settlement of the run onward), 0 otherwise) — the convention that
reproduces the reported occupancy (24.3%) and was cross-validated both with
shadow windows including and excluding the current settlement.

| Statistic | Expected (claim) | A7 recompute | Δ / match |
|---|---|---|---|
| n_settlements | 7,261 | 7,261 | exact |
| duplicate fundingTime | 0 | 0 | exact |
| first fundingTime | 2020-02-10T08:00Z | 2020-02-10T08:00:00+00:00 | exact (floor match) |
| sum (bps) | −27.4199 | −27.4199 | exact |
| mean (bps) | −0.0037763 | −0.0037763256 | exact |
| median | 0 | 0.0 | exact |
| zeros (share) | 3,601 (49.6%) | 3,601 (0.495937) | exact |
| neg_share | 0.2394 | 0.239361 | exact |
| worst (bps) | −58.44 | −58.4369 (2020-03-13T08:00Z) | exact |
| max (bps) | +44.19 | +44.1898 (2021-02-20T16:00Z) | exact |
| non-8h spacings | 0 | 0 (all 7,260 gaps = exactly 28,800 s) | exact |
| run census pos/neg | 418/447, longest 63/46, ≥3: 187/166, ≥5: 108/94, ≥8: 64/55 | identical | exact |
| theta sweep K=3 (θ=1/2/3/4 pos;neg) | 1195;1396 / 816;916 / 604;655 / 458;501 | identical | exact |

### 2b. Klines (all 79 zips re-read, header rows skipped where present)

| Measure | Expected | A7 recompute | Δ |
|---|---|---|---|
| n_zips | 79 (2020-02..2026-08) | 79, same first/last zip | exact |
| total_bars | 57,472 | 57,472 (sum of per-zip counts = same) | exact |
| duplicate open times | 0 | 0 (57,472 unique) | exact |
| first open | 2020-02-10T08:00Z | 2020-02-10T08:00:00+00:00 | exact |
| last open | 2026-08-31T23:00Z | 2026-08-31T23:00:00+00:00 | exact |
| ideal grid | 57,472 | 57,472 | exact |
| missing bars / gaps | 0 / none | 0 / none (full hourly walk min→max) | exact |
| header-bearing zips | census lists 2022-01..2026-08 | 56 (exactly 2022-01..2026-08) | exact |
| monthly spot-checks | 2020-02=472, 2021-02=672, 2023-02=672, 2026-08=744 | identical | exact |

### 2c. Skeptic spot-checks (own implementation, from the same raw scan)

| Check | Expected (SKEPTIC_VERIFY_REPORT) | A7 recompute | Δ |
|---|---|---|---|
| sign persistence lag-1 (zeros=0) | +0.7587 | +0.7588 | +0.0001 |
| lag-2 / lag-3 / lag-6 | +0.6919 / +0.6642 / +0.5845 | +0.6919 / +0.6641 / +0.5842 | ≤0.0003 |
| P(same sign \| adjacent both nonzero) | 0.9940 | 0.9940 (n=2,812) | exact |
| P(same sign \| nonzero, zeros break) | 0.7637 | 0.7637 (n=3,660) | exact |
| episodes θ=0.5 two-sided | 152 pos / 156 neg (occ 24.3%) | 152 / 156 (occ 0.243) | exact |
| episodes θ=1.0 two-sided | 102 / 126 (occ 21.3%) | 102 / 126 (occ 0.213) | exact |
| rho vs W3/W9/W21/W90, θ=0.5 two-sided | +0.594/+0.527/+0.479/+0.383 | +0.594/+0.527/+0.479/+0.386 | ≤0.003 |
| rho vs W21, θ=1.0 two-sided | +0.445 | +0.446 | +0.001 |
| rho vs W3/W9/W21, θ=0.5 neg-only | +0.438/+0.390/+0.354 | +0.438/+0.390/+0.354 | exact |
| rho vs W90 neg-only θ=0.5 / θ=1.0 | +0.237 / +0.225 | +0.240 / +0.228 | ≤0.003 |
| rho vs UNCOND (both conventions) | −0.058/−0.035; −0.175/−0.168 | −0.057/−0.035; −0.175/−0.168 | ≤0.001 |
| ceiling θ_min=3.333 (fee-only floor) | 35 pos / 45 neg / 80 combined | 35 / 45 / 80 | exact |
| ceiling full grid (3.5, 5.0, 5.25, 5.5, 6.667, 7.0, 7.333) | 76, 46, 44, 40, 32, 28, 24 | identical (pos/neg splits identical) | exact |
| lookahead bracket @3.333 | 144 | 144 | exact |

Every delta ≤ 0.004 in a correlation whose kill margin is 1.12×–2.97× the 0.20
bar; all substantive conclusions reproduce exactly: level-window shadows breach
the K-ANC bar at every θ/side; the vs-UNCOND leg does NOT breach it on BNB
(honestly disclosed in the report); ceiling grid non-empty but < 100 under
every PIT reading.

## 3. Gate consistency

1. **Registry** (`plans/CYCLE_REGISTRY.json`, row `PWS-CX-BNBUSDT-C1`): budget
   `used 0 / max 18`; `go_phrase_state: REGISTERED_NOT_CONSUMED` (phrase `GO
   PWS CX BNBUSDT C1 SCORED EXECUTION` dies UNCONSUMED); `s1:
   SEALED_UNTOUCHED`; `workers: 0`; `active_heavy: false`; head field =
   `acdd4649…` = measured checkout HEAD; phase reads "C3 COMPLETE … pending A7
   terminal" — the expected pre-A7-close state; flipping it is the
   orchestrator's post-audit action, not this lane's.
2. **IDENTITY_REGISTRY** (`research/control/PWS-PROGRAM-V1/IDENTITY_REGISTRY.jsonl`):
   exactly 2 rows, both `PWS-CX-SOLUSDT-I001` (PROPOSED → F0_KILLED). No BNB
   identity; N_registry stays 1/100. Unchanged by this cycle, as claimed.
3. **GO RECORD** (`research/control/PWS-PROGRAM-V1/GO1_RECORD_PWS-CX-BNBUSDT-C1_2026-09-26.json`):
   exists; cites the delegation charter
   (`OWNER_DELEGATED_DECISION_charter_and_go1_2026-09-26.json`), the owner
   sprint instruction 13:41Z (next-pair check ordered; "same old information ⇒
   close NO_NEW_INFORMATION, don't backtest"), the A7 child-plan review, the Q3
   pair order (SOL→BNB), the closed SOLUSDT predecessor, and explicit
   scope/constraints stopping **before** GO-2. Divergent OWNER_PACKET §6 reading
   is disclosed and resolved by the later, explicit sprint instruction.
4. **A7 child-plan review 9caac6ba**: present at root
   `research/control/PWS-PROGRAM-V1/plan_review/A7_child_plan_review_BNBUSDT_REPORT.md`
   with verdict **AUTHORIZED_FOR_GO1_GATE** (0 HIGH / 0 blocking; 1 MED
   gate-time precondition = SOLUSDT close, satisfied and cited in the GO
   record). Handoff `HANDOFF_a7_child_plan_review_bnbusdt.json` verdict
   matches.
5. **No scored/PnL artifact**: full recursive listing of the child control dir
   (excluding `data_local/`) shows only narrative reports, the two machine
   censuses, and 3 schema-valid handoffs. No scored cell, no PnL, no backtest
   output, no outcome view anywhere. 0/18 budget corroborated by the registry.
6. **Disk evidence for NOT_RUN_DISK_CONSTRAINT**: `df -g /` measured by this
   lane during the audit: capacity 228 GB, used 17 GB, **available ~7 GB** <
   25 GB precondition. Consistent with the C1 §3 record; no bookTicker bytes
   staged (`data_local/` contains klines + funding only).

## 4. Findings

No HIGH or CRITICAL findings. Three LOW bookkeeping findings:

- **F-1 (LOW) — `trial_ledger.jsonl` absent.** The dispatch inventory (and
  CYCLE_VERDICT's "trial_ledger 0 rows") reference a ledger artifact that does
  not exist anywhere in the child control dir. The substantive claim (0 trials
  booked) is independently corroborated — registry budget 0/18, identity
  registry unchanged (1/100), zero scored artifacts on disk — so this is an
  unbacked bookkeeping claim, not an unaccounted trial. Fix: either create the
  empty ledger at close or reword to "no trial ledger file; 0 trials booked
  (corroborated by registry + identity registry)".
- **F-2 (LOW) — stale sha pin for C2 in C1 §7.** C1's artifact table pins
  `C2_EXPOSURE_VERIFICATION.md` at `dbb973a1…`; the final C2 file hashes to
  `7feeb2e7…`. C2 was evidently amended after C1 wrote its table. No integrity
  consequence (machine-file shas all match; nothing consumes that pin), but
  cross-artifact sha tables should pin final bytes.
- **F-3 (LOW) — handoff count in C3 prose.** C3 says "handoffs/ (4 handoff
  JSON đúng schema)"; the directory contains 3 (pre-A7). Count error only;
  each named handoff exists and validates.

## 5. Verdict

**CONFIRM_WITH_FINDINGS** (0 HIGH / 0 CRITICAL; 3 LOW as above).

The terminal close is sound: C0 PASS, C1 klines PASS (57,472 bars gapless,
floor exact) + funding PASS WITH CAVEATS (all 14 headline statistics reproduced
exactly from raw bytes) + spread NOT_RUN_DISK_CONSTRAINT (df evidence
independently confirmed) + license PASS (ToU cited-by-sha verified on disk),
C2 CONFIRMED, C3 slate empty with the kill **measured on BNB's own series**
(all skeptic spot-check families reproduced within rounding: persistence,
representation rho vs level-window shadows at two thetas × two conventions,
ceiling×power grid exact on all cells), 0/18 scored cells, 0 outcome views, 0
registry slots burned, GO-2 UNCONSUMED, S1 SEALED. The NO_ELIGIBLE_PROPOSAL
verdict is supported by evidence that this lane re-derived independently.

— A7 independent terminal auditor, lane `a7-terminal`, 2026-09-26.
