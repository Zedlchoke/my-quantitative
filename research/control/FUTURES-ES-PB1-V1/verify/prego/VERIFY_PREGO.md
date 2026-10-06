# VERIFY_PREGO — FUTURES-ES-PB1-V1, pre-GO follow-up wave (final fresh-context independent verifier)

- Verifier: fresh-context independent verifier (sub-wave check). Audit only; repaired nothing.
- Generated: 2026-10-04. Zero network. Zero PnL/quarantine-numeric reads (quarantine numerics
  never used as verification targets; the only quarantine content read was STRUCTURAL:
  field-path locations of regex matches + the already-public shas/counts in the handoff).
- Write boundary honored: this file + `verify_prego.json` in this directory ONLY.
  No handoff JSON written — this is a sub-wave check, not a delegated lane.

## Measured state (mandatory start check)

| repo | path | HEAD (one bare rev-parse each) | expected | match |
|---|---|---|---|---|
| worktree | `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep` | `d44de21b6464d3f1b427ce69fc3298f823531d0f` | `d44de21b…` | YES |
| root | `/Users/hoangminhlong/my-quantitative` | `64e71c44dfa2c1f674da557b215594be41876a9e` | `64e71c44…` | YES |

`git status --porcelain` at start: BOTH EMPTY. Proceeded.

---

## Z1 — Wave diff discipline: PASS

- `git diff --stat 8324a8c0 d44de21b` (worktree): exactly 9 files, ALL under
  `research/control/FUTURES-ES-PB1-V1/{pins,holiday,dispatch}/**`:
  pins (PIN_DECISION_PACKET.md 262, pin_decisions.json 154),
  holiday (HOLIDAY_CLOSURE.md 172, exposure_proof.py 558, exposure_proof_2011_2016.json 2210,
  extract_equity_pdf_evidence.py 276, pdf_equity_evidence_2011_2015.json 3908),
  dispatch (handoff_HOLIDAY-CLOSURE.json 128, handoff_PIN-ADJUDICATION.json 60).
  7728 insertions, 0 deletions, nothing else.
- Root `git show --stat 64e71c44`: exactly 3 control-plane files —
  `plans/ACTIVE_CYCLES.json`, `plans/CYCLE_REGISTRY.events.jsonl`, `plans/CYCLE_REGISTRY.json`.
- Registry row diff (commit diff hunk inspection): header shared metadata only
  (`updated_at_utc`, `writer`, `write_token`) + the FUTURES-ES-PB1-V1 row
  (`head` e7fc1d8d→d44de21b, row `updated_at_utc`). NO hunk touches any other row —
  NBA/NFL rows byte-identical. `CYCLE_REGISTRY.events.jsonl` diff = exactly 2 appended
  lines (REGISTRY_SAVED + CYCLE_UPDATED head e7fc1d8d→d44de21b for this cycle only).
  `ACTIVE_CYCLES.json` projection diff = same head + timestamps only.

## Z2 — PIN-ADJUDICATION claims (from bytes): PASS

- (a) `pins/pin_decisions.json`: exactly 3 pins (D-A1 q80 method, D-A2 C2 direction,
  D-A3 C1 RNG algorithm); ALL THREE `classification: OWNER_RATIFICATION_REQUIRED`;
  zero ALREADY_FROZEN; `critical_findings: []`, `critical_deviation: false` ×3, CRITICAL count 0.
