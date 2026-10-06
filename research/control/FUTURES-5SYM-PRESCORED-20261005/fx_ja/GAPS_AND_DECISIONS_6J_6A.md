# GAPS_AND_DECISIONS_6J_6A — gap inventory and decision requests (P5-* namespace)

- Lane FXJA, round FUTURES-5SYM-PRESCORED-20261005. Three tiers:
  **(a) workable-now** (evidence complete, PREP-legal, no owner input
  needed), **(b) owner decisions** (new IDs, prefix **P5-**; prior decisions
  cited by their original IDs — ADOPT-D8/D9, D2/D5, SIXGATE-class — never
  renumbered, never reused), **(c) post-approval gates + GO** (what happens
  after the owner signs). Missing evidence = NOT_RUN, never PASS.

## (a) Workable now — complete on committed evidence

1. **6J identity + orientation**: tick 5e-07 = $6.25, 12.5M JPY, quote
   direction PROVEN (own raw slice) — SPEC_6J §1–§2. Nothing open.
2. **6A tick-era adjudication**: RESOLVED_PER_ERA from 327k+ closes;
   era-aware cost tables delivered (D-2) — SPEC_6A §1–§2. The DATA-side
   work is closed; only the D8 SIGNATURE is open.
3. **Roll mechanics both symbols**: 27 rolls each measured; 6A cease-guard
   variant 0 violations; mode ledger 19/8 (6J), 21/6 (6A); CEASE-SYNC
   descriptive table (18 four-symbol abrupt weeks of 24) — chain layer
   closed.
4. **Calendar**: 6J 62/68, 6A 66/68 expiry cells (post-CAL_JANQ); proven
   absences documented with CDX evidence; fail-closed exclusion law
   written — CALENDAR_PIT_POLICY §1–§2.
5. **Cost contracts**: 6J RT $67.42 = 8.4499 bp (tier 8.30–12.10 bp); 6A
   era-aware $104.92/15.18 bp vs $54.92/8.20 bp; stress ladders tabulated —
   COST_CONTRACT §1–§3. Arithmetic closed; ACCOUNT verification open (b).
6. **Budget decomposition**: J-A 29 / J-B 36 / J-C 33–40 with explicit ID
   enumeration and signature list — IDENTITY_BUDGET_6J. Ready for the
   owner's ceiling signature.
7. **Freeze-builder + runner contracts**: drafted, hash-pinned, hard-refuse
   logic specified — executable the moment (b) lands.

## (b) Owner decisions (new, P5-prefixed; nothing here self-ratifies)

| ID | decision | exact ask | fail-closed default if unanswered |
|---|---|---|---|
| **P5-D1** | **6J ceiling** | Sign ONE option — J-A (29) / J-B (36) / J-C (33 or 40) — AND name the clock-shadow reading **(a)** (shadow inside the 3 controls; all totals) or **(b)** (additive +1/family block). No 6J cap exists anywhere (CENSUS_FINAL §4). | No 6J registration; SPEC_6J stays a draft; builder refuses (`BLOCKED_NO_CEILING`) |
| **P5-D2** | **DC §1.3 boundary ruling (6J RMM leg)** | Required ONLY if J-C: rule that a migration-mode microstructure hypothesis (abrupt vs gradual, 27 measured rolls) is distinguishable from "roll timing as construction" under DC §1.3's roll≠alpha law (NQ-F4 Role B precedent; GC-F2 construction-only precedent). | J-C unavailable; J-A/J-B remain signable |
| **P5-D3** | **6J BBO/fill ruling** | Accept the conservative fill law (next-bar open; close-proxy spread $25 high-biased; SL-priority; BBO NOT_RUN per D5) as the fill model of record for 6J — or fund a BBO study (none exists; BBO NOT_RUN stands). | BBO NOT_RUN binds; no scored 6J cell passes any fill-sensitive gate |
| **P5-D4** | **6J/6A fee A7 posture (feeds D2)** | Whether 6J/6A wait for the standing D2 fee A7 (packet READY-not-run) or receive a separate FX-fee A7 authorization; until ruled, ALL cells stay MODELED COST / UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN. | No scored cell on any FX symbol passes a cost gate |
| **P5-D5** | **6A activation package (bundle pointer)** | Acknowledge the activation chain for the frozen 26-ID contingency: **PB3 lift → ADOPT-D8 ratification** (Option A ratify the measured 2020-11-20/23 boundary / Option B demand the exchange document) **→ ADOPT-D9** cease-guard standing law → D2 fee A7 → ABS/China calendar acquisition ruling (AF3 K4). This mints no new substantive question — it sequences existing owner-held decisions for 6A. | 6A stays PB3 PARK: 0 budget, 0 identities; builder/runner refuse (`BLOCKED_PB3_PARK`, `BLOCKED_D8_UNRATIFIED`) |
| — | *(carried, not re-minted)* BoJ intraday stamps | Owner decision stands: NOT_IN_CORPUS; JF1 window-convention-only. Restated inside every 6J signature; no new ID minted. | Stamps stay out; K3 anchor law governs |
| — | *(carried)* JF2 threshold constant | If any JF2 block is inside a signed option, owner fixes the zone threshold a priori (PARAM-GAP). | JF2 block cannot freeze |
| — | *(carried)* Placebo budget | Single-seed/single-delay publication law binds; ≥100-seed expansions are separate owner rulings (IDENTITY_TABLES §7.3). | No permutation-robustness claims exist |

