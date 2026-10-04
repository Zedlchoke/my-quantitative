# COST_AUTHORITY_TABLE — SLEEVE-FX5-100K-V1 (Lane PC, pre-GO)

Companion to `PIT_COST_FREEZE_DRAFT.md` (same session, same laws). This is
the component × pair cost-authority matrix for the 5-pair sleeve. **Verdict
law: MEASURED beats stated; a load-bearing component with no measurement is
DECLARED_PESSIMISTIC and caps every downstream survivor at PROVISIONAL;
nothing optimistic may be inferred.** Owner directive 2026-09-29 (verbatim):
the IBKR London-fix measurement is ONE DAY on a paper venue — NOT edge
evidence and NOT sufficient cost authority.

Status legend:

- **MEASURED** — cited file/statistic exists; every number names its source.
- **DECLARED_PESSIMISTIC** — COST_ACCOUNTING_SPEC §4 register band; honest
  pessimism, no file evidence; listed with its register id.
- **BLOCKED** — no authority at all; using it is forbidden.
- **n/a** — structurally absent (spot OTC).

## 1. Component × pair matrix

### C1 — Spread at the sleeve's fill hours (entry/exit, next-bar-open side quotes)

Per pair, Friday 20:00 UTC decision → fill at next bar open (PIT freeze R3);
statistic = spread (ask−bid) at the fill instant, pips, p50/p90, sleeve
window 2021-01-08→2026-06-26; M1 pairs from the staged .bi5 bid/ask corpora
(measured this lane 2026-09-29; panels + digests in `data_manifest_fx.json`),
H1 pairs from ANC `s_open` of the Friday 20:00-open bar.

| pair | status | p50 / p90 | n | source |
|---|---|---|---|---|
| EURUSD | **MEASURED** (panel venue) | 0.3 / 0.5 | 286/286 Fridays | fx-rangefade M1 .bi5, spread_open of [20:00,20:01) bar |
| GBPUSD | **MEASURED** (panel venue) | 0.8 / 1.3 | 286/286 | fx-majors-search M1 .bi5, same |
| USDJPY | **MEASURED** (panel venue) | 0.5 / 0.9 | 286/286 | fx-majors-search M1 .bi5, same |
| USDCAD | **MEASURED** (panel venue) | 1.2 / 1.6 | 247/286 | bars1h_ANC_USDCAD.parquet `s_open` |
| AUDUSD | **MEASURED** (panel venue) | 1.0 / 1.3 | 199/286 | bars1h_ANC_AUDUSD.parquet `s_open` |

Caveats (load-bearing, per pair): (i) **H1 deferral** — on the 39 (USDCAD) /
87 (AUDUSD) Fridays without a 20:00-open bar the fill defers to Sunday reopen
and is charged at C3's measured reopen spread, not this cell; (ii) **venue** —
these are Dukascopy-feed spreads; the only IBKR readings are the n=1-day
paper windows (§3 of the freeze draft); the panel↔IBKR transfer is
UNMEASURED and must be labeled in every trial's `cost_tier`. Full per-hour
p50/p90 schedule (all 24 UTC hours × 5 pairs) measured — Appendix A of the
freeze draft; it supersedes COST_ACCOUNTING_SPEC U1's "double the one
measured 02Z bucket" rule **for the panel venue only**.

### C2 — Rollover-window spread (21:00–22:00 UTC roll window)

| pair | status | statistic (pips) | source |
|---|---|---|---|
| EURUSD | **MEASURED** (panel venue) | Mon–Thu 0.6/2.7; Fri 0.5/1.1 (per-minute close) | M1 .bi5, minutes closing in (21:00,22:00] |
| GBPUSD | **MEASURED** (panel venue) | Mon–Thu 1.4/5.8; Fri 1.2/2.3 | same |
| USDJPY | **MEASURED** (panel venue) | Mon–Thu 1.0/4.9; Fri 0.8/1.8 | same |
| USDCAD | **MEASURED, structural absence** | bar present 431/30,043 weekday rows; s_open 1.2/2.3 when present | ANC parquet, 21:00-open bars |
| AUDUSD | **MEASURED, structural absence** | 320 rows; s_open 1.2/2.9 when present | same |

