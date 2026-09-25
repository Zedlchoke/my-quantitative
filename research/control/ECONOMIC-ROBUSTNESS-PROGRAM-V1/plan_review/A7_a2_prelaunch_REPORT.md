# A7 PRELAUNCH AUDIT REPORT — PSCTV1 AMENDMENT A2 (BANDRIDGE PINS)

- Auditor: A7 fresh-context (no prior context; audit-only, no repairs)
- Date: 2026-09-25 (audit window 03:41–03:55Z)
- Object: Phase I change-set for amendment
  `plans/DRAFT_amendment_PSCTV1_A2_bandridge_pins.md` @ root commit
  `8801639980deda72bf3bace29a53f9a4356d243b`
- Lifecycle position measured: Phase V (fixtures + A7) complete; Phase A
  (activation, T_act) NOT done.

## VERDICT: AUTHORIZED_FOR_ACTIVATION

Findings: 0 HIGH, 1 MEDIUM, 2 LOW (advisory). The MEDIUM is a fixture-fidelity
weakness, not a code defect; the production guard it under-exercises was
verified independently against production bytes in this audit.

## Measured state

| Item | Measured | Expected | Match |
|---|---|---|---|
| PSV1 worktree HEAD | `d059287bbc41bd942d4eb9a53c93e492ff1cb9c7` | same | YES |
| PSV1 branch | `orca/prospective-shadow-v1-integration` | same | YES |
| PSV1 worktree status | clean (0 entries) | clean | YES |
| Band-risk worktree HEAD | `d396ae9a92b86508a937f70af46099727502a8c1` | same | YES |
| Band-risk status | clean | clean | YES |
| Root draft commit | `88016399…` contains `plans/DRAFT_amendment_PSCTV1_A2_bandridge_pins.md` | same | YES |

## C1 — GO gate: PASS

- `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/A2_gate/GO_RECORDED.json`
  (schema `erp1_amendment_go_record@1`): `go_phrase_typed` ==
  `go_phrase_expected` == draft §4 phrase `GO PSCTV1 AMENDMENT A2 BANDRIDGE
  PINS`, `form_check: EXACT_MATCH`. Draft §4 (L96) carries the identical
  phrase — character-for-character.
- Prerequisites recorded: independent review PASS (round-2 + round-2b delta;
  `DRAFTS_review_round2_REPORT.md` present in draft commit 88016399),
  `bandridge_fills_before_gate: 0`, `ledger_rows_before_gate: 61` — both
  independently re-measured true in this audit.
- `consumed_at_utc: 2026-09-25T03:41:00Z` sane: before the implementation
  commit (03:48:33Z), before the band-risk SPEC commit, after the draft
  commit; `authority_granted` scopes to Phase I only; Phase A explicitly not
  granted.

## C2 — Scope containment: PASS

- `git show --stat d059287b`: exactly 4 files, 310 insertions / 1 deletion —
  `research/shadow_v1/executor.py` (M),
  `research/control/prospective_shadow_v1/e/shadow_worker.py` (M),
  `research/control/prospective_shadow_v1/cost_regime_boundaries/BANDRIDGE_A2_PINS.json` (A),
  `tests/test_bandridge_a2_pins.py` (A). No other production file changed.
- Frozen family adapter `research/shadow_v1/families/btc4h_bandridge.py` is
  NOT in the commit and has a clean worktree status (no uncommitted diff).
- Band-risk commit `d396ae9a`: `SPEC.md` only, 40 insertions / 0 deletions —
  pure append; the frozen mount block above is byte-unchanged (diff contains
  no `-` lines outside the hunk header).

## C3 — Per-family isolation: PASS

- Diff review: `FEE_RATE_CURRENT = 0.0005` and `SLIPPAGE_TICKS_CURRENT = 1.0`
  untouched (runtime import confirms 0.0005 / 1.0; lineage 0.00075). The
  `cost_books_for` BANDRIDGE branch early-returns fresh copies of
  `BANDRIDGE_COST_BOOKS_PINNED` (both books fee 0.0006 / 0 ticks); the shared
  frozen construction for ILLIQ/PREMFADE/CARRY below is unchanged.
- Independent recomputation (this audit's own python run against the
  integration tree), all full sha256s match the boundary artifact:
  - BANDRIDGE  = `b84ae93ec764fd7e1615c8be7aa2b40c3cef2242b6438028057fd46e6e2cffa6`
  - ILLIQ      = `71ea4bd61bdf6f654a00b3ed6395c1c45a6c6df004aaeeb69b6b2f43ef2c7e68`
  - BASISLV    = `130d2e7ee97478c0ddc7d8209e62bf4e74ae82460833307a726884f3cbfd29ff`
  - XSECT      = `130d2e7ee97478c0ddc7d8209e62bf4e74ae82460833307a726884f3cbfd29ff`