Prior-ID citations used above (not renumbered): D2 (fee A7), D5 (BBO law),
D8 (6A tick-era), D9 (cease-guard standard) — per the launch packet
`open_decisions_dependency.json` and six-readiness OWNER_DECISIONS.

## (c) Post-approval gates + GO (sequence, per CYCLE_LAUNCH_DRAFT §6)

1. **Registration** at the future cycle's own gate: freeze set with all
   sha256 (spec + exclusion list + identity table + chain digests + cost
   digest + calendar provenance).
2. **Prelaunch A7** (key 1 of 2): 0 HIGH/CRITICAL unresolved — identity
   enumeration vs IDENTITY_BUDGET_6J, cost arithmetic vs COST_CONTRACT,
   PIT/exclude coverage, budget accounting, forbidden-word scan.
3. **Exact-arm dry-run**: rehearsal of the exact registered set under ×1.0
   costs; quarantined descriptive-only; identity enumeration byte-exact.
4. **Owner typed GO** (key 2 of 2): `GO <REGISTERED-CYCLE-ID> SCORED
   EXECUTION`, verbatim, recorded `auth/GO_RECORDED.json`.
5. **Scored run under the canonical heavy lock** (one heavy job machine-wide).
6. **Reproduction twin** (G8): byte/logical match incl. chain digests.
7. **Terminal A7 + two-half close**; terminal outcomes pre-decided at
   freeze (`*_REJECT_ALL` / `*_NO_ELIGIBLE_IDENTITY` / `*_SURVIVOR_PENDING_S1`
   / `*_BLOCKED_<reason>`); REJECT_ALL is a clean, valid result.

6A-specific post-approval additions (only after P5-D5 chain completes):
era-aware cost binding verified at runtime (runner A3 probe); era-1 rows
routed descriptive-only; the 26-ID table consumed verbatim, never expanded.

## Standing NOT_RUN register (this lane)

- Builder execution, runner execution, all acceptance probes A1–A9: NOT_RUN
  (authority-refuse armed).
- BBO/true spread/queue/fill on both symbols: NOT_RUN (D5).
- Fee VERIFIED_VS_ACCOUNT: NOT_RUN (A7/D2 posture).
- BoJ intraday stamps: NOT_IN_CORPUS. 6J 2023 + 2 unidentified expiry cells
  and 6A 2023Q1/Q2: NOT_OBTAINED (derivation forbidden). FX holiday session
  times: NOT_OBTAINED/NOT_IN_CORPUS. 6E/6B tick constancy at 2020-11-23
  (AF4 secondary negative): NOT_RUN (FXEB lane's step). ABS/China calendars:
  NOT_RUN. RBA decision times: not carried (declared convention).
- 0 scored runs, 0 PnL anywhere in this lane.

— End GAPS_AND_DECISIONS_6J_6A.
