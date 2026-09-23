# PLAN BTC-H4-TWO-REGIME-V1 — three-state BULL/BEAR/UNCERTAIN router over the frozen PSV1 BTC_H4 Donchian long leg + a mechanism-backed DOWN leg candidate

> Status: `PLANNED_NOT_STARTED`. Owner instruction 2026-09-23 explicitly
> authorizes this successor cycle: a causal three-state regime system where
> (1) BULL-with-evidence permits the frozen PSV1 BTC_H4 Donchian long arm,
> (2) BEAR-with-evidence permits ONE NEW downtrend leg with its own economic
> mechanism and PIT data, (3) UNCERTAIN/TRANSITION is FLAT. The question is
> whether this system REDUCES the measured F2/F4 losses without DESTROYING
> the F1/F3 gains, after real costs and against controls. No goal of
> "erasing losses" by memorizing history. EVERYTHING here is POST-HOC S0
> DISCOVERY: 2020–2026 is outcome-observed; every number this cycle can
> produce is post-hoc, never OOS, never validation. Ceiling verdict (exact
> string) `POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION`.
> NOT a rescue cycle, NOT a rename of RSM-V1/V2/PSV1 classes, NOT a
> parameter sweep. S1 `SEALED_UNTOUCHED`. No paper/live/orders.

## 0. Cycle identity

```text
cycle_id     BTC-H4-TWO-REGIME-V1
asset        crypto (single cell BTC_H4: BTCUSDT-PERP, H4 grid)
class        POSTHOC S0 DISCOVERY. A passing candidate earns only a
             prospective-validation successor cycle. No shadow/paper/live.
question     (i) DETECTOR: does a causal, PIT, hysteresis BULL/BEAR/
             UNCERTAIN state machine — designed with NO access to fold PnL,
             no year labels, no future peaks/troughs — actually recognize
             bear states in time, measured by transition counts, detection
             lag (descriptive), and independent-episode samples?
             (ii) SYSTEM: does the router (BULL->long / BEAR->down /
             UNCERTAIN->flat) reduce F2+F4 losses without killing F1+F3 vs
             the ungated arm and all baselines — or does it win only by
             trading less?
             NO_ELIGIBLE_PROPOSAL (closing with zero scored candidates:
             no PIT-verifiable detector, no floors-passing state, or no
             eligible DOWN leg) is FIRST-CLASS. Do not force a router.
inputs       PRIMARY: SAME frozen BTC_H4 panel only. Pinned manifest sha256
             3f1a668798c82fbfe7311fadf65a300a583043cdbeba226164bd28c81885b66d
             (Binance Vision keyless USDT-M klines; H4 bucket = floor(open/4h)
             UTC; PIT: decision at H4 close, first fill next H4 open).
             NEW-STREAM door (owner-authorized, gated): Binance Vision
             monthly fundingRate (BEAR-leg observables only) — MEASURED
             available 2020-01..2026-08 by the owner recon probe
             (research/control/bear_opportunity_recon_2026-09/data_a2/
             data_inventory.json: HTTP 200, sha-pinned, deterministic
             re-retrieval byte-identical). liquidationSnapshot / metrics /
             bookTicker / bookDepth measured 404 = UNAVAILABLE_FAIL_CLOSED.
             Any stream admitted under this door must still pass its own
             license/coverage/PIT/data-gate audit before eligibility.
             Costs: 6 bps/side full stack + funding 1.377e-5 per 8h signed
             at 8h boundaries; tiers 1.0x/1.5x/2.0x; capital $100,000,
             fraction 1.0 (PSV1 frozen cost law, unchanged).
folds        FROZEN (identical to PSV1/V2): F1 2020-01-01->2021-04-30 ·
             F2 2021-05-01->2022-12-31 · F3 2023-01-01->2024-12-31 ·
             F4 2025-01-01->data end. Ends force-flat; warmup truncated per
             PSV1 lane convention (153 H4 bars);
             L1_FOLD_EDGES = ["2021-05-01","2023-01-01","2025-01-01"].
budget       max 4 scored arms = {B, C, D, ABLATION}. A (COMPARATOR) and all
             E-controls are reference computations inside the scored run,
             not budget cells. If C closes NO_ELIGIBLE, D is not built and
             the cycle closes at P2 (STOP-1 moot) — B alone is NOT scored
             (a state-gated long-only book without the DOWN leg is exactly
             the gate-timing class PSV1 G6-killed; scoring it alone would be
             a forced router, owner-forbidden).
s1           SEALED_UNTOUCHED
orders       NONE (no broker/paper/testnet/live surface anywhere; no API keys)
go_phrase    GO BTC H4 TWO REGIME V1 SCORED EXECUTION
             (STOP-1 gate, §7; the dispatching prompt is NOT a GO)
predecessors PHASE-STRATEGY-V1 TERMINAL
             PHASE_STRATEGY_V1_NO_INCREMENTAL_VALUE (anchor af52f3582270bcc1
             9634add3d88858e0c28959bf, branch orca/phase-strategy-v1-
             integration); BTC-H4-CONTINUATION-V2 TERMINAL
             BTC_H4_CONTINUATION_V2_NO_ELIGIBLE_PROPOSAL (head c390375eafa6
             03701e8818b504df5b706e9c275e). Both byte-untouched.
             THE OLD BUY LEG FAILED G3/G5/G6: it is a TEST COMPONENT under
             measurement here, never a certified strategy.
forbidden     choosing any detector constant or DOWN-leg parameter by
             scanning fold PnL; F2/F4 labels, per-fold PnL, trade outcomes,
             future tops/bottoms, or "bad year" tags anywhere in detector or
             leg logic; reopening the PSV1/V2 verdicts; mutating any PSV1/V2
             artifact; renaming dead families to retry them (breakdown-short,
             OI-cascade, short-horizon reversal, basis-fade, RSM-V1
             specialist library — see §5.3); relaxing the §1.4 floors after
             any PnL; moving/excluding folds; mid-run stop on ugly numbers;
             git add -A.
```

