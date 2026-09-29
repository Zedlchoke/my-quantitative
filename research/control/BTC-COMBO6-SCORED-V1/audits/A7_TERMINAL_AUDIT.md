# A7 TERMINAL AUDIT — BTC-COMBO6-SCORED-V1 — 2026-09-29

- Auditor: A7-TERM (fresh context; implemented, scored and reproduced nothing audited
  here; recompute-from-bytes with an A7-written stdlib-only script — no
  `research.btcombo6` imports on any verification path; every scored claim treated as
  a refutation target).
- Target: worktree `.worktrees/btc-combo6-scored-v1/integration`, branch
  `orca/btc-combo6-scored-v1-integration`, HEAD
  `7f3cce39df0cfe1d8aed40344d60c283a8b94bd8` (scored + repro landing).
- Reproduction twin (read-only): `.worktrees/btc-combo6-scored-v1/repro_twin`,
  detached at freeze `c0f97a9db2e460707188877348af01d1c5d395d6`.
- Audit question: is the heading-negative terminal `COMBO6_NO_INCREMENTAL_VALUE`
  real, correctly computed, correctly labeled, honestly closed — and were the two
  positive legs (LEG-2, LEG-3) fairly treated in the verdict logic?

## Findings

| item | result | evidence | severity |
|---|---|---|---|
| T-1 DSR claim not backed by artifact bytes | SCORED_REPORT.md L57 says "DSR computed in artifact"; NO `dsr`/`sharpe`/`deflated` field exists in any scored artifact (integration or twin; case-insensitive grep = 0 hits across all 4 JSONs; combo metrics keys enumerated). Plan §8 requires DSR per combo cell when ≥100 observations — combo has 6,080 obs, condition met, value absent. Does NOT touch P1–P7 or the label (DSR is not a bar input). Report misstatement + §8 deliverable gap. | grep + metrics-key enumeration (both worktrees) | MEDIUM |
| T-2 Ledger header `freeze_commit: "PENDING_FREEZE"` | Engine constant (`combo.py` `FREEZE_COMMIT_PLACEHOLDER`), never resolved at scored time. Freeze sha is pinned unambiguously in ≥5 other records (FREEZE.md SHA chain, SCORED_REPORT L3, REPRO_REPORT L5, R_REPRO.json, lock_run_summary.json `freeze_sha`). **Recommendation: accept the placeholder — do NOT hand-edit TRIAL_LEDGER.jsonl** (`update_ledger` silently drops non-standard rows on any recompute, and a manual edit would break the twin equality property); the terminal/close record must instead state freeze `c0f97a9d` explicitly (condition C2). | TRIAL_LEDGER.jsonl L1; combo.py L29, L421 | LOW |
| T-3 Registry row stale at audit time | `plans/CYCLE_REGISTRY.json` still reads head `c0f97a9d`, budget `{used:0}`, `go_phrase_state: REGISTERED_NOT_CONSUMED`, phase "scored 0/12 awaiting two-key" — pre-GO state. Expected (registry is gate-written by A1/orchestrator; audit precedes close), but the close MUST update: head `7f3cce39…`, budget used 7, GO CONSUMED, terminal `COMBO6_NO_INCREMENTAL_VALUE` (condition C2). | registry row vs actual state | LOW |
| T-4 Incident I-1 (dispatch digest typo) verified | Actual stress-2.0 content digest independently recomputed from artifact bytes in BOTH worktrees = `e1a43807dd659175fbda60b3…` (char 22 = `b`), equal to artifact self-declaration, all 7 ledger row dicts, twin artifact, twin ledger. The `…fbda6033…` variant exists nowhere in any artifact or ledger — it was only ever in the R-REPRO dispatch packet constant. Typo confirmed in the dispatch, not the artifacts; every terminal record carries the correct digest (condition C3 keeps it that way). | A7 digest recompute (both worktrees); REPRO_REPORT §3-I-1; R_REPRO.json incidents[0] | INFO |
| T-5 Combo MDD exact value not independently derivable | Artifacts carry metrics + trades but no bar-level equity series, so MDD 97,270.69 cannot be recomputed exactly from artifact bytes. Internal consistency verified (equity_end −3,617.86 = 60,000 + Σnet exactly; sleeve sum identity in report L22 checks out). A7's realized-equity (trade-close) max-DD lower bound = **95,718.17 > 15,000** independently confirms P4 FAIL regardless of the un-recomputable intra-trade component. | recompute script; combo metrics | INFO |
| T-6 SCORED_REPORT gate table row "reproduction \| PENDING" stale at landing | Report written 09:53Z, repro landed 10:01Z, both committed together in 7f3cce39; the committed gate table still says PENDING/"in flight" while REPRO_REPORT.md (same commit) is ALL_MATCH. No factual contradiction (REPRO_REPORT is the authority), but the row is stale in the landing commit. | SCORED_REPORT.md L72 vs commit 7f3cce39 contents | INFO |
| T-7 Engine verdict vocabulary superset | `_terminal_outcome` also defines `COMBO6_UNCATEGORIZED_DEFER_OWNER`, which is NOT in plan §7's predecided set. It is a defer-owner escape hatch and was NOT invoked: the emitted label `COMBO6_NO_INCREMENTAL_VALUE` is in the predecided set and matches §7's definition exactly (some legs pass P1; combo fails P7). | engine.py L445-460; plan §7 | INFO |

