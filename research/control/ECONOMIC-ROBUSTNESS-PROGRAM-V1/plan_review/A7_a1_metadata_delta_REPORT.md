# A7 fresh-context delta review — A1 metadata patch (FX-RANGEFADE-2M-SHADOW-V1)

- Audit time: 2026-09-25T07:14:20Z (all times UTC unless noted)
- Auditor: A7 fresh-context delta reviewer (audit only — no repair, no restart)
- Object: FX worktree `/Users/hoangminhlong/my-quantitative/.worktrees/fx-rangefade-2m-shadow-v1`,
  branch `orca/fx-rangefade-2m-shadow-v1`, HEAD `651b5c94cea005d9012df786158aa6efeebf6bf2`
  (parent `6815602517acd8ab9e59c58f7e51f2d2722c1eba` — both measured, match dispatch)
- Owner authorization scope: PREPARATION only. Restart NOT authorized; daemon pid 72270
  left untouched by this audit.

## Exact diff stat

```
68  0  research/control/FX-RANGEFADE-2M-SHADOW-V1/daemon/fx_shadow_core.py
25  8  research/control/FX-RANGEFADE-2M-SHADOW-V1/daemon/shadow_daemon.py
128 0  research/control/FX-RANGEFADE-2M-SHADOW-V1/tests/test_a1_metadata_patch.py
3 files changed, 221 insertions(+), 8 deletions(-)
```