## 1. The three-state detector (P1 contract — frozen BEFORE any census)

The hardest problem is knowing the state WHILE LIVING. The machine below is
preregistered now: every constant is round, with a stated provenance, fixed
before any state-conditional number exists. It may be killed by the census;
it may not be tuned.

### 1.1 Observable (causal; H4 close grid)

```text
runmax_t  = max(close_0 .. close_t)          running maximum over the staged
                                             panel (panel starts 2020-01-01;
                                             NO pre-2020 ATH anchor —
                                             disclosed: a true-ATH anchor
                                             would pin 2020–2023 non-BULL by
                                             construction and is not used)
dd_t      = close_t / runmax_t - 1           (<= 0)
```

### 1.2 Constants (round; provenance)

```text
DD_BEAR    = -0.30   enter BEAR at a 30% drawdown from the running high —
                     the PSV1 SPARSE_RISK_OFF frozen flat threshold (§8
                     baseline constant already in the program; round domain
                     convention; NOT chosen on any PnL)
DD_RECOVER = -0.10   recovery band — the PSV1 SPARSE_RISK_OFF frozen
                     re-entry threshold (same provenance law)
BULL_DWELL = 90 H4 bars (= 15 days) sustained-recovery confirmation; round;
                     its only purpose is the owner-mandated discrimination:
                     a REBOUND inside a big bear must NOT read as BULL
```

### 1.3 State machine (evaluated at every H4 close t, in this order)

```text
initial state: UNCERTAIN (warmup/truncated bars included; window opens
               2020-01-26 12:00 UTC post-warmup in UNCERTAIN)
1) dd_t <= DD_BEAR                        -> BEAR      (from ANY state;
                                            immediate: the drawdown itself is
                                            the evidence; no dwell confirm)
2) state==BEAR and dd_t >= DD_RECOVER     -> UNCERTAIN (first recovery bar:
                                            recovery attempt, UNCONFIRMED)
3) state==UNCERTAIN and dd >= DD_RECOVER
   sustained for BULL_DWELL consecutive
   bars (global streak; any dd < -0.10 bar
   resets it)                             -> BULL      (sustained recovery:
                                            the only path to BULL)
4) otherwise hold state.

BULL persistence: NO exit to UNCERTAIN (preregistered: shallow corrections
do not revoke bull evidence; BULL exits only via rule 1).
UNCERTAIN: no timeout; dd between the bands persists indefinitely.
```

