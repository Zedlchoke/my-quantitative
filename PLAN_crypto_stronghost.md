# CRYPTO V12 STRONG-HOST RUNBOOK

> Owner operations addendum dated 2026-09-04.
>
> This file does not amend the frozen strategy identities, data window, gates,
> costs, controls, budget or W12 code in `PLAN_crypto.md`. It tells a fresh A1
> how to move the already-authorized V12 execution to the stronger host and
> incorporates the completed Stocks V3 and Forex Free V1 lessons before the
> first Crypto V12 score.

## 0. Current authority and measured checkpoint

The authoritative Crypto integration branch is:

```text
branch                         orca/v12-integration
prelaunch integration SHA      de77b29000092557a0bc11b90d8b28d72d8be10d
prelaunch verdict              V12_S0_LAUNCH_AUTHORIZED
W12 execution/reproduction SHA f0799cae6fc47846937cf1a370719314696ee990
eligible families              OILEV-V2 and BAB-LOWBETA
frozen arms                    6 total, 3 per family
ILLIQ replication              BLOCKED_DATA; its 3 slots stay unused
budget                         0/9
logical denominators           125 published / 128 observed
S1                             SEALED_UNTOUCHED
scored V12 cells               0
owned workers                  0
staged market-data files       90 per execution tree
staged manifest SHA-256        f855ad9c778f7a8695d6416b1c912efd7ddc353bf70935669504016cbf3c3c40
```

Authority order:

1. frozen `PLAN_crypto.md` and V12 `run_contract.json`;
2. A7 prelaunch authorization and its four binding launch conditions;
3. `selection_freeze.json`, `w12_freeze.json` and the W12 Git tree;
4. this strong-host operational runbook;
5. lower-level state, heartbeat and prose.

If any identity, digest, window, counter, W12 SHA or staged-data hash differs,
stop fail-closed. This runbook never permits repairing a scientific mismatch.

## 1. What Stocks and Forex taught us

### 1.1 Raw profit is not an edge

Stocks V3 `SFV3-A6-TOM-SETTLE` made +38.52%, PF 1.620 and had 3/3 positive
folds, but its incremental alpha was -0.126 and the placebo control reproduced
the direction. It was correctly rejected as scaled sector beta.

For Crypto V12:

- report absolute PnL and BTC-factor/residual evidence separately;
- raw PnL never overrides a failed frozen control or concentration gate;
- BAB-LOWBETA must demonstrate information beyond broad BTC/crypto beta;
- OILEV-V2 must demonstrate information beyond generic market direction.

No new beta model or threshold may be invented after seeing a score. Use only
the diagnostics frozen at W12; otherwise mark the unavailable claim honestly.

### 1.2 A plausible mechanism may still be negative after costs

Forex Free V1 scored six cells exactly. All six had negative after-cost
expectancy, including both anchors, despite directionally coherent controls.
The correct terminal result was `FOREX_FREE_V1_REJECT_ALL`, not a fee reduction
or parameter rescue.

For Crypto V12:

- native funding and frozen execution costs are mandatory;
- publish trade count, turnover, break-even cost and after-cost expectancy;
- a negative anchor is a reject, even when its control is worse;
- do not reduce fees, remove funding, select winning symbols or change clocks;
- very high trade count is treated as cost sensitivity, not extra confidence.

### 1.3 Sidecars and bookkeeping can corrupt a correct strategy result

Stocks V2/V3 exposed three operational hazards: CASH counted twice, costs
counted twice, and a turnover convention doubled by a reporting layer. Stocks
V3 also initially hashed a publication wrapper instead of the exact artifact
bytes. These defects did not justify changing frozen science; they required
independent reconciliation and append-only correction.

Therefore, before Crypto scoring, A1 and A7 must prove:

- cash is not a tradable symbol and is not counted in concentration/turnover;
- costs and funding enter exactly once;
- turnover uses one named frozen convention end to end;
- every published digest hashes the exact canonical artifact bytes;
- execution and reproduction calculate the same fields independently;
- corrections, if any, are append-only and never overwrite scored artifacts.

### 1.4 Controls are decisive, not decoration

Forex controls were worse than their anchors but could not rescue negative
expectancy. Stocks TOM's placebo showed that positive raw PnL was not caused by
the proposed calendar mechanism.

For each V12 family, record three separate conclusions:

1. is the anchor profitable after costs?
2. does the neighbour support the same mechanism?
3. does the causal negative control falsify broad beta/drift explanations?

A family survives only if the frozen Stage-A rule accepts all applicable
answers. No narrative vote can overrule the machine gate.

## 2. Why the strong host is required

