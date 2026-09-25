# PROPOSER2 (BLIND) — ERP1-TRACKA-COHORT-1 — Future-cohort mechanism proposals + adversarial design review

> Lane: blind proposer P2 (umbrella §5.1 fourth council element; owner decision
> D-E context, draft plan §7.1 deviation disclosure). Status: READ-ONLY council
> artifact. This lane measured root `main` @
> `69ddc60447d223249319f82b71b21e26ab941203` (matches the dispatch expectation),
> read ONLY: `plans/DRAFT_ERP1_TRACKA_COHORT_1.md` (binding contract, in full),
> `research/wayfinder/FAMILY_FAILURES.jsonl` (126 entries, failure memory),
> `plans/CYCLE_REGISTRY.json` (lifecycle keys only),
> `.worktrees/fx-rangefade-2m-shadow-v1/research/control/EURUSD-RANGEEXP-SCORED-V1/scripts/v2_lib.py`
> (code authority), `CLAUDE.md`/`HOW_TO_BE_A_LEAD_ENGINEER.md` (schema §34.4).
> Nothing else was opened. No scored outcome, no journal/state/dashboard bytes,
> no adjudication numbers, no other lane's output, no winner/ranking
> information was read or requested. Both proposals are FUTURE-cohort
> candidates: the frozen cohort (M1, M3; M2 vetoed) has no open slots and this
> document does not request one.

## 0. Ancestry disclosure (binding, draft §3 — carried verbatim in substance)

The RANGEFADE ancestry is OUTCOME-EXPOSED (`EURUSD-OPEN-SEARCH-V1`,
`EURUSD-OPEN-SEARCH-V2`, `EURUSD-RANGEEXP-SCORED-V1`, `FX-MAJORS-SEARCH-V1`,
`FX-RANGEFADE-2M-SHADOW-V1`). EURUSD/GBPUSD/USDJPY full scored windows
(2021-01 .. 2026-06 inclusive) are outcome-exposed surfaces. This packet cites
no PnL, PF, win-rate, trade-count outcome, journal content, or ranked/selected
information from any scored or shadow surface. All 12 census families (GAP,
PDHLOC, DOW, ASIAFADE, SESSMA, H1TSMOM, H1DONCH, DAYMOM, RANGEEXP, STOCH,
ROUNDNUM, HOURREV) carry dev-window exposure; selection on remembered dev PnL
is prohibited and structurally impossible here. Code facts used are the
council-verified ones (draft §4.2): `pct[d]` ranks day d's OWN full-day range
(PIT leak); deployed mapping pct==0→flat, 0<pct≤0.7→FADE, pct>0.7→FOLLOW;
daemon runs a third (partial-range) law; no artifact may cite "shadow parity
PASS" about R-ORIG semantics.

---

## 1. Proposals offered: TWO. Self-vetoed before offering: FOUR (§4).

### 1.1 P2-A — RECLAIM-ABSORB (sweep-and-reclaim absorption of the previous-day band)

**Mechanism (one sentence):** When an H1 bar during 07:00–18:00 UTC has its
high (or low) trade beyond the previous traded day's high (low) but CLOSES
back inside the band — the edge visibly rejected the probe within one bar —
enter short (long) at the NEXT H1 open at the opposite quote and harvest the
recovery to the family's middle-quarter reversion exit, flat before 20:00 UTC.

