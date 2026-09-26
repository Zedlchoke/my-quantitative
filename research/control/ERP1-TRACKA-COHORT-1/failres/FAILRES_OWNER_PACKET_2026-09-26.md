# FAILRES OWNER PACKET — EURUSD R-DAEMON failure root-cause research (2026-09-26)

**Verdict: `NO_ELIGIBLE_PROPOSAL` — 0 scored cells, 0 holdout looks, 0
new windows consumed. Shadow FX-RANGEFADE-2M-SHADOW-V1 untouched (worker,
journal, dashboard, labels — nothing restarted, nothing edited). S1
`SEALED_UNTOUCHED`. This prompt was treated as diagnostic + hypothesis
authority ONLY — it is not GO-2, not S1 authority, and no GO phrase is
requested because no hypothesis survived Phase B.**

Owner instruction (2026-09-26, verbatim intent): nghiên cứu vì sao luật
EURUSD R-DAEMON đang shadow thua ở F1/F2/F5 (nhất là F2 11/2021–08/2022),
đề xuất tối đa 3 hypothesis kinh tế mới — mục tiêu KHÔNG phải cứu
identity RANGEFADE đã thất bại.

---

## 1. Answer to "why did F1/F2/F5 lose" (Phase A, reproduced ALL_MATCH)

Everything below is `DIAGNOSTIC_OUTCOME_EXPOSED` on the RANGEEXP family's
own development surfaces (umbrella §5.8/§6 ancestry law) — an explanation
of a dead law's behavior, never candidate evidence. All numbers k=1.0,
EURUSD R-DAEMON unless stated; A7 reproduced every headline from M1 bytes
with independent code (plane rebuild max-abs-diff 0.0; fold nets delta
0.0; 48 identity checks green).

**The single most consistent fact (12/12 pair-fold cells):** trades that
exited by FORCE_FLAT at the 20:00 UTC day-close lost in every fold
(full panel −5,466 pips / 839 RT) while trades that reached the
mid-quarter TARGET_EXIT were positive in every fold (+6,278 / 223 RT).
The reversion engine works **including in F2** (TARGET_EXIT gross
+1,258.5 on 38 RT, cost only −26.4). What kills the law is the
continuation tail: band-breaks that keep running until the day-close
force-flat.

**F2 (−884.4) decomposition:**
- Gross −769.1 vs cost −115.3 (13%) — **GROSS_NEGATIVE** (87%), not a
  cost story. No adverse spread timing (fill p50 0.3 pips = panel p50).
- Direction: long fades −696.0 on 95 RT = 79% of the fold loss — buying
  pd_l-breaks in a falling market. Short fades ALSO lost (−188.4) on
  days both edges ran.
- Mode-plane noise: flip-day pool −1,455.5 (102 RT, −14.27/RT) vs
  non-flip +571.1 (64 RT); follow-mode entries −407.9 on 28 RT worst
  per-trade; several worst days are near-mirror inversions of R-ORIG on
  the SAME day (2022-07-05 daemon −109.0 vs R-ORIG +108.1; min-range day
  pct 0.0167, R-ORIG-SEMANTICS label).
- NOT beta: daemon−SHORT = −1,723.2 in F2, daily rho −0.189
  (anti-correlated — the daemon faded whatever moved, losing on both
  legs while SHORT_ALWAYS earned +838.8).
- Silencing is NOT the F2 driver (R-ORIG on daemon-silenced days only
  +139.2 vs +1,736.5 on daemon-active days).

**Events are context, not proximate cause (the owner's prior):** the
energy shock / Fed decision days are NOT where F2 was lost. No-event
days carry ≥85% of every losing fold's loss (F2: −756.2 of −884.4 =
85.5% union rule / 81.6% strict partition — conclusion unchanged);
F2's 8 surprise energy/geopolitical days were net POSITIVE (+43.6).
Scheduled-macro days carry the worst per-RT tail (FF −18.2/RT) but only
−346.2 of the −2,116.5 FF bleed. **F2 was lost in the ordinary-day
persistent regime** (policy-path divergence + energy terms-of-trade made
band-break persistence the norm for months), not on shock days.

**F1/F5:** same mechanism, smaller scale — F1 −188.8 (gross −94.8 /
cost −94.0, borderline MIXED; 100% of loss on no-event days); F5 −191.5
(gross −113.0 / cost −78.5; idiosyncratic — daemon−SHORT −21.4, rho
−0.026). **GBPUSD context:** its whole −1,708.9 is essentially cost
(gross +33.5, cost −1,742.4 on 0.8-pip spreads vs EURUSD 0.3) — the
family is untradeable on GBPUSD at the taker book regardless of signal.

## 2. The three hypotheses and the skeptic's table (Phase B, pre-PnL)

