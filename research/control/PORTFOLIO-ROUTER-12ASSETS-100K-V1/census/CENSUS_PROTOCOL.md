# CENSUS_PROTOCOL — PORTFOLIO-ROUTER-12ASSETS-100K-V1 (FROZEN pre-dispatch, 2026-09-28)

**Status:** PRE-GO research artifact. No cycle registered. Owner prompt 2026-09-28
is the authority for this work; it is explicitly NOT a GO phrase for registration,
scored execution or S1.

**PnL-freeze attestation:** at freeze time, ZERO of the 1,200 ideas have any
computed PnL/PF/backtest number anywhere in the repo (brainstorm README declares
all HYPOTHESIS/NOT_RUN; no cycle consumed them). The rubric below is therefore
published strictly BEFORE any outcome can exist. Ranking = research priority
only, never measured profit expectation.

## 1. Corpus (verified)

- Source: `research/control/FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/symbols/{SYM}.md`
  for the 12 symbols EURUSD GBPUSD USDCAD USDJPY AUDUSD NZDUSD USDCHF XAUUSD
  XAGUSD BRENT WTI NATGAS.
- Verification (regex `^\s*-\s*\*\*S(\d+)\s*[—–-]` / `^\*\*S(\d+)\s*[—–-]`,
  2026-09-28): each file contains exactly S1–S100, no gaps, no duplicates.
  **Total = 1,200 rows.** Two macro maps (`macro/CURRENCIES_CORE.md`,
  `macro/CURRENCIES_BLOC.md`, ~60 coupling rules) and `UNIFIED_STRATEGY.md`
  are context inputs, NOT census rows.
- Every row is **HYPOTHESIS / NOT_RUN**. The per-file "Top-10" lists in Phần 3
  are the brainstorm lane's own priors — they are NOT winners and MUST NOT be
  described as such anywhere.

## 2. Output format (TSV, one file per symbol → merged by A1)

Path: `census/parts/census_<SYM>.tsv`. Canonical header, 21 columns, binding:

```
symbol	s_id	gid	family	title_short	mech_key	mechanism	payer_or_flow	horizon	signal_available_at	vehicle	required_pit_data	costs_to_measure	causal_control	ancestry_hits	data_status	verdict	verdict_reason	exemplar_ref	priority_score	source_ref
```

Column notes:
- `gid` = `<SYM>-S<NNN>` zero-padded to 3 (e.g. `EURUSD-S037`).
- `family` normalized to the canonical 10: `A-TREND B-MEANREV C-BREAKOUT
  D-CARRY_TERM E-SESSION F-EVENT G-XASSET H-POSITIONING I-STATARB J-REGIME_OPT`.
  Files numbering families 1–10 (BRENT/NATGAS/WTI/NZDUSD) map 1→A … 10→J.
- `mech_key`: lowercase snake_case mechanism key, ≤5 tokens, symbol-agnostic so
  the same mechanism across symbols gets the SAME key (e.g.
  `donchian_breakout`, `tsmom_3_12`, `rsi2_fade`, `carry_diff_filter`,
  `cot_zscore_fade`, `session_open_breakout`, `eia_surprise_drift`,
  `snb_deposits_band`, `weekend_gap_cont`, `termstruct_carry`, `gsr_ratio`,
  `vol_target_trend`, `event_surprise_drift`, `fix_flow_tilt`). This is the
  dedup key for cross-symbol merge.
- `mechanism` ≤25 words; `payer_or_flow` names who pays / what forced flow or
  risk premium carries the money (or `UNCLEAR`).
- `horizon` ∈ {INTRADAY, DAILY, WEEKLY, MULTIWEEK, MULTIMONTH}.
- `signal_available_at`: the timestamp rule when the signal is decidable
  (e.g. `D1 close`, `EIA release Wed 10:30 ET`, `COT Fri 15:30 ET (Tue data)`,
  `H4 close`). If the idea gives no decidable timestamp → likely NOT_FALSIFIABLE.
- `vehicle` from the symbol's row in the DATA_COST_MATRIX (FX: `FX-spot`;
  metals/energy: pending L1, use `CFD-futures-TBC` etc.).
- `causal_control`: one falsifier design (clock-shadow / lagged twin /
  random-entry same dwell / shuffled-condition / index-points book).
- `ancestry_hits`: `;`-joined dead-family ids from the digest whose MECHANISM
  CLASS matches (skeleton/payer/information), else `none-found`.
- `data_status` ∈ {HAVE_REPO, PARTIAL_REPO, PUBLIC_UNEVIDENCED,
  PROSPECTIVE_ONLY, MISSING, NA} per the cheat sheet (§4).
- `verdict` per §3. `verdict_reason` ≤20 words.
- `exemplar_ref`: `self` if this row is its mech_key's best instance in-file,
  else the gid of the in-file exemplar (cross-symbol exemplars chosen by A1).
- `priority_score`: leave empty — A1 computes uniformly (§5).
- `source_ref`: `symbols/<SYM>.md:<startline>-<endline>`.
- Fields MUST NOT contain tabs or newlines; use `;` for lists.