- (b) Citation spot-checks against `research/control/FUTURES-ES-V1-PACKET/…` bytes —
  SPEC_PB1_ES.md sha256 = `445f74990648…` (matches the pin's anchor exactly):
  - §3 L73-74 contains verbatim "điều kiện |m| ≥ q80(|m|, trailing-252d, strict-past) —
    q80 từ anatomy …, không tune" with NO method name: grep for
    `interpolat|linear|nearest.rank|percentile|midpoint` over the whole SPEC = ZERO hits.
  - §6 L127 carries "C1 placebo | `FBES1-PLA-D0-S2` (seed 20261002; đơn seed đơn delay …)".
  - §8 (L145 "## 8. Stage-A gates") G7 (L149-150): "G7 arm vượt C2 và C1 về after-cost
    expectancy tại S2 (không vượt ⇒ "no conditioning information")" — exists; grep for
    long/short direction words over the whole SPEC = ZERO hits (role only, no direction).
- (c) Recorded defaults labeled "not yet law" in all three `owner_decision_text`s
  ("the default currently recorded in rehearsal machinery - not yet law" ×3);
  pre-selects NOTHING: `authority_claims.no_option_chosen_by_this_lane: true`,
  `append_only_closure_draft: null` ×3, no option carries a selected/pointer field;
  packet §1.3/§2.4/§3.4 each headed "no pre-selection".
- (d) Enumeration-invariance statement present:
  `consistency_statement.identity_enumeration_invariant: true` with the full 24-cell
  invariance argument (JSON) mirrored at packet §4. The one design-disturbing option
  (C2 side-of-signal ≡ C4) is excluded as inadmissible.

## Z3 — HOLIDAY-CLOSURE claims (from bytes; load-bearing re-derivations): PASS

- (a) Re-run: `holiday/exposure_proof.py` copied to /tmp with ONLY the output path
  patched (repo untouched), executed with root .venv against the pinned inputs at this
  HEAD. Result: **output byte-identical to the committed
  `exposure_proof_2011_2016.json`** (rerun sha256 `8ffc0fa2799e…` == committed file ==
  the sha recorded in handoff_HOLIDAY-CLOSURE.json). Band census for 2011-2016
  re-derived from the pinned panel: **cov==0: 4; 0<cov<0.60: 40; 0.60≤cov<1.0: 0 (BAND
  EMPTY); cov==1.0: 1491** — exactly the claimed 4/40/0/1491; 27/28 checks PASS, single
  FAIL is the non-fatal exposure discovery; verdict field `NOT_RUN_BLOCKER`.
- (b) The one exposure row 2015-07-02, all four legs independently verified:
  1. `…/FUTURES-OVERNIGHT-PREP-20261003/cme_cal_gap/fx_comm/captures/2015-4th-of-july-holiday-schedule.pdf`
     exists; sha256 = `2c8831c207c60a421d3d1ae283632b77959198de83a07d16db4b4bc713abbaeb` (matches).
  2. Independent pypdf text extraction of the "CME Group Equity Products" section:
     verbatim lines `'Thursday, July 2'` + `'1215 CT / 1315 ET / 1715 UTC –Early close'`
     (en-dash spacing is a pypdf artifact; matches the cited "1215 CT … Early close").
  3. Panel recount (fresh parquet read, held symbol ESU5, 2015-07-02): **390 RTH-core
     bars** (08:30≤t<15:00 CT); from 12:00 CT: **619 bars, volume sum 476,608**, last bar
     `2015-07-02 23:59:00-05:00` — real trading, not synthetic.
  4. `freezegen/exclude_list.json` (1297 exclusions): **2015-07-02 ABSENT** (July-2015
     rows are only 2015-07-03 and 2015-07-29) — the conflict is real, not already handled.
- (c) PDF evidence tallies from `pdf_equity_evidence_2011_2015.json`:
  inventory `n_files = 53` and `files` list n=53, and the inventory filename set is
  EXACTLY the on-disk PDF set in the captures dir (53 .pdf on disk); candidates
  `candidate_dates_closed_halt_early` n=56 with classification counts CLOSED 12 /
  HALT 27 / EARLY_CLOSE 17 (=56); `regular_adjudicated_dates` n=106;
  `n_equity_sections_found=48`; lemma2 flag True with 0 violations; 5 documented
  anomalies as claimed. 3-PDF sha spot-checks ALL MATCH:
  `2015-labor-day-holiday-schedule.pdf` = `56d4554c99031fb8…`,
  `2011-martin-luther-king.pdf` = `2e389e2688d67607…`,
  `2014-thanksgiving-holiday-schedule.pdf` = `436214e8c3f9a4c3…`.
- (d) Verdict text NOT softened: HOLIDAY_CLOSURE.md "## VERDICT: NOT_RUN — the
  obligation is a REAL, NAMED blocker. NOT closed."; proof JSON `verdict:
  NOT_RUN_BLOCKER` naming 2015-07-02; handoff `readiness_conclusion` "VERDICT: NOT_RUN
  (blocker) … NOT closed" with the 3-step resolution path (builder round preferred /
  fetch round / owner ruling). Gate 6 implication carried.

## Z4 — Registry + doctor: PASS

- ROOT registry row FUTURES-ES-PB1-V1: `head = d44de21b6464d3f1b427ce69fc3298f823531d0f`
  ✓; `go_phrase = "GO FUTURES-ES-PB1-V1 SCORED EXECUTION"` exact and unchanged (no
  go_phrase hunk in the reconcile diff); `lifecycle = ACTIVE_LIGHT` ✓;
  `budget = {used: 0, max: 24}` ✓; `go_phrase_state = REGISTERED_NOT_CONSUMED` ✓;
  s1 SEALED_UNTOUCHED ✓.
- `cycle doctor --json` (root .venv, read-only, from ROOT): 69 total findings —
  **ZERO findings for FUTURES-ES-PB1-V1** (all findings belong to other cycles,
  mostly TERMINAL worktree-cleanup noise). The reconcile commit's claim "closes doctor
  HEAD_MISMATCH LOW" is consistent.

## Z5 — Stale/GO-law sweep: PASS

- Stale values `1.386|21.006|33.506|46.006`: **use-as-value = 0**. Non-quarantine hits
  (12 lines) are exclusively: builder ban-list guard (`for banned in (…)`, dryrun_builder.py
  L154), retirement-law comment (L30) and cost doc string (L541 "…retired"),
  selection_freeze `forbidden_values_law` field, and A7/dryrun handoff/report texts
  asserting absence. Quarantine hits (48 files × 1) were checked STRUCTURALLY (field
  paths only, no numeric values read): every hit is inside the
  `mechanics_citations.cost` STRING field — zero numeric occurrences anywhere.
- Exact GO string `GO FUTURES-ES-PB1-V1 SCORED EXECUTION`: appears ONLY in
  registered-plan/law/registry contexts — ROOT `plans/PLAN_futures_es_pb1_v1.md` §5,
  ROOT `plans/CYCLE_REGISTRY.json`, worktree REPORT_VI.md (cited as go_phrase,
  REGISTERED_NOT_CONSUMED), DRYRUN_REPORT/handoff_DRYRUN ("NO GO exists or is implied"),
  handoff_PIN-ADJUDICATION ("types no GO"), A7_PRELAUNCH + a7_prelaunch_digest
  (go_phrase law table), handoff_A7 (owner-only). Every occurrence is a
  REGISTERED_NOT_CONSUMED / owner-only restatement.
- "GO typed"/GO_GRANTED: zero hits in the cycle tree + plan; registry events history
  for this cycle = CYCLE_REGISTERED ("registration only - no GO delegated") +
  REGISTRY_SAVED + CYCLE_UPDATED(head) only — no GO/consumption event ever.
- Scored-run claims: zero positive scored-run claims found (targeted sweep exit 1);
  REPORT_VI gate table lists Gate 5 NOT_RUN (owner-owned) and Gate 6 NOT_RUN;
  dry-run artifacts self-describe as "QUARANTINED DESCRIPTIVE-ONLY — NOT SCORED —
  ZERO DENOMINATOR CONSUMPTION".
- Quarantine untouched since gate 4: `quarantine/trades_index.json` sha
  `b063ab0c7fc1…` and `quarantine/summary.json` sha `658efe587968…`, DRYRUN_REPORT
  `97a4ff6a…`, dryrun_digest `96aa2d84…`, dryrun_builder `867946f3…` — ALL equal the
  handoff_DRYRUN recorded outputs; `quarantine/` vs `quarantine_rerun/` diff -r =
  byte-identical (26 files each); worktree git status clean ⇒ everything is the
  committed state at d44de21b.

## Z6 — Verdict

| check | verdict |
|---|---|
| Z1 wave diff discipline | PASS |
| Z2 PIN-ADJUDICATION claims | PASS |
| Z3 HOLIDAY-CLOSURE claims (incl. byte-identical proof re-run) | PASS |
| Z4 registry row + doctor | PASS |
| Z5 stale/GO-law sweep | PASS |

**OVERALL: PREGO_STATE_VERIFIED** — the wave is committed at exactly the audited SHAs,
every byte-level claim of both follow-up lanes reproduces, the registry/control plane is
consistent, and no GO/scored-consumption exists. The two OPEN items are correctly OPEN
by design and are owner decisions, NOT defects:
1. Holiday blocker: 2015-07-02 evidence-vs-data conflict (HOLIDAY-CLOSURE verdict
   NOT_RUN, resolution path recorded — owner-authorized builder round or fetch round).
2. Three pin ratifications (D-A1/D-A2/D-A3) await the typed owner gate; the packet
   pre-selects nothing.

## Discipline record (git + other commands, all read-only except the two artifact writes)

- `git -C <worktree> rev-parse HEAD` (once) → d44de21b… ; `git -C <root> rev-parse HEAD`
  (once) → 64e71c44…
- `git status --porcelain` both repos at start (both empty) and again at end (worktree:
  only `research/control/FUTURES-ES-PB1-V1/verify/prego/**` new-untracked; root: empty).
- `git -C <worktree> diff --stat 8324a8c0 d44de21b`;
  `git -C <root> show --stat 64e71c44`; `git -C <root> show 64e71c44 -- plans/CYCLE_REGISTRY.json`;
  `git -C <root> show 64e71c44 -- plans/ACTIVE_CYCLES.json plans/CYCLE_REGISTRY.events.jsonl`.
- Non-git: shasum/grep/diff/ls/find; root .venv python for JSON parsing, pypdf PDF text
  extraction, parquet recount (panel columns raw_symbol/ts_event/volume only — bar and
  volume counts, no PnL), the /tmp-copy proof re-run, and the structural quarantine
  field-path scan. `cycle doctor --json` run read-only per Z4. Zero network.

— End VERIFY_PREGO.
