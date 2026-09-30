# TERMINAL_DECISION — ETHUSDT-OPEN-SEARCH-V2 (A1/co-owner, 2026-10-01)

**Typed close: `ETHUSDT_OPEN_SEARCH_V2_NO_INCREMENTAL_VALUE`** — STOP-1
scored 8/8 cells; `all_pass_cells: []`; G3 wall fails 4/4 (best B2
403,801.90 vs ALWAYS_ON 1,653,470.33; margin −1,249,668.43); G10 fails 4/4
(all below TREND_LF 472,864.82); references reproduce V1 terminal
**28/28 cent-exact**; controls lawful; G8 repro twin ALL_MATCH; G9 A7
terminal **CONFIRM_WITH_CONDITIONS (0 CRITICAL / 0 HIGH / 1 MEDIUM / 1
LOW / 2 INFO)** — verdict recomputed and confirmed, zero status flips.

## Authorization of record

GO `GO ETHUSDT OPEN SEARCH V2 SCORED EXECUTION` transmitted 2026-09-30T21:20:00Z
by CO-OWNER DELEGATION (owner grant verbatim in
auth/GO_RECORDED_STOP1_COWNER.json; two-key complete: A7 prelaunch
AUTHORIZED_FOR_STOP1 + co-owner transmission; no double consumption — the
phrase stood REGISTERED_NOT_CONSUMED since 2026-09-25).

## A7 conditions — discharged here (recording-only; budget exhausted 8/8)

- **C-1 (M-1) registry structured-field staleness**: budget.used=0 and
  go_phrase_state=REGISTERED_NOT_CONSUMED contradict the phase prose at
  all four syncs — researchctl exposes no field setters for them
  (recurring V1 defect, same disposition as BTC-COMBO6/ILLIQ precedent):
  the authoritative accounting lives in phase text + state.json +
  events.jsonl (budget 8/8 consumed, GO CONSUMED 2026-09-30T21:20:00Z).
- **C-2/C-3 (recording)**: r1 remediation full-disclosure block and the
  G8 single-field root-cause stand as written in the scored report and
  G8_REPRO_TWIN.md; this decision incorporates them by reference.

## r1 remediation — adjudication of record

Lawful remediation-with-disclosure (A7 G9): pure crash-guard in
post-compute aggregation (`g.get('all_pass')`), engine digest unchanged
byte-exact, freeze diff = digest-supersede + additive r1 record (old
digest 974111c5… preserved), zero outcome exposure proven structurally
(KeyError at line 201 precedes the only write at 219) AND by the
heavy-lock FAILED-release stderr (pid 21026, 21:23:36Z, pre-fix traceback
verbatim). Deviation from V1's fresh-delta precedent disclosed; cured by
stronger retrospective evidence incl. G8 + this terminal audit.

## Plan §8 branch and the owner decision

Operative branch: **tranche V3 with new lawful tuples** (no lane veto).
V3 is NOT dispatchable without the owner: it requires owner data decisions
(new tuples beyond the thin remaining lawful set) and, per §34.5, any
G3-wall redesign is an owner decision. The owner faces, on return:
(1) accept this terminal and direct V3 with named new tuples; (2)
owner-redirection (asset/data/wall); (3) end the campaign. Nothing runs
until then (fail-closed).

## Boundaries at close

S1 SEALED_UNTOUCHED; no orders/paper/live; heavy lock FREE_PROVEN; GO
consumed-then-extinguished (P-8); budget 8/8 exhausted; zero post-verdict
cells. Denominators: +1 hypothesis ledger row; FAMILY_FAILURES +1 (class:
ETH breadth-gate overlay — dead by G3 ALWAYS_ON wall + G10 no-increment on
untouched folds).
