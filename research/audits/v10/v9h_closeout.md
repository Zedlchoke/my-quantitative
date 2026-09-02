# V9H CLOSEOUT — 2026-08-27

## Verdict

**`V9H_PASS_V10_AUTHORIZED`** — carrying A7-R's independent recommendation
`V9H_PASS_V10_AUTHORIZED_EVIDENCE` verbatim (14/14 checks PASS, 0 unresolved
HIGH/CRITICAL), audited at `5c8a979`.

## What closed tonight

| Evidence | Result |
|---|---|
| Full suite, alone, clean integration | **1078 passed / 1 skipped / exit 0** (68.5 s) |
| R-A3 runtime validation | ALL_GATES_PASS — 10/10 timeout rounds zero orphan, heartbeat/log live samples, 3/3 two-worker probes safe |
| R-A4 reproduction validation | 6/6 gates measured — cache byte-parity, fresh-process `all_match`, raw-bars = 2 loads (control 4 proves counter non-vacuous), golden ×2 roots == committed baseline |
| R-A5 contract/data validation | denominator=117 via three independent recounts; funding sign pinned; returns matrix deterministic; PIT invariants demonstrated with violating cases |
| Independent A7 audit | re-hashed 207 archive blobs, re-ran golden as third agent, settled G-H08/G-H06 fail-closed rows as **non-blocking** (not PLAN.md-required gates) |
| Resource cap | stored==recomputed via production `_recompute_governor`; **owner directive sets effective_heavy_workers = 1** (`e746f9a`) → future waves run `min(2,1)=1` |

## Honest open items (documented, none blocking)

- **F1**: adversarial map declares 20, only 11 enumerable anywhere. Cases 12–20
  must be enumerated by the project owner as contract text.
- **F2**: strict G-H06 needs a same-workload cached-vs-uncached wall-time pair;
  next validation pass must record it.
- **F3/env**: primary vs secondary RAM metrics disagree materially on this
  8 GB host (enforced metric reads ~1.3 GB < 2 GB reserve); directive already
  supersedes the resulting 0-cap for sprint purposes.

## Worktree consolidation (owner-authorized this session)

68 worktrees removed, all without force; every unique stray preserved first on
branch `orca/preserve-v9-exec-strays@a1fb57d`; ~4.0 GB freed; branches and all
history intact. Surviving git objects now hold sole-copy status for archived
sprint working content — A7's hash verification is the load-bearing anchor.

## Before any V10 wave

1. Owner decisions on F1/F2 above.
2. Freeze the separate ≤12 h V10 contract from an authorized SHA (this chain,
   closeout commit or later).
3. Fresh proposal worktrees ONLY from that SHA — stale `acbc79b` bootstraps of
   a8/a9 remain forbidden for proposals.
4. Prelaunch G01–G20; scored waves then execute with heavy workers capped at 1.

## Note on root sync

Root `main` carries owner-edited `PLAN.md`/`CONTINUE.md` uncommitted; merging
`orca/v10-integration` into main is deferred to its own owner-visible step
because control manifests diverged on both sides and conflicted files require
manual inspection under PLAN §4.2. Nothing is lost by waiting: every branch is
local and intact.
