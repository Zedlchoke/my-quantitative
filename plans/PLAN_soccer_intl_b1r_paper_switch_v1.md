# PLAN — SOCCER-INTL-B1R-PAPER-SWITCH-V1 (successor, owner instruction 2026-10-10)

Mission: switch the men's-soccer PAPER decision model from **B1** to
**B1R** (frozen train-only draw recalibration) for FUTURE qualified
matches, through the control plane only. This plan is prepared and
executed UP TO a registered GO; the owner's instruction message is
explicitly NOT a GO phrase. No GO is consumed by any lane.

## Object of the switch (all pins frozen here, verifiable)

- **Map of record**: `SOCCER-INTL-90MIN-PREP-V1/lanes/L_DRAWHYP/
  DRAW_CAL_MAP_FROZEN.json` in worktree
  `.worktrees/soccer-intl-90min-prep-v1/integration` (branch head at
  freeze: `683de135…`), file sha256
  `b72a115193d4c51e7da4ee65ac837082288554a879182a24e81fc8b0f48e64a7`,
  inner `map_sha256`
  `1f4a4c4f26639b31dcb9c79035e8cfe3fb57deb693c5def729e402bba953befd`,
  PAV isotonic 18 pools, fit [1971-01-01, 1991-01-01) n=9,289, zero
  post-2001 contact (verifier V2 PASS).
- **B1R law (frozen, no refit ever)**: given the immutable B1 forecast
  (p_H, p_D, p_A) from the frozen engine arm (K=48, ν=0.6, HCA=65,
  day-batch PIT law I1–I5), set p_D' = g(p_D) by the map (constant
  extrapolation at edges); p_H' = p_H·(1−p_D′)/(1−p_D);
  p_A' = p_A·(1−p_D′)/(1−p_D). Nothing else changes.
- **Status honesty (binding)**: B1R's only measured improvement is
  TRAIN_INTERNAL_DIAGNOSTIC (holdout [1991,2001): ΔLL −0.00588,
  ΔRPS −0.00032 — below the 0.01 margin). It is NOT edge, NOT a
  profit conclusion. The pre-registered prospective test
  (`DRAW_CAL_HYPOTHESIS.md`, n=1,000 decision) remains the arbiter;
  this paper switch is NOT that test's verdict.

## Ledger boundary (frozen BEFORE the first B1R row)

Live ledger `~/.my-quantitative-data/sports-papertrade-exec-v1/ledger/
paper_ledger.jsonl` measured 17 rows, hash-chained
(prev_row_sha256 → row_sha256). Frozen facts: **0 soccer DECISION rows
exist**; soccer has 1 FORECAST row (England–Croatia 2026-11-12,
model_version_sha `soccer_b1_replay`, row_sha256 `efea6160…`) + 1
NO_QUOTE row. Boundary law:
- All 17 rows immutable; no relabel/recompute of anything pre-switch
  (and nothing post-switch may rewrite any row; ledger append-only).
- The existing B1 FORECAST row for 2026-11-12 is retained verbatim as
  the CONTROL forecast for its fixture; a B1R FORECAST row may be
  APPENDED for the same fixture (never replacing), referencing the B1
  row via `control_ref_row_sha256`.
- First soccer DECISION row after the switch must carry
  `model_id: "B1R_SOCCER"` + `map_sha256` (the inner sha) and
  `decided_at_utc > switch_ts`, where `switch_ts` = the registry CAS
  event timestamp of THIS cycle's GO consumption. Any soccer DECISION
  row without those fields after switch_ts = violation (battery T2/T3).

## Qualification law (frozen; unchanged economics)

Shared wallet $1,000 / stake $5 (500c) / open cap $100 / EV gate / DD
pause / quota / PIT / bookmaker / settlement laws of
SPORTS-PAPERTRADE-V1 + EXEC-V1: **unchanged**. Only these match-gates
apply to B1R decisions:
1. Target and odds must be the SAME 90-minute 1X2 definition (3-way incl.
   DRAW). Missing or ambiguous evidence ⇒ NOT_RUN (no decision).
2. **Knockout stays BLOCKED/NOT_RUN** for paper until target AND odds
   settlement are both proven 90-minute (inherited from the freeze
   packet; unchanged here).
3. Competition set frozen = exactly the current paper soccer league key
   `soccer_uefa_nations_league`. NO new competitions in this change.
4. A match already decided is never re-decided (duplicate law T3).
5. This API/results landscape provides LABELS, never pre-match odds;
   odds keep their own qualified sources + PIT snapshots.

## Deliverables in this cycle (pre-GO)

- `L_SWITCH`: adapter + battery code, `FREEZE_BOUNDARY.json` (map pins,
  ledger boundary row_shas, law constants), byte-level repro of the
  B1R transform on the recorded England–Croatia B1 forecast.
- Fail-closed battery (SANDBOX ledger only; live ledger read-only):
  T1 map pin drift ⇒ REFUSE; T2 PIT/anchor ordering violations ⇒ REFUSE;
  T3 duplicate (match_id, model_id) ⇒ REFUSE; T4 B1/B1R must read the
  same odds snapshot (identical quote payload sha) ⇒ REFUSE on mismatch;
  T5 live-ledger chain integrity check; T6 byte-repro equality.
- `GO_PACKET_B1R_SWITCH.md`: what the GO activates (register B1R as the
  soccer decision model in the forecast/decision pipeline; append B1R
  FORECAST + keep B1 control; post-GO steps: dashboard fields B1/B1R/
  Δp_draw/deciding-model, cadence unchanged, audit first rows), and the
  explicit STOP.
- Independent A7 verifier on pins, battery, boundary, no-live-writes.

## GO and post-GO (NOT executed by this plan)

GO phrase (registered REGISTERED_NOT_CONSUMED):
**`GO SOCCER INTL B1R PAPER SWITCH V1`** — consuming it authorizes the
switch live (B1R becomes the soccer decision model from switch_ts).
Post-GO steps (own cycle rounds, still paper-only): wire the dashboard
fields; append the first B1R FORECAST row for the first qualified
fixture with B1 control on the same snapshot; audit the first rows;
report with RETROSPECTIVE labels on nothing (all prospective), no edge
claims. No real money, no push/merge, ever.

## Terminal outcomes

`B1R_SWITCH_READY_PENDING_GO` (expected at this round's end) |
`BLOCKED_*` | `NOT_RUN_*`. Negative-first: if any battery fails or a
pin drifts, no GO packet is presented.
