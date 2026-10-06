# OWNER_DECISION_PACKET — FUTURES-SIX-SCORED-GATE-PREP-20261004

- **NOTHING HERE IS RATIFIED BY THIS THREAD.** The owner's 2026-10-04
  speech ("Tôi cho phép thử thêm" / "thử NQ với lại ES" / "còn 4 mã forex
  thì cũng thử luôn đi, nếu mà có") was consumed as PREP-to-gate
  authorization only — including executing the fee A7 audit — and is NOT a
  typed GO, NOT registration, NOT PB2/PB3 lift, NOT a cap change.
- Fail-closed defaults below apply wherever a slot stays empty.

## Interpretation ruling the owner may override (one line)

This thread read the speech as authorizing the fee A7 EXECUTION. The audit
ran clean (0 HIGH/CRITICAL). If the owner disagrees with that reading,
the artifacts remain valid audit evidence but D2 stays open pending
explicit ratification — no scored cell has consumed anything either way
(0 trials exist).

## OD-1 — Cycle scope for the FIRST scored run (pick one; recommended first)

| Option | Scope | IDs | Signatures it requires | Consequence |
|---|---|---|---|---|
| **CYCLE-1 `FUTURES-ES-PB1-V1` (RECOMMENDED)** | ES, PB1 only | **24** (no cap change) | **OD-2 D3 signature (EXPLICIT — no silent default)** + registration + prelaunch A7 + typed GO | Earliest lawful scored run; zero new-family risk; NQ/FX follow in later cycles |
| CYCLE-1b ES+NQ | ES PB1 24 + NQ option NQ-A/B/C/D | 46 / 53 / 60 / 67 | OD-2 + **OD-3 (D9)** + NQ ceiling + registration + A7 + GO | One registration covers both; slowest single blocker = D9 |
| CYCLE-0 all-6 | maximal | see budget tables | OD-2 + OD-3 + OD-4 (D4 cap if ES>24) + **OD-5 (PB2)** + **OD-6 (PB3)** + OD-7 ceilings + registration + A7 + GO | Lawful but couples ES to the slowest rulings; NOT recommended |

## OD-2 — D3 fee basis (+ e.1-e.4 sub-rulings) — **REQUIRED, EXPLICIT, before CYCLE-1 freeze** (see `synth/COST_FREEZE_ERRATUM.md`)

Exchange cell 1.38 is EVIDENCE-SETTLED (glued 1.386 retired — RAW-HTML
`1.38<sup>6</sup>` ×2, footnote-6 "$1.30 spread orders", IBKR worked
example exact; A7 §2-§4). The ONLY choice is the regulatory basis:

| Option | Regulatory basis | Fee/side (0.85+1.38+reg) | ES all-in/side S1/S2/S3 (+6.25 spread +12.5/25/37.5 slip) | RT S1/S2/S3 |
|---|---|---|---|---|
| **A** | NFA 0.02/side; 0.01 only 2014-10-01→2017-12-31 | **2.25** | **21.00 / 33.50 / 46.00** (window: = B's row) | 42.00/67.00/92.00 |
| **B** | IBKR captured offset 0.01 throughout | **2.24** | **20.99 / 33.49 / 45.99** | 41.98/66.98/91.98 |

- **Stale SPEC print 21.006/33.506/46.006 is NEVER consumable** (frozen
  historical evidence of the SPEC only; six-adopt packet's Variant-A line
  superseded by the erratum).
- The old "silence ⇒ SPEC §5 binds" default is WITHDRAWN as an operating
  rule: its only lawful reading was "Variant A basis × corrected 1.38",
  and the packet now requires the explicit signature instead
  (fail-closed). **CYCLE-1 is BLOCKED_COST_FREEZE until this lands.**

e.1 (FX fee alias PARTIAL) · e.2 (US-entity basis) · e.3 (NYMEX epoch
rule) — each may be signed "accept as tabulated" (A7 documents all
three; none blocks an ES cycle).

## OD-3 — D9: canonicalize NQ cache_v3 + cease-guard standing law

Evidence complete and verified (66 rolls, cg variant byte-identical,
crash roll exact, deprecated v2 untouched). Signature text is in
`FUTURES-SIX-ADOPT-PREP-20261004/adopt/D8_D9_DECISION_SHEET.md`. Blocks
every NQ scored path; blocks RMM Role-B 6J/6A legs.

## OD-4 — D4 ES cap amendment (ONLY if scope > 24)

Options with exact arithmetic in `budget/IDENTITY_TABLES.md`: ES-1 = 35 ·
ES-2 = 46 · ES-3 = 60 · ES-4 = 67. Each >24 line is a signed amendment,
never silent. CYCLE-1 (PB1-only) needs NONE.

## OD-5 — PB2 lift (6E/6B) | OD-6 — PB3 lift (6A) + D8

Lift instruments: FX options FX-A/B/C (44/66/96) + J-A/B/C (29/36/33-40);
6A contingency 26 (needs PB3 + D8 tick-era signature). Until signed: 6E/6B
stay HOLD, 6A stays PARK — recorded plainly.

## OD-7 — Ceilings + two counting rulings (needed at any FX/NQ/6J freeze)

- NQ ceiling (22/29/36/43) · 6J ceiling (29/36/33-40) · FX ceiling
  (44/66/96 CONV-D or census-native 32/48/72 — the option must name which).
- Clock-only shadow counting: reading (a) inside-family (default used in
  the tables) vs (b) additive — signature must name one.
- Placebo ≥100-seed expansion: EMPTY owner ruling (single-seed/single-delay
  ES precedent binds otherwise).

## The GO phrase (exact, typed, at the registered cycle's own gate, AFTER cost-freeze signature + registration + prelaunch A7 + dry-run)

`GO <REGISTERED-CYCLE-ID> SCORED EXECUTION`

Early/paraphrased GO = intent only, dies unconsumed. Two-key completion:
key 1 prelaunch A7 authorized (0 HIGH/CRITICAL unresolved); key 2 the
phrase above, exact match, recorded `auth/GO_RECORDED.json`.

## Minimal decision sentence (if the owner answers only one thing)

> "D3 basis = [A|B] (A: 2.25/side, 21.00/33.50/46.00 · B: 2.24/side,
> 20.99/33.49/45.99). Chọn CYCLE-1 FUTURES-ES-PB1-V1 (PB1-only 24), và
> tôi đăng ký cycle + gõ GO đúng mẫu ở gate."

**CYCLE-1 remains BLOCKED_COST_FREEZE until the D3 half of that sentence
is signed** (COST_FREEZE_ERRATUM §4).

— End OWNER_DECISION_PACKET.md. Slots empty; nothing self-ratified.
