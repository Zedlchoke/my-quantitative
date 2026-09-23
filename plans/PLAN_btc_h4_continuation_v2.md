# PLAN BTC-H4-CONTINUATION-V2 — forensic causal origin + at-most-one upgrade of the PSV1 BTC_H4 Donchian-continuation arm

> Status: `PLANNED_NOT_STARTED`. Owner instruction 2026-09-23 explicitly
> authorizes this successor cycle to investigate and attempt to upgrade
> `PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION`. PHASE-STRATEGY-V1 closed
> TERMINAL `PHASE_STRATEGY_V1_NO_INCREMENTAL_VALUE`. EVERYTHING here is
> POST-HOC S0 DISCOVERY: the entire 2020–2026 history has been seen; every
> number this cycle can produce is post-hoc, never OOS, never validation.
> Ceiling verdict (exact string):
> `POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION`. NOT a rescue
> cycle and NOT a parameter sweep: no PSV1 artifact mutated, no fold edge
> moves, no new data source, no threshold chosen on fold PnL.
> S1 `SEALED_UNTOUCHED`. No paper/live/orders.

## 0. Cycle identity

```text
cycle_id     BTC-H4-CONTINUATION-V2
asset        crypto (single cell BTC_H4: BTCUSDT-PERP, H4 grid)
class        POSTHOC S0 DISCOVERY (see header). No promotion to shadow,
             paper or live — ever. A passing candidate earns only a
             prospective-validation successor cycle.
question     (i) FORENSIC: identify the MEASURED causal origin of the F2/F4
             losses vs F1/F3 gains of PSV1-BTC_H4-UPTREND-DONCHIAN_
             CONTINUATION (same metric set for all folds, §1.2).
             (ii) UPGRADE: test AT MOST ONE strategy change with an
             explicit economic mechanism and a PIT-observable input.
             NO_ELIGIBLE_PROPOSAL — closing with zero scored candidates —
             is FIRST-CLASS: do not manufacture a backtest.
inputs       SAME BTC_H4 panel only. Pinned manifest sha256
             3f1a668798c82fbfe7311fadf65a300a583043cdbeba226164bd28c81885b66d
             (Binance Vision keyless USDT-M klines; H4 bucket =
             floor(open/4h) UTC; complete iff 4 aligned H1 bars). PIT
             unchanged: decision at H4 close, first fill next H4 open, no
             intra-bar lookahead; Vision klines are retrospective exchange
             snapshots (retrieved 2026-09, disclosed). Costs: 6 bps/side
             full-stack fees + funding 1.377e-5 per 8h signed at 8h
             boundaries; tiers 1.0x/1.5x/2.0x; capital $100,000, fraction
             1.0. NO new data source — one would need its own data gate +
             PIT + license audit; OUT of scope this cycle.
folds        FROZEN: F1 2020-01-01→2021-04-30 · F2 2021-05-01→2022-12-31 ·
             F3 2023-01-01→2024-12-31 · F4 2025-01-01→data end. Ends
             force-flat; warmup truncated per PSV1 lane convention;
             L1_FOLD_EDGES = ["2021-05-01","2023-01-01","2025-01-01"].
budget       max 2 scored arms = CANDIDATE + ABLATION. COMPARATOR and all
             controls/baselines are reference computations inside the
             scored run, not budget cells (§3).
s1           SEALED_UNTOUCHED
orders       NONE (no broker/paper/testnet/live surface anywhere; no API keys)
go_phrase    GO BTC H4 CONTINUATION V2 DISCOVERY SCORED
             (STOP-1 gate, §6; this prompt session is NOT a GO)
predecessor  PHASE-STRATEGY-V1 TERMINAL
             PHASE_STRATEGY_V1_NO_INCREMENTAL_VALUE; anchor
             af52f3582270bcc19634add3d88858e0c28959bf, branch
             orca/phase-strategy-v1-integration. PSV1 artifacts
             byte-untouched; verdict never reopened here.
forbidden    choosing any threshold/parameter by scanning PnL on F2/F4 or
             any fold (§2); "bad year" labels or post-trade future
             information in trade logic; new data sources; moving or
             excluding folds to flatter results; reopening the PSV1
             verdict; >1 change vs COMPARATOR per arm; parameter rescue
             after candidate PnL is visible; mid-run stop on ugly numbers.
```

## 1. Forensic phase (P1) — measured causal origin of the fold split

Predecessor scored record (MEASURED, committed PSV1 artifacts; facts to investigate, not targets):

