# SCREENING MATRIX — EVENT-MECHANISMS-V1 (G1, A1/proposer role, outcome-blind)

Written BEFORE any PnL exists on these surfaces (no scored surface has been
computed; S1 sealed). Eight fields per direction exactly as the owner
directed. Collisions cite `research/wayfinder/FAMILY_FAILURES.jsonl` (139
rows) + DTP death ledger (38 ids) + verdict classes in
`HYPOTHESIS_LEDGER.md`. The INDEPENDENT SKEPTIC (separate report) holds VETO
over every KEEP; skeleton-merge is applied by the court after both roles
have written.

---

## D1 — STOCKS: EDGAR acceptance-timestamp filing-flow (PEAD-class on minute clock)

1. **Ai trả tiền (payer):** investors and funds whose information set is the
   *filing date* or vendor rows keyed on *period date*, not the
   second-precision acceptance stamp; plus after-hours liquidity providers
   quoting marks that do not yet reflect a filing accepted 16:05 vs 18:40.
   The payer is real only if reaction conditional on acceptance-time strata
   (in-session vs after-close vs Friday-evening) differs from reaction
   conditional on date alone.
2. **Vì sao phải trả (why forced):** attention and processing are finite;
   filings accepted outside monitoring windows are incorporated with a lag
   by a measurable subset of participants (Q-7: the clock is where event
   variance lives). Nobody is "forced" to lose — the mechanism is slow
   diffusion of the *timestamped* information, which must be measured, not
   assumed.
3. **Observable tại thời điểm quyết định:** `filings.recent.acceptanceDateTime[]`
   from `data.sec.gov/submissions/CIK##########.json` (measured HTTP 200 at
   intake, keyless, second precision) + form type + accession; EODHD EOD
   bars for the price plane (entitled, on disk). Decision at next-session
   open after acceptance.
4. **Khi nào edge hết:** PEAD-style drift decays days–weeks; the
   *timing-stratum* edge decays as EDGAR real-time feeds (RSS/atom)
   proliferate; a filing accepted pre-open vs post-close changes
   mechanically if SEC alters posting cadence. Edge claim must state its
   expiry: "timing-stratum conditional drift, expected half-life ≤ weeks".
5. **Trần chi phí:** EOD execution at next open; Q-2 conditional-cost law
   (open costs 3.33×/3.35× midday — open-crossing entries priced at the
   expensive band) + L-SAMV1-3 X1/X2 fill-feasibility. Holding days–weeks ⇒
   low turnover; ceiling on paper: gross per-event expectancy must exceed
   (open-band cost + slippage allowance) at 1.0× and survive 2.0×.
6. **Control đơn giản:** (a) date-only baseline — same filings, decisions on
   filing-date strata without acceptance time: if the date-only control
   reproduces the anchor, acceptance adds nothing (kill);
   (b) permuted-acceptance placebo — acceptance stamps shuffled across
   filings within issuer×form (moves the clock, keeps the event set):
   must NOT reproduce.
7. **Falsifier:** post-acceptance return spread between timing strata ≈ 0
   after costs; or date-only control ≈ anchor; or acceptance-clock signal
   is actually the filing-date signal re-labeled (representation-rho vs
   date-only signal > 0.20 → ancestry/self-collision kill).