Finding count: **CRITICAL 0 · HIGH 0 · MEDIUM 1 (T-1) · LOW 2 (T-2, T-3) · INFO 4 (T-4..T-7)**.

## Checked and clean (absence reporting)

1. **C-1 SHA chain + cleanliness (both worktrees)**: integration HEAD =
   `7f3cce39df0cfe1d8aed40344d60c283a8b94bd8`; parent chain exactly
   `7f3cce39 → ce1dd0ef (A7-pre+GO) → c0f97a9d (FREEZE) → 2db0e19b (IMPL) →
   2481f307 (BASE/plan)`; `git status --porcelain` empty (audit artifacts excluded
   until A1 lands them). Twin detached at `c0f97a9d…`, HEAD unmoved, ZERO tracked-file
   modifications (`status --porcelain` non-`??` count = 0); only untracked outputs
   (scored/, TRIAL_LEDGER.jsonl, scored_repro/) exactly as R_REPRO declared.
2. **C-2 Content digests re-derived from bytes** (A7 canonical-JSON re-implementation,
   `sort_keys` + compact separators + `ensure_ascii`, key set minus `generated_utc` /
   `content_sha256`): stress 1.0 `d7876974…5e5e6`, 1.5 `f5eb9c91…a9276`,
   2.0 `e1a43807…2776d` — each equals the artifact's self-declared
   `content_sha256`, the ledger's `scored_content_sha256` dict (identical dict in all
   7/7 rows), and the twin's digest. File-level sha256s (8790e17e…/3a8ea4e6…/d2ed6737…
   integration; 136d59c1…/0ff829cb…/0189e112… twin) match compare_artifacts.json and
   differ across worktrees only via `generated_utc`, as disclosed.
3. **C-3 Ledger integrity**: 1 header + 7 `scored_outcome` rows (COMBO + LEG-1..6) =
   8 lines ≤ 20-row cap; observed 7 = published 7 = 7 unique cells; budget_max 12,
   used 7 ≤ 12 (no overflow); `go_phrase` == registry phrase
   ("GO BTC COMBO6 SCORED V1 SCORED EXECUTION"); every row's stress block (net +
   trade_count per tier) equals A7's trade-list recompute exactly (table below).
