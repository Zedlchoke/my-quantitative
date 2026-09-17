# Remediation note — fsearch-remediation-r2 (A7 prelaunch findings)

Cycle: FOREX-SEARCH-V1 (store cycle ZCODE-ORCHESTRATION-V3). Branch
`orca/forex-search-v1-integration`, worktree
`/Users/hoangminhlong/my-quantitative/.worktrees/forex-search-v1/integration`.
Input: `research/control/forex_search_v1_run/audits/
a7_prelaunch_forex_search_v1.json` (verdict BLOCKED_PRELAUNCH; read-only).
Base SHA `051ce5318418f3209d89c9abccf2765caa081cf6` (verified before any
work: pwd, branch, HEAD all matched the dispatch packet).

Scope honoured: NO real-data execution, NO scored outputs, D2 stays
SKIPPED (§3b, R0 NOT_RUN), no network, staging loader untouched and still
GO-gated, no plan/ edits, no audit-dir edits.

## Finding -> fix

### F-1 (HIGH) — §4 F4 financing block missing from the D1 freeze

`cost_financing_block()` was dead code in `d1/build_d1_manifest.py` while
`plan_sections_frozen` claimed "§4 F4". Fixed: the block is now embedded in
the manifest as top-level `cost_financing_s4_F4` (constants ladder
1.5 bps/fill + 1.7 bps/night, stress 2.0 PRIMARY = 9.4 bps worst case; the
financing derivation VERBATIM — NG7 "~5.1 bps over 3 nights" for NZD-USD,
5.1/3 = 1.7, both caveats: a 3-night cumulative average does NOT bound the
single worst night, NZD-USD-worst generalized to all five legs without a
per-leg differential census; dual-books wiring; source digest of
`p0/cost_financing_manifest.json` re-verified). The selfcheck required-
fields list now includes the block and FAIL-CLOSED-verifies the verbatim
derivation needles, the constants ladder, the disclosure language and the
source digest. The claim `plan_sections_frozen: ["§3b","§4 F3","§4 F4",
"§5","§6","§8"]` is now TRUE.

### F-2 (HIGH) — DSR + P-11 absent from the scored-path harness

`i/adjudicate.py` now implements, inside `stage_a`:

* **P-11** `p11_per_period_series()` — the per-period (per-session)
  financed stress-2.0 net bps series on the frozen master calendar,
  PERSISTED inside the verdict (`series_persisted`, `series_digest`,
  `n_periods`, `n_active_periods`) plus `persist_p11_series()` for the
  scored E runner to write the series artifact.
* **DSR** `deflated_sharpe_ratio()` — Bailey & López de Prado (2014):
  `DSR = Phi((SR - SR0) sqrt(T-1) / sqrt(1 - g3*SR + ((g4-1)/4)*SR^2))`
  with `SR0 = E[max SR] = (1-gamma) Z(1-1/N) + gamma Z(1-1/(N e))`,
  deterministic stdlib-only normal ppf (bisection to 1e-12). GATING subgate
  at N = frozen grid size 33 (§5), alpha 0.10 (§3 owner-relaxed), bar
  `>= 1 - alpha = 0.90`, computed on the persisted P-11 series (per-session
  financed net returns over the frozen master calendar; flat sessions
  contribute 0.0; documented conservative convention: the other N-1
  configurations are outcome-blind so their SR variance does not exist
  pre-E — unit-variance normal-trials reading). The program-cumulative
  N=260 (P-9) at alpha 0.05 row is computed on the same series and carried
  as REPORTED ONLY (never gating), exactly per §6.
* **Outcome-name gating**: `adjudicate_cycle()` emits
  `FOREX_SEARCH_V1_SURVIVORS_UNDER_RELAXED_BATTERY_R0_NOT_RUN_PBO_NOT_RUN`
  ONLY after the DSR gate has COMPUTED and PASSED on every survivor;
  `dsr_gate_on_survivors` is printed on the cycle output; otherwise the
  cycle is INCOMPLETE_NOT_PROMOTABLE. DSR executes only at the scored E run
  behind the owner GO (Stage-A runs on survivors of the ordered battery);
  all numbers exercised in tests are synthetic fixtures.
