# PAUSE PACKET — CRYPTO-V17 (SYSTEM-HARDENING-V1 H0)

Machine-readable twin: `PAUSE_CRYPTO_V17.json`. Protocol form: SHV1 plan §4
(items 1–7 + `hard_stop_reason` clause). Packet UTC 2026-09-08T10:57:20Z.

## Identity

- Worktree: `.worktrees/crypto/v17/integration` — left on disk, resources released.
- Branch: `orca/v17-integration`.
- HEAD pre-pause `2b176e3e` → pause commit `41de5c9e` → HEAD post-pause `41de5c9e`.
- Tree post-pause: CLEAN (`git status --porcelain=v1` empty, measured).
- Status retained: `ACTIVE_LIGHT` / phase `P0_ACTIVE` (legacy record unchanged —
  no new status invented, §4). **`hard_stop_reason: SYSTEM_HARDENING_V1`** added
  additively; pause event appended to the cycle event log (append-only).

## Safety state (all measured, not asserted)

- Budget **0/6**; S1 **SEALED_UNTOUCHED**; workers 0; machine heavy lock **FREE**
  (last release STOCKS-FREE-V12/D2 FINISHED 07:50:35Z); zero live repo workers on
  `ps` sweep.
- GO phrase `GO CRYPTO V17 SCORED EXECUTION` registered-**not-consumed**; per
  SHV1 §10 no GO carries across the maintenance pause.
- No scored-cell publication in the transition (no cell ever computed).

## Frozen scientific artifacts — hashes re-measured at pause (5/5 MATCH)

| Artifact | sha256 (first 12) |
|---|---|
| `p0_freeze_v17.json` (contract freeze v5) | `1ca4fa3d4534` |
| extractor self-pin `extract_v17_panel.py` | `9ea77d21e1ad` |
| reconcile self-pin `reconcile_v17_daily.py` | `26737e563bf3` |
| V16 daily panel BTC (freeze v5 anchor) | `5bb5016da6e6` |
| V16 daily panel ETH (freeze v5 anchor) | `c54147674dea` |

Hash drift: **NONE**.

## Drift recorded, not normalized (§2)

`state_v17.json.head` is stale (`09ccfcc`, bootstrap-era) vs actual integration
HEAD `2b176e3e` at pause. Repair belongs to the SHV1 registry (H2), not the
paused record.

## Next safe action (held for resume)

Full 39-symbol-month build attempt 3 (freeze v5, stall-hardened) under the
machine-wide heavy lock — only after SHV1 G0–G8 pass, hash/budget/S1 re-verify,
cheap gates rerun, and a **fresh** owner GO at the cycle's own prelaunch (P-8).

Pause executed by the SHV1 controller under owner dispatch; no cycle A1 thread
was live (owner pause already in effect per router 2026-09-08). Zero scientific
artifact touched.
