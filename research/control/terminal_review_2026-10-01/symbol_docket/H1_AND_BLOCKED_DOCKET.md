# H1_AND_BLOCKED_DOCKET — Symbol docket, group C (PC12A terminal review 2026-10-01)

Scope: (i) USDCAD + AUDUSD — the H1 pairs whose legs carry TRAIN-only
diagnostics and died at Stage-A COST_DOMINATED (never reached scored
folds); (ii) the 7 data-blocked assets (NZDUSD, USDCHF, XAUUSD, XAGUSD,
BRENT, WTI, NATGAS).

Method: analysis of existing artifacts only. No new scored run, no engine
execution, no S1, no network. Every number below carries its artifact
path; anything not present in an artifact is marked **[NR]**. TRAIN-side
diagnostics are HYPOTHESIS-GENERATING ONLY (label `DISCOVERY-TRAIN-ONLY`,
`DIAG_MAIN_H1_*.json`; campaign §2: "Stage-A numbers NEVER enter any
publication as evidence of edge").

Cycle root (abbreviated `C/` below) =
`research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/`.

---

## PART 1 — USDCAD + AUDUSD (TRAIN-only forensics)

### 1.1 Eligibility lines (panels staged, costs, PIT)

**Panels (H1 ANC bar panels, staged by Stage-A wave 2)** — source
`C/data_freeze/H1_PANELS.json` (schema `pc12a_h1_panels_freeze@1`,
recorded 2026-09-30T11:31:47Z, `read_only: true`, source_cycle
ERP1-TRACKA-COHORT-1, source DATAGATE_REPORT BUILD_PASS both pairs):

| field | USDCAD | AUDUSD |
|---|---|---|
| rows | 30,386 | 30,420 |
| first_ts / last_ts | 2021-01-03T23:00Z / 2026-06-30T23:00Z | 2021-01-03T23:00Z / 2026-06-30T20:00Z |
| sha256 | `335a6e2aab25aebff17f9198f1b939448262186ed20e63f3041f8818d02f376b` | `4e0ca174a21e155271a481727259daa0d3df888bb9f96eb7a34d8c6f06881364` |
| columns | ts, b_o/b_h/b_l/b_c, a_o, a_c, s_open, s_close (9; ANC plane — no a_h/a_l) | same |
| nonpositive-spread rows | 0 | 0 |
| s_open pips p50/p90/p99 (census, whole panel) | 1.2 / 1.7 / 5.4 | 1.0 / 1.4 / 3.4 |
| pair facts | pip 0.0001, price_scale 100,000, quote USD | same |

Campaign fold window context (`C/campaign/BACKTEST_CAMPAIGN_DESIGN.md` §3):
2021-01-08 → 2026-06-26, panels end 2026-06 for H1 pairs (M1 tail beyond
2026-06-26 unused, one common calendar).

**Costs — measured cells and DECLARED bands.** Governing table
`research/control/SLEEVE-FX5-100K-V1/pitcost/COST_AUTHORITY_TABLE.md`
(C1/C2/C3 sections) and the frozen per-pair cells in
`C/data_freeze/H1_PANELS.json` `cost_cells_declared`:

- **C1 (Friday-20:00 fill cell)**: USDCAD **1.2 / 1.6 pips** (p50/p90,
  n=247/286 Fridays); AUDUSD **1.0 / 1.3 pips** (n=199/286). H1_PANELS
  carries the same cells with provenance "wave-2 dispatch
  COST_AUTHORITY_TABLE C1 note (governing); census overall_open p90
  1.4/1.7 disclosed alongside" (i.e., the census p90 1.7 USDCAD / 1.4
  AUDUSD is the disclosed-alongside figure; the governing cell is
  1.6 / 1.3).
- **C2_FRI (declared)**: USDCAD 1.3/2.0; AUDUSD 1.1/1.6 — "census
  friday_20_23_open quantiles" (H1_PANELS).
- **C2_MON_THU (declared)**: USDCAD 2.3/7.7; AUDUSD 2.0/5.4 — "census
  rollover_21_22 OPEN quantiles" (H1_PANELS).
- **C3 (Sunday reopen, measured)**: USDCAD 5.0/9.7 (n=233); AUDUSD
  2.8/6.3 (n=247) — COST_AUTHORITY_TABLE C3.
- DECLARED bands on every leg: commission U2 0.35 bps/side, slippage U3
  0.2/1.0 pip, swap U4/U5 1.0 pip/night against (Wed ×3) —
  `C/campaign/BACKTEST_CAMPAIGN_DESIGN.md` §4; stress tiers ×1.0/×1.5/×2.0
  on all variable cost components (`C/journal/FILL_ACCOUNTING_SPEC.md` §5).
- Eligibility rows (`C/eligibility/PORTFOLIO_ELIGIBILITY_1200.tsv`): all
  9 diagnosed legs have `price_axis=H1_BAR_PANEL`,
  `cost_axis=PROVISIONAL_PENDING_COST_AUTHORITY`, `pit_class=PRICE_ONLY`,
  `exploratory_status=EXPLORATORY_CANDIDATE`, block_reason "rules+data+cost
  testable on evidenced panels; ancestry carried as label only". All 100
  USDCAD rows and all 100 AUDUSD rows are `H1_BAR_PANEL`.