The 8 GB preparation host measured only 0.05 GB free RAM and
`measured_safe_cap=0`. It must not start scored execution in that state.

On the stronger host, run a fresh probe using:

```text
measured_safe_cap = min(3, floor((free_gb - 1.5) / 2.0))
```

Rules:

- cap 0: stop; no scored cell;
- cap 1: run one family chain at a time;
- cap >=2: the two family chains may run concurrently;
- arms within one family are always serial: anchor, neighbour, control;
- never run pytest while a heavy scored worker is active.

There are only two eligible chains, so a measured cap of 3 does not authorize a
third family or reuse ILLIQ's blocked slots.

## 3. Git transfer is code-only

GitHub receives code, manifests and audit evidence. It must not receive raw
market data, credentials, local ledgers or generated scored artifacts that the
contract marks gitignored.

The source host creates one archive from the execution tree's `staged_data/`.
The archive contains 90 data files plus its local manifest file. Record the
archive byte count and SHA-256 outside Git.

Verified source-host transfer artifact created on 2026-09-04:

```text
path       /Users/hoangminhlong/Downloads/v12-staging-W12-f0799cae.tar.gz
size       108 MiB compressed; 147181897 bytes uncompressed regular files
contents   91 regular files = 90 frozen data files + staged_manifest_.json
safety     no absolute path, .. traversal, symlink, hardlink or AppleDouble file
sha256     dc7608596a74e79629b04f2fb2aca7020569297ed4869159fbbd05d56e4d0ed8
```

The archive checksum verifies transport integrity. It does not replace the
mandatory per-file 90/90 check against the committed staging manifest.

The new host must obtain:

```text
origin/orca/v12-integration at the pushed pre-execution tip
W12 commit f0799cae6fc47846937cf1a370719314696ee990
the separate staged-data archive
```

Git pull alone is never proof of data transfer.

## 4. Strong-host bootstrap

Use a fresh clone or a clean existing clone. Do not copy `.git/worktrees` from
macOS to Windows.

PowerShell outline:

```powershell
cd C:\Users\ROYAL\my-quantitative
git fetch origin --prune
git switch --force-create orca/v12-integration origin/orca/v12-integration
git status --porcelain=v1
git rev-parse HEAD
git cat-file -t f0799cae6fc47846937cf1a370719314696ee990

git worktree add --detach .worktrees\crypto\v12\exec-v12-1 `
  f0799cae6fc47846937cf1a370719314696ee990
git worktree add --detach .worktrees\crypto\v12\repro-v12-1 `
  f0799cae6fc47846937cf1a370719314696ee990
```

If either path already exists, inspect it; never delete/reset it blindly.
Both trees must be detached at W12 and clean.

Before extracting an archive, list it and reject:

- absolute paths;
- `..` traversal;
- symlinks or unexpected top-level entries;
- anything outside `staged_data/`.

Extract the same bytes into both W12 trees. Make staged files read-only where
the platform allows it. Recompute every SHA-256 against
`research/audits/v12p/a3_staging_manifest.json`; require 90/90 PASS in each
tree and execution/reproduction byte equality. The derived staged manifest must
equal `f855ad9c778f7a8695d6416b1c912efd7ddc353bf70935669504016cbf3c3c40`.

Seed `results/registry/experiments_v12.jsonl` as an empty file only after
verifying its SHA-256 is the empty-file digest recorded in
`ledger_package/transfer_manifest.json`.

## 5. E0 launch gate before the first score

A1 must write a strong-host launch evidence artifact containing:

- UTC time, hostname, OS, CPU, total/free RAM and disk;
- integration tip and ancestry to W12;
- exec/repro HEAD, detached state and porcelain;
- 90/90 execution hashes and 90/90 reproduction hashes;
- staged-manifest digest and empty-ledger digest;
- six frozen arm digests recomputed from the W12 implementation;
- resource cap and planned concurrency;
- budget 0/9, denominators 125/128, S1 sealed, workers 0;
- the owner's explicit `GO V12 SCORED EXECUTION` authority.

### Mandatory execution-driver check

Stocks and Forex showed that an unaudited runner/sidecar can change accounting.
Therefore E0 must identify the exact W12 scoring entrypoint and hash every file
that can affect schedule, fills, costs, funding, metrics, publication and
digests.

If no complete scored execution entrypoint exists in W12, stop with:

```text
V12_BLOCKED_EXECUTION_DRIVER_ABSENT
```

Do not write an ad-hoc post-freeze scorer, do not borrow the Stocks/Forex runner,
and do not treat a dummy dry-run as proof of scored execution. A new scorer
would require a new code freeze and another independent A7 delta audit before
any score.

