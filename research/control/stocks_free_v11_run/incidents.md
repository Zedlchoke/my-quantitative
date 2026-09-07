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