4. **C-4 PIT / sealed tail at terminal**: across ALL three stress artifacts, every
   leg's every trade satisfies `fill_ts < 2025-12-29T00:00Z` and
   `exit_ts < 2025-12-29T00:00Z` (max fill 2025-12-26T02:25Z, max exit
   2025-12-28T23:55Z; violations = 0). B1 wall exit in-window (implied exit px
   87,920.50 at the last in-window 5m close; `open=False`). Timestamp grep of the
   artifacts finds the wall value only at fold-calendar boundary declarations plus
   `generated_utc`. Registry `s1: SEALED_UNTOUCHED`. No sealed-tail bytes were
   evaluated.
5. **C-5 Verdict-law conformance (§6/§7)**: A7 recomputed all seven bars from
   artifact numbers: P1 net −63,617.86 ≤ 0 FAIL; P2 PF 0.9158 < 1.25 FAIL; P3 4/10
   net-positive folds < 7 FAIL; P4 MDD 97,271 > 15,000 (=25% of 60k) FAIL; P5
   stress-1.5 net −100,107.48 ≤ 0 FAIL; P6 vacuous-PASS (plan §6 conditions P6 on
   net > 0); P7 −63,618 < B1 +10,689 and < mean-leg −10,603 FAIL. Some legs pass P1
   (LEG-2 +4,707.81, LEG-3 +1,662.25) and combo fails P7 ⇒ §7's predecided label
   `COMBO6_NO_INCREMENTAL_VALUE`. A7's independent label = engine label = artifact
   verdict block = ledger COMBO row. No label invented outside §7 (see T-7 for the
   unused escape hatch).
