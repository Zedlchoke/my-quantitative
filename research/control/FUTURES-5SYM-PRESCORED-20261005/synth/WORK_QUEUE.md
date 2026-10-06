# WORK_QUEUE — FUTURES-5SYM-PRESCORED-20261005 remaining work (dependency-ordered)

Status codes: [B] = blocked on owner decision (see OWNER_DECISION_PACKET_P5 §0);
[A] = workable now; [C] = post-approval gates only.

| # | Item | Class | Depends on | Lane owner |
|---|---|---|---|---|
| 1 | Verify EXEC runner contract numbers vs per-symbol lane identities (NQ 20/0.25, 6E 125k/0.00005, 6B 62.5k/0.0001, 6J 12.5M/5e-07 + direction, 6A era table) | [A] | wave-2 verifier first pass | VERIFY → EXEC |
| 2 | Independent round VERIFY (all 7 lanes at committed SHA) | [A] | this synthesis commit | VERIFY lane |
| 3 | NQ-F3 full-era rebuild re-run on cache_v3 | [C-prep] | P5-NQ1 (D9) signed | NQ |
| 4 | NQ freeze-builder implementation per FREEZE_BUILDER_SPEC_NQ (GATE-0 refusal while D9 unsigned) | [C-prep] | P5-NQ1 + P5-NQ2 | NQ + EXEC |
| 5 | 6E/6B freeze-builder implementation | [B]→[C-prep] | P5-FXEB-OD1 (PB2) + OD2 | FXEB + EXEC |
| 6 | 6J freeze-builder implementation | [B]→[C-prep] | P5-FXJA-D1 | FXJA + EXEC |
| 7 | 6A contingency builder (era-aware cost binding at runtime; era-1 rows descriptive-only) | [B] | full P5-FXJA-D5 chain | FXJA + EXEC |
| 8 | FX-F5 CIP-vintage sensitivity quantification (HYPO G3) | [A] | committed ALFRED captures | CALCOST-class lane |
| 9 | FX-F6 transfer measurement (HYPO G4) | [A] | none | FXEB |
| 10 | AF2 K2 vintage-flip test (HYPO G9) | [A] | same machinery as #8 | CALCOST-class |
| 11 | NQ session-σ dispersion proxy re-derivation on v3 (HYPO G11) | [A] | cache_v3 committed | NQ |
| 12 | FX-F4 M2c-corrected RT/MDE re-derivation (HYPO G8) | [A] | committed erratum | FXEB |
| 13 | Court §b1.1 1m trigger-time anatomy (commissioning decision P5-FXEB-OD11; machinery prep is [A]) | [A-prep]/[B-run] | PB2-path decision | FXEB |
| 14 | Registration packets assembly (per-symbol SPEC + identity annex + cost table + calendar manifest, all sha-pinned) | [B]→[C] | the §2 signature chains | controller |
| 15 | Prelaunch A7 (fresh-context) / exact-arm dry-run / typed GO / scored under lock / twin / terminal A7 | [C] | registration | future cycle lanes |

Residual NOT_OBTAINED inventory (fail-closed exclusions stand until/unless the
paired decision lands): NQ 2026 holiday product-level 0/10 (P5-CALC-NQ-HOLPROD);
6B 2023Q1-24Q2 expiries + 0/42 holidays (proven absent); 6J 2023 ×4 + 2
identity-undetermined (P5-CALC-6J-IDENT) + holidays; 6A 2023Q1/Q2; 6E ECU26/ECZ26
+ 8 aged-out; RBA forward Nov/Dec-2026 (P5-CALC-RBA-FWD); ABS/China calendars
(P5-HYPO-OD3). Closed this round: BoE MPC 2026 full set, BoJ MPM remaining-2026
(dates), FOMC remaining-2026 (Oct 27-28, Dec 8-9), RBA 2026-to-date — all
official captures sha-pinned under cal_cost/captures/.

— End WORK_QUEUE.