Resulting semantics: BEAR = deep-drawdown evidence; UNCERTAIN = recovery
attempt not yet sustained (where "BTC hồi lên trong bear lớn" lives — FLAT);
BULL = sustained recovery confirmed by dwell. Hysteresis = the 30/10 bands
plus the 90-bar dwell. Detection lag is an HONEST OUTPUT (reported vs the
public calendar anchors top 2021-04 / bottom 2022-12, DESCRIPTIVE ONLY,
never a rule input), not a design target.

Sensitivity ladder (label-agreement % only; REPORTED, NEVER optimized):
DD_BEAR {-0.25,-0.30,-0.35} x DD_RECOVER {-0.05,-0.10,-0.15} x
BULL_DWELL {60,90,120}.

### 1.4 Census contract (counts only; NO strategy PnL anywhere in P1)

Per state (BULL/BEAR/UNCERTAIN) over the post-warmup window, per fold and
total: occupancy share; raw runs; merged independent episodes (merge two
adjacent same-state runs iff the gap is < 12 H4 bars — recon convention);
dwell distribution; transition counts (state-pair matrix); detection lag vs
the two calendar anchors (bars, descriptive); margin-to-floor per state
(per §1.5); the §1.2 sensitivity ladder agreement table; and the audits:

- vs the OLD PSV1 UPTREND phase label (code-owned label imported verbatim
  read-only): agreement % + contingency matrix. The cycle premise requires
  the new BULL law to be a DIFFERENT rule (different observable family:
  drawdown-hysteresis vs SMA-slope quadrants); identity or near-identity is
  reported and is itself ancestry evidence.
- vs the SMA200(H4) lens (close > SMA200): agreement % + contingency; the
  V2 forensic fact is carried: the SMA200 gate bound 0/86 entry bars and is
  an ineffective gate — the census must show what the new law does and does
  NOT share with it.
- no-lookahead mutation fixture: perturbing any future bar must not change
  any past state; hysteresis fixtures: a rebound that fails the dwell stays
  non-BULL; a 30% break enters BEAR immediately from BULL.

### 1.5 Sample floors (PSV1 §4.3, IMMUTABLE, owner-confirmed; never relaxed)

```text
>= 20 merged independent episodes / state / cell (total);
>=  3 raw episodes (fold-clipped)  / state / outer fold;
>= 100 state-true decision bars    / state / outer fold.
```

