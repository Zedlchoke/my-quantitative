# A7 Independent Pre-launch Challenge Memo — Sprint V8R (T14)

- Auditor: A7-independent-v8r (independent; no production code touched)
- Audited at UTC: 2026-08-26T02:06:56Z
- Launch SHA W: `a1f86d185867378a3721d2d39585e4427166f27c`
- Integration chain: `291a158` → … → `fe7f9bc` (contract freeze_final) → `4b129e5` (equity addendum, current tip)
- Method: every pinned claim re-measured from bytes/artifacts, not trusted. Full pytest suite re-run at W in exec-r1.

## Verdict

**T14: PASS → V8_LAUNCH_AUTHORIZED**

All 12 audit checks True. Pre-launch attestations written ×4 via
`research.provenance_v6p.write_attestation` (byte-identical across trees,
sha256 `1789ca7f7849625a28c67a39b50827f0f5b72a2abda063561be69cc42f5d7366`);
`validate_launch_provenance` returns `[]` in all four exec trees post-write.

## Adversarial re-measurements (all passed)

1. **Heads/cleanliness**: all four exec trees detached exactly at W; only
   untracked entry per tree is the exempt `research/audits/v8p/baseline_root.json`
   (explicitly allowed by baseline `allowed_uncommitted_at_launch` and by the
   validator's exempt set).
2. **Hashes recomputed**: resolved contract (integration tree)
   `6081b31c…886b6`; t12_gate `ccd421da…fc529`; golden `f529d1e5…aa800`;
   crypto selection `e73c703f…56376`. All match preflight pins.
3. **Contract dataset_hashes vs my recomputation**: data_audit_v8 `fe362484…`,
   data_manifest_v8 `78642d1b…`, funding_coverage_v8 `a667c1b6…`,
   gap_census_v8 `8b8e2562…`, t12_gate `ccd421da…` — every value matches the
   bytes I hashed in exec-r1.
4. **Contract content**: grep `PENDING|TO_FREEZE|TEMPLATE_PENDING` = 0 hits;
   frozen trial inventory is EXACTLY {XSECT-WREV-3D, XSECT-WREV-7D,
   XSECT-WREV-14D, XSECT-WMOM-7D-CONTROL}; universe = 6 traded alts
   (ADA/BNB/DOGE/LINK/SOL/XRP) + BTCUSDT benchmark-only; window/folds(×3,
   purge+embargo 7d)/costs(5bp taker, 1 tick) present;
   `launch_sha == W` and `launch_sha_frozen: true`.
5. **T12 held-exposure proof sanity**: verdict `T12_PASS_HELD_EXPOSURE_PROOF`.
   Methodology is coherent and strictly conservative: held region defined as
   [earliest contract-compliant fill, scored-window END] — the *widest*
   possible span, so folds/purge/eligibility can only delay exposure further
   (dominating bound; no trimming dodge). Earliest fill Mon
   2024-09-09T00:14:59.999Z (readiness 2024-09-04 + first Monday cutoff +
   next completed 15m bar). Funding head shortfall [2024-08-21T14:44:59.999Z,
   2024-08-23T08:00Z) precedes held time; margin 400.25h — arithmetic
   independently verified (16d16h15m). Coverage 2132/2132 cadence slots,
   0 missing, across all 6 required symbols (+BTC context).
6. **Golden determinism**: no `/private/var`, `pytest-of`, or `/tmp` paths in
   the committed artifact; `two_run_canonical_digests_equal: true`; expected
   vs actual all-match (24 orders, weights 0.2/synthetic leg).
7. **A8 selection conformance**: schema 2.0.0 correction manifest;
   `btc_excluded: true`; ranking = median daily quote volume over PRE-window
   [2025-07-22, 2025-08-21) only; BTCUSDT ineligible before ranking
   (`BTC_BENCHMARK_MEASUREMENT_ONLY_EXCLUDED_BEFORE_RANKING`); chosen top10 =
   ETH,SOL,XRP,DOGE,ENA,SUI,1000PEPE,ADA,BNB,LINK — BTCUSDT absent; census:
   758400 slots total, 57 gaps all explained (ETH capture boundary), 0
   unexplained; funding held-exposure complete for all top10.
8. **Equity dual blockers**: `equity_provider_audit.md` →
   `V8X_EQUITY_NOT_STARTED_PROVIDER_BLOCKED` (present at W);
   `equity_spec_mapping_addendum.md` → `SPEC_MAPPING_AMBIGUITY_BLOCKED`
   (committed at 4b129e5, integration tree — after W by design, doc-only).
   Frozen equity candidate.yaml sha256 = `b8a8d2d9…0db9` untouched.
9. **No scored V8 artifact**: `results/portfolio_v8` absent in root, exec-r1,
   integration; root registry `experiments.jsonl` has 0 V8 rows
   (case-insensitive); no v8 shards under results/registry/shards.
10. **Tests re-run at W (exec-r1)**: test_live_guards_sprint.py → **15 passed**
    (no S1 live-order capability); targeted contract+golden-e2e → **52
    passed**; FULL suite independently re-executed → **862 passed, 16
    warnings**, matching the T02 claim exactly.
11. **Baseline hash chain**: identical bytes ×4 trees, sha256 `738f1985…953e6`;
    `launch_head == W`; `resolved_run_contract_sha256 == 6081b31c…` (contract
    file hash); `worktree_manifest_sha256 == 54b55f39…` (hash of control
    `exec_worktree_manifest.json`). No self-referential hash slot.

## Residuals (non-blocking; for terminal audit)

- R1 **integration_head lag in pins**: `exec_worktree_manifest.json` and
  `baseline.integration_head` record `fe7f9bc`; final integration tip is
  `4b129e5` (equity addendum landed after those artifacts were written).
  Doc-only commit; launch_sha pinning unaffected. Preflight T01 wording
  ("10 commits 291a158->fe7f9bc") counts cherry-picks only; full chain to
  tip is 13 commits (10 picks + a1f86d1 wiring + fe7f9bc freeze + 4b129e5).
- R2 **contract provenance path naming**: `provenance_contract` inside the
  resolved contract names `baseline_root_v8.json` /
  `a7_prelaunch_attestation_v8.json`, but actual enforcement filenames are
  `baseline_root.json` / `a7_prelaunch_attestation.json`
  (`research/provenance_v6p.py` constants). Stale naming; validator uses
  canonical names (attestation now present ⇒ reasons []).
- R3 **contract.source_commit lineage pointer**: points at `dd026c0`
  ("BOOTSTRAP: V7P→V7 execution contract", prior sprint) rather than V8's
  `291a158`. Informational field; `launch_sha` (the operative pin) is
  correct and frozen.
- R4 **T12 schedule provenance note**: gate records that
  `weekly_reversal.py` was not present in the auditing worktree at audit
  time, so schedule semantics were derived from frozen docs; at W the module
  exists and its tests pass. Acceptable; terminal audit may wish to confirm
  module behavior equals documented semantics (already covered by 862-test
  suite incl. weekly golden e2e).
- R5 **full-suite verification depth**: 862-pass claim re-verified once
  (exec-r1); r2–r4 verified by identical HEAD + identical tracked bytes, not
  by independent runs.
- R6 **attestation clock**: the four attestations share one timestamp
  (2026-08-26T02:06:56.041582+00:00) because byte-identical artifacts were
  required; the repo tool stamps per-call wall time otherwise. Driver-side
  clock freeze; tool code untouched.
