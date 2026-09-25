# A7 PRELAUNCH AUDIT — PSCTV1 AMENDMENT A3 (XSECT identity retirement), Phase I

- Auditor: A7 fresh-context (no prior context; audit only, never repaired)
- Audit date: 2026-09-25 (first measurement 2026-09-25T04:29:37Z)
- Object: PSV1 worktree `/Users/hoangminhlong/my-quantitative/.worktrees/prospective-shadow-v1/integration`,
  branch `orca/prospective-shadow-v1-integration`,
  HEAD measured `73e138601e3ac6a5461bad641478a416fa89cc5b` (== dispatch expected; worktree clean)
- Amendment law: `plans/DRAFT_amendment_PSCTV1_A3_xsect_retire.md` @ root commit `8801639980deda72bf3bace29a53f9a4356d243b`
- GO record: `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/A3_gate/GO_RECORDED.json`

## VERDICT: AUTHORIZED_FOR_ACTIVATION

Nothing HIGH. Two MEDIUM findings (F1 terminal-payload re-emission, F3 fixture
coverage gap on the inline stop-open wiring) are non-blocking: neither touches
exposure, fills, the digest scoping, or the state condition of the law, and
both are independently bounded by this audit's direct code read and behavioral
recompute. Phase A (activation restart) may proceed per §Phase A below.

---

## C1 GO gate — PASS

`GO_RECORDED.json` (schema `erp1_amendment_go_record@1`):
`go_phrase_expected == go_phrase_typed == "GO PSCTV1 AMENDMENT A3 XSECT RETIRE"`,
`form_check: "EXACT_MATCH"`, `consumed_at_utc: 2026-09-25T04:21:15Z`.
Draft §4 contains the byte-identical phrase. Prerequisites recorded and verified:
`draft_committed: true` (draft file present in root commit `88016399`, verified
via `git show --stat`), independent review `PASS r2+2b`
(`DRAFTS_review_round2_REPORT.md` + round-2b handoff record A3 PASS after
A3-MED-1 closure). Authority granted is "Phase I ONLY" — and Phase I is exactly
what `73e13860` did (code + fixtures; no worker restart, no ledger touch).

## C2 Scope — PASS

`git show --stat 73e13860`: exactly the 4 declared files, `360 insertions(+), 1 deletion(-)`:
- `research/shadow_v1/executor.py` (+102)
- `research/control/prospective_shadow_v1/e/shadow_worker.py` (+35)
- `tests/test_xsect_a3_retire.py` (new, +216)
- `tests/test_bandridge_a2_pins.py` (t_act fixture consistency, +8/−1)

Frozen XSECT adapter `research/shadow_v1/families/xsect_fund_carry.py`:
byte-untouched (last commit `7986c297`, long pre-A3; not in the diff; worktree
clean). Wiring sites enumerated by grep across `research/`:
`retire_after_utc` appears ONLY in (a) `executor.py` as the generic
config-gated mechanism, and (b) `shadow_worker.py:730` — inside the
`FAMILY_CARRY` branch (diff context confirms it sits directly after
`config["fill_symbols"] = list(CARRY_TRADED_UNIVERSE)` under
`if family_id == FAMILY_CARRY`). No ILLIQ / PREMFADE / BANDRIDGE config or
family module mentions the retire keys.

## C3 Law correctness — PASS, with findings F1/F3/F4

Verified by reading the `73e13860~1..73e13860` executor diff plus the live file.

1. **None ⇒ zero behavior change.** `retire_after_utc=None` → `retired_now`
   false on every path (`executor.py:809-812`, `:943-949`); `_rebalance_steps`
   and all event construction unchanged. Digest: the retire keys are injected
   into the `config_digest` payload ONLY under
   `if self.retire_after_utc is not None` (`executor.py:447-456`) — same
   conditional-injection pattern as the A2 `cost_aware_sizing` key.
   Recompute with the real `canonical_digest`: payload WITHOUT the keys is
   byte-identical to the pre-A3 payload (gate-off equality proven), payload
   WITH the keys yields a different digest — i.e. the XSECT identity moves at
   activation and ONLY XSECT's.
2. **Stop-open (R-1).** Inline at `executor.py:813-818`:
   `if retired_now and not block.blocked: approved = {}`. Empty targets make
   opening impossible. Correct. (Blocked-path note: when `block.blocked`,
   `final_weights` stays `{}` anyway — no orders can escape; the record is
   still honestly flagged `retired`.)
3. **Closing permitted (R-1, distinct law).** `_rebalance_steps({}, ...)`
   computes `desired={}` and, for every held symbol, emits phase-1
   `reduce_longs` sells / phase-2 `cover_shorts` buys toward flat
   (`executor.py:1131-1163`). Verified behaviorally: a held 0.5 ETHUSDT long
   yields exactly `[("ETHUSDT","sell",0.5)]`. The two laws are distinct and
   both hold.
