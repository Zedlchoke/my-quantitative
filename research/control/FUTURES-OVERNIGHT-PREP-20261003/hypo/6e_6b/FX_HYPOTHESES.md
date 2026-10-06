# FX_HYPOTHESES — 6E / 6B competing-hypothesis family portfolio (P1-6E6B)

- Task: `FUTURES-OVERNIGHT-PREP-20261003`, lane **P1-6E6B**, generated
  2026-10-04 UTC. Worktree HEAD at write: `72c9bc5b` (batch-1 checkpoint;
  dispatch_sha == actual_start_sha == `72c9bc5b1d94b812044a9bd21768c53b4d378436`).
- Class: PREP hypothesis dossier. **0 PnL, 0 scored runs, 0 sweeps, 0 selection
  by any return statistic.** Every parameter **[PROVISIONAL]**. Outcome-blind.
- **PB2 remains HOLD by Co-Owner ruling.** Nothing here proposes reopening; the
  London-range family's trial census is written as **CONTINGENCY ONLY** (§8).
- Evidence base consumed in full before writing (this worktree):
  `FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/deep/6e_6b/{6E,6B}_DEEPFOUR_V3_ADDENDUM.md`
  (addendum §n), `PB2_ANCESTRY_COURT_DRAFT.md` (court §a–§d),
  `FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/source/FEES_CORRECTED.md`
  (FEES §n — **tier-1 all-in 6E/6B = 2.46 USD/side, corrected; MODELED COST;
  account NOT_RUN; UNDER REVIEW until a new A7**),
  `.../cme_cal_gap/fx_comm/FXCOMM_GAPFILL_EVIDENCE.md` (FXCAL §n — FX expiries
  208/272, 2010-2022 complete per symbol, 2023-2026 NOT_OBTAINED; FX holiday
  times 2017-2023 expanded),
  `.../bls_vintage/BLS_VINTAGE_INVESTIGATION.md` (BLSV §n — 2025-vintage law),
  parent `events_bbo_coverage/bls_dates.json` (A5 grid: CPI/EMPSIT
  PASS_EVIDENCED_CALENDAR 2010-2026, 204/204 rows @08:30 ET each), dossiers v2
  + DATACONTRACT (DC §n) + PLAYBOOKS r5 (PB §n) + SUMMARY_QUAL_ACTIONS r6
  (SQA §n), and the v2 analysis JSONs cited as `script:field`. Every cited
  local artifact is sha256-pinned in `captures/source_sha256.tsv`.
- Taxonomy (labels used throughout): **FACT** (primary source + date) /
  **OBSERVED** (script + window) / **MECHANISM_HYPOTHESIS** (unmeasured
  mechanism) / **INFERENCE** (reasoning over measured inputs) / **NOT_RUN**
  (missing evidence is never PASS) / **DERIVED** (arithmetic from named
  measured inputs).

---

## 0. Portfolio overview — why these families genuinely compete

Six families. Each symbol gets **four tradable-window families** (F1–F4) plus
two **conditioning overlays** (F5–F6, H-G law: conditioning, never standalone
signals). The competing structure is enforced by mutually exclusive day-sets
and different clock anchors, not by parameter variation:

| id | name | symbols | window / anchor | mechanism class | day-set relation to F1 |
|---|---|---|---|---|---|
| FX-F1 | London-Range Absorption (H-C vs H-D) | 6E, 6B | London 08:00–11:00 range, trigger 11:00–15:30 local, hold → 16:00 CT | liquidity-absence information discovery vs over-extension | — (base excludes event days) |
| FX-F2 | Policy-Decision Resolution | 6E (FOMC anchor; ECB stratum), 6B (MPC anchor; FOMC stratum) | decision minute +13:00 CT (6E) / +12:00 London (6B) | scheduled-uncertainty resolution: drift vs reversal after the spike | **exactly F1's excluded days** |
| FX-F3 | US-8:30 Spillover into the London book | 6E, 6B | 07:30 CT (08:30 ET) release minute, known-type days | information transfer from US data into still-open London window | **the ×1.95 spike inside F1's trigger window** (K1 reclassification path) |
| FX-F4 | Globex Reopen Gap | 6E, 6B | 17:00 CT reopen vs 16:00 CT prior close | liquidity-provision timing vs clock-law artifact | different session segment (evening open) |
| FX-F5 | Rate-Differential Regime Conditioning | 6B-primary, 6E (fragile) | overlay on F1/F4 | CIP regime splits conditioning (H-G law) | overlay |
| FX-F6 | Crowded-Positioning Conditioning | 6E-primary | overlay on F1/F4 | positioning-crowding → forward-vol conditioning | overlay |

Genuine-competition proof [INFERENCE]: F2 trades precisely the days F1 stands
aside (ECB GC 55 / BoE MPC 56 / FOMC 58 in panel); F3 attributes F1's trigger
window's largest scheduled volume spike (07:30 CT ×1.95) to a source F1's
mechanism does not mention; F4 sits in a different segment of the same 23h
session with a different natural experiment (DST-mismatch weeks). If F1's
effect is "really" F2's or F3's day-type, K1 kills F1 — the families falsify
one another by construction. This is not disguised multi-trials of one idea.

---

## 1. FX-F1 — London-Range Absorption (H-C continuation vs H-D fade)

**Status: PB2 ancestry pair. HOLD by Co-Owner ruling — this section is a
consolidated [PROVISIONAL] spec + contingency census only. It does NOT propose
reopening.** Full 11-field table lives in addenda §9 (6E/6B) and court §c;
repeated here in compressed form for portfolio completeness.

1. **Mechanism** [MECHANISM_HYPOTHESIS]: London-morning flow discovers
   information while US liquidity is absent; a 1m close outside the
   08:00–11:00 London range encodes it; arriving US liquidity either continues
   (H-C) or absorbs-and-fades (H-D) the move to 16:00 CT. OBSERVED anatomy:
   London-local 08:00–12:00 = 21.59% of 6E volume vs 17.14% for fixed CT
   02:00–05:00 [`6E_a2_sessions.json:london_views`]; London morning 16.60% of
   session RV, top per-session median share 17.6% [`6E_a2_sessions.json:
   rv_share_by_segment`]; DST-mismatch weeks shift the volume profile by
   exactly one CT hour (h+02 6.79→4.71, h+03 5.64→6.80; 159,982 bars)
   [`6E_a2_sessions.json:dst_mismatch_effect`; 6E addendum §3]. 6B: London
   07:00–12:00 share 28.7% (2020-21) → 23.7% (2025-26) [`6B_a2_sessions.json:
   london_morning_share_07_12`].