Pricing rule: fills inside the window use `S_roll = max(measured p90 of the
window cell, general-hour p90)`; H1 absence is surfaced, never smoothed.
22:00–23:00 UTC (the rest of the declared 21:00–23:00 event window) stays on
the DECLARED schedule — not measured as a distinct window here. Corroboration
(n=1 day, paper): IBKR rollover capture p50 1.7–5.6 pips across pairs — see
freeze draft §4.2; corroborating only.

### C3 — Sunday-reopen spread (deferral/weekend-reopen pricing; measured)

EURUSD 5.9/9.0 (n=284); GBPUSD 13.4/23.8 (n=283); USDJPY 11.0/22.0 (n=284);
USDCAD 5.0/9.7 (n=233); AUDUSD 2.8/6.3 (n=247) — p50/p90 pips at the first
tradable bar of the week, sleeve window. **MEASURED** (panel venue), same
sources as C1. Any sleeve entering at Sunday reopen is priced here; GBPUSD
and USDJPY reopen medians (13–14× their liquid-hour medians) make
reopen-entry families structurally fragile — this cell is why the freeze
recommends declaring reopen entries explicitly.

### C4 — Commission (per side)

| pair | status | band |
|---|---|---|
| all 5 | **DECLARED_PESSIMISTIC (U2)** | 0.35 bps of notional ≈ $3.5 per $100k lot per side |

No statement exists anywhere in the workspace (VERDICT_session2 V3 row 2
NOT_RUN; ERRATUM leaves it NOT_RUN; the n=1-day windows measure quotes only,
never fees). LOAD-BEARING for every net-PnL statement → all pairs capped at
PROVISIONAL until unblocked.

### C5 — Swap / financing for overnight holds

| pair | status | band |
|---|---|---|
| all 5 | **DECLARED_PESSIMISTIC (U4, U5)** | 1.0 pip/night charged AGAINST the position both directions; Wednesday ×3 (spot T+2 weekend-skip); accrual boundary 22:00 UTC; never income |

UNMEASURED (no Interest Accruals statement). **A sleeve whose PROFIT depends
on receiving swap is BLOCKED_COST** until an owner statement provides real
two-sided rates — pessimistic-symmetry law (COST_ACCOUNTING_SPEC §2.7); this
is a hard verdict, not a labeling choice.

### C6 — Slippage beyond spread + fill model

| pair | status | band |
|---|---|---|
| all 5 | **DECLARED_PESSIMISTIC (U3)** | 0.2 pip non-event / 1.0 pip inside event windows (rollover 21:00–23:00 UTC per UNIFIED §7) per side |

Fill MODEL itself is DECLARED by the PIT freeze (R3): next-bar-open at the
quoted side plus half-spread crossing (i.e., cost = full observed spread
charged per side at the quoted quotes + U3 beyond-spread band). No paper
fills, no statements, no L2 for these pairs exist → nothing measured.
LOAD-BEARING → PROVISIONAL cap.

### C7 — Exchange / venue fees

**n/a** — spot OTC FX (IDEALPRO CASH / Dukascopy spot); no exchange fees
exist structurally. If the future statement reveals pass-through venue fees,
they enter through the C4 unblock, not as a new component here.

### C8 — Margin