* Synthetic tests added in `tests/test_forex_search_v1_i.py`: normal
  CDF/PPF anchors, E[max SR] monotonicity + hand values (2.112401 @ N=33,
  2.850201 @ N=260), independent in-test reimplementation of the DSR
  formula vs the harness (3 series x 3 trial counts), fail-closed
  zero-variance/degenerate series, deflation monotonicity d(5) > d(33) >
  d(260), gate alpha/bar wiring, P-11 persistence round-trip via
  `persist_p11_series`, DSR-failing arm rejected, survivor outcome name
  emitted only after DSR passes.

### F-3 (HIGH) — M0 ran a predecessor's 10-gate suite without disclosure

`m0/` now runs the plan-§9 M0 content in full:

* Inherited core `m0/test_m0_golden.py` (G1-G10) + `m0/m0_contract.py` are
  UNTOUCHED and verified BYTE-EXACT against the predecessor cycle's frozen
  digests (dad5de33…, ba3991bd… as recorded in the pre-remediation
  m0_verdict.json and cited by the audit).
* `m0/test_m0_extension.py` (NEW) adds **G4N** (verdict-purity negative
  control per plans/PLAN_stocks_ng6.md §3: no payoff-correlation primary
  normalization — the payoff-contaminated shared-instrument kernel merges
  two genuinely different signals and is CAUGHT by the contract verdict;
  the shared-instrument normalization identity is proven: elementwise
  normalization by a shared series is invariant to positive rescaling and
  decorrelates only when the stream stops being shared; no normalizer/
  payoff argument exists in the contract verdict path) and the **dual-books
  degenerate fixture** (hand-computed uniform-charge arithmetic on 3
  fixture arms at stress 1.0 / 2.0 PRIMARY / negative price book: the
  financed book never inverts sign, strictly differs from the price book by
  exactly 1.7 x stress per round trip; sign-inversion and pnl-adding-charge
  sensitivity fixtures are flagged).
* `m0/run_m0.py` re-run: core 10/10 PASS + extension 6/6 PASS
  (G4N x3 + DB x3) => 11/11 gates + fixture per §9.
* `m0/m0_verdict.json` re-written: cycle_id FOREX-SEARCH-V1, gate
  "M0 (plans/PLAN_forex_search_v1.md §9)", `inherited_core_byte_exact`
  block (digests recorded vs expected), extension block with its own file
  digest, exit codes and output.

### F-4 (MEDIUM) — f1_repull divergence flag never flips

`p0/f1_repull.py`: the DIVERGENCE branch now clears `ok_all` (previously
only VENDOR_UNREACHABLE / NO_OVERLAP did). `p0/f1_repull_result.json`
re-derived OFFLINE from the ALREADY-RECORDED per-leg evidence (new
`rederive` mode; NO network, NO re-pull; per-leg records byte-identical —
verified against the pre-fix file): `any_divergence_or_unreachable`
false -> TRUE against the five DIVERGENCE legs, with an `f4_correction`
block (prior flag, corrected flag, recomputation basis, archive-remains-
authority law). Consumer check: only f1_repull.py itself referenced the
field; `p0/assemble_gate.py` adjudicates F1(iii) from the per-leg verdicts
(unchanged, PASS_WITH_DISCLOSURE stands).

### F-5 (MEDIUM) — MONTHPOS-SECOND state_formula self-contradiction

The per-config formula was built by a fragile string `.replace()` that
produced `"(day-of-month of the decision date D <= 15) = (day-of-month >=
16)"` on the SECOND-half arms. Fixed with a direct single-predicate
constructor `monthpos_state_formula(half)`: SECOND now reads
`state = (day-of-month of the decision date D >= 16) — MONTHPOS SECOND-half
(day 16..end-of-month) …` (FIRST symmetric), each stating the complementary
half and the verification note: the engine (`p0_census.py
state_clock_cond`: `hit = first_half if monthpos == 'FIRST' else (not
first_half)`) and the census arithmetic (FIRST 11975 + SECOND 12330 = 24305
complementary) implement day>=16 for SECOND — the frozen text now matches
them. The corrected formula travels into the S freeze excerpts and the arm
identity hashes via the cascade re-freeze.