**PIT at the H1 clock** (`C/data_freeze/H1_PANELS.json`
`adapter_conventions`): hour-h bar [h,h+1) at minute slot h*60+59; the
engine stamps the close at (h+1):00 ("PIT-honest"); next-bar-open fills
execute at the next hour's open; "campaign 1 clock law: H1 pairs fill
from the 20:00-open bar". No intra-hour path is fabricated (each slot
carries its hour's true OHLC); day_open = first tradable hour's close
(coarser, disclosed); volume is a presence indicator (1.0) on traded
slots — lawful because no size-weighted consumer (VOLPROF) runs on H1
pairs.

Note on the audit trail: `C/poolB/data_audit/audit_summary.json`
(schema `pc12a_poolB_data_audit@1`) covers **M1 pairs only** — EURUSD,
GBPUSD, USDJPY (2,092 files/side, 1,440 records each, census tradable
minutes 2,130,647/2,130,680/… over 2021-01-01→2026-09-23). It contains
no USDCAD/AUDUSD rows; the H1 pairs' data audit lives upstream in the
source cycle (DATAGATE_REPORT, BUILD_PASS, cited in H1_PANELS
`source_report`).

### 1.2 Per-leg TRAIN outcome anatomy (all numbers from the DIAG jsons + ledger rows)

Files: `C/diagnostics/DIAG_MAIN_H1_USDCAD.json` /
`DIAG_MAIN_H1_AUDUSD.json` (tier 1.0, schema `pc12a_diag_report@1`,
label DISCOVERY-TRAIN-ONLY, data_digest `98a574b7…` USDCAD /
`495b32d4…` AUDUSD, max_train_end 2025-06-20) and the X2 stress variants
`C/diagnostics/DIAG_X2_H1_USDCAD.json` / `DIAG_X2_H1_AUDUSD.json`
(tier 2.0, fold 7 only, identical episodes/gross, cost_total exactly
×2.0 of MAIN). Ledger: `C/TRIAL_LEDGER.jsonl` stage A-DIAG — 90 rows for
these two symbols (72 MAIN fold rows + 18 X2 fold rows; every X2 leg has
a fold-7 row).

**Floor kills: none.** The dispatch framing "COST_DOMINATED / floors"
resolves, in the ledger, to COST_DOMINATED for all nine legs: zero
`NOT_RUN_THIN` (or any NOT_RUN_*) rows exist in TRIAL_LEDGER.jsonl for
these symbols (ledger-wide the only NOT_RUN strings are 14 A-MECH
`IMPLEMENTED` rows). Floors (campaign §3: ≥20 decisions full window /
≥3 per fold / ≥100 aggregate, frozen pre-Stage-A) were not the binding
constraint; the typed kills are all cost kills.

**Kills — all nine legs, typed COST_DOMINATED at stress tier ×2.0, fold 7
(train window 2021-01-08 → 2025-06-20)**, ledger detail verbatim:
`"typed kill: TRAIN expectancy at x2.0 measured spread + DECLARED bands
<= 0 per campaign §4"`, recorded_utc 2026-09-30T13:45:23Z. Row IDs:
AUDUSD ADIAG-W2-0669/0671/0673/0675/0677/0679; USDCAD
ADIAG-W2-0681/0683/0685. (Artifact nuance, not smoothed: campaign §4
line 78 says a leg whose TRAIN expectancy dies at ×1.5 is
COST_DOMINATED, but the operative ledger carries only MAIN and X2 tags —
no X1.5 rows exist in A-DIAG — and every recorded kill is typed at ×2.0.)

Full-window (fold 7) anatomy, MAIN (×1.0) vs X2 (×2.0) — gross, costs,
net, expectancy per trade, decision counts (source: DIAG jsons fold 7;
ledger rows ADIAG-W2-0107…0147 for MAIN):

