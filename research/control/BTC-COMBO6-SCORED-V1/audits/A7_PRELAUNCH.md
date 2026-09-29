# A7 PRELAUNCH AUDIT — BTC-COMBO6-SCORED-V1 — 2026-09-29

- Auditor: A7-PRE (fresh context; implemented nothing audited here; audit artifacts only)
- Target: worktree `.worktrees/btc-combo6-scored-v1/integration`, branch
  `orca/btc-combo6-scored-v1-integration`, freeze commit
  `c0f97a9db2e460707188877348af01d1c5d395d6`
- Method: recompute-from-bytes. Digests re-derived with `shasum -a 256` and an
  A7-written stdlib-only zip loader (no `research.btcombo6` imports on the
  corpus-digest path); tests re-run by A7; every implementer claim treated as
  a refutation target. Read-only inside the worktree except this audit
  namespace. The dry CLI was NOT re-executed (it rewrites `generated_utc`);
  instead the committed artifact was verified for internal consistency and its
  record ids / signal digests were re-derived from the cached panel + frozen
  constants.

## Findings

### F-1 — scored wrapper passes a CLI flag that does not exist (fail-closed blocker)
- Item: `research/control/BTC-COMBO6-SCORED-V1/run_scored_locked.py` (ROOT
  control-plane copy) builds `CMD = [... run_btcombo6.py, "--mode", "scored",
  "--stress-all"]`, but `run_btcombo6.py` argparse defines only `--mode` and
  `--worktree-root`.
- Result: subprocess aborts with
  `run_btcombo6: error: unrecognized arguments: --stress-all` (argparse exit 2)
  BEFORE any computation: no scored artifacts, no TRIAL_LEDGER row, no budget
  consumption, lock released by the handle context. FAIL-CLOSED — this cannot
  invalidate a scored run; it prevents the scripted scored run from starting
  at all. Left unfixed it would turn the scored gate into a NOT_RUN/TECHABORT.
- Evidence: A7 probe `python research/btcombo6/run_btcombo6.py --mode scored
  --stress-all --worktree-root /tmp/a7_probe` → `error: unrecognized
  arguments: --stress-all` (run outside the worktree against an empty root;
  no real-corulus touch). Source: run_btcombo6.py lines 33-35 (argparse
  definitions), run_scored_locked.py line 20-22 (CMD).
- Severity: **MEDIUM** (availability of the next gate; zero integrity impact;
  budget untouched).
- Remediation owner: A1 — remove `"--stress-all"` from CMD in the ROOT
  control-plane wrapper (root `run_scored_locked.py` is not part of the
  frozen worktree identity; no code-freeze change needed, no rescue of
  owner-pinned specs involved). Must be done before scored execution.

### F-2 — SPEC_FREEZE.md still carries the pre-erratum fold end (documentation drift)
- Item: root `SPEC_FREEZE.md` (frozen at registration commit 2481f307) line:
  "Folds: F1 2021-01-04Z +10×26w → EVAL_END 2025-12-26T00:00Z".
- Result: stale relative to the binding spec: plan §12 erratum E1,
  DATA_COST_FREEZE.md ("AUTHORITATIVE calendar … EVAL_END 2025-12-29T00:00Z"),
  spec.py (EVAL_END = F1_START + 260w = 2025-12-29, pinned by
  test_fold_calendar_erratum_applied) and the dry artifact all say
  2025-12-29. A7 independently re-derived the arithmetic: 2021-01-04 + 260w
  = 1820 days = 2025-12-29 (Monday); 2025-12-26 − 2021-01-04 = 1817 days =
  259.57 weeks — the erratum is arithmetically justified and consistently
  implemented. The plan (with §12) is the binding spec per FREEZE.md, so this
  is documentation drift in a registration-time snapshot, not an identity
  conflict.
- Evidence: read + diff of the named files; A7 python recompute of the fold
  arithmetic (output: `2025-12-26 - 2021-01-04 = 1817 days = 259.57w`,
  `2025-12-29 - 2021-01-04 = 1820 days = 260.0w`, `EVAL_END = 2025-12-29
  Monday`).
- Severity: **LOW**.
- Remediation owner: A1 — one-line annotation at GO_RECORDED time (or a
  control-plane note) that SPEC_FREEZE.md's fold line predates erratum E1 and
  is superseded by plan §12 + DATA_COST_FREEZE.md. No code change.