4. **Terminal row (R-2) — state condition holds.** Emission gate
   `retired_now and self.retire_terminal and exposure["gross"] == 0.0`
   (`executor.py:937`) where `exposure` is measured AFTER this decision's
   fills (`:864-865`) — a measured state at a decision boundary, never a
   timestamp assumption. Mark gap ⇒ `gross=None` ⇒ no terminal row (fail-safe).
   Payload carries `terminal_label` = `IDENTITY_RETIRED_COST_DOMINATED` (worker
   constant `XSECT_RETIRE_TERMINAL`), pinned
   `historical_verdict_label` starting `CANDIDATE_FAIL`, full decomposition
   (starting_cash/equity/cash/counts/books) and `equity_basis_note` naming the
   decision-row-ledger vs valuation-mark basis.
   - **F1 (MEDIUM): no one-shot latch.** The gate has no "already emitted"
     state, so the terminal payload re-attaches to EVERY post-T_ret decision
     row measured flat — confirmed by behavioral recompute. The in-code claim
     "Exactly one row per family (deterministic terminal event id; run_due's
     known_ids idempotence covers re-runs)" is NOT enforced: the payload
     carries the per-decision `event_id` (unique per scheduled stamp), so
     `known_ids` dedup only covers re-runs of the SAME decision, not later
     decisions. Downstream consumers must take the FIRST
     (`min measured_flat_at_utc`) as THE terminal record, or a small latch can
     be added post-activation. The load-bearing state condition itself is
     correct and fail-safe.
   - **F2 (LOW, dispatch-expectation correction).** Because `exposure` is
     measured post-fill, the terminal payload coincides with the CLOSE
     decision itself, not "the next decision when flat" as the dispatch packet
     predicted. See C5 for the corrected Phase A expectation.
5. **`_retire_override` is dead in production** — defined `executor.py:951-959`,
   called only by the test fixture. The live override is the inline block.
   Bounded by F3 below.

## C4 Timestamp law — PASS

- `XSECT_RETIRE_AFTER_UTC = "2026-09-25T05:45:00Z"` committed at
  `shadow_worker.py:241` (matches the dispatch constant; fixture also pins it).
- Running e-worker: pid 57505, `ps lstart` = 2026-09-25 10:57:05 +0700 ==
  **03:57:05Z**, cwd = the PSV1 integration worktree, command
  `shadow_worker.py --shadow-start 2026-09-14T23:48:01Z --runtime-root results/prospective_shadow_v1`.
  It started 28 minutes before commit `73e13860` existed (authored 04:25:17Z)
  from the pre-A3 tree (`73e13860~1 == 2ab63141`, the A2 Phase A activation
  commit that documents this very restart). Python loads code at import time;
  the long-running loop never re-imports — so the running process provably
  ignores the constant, exactly as the transition-window law assumes.
- Ledger honesty: 11 rows total in
  `results/prospective_shadow_v1/ledgers/XSECT-FUND-CARRY-7D.jsonl`;
  **0 rows at/after the 04:21:15Z GO** (last row scheduled 00:00:00Z,
  observed 00:17:35Z). The transition window produced no old-law rows, so
  nothing needed a `TRANSITION_OLD_LAW` label; nothing was backfilled.
- Deadline: audit clock 2026-09-25T04:29:37Z vs T_ret 05:45:00Z → ≈75 min
  margin, AND the XSECT decision clock is daily 00:00:00Z (11/11 rows), so the
  first decision at/after T_ret is **2026-09-26T00:00:00Z**. A restart any
  time before that stamp enforces the law at the first affected decision; the
  worker comment additionally documents moving T_ret forward if activation
  slips past a decision (the pre-A3 running worker is unaffected by such a
  move). Deadline risk: LOW.

## C5 Current XSECT holdings + post-T_ret sequence — PASS (expectation corrected)

Latest ledger row (2026-09-25T00:00:00Z, observed 00:17:35Z):
`target_weights = {ADAUSDT:-0.2, BNBUSDT:+0.2, DOGEUSDT:-0.2, XRPUSDT:+0.2}`
(2 longs BNB/XRP, 2 shorts ADA/DOGE), gross 0.8004, net 0.0, equity
99948.37724941608, cash equal, risk/accounting OK, pre-A3 `code_freeze_sha
af4df157…`, no `retired`/`retire_terminal_row` fields. All 11 event_ids unique.