| leg | mech (family) | outcome label | n_dec / entries / fills / closed (f7) | gross | costs ×1.0 → ×2.0 | net ×1.0 → ×2.0 | exp/trade ×1.0 → ×2.0 |
|---|---|---|---|---|---|---|---|
| USDCAD-S004 | tsmom_20d (A-TREND) | F0_INDIVIDUAL_REJECT | 47 / 6 / 11 / 5 | +322.00 | 1,194.36 → 2,388.72 | −872.36 → −2,066.72 | −145.39 → −344.45 |
| USDCAD-S011 | rsi2_fade (B-MEANREV) | FAMILY_HISTORY_NEGATIVE | 76 / 38 / 76 / 38 | +393.80 | 282.08 → 564.15 | **+111.72** → −170.35 | +2.94 → −4.48 |
| USDCAD-S091 | vol_regime_alloc (J-REGIME_OPT) | FAMILY_HISTORY_NEGATIVE | 90 / 13 / 41 / 13 | +673.65 | 360.04 → 720.08 | **+313.61** → −46.43 | +24.12 → −3.57 |
| AUDUSD-S002 | donchian_breakout (A-TREND) | F0_INDIVIDUAL_REJECT | 15 / 2 / 3 / 1 | +962.00 | 1,494.61 → 2,989.22 | −532.61 → −2,027.22 | −266.30 → −1,013.61 |
| AUDUSD-S003 | adx_macd_persistence (A-TREND) | F0_INDIVIDUAL_REJECT | 24 / 2 / 3 / 1 | −846.25 | 1,391.93 → 2,783.87 | −2,238.18 → −3,630.12 | −1,119.09 → −1,815.06 |
| AUDUSD-S006 | tsmom_3_12 (A-TREND) | FAMILY_HISTORY_NEGATIVE | 184 / 1 / 184 / 0 | −516.90 | 1,388.24 → 2,776.47 | −1,905.14 → −3,293.38 | −1,905.14 → −3,293.38 |
| AUDUSD-S026 | vol_compression_breakout (C-BREAKOUT) | FAMILY_HISTORY_NEGATIVE | 28 / 2 / 4 / 2 | −66.20 | 24.81 → 49.62 | −91.01 → −115.82 | −45.50 → −57.91 |
| AUDUSD-S029 | weekly_range_breakout (C-BREAKOUT) | FAMILY_HISTORY_NEGATIVE | 120 / 49 / 98 / 49 | −249.35 | 933.49 → 1,866.98 | −1,182.84 → −2,116.33 | −24.14 → −43.19 |
| AUDUSD-S096 | vol_target_sizing (J-REGIME_OPT) | FAMILY_HISTORY_NEGATIVE | 1,132 / 1 / 1,132 / 0 | −1,539.84 | 2,009.08 → 4,018.15 | −3,548.92 → −5,558.00 | −3,548.92 → −5,558.00 |

Reading (arithmetic on the table above, derived here, not an artifact
statement):

- At ×1.0, seven of nine legs were already net-negative; only USDCAD-S011
  (+111.72) and USDCAD-S091 (+313.61) survived ×1.0 and both flipped at
  ×2.0. No H1 leg passed ×2.0 — hence zero H1 legs in the Stage-C scored
  set (ledger C-SCORED corpus_gids contain no USDCAD-/AUDUSD- legs; the
  12 scored legs are EURUSD ×4, GBPUSD ×2, USDJPY ×6).
- Gross-vs-cost decomposition is available at total level (columns
  above). **Per-component cost decomposition (spread vs slippage vs
  commission vs swap dollars) is [NR]** in the DIAG jsons — only
  `cost_total_usd` and `n_swap_events` are recorded.
- Swap exposure by count is extreme on long-hold legs: fold-7
  `n_swap_events` / `n_fills` = S002 1,058/3 · S003 985/3 · S006 889/184 ·
  S096 1,107/1,132 · S004 831/11 (DIAG jsons). With swap DECLARED at 1.0
  pip/night against (Wed ×3), swap-nights are the numerically dominant
  recurring cost event on every hold-heavy leg; dollar attribution [NR].

**Cost anatomy → H1 fill cadence (what the artifacts say):**

- **C2 structural absence** (COST_AUTHORITY_TABLE C2): the 21:00-open bar
  exists on only **431 / 30,043 weekday rows (1.4%)** for USDCAD and
  **320 rows** for AUDUSD; when present, s_open is 1.2/2.3 (USDCAD) and
  1.2/2.9 (AUDUSD) pips. The authority's rule: "H1 absence is surfaced,
  never smoothed" — rollover-window H1 pricing rests on a nearly empty
  cell.
- **20:00-open absence → Sunday-reopen deferral** (COST_AUTHORITY_TABLE
  C1 caveat (i)): on the **39/286 Fridays (13.6%)** (USDCAD) and
  **87/286 (30.4%)** (AUDUSD) without a 20:00-open bar, the fill defers
  to Sunday reopen and is charged at **C3**, not C1 — USDCAD 5.0/9.7 vs
  C1 1.2/1.6; AUDUSD 2.8/6.3 vs C1 1.0/1.3. AUDUSD's deferral rate is
  2.2× USDCAD's, and its C3 p90 is 4.8× its C1 p90 — an asymmetric
  structural cost penalty on the weekly clock that lands on the pair with
  the thinner Friday book. (Per-leg deferral counts [NR] — DIAG jsons do
  not record which fills deferred.)
- FILL_ACCOUNTING_SPEC §3 (lines 176–177) closes the loop: "H1 pairs
  without a 20:00-open bar defer to Sunday reopen and price here (C1
  caveat (i), same law)" — S_eff = max(window p90, general p90) + 1.0 pip
  event slip.

### 1.3 Entry-time / exit-mechanism observations the TRAIN artifacts DO support

Schema read first (`pc12a_diag_report@1`): per leg — leg_id, symbol,
family_id, cluster_id, mech_key, sleeve_id (POOL_B_TRIAGE), tier,
outcome_exposed_label, arm_config_digest; per fold — train_window,
friday_equity (weekly mark series), n_decisions/n_entries/n_fills/
n_closed_episodes, n_swap_events, gross/cost/net USD,
expectancy_per_trade_usd, mark_close, units_open, residual_usd; per
episode (final fold shown in `episodes_serialized`) — direction,
entry_ts, exit_ts, units. What the episodes support:

- **Decision clocks.** Eight of nine legs stamp every final-fold entry at
  **T00:00:00Z** — the daily decision clock on the H1 panel (close of the
  23:00 bar, PIT-honest per the slot-mapping law). The exception is
  AUDUSD-S029 (weekly_range_breakout): all 49 final-fold entries land on
  the 4-hour grid at 04/08/12/16/20 UTC (counts 14/11/6/5/13) and never
  at 00 — an H4-cadence rule (H1_PANELS: D1/H4 aggregates from slots
  preserve true highs/lows/first/last).
- **Position sizing.** Every closed episode on all nine legs is a fixed
  10,000-unit clip (units=10000). Sizing variation exists only on the two
  never-closing legs: AUDUSD-S006 fold-7 units_open −12,809; AUDUSD-S096
  fold-7 units_open +12,429 (with fold-sequence units_open ranging e.g.
  −10,282 … +12,627 on S006) — continuous vol-target/TSMOM resizing
  journaled as fills, not episodes (S006: 184 fills on n_trades=1; S096:
  1,132 fills on n_trades=1).
- **Direction mix.** USDCAD-S004: all 5 final-fold episodes long.
  AUDUSD-S029: 40 of 49 short. USDCAD-S011: 30 long / 8 short (DIAG
  episode arrays).
- **Hold durations** (final fold, computed from entry/exit dates):
  S004 9/34/51 days (min/med/max) · S011 1/4/17 · S091 1/8/105 ·
  S002 47/47/47 (single episode) · S003 85/85/85 (single) · S026 12/12/12
  · S029 0/4/120.
- **Decision-to-entry ratios.** Most decisions are no-trade on the
  regime legs: S091 90 decisions → 13 entries; S004 47 → 6. The resize
  legs decide daily and fill daily (S096 1,132/1,132).
- **Weekly equity marks** exist per fold (friday_equity dictionaries),
  mark_close per fold; residual_usd = 0 on every fold (book identity
  clean at both tiers).
- **Stress behavior.** X2 variants are byte-comparable reruns of fold 7
  with cost_total exactly ×2.0 (e.g. USDCAD-S004 1,194.359891 →
  2,388.719884; AUDUSD-S002 1,494.61 → 2,989.22); episodes, gross and
  decision counts identical to MAIN.

Everything else — intra-episode MAE/MFE, per-fill spread cell actually
charged, deferral flags, per-component cost dollars, causal-control
per-leg readouts for these two symbols (**[NR]**: DIAG_CONTROLS.json
covers the M1 scored legs' controls; no H1 control variant file exists in
`C/diagnostics/`) — is [NR].

### 1.4 Falsifiable hypotheses IF a future calendar/panel upgrade arrives

Framed per the docket law: trigger / rationale / predicted benefit /
failure condition / floor. Each names the exact data that would test it.

- **H-C1 (spread-cell-driven cost dominance on the two near-miss legs).**
  Trigger: panel/calendar upgrade that yields per-fill hour-stamped
  pricing (or an owner-frozen per-hour cell schedule; note COST_AUTHORITY
  Appendix A already claims a measured full per-hour p50/p90 schedule,
  24 UTC hours × 5 pairs — "for the panel venue only"). Rationale: at ×1.0
  USDCAD-S011 (+111.72) and S091 (+313.61) were net-positive and died
  only at ×2.0 — the gross-vs-cost margin is thin, and 13.6% of USDCAD
  Friday fills are forced into the 4–6× wider C3 reopen cell. Prediction:
  re-pricing entries at hours with measured sub-p90 s_open (and/or
  eliminating 20:00-bar deferrals to the first available hour) flips the
  ×2.0 verdict on exactly these two legs, not the seven already
  net-negative at ×1.0. Test data: per-episode fill timestamps joined to
  per-hour measured s_open cells, recompute cost_total, re-read the ×2.0
  rule. Failure condition: with measured entry-hour cells, ×2.0 TRAIN
  expectancy remains ≤ 0 on S011/S091 — hypothesis dead, cost dominance
  is gross-edge-driven, not cell-driven. Floor: ≥0 net at ×2.0 on the
  full fold-7 window with identity digests re-derived (any measurement
  replacing a DECLARED band bumps `defaults_digest`; trials under
  different digests are not comparable without re-running both —
  COST_AUTHORITY standing rule).
