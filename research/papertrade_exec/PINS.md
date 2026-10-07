# PINS — SPORTS-PAPERTRADE-EXEC-V1 (Lane EXEC-RUNNER)

Machine-readable source of truth: `research/papertrade_exec/pins.json`
(schema `sports_papertrade_exec_pins@1`). Every file this runner imports or
consumes from a sibling worktree is byte-pinned there; `verify-pins` re-measures
at run time. **sha256 is the binding identity; worktree HEADs are ADVISORY**
(sibling lanes legitimately advance while this cycle runs — the byte pins are
what makes the imported code identity-stable).

Enforcement (fail-closed):

* Any REQUIRED file/data pin mismatch at a mutation command -> `BLOCKED_PIN_DRIFT`
  (exit 7), nothing written.
* Engine entry pins (`wnba26/predict.py`, `soccer/replay.py`, `nba26/loader.py`
  + `nba26/predict.py`): drift is `BLOCKED_PIN_DRIFT_ENTRY` in the wiring probe
  (sandbox rehearsal still runs the labeled synthetic adapter); a REAL-mode
  forecast refuses outright (`BLOCKED_PIN_DRIFT` for NBA).
* Optional-but-absent entry files surface `BLOCKED_WNBA_ENTRY` /
  `BLOCKED_SOCCER_ENTRY` / `BLOCKED_NBA_ENTRY` (rehearsal falls back to the
  labeled synthetic-p adapter; a real run refuses).
* `verify-pins --expect-head <sha>` additionally hard-checks THIS worktree's
  HEAD (exit 6 `HEAD_DRIFT`) — the controller's re-measure hook.

## Pinned packages (imported read-only at runtime)

| alias (module name) | source worktree | dispatch head | measured head 2026-10-07 | files pinned (sha256 = pins.json) |
|---|---|---|---|---|
| `spt_core` (paper core) | `.worktrees/sports-papertrade-v1/integration` | a752553f | `8105e878ec6c96fbe65cac9313e87b2e64654012` (advanced; pinned files byte-identical) | `__init__.py` 9ba57fc6…, `ledger.py` 66921271…, `risk.py` 13c7cbe6…, `dashboard.py` 27916d68…, `odds_client.py` 5d67c29d…, `go_gate.py` e3012845…, `sandbox.py` c27a56d4… |
| `wnba26` | `.worktrees/wnba-2026-remainder-v1/integration` | d6ed119e | 4620… (advanced; Lane B landed the entry mid-build) | `wnba_2026_remainder_ledger.py` 745014f0…, `predict.py` 5fc6459c… (entry `wnba26_predict`, contract-compatible with the dispatch's `predict_matches`; both names accepted) |
| `nba_harness` | `.worktrees/nba-winprob-ng-scored-v1/integration` (research/control/NBA-WINPROB-NG-SCORED-V1/harness) | a76dadb1 (scored terminal) | `a76dadb1c430aeb2436deb74c3f852a6aee7d01d` (== dispatch) | `arms.py` 5cfdb0b8…, `game_universe.py` e1c4fffb…, `real_loader.py` 948002b9… — RETAINED FOR THE BATTERY ONLY since EXEC-NBA-REWIRE (synthetic-inputs history replay); the scored-corpus read is DEAD (see `research/control/SPORTS-PAPERTRADE-EXEC-V1/ERRATUM_NBA_REWIRE.md`) |
| `nba26` | `.worktrees/nba-winprob-prospective-prep-v1/integration` (research/papertrade_nba) | 65ebefc4 (content; lane final HEAD 82542aa8) | 82542aa8 (measured 2026-10-07) | `loader.py` 2679be80…, `predict.py` 57f0c810… (entry `nba26_predict(upcoming, completed_rows, asof_anchor_utc)`; frozen B1_STAR law K=32/HCA=100/γ=0.75 quoted, warm-up R0=1500 carried pre-registration; frozen ESPN payloads ONLY — the scored bind corpus is never read). EXEC-NBA-REWIRE engine path |
| `soccer_prep` | `.worktrees/soccer-intl-winprob-prospective-prep-v1/integration` | 24e5745f | 1ca5cd7d… (advanced; Lane C landed the entry mid-build) | `replay.py` 22553f6b… (entry `soccer_b1_replay(fixtures, corpus_csv, asof_date)`), `PROVIDER_NAME_CROSSWALK_SEED.csv` 2132533b… |

## Pinned data snapshots (outside git)

| alias | path | pin |
|---|---|---|
| WNBA schedule snapshot | `~/.my-quantitative-data/wnba-2026-remainder-v1/refresh_20261007/wnba_schedule_2026.csv` | sha256 `0ed97fafa4392a38f2467e5a588b0a8713ece835ec7cb4fb96a48f8761d05f26` (== WNBA-WINPROB-2026-REMAINDER-V1 FREEZE_PACKET §5) |
| NBA 2026-27 schedule payloads | `~/.my-quantitative-data/nba-winprob-prospective-prep-v1/espn_schedule_2026_27/` | composite `3d527b3c1b3a215dc1bf480a79776602f3b8c4ee1f68463102c05d8ae2bc25e6` (sha256 of newline-joined per-file sha256 list, 208 `scoreboard_*.json`, lexicographic — recipe from NBA-WINPROB-PROSPECTIVE-PREP-V1 DATA_REFRESH_MANIFEST.md; re-derived and matched at every `verify-pins`). EXEC-NBA-REWIRE: post-GO only, the incremental refresh may lawfully extend the corpus — bytes + .meta written per game-day and a self-hashed `REFRESH_MANIFEST.jsonl` record chain (anchored at the frozen pin) documents the extension; verification accepts composite == frozen pin OR the manifest-chained extension, everything else fails closed (BLOCKED_NBA_PAYLOAD_TAMPER / BLOCKED_PIN_DRIFT). PRE-GO the frozen snapshot is the only lawful state and the refresh never executes |
| soccer corpus | `~/.my-quantitative-data/soccer-intl-winprob-prospective-prep-v1/corpus/results.csv` | sha256 `df35268f8fc341ff7fb93d448b4e40356676ac35300a6b4461fd199a99ac1514` (post-GO engine input; byte-identical to the SOCCER-INTL prep pins) |

## Key hygiene

The Odds API key: read at runtime only via the paper core
`read_key_fingerprint` (mode 0600 required, fail-closed); only the 12-hex
fingerprint may be journaled. Key bytes never appear in chat, prompts, argv,
logs, git, or tests (tests use tmp files with fake bytes). Default key path
`~/.config/wnba-money-capture/odds_api_key`; `key-check` probes it without
network.