2. **Expected direction, falsifiable**: H-C — E[ret | first 1m close above
   R_lon] > 0 and E[ret | below] < 0 (sign-carry); H-D — the same two
   conditionals carry the opposite signs. The two cannot both survive (PB §0).
3. **PIT availability**: ECB GC 55/55 machine-verified (D4, SQA §D4); BoE MPC
   assembly PASS_EVIDENCED (6B_v2 §0); FOMC 58/58 in-panel time-proof
   [`6E_a4_events.json:fomc`]. All exclusion calendars PASS_EVIDENCED.
4. **Contract/session/roll**: 6E EUR 125,000, USD per EUR, tick 5e-05 =
   $6.25, 0 violations on 3.05M bars; 6B GBP 62,500, tick 0.0001 = $6.25
   adjudicated (GLBX 19,183 rows). LOCAL-CLOCK LAW: all bucketing
   Europe/London local (DST-proven both symbols; BoE anchor minute-720
   stable). Roll: 6E Friday-of-expiry-week 27/27 volume-crossover measured;
   6B PIT k=5 + cease-guard, thin-window 1,069..13,222 contracts/day measured.
   Expiry dates official 2010-2022 (208/272; FXCAL §1), **2023-2026
   NOT_OBTAINED — IMM-rule derivation forbidden**; families touching 2023+
   expiries declare the gap (none of F1's windows touches expiry timing beyond
   the roll rule already bar-validated 80/80 on 6E).
5. **Entry/stand-aside/exit [PROVISIONAL]**: trigger = first 1m close strictly
   outside R_lon during 11:00–15:30 London; fill = open next 1m; **mandatory
   delay variants +1 bar and +30m**; base-EXCLUDE ECB GC (6E) / MPC (6B) /
   FOMC days, INCLUDE = sensitivity leg only (Co-Owner decision at any
   reopen); London-morning coverage <80% EXCLUDE (load-bearing on 6B thin
   k=5 windows); warmup 60d; calendar-uncertain dates EXCLUDE/NOT_RUN (now
   largely closed by FXCAL §2 for 2017-2023 holidays; 2024-2025 holiday times
   still NOT_OBTAINED). TP 2×SL; SL 1.0×ATR(20d); same-bar SL-priority; time
   exit 16:00 CT.
6. **Controls**: C1 clock/placebo (multi-seed ≥100, seeded random-sign at
   identical entry times); C2 always-in-London-window; C3 weekday-matched
   non-event clock (same weekday distribution, event days removed — the
   family-specific negative); C4 delay-pair; 6B adds the **London-share-drift
   split 2020-22 vs 2023-26 (28.7→23.7%) as built-in falsifier**; 6E/6B
   trigger co-occurrence diagnostic (court §b1.3).
7. **Refutation**: mechanism-level K1–K5 (addenda §9), incl. K1 event-day
   reclassification → family belongs to FX-F2/F3; K4 DST-mismatch sign flip =
   clock-law bug. Cost-level: 6E modeled RT ≈ 3.6–6.3 bp, 6B ≈ 6.3–11.2 bp
   (§7 below) vs court MDE 3.27/3.88 bp at full n=1,573/1,572, 5.80/6.88 bp
   at n=500 — **at realistic trigger densities (300–900) MDE 4–9 bp sits at
   or above the full modeled cost; both-arms-below-floor ⇒ dead (K2)**.
   Census gate ≥500 triggers/symbol [PROVISIONAL] BEFORE any scored spec.
8. **Cost sensitivity**: MODELED COST; fee layer now CORRECTED (2.46 USD/side
   T1, FEES §2) but UNDER REVIEW until a new A7; spread close-proxy
   $18.75/side high-biased (BBO NOT_RUN); slippage {1,2,3} ticks/side
   assumptions. Words "measured cost"/"complete cost" FORBIDDEN.
9. **Regime breaks**: K5 rolling 2020-22 vs 2023-26 sign stability; 6E
   v1-window percentile 6.8th (quiet-regime calibration hazard); 6B VR21 0.73
   mean-reversion suspended in 2022 (VR21 0.98).
10. **Coverage**: 6.8y 2020-01→2026-09; 1,746 held-chain sessions ×2; serials
    dead (6E 0.34% volume; 6B 57 dead serial clusters); strays isolated
    (6JZ7/SIJ5 filtered; GCQ4 + 6BM5 quarantined); 0 OHLC/zero-vol/duplicate
    violations on 3.05M/2.55M bars.
11. **Sources**: all citations above are local artifacts sha256-pinned in
    `captures/source_sha256.tsv` (addenda, court, dossiers, DC, PB, analysis
    JSONs). Upstream URL/archive authority documented inside those artifacts
    (ECB press-release scheme, bankofengland.co.uk MPC pages, archived
    federalreserve.gov, cmegroup.com captures).

---

## 2. FX-F2 — Policy-Decision Resolution (6E: FOMC-anchored; 6B: MPC-anchored)