- **H-C2 (swap drag dominates the AUDUSD hold-heavy legs).** Trigger:
  the owner Activity/Flex statement (Interest Accruals rows) replacing
  the DECLARED U4/U5 pessimistic-symmetric swap calendar (COST_AUTHORITY
  §3 upgrade table, swap C5). Rationale: fold-7 swap events outnumber
  fills by 353:1 on S002 (1,058:3) and 985:3 on S003; swap is declared
  1 pip/night against, never income (campaign §4), so multi-month holds
  accrue hundreds of pip-nights regardless of spread cells. Prediction:
  two-sided measured swap rates move AUDUSD long-hold net more than any
  spread-cell change; if measured swap income exists on either side of
  these books, S002's +962.00 gross could survive netting. Test data:
  cost decomposition per component [currently NR] recomputed with
  measured swap calendar, same folds. Failure condition: net-of-measured-
  swap ×2.0 expectancy still ≤ 0 on all four hold-heavy AUDUSD legs
  (S002/S003/S006/S096). Floor: sign flip at ×2.0 with the swapped-in
  measured calendar, defaults_digest bumped.
- **H-C3 (deferral asymmetry is an AUDUSD-specific artifact).** Trigger:
  a denser Friday panel (or an amended fill law allowing the next
  available hour after 20:00 Friday at C1-class pricing). Rationale:
  AUDUSD misses the 20:00-open bar on 87/286 Fridays vs USDCAD 39/286 —
  a 2.2× deferral rate charging C3 2.8/6.3 instead of C1 1.0/1.3.
  Prediction: replacing deferral pricing with next-available-hour C1
  pricing reduces AUDUSD leg cost_total by approximately
  (87/286) × per-fill (C3−C1) crossing gap, a larger relative change than
  on USDCAD; the AUDUSD cost ranking vs USDCAD narrows. Test data:
  per-fill deferral flags (requires the upgraded panel/journal; [NR]
  today), recomputed cost_total under both fill laws. Failure condition:
  recomputed AUDUSD costs change < 5% (i.e., deferrals were not the
  binding cadence cost) or AUDUSD legs remain ≤ 0 at ×2.0 either way.

---

## PART 2 — The 7 data-blocked assets

Common frame (all citations:
`C/ibkr_capability_probe_2026-09-30/GATE_TABLE_7ASSETS.md` (GT),
`.../data_freeze/IDENTITY_FREEZE_2026-09-30.json` (IF),
`.../LEG_RESOLUTION_MATRIX.tsv` (MX, 294 rows) and
`.../LEG_RESOLUTION_MATRIX.md` (MX.md),
`.../ERRATUM_LABELS_2026-09-30.md` (ERR)). Probe = IBKR-BOUNDED-ACQ-2026-09-30,
read-only, 131 raw files, DV re-hashed 131/131 with 0 mismatches
(DV_VERIFICATION_EVIDENCE.json; GT verification table). Identity fields
are AS REPORTED (conId etc. cannot be re-derived from raw bars — F-4, IF
`identity_caveat`). Nothing below is an eligibility change: IF header —
"daily data does NOT raise any leg's status; M1/intraday remain NOT_RUN;
admission requires a plan amendment + trial accounting per owner law."

Matrix row counts per blocked asset (counted from MX `probe_assets`
column; classes per MX.md: (a) ALREADY-RUNNABLE 150 · (b)
NEW-DAILY-CANDIDATE 7 (BLOCKED pending amendment) · (c) STILL-NOT_RUN 128
· (d) FUTURES-BLOCKED 9):

| asset | rows naming it in MX | class breakdown |
|---|---|---|
| NZDUSD | 5 | (b) NEW-DAILY-CANDIDATE ×5 — AUDUSD-S081, USDJPY-S083, EURUSD-S006/S061/S085 |
| USDCHF | 4 | (b) ×4 — USDJPY-S083, EURUSD-S006/S061/S085 |
| XAUUSD | 2 | (b) ×2 — USDJPY-S063, AUDUSD-S100 |
| XAGUSD | 0 | none — "no triage row needs only silver" (MX.md; EURUSD-S068 names HG copper, XAG proxy unverified) |
| BRENT | 1 | (d) FUTURES-BLOCKED ×1 — USDJPY-S065 (Brent leg evidenced G-PIT-V3; NATGAS chain absent) |
| WTI | 7 | (d) ×7 — USDCAD-S005/S062/S081/S089/S098, USDCAD-S090, EURUSD-S063 |
| NATGAS | 4 | (d) ×4 — USDCAD-S065, USDJPY-S065, EURUSD-S063, USDCAD-S090 |

(STILL-NOT_RUN is attributed to the leg's own symbol in MX.md's count
table — EURUSD 24, GBPUSD 31, USDJPY 21, USDCAD 21, AUDUSD 31 — not to
the blocked input asset; the rows above are the ones a given unblock
would actually feed.)

### NZDUSD — FX spot (CASH)

- Vehicle: FX-spot, 100/100 census rows (GT). Identity as reported:
  conId 39453441, NZD.USD, CASH, IDEALPRO, USD, minTick 5e-05 (IF).
- Price: span **PASS** — D1 BID+ASK 2020-10-02→2026-09-30, 1,553
  days/side, 0 holes >5d, max calendar gap 4d (IF `panel_daily`;
  DV-verified). Interior intraday gaps **NOT_RUN_INTERIOR_GAPS** (ERR
  label correction: the PROBE_RESULT `gaps_2021_now: PASS` was sample
  capability only, 4 daily MIDPOINT bars). M1 **NOT_RUN_SIZE_CAP**
  (3 M1 sample days + 6 March H1 windows, samples only).
