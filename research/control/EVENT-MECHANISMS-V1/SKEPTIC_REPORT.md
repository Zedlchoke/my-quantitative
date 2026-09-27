# SKEPTIC_REPORT — EVENT-MECHANISMS-V1 (G1, INDEPENDENT SKEPTIC, VETO authority)

Written 2026-09-27 by the independent skeptic subagent, fresh context,
outcome-blind: no scored PnL exists for any surface in this cycle (intake
`INTAKE_2026-09-27.md` §"Live-gate census"; registry budget 0/6). I audited
every A1 verdict in `SCREENING_MATRIX.md` adversarially. I read: the owner
directive verbatim, the plan, the screening matrix, all 139 rows of
`FAMILY_FAILURES.jsonl` (extracted per cycle), LESSONS.md P-18/P-27/P-29/P-30,
Q-7/Q-11, L-SAMV1-1/2/3, the DTP viability review, the STOCKS-NG1/NG2/NG6
terminal artifacts on their branches, the DFV1 deliverables at `bb010bc9`
(gap matrix, frontier, stocks/cx/fx lane reports, FINAL_REPORT), the cycle
PROBE_LOG, and I re-measured the on-disk substrate (tar listings, worktree
listing) where the G2 question demanded it. Read-only except this file.

Standing laws applied: F-0 skeleton test (drop the specific observable, keep
trigger/direction/exit — same shape = same dead family; DTP viability review
§2, P-30: "trục dữ liệu chưa test ≠ cơ chế mới"); ancestry rho bar 0.20
immovable; representation-rho kills pre-PnL (P-27/P-29); P-27 (better data on
the same skeleton is not a new mechanism); Q-7 (the clock did the work —
91.7% of 8-K windows at the 09:30 bar; plain 8-K adds only 1.05×, earnings
1.74×, vs 2.53× originally credited); Q-11 (a permutation is a null only if
it moves the signal — control validity must itself be measured); Q-10 (a
closed door states its reopening condition once); P-26 (FTD posting bound);
L-SAMV1-1 (adjusted series as-of-pull = lookahead by construction).

---

## 1. Per-direction rulings

### D1 — EDGAR acceptance-timestamp filing-flow → **KEEP (conditions)** — concur with A1

- **Ancestry collision (F-0):** Drop the acceptance observable → skeleton is
  "EDGAR filing event → next-open entry → multi-day drift window". No
  measured-dead stocks family has this shape. The dead stocks set is:
  momentum (A4_XSEC_ETF_RELATIVE_MOMENTUM, CONTROL_REPRODUCED_MECHANISM),
  reversal (SFV3-A5-IDIO-SHOCK-REVERSAL L18; SAMV1-C-REVERSAL5 L112;
  RETEST-REVERSAL5), goodwill/accrual characteristics (SFV8/V12/V13),
  10b5-1 plan-flag cadence (SFNG1-A4-P1/P2, ANCESTRY_RHO_BLOCK), amendment
  cadence (SFNG2-A4, fail-closed data), illiquidity (SAMV1/RETEST), bear-trap
  event book (NG6, ancestry). **D1 does not collapse into any of them.**
- **NG6 distinction verified, not assumed:** NG6's anchor was
  SNG6-A2-P1 "single-name failed-breakdown unwind (bear-trap reclaim)" — a
  *price-condition* event (252-session-low break + elevated-participation
  reclaim) keyed to **session dates**; its killers were event-DATE-conditional
  vol/shock/reversal states (vol_restricted_event_20d 0.260 / 60d 0.219 /
  dvol_shock −0.320 / reversal_5d 0.201 — registry STOCKS-NG6 row;
  `terminal_verdict_stocks_ng6.json` decision_path). No acceptance timestamp
  exists anywhere in NG6. The acceptance-*minute* stratum (in-session vs
  after-close vs Friday evening) is a different conditioning axis from
  NG6's price-state conditioning. Not collapsed.
- **"Cadence-latency" class distinction:** the killed cadence-latency form is
  SFNG2's v11 (firm-level inter-acceptance stream gaps >460d as a
  characteristic; FAMILY_FAILURES L96 — UNMEASURABLE, zero-variance data
  fact). D1's observable is event-level time-of-day strata, not a firm-level
  inter-filing gap. Different observable, different shape. Not collapsed.