### F-3 — DATA_COST_FREEZE.md funding census number measured to the pre-erratum window
- Item: DATA_COST_FREEZE.md: "5,451 events inside eval window".
- Result: the dry artifact reports 5,460 in-window events for the
  authoritative window [2021-01-04T00:00Z, 2025-12-29T00:00Z). A7
  independently recomputed from `funding_events.parquet`: floored-8h events
  in [2021-01-04, 2025-12-29) = 5460 = 1820d × 3/day; in [2021-01-04,
  2025-12-26) = 5451 = 1817d × 3/day. The freeze-doc number is exactly the
  pre-erratum-window count; the engine number is correct for the erratum
  calendar. The delta was already honestly disclosed in
  handoffs/IMPL.json ("5,460 … = DATA-VERIFY's 5,451 (counted to the
  uncorrected 2025-12-26 end) + 9 events in the 3 erratum days").
  All other funding census numbers (7,643 rows, contiguous 8h, min/median/max
  rate −0.003/0.0000972/+0.003, jitter ≤47 ms) re-verified by A7 and match.
- Evidence: A7 pandas recompute of the parquet (own logic): rows=7643,
  w1=5460, w2=5451, interval unique=8h, max jitter=47 ms.
- Severity: **LOW** (documentation staleness in a lane-measured freeze note;
  no code or artifact inconsistency).
- Remediation owner: A1 — note alongside F-2; no code change.

### F-4 — registry row `head` pins BASE_SHA 2481f307, not the freeze commit
- Item: plans/CYCLE_REGISTRY.json row BTC-COMBO6-SCORED-V1 `head:
  2481f307…`, while worktree HEAD is c0f97a9d.
- Result: expected governance behavior — the registry is writable only at
  gates by owner/orchestrator; lanes never touch registries (AGENTS.md), and
  the IMPL/FREEZE commits are lane commits. All other registry fields verify
  (see clean checks C-2). A1 updates the head at GO_RECORDED/close.
- Severity: **INFO** (no action; recorded so the mismatch is explained, not
  hidden).

### F-5 — truncation-replay prefix test exercises LEG-1 only
- Item: test_truncation_replay_prefix_stability runs prefix re-computation on
  the momentum leg (6 prefix lengths) but not on LEG-2..LEG-6.
- Result: mitigations verified by A7: (a) all legs share one engine
  fill/exit/force-flat code path with no per-leg branching beyond spec
  constants; (b) the signal layer for every leg uses only trailing rolling /
  shift(1) / prior-emitted-bar operations (read line-by-line); (c) the
  cross-state machines for all legs are covered by hand-computed tests
  (SMA-NaN ineligibility, incomplete-bucket absence, momentum state-change).
  Residual risk: a leg-specific prefix instability would not be caught by the
  suite. Not a violation of the plan; noted as a reproduction-twin target.
- Severity: **INFO** (suggested: R-REPRO twin covers all 6 legs, which the
  plan already requires).

### F-6 — engine's dry-run ban list is 7 words; A7 mandate list is 10
- Item: combo.BANNED_SUBSTRINGS = [pnl, profit_factor, equity, win_rate,
  drawdown, expectancy, return] — omits sharpe, gross, net.
- Result: A7 re-scanned the committed dry artifact recursively (keys AND
  string values, all depths, case-insensitive) with the full 10-word mandate
  list: ZERO hits. The narrower engine list is currently inconsequential (the
  engine also deliberately does not serialize the banned words themselves, to
  avoid self-tripping recursive greps — disclosed in IMPL.json).
- Severity: **INFO** (no action required pre-launch; any future dry artifact
  change should keep the A7-10-word scan as the outer court).

## Checked and clean (absence reporting)

1. **C-1 Identity chain**: `git rev-parse HEAD` =
   c0f97a9db2e460707188877348af01d1c5d395d6 (equals dispatch freeze SHA);
   parents verified exactly: c0f97a9d → 2db0e19bd0dfa43ddf4ecb36d6d8136367110a44
   (IMPL) → 2481f307cbc5089d2895a24b4b2716b2254cc464 (BASE) → e12a5d30 (prior
   terminal cycle). Branch = orca/btc-combo6-scored-v1-integration.
   `git status --porcelain` empty before AND after all A7 commands (pytest
   caches are gitignored; probes wrote only to /tmp). Plan file byte-identical
   to the freeze-commit blob (`git show c0f97a9d:plans/... | diff -` →
   identical).