Corrected Phase A prediction (supersedes the dispatch packet's "terminal at the
NEXT decision"):
- First decision at/after T_ret = **2026-09-26T00:00:00Z** (assuming the Phase A
  restart precedes it): stop-open forces `approved={}`; cover ADA+DOGE shorts,
  sell BNB+XRP longs; all four close in that one decision; `gross` measured
  post-fill is exactly 0.0 → the terminal payload attaches to **that same row**
  (F2), not the next one.
- Every subsequent daily decision (flat) re-attaches the terminal payload (F1);
  the canonical terminal record is the 2026-09-26T00:00:00Z one.
- If the restart slips past 2026-09-26T00:00:00Z without moving T_ret, the
  pre-A3 worker would run old law at that stamp — the worker comment's
  documented timestamp-move procedure exists precisely for this; it must be
  executed BEFORE any decision at/after the current constant.

## C6 Fixtures — PASS (13/13 + 78/78 = 91/91), honesty findings F3/F4

Executed by this audit from the PSV1 integration dir with
`/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest`:
- `tests/test_xsect_a3_retire.py tests/test_bandridge_a2_pins.py -v` → **13 passed**
  (a1, a2, b, c/d, helper-existence + 8 A2 pins)
- `tests/test_shv1_executor.py tests/test_shv1_accounting.py tests/test_shv1_families.py tests/test_funding_accounting.py` → **78 passed**
- Total 91/91, matching the commit message.

Honest assessment of what the fixtures actually exercise:
- **Genuine production paths**: fixture a2 drives the real `_rebalance_steps`
  (the closing-sells law) on a real `SleeveAccount`; fixture b drives the real
  `_retire_terminal_payload` and asserts the label/decomposition/book set;
  fixture c/d pins the worker constant and the single CARRY wiring site.
- **F3 (MEDIUM): the production stop-open wiring is source-asserted, not
  behaviorally tested.** The test executor is built via
  `object.__new__(ForwardExecutor)` bypassing `__init__` (no feed/scheduler),
  so `_execute_decision` never runs; the inline `retired_now`/`approved = {}`
  block is covered only by `inspect.getsource` string assertions
  (`test_retire_override_helper_exists`, and fixture b's
  `exposure["gross"] == 0.0` source check). The behaviorally tested
  `_retire_override` is dead code in production. Residual risk is real but
  bounded: (i) `_retire_is_due`, shared by both paths, is behaviorally
  exercised; (ii) the wiring is 5 lines and this audit verified it by direct
  read; (iii) the string assertions still force the source to contain the
  override and the state condition. A future semantic edit that preserves the
  literal strings could pass fixtures while breaking the law — the honest
  remediation (post-activation) is a feed-stubbed `_execute_decision` fixture.
- **F4 (LOW): misleading fixture docstring.** `_mk_executor` claims
  "Constructs through the real __init__ path" but hand-assigns attributes after
  `object.__new__`, and its `config_digest` is a hand-replicated payload rather
  than the production expression. This audit verified the production digest
  gating independently (C3.1), so the gap does not gate the verdict.

## C7 Ledger append-only — PASS

`ledger.append_event` opens `O_APPEND` with read-back idempotency
("committed bytes are never rewritten"); the `73e13860` diff touches no
ledger-write code path (run_due untouched); worktree clean; 11 rows, all
event_ids unique; no historical row modified (last-row fields consistent with
the pre-A3 identity digests).

---

## Findings summary

| ID | Severity | Finding |
|----|----------|---------|
| F1 | MEDIUM | Terminal payload re-emits on every post-T_ret flat decision (no latch); in-code "exactly one row / deterministic terminal event id" claim not enforced; canonical record = first (min measured_flat_at_utc). State condition itself correct and fail-safe. |
| F2 | LOW | Terminal payload coincides with the close decision (exposure measured post-fill), not the next decision; Phase A expectation corrected (C5). |
| F3 | MEDIUM | Production stop-open wiring in `_execute_decision` covered by source-string assertion only; behaviorally tested `_retire_override` is dead code in production. Bounded by this audit's direct read; recommend a feed-stubbed `_execute_decision` fixture post-activation. |
| F4 | LOW | `_mk_executor` docstring says "real __init__ path" but uses `object.__new__` + hand-built digest payload; production digest gating verified separately (C3.1). |
| F5 | LOW | `data_blocked` early-return rows carry no `retired` flag (they carry no target either; harmless). |

No HIGH findings. No incidents.

## What Phase A requires (activation, per draft §1/§3 and this audit)

1. Restart the e-worker from PSV1 HEAD `73e138601e3ac6a5461bad641478a416fa89cc5b`
   (SIGTERM-clean the current pid 57505, which runs pre-A3 code), BEFORE
   `T_ret = 2026-09-25T05:45:00Z`. Measured margin at audit time ≈75 minutes;
   the hard operational backstop is the first affected decision at
   2026-09-26T00:00:00Z — restart before that stamp (or execute the worker
   comment's documented T_ret-move procedure if activation slips).
2. From 05:45:00Z the committed constant enforces: no new opens; holdings
   close at the first decision at/after T_ret (2026-09-26T00:00:00Z); closing
   fills lawful and required.
3. Expected terminal row: attached to the 2026-09-26T00:00:00Z decision row
   (NOT a later row — F2), label `IDENTITY_RETIRED_COST_DOMINATED`, pinned
   CANDIDATE_FAIL, full decomposition, equity-basis note. Later rows will
   re-carry the payload (F1) — consume the first.
4. Record the actual activation moment to the second in a Phase A artifact;
   ledger remains append-only; no backfill of the quiet transition window
   (0 rows since the GO).
