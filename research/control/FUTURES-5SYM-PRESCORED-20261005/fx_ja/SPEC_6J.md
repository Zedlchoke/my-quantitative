# SPEC_6J — Japanese Yen futures (CME 6J) executable-spec DRAFT, outcome-blind

- Lane **FXJA**, round **FUTURES-5SYM-PRESCORED-20261005**, worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep`
  (branch `prep/futures-5sym-prescored-20261005`, base `ffed828f73fa19fa0ff4aee3ac1b441909a43940`).
- Class: **PREP-only draft.** 0 scored runs, 0 PnL, 0 conditional-on-signal
  statistics, 0 registrations. This spec is NOT frozen, NOT registered, NOT
  authorized. `NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER` in force. It is
  written to the structure of the ES precedent
  `research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md` so a future freeze
  can consume it section-for-section.
- **Standing blockers restated (never reopened):** 6J has **no trial cap** —
  an explicit owner **ceiling signature** is required before any registration
  (CENSUS_FINAL §4); fees are **MODELED COST / UNDER REVIEW /
  VERIFIED_VS_ACCOUNT=NOT_RUN** (A7/D2 open); **BBO NOT_RUN** (D5 law) —
  conservative fill law binds; **BoJ intraday stamps NOT_IN_CORPUS** (owner
  decision). Missing evidence is NOT_RUN, never inferred PASS.
- Every load-bearing number cites a committed artifact; hashed artifacts carry
  sha256. New decision IDs are prefixed **P5-** (see
  `GAPS_AND_DECISIONS_6J_6A.md`).

---

## §1 Instrument identity — VERIFIED (measured, not assumed)

| item | value | evidence of record |
|---|---|---|
| Symbol / venue | 6J, CME Globex | dossiers `FUTURES-DEEPRESEARCH-V2-20261003/dossiers_v2/6J_DEEP_v2.md` (sha256 `ef95ad8dd062e654e958f44ca06e47af22c44dc9a3c451a67528b9e7f4cdb92f`) |
| Multiplier | **12,500,000 JPY** | `fx_ja/6j_identity.json` (FUTURES-SIX-READINESS-20261004, sha256 `c342e872a637d07fe3f57cfc3f9d1984c6ff1b4b12af8e5fbd81f2f5c048ca95`): `unit_of_measure_qty` = 12500000000000000 int-nano = 12,500,000 JPY decoded, unique across all 72 definition rows 2023-10+; corroborated by `S1_IDENTITY.json` `symbols.6J.front.multiplier='12500000'` (sha256 `d217ab9dcd865765e1bcae8f8131dee2f7f200cd90c07403280134da32b05822`, re-hashed and matched that lane) |
| Tick | **5e-07 USD/JPY = $6.25/contract** | same `6j_identity.json`: `min_price_increment` = 500 int-nano **unique across all 72** definition rows; observed close-to-close increment **GCD = 500 int-nano in all three sampled eras** (2020-03 backfill, 2023-01, 2026-07); the coarser 1e-6 grid FAILS (48.49% of closes on-grid in the 2020-03 window; ≤ threshold) — the dispatch's tentative 1e-7/$1.25 alternative and any 1e-4/$12.50 legacy are **rejected on data** |
| Quote orientation | **USD per JPY; 6J price UP = JPY strengthens vs USD** | **QUOTE-DIRECTION LAW, §2 below — PROVEN from own raw slice** |
| Representative notional | **$79,787.50** = 12,500,000 × 0.006383 | `fx_ja/6j_orientation_recheck.json` (sha256 `6ca0baebe85abc7df9204f70252da44e72e0e396751a5114561640a25331ae54`): representative price re-measured from the raw 2026 tail (last bar 2026-09-30 23:59Z) |
| Residual identity note | legacy 1e-4 "JY" (TradingCharts-class) tick stays unadjudicated vs the CME rulebook (BLOCKED_TRANSPORT) — moot on this corpus (zero support in 2.84M bars) | DATA_READINESS_6J.md Dim 1 |

**Verification status: PASS as stated in the dispatch task.** Tick 0.0000005 =
$6.25 and multiplier 12,500,000 JPY are both measured from vendor definition
rows AND from the price grid itself; no assumption is load-bearing.

## §2 QUOTE-DIRECTION LAW (explicit, load-bearing for every sign in any 6J arm)

**6J is quoted USD per JPY. When the yen STRENGTHENS against the US dollar,
the 6J price RISES.** Every drift/reversal sign, every "decision-window move
sign", every continuation arm convention in this spec is expressed **in 6J
price terms** (yen-strong = positive 6J return). No arm may re-express
signals in USDJPY terms without an explicit sign inversion declared in its
identity table.

Proven from this program's own raw slice (not vendor docs):
`fx_ja/6j_orientation_recheck.json` — 2024-07-11 (MOF intervention day), front
contract 6JU4: session open 0.0062485 → close 0.0063565 (**+1.73%** in the
dossier's CT-trade-date convention; day range 0.0062415–0.0064140) while the
implied USDJPY fell **160.04 → 157.32** — yen stronger, 6J price UP. Burst
minute exact: 12:41→12:42 UTC close 0.0062800 → 0.0063325 = **+105 ticks in
one minute**, 12:42Z volume 17,448 lots (bit-identical to `6J_DEEP_v2.md` §5
and the sibling P3 re-proof).

Framing note (contradiction disclosed, not smoothed): the P3 check's "415,392
lots / close 0.0063775 / +2.056%" are **UTC-calendar-day aggregates**
(re-measured +2.07%); the dossier's CT-session convention gives 364,917 lots /
+1.73%. Both framings prove the same law; the P3 session label was the only
mislabeled element.

## §3 Session law + DST (calendar facts only; no trading claim)

- Template: **23h CT continuous, 17:00 → 16:00 CT, 1,380 nominal minutes, no
  maintenance break; median held session 1,357 1m bars** (measured;
  `6J_qa_ledger.json` via `6J_DEEP_v2.md` §8; JPY_AUD_HYPOTHESES JF1 f4).
- Clock laws: **all Tokyo-side windows (BoJ MPM window, Tokyo morning) are
  bucketed in Asia/Tokyo local time, DST-correct via zoneinfo** — the BoJ
  decision window is US-overnight (~22:00–01:00 CT) and only Tokyo-clock
  bucketing keeps it stable across US DST flips (DC §1.2; JF1 f4 local-clock
  law). US/London/UTC offsets enter only as calendar facts; **JF3's C3″
  DST-mismatch falsifier** (a ±1h CT shift of a Tokyo-anchored effect = clock
  bug, kill) is the standing clock-law test.
- Book structure facts (measured, descriptive): BoJ decision window median 1m
  volume 34 vs 53 full-day (**35.8% thinner**); tokyo_am 59 vs ny_am 120;
  tokyo_am carries 11.0% of session volume / 13.0% of range and prints **18.1%
  of session highs / 15.2% of lows** (`6J_a2_sessions.json`; JPY_AUD f1/f3).
- Volume definition law: 6J 1m summed volume = **0.455× (median) the GLBX
  cleared-volume statistic** (p10–p90 0.29–0.48, 2023-10+, n=752 days) —
  volume usable as **shares/ratios only, never absolute levels** (no liquidity
  claim in levels anywhere).

## §4 Calendar law (expiry cells, holiday grid, exclusions — fail-closed)

- **Expiry pointers: 62/68 cells of the 2010–2026 grid are OBTAINED** =
  52 official FxCAL 2010–2022 + 6 from the Q5 capture (2024Q3–2025Q4) + **4
  dual-vintage 2026 quarters added by CAL-JANQ** (FUTURES-SIX-ADOPT-PREP-20261004
  `cal_janq/CAL_JANQ_REPORT.md`): J1H26 2026-03-16, J1M26 2026-06-15,
  J1U26 2026-09-14, J1Z26 2026-12-14 — identical values in the re-verified Q5
  XLS (`pcal_69_6j_dl_20240904.xls`, sha `09a85ef7…`) and the new Nov-2025 XLS
  (`captures/pcal_69_6j_dl_20251104.xls`, Wayback 20251104084217, sha
  `f4ed4513…`). Residual **6 NOT_OBTAINED cells: 4 × 2023 quarters + 2 cells
  whose identity is not determinable from captures** (dispatch said 10
  missing; bounded scope was 8; the other 2 are flagged to the owner, NOT
  inferred). **Derivation (IMM-rule) FORBIDDEN.**
- **Holiday grid:** 6J 2023 measured holes = exactly **2 missing weekdays —
  2023-01-02 (New Year) and 2023-12-25 (Christmas)**, both exchange holidays
  (`fx_ja/session_holes_2023.json`, sha256 `58b4faa44d61f2b3f1d9b611c490e40a843ad56a6ec058c0b994458003b4bcaf`).
  FX holiday **session TIMES (early-close minutes) 2024–25 are NOT_OBTAINED**
  (0/42 product-code windows; `trading-hours-holiday-download` replays are
  HTTP 403 at the Wayback edge — BLOCKED_TRANSPORT, ≤2 attempts/URL honored;
  CAL_JANQ §4).
- **Early-close / holiday-shortened sessions: EXCLUDED fail-closed** by the
  deterministic bar-count/coverage rule of the family specs (JF3: Tokyo-window
  must carry ≥80% of nominal bars else EXCLUDE; the session-level rule drops
  any session the calendar cannot prove full-length). The exclusion list is
  generated by script at freeze and sha-pinned; never edited post-GO.
- 2026-10-01 partial tail (~2h) — full-session statistics end 2026-09-30.

## §5 Roll / chain law (measured k=5 + cease-guard; 2022-09-20 is the standing example)

- **Chain of record:** baseline k=5 trailing-5-session-volume-crossover chain,
  **27 rolls 2020–2026, 1,745 held sessions**
  (`FUTURES-DEEPRESEARCH-V2-20261003/analysis/6J_cache/held_volume_k5.parquet`,
  sha256 `1da2923a649591f312b8dd1a5e77bda7f3b341f9fb9e6d2bf9b6af39fbdabdba`;
  cross-checked to the derived chain in
  `FUTURES-K6GATE-PREP-20261004/fx_ja/rmm_mode_ledger.json` — 27/27 dates and
  pairs exact).
- **Cease-guard law (6J_DEEP_v2.md §8 / ERRATUM M-5; DC §1.3 "guard bắt buộc
  toàn FX"): PASS, re-proven element-by-element from raw**
  (`fx_ja/6j_cease_guard_2022.json`, sha256 `1d67f6b60bfece036efd107a879817527a99c4920f6684b4b9a4e83f5ea7b308`):
  2022-09-20 exchange OPEN (1,466 6J rows across 4 symbols); receiving **6JZ2
  traded 125,303 lots over 1,357 bars** while k=5 still held **ceased 6JU2**
  (stale trailing-5 mean 92,857.8 > Z2 ramp 88,234.0; U2 had zero bars that
  day); switch to Z2 on **2022-09-21**; U2's final session 2022-09-19 (97
  bars); the new contract year J1U27 began trading 2022-09-20 ("First Trade"
  row, hash-verified Q5 capture). The baseline held-MAP keeps a 09-20 row
  (held=U2) but the bar-level chain drops the session — the artifact sits
  INSIDE the September-2022 intervention week and is flagged, never a base
  stratum.
- **Mode ledger (RMM D-1, Role A): 6J = 19 abrupt / 8 gradual of 27**
  (`rmm_mode_ledger.json`, sha256 `f466ff845f4167fbf16aa19e7d0e4fd38815e7004f4c29e390246de5825d9c43`;
  trigger = `cease_guard_no_bars` → abrupt, `k5_crossover` → gradual;
  derivation verified against the committed chain 27/27).
- **Standing chain law for any scored 6J implementation:** (i) implement
  cease-guard — "if the held contract ceases trading (<25% bars or ≈0 volume
  of the session) while the rule has not switched, force-switch at that
  session's close"; (ii) timing disclosure "decided at close t, effective
  t+1" verbatim (DC §1.3); (iii) chain choice (baseline k=5 vs explicit
  cease-guard variant) **must not flip any sign** (RMM K6(a)); (iv)
  switch-day returns spread-adjusted (corr 0.999 phantom-drift law via DC
  §1.3); (v) the **ADOPT-D9 proposal** (explicit cease-guard as the standard
  chain-builder, 3-symbol evidence) is **law-pending — unratified**; until
  ratified, any builder must measure and disclose guard violations first
  (CYCLE_LAUNCH_DRAFT D9 fail-closed default). OI leads the raw volume
  crossover 1–3 calendar days (12/12 rolls, mode 2; OI 2023-10+ only) —
  annotated, never a rule.

## §6 Event law — BoJ and MOF (PIT-exact)

- **BoJ: dates are FACT; intraday stamps are NOT_IN_CORPUS.** 156 statement
  files 2011-01-25..2026-09-18 (30 dated decisions 2023–2026) + 17 mpmdeci
  index files; **54 MPM decision dates 2020–2026 measured**
  (`FUTURES-DEEPRESEARCH-V2-20261003/analysis/6J_a4_events.json`, sha256
  `8dab93186b5bc3792e3dc2ab6c7ce057ed2da0f262b00e77ce59b2afe83da0c1`;
  `fx_ja/ja_event_pit.json` sha256 `003c6821d9f791b6d2985b1c059baa4f5501191ffd7eb114dfa271d08b0e5d49`).
  **No minute-level release stamp exists in corpus — owner decision owns
  stamps. Therefore JF1 is WINDOW-CONVENTION-ONLY:** the 12:00–15:30 JST
  decision window is a declared convention (Tokyo-afternoon block where
  decisions land; range-share 13.43% vs 10.35% on record), never a
  minute-anchored release. The K3 anchor-robustness substitute has been
  delivered descriptively: **ANCHOR_INSENSITIVE_AT_45MIN** — W0's lead over
  its ±45-min neighbors is −9.78 pp on MPM-day range share (n=54; all 7
  variants reported; `jf1_k3_anchor.json`, sha256 `235e0472169b9a0aa8f274042fcec7b21aaa9538d6e9b1513735e31744e545dc`)
  — the Tokyo-afternoon concentration is a BLOCK property, not a property of
  the exact bounds. (Level reconciliation: this lane's W0 medians 34.66/28.57
  do NOT reproduce the a4-lane 13.43/10.35 convention levels — disclosed
  LEVEL_NON_IDENTITY; the variant comparison is unaffected.) Titled
  regime-change subset n=4+2 (2024-03-19, 2024-07-31 +1.77%/2.68×, 2025-01-24,
  2025-12-19; v1-FACT 2026-06-16/09-18) — **any fold on it fails the ≥5/fold
  floor: descriptive view forever, 0 identities (pre-declared)**.
- **MOF: ex-post-only, lag law.** 386 daily ops 1991-05-13..2026-05-06
  (SOURCE_TIDY_RESOLVED regenerated 386-row tidy; the 81-row `.bak` is
  forbidden evidence — ERRATUM M-1). **Op amounts publish ~1 month (monthly) /
  quarterly (daily detail) after the fact — same-day intervention signals are
  FORBIDDEN; JF2 regime labels are built on the DISCLOSURE date, never the op
  date** (DC §1.4). The 2026-07-30 window (+2.36%, 607,579 contracts, burst
  13,366/min 13:36 UTC) is **NOT MOF-verified — price anatomy only, never
  merged into the 10-op set**. JF2 threshold constant
  ("distance-to-highest-USDJPY-acted-upon" zone) is **owner-gated**
  (PARAM-GAP, 6J_DEEP §7-H5).
- US-side DFF: 16 year-end vintages (2010–2024 + 2026-09-30; **no 2025
  vintage**) + latest snapshot. **Vintage law: `available_time =
  vintage(decision_date)`; current-calendar inference FORBIDDEN.** If any
  BLS-sourced conditioning ever enters, the BLSV 2025-vintage law applies.

## §7 Cost contract (MODELED COST; full detail in COST_CONTRACT_6J_6A.md)

- Fee tiers (FEES_CORRECTED, P0-VERIFY upheld; FX fee-group mapping PARTIAL):
  **T1 2.46 / T2 2.26 / T3 2.06 / T4 1.86 USD/side** — MODELED COST / UNDER
  REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN.
- Committed re-derivation (`6j_orientation_recheck.json:notional_and_cost_arithmetic`):
  spread close-proxy **$25.00/side** (4 ticks × $6.25, 20d median, HIGH-BIASED);
  slippage tiers {1,2,3} ticks × $6.25/side;
  **RT T1 / 1-tick = 2 × (2.46 + 25.00 + 6.25) = $67.42 = 8.4499 bp** of
  $79,787.50; **tier range 8.30–12.10 bp** (T4/slip1 8.2995 bp low; T1/slip3
  at the band-low price 12.1018 bp high; full T1–T4 × slip table committed).
- Labels: every cell MODELED COST / UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN.
  The words "measured cost" and "complete cost" are FORBIDDEN. **BBO NOT_RUN
  (D5 law)** — true spread, queue, fill probability NOT_RUN; conservative
  fill law binds (fill = next-bar open, no limit/queue claims, SL-priority on
  same-bar TP/SL). Session-of-day floor: Tokyo-window fills carry the
  thinner-book slippage assumption (+1 tick on entry-side, PROVISIONAL, JF1-7
  / JF3-8). Stress ladder ×1.0/×1.5/×2.0 on (spread + declared slippage), fee
  layer invariant (tabulated in COST_CONTRACT_6J_6A.md; ×1.5/×2.0 columns
  DERIVED arithmetic on committed inputs).

## §8 Folds (DRAFT — final boundaries fixed at registration freeze)

ES precedent 4-fold shape (`SPEC_PB1_ES` §7: folds multiply evaluation, never
identities; S1 = SEALED_UNTOUCHED) mapped to the 6J measured span
2020-01-02..2026-09-30, yearly sequential with a **252-session warmup
carve-out excluded from scoring at each fold head**:

| fold | window (DRAFT) | era note |
|---|---|---|
| F1 | 2020-01 .. 2021-12 | quiet regime (5.6% vol); 252-session warmup consumes much of F1 head — disclosed |
| F2 | 2022-01 .. 2023-12 | YCC shock (11.4%) incl. the 2022-09-20 cease-guard exemplar week (flagged stratum) |
| F3 | 2024-01 .. 2025-12 | intervention era; titled-MPM cluster |
| F4 | 2026-01 .. 2026-09 | partial year; ends at the measured corpus tail |

Era seams (2021 quiet / 2022 YCC / 2024–26 intervention) enter as **declared
K-views (era-sign stability), never as fold cuts or resplits** (CYCLE_LAUNCH_DRAFT
§4). RMM K5-style era concentration and JF1/JF3 rolling 2020–22 vs 2023–26
splits are mandatory views. Any calendar-unproven session is EXCLUDED before
folding (fail-closed, §4).

## §9 Baselines / controls — convention CONV-B

Per family: minimal = minimal-core (8 @ tier S2: 2 arms × 2 tails × 2 delays)
+ **3 scored controls inside the total** (C1-class clock-only shadow,
single-seed/single-delay per the PB1 C1 law — seed declared at freeze,
publication limit, no permutation-robustness claim; C2 always-on; C3
anchor/weekday-matched family-specific negative). Family-specific negatives:
JF1 C3 weekday-matched non-event clock + C3′ regime-change-vs-ordinary-MPM
split; JF2 C3′ disclosure-date label shuffle (block, ≥100 seeds only if the
owner rules the placebo budget) + C3″ pre-2022 null era (zero in-window ops
2020-01→2022-08 — any "effect" there is a construction bug); JF3 C3
weekday-matched with MPM/op days removed + C3″ DST-mismatch falsifier.
Controls are inside the quoted totals (IDENTITY_TABLES §7.3 convention);
≥100-seed expansions are owner rulings, never silent additions.

## §10 Verdict criteria + power honesty

- Family kill law (K2, ES precedent): if BOTH signed arms sit below the
  after-cost floor at realistic n, the family is dead — re-parameterization
  forbidden; a null is the pre-registered death, **never evidence of absence**.
- **Power honesty (committed):** JF1 at n=54 MPM days — per-event MDE ≈
  2×(σ_day/√54) ≈ **13–19 bp**, at/above the modeled RT cost band (8.5–14.7
  bp): **K2 is a live, stated risk** (JPY_AUD f1-7). RMM 6J leg (if ever
  legalized under J-C): MDE ≈ 12.5 bp-class at n≈108 events vs modeled RT
  ≈8.5–14.7 bp — **power-marginal by construction** (HYPOTHESES_R2 §2 field 7
  K2 clause, transfers verbatim). JF3 at n≈1,600 non-excluded sessions needs
  a window-move scale well above ~10 bp — plausible only on tail triggers
  (stated plainly). MPM-day median |return| 0.568% = 57 bp vs RT 8.5–14.7 bp:
  the family is not automatically cost-dead — the honesty is about MDE, not
  cost alone.
- Gates (G-series, ES precedent G1–G9 shape) are drafted per identity in the
  future cycle's registration freeze; the sequence is registration → prelaunch
  A7 → exact-arm dry-run → typed owner GO → scored run under heavy lock →
  reproduction twin → terminal A7 (CYCLE_LAUNCH_DRAFT §6).
- **This document computes nothing and authorizes nothing.** Verdict criteria
  bind only after: owner ceiling (P5-D1), BBO/fill ruling (P5-D3), cost A7
  posture (P5-D4; D2), and a typed GO at a future cycle's own gate.

— End SPEC_6J draft. 0 PnL, 0 scored runs, 0 network, write surface confined
to `research/control/FUTURES-5SYM-PRESCORED-20261005/fx_ja/**`.