2. **C-2 Registry row**: ACTIVE_LIGHT; budget {used:0, max:12}; go_phrase
   "GO BTC COMBO6 SCORED V1 SCORED EXECUTION" REGISTERED_NOT_CONSUMED; plan
   path `plans/PLAN_btc_combo6_scored_v1.md` matches; worktree + branch match;
   s1 SEALED_UNTOUCHED; s0 OPEN; workers 0; active_heavy false.
3. **C-3 Artifact digests** (shasum -a 256, A7):
   - dry_run/btcombo6_dry.json = 53e3122e5fe39d7d5b17a088f3afc1cb53efbe035040049454ee0d08f5803806 = FREEZE pin ✓
   - staging/data_manifest.json = ba6dcae425b03d849725f740fd5c578f3ff7103823fd56cd9b40a6b99f09c56f = FREEZE pin ✓
   - handoffs/IMPL.json = e3e7801e5f4a84e981d38b98e420ce0247d8e6d86e76e80885e00acc80e775df = FREEZE pin ✓
   - owner_screenshots: Capture.PNG d85e4b0e6eb8742d6dc2709a2c3b33765c8665a9ea2ff739941eb50af3e2560a,
     Capture-1.png 3fde620aada3a40df9e4ed44feaf4347093b2e350f63735a602b49a884fa9077 —
     both equal SPEC_FREEZE pins ✓.
4. **C-4 corpus_digest independent recompute** (A7 stdlib-only loader: csv +
   zipfile + hashlib, no engine imports): 102 kl_*.zip, 32,532,793 bytes
   (equals DATA_COST_FREEZE), 707,616 csv rows, 707,616 unique open_time
   (0 duplicates keep-first), 0 non-5m-aligned stamps, first ts
   2020-01-01T00:00:00+00:00, last ts 2026-09-22T23:55:00+00:00 (all equal
   manifest panel stats and DATA-VERIFY census; expected-slot arithmetic
   2456d×288+288 = 707,616 → 0 missing of 707,616 slots); funding parquet
   sha256 fbc99a3ade3b2703e8fd53afd8ff191ca2b5bc136596e80215ef7ca3132de41b =
   manifest pin. Digest over data.py's recipe (schema btcombo6/corpus_digest@1,
   sorted [name,sha] pairs, panel_rows, first/last ts isoformat, funding sha;
   canonical JSON sort_keys/separators/ensure_ascii/allow_nan=False):
   **e270c9c77801aa19e250cceaae92b918062ed8777aea237ddf734ebcbfd06232** —
   byte-equal to FREEZE pin, manifest field, and dry artifact. All 102
   per-zip sha256s match the manifest individually (102/102).
   Committed m5_panel.parquet cache: 707,616 rows, same first/last —
   consistent with manifest panel stats.
5. **C-5 Dry-run hygiene**:
   - Recursive banned scan, mandate 10-word list (pnl, profit_factor, equity,
     win_rate, drawdown, expectancy, return, sharpe, gross, net — keys and
     string values, any depth, case-insensitive): **NONE**.
   - replay.first_digest == replay.second_digest ==
     2238dc08849e14ba7d669758dfe118f5315655c3cc98ca596dc58afb138351e3,
     replay.identical = true, replay_ok = true (matches FREEZE.md).
   - 6/6 legs non-vacuous: trades 3795 / 401 / 226 / 581 / 660 / 417 (all ≥
     30); per-fold sums equal totals; counter conservation holds for every
     leg (enter_signals = filled + discarded_while_long +
     expired_at_fold_boundary + dropped_no_bar).
   - Decision counts exactly on-grid (5m 524,160 = 260w×7×288; 4h 10,920;
     15m 174,720; 1h 43,680) — consistent with the 0-gap census.
   - Timestamps: only ISO timestamp after 2025-12-29T00:00Z anywhere in the
     artifact is `generated_utc` (2026-09-29T02:33:35Z — artifact stamp, not
     a trade/exposure timestamp). Values exactly AT the wall appear only at
     fold_calendar.eval_end / sealed_tail_start (boundary declarations).
     No trade or exposure timestamp exists in the artifact (it carries only
     counts/digests).
   - record_id fields re-derived for all 6 legs from frozen spec + corpus
     digest (canonical-JSON sha256): 6/6 match. signal_digest fields
     re-derived by A7 from the cached panel via the signal layer (no engine
     PnL path): 6/6 match, and warmup-window enter counts (e.g. LEG-1 9647
     full-panel vs 7788 in-window) confirm the dry counters mask correctly to
     [F1_START, EVAL_END).
