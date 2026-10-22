# ERRATUM_EXEC_7 — B1R FAIL-CLOSED (owner round-11 instruction, 2026-10-10)

Closes the binding condition of ERRATUM_2 E-1 (disposition 2,
SOCCER-INTL-WC-EURO-PAPER-PREP-V1) and lands the switch GO-packet's
post-GO step 1. **This erratum consumes no GO.** Authority chain:
owner instruction 2026-10-10 (this chat) →
SOCCER-INTL-B1R-PAPER-SWITCH-V1 plan + FREEZE_BOUNDARY.json + GO_PACKET →
ERRATUM_2 E-1 → the exec cycle's own standing GO_CONSUMED law.

## Law (now enforced in the production runner)

After `switch_ts = 2026-10-10T02:20:20Z` (registry CAS instant of
`GO SOCCER INTL B1R PAPER SWITCH V1`, pinned + re-verified against the
registry on every soccer command), a SOCCER DECISION is lawful ONLY when
its forecast is a `B1R_SOCCER` FORECAST row that:

1. carries `map_sha256` equal to the frozen inner map sha
   `1f4a4c4f…953befd` and `model_version_sha = soccer_b1r_v1`;
2. resolves `control_ref_row_sha256` to the parallel B1 control row of the
   SAME fixture (`soccer_b1_replay` / `B1_SOCCER`);
3. stores `p_control_b1` byte-equal to that control row's `p` AND is the
   byte-exact frozen-map transform of it (switch battery T4+T6 re-derived
   at decision time through the byte-pinned `b1r_adapter.py`);
4. was recorded STRICTLY before its own anchor.

Anything else — above all a B1-only match — journals a terminal
**`NOT_RUN_NO_B1R_FORECAST`** DECISION row (stake 0, specific reason,
dashboard-visible). A B1 forecast is CONTROL-ONLY after switch_ts and can
never silently ground a decision. Lawful BET_PAPER/NO_EDGE soccer rows now
additionally cite `decision_forecast_row_sha256` + `map_sha256` +
`control_ref_row_sha256`.

## Emission (GO-packet step 1, the piece 073d9e45 never landed)

`cmd_forecast` (SOCCER, post-write) appends the B1R twin next to every B1
row of the batch through `b1r_adapter.build_forecast_rows` (byte-pinned via
`pins.json → packages.b1r_switch`), idempotent (any existing B1R row skips),
anchor-gated (never a late backfill; the command-level anchor refusal still
fires first). The England–Croatia twin (row `dadbec71`, appended post-GO)
makes the live match idempotent-stable.

## Hard blocks (fail-loud, not per-match NOT_RUN)

- MAP FILE drift → `BLOCKED_B1R_MAP_PIN` (T1; pin exit 7).
- Registry no longer records the pinned switch_ts →
  `BLOCKED_B1R_SWITCH_TS_UNVERIFIED` (soccer commands only; NBA/WNBA
  unaffected). **This fired during development**: the exec worktree's
  registry mirror was stale (B1R row ABSENT, mirror last refreshed
  2026-10-07); the mirror is hereby refreshed to the root registry bytes.
  Re-pin procedure for future drift: refresh the mirror from
  `plans/CYCLE_REGISTRY.json` (root is authority), evidence in-commit.

## Scope answers (owner instruction Part A)

- Paths covered: `cmd_forecast` (fresh + rerun), `cmd_decide` (fresh +
  rerun), `cmd_run_day` chain, service cadence `_run_chain` (forecast step
  now re-runs when a soccer match lacks a VALID B1R — decide then journals
  NOT_RUN_NO_B1R_FORECAST), service restart (stateless re-derivation),
  already-decided matches (terminal, never re-decided). The four WC/Euro
  keys are NOT armed; the guard is key-agnostic, so when the WC/EURO
  cycle's own GO arms them the same law applies with zero further code.
- Dashboard: NOT_RUN_NO_B1R_FORECAST rows flow into the pinned dashboard's
  status census and `soccer_by_competition.json` (NOT_RUN bucket) like
  every DECISION family. Display-only gap, consistent with the existing
  NOT_RUN_STAGE_LAW precedent: the pinned core's NOT_RUN_CAUSE strip has no
  bucket for statuses newer than its seal (status census unaffected). A
  core re-seal for a display label alone was deliberately NOT taken.
- Gates (Part A.4): writing NOT_RUN-family rows needs NO new GO — the
  family is journaled under the standing GO_CONSUMED law since genesis
  (NO_QUOTE / QUOTA_SKIP / CROSSWALK_MISS / NOT_RUN_STAGE_LAW precedents);
  this row adds a reason, changes no economics. Arming the four WC/Euro
  keys stays behind `GO SOCCER INTL WC EURO PAPER PREP V1 INTEGRATE`
  (REGISTERED_NOT_CONSUMED; untouched) — `config.json` unchanged here.

## Evidence

`B1R_FAIL_CLOSED_REHEARSAL.json` (this dir): dedicated battery 16/16
(`tests/papertrade_exec/test_b1r_fail_closed.py`, real ledger sha asserted
unchanged around EVERY test), full-suite failure set byte-identical to
HEAD b6459892 (12 pre-existing sibling-entry-drift failures re-measured via
stash; 0 new failures), real-ledger byte-unchanged across all rehearsal CLI
runs, GO-state inventory. Two law-affected battery tests updated
deliberately with in-test comments.

## Known pre-existing failures (recorded, not normalized)

12 tests in `test_exec_battery.py` fail identically at HEAD b6459892 and
after this change: sibling engine entries (`wnba26/predict.py`,
`soccer/replay.py`, `nba26` package) are absent/advanced in their pinned
worktrees (real-mode compute paths only; sandbox + decide/quote laws
unaffected). Environment drift outside this round's scope.

## STOP

No GO typed or consumed by this round. `GO SPORTS PAPERTRADE EXEC V1
POLYMARKET CUTOVER` and the WC/EURO INTEGRATE phrase remain
REGISTERED_NOT_CONSUMED. No push, no merge, no production price-source
change.
