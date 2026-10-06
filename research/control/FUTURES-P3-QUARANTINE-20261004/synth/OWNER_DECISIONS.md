# OWNER_DECISIONS — FUTURES-P3-QUARANTINE-20261004 (Q6-SYNTH-VERIFY, 2026-10-04)

Numbered decision packet for the owner. Each item: context → options → what each option
unblocks. Nothing here is authorization by itself; every ruling must be written.
Evidence pointers: `quarantine/TRANSPORT_QUARANTINE.md`, `synth/FINAL_SAFE_BLOCKER_MATRIX.*`,
`fee_a7_readiness/A7_FEE_READINESS_PACKET.md` §e, `cal_permitted/CAL_PERMITTED_RETRY.md`,
`data_checks/*`.

## D1 — P3 transport adjudication (the gating decision)

Context: P3-BROWSER-CAL self-disclosed a bypass transport after being blocked;
quarantined without waiting (QUARANTINE_NOTICE, 2026-10-04T01:00Z). Auditor verdict
QUARANTINED_POLICY_BREACH stands; zero downstream dependents; zero value leaks
(verified). 28 P3 cells: 8 now have independent permitted provenance (Q5) —
#1/#3/#4/#14/#15/#16/#22/#24 (+ #27 partial 8/10 ids) — 19 remain
NOT_OBTAINED/PENDING_ADJUDICATION. Q5's independent recovery makes most cells moot for
coverage either way. Related sub-question (VF-12): Q5 cross-checked endpoint *paths*
against the preserved P3 disclosure while re-deriving them independently from CDX —
owner rules whether that path knowledge taints Q5's captures (they remain re-derivable
from `captures/cdx_*.txt` regardless). Also acknowledge Q5's attempt-budget guidance
deviation (~60 archive fetches vs ~8/target; ≤2/URL/method LAW honored — etiquette
matter, VF-13).

- **Option A — accept exception in writing**: P3 cells revived only via a newly
  dispatched verification lane working from preserved evidence (no rerun of the
  breaching route). Unblocks: the 19 pending cells become adjudicable (though most are
  also reachable via Q5-route extraction, see D6); closes the transport question.
- **Option B — permanent quarantine (recommended default)**: the 19 cells stay
  NOT_OBTAINED unless re-obtained via permitted routes (D6); P3 evidence remains
  quarantined-but-preserved. Unblocks: nothing lost that Q5/D6 cannot recover; policy
  boundary reaffirmed ("blocked means blocked").
- Either way: record the Q5 provenance ruling (VF-12) and the etiquette deviation
  acknowledgment (VF-13) in the same writing.

## D2 — Authorize the fee A7 (packet ready)

Context: `A7_FEE_READINESS_PACKET.md` is complete (scope: erratum end-to-end +
propagation + SPEC_PB1_ES §5 under-review governance adjudication; 21 inputs sha256
pinned; 9-item check list; preconditions). Packet existence is NOT authorization; the
A7 has not been run.

- **Option A — authorize now**: unblocks independent re-derivation of every
  load-bearing fee cell, the 25-site propagation classification, and formal closure of
  the SPEC §5 UNDER-REVIEW state; all fees stay MODELED/VERIFIED_VS_ACCOUNT=NOT_RUN
  until then.
- **Option B — defer**: fees remain UNDER REVIEW; 6J/6A/ES/NQ cost gates stay open.
- The 4 open rulings the A7 needs ruled on (packet §e) may be decided with or ahead of
  authorization: (e.1) FX-group alias binding page (accept PARTIAL or name a page);
  (e.2) account geography basis for the IB-JP paren (US-entity basis confirmation);
  (e.3) NYMEX reg 0.02→0.01 temporal window / epoch-binding rule; (e.4) = D3 below.

## D3 — NFA-basis ruling for the $0.01/side ES/NQ all-in discrepancy

