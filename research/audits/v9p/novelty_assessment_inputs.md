# V9 novelty assessment inputs — F1 ts_trend, F2 residual_mr, F3 vol_shock

Author: A6-support LEDGER+NOVELTY compiler. Compiled 2026-08-26 from read-only
sources (see `global_trial_ledger.json` for the full path list). No backtests
were run; only verdict/metadata and headline PF/net_pnl fields were read.
Companion machine artifact: `p07_no_rescue_check.json`.

## 0. Rejected-family reference (from global_trial_ledger.json)

| Forbidden family | Era | Terminal label | Mechanism class | Failure mode |
|---|---|---|---|---|
| weekly_reversal_V8 (`H-XSECT-REVERSAL-v2`) | V8R | `V8_REJECT_ALL_CANDIDATE` | xsec_reversal | All lookbacks 3D/7D/14D negative PnL, PF<1; momentum control (+5,973) beat best reversal (-3,265); zero passing adjacent pairs |
| xsec_momentum_V4 (`H-XSECT-MOM-v1`, context — not on V9 forbidden list) | V4 | `V4_REJECTED_PIPELINE_PASS_CANDIDATE_FAIL` | xsec_momentum | Direction had signal (MOM-7D +9,735 vs reverse control -27,171) but risk side failed: gross drift >1.0, MDD 24–37%, extreme fold concentration |
| funding_carry_V6 (`H-XSECT-FUNDING-CARRY-v1`) | V6 | `V6P_PASS_V6_CANDIDATE_FAIL` | funding_carry | PF 0.978/1.012 below floor; 7D died on FG3 concentration (top fold 51.66%>50%) |
| funding_price_divergence_V7 (`H-XSECT-FUNDING-PRICE-DIVERGENCE-v1`) | V7 | `V7_REJECT_ALL_CANDIDATE` | funding_divergence | PF 0.976/0.983/1.005 all < 1.10 prereg floor |
| funding_crowding_MR (`H-FUNDCROWD-MR-v2`) | V2/V3 | `V3_SURVIVORS_NOT_LOCKED_FAMILY_REJECTED` | mr_funding_crowding | 96/98 G3 FAIL; 2 ETH survivors never locked (G4 stress not implemented), status REJECTED stands |
| volatility_compression_breakout (`H-VOLCOMP-BRKOUT-v1`) | V1(+V2 reruns) | `REJECT_REDESIGN_CANDIDATE_FAIL_ALL` | vol_compression_breakout | 28-cell grid: 0 PASS; squeeze→Donchian+volume-burst entries all CANDIDATE_FAIL |
| Stage-A singles ×7 (`H-EXISTING-*-v1`) | V1 | `V1_STAGE_A_CANDIDATE_FAIL_ALL` | other | 49/49 cells CANDIDATE_FAIL incl. trend_pullback and mean_reversion pattern variants |

Multiple-testing denominator: **N = 112 unique scored trials** (99 official
unique configs through V5R + 1 negative control + 4+4+4 portfolio-era trials);
conservative raw bound 488 verdict-bearing rows.

## 1. F1 ts_trend — per-symbol time-series trend continuation

**Spec under review:** position direction = sign of each symbol's OWN trailing
return; no cross-sectional ranking, no pairing into long-loser/short-winner legs.

**Pairwise overlap vs rejected families:**

- **vs weekly_reversal_V8 (xsec_reversal):** DISTINCT. Opposite sign hypothesis
  AND different construction class: time-series own-sign exposure vs cross-
  sectional relative rank with dollar-neutral legs. F1 can hold long-only or
  net-long books; WREV is structurally market-neutral by pairing. Shared
  information source (trailing returns) ⇒ correlation risk is real but the
  estimable object differs (per-symbol drift vs cross-rank spread).
- **vs xsec_momentum_V4:** closest neighbor in *direction* of bet. V4 proved XS
  momentum ordering carried signal but died on RISK construction (gross drift,
  MDD, concentration), NOT on mechanism absence. F1 must not become a re-run of
  momentum with per-symbol packaging while importing none of the risk lessons.
  Safeguard: pre-register intraperiod exposure clamps + MDD gates that actually
  bind (the V4 failure mode), and report F1's return correlation to the archived
  XSECT-MOM-7D equity curve.