- PIT: **NOT_RUN** — "no cross-source overlap measured for NZDUSD" (GT).
- Cost: **NOT_RUN** — spread measured p50 0.88 / p90 18.65 / max 239.07
  bps (IF `spread_daily`, n=1,553); commission/swap/slippage unmeasured
  (no Activity/Flex statement).
- Legs if unblocked: 5 corpus rows (MX above) — all DAILY/MULTIWEEK/WEEKLY
  clock, basket/band rules.
- Exact unlocking action (GT "Single named action per blocker"): costs →
  owner exports IBKR Activity/Flex statement (FX trades + Interest
  Accruals) to `~/.my-quantitative-data/ibkr_statement/` (one export also
  covers USDCHF/XAUUSD/XAGUSD); PIT → owner declares the panel-of-record
  and availability lag. **Both owner-only** — the statement requires the
  owner's brokerage account (owner-documents list, P_A); the declaration
  is an owner decision. No Lead-fetchable (free/keyless) action is named
  by the gate table; the daily bars themselves are already acquired and
  frozen (IF), so there is no remaining "fetch".
- **Cannot support trade-level inference yet** (PIT NOT_RUN, costs
  NOT_RUN, admission requires plan amendment — GT footer).

### USDCHF — FX spot (CASH)

- Vehicle: FX-spot, 100/100 census rows (GT). Identity: conId 12087820,
  USD.CHF, CASH, IDEALPRO, CHF, minTick 5e-05 (IF).
- Price: span **PASS** — 1,553 d/side, 2020-10-02→2026-09-30, 0 holes
  (IF, DV-verified); intraday interior NOT_RUN_INTERIOR_GAPS; M1
  NOT_RUN_SIZE_CAP.
- PIT: **NOT_RUN** (GT). Cost: **NOT_RUN** — spread measured p50 4.51 /
  p90 16.02 / max 216.10 bps (IF, n=1,553); no statement.
- Legs if unblocked: 4 corpus rows (MX) — same basket family as NZDUSD.
- Exact unlocking action: identical to NZDUSD (same statement export; same
  PIT declaration) — **owner-only**, same reasoning.
- **Cannot support trade-level inference yet.**

### XAUUSD — spot gold (CMDTY)

- Vehicle: `metals-spot-TBC` 100/100 census rows; the probe converts the
  venue TBC into pinned evidence: IBKR CMDTY XAUUSD SMART USD (London
  Gold), minTick 0.01 — "usable as the executable-venue exhibit in a
  future amendment, NOT an eligibility change today" (GT). Identity: conId
  69067924 (IF).
- Price: span **PASS** — 1,544 d/side, 2020-10-02→2026-09-30, 0 holes,
  max gap 4d (IF); intraday interior NOT_RUN_INTERIOR_GAPS; M1
  NOT_RUN_SIZE_CAP.
- Cost: **NOT_RUN** — spread measured p50 5.52 / p90 18.61 / max 74.17
  bps, n=1,543 (one crossed-book day excluded by the a≥b rule:
  2025-05-23, BID close 3,361.0 > ASK close 3,359.78 — IF
  `spread_caveats`); commission/swap/slippage unmeasured.
- **PIT — measured but unfrozen (the extra detail):** overlap vs the TD
  archive `XAUUSD_1day_full.json` (archive sha256 `49c2684e…`,
  DV-verified; **F-2**: exists only at the forex-ng6 worktree path
  hardcoded in acquire_bounded.py, NOT under
  research/control/DATA-FOUNDATION-SIXSOURCE-V1/ — owner must pin the
  canonical location): 1,531 days aligned, 2020-10-02→2026-09-16 (ends
  where the TD archive ends), abs basis p50 3.2462 bps / p95 26.5142 bps,
  signed mean +0.3359 USD (IF `xau_overlap_vs_td_archive`; GT
  verification table: reproduces exactly). But: `pit_lag =
  ASSUMED_NEXT_BUSINESS_DAY`, `pit_status = NOT_MEASURED`,
  `basis_acceptance = NOT_RUN_THRESHOLDS_UNFROZEN` (IF, GT PIT row
  "MEASURED-BUT-UNFROZEN"). Basis definition: HMDS daily (BID+ASK)/2 mid
  minus TD close — not the frozen 17:00 ET window mid.
- Legs if unblocked: 2 corpus rows (MX) — AUDUSD-S100 (crisis-alpha tail
  switch) and USDJPY-S063 (gold–JPY safe-haven), both DAILY-clock, VIX
  already evidenced (GT).
- Exact unlocking action (GT): costs → same Activity/Flex export
  (owner-only); PIT → **owner freezes the numeric basis-acceptance
  thresholds** in
  `research/control/xauusd_ibkr_probe_2026-09/td_archive_join_contract.json`
  (currently unfrozen) and either accepts the assumed next-business-day
  lag or funds a publish-timestamp measurement — one decision + one
  threshold freeze (owner-only). Venue: no further data action
  (identity evidenced, F-4 caveat).