1. **Mechanism** [MECHANISM_HYPOTHESIS]: scheduled macro uncertainty resolves
   at a known minute inside a continuously-traded 23h venue with local-clock
   structure. Two competing microstructure stories: **R-C (resolution
   drift)** — the statement resolves a genuine uncertainty premium; late-arriving
   liquidity keeps processing the news for hours (underreaction/limited
   attention at the 23h venue's dispersed participants) and price drifts in
   the spike direction; **R-D (spike reversal)** — the first-minute print is a
   liquidity-hole overshoot (thin resting depth at the release minute) that
   arriving liquidity corrects. OBSERVED anatomy:
   - 6E FOMC statement minute 13:00 CT (minute 780): median volume ×17.24 vs
     control Wednesdays same minute; +5m ×9.96; +10m ×5.61; **re-amplifies
     ×8.81 at minute 820 (13:40 CT — the press-conference/Q&A complex)**;
     88.9% of the 12:00–16:00 CT volume arrives after 13:00 on event days vs
     68.8% on control Wednesdays [`6E_a4_events.json:fomc` →
     `volume_ratio_event_vs_control`, `share_of_1200_1600_volume_after_1300ct`;
     6E addendum §5]. **The single largest scheduled 1m-volume event of the
     6E day — FOMC, not ECB** (ECB decision minute is ×1.73, a different
     class) [`6E_a4_events.json:ecb` → `volume_ratio_event_vs_control.m435`].
   - 6B MPC first-5m 18.7× (7,090.5 vs 379.5 contracts), ±30m 5.2×, spike
     minute exactly 720 London-local (3,450.8/min) and **minute-stable across
     8 UK/US DST-mismatch dates (07:00 CT except 2022-10-06 06:00 CT)**
     [`6B_a4_events.json:boe`; `6B_a2_sessions.json:
     boe_1200_london_in_ct_clock`, `mpc_day_top5_minutes`]; FOMC secondary on
     6B at 9.5× first-5m [`6B_a4_events.json:fomc`].
   - Event-window execution law (6B_v2 §8-H2'): entry must assume ≥1 minute
     post-release; same-minute fills are optimistic against the 18.7× spike.
2. **Expected direction, falsifiable**: R-C — E[ret from T+60s fill to 16:00
   CT | sign of the first-5m move after the decision minute] carries the same
   sign; R-D — carries the opposite sign. Secondary strata: ECB-decision days
   (6E, ×1.73 class), FOMC days (6B, 9.5× class) — predicted weaker, and the
   strength ordering across strata is itself part of the falsifiable claim
   [MECHANISM_HYPOTHESIS: resolution-drift scales with event intensity].
3. **PIT availability**: FOMC 58/58 in-panel with in-document release-time
   proof (archived federalreserve.gov HTML on disk; 53 at 13:00 CT, remainder
   2020 emergency timings disclosed) [FACT/OBSERVED, `6E_a4_events.json:
   fomc`; 6B_v2 §0 M4]. BoE MPC calendars 2020→2027 PASS_EVIDENCED
   (assembly-method disclosed; rate-change subset == local parquet). ECB GC
   55/55 machine-verified. **Surprise/decision-content data NOT_RUN** (no
   consensus vintages on disk) ⇒ the family conditions on the EVENT and
   first-5m realized sign, never on a surprise measure — stated as a design
   limitation, not a claim.
4. **Contract/session/roll**: identical to F1 §1.4 (tick/orientation/
   local-clock/roll laws). Anchor minutes: 13:00 CT (FOMC, both symbols), 780
   CT-minute; 12:00 Europe/London (MPC, minute-720 anchor, DST-proven). No
   expiry-window contact; 2023-2026 expiry-date gap irrelevant to this family
   (roll rule bar-validated; declared anyway per law).
5. **Entry/stand-aside/exit [PROVISIONAL]**: universe = the EXCLUDED day-sets
   of F1 (6E: FOMC days, with ECB-day stratum; 6B: MPC days, with FOMC-day
   stratum). Signal = sign of the 1m close move over the first 5 minutes
   after the anchor minute. Fill = open of the bar at anchor+6m (T+60s law);
   **mandatory delay variants +1 bar and +30m** (spike-decay artifact
   detector; the ×9.96/+5m decay means fill timing is first-order here).
   Stand-aside: (i) days where the anchor minute is missing/rare-timed
   (2020 emergency FOMC timings — EXCLUDE from base; sensitivity only);
   (ii) MPC change-vs-hold split reported as descriptive strata (22 change /
   34 hold measured; change days show larger first-5m volume and |move|)
   [OBSERVED, `6B_a4_events.json:boe`] — base pools, strata reported;
   (iii) warmup 60d. Exit: TP 2×SL, SL 1×ATR(20d), same-bar SL-priority,
   time exit 16:00 CT (6E FOMC 13:00 CT anchor leaves a 3h holding window;
   6B MPC 12:00 London ≈ 06:00/07:00 CT leaves ~9h).
6. **Baselines/placebo/negative controls**: C1 clock/placebo — same anchor
   minutes on NON-event Wednesdays/Thursdays, random sign, multi-seed (this
   is exactly the weekday-matched non-event clock negative); C2
   always-in-window baseline = unconditional entry at the same anchor minute
   every event day regardless of first-5m sign (does the SIGN carry
   information or just the day?); C4 delay-pair; family-specific negative =
   **the ECB stratum on 6E** (a scheduled central-bank event with an
   order-of-magnitude weaker spike — if "post-decision drift" appears with
   equal strength on ×1.73 and ×17.2 events, the mechanism is day-of-week
   artifacts, not resolution intensity).
7. **Refutation**: mechanism-level first: (i) both R-C and R-D below Stage-A
   floor ⇒ family dead; (ii) sign-ordering across intensity strata (×18.7 /
   ×9.5 / ×1.7) must be monotone in event intensity, else resolution-
   intensity story dead; (iii) K4-analog — effect flips with CT-vs-local
   bucketing on MPC days (minute-720 stability is the measured anchor);
   (iv) first-5m sign must not be predictable pre-release (else look-ahead —
   PIT violation). **Power honesty [DERIVED from court §c3 method]: n=58
   (6E FOMC) → MDE ≈ 12.97×√(100/58) ≈ 17.0 bp/trade; n=56 (6B MPC) →
   ≈ 15.38×√(100/56) ≈ 20.6 bp — versus modeled RT cost 3.6–6.3 bp (6E) /
   6.3–11.2 bp (6B). The court can only detect effects ~3–5× the full
   modeled cost; a cost-scale edge is undetectable at n≈56-58. This family's
   minimum-survivable-cost reasoning: it survives power ONLY with effects
   ≥17-21 bp/trade, i.e. tail-event-scale post-decision moves; anything
   smaller is unrecoverable at this n.** Event-day dispersion is itself
   elevated (first-5m |ret| 7.6× control), so the daily-σ proxy may
   understate MDE — stated as a bias direction, not a number [INFERENCE].
8. **Cost sensitivity**: MODELED COST; 2.46 USD/side T1 CORRECTED (under
   review); spread close-proxy high-biased ($18.75/side); slippage {1,2,3}
   ticks — **slippage is first-order on this family**: fills sit inside a
   decaying ×9.96→×5.6 volume spike; tier-3 slippage (2.7 bp/side 6E, 4.6 bp
   6B at mid-px) plausibly understates spike-minute reality (BBO NOT_RUN).
9. **Regime/era breaks**: 2020 emergency-timing FOMC excluded from base;
   2022 policy-cycle regime (6B change-days cluster) reported as stratum;
   2020-22 vs 2023-26 sign stability mandatory (K5 analog).
10. **Coverage**: event days are a subset of the same 6.8y panels (1,746
    sessions/symbol); no extra holes: FOMC 58 in panel (6E) / 58+1 dates
    (6B, M4-disclosed), MPC 56, ECB 55 — all PIT-verified; zero missing
    event-day bars (session coverage median 1,356 bars 6E).
11. **Sources**: local analysis JSONs + addenda (sha256 in
    `captures/source_sha256.tsv`); upstream URL/archive authority:
    federalreserve.gov archived HTML (FOMC time proof, documented in 6E_v2 §6
    / 6B_v2 §0), bankofengland.co.uk "MPC dates for YYYY" pages (fetched
    2026-10-02, method disclosed in 6B_v2 §0), ecb.europa.eu press releases
    (D4 lane verification, SQA §D4). No new web numerics fetched this lane.

---

## 3. FX-F3 — US-8:30 Spillover into the Still-Open London Book

1. **Mechanism** [MECHANISM_HYPOTHESIS]: US data releases at 08:30 ET (07:30
   CT) transfer information into a European-morning book that is still open
   and carrying its own flow; because the London window's US-absent liquidity
   is thinner, the imported print is either (a) **continued** as London
   liquidity re-prices consistently with the US news (S-C), or (b) **faded**
   as the spike is a temporary dislocation between two liquidity pools
   (S-D). This family deliberately targets the largest scheduled spike
   INSIDE F1's trigger window: if F1's "London discovery" is really US-data
   spillover, F1 dies by K1 and this family owns the effect. OBSERVED
   anatomy: 07:30 CT median volume 277 vs 142 the minute before (×1.95),
   range 0.0003 vs 0.0002 (×1.5), present 1,732/1,746 sessions, **every
   weekday**, event-type decomposition NOT_RUN in the raw measurement
   [`6E_a2_sessions.json:us_830et_block`]; the 06:30–08:00 CT ECB/US-data
   block carries **15.58% of session RV on 12.5% of volume — the highest
   information-per-contract segment of the 6E day** [`6E_a2_sessions.json:
   rv_share_by_segment`]. 6B: 07:00–12:00 London share drift 28.7→23.7% with
   the 08:00 London hour falling hardest (7.7→5.7%) — the US-macro dominance
   drift [OBSERVED, `6B_a2_sessions.json`; 6B addendum §3].
2. **Expected direction, falsifiable**: on CPI/EMPSIT-known days, E[ret from
   07:31 CT fill to a fixed horizon | sign of the 07:30 CT 1m move] carries
   sign (S-C) or opposite sign (S-D). Additional falsifiable layer: the
   known-release-day effect differs from the "quiet 8:30" days (days with no
   known CPI/EMPSIT release still show the ×1.95 volume spike — other/weekly
   releases — so the sign-carry must be WEAKER on unclassified days if the
   mechanism is information, not clock).
3. **PIT availability [now partially unlocked — this family exists because of
   it]**: **BLS schedule calendars PASS_EVIDENCED** — CPI 204/204 rows
   2010-2026, EMPSIT 204/204, all stamped 08:30 AM ET, official archive
   snapshots with timestamps [FACT, `events_bbo_coverage/bls_dates.json`
   verdicts; BLS_PIT_EVIDENCE.md]. **Vintage law mandatory (BLSV §5)**: for
   decision date D use the schedule vintage as known at D — dated captures;
   2025 late-year revision: CPI Sep-ref Oct 15→24, Oct-ref CANCELED, Nov-ref
   Dec 10→18; EMPSIT Sep-ref Oct 3→Nov 20, Oct-ref CANCELED, Nov-ref Dec
   5→16; **2025 actual prints: 11 CPI / 10 EMPSIT — a backtest assuming 12/12
   is structurally wrong**; the two canceled-but-expected releases'
   NON-arrival was itself information; 2026 recurrence already visible (ics).
   NOT_RUN: actual-publish-latency vs BLS API/ALFRED (inherited); full
   release-type census of ALL 8:30 ET events (PPI, retail sales, GDP,
   claims...) — NOT_RUN ⇒ base family is restricted to CPI+EMPSIT-known
   days, with "other 8:30 days" as a separately-reportable stratum, never
   pooled into the base.
4. **Contract/session/roll**: identical to F1 §1.4. Anchor minute 07:30 CT
   falls inside London-local morning (13:30 London winter / 14:30 summer DST
   states — bucket by Europe/London law for the RESPONSE window; the anchor
   itself is America/New_York 08:30 ET, fixed by BLS). No expiry contact.
5. **Entry/stand-aside/exit [PROVISIONAL]**: signal = sign of the 07:30 CT 1m
   close-to-close move on CPI/EMPSIT-known days (vintage-correct as-of-D);
   fill = open of 07:31 CT bar; **mandatory delay variants +1 bar and +30m**
   (the dispatch law — this window's spike is the reason delay variants
   exist); stand-aside: (i) days whose as-of-D expected release was CANCELED
   or moved are handled by the vintage table — canceled days are NOT event
   days (and form a natural negative-control stratum: expected-but-canceled);
   (ii) days overlapping ECB GC / MPC / FOMC — EXCLUDE base (double-event
   contamination; the 07:30 and 13:00 CT anchors are distinct but the
   holding windows overlap on 6E), sensitivity only; (iii) DST-mismatch
   weeks where 07:30 CT's London-local position shifts — report split;
   (iv) warmup 60d. Exit: TP 2×SL, SL 1×ATR(20d), SL-priority, time exit
   16:00 CT.
6. **Baselines/placebo/negative controls**: C1 clock/placebo at 07:31 CT on
   non-release weekdays, multi-seed; C2 always-in at 07:31 CT every day
   (clock vs information); C4 delay-pair; family-specific negatives:
   (a) **weekday-matched non-event clock** (Thursdays-without-EMPSIT for
   EMPSIT strata etc.); (b) **expected-but-canceled 2025 days** (4 days:
   CPI Nov 13, EMPSIT Oct 3 + Nov 7 as-known windows — the information
   arrived as NON-arrival; if the family's effect appears equally on these
   days, it is a calendar artifact, not information transfer) [DERIVED from
   BLSV §5]; (c) unclassified-8:30 stratum must show weaker sign-carry than
   CPI/EMPSIT days.
7. **Refutation**: mechanism-level: (i) sign-carry on known-release days ≤
   placebo band ⇒ S-C and S-D both dead; (ii) known-release-day effect ==
   unclassified-day effect ⇒ clock artifact, not information (the family's
   core distinction); (iii) effect survives only when overlapping
   central-bank days are INCLUDED ⇒ reclassify to FX-F2. Power [DERIVED,
   court §c3 method]: known-type n ≈ 165/symbol (CPI ~83 + EMPSIT ~82,
   2020-2026 vintage-corrected) → MDE ≈ 10.1 bp (6E) / 12.0 bp (6B) vs
   modeled RT 3.6–6.3 / 6.3–11.2 bp — **detectable only for effects ~1.6–3×
   full cost at base tiers; per-release-type strata (n≈82) are MDE ≈ 14-17
   bp and effectively exploratory**. Minimum-survivable-cost: needs
   ≥10-12 bp/trade gross at pooled n; pooling CPI+EMPSIT is a design claim
   ("US-hard-data 8:30 class") that must be declared, not silently assumed.
8. **Cost sensitivity**: MODELED COST; 2.46 USD/side T1 corrected (under
   review); spread close-proxy high-biased; slippage {1,2,3} — spike-minute
   fills are the family's own subject; tier sensitivity is a first-order
   result, not a footnote.
9. **Regime/era breaks**: BLS vintage regime break 2025 (hard); 2020-22 vs
   2023-26 sign stability (K5 analog); 6B London-share drift split mandatory;
   2022 LDI/fiscal crisis (6B top-8 stress windows all end 2022-11-28→12-20)
   as a declared high-vol stratum.
10. **Coverage**: CPI/EMPSIT calendars complete 2010-2026 (204/204 each) —
    full-window coverage inside 2020-2026 panel; expected-but-canceled days
    enumerated (4 in 2025); latency NOT_RUN is the open hole (schedule vs
    actual feed availability — inherited, owner-gated).
11. **Sources**: `bls_dates.json` + `BLS_PIT_EVIDENCE.md` (parent A5, local,
    sha256-pinned), `BLS_VINTAGE_INVESTIGATION.md` + machine companion (P2C
    lane; 43 captures with sha256 under `bls_vintage/captures/`; URLs =
    bls.gov schedule pages + web.archive.org replays, documented therein);
    anatomy from `6E_a2_sessions.json` / `6B_a2_sessions.json` (pinned).
    **No new web numerics fetched by this lane** — the vintage tables are
    consumed from P2C's captures (fetch_log records the zero-fetch decision).

---

## 4. FX-F4 — Globex Reopen Gap (17:00 CT reopen vs 16:00 CT prior close)

1. **Mechanism** [MECHANISM_HYPOTHESIS]: the 23h venue closes 16:00 CT and
   reopens 17:00 CT after a 1h maintenance break. Two competing stories:
   **G-C (gap continuation)** — the reopen auction's price discovery continues
   into the overnight/Asia session (momentum in liquidity-provision timing:
   the first-hour sign predicts the session-leg sign); **G-D (gap
   mispricing/revert)** — the reopen print is a liquidity-provision artifact
   (thin initial depth; median first-30m Sunday volume only 1,306 contracts
   vs session median 156k total [OBSERVED, `6E_a2_sessions.json:
   sunday_evening_open`]) that mean-reverts once Asia's primary liquidity
   arrives. The DST-mismatch weeks are the natural experiment separating
   liquidity timing from clock-law artifacts (K4). OBSERVED anatomy: session
   template 17:00 CT (D-1) → 16:00 CT (D), 23h + break, 348/1,746
   Sunday-evening opens (1.9% of front volume) [6E addendum §3]; **reopen-gap
   vol is large relative to the day: gap std 0.3778% vs full-day return std
   0.4695% (ratio 0.805, n=1,739, measured directly on the 23h venue —
   replacing v1's RTH-only proxy 0.79)** [`6E_a2_sessions.json:
   v1_gap_remeasure`]; DST-mismatch 1-hour profile shift (159,982 bars)
   [`6E_a2_sessions.json:dst_mismatch_effect`]. 6B: 2,549,633 rows, 0 weekend
   bars, exactly 1 maintenance-break bar in 6.8y [OBSERVED, `6B_a7_quality`;
   6B addendum §3]; **6B gap-std anatomy NOT_RUN** (declared hole).
2. **Expected direction, falsifiable**: G-C — E[session-leg return from
   17:05 CT fill to a fixed horizon | sign of the reopen gap] carries sign;
   G-D — opposite. Sub-claims: effect differs between Sunday opens (348) and
   weekday opens (break-only) and between DST-mismatch and aligned weeks.
3. **PIT availability**: no external calendar needed for the base (reopen
   times are the venue's own template, measured); holiday/early-close days
   now official for FX 2017-2023 (FXCAL §2 — incl. the **2022 Monday-halt
   regime change: 12:00 CT halt 2017-2021 GONE by 2022 → 16:00 close +
   17:00 reopen; year-aware pipeline mandatory**), 2024-2025 holiday times
   NOT_OBTAINED — those days EXCLUDE/NOT_RUN. Gap definition uses prior
   16:00 CT close from the same held chain — no external data.
4. **Contract/session/roll**: identical to F1 §1.4. Roll interaction is
   first-order here: 6E rolls AT the close of the Friday of expiry week —
   roll-session gaps are chain-construction artifacts, excluded by law
   (roll-boundary returns excluded on both chains, 6B_v2 §0.1); 6B k=5
   crossover gaps likewise. 2023-2026 expiry-date gap declared (declared
   roll rule is bar-validated, not expiry-date-dependent).
5. **Entry/stand-aside/exit [PROVISIONAL]**: signal = sign of (reopen first
   trade/close vs prior 16:00 CT close) beyond a minimum-gap threshold
   [PROVISIONAL, e.g. ≥1×ATR(20d,1m-bar) fraction — exact value a
   registered-cycle decision, NOT tuned here]; fill = open of the 5th 1m bar
   after 17:00 CT (T+5m; reopen auction minute excluded — same execution-law
   logic as 6B_v2 §8-H2'); **mandatory delay variants +1 bar and +30m**;
   stand-aside: (i) roll sessions and the session after a roll EXCLUDE;
   (ii) holiday/early-close-adjacent sessions with uncertain 2024-2025
   schedules EXCLUDE/NOT_RUN; (iii) Sunday opens are a separate stratum
   (1.9% volume, distinct liquidity), base = weekday reopens; (iv) warmup
   60d. Exit: TP 2×SL, SL 1×ATR(20d), SL-priority; **time exit 09:00 CT
   [PROVISIONAL]** — before the London/US information blocks (this family's
   claim is about liquidity timing, not information; ending before 07:30 CT
   avoids F3 contamination — 07:30 CT alternative stated as sensitivity).
6. **Baselines/placebo/negative controls**: C1 clock/placebo at 17:05 CT,
   random sign, multi-seed; C2 always-in at 17:05 CT (does gap SIGN carry
   information vs mere overnight drift?); C4 delay-pair; family-specific
   negatives: (a) **zero/minimum-gap-day placebo** (days below threshold —
   if "effect" appears there too, it is session exposure); (b)
   **DST-mismatch-week split** (the K4 natural experiment — sign flip under
   CT bucketing = clock-law bug); (c) 6B gap-std NOT_RUN ⇒ the 6B leg of
   this family carries an explicit anatomy-first gate: measure 6B gap std
   before any 6B spec is frozen (descriptive, prep-legal).
7. **Refutation**: mechanism-level: (i) both G-C/G-D below floor ⇒ dead;
   (ii) effect present only on roll-adjacent sessions ⇒ construction
   artifact; (iii) DST-mismatch sign flip ⇒ clock bug (K4); (iv) effect
   concentrated in the first 30m only and gone by +30m delay ⇒ reopen
   auction microstructure artifact, not session-leg liquidity timing.
   Power [DERIVED, court §c3]: n ≈ 1,573/1,572 minus threshold thinning —
   if thresholding leaves n≈500 → MDE 5.80/6.88 bp ≈ or above full modeled
   cost (3.6–6.3 / 6.3–11.2) — same power-cost coincidence as F1; unthresholded
   n→full gives 3.27/3.88 bp. Minimum-survivable-cost reasoning: the family
   must clear ≈6.4–11.2 bp RT on 6B — the court's finding that **6B's
   modeled RT cost is 2.1–3.7× the dead spot families' 3.0 bp** makes the 6B
   leg the cost-weakest in the whole portfolio; 6E leg is borderline.
8. **Cost sensitivity**: MODELED COST; 2.46 USD/side T1 corrected (under
   review); spread close-proxy high-biased — **specifically hazardous here**:
   the close-proxy spread is measured on full-session closes, but this family
   trades the THINNEST liquidity window (first hour after reopen; p05 session
   volume 7,904 contracts) — the $18.75/side proxy is likely MORE biased-low
   at 17:00 CT than anywhere else in the day [INFERENCE; BBO NOT_RUN].
9. **Regime/era breaks**: 2022 FX Monday-halt regime change (FXCAL §2b) —
   pre-2022 Monday holiday reopen structure differs; 2020-22 vs 2023-26 sign
   stability; 6E unadjusted-chain drift hazard largest in high-differential
   years (back-adjustment mandatory — already applied in panels).
10. **Coverage**: full 1,746 sessions/symbol minus roll/holiday exclusions;
    maintenance-break bar discipline proven (1 bar in 6.8y on 6B); Sunday
    stratum enumerated (348). Hole: 6B gap-std anatomy NOT_RUN; 2024-2025
    FX holiday times NOT_OBTAINED (FXCAL §2).
11. **Sources**: `6E_a2_sessions.json` (v1_gap_remeasure, sunday_evening_open,
    dst_mismatch_effect, session_coverage), `6B_a7_quality.json`,
    FXCOMM_GAPFILL_EVIDENCE.md §2 (holiday XLS captures with sha256 under
    `cme_cal_gap/fx_comm/captures/`; URLs = cmegroup.com holiday files +
    web.archive.org, documented therein) — all pinned in
    `captures/source_sha256.tsv`. No new web numerics.

---

## 5. FX-F5 — Rate-Differential Regime Conditioning (H-G law; overlay; NOT a standalone signal)

1. **Mechanism** [MECHANISM_HYPOTHESIS]: the CIP/rate-differential state is a
   REGIME CONDITIONER on intraday families (per owner law, CIP facts are
   INPUTS, not alpha): when the US-minus-foreign policy differential is wide
   and rising, the currency carries a persistent flow tilt (hedging demand,
   carry positioning), which plausibly changes the sign-stability of
   liquidity-absorption effects (F1/F4) — direction of the modulation is
   itself the hypothesis content and is declared UNKNOWN a priori
   [MECHANISM_HYPOTHESIS, deliberately two-sided]. OBSERVED anatomy: 6B
   corr(roll-gap ticks, DFEDTARU − Bank Rate) = **Pearson +0.8423 /
   Spearman +0.7445** (n=27 rolls; mean gap +9.37 ticks when diff>0 (n=19)
   vs −3.0 when diff<0 (n=1); realized carry ≈ 73% of textbook CIP slope)
   [`6B_a3_term.json:gap_vs_policy_diff`, `cip_check`]; 6E roll gaps 27/27
   positive, sign agreement with SOFR−€STR 27/27 latest-vintage / 26/27
   PIT-as-of — but **correlation vintage-fragile: r=+0.9097 latest-vintage
   vs r=−0.107 PIT-as-of (ALFRED year-end vintages; no 2025 vintage exists)**
   [`6E_a3_term.json:gap_summary`; ERRATUM MAJOR-2].
2. **Expected direction, falsifiable**: conditional version: the host
   family's sign-carry in the diff>0 regime differs from diff≤0 regime
   (two-sided); falsified if the regime split shows no difference beyond
   placebo band. NOT a standalone: no entry is ever defined from the
   differential itself.
3. **PIT availability**: **rates NOT PIT-strict** (FRED SOFR/DFEDTARU
   latest-vintage; ECB €STR latest; ALFRED year-end vintages only; BoE Bank
   Rate revision-free). **MANDATORY declared dependency (court §d row 7):
   (i) CIP-vintage sensitivity must be quantified and (ii) the owner's
   real-time SOFR source decision must land BEFORE any F5-conditioned
   registration — the 6E r=+0.91→−0.11 flip is the measured proof that
   vintage choice flips conclusions. Until then F5 is NOT_RUN for
   registration purposes.**
4. **Contract/session/roll**: identical to F1 §1.4; roll-gap facts above are
   the conditioning variable's measured basis (27 rolls each symbol,
   2020-2026 — the differential regime varies across the same window).
5. **Entry/stand-aside/exit [PROVISIONAL]**: NONE of its own — inherits the
   host family's spec (F1 or F4), splitting evaluable days into diff>0 vs
   diff≤0 strata using the differential AS OF the decision date (vintage
   law; latest-vintage split reported as sensitivity with the fragility
   caveat).
6. **Controls**: the host family's full control set C1–C4 run WITHIN each
   regime stratum (placebo bands per stratum); family-specific negative =
   **the 2025-26 synchronized-policy window on 6B where the differential sat
   at exactly 0.00pp for four consecutive rolls (v1's mixed-sign verdict
   arose exactly there — zero-diff rolls show small mixed-sign gaps −5..+13
   ticks)** [OBSERVED, 6B_v2 §3 ERRATUM M2]: a regime conditioner that
   "matters" only at zero-diff is noise.
7. **Refutation**: (i) host effect identical across diff regimes ⇒ F5 dead
   (no conditioning value); (ii) conclusion flips between latest-vintage and
   PIT-as-of splits ⇒ vintage-fragile, dead until owner decision lands;
   (iii) any suggestion of standalone differential entries is out-of-law
   (H-G) and void. Cost-level: F5 adds ZERO cost of its own (pure
   conditioning) — its cost statement is the host's; the honest minimum-cost
   note is that conditioning HALVES the host's n per stratum (~786/symbol
   for F4), raising MDE by √2 (court §c3 method) — conditioning is bought
   with power.
8. **Cost sensitivity**: host's MODELED COST statement unchanged; 2.46
   USD/side T1 corrected (under review).
9. **Regime/era breaks**: the differential itself IS the regime variable;
   2020-22 (wide positive diff) vs 2023-26 (converging to zero) is the
   measured split (calendar-spread medians walk with the differential:
   +19.5 ticks 2022 → −1.0 2026 on 6B).
10. **Coverage**: 27 rolls/symbol measured for the conditioning basis;
    differential series full-window daily; hole = PIT vintages (annual
    year-end only; no 2025 SOFR vintage exists).
11. **Sources**: `6B_a3_term.json`, `6E_a3_term.json` (pinned); rate-series
    provenance (FRED/ECB SDW/ALFRED/BoE) documented in 6E_v2 §5 ERRATUM
    MAJOR-2 and 6B_v2 §0/§3. No new web numerics.

---

## 6. FX-F6 — Crowded-Positioning Conditioning (6E-primary; overlay; NOT a standalone signal)

1. **Mechanism** [MECHANISM_HYPOTHESIS]: extreme non-commercial crowding
   (CFTC CoT) conditions the risk state of the book: crowded-POSITIONING
   regimes change the volatility response of intraday liquidity absorption
   (again two-sided, direction declared unknown a priori; the measured
   descriptive is vol, not return). OBSERVED anatomy (6E): net-noncomm
   1,082 weeks 2006-01→2026-09, PIT structure = observe Tuesday / release
   Friday 15:30 ET, as_published no-revision vintage
   [`6E_a5_cot.json:coverage`]; **forward-21d vol after ≥80th-pctile
   (crowded-long) observations: mean 6.52% vs ≤20th-pctile (crowded-short):
   7.68% (n=347 joined; strict-past 3y percentiles; release-safe obs+3)** —
   i.e. crowded-SHORT regimes precede HIGHER forward vol on 6E
   [`6E_a5_cot.json:positioning_vs_fwd_vol_descriptive`]; era means show the
   full positioning cycle (2020-22 mean +61.9k → 2023-26 +71.7k vs
   2010-2019 structurally short) [same file]. **6B falsifier already
   measured: corr(|z|, fwd vol20) = −0.074 (n=326, 2020-2026) — near-zero**
   [`6B_a5_cot.json:corr_abs_z_fwd_vol20`] — the conditioning value is
   6E-specific at today's evidence.
2. **Expected direction, falsifiable**: the host family's dispersion or
   sign-stability differs between ≥80/≤20 positioning regimes (two-sided);
   falsified if identical. Standalone entries from CoT are out-of-law
   (weekly conditioning only).
3. **PIT availability**: CoT PIT structure measured and safe (Tuesday
   observe / Friday 15:30 ET release; median release lag 3d, min 2, max 4 on
   6B [`6B_a5_cot.json:release_lag_days`]); as_published vintage verified.
   Conditioning may only use observations ≥ release-safe (obs+3 sessions —
   the 6E measurement's own law).
4. **Contract/session/roll**: identical to F1 §1.4 (conditioning does not
   touch construction).
5. **Entry/stand-aside/exit [PROVISIONAL]**: none of its own — host (F1/F4,
   6E leg only today) split into ≥80 / ≤20 net-noncomm pctile strata
   (strict-past 3y rolling percentile, release-safe).
6. **Controls**: host's C1–C4 within each stratum; family-specific negative
   = mid-pctile (20-80) stratum (a "monotone-in-|crowding|" claim must not
   show its extreme in the middle); 6B near-zero correlation is the
   cross-symbol negative [OBSERVED].
7. **Refutation**: (i) host effect identical across strata ⇒ dead; (ii)
   6E-style vol gap does not replicate as a conditioning split on the host's
   intraday horizon (the measurement is fwd21 VOL — transferring a 21d-vol
   fact to intraday sign-carry is itself a hypothesis [INFERENCE]; the
   refutation condition is that the transfer shows nothing); (iii) effect
   appears mid-pctile ⇒ artifact. Cost: zero of its own; halves host n per
   stratum (√2 MDE inflation), same power purchase logic as F5.
8. **Cost sensitivity**: host's MODELED COST; 2.46 USD/side T1 corrected
   (under review).
9. **Regime/era breaks**: positioning cycle era means differ structurally
   pre/post-2020; 2022 crisis path measured (net −1.5k Jan → +124.9k Dec
   2022); split reported.
10. **Coverage**: 6E 1,082 weeks full; 6B 326 joined obs 2020-2026; holes:
    intraday-horizon transfer NOT_RUN; 6B conditioning value measured
    near-zero (declared, not hidden).
11. **Sources**: `6E_a5_cot.json`, `6B_a5_cot.json` (pinned); CoT provenance
    (CFTC as_published, market-mapping verification) documented in 6E_v2
    CoT section. No new web numerics.

---

## 7. Corrected cost arithmetic (all families reference this section)

Fees [FACT, FEES_CORRECTED §2 — glued-superscript erratum, MODELED COST,
VERIFIED_VS_ACCOUNT=NOT_RUN, UNDER REVIEW until a new A7]: **6E/6B all-in
tier-1 = fixed = 2.46 USD/side** (commission 0.85 + exchange 1.60 + reg
0.01; FX row mapping PARTIAL-corroboration disclosed); tiers T2 2.26 /
T3 2.06 / T4 1.86.

[DERIVED from named measured inputs — spread $18.75/side close-proxy
high-biased (DC §1.7), fees above, slippage {1,2,3} ticks × $6.25/side]:

| component (round trip) | 6E (notional $119.4k–155.4k; px 0.9552–1.2429) | 6B (notional $65.0k–88.8k; px 1.0392–1.4205) |
|---|---|---|
| spread (2 × 18.75) | 2.41–3.14 bp | 4.22–5.77 bp |
| fees (2 × 2.46 = 4.92 USD) | 0.32–0.41 bp | 0.55–0.76 bp |
| slippage 1/2/3 ticks per side | 0.91 / 1.82 / 2.73 bp | 1.54 / 3.08 / 4.62 bp |
| **MODELED RT TOTAL** | **3.6–6.3 bp** | **6.3–11.2 bp** |

Court comparison (court §b4): dead spot families' frozen proxy = 3.0 bp RT.
**6E modeled is 1.2–2.1× the dead floor; 6B is 2.1–3.7× — the court finding
stands with the corrected fee layer: the futures vehicle is NOT cheaper per
notional than the dead spot proxy, and the honest cost distinction is
structural (tick grid, decomposable fees), not level-based.** BBO NOT_RUN
everywhere; "measured cost"/"complete cost" FORBIDDEN.

Per-family minimum-survivable-cost one-liners (mechanism honesty):
- F1: needs ≥ MDE(n) which coincides with cost at n≈500; census gate ≥500.
- F2: needs 17–21 bp/trade at n=56–58 (power-starved; only tail-scale
  post-decision effects are detectable).
- F3: needs 10–12 bp/trade at pooled known-type n≈165.
- F4: 6E borderline (3.6–6.3 vs MDE 3.3–5.8 at n 500–full); 6B leg weakest
  (6.3–11.2 vs 6.9–3.9) — 6B leg carries an explicit cost-viability doubt.
- F5/F6: no own cost; buy conditioning with √2 MDE inflation on the host.

---

## 8. Trial-identity census [PROVISIONAL, contingency only — nothing registered]

Census unit = one trial identity = (family, symbol, arm, tail, delay, tier).
No FX trial cap is defined by any standing ruling — **stated plainly: the
census below has no ceiling applied to it; if the owner sets one, the
census is the input to that decision.** Arms×tails×delays×tiers convention:
arms = competing direction hypotheses (2 each family); tails = long/short
sign (2, both registered by PB §4.6 law); delays = {0, +1 bar, +30m} (3);
tiers = slippage {1,2,3} ticks (3).

| family | symbol leg | arms×tails×delays×tiers = IDs | notes |
|---|---|---|---|
| FX-F1 | 6E | 2×2×3×3 = 36 | **PB2 HOLD ⇒ CONTINGENCY ONLY — not proposed for registration** |
| FX-F1 | 6B | 36 | same |
| FX-F2 | 6E (FOMC base) | 36 | ECB stratum +36 contingency |
| FX-F2 | 6B (MPC base) | 36 | FOMC stratum +36 contingency |
| FX-F3 | 6E (CPI+EMPSIT pooled base) | 36 | per-release-type split +36 contingency; unclassified-8:30 stratum +36 |
| FX-F3 | 6B | 36 | same strata contingencies |
| FX-F4 | 6E (weekday reopens) | 36 | Sunday stratum +36 contingency |
| FX-F4 | 6B | 36 | gated on 6B gap-std anatomy (NOT_RUN) |
| FX-F5 | overlay | 0 standalone | ×2 regimes on ONE chosen host leg (e.g. F4-6E 36 → 72) |
| FX-F6 | overlay (6E) | 0 standalone | ×2 regimes on one 6E host (36 → 72); 6B only as falsifier |
| **Total if ALL families + ALL strata** | | **≈ 360 base + ≈ 288 strata/overlays ≈ 648** | plainly stated, uncapped |

Controls are NOT counted as trial identities here (court §c4 treats placebo
seeds as diagnostics or budgeted identities — Co-Owner ruling pending, court
§d row 6); if ruled budgeted, add ≥100 seeds × families run.

---

## 9. NOT_RUN register + dependency list (this lane)

1. Trigger census + 1m trigger-time anatomy (F1; court §c2's first input) —
   NOT_RUN, prep-legal pass not executed here (desk lane).
2. 6B reopen-gap std anatomy (F4 6B leg) — NOT_RUN; anatomy-first gate
   declared.
3. Actual-publish-latency of BLS releases vs market feeds (F3) — NOT_RUN,
   inherited (A5/P2C).
4. Full 8:30 ET release-type census beyond CPI/EMPSIT (F3) — NOT_RUN.
5. Surprise/consensus vintages for ECB/BoE/FOMC/BLS (F2 content conditioning)
   — NOT_RUN; families condition on event + realized first-5m sign only.
6. CIP-vintage quantification + owner real-time SOFR source decision (F5) —
   NOT_RUN, owner-gated (court §d row 7).
7. FX official holiday times 2024-2025; FX quarterly expiries 2023-2026
   (64 cells; IMM-rule derivation forbidden) — NOT_OBTAINED (FXCAL §1d/§2).
8. BBO true spread / execution realism everywhere — NOT_RUN (D5 ruling);
   account fee verification — NOT_RUN (fee layer UNDER REVIEW until new A7).
9. ATR(20d) numeric levels for SL sizing — NOT_RUN (all families).
10. FX official holiday calendar completeness pre-2017 (gap-fill lane closed
    2017-2023; earlier parent-era coverage per FXCAL) — carried from
    FXCOMM_GAPFILL_EVIDENCE.md NOT_OBTAINED register.

— End FX_HYPOTHESES. Every number traces to a pinned artifact or is labeled
DERIVED with inputs named; missing evidence is NOT_RUN, never PASS.
