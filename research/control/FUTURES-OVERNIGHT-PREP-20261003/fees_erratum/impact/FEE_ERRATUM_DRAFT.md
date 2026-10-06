# FEE_ERRATUM_DRAFT — suspected fee-number defect (superscript/footnote glue)

- Round: FUTURES-OVERNIGHT-PREP-20261003, lane P0B-FEEIMPACT
- Status: **DRAFT / UNDER REVIEW — no value scenario is adopted by this document**
- Written: 2026-10-03 (prep worktree `prep/futures-behavior-10syms-20261002` @ a8cd06f2603a8df5a2db5999c63ab09c3a7134e7)
- Companion artifacts: `validate_fee_sources.py` (independent source-level validator, same dir), `GATE_REVIEW_NOTE.md` (same dir), P0A source re-reads → `../source/`
- Final values get locked by a later P0-VERIFY lane, not here.

## 1. Defect hypothesis (owner-reported; taxonomy = HYPOTHESIS, not established)

The owner reports that fee values transcribed by the parent rounds from IBKR
"fees charged to offset" pages (CME.php / NYMEX.php / COMEX.php) may carry a
**superscript/footnote-marker glue defect**: a rendered cell such as `1.38⁶`
(base value `1.38` + footnote marker `6`) or `0.01¹` may have been flattened
into the plain number `1.386` / `0.011`. Under this hypothesis the extra
terminal digit is not part of the value.

Supporting circumstance (in-repo, pre-existing, no new fetch): D2-FEESRC
already recorded the IBKR ES worked examples verbatim —

> `"1 ES Futures Contract = IBKR Execution Fee USD 0.85 + Exchange Fee USD
> 1.38 + Clearing Fee USD 0.00 + Regulatory Fee USD 0.01 = USD 2.24"`
> (`FUTURES-DATACONTRACT-QUAL-V1/analysis/d2_feesrc/fees_table_es.json:326`,
> label DOC_EXAMPLE_NOT_ACCOUNT_VERIFIED)

— i.e. the page's own printed components are **1.38 / 0.01 / total 2.24**,
while the offset-table-derived values used downstream are 1.386 / 0.011 /
2.247. A TradeStation mirror independently cross-references ES **$1.38**
(`ES_FEE_SOURCES.md` S6/X1m). The glue hypothesis, if confirmed, reconciles
all three.

Critical evidence gap: **A4-FEES saved no raw capture** of the offset pages
(only `fetch_log.jsonl` outcome lines + the derived table). The numbers
cannot be re-derived from committed evidence; P0A re-reads the live pages.

## 2. Both value scenarios carried side by side (value-agnostic map)

Per-side, per-contract USD, tier-1 (≤1k / Fixed; commission 0.85 both plans).
Scenario A = as-committed (A4/D2 values). Scenario B = owner-provisional
correction. **Neither is adopted here.**

| Code | Exchange A | Reg A | All-in T1 A | Exchange B | Reg B | All-in T1 B | ΔT1 |
|---|---|---|---|---|---|---|---|
| ES | 1.386 | 0.011 (used only as offset note; SPEC uses NFA 0.02) | 2.247 (D2 E3; offset-based) | 1.38 | 0.01 | 2.24 | −0.007 |
| NQ | 1.386 | 0.011 | 2.247 | 1.38 | 0.01 | 2.24 | −0.007 |
| 6E/6B/6J/6A | 1.60 | 0.011 | 2.461 | 1.60 | 0.01 | 2.46 | −0.001 |
| CL | 1.50 | 0.02 | 2.37 | 1.50 | 0.01 | 2.36 | −0.01 |
| NG | 1.60 | 0.02 | 2.47 | 1.60 | 0.01 | 2.46 | −0.01 |
| GC | 1.65 | 0.01 | 2.51 | 1.65 | 0.01 | 2.51 | 0 |
| SI | 1.65 | 0.01 | 2.51 | 1.65 | 0.01 | 2.51 | 0 |

Tier-2/3/4 values shift by the same per-component delta (commission ladder
unchanged): e.g. NQ 2.047/1.847/1.647 → 2.04/1.84/1.64; FX 2.261/2.061/1.861 →
2.26/2.06/1.86; CL 2.17/1.97/1.77 → 2.16/1.96/1.76; NG 2.27/2.07/1.87 →
2.26/2.06/1.86; GC/SI unchanged.

SPEC_PB1_ES §5 derived all-in (0.85 + exchange + NFA 0.02 + spread 6.25 +
slippage): A = **21.006 / 33.506 / 46.006**; B = **21.00 / 33.50 / 46.00**
(Δ −0.006/side; window 2014-10-01..2017-12-31 −0.01 likewise shifts only by
the exchange delta).

