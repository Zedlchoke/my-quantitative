# CARRIED_STATUS — COMM-EN lane, round FUTURES-TEN-HYPO-PREP-20261004

- Lane **COMM-EN** (symbols **CL** WTI NYMEX, **NG** Henry Hub NYMEX — the two
  symbols with NO vendor O1M panel). Generated 2026-10-04 UTC. Worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-ten-hypo/prep` @
  base `a4a882658e09092b5b282b666b30a3cfc5ac3418` (one permitted
  `git rev-parse HEAD`, == dispatch base), branch
  `prep/futures-ten-hypo-20261004`.
- Class: PREP carry/status document. **0 PnL, 0 returns, 0 scored runs; every
  parameter [PROVISIONAL]; outcome-blind; missing evidence is NOT_RUN, never
  PASS.** No registration, no trial creation, no self-ratification.
- Authority stack used: (a) baseline verdicts in
  `research/control/FUTURES-OVERNIGHT-PREP-20261003/hypo/comm/COMM_HYPOTHESES.md`
  (+ `RANKING_INPUT.md`, `captures/source_sha256.tsv`) [worktree, committed at
  base]; (b) the newer IBKR corpus measurements in **root** (READ-ONLY)
  `research/control/FUTURES-DATA-10SYMS-V1/**`, cited
  **"root main d8cf8eca300d9eadc703f0d99629bec79102b325"**;
  (c) new primary-source captures this lane
  (`comm_energy/captures/`, hashed in `SHA256SUMS_lane.txt` (comm_energy/)).
- **Baseline-hash re-verification (done BEFORE any fetch): all 24 rows of the
  baseline `source_sha256.tsv` re-hashed this lane = 24 OK / 0 missing /
  0 mismatch** (rows 01–09 resolved via the committed copies in THIS worktree
  at base; the original `.worktrees/futures-behavior/prep` path is
  P3-QUARANTINED and was NOT accessed — dispatch law; rows 10–24 hashed at
  their `~/.my-quantitative-data` paths). Full 48-row ledger:
  `SHA256SUMS_lane.txt` (comm_energy/). Because every hash matched, NO re-fetch of any
  baseline source was needed.

---

## 1. Classification law for this carry

Per dispatch: the four energy families below are carried **unchanged in
design**, with classification

> **CARRIED — DATA-BLOCKED, scored status `NOT_RUN_DATA_ABSENT`**

against BOTH authority layers:

- **(a) Baseline qualification verdict (unchanged):** CL/NG are
  **NOT_QUALIFIED_V2** (DATACONTRACT_QUALIFICATION §2, sha256 df175a2d…,
  re-verified); "no path" law stands — no registration path until the owner
  data decision. Nothing in this lane reopens or upgrades it.
- **(b) IBKR corpus verdict (root FUTURES-DATA-10SYMS-V1, FINAL_REPORT.md
  @ root main d8cf8eca):** for CL and NG,
  `SIGNAL_RESEARCH_READY = PASS`, `DAILY_FUTURES_BACKTEST_READY = BLOCKED`,
  `INTRADAY_FUTURES_BACKTEST_READY = BLOCKED` (10/10 symbols; the two
  measured walls: expired-contract resolve ≈1 year ⇒ continuous front
  true-volume only 2025-08→2026-10 ≈ 14 months; intraday depth ~10 months,
  NG ~2.2 years; earlier per-contract bars are settlement-derived
  O=H=L=C volume=0 — reference only, never fills). A scored identity
  therefore cannot exist today for either symbol: **NOT_RUN_DATA_ABSENT**.

## 2. Corpus data posture (the layer (b) facts every family inherits)

All OBSERVED from root artifacts @ root main d8cf8eca (file:field cited):

| fact | CL | NG | artifact |
|---|---|---|---|
| daily per-contract depth | from 2019-09 (front-contract probes reach 2018-01/2020-01) | same | FINAL_REPORT.md table row CL/NG; S7 probes |
| front true-volume era | 2025-08→2026-10 (~14 months; 280d in baseline dossiers) | same | FINAL_REPORT.md "Điều kiện nhãn" §; baseline §0.3 |
| settlement-derived bar law beyond true-volume | O=H=L=C, v=0 (25-90% of life) | same | FINAL_REPORT.md tech note 3; baseline §0.3 |
| H1 depth | ~2025-11 (probe first 2025-11-18) | **~2023-11** (probe first 2023-11-21) | S7_DEPTH_ACTIVE.json symbols.CL/NG probes |
| M1 depth | ~2025-12 (probe first 2025-12-22) | **~2023-11..12** (probe end-2024 M1 7D n=211, first 2023-12-29) | S7_DEPTH_ACTIVE.json |
| front spread proxy (median 20d, close-proxy) | 3.0 ticks = **$30** | 2.0 ticks = **$20** | S6_FRONT_SPREADS.json CL.median_usd / NG.median_usd |
| BID/ASK daily | 1 year (571 bars, v0=0 crossed) | 1 year (834 bars, crossed 0) | S7 BID 1-day-6Y probes; FINAL_REPORT cost table |
| commission | 0.85 + exchange **NOT_FETCHED** (CME 403) | same | costs/IBKR_futures_commissions_2026-10-02.json |
| margins (public, 2 sources <2% drift) | ~8,021/8,823 maint/initial | ~2,815/3,096 | costs/SPECS_MARGINS_PUBLIC_2026-10-02.md §3 |
| contract specs (units/tick — verified vs captured mirrors) | 1,000 bbl, tick 0.01 = $10 | 10,000 MMBtu, tick 0.001 = $10 | SPECS_MARGINS §1 CL/NG rows (AMP/NT/Wikipedia, fetched 2026-10-02) |

**New lane-measured fact (supersedes a baseline candidate path):** the free
EIA NG futures-price extension candidate cited in baseline NG-F1 Field 11(4)
(`eia.gov/dnav/ng/ng_pri_fut_s1_d.htm`) is **dead for futures**: the page now
states "(Futures prices after April 5, 2024, are not available)"
[OBSERVED, captures/eia_ng_futures_dnav.html, sha256 1bcc2f81…; fetched
2026-10-04, fetch_log seq 8]. The **Henry Hub spot** daily series (1997-2026)
continues on the same page — usable only as a conditioning-measurement leg,
never fills (baseline law). The pre-2025 free-price-extension route for NG
futures is therefore **NOT_OBTAINABLE** from this page; any scored pre-2025
price leg requires the owner vendor decision (unchanged) or another
as-published source NOT identified this lane (NOT_RUN).

## 3. Carried families — status one block each

### 3.1 NG-F1 `WNGSR-DESK` (baseline COMM_HYPOTHESES §1)

- **Status: CARRIED — DATA-BLOCKED (NOT_RUN_DATA_ABSENT).** Spec pointer
  unchanged (baseline §1 NG-F1 Fields 1–11, incl. the pre-registered r-1
  unsigned-surprise blocker = NOT_RUN_BLOCKED_R1 until the sign rule is
  written/frozen; the 369-median / 1,205-vintage free feature legs; The-Desk
  release-embedded consensus).
- **Corpus update (b):** NG intraday is the deepest of all 10 symbols —
  M1/H1 back to ~2023-11 [OBSERVED, S7]. Nominal consequence: ~150 WNGSR
  Thursday releases (2023-11→2026-10) MAY fall inside the M1/H1 coverage ⇒
  the baseline Field 10 hole "release-window intraday (any year)" narrows to
  "release-window intraday **before 2023-11**". **Per-release per-contract
  completeness is NOT_RUN** (S7 probes only 3 windows; the named, prep-legal
  unlock is a bulk-log audit pass over `~/.my-quantitative-data/
  futures-10syms-v1/raw/NG_*` M1 files vs the captured WNGSR schedule — this
  lane did not execute it). BBO absent ⇒ no fill story; scored intraday
  identity remains NOT_RUN_DATA_ABSENT; the daily design (Fields 5–8) is
  unchanged and remains the only registerable shape.
- **Update to Field 11 sources:** the free futures price-extension candidate
  is dead post-2024-04-05 (§2 above). The 2018-2026 surprise×price overlap
  the baseline planned via EIA dnav futures is **NOT_RUN_DATA_ABSENT** free;
  feature window (369 events) unchanged; price-window asymmetry unchanged.
- **Release-clock hardening (new capture):** WNGSR schedule page verbatim —
  "standard release time … 10:30 a.m. eastern time on Thursdays with the
  following exceptions", 2026 holiday rows Nov 13 (Fri 10:30, Veterans) /
  Nov 25 (Wed 12:00, Thanksgiving) [OBSERVED, captures/
  eia_wngsr_schedule.html, sha256 b54595ec…]. Matches baseline FACT; now
  hash-pinned this lane.

### 3.2 NG-F2 `CPC-REVISION` (baseline §1)

- **Status: CARRIED — DATA-BLOCKED (NOT_RUN_DATA_ABSENT).** Spec unchanged;
  revision-leg computable, error-leg NOT_RUN_DATA_ABSENT (monthly observed
  HDD/CDD only); degree-day aggregation rule still to be built + frozen.
- **Corpus update (b):** same NG intraday note as NG-F1 (daily design
  unchanged; M1-era coverage is irrelevant to the revision mechanism but
  removes nothing from the walls). 14-month true-volume + settlement law
  inherited.
- **Issuance-time law CLOSED (new capture):** CPC page verbatim —
  "**6-10 Day outlooks are issued daily between 3pm & 4pm Eastern Time**"
  [OBSERVED, captures/noaa_cpc_610day.html, sha256 c417042a…; fetch_log
  seq 11]. This upgrades baseline Field 3's NOT_RUN on the official
  publication-time schedule; it is consistent with the corpus zip-internal
  file clock 15:02 [OBSERVED, baseline §0.4/NG-F2 F3]. Correct URL is
  `/products/predictions/610day/` (no underscore) — the baseline-URL spelling
  `6_10day` 404s [OBSERVED, fetch_log seq 7/9].
- **Cadence-break caveat sharpened:** the corpus archive switches daily→weekly
  at 2025-06 [OBSERVED, baseline §0.4]; the official page says "issued daily"
  — the archive cadence is an **archive-collection property**, not proven
  issuance change; any design must declare both layers and never conflate
  them (declared; NOT_RUN adjudication of the 2025-07+ issuance cadence).

### 3.3 CL-F1 `WPSR-NAIVE` (baseline §2)

- **Status: CARRIED — DATA-BLOCKED (NOT_RUN_DATA_ABSENT).** Spec unchanged;
  naive-expectation freeze blocker unchanged (no free CL consensus —
  measured at baseline); double-proxy robustness rule inherited.
- **Corpus update (b):** CL M1 ~2025-12 / H1 ~2025-11 [OBSERVED, S7] ⇒
  ≤ ~47 WPSR Wednesdays nominally inside intraday coverage (2025-11/12→
  2026-10), single regime, BBO absent ⇒ scored intraday NOT_RUN_DATA_ABSENT;
  per-Wednesday completeness NOT_RUN (same named bulk-log audit pass, CL
  side). Daily design unchanged. True-volume 280-day front era +
  100%-backwardation cost law unchanged.
- **Release-clock hardening (new capture):** WPSR schedule page —
  "10:30 a.m. eastern time on Wednesday" + Holiday Release Schedule table
  (Thursday 12:00 shifts) [OBSERVED, captures/eia_wpsr_schedule.html,
  sha256 122d44c7…; fetch_log seq 1].
- **Conditioning-measurement leg clarified:** WTI–Cushing OK spot daily
  (1986-2026) + Brent-Europe (1987-2026) remain free on the corrected dnav
  URL `/dnav/pet/pet_pri_spt_s1_d.htm` [OBSERVED, captures/
  eia_wti_spot_dnav.html, sha256 5f9184d7…; the baseline-cited
  `/dnav/petroleum/…` path 404s — spelling erratum recorded, fetch_log
  seq 10/14]. Latest-vintage page only ⇒ NOT PIT-strict (DATACONTRACT §1.4
  law); conditioning-measurement only, never fills.

### 3.4 CL-F2 `CONFLICT-REV` (baseline §2)

- **Status: CARRIED — DATA-BLOCKED (NOT_RUN_DATA_ABSENT).** Same corpus
  posture as CL-F1 (§3.3); conflict inputs unchanged (Cushing line 790/790
  ttable4, byte-checked at baseline; ttable1/3/4 in corpus ⇒ the
  crude-vs-Cushing conflict AND the crude-vs-products conflict both remain
  computable free on the feature side). Adjudication-on-one-frozen-event-set
  law with CL-F1 unchanged. No separate corpus delta.

### 3.5 NG-F3 construction law + CL cost-law declaration

- **Status: CARRIED — unchanged, construction class.** NG-F3
  (seasonal-flip/roll-structure construction law) and the CL cost-law
  (backwardation 280/280 = carry conditioning input, not alpha; term-
  structure momentum NOT registered for regime-breadth absence) are inherited
  verbatim by every family in this lane including the two NEW ones
  (HYPOTHESES_COMM_EN_R3.md §V-2/§2-F4 bindings). Root adds margin/spread
  posture (§2 table) but changes no construction rule.

## 4. Aggregate budget law (restated, never reopened)

COMMODITIES aggregate minimal trial identities = **54 > 24 ⇒
BLOCKED_TRIAL_BUDGET** on any single-cycle attempt (baseline RANKING_INPUT
census: NG-F1 11 + NG-F2 11 + CL-F1/F2 joint 11 + GC-F1 7 + GC-F2 0 +
SI-F1 7 + SI-F2 7). The two NEW families in this round (CL-F3 11 minimal;
CLNG-F4 22 minimal across two legs) would raise the hypothetical aggregate
to 87 if ever legalized — enumerated so a future packet cannot discover this
late. **Nothing is registered or scheduled; no comm identity enters any
cycle's 24-ceiling arithmetic.**

## 5. NOT_RUN / NOT_OBTAINED register (this carry)

1. Per-release intraday completeness audit for NG (2023-11+) and CL
   (2025-11+) vs captured EIA schedules — NOT_RUN (named prep-legal pass;
   S7 probes are 3 windows only).
2. Free pre-2025 NG futures price extension — NOT_OBTAINABLE via EIA dnav
   (page kills futures after 2024-04-05); any substitute source NOT_RUN.
3. WNGSR issues beyond 2026-01-22 in corpus; 2017-05..2018-04 Desk-text
   adjudication — unchanged (baseline).
4. CPC issuance cadence post-2025-06 (official) — NOT_RUN (archive-property
   vs issuance-property not adjudicated).
5. STEO vintage-archive completeness — NOT_RUN (archives page 403 this lane;
   fetch_log seq 18).
6. Fees account verification (A7) — NOT_RUN; all costs MODELED / UNDER
   REVIEW; BBO NOT_RUN on CL/NG; exchange fee NOT_FETCHED.

— End CARRIED_STATUS.md. Outcome-blind; no return statistic computed or
used; missing evidence is NOT_RUN everywhere.
