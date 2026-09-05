# Staging backups manifest — worktree cleanup 2026-09-06

> Owner-authorized cleanup (2026-09-06). All closed-cycle worktrees were
> removed AFTER: (1) every branch was pushed to origin (the only rejected
> ref was `orca/v11-integration`, which is BEHIND its remote counterpart —
> protected, not lost); (2) every forest was archived whole (including
> gitignored staged data and generated files) into `~/staging_backups/`
> with sha256 manifest `SHA256SUMS.txt` (12 archives, ~1.8 GB compressed).
> The v12-lesson protocol (no worktree deletion without data backup) was
> followed; any V3R-style remediation can restore the exact bytes a frozen
> cycle scored on.

## Kept on disk (12 worktrees)

```text
/Users/hoangminhlong/my-quantitative                       root checkout (owner space)
.worktrees/crypto/v15/integration                         ACTIVE cycle V15
.worktrees/forex-free-v5/*  (9 worktrees)                 ACTIVE cycle V5
.worktrees/stocks-free-v10/integration                    ACTIVE cycle V10
.worktrees/stocks-free-v9/integration                     canonical death-inclusive
                                                          universe + panel (V10 re-hashes this)
```

## Archived and removed (restore: tar xzf <archive> -C .worktrees/)

```text
~/staging_backups/crypto-v14_full.tar.gz             V14 full forest (staged basis/OI/klines)
~/staging_backups/forex-free-v3_full.tar.gz          V3 forest (price snapshots, macro vintages)
~/staging_backups/forex-free-v3r_full.tar.gz         V3R remediation tree
~/staging_backups/forex-free-v4_full.tar.gz          V4 forest (evidenced vintages, scored staging)
~/staging_backups/forex-free-v1_full.tar.gz          V1 remnants
~/staging_backups/stocks-free-v2_full.tar.gz         z8-exec-1 ETF snapshot authority
~/staging_backups/stocks-free-v5_full.tar.gz         V5 forest (single-vintage SEC staging — F1 evidence)
~/staging_backups/stocks-free-v6_full.tar.gz         V6 forest (multivintage panel lane, sha 1cb115d3 source)
~/staging_backups/stocks-free-v7_full.tar.gz         V7 forest (Twelve Data probe evidence)
~/staging_backups/stocks-free-v8_full.tar.gz         V8 forest (staged panel+prices, twins)
~/staging_backups/stocks-free-v1_full.tar.gz         V1 remnants
~/staging_backups/tmp-a7_audit_v8.tar.gz             temp audit worktree
~/staging_backups/SHA256SUMS.txt                     integrity manifest
```

Branch evidence for every removed worktree remains on GitHub (all `orca/*`
cycle branches pushed). Historical worktree trees at any frozen SHA can be
recreated with `git worktree add <path> <SHA>`.