**DECLARED (U12 / AUDIT §5)** — FX majors 30:1 initial (3.33%), maintenance
= 50% of initial; whatIf is forbidden pre-GO (VERDICT #9) so this cannot be
measured now. Not score-affecting at sleeve sizes on a $100k book (a book at
the 250%/150% gross-cap proposal is far from a 30:1 margin fence); it gates
position blocking only, never PnL.

## 2. Per-pair verdict

| pair | C1 spread | C2 roll | C3 reopen | C4 comm | C5 swap | C6 slip | C7 | C8 margin | **verdict** |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD | MEASURED | MEASURED | MEASURED | DECLARED | DECLARED | DECLARED | n/a | DECLARED | **PROVISIONAL_PENDING_COST_AUTHORITY** |
| GBPUSD | MEASURED | MEASURED | MEASURED | DECLARED | DECLARED | DECLARED | n/a | DECLARED | **PROVISIONAL_PENDING_COST_AUTHORITY** |
| USDJPY | MEASURED | MEASURED | MEASURED | DECLARED | DECLARED | DECLARED | n/a | DECLARED | **PROVISIONAL_PENDING_COST_AUTHORITY** |
| USDCAD | MEASURED | MEASURED (absence) | MEASURED | DECLARED | DECLARED | DECLARED | n/a | DECLARED | **PROVISIONAL_PENDING_COST_AUTHORITY** |
| AUDUSD | MEASURED | MEASURED (absence) | MEASURED | DECLARED | DECLARED | DECLARED | n/a | DECLARED | **PROVISIONAL_PENDING_COST_AUTHORITY** |

- **Fully cost-runnable today (all load-bearing components measured): NO
  pair.** The measured spread family (C1–C3) is necessary but not sufficient:
  commission, slippage and swap are load-bearing for net PnL and are all on
  declared bands.
- **PROVISIONAL (cost-runnable under declared bands with the mandatory
  label): all 5 pairs.** Any survivor computed under this table carries
  `PROVISIONAL_PENDING_COST_AUTHORITY` and its NET result carries
  `NET_DEFAULT_COST` (COST_ACCOUNTING_SPEC §4 standing rule). **A survivor
  under DECLARED bands can never be called cost-PASS — only provisional.**
- **BLOCKED: swap-dependent sleeves** (C5 rule) — a family whose profit
  requires receiving financing is BLOCKED_COST on every pair until the owner
  statement. (No data BLOCKED rows: all 5 panels exist with measured spread
  authority; USDCAD/AUDUSD M1-feature families remain BLOCKED_DATA by the
  H1 ceiling — PIT freeze R6 — which is a data-plane verdict, not a cost
  one.)

## 3. What upgrades each DECLARED → MEASURED (owner evidence, exact paths)

| component | register | upgrade evidence | effect |
|---|---|---|---|
| Commission C4 | U2 | **IBKR Activity/Flex statement** containing FX trades (Trade+Commission rows) placed at `~/.my-quantitative-data/ibkr_statement/` (machine-local, never chat/git — VERDICT owner-documents list) | U2 → measured rate; bumps `defaults_digest` |
| Swap C5 | U4/U5 | Same statement's **Interest Accruals** rows with overnight FX positions + dated rollover rows (clock, Wed ×3 calendar) | two-sided rates replace pessimistic symmetry; swap-receiving sleeves un-BLOCK |
| Slippage C6 | U3 | (a) statement fills vs contemporaneous quotes (partial), or (b) post-GO paper fills (whatIf forbidden now) | beyond-spread band → distribution |
| Spread venue transfer (C1–C3 caveat) | U1 | SIXSOURCE bounded read-only sessions accumulating ≥200 valid two-sided obs per (pair, hour-bucket) — 2–3 sessions/week already scheduled (FINAL_REPORT pilot); the two 2026-09-28 windows are the first n=1 cells and do NOT yet qualify | per-bucket IBKR-venue p90 replaces panel-venue schedule for the execution-venue book |
| Min size (not tabled, affects R4-style blocking) | U6 | statement or broker contract spec | blocking threshold measured |
| Margin C8 | U12 | broker contract spec; whatIf only post-GO | initial/maintenance measured |

Standing rule inherited: any default replaced by a measurement bumps
`defaults_digest` (cost-kernel version change); trials run under different
digests are not comparable without re-running both. UNMEASURED never becomes
a favorable assumption.

## 4. One-line summary

Spreads (liquid hours, roll window, Sunday reopen) are **measured on all 5
pairs from 5.7 years of two-sided panels**; commission, slippage and swap are
**declared pessimistic and unmeasured workspace-wide**; therefore every
cost-runnable sleeve today is **PROVISIONAL_PENDING_COST_AUTHORITY**, no
survivor can be called cost-PASS, and swap-dependent sleeves are
**BLOCKED_COST** until the owner statement lands.
