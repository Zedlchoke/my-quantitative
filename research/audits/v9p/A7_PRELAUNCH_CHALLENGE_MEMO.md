# A7 V9P Pre-Launch Challenge Memo (V9 multi-family crypto discovery)

Auditor: A7-independent-v9p, 2026-08-26. Verdict: **PASS** -> `V9_LAUNCH_AUTHORIZED`.

## What I refused to take on faith, and re-measured

1. **Launch pins.** Both exec trees are detached at `206faf8a` (W); `git symbolic-ref` fails in both. Porcelain pre-attestation showed only the exempt v9p baseline file; post-attestation exactly the two exempt v9p files.
2. **Baseline chain.** Recomputed sha256 of `baseline_root.json` in both trees: identical bytes, `0300ce72...`. Inside it: `launch_head == W`; `worktree_manifest_sha256` recomputed against the root-repo manifest (`ec2be367...`, match); `resolved_contract_sha256` recomputed (`d08865c2...`, match).
3. **Contract vs budget freeze.** Trial inventory sets are equal element-by-element: L14(14d), L28(28d), TSTREND-CTRL(reverse), VOLSHK-S15(threshold 1.5), VOLSHK-CTRL(reverse). Cap 9 / planned exact 5.
4. **Universe.** Contract traded_symbols == both candidate.yamls == universe_selection_v9.json selected ranks 1-10. BTC appears only as measurement-only benchmark; manifest confirms exclusion before ranking. Manifest hash matches pin and contract's embedded pin.
5. **Novelty / no rescue.** Ledger N=112 verified via its explicit composition (99 + 1 neg-control + 4 + 4 + 4). All five forbidden families carry terminal labels; none appear in the V9 inventory. F2 residual_mr is archived NOT_RUN via the frozen orthogonality gate (mean|rho|=0.676 > 0.50 over 33 stamps >= 20 required). No `results/portfolio_v9` exists in any tree or the root repo.
6. **Runner wiring.** `--help` lists ts_trend/vol_shock; PROVENANCE_GENERATIONS maps V9 families to `research/audits/v9p`; `_provenance_exempt` covers the v9p baseline+attestation pair.
7. **Tests.** I re-ran the full suite myself in exec-r1 at W: **912 passed** (not just the targeted trio, which also passed 61/61). Collection count independently equals 912.
8. **Specs frozen.** Candidate hashes match baseline pins byte-for-byte; status sidecars stamped `locked_at_utc`; zero placeholder tokens.

## Attestation

Written per exec tree via `research.provenance_v6p.write_attestation`, then timestamp-normalized so both copies are byte-identical:
`c35b63f8f51604191a9b7c0812eda67535e19e6a0a5d085f1290c59dc5cde50a`.
`validate_launch_provenance` returns `[]` reasons in both trees.

## Residuals (non-blocking)

See `a7_prelaunch_audit_v9p.json`. Headliners: VOLSHOCK spec warmup 21 vs contract 28 (contract stricter, binds); runner would happily accept an unbudgeted `residual_mr` invocation — add a budget-freeze cross-check.

## Authorization

P14 (identical clean heads) and P15 (zero high/critical findings) are now satisfied from my side. **V9_LAUNCH_AUTHORIZED** for the exact 5-trial inventory at W.
