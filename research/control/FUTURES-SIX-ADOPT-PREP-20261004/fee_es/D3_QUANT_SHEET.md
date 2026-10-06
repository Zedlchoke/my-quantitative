# D3_QUANT_SHEET — the $0.01/side reg-basis divergence, quantified (FEE-ES lane, 2026-10-04)

**Decision requested (owner D3, carried; = A7 packet ruling e.4): standardize the regulatory
component of modeled ES/NQ all-ins on the NFA timeline (0.02) or the IBKR offset (0.01).
This sheet quantifies. Nothing here is a ruling. Both source files re-hashed unedited this round:
SPEC_PB1_ES.md `445f7499…7073`, fees_corrected.json `7cd65f25…aca8`.**

## 1. The two bases

| | basis law | fee all-in | ES all-in/side S1/S2/S3 | NQ all-in/side S1/S2/S3 |
|---|---|---|---|---|
| **NFA basis** (SPEC_PB1_ES §5 L101: "timeline chính thức NFA — dùng MỘT nguồn duy nhất"; IBKR offset "KHÔNG dùng, KHÔNG cộng kèm") | reg 0.02 default; 0.01 only 2014-10-01→2017-12-31 | 0.85+1.38+**0.02** = **2.25** | **21.00 / 33.50 / 46.00** | **23.50 / 28.50 / 33.50** |
| **Offset basis** (hypo/es_nq composition: "2.24 fees + spread + slippage", the 2.24 bundles reg 0.01) | corrected IBKR capture (worked example `0.85+1.38+0.00+0.01=2.24`); IB-JP paren 0.011 = 0.01×1.1 tax, pending ruling e.2 | **2.24** | **20.99 / 33.49 / 45.99** | **23.49 / 28.49 / 33.49** |

(As published, SPEC §5 prints 21.006/33.506/46.006 — that carries the stale exchange 1.386; under
the corrected 1.38 the NFA-basis values are exactly 21.00/33.50/46.00. Direction of the divergence:
**offset basis understates cost** by construction.)

## 2. Delta arithmetic

- Per side: **$0.01** (2.25 vs 2.24). Per round trip: **$0.02**.
- As % of the fee cell: 0.01/2.24 = **0.446%** of the tier-1 fee.
- As % of tier RT cost (all-in ×2, spread 6.25 + slippage included):

| tier | RT cost NFA (42.00 / 67.00 / 92.00) | RT cost offset (41.98 / 66.98 / 91.98) | Δ as % of RT cost |
|---|---|---|---|
| S1 | 42.00 | 41.98 | **0.0476%** |
| S2 | 67.00 | 66.98 | **0.0299%** |
| S3 | 92.00 | 91.98 | **0.0217%** |

- As bp of ES notional (SPEC §1: multiplier $50; at 5200 index pts notional = 5200 × 50 =
  **$260,000**): $0.01/side = 0.01/260,000 = **0.00038 bp**; $0.02/RT = **0.00077 bp**.
  Scale reference: the whole S2 RT cost 67.00 = **2.58 bp** of notional (S1 1.62 bp, S3 3.54 bp) —
  i.e. the divergence is 0.03% of the cost bar it sits in; spread+slippage assumptions
  (62.50 of the 67.00 S2 RT = 93.3%) dominate modeled cost by three orders of magnitude.
- Effect on the G1 gate bar (after-modeled-cost expectancy > 0 at S2): +0.01 on a 33.50/side bar
  = **+0.0299%** — no plausible pass/fail flip, but the number feeding the gate must be the ruled
  one before any adjudication.

## 3. How many baseline sites cite each basis (grep, this worktree, 2026-10-04)

Pattern `20\.99|33\.49|45\.99|23\.49|28\.49` over `FUTURES-OVERNIGHT-PREP-20261003/hypo/es_nq/` +
`FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md`:

| file | offset-basis tokens (lines) | NFA-basis tokens | notes |
|---|---|---|---|
| `esnq_hypotheses.json` | **20 (16)** | 0 | L17 ES + L18 NQ all-in compositions; **6 cost_survival gate cells** at L66/92/143 (ES "S2 33.49") and L170/195/220 (NQ "S2 28.49") |
| `ESNQ_HYPOTHESES.md` | **21 (14)** | 0 | L42/L45 headline all-ins + 12 prose/table sites |
| `RANKING_INPUT.md` | 0 | 0 | cites fee-level `2.24` ×1 (L114, "MODELED, UNDER REVIEW") |
| `SPEC_PB1_ES.md` | 0 | **L101 (law row) + L104 (all-in row: 3 tokens, 21.006/33.506/46.006)** | the frozen law side |
| **Total** | **41 tokens on 30 lines** | SPEC-only | |

Fee-level basis: token `2.24` ×**12** (5 json + 6 md + 1 RANKING_INPUT); `2.247` ×**0** (the family
already re-sourced to corrected values); `2.25` ×**0 as a fee** (2 grep hits in ESNQ_HYPOTHESES.md
are volume multiples "2.256×"/"2.25→" — false positives). So today the offset basis is cited **41
all-in tokens + 12 fee tokens = 53 value sites**, the NFA basis only by the frozen SPEC law line.

## 4. Options and consequences

- **Option A — standardize on NFA 0.02 (SPEC-consistent, conservative floor)**
  - Consequence: all 41 offset-basis all-in tokens + 12 fee tokens in hypo/es_nq become
    superseded-by-ruling (annotated, not edited); modeled floors rise $0.01/side; ES/NQ all-ins
    read 21.00/33.50/46.00 and 23.50/28.50/33.50; SPEC §5 needs **no** basis edit (only the pending
    exchange-cell erratum application after the A7); consistent with A7-SPEC NOTE N-1 conservatism
    (0.02 is also the higher-cost choice).
  - Unblocks: A7 check 8; any future cost-gate adjudication. Can be folded into D2's writing.
- **Option B — standardize on offset 0.01 (account-realistic)**
  - Consequence: matches the corrected IBKR capture basis (worked example; current-epoch reg 0.01)
    and the family's existing composition; floors stay $0.01/side lower; **requires a dated owner
    annotation reversing the SPEC §5 L101 single-source law** (a frozen line currently forbids the
    offset) — i.e. Option B edits the frozen spec's law, Option A does not; the NFA timeline still
    governs the 2014-10-01→2017-12-31 window either way (both bases agree at 0.01 there).
  - Unblocks: same set, with the additional SPEC-annotation step.
- Either way the ruling must land **before** any cost-gate adjudication; nothing scored today
  depends on it (ES blocked by D4; NQ contingent; nothing registered).

## 5. Fail-closed default if undecided

Divergence stays OPEN; both bases coexist (SPEC law vs family composition, $0.01/side apart);
no cost gate may consume either number; A7 check 8 records it unadjudicated.

— Proposals only. FEE-ES raises no gate and grants no GO.