This check is mandatory even though prelaunch passed, because the prelaunch
evidence proves family implementations, dummy publication and pinning; it does
not license an unpinned host-specific sidecar.

## 6. Scored execution order

The eligible cells are exactly:

```text
OILEV-V2
  1. OILEV-V2-28D-FLOW-W       anchor
  2. OILEV-V2-56D-STOCK-W      neighbour
  3. OILEV-V2-28D-FLOW-W-INV   causal control

BAB-LOWBETA
  1. BAB-90D-W                  anchor
  2. BAB-DOWNCORR-90D-W         neighbour
  3. BAB-90D-W-INV              causal control
```

Within each chain, publish and checkpoint one cell before starting the next.
With cap >=2, OILEV and BAB may be separate workers, but A1 remains the sole
ledger publisher. Use a lock or queue so simultaneous workers cannot append the
registry directly.

For every cell:

```text
verify W12 + arm digest + data digest
-> record OBSERVED exactly once when a scored metric exists
-> compute from frozen schedule/folds only
-> next-allowed-event fills
-> execution costs once + native funding once
-> frozen stresses and meaningful drop-one
-> canonical artifact bytes and SHA-256
-> A1 publish exactly once
-> replay proves zero counter delta
-> update heartbeat and release worker resources
```

ILLIQ stays `BLOCKED_DATA`; do not create three replacement cells. Final V12
budget may therefore be 6/9 with six computed/published cells.

## 7. Cross-asset-derived science checks

In addition to the frozen V12 gates, terminal reporting must make these existing
gate meanings explicit; they do not add or alter thresholds:

- separate raw PnL from incremental mechanism evidence;
- show BTC/common-market exposure where already frozen and available;
- show anchor, neighbour and control side by side;
- reconcile positions, cash, gross, turnover, costs and funding from trades;
- confirm costs/funding are not duplicated by a sidecar;
- report symbol and positive-fold concentration;
- report drop-one selected a held maximum-weight symbol;
- report base and every frozen cost/funding stress;
- state clearly that a coherent but negative mechanism is still rejected;
- state clearly that positive raw PnL with failed control is still rejected.

No post-score diagnostic may retroactively become a gate or rescue a family.

## 8. Reproduction and terminal A7

After all computed cells finish:

1. stop and verify execution workers are zero;
2. copy only the immutable input snapshot and content-addressed execution
   evidence required by the reproduction contract;
3. rerun every computed cell in fresh processes from the detached reproduction
   tree at W12;
4. require exact matches for arm identity, schedules, trades, costs, funding,
   metrics, gate verdicts and canonical digests, excluding only explicitly
   volatile metadata;
5. independently reconcile cash/turnover/cost/funding and exact artifact-byte
   hashes;
6. run terminal A7 without giving it permission to repair producer outputs;
7. append terminal state, MAP and evidence; never rewrite earlier ledger rows.

Allowed outcomes remain those in `PLAN_crypto.md`. A survivor is only locked for
a later owner-approved S1 cycle; it is not paper/live authorization.

## 9. Clock and stop rules

The 12-hour scoring clock starts only after all E0 gates pass and the explicit
owner GO is recorded.

- with less than 120 minutes remaining, start no new scored cell;
- with less than 45 minutes remaining, stop workers safely and close incomplete;
- a technical abort costs zero budget only if no scored metric exists and a
  forensic TECHABORT artifact proves it;
- a scored but rejected cell remains observed and cannot be erased;
- any mismatch, S1 access, credential access, live/paper path, unknown process,
  dirty W12 tree or counter conflict is an immediate fail-closed stop.

## 10. Required owner checkpoints

A1 reports:

1. strong-host intake and resource cap;
2. 90/90 equal-twin staging plus W12/ledger/driver gate;
3. after each family chain (three cells), not every log line;
4. reproduction result;
5. independent terminal A7 verdict and released resources.

Each report includes full SHA values, commands, exit codes, counters, budget,
S1 seal, worker PIDs, artifact paths and exact blockers.

## 11. Boundaries

This runbook authorizes neither S1 nor deployment. It forbids:

- changing W12 strategy/scoring bytes after seeing results;
- parameter grids, optimization, substitute families or unused-slot reuse;
- inspecting or copying S1;
- paper, testnet, live, orders or credentials;
- committing raw market data or local ledgers;
- force-push, history rewrite, merge to `main` or worktree deletion;
- presenting a positive return as an edge when the frozen mechanism/control
  gates reject it.

The objective is a trustworthy answer, including `V12_REJECT_ALL` if that is
what the six frozen cells show.
