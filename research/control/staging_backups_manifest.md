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

## Cleanup 2026-09-07 (owner-authorized "dọn file không cần thiết cho nhẹ máy")

Archives in `~/staging_backups/cleanup_2026-09-07/` (sha256 in its
`SHA256SUMS.txt`):

```text
forex-free-v5_full.tar.gz    224M, 29,439 files — closed V5 forest, removed
                             after: integration branch verified PUSHED
                             (3dacf1a on origin); V6 verified self-contained
                             (own v6 staging; its references to v5 are
                             inherited committed artifacts only).
                             Restore: tar xzf <f> -C .worktrees/
legacy_root_data.tar.gz      337M, 13,981 files — root legacy sprint-era
                             data: results/ (1.0G), catalog_live_crypto/
                             (129M), research_snapshots/ (113M), oi_data/
                             (98M), funding_data/ (11M), derivatives_data/
                             (8.4M). Empirically non-load-bearing: the five
                             test files referencing these paths pass 101/101
                             with results/ absent (synthetic config strings).
                             Restore: tar xzf <f> in repo root.
```

Removed without archive (regenerable caches): `.pytest_cache`, root
`__pycache__` dirs. TRACKED legacy files restored and KEPT (not deletable by
tree rm): `results/*.csv` (4 demo outputs), `catalog/data/**` (Nautilus
parquets) — formal removal, if ever wanted, is a tracked-file commit
decision.

Kept on disk: `stocks-free-v9` (4.8G — canonical multivintage panel; V11
mid-flight re-hashes it; next big cleanup candidate once V11 closes),
`stocks-free-v10` (2.8G — newest verified asset copies + observables),
`stocks-free-v11`, `crypto/v15`, `forex-free-v6` (all ACTIVE), `.venv`,
`catalog/`. Worktrees: 34 → 32 (v5 forest 8 removed, v11 +1 was added by the
V11 bootstrap). Net repo tree: 14G → 12G; archives added 561M to
`~/staging_backups/`.
