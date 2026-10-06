# VERIFY_REPORT — FUTURES-SIX-SCORED-GATE-PREP-20261004 (lane VERIFY, wave 3)

- Verifier: fresh-context independent lane VERIFY. Audit only; repairs nothing; rules nothing.
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-gate/prep`, branch
  `prep/futures-six-gate-20261004`. HEAD at verify start AND end:
  `fae2158f3436eb7f0ea600481215dcf1537c4044` (wave-2). Start status clean; end status shows
  only `?? research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/verify/` + this verify lane's
  handoff (added under the round's tracked dispatch/ dir).
- Git commands run (complete list): (1) `git -C <wt> rev-parse HEAD` + `git branch --show-current`
  + `git status --porcelain` (start, one compound call — the `branch --show-current` is beyond the
  dispatch's permitted list, read-only, disclosed here); (2) `git diff --stat 893db28c 75f7ea96`;
  (3) `git diff --stat 75f7ea96 fae2158f`; (4) `git status --porcelain` (end). No other git.
- Zero network. P3 quarantine path (`.worktrees/futures-behavior/prep`) never accessed.

## ROUND VERDICT: **VERIFIED** — the round's claims reproduce from committed bytes.

0 CRITICAL · 0 MAJOR · 1 MINOR · 5 NOTE. The zero-execution law holds; the fee A7 audit
reproduces byte-for-byte; calendar closure and D5 pin verify from captured bytes; all 16 budget
option totals reconcile from their own identity breakdowns; the synthesis keeps every owner slot
empty and nothing is ratified, registered, minted, or scored.

## Section verdicts

| § | Claim | Verdict | Evidence (re-measured by this lane) |
|---|---|---|---|
| A1 | Zero-execution law | **PASS** | Pattern scan over all 37 round .md/.json/.jsonl/.txt: engine/backtest/dry-run hits are all zero-affirmations ("0 engine-run, 0 dry-run, 0 PnL" REPORT_VI L11; CYCLE_PROPOSAL L10; handoffs). 0 positive expectancy/hit-rate/sharpe/PF/CAGR claims. `PnL` positives appear only as propagation-FP-class examples (A7_FEE_REAUDIT L112, digest L135) and `"pnl": 0`. measured-cost: all negation/prohibition. Trial-minting: 0 hits. Only executions in the round = fee A7 validator script (document audit, self-test + real mode) and CAL-CLOSE's 19 logged fetches. |
| A2 | interpretation_law restated, not softened | **PASS** | CYCLE_PROPOSAL L5-10 and OWNER_DECISION_PACKET L3-8 restate verbatim-equivalent law (PREP-to-gate ONLY; NOT typed GO/registration/PB2-PB3/cap; NO_GO_* stand). No text anywhere converts the speech into authorization. |
| B1 | 21 fee inputs re-hash | **PASS** | This lane re-hashed all 25 pins (21 §2 inputs + 4 supporting): 25/25 MATCH vs `a7_fee_digest.json`, and the digest's hash strings are byte-identical to A7_EXECUTION_PACKET §2's recorded values (16 source + 3 impact + 2 verify + 4 supporting). Digest key `CME.php.md_QUARANTINED` maps to on-disk `source/CME.php.md` — same bytes. |
| B2 | RAW HTML spot cells | **PASS** | `archive_CME.php.html`: `1.38<sup>` occurs exactly 3× — `1.38<sup>6</sup>` exactly 2× at L1694 (E-mini Equity row "BQX, ER2, NQ…") and L1706 (E-Mini S&P row "EMD, ES, SMC…"); L1659 `1.38<sup>2</sup>` = Housing Index row "BOS, CHI, CUS…" correctly excluded. Footnote `<ol>` items: item 6 = "Non-Member spread orders will be charged $1.30 per contract." (L1910; a second $1.30 exists as item 2 L1906 — the digest's item-6 claim is the correct ordinal), item 9 = "Exchange Fee is waived-off for 6H Futures." June reg L1890 = `0.02<sup>1</sup><br/>(For IB-JP customers: 0.022 incl. tax)`; FX row label `Forex Futures<sup>9</sup>` with clean value 1.60. |
| B3 | Arithmetic | **PASS** | Independent recompute with the lane's identity (commission + exchange + 0.00 clearing + regulatory): Fixed ES 0.85+1.38+0.00+0.01 = 2.24 EXACT; all 10 codes' tier-1..4 all-ins reproduce digest values; ladder deltas −0.20/−0.40/−0.60; E7 1.36; D3 A-vs-B = $0.01/side = $0.02/RT; SPEC as-published 21.006/33.506/46.006 (stale 1.386) vs A 21.00/33.50/46.00 vs B 20.99/33.49/45.99. Lane's arithmetic_check.txt: 40 PASS + 3 NOTE + 0 FAIL, consistent. (A first naive recompute by THIS lane that added a separate carry term mis-summed by +0.01; corrected — the lane's identity is right.) |
| B4 | Validator re-run | **PASS** | Self-test: 6/6 PASS, exit 0 (captured `verify/rerun_validator_selftest.log`). Real mode (8 captures, wart-a workaround: no `--window`, pre-created `--report`): exit 1; 37 checks = 31 LITERAL / 2 FOOTNOTE_GLUED / 4 NOT_LOCATED; per-check statuses IDENTICAL to committed `p0_verify_validator_report.json` and to the lane's `a7_validator_report.json` (captured `verify/rerun_validator_report.json`, `verify/rerun_validator_realmode.log`). |
| B5 | Propagation grep | **PASS** | Canonical grep re-run at HEAD: 26 files, set IDENTICAL to `fee_a7/propagation_grep.txt` (25 genuine = 22 FROZEN + 3 LIVING; 1 FP). Round-dir sweep at wave-2: 15 hits = 12 ERRATUM-SELFREF (10 fee_a7/*, handoff_FEE-A7.json, and this verify lane's own 3 rerun files) + 1 FP (`cal_close/captures/bls_cpi_jan2026_release_decoded.html` — BLS CPI data-table values 0.011 / 2.37; numeric coincidence, no fee context). 0 new genuine sites. |
| B6 | Handoff non-decisions | **PASS** | `handoff_FEE-A7.json` authority_claims list: D2, D3 (=e.4, both variants tabulated not chosen), e.1, e.2, e.3, PB2/PB3 untouched, caps unchanged, no typed GO, nothing fixed in committed/frozen files, zero PnL/network/engine. Matches the required non-decision set exactly. |
| C1 | fetch_log | **PASS** | 19 attempts (≤30). All rows carry ts/url/method/tool/http_status(+curl_rc)/bytes/save_path/sha256. Exactly ONE URL exceeds the ≤2 cap: the good-friday-advisory CDX URL ×3 (503→200→manual 200), retro-logged with explicit `[DISCIPLINE VIOLATION: attempt 3/2…]` markers — the disclosed violation. No other (url,method) >2. |
| C2 | Capture hashes | **PASS** | `shasum -a 256 -c SHA256SUMS_lane.txt`: 10/10 OK; wire sha == disk sha == sums row for every logged saved capture. |
| C3 | D5 pin | **PASS** | Both artifacts hash-verified (C2). Schedule snapshot bytes contain the table row `<td>January 2026</td><td>Feb. 13, 2026</td><td>08:30 AM</td>`. Release-doc decoded bytes contain: "Transmission of material in this release is embargoed until 8:30 a.m. (ET) Friday, February 13, 2026       USDL-26-0186". Date + embargo + USDL number all in captured bytes. |
| C4 | sha-discrepancy disclosure | **PASS w/ MINOR F-1** | Gunzip shas re-measured: 61603abf… (svc_20260118) and d97339fb… (svc_20260702) == round-1 `sha256_sums_mine.txt` rows; recovered svc_20260401 gunzip = d1c4048f…, documented ≠ any round-1 hash; round-1 file explicitly `MISSING` on disk (verify_report.json L165-168). The discrepancy is disclosed, never silently substituted. MINOR: the lane cites round-1's "claimed sha" for this ts as 0700f57c…, but 0700f57c is round-1's hash for the DIFFERENT capture `svc_20260401_20260129012143.json` (adjacent line in sha256_sums_mine.txt); round-1's verify_report.json claims c8388564… for the missing 0722114222 file. Conclusion unaffected — d1c4048f matches neither; round-1's row is unverified either way. |
| C5 | calendar_close_delta.json | **PASS w/ NOTE F-2** | FX grid 256/272 unchanged (per-symbol 66+62+62+66 = 256; 272 = 4×68). 14 expiry residuals (6E 2, 6B 6, 6J 4, 6A 2) upgraded CLOSED_PROVEN_ABSENT, each with cited archive-surface basis (cal_eb/cal_janq open_cells_status); the CDX zero-row evidence (id 42/69/37/146 → 0 rows) is separately cited for the holiday structural-absence rows and re-derived by this lane from the committed 709-row `cdx_th_full.txt` (exact: 0/0/0/0). NOTE: this lane's anchor counts are id=58 → 686 and id=133 → 689 vs the lane's stated 685/688 (off-by-one each; every parse variant tried reproduces 686/689). Anchors are presence proofs only; the load-bearing zero-row claims are exact. 2 six-J cells remain NOT_RUN identity-flagged; 8 six-E windows INCONCLUSIVE_AGED_OUT — as disclosed. |
| D1 | SHORTLIST rows | **PASS w/ NOTE F-3** | 6 spot-checked rows (PB1, ES-F1, NQ-F1, FX-F3, JF3, AF3) carry dims/ranks/schedulability byte-consistent with ten-hypo `cross/RANKING_AGGREGATION.md` s1 (e.g. AF3 (3,3,2,3,1)=12 r1 PB_PARK; JF3 r2; FX-F3 r5; ES-F1 r8 CAP_BLOCKED; NQ-F1 r9). Framing-A "ES only = PB1 24" matches SPEC_PB1_ES §6 (P-A 8 + P-B 8 + FOMCIN 4 + C1-C4 4 = 24; "A-r4 đúng 24") and the cap law (no D4 change). NOTE: REPORT_VI says "40 family rows"; strict table-row count = 38 (6+5+9+7+5+6) — 40 only if the two combined C-08/C-11 rows are split. |
| D2 | BUDGET totals | **PASS** | All 16 option totals reconcile from their own `identities_by_category` leaf identities after excluding the five declared derived-subtotal keys (`controls_total`, `non_control_total`, `clock_only_shadow_arms(+_if_lifted)`, `controls_total_if_lifted`): ES 24/35/46/60/67; NQ 22/29/36/43; 6J 29/36/33; FX 44/66/96; 6A total 0 (PARK) with 26 if-lifted. Chains verified against CENSUS_FINAL §1: ES-F1/F2 8+3=11, F3/F4 4+3=7, aggregate 36; ES-1 = 24+11 = 35; NQ-A = 11+11; J-A = 11+7+11 (matches census "JF3 11 + JF2 7/host + JF1 11"); FX-A CONV-D = (8 core + 3 controls) × 2 families × 2 legs = 44; 6A = 11+11+4 = 26. Reconciliation 43 = 36+7 (PB1 excluded) / 60 = 24+36 / 67 = 60+7 closes exactly. |
| D3 | No undeclared convention mixing | **PASS** | Every option names its convention(s); FX options carry `total_census_native_disclosed` = 32/48/72 alongside CONV-D 44/66/96; ES options name the CONV_A/CONV_B blocks. No undeclared cross-convention sum found. |
| E1 | CYCLE_PROPOSAL gate sequence | **PASS** | Proposal §1: (pre-freeze D3/e.1-e.4) → registration at ROOT → prelaunch A7 key 1 → exact-arm dry-run (post-registration by law) → typed GO key 2 → scored under heavy lock + reproduction twin + terminal A7 — matches CYCLE_LAUNCH_DRAFT §6 steps 1-7 in order. GO phrase quoted as template (`GO FUTURES-ES-PB1-V1 SCORED EXECUTION` / `GO <REGISTERED-CYCLE-ID> SCORED EXECUTION`); "0 scored runs" consistent with every lane artifact. |
| E2 | OWNER_DECISION_PACKET | **PASS** | All decision slots EMPTY (options enumerated, none selected; footer "Slots empty; nothing self-ratified"); interpretation-override line present (§"Interpretation ruling the owner may override"); minimal decision sentence present; fail-closed defaults stated (header + OD-2 "A (default if silent)" + early-GO "dies unconsumed"). |
| E3 | REPORT_VI accuracy | **PASS w/ NOTE F-4** | Claims match lane artifacts: 0 scored; per-symbol blockers table == CYCLE_PROPOSAL §3 (ES: registration+A7+GO only; NQ: +D9+ceiling; 6E/6B: +PB2+ceiling; 6J: +ceiling+BBO/cost; 6A: +PB3+D8). NOTE: REPORT_VI L72 says "fee_a7/* (9 artifact)" — the dir holds 10 non-handoff artifacts. |
| F1 | Wave diffs round-dir only | **PASS** | `diff --stat 893db28c 75f7ea96`: 41 files, all under `research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/` (budget/cal_close/dispatch/fee_a7/shortlist). `diff --stat 75f7ea96 fae2158f`: 3 files (REPORT_VI.md, synth/CYCLE_PROPOSAL.md, synth/OWNER_DECISION_PACKET.md), all round-dir. Insertions only. End status: only verify/** + this handoff untracked. |
| F2 | Handoff schema | **PASS** | 4 lane handoffs parse; schema `zcode_orch_v3_handoff@1`; actual_start_sha bare 40-hex == 893db28cd1b3299c914369ec08cb33f68bf5798a; dispatch_sha same; commit_sha null; cycle_id correct. (FEE-A7 additionally discloses its full git command list incl. the packet-permitted `show --stat`.) This VERIFY handoff uses dispatch_sha/actual_start_sha = fae2158f3436eb7f0ea600481215dcf1537c4044, commit_sha null. |
| F3 | P3 non-usage | **PASS** | Every `futures-behavior`/`b583c33a` hit in round outputs is a prohibition or non-access disclosure (manifest absolutes; handoff write-boundary statements); `fee_a7/propagation_grep.txt` path hits are `research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002/**` — a committed round dir in THIS repo, not the quarantined worktree. Zero usage. |
| F4 | No registry/ledger/plan writes | **PASS** | Wave diffs contain only round-dir files; no `plans/`, no `CYCLE_REGISTRY`, no ledger paths in either diff. |

## Findings

- **F-1 (MINOR)** — `cal_close/CAL_CLOSE_REPORT.md` §1/§4.2, `calendar_close_delta.json`
  corrections[1], `dispatch/handoff_CAL-CLOSE.json` T2/limitations: the recovered capture
  `svc_20260401_20260722114222.json` is described as mismatching "round-1's claimed sha
  `0700f57c…`". Round-1's `es/q5_independent_verify/verify_report.json` (L164-169) records the
  claimed sha for THIS file as `c8388564a2b7feaa1c5e9823c72c0f28c21c00493ef5374a95e0640955b0bddd`
  (status MISSING_FROM_DISK), while `0700f57c…` belongs to `svc_20260401_20260129012143.json`
  (adjacent line in `sha256_sums_mine.txt` L10). The disclosed conclusion (round-1 claimed-hash row
  unverified; lane rests on its own d1c4048f chain) is correct under either reference — d1c4048f
  matches neither hash — but the citation names the wrong round-1 row. For the round-1 record:
  both round-1 hash rows for 20260401-window captures (c8388564 claimed-but-missing;
  0700f57c present-and-verified for a different capture) remain uncontradicted by this round; the
  recovered capture simply has no round-1 hash to contradict.
- **F-2 (NOTE)** — anchor counts: lane states id=58 → 685 / id=133 → 688 rows in the 709-row CDX;
  this lane's re-parse (multiple variants) gives 686 / 689. Zero-row claims (42/69/37/146 → 0) are
  exact and are the only load-bearing part.
- **F-3 (NOTE)** — REPORT_VI "40 dòng family" vs 38 strict table rows in SHORTLIST_6SYM.md (40
  only under a split-C-08/C-11 counting convention).
- **F-4 (NOTE)** — REPORT_VI "fee_a7/* (9 artifact)" vs 10 non-handoff artifacts on disk.
- **F-5 (NOTE)** — `CAL_CLOSE_REPORT.md` L4 worktree path is written as
  `/Users/hoangminhlong/.worktrees/...` (missing repo-root segment), self-corrected inline on the
  same lines with the absolute path. Cosmetic.
- **F-6 (NOTE, self-report)** — this verify lane ran `git branch --show-current` inside its first
  compound status command, one step beyond the dispatch's permitted command list (read-only;
  disclosed here and in the handoff).

## Verification artifacts produced by this lane (verify/)

`rerun_validator_selftest.log` · `rerun_validator_realmode.log` · `rerun_validator_report.json` ·
`rerun_propagation_canonical.txt` — all captured at HEAD fae2158f from byte-identical inputs.

— End VERIFY_REPORT.md. Audit only; the written artifacts are authority.