- **vs H-EXISTING-trend_pullback-v1 (V1, rejected):** same "trend continuation"
  lineage but categorically different trigger: trend_pullback was a discrete
  15m-bar pullback-in-uptrend entry pattern (Stage-A single-symbol grid);
  F1 is a continuous sign-of-trailing-return positioning rule. DISTINCT with a
  mandatory delta statement (cadence, horizon, no bar-pattern trigger).
- **vs funding families (carry/divergence/crowding):** no funding observable
  anywhere in F1 → LOW risk.

**Verdict: DISTINCT. Overlap risk MEDIUM** (momentum lineage shares the
information source). Conditions: (a) explicit no-cross-sectional-term clause;
(b) binding risk gates addressing the documented V4 failure modes; (c)
correlation-to-archived-momentum report at scoring time.

## 2. F2 residual_mr — mean reversion on BTC-residualized alt returns

**Spec under review:** compute alt returns residualized against BTC (market
component removed), trade short-horizon reversion of the residual — a
market-neutral relative-value construction.

**Pairwise overlap vs rejected families:**

- **vs weekly_reversal_V8 (xsec_reversal): THIS IS THE CRITICAL PAIR.** Both
  are short-horizon loser→winner reversion bets among alts. The difference is
  the signal estimator: residual (idiosyncratic) return vs raw return rank.
  Because BTC dominates alt common variance, residuals are approximately
  affine transforms of raw returns over short horizons — the two signals can be
  highly correlated precisely where the rejected family was falsified.
  **Overlap risk HIGH.** This is rescue-shaped unless the residualization is
  proven to select materially different trades than raw-return reversal would.
  Required safeguards (pre-registered, before any scored run): (i) an
  orthogonality gate — e.g., pre-launch on data ≤ freeze date, show
  rank-correlation between residual-reversal positions and raw-reversal
  positions below a frozen threshold, else AUTO-ARCHIVE; (ii) horizon must be
  justified independently of the dead 3D/7D/14D chain; (iii) explicit statement
  of the economic mechanism tested (idiosyncratic liquidity-provider inventory
  reversion) that raw reversal does not capture.
- **vs funding_crowding_MR:** both mean-reversion-flavored, but fundcrowd is a
  single-symbol reclaim-MR entry gated by a funding percentile skip-rule — no
  residualization, no BTC benchmark, funding observable present. **MEDIUM.**
  Safeguard: F2 spec must contain zero funding terms.
- **vs funding_carry_V6 / funding_price_divergence_V7:** carry ranks on trailing
  settled funding alone; divergence is a two-term price-vs-funding percentile
  spread. F2 uses neither. LOW.
- **vs H-EXISTING-mean_reversion-v1 (V1):** single-symbol bar-pattern MR, no
  cross-symbol residual. LOW-MEDIUM; covered by the same delta statement duty.

**Verdict: DISTINCT mechanism class (residual RV ≠ raw-rank reversal), OVERLAP
risk HIGH vs weekly_reversal_V8. Eligible ONLY conditionally**: pass the frozen
orthogonality gate pre-launch; failing it, F2 is classified a rescue attempt of
`weekly_reversal_V8` and must be archived without consuming budget.

## 3. F3 vol_shock — volume-shock-conditioned short-horizon continuation

**Spec under review:** condition on volume shocks (liquidity events); trade
short-horizon continuation among shocked names.

**Pairwise overlap vs rejected families:**

- **vs volatility_compression_breakout:** nearest neighbor. VOLCOMP = price-range
  squeeze precondition → Donchian breakout entry, volume burst as confirmation,
  single-symbol long-only. F3 = volume shock as the *selection variable* among a
  cross-section, trading continuation of the shocked names. Both monetize
  post-volume-event continuation, so the PnL streams can correlate. **Overlap
  risk MEDIUM-HIGH.** Safeguards: (i) shock defined purely by a frozen
  volume-statistic outlier rule (e.g., z-score/multiple-of-median) — NO
  Donchian/squeeze/price-range precondition anywhere in spec; (ii) direction may
  be two-sided (continuation of up- or down-shocks), unlike long-only breakout;
  (iii) report position overlap vs the archived VOLCOMP grid entries at scoring.
  If implementation collapses to breakout-on-volume, it IS the rejected family.
