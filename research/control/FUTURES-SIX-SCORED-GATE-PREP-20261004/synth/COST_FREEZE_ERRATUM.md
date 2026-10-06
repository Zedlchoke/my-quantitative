# COST_FREEZE_ERRATUM — FUTURES-SIX-SCORED-GATE-PREP-20261004 (append-only correction of record)

- Trigger: owner-side follow-up review 2026-10-04 (this thread). The
  round's wave-2 synthesis carried a **load-bearing fee inconsistency**:
  `synth/OWNER_DECISION_PACKET.md` OD-2 printed Variant A's default as
  "ES all-ins 21.006/33.506/46.006" (the frozen SPEC's STALE, glued-value
  numbers) while `synth/CYCLE_PROPOSAL.md` §2 printed "corrected fee
  table (2.24/side tier-1 ES)" (the Variant-B composition). Both cannot
  be true at once. This erratum is the correction of record; the two
  synthesis files are superseded **by reference** (edited in the same
  commit, with the edit diff disclosed); **no frozen historical file is
  touched** (SPEC_PB1_ES and the six-adopt packet stand as committed).

## 1. What the bytes say (re-measured for this erratum, 2026-10-04)

1. **Exchange cell ES/NQ = 1.38 — EVIDENCE-SETTLED, not a choice.**
   RAW-HTML `1.38<sup>6</sup>` occurs exactly twice (NQ L1694, ES L1706);
   footnote 6 = "Non-Member spread orders will be charged $1.30 per
   contract."; the sibling proof (`0.95<sup>4</sup>` → "0.954") and the
   IBKR worked example `0.85 + 1.38 + 0.00 + 0.01 = 2.24` (arithmetic
   EXACT) close the adjudication [`FEES_CORRECTED.md`; P0_ERRATUM_VERDICT;
   A7_FEE_REAUDIT §2-§4 — all committed]. **No future freeze may consume
   1.386.**
2. **The frozen SPEC's numbers are historical evidence of the SPEC, not
   executable cost.** SPEC_PB1_ES §5 L100 prints `1.386` (the retired
   glued superscript) and L104 prints `S1 21.006 · S2 33.506 · S3 46.006`
   (decomposition: 0.85 + 1.386 + 0.02 + spread 6.25 + slippage
   12.50/25.00/37.50). GATE_REVIEW_NOTE §1 and FEE_ERRATUM_DRAFT §4
   (LAW 2-4) already record these lines **UNDER REVIEW** and state "P1
   families consume `fees_corrected.json`" [OBSERVED, cited].
3. **The six-adopt CYCLE_LAUNCH_DRAFT §3 carries the same stale
   inheritance** — its Variant-A line prints 21.006/33.506/46.006 (window
   −0.01 ⇒ 20.996/…) while its cost table prints tier-1 2.24. That packet
   is a completed round's committed text: it stands as history and is
   **superseded by this erratum for every future freeze**. Nothing in it
   is edited.
4. **The only internally consistent dual-variant statement in the
   program is A7_FEE_REAUDIT §8** (this round, wave-1, verified): the
   table below.

## 2. The corrected, executable-at-new-freeze cost table (PROPOSED; MODELED COST; VERIFIED_VS_ACCOUNT=NOT_RUN)

| | Variant A — NFA basis | Variant B — IBKR offset basis |
|---|---|---|
| Regulatory component | 0.02 default; 0.01 only 2014-10-01→2017-12-31 | 0.01 throughout (current capture epoch) |
| Fee all-in/side (exchange 1.38) | 0.85+1.38+0.02 = **2.25** | 0.85+1.38+0.01 = **2.24** |
| ES all-in/side S1/S2/S3 (+spread 6.25 + slippage 12.50/25.00/37.50) | **21.00 / 33.50 / 46.00** | **20.99 / 33.49 / 45.99** |
| ES round-trip S1/S2/S3 | 42.00 / 67.00 / 92.00 | 41.98 / 66.98 / 91.98 |
| NQ all-in/side S1/S2/S3 | 23.50 / 28.50 / 33.50 | 23.49 / 28.49 / 33.49 |
| Stale SPEC print (NEVER consumable) | 21.006 / 33.506 / 46.006 | — |
| Delta A−B | +$0.01/side = +$0.02/RT | — |

Window note (A only): inside 2014-10-01→2017-12-31 Variant A's reg drops
to 0.01, so its all-ins equal B's (20.99/33.49/45.99) in that window.

## 3. Answers to the four questions posed (no self-ratification)

1. **Historical frozen evidence**: SPEC_PB1_ES §5 as committed (1.386;
   21.006/33.506/46.006) and six-adopt CYCLE_LAUNCH_DRAFT §3's
   Variant-A line — both stand as history, both already marked
   UNDER-REVIEW by the fee-erratum rounds, both superseded for future
   freezes by §2 above.
2. **Proposed executable cost at a new freeze**: §2's dual-variant table
   with exchange 1.38. Which variant executes is decided ONLY by the
   owner (next item).
3. **Mandatory owner ruling**: **D3 (= e.4) — the regulatory basis
   choice — is REQUIRED and now EXPLICIT for CYCLE-1**; e.1-e.3 may be
   signed "accept as tabulated" (documented by the A7) without blocking
   an ES cycle. D2's execution half is discharged (A7 ran clean); its
   ruling half rides the D3 signature.
4. **Is "default A" only a regulatory basis, or does it inherit 1.386?**
   **Basis only.** The lawful reading of the old "silence ⇒ frozen SPEC
   §5 law binds" is: the NFA-basis RULE (0.02 default / 0.01 window)
   inherits; the glued VALUE 1.386 does not (retired by the erratum
   chain). Under silence, the executable default is therefore
   **Variant A × corrected 1.38 = 2.25 / 21.00-33.50-46.00**. However —
   because relying on that silent-default reading is exactly where this
   inconsistency crept in, the packet now requires the **explicit D3
   signature** (fail-closed) and CYCLE-1 is declared
   **BLOCKED_COST_FREEZE** until it lands.

## 4. Status change (binding on this round's synthesis)

CYCLE-1 `FUTURES-ES-PB1-V1` is **BLOCKED_COST_FREEZE pending the owner's
D3/e.4 basis ruling** (plus the already-listed registration → prelaunch
A7 → typed GO). The earlier "chỉ còn registration + A7 + GO" phrasing is
**withdrawn**. No scored run, no dry-run, no freeze consumption occurred
while the inconsistent numbers were live (0 identities, 0 trials — the
defect was caught at packet review, pre-freeze).

— End COST_FREEZE_ERRATUM. Append-only; supersedes by reference; picks
nothing; ratifies nothing.
