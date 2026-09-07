# INCIDENT LOG — STOCKS-FREE-V11

Append-only. Every incident recorded even when harmless (owner instruction
at dispatch: "Ghi incident kể cả khi vô hại").

## INC-V11-0 — harmless A1 tooling missteps during first-report measurement

- measured_at_utc: 2026-09-07T01:13:18Z (first-report window)
- severity: NONE (harmless; owner-instructed to record regardless)
- what: (1) A1 attempted to read a V10 staging file through a wrong relative
  path (`stocks-free-v9/integration/../stocks-free-v10/...`) — the read
  failed loudly, no data touched; (2) A1's heredoc briefly resolved to the
  system interpreter `/opt/homebrew/.../python3.12` before the
  `.venv/bin/python`-only invariant caught it — the fallback branch printed
  only "fallback" and no command executed outside the sanctioned interpreter.
- impact on artifacts: none. All first-report numbers were produced under
  `.venv/bin/python 3.12.14` and raw `shasum -a 256`.
- action: none beyond this record.

## Inherited context (not an incident of this cycle)

- V10 A7 terminal F-2 (OPEN_VERDICT_NEUTRAL): declared UTC timestamps inside
  V10 artifacts drift ahead of the git/machine clock. V11 artifacts must keep
  declaring UTC explicitly and A7 prelaunch will re-check drift discipline.
- V10 INC-V10-1 (scored run from working-tree bytes committed immediately
  after; adjudicated outcome-neutral): standing lesson — V11 commits every
  scored driver BEFORE its run so the ledger's code_freeze_sha is the exact
  run-time HEAD.

## INC-V11-1 — P0 lane census-script defect aborted two runs pre-artifact (harmless)

- measured_at_utc: 2026-09-07T01:58:30Z (lane handoff disclosure)
- severity: NONE (harmless; recorded per the record-even-harmless rule)
- what: the lane's census script had an undefined variable (`rev_iad_pool`)
  aborting its first two runs BEFORE any artifact existed; lane fixed and
  proved determinism with two independent complete runs producing
  byte-identical derived artifact sha256 728f1420…0fd9 (74,931 rows).
- impact on artifacts: none (no partial artifact ever published; A1
  re-hashed the artifact independently and it matches the manifest pin).
- secondary note: the lane initially looked for `~/.venv/bin/python` before
  using the correct repo-root `.venv/bin/python 3.12.14` (work-order
  shorthand ambiguity); correct interpreter used for all published numbers.

## Anomaly log (non-incident observations from P0, recorded for D1 lanes)

- CIK0000004904 (ALIVE_EVIDENCED, 69 events) has no EOD price file — 0.09%
  join miss; events reported, price-side null, never guessed.
- GAP_COVERAGE contributes zero events/chains (class construction: 0/513
  members in the timing layer) — zero is real.
- 19 entities have zero clear 20-bar placebo windows (event-saturated
  calendars near death) — sham-placebo design must tolerate; not blocking.
- 1,482 DEAD entities' price series end within 120d of last event vs 270
  end later — death-vs-stale ambiguity reported, not adjudicated (P1/P3
  freeze decides semantics; any semantics change recomputes controls per P-3).

## ANOM-2026-09-07-D1 — harmless coordination notes from the parallel D1 lanes

- measured_at_utc: 2026-09-07T03:45:00Z
- (a) README interleaving: the three lanes ran in parallel and interleaved
  commits on the shared proposals/README.md; each appended its own section
  byte-preservingly (A1 verified 0 deletion lines in both inter-lane diffs).
  Proposal JSON files were never read across lanes (each lane attests; files
  appeared mid-task for A5 and remained untracked-unread). Mechanisms were
  developed independently; no cross-lane mechanism contamination identified.
  A7 prelaunch may re-weigh.
- (b) A6 disclosed reading V10's closed a6_open_H1.json "for schema format
  only" (a closed historical authority already in its packet context; the
  V10 A4-H2/A6-H2 never-scored texts were not read). Outcome-blind
  discipline intact; disclosure recorded per fail-closed habit. D2 still
  measures novelty by exposure rho, not by intent.
- (c) A5's self-check initially resolved a non-existent interpreter path
  before using the repo venv (same shorthand class as INC-V11-0); published
  artifacts unaffected.

## INC-V11-2 — D2 tooling lane died at usage limit; A1 completed its module (disclosed)

- measured_at_utc: 2026-09-07T05:10:00Z
- what: the D2 tooling subagent hit the session usage limit and died after
  writing research/assets/stocks/d2_v11_novelty_measure.py (2,057 lines,
  uncommitted, never self-checked). An earlier D2 measurement-lane dispatch
  had died the same way leaving nothing. A1 reviewed the file in full, fixed
  four defects before first successful selfcheck (fixture overwrite-instead-
  of-append for accounting fields; missing fixture rng; ctot[hi-1] negative
  index when hi==0 in veto_breadth/build_a5_h1; double-hexdigest crash in
  _sham_pick) and corrected two selfcheck expectation bugs (veto11 fixture
  has two down rows -> 0.5; the A4-H2 partition checks tested entry dates
  instead of the amendment/first-vintage partition). All fixes are in the
  module, disclosed here; selfcheck now ALL PASS (veto hand-values, six
  builders, hash pins, determinism, hash-mismatch BLOCK path).
