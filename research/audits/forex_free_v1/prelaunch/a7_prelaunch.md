# A7 FOREX-FREE-V1 F7 Prelaunch Audit

- **measured_at_utc:** 2026-09-03T12:05:43Z
- **auditor:** A7_PRELAUNCH (independent recompute; no repair, no scoring)
- **worktree:** `/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v1/f7-a7-prelaunch`
- **branch:** `orca/forex-free-v1-f7-a7-prelaunch` — clean at start
- **bootstrap_sha / HEAD:** `d26c6886a12957d725062cb3722025cba29c6a39` (verified match)
- **verdict: `FOREX_FREE_V1_LAUNCH_AUTHORIZED`** — zero blockers, zero unresolved HIGH/CRITICAL objections

Interpreter note: the brief named `/Users/hoangminhlong/.venv/bin/python`, which does not exist;
the project virtualenv `/Users/hoangminhlong/my-quantitative/.venv/bin/python` (3.12.14) was used.
Informational (LOW), same commands and counts.

## Per-check results

| # | Check | Result |
|---|-------|--------|
| C1 | Pin chain ancestry + selection freeze + rubric precedence | PASS |
| C2 | Frozen-spec fidelity (family1.py / family2.py vs proposal JSONs) | PASS |
| C3 | Tests (targeted then full suite) | PASS — 214 / 1162 passed |
| C4 | Dry-run digests + replay idempotence | PASS |
| C5 | Data authority + independent loader re-verification | PASS |
| C6 | Cost honesty | PASS |
| C7 | Boundary (budget 0/6, S1 seal, credentials, no push/merge) | PASS |
| C8 | Resource (8 cores / 8 GB, serial cells, suite alone) | PASS |
| C9 | Known accepted deviations verified | PASS |

## C1 Pin chain

`de904c2` (prior terminal, FOREX_BLOCKED_SELECTION_INSUFFICIENT) -> `9911016` (F5 wave, selection
frozen) -> `62cb736` (family-1 FXFV1-A3-P1) + `261cc03` (family-2 FXFV1-A3-P2) -> `d26c688`
(W1 prep = HEAD): every link verified with `git merge-base --is-ancestor` — all TRUE.

- `selection_freeze.json` selects exactly **FXFV1-A3-P1 + FXFV1-A3-P2**; rubric: highest satisfied
  count (all six eligible at 9/9), HIGH/CRITICAL disqualify, tie-break lexicographic.
- Rubric commit `8783bd2` (frozen_before_any_audit_or_selection=true) **precedes** audit
  integration `bd5f2a3`; the `selection_rubric_frozen_before_audit` block is **byte-identical**
  between `8783bd2` and HEAD — no post-audit rubric edits. Post-freeze manifest commits only
  added F6 lane records.

## C2 Spec fidelity (recomputed, not trusted)

- **family1:** m = c3/c0 − 1 over exactly 3 bars; anchor = London 08:00 Europe/London sign(m);
  neighbour = NY 08:00 America/New_York sign(m); control = London −sign(m).
- **family2:** r = p4/p0 − 1 over exactly 4 NY-session bars; gate |z| ≥ 1.0 exactly;
  sigma20 = sample stdev (n−1) of 20 rollover-to-rollover daily log returns from 21 prior-weekday
  16:00-NY closes **strictly before the signal date** — PIT independently executed and confirmed;
  neighbour = Tokyo 09:00 Asia/Tokyo (same gate, same NY-rollover sigma series); control = sign-flipped continuation.
- **Session clocks:** all instants from named IANA zones via zoneinfo, explicit fold=0 policy,
  fail-closed on nonexistent wall times, whole-hour alignment asserted.
- **Fills:** both families fill at the close of the NEXT allowed bar (never the signal bar, never
  intra-bar); top cost tier adds exactly one entry-delay event; flatten never delayed.
- **Flatten DST (independently reproduced):** last completed bar ends 16:00 America/New_York wall
  clock — 20:00Z in EDT weeks, 21:00Z in EST weeks — strictly before the 17:00 NY rollover; the
  flatten bar is required and never substituted; no position spans the rollover.
- **Costs:** 1.5 bps/side × {1.0, 1.5, 2.0} on every fill in both; S3 = 3.0 bps/side + delay.
- **Arm digests:** 3 distinct stable digests per family, independently recomputed; the digests
  recorded in the family-2 ledger match my recomputation.

## C3 Tests (exact counts)

- Targeted (`pytest tests/assets/forex_free_v1 tests/assets/forex tests/test_protocol_contracts.py tests/test_protocol_metrics.py -q`): **214 passed** (4.48s).
- Full suite (`pytest -q`, run alone after a ps check showing zero pytest processes): **1162 passed**, 16 pre-existing pandas deprecation warnings (61.72s).
- Delta vs F6 closeout's 1156: `d26c688` added exactly 6 tests to `test_td_loader.py` (verified via git diff) → 1156 + 6 = 1162 accounted for.