## C4 — Sizing law (packet B): PASS

- `executor.py` L349: `self.cost_aware_sizing = bool(config.get("cost_aware_sizing", False))`
  — default False; only `build_executors`' BANDRIDGE branch sets it True.
- config_digest payload (L412–436): the key is injected via
  `**({"cost_aware_sizing": True} if self.cost_aware_sizing else {})` — key
  ABSENT when disabled. Proof: (i) the commit diff adds nothing else to the
  payload dict, so the disabled-path payload is byte-identical to pre-A2;
  (ii) targeted recompute: `canonical_digest` of a payload without the key
  (`64dffa5b…`) differs from with the key (`fa17836b…`), and an empty-spread
  payload is identical to the base — confirming the mechanism. Non-BANDRIDGE
  config_digest therefore stays byte-identical.
- `_rebalance_steps` (L999–1015): buy qty capped as
  `qty = min(w*equity/ref, self.sleeve.cash / (ref * (1 + fee)))` with
  `fee = self.sleeve.books[self.primary_book].params.fee_rate` (primary book =
  CURRENT_CONSERVATIVE_COST) — matches the packet formula
  `qty = min(w*equity/ref, cash/(ref*(1+fee)))` verbatim; applied only when
  enabled and only for positive weights (buys).

## C5 — Build guard: PASS (code-level)

- `build_executors` BANDRIDGE branch: calls `cost_books_for(family_id)`,
  raises `WorkerConfigError("…UNPINNED_COST_LAW fail-closed; amendment A2
  P-4")` if the result != `BANDRIDGE_COST_BOOKS_PINNED`, BEFORE the
  ForwardExecutor is constructed. The executor's `config["cost_books"]` and
  the guard's `built_books` come from the same `cost_books_for` call site in
  the same loop iteration — the guard checks exactly what the executor would
  receive.
- `config["cost_aware_sizing"] = True` is set inside the same BANDRIDGE-only
  branch.

## C6 — Fixtures genuine: PASS (1 MEDIUM caveat)

- Ran from the PSV1 integration dir:
  - `python -m pytest tests/test_bandridge_a2_pins.py -v` → 8 passed (0.24s)
  - `python -m pytest tests/test_shv1_executor.py tests/test_shv1_accounting.py
    tests/test_shv1_families.py tests/test_funding_accounting.py` → 78 passed
    (13.78s)
- Non-vacuity confirmed:
  - `test_a_sizing_b_replaces_the_a_failure_mode` FIRST proves the A-failure
    (`InsufficientCashError` raised at uncapped qty=1.0 under 6 bps full
    stack), then `test_a_entry_fills_first_completed_bar_exactly_6bps_with_sizing_b`
    succeeds under the packet formula with `cash >= -1e-9`, exact
    `fill.fee == qty*ref*0.0006`, zero slippage, both books at the pin, and
    `select_fill_bar` picking the first bar closing strictly after the
    decision (fill law A).
  - `test_c`/`test_e` re-derive the three family digests and prove fresh-copy
    semantics + global constants untouched.
- MEDIUM (F-1): `test_b_cost_mismatch_fails_closed` monkeypatches
  `cost_books_for` and then RE-IMPLEMENTS the guard INLINE inside
  `pytest.raises` — it proves the comparison logic and `WorkerConfigError`
  usage, but does NOT execute the production `build_executors` guard
  end-to-end (`test_b_guard_source_present` is grep-level only). Assessed:
  the production guard was verified in this audit against production bytes
  (C5), so this is a fixture-fidelity gap, not a code defect. Recommend at
  the next touch: a fixture that calls `build_executors` with a patched
  `cost_books_for` and asserts the real `WorkerConfigError`.
- LOW (F-3, advisory): the production guard calls `cost_books_for` a second
  time instead of reusing `config["cost_books"]` — equivalent for the
  production deterministic function; only a non-deterministic patch could
  diverge between the two calls.
- LOW (F-4, advisory): `test_d_frozen_family_logic_no_diff` proves
  "no uncommitted diff" via git status, not "no diff vs pre-A2" — the latter
  is independently established by this audit's C2 commit-scope check.

## C7 — Boundary artifact: PASS