Open mechanism note (flagged for P0A/P0-VERIFY, NOT resolved here): scenario
B as given is not uniform — ES/NQ/FX change exchange-or-reg terminal digits
consistent with single-digit glue, while CL/NG imply regulatory 0.02→0.01
which a single-digit glue on `0.02` does not produce (glue only appends).
P0A's row-level re-read must adjudicate each cell individually.

## 3. Propagation map — site-by-site

Grep re-run (prep worktree root, exit 0):
`grep -rln -E "1\.386|2\.247|0\.011|2\.461|2\.37\b|2\.47\b" research/control/FUTURES-ES-V1-PACKET research/control/FUTURES-DATACONTRACT-QUAL-V1 research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003`
→ **26 files** (matches the Lead's chat list; the DISPATCH_MANIFEST.json
mission text says "27 files" — off by one vs this re-run; the 26 below is
the measured truth at this HEAD). Of the 26, **1 is a false positive**
(`coverage_remeasure.json`, sub-second timestamp `00:00:00.011588`) →
**25 genuine fee-value sites = 22 FROZEN-HISTORICAL + 3 LIVING-DOC**, plus
PLAYBOOKS_DRAFT.md as a supplementary rounded-value living site (§4 below).

Classification law for this round: FROZEN-HISTORICAL = committed evidence of
a past round (never edited, correct or not — the erratum lives beside them);
LIVING-DOC = a document future rounds will update (stale statements get
corrected by their owning lane in a future round, still not by this one).

### 3.1 FUTURES-ES-V1-PACKET (7 files — all FROZEN-HISTORICAL)

| File | Site lines (quote digest) | Scenario-B impact |
|---|---|---|
| `SPEC_PB1_ES.md` (r3, freeze-ready) | L100 `\| Exchange (CME) \| 1.386 \| public LIVE_OFFICIAL (IBKR CME.php offset table)...`; L101 `...IBKR offset 0.011 KHÔNG dùng, KHÔNG cộng kèm...`; L~106 `All-in/side S1 21.006 · S2 33.506 · S3 46.006` (derived, not grep-caught) | exchange row stale (1.386→1.38 under B); all-in row 21.006-family stale; NFA 0.02/0.01 timeline unchanged; the "0.011 KHÔNG dùng" note becomes "0.01 offset, not used" |
| `PLAN_futures_es_v1.md` | L35 `SPEC §5: commission Fixed 0.85 + exchange 1.386 (current-as-approx) + NFA theo timeline chính thức` | "exchange 1.386" stale under B |
| `audit/a7_spec/A7_SPEC.md` | L53 `+ 1.386 (X1, S2 IBKR`; L60-63 `IBKR regulatory offset 0.011 (X2) is NOT added anywhere`; L201 N-2 `Exchange 1.386 is IBKR's published OFFSET rate` | A7 audit statements reference the suspect cells; R2 arithmetic verdict (below) rests on them |
| `audit/a7_spec/a7_spec_checks.json` | L27 `"exchange_1.386": "X1 S2 offset"`; L47 `R2 PASS — 21.006/33.506/46.006 recomputed exact`; L59 N-2 note | R2 "recomputed exact" = arithmetic-vs-table only, **not source re-read** — this is exactly the parent round's blind spot |
| `audit/a7_spec/probes/probe_r2_cost_arithmetic.py` | L28 `x1 = comp["X1"]["value_usd"] # exchange 1.386`; L45 `COMM, EXCH, ... = 0.85, 1.386, 0.02, 0.01, 6.25` | probe asserts arithmetic vs fees_table_es.json values; under B its constants + expected outputs stale |
| `audit/a7_spec/probes/out_probe_r2_cost_arithmetic.json` | L5/8 source bindings; L32 `"exchange": 1.386`; L43-47 0.011 mention lines; L59 verbatim ctx quote incl. `exchange (cme) | 1.386` | output of the above probe — same staleness class |
| `dispatch/handoff_A7-SPEC.json` | L26 R2 detail: `0.85 (C5...) + 1.386 (X1) + 0.02 (X2n) ... = 21.006/33.506/46.006 exact; ... IBKR offset 0.011 (X2) appears only in the explicit not-used note` | recorded verdict language ("exact", "confirmed") inherits the suspect source values |

### 3.2 FUTURES-DATACONTRACT-QUAL-V1 (6 files: 3 FROZEN-HISTORICAL + 3 LIVING-DOC)