- **vs weekly_reversal_V8:** continuation-direction hypothesis is opposite to
  reversal; conditioning variable (volume) absent from WREV spec. LOW-MEDIUM.
- **vs xsec_momentum_V4 (context):** continuation lineage shared; if F3 uses
  cross-sectional selection among shocked names, the V4 risk-gate lessons apply
  verbatim (exposure clamps, MDD).
- **vs funding families:** volume observable ≠ funding observable. LOW.

**Verdict: DISTINCT conditional on the shock-definition safeguards. Overlap risk
MEDIUM-HIGH vs volatility_compression_breakout**, LOW-MEDIUM elsewhere.

## 4. H-XSECT-REVERSAL-BREADTH-CRYPTO-v1 — rescue question

Frozen prereg (2026-08-25T23:50Z, `v8x_spec_freeze.json`): weekly cross-sectional
reversal, formation lookbacks exactly [3,7,14] days, long bottom-2 losers /
short top-2 winners, Monday 00:00 UTC — i.e., **identical mechanism_class
(xsec_reversal) and identical signal construction** to the V8 core, differing
only in universe (rule-based top-10 median-quote-volume vs hand-frozen six alts),
data span (1y vs ~2y), accounting scaffolding, and outcome ceiling (hard-capped
at S0_EXPLORATORY_BREADTH_SCREEN, never promotion evidence).

The prereg itself was authored blind and remains procedurally intact — running
or archiving it cannot violate the freeze. The question is mechanistic, and the
ledger now answers it:

1. The mechanism this cohort tests was **falsified after the freeze**: valid V8
   terminal = `V8_REJECT_ALL_CANDIDATE` (zero passing lookbacks; control beat
   every reversal candidate on net PnL). The cohort's own status.yaml gating —
   "none may run before valid V8 terminal + X01-X12 gates" — contemplated a V8
   terminal, but the terminal that arrived is a family-level rejection.
2. A top-10-by-volume crypto universe heavily overlaps the rejected six-alt set
   (SOL/BNB/XRP/DOGE/LINK/ADA are all top-10 quote-volume names). Swapping
   universe/span after an in-family rejection is a sample-change retry of a
   falsified mechanism — the canonical rescue shape — even when dressed as a
   breadth screen.
3. The exploratory cap means the cohort cannot promote anything even if it
   "passes": there is no scientific payoff that offsets spending fresh scored
   trials on a dead mechanism class, and any pass would immediately tempt a
   third instantiation (the actual anti-rescue hazard).
4. Doctrine consistency: V9 family selection should spend budget on NEW
   mechanisms (F1/F2/F3 above). If reversal exposure is ever revisited, it must
   enter through a new mechanism hypothesis with its own orthogonality evidence
   (cf. F2's conditional route), not through a universe swap of
   `FAM-V8-WEEKLY_XSEC_REVERSAL`.

**Recommendation: ARCHIVE_NOT_RUN** — grounded in mechanism class:
`xsec_reversal` is terminal-rejected in this repo's ledger; the breadth cohort
is a same-mechanism sample change, its exploratory ceiling removes any
compensating value, and shelving it preserves prereg integrity (archive ≠
breach). The equity twin (`H-XSECT-REVERSAL-BREADTH-EQUITY-v1`) inherits the
same mechanism-class ruling and is additionally provider/spec-mapping blocked;
both stay archived un-run with hashes intact.

## 5. Summary table

| Candidate | Verdict | Highest-risk neighbor | Binding conditions |
|---|---|---|---|
| F1 ts_trend | DISTINCT | xsec_momentum_V4 (info source shared); trend_pullback V1 | no XS term; binding risk gates vs V4 failure modes; correlation report |
| F2 residual_mr | DISTINCT, HIGH overlap risk | weekly_reversal_V8 | pre-launch orthogonality gate vs raw reversal; independent horizon justification; zero funding terms |
| F3 vol_shock | DISTINCT conditional, MEDIUM-HIGH risk | volatility_compression_breakout | pure volume-outlier shock definition; no squeeze/Donchian precondition; two-sided allowed; overlap report |
| H-XSECT-REVERSAL-BREADTH-CRYPTO-v1 | **ARCHIVE_NOT_RUN** | weekly_reversal_V8 (same mechanism) | none — shelve intact; revisit only via new mechanism-class hypothesis |