```text
arm            PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION (Donchian-
               continuation long book gated by a code-owned PIT UPTREND
               phase label, BTCUSDT-PERP H4, Binance Vision data)
net @1.0x      +177,691.82 USD on $100,000 capital; max_drawdown −0.2936
trades         86 entries / 86 exits (79 DONCHIAN_STOP, 7 GATE_INACTIVE);
               median hold 23 H4 bars
folds          F1 +140,843.28 | F2 −46,959.99 | F3 +133,820.83 |
               F4 −50,012.30; fold_concentration 0.5128
gates          G1 PASS · G2 PASS (+161,531.83 @1.5x) · G3 FAIL (loses to
               baselines: ALWAYS_ON_TREND_LF +1,278,270.73, ALWAYS_ON_LONG
               +814,203.60, SPARSE_RISK_OFF +99,457.04 @1.0x) · G4 PASS
               (best-fold-removed > 0) · G5 FAIL (0.5128 > 0.50) · G6
               KILLED (block-shuffled gate placebo +190,391.51 > candidate
               — TIMING carried no information) · G7 PASS · G8 repro
               byte-identical 5/5 · G9 A7 terminal clean (0 HIGH/CRITICAL)
```

### 1.1 Rebuild + HARD reconciliation gate (blocking)

P1 rebuilds the original arm's per-trade ledger from the FROZEN PSV1
engine code: forensic code lives in the cycle worktree and imports the
PSV1 lane machines verbatim from `.worktrees/phase-strategy-v1/integration`
at terminal anchor af52f358…; data staging dirs are the PSV1 lanes' (same
bytes, same manifest digests). Per-fold net sums, entries/exits counts,
exit-reason counts, and gross/fees/funding totals at 1.0x/1.5x/2.0x MUST
match the committed PSV1 `scored_ledger.json` (schema
`psv1_scored_ledger@1`) within 1e-6 relative. ANY mismatch ⇒ `TECHABORT` —
no filter research on a broken rebuild.

### 1.2 F2/F4 vs F1/F3 comparison metrics (identical set for all four folds)

- trade count; hit rate; avg win / avg loss;
- gross / fees / funding per fold; funding drag share of gross;
- MFE / MAE distributions; hold-time distribution;
- DONCHIAN_STOP fraction; failed-breakout rate (stop within k = 6 H4 bars
  of entry; k fixed a priori = the original 12-bar min-hold halved —
  disclosed as an a-priori DESCRIPTIVE constant, NOT tuned);
- realized vol / trend slope / drawdown-from-rolling-high AT decision time
  (PIT fields computed as-of the entry decision bar).

### 1.3 Min-hold law audit (measured, not assumed)

From the frozen code: does the 12-bar min-hold delay DONCHIAN_STOP exits,
and how many stops were delayed (count + bar distribution)? A POST-HOC-
DESCRIPTIVE-ONLY counterfactual (immediate-stop net impact) is computed
and reported — NEVER an input to the proposal, NEVER optimized over.

## 2. Anti-overfitting law (owner-ordered; binds every phase)

- NO threshold or parameter may be chosen by scanning PnL on F2/F4 or any
  fold. No "bad year" label and no post-trade future information may enter
  trade logic.
- Candidate selection is by economic mechanism + PIT observability ONLY,
  decided BEFORE any candidate PnL exists.
- The original arm's PnL is already known and disclosed (§1) — that
  exposure IS the POSTHOC risk this plan manages, via: ONE pre-registered
  candidate; frozen ABLATION + COMPARATOR + controls; full same-window
  scoring over ALL folds; no fold exclusion; verdict ceiling
  POSTHOC_DISCOVERY; mandatory G10 disclosure of the F1/F3 cost paid for
  any F2/F4 improvement.

## 3. Arms

```text
COMPARATOR  PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION re-run UNCHANGED
            (reference anchor for every delta; not a budget cell).
CANDIDATE   COMPARATOR + EXACTLY ONE change: registered economic
            mechanism, PIT-observable input, round frozen parameters with
            a stated NON-PnL rationale (mechanism or domain convention).
ABLATION    CANDIDATE with the single change removed. MUST reproduce
            COMPARATOR behavior; identity check vs the COMPARATOR ledger
            is required (ablation identity gate).
controls    reference computations, not budget cells:
            - PLACEBO-30BAR-BLOCKSHUFFLE on the candidate's gate/entry
              series (PSV1 CTL-BLOCKSHUFFLE semantics; movement
              validation entries >= 50%);
            - CASH; ALWAYS_ON_LONG; ALWAYS_ON_TREND_LF (SMA200 on the H4
              grid); SPARSE_RISK_OFF (flat while trailing drawdown > 30%
              from running high, re-enter <= 10%, min-hold 5 bars) — the
              four PSV1 §8 baseline definitions VERBATIM.
```

Same engine, same capital ($100,000, fraction 1.0), same execution, same
folds, same cost tiers — for every arm and every control.

## 4. Gates (per candidate; ALL must PASS)

G1–G9 thresholds identical to PSV1 §16.3:

```text
G1  net > 0 at 1.0x costs
G2  net > 0 at 1.5x costs
G3  beats ALL four §3 frozen baselines at 1.0x
G4  fold robustness: positive in ≥3/4 folds OR best-fold-removed net > 0
G5  no single fold contributes >50% of positive net
    (fold_concentration ≤ 0.50)
G6  preregistered PLACEBO-30BAR-BLOCKSHUFFLE must NOT out-earn the
    candidate (out-earn ⇒ kill; null control ⇒ disclosed, rest on G1–G5)
G7  turnover within frozen ceiling; zero unnecessary close-reopen
G8  reproduction byte-match (P5)
G9  A7 terminal clean (0 unresolved HIGH/CRITICAL)
G10 FOLD-TRADE-OFF DISCLOSURE (preregistered NOW, before any candidate
    run): at 1.0x report Δ(F2)+Δ(F4) improvement AND Δ(F1)+Δ(F3) cost vs
    COMPARATOR; improving F2+F4 by destroying F1+F3 is not an upgrade.
    Fixed now: (a) combined net MUST increase vs COMPARATOR; (b) NO fold
    may flip positive→negative vs COMPARATOR. Qualitative gate.
```