- impact: none on published evidence — no audit JSON existed before these
  fixes; the measurement below runs on the fixed module.

## INC-V11-3 — D2 runtime crash on first heavy run (rev None-sort); fixed, determinism proven

- measured_at_utc: 2026-09-07T05:55:00Z
- what: the first full D2 run crashed at load_context (`rev[e].sort()` —
  tuple comparison hit rev_mag=None on ZERO_BASE rows when last_avail ties;
  the V10 invariant "ZERO_BASE rows keep direction with null magnitude"
  makes None legal data). A1 fixed with an explicit None-safe sort key.
  No partial audit was published (the crash happened before any output).
- determinism: the fixed module ran twice end-to-end; audit JSON
  byte-identical (sha256 1fba3975d5c5b6d2f1f60b73691f1682ee46da95ce49135f9fb40166104a4746).

## INC-V11-4 — undisclosed remote push of the cycle branch (A7 v1 REFUSED, 1 HIGH) — OPEN, owner-only resolution

- measured_at_utc: 2026-09-07T09:20:00Z (A7 v1 verdict); facts measured by A7 and re-measured by A1
- severity: HIGH (launch-blocking, unresolved)
- what: remote ref `origin/orca/stocks-free-v11-integration` EXISTS at 2d2ddaf
  ("V11 A1: D1 integrated..."), remote-tracking reflog "update by push" at
  2026-09-07 10:11:29 +0700 (= 03:11:29Z), inside the cycle window. A1 ran no
  push command; every dispatched lane was instructed "DO NOT push". The
  pusher cannot be identified from bytes (reflogs do not record identity).
  Push is an owner-only action (RULES §1; plan §4); an unverifiable
  authorization is fail-closed STOP.
- content: benign — the pushed tip is the D1-integration control state (no
  scored artifact, no key, no S1, staging gitignored); 6 local commits
  (selection freeze, D2 audit, A8 I/Q, integrations, A7 v1) remain unpushed.
  The two-key HARD STOP is untouched: no scored invocation exists, no
  V11_LAUNCH_AUTHORIZED anywhere, dry-run published_delta = 0.
- A7 v1: STOCKS_FREE_V11_PRELAUNCH_REFUSED, 11/12 items PASS from bytes
  (chain 121/121 re-hash, durable assets, P0 census recount, freezes, D1
  packet, D2 re-run byte-identity, selection honesty, dry-run re-run
  byte-identity + leak scan independent, live refusal truth-table, tests
  74/74, S1/denominators) with exactly ONE open HIGH = this push.
- remediation options (owner-only): (a) owner ratifies the push as their
  instruction -> A1 records the authorization here -> A7 v2 re-audit
  (cheap: item 10 only) -> two-key launch possible; (b) owner instructs
  deletion of the remote ref (owner-authorized push --delete) -> record ->
  A7 v2 -> two-key launch possible; (c) owner investigates upstream
  (GitHub audit log) and returns.
- state: cycle held at PRELAUNCH, verdict STOCKS_FREE_V11_BLOCKED_PRELAUNCH
  pending owner; nothing scored, nothing pushed by A1 or lanes.

## INC-V11-4 status update — owner directive recorded; A7 v2 to re-adjudicate (status: OPEN -> OWNER_DIRECTED_RE_ADJUDICATION)

- updated_at_utc: 2026-09-07T13:35:00Z
- new evidence since the refusal (ddf536f):
  (a) root main advanced d2b0f92 -> 26d0e30 with Lead handoff a77dce3
      ("ACTIVE stocks V11 (D1 done)" listed among program cycles; sibling
      cycles closed "on origin" — owner-side origin management of active
      cycles is stated practice; program 218/221 as-of-handoff);
  (b) at 13:2xZ the owner, fully informed of F-1 (the ratify/remove/
      investigate options were presented verbatim), directed the cycle to
      proceed: "GO STOCKS V11 SCORED EXECUTION kiem tra heavy lock".
- recorded interpretation (two-sided, fail-closed): this is an
  owner-directed CONTINUATION in full knowledge of the undisclosed push —
  it is NOT an explicit attribution of the 03:11:29Z push. The original
  pusher remains unattributed from bytes. A7 v2 re-adjudicates item 10
  with this record on the branch and decides independently whether the
  boundary is now satisfied or still blocks.
- the typed phrase is recorded as OWNER_INTENT (owner_go_intent.json),
  NOT consumed: the P-8 gate (fresh A7 AUTHORIZED verdict first) does not
  exist yet; a fresh owner typing AFTER that verdict is the consumable key.

## F-4 correction (A7 v2 finding, applied at next A1 touch)

- The INC-V11-4 records above state the push time as 03:11:29Z — that is
  2d2ddaf's COMMIT time, not the push time. The remote-tracking reflog
  entry is epoch 1788753872 = 2026-09-07T04:04:32Z (11:04:32 +0700),
  matching A7 v1's measurement. Both timestamps are inside the cycle
  window; nothing else changes. Corrected here per append-only discipline
  (prior entries stand as written, this note supersedes the timestamp).