Application: a state gate that fails ANY floor makes every arm gated on it
`NOT_RUN_THIN` (slot FLAT, reported, never scored). Floors are never
relaxed after any PnL (owner law: "Mẫu mỏng -> NOT_RUN, không nới floor sau
PnL"). Expected-outcome note, preregistered: a hysteresis machine on one
asset over 6.7 years may legitimately produce few independent episodes;
that is a valid scientific result, not a failure of the census.

## 2. Anti-overfitting law (owner-ordered; binds every phase)

- NO constant of the detector or of any leg is chosen by scanning fold PnL.
- No fold PnL, no F2/F4 outcome labels, no trade outcomes, no future
  peaks/troughs, no calendar-year tags enter ANY rule.
- Detector and DOWN-leg adjudication are decided by economic mechanism +
  PIT observability + data authority ONLY, before any arm PnL exists.
- The ancestor's PnL is already known and disclosed (§3) — that exposure IS
  the POSTHOC risk, managed by: preregistered machine + preregistered
  eligibility law + frozen arms/controls + full same-window scoring on ALL
  folds + no fold exclusion + ceiling POSTHOC_DISCOVERY + mandatory G10
  fold-trade-off disclosure.

## 3. Ancestor record (MEASURED, committed; facts, not targets)

```text
arm            PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION (Donchian-
               continuation long book gated by the code-owned PIT UPTREND
               phase label; Donchian 30/15, min-hold 12, max-hold 450,
               exit-buffer 6; BTCUSDT-PERP H4)
net @1.0x      +177,691.82 USD on $100,000; max_drawdown -0.2936
trades         86 entries / 86 exits (79 DONCHIAN_STOP, 7 GATE_INACTIVE)
folds          F1 +140,843.28 | F2 -46,959.99 | F3 +133,820.83 |
               F4 -50,012.30; fold_concentration 0.5128
gates          G1 PASS, G2 PASS, G3 FAIL (loses to ALL_ON_TREND_LF
               +1,278,270.73 / ALL_ON_LONG +814,203.60 / SPARSE_RISK_OFF
               +99,457.04 @1.0x), G4 PASS, G5 FAIL (0.5128 > 0.50),
               G6 KILLED (block-shuffled gate placebo +190,391.51 >
               candidate: gate TIMING carried no information),
               G7/G8/G9 PASS. V2 forensics: F2/F4 losses are GROSS
               (-41,885/-43,504), not cost artifacts; no separating PIT
               entry observable found; min-hold fix counterproductive.
STATUS         FAILED G3/G5/G6. A TEST COMPONENT here, never certified.
```

## 4. Arms and account law (frozen now, before any arm PnL)

```text
A  COMPARATOR  PSV1 Donchian long arm re-run UNCHANGED on the same engine,
               folds, costs (reference anchor for every delta; not budget).
B  GATED-LONG  = A + state gate: long arm may OPEN only while state==BULL;
               its own exit law unchanged (Donchian stop, min/max hold)
               plus force-flat on any ->BEAR transition (next H4 open).
               Scores ONLY if the full router (D) is eligible (§0 budget).
C  DOWN-LEG    the BEAR-gated short candidate; exists ONLY if it passes the
               §5 eligibility law; else NOT_RUN/NO_ELIGIBLE (first-class).
D  ROUTER      BULL->long leg / BEAR->down leg / UNCERTAIN->flat, ONE
               account, fraction 1.0, no simultaneous long+short. Exists
               only if B and C are both eligible.
ABLATION       B with the state gate deleted; MUST reproduce A byte-
               identical (ablation identity gate).
E  CONTROLS    reference computations, not budget cells:
               - STATE-SHUFFLE ROUTER: block-shuffle the state series
                 (30-H4-bar blocks, PSV1 CTL-BLOCKSHUFFLE semantics) with
                 matched constraints — transition count within ±10% and
                 exposure share within ±2pp of the realized state series,
                 movement validation entries >= 50% coverage, 1000 draws,
                 fixed seed 20260923; the D-analog under shuffled states is
                 the preregistered KILL control (G11).
               - CASH; ALWAYS_ON_LONG; ALWAYS_ON_TREND_LF (SMA200 on the H4
                 grid); SPARSE_RISK_OFF — the four PSV1 §8 baseline
                 definitions VERBATIM.
```

Account/transition law (all arms, frozen): decisions at H4 close; fills at
the NEXT H4 open; no mid-bar fills. UNCERTAIN: no NEW entries in either
direction; open positions keep their own exit law (a short is force-flattened
when the state LEAVES BEAR — to UNCERTAIN or BULL; a long only via its own
stop or force-flat on ->BEAR). A direction switch charges BOTH fills
(close old leg + open new), fees and funding exactly once per fill. One
account; capital $100,000; fraction 1.0; funding signed at 8h boundaries.
Fold ends force-flat.

## 5. DOWN-leg eligibility law (P2 — frozen BEFORE any rho measurement)

### 5.1 Admission questions (ALL must hold for a candidate)

```text
E1 mechanism   names WHO is forced to trade (or is slow/late) and the leg's
               OWN profit source — after fees + signed funding. "Giá đang
               giảm nên short" is not a mechanism (owner law). An overlay
               whose only profit source is price decline is NOT a new
               mechanism.
E2 data        every observable carries license/coverage/PIT evidence
               measured in THIS tree (the recon data_inventory is the
               starting map; 404 sources are UNAVAILABLE_FAIL_CLOSED).
E3 ancestry    candidate's signal-series |rho| <= 0.20 vs EVERY applicable
               dead shadow (PSV1 §7.2 crypto list + funding-LEVEL carry
               proxy + OI family + breakdown + rev24 + basis-fade +
               run_imbalance + amihud + DVOL + pair-spread), measured
               PRE-PnL at the decision frequency; A1 re-measures at freeze.
E4 floors      BEAR-state §1.5 floors PASS (a DOWN leg gated on a thin state
               is NOT_RUN_THIN regardless of mechanism).
E5 ceiling     cadence arithmetic survivable at 1.5x costs (PSV1 §11 law).
```

### 5.2 Adjudication basis already in evidence (owner recon, read-only)

`research/control/bear_opportunity_recon_2026-09/` (AUTHORIZED_HANDOFF
owner evidence; byte-untouched by this cycle): ANCESTRY_TABLE.md records 14
mechanism classes measured-dead; data_a2 records the measured availability
of every Vision stream. Standing gaps and their status under E1–E4:

```text
liquidation-print tape        liquidationSnapshot 404 (monthly + daily +
                              bm) -> UNAVAILABLE_FAIL_CLOSED at E2.
cross-venue lead-lag          no staged authority, license unmeasured ->
                              UNAVAILABLE at E2 (owner decision required
                              to stage; not assumed).
funding-extreme overlay       ancestry-exposed at E3 (V17 FUNDJUMP: the
                              announced-change form still carried the
                              funding-LEVEL shadow, |rho| 0.2439); and at
                              E1 an overlay whose profit source is price
                              decline collapses into the DOWN_SHORT class.
```

### 5.3 Forbidden reborn forms (vetoed at admission, no measurement needed)

breakdown-short; OI-cascade; OI-level/share/term-structure; short-horizon
reversal (rev24/close-displace-fade per-leg); basis/premium-level fade;
funding carry/level/announced-change events; DOWN_SHORT_BTC /
DOWN_FLAT_RISKOFF (RSM-V1 specialist library, §7.1 reopening law);
liquidation-EPISODE price-defined books; taker-flow/aggressor/elite-size;
run-imbalance; amihud; DVOL-shock; pair-spread. At most TWO mechanism
proposals may be frozen for measurement; both may die.

## 6. Gates (post-GO, per scored arm; G-thresholds = PSV1 §16.3 unless stated)

```text
G1  net > 0 at 1.0x;  G2 net > 0 at 1.5x
G3  (B and D only) beats ALL four E baselines at 1.0x
G4  fold robustness: positive in >=3/4 folds OR best-fold-removed net > 0
G5  no single fold contributes >50% of positive net
G6  preregistered control does not out-earn the candidate (out-earn => kill;
    invalid-control null => disclosed, rest on G1–G5)
G7  turnover within frozen ceiling; zero unnecessary close-reopen
G8  reproduction byte-match; G9 A7 terminal clean (0 HIGH/CRITICAL)
G10 FOLD-TRADE-OFF (the owner's core question, vs COMPARATOR A at 1.0x):
    report Δ(F2)+Δ(F4) improvement AND Δ(F1)+Δ(F3) cost. Fixed now:
    (a) combined net MUST increase vs A; (b) NO fold may flip
    positive->negative vs A. Qualitative gate, preregistered.
G11 ROUTER-KILL: the STATE-SHUFFLE ROUTER control (E) out-earning D => the
    state timing carried no information => KILL.
G12 DECOMPOSITION DISCLOSURE: D-vs-A delta split into state-timing effect
    (position vs the G11 shuffle distribution) and trade-count/cost effect
    (fees avoided); plus per-leg PnL and transition-attributed PnL.
    Reported regardless of verdict.
```

ALL-PASS on the system => ceiling verdict
`BTC_H4_TWO_REGIME_V1_POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_
VALIDATION` (never OOS, never deployable, no orders).

## 7. Cycle phases and verdicts

```text
P0   intake: AGENTS/CLAUDE/handbook/MAP/ledger/failure-memory + PSV1/V2
     terminals re-measured; heavy lock measured (HELD by CRYPTO-HISTORICAL-
     REPLICATION-3F-V1 at open — light work only this session); owner recon
     intake (read-only).
P1   detector census (§1) in the cycle worktree; light compute (<5 min CPU,
     lock-exempt); artifacts + audits + floors margins.
P2   DOWN-leg adjudication (§5); if no candidate passes admission OR a
     state fails §1.5 floors => close NO_ELIGIBLE_PROPOSAL (P2 close, V2
     precedent; STOP-1 moot; GO phrase dies UNCONSUMED at close).
P3   (conditional) freeze arms/cells/gates/digests BEFORE any candidate PnL;
     implement + hand-computed fixtures (PIT/transition/no-lookahead, no
     long+short overlap, no missed fees on reversals, force-flat, tier
     exactness) + sanitized dry-run (non-vacuous) + A7 prelaunch
     fresh-context.
STOP-1 OWNER GATE: report frozen system + controls + budget + POSTHOC risk
     + the exact GO phrase. The owner types, at this gate, verbatim:
     GO BTC H4 TWO REGIME V1 SCORED EXECUTION
     No other phrase consumes; this prompt is NOT a GO.
P4   scored run: full frozen denominator under the machine-wide heavy lock;
     no mid-run stop on ugly numbers; no parameter edit after PnL.
P5   independent reproduction byte-match + A7 terminal fresh-context.
P6   two-half close; verdict exactly one of §7.1.
```

### 7.1 Terminal verdicts (exactly one)

```text
BTC_H4_TWO_REGIME_V1_POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION
BTC_H4_TWO_REGIME_V1_NO_INCREMENTAL_VALUE
BTC_H4_TWO_REGIME_V1_NO_ELIGIBLE_PROPOSAL
BTC_H4_TWO_REGIME_V1_BLOCKED_DATA_OR_SELECTION
TECHABORT
```

## 8. Trial identity and denominators

Every scored arm carries: cycle_id BTC-H4-TWO-REGIME-V1; cell BTC_H4;
family_id TRV1-<MECH>; arm_id; arm_config_digest; data manifest digest
3f1a6687…; code_freeze_sha; cost_tier; fold contract. Observed denominator
counts EVERY computed arm×tier (publication failures included); published
denominator successes only; both at every checkpoint (P-9). Budget cells:
B, C, D, ABLATION only.

## 9. Boundaries

Worktree `.worktrees/btc-h4-two-regime-v1/integration`, branch
`orca/btc-h4-two-regime-v1-integration`; base = PSV1 terminal anchor
af52f3582270bcc19634add3d88858e0c28959bf (frozen engine inherited verbatim,
V2 convention; V2 forensic machinery available via read-only verbatim import
from `.worktrees/btc-h4-continuation-v2/integration` if needed). Registry
only via researchctl/governance. Machine-wide heavy lock for scored AND
heavy forensic compute; light census jobs exempt if <5 min CPU / <2 GB;
never kill a foreign worker. No push from lanes; no merge to main without
owner. S1 sealed. No broker/paper/testnet/live surface, no orders, no API
keys, no credentials in logs. Cycle artifacts under
`research/control/btc_h4_two_regime_v1/` in the cycle worktree; PSV1/V2
artifacts byte-untouched; the owner recon dir is read-only evidence; root
checkout is bootstrap/owner space. Turn-scope: pre-GO turns may rebuild,
test, census, freeze, audit — not run the scored backtest.

## 10. Amendments log

None yet. Amendments must be pre-outcome (before P4), dated, attributed,
and must not touch folds, tiers, floors, gates or the verdict ceiling.