ALL-PASS ⇒ ceiling verdict
`BTC_H4_CONTINUATION_V2_POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION`
(never OOS, never deployable, no orders).

## 5. Ancestry law

- The named ancestor `PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION` is
  OWNER-WAIVED this cycle (owner instruction 2026-09-23 names it): high
  signal-correlation with the ancestor is EXPECTED (candidate = comparator
  + one change) and is NOT a veto.
- ALL other PSV1 §7.2 crypto dead shadows apply on the candidate's entry
  signal series; pass requires |rho| ≤ 0.20, EXCEEDS ⇒ vetoed:
  close-displace-fade; rev24 short-horizon reversal per-leg; run_imbalance;
  amihud-illiquidity proxy; OI-level and OI-share/stoch; generic DVOL
  shock; pair spread-trend composites.
- rho is measured PRE-PnL from signal information content (PSV1 D2
  convention), recorded in the P2 freeze; A1 re-measures at freeze.

## 6. Cycle phases and verdicts

```text
P0    intake: this plan -> registry hygiene (researchctl) -> PSV1
      two-half close verified (TERMINAL; artifacts byte-untouched).
P1    forensics (§1) in the cycle worktree; §1.1 reconciliation gate is
      blocking (mismatch ⇒ TECHABORT).
P2    proposal + freeze: arms/cells/gates/digests committed BEFORE any
      candidate PnL exists; family_id naming frozen here.
P3    implement + targeted tests + hand-computed fixtures (lookahead
      mutation; next-bar fill; funding sign/cadence; stop/min-hold; fold
      force-flat; cost-tier exactness 1.0/1.5/2.0; no-op churn) +
      sanitized dry-run (no PnL, non-vacuous, distinct IDs) + A7
      prelaunch fresh-context independent audit.
STOP-1 OWNER GATE: report the frozen candidate + controls + cell count +
      POSTHOC risk + the exact GO phrase. The owner types, at this gate,
      verbatim: GO BTC H4 CONTINUATION V2 DISCOVERY SCORED. No other
      phrase consumes; the dispatching prompt is NOT a GO.
P4    scored run: full frozen denominator under the machine-wide heavy
      lock; no mid-run stop on ugly numbers; no parameter edit after PnL.
P5    independent reproduction byte-match + A7 terminal fresh-context.
P6    two-half close; verdict exactly one of §6.1.
```

### 6.1 Terminal verdicts (exactly one)

```text
BTC_H4_CONTINUATION_V2_POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION
BTC_H4_CONTINUATION_V2_NO_INCREMENTAL_VALUE
BTC_H4_CONTINUATION_V2_NO_ELIGIBLE_PROPOSAL
BTC_H4_CONTINUATION_V2_BLOCKED_DATA_OR_SELECTION
TECHABORT
```

`BTC_H4_CONTINUATION_V2_NO_ELIGIBLE_PROPOSAL` (P1/P2 closes with no scored
candidate) is first-class.

## 7. Trial identity and denominators

Every scored arm carries: cycle_id BTC-H4-CONTINUATION-V2; cell BTC_H4;
family_id V2-<MECH> (naming frozen at P2); arm_id; arm_config_digest; data
manifest digest 3f1a6687…; code_freeze_sha; cost_tier; fold contract. The
observed denominator counts EVERY computed arm×tier (publication failures
included); the published denominator counts successes only; both reported
at every checkpoint. Budget cells: CANDIDATE + ABLATION only.

## 8. Boundaries

Worktree `.worktrees/btc-h4-continuation-v2/integration`, branch
`orca/btc-h4-continuation-v2-integration`; base = PSV1 terminal anchor
af52f3582270bcc19634add3d88858e0c28959bf (frozen engine inherited
verbatim). Registry only via researchctl/governance. Machine-wide heavy
lock for scored AND forensic compute (light <5 min CPU / <2 GB exempt);
never kill a foreign worker. No push from lanes; no merge to main without
owner. S1 sealed. No broker/paper/testnet/live surface, no orders, no API
keys, no credentials in logs; `git add -A` forbidden. V2 artifacts live
under `research/control/btc_h4_continuation_v2/` in the cycle worktree;
PSV1 artifacts byte-untouched; root checkout is bootstrap/owner space.
Turn-scope: pre-GO turns may rebuild, test, census, freeze, audit — not
run the scored backtest.

## 9. Amendments log

None yet. Amendments must be pre-outcome (before P4), dated, attributed,
and must not touch folds, tiers, gates or the verdict ceiling.