- **Cannot support trade-level inference yet** — thresholds unfrozen, lag
  assumed, costs NOT_RUN.

### XAGUSD — spot silver (CMDTY)

- Vehicle: `metals-spot-TBC`, 100/100 census rows (GT). Identity: conId
  77124483, XAGUSD, CMDTY, SMART, USD, minTick 0.0005 (IF).
- Price: span **PASS** — 1,544 d/side, 2020-10-02→2026-09-30, 0 holes
  (IF); intraday interior NOT_RUN_INTERIOR_GAPS; M1 NOT_RUN_SIZE_CAP.
- Cost: **NOT_RUN** — spread measured p50 10.35 / p90 40.83 / max 162.81
  bps — "the widest p50 of the four — cost-gate relevant for any future
  silver leg" (GT; IF n=1,544).
- PIT: **NOT_RUN** — "no independent XAG archive on file to overlap
  against" (GT).
- Legs if unblocked: **0** (MX). No triage row needs only silver;
  EURUSD-S068 names HG copper and its source explicitly flags the XAG
  proxy as unverified — stays class (c) "unless the owner accepts the
  proxy (a corpus decision, not a probe delivery)" (MX.md).
- Exact unlocking action (GT): costs → same statement export (owner-only);
  PIT → owner names an independent XAG daily archive or declares IBKR
  HMDS the panel of record (owner decision). Identity frozen "for future
  cohorts even though no current leg consumes it" (GT).
- **Cannot support trade-level inference yet** — and additionally has no
  consumer leg in the current corpus.

### BRENT — ICE Brent outright futures (FUT COIL IPE)

- Vehicle: `energy-futures/CFD-TBC`, 100/100 census rows; frozen
  pre-declaration: ICE Brent outright COIL on IPE (BZ Last-Day the
  unselected alternate; BRN/IPE returned error 200; CFD not a candidate)
  (GT). The corpus legs citing "Brent daily close (G-PIT-V3)" use the
  existing PIT dossier archive, NOT this probe (GT).
- Gates (GT BRENT table): span(chain) **FAIL** — no certified chain
  reaches 2021; the CONTFUT 6Y span PASS is over a synthetic-majority
  series (front COILX6 conId 361002948; CONTFUT COILZ6 conId 361002955
  ≠ front; expired FUT quarters 202103–202506 all error 200; CONTFUT 6Y
  1,549 bars 2020-10-01→2026-09-30, 0 holes, but **63% flat-OHLC
  zero-volume synthetic** — 100% of 2020–2022 bars, 0% from 2025 — F-1);
  roll rule **FAIL** (adjustment method not in contract details; CONTFUT
  localSymbol is one month); chain **FAIL**; entitlement **FAIL** (live
  error 354; delayed no quote); costs **NOT_RUN**; PIT **FAIL/NOT_RUN**
  ("no PIT source exists for a chain that does not exist"). Interior
  gaps NOT_RUN_INTERIOR_GAPS; M1 NOT_RUN.
- Legs if unblocked: 1 row (MX) — USDJPY-S065 (Brent leg already
  evidenced G-PIT-V3; the NATGAS half of that row is what is absent).
  Signal-only Brent-daily-close rows already run on the G-PIT-V3 archive
  and are unaffected (GT).
- Exact unlocking action (GT): one owner decision names the certified
  roll-chain source (licensed vendor or ICE-direct back-adjusted series
  with documented roll + adjustment rule, or an owner-accepted CONTFUT
  convention with the F-1 synthetic-bar disclosure) — clears the
  chain/span/roll evidence path; plus ICE (IPE) market-data subscription
  toggle on the paper account; plus the same Activity/Flex statement.
  **All owner-only** — a licensed chain series is not free/keyless, and
  the subscription lives on the owner's account. "No honest amendment
  scope exists until the chain source is named; futures columns stay
  BLOCKED (FLAT-by-authority)" (GT).
- **Cannot support trade-level inference yet.**

### WTI — NYMEX crude futures (FUT CL NYMEX)

- Vehicle: `energy-futures/CFD-TBC`, 100/100 census rows (GT).
- Gates (GT WTI table): span(chain) **FAIL** (same F-1 basis; CONTFUT 6Y
  1,526 bars, 61% flat synthetic); roll rule **FAIL**; chain **FAIL** —
  CONTFUT echoes the SAME conId as front CLX6 304037511 with a
  single-month localSymbol (ERR: "proof it is not a chain"); entitlement
  **FAIL** (live 10168 delayed-not-enabled; delayed type3 no positive
  quote); costs **NOT_RUN**; PIT **FAIL/NOT_RUN**; interior gaps
  NOT_RUN_INTERIOR_GAPS; M1 NOT_RUN. Retry front-FUT 1Y TRADES / 5d
  BID/ASK numbers exist only in ADDENDUM_FUTURES_RETRY.json with **no raw
  file landed** — REPORT_ONLY until re-pulled (F-3, GT verification
  table).
