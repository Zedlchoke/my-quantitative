# FREEZE — BTC-COMBO6-SCORED-V1 — 2026-09-29 (A1, code+data freeze)

## SHA chain
- BASE_SHA (dispatch): 2481f307cbc5089d2895a24b4b2716b2254cc464
- IMPL_SHA (lane IMPL, one commit): 2db0e19bd0dfa43ddf4ecb36d6d8136367110a44
- CODE_FREEZE_SHA: this commit (HEAD after commit; measured by A7 via rev-parse)
- DATA_MANIFEST: staging/data_manifest.json sha256 ba6dcae425b03d849725f740fd5c578f3ff7103823fd56cd9b40a6b99f09c56f
- corpus_digest (engine): e270c9c77801aa19e250cceaae92b918062ed8777aea237ddf734ebcbfd06232

## Frozen artifacts (sha256)
- dry_run/btcombo6_dry.json: 53e3122e5fe39d7d5b17a088f3afc1cb53efbe035040049454ee0d08f5803806
- handoffs/IMPL.json: e3e7801e5f4a84e981d38b98e420ce0247d8e6d86e76e80885e00acc80e775df
- plan (with §12 erratum E1 fold 2025-12-26→2025-12-29): plans/PLAN_btc_combo6_scored_v1.md (in-commit)
- data manifest: ba6dcae425b03d849725f740fd5c578f3ff7103823fd56cd9b40a6b99f09c56f

## Freeze-time verification (A1 re-measured 2026-09-29T02:3xZ)
- pytest research/btcombo6/tests/ → 27 passed in 2.74s (worktree, root .venv)
- dry-run replay: exit 0, replay identical=True (2238dc08849e…), elapsed 6.1s (cached);
  diff vs IMPL-committed artifact = generated_utc only
- worktree tree clean pre-freeze-commit (only this freeze set added)
- dry artifact regenerated at freeze (generated_utc 2026-09-29T02:33:35Z) — canonical
  content byte-identical to IMPL run apart from that stamp

## Frozen execution law deltas disclosed at freeze (from lane IMPL handoff)
1. Final-fold EVAL-wall + B1 wall exit priced at last in-window 5m close (sealed
   tail untouched; hard-cap wins over literal next-bar wording).
2. decision_ts = last-constituent-5m-bar open; unified next-bar fill law.
3. While-LONG signals discarded (not queued); panel-end-open positions stay open.
4. Funding window (fill_ts, exit_ts], ts floored to 8h slots.
5. Ledger rows keyed by cell (7 cells); recomputation replaces, denominator counts
   unique cells.

## Next gates (in order)
sanitized dry-run ✔ (this freeze) → A7 prelaunch (fresh context, audits/) →
GO_RECORDED (owner standing directive consumed at gate) → scored under heavy lock
(≤12 cells) → reproduction twin → A7 terminal → two-half close.