6. **C-6 Spec conformance vs plan §1** (source-verified, spec.py + signals.py
   + engine.py): clocks 5m/4h/4h/15m/15m/1h ✓; TP/SL 1/1, 8/3, 8/4, 8/3,
   8/3, 8/4 % ✓; SMA time-windows on the 5m grid-close master with
   min_periods=window (48/288, 144/864, 24/96, 24/144) ✓; RSI two Wilder
   lines (TA-Lib SMA seed, out[i] uses only closes ≤ i), 20 crossing above
   55 on complete-bucket 15m closes ✓; momentum state-change of
   close/close[-48]−1 ≥ +1% ✓; $10,000 notional per entry ✓; long-only (no
   short/sell path anywhere in the engine) ✓; max-1-position (fill bar must
   be strictly after previous exit bar) ✓; next-5m-open fill, deferral to
   next present bar ✓; TP/SL levels from actual fill price ✓; same-bar
   TP+SL ⇒ SL first ✓; SL gap-through fills at min(SL level, bar open) ✓;
   force-flat at first 5m bar ≥ fold end at its open with fees, attributed to
   the closing fold ✓; funding measured, signed, floored to 8h slots,
   window (fill_ts, exit_ts] (strict-low, inclusive-high; A7 re-checked
   _funding_between searchsorted semantics + the dedicated test) ✓; cost 6
   bps/side = fee 5 + half-spread 1, stress ×1.0/1.5/2.0 applied to fee+spread
   only, funding unstressed ✓ (test_cost_stress pins it).
7. **C-7 Fold calendar**: F1_START 2021-01-04T00:00Z is a Monday; 10 folds ×
   exactly 26 weeks, Monday-aligned; EVAL_END 2025-12-29T00:00Z Monday =
   F1_START + 260w (A7 recomputed independently); sealed tail
   [2025-12-29, 2026-09-22T23:55Z) loaded+digested but never evaluated:
   decisions truncated at decision_ts < EVAL_END, engine eval frame capped at
   open_time < EVAL_END, final-fold force-flat priced at last in-window close
   (disclosed delta 1), _guard_sealed asserts no trade/equity ts ≥ EVAL_END,
   and the poison-the-tail test proves sealed bytes cannot move results.
8. **C-8 Lookahead**: grep across research/btcombo6 for `shift(-`, 
   `center=True`, `iloc[i+`, forward indices, cross joins → only one hit, a
   comment describing np.diff semantics in wilder_rsi (verified non-lookahead:
   RSI at i uses deltas ending at close[i]). All rolling windows are trailing
   with min_periods=window; state machines compare only consecutive emitted
   (complete-bucket) bars; equity marks use bar closes ≤ current bar.
   Complete-bucket law: aggregate() emits a bucket iff all constituent 5m
   bars present (n == 3/12/48), incomplete buckets ABSENT (not padded) —
   pinned by test_incomplete_bucket_absent_and_decision_defers, including
   15m and 4h holes.
   Truncation-replay test asserts canonical-bytes prefix identity of the
   trade list plus equity equality over 6 prefix lengths (60, 150, 288, 400,
   600, 863) ≥ 3 required.
9. **C-9 Test suite re-run by A7**: `/Users/hoangminhlong/my-quantitative/.venv/bin/python
   -m pytest research/btcombo6/tests/ -q` (cwd = worktree) → **27 passed in
   2.74s**, exit 0 — equals the IMPL/FREEZE claim of 27/27. Frozen constants
   are test-pinned: perturbing EVAL_END to 2025-12-26 (or any fold constant)
   fails test_fold_calendar_erratum_applied; perturbing LEG-1 TP or the 6 bps
   kernel fails test_fill_law_next_bar_open_exact_numbers (exit_px 101,
   fees 6.00/6.06); perturbing the stress law fails
   test_cost_stress_scales_fees_only (1.5× fees, funding unchanged).