- **Q-7 warning is the real risk, and the A1 has the right control:** the
  clock lesson says most event variance IS the session-open clock (Q-7,
  LESSONS.md:446-455). D1 lives or dies on whether the *acceptance-minute
  stratum* carries variance **above** the session clock. The A1's
  permuted-acceptance placebo and date-only control (matrix D1 fields 6–7)
  are the correct instruments; under Q-11 their validity must itself be
  measured (does the permutation move the signal; check autocorrelation of
  the permuted variable within issuer×form).
- **Conditions I attach (G2/G3, fail-closed):**
  1. The acceptance observable is measured on ONE ticker (AAPL, HTTP 200,
     163,991 B — PROBE_LOG.md #1, probe_submissions_aapl.json). That proves
     *reachability*, not *sufficiency*: `filings.recent` caps at 1000 recent
     filings per entity and deeper history requires the paged `filings.files`
     index. Cohort coverage over the death-inclusive cohort (410 alive +
     1,769 dead; DFV1 stocks lane Form-15 census) is **UNMEASURED** — DFV1
     N2's "thousands of light calls, <100 MB" is an estimate, not a
     measurement. G2 must run a staged probe measuring per-entity acceptance
     history depth (recent + paged), with per-file sha manifest (N9 lesson)
     and a canary, BEFORE the G3 freeze. This is within plan scope (G2 data
     authority; DFV1 N2: "no owner action needed").
  2. Representation-rho battery at G3 must include, explicitly: (a) the
     date-only signal (registered by A1); (b) NG6's event-conditional dead
     forms as shadows (vol_restricted/dvol_shock/reversal event-conditional
     rhos — the A4 methodology NG6 lists as its durable asset); (c) the
     Q-7 clock-only session-open shadow, credited only above the clock.
  3. Price plane: the 111,323-file stocks-search-v1 EOD cache is on disk
     (re-measured today) but sha-unpinned (6/111,322; DFV1 gap N9) and
     EODHD adjusted prices are as-of-pull (L-SAMV1-1). Lawful planes until
     N9/N3 are the ALL_MATCH amihud staging (2017-07..2022-12) or the
     sha-pinned NG6 death-inclusive panel (2015+, inside
     `~/staging_backups/cleanup_2026-09-17/stocks-ng6_integration.tar.gz`,
     present — verified today; sha 808ca4f1 MATCH per DFV1 stocks lane).
- **Payer testability:** the "slow diffusion" payer is honest in the A1's
  phrasing ("must be measured, not assumed"); the after-hours-LP leg of the
  payer story is NOT testable (no tape — stocks cost components 0/10
  measured, DFV1 FINAL_REPORT) and must be dropped from the mechanism claim,
  leaving the EOD drift decomposition as the only lawful test.

### D2 — Form 4 insider event flow on the acceptance clock → **KEEP (conditions; amendment arm fenced)** — A1 KEEP upheld with corrections

- **Ancestry collision (F-0):** Drop the Form-4 transaction conditioning →
  trigger = "EDGAR filing accepted" — the D1 skeleton. What makes D2 a
  distinct *identity* (not a variant) is the payload: insider transaction
  role/value/open-market vs mere filing existence, carrying a different
  payer hypothesis (informed-trader underreaction vs diffusion lag). Payer +
  information-payload = 2 axes distinct from D1; risk shape shared. Passes
  the ≥2/3 anti-variant law **as against D1**; passes as against the dead
  set because insider-buy → drift is a continuation/post-event shape, not
  the measured-dead reversal shape (SFV3-A5, SAMV1-C-REVERSAL5,
  RETEST-REVERSAL5 are all EXPECTANCY_NONPOSITIVE reversals).
- **SFNG1 boundary correctly drawn:** SFNG1-A4-P1/P2 died on the
  *plan-flag cadence* observable (declared-plan supply persistence,
  plan-share-of-sells composition — ANCESTRY_RHO_BLOCK vs goodwill_bloat
  −0.3547/−0.384, FAMILY_FAILURES L80/81; NG1 terminal report
  family_verdicts). D2's open-market role/value conditioning on the
  acceptance clock is a different observable, and D1's field 7 correctly
  registers rho vs the SFNG1 signal as the kill test.
- **CORRECTION 1 — the amendment-lag (4/A) axis is NOT new.** The A1's D2
  field 8 lists "amendment-lag (4/A)" as a new axis and its field 3 lists
  the 4/A corpus as an observable, without citing STOCKS-NG2 at all. The
  measured record: SFNG2-A4-P1/P2 attempted exactly the 4/A amendment-lag
  family and died **fail-closed on data, not ancestry** — 16/17 vetoes
  CLEAN (max |rho| 0.1527 / 0.1458; goodwill_bloat only 0.0376) but
  v11_cadence_latency_form UNMEASURABLE (zero panel entities with a >460d
  inter-acceptance gap; the sole big-gap 4/A issuer VNO's originals carry
  0 rows in the pinned stream — NG2 A7 terminal A7-SNG2-4), and P2's frozen
  Q-6 floor failed (0 bookable 2025 decisions < 30; FAMILY_FAILURES L96/97;
  NG2 registry row "2/2 fail-closed"). The 4/A corpus is frozen at 6,123
  files / 3,062 accessions / 1,877 resolvable pairs / 294 issuers
  (A7-SNG2-5, census crosscheck) and `www.sec.gov` is now 403-blocked
  (PROBE_LOG #2–4), so the population cannot be lawfully widened. Under
  Q-10/P-27: reopening needs a materially changed basis, which does not
  exist. **Ruling: D2 goes to G2/G3 WITHOUT the amendment-lag arm unless the
  G3 dossier names a measured basis change; otherwise the amendment arm is
  dead-by-precedent and including it would be a variant resurrection.**
- **Conditions I attach:** substrate restore + re-pin before any computation
  (form4_stream 546,039 rows pin `6ac2cd5b…`, XML manifest `5d351623…` EXACT
  per DFV1 — bytes live ONLY inside
  `~/staging_backups/cleanup_2026-09-17/stocks-free-v13_integration.tar.gz`,
  which I verified present today by tar listing: 345,150 form4_xml docs +
  manifest; the stocks-free-v13/stocks-ng2 worktrees are emptied); N4 dated
  identity map derived before any insider×price join (ghost-series law
  L-SAMV1-2); illiquidity re-label fence (A1 already has it) enforced via
  the A4 rho methodology on liquid-name conditioning; Q-11 validity
  measurement for the random-date placebo.
- **Payer testability:** testable as stated (drift after open-market buys vs
  value-matched gift/grant placebo) on the EOD plane; honest.

### D3 — Corporate-action PIT rebuild + ex-date event book → **SPLIT: data-plane KEEP as G2 authority work; ex-date event book VETOED as a scored identity** — correction to A1

- **Data plane (N3/N4): KEEP.** The repair is real, needed (L-SAMV1-1: AAPL
  2015 adjusted_close 24.17 vs close 109.33, as-of-pull — re-observed DFV1
  stocks lane finding 5), derivation-only from entitled bytes on disk, and I
  verified the substrate today: `eodhd_div` 2,168 files + `eodhd_splits`
  2,168 files inside the sha-verified v13 archive. This is lawful G2 work
  and benefits D1/D2 (honest adjusted returns, PIT joins). It is NOT an
  identity and consumes no scored-cell budget.
- **Event book: VETOED.** The A1 kept it conditionally ("weakest event
  candidate; survives to G2 … event book only if F-0 clears it"). I rule it
  does not clear F-0, on three independent grounds:
  1. **Payer mechanics are false as written.** The A1's payer is "index
     funds rebalancing weights at split/dividend effective dates … rules-
     based holders MUST trade at the effective date". A split leaves an
     index weight invariant (price and shares scale together) — index funds
     do NOT trade at split ex-dates; total-return-tracking dividend
     treatment likewise generates no constituent trade. The named forced
     flow does not exist for the named action classes. The residual
     mechanisms (nominal-price/attention, dividend-capture inventory) are
     not forced flows and are not observable with on-disk authority (no
     tape, costs 0/10 measured).
  2. **Skeleton collapse.** F-0 (drop the action observable, keep
     trigger/direction/exit) yields "8-K-style dated event → next-open →
     short drift window" — literally D1's skeleton, and the A1's own control
     #2 concedes it ("non-action 8-K filings … the D1 clock WITHOUT the
     action content"). The pattern-claim version (ex-date → drift) collides
     with the measured-dead reversal set (SAMV1-C-REVERSAL5 L112;
     SFV3-A5-IDIO-SHOCK-REVERSAL L18; NG6 reversal_5d event-conditional
     0.201 over the 0.20 bar) and with the most-published-anomaly decay law
     (Q-6), which the A1 itself flags. Admitting it would be a third arm on
     the D1 skeleton — variant multiplication (E3).
  3. **No distinct falsifier:** its distinguishing falsifier ("rebuilt PIT
     state diverges from served adjusted_close") is the data-plane test, not
     an event-book mechanism test.
- **Control-plane use preserved:** non-action filing events as a D1/D2
  control remain lawful (they are D1 controls, not an identity).

### D4 — FTD × price cross → **CONTROL-PLANE-ONLY** — concur with A1

- The posting clock is structural: FTD half-month data is posted ≥15d
  (conservative) / ≥17d (P-26 binding) after half-month end, machine-
  readable posting dates NOT found (DFV1 stocks lane; DEU Lane S ruling).
  Flow/change forms are dead-on-arrival by clock arithmetic — any PIT
  decision would use a state ≥16 days stale, i.e., a characteristic, and
  characteristic-class shapes route into the dead bloat/illiquidity set.
- The A1's "NOT SCORED, control-plane-only, recorded not killed-as-class" is
  the correct disposition: UNDETERMINED w.r.t. the class absent a per-row
  publication-timestamp source (which no owner action can create — it is
  the SEC's cadence). FTD state-conditioning remains lawful as a D1/D2
  falsifier control. Panel is VALIDATED and live (434 zips, 601 MB,
  `~/.my-quantitative-data/free-data-frontier-v1/raw/sec_ftd_archive/`,
  15/15 sampled MATCH).

### D5 — Crypto funding settlement / forecast-funding surprise → **VETO** — concur with A1

- Ancestry identity, measured, not arguable: TRACKB1 continuous pooled rho
  **1.0000** vs CARRY-BAB ("the lawful entry observable IS the dead carry
  class's observable", FAMILY_FAILURES L135); V17 FUNDJUMP rho 0.2439 — the
  announced-change event form still carries the funding level (L59);
  SRLV-CX M1 settle-adjacent dead BOTH directions with a full revival
  clause spent (L136, P-28); PWS run-gate killed by representation math
  (rho 0.316–0.703, L137, P-29).
- Forecast funding is a smooth input of settled funding — under P-27/P-29
  the representation-rho measurement is mandatory and its expected outcome
  is a kill; the "surprise" form was already tried as FUNDJUMP and died at
  the bar. The plane is closed by identity; reopening conditions were
  preregistered by TRACKB and are not met. VETO confirmed; no owner action
  could change this (it is not a data gap).

### D6 — Crypto liquidation / forced-flow cascade → **BLOCKED_DATA** — concur with A1

- I checked the specific question posed: is there a keyless PIT liquidation
  source in the repo's authority? **No.** DFV1 cx lane: liquidationSnapshot
  404 measured; `oi_history_usdm`, `liquidation_history`, `l2_orderbook_history`
  carry the owner prohibition verbatim ("Không suy ra order book hay forced
  flow từ nến"); gap O2 = "No keyless path; needs vendor $ + license
  screen"; the historical V14 OI bytes are ABSENT (I-1, 8/14 tarballs lost,
  FINAL_REPORT); WS collectors cover 8.25h + 42min TOTAL, PROSPECTIVE-only.
  aggTrades carry no liquidation flag — inferring forced flow from them is
  inference without authority and its absorption skeleton is the SRLV-dead
  shape (DTP viability review §2.2). DTP review RC-1 names exactly this
  reopening condition (real liquidation tape via a data-authority cycle).
- BLOCKED_DATA with owner action R4/O2 (vendor-quote decision) is correct;
  the class stays UNDETERMINED w.r.t. PIT data, not evidence-absent — the
  A1 recorded this honestly.

### D7 — Crypto delta-neutral basis/carry convergence → **VETO** — concur with A1

- Plane closed by identity: TRACKB1 continuous pooled rho 1.0000 (L135);
  BASISLV axis 0.3337 over bar; PREMFADE-28D fold-concentration (V14);
  CARRY-1D/3D/7D SCIENTIFIC_REJECTION (L1 of FAMILY_FAILURES). Reopening
  conditions preregistered by TRACKB: a non-funding-level PIT axis (=
  D6, itself BLOCKED_DATA) or a dated measured cost-regime break (none
  exists). plan_at §3B provenance does not reopen a measured-dead plane.
  VETO confirmed.

### D8 — FX after-cost event families → **NOT-SCORED** — concur with A1

- Release-clock class measured dead on two independent tracks: FXFV5-A6
  sham-calendar control OUT-EARNED the anchor (L40, falsification-by-control
  #10); RATESNG1 AGGRESSIVE arm killed R2 by clock-only shadow +94.16 vs
  +72.42 (L100; registry "clock-shadow falsification #16"); COMMODITIES-NG1
  release-clock law (registry: "D1 falsification law fired: release-clock
  control out-earned every anchor"); P-24: "the release calendar owns the
  money". DFV1 explicitly does NOT offer this class as a frontier.
- Cost authority BLOCKED: FX 2/10 components measured (FINAL_REPORT),
  ERP1 3.6/4.4-pip stressed RT floor, N1/R1 account-bound bytes pending;
  replication source O1/R2 pending. Owner today: "FX không score trên
  frontier đã đóng" (OWNER_DIRECTIVE.md:38). NOT SCORED with R1/R2 owner
  actions recorded is correct and terminal for this cycle.

---

## 2. Skeleton-merge ruling (identities)

The plan's ceiling is 3 identities. Ruling:

- **D1 and D2 share one information layer (acceptance clock) and one F-0
  skeleton (EDGAR filing event → next-open → drift book). They remain TWO
  distinct identities** because payer hypothesis and information payload
  differ (diffusion-lag on filing existence vs informed-trader
  underreaction on insider transaction economics) — 2 of 3 axes — and their
  ancestry fences differ (rho vs NG6/date-only vs rho vs SFNG1
  plan-cadence/illiquidity). They MUST share one control battery: date-only
  control, permuted-acceptance placebo (Q-11-validated), Q-7 clock-only
  shadow.
- **Preregistered merge condition (G3):** if D2's measured drift is not
  distinguishable from D1's generic-filing drift (i.e., the Form-4 event
  set's spread vs the matched non-Form-4 filing set ≈ 0), D2 collapses into
  D1 as a neighbour arm — one identity, not two. This is the honest
  skeleton-identity test between them, symmetric to D3's "D1-clock without
  action content" control.
- **D3's event book does NOT join** — it is vetoed (§1 D3) and would
  otherwise have been a third arm on the same skeleton.
- **Count of DISTINCT identities surviving to G3: 2** (D1, D2), both
  stocks, matching the owner's stated priority. D3's N3/N4 repair travels
  as G2 authority work, not an identity. D4 is control-plane. D5/D7 vetoed,
  D6 blocked, D8 not scored. If G2 data authority fails either surviving
  identity, the honest fallback is 1 or `NO_ELIGIBLE_PROPOSAL` — both
  valid terminals per the owner directive.

---

## 3. Errors found in the A1's screening

1. **D3 event book (over-kept).** A1: conditional KEEP. Skeptic: VETO as a
   scored identity — payer mechanics false for the named action classes
   (split-invariant index weights), skeleton collapses onto D1, pattern
   version collides with measured-dead reversals + Q-6. Data-plane N3/N4
   KEEP unchanged.
2. **D2 amendment-lag axis (unfenced resurrection).** A1 listed it as a new
   axis/observable without citing SFNG2-A4, which died fail-closed on
   exactly that form (UNMEASURABLE v11 + Q-6 zero bookable 2025) with a
   frozen, un-widenable corpus and a now-403 re-fetch path. Fenced: drop or
   re-justify at G3 with a named, measured basis change.
3. **D1 sufficiency conflated with reachability (under-specified G2).** One
   200-probe on AAPL proves the estate is open; it does not measure
   acceptance-history depth for a 2,179-entity cohort under the 1000-recent
   cap + paged files. DFV1 N2's volume/call estimate is a hypothesis (Q-8).
   A staged, sha-manifested probe measuring depth per cohort stratum is a
   G3-freeze precondition.
4. **(Minor) stocks cost book presented as if priced.** D1/D2 field 5 cite
   Q-2 bands (open 3.33×/3.35× midday) — these are EODHD-derived proxy
   relations, while DFV1 FINAL_REPORT measures stocks execution-cost
   components at **0/10**. G6 ceilings are proxy arithmetic only; the owner
   data-gap matrix must carry "stocks conditional-cost book = proxy-prior;
   broker/tape bytes only via O3/R5".
5. **(Minor) no wrongful KEEP/VETO found in the other direction:** I found
   no A1 veto/blocked verdict that a lawful path rescues this cycle. D6's
   BLOCKED_DATA is airtight under the current authority census (no keyless
   PIT liquidation source exists; O2 is the only path and it is
   vendor-gated). D5/D7 have no reopening condition satisfied. D8's
   NOT-SCORED is owner-commanded.

## 4. Provenance-label audit (SCREENING_MATRIX §3)

- D1/D2/D3 "owner instruction 2026-09-27 verbatim" — **VERIFIED**:
  OWNER_DIRECTIVE.md:32-34 names "EDGAR acceptance timestamp", "Form 4",
  "corporate-action PIT" verbatim.
- The owner's enumeration of "tám hướng" is genuinely not in the repo
  (OWNER_DIRECTIVE.md:27 references "tám hướng tôi nêu" without listing
  them); the plan's §3 reconstruction note is honest.
- D4 "DFV1 frontier F1 + DEU Lane S" — **VERIFIED** (F1 text carries the FTD
  archive and the Lane S fence; stocks lane re-states it).
- D5/D7 "plan_at.md §3C/§3B (owner-reviewed 2026-09-25)" — **PARTIALLY
  HONEST: approval status UNVERIFIED.** plan_at.md:3 self-describes as
  "**DRAFT FOR OWNER REVIEW** … đề xuất trao đổi với owner ngày
  2026-09-25"; the intake classifies it as the owner's draft preserved as
  guidance. Whether the owner reviewed/approved it is not evidenced.
  Label should read "owner draft 2026-09-25, approval status unverified".
  Verdicts unaffected (both vetoed on measured ancestry).
- D6 "plan_at.md §3C; DFV1 O2" — **VERIFIED** (liquidation named in
  plan_at.md:37; O2 row as described).
- D8 "plan_at.md §3A" — **PARTIALLY MISMATCHED**: §3A is FX liquidity
  provision / RANGEFADE replication; D8's macro-release-clock element is
  the measured-dead class (FXFV5-A6/RATESNG1/COMMNG1/P-24), not §3A. The
  verdict (NOT SCORED) is correct under either reading; the label should
  say "dead release-clock class + plan_at §3A replication track (R2-gated)
  + DFV1 F3 cost block".

## 5. G2 data-authority blockers per surviving direction (stocks priority)

Measured this session where marked:

| # | Blocker | Affects | Status / owner action |
|---|---|---|---|
| B1 | `data.sec.gov` submissions: 1000-recent cap + paged `filings.files`; cohort acceptance-history depth UNMEASURED | D1, D2 (stamps), D3 (form-type control) | In-scope staged G2 probe (sha manifest + canary; DFV1 N2: no owner action). Reachability measured 200 (PROBE_LOG #1, #5). |
| B2 | `www.sec.gov` Archives 403, UA-independent, identical 4819-byte body (4/4 attempts, PROBE_LOG #2–4) | any raw-filing/primary-doc need; 4/A re-fetch; FTD re-pull | Environment estate block (L-FIBV1-1/L-FXFF-1 class). Owner action = network unblock (one action also covers Dukascopy + CME). Not needed unless raw documents become load-bearing. |
| B3 | Form-4 substrate survives only in archive; worktrees emptied | D2 | `stocks-free-v13_integration.tar.gz` present in `~/staging_backups/cleanup_2026-09-17/` (verified today: 345,150 form4_xml + stream + manifests). G2 must restore + re-pin (P-13) before any D2 computation. Pins `6ac2cd5b…`/`5d351623…` EXACT per DFV1. |
| B4 | div/splits substrate archive-only | D3-data-plane | Verified today: `eodhd_div` 2,168 + `eodhd_splits` 2,168 files inside the v13 archive. Restore + N3 forward-rebuild with the FULL-DIRECTION fixture matrix (L-SAMV1-1: forward/reverse/ratio extremes/dividends/renames) at its own gate. |
| B5 | "8-K corpus" named in D3's observable is NOT on disk | D3 control | Raw 8-K text cannot be re-fetched (B2). A form-type-level control is constructible from `data.sec.gov` submissions metadata alone (200 measured); raw text must not be assumed. |
| B6 | EODHD price planes: search-v1 cache sha-unpinned (6/111,322), adjusted prices as-of-pull | D1, D2, D3 | Lawful until repaired: amihud staging (ALL_MATCH, 2017-2022) or NG6 panel (2,168 tickers, 2015+, `stocks-ng6_integration.tar.gz` present, sha 808ca4f1 MATCH per DFV1). N9 re-pin (~2 min CPU) + N3 rebuild before broader use. |
| B7 | N4 dated identity map (ticker↔CIK↔CUSIP) does not exist yet | D2 (joins), D4 (CUSIP), D3 | Derivation from entitled artifacts (~1 day, DFV1 N4); G2 prerequisite before any cross-dataset join (L-SAMV1-2 ghost law). |
| B8 | Stocks execution-cost components 0/10 measured (DFV1 FINAL_REPORT) | D1, D2 | G6 ceiling = proxy arithmetic (Q-2 + L-SAMV1-3) labeled proxy-prior in the owner data-gap matrix; broker/tape bytes only via O3/R5. Not a G2 pass/fail blocker; a disclosure blocker. |
| B9 | Crypto/FX staging | D5/D7/D6/D8 | None required this cycle: D5/D7 vetoed pre-PnL, D6 blocked on R4/O2 (vendor decision), D8 blocked on R1/R2 (statement + replication source). |

## 6. Verdict table

| Direction | A1 verdict | Skeptic verdict | Final court recommendation | One-line reason |
|---|---|---|---|---|
| D1 acceptance-clock filing flow | KEEP (priority 1) | KEEP (conditions) | **KEEP** | No measured-dead skeleton; NG6/cadence-latency distinctions verified; G2 staged acceptance-depth probe + NG6-conditional rho battery + Q-7/Q-11-validated controls are preconditions. |
| D2 Form-4 insider flow | KEEP (priority 2) | KEEP (conditions; amendment arm fenced) | **KEEP** | Distinct payer/payload from D1; SFNG1 boundary correctly drawn; amendment-lag arm carries the SFNG2-A4 fail-closed precedent — drop or re-justify with a named measured basis change at G3; substrate restore + N4 map are G2 prerequisites. |
| D3 corp-action PIT + ex-date book | KEEP as data-plane + weakest event candidate | SPLIT: data-plane KEEP (G2 work); event book VETOED | **KEEP (N3/N4 data-plane only); event book VETO** | Payer mechanics false (index weights are split-invariant — no forced trade at ex-dates); skeleton collapses onto D1; pattern version is dead-reversal shape + Q-6-published. |
| D4 FTD × price | NOT SCORED, control-plane-only | CONTROL-PLANE-ONLY | **CONTROL-ONLY** | P-26/Lane S posting bound (≥17d) makes every flow/change form retrospective by clock arithmetic; state-conditioning survives only as a D1/D2 falsifier control. |
| D5 funding settlement / forecast surprise | VETO-RECOMMEND | VETO | **VETO** | Plane closed by measured identity (TRACKB1 rho 1.0000; FUNDJUMP 0.2439; SRLV both directions; P-29 representation law); forecast funding is a smooth input of the dead observable (P-27). |
| D6 liquidation cascade | BLOCKED_DATA | BLOCKED_DATA | **BLOCKED** | No keyless PIT liquidation source in authority (O2 vendor-gated; V14 archive lost; snapshot 404; candle/trade inference owner-forbidden); reopening = RC-1 data-authority cycle. |
| D7 basis/carry convergence | VETO-RECOMMEND | VETO | **VETO** | Same closed plane by identity (rho 1.0000; BASISLV 0.3337; PREMFADE; CARRY-1D/3D/7D); TRACKB's preregistered reopening conditions unmet. |
| D8 FX after-cost events | NOT SCORED | NOT-SCORED | **NOT-SCORED** | Release-clock class measured dead twice over (sham-calendar and clock-shadow controls out-earn) + FX cost authority BLOCKED (2/10 components, ERP1 floor); owner today: no FX scoring on the closed frontier. |

**Identity count surviving to G3: 2** (D1, D2) — with the preregistered
merge condition that collapses D2 into D1 if its drift is indistinguishable
from generic filing-flow drift; D3 travels as G2 authority work, not an
identity. `NO_ELIGIBLE_PROPOSAL` remains a valid terminal if G2 kills a
surviving identity.

*Outcome-blind certification: no PnL, scored cell, or sealed surface was
read or computed for this report; every number cited above is a death
record, a data-census measurement, or a probe result from prior cycles.*