Design identity notes: NO regime/percentile selector anywhere (the ancestor's
range-percentile mode layer is absent, not re-tuned); NO spread layer (M3's
layer is absent, not transplanted); NO cross-pair leg (M2's corpse avoided);
NO thresholds — the event definition is parameter-free. The ONLY new object is
the event class: rejection-completed probes (bar-close back inside) instead of
live breaks (bar-close beyond). Entry bars are disjoint per-bar from the
ancestor's trigger bars (ancestor triggers on close-beyond; P2-A triggers on
traded-beyond-but-closed-inside). Exit law, session window, next-H1-open
opposite-quote fills, force-flat 20:00 and weekend-flat are inherited family
identity (in-family per V-1's own statement of the family boundary).

**Ten mandatory fields:**

1. **Payer + non-arbitrage:** breakout entrants chasing the sweep extreme and
   stop-loss orders resting beyond the visible prior-day extremes; both are
   mandatory, anonymous, dispersed, price-insensitive at the moment of the
   sweep (stops trigger mechanically; chasers pay for immediacy). They cannot
   arbitrage the premium away because their flow is produced by risk-management
   convention (placing protective stops beyond yesterday's high/low) and by
   breakout playbooks, not by a trade they can refrain from making without
   abandoning their mandate.
2. **Premium bps/decision (DECLARED HYPOTHESIS, unmeasured):** 2–6 pips gross
   per round trip on AUDUSD-scale majors (harvest = partial reversion toward
   the band's middle quarter, band quarter-width ≈ 8–20 pips on typical
   50–90-pip ranges; the mechanism needs only ~1/4 of that quarter to clear
   the stressed book). Risk transferred: short genuine-breakout continuation —
   named tail = trend day where the reclaim fails and price runs one full
   band+ (max adverse excursion to the 20:00 force-flat ≈ up to one daily
   range); secondary tail = news whipsaw (reclaim for minutes, then resume —
   double loss within the day).
3. **Persistence + erosion:** stop-cluster placement beyond prior-day extremes
   and breakout-entry playbooks are persistent conventions (decade-scale).
   Erosion: sweep/reclaim pattern scanners front-running the reclaim compress
   the recovery below the stressed round trip; migration of stop flow to
   execution venues/timing our M1-costable law cannot observe (sub-M1
   sequencing) degrades fill quality, which this cycle can only stress-cover,
   never measure (draft §6 condition 4).
4. **PIT observable (event/effective/available separated):** EVENT = H1 bar t,
   07:00–18:00 UTC, bid-series OHLC: `b_h[t] > PDH` (upper) or `b_l[t] < PDL`
   (lower), where PDH/PDL are the previous traded day's traded-hours high/low
   (family `_prev_day_stats` convention), AND `b_c[t]` back inside
   `[PDL, PDH]`. Known at t's close; no intrabar decision. EFFECTIVE = t+1
   open. AVAILABLE = t+1 open (fill at opposite quote under the family
   executor law). Source: Dukascopy M1 bid/ask day files — ALREADY authorized
   corpora (draft §5.1/§5.2); no new data layer, no volume, no tick events.
5. **Holding horizon + clock:** intraday only; entry on the H1 grid at t+1
   open; exit at middle-quarter reversion touch (family exit law) or the
   day-close force-flat before 20:00 UTC; weekend flat; declared hypothesis
   2–8 H1 bars mean holding (UNMEASURED). No fills on/after the 19:00 bar.
6. **Capacity:** paper-tier irrelevant by construction; at scale the binding
   constraint is the edge's own size, not depth — taker fills at next-H1 open
   on majors absorb low-tens of MM USD notional without self-impact; declared
   ceiling class, no depth claims (queue/depth evidence does not exist on M1).
7. **Costs base + stress:** base = the fill bar's own measured spread × k at
   each crossing (entry `s_open`, exit `s_close`; one crossing per side), per
   the draft §6 charging semantics, against the sha-pinned per-session census
   curve of the home pair; stress = ×2.0 per-regime medians with ×1.5 and ×2.0
   both reported; F-5 uses the CONDITIONAL spread at break-style bars (the
   family fills when spreads widen). Declared band arithmetic (no backtest):
   base RT ≈ 0.6–1.6 pips, stressed ×2.0 ≈ 1.2–3.2 pips (pending the new-pair
   census; ancestry majors' session p50 0.3–0.8 pips is the prior). Hypothesis
   2–6 pips/event ⇒ positive ceiling hypothesis with a thin stress-tail
   margin — declared the second most-likely killer after F-1.
8. **Falsifier (with the control that must NOT reproduce):** CAUSAL CONTROL =
   live-break complement book — fade on close-beyond entries (no reclaim
   requirement), same days, same clock, same exit law; it must NOT reach
   ≥0.5× anchor net @×1.0 (`KILL_CONTROL_REPRODUCED`, draft §9.4) — if the
   plain band-fade reproduces, the edge is the family's range-fade, not
   rejection absorption. INVERTED control (buy rejections) must be strictly
   below anchor. F-1 rho machinery: Spearman |rho| vs R-ANCHOR target array
   >0.60 ⇒ `VETO_NOVELTY_RENAME`; pooled |rho| ≤ 0.20 vs dead families
   computed by the skeptic on the exact scored representation. Plus M-2-style
   non-vacuity (reclaim event set must differ from the break event set in
   ≥2% of session bars), G8 hour-concentration, beta-kill at 0.5× (§9.4).
9. **Controls / baseline (1 anchor / ≤2 neighbours / 1 causal / 1 inverted /
   1 baseline set):** anchor = reclaim-fade as specified; N1 =
   first-reclaim-only book (max one trade per edge per day — sparsity
   support); N2 = two-consecutive-close reclaim confirmation (strictness
   support; both neighbours never verdict-bearing, R-NEIGH-class); causal =
   live-break complement; inverted = sign-flipped reclaim book; baseline set
   = FLAT + day-session SHORT_ALWAYS + day-session LONG_ALWAYS with
   beta-matched reporting per draft §8 F-4 frozen directions.
10. **Home pair:** AUDUSD (tight-spread class; USD-quote so the SHORT_ALWAYS
    beta control keeps ancestry semantics; subject to the §5.2 new-pair gate).

**Six economic questions (draft §7.3), explicit:**

- **Q1 (payer + non-arbitrage):** answered in field 1 — mandatory stop flow +
  chasing breakout entries at the swept extreme; not arbitrageable because the
  flow is a byproduct of risk conventions, not a priced trade.
- **Q2 (premium bps + named tail):** 2–6 pips gross/event hypothesis;
  tail = trend-day continuation through a reclaimed edge (loss bounded by the
  20:00 force-flat, up to ~one daily range); secondary = news whipsaw.
- **Q3 (persistence + erosion):** field 3 — stop-placement and breakout
  playbooks persist; erosion via front-running scanners and sub-M1 execution
  migration (fill quality unmeasurable on M1, stress-covered only).
- **Q4 (PIT observable + authorized source):** field 4 — event at H1 close,
  effective and available at next H1 open; Dukascopy M1 bid/ask, already
  authorized; no new layer.
- **Q5 (falsifier + control prediction):** field 8 — live-break complement
  must NOT reach 0.5× anchor; inverted strictly below; F-1 rho fixtures may
  kill pre-PnL (declared most-likely kill, see §3 below).
- **Q6 (cost-survivability ceiling):** field 7 — stressed RT 1.2–3.2 pips vs
  hypothesis 2–6 pips/event: positive-ceiling hypothesis, thin stress tail;
  F-5 declares the arithmetic pre-PnL and vetoes on a negative ceiling.

**Expected decisions/year (clock arithmetic only, no backtest):** 12 session
H1 bars × ~260 trading days = 3,120 session-bar slots/pair/yr; declared
UNMEASURED assumption band 0.4–1.0 qualifying reclaim round trips per trading
day after one-position/edge caps ⇒ ~100–260 RT/pair/yr. Warmup ≈ 2 traded
days (band needs one prior traded day; no regime window — a design virtue vs
M1's ≈61-day warmup). G5 (≥100 RT on the dev union) plausibly met mid-band;
F-6 decides on the last-6-months window.

**Self-veto pass vs FAMILY_FAILURES.jsonl (cited family_ids):**
- `FXFV2-A4-P2` "London-AM range break + retest-hold"
  (CONTROL_REPRODUCED_MECHANISM) — nearest dead relative: a retest-hold
  confirmation of a range break. Distinguishing facts: P2-A's edge is the
  PREVIOUS TRADED DAY's band (not an intraday London-AM range), the event is
  the same-bar close-back-inside (not a later retest hold), the clock is the
  family session (not London-AM), and there is no second leg. Still the
  closest failure-memory entry; declared, to be adjudicated by the rho gate.
- `FXFV1-A3-P2` "Late-NY fade" (EXPECTANCY_NONPOSITIVE) — session-local fade;
  P2-A is event-driven across the full family session, not a clock-local fade.
- `FXOS-04` Bollinger mean-reversion fade (HOLDOUT_NET_NEGATIVE) — different
  trigger (band statistic vs structural edge) and no force-flat-inherited
  identity overlap beyond the fade sign.
- `FXFV2-A4-P1` "Tokyo-range compression → London-morning expansion"
  (EXPECTANCY_NONPOSITIVE, COST_DOMINATED) — range-transition book; P2-A has
  no range measurement at all (no V-2 surface).
- Registry-level: 29 of 126 recorded failures are `ANCESTRY_RHO_BLOCK` — the
  rho gate is empirically the binding constraint for this program's FX
  proposals; P2-A enters with that expectation stated, not discovered later.

**Veto pass V-1..V-8 (declared adjacencies in bold):**
- V-1 renamed ancestor: **ADJACENT — the trigger band and clock are the
  family's; the event class differs (rejection-complete vs live break) and no
  mode layer exists. The Spearman fixture vs R-ANCHOR on AUDUSD is the
  mechanical test and is declared the PRIMARY KILL RISK of this proposal**
  (positions persist across bars, so target-array correlation is not zero a
  priori).
- V-2: CLEAN — no percentile/quantile of any range anywhere; no threshold
  exists in the mechanism.
- V-3 re-clock/re-session: CLEAN — family session window, family fill law and
  family exit inherited unchanged; entry timing is event-determined, not
  re-chosen. **Declared subset adjacency: on bars where the reclaim follows
  the immediately prior close-beyond bar, entry is displaced one bar from the
  family's — the draft §3.4 "displaced-fade" class-veto adjacency is declared;
  distinguishing fact: displacement is event-conditioned, never fixed.**
- V-4 blend/gating: CLEAN — one mechanism, one observable (the reclaim event),
  one causal control; no second ancestry observable anywhere.
- V-5 sign-flip: CLEAN — fade direction is absorption-consistent; the
  inverted control is a control, not the anchor.
- V-6 census re-entry: **ADJACENCY DECLARED with sign risk: PDHLOC is a
  FOLLOW book on the same band and RANGEEXP-fade/ASIAFADE are fade books on
  adjacent bands; because the gate uses |rho| ≤ 0.20, a mechanically
  plausible outcome is a NEGATIVE rho beyond −0.20 vs PDHLOC (same hours,
  opposite signs on neighbouring bars). Declared as the second most-likely
  kill.** Skeptic computes it on the exact scored representation.
- V-7 calendar geometry: CLEAN — no calendar object anywhere.
- V-8 cross-horizon rescue: CLEAN — not a rescue of any killed family.

### 1.2 P2-B — PROBE-DEPLETION GATE (same-edge intrabar probe count gates the family fade)

**Mechanism (one sentence):** Fade a previous-day-band break (H1 close beyond
the edge, 07:00–18:00 UTC, family fill/exit/flat law) ONLY when the same edge
has already been probed intrabar ≥2 times during the current trading day by
M1-bar extremes without an H1 close holding beyond — depleted stop fuel makes
the late break the weakest carrier.

Design identity notes: the trigger EVENT is the family's own (H1 close
beyond); the NEW object is a single gate — the within-day same-edge count of
M1 bars whose extreme pierced the edge (counting closed M1 bar extremes;
no sub-M1 event timing, no tick sequencing — M1 bars are the corpus). No
percentile/quantile (a COUNT is not a window ranking); no spread layer; no
cross-pair leg. Frozen k=2; one threshold, one value, no grid (M3 precedent:
one p60 + support neighbours).

**Ten mandatory fields:**

1. **Payer + non-arbitrage:** breakout entrants entering the late re-break
   expecting the stop-cascade that has already been consumed by earlier
   intrabar probes; their follow-through supply is structurally thinner and
   they cannot re-create consumed stop liquidity on demand.
2. **Premium bps/decision (DECLARED HYPOTHESIS, unmeasured):** 2–6 pips gross
   per round trip (same harvest geometry as P2-A: reversion toward the band's
   middle quarter). Risk transferred: short the break that DOES still have
   fuel — named tail = news-driven break on a heavily-probed day (the probes
   were accumulation, not depletion); secondary = probe-count regimes that
   coincide with rollover-adjacent thin hours (handled by the per-session
   spread curve, disclosed).
3. **Persistence + erosion:** stop placement beyond visible extremes persists;
   erosion is FASTER than P2-A's because intrabar probe-counting is known
   sell-side order-flow folklore — scanner adoption compresses the gate's
   information edge; declared honestly as the weaker-persistence proposal.
4. **PIT observable:** EVENT = H1 close beyond edge at bar t on a day whose
   same-edge intrabar M1-probe count (strictly before t's close, counting
   bars whose high > PDH / low < PDL while all H1 closes so far held inside)
   is ≥2. EFFECTIVE/AVAILABLE = t+1 open, opposite quote. Source: the same
   authorized Dukascopy M1 bid/ask corpora; counting uses closed-bar
   extremes only.
5. **Holding horizon + clock:** identical family law to P2-A (mid-quarter
   exit, no fills ≥19:00, flat <20:00 UTC, weekend flat); holding hypothesis
   2–8 H1 bars (UNMEASURED).
6. **Capacity:** as P2-A — taker-at-next-open on majors; edge-size-bound.
7. **Costs base + stress:** same book as P2-A (fill-bar spread × k per
   crossing; ×2.0 stress; F-5 conditional break-hour bucket). NOTE: fills
   occur strictly on close-beyond bars (same bars as the family), so the
   conditional-spread concern is identical to M1's, not worse. Declared band
   arithmetic identical: base ≈ 0.6–1.6 pips, ×2.0 ≈ 1.2–3.2 pips vs
   hypothesis 2–6 pips.
8. **Falsifier:** CAUSAL CONTROL = k≤1 complement book (fade close-beyond
   breaks on days with ≤1 same-edge probe — the fuel-rich class); must NOT
   reach ≥0.5× anchor net @×1.0. INVERTED strictly below. F-1 fixtures:
   **Spearman |rho| vs R-ANCHOR >0.60 is declared the PRIMARY KILL RISK —
   heavily-probed days and wide-range days are mechanically correlated
   states, so the gate's selected set may overlap the ancestor's fade set
   strongly.** Non-vacuity: the probe-state shifted one day must move the
   book (M3's T-3 pattern); G8 hour-concentration; beta-kill 0.5×.
9. **Controls / baseline:** anchor = k=2 gated family fade; N1 = k=3
   (strictness support, never evidence); N2 = probe count taken from the
   PREVIOUS day instead of the current day (state-shift support + mutation
   non-vacuity companion, M3's N2 pattern); causal = k≤1 complement; inverted
   = sign-flipped anchor; baseline set = FLAT + SHORT_ALWAYS + LONG_ALWAYS,
   beta-matched per §8 F-4.
10. **Home pair:** USDCAD (USD-base structural generalization, §A.1
    precedent; subject to the §5.2 gate).

**Six economic questions:** Q1/Q2/Q3: fields 1–3 (payer = fuel-depleted
breakout entrants; premium 2–6 pips hypothesis; named tails = fuel-ful news
break and rollover-thin probe hours; persistence weakest of the two —
folklore-erodible). Q4: field 4 (event at H1 close, gate state from closed
M1 extremes, available at t+1 open, authorized source). Q5: field 8 (k≤1
complement must NOT reproduce; rho fixture declared primary kill). Q6: field
7 (same ceiling arithmetic as P2-A; conditional break-hour bucket identical
to M1's fill bars).

**Expected decisions/year (clock arithmetic, UNMEASURED):** qualified events
= close-beyond bars on ≥2-probe days; declared assumption band 0.25–0.7
qualified round trips per trading day ⇒ ~65–180 RT/pair/yr; **the low end
breaches G5's 100-RT floor — population risk flagged as a co-equal kill
candidate with the rho fixture (F-6 decides).** Warmup ≈ 2 traded days.

**Self-veto pass vs FAMILY_FAILURES.jsonl:** no dead family used a within-day
intrabar probe count as a gate; nearest adjacencies: `FXFV2-A4-P1` (range
regimes — different object: no range is measured) and `FXNG1-A5-P1`
(opening-follower clocks — different clock class, macro-event driven);
census adjacency: RANGEEXP (shared trigger bars — the declared V-1/V-6 risk
above, |rho| fixtures decide); STOCH (extremes-persist adjacency is
thematic only — different observable and clock). Declared: probe count is
partially an intraday-activity proxy; the draft §3.4 "vol-level" class-veto
adjacency is declared, with the distinguishing fact that the count is of
discrete same-EDGE touch events, not a level or threshold of any volatility
measure.

**Veto pass V-1..V-8:** V-1 **PRIMARY KILL RISK declared** (rho fixture);
V-2 CLEAN (count, not quantile); V-3 CLEAN (family trigger, clock, and exit
unchanged — the gate selects among the family's own events); V-4 CLEAN by
construction (one observable: the same-edge probe count; no combination) —
**with the declared adjudication risk that the counted events are themselves
band-touch events; the skeptic adjudicates whether a count of one ancestry
trigger class is "one observable" (M3 precedent: a spread state — a
different layer — was admitted; a count on the SAME layer is the novel
adjudication question this proposal poses)**; V-5 CLEAN; V-6 **declared**
(RANGEEXP/PDHLOC overlap, |rho|); V-7 CLEAN; V-8 CLEAN.

---

## 2. Candidates considered and SELF-VETOED before offering (not proposals)

- **S-V1 "DECEL-GATE"** (fade band breaks only when approach momentum is
  decelerating over the two prior closes): momentum-state gate sits inside
  the failure neighborhood of dead momentum-state fades (census SESSMA,
  STOCH; `FXFV1-A3-P2`); cannot honestly clear the census |rho| law nor the
  V-4 "indicator" smell. Self-vetoed.
- **S-V2 "PREV-WEEK BAND" absorption** (same fade on the prior week's
  H/L): band-source/lookback swap of the family trigger = V-1 rename class
  (the lo_q/hi_q re-tune ban's moral equivalent at the band horizon).
  Self-vetoed.
- **S-V3 "CROSS-PAIR CALM GATE"** (home fade gated on a reference pair's
  state): every concrete instantiation I could construct reuses an ancestry
  observable on the reference leg (M2's exact V-4 corpse) or transplants
  M3's spread layer (rename). The draft's allowance for "a cross-pair gate
  on a NON-ancestry observable" (§A.2, M2 disposition) remains formally
  open, but I found no instantiation I could honestly differentiate.
  Self-vetoed.
- **S-V4 "CONFIRMED-BREAK LAG ENTRY"** (enter the family fade one bar later
  on confirmation): V-3 re-clock of the same signal; also subsumed by P2-A's
  event definition. Self-vetoed.

---

## 3. Kill-first honesty — the strongest reason NOT to spend a future cohort on P2-A/P2-B

Both proposals' most likely fate is a PRE-PNL kill at F-1, not an economic
refutation: the prev-day band is the most heavily searched observable in this
program's FX history (12-family census; 29 `ANCESTRY_RHO_BLOCK` entries in
`FAMILY_FAILURES.jsonl`; the frozen M1 and M3 already occupy its regime layer
and spread layer), and the |rho| ≤ 0.20 census law is sign-sensitive — a fade
book on the family's own band can fail by anti-correlating with PDHLOC's
follow book. If the owner's question is "is there a fundable mechanism left
on this band?", the honest answer from this lane is: probably not on the band
itself; the next genuinely open proposal space is a different edge FORMATION,
and every candidate formation I generated (intraday opening range, Asia
range, Donchian extremes, round-number grids) collides with dead census
families (ASIAFADE, H1DONCH, ROUNDNUM) or V-2. The defensible reason to fund
this future cohort anyway is cheap information: both proposals die or
survive at the rho fixtures BEFORE any scored cell is spent, so the cost of
adjudication is near-zero — but the owner should not expect either to reach
scoring. Secondary kill argument: the declared premium band (2–6 pips) vs the
stressed book (1.2–3.2 pips) leaves a thin stress-tail margin of the same
fragility class the frozen cohort already carries in M3 (§A.2: "most
cost-fragile cell") — a future cohort would be concentrating in a
cost-fragile family.

---

## 4. Adversarial design review of the FROZEN M1 and M3 (design-level only; no outcomes exist anywhere)

### 4.1 M1 (RANGEFADE-PIT replication; draft §4.2, §8, §9)

1. **HOLDOUT COMPANION LIST OMITS THE INVERTED CONTROL (strongest finding).**
   §9.1's one-look pass admits "the promotable ANCHOR arms … plus … their
   preregistered causal control and baseline books"; §9.3 PROMOTE then
   requires "inverted control strictly below anchor". As frozen, the inverted
   control is neither a holdout companion nor explicitly dev-bound — the
   inversion clause is evaluable on dev only, so an anchor that passes dev
   while inversion appears only on holdout would PROMOTE un-checked. Closing
   the hole costs nothing if the inverted arm is computed inside the same
   single pass (it consumes no additional look); recommend a one-line
   amendment adding it to the §9.1 companion list.
2. **Beta-control composition gap (§8 F-4, §9.4 beta law).** The beta-matched
   book matches the USD SIGN only; the anchor's exposure is regime-day
   conditional (fade-mode days are the majority under the frozen mapping).
   `anchor_minus_beta_control` can therefore be positive from
   regime-conditional volatility timing rather than edge. The slice is
   computable from the already-scored SHORT/LONG_ALWAYS cells (restrict to
   the anchor's fade-mode days) — recommend mandating that decomposition
   table in every artifact, no new cell needed.
3. **F-3 clock-placebo hour-profile blindness (§8 F-3, §9.2 G8).** The
   placebo matches average entries-per-day and average entry hours but its
   non-vacuity predicates never compare the HOUR DISTRIBUTIONS of the two
   books; an anchor whose edge concentrates in the first session hours can
   pass against a placebo spread flatly across the session. G8 bounds the
   anchor's own hour concentration but not the control's comparability.
   Recommend an hour-profile comparison predicate (report-only is acceptable;
   a kill is not required to close the comparability gap).
4. **F-5 bucket keying (§8 F-5).** The ceiling uses the census's break-hour
   bucket, but M1's fills occur at the NEXT bar's open — often one hour after
   the qualifying close, occasionally at the 07:00 open after overnight
   breaks. A mis-keyed bucket understates the conditional spread actually
   paid. Recommend keying F-5 to the dry-run arm's ACTUAL fill-hour
   distribution (arm_config_digest-specific), which exists pre-PnL from the
   exact-arm dry run.
5. **Seam-law clause (iii) small-N noise (§9.4).** The per-trip nearest-pair
   test within the same UTC day can be evaluated on a tiny matched subset
   (unmatched trips are excluded and counted — good), making the 1×c_rt
   comparison noisy in both directions. Recommend a minimum matched-pair
   count for clause (iii) evaluability, below which the clause is
   NOT_EVALUABLE and escalation is to clauses (i)/(ii) only.
6. **R-NEIGH contaminates the DSR denominator (§10).** Support-only
   neighbours consume scored cells and enter "DSR across ALL cohort trials";
   arms designed not to be evidence still inflate the multiple-testing
   adjustment in the anchor's favor. Recommend reporting DSR with and without
   support-only neighbours (disclosure, no gate change).
7. **F1 warmup erosion (§A.1, §9.1).** The ≈61-traded-day warmup consumes the
   head of fold F1; G3's fold counting then compares folds of unequal
   effective length. Recommend per-fold warmup exclusion zones in the Q-12
   logs (partially covered) and an explicit F1-effective-length note in the
   ledger row.

### 4.2 M3 (QSTATE-ABSORB; draft §A.2)

1. **Causal-control cost asymmetry weakens its evidentiary value.** The
   spread-WIDE complement fills precisely at the widest-spread hours by
   construction, so its predicted failure is guaranteed by costs alone; a
   PASS on the anchor then does not isolate the gate's information value
   from a mere affordability asymmetry. The control is correctly
   occupancy-matched (§A.2), but cost-matching is impossible by design.
   Recommend persisting the complement's GROSS-vs-NET decomposition in the
   ledger row (F-4-style) so the design asymmetry is visible at adjudication;
   kill stays NET as preregistered.
2. **Runtime state PIT on thin buckets.** The trailing 20-trading-day
   same-hour p60 needs trading-day alignment and fail-closed handling of
   thin buckets; the §6 census schema hardening (LOW_SAMPLE_BUCKET, no
   silent drops) is specified for the census but not extended into the
   RUNTIME state computation. A silently thin p60 bucket is a hidden
   parameter drift. Recommend extending the same fail-closed rule to the
   state.
3. **T-1 is necessary, not sufficient.** The ≥80%/≤6h session-collapse
   tripwire bounds gross clock concentration of gate-OPEN bars, but a gate
   open ~uniformly that nonetheless selects breaks concentrated at
   rollover-adjacent hours remains clock-confounded; G8 partially covers the
   residual. Acceptable as frozen; noting for the record.

### 4.3 What could let a weak positive through (summary)

The single largest design-level route to a weak positive is review item 4.1.1
(holdout inversion hole); the second is 4.1.2 (beta sign-matching without
regime matching); the third is 4.2.1 (a causal control whose failure is
cost-guaranteed). None requires new data, new cells, or new authority to
close.

---

## 5. Signed outcome-blindness disclosure

I, the P2 blind proposer lane of the ERP1-TRACKA-COHORT-1 outcome-blind
council, attest: (a) I read only the binding draft plan, the failure-memory
registry, the cycle registry's lifecycle keys, the code authority
`v2_lib.py`, and the handbook schema section; (b) I did not read, request, or
infer any scored outcome, PnL/PF/win-rate/trade-count result, shadow
journal/state/dashboard content, adjudication number, or winner/ranking
information from any cycle; (c) I did not read `research/wayfinder/MAP.md`,
`NOTES.md`, any plan other than the draft, any other cycle's control
directory or report/review/verdict file, and nothing under
`research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort1/` other than
writing my own two artifacts; (d) all decision/year figures above are clock
arithmetic on declared unmeasured assumptions, and all premium figures are
declared hypotheses, never measurements; (e) the self-vetoes in §2 were
applied to myself under V-1..V-8 before offering. Violation of this
disclosure voids this artifact.

— BLIND PROPOSER LANE P2, 2026-09-25, root main @
`69ddc60447d223249319f82b71b21e26ab941203`.
