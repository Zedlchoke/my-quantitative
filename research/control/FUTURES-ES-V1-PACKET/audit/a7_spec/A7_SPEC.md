# A7-SPEC — Independent fresh-context audit of FUTURES-ES-V1-PACKET (SPEC_PB1_ES r2 + PLAN_futures_es_v1)

- Lane: **A7-SPEC** (independent auditor; audit-only — no repairs, no PASS-hunting,
  no parameter suggestions beyond errata text needed to close ambiguity).
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep`,
  branch `prep/futures-behavior-10syms-20261002`,
  HEAD `cce2cfa01042ac3f683493761da80377bb2e152a` (measured = dispatch_sha; unchanged).
  Packet files are UNCOMMITTED working-tree files — audited as-found.
  SPEC_PB1_ES.md sha256 `69899341aa0a0bafc3e0bb0ead4eaebb7449b4b15dbd1dcb57a0a9c73a5f3787`;
  PLAN_futures_es_v1.md sha256 `06140882f13d96fd1325c472ef3788da7d4ce1c6b571c7c27d75b8e8e0c7a06b`;
  root `plans/CYCLE_REGISTRY.json` (read-only) sha256
  `b292229770b748442f58911da6e7ac8e79a3ef8d9c5b96503bce398efb6a9027`.
- References read in full: DATACONTRACT_QUALIFICATION.md, PLAYBOOKS_DRAFT.md (r5),
  SUMMARY_QUAL_ACTIONS.md, OWNER_DECISION_PACKET.md,
  `analysis/d2_feesrc/{ES_FEE_SOURCES.md, fees_table_es.json}`,
  `analysis/d3_cmecalendar/{ES_CALENDAR_EVIDENCE.md, cmecal_coverage.json}`,
  `analysis/d5_esschema/es_schema_eval.md`, ES dossier v2 (`ES_DEEP_v2.md`),
  NQ dossier v2 §8-H4 (q80 provenance), root registry (GO-phrase/cycle-id only).
- Probes (deterministic, re-runnable, this directory):
  `probes/probe_r1_identity_grid.py`, `probes/probe_r2_cost_arithmetic.py`,
  `probes/probe_r4_r5_expiry_rule_and_holidays.py`, `probes/probe_standard_audit.py`
  → outputs `probes/out_*.json`; machine digest `a7_spec_checks.json`.
  All four verdicts: PASS.

---

## 1. Mandatory adjudications R1–R5

### R1 — Identity table (SPEC §6) — **PASS**

Recomputed by enumeration (`out_probe_r1_identity_grid.json`):

- **P-A** `{CONT,REV}×{UP,DN}×{D0,D30}×S2` = **8**; **P-B**
  `{CONT,REV}×{UP,DN}×D0×{S1,S3}` = **8**; **primary = 16**.
- FOMC sensitivity `{CONT,REV}×{UP,DN}×D0×S2×FOMCIN` = **4**; C1 placebo
  (`FBES1-PLA-D0-S2`, seed 20261002, single-seed/single-delay limitation declared) +
  C2 `FBES1-ALW-D0-S2` + C3 `FBES1-FLAT` + C4 `FBES1-DOSE-D0-S2` = **4**.
  **Total = 24**, exactly the Co-Owner A-r4 scope ratified in PLAYBOOKS_DRAFT r5
  ("8+8+4+1+1+1+1 = 24 đúng trần") and PLAN §2. No duplicates; budget ≤24 respected.
- **No implicit 24-grid remains**: SPEC states in-band "KHÔNG phải full grid
  2×2×2×3=24"; probe confirms the full grid would be 24 cells of which the 8
  `D30×{S1,S3}` cells are absent, and SPEC declares exactly those (and any other
  combination outside the two families) **non-existent** ("không tồn tại… mở rộng =
  owner amendment + re-check trần"). Gates reference only existing families
  (G1 S2/S1; G5 D0/D30 within P-A).

### R2 — Cost arithmetic (SPEC §5) — **PASS**

Recomputed from D2 source values (`out_probe_r2_cost_arithmetic.json`; binding
verified inside `fees_table_es.json`):

- 0.85 (C5 Fixed, S1 LIVE_OFFICIAL 2026-10-03 — the **max** of all published
  plan/tier rows 0.85/0.65/0.45/0.25, i.e. conservative) + 1.386 (X1, S2 IBKR
  CME.php offset table) + 0.02 (X2n NFA official timeline, S5 CFTC filing) +
  6.25 (half-turn of the D5-reproduced 1.0-tick median full spread $12.50) +
  {12.50, 25.00, 37.50} (D1 declared 1/2/3-tick assumption) =
  **S1 21.006 / S2 33.506 / S3 46.006 per side** — matches SPEC exactly; window
  2014-10-01..2017-12-31 (inclusive) −0.01 (NFA 0.01 per X2n verbatim timeline
  "From October 1, 2014 to December 31, 2017 … $.01") → 20.996/33.496/45.996.
- **IBKR regulatory offset 0.011 (X2) is NOT added anywhere** — the only mention
  of 0.011 in SPEC is the explicit "KHÔNG dùng, KHÔNG cộng kèm" single-source
  note; probe confirms the value 0.011 is not a term of any additive combination
  the SPEC table can produce (no double count; 0.02 > 0.011 so the chosen NFA
  source is also the conservative one).
- NFA timeline confirmed in D2 JSON: 0.02 → 0.01 (2014-10-01) → 0.02
  (2018-01-01, open-ended, last official doc fetched). See NOTE-1.

### R3 — No bias-direction for current-as-approximation historical fees — **PASS**

- D2 artifacts support the SPEC's stance: CME official PDFs (eff. 2020-10-01 /
  2025-02-01 / 2026-02-01) fetched but **per-cell values not extractable**
  (column scrambling — X1o value null, no inference); historical IBKR snapshots
  exist for 2022/2023/2025 but **content never retrieved** (D2 §5 limitation 5);
  the only official per-year series is the NFA timeline. I.e., no per-year fee
  values are extractable ⇒ current-as-approximation is the only legal
  construction and **no direction is provable**.
- SPEC r2 §5 note and PLAN §3 carry **no residual direction claim** (probe: zero
  residual hits after excluding the permitted conservative-row-choice
  justification "hàng bảo thủ nhất bảng public" — which is a statement about
  which public row is picked, not a historical-direction claim — and the
  spread-proxy "thiên cao" caveat, which concerns spread, not fees). D2's
  "KNOWN-WRONG in ≥2 documented ways" (NFA — handled by the timeline; unfetched
  search leads about CME increases) documents wrongness, not a per-year
  direction — refusing to convert that into a direction claim is correct
  evidence-first behavior. (Disclosure nicety: NOTE-3.)

### R4 — Roll lookahead / expiry rule (SPEC §1) — **PASS (PIT-LEGAL), one MINOR pin**

Ruling (one line): **PIT-LEGAL — the decision law is the deterministic public
rule (3rd Friday of delivery month + CME-observed holiday displacement:
2026-06-18, 2027-06-17), computable ex ante from public calendars/statutes; D3
authority and bars are used only as ex-post validation, so authority-less
quarters (2019-2023, 2026, and partials Sep/Dec-2010, Mar/Jun/Sep-2011,
Mar/Jun-2024) are ALLOWED-with-validation — bars validation covers 66/66
in-window expiries (dossier §1) — and any mismatch ⇒ EXCLUDE-ENTIRE-QUARTER
(fail-closed), which is the correct treatment; NOT excluded by default.**

Reasoning and evidence:

- The SPEC explicitly forbids "last session with volume" as the *law* (future
  information at decision time) and demotes bars to *validation* — using the
  future to verify (not to decide) injects no lookahead into any decision; roll
  dates are fixed by the public rule alone.
- Probe implements the rule and reconciles it against **all 37** rows of the D3
  ARCHIVED_OFFICIAL expiration master table: **37/37 agree, 0 mismatch**
  (transcription cross-checked against the evidence file). Within the evaluation
  window (2010-06..2026-09) the D3 table carries 36 of the 66 in-window
  quarters; bars (dossier ES §1) carry all 66 — including the single in-data
  exception ESM6 → 2026-06-18 (Juneteenth), with ESM7 2027-06-17 from vendor
  definitions. Both are encoded in the rule.
- **MINOR-2 (pin needed)**: the generic clause "dịch chuyển theo lịch nghỉ liên
  bang Mỹ quan-sát-được" (shift by observed US federal holidays) is NOT the
  operative rule and would mispredict **June 2021**: Juneteenth became a federal
  holiday 2021-06-17 and Sat 2021-06-19 was observed Fri 2021-06-18 — exactly
  the 3rd Friday — yet CME did **not** displace (dossier: "2010–2025 June
  expiries were never displaced"; naive federal-shift reading predicts
  2021-06-17 vs actual 2021-06-18, probe-confirmed). If the engine implements
  the generic clause, validation (b) fails for Q2-2021 and the fail-closed rule
  needlessly EXCLUDES an entire clean quarter. Erratum text: replace the generic
  clause with "3rd Friday, displaced ONLY where CME actually displaced — measured
  precedents: Juneteenth 2026-06-18 (obs. Fri), 2027-06-17 (Jun-19 Sat → obs.
  Fri 06-18 → Thu 06-17); June 2021 NOT displaced despite federal observance;
  66/66 bars-validated."
- (NOTE-4) Wording: for authority-less quarters validation "(a)+(b)" is vacuous
  in (a); read as "(b), plus (a) where authority exists".

### R5 — Holiday / early-close coverage (SPEC §2-E1) — **PASS with adjudicated coverage map**

Ruling (one line): **The archived 2011-2025 tables carry CME-wide Globex
holiday WINDOWS plus ClearPort/floor tables — NOT per-day ES-specific Globex
early-close TIMES; per-day/per-time ES-provable evidence exists ONLY for 2010
(official 38-page Globex PDF, Equity section verbatim), and 2026 ES Globex
times sit behind a live widget (NOT_OBTAINED) — therefore every
holiday-suspect session-day 2011-2026 whose ES-specific status/time is unproven
must take E1 EXCLUDE (fail-closed; expected bite = the dossier-measured 3-10
early-close sessions/yr plus unproven window days), while 2010 (in-window H2)
is per-day ES-provable.**

Coverage map (from `ES_CALENDAR_EVIDENCE.md` + `cmecal_coverage.json`, probe-rebuilt):

| Year-range | What the archived evidence actually carries | Per-day ES-provable? | E1 consequence |
|---|---|---|---|
| 2010 (H2 in eval) | Full per-day/per-time Equity-family Globex detail (official PDF): closures Jan 1/Dec 24; early closes Good Friday 08:15 CT, Fri Nov 26 12:15 CT; Mon holidays = 10:30 CT halt + 17:00 resume; Columbus/Veterans normal | **YES** | Days provable; no E1 exclusion needed for status |
| 2011-2015 | Globex WINDOWS verbatim only (2014: Jul-3 settlement notice; 2015: Jul-2/Sep-4 notices; ClearPort 2015 = JS-tab caveat) | **NO** | E1 EXCLUDE every suspect day |
| 2016-2020 | WINDOWS + ClearPort + floor; floor rows carry product-group "EQUITIES 12:15 CT" on specific days (Jul 3 2017/18/19, Nov 25/24/23/29, Dec 24 2018-20) — floor ≠ Globex ES | **NO** (day-level half-day identification only, no ES Globex time) | E1 EXCLUDE every suspect day |
| 2021 | WINDOWS + ClearPort; floor table dropped product breakdown; D3's own note: "ES product-level Globex early-close times NOT_TRANSCRIBED" | **NO** | E1 EXCLUDE every suspect day |
| 2022-2025 | WINDOWS + ClearPort + floor (generic 12:00 CT, no product breakdown; 2024-2025 from capture 20241112201950) | **NO** | E1 EXCLUDE every suspect day |
| 2026 | LIVE page: WINDOWS + ClearPort/floor static; ES-specific Globex times behind widget — NOT_OBTAINED | **NO** | E1 EXCLUDE every suspect day (SPEC E1(i) already says this) |

Sanity check vs expected pattern (2010 PDF + floor/ClearPort rows + windows):
early-close days/year run ~2-5 (Good Friday partial, Black Friday, Dec-24
vicinity, Jul-3-adjacent in Tue/Thu years, occasionally Dec 31), plus
MLK/Presidents Mondays which are 10:30-halt days in the 2010 pattern but
"equity Globex NORMAL" per the 2026 live note and unproven per-year for
2011-2025 — consistent with the dossier's measured **3-10 early-close
sessions/yr** (ES_DEEP_v2 §7). The SPEC's E1 law ("mọi ngày không chứng minh
được ES-specific ⇒ EXCLUDE") is therefore correctly calibrated to the real
(thin) coverage; full-closure days self-exclude (no bars). Expected E1 bite is
small and deterministic (~0.2-1.5% of ~4,200 sessions for proven-closure tails,
more if the freeze script also excludes all window-Mondays — see NOTE-5).

**Also found (MINOR-1, reference artifact)**: the D3 headline count "36/68" is
off by one — the master table enumerates **37** ARCHIVED_OFFICIAL quarters (2012-2018
+ 2025 complete = 32; 2010 Mar+Jun, 2011 Dec, 2024 Sep+Dec = 5; 32+5 = 37), and
`cmecal_coverage.json`'s own `fully_covered_years`/`partial_years` fields also
recompute to 37. Coincidentally 36 is the count **within the evaluation window**
(ESH10 2010-03 falls before data start 2010-06). SPEC §1, DATACONTRACT §1.2 and
SUMMARY quote "36/68". Direction of error is conservative (understates
authority); no effect on the fail-closed logic. Erratum text: "37/68 quarters
ARCHIVED_OFFICIAL (36 within the 2010-06..2026-09 evaluation window)".

---

## 2. Standard audit

| Check | Result | Evidence |
|---|---|---|
| Outcome-blindness | **PASS** | SPEC header "Chưa có số PnL nào được tính"; no PnL/realized numbers anywhere in SPEC/PLAN; gates/kill-rules pre-registered (G1-G9, K1-K4); C1-C4 controls pre-listed; G7 explicitly allows "no conditioning information" outcome |
| Parameter provenance | **PASS** | q80 + trailing-252d strict-past + D30 mandatory variant + both-tails + CONT/REV co-registration all verbatim in NQ dossier §8-H4 refined pre-registered spec (anatomy, no PnL); ES §8-H5 the ES-side basis; R=2 marked "frozen a priori"; seed 20261002 (owner-published single-seed limitation); slippage {1,2,3} ticks = D1 declared assumption; commission 0.85 = max published tier (conservative) |
| Fold coverage | **PASS** | F1 2010-06..2012-12 → F2 2013-01..2017-12 → F3 2018-01..2021-12 → F4 2022-01..2026-09: contiguous month-tuples, no gap/overlap (probe); F1 start = data start 2010-06; F4 end 2026-09 correctly leaves the 2026-10-01 partial tail out (DATACONTRACT §1.6(5)) |
| GO phrase uniqueness | **PASS** | `GO FUTURES ES V1 SCORED EXECUTION`: 0 exact matches among 170 `go_phrase` fields, 0 raw-containment hits in the whole registry, near-misses share only the generic "GO … V1 SCORED EXECUTION" frame with 20 other cycles (distinct by their own tokens); no `FUTURES-ES*` cycle_id registered (85 cycles) |
| Two-key law | **PASS** | PLAN §6: key 1 = independent A7 prelaunch AUTHORIZED (0 HIGH/CRITICAL unresolved); key 2 = owner types the phrase verbatim, fresh, at the cycle's own gate; early GO = intent, dies unconsumed |
| S1 sealed | **PASS** | SPEC §7 "S1 = SEALED_UNTOUCHED (prospective post-freeze)"; PLAN §9 non-goals: no S1/paper/live/order |
| Registration runbook root-write blocker | **PASS** | PLAN §7 step 2 flags that `cycle register` writes `plans/CYCLE_REGISTRY.json` on ROOT main, outside this prep session's authority (owner runs it or delegates a root-authorized session, registry-only, pathspec); restated as Blocker 1 in §10. Consistent with observed state: packet untracked in prep worktree; registry untouched |
| MODELED COST language law | **PASS** | No "complete-cost"/"measured-cost" claims; the only "measured" occurrences are negations ("không phải BBO measured") and the ban itself; commission/exchange/slippage all labeled MODELED/assumption; spread labeled close-proxy; "Cấm ngôn ngữ measured/complete" in PLAN §3 |
| Contract binding | **PASS** | mult 50 / tick 0.25=$12.50, ts_event=interval-start, dash-filter mandatory, deferred-2027 floor ≥100k, era-correct closes 16:30→16:15→16:00 CT, IBKR closes = settlement marks (96/96, reference only, never fill) — all match DATACONTRACT §1 / D5 |
| C1 placebo limitation | **PASS** | single seed 20261002, single delay — declared as a published limitation, no permutation-robustness claim (consistent with PLAYBOOKS r5 full-design D1=52/D2=53 both BLOCKED_TRIAL_BUDGET) |

## 3. Findings ledger

Severity counts: **BLOCKER 0 · MAJOR 0 · MINOR 5 · NOTE 7**.

| id | severity | where | finding | erratum / action |
|---|---|---|---|---|
| M-1 | MINOR | SPEC §1 (+ D3 reference artifacts) | "36/68" understates the D3 authority table: 37 quarters enumerated (36 in eval window); D3's own JSON fields recompute to 37 | Re-label "37/68 ARCHIVED_OFFICIAL (36 within eval window 2010-06..2026-09)"; optionally file against D3 artifacts (read-only for this lane) |
| M-2 | MINOR | SPEC §1 roll rule | Generic "observed-US-federal-holiday shift" clause would mispredict June 2021 (federal observance Fri 2021-06-18 on the 3rd Friday; CME did NOT displace) → needless fail-closed EXCLUDE of Q2-2021 | Pin the operative displacement calendar: 3rd Friday, displaced ONLY where CME actually displaced (2026-06-18, 2027-06-17; June 2021 not displaced; 66/66 bars-validated) |
| M-3 | MINOR | SPEC §3 stand-aside | Base-EXCLUDE defined as "FOMC-days (92 timed)"; the 40 untimed FOMC statements 2011-2015 (dates public at day level) have no declared treatment in base or FOMCIN | Pin: all FOMC statement days base-EXCLUDED at day level (2011-2015 included); FOMCIN = INCLUDE set. Day-level exclusion is time-insensitive, hence safe |
| M-4 | MINOR | SPEC §3 stand-aside | "coverage RTH-core <60% EXCLUDE" — "RTH-core" minute range undefined per era | Define RTH-core (e.g. 08:30-15:00 CT bars present share, era-correct close) in the freeze spec before hashing |
| M-5 | MINOR | SPEC §4 SL | "ATR(20d median RTH range)" — name vs formula mismatch (Wilder ATR vs median of trailing-20 daily RTH ranges) and window/close-source not pinned | Pin: SL = 1.0 × median of trailing 20 RTH session ranges (strict past, era-correct close marks, excludes short/flagged sessions) — as written in PLAYBOOKS §1 |
| N-1 | NOTE | SPEC §5 | NFA 0.02 for 2018-01-01.. rests on the last official doc (2017 filing, open-ended); D2 records an unverified conflicting mirror ($0.01 as of 2026-07-01), NOT adopted — SPEC's 0.02 is the conservative (higher-cost) choice | Optional disclosure sentence; no change required |
| N-2 | NOTE | SPEC §5 | Exchange 1.386 is IBKR's published OFFSET rate (CME tariff per-cell not extractable; mirror 1.38 agrees) — SPEC attributes the source correctly | Keep the "offset table" attribution when freezing |
| N-3 | NOTE | SPEC §5 bias note | Could additionally carry D2's "current-schedule approximation is KNOWN-WRONG in ≥2 documented ways (NFA timeline — handled; unfetched leads re CME increases)" — without asserting direction | Optional completeness-of-disclosure sentence |
| N-4 | NOTE | SPEC §1 validation | "(a)+(b)" is vacuous in (a) for authority-less quarters | Re-word "(b), plus (a) where authority exists" |
| N-5 | NOTE | SPEC §2-E1 | The candidate-day enumeration rule (which days are "holiday-suspect": all days inside any authority Globex window + notice-named early-close days + adjacent eves) must be pinned in the freeze-time deterministic exclude script | Ensure the freeze script emits the explicit per-day list + reason (SPEC already requires sha256 of it) |
| N-6 | NOTE | SPEC §4 sizing | risk 0.5%/trade deferred "[freeze tại GO]" | Pin before GO (declared deferral — acceptable) |
| N-7 | NOTE | process | `audit/a7_spec/` contained artifacts of an interrupted earlier attempt of this lane (probes + draft report, no handoff delivered); overwritten in full by this audit within the allowed write zone | Transparency record only |

## 4. Completeness for registration (what prelaunch A7 will need)

Present and adequate: identity table (24, enumerated), folds, gates G1-G9 +
kills K1-K4, terminal outcomes, MODELED COST table with sources, signal spec
(strict-past), fill law (conservative), same-bar SL-priority, era-correct
session clock, E1-E5 exclude rule set, two-key GO, runbook with root-write
blocker.

Still to be produced after owner approval (all promised by SPEC/PLAN at
registration/freeze — none is a spec defect): (1) deterministic exclude-list
script + per-day output + sha256 (SPEC §2); (2) frozen identity-table file +
spec/IDs shas into the selection freeze (SPEC footer); (3) resolution of
M-2/M-3/M-4/M-5 pins into the frozen spec text before hashing; (4) sizing pin
(N-6) before GO; (5) A7 prelaunch (separate from this A7-SPEC) as two-key #1.

## 5. Verdict

The five Co-Owner review points are all correctly resolved in SPEC r2 (R1, R2,
R3 verified by recomputation; R4 ruled PIT-legal with fail-closed validation;
R5 coverage adjudicated and already encoded fail-closed in E1). No BLOCKER, no
MAJOR. Five MINOR pin/erratum items should be applied to the spec text before
it is hashed at freeze — none changes the design, the budget, or any gate.

**SPEC_VERDICT: FREEZE_READY_WITH_ERRATA**

- R4 ruling: **PIT-LEGAL; authority-less quarters ALLOWED-with-validation
  (bars 66/66 covers them; full-quarter EXCLUDE on any mismatch), not excluded
  by default — pin the Juneteenth displacement calendar (June 2021 NOT
  displaced) per M-2.**
- R5 ruling: **2011-2025 archived tables are CME-wide windows + ClearPort/floor
  only — per-day ES-specific early-close TIMES exist ONLY for 2010 (official
  PDF); 2026 ES times widget-blocked; hence every unproven ES holiday-suspect
  day 2011-2026 takes E1 EXCLUDE (fail-closed, ≈3-10 early-close sessions/yr
  measured), 2010-H2 per-day ES-provable.**

— End A7-SPEC. Audit-only; nothing outside `audit/a7_spec/**` +
`dispatch/handoff_A7-SPEC.json` written; no repairs made to audited objects.