- Legs if unblocked: 7 rows (MX) — USDCAD-S005 (CL1–CL6 curve), S062
  (short-WTI execution), S081 (cointegration execution), S089 (S62
  overlay), S098 (6M slope), S090 + EURUSD-S063 (with NATGAS).
  Signal-only WTI daily-close rows (USDCAD-S001/S008/S013/S017/S063)
  already run on G-PIT-V3 and are unaffected (GT).
- Exact unlocking action (GT): chain-source decision (as BRENT, NYMEX
  flavor) + NYMEX subscription toggle + Activity/Flex statement — **all
  owner-only**, same reasoning as BRENT.
- **Cannot support trade-level inference yet.**

### NATGAS — Henry Hub futures (FUT NG NYMEX)

- Vehicle: `energy-futures/CFD-TBC`, 100/100 census rows; the
  weather-gated ladder ideas (S001/S024/S058/S074/S094) stay
  BLOCKED_NO_PRICE_DATA (GT).
- Gates (GT NATGAS table): span(chain) **FAIL** (CONTFUT 6Y 1,526 bars,
  41% flat synthetic; front NGX26 conId 269460170, CONTFUT same-conId
  echo — ERR); roll rule **FAIL**; chain **FAIL**; entitlement **FAIL**
  (live 354; delayed 10167 then no positive quote); costs **NOT_RUN**;
  PIT **FAIL/NOT_RUN**; interior gaps NOT_RUN_INTERIOR_GAPS; M1 NOT_RUN.
- Legs if unblocked: 4 rows (MX) — USDCAD-S065 (NATGAS + AECO), USDJPY-
  S065 (NATGAS+Brent), EURUSD-S063 (Henry Hub + TTF), USDCAD-S090
  (NATGAS/WTI ratio). **Extra honesty item (GT):** AECO (USDCAD-S065)
  and TTF (EURUSD-S063) are not IBKR-traded instruments at all — those
  rows additionally need an owner-named gas-hub price source; an IBKR
  chain alone can never clear them.
- Exact unlocking action (GT): chain-source decision (NYMEX NG) + NYMEX
  subscription + Activity/Flex statement — **owner-only**; the AECO/TTF
  rows additionally require the owner to name a gas-hub source.
- **Cannot support trade-level inference yet.**

---

## PART 3 — Cross-symbol notes

**Who could realistically join a successor cycle's validation calendar
(fresh data)?** Per the GATE_TABLE amendment footer ("Exact scope
available today"):

- **NZDUSD, USDCHF, XAUUSD, XAGUSD** — admissible scope exists today for
  a **daily-clock (D1 BID/ASK) cohort, daily-horizon cross-asset rules
  only**, identity per IDENTITY_FREEZE, spreads measured, **still gated**
  on costs (statement export) and PIT (declaration / threshold freeze),
  and on the plan amendment itself (plan §2: "blocked columns activate
  ONLY via their named owner unblock + PIT/cost gates, as plan
  amendments"). H1/M1 legs on these assets remain NOT_RUN. The 7 corpus
  rows this would make data-ready are the MX class-(b) rows listed in
  Part 2.
- **BRENT, WTI, NATGAS** — cannot join: "no honest amendment scope exists
  until the chain source is named"; futures columns stay BLOCKED
  (FLAT-by-authority).
- **EURUSD, GBPUSD, USDJPY** — already fully paneled (M1) through
  2026-09-23 (`C/poolB/data_audit/audit_summary.json`); the cycle's
  common calendar capped use at 2026-06-26 (campaign §3); extension is an
  owner amendment.
- **USDCAD, AUDUSD** — H1 panels staged through 2026-06-30 (H1_PANELS);
  their M1-feature families remain BLOCKED_DATA by the H1 ceiling (PIT
  freeze R6 — a data-plane verdict, not a cost one; COST_AUTHORITY_TABLE
  §2 note). A successor cycle could re-attempt them only with a changed
  mechanism axis (TERMINAL_DECISION reopening condition Q-10) and/or the
  Part-1 hypotheses tested.

**The honest count: 3 of 12 assets support trade-level inference today.**

- EURUSD, GBPUSD, USDJPY: the only symbols whose legs reached Stage-C
  scored test folds — all 12 scored MO legs in TRIAL_LEDGER (C-SCORED
  corpus_gids `C-B1_MO_*`) sit on these three pairs (EURUSD ×4 incl.
  VC2-LVNFAIL, GBPUSD ×2, USDJPY ×6 incl. VC2-LVNFAIL); scored evidence
  chain per `C/TERMINAL_DECISION.md` (846/1,500 ledger rows, budget
  40/48, typed close POLICY_NO_INCREMENTAL_VALUE).
- USDCAD, AUDUSD: 9 legs diagnosed, all 9 killed COST_DOMINATED at ×2.0
  before any scored fold — TRAIN-only, hypothesis-generating (this
  docket, Part 1). Not inference.
- NZDUSD, USDCHF, XAUUSD, XAGUSD, BRENT, WTI, NATGAS: no admissible
  panel in the cycle; every inference gate at NOT_RUN/FAIL per Part 2.
  Not inference.

**Statement of record:** every conclusion above is read from artifacts;
no backtest was run, nothing was re-scored, and no statement about what
any leg "would have" shown is made.
