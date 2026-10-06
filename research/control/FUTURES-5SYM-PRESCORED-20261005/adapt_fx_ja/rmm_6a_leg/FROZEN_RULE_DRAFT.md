# FROZEN_RULE_DRAFT — 6A RMM Role-B leg, M-COMPRESS (PROPOSED — never an approved freeze; CONTINGENCY-PB3-PARK)

> **CONTINGENCY-ONLY BANNER (binding).** 6A is PB3 PARK — 0 budget, 0
> identities. The RMM-6A leg is a contingency-only census line (**4 IDs, all
> zero until PB3 lift + D8 + D9 + DC §1.3** — slot **P5-FXJA-D5** + **P5-FXJA-D2**).
> 0 PnL, outcome-blind; real-data execution **NOT_RUN**; never activated.

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXJA**, 2026-10-05.
- Parents: `../../fx_ja/SPEC_6A_CONTINGENCY.md` §3 (measured chain + mandatory
  explicit guard) · `../../hypo/CENSUS_5SYM.md` RMM dossier + RMM-6A leg ·
  `../../fx_ja/6a_roll_measured.json` (sha `4172d288…`, 27 rolls 2020-03-17..
  2026-09-14) · frozen 26-ID table sha `1a96b8ea…` (RMM_6A_contingency = 4).
- Family bindings (6A-specific): mode split **MEASURED 21 abrupt / 6 gradual**
  on the explicit cease-guard variant; **baseline-code k=5 has 2 cease-guard
  violations — 2024-12-17 (held dead 6AZ4 while 6AH5 traded 55,675 lots) and
  2026-06-16 (held dead 6AM6 while 6AU6 traded 55,533)** — the exact 6J
  2022-09-20 pathology, twice ⇒ **the explicit cease-guard variant IS the
  mandatory chain-builder** (law-pending ADOPT-D9: measure and disclose
  violations first; `fc.measure_and_disclose_guard_violations`).

## 1. Observables (PIT)

Switch tables (injected/measured), mode labels (`cease_guard_no_bars` →
ABRUPT, `k5_crossover` → GRADUAL), "decided at close t, effective t+1"
verbatim; era label per switch date (measured 2020-11-20/23 boundary);
**era-1 switch sessions are descriptive-only (era tick caveat, $10.00/tick,
no-back-cast)**. K6(c): declared calendar-rule rolls land ~9–15d (median 11)
before the k=5 crossover dates — roll-rule choice is material to timing,
disclosed, never silently normalized.

## 2. Signal / entry / exit (law sketch — REFUSED while unsigned)

Identical machinery to the RMM-6J leg draft: event clock = switch session t;
arms MCOMPRESS-REV/CONT both tails; delays D1/D30M; TP 2×SL, SL 1.0×ATR(20);
time exit switch+K (K=5 [PROVISIONAL]); event-stacking EXCLUDE vs central-bank
windows; extremal abrupt stratum (2022-09-20 + the two 6A dates) descriptive-
only, n=3 (pre-declared fold-floor failure).

## 3. Identity enumeration (CONTINGENCY-PB3-PARK shapes)

```
C6A0-CONT-RMM-MCOMPRESS-REV-D1    C6A0-CONT-RMM-MCOMPRESS-REV-D30M
C6A0-CONT-RMM-MCOMPRESS-CONT-D1   C6A0-CONT-RMM-MCOMPRESS-CONT-D30M
```

C1 block-shuffle placebo layer sits OUTSIDE the 4 (owner ruling if ever
budgeted). Era-1 rolls never trade (era tick caveat).

## 4. Owner-pending law — fail-closed refusal chain

| order | slot | law |
|---|---|---|
| 1 | `P5-FXJA-D5` | PB3 lift → D8 → D9 → D2 → calendar (`BLOCKED_PB3_PARK`) |
| 2 | `P5-FXJA-D2` | DC §1.3 boundary ruling (never self-ratified) |
| — | era-1 law | `RefusedEra1NoTradeIntent` on era-1 switch sessions |

Real-data adapter execution: **NOT_RUN**. CONTINGENCY machinery — never
activated.