(Dispatch's "+33/−8" for shadow_daemon.py is the churn total: 25 insertions + 8 deletions.)

## VERDICT: REMEDIATION_REQUIRED

0 blocking safety issues; 1 HIGH wiring defect that makes the patch unable to deliver its
owner-approved restart outcome, plus 1 MEDIUM honesty finding and 4 LOW. The restart must
NOT be GO'd until F1 is remediated by a follow-up commit in the same lane; everything else
about the patch is sound and restart-ready.

---

## D1 Scope — PASS

- `git diff --name-only 68156025..651b5c94` = exactly the 3 declared files.
- `fx_shadow_core.py`: pure additions between existing constants — `ACTIVATION_SKEW_TOLERANCE_S`
  + `derive_a1_activation` + `short_beta_label_for` (hunk has zero `-` lines). Frozen surface
  (`v2_lib.py`, `engine.py`, the entire signal/fill/cost/replay path) byte-identical at git level.
- `shadow_daemon.py` hunks touch ONLY: the boot metadata section (artifact read, cost_book
  journal row kwargs, derive call, first_ctrl_ts), the label line, and the `a1_controls` state block.
- Journal: `Journal.log` opens append-only (`"a"`), monotone seq; kwargs land on NEW rows only.
  On-disk `shadow_journal.jsonl` = 108 rows, 0 contain `t_ctrl_artifact`/`cost_book_row_ts`;
  the single cost_book row (seq 97, 05:35:04+00:00) keeps its old shape. No history rewrite.
- Disclosure (F5): the schema change is additive-plus-drop on NEW rows only — the stale
  `control_phase="PHASE_I_code_only_NOT_ACTIVATED"` kwarg is no longer written on new boot rows.
  `grep -rn control_phase --include=*.py` over the cycle: zero consumers. Consistent with the
  owner-approved "placeholders removed" intent; history untouched either way.

## D2 T_ctrl authority — PASS in the derivation, FAIL in the wiring (see F1/HIGH)

- `derive_a1_activation` returns artifact `phase_a.t_ctrl_utc` verbatim as `T_ctrl`; the journal
  ts appears ONLY inside `cross_check` (skew) and as the distinct `cost_book_row_ts` journal field.
  Exhaustive read + grep: no code path assigns any journal ts to `T_ctrl`.
- Production VALUES through the function: artifact `2026-09-25T05:35:03Z` + cost_book
  `2026-09-25T05:35:04+00:00` (seq 97, on disk) → `ACTIVATED`, skew 1.0s, `CONSISTENT`
  (test `test_i_production_case_one_second_skew_consistent` + auditor inline re-run). PASS.
- BUT the daemon never feeds those production values: `shadow_daemon.py` line ~492 sets
  `_cb_ts = now_utc().isoformat(timespec="seconds")` (the FRESH boot row) and passes that to
  `derive_a1_activation`. The activation-time journal row (seq 97 @ 05:35:04+00:00) that the
  owner spec designates as "the journal cost_book row at 05:35:04Z ... CROSS-CHECK evidence"
  is never read. Auditor live simulation at 07:14Z: `derive_a1_activation(ART, now_utc())` →
  `ACTIVATION_UNVERIFIED_FAIL_CLOSED`, `SKEW_EXCEEDS_TOLERANCE`, skew 5900.0s, T_ctrl None,
  label stays `SHORT_BETA_UNSEPARATED — NOT PROMOTABLE` even with ctrl records present.

### F1 (HIGH — wiring defeats the patch's purpose)
The skew check compares T_ctrl against the restart boot time, not the activation-time
cross-check evidence. The pass window [05:35:03Z, 05:40:03Z] closed ~85 minutes BEFORE the
commit existed (07:05:39Z), so the owner-GO'd restart structurally CANNOT produce
ACTIVATED / T_ctrl=05:35:03Z / ACCRUING — it will write FAIL_CLOSED. Fixtures didn't catch it
because they inject `CB_TS` directly and the state-block test is source-string-only.
Fail-closed direction is preserved (no false ACTIVATED, no data corruption) — this is a
purpose/correctness defect, not a safety incident. Remediation sketch: extract the activation-time
`cost_book` row ts from the already-replayed `a1_lines` (event=="cost_book"; seq 97 @
05:35:04+00:00 on disk) and pass THAT to `derive_a1_activation`; keep the fresh boot row
fields as additive evidence. Add one wiring-level fixture that exercises the daemon's actual
input selection.

## D3 Fail-closed matrix — PASS

All dispatch cases verified in fixtures and by direct read: artifact None/unreadable,
`{}`, `phase_a:{}`, non-string t_ctrl → `ARTIFACT_MISSING_OR_UNREADABLE` /
`ARTIFACT_MALFORMED_NO_T_CTRL`; journal row missing → `JOURNAL_COST_BOOK_ROW_MISSING`;
unparseable ts → `TIMESTAMP_PARSE_ERROR`; journal-precedes-artifact (−1s) →
`JOURNAL_ROW_PRECEDES_ARTIFACT_T_CTRL`; skew>300s → `SKEW_EXCEEDS_TOLERANCE`. Every branch:
`ACTIVATION_UNVERIFIED_FAIL_CLOSED` + `T_ctrl: None` + label stays UNSEPARATED — NOT PROMOTABLE
even when ctrl records exist (asserted with `ctrl_emitted=True`). Boundary skew exactly 0.0s →
CONSISTENT. NOT PROMOTABLE holds in every fail branch.

## D4 Label law — PASS

ACCRUING wording contains "no FX-vs-control conclusion" and gates interpretation on the
preregistered decision-count law. UNSEPARATED when no ctrl records OR activation not ACTIVATED.
`grep -rn "SHORT_BETA_SEPARATED"` over the whole cycle dir (py/md/json): zero matches — the old
over-strong claim is gone from code. The on-disk `shadow_state.json` still carries it because the
RUNNING daemon is pre-patch (D7).

## D5 Idempotence / purity / paths — PASS

- `derive_a1_activation` is pure (no clock/random/globals beyond the tolerance constant);
  same inputs → identical dict (tested).
- Artifact read ONCE at boot; path verified: `HERE = daemon/`, `HERE.parent` = cycle root,
  `A1_ACTIVATION.json` exists there (2151 bytes, pinned t_ctrl_utc `2026-09-25T05:35:03Z`).
- `first_ctrl_ts` derived from replayed `a1_lines` (ctrl_open/ctrl_close filtered, sorted):
  journal has seq 103/105 @ `2026-09-25T06:00:06+00:00` → post-fix value will be that ts.
- Python 3.12.14 (venv): the nested-quote f-string (PEP 701) is legal; both patched files
  AST-parse clean.

## D6 Fixtures — PASS 65/65, with honesty finding F2

Auditor ran from the tests dir: `.venv/bin/python -m pytest . -q` → **65 passed in 2.24s**
(15 new: 4 one-second-boundary cases, idempotence, label-law all-branches, state-writer,
7 fail-closed cases incl. parametrized malformed artifacts, scope containment).
- F2 (MEDIUM, honesty): `test_ii_state_writer_uses_derived_block` asserts SOURCE STRINGS, not a
  booted daemon; the boot-input selection (which ts reaches derive) — the exact seam where F1
  lives — is untested. Derivation + label functions ARE behaviorally tested. Given the restart
  is not yet authorized this is tolerable for preparation, but the F1 remediation must add a
  wiring-level fixture; the first authorized restart remains the only in-vivo integration test.

## D7 Running-process truth — CONFIRMED, DISCLOSED

- pid 72270 alive at audit time (elapsed 1:33:36), started `Fri Sep 25 12:35:03 +0700`
  = 2026-09-25T05:35:03Z — matches artifact `new_daemon` (heartbeat 05:35:20Z) — i.e. PRE-patch
  code (commit 07:05:39Z). No restart performed or attempted by this audit.
- On-disk `shadow_state.json` (written by old code, heartbeat 07:07Z) currently shows:
  `phase: PHASE_I_code_only_NOT_ACTIVATED`, `T_ctrl: null`, label
  `SHORT_BETA_SEPARATED (control arms emitting; ...)`, `journal_row_cost_status:
  ACTIVE_SINCE_T_CTRL` — the WRONG placeholders/over-strong claim persist until the
  owner-GO'd restart. EXPECTED; disclosed, not a defect of the patch.

## D8 A3 non-interference — PASS

Commit lives only on `orca/fx-rangefade-2m-shadow-v1`. PSV1 worktree
(`.worktrees/prospective-shadow-v1`, branch main @ `69ddc604`, HEAD committed 05:36:21Z)
predates the patch and does NOT contain it (`merge-base --is-ancestor` false). XSECT decision
2026-09-26T00:00Z still PENDING per `POST_ACTIVATION_AUDIT_2026-09-25.md` ("Now 06:53Z <
decision ⇒ PENDING") and OWNER_DECISIONS.md D4 ("chờ GO").

---

## What the owner-GO'd restart will do

- AS COMMITTED (F1 unfixed): new code loads; A1_ACTIVATION.json read at boot; new cost_book
  journal row gains `t_ctrl_artifact` + `cost_book_row_ts`; state block writes
  **ACTIVATION_UNVERIFIED_FAIL_CLOSED / T_ctrl null / UNSEPARATED label** (skew = restart
  latency > 300s). NOT the intended ACTIVATED outcome. Conservative but purpose-defeating; a
  second restart would be needed after remediation.
- AFTER F1 REMEDIATION (cross-check vs seq-97 row 05:35:04+00:00): state block flips to
  `ACTIVATED` / `T_ctrl: 2026-09-25T05:35:03Z` / `activation_cross_check.skew_s: 1.0,
  verdict CONSISTENT` (journal row cross-check evidence only, never substituted) / label
  `SHORT_BETA_SEPARATION_ACCRUING (control records since 2026-09-25T06:00:06+00:00; ...
  no FX-vs-control conclusion)` / `first_ctrl_record_ts: 2026-09-25T06:00:06+00:00`.

## Residual risks

- Even post-fix, the restart is the first in-vivo execution of the daemon glue (F2); a boot-time
  exception (F3/F4 family) would halt the daemon visibly rather than corrupt anything.
- On-disk state stays WRONG (over-strong SEPARATED claim) for the entire window until the
  authorized restart — consumers of shadow_state.json must treat it as pre-patch output.
- F3: a malformed non-dict artifact (top-level or phase_a) crashes boot with AttributeError
  instead of failing closed gracefully (owner-controlled artifact; low probability).

## Findings ledger

| ID | Sev | One-line advisory |
|----|-----|-------------------|
| F1 | HIGH | Daemon feeds boot-time `now_utc()` into the skew cross-check instead of the activation-time journal row (seq 97 @ 05:35:04+00:00); every future restart yields FAIL_CLOSED — the dispatch's own "state flips to ACTIVATED/ACCRUING" is unreachable; remediate before any owner GO. |
| F2 | MEDIUM | State-block coverage is source-string assertion only; the tested functions are real but the boot wiring seam (where F1 sits) has no behavioral fixture — add one with the remediation. |
| F3 | LOW | Non-dict JSON shapes (top-level list/str, or truthy non-dict `phase_a`) raise AttributeError at boot instead of returning FAIL_CLOSED — fail-closed direction preserved, not graceful. |
| F4 | LOW | `sorted(ln.get("ts") ...)` would raise TypeError on a ts-less journal line; unreachable in practice (Journal.log always stamps ts). |
| F5 | LOW | Journal change is additive-plus-drop on NEW rows only (control_phase placeholder dropped, zero consumers); all 108 existing rows keep the old shape — no history rewrite. |
| F6 | LOW | Pre-existing comment "label flips to separated" (shadow_daemon.py ~line 480) is stale vs the ACCRUING law; cosmetic, not introduced by this patch. |

---

# ROUND 2 — F1 remediation delta confirmation (audit time 2026-09-25T07:19:55Z)

- Object: commit `f811d736b3aa6d1cc8cd1f2c35debb405bd0f874` (parent `651b5c94` — the round-1
  audited HEAD), same branch `orca/fx-rangefade-2m-shadow-v1`. Measured, matches dispatch.
- Diff stat: `fx_shadow_core.py +15/0` (helper `boot_cross_check_ts`), `shadow_daemon.py +4/−1`
  (wiring only), `test_a1_metadata_patch.py +35/0` (3 seam fixtures). Same 3-file lane, nothing
  else touched; frozen surface still byte-identical; tracked tree clean (pre-existing untracked
  files unchanged).

## F1 — CLOSED (verified, not taken on trust)

- Helper returns the FIRST `cost_book` row ts from the replayed journal (parse-error lines
  skipped; ts-less row falls through to fallback; fallback = caller's fresh ts only when no
  prior row exists — a genuine first boot late after T_ctrl still fails closed: correct).
- Daemon wiring verified by diff read: `_cb_ts = C.boot_cross_check_ts(a1_lines, now_utc()...)`
  — `a1_lines` is in scope (journal replay precedes it); fresh clock only as fallback.
- Auditor live simulation against the REAL on-disk journal (daemon-identical replay filtering):
  helper picks `2026-09-25T05:35:04+00:00` (seq 97) → derive → **ACTIVATED, T_ctrl
  2026-09-25T05:35:03Z, skew 1.0s CONSISTENT**; label with ctrl records → ACCRUING
  (…no FX-vs-control conclusion). Empty-journal fallback verified True.
- Fixture 1 additionally encodes the steady state AFTER the first post-patch boot (two cost_book
  rows in the replay: 05:35:04 and a later one) and asserts the FIRST is chosen, plus the
  counterfactual (boot-clock wiring would FAIL_CLOSED). Fixture 2: empty-journal fallback.
  Fixture 3: source assertion the daemon calls the helper and the bare boot-clock assignment
  is gone (string-brittle but positive+negative).
- Informational note (no defect, no new LOW number): on subsequent boots the new row's
  `cost_book_row_ts` field carries the activation-evidence ts (identical to
  `cross_check.journal_cost_book_ts` in state) rather than the boot wall clock; the wall clock
  remains in the row's own `ts` field from Journal.log — no information lost, self-consistent.

## F2 — reclassified MEDIUM → LOW-residual

The seam that hid F1 (boot-input selection) now has behavioral coverage: helper + derive +
counterfactual on realistic journal lines (fixture 1), fallback (fixture 2). What remains is the
generic "main() itself is never booted by tests; fixture 3 is source-level" — the first
owner-GO'd restart is still the in-vivo integration test. Bounded by this round's direct reads
and the live real-journal simulation above.

## Round-2 test evidence

`.venv/bin/python -m pytest . -q` from the tests dir → **68 passed in 1.55s** (65 + 3 new).
Process truth re-confirmed: pid 72270 untouched (same start 2026-09-25T05:35:03Z, elapsed
1:44:10), tracked tree clean, both patched files AST-parse clean on Python 3.12.14.

## ROUND-2 VERDICT: AUTHORIZED_FOR_RESTART_PENDING_OWNER_GO

0 HIGH, 0 MEDIUM, 4 LOW carry-over (F3 non-dict-artifact AttributeError family, F4 sorted-None,
F5 journal schema note, F6 stale comment) + 1 informational (cost_book_row_ts semantics above).
Restart what-will-happen (now realizable): new code loads, artifact read at boot, new cost_book
row carries `t_ctrl_artifact` + `cost_book_row_ts`, and the a1_controls block flips to
`ACTIVATED` / `T_ctrl: 2026-09-25T05:35:03Z` / `activation_cross_check {journal_cost_book_ts:
2026-09-25T05:35:04+00:00, skew_s: 1.0, verdict: CONSISTENT}` / `first_ctrl_record_ts:
2026-09-25T06:00:06+00:00` / label `SHORT_BETA_SEPARATION_ACCRUING (… no FX-vs-control
conclusion)`. Residual risks unchanged: boot-time exception family (F3/F4) would halt visibly
rather than corrupt; on-disk state stays pre-patch/wrong until the restart itself.