| File | Site lines | Class | Scenario-B impact |
|---|---|---|---|
| `analysis/d2_feesrc/ES_FEE_SOURCES.md` | L57 S2 row `ES 1.386 / 0.011`; L88 X1 `**1.386**`; L91 X2 `**0.011**`; L102 E3 `0.85 + 1.386 + 0.011 = 2.247`; L103 E4 tier ladder `2.247 / 2.047 / 1.847 / 1.647` | FROZEN-HISTORICAL | primary transcription site of the suspect values |
| `analysis/d2_feesrc/fees_table_es.json` | L57-58 row-verbatim claims `'ES ... 1.386 \| 0.011'`; L228/262 value_usd; L337-338 `= 2.247`; L348; L397 | FROZEN-HISTORICAL | machine-readable source of every downstream recompute |
| `dispatch/handoff_D2-FEESRC.json` | L24 summary (`exchange offset 1.386 + regulatory offset 0.011 ... computed ... 2.247`); L32 open item | FROZEN-HISTORICAL | as above |
| `DATACONTRACT_QUALIFICATION.md` | §1.7 L162 `\| Exchange fee \| **1.38+reg → all-in 2.24 (doc)** ...` — pre-r6 doc values, **valid under BOTH scenarios**; §3 L206-207 `(r6, D2: ... + exchange 1.386 + regulatory 0.011; all-in tính 2.247 @≤1k)` | LIVING-DOC | §3 r6 sentence stale under B (2.247→2.24, which then agrees with §1.7's doc row); §1.7 needs no value change |
| `SUMMARY_QUAL_ACTIONS.md` | L15 D2 row: `components exchange 1.386 + regulatory 0.011 ...; all-in tính từ components = **2.247** (tier ≤1k) — khớp ví dụ 2.24 của IBKR` | LIVING-DOC | stale under B; note "khớp ví dụ 2.24" (matches the 2.24 example) was already rounding-generous at Δ0.007 |
| `OWNER_DECISION_PACKET.md` | L17 D2 row: `+exchange 1.386 +regulatory 0.011; all-in tính 2.247 @≤1k; mọi dòng VERIFIED_VS_ACCOUNT=NOT_RUN` | LIVING-DOC | value phrases stale under B; the VERIFIED_VS_ACCOUNT=NOT_RUN and MODELED COST labels remain exactly correct (they never depended on the values) |
| `PLAYBOOKS_DRAFT.md` (supplementary — not in grep pattern) | L75 `commission $0.85/side + exchange — ES 2.24 all-in là biểu phí HIỆN TẠI (doc 2026-10-02)`; L185 `fee 2.24 all-in = biểu HIỆN TẠI`; L210 `2.24 doc là biểu hiện tại` | LIVING-DOC | carries only rounded doc values (2.24/0.85); under B the computed value CONVERGES to these — no stale number, but the "computed 2.247 vs doc 2.24" distinction cited elsewhere collapses |

### 3.3 FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003 (13 files: 12 FROZEN-HISTORICAL genuine + 1 false positive)

| File | Site lines | Scenario-B impact |
|---|---|---|
| `fees/FEES_BY_CODE.md` | L60-64 grid rows (NQ 1.386/0.011; FX 1.60/0.011); L72 reg rows `0.011 / 0.02 / 0.01`; L88-93 NQ math `0.85+1.386+0.011 = 2.247`, mirror note `same as it did for ES 1.38 vs 1.386`; L96-97 FX `= 2.461`; L103 CL `= 2.37`; L107 NG `= 2.47`; L121-127 summary grid; L139 offsets note | primary parent-round publication; stale under B per §2 deltas |
| `fees/fees_table_all.json` | L71-74 verbatim-row claims; L157 mirror cross-ref `$1.38`; L248/263/276-333 NQ component+all-in; L426/439-496 + L589/602-616 FX rows (2.461); analogous CL/NG/GC/SI blocks | machine-readable parent table; stale under B |
| `fees/fetch_log.jsonl` | L5 (CME.php SUCCESS_FULL_RENDER detail quoting `NQ 1.386; ES 1.386 ... Regulatory ... 0.011`) | the log's own prose already embeds the flattened digits — evidence of the transcription act, not of the true cell |
| `fees/validate_fees_table.py` | L56-60 expected components (NQ 1.386 / 0.011 etc.); L69-71 expected all-in grid (2.247/2.461/2.37/2.47/2.51) | validator of round VI hard-codes scenario-A values — the validator that "passed" is itself value-locked to the hypothesis under review |
| `REPORT_VI.md` | L39-40 `NQ all-in 2.247/2.047/1.847/1.647 (= 0.85+1.386+0.011)`; L40 FX `2.461`; L42 `CL 2.37…; NG 2.47…; GC/SI 2.51…`; L60 `all-in tier-1 2.247 từ A4 (cost gate còn lớp account + slippage...)` | round-VI published verdicts; NQ-cost-gate input number stale under B |
| `verify/CROSSCHECK_REPORT.md` | L21 `45/45 ALL_IN rows = commission+exchange+regulatory exact (NQ 2.247=0.85+1.386+0.011; ...)`; L77 `(all-in 2.247 tier-1)` | "VERIFIED" here = internal arithmetic consistency of A4's table against itself — **not source-text location**; this is the exact blind spot the new validator closes |
| `verify/recompute_A4_fees.py` | L35 expect dict (`("NQ","<=1,000/mo"):2.247 ... 2.461 ... 2.37 ... 2.47 ... 2.51`) | recompute script re-derives from the same suspect components |
| `verify/verify_findings.json` | L88 A4 verdict `45/45 ... NQ 2.247=0.85+1.386+0.011`; L97 `NQ all-in 2.247 tier-1` | same |
| `dispatch/handoff_A4-FEES.json` | L29 spot-check detail `27 component spot-checks match verbatim page values (NQ 1.386/0.011; FX 1.60/0.011; CL 1.50/0.02; NG 1.60/0.02; GC/SI 1.65/0.01 ...)`; L44/51/52 grids; L83 summary | "match verbatim page values" claim is precisely what P0A re-tests; no raw capture was saved to back it |
| `dispatch/handoff_VERIFY.json` | L98 recommended_next_action `NQ cost gate adjudication using A4 (all-in 2.247 tier-1)` | recommended action's number stale under B; action itself still valid with corrected value |
| `deep/es_nq/ES_DEEPFOUR_V3_ADDENDUM.md` | L200 `exchange CME **1.386**`; L204 `IBKR 0.011 NOT added`; L208 `$2.247 all-in doc example carries...` | deep-four addendum cost recap stale under B |
| `deep/es_nq/evidence_index.json` | L110 `D2 fee components (0.85/1.386/NFA timeline, all-in 2.247 ...)`; L169 `used_for: ES exchange 1.386/side` | evidence index pointer values stale under B |
| `events_bbo_coverage/coverage_remeasure.json` | L1784 `"ts_event_min_utc": "2025-04-01T00:00:00.011588+00:00"` | **FALSE POSITIVE** — timestamp sub-second field, not a fee value; no impact |

### 3.4 What does NOT change under the correction scenario

- **Commission structure**: IBKR 0.85 Fixed; Tiered 0.85/0.65/0.45/0.25 — no
  hypothesis path touches these (owner scenario changes only exchange/
  regulatory offset cells).
- **Tier ladder shape** (4 tiers + Fixed) and the MODELED_COST framing.
- **NFA official timeline** 0.02 → 0.01 (2014-10-01) → 0.02 (2018-01-01):
  an independent official source (S5 filing), not the offset pages.
- **Labels**: every row's SOURCE=PUBLIC_REFERENCE and
  **VERIFIED_VS_ACCOUNT=NOT_RUN remain true under both scenarios** — account
  verification was never run and remains the binding gap (r6b: owner account
  artifacts had no futures lines).
- Spread proxy 6.25, slippage {12.50, 25.00, 37.50} assumptions, NQ re-measure
  +38.43%, all data-plane/calendar/BBO findings — untouched.
- Magnitude note: max delta is $0.01/side (CL/NG) — immaterial to any pass/
  fail threshold seen so far, but correctness of published numbers is the
  issue, not threshold flips.

## 4. LAW (append-only round)

1. **No committed file is edited by this round.** All 25 genuine sites above
   stay byte-identical at HEAD a8cd06f2. This erratum and its siblings are
   the only writable surface (round dir only).
2. **SPEC_PB1_ES r3 freeze-ready status and every cost gate/verdict derived
   from 2.247 (or 21.006-family) are recorded as UNDER REVIEW** until a new
   A7 re-audits cost arithmetic against corrected, capture-backed sources.
   Missing evidence is NOT_RUN; suspected-wrong evidence is not silently
   "kept" nor silently "fixed".
3. Stale-under-B SPEC/PLAN/A7 statements are listed (§3.1 quotes) — NOT
   edited. Their owning lanes correct them in a future committed round after
   P0-VERIFY locks values.
4. The A7/CROSSCHECK "exact/VERIFIED" language is re-read as
   *arithmetic-consistent-with-transcribed-values* — it never asserted
   source-text verification. No past verdict is rewritten; the erratum
   records the distinction.

## 5. Validation path

`validate_fee_sources.py` (this dir) checks claimed values **against capture
source text** — literal numeric token with clean boundaries = located; base
number immediately followed by a superscript/bracket/caret marker of exactly
the dropped digit = located-but-FOOTNOTE_GLUED (FAIL, needs human
adjudication); anything else = NOT_LOCATED (FAIL). Internal arithmetic
consistency is never a pass condition. Self-test mode embeds a synthetic
capture and asserts all three outcomes. Real captures come from P0A.