## C4 Dry runs

- family1 six-arm idempotent ledger at gitignored `data_raw/forex_free_v1/dryrun/f6_family1_dst_fixture_ledger.jsonl` (git check-ignore OK): 6 distinct digests; all six **independently re-derived and match**.
- family2 exact-arm digest **re-derived exactly**: `d53dc7bc3bbf3563cd877bcf6b803f891d35df9e7ef323e6c462d290172b0edc` (ledger header, 19 rows).
- Replay idempotence is **test-enforced**: `test_family1.py:271,429` (NOOP, row count pinned) and `test_family2.py:472,701` (REPLAY_NOOP, rows_added 0); both green in C3.

## C5 Data authority

- `data_contract.json`: **H1_RESEARCH_AUTHORIZED**, amended 6.5y floor (owner-authorized before proposals/outcomes; original 8-year gate failure preserved verbatim); H4 / bid-ask / rollover-financing UNAVAILABLE_FAIL_CLOSED.
- All 7 pairs re-computed at **6.5886–6.5926y** ≥ 6.5y (2020-01-29/30 → 2026-09-02); **zero gaps > 85h**; **12 EUR/USD artifact bars quarantined** (0.0281% < preregistered 0.1% fail-closed ceiling), manifest rows reconcile (42670 = 42658 + 12).
- `request_manifest.json` `canonical_digest_ledger` present; all 18 EUR/USD canonical `_a.json` windows sha256-verified against it — 0 failures.
- **Independent loader re-verification (EUR/USD):** `td_loader.load_pair_h1` → 42658 rows, 12 quarantined, first/last exactly as committed, ascending unique timestamps, 6.5892y, deterministic reload digest.

## C6 Cost honesty

No bid/ask, volume, financing or live-readiness claims anywhere in the family modules or
proposals — every such mention is an explicit negation / forbidden-assumptions check.
`RESEARCH_CANDIDATE_NOT_LIVE_READY` present in all four artifacts; `schedule_only=True`,
`scoring_authorized=False`, `scope=SCHEDULE_ONLY_DRYRUN_NO_SCORING`.

## C7 Boundary

- **Budget 0/6:** no forex-free-v1 scored artifact anywhere (repo-wide search negative). The
  `results/` CSVs are a pre-cycle upload (2026-08-19, prior-cycle USDT backtest), untouched by
  `de904c2..HEAD`.
- **S1:** SEALED_UNTOUCHED declared in run_contract/state/selection_freeze; not inspected (per contract).
- **Credentials:** `.env.example` placeholders empty; key_source = gitignored root `.env`; no embedded key values committed.
- **History:** zero merge commits in `de904c2..HEAD`; no `orca/forex-free-v1-*` remote refs (no push); `origin/main` at `b8876ef` predates the cycle; forbidden historical paths untouched; selected proposals unchanged since audit `bd5f2a3`.

## C8 Resource

hw.ncpu = 8, hw.memsize = 8 GB exactly; six cells run serially (cap ≥ 1 satisfied); full suite
ran with no forex-cycle worker concurrent. Note: a pytest from the unrelated **crypto/v12**
cycle started on the machine at 19:02:16+07, *after* the recorded runs (different worktree and
interpreter; no forex interaction).

## C9 Accepted deviations (verified, not new findings)

1. Both families fill at next-bar CLOSE per the frozen spec — implemented identically in both modules.
2. A4-P1 MEDIUM objection is on an UNSELECTED proposal — moot.
3. The HIGH orthogonality pair (FXFV1-A3-P1 ↔ FXFV1-A4-P2) has only its A3-P1 member selected; A4-P2 unselected (recorded in selection_freeze.json).

## Objections

| ID | Severity | Status |
|----|----------|--------|
| OBS-A7-PRE-01 (interpreter path in brief absent; project venv used) | LOW | accepted_informational |
| OBS-A7-PRE-02 (concurrent crypto/v12 pytest after recorded runs) | LOW | accepted_informational |
| OBS-A7-PRE-03 (pre-cycle results/ files present, untouched) | LOW | accepted_informational |

## Blockers

None.

**VERDICT: FOREX_FREE_V1_LAUNCH_AUTHORIZED** — the six frozen scored cells
(2 families × 3 arms × 3 cost cells, 21 scored trials per family, 0/6 scored so far,
`RESEARCH_CANDIDATE_NOT_LIVE_READY`) may proceed to F8 scoring under the frozen falsification rules.
