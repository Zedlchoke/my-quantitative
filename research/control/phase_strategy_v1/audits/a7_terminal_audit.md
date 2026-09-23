# A7 TERMINAL AUDIT — PHASE-STRATEGY-V1

- Schema: `psv1_a7_terminal_audit@1` (machine-readable twin: `a7_terminal_audit.json`)
- Auditor: A7 terminal, fresh context, independent
- Audited: evidence head `17a1bea5` (this worktree, `orca/psv1-a7-terminal`); scored code
  state `a9c8a67c` (verified: `git diff a9c8a67c..17a1bea5` touches only
  `runtime/scored/*` evidence); code freeze declared in ledger `8865e7d3`
- Measured: 2026-09-23T10:38:17Z
- **TERMINAL VERDICT: `PHASE_STRATEGY_V1_NO_INCREMENTAL_VALUE`**

## 1. What was recomputed from bytes and source

| # | Check | Verdict | Margin |
|---|---|---|---|
| C1 | Chain: plan `c6d80a9f` → wave `6e6ffa3b` → lanes `88a42ed5/c8ea871b`, `8a427571`, `4c17b7f4/48388fbf` → amendment `eaef65d6` → freeze `4b7eae34` → A7 r1 `991b4e02` → remediation `458d8aa3`/`75765be2`/`a7d355db`/`8865e7d3` → A7 r2 `bbc5a778` → engine `b4246ac7` → code `a9c8a67c` → evidence `17a1bea5` | PASS | 18/18 resolve, subjects match roles |
| C2 | GO law: r2 AUTHORIZED 09:28:37Z → owner typed verbatim `GO PHASE STRATEGY V1 SCORED EXECUTION` at the cycle's own gate 09:38:00Z → `ACTIVE_HEAVY` (events journal lines 781/783/784) | PASS | phrase exact; ordering correct |
| C3 | Auditor re-ran the scored engine (`run_scored.py --mode scored`, WITHOUT the lock wrapper — heavy-lock discipline already discharged by primary+twin; lock inspected FREE_PROVEN before launch): `scored_ledger.json` + 3 tier files **BYTE-IDENTICAL 5/5** to the committed primary | PASS | G8 independently reproduced (3rd run) |
| C4 | Ingest verification: committed 284/284 re-downloaded, 0 mismatch, fail-closed code verified; auditor sampled 12/12 staged-file digests MATCH; SPY snapshot MATCH; 80/80 cross-manifest period digests agree; zip→parquet chain exact (L1 2024-03 max diff 0.0; L2 native-4h 2023-05 186/186 rows max diff 0.0); 58,968 H1 bars / 14,742 H4 buckets = freeze claims | PASS | 0 drift anywhere |
| C5 | Gates G1–G7 recomputed for all 4 candidates with auditor-owned arithmetic | PASS | every ledger gate field matches; `candidates_passing_G1_G7: []` CONFIRMED on the merits |
| C6 | Identities: `net = gross − fees + funding` ≤ 8.5e-10 everywhere; `Σ fold_net = net` exact; concentrations equal to 6dp; funding signs correct | PASS | exact |
| C7 | Adversarial: BTC_H4 `ALWAYS_ON_TREND_LF` +1.278M re-implemented from scratch → 1,264,374 (−1.09%; fold force-flat + warmup conventions) — genuine BTC beta, not an engine bug | PASS | −1.09% explained |
| C8 | BTC_H4 fold-0 dominance +140,843 (ERA-B1 bull): real, G5 FAIL recorded correctly (0.5128 > 0.50), and neutralized by the G6 block-shuffle KILL | PASS | kill margin +7.1% |
| C9 | Denominator 52 = 4×3 + 12×3 + 4; budget 4 ≤ 4 expected ≤ 15; trial identity present | PASS | 52/52, 4/15 |
| C10 | Boundaries: forbidden predecessor artifacts appear ONLY in guard deny-lists/hygiene tests; broker/order tokens ONLY in FORBIDDEN lists; S1 never touched by scored/lane runtime code | PASS | 0 non-guard hits |
| C11 | Registry: events journal authoritative and correct; projection fields (`go_phrase_state`, `budget.used=0`, `head=8865e7d3`) lag → **expected-closeout** (A1's step), not a defect | PASS | see T-I1 |
| C12 | `scored/tests_py` standalone: 10/10 green | PASS | 10/10 |

## 2. Gate table (auditor recompute @1.0x)

| Candidate | net | G1 | G2 | G3 | G4 | G5 | G6 | G7 |
|---|---|---|---|---|---|---|---|---|
| BTC_H1 UPTREND | +89,636.78 | ✓ | ✓ | ✗ (loses to AOL 429,476 / TREND 167,350) | ✗ (2/4 folds; BFR −21,219) | ✗ (0.854) | PASS (ctl 40,627) | ✓ |
| BTC_H1 ACC | +45,744.31 | ✓ | ✓ | ✗ | ✓ (BFR +5,970) | ✗ (0.550) | PASS (ctl −61,339) | ✓ |
| BTC_H1 DOWNTREND | −44,485.96 | ✗ | ✗ | ✗ | ✗ | ✗ (1.000) | **KILLED** (ctl −25,948) | ✓ |
| BTC_H4 DONCHIAN | +177,691.82 | ✓ | ✓ | ✗ (loses to AOL 814,204 / TREND 1,278,271) | ✓ (BFR +36,849) | ✗ (0.513) | **KILLED** (block-shuffle 190,392) | ✓ |

Controls' kill law verified exactly: BTC_H4 190,391.51 > 177,691.82 → KILL;
BTC_H1 DOWNTREND shuffled median −25,947.50 > −44,485.96 → KILL; UPTREND
40,626.91 ≤ 89,636.78 → PASS; ACC clock-only −61,339 ≤ +45,744 → PASS.

## 3. Findings

**HIGH/CRITICAL: none. MEDIUM: none. Blocking: none.**

- **LOW T-L1** — `run_scored.py` serializes G1/G2/G5 gate values as strings
  (`"True"`) while G3/G4/G6/G7 serialize as booleans (numpy lineage via
  `default=str`). The `candidates_passing_G1_G7` filter `v in (True, "PASS", …)`
  would not match `"True"` — a latent **false-negative** (conservative) bias in
  the pass list. Non-outcome-affecting here: my own arithmetic confirms all
  failures are substantive (G3 fails 4/4, G5 fails 4/4, G6 kills 2, G1/G2 fail 1,
  G4 fails 1). Recorded for any successor cycle that reuses the engine.
- **INFO T-I1** — Registry projection lag (`go_phrase_state`, `budget.used=0`,
  `head=8865e7d3`): expected-closeout, events journal authoritative.
- **INFO T-I2** — OWNERSHIP_MANIFEST `a7` slot lacks a terminal-round entry
  (bookkeeping lag only).
- **INFO T-I3** — Frozen full-stack tier law scales funding with the tier, so
  the funding-receiving DOWNTREND short improves (−44,486 → −42,828) rather
  than degrades at 2.0x. Frozen, disclosed, gate-irrelevant (fails G1 at 1.0x).
- **INFO T-I4** — Gross varies across tiers because accruals are
  equity-proportional under compounding; identity still holds ≤8.5e-10.

### Carried findings adjudication (all NO_ESCALATION)

- **A7-I6** (SPY fold-truncated episode convention): no SPY candidates exist → nothing to escalate.
- **A7-I7** (per-lane pytest): scored harness runs standalone, 10/10 green.
- **A7-I8** (dual amendment commit): re-verified byte-identical plan bytes (`git diff eaef65d6 b75f35f7` on the plan path is empty).
- **A7-I9** (§7.1 breadth): scored-arm geometry (median holds 108/117/118 H1 bars, 23 H4 bars; structure-stop-dominant exits) matches the recorded event-conditional-book arguments, not the forbidden continuous-regime specialists; G6 controls directly tested gate informativeness and killed what deserved killing. No predecessor artifact opened (C10).
- **A7-R2-I1 / R2-I2**: shadow construction/window conventions — immaterial (worst rho +0.168 vs 0.20 bar).

## 4. Verdict

**`PHASE_STRATEGY_V1_NO_INCREMENTAL_VALUE`** (plan §18).

Candidates existed (4, frozen pre-PnL), all were scored (full denominator, no
mid-run stop), and all fail G1–G7 on the merits. The best candidate
(BTC_H4 Donchian, +177,692 @1.0x) is killed by its own preregistered control,
loses G3 to a plain SMA200 long/flat baseline by 7.2x, and fails G5 by 2.6pp.
Phase gating adds no demonstrated incremental value after costs. G8 PASS
(auditor run byte-identical 5/5); G9 PASS (0 unresolved HIGH/CRITICAL).
SPY_D1 zero-eligible is a cell-level `NO_ELIGIBLE_PROPOSAL` result inside this
verdict, not the cycle label. Per §2, nothing here is OOS or deployable; no
orders exist or may follow.