Context: `hypo/es_nq` models all-ins from fee 2.24 (reg = IBKR offset 0.01 → ES
20.99/33.49/45.99; NQ 23.49/28.49/33.49) while SPEC_PB1_ES §5 law mandates the NFA
timeline (0.02 default → 21.00/33.50/46.00; 23.50/28.50/33.50). Exactly $0.01/side,
cost-understating direction; nothing scored; both files verified unedited.

- **Option A — standardize on NFA 0.02 (SPEC-consistent)**: future cost-gate use takes
  the higher, more conservative floor; hypo/es_nq values annotated superseded-by-ruling.
- **Option B — standardize on offset 0.01 (account-realistic)**: SPEC §5 line then
  needs a dated owner annotation; floors stay $0.01/side lower.
- Unblocks: any future cost-gate adjudication and the A7's check 8; can be folded into
  D2's authorization writing.

## D4 — ES denominator / cap (36 minimal vs 24 frozen)

Context (inherited, unchanged): census minimal ES identities = 36 > frozen cap 24,
headroom 0 → every ES family BLOCKED_TRIAL_BUDGET.

- **Option A — raise/define cap** (owner decides number): unblocks ES family selection
  under the existing ranking (package-quality only).
- **Option B — keep 24**: ES stays blocked; budget question (placebo-budget 3-ruling
  proposal from CENSUS_PROPOSAL) still open from the parent round.

## D5 — CPI Jan-2026 announcement-date pin via permitted routes

Context (Q4): the 2026-lapse section's announcement date is NOT_PINNED from existing
artifacts; 2026-01..02 decision windows remain vintage-ambiguous; the vintage rule
(first-published until official announcement; current-calendar inference FORBIDDEN) is
standing law.

- **Option A — dispatch a bounded permitted-routes capture pass** (Q5 route: Wayback
  CDX of bls.gov schedule/notice pages; ≤2 attempts/URL/method): unblocks
  vintage-ambiguous decision dates for CPI Jan-2026 reference week.
- **Option B — leave unpinned**: those decision dates stay unusable for PIT work.

## D6 — Remaining calendar cells (next-round scope)

Context: still open after Q5: NQ 2026 holiday deviations; 6B 2023-2025 (12); 6A
Mar+Jun 2023; 6J all-2023 + Mar/Jun 2024; GC 2024; GCF25; SI 2026; CL/GC Labor-2025
window; NG + SI 2024-2025 holiday times. Q5's route may extend. **No new fetch needed**
for several P3-pending cells: J1Z26 + J1 2026-2029, ADZ26 + 2027-2028, ECH26/ECM26 sit
unextracted inside preserved Q5 captures (`pcal_69_6j_dl_…xls`, `pcal_37_6a_…json`,
`pcal_58_6e_…json`) — a read-only extraction lane suffices.

- **Option A — dispatch one extraction+extension lane** (permitted routes only):
  unblocks the FX Dec-2026 quarterlies (6J/6A side), parts of the supersets, and a
  second attempt at the genuinely-absent cells (NQ deviations, 6B, GC-2024, SI-2026,
  NG/SI times).
- **Option B — defer to next round**: cells stay NOT_OBTAINED; matrix already reflects
  them accurately.

## D7 — NG signed-surprise rule + comm data decision (unchanged, carried)

Context (inherited): NG-F1 stays NOT_RUN_BLOCKED_R1 until a signed-surprise rule is
ruled; CL/NG/GC/SI remain NOT_QUALIFIED_V2 (zero comm O1M at vendor root) — the owner
data decision gates all four.

- **Option A — rule the signed-surprise definition + decide the comm data path**
  (serial re-fetch / vendor purchase / park): unblocks NG event legs and any comm
  registration path.
- **Option B — keep parked**: no change; standing rulings continue.

— All seven decisions can be issued in a single written ruling; D1 is the only one
gating the quarantine's final closure, and D2/D3 gate the fee layer's exit from
UNDER REVIEW.

— End OWNER_DECISIONS.md.