`research/control/prospective_shadow_v1/cost_regime_boundaries/BANDRIDGE_A2_PINS.json`
(schema `psv1_cost_regime_boundary@1`): all four digests match my independent
recomputation exactly (full sha256s above); `activation.t_act_utc: null`
(FILLED AT PHASE A only); `laws.transition` = every BANDRIDGE record between
GO and T_act is TRANSITION_OLD_LAW under `130d2e7e…`; `laws.unpinned` = any
pre-T_act BANDRIDGE FILL is permanently `UNPINNED_COST_LAW — NOT PROMOTABLE`,
disclosed evidence only; `laws.no_backfill` = records never rewritten,
re-costed or re-labelled; the boundary is carried by the record digests
themselves.

## C8 — Worker untouched / ledger frozen: PASS

- Exactly ONE worker process: pid 35779,
  `python research/control/prospective_shadow_v1/e/shadow_worker.py
  --shadow-start 2026-09-14T23:48:01Z --runtime-root results/prospective_shadow_v1`,
  STARTED Thu Sep 24 15:21:21 +0700 (= 2026-09-24T08:21:21Z) — predates both
  the GO (2026-09-25T03:41:00Z) and the commit (03:48:33Z). The running
  worker is OLD code (5 bps + 1 tick law).
- Ledger
  `results/prospective_shadow_v1/ledgers/BTC4H-BANDRIDGE.jsonl`: EXACTLY 61
  rows (== `ledger_rows_before_gate: 61`). ZERO fill rows (all `fee: 0`).
  All 61 rows carry the OLD cost digest `130d2e7e…` and the OLD config
  digest `d7f1ae50…`. Max `observed_at_utc` = 2026-09-25T00:17:35Z — NOTHING
  has been appended since the GO (03:41Z), not even old-law rows. No
  UNPINNED_COST_LAW exposure exists.

## C9 — Restart plan / activation undone: PASS

- The change-set restarted nothing (worker start predates the commit by ~19h).
- `activation/` in the control dir contains only the ORIGINAL cycle's
  artifacts (activation.json Sep 15, mtm_cutover.json, mtm_prelaunch.json) —
  no A2 activation artifact exists yet, consistent with `t_act_utc: null`.
- Phase A remains open and is the only remaining step.

## WHAT PHASE A REQUIRES (per amendment §1b/§3 and the boundary artifact)

1. Restart the worker per the cycle's own procedure (precedent artifact:
   `research/control/prospective_shadow_v1/activation/activation.json` from
   the Sep-15 mount), with restart-idempotence proof and the forward-only law
   (no backfill of the fail-closed rows). Preserve cwd (the PSV1 integration
   worktree) and args `--shadow-start 2026-09-14T23:48:01Z --runtime-root
   results/prospective_shadow_v1`; the same path now carries d059287b
   (tree clean), so a restart picks up the new code.
2. Record T_act to the second (UTC) in an activation artifact: timestamp +
   cost-override digest (`b84ae93e…`) + executor hash-match proof; fill
   `t_act_utc` in `BANDRIDGE_A2_PINS.json`.
3. Boundary semantics: the FIRST new-digest BANDRIDGE record (cost_regime
   digest `b84ae93e…`; its config_digest will also change because
   `cost_aware_sizing` is now included) marks the boundary. Every BANDRIDGE
   record between GO and T_act stays TRANSITION_OLD_LAW; any such FILL is
   permanently UNPINNED_COST_LAW — NOT PROMOTABLE, disclosed only.

## RISKS IN THE RESTART PATH

- R-1 (time window, MEDIUM-ish advisory): until restart, the live worker
  charges the OLD law. The next fillable BANDRIDGE H4 decision that produces
  a FILL before restart would be UNPINNED_COST_LAW — NOT PROMOTABLE
  permanently. Restart before the next fillable H4 boundary.
- R-2 (LOW): restart must respect the one-heavy-job machine lock discipline
  (`researchctl.py locks inspect`) and must not disturb the other three
  families — their cost books/digests are proven byte-identical, so their
  rows continue unchanged across the restart.
- R-3 (LOW): the new config_digest for BANDRIDGE records will differ from
  `d7f1ae50…` — expected by design (P-1 key inclusion); consumers must not
  read that change as a strategy change. It is part of the boundary evidence.

## FINDINGS LEDGER

| ID | Severity | Finding |
|---|---|---|
| F-1 | MEDIUM | Fixture (b) re-implements the guard inline instead of exercising production `build_executors`; production guard verified independently in this audit (C5). Non-blocking. |
| F-3 | LOW | Guard re-calls `cost_books_for` rather than reusing `config["cost_books"]`; equivalent for the deterministic production function. |
| F-4 | LOW | `test_d` proves only "no uncommitted diff" on the frozen adapter; "no diff in commit" established by audit C2. |

No HIGH findings. No incidents.
