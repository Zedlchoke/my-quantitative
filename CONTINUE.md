# CONTINUE.md — V10 PRELAUNCH REMEDIATION

Read `PLAN.md` completely. It is the fresh-context authority.

## Measured state

- Integration workspace:
  `/Users/hoangminhlong/my-quantitative-v10-wt/integration-v10`
- Integration HEAD: `orca/v10-integration@832fa6f`, clean when measured.
- V9H PASS; M01 selected and implemented.
- Prelaunch: `NO_GO_SCORED_WAVES`.
- V10 budget consumed: 0/3 planned cells.
- Old W=`79fc883` and old R1/R2 are stale; preserve, never score from them.
- Deadline: `2026-08-27T16:55:00Z`, no auto-extension.

## Immediate critical path

1. Freeze a family-neutral adapter interface.
2. Create three worktrees from current clean integration.
3. Dispatch concurrently:
   - G1: BG-1/BG-2/BG-4/BG-5/BG-6 generic runner/finalizer;
   - G2: BG-3/G15/F2/G17 funding/cache/resource;
   - G3: acceptance/fault tests and H08 cases 12–20.
4. Integrate sequentially; targeted tests after each; full suite alone.
5. Freeze W2; create fresh detached R1b/R2b and stage/hash data.
6. Run fresh independent A7 G01–G20 audit.
7. Only `V10_LAUNCH_AUTHORIZED` permits the 3 serial scored cells.
8. Reproduce 3/3, score and close honestly.

## Boundaries

- A1 + at most 3 light agents; heavy maximum 1 and may fall to 0.
- No new hypothesis, M01 tuning, PnL inspection, push, deletion, S1, equity,
  paper/testnet/live or orders.
- If deadline expired, close incomplete; never extend automatically.
- If <120 minutes, start no new scored cell.

## First fresh-thread report

Return current UTC, HEAD/status, time left, budget=0 confirmation, exact three
worktrees/allowlists and remaining blockers; then continue without repeated GO.
