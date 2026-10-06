# SHORTLIST_STALE_COST_ERRATUM — FUTURES-K6GATE-PREP-20261004 (append-only correction of record)

- Trigger: independent fresh-context packet check at EXACTLY HEAD
  `05e54939` (`verify/PACKET_05e54939_CHECK/PACKET_05e54939_CHECK.md`,
  verdict **FAIL**) found stale-cost residue in the PRIOR round's
  shortlist lane deliverables that both correction waves and the
  doc-scoped follow-up verifier had missed. The owner-packet authority
  chain itself (OWNER_DECISION_PACKET + COST_FREEZE_ERRATUM +
  CYCLE_PROPOSAL + REPORT_VI) PASSED all checks (C1/C3/C4/C5); the FAIL
  is confined to `FUTURES-SIX-SCORED-GATE-PREP-20261004/shortlist/**`.
- Per the owner's condition: **CYCLE-1 stays BLOCKED_COST_FREEZE**
  (unchanged), and this correction is **append-only** — the shortlist
  files stand as committed; this erratum supersedes the named lines **by
  reference** and is the correction of record for every downstream
  consumer. No frozen file is edited.

## 1. Superseded lines (exact quotes, as committed at 05e54939)

| # | Location | Offending text (verbatim) | Defect class |
|---|---|---|---|
| F-4a | `FUTURES-SIX-SCORED-GATE-PREP-20261004/shortlist/SHORTLIST_6SYM.md` PB1 row, C5 cell | `S1 21.006 / S2 33.506 / S3 46.006 per side FROZEN (Variant A) — binds until D3 (SPEC §5)` | retired stale print presented as OPERATIVE cost, no stale label — violates COST_FREEZE_ERRATUM §2 "NEVER consumable" |
| F-4b | `…/shortlist/shortlist_6sym.json` PB1 `cost` field | `S1 21.006 / S2 33.506 / S3 46.006 per side FROZEN Variant A (SPEC s5), binds until D3` | same |
| F-5 | `…/shortlist/SHORTLIST_6SYM.md` ES-F1 row, C4 cell | `armed n≈91 × tail-split with S2 33.506/side floor` | numeric USE of the stale value as an MDE floor |
| F-6a | `…/shortlist/SHORTLIST_6SYM.md` PB1 row, C7 cell | `needs registration + prelaunch A7 (0 HIGH/CRIT) + typed owner GO` | blocker enumeration missing the now-REQUIRED D3 signature (pre-erratum phrasing) |
| F-6b | `…/shortlist/SHORTLIST_6SYM.md` ESNQ-F5 row | `frozen variant default-binding` phrasing | silent-default residue (withdrawn by COST_FREEZE_ERRATUM §3.4) |

## 2. Corrected statements (authoritative; from COST_FREEZE_ERRATUM §2)

1. **Operative ES cost at any new freeze** = the dual-variant table with
   exchange 1.38: Variant A 2.25/side, all-in S1/S2/S3
   **21.00 / 33.50 / 46.00** (RT 42.00/67.00/92.00); Variant B 2.24/side,
   **20.99 / 33.49 / 45.99** (RT 41.98/66.98/91.98). The print
   21.006/33.506/46.006 is the frozen SPEC's historical glued-value line
   — NEVER consumable. "Binds until D3" is corrected to: the NFA-basis
   RULE is what a D3-A signature would adopt, at corrected 1.38; no
   silent default exists (withdrawn).
2. **ES-F1 MDE floor cell**: S2 floor = **33.50 (A) / 33.49 (B)**, not
   33.506. Arithmetic note (recorded, not a rescue): the 0.006 USD/side
   delta changes no MDE or gate verdict anywhere it is cited (all such
   comparisons are bp-class magnitudes vs MDE ≥ 12 bp-class); any future
   freeze re-derives the cell against the signed variant.
3. **PB1 blocker enumeration**: `D3 cost-freeze signature
   (BLOCKED_COST_FREEZE) + registration + prelaunch A7 + typed GO` —
   the D3 signature leads.
4. **ESNQ-F5 phrasing**: any variant-default language is void; EXPWITCH
   is moreover DEAD at its pre-declared F5-K6 on BOTH legs (this round's
   ES-K6/NQ-K6 gates) — its cost cells are moot for scheduling.

## 3. Why append-only (law)

The shortlist artifacts are a completed verified round's lane
deliverables (wave-1 @ 893db28c; byte-identical through 4531c5f5 and
05e54939 — the correction-wave diffs exclude shortlist/, so this is
surviving residue, NOT a regression). Historical/committed artifacts are
append-only evidence; corrections supersede by reference (same pattern
as COST_FREEZE_ERRATUM superseding the six-adopt packet's Variant-A line
without editing it).

## 4. Authority chain after this erratum

Consumers of the six-gate round's shortlist MUST read it through this
erratum. The packet-check FAIL is thereby dispositioned: F-4/F-5/F-6
closed by supersession; the owner-packet chain (which passed C1-C5
clean) remains authority together with this erratum. CYCLE-1 =
**BLOCKED_COST_FREEZE** pending the D3 signature — exactly as before.

— End SHORTLIST_STALE_COST_ERRATUM. Append-only; supersedes by
reference; ratifies nothing; keeps every gate closed.