### F-6 (LOW) — §4 F5 fired-rate band supersession pinned

New manifest block `f5_fired_rate_supersession`: the measured per-config
fired rates REPLACE the [0.02, 0.10] bars/leg/day form before selection
(§4 F5 substitution clause), form evaluation recorded as FORM-only, fail-
closed population floors (pooled >= 30/fold) unaffected, plus all 33
configs' measured fold-3 rates from `p0/fired_census.json` and the three
census-walk-selected arms' rates printed for owner visibility:
MONTHPOS-SECOND-LONG 0.504263, OPEN-GAP-CONFIRM-Q50 0.903167,
VOL-DRIFT-MOM-L63 0.508404 bars/leg/day.

### F-7 (LOW) — 97 weekend-dated master bars explained

New manifest field `clock_contract.weekend_dated_master_bars_note`
(computed from `p0/calendar_census.json` before writing): the 97
weekend-dated bars (62 Saturday-dated + 35 Sunday-dated, all 2025..2026)
are vendor-served daily sessions under TD's 16:00-NY date-only stamp
convention in that window — accepted as-is under the frozen convention,
counted, never repaired or ffilled; CLOCK-COND weekday states (ISO 1..5
only) never fire on them; MONTHPOS/fold/warmup construction treats them as
ordinary sessions.

### F-8 (LOW) — explicit scored-cell budget counter

`adjudicate.py`: `SCORED_CELL_BUDGET_MAX = 3`; `adjudicate_cycle()` now
prints `scored_cell_budget {used, max, within_budget, source}` and treats a
breach as fail-closed; the pre-GO skeleton carries `{used: 0, max: 3}`.
(F-8's other half — `verify_positions_vs_freeze()` before any book — was
already wired in `i_engine.py` and is carried as GO condition C-2.)

## Deterministic digest re-pin cascade

The cascade ran TWICE, by construction, not by accident: the pass-1 rebuild
of the manifest re-ran `build_d1_manifest.py --selfcheck`, whose
fail-closed `load_p0()` verifies every digest in `p0_gate.json
artifact_sha256` — and the F-4-corrected `f1_repull_result.json` no longer
matched its recorded P0 digest. The gate was therefore re-assembled through
its own builder (`p0/assemble_gate.py`, offline, deterministic; F1(iii)
stays PASS_WITH_DISCLOSURE from the unchanged per-leg verdicts) and the
full cascade re-ran. FINAL values below are the pass-2 (current) ones.

1. `f1_repull.py` flag fix + offline `rederive` of `f1_repull_result.json`.
2. `p0/assemble_gate.py` re-run: gate PASS, F1 PASS_WITH_DISCLOSURE (per-leg
   evidence unchanged); `artifact_sha256` table refreshed; `measured_at_utc`
   refreshed (measured_* convention).
3. `build_d1_manifest.py` rebuild + `--selfcheck` PASS (extended checker
   now fail-closed-verifies the §4 F4 block, the F5 supersession rates and
   the weekend-bars note).
4. `s_select.py` manifest pin re-pointed (twice); walk re-run each time —
   census-determined outcome reproduced EXACTLY both times: same 3 arms,
   same order, same visits, UNCHANGED positions digests
   85c8f875… / 57eed8b9… / 7eee7cf0… (the GO condition C-2 digests), P-20
   matrix max |rho| 0.013307469016 unchanged; `--selfcheck` PASS (byte-exact
   walk reproduction). No WALK_DIVERGED.
5. `i/i_engine.py` FREEZE_SHA256 re-pinned to the final selection_freeze.json
   digest (0a936857… -> be83bbdf…).
6. `adjudicate.py` F-2/F-8 changes; `z_run.py` static-scan allowlist
   extended for the new DSR outcome-space statistics (classified
   METRIC_ON_PNL on the persisted P-11 series; state engines untouched).
7. `z_run.py` fresh run: 22/22 checks PASS, static suspects 0, dynamic
   NO_LEAK_FOUND; `--selfcheck` byte-identical PASS. The regenerated report
   pins the final freeze/engine digests.