## 3. Verdict definitions + frozen decision order

Apply in this order, first match wins:
1. `NOT_FALSIFIABLE` — no pre-decidable observable / refutable statement
   (narrative-only, discretionary, or meta-rules that cannot produce a book).
2. `VARIANT_OR_DUPLICATE` — same mechanism class (payer + information source +
   skeleton) as another idea in-file or a dead family, differing only in
   threshold / timeframe / pair / name / direction / session. Rename does not
   create a new mechanism (handbook §14.3, ERP1 P-27 F-0 court).
3. `BLOCKED_DATA` — required data has no evidenced obtainable source (repo
   miss + no evidenced public channel; e.g. news-intensity datasets, FX/commodity
   options chain history, CME intraday [transport-blocked]).
4. `PIT_UNPROVEN` — data plausibly public but the repo lacks evidenced
   event/publication/vintage timestamps (COT, EIA, GDT, SNB deposits, OIS,
   TIPS/DXY/VIX history…) → usable only after a PIT authority gate passes.
5. `BLOCKED_COST` — vehicle cost stack cannot be measured with authority
   (CFD terms, swap marks, roll calendars UNMEASURED) so any backtest would
   rest on favorable assumptions.
6. `DISTINCT_TESTABLE` — distinct mechanism + data evidenced/obtainable +
   costs measurable + falsifiable control definable.

Rule 2 before 3–5 is intentional (frozen): verdict classifies the IDEA first
(dup of a dead class is a dup even when its data is missing), the world second.
Blocked-only counts will be reported alongside dup-adjusted counts in the
summary so both views exist.

## 4. Data-status cheat sheet v1 (from repo evidence 2026-09-28; L1 supersedes)

- FX spot history: EURUSD/GBPUSD/USDJPY panels exist via RANGEFADE/ERP lineage
  (H1-class grids); AUDUSD/USDCAD were acquired fresh for ERP track-a →
  `PARTIAL_REPO`. USDCHF/NZDUSD → `PUBLIC_UNEVIDENCED` until L1 measures.
- XAUUSD: shadow cycle + IBKR probe exist → `PARTIAL_REPO` (spot quotes);
  XAGUSD → `PUBLIC_UNEVIDENCED`.
- BRENT/WTI/NATGAS futures/CFD history: no repo inventory →
  `PUBLIC_UNEVIDENCED`; CME intraday is transport-blocked (sixsource #5/6a).
- Macro/event series (COT, EIA WPSR/NG, GDT, SNB sight deposits, OIS/fed-funds
  futures history, TIPS, DXY, VIX/OVX, BTP-Bund, weather HDD/CDD):
  `PUBLIC_UNEVIDENCED` → verdict normally `PIT_UNPROVEN`.
- SOFR/EFFR daily: AVAILABLE_VALIDATED (NY Fed) — the one evidenced macro daily.
- News/headline-intensity, multi-source-confirm feeds: `MISSING` (repo has none;
  UNIFIED_STRATEGY admits manual-only) → `BLOCKED_DATA`.
- Options chains/risk-reversal/OVX history: `MISSING`/`PUBLIC_UNEVIDENCED` →
  `BLOCKED_DATA` or `PIT_UNPROVEN` accordingly.
- IBKR FX cost-band: PROSPECTIVE from 2026-09-28 only (never historical);
  commission/swap/rollover UNMEASURED (needs owner statement) — prospective
  cost data can price future execution, NEVER pretend to be history.
- Broker facts measured so far: FX majors two-sided spread p50 0.1–0.6 pip in
  ONE 02Z bucket (see `research/control/DATA-FOUNDATION-SIXSOURCE-V1/FINAL_REPORT.md`).

## 5. Priority rubric (frozen; A1 computes at merge, no agent judgment)

subscores 0–3 each: pit_feasibility (HAVE_REPO=3, PARTIAL_REPO=2,
PUBLIC_UNEVIDENCED=1, else 0) · mechanism (payer named + plausible = 3;
named but thin = 2; UNCLEAR = 1; none = 0) · falsifiability (control
definable + decidable timestamp = 3 …) · cost_determinability (measured
vehicle stack = 3; vehicle known cost UNMEASURED = 2; vehicle TBC = 1 …) ·
ancestry_distance (no hit = 3; adjacent class = 1; direct dead-class match =
0; VARIANT rows inherit 0).
`priority_score = round(10 * (3*P + 2.5*M + 2*F + 1.5*C + 1*A) / 32.5, 2)`.
Ties broken by (family, gid). Ranking is research-priority ONLY.

## 6. Merge & validation (A1)

Row-count == 1,200 (hard), header/enum checks, gid uniqueness, verdict counts
per class + per symbol + per family, cross-symbol mech_key groups (exemplar =
highest data_status then lowest gid), dup-adjusted blocked counts, links back
to source lines. Any repair re-dispatches only the affected symbol file.
