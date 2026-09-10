# MDP-V2 A7 audit log (independent, fresh context)

- Audited SHA: 70620a05be99e8d5d4fcd0c6f5542d3b3722d178 (verified via `git rev-parse HEAD` on this audit worktree, branch `orca/market-data-plane-v2-a7-audit`, tree clean before this commit).
- Base for V1-preservation diff: 8f5ee9c4e7c26416732a3b2c31957e58546d45df (V2 plan base).
- Venv used: the shared `/Users/hoangminhlong/my-quantitative/.venv` (same interpreter family as the cycle; nautilus_trader 1.230.0 confirmed).

## Commands executed by A7 (all from this worktree)

1. `git diff --stat / --name-status 8f5ee9c..70620a0 -- research/control/market_data_plane_v1_run/` -> only 2 new files + append-only event_log.jsonl hunk.
2. Read `research/market_data_plane/archive.py`, `manifest.py`, `replay.py`, `bar_archive.py`; grep of grammar/binding/confinement call sites.
3. `.venv/bin/python -m pytest -q tests/test_mdp_archive_confinement.py` -> 74 passed.
4. Inline Python: `governance.terminal_consistency.check_v1_run_dir` on the real V1 run dir -> 9 findings without addendum, 0 with; sha256 of state/heartbeat/terminal_report/worktree_manifest identical before/after.
5. Registry: parsed `plans/CYCLE_REGISTRY.json` (cycle_registry@1), read journal lines 21-32, recomputed `plans/ACTIVE_CYCLES.json` sha256 = last journal projection_sha256 (24ce77de...).
6. Inline Python: hand RSS math (1293058048 B -> 1233.15625 MiB; 1234567 kib -> 1264196608 B -> 1205.6318359375 MiB) + `normalize_rss` outputs; `pytest -q tests/test_mdp_perf_portable.py` -> 7 passed.
7. Grep sweeps: microstructure terms in bars/stream/adapters; bar imports in bbo/depth/tca (none); bridge reject paths.
8. `pytest -q tests/test_mdp_bars.py tests/test_mdp_bar_stream.py tests/test_mdp_nautilus_bar_bridge.py` -> 42 passed.
9. `pytest -q tests/test_mdp_adapter_crypto.py tests/test_mdp_adapter_forex.py tests/test_mdp_adapter_stocks.py` -> 55 passed; targeted greps of DST-fold/macro/entity/delist/calendar tests.
10. Crypto blocker reproduction: `PYTHONPATH=<this research dir> .venv/bin/python` calling `ParquetDataCatalog.query(data_cls=BinanceBar, identifiers=['ETHUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL'])` -> Rust panic at session.rs:268, precision-mode mismatch 8 vs 16 bytes. Input file sha256 recomputed, matches artifact. pyarrow metadata check: 35040 rows; row0 open blob LE-i64 2658930774144 /1e9 = 2658.93 matches sample_rows[0].
11. Host checks: `catalog_live_crypto` absent; wayfinder MAP S1 SEALED entries.
12. Parity-claim grep across V2 control (zero parity PASS claims); PnL-family grep over shadow artifacts and adoption records (only the leak-scan meta-block); schedule denylist inspected in forex/schedule.py.
13. Reproduction: 6-file subset (models, bars, archive_confinement, nautilus_bar_bridge, terminal_consistency, doctor_waivers) -> 196 passed; then the exact 16-file G3 suite -> 397 passed in this third tree; `git diff --name-only 6e2f01d..70620a0` over the 16 core files -> empty (counts directly comparable).
14. `.venv/bin/python research/researchctl.py locks inspect` -> HELD_PROVEN (foreign STOCKS-FREE-V13 pid 49521, token match, flock held); `researchctl.py job list` -> V2 job 190360b93b0e WAITING 0/3, V1 job 20545b514b91 WAITING 0/3 untouched.
15. Diff path audit: no `.worktrees/`, no foreign plan, no foreign control dir; registry delta limited to MDP-V1 row corrections + MDP-V2 registration; ACTIVE_CYCLES.json change is canonical-writer projection regeneration (foreign FOREX-FREE-V9 row change pre-dated base in journal line 25).
16. Secret/payload scan of full diff: one benign `token = str(platform).lower()`; largest file ~37KB; zero >100KB files.
17. `git worktree list` (10 V2 trees); `ps` (no V2 processes; foreign pid 49521 alive untouched); porcelain status of all 10 V2 trees (all clean).

## Findings

- MED-1: `perf_v1_unit_erratum.json` (plan F4 closure) absent anywhere in the tree; truthfully disclosed as pending in V2-G2; must land at P10.
- LOW-1: V2 state.json `head_integration` and registry MDP-V2 row head still record base 8f5ee9c; sync at P10.
- LOW-2: `row_hash_sample_16` holds 3 entries (cosmetic).

## Verdict

Audit PASS, 0 HIGH/CRITICAL. Recommended terminal label: `MARKET_DATA_PLANE_V2_BLOCKED_RESOURCE_CONFLICT` (see a7_verdict.json strongest_verdict_recommendation).