10. **C-10 Governance / two-key posture**: heavy lock
    `researchctl.py locks inspect` → **FREE_PROVEN** (flock free, no
    registry row). GO phrase REGISTERED_NOT_CONSUMED in the registry; no
    auth/GO_RECORDED.json for this cycle (root auth/ empty; the only
    GO_RECORDED files in the worktree belong to other, pre-existing cycles).
    scored/ absent in the worktree control dir and empty in the root copy;
    no TRIAL_LEDGER.jsonl anywhere in this cycle's control dirs → observed /
    published scored denominators are 0/0 by absence; no PnL, equity,
    profit-factor or any scored output exists anywhere in the worktree or
    the cycle's root control-plane (grep). Owner directive verbatim on disk,
    root and worktree copies byte-identical; scored authority explicitly
    two-key: key-1 = this A7 prelaunch verdict, key-2 = owner standing
    directive consumed at the gate. S1 SEALED_UNTOUCHED.
11. **C-11 Declared-assumption honesty**: D1-D8 register present in plan §1;
    implementation matches each (verified in source: D1 long-only, D2 SMA
    time-windows, D3 RSI 20↑55 two-line, D4 trend leg = cross-up + TP/SL, D5
    $10k + max-1, D6 fresh false→true state-change, D7 spread ≤0→>0 on
    consecutive emitted clock bars, D8 TP/SL from fill). FREEZE.md's 5
    disclosed execution-law deltas match the code: delta 1 (final-fold
    EVAL-wall + B1 wall exit at last in-window close — engine.py final-fold
    branch + always_long_baseline sealed_exists branch), delta 2
    (decision_ts = last-constituent-5m-bar open; unified next-bar fill —
    signals.py decision_ts = bucket open + clock_td − 5m), delta 3
    (while-LONG signals discarded, not queued; panel-end-open positions stay
    open — counters + open_at_frame_end + break), delta 4 (funding
    (fill_ts, exit_ts], ts floored to 8h — _funding_between + load_funding),
    delta 5 (ledger rows keyed by cell, 7 cells, recompute replaces —
    update_ledger). B0/B1/B3 baselines match plan §6 (B1 wall exit uses the
    disclosed delta-1 law; B3 prior-folds-only selection with lowest-leg-id
    tie-break and F1→LEG-1 default; both marked re-evaluations, not trials).

## Verification ledger summary

| check | result |
|---|---|
| HEAD == freeze SHA / parents / branch / clean tree | PASS |
| registry row (ACTIVE_LIGHT 0/12, GO REGISTERED_NOT_CONSUMED, plan path) | PASS |
| 3 artifact digests + 2 screenshot digests vs pins | PASS (5/5) |
| corpus_digest independent recompute (102 zips, stdlib loader) | PASS (byte-equal) |
| panel census 707,616 / 0 dup / 0 missing / 0 non-aligned | PASS (A7 re-measured) |
| dry artifact banned scan (10-word, recursive) | PASS (zero hits) |
| dry replay fields equal + present | PASS |
| 6/6 legs non-vacuous + counters conserve | PASS |
| no trade/exposure ts ≥ 2025-12-29T00:00Z in dry artifact | PASS |
| record_id + signal_digest re-derivation (6 legs each) | PASS (12/12) |
| spec conformance (clocks/TP/SL/SMA/RSI/momentum/costs/funding/folds/sealed) | PASS |
| lookahead greps + truncation replay + complete-bucket law | PASS |
| pytest re-run | PASS (27/27) |
| frozen constants test-pinned (mental perturbation) | PASS |
| lock FREE_PROVEN / no GO consumption / no scored outputs / no PnL | PASS |
| D1-D8 + 5 freeze deltas vs code | PASS |
| scored wrapper runnable as scripted | **FAIL-CLOSED DEFECT (F-1, MEDIUM)** |
| freeze-doc numbers vs erratum calendar | DRIFT (F-2, F-3, LOW) |

Finding count: CRITICAL 0 · HIGH 0 · MEDIUM 1 (F-1) · LOW 2 (F-2, F-3) ·
INFO 3 (F-4, F-5, F-6). No unresolved CRITICAL/HIGH. F-1 must be remediated
by A1 (one-line root control-plane wrapper fix) BEFORE scored execution; it
does not compromise any evidence audited here and fails closed.

PRELAUNCH_VERDICT: AUTHORIZED_WITH_FINDINGS
