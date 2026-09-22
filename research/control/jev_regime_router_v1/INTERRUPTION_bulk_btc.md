# JEV-REGIME-ROUTER-V1 — owner-authorized graceful interruption of the BTC bulk replay

## Stop reason (verbatim owner vocabulary)

`OWNER_STOP_FOR_NEW_DESIGN_AFTER_PREDECLARED_CANARY_AND_EARLY_REPLAY_COLLAPSE`

## Disclosure (verbatim owner law)

Stop occurred AFTER observing regime occupancy, therefore the V1 partial
result is **outcome-observed** and **cannot be treated as a clean terminal
comparison**. No `JEV_NO_INCREMENTAL_VALUE` conclusion may be drawn from
this partial history. No scored backtest was ever run; no PnL was computed
or observed; S1 remains `SEALED_UNTOUCHED`.

## Timeline (UTC, 2026-09-22)

| Event | Time |
|---|---|
| Bulk worker start (ps token `Tue Sep 22 14:06:42 2026` +07) | 07:06:42Z |
| Owner stop request received | ~07:21:30Z |
| SIGTERM → worker pid 88920 (identity verified vs lock registry: cycle JEV-REGIME-ROUTER-V1, role quant-implementer/jrv1-bulk-btc, worktree integration, token match) | 07:21:41Z |
| Worker exited (graceful, ~5 s) | 07:21:46Z |
| Orphaned replay child pid 88923 (spawned `run.py replay --asset btcusdt`) detected still appending; SIGTERM | 07:24:41Z |
| Replay child stopped; final file quiesced at 990 lines, tail parses clean | 07:24:51Z |
| Heavy lock recovered via sanctioned `cleanup_stale` (proven pid_dead → archived_stale); `FREE_PROVEN` | 07:23:17Z (pre-child-stop recheck after: FREE_PROVEN) |

Process discipline note (incident, disclosed): SIGTERM to the worker did not
propagate to its `run.py replay` subprocess; the replay child continued
appending ~36 extra states until identified and separately SIGTERMed. All
appends were atomic JSON lines; the final tail is a complete, parseable
record (`64cae8ff19c07953`, status OK). No kill -9 was used at any point.

## State at stop (branch-side)

```text
branch     orca/jev-regime-router-v1-integration
HEAD       f5ad69161e53d87b4a4a90a97f9dd9da56e3a0fe (pre-closure; this artifact commits after)
worktree   /Users/hoangminhlong/my-quantitative/.worktrees/jev-regime-router-v1/integration
```

## Partial replay accounting (BTCUSDT, of 8,567 frozen evaluable decisions)

| Quantity | Value |
|---|---|
| States expected (fold contract) | 8,567 |
| States started/responded (decisions jsonl lines) | **990** (11.6%) |
| Status OK | 981 |
| SCHEMA_ERROR (→ TRANSITION_UNKNOWN per frozen law, no retry) | 9 |
| Raw regime counts (OK only) | TRANSITION_UNKNOWN 963 (98.2%), UPTREND 18 (1.8%), DOWNTREND 0, ACCUMULATION 0, DISTRIBUTION 0 |
| Persisted regime counts (frozen persistence layer applied offline, classification-only) | **TRANSITION_UNKNOWN 990/990 (100%)** |
| Cache entries preserved (append-only, prompt-V1 keys) | 991 |
| New billable calls this bulk (excl. 94 canary states served from cache) | 896 |
| Tokens consumed (ESTIMATE from canary-measured ~1,315 input / ~75 output per call; per-response usage was not persisted — V2 design note) | ≈ 1.18M input, ≈ 67k output |
| Calls + tokens spent across whole V1 live phase (probes + fixtures v0/v1 + canary 94 + bulk 896) | ≈ 1,007 calls, ≈ 1.35M input tokens |
| Last complete state | `64cae8ff19c07953` OK TRANSITION_UNKNOWN (input_digest in decisions jsonl tail) |

## Evidence preserved (byte-intact, append-only; NEVER truncated/renamed/reused)

- `runtime/replay/btcusdt/decisions_btcusdt.jsonl` (990 lines, final)
- `runtime/replay/btcusdt/adapter_cache/` (991 entries)
- `runtime/replay/btcusdt/req_1line.jsonl` / `resp_1line.jsonl` (in-flight pair)
- `runtime/bulk_btc.log` path (empty: worker killed before capture), `runtime/bulk_btc_worker.out`
- canary artifacts: `runtime/fixtures_responses_preview.jsonl` (v0 channel),
  `runtime/fixtures_responses_pinned.jsonl` (v0 prompt),
  `runtime/fixtures_responses_v1.jsonl` (amendment_2 prompt),
  `runtime/jev_cache_preview/`, `runtime/jev_cache/`
- all audits: `audits/a7_1_pre_api_audit.*`, `audits/a7_1_r1_delta_audit.*`
- `INCIDENTS.md` (incl. JRV1-1), all freezes + amendment history, handoffs

## V1 failure class (for V2 design; classification-observation only, no PnL)

`UNKNOWN_COLLAPSE`: with the frozen V1 design (single choice question over 5
labels incl. TRANSITION_UNKNOWN as a selectable label), the pinned model
jev-1.13.0 returned TRANSITION_UNKNOWN for 98.2% of real BTC warmup-window
states at sub-threshold confidence (canary: median 0.44; only 19/92 ≥ 0.50),
yielding a 100%-UNKNOWN persisted path. The five-label forced-choice allows
the model to abstain; V2 removes abstention from the model's choice set and
makes abstention code-owned.
