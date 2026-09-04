# V12R staging + A7 delta audit plan (strong host ROYAL)

Operational plan for the remaining launch gates after the W12R freeze
(`ccfd33e3ed302de642e1ebdecb8adb6830dba887`). No scored cell may start
before every gate below is recorded PASS and A7 returns LAUNCH_AUTHORIZED.

## 1. Archive arrival gate

```text
path     C:\Users\ROYAL\Downloads\v12-staging-W12-f0799cae.tar.gz
sha256   dc7608596a74e79629b04f2fb2aca7020569297ed4869159fbbd05d56e4d0ed8
```

1. `certutil -hashfile <path> SHA256` must equal the expected digest
   (mismatch or absence = fail-closed stop; never re-download and treat as
   byte-identical; never regenerate the 7 funding_20240820 files).
2. Safety inspection BEFORE extraction (`tar -tzf`):
   reject absolute paths, `..` traversal, symlinks/hardlinks, AppleDouble
   (`._*`) entries, and any top-level entry outside `staged_data/`.
   Expected: 91 regular files = 90 frozen data files + `staged_manifest_.json`.

## 2. Equal-twin staging (both W12R trees)

1. Extract into a temporary directory only; verify the extracted tree.
2. Copy `staged_data/` into `.worktrees/crypto/v12/exec-v12r-1/` and
   `repro-v12r-1/` (byte copy; make files read-only where the platform
   allows).
3. Recompute per-file SHA-256 in BOTH trees against the committed
   `research/audits/v12p/a3_staging_manifest.json`: 90/90 PASS each tree.
4. Derive the staged manifest (frozen
   `research.v12.data_contract.build_file_manifest`) in both trees; both
   derived manifests and the shipped `staged_manifest_.json` must hash to
   `f855ad9c778f7a8695d6416b1c912efd7ddc353bf70935669504016cbf3c3c40`
   (exec == repro == frozen).
5. Record the staging evidence JSON under `research/control/v12_run/`.

## 3. Windows path shim for frozen Mac-rooted loaders (DISCLOSED to A7)

The frozen V12 loaders resolve raw data through Mac workspace constants
(`/Users/hoangminhlong/my-quantitative/...`, `research/v12/data_contract.py`,
`bab_lowbeta/audits.py CATALOG_PATH`). No frozen byte may be edited, so the
host shim is: create `C:\Users\hoangminhlong\my-quantitative\{oi_data,
funding_data, catalog_live_crypto\data}` with NTFS junctions onto the exec
tree's `staged_data\` subdirectories (read-through; no data copied; same
bytes). This shim affects WHERE bytes are read from, never WHICH bytes.

The driver itself does not need the shim (explicit `--staged-root` roots);
only the frozen evidence/dry-run entry points that hardwire Mac roots do.

## 4. Exact-arm dummy dry-run (owner condition 7)

* BAB: PASS already recorded
  (`research/control/v12_run/gates/V12R_BAB_EXACT_ARM_DRYRUN.json`,
  synthetic frame, temp ledger, zero denominator delta).
* OILEV: run `research.v12.families.oilev_v2.audits.run_exact_arm_dummy_dryrun`
  in the exec tree AFTER staging (frozen loader reads real OI through the
  shim). Record as `V12R_OILEV_EXACT_ARM_DRYRUN.json`.
* Confirm `results/registry/experiments_v12.jsonl` still hashes to the
  empty digest `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

## 5. Independent A7 delta audit (fresh lane from W12R)

A7 worktree: `.worktrees/crypto/v12/a7-v12r` (detached at W12R). A7 may
write ONLY `research/audits/v12r/a7_delta/a7_delta_v12r.{json,md}` (in its
own tree; A1 integrates). A7 must independently re-verify:

1. six-arm identity (recompute 6/6 digests vs selection_freeze v2);
2. no strategy mutation (W12 family/adapter bytes identical to W12;
   `git diff f0799cae..ccfd33e` adds exactly the driver + its tests);
3. cost/fold/ledger accounting (driver publishes ONLY through
   `publish_v12_cell`; family contract cells from the frozen folds
   derivation; scored metrics from the baseline cell only);
4. first-publish / replay semantics (observed +1 published +1 once; replay
   zero delta; refusal = one observation row; no partial record);
5. no lookahead (features PIT-completed; one declared execution lag; purge
   folds; drop-one = held max |weight|);
6. no S1 access anywhere in the lane;
7. exec/repro isolation (two detached trees; `--repro` cannot write any
   ledger; repro exact-match field list excludes only volatile metadata);
8. staging 90/90 equal-twin (section 2 evidence, re-hashed independently);
9. no V11 hardwiring (driver imports no V11 family logic; V11 import limited
   to the frozen digest function `publication_identity.arm_config_digest`
   and the frozen `Bar` dataclass via the frozen V12 modules).

Required verdict: `V12_S0_LAUNCH_AUTHORIZED_V12R` (or any mismatch =
fail-closed STOP). Budget 0/9, denominators 125/128, S1 sealed, workers 0.

## 6. E0 + scored execution (only after A7 authorizes)

Fresh resource probe; then the six cells exactly as
`PLAN_crypto_stronghost.md` section 6 orders them (family-serial
anchor -> neighbour -> control; two chains only if measured_safe_cap >= 2;
A1 sole publisher via per-family shard ledgers; driver `--publish
--expect-head ccfd33e3ed302de642e1ebdecb8adb6830dba887 --ledger ...`).
Reproduction afterwards: rerun each cell with `--repro --compare-with <exec
cell dir>` from `repro-v12r-1`; require exit 0 (ALL_MATCH) for 6/6.