8. Full test sweep re-run (see Tests below).

## Digest table (old -> new, sha256; NEW column = FINAL committed values)

| Artifact | Old (pre-remediation) | New (final) |
|---|---|---|
| p0/f1_repull.py (flag fix + rederive mode) | 8bab777a203df2d6970d79d177a19a41e111bbe8d500d506fae6a4cf7a65a909 | 5221be3495e0ac0e19f6ba02419301ddf2105839feeab3ad1158dce351c20f13 |
| p0/f1_repull_result.json (offline rederive; per-leg evidence byte-identical, flag false->true + f4_correction block) | 477a0e92e56903571aa9502254986d754b6463cebf744ea836ce13cb7d95dc5a | 68f63504bb856b473dce5ebc0a3defae2099b19fba44f19a6a94135a5bd00a83 |
| p0/p0_gate.json (re-assembled; refreshed f1_repull digest + measured_at_utc; verdicts unchanged) | dcbe8f23d1d8a6cfd1d9f69a80c49082dad6f5ad976f813d2e05ae8d4fab0aba | 01e42e53aff44496326f0fc7ec6dd10e8fccb7676dfab299da47e2e17d1ec3b2 |
| d1/build_d1_manifest.py (F-1/F-5/F-6/F-7 + extended selfcheck) | dde191f041fba0d9d00ec82819576f1a8bb7c36271b7dfd115c8f7e221d9812f | 3ee906bd5a4dfc1a57852f82c45300132f586e00b94409cd2e64f1e1a8f5b76c |
| d1/search_space_manifest.json (file) | 1b39aa6f726215df973833d1db5a8e3639aa226e62b7ce0f077c7e829c4d07b9 | 30e38a9935c3e2bc0080ef65709b998432e13db137280fc7134f397fd082bd65 |
| d1/search_space_manifest.json (self_sha256 convention) | 5db03cdba179d3713181fbb34638164a23e153b4706043836c611a4e7b8cfe33 | 4ca19c115505ed8e0f16c7d9307acbc67ab4a1b0b0bdc108997c9ca0e57b0649 |
| s/s_select.py (manifest pin, final) | ffc4154b90bc902c8c7d0f722e154767d8faf17cefa5796259c6f49b02b58aae | dcaae0c3878c63fbad1aa415e1d68451bd147a3fb197ca09d4679e34d370c217 |
| s/selection_freeze.json (re-frozen; walk identical, positions digests unchanged) | 0a93685758e0bb317633a9eb08f14ce66061314cc15a48bb262b6ae9b0130d74 | be83bbdf4f5dfee660cdacc42e41a882da535e9211954c6fd7bc3717acaafb8a |
| i/i_engine.py (FREEZE_SHA256 re-pin + F-2 constants context) | 4fe43df92fae1e945b22a89f8a72915da6941819f452c8f9176ff4da7c743068 | b935dcb4bcaf5b35c912d9180492aa91a831da96ac400cee789270d1d2c77ea9 |
| i/adjudicate.py (DSR + P-11 + F-8 budget + outcome gating) | 6862a417a86f366f2eaf16c5c36c9970b42dd0651977ba30517d7b0b308c17ad | 73350e6ad1d7ec852df88903536b2f7a9baa92208cef366214b65699d2764318 |
| z/z_run.py (scan allowlist for DSR outcome-space stats) | d6739a66307dcceb8cc8d0360010e811c6da90665eecbf888123fc2dad934af9 | e5abad1d4831b0fa43a439c8b7a09632960b5116d6993c03e2e60ad53228c05e |
| z/dry_run_report.json (regenerated) | 7edc70cc6244897106fad5bbb835c0033fbf3d6ad9188142c2d188ed902c5b45 | 842afe25740de819aaa738eca478c496e4d5e0a899396165e34700bab03196bf |
| z/leak_scan.json (regenerated) | 1073cd655394586969c29ae1fa8a5d0e064a1ca793e9e781f41807be184e2d32 | 544e45968e1b2832f71615290bd6406f8b32a8593d811ed2547979034511dc25 |
| m0/run_m0.py (core + extension runner) | c9f5f9aa3871d62d2764e61bf5fc763c95012391ab1b02d8fedcec95a2d1ac6e | 7a76182b770fa0bd025b052ef28237c4f7358eb01dd781f5dd3f3693621836ad |
| m0/test_m0_extension.py (NEW: G4N + dual-books fixture) | (new file) | f04c3ba3e058acb46d4a742a1ecb0b70014d3fc0dfeea9744e89a0934ea34edb |
| m0/m0_verdict.json (extended verdict) | b642da135bb840fdc2a20b1e063b028020fc52e6b73d912a3841ff13c9669e85 | see git blob (regenerated by run_m0.py) |
| tests/test_forex_search_v1_i.py (new DSR/P-11 tests; 27 -> 32) | e05dc67d2449a8e497632806a7a0726d41f7ef830183d1e57abac01c248e7f79 | see git blob |
| d1/d1_freeze_note.md (remediation addendum) | a3412013280480e1722d0bcf9f48a899d3f18348dc0925e70f7d8b1d5a667657 | see git blob |

