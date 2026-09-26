# FAILRES — lead overlay join (event-day × daily PnL × exit-type) — 2026-09-26

**Labels: `DIAGNOSTIC_OUTCOME_EXPOSED` · `SINGLE_SOURCE_PANEL` ·
`FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK` · `PAPER_TIER` ·
`FAILURE_ROOT_CAUSE_RESEARCH` · `EVENTS_OVERLAY_ONLY — NOT_CAUSAL_EVIDENCE`.**

Computed by the Lead session (A1 role) as Phase-A synthesis from two lane
artifacts — `failres_daily_EURUSD.json` (failres-attrib, work commit
`da4a92c2`) and `failres_events_timeline.jsonl` (failres-events, work
commit `fb3cfbf1`) — by an inner-join on UTC date. No lane wrote this
file; the skeptic lane (Phase B) independently re-derives and adjudicates
it. Reproduction: the join script is recorded verbatim in
`failres_lead_overlay_provenance.json` (same computations, seed-free).
All numbers EURUSD R-DAEMON at k=1.0 unless stated.

## 1. Event-day vs no-event-day split (daemon daily net; folds = FOLD_TABLE)

| Fold | ALL | SCHED_MACRO days | SURPRISE (energy/geo) days | NO-EVENT days |
|---|---:|---:|---:|---:|
| F1 | −188.8 (n=215) | −1.4 (22) | +10.2 (1) | **−190.1 (191)** |
| F2 | −884.4 (218) | −136.9 (27) | **+43.6 (8)** | **−756.2 (185)** |
| F5 | −191.5 (216) | −25.1 (21) | +21.9 (2) | −162.9 (191) |
| F3 (+) | +1,049.8 (217) | +143.5 (17) | −47.0 (3) | +975.5 (196) |
| F6 (+) | +257.0 (217) | +92.5 (13) | −189.4 (3) | +353.9 (201) |
| F4 (+) | +348.3 (216) | n/a — F4 not covered by the timeline (disclosed limitation) | | |

Reading (facts only): in EVERY losing fold the no-event days carry
≥85% of the loss (F1 100.7%, F2 85.5%, F5 85.0%); surprise
energy/geopolitical days in F2 were net-POSITIVE for the daemon
(+43.6). The "energy shock / Fed decision days" context is NOT the
per-day proximate driver of F2; the ordinary-day persistent regime is.

## 2. Exit-type × event-day cells (net pips, RT)

| Fold | SCHED FF | SCHED TE | SURP FF | SURP TE | NON FF | NON TE |
|---|---:|---:|---:|---:|---:|---:|
| F1 | −45.4 (11) | +44.0 (3) | +23.1 (1) | −12.9 (1) | −887.3 (109) | +689.7 (39) |
| F2 | **−346.2 (19)** | +209.3 (6) | −26.1 (4) | 0 (0) | **−1,744.2 (105)** | +1,022.8 (32) |
| F5 | −195.8 (16) | +170.7 (5) | +21.9 (2) | 0 (0) | −681.0 (117) | +492.7 (19) |
| F3 | −49.9 (11) | +193.4 (4) | −47.0 (2) | 0 (0) | −511.6 (107) | +1,464.9 (40) |
| F6 | +74.8 (7) | +17.7 (1) | −189.4 (3) | 0 (0) | −345.7 (123) | +699.6 (23) |

FF = FORCE_FLAT (day-close cut), TE = TARGET_EXIT (reversion completed).
The FF<0 / TE>0 asymmetry holds inside the no-event cells — the tail is
not an event artifact. Scheduled-macro days carry the worst per-RT tail
in F2 (FF −18.2/RT) but are a small share of it (−346.2 of −2,116.5 FF).

## 3. Mode-at-entry per fold (RT, net)

| Fold | fade | follow |
|---|---:|---:|
| F1 | −177.0 (153) | −11.8 (11) |
| F2 | −476.5 (138) | **−407.9 (28)** (−14.6/RT — worst pool) |
| F5 | −106.7 (136) | −84.8 (23) |
| F3 (+) | +830.8 (148) | +219.0 (16) |
| F6 (+) | +161.6 (144) | +95.4 (13) |

## 4. TARGET_EXIT gross pool per fold (RT, gross, cost) — the working part

| F1 | F2 | F3 | F4 | F5 | F6 |
|---|---|---|---|---|---|
| 43, +745.6, −24.8 | 38, +1,258.5, −26.4 | 44, +1,692.0, −33.7 | 37, +1,036.8, −19.8 | 24, +676.7, −13.3 | 24, +736.8, −19.5 |

Positive gross in every fold including F2; the reversion engine works —
the day-close continuation tail (attribution C1) swamps it.

## 5. F2 worst-days detail (top-12 by daemon net)

10/12 worst days carry mode flips; several are near-mirror inversions of
R-ORIG on the SAME day (2022-07-05: daemon −109.0 vs R-ORIG +108.1 =
SHORT +108.1, ex-ante pct 0.0167 — minimum-range day, daemon faded the
opposite way); 2022-03-10 (ECB decision + US CPI same day) everyone lost
(daemon = orig −113.7) — a genuine continuation day. Worst days span
BOTH ex-ante-vol extremes (pct 0.98 / 0.88 / 0.95 and 0.017 / 0.083) —
no single ex-ante tercile isolates the tail.

## 6. What this overlay does NOT establish

No causal claim about events, war, or policy; no promotable reading
(outcome-exposed surfaces); no gate is proposed here. Phase-B hypothesis
adjudication belongs to the skeptic lane (`SKEPTIC_failres_REPORT.md`).