8. **Collision với family chết:** STOCKS-NG6 event-conditional forms died by
   ancestry rho (vol_restricted_event_20d 0.260 / dvol_shock −0.320 /
   reversal_5d 0.201 vs bar 0.20) — but NG6's event clock was date-based;
   the acceptance-minute clock is precisely the N2 gap DFV1 recorded
   ("no honest earnings/filing family without publication timestamps").
   Momentum, "cadence-latency" and chain-structure classes are
   ancestry-vetoed (F1). Skeleton check: F-0 must drop the acceptance
   observable and test whether trigger/direction/exit shape collapses into
   the NG6 dead forms — if it does, D1 dies; if the *timing-stratum
   conditioning* is the load-bearing axis (clock-only shadow, Q-7), it is a
   genuinely new information layer (axis 2 new; axis 1 payer partially
   named; axis 3 risk shape = multi-day event book, arguably new vs
   NG6's short-window forms). **KEEP for G2/G3 — priority 1 per owner.**

## D2 — STOCKS: Form 4 insider event flow on the acceptance clock

1. **Payer:** latecomers who trade against persistent post-insider-buy
   drift; under-reactors who discount open-market buys by officers.
2. **Why forced:** insiders have private information advantage; the 2-
   business-day reporting deadline creates a dated, machine-readable event;
   outsiders processing slowly leave the drift. (Classic, must be MEASURED
   on this substrate — SFNG1 already showed one Form-4 observable dead.)
3. **Observable:** form4_stream (546,039 rows, VALIDATED, pin 6ac2cd5b,
   restorable per P-13) with acceptance datetimes + transaction fields;
   4/A amendment corpus with acceptance stamps; join to EODHD bars via
   dated identity map (N4). Decision next open after acceptance.
4. **Edge hết:** insider-signal decay over ~weeks–months; crowding by
   systematic 13F/Form-4 followers; the SEC 2023+ 30-day-delay regime for
   10b5-1 (already reflected in SFNG1 census — 22,622 flagged txs
   post-2023).
5. **Trần chi phí:** same EOD contract as D1; event books are sparse ⇒
   per-event cost dominance must be checked against event frequency
   (ceiling×power grid, DTP I002 template: empty grid = no θ works).
6. **Control đơn giản:** (a) random-date placebo within issuer (same value
   distribution, no insider); (b) matched non-open-market (gift/grant)
   filings — value-matched but non-informative category; (c) date-only
   (acceptance-day vs filing-date) as D1.
7. **Falsifier:** drift after open-market buys ≈ 0 after costs; random-date
   placebo reproduces; representation-rho vs the SFNG1 declared-plan
   cadence signal > 0.20.
8. **Collision:** SFNG1-A4-P1/P2 (10b5-1 declared-plan supply persistence)
   died ANCESTRY_RHO_BLOCK vs goodwill_bloat — the *plan-flag cadence*
   observable is dead. New axes here: acceptance-minute clock + role/value/
   open-market conditioning + amendment-lag (4/A) — different observable,
   but the F-0 skeleton (event → short-side/long-side disposition window)
   is adjacent to SFNG1's shape; the court must decide whether role/value
   conditioning + clock is ≥2 axes new. Amihud/illiquidity classes dead
   (SAMV1/RETEST) — insider events must not be an illiquidity re-label
   (cross-check: condition on liquid names). **KEEP for G2/G3 — priority 2.**

## D3 — STOCKS: corporate-action PIT rebuild → honestly-adjusted state + ex-date event book

1. **Payer (event version):** mechanical flows around ex-dates — index
   funds rebalancing weights at split/dividend effective dates; nominal-
   price/attention effects post-split; dividend-capture inventory shifts.
2. **Why forced:** rules-based holders MUST trade at the effective date
   (index membership, NAV tracking); their counterparties earn any
   temporary imbalance. Must be measured on the rebuilt PIT state.
3. **Observable:** EODHD div/splits files (2,168+2,168 entitled, on disk)
   + 8-K corpus; N3 derivation = rebuild adjusted series FORWARD from
   action dates (never as-of-pull adjusted_close); identity joins N4
   (ticker↔CIK↔CUSIP dated) against the death-inclusive cohort (NG6 panel
   archived).
4. **Edge hết:** ex-date effects are among the most-published anomalies
   (splits 101); any measured premium is presumed contested by dedicated
   corporate-action arbitrage desks — edge claim must clear the Q-6 decay
   question explicitly.
5. **Trần chi phí:** EOD contract; ex-date books concentrate at opens ⇒
   open-band cost applies; ceiling×power grid over event counts.
6. **Control đơn giản:** random-date placebo matched on name/date-range;
   non-action 8-K filings (same filing flow, no action) — the D1 clock
   WITHOUT the action content: if D1-clock explains the ex-date return,
   the action adds nothing.
7. **Falsifier:** ex-date-conditional drift ≈ 0 after costs; placebo
   reproduces; rebuilt-PIT adjusted state does not diverge from served
   adjusted_close at ≥2 vintages in the expected direction (the rebuild
   itself must first PROVE divergence — else it fixes nothing and the
   "new information" claim collapses).
8. **Collision:** momentum dead (multiple); SAMV1-C-REVERSAL5 dead;
   level-break/52W-high families never honestly testable (L-SAMV1-1
   lookahead by construction) — this direction's PRIMARY value is the
   data-plane repair (N3/N4) making honest tests possible; the event book
   itself is thin and the skeleton (ex-date → drift window) collides with
   generic reversal/momentum shapes unless the forced-flow payer
   distinguishes it. **KEEP as data-plane work (N3/N4) + weakest event
   candidate; survives to G2 primarily as authority repair, event book
   only if F-0 clears it.**

## D4 — STOCKS: FTD × price cross

1–8 (abbreviated, court record): payer = locates/buyers-in forced to cover
fails; observable = FTD half-month panel (VALIDATED, live on disk) BUT
availability = posting-bound ≥17 days after settlement half-month end (P-26
binding, DFV1 Lane S ruling); **direct historical scored use is
RETROSPECTIVE_ONLY** — flow/change forms DEAD-ON-ARRIVAL by clock
arithmetic (16–31d staleness, DFV1 measured). Any "conditioning" use is a
D2-control plane at best. **VERDICT (A1): NOT SCORED — control-plane-only
this cycle; no owner action can change the posting clock (it is the SEC's
publication cadence). Recorded, not killed-as-class (state-conditioning
remains legal as a CONTROL for D1/D2 falsifiers).**

## D5 — CRYPTO: funding settlement / forecast-funding surprise

1–8 (abbreviated): payer = funding payers holding against the crowd;
observable = settled 8h funding (VALIDATED) + forecast funding via
premiumIndexKlines (DFV1 PS1 verified, 7MB). **COLLISION (decisive):** the
funding plane is closed by identity — TRACKB1 continuous pooled rho 1.0000
vs CARRY-BAB ("the lawful entry observable IS the dead carry class's
observable"); PWS-CX-SOLUSDT I001 tail-payer-run-regime killed by
representation math (P-29: sign-run ≈ level-window); SRLV-CX M1
settle-adjacent dead BOTH directions; V17 FUNDJUMP dead. Forecast funding
is a smooth input of settled funding (representation-rho expected high —
one-evening measurement per P-29 template). P-27 law: better data on the
same skeleton is not a new mechanism. **VERDICT (A1): VETO-RECOMMEND
(ancestry identity).**

## D6 — CRYPTO: liquidation / forced-flow cascade

1–8 (abbreviated): payer = forced liquidators; observable = **NONE with
authority** — liquidationSnapshot 404 (measured, BTC-H4-TWO-REGIME E3);
historical OI/liq/L2 zero bytes on disk (DFV1 incident I-1: V14 archive
ABSENT, unrecoverable locally); vendor corpus O2 = provider-gated; owner
law verbatim: "Không suy ra order book hay forced flow từ nến" (no
inference from candles). **VERDICT (A1): BLOCKED_DATA — no PIT observable
exists at decision time within current authority. Owner action (runbook
R4/O2): vendor-quote decision for PIT liquidation tape; until then this
class is closed-but-not-adjudicated (UNDETERMINED w.r.t. data, per DFV1 —
not evidence of absence).**

## D7 — CRYPTO: delta-neutral basis/carry convergence

1–8 (abbreviated): payer = segmented capital paying the basis/funding
premium. **COLLISION (decisive):** ERP1-TRACKB admitted exactly one lawful
class and killed it by identity (rho 1.0000 vs CARRY-BAB); BASISLV axis
0.3337 also over bar; PREMFADE-28D dead fold-conc (V14); CARRY-1D/3D/7D
dead. Reopening conditions preregistered by TRACKB: non-funding-level PIT
axis (= D6, itself blocked) or dated measured cost-regime break (none).
**VERDICT (A1): VETO-RECOMMEND (ancestry identity; plane closed).**

## D8 — FX: after-cost event families (macro-release clock / session liquidity)

1–8 (abbreviated): payer = macro-data-reactive flow. **COLLISION +
BLOCK:** macro release-clock class dead across two tracks (FXFV5-A6
pre-release-avoidance; RATESNG1 clock-shadow falsification #16; COMMNG1
release-clock law; P-24: "the release calendar owns the money"); FX
after-cost frontier BLOCKED_BROKER_COST_AUTHORITY (DFV1 census #4:
components 3–6 need account-bound bytes; ERP1 floor 3.6/4.4 pips — across
38 forex failures no honest gross premium ever reached it); IBKR tick
geometry makes conditional crossing arithmetically unattainable at
IDEALPRO (≥0.5 pip tick ⇒ ≥1.0 pip crossing @k=2.0 vs frozen 0.41);
FOREX-NG1: re-entry needs materially new evidenced source. Owner today:
FX không score trên frontier đã đóng. **VERDICT (A1): NOT SCORED (dead
class + cost-blocked). Owner action (runbook R1): IBKR statement + FX
delayed data enable a FUTURE cost-authority cycle; range-fade replication
needs R2 replication source. Neither is this cycle.**

---

## Skeleton-merge + COURT RULING (G1 final, 2026-09-27 — skeptic report applied)

Skeptic report: `SKEPTIC_REPORT.md` (fresh-context subagent, VETO power,
independent reads incl. substrate re-measurement). Court = A1 applying the
skeptic's rulings. Three material corrections to the A1's draft:

1. **D3's ex-date event book VETOED** (skeptic): the payer story is
   mechanically false — index weights are split-invariant, so index funds
   do not trade at split ex-dates; no forced flow exists for the named
   classes; the residual pattern collapses into measured-dead reversal
   classes (SAMV1-C-REVERSAL5, SFV3-A5-IDIO-SHOCK-REVERSAL, NG6 reversal_5d
   ec 0.201) and the anomaly is Q-6-published. The **N3/N4 data-plane
   repair survives as G2 authority work** (it fixes L-SAMV1-1 for FUTURE
   families) but carries no scored identity this cycle.
2. **D2's amendment-lag (4/A) arm DROPPED at freeze** (skeptic): SFNG2-A4-
   P1/P2 died fail-closed on exactly that form (v11 cadence-latency
   UNMEASURABLE — zero panel entities with >460d gaps; Q-6 = 0 bookable
   2025 decisions), the 4/A corpus is frozen at 3,062 accessions, and
   www.sec.gov is now 403 — no lawful widening. D2 keeps ONLY the
   original-filing acceptance-clock flow.
3. **D1 KEEP is CONDITIONAL**: reachability (measured 200) ≠ sufficiency —
   the 1000-recent cap + paged `filings.files` history depth over the
   death-inclusive issuer cohort is UNMEASURED; a staged G2 probe must
   measure acceptance-history depth before identity freeze becomes
   operable. Stocks execution-cost components are 0/10 measured ⇒ all G6
   ceilings are PROXY-PRIOR (labeled as such; measured-beats-stated Q-8
   applies).

**Skeleton-merge ruling:** D1 and D2 share ONE information layer (EDGAR
acceptance clock) and one F-0 skeleton (EDGAR filing event → next-open →
multi-day drift book) but differ on payer + information payload (2 of 3
axes) with different ancestry fences (NG6 event-forms vs SFNG1
plan-cadence) ⇒ **two distinct identities, one shared control battery**
(date-only baseline; permuted-acceptance placebo; clock-only shadow per
Q-7/Q-11). Preregistered merge condition: if D2's drift is
indistinguishable from generic filing-flow drift (representation-rho > 0.20
vs D1 signal), D2 collapses into D1 as a neighbour arm at the G3 court.

| Direction | A1 verdict | Skeptic verdict | COURT FINAL | One-line reason |
|---|---|---|---|---|
| D1 | KEEP (prio 1) | KEEP (conditions) | **KEEP → G2/G3 conditional on depth probe** | acceptance-minute clock = the untested N2 information layer; NG6 events verified date-based, no skeleton collision |
| D2 | KEEP (prio 2) | KEEP (fenced) | **KEEP → G3 WITHOUT amendment arm** | payer/payload distinct from D1 (≥2/3 axes); SFNG1 boundary = plan-cadence observable, not insider-flow |
| D3 | KEEP (prio 3, data-plane + event book) | SPLIT: data-plane KEEP, event book VETO | **data-plane G2 work only; event book VETOED** | payer story mechanically false; residual = dead reversal classes |
| D4 | control-plane-only | concur | **CONTROL-PLANE-ONLY** | P-26 ≥17d posting bound kills every PIT flow form (DFV1 Lane S law) |
| D5 | veto-recommend | VETO | **VETOED** (ancestry identity) | TRACKB1 rho 1.0000; FUNDJUMP 0.2439; SRLV both directions; P-27/P-29 |
| D6 | BLOCKED_DATA | concur (verified no keyless PIT source exists) | **BLOCKED_DATA** | no PIT liquidation tape in authority; O2 owner-gated; candle-inference forbidden |
| D7 | veto-recommend | VETO | **VETOED** (plane closed) | TRACKB1 reopening conditions unmet (needs non-funding PIT axis = D6, itself blocked) |
| D8 | not-scored | concur | **NOT SCORED** (dead class + cost-blocked) | release-clock dead two tracks; ERP1 floor; owner verbatim FX ban |

**Identities to G3: exactly 2 (EMV1-A1 filing-flow acceptance-clock,
EMV1-A2 insider-flow acceptance-clock), both stocks** — under the ≤3 cap,
honoring the owner's stocks priority. NO_ELIGIBLE_PROPOSAL remains the
lawful terminal if G2 kills a survivor. Skeptic substrate re-measurement
recorded: v13 archive present (345,150 Form-4 XMLs + 2,168+2,168 div/splits
files), NG6 panel archive present, eod_cache 111,323 files on disk but
sha-unpinned (N9 defect carried).
