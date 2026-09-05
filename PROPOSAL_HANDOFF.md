# PROPOSAL_HANDOFF — lane A5, cycle FOREX-FREE-V5, D1 blind proposal wave

```yaml
agent: A5_FOREX_V5_BLIND_LANE_AXIS2
lane: A5 (blind proposal lane, vintaged market-based real-rate axis / axis 2)
cycle: FOREX-FREE-V5
base_sha: e2b7a0e1e29794ca8449625f271f9a67c302fcf2
branch: orca/forex-free-v5-d1-a5-proposals
commit_sha: printed in the lane return as `git -C <worktree> rev-parse HEAD` immediately after the single semantic commit (a commit cannot contain its own sha — single-commit fixed-point constraint, same disclosure convention as the V4 A5 lane handoff)
commit_message_prefix: "FOREX-FREE-V5 D1 lane A5: ..."
changed_files:
  - PROPOSAL_FXFV5-A5-P1.json
  - PROPOSAL_FXFV5-A5-P2.json
  - PROPOSAL_HANDOFF.md
tests: none run (documentation lane) — no pytest invocation, no scored computation, no S0 data read; JSON well-formedness only (python json.load check, file hygiene, not a test)
tree_clean: true (verified `git status --porcelain` empty after the commit)
workers: 0
pushed: false
outcome_blind: true (both packets written before any FOREX-FREE-V5 scored outcome exists; no PnL, expectancy, fold statistic, or arm comparison for either hypothesis was computed or consulted)
```

## Files

| file | content |
|---|---|
| `PROPOSAL_FXFV5-A5-P1.json` | FXFV5-A5-P1 — breakeven-driven: vintaged US 10Y breakeven (T10YIE) 5-day shock continuation, daily 16:00-NY, **DATA_BLOCKED_VALID** |
| `PROPOSAL_FXFV5-A5-P2.json` | FXFV5-A5-P2 — real-yield-driven: vintaged TIPS real-curve slope (DFII5−DFII10) weekly-change drift, weekly clock, **DATA_BLOCKED_VALID** |
| `PROPOSAL_HANDOFF.md` | this handoff |

## Axis-2 determination (why both packets are DATA_BLOCKED_VALID, verbatim blockers, no softening)

`research/control/forex_free_v5_run/p0b_alfred_probe_verdict.json` (verdict **BLOCKED_DATA_AUTHORITY**, measured 2026-09-05T15:33:07Z) is cited verbatim in both packets:

- `deterministic_retrieval`: "FAIL - 1 success in 13+ attempts; channel fails the deterministic-retrieval data gate"
- `endpoint_semantics`: "NOT ESTABLISHED - alfredgraph.csv (vintage CSV) never returned bytes; the single fredgraph.csv success carried current data only (observation_date,value), no realtime/vintage column"
- `coverage_vs_S0`: "NOT MEASURABLE this host (no vintage payload retrievable)"
- `revision_behavior`: "NOT MEASURABLE this host"
- `license`: "LICENSE_UNVERIFIED_FAIL_CLOSED - legal/terms text unreachable from all channels; storage authorization cannot be granted without reading terms (handbook 11.4)"
- keyless API: "HTTP 400 'Variable api_key is not set' (host reachable, key required)"

Per lane instruction the mechanisms are proposed BLIND anyway (they define what WOULD be funded the moment the owner wires a key or network path); `data_availability` is `DATA_BLOCKED_VALID` in both; **no substitute data sources are proposed**; the pre-registered `real_differential` / `PPP_deviation` classes remain untouched (these two packets are new mechanisms on the same axis, not resurrections of those classes).

## Why the two mechanisms are materially different (not threshold neighbours)

| | P1 | P2 |
|---|---|---|
| market segment | inflation-expectations component (breakeven = nominal − real) | real component (TIPS real-yield term structure) |
| series | T10YIE | DFII5, DFII10 (+ DGS10 placebo-only) |
| statistic | 5-business-day CHANGE (shock) | weekly CHANGE of the curve SLOPE (structure) |
| clock | daily 16:00-NY | weekly (first completed 16:00-NY bar of the week) |
| hold | 3 sessions | 5 sessions, non-overlapping |
| causal control | vintage-shuffled placebo (must fail) | nominal-yield-level placebo (must fail; kills the carry-adjacent explanation in-run) |
| vintage-shuffle | control arm | I/Q availability-lag mutation test |

The only shared machinery is the inherited runner contract (one-event-lag, 16:00-NY bars, folds, dual books, stress tiers, gates).

## Carry-closure discipline (ex ante, binding)

The carry region is CLOSED at D2 by measured rho 0.997–1.000 vs both invalidated-ancestor variants. Both packets carry an explicit `decorrelation_from_carry_ex_ante` section: neither uses any policy-rate input; both are sign-FLIPPING change statistics (breakeven change; real-slope change) versus the ancestor's near-static differential level; and both pre-register the |rho| ≤ 0.20 measured Spearman bar vs BOTH V3 family2 anchor variants (as-scored and evidenced-corrected) AND vs the V4 family1 commodity-bloc anchor as a binding pre-selection kill-switch. P2 additionally carries the nominal-yield-level placebo as an in-run kill of the yield-level/carry explanation.

## Unblock conditions (owner actions only, never agent actions)

1. Owner signs up for a FRED API key (free) and places it in gitignored `.env` + owner license review of FRED/ALFRED terms for internal research storage (handbook 11.4); recorded owner option in the probe verdict ("api.stlouisfed.org was reachable from this host, so key-based PIT pull may work where graph CSV does not").
2. Owner-provided different network path / machine; probe re-run under the same evidence standard.

Evidence gate per proposal (successor P0b): deterministic retrieval ≥ 3/3 consecutive; per-row `realtime_start` vintage column verified from archived bytes; measured S0 coverage ≥ 99% of decision-clock bars; revision matrix across ≥ 2 vintages (the ONLY provable PIT check — mandatory, zero revisions ⇒ BLOCKED not scored); license text archived and storage authorized by owner. Any miss ⇒ stays DATA_BLOCKED_VALID.

## Known limitations (stated honestly)

1. Both families are UNRUNNABLE this cycle; the lane's output is two complete preregistrations plus blocker specifications — the sanctioned DATA_BLOCKED_VALID path, not a scored candidate.
2. All US-only conditioning (the vintaged series named by the axis are US series): the signal is common across the 7 pairs, so USD-index beta is a real kill risk; the runner-owned USD-drift gate is disclosed as a probable kill, not engineered around.
3. Expected decision counts are bands conditioned on the unwired ALFRED path; realized counts below the frozen floor record the gate, never a rescore.
4. The D2 novelty rho claim is an ex-ante expectation, not evidence — the measured bar decides, not the prose.
5. `commit_sha` cannot be embedded in a file inside the commit it names (fixed-point impossibility); it is `git rev-parse HEAD` on this branch after the single lane commit and is printed in the lane return.
6. Tests: none run (documentation lane) — no pytest, no scored computation, no network fetch, no key/signup attempt, no S1 access.

## Outcome-blind attestation

Both packets were designed before any FOREX-FREE-V5 outcome exists for the vintaged market-based real-rate axis. No S0 price read, no macro read, no scored computation, and no arm comparison informed either packet; every performance statement is an ex-ante prior; both packets would be byte-identical if every cell in the program's history had scored zero.

signed: A5_FOREX_V5_BLIND_LANE_AXIS2 — 2026-09-05T16:08:06Z