Pass-1 intermediate values (superseded by the second cascade pass, recorded
for the trail): manifest file acc33f19…/self f6dfbc8e…; freeze 1065b464…;
i_engine 8a58a557….

Unchanged by design: `m0/test_m0_golden.py` (ba3991bd…), `m0/m0_contract.py`
(dad5de33…), `m0/contract_frozen.json` (8b5ee44b…), all other `p0/`
artifacts, `plans/`, `audits/`.

## Tests executed (this lane)

All commands run with `/Users/hoangminhlong/my-quantitative/.venv/bin/python`
from the worktree root; exit codes are the commands':

| Command | Exit | Verdict |
|---|---|---|
| `research/control/forex_search_v1_run/p0/f1_repull.py rederive` (offline) | 0 | flag false -> true, per-leg evidence byte-identical |
| `research/control/forex_search_v1_run/p0/assemble_gate.py` (gate re-assembly) | 0 | gate PASS; F1 PASS_WITH_DISCLOSURE (unchanged verdicts) |
| `research/control/forex_search_v1_run/d1/build_d1_manifest.py` (rebuild) | 0 | PASS |
| `research/control/forex_search_v1_run/d1/build_d1_manifest.py --selfcheck` | 0 | PASS |
| `research/control/forex_search_v1_run/s/s_select.py` (walk re-run) | 0 | PASS (arms identical, both passes) |
| `research/control/forex_search_v1_run/s/s_select.py --selfcheck` | 0 | PASS |
| `python -m pytest tests/test_forex_search_v1_i.py tests/test_forex_search_v1_p0.py -q` | 0 | 48 passed (32 + 16) |
| `research/control/forex_search_v1_run/m0/run_m0.py` | 0 | core 10/10 + extension 6/6, byte-exact |
| `research/control/forex_search_v1_run/z/z_run.py` (fresh) | 0 | 22/22 checks, NO_LEAK_FOUND |
| `research/control/forex_search_v1_run/z/z_run.py --selfcheck` | 0 | byte-identical payload |

## Limits / notes for the re-audit

* The DSR per-period basis is the frozen master calendar (flat sessions
  contribute 0.0 bps) — a deliberately conservative, documented convention;
  changing it requires an owner decision, not an in-cycle edit.
* E[max SR] uses the unit-variance normal-trials convention (the D1 freeze
  is outcome-blind; the other 30 configurations' SR variance does not exist
  pre-E). Documented in code (`DSR_LAW`) and in the subgate payload.
* The synthetic Z dry-run still ends REJECT_ALL on the synthetic books
  (R1 kill) — unchanged mechanic evidence; DSR is now computed inside
  Stage-A wherever Stage-A runs.
* GO conditions C-1..C-7 of the audit: C-1 items are remediated here
  (F-1/F-2/F-3/F-4/F-5 fixed; F-6/F-7 pinned in the manifest for the GO
  materials); C-2/C-3/C-4/C-5/C-6 remain binding at GO/E unchanged.