6. **C-6 Fair treatment of the positive legs**: LEG-2 and LEG-3 verdict rows record
   `p1_net_positive: true`, `non_vacuous: true`, `trade_count_only: false` in BOTH
   the artifact and the ledger (byte-equal). SCORED_REPORT shows them with their
   exact positive nets, PFs (1.0537 / 1.0280) and pos-folds (6/10, 5/10), calls them
   "the only positive cells", and the terminal text explains rather than buries them
   ("two legs pass P1 in isolation … but the combined portfolio fails every
   risk/value bar"). §7's label branch (some-legs-P1, not REJECT_ALL) is the
   honest disposition of the negatives-plus-positives pattern. No post-PnL
   parameter changes: `git diff c0f97a9d..HEAD -- research/btcombo6/` is EMPTY
   (landing commit touched control/evidence files only).
7. **C-7 Baselines recomputed**: B1 — entry fee = 10,000 × 6bps = 6.000000 (exact);
   exit fee 15.9595 = 87,920.50 × 0.30253589 qty × 6bps (exact); gross identity
   qty × (87,920.50 − 33,053.93) = 16,599.1064 (exact, d=0);
   net = gross − 6.00 − 15.9595 − 5,887.936 = **+10,689.2109** (exact vs artifact);
   fill 33,053.93 @ 2021-01-04T00:00Z as reported; total fees 21.96 as reported.
   Funding magnitude sane vs census: 5,460 in-window events, implied mean charged
   rate 1.078e-4 vs census median 9.72e-5 (same order, positive skew plausible).
   B3 — prior-fold argmax (ties lowest id, F1→LEG-1) re-run on A7's per-fold nets:
   chosen sequence F1 LEG-1; F2,F3 LEG-2; F4–F7 LEG-3; F8–F10 LEG-2 — identical to
   artifact; total **−12,645.2406** (exact). B0 = 0 sanity present.
8. **C-8 Reproduction evidence internally consistent**: compare_artifacts.json —
   `content_sha256_equal` true and `canonical_equal_ignoring_generated_utc` true on
   all 3 tiers, first_diff null everywhere, integration==twin digests (A7 re-derived
   the twin digests independently); ledger equal ignoring the 3 timestamp fields (A7
   re-compared the twin ledger itself: 8 rows, equal). truncation_check.json —
   18/18 cells `prefix_ok`+`count_ok` true, `all_pass` true; **A7 spot-recomputed
   all 18 expected prefix lengths from the twin artifact's own trade lists
   (exit_ts < cut): LEG-1 1778/2555/3549, LEG-2 188/269/370, LEG-3 89/144/206,
   LEG-4 301/406/546, LEG-5 339/463/621, LEG-6 205/278/391 — including the mandated
   LEG-3 @ 2024-01-01 = 144 — all 18 match**, and LEG-3 total 226 matches the
   full-run artifact. Lock evidence: lock_run_summary.json released_status FINISHED
   02:56:44.517Z, scored_rc 0, truncation_rc 0.
9. **C-9 Two-key + budget + locks**: GO_RECORDED key_1 sha256
   `7f89e63948111004…3f01` == A7's shasum of audits/A7_PRELAUNCH.md (byte-pinned);
   key_2 verbatim string == OWNER_DIRECTIVE_2026-09-29.md verbatim quote (A7
   string-compared); consumption order correct (A7 verdict with 0 unresolved C/H
   first). Budget 7/12. Heavy-lock history (heavy_worker.history.jsonl) contains
   exactly 2 BTC-COMBO6 rows: E_SCORED_CELLS pid 19747, phase done, rc 0, 7.4s,
   command = integration `run_btcombo6.py --mode scored`, expected artifacts = the 3
   stress JSONs; R_REPRODUCTION pid 20268, release note "scored rc=0; truncation
   check rc=0 (all legs/cuts PASS)". Current lock state FREE_PROVEN. F-1 remediation
   verified on disk (root `run_scored_locked.py` CMD no longer passes `--stress-all`);
   F-2/F-3 remediations verified (root SPEC_FREEZE.md now carries EVAL_END
   2025-12-29 (erratum E1); DATA_COST_FREEZE.md annotates 5,451 pre-erratum vs 5,460
   corrected-window counts).
10. **C-10 Freeze pins still true at HEAD**: dry artifact
    `53e3122e…3806`, data_manifest `ba6dcae4…9c56f`, IMPL handoff
    `e3e7801e…775df` — all re-hashed by A7 at HEAD, all equal FREEZE.md pins;
    corpus_digest `e270c9c7…06232` present and equal in all three scored artifacts.

## Recompute table (committed value vs A7 recompute vs delta)

All from `scored/btcombo6_scored_stress1.0.json` trade lists unless noted.
Delta = A7 recompute − committed. Tolerance ±0.01; all deltas are 0 or float-noise.

| quantity | committed | A7 recompute | delta |
|---|---|---|---|
| LEG-1 net / n / PF | −46,534.2066 / 3,795 / 0.7813 | −46,534.206566 / 3,795 / 0.781338 | 0 |
| **LEG-2 net / n / PF** | **+4,707.8123 / 401 / 1.0537** | **+4,707.812291 / 401 / 1.053698** | **0** |
| LEG-3 net / n / PF | +1,662.2540 / 226 / 1.0280 | +1,662.254004 / 226 / 1.028011 | 0 |
| LEG-4 net / n / PF | −6,618.2198 / 581 / 0.9496 | −6,618.219827 / 581 / 0.949639 | 0 |
| LEG-5 net / n / PF | −9,515.5085 / 660 / 0.9365 | −9,515.508545 / 660 / 0.936469 | 0 |
| LEG-6 net / n / PF | −7,319.9905 / 417 / 0.9360 | −7,319.990491 / 417 / 0.936017 | 0 |
| **COMBO net / n / PF** | **−63,617.8591 / 6,080 / 0.9158** | **−63,617.859135 / 6,080 / 0.915785** | **0** |
| Σ(leg nets) − combo net | — | −63,617.859135 vs −63,617.859135 | 0 |
| COMBO per-fold F1..F10 | −24,991 / −12,330 / −39,078 / −10,639 / +11,550 / +10,876 / −100 / +9,504 / +4,295 / −12,706 | −24,990.71 / −12,329.68 / −39,078.35 / −10,638.58 / +11,550.11 / +10,875.84 / −99.60 / +9,504.48 / +4,294.85 / −12,706.23 | ≤ 0.41 (report rounds to $) |
| COMBO net-positive folds | 4/10 | 4/10 | 0 |
| COMBO equity_end | −3,618 (=60,000+net) | −3,617.8591 | 0 |
| COMBO MDD | 97,271 | ≥ 95,718.17 (realized lower bound; P4 FAIL confirmed) | n/a (T-5) |
| COMBO net stress 1.5 / PF | −100,107.48 / 0.871 | −100,107.478520 / 0.871008 (from 1.5 trades) | 0 |
| COMBO net stress 2.0 / PF | −136,597.10 / 0.8286 | −136,597.097906 / 0.828554 (from 2.0 trades) | 0 |
| B1 entry fee | 6.00 (=10,000×6bps) | 6.000000 | 0 |
| B1 exit fee / gross / funding | 15.96 / 16,599.11 / −5,887.94 | 15.9595 / 16,599.1064 / −5,887.9360 | ≤ 0.01 |
| **B1 net** | **+10,689.21** | **+10,689.2109** | **0** |
| B3 total | −12,645.24 | −12,645.240573 | 0 |
| content_sha256 1.0 / 1.5 / 2.0 | d7876974… / f5eb9c91… / e1a43807…fbda60b3… | identical (re-derived, both worktrees) | 0 |
| truncation LEG-3 @ 2024-01-01 | 144 (expected prefix) | 144 (counted from twin artifact trades) | 0 |
| my P1–P7 vector | FAIL/FAIL/FAIL/FAIL/FAIL/PASS(vac)/FAIL | identical | — |
| my terminal label | COMBO6_NO_INCREMENTAL_VALUE | COMBO6_NO_INCREMENTAL_VALUE | — |

## Negative-terminal honesty assessment

The negative is real and honestly closed: every number in SCORED_REPORT reconciles
to the artifact bytes exactly; the bars were evaluated with the frozen §6 thresholds
(no bar loosening after PnL visibility); the §7 label is the predecided one and its
preconditions independently re-verified; the two positive legs are recorded as
PASSes with exact arithmetic and are the stated reason the label is
NO_INCREMENTAL_VALUE rather than REJECT_ALL; the engine is byte-identical to the
audited freeze; the report itself fences off rescue ("NO parameter rescue, NO leg
removal, NO re-run under relaxed costs"). Nothing was buried; the only defects found
are documentation-level (T-1, T-6) and governance bookkeeping at close (T-2, T-3).

## Conditions (A1-executable at close; none require touching frozen artifacts)

- **C1 (T-1, MEDIUM)**: The terminal record must correct the DSR claim:
  TERMINAL_DECISION/close packet records `DSR: NOT_COMPUTED` for the combo cell
  (6,080 obs met the ≥100 precondition; value absent from artifacts) and flags
  SCORED_REPORT L57 "DSR computed in artifact" as a misstatement (append-only
  erratum; do not rewrite the committed report/artifact bytes). Optionally compute
  DSR honestly from the artifact trades in the close packet with method disclosed.
- **C2 (T-2, T-3)**: Close binds the cycle to the code freeze explicitly:
  registry row updated (head `7f3cce39…`, budget used 7/12, GO CONSUMED, terminal
  `COMBO6_NO_INCREMENTAL_VALUE`) and TERMINAL_DECISION.md states freeze
  `c0f97a9d…` + chain. TRIAL_LEDGER.jsonl is NOT hand-edited; `PENDING_FREEZE`
  stays as the disclosed engine placeholder.
- **C3 (T-4)**: All terminal/close records carry the correct stress-2.0 content
  digest `e1a43807dd659175fbda60b3239d1238757505ef52ebe70d0bc438cd24a2776d`
  (never the dispatch typo `…fbda6033…`), with incident I-1 acknowledged.

A7_TERMINAL_VERDICT: CONFIRM_WITH_CONDITIONS