| ID | Claim (short) | Verdict | Veto class / evidence |
|---|---|---|---|
| H-FR1 MACRO-DIV-PERSIST | policy-path divergence → band-break persistence premium, multi-day holds | **VETOED_DEAD_CLASS_MACRO** + multi-day arm **BLOCKED_FINANCING_UNCOSTABLE** | class #7/#2 dead (FXFV5 sham out-earned; FXFV3-A6 stress+PIT fail; FXNG1; DINV rho 0.303/0.310); no citable financing band exists on vendor data (FOREX-NG6/NG7); premise also factually weak — timeline gaps (FOMC 2021-12-15, 2022-05-04 missing) and FF bleed not month-isolated |
| H-FR2 SCHED-TAIL-AVOID | stand the fade down on scheduled macro days ("RANGEFADE + news filter") | **VETOED_VARIANT_SAME_FAMILY** | the owner's kill-on-sight case, confirmed: the filter is net **−72.6 pips** on the family's own book (saves +163.4 in F1/F2/F5, removes +236.0 of winners in F3/F6); F2 stays −747.5; the −18.2/RT cell is 19 hindsight-selected trades; FXFV5 sham-counter-evidence |
| H-FR3 BOUNDED-REVERSION | keep the TARGET_EXIT pool, cut the FORCE_FLAT tail (time-box / maker form) | **VETOED_VARIANT_SAME_FAMILY** + **VETOED_UNFUNDABLE_ARM** (maker form) | re-gating after seeing the ex-post exit_type pool = selection on outcome (hold-time distributions overlap: FF p25=4 vs TE p75=5 bars); TRACKA2-C1C2C3 precedent + owner law 2026-09-26; maker form has zero queue-position bytes (P3-A arithmetic: ALL-IN ≥ quoted crossing) |

Skeptic enumeration duty: CLOSED — no class the Phase-A facts open that
the 12-class viability table did not already close (TE+/FF− is a
decomposition of the family's own outcome, not a new observable; the F2
no-event persistence implies no tradable layer on Dukascopy M1; no pair
flips at the cost floor). §7 ruling: **NO** — Phase A is new *diagnostic
knowledge about a dead family's internals*, not a new information layer,
payer, or data/cost authority.

## 3. Frontier status (unchanged by this research)

VIABILITY_cohort3 `NO_CANDIDATE` stands confirmed. Reopening remains
owner-gated (viability §C): (1) broker cost authority — the R1 probe's
P3-A reopening condition is arithmetically unattainable at IBKR
IDEALPRO (min crossing 1.0 pip @k=2.0 vs frozen ≤0.41 — see R1 terminal
commits); any OTHER measured all-in venue could still open it;
(2) EDQ1 independent source decision; (3) citable financing band
(reopens H-FR1's multi-day class lawfully — this packet's F2 persistence
facts would then be the diagnostic motivation, disclosed as
outcome-exposed ancestry). Then a fresh F-0 mechanism-class court before
any rho/PnL — not this packet.

## 4. Exposure accounting (what this research consumed)

Nothing: all analyzed windows (EURUSD/GBPUSD 2021-01..2026-06) were
ALREADY outcome-exposed/consumed surfaces; sealed holdouts (2026-H1
AUDUSD/USDCAD) never read; no trial ledger rows written; no shadow
journal/journal-schema change; no registry write (no cycle was created —
this ran as a post-terminal diagnostic on the ERP1-TRACKA-COHORT-1
control namespace, the diag-daemon precedent). Machine lock: FREE_PROVEN
throughout; the A7 lane's M1 rebuild held and released it cleanly.

## 5. Artifact index (all on main under research/control/ERP1-TRACKA-COHORT-1/failres/)

- Phase A attribution: `ATTRIB_failres_REPORT.md` + trades/agg/daily
  JSONs (lane commit da4a92c2; landed 5b0b34b1)
- PIT events: `EVENTS_failres_REPORT.md` + `failres_events_timeline.jsonl`
  (fb3cfbf1) — 131 events, 110 PRIMARY; DST + ECB-format corrections;
  gaps disclosed (2 FOMC dates, decision sizes free-text)
- Cost/execution: `COSTEXEC_failres_REPORT.md` + agg (7bf55f34) — EURUSD
  ceiling 0.6 base / 1.2 ×2.0 / 2.4 non-fragile line pips per RT
- A7 reproduction: `A7_failres_repro_REPORT.md` (ed3e0bbf) — ALL_MATCH
- Lead overlay: `FAILRES_LEAD_OVERLAY.md` (+ provenance; in 5b0b34b1)
- Skeptic: `SKEPTIC_failres_REPORT.md` + verdicts JSON (6e946e5e)
- Lane handoffs (zcode_orch_v3_handoff@1): `HANDOFF_failres_{attrib,
  events,costexec,a7repro,skeptic}.json`
- Lane branches: orca/erp1-ta1-failres-{attrib,events,cost,a7,skeptic}
  (worktrees left in place under .worktrees/erp1-tracka-cohort-1/)

No FAMILY_FAILURES/LESSONS/MAP append was performed by this session —
that is a close-out action for the owner/A7 terminal flow, and this
research added no scored trial to record.
