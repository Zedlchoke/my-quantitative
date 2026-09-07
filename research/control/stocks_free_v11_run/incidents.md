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
