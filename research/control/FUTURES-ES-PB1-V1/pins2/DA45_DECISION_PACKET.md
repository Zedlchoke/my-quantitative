# DA45_DECISION_PACKET — FUTURES-ES-PB1-V1, lane DA45-GATE6 (Part A: D-A4/D-A5 adjudication)

- Adjudication lane (independent; **no self-ratification**): prior-authority
  hunt + classification of the two remaining declared non-ratified
  implementation pins **D-A4 / D-A5** (the dry-run lane's own wording, quoted
  below). D-A1/D-A2/D-A3 were already ratified by the owner
  (freeze `owner_ratified_pins_law`, owner verbatim "Đồng ý cả ba cách trên");
  D-A4/D-A5 were explicitly **not** part of that ratification
  (A7_PRELAUNCH_V2 finding N-4: *"Declared non-ratified implementation pins
  D-A4 … and D-A5 … remain LOW recorded findings of the dry-run lane … not
  part of the owner's three-way ratification and were not adjudicated here"*).
- Measured at worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`,
  branch `prep/futures-es-reg-20261004`, HEAD **`456dac6bc75f84ea860a977068568f9688053743`**
  (one bare `rev-parse` at start; `git status --porcelain` empty at start —
  every artifact read below is the committed corpus at this HEAD). No other
  git command. No commit/stage/push.
- **Outcome-blindness law honored**: zero quarantined rehearsal numerics read
  or used. The only dry-run artifacts consumed are DRYRUN_REPORT.md
  (pin declarations + findings text), the builder source headers (recorded
  machinery text), and A7 records. Every corroboration below cites FROZEN
  configuration (SPEC/PLAYBOOKS/addenda/ESNQ/freeze), never rehearsal output.
- Machine mirror: `pins2/da45_decisions.json` (same directory).

## 0. The pins under adjudication (verbatim from DRYRUN_REPORT.md L56, sha `97a4ff6a…`)

> **D-A4** — q80/SL windows chain-wide strict-past (not fold-fenced); trading
> fold-fenced. Corroboration: fold-fenced windows would leave F2-F4 eval heads
> trade-free for weeks, contradicting the frozen eval counts.
> **D-A5** — costs booked as USD lines at pinned table values; TP/SL levels
> derive from fill price.

## 1. Executive classification

| pin | question | prior authority on the exact item | classification | owner action remaining |
|---|---|---|---|---|
| **D-A4** | donor-window fencing: chain-wide strict-past vs fold-fenced | **AUTHORITY_EXISTS** — the SPEC's window definitions are complete on their face and nowhere fold-qualified; folds are defined by the same SPEC as an evaluation-only surface | **SPEC-TEXT DISPOSITIVE** | formal acknowledgment only (elevate the adjudicated reading into the scored-run law text); no substantive choice exists |
| **D-A5** | cost booking as USD lines; TP/SL level anchor | **AUTHORITY_EXISTS** — cost half: denomination-dispositive (per-side USD table + RT×2 + stress ladder); anchor half: dispositive by R-multiple semantics + the fill law (the fill is the only transacted entry price in the law) | **SPEC-TEXT DISPOSITIVE** | formal acknowledgment only |

Zero `OWNER_DECISION_REQUIRED` outcomes. Neither pin is a free design choice:
no authority text supports any competing reading, and the dry-run's recorded
implementations match the adjudicated readings exactly (machinery text:
`dryrun_v2_1/dryrun_builder_v2_1.py` module header, sha `00141bf0…`).

## 2. D-A4 — donor-window fencing

### 2.1 The two SPEC texts the dispatch names

| artifact (sha256, prefix) | location | exact wording |
|---|---|---|
| SPEC_PB1_ES r3 `445f7499…` | §3 L73-74 | "điều kiện \|m\| ≥ q80(\|m\|, **trailing-252d, strict-past**) — q80 từ anatomy (NQ dossier H4 refined spec; ES §8-H5), không tune" |
| SPEC_PB1_ES r3 `445f7499…` | §4 L87-89 | "[ERRATUM A7-SPEC-M5] **SL = 1.0 × median của 20 range RTH session liền trước (strict past; close marks era-correct; loại session short/flagged)** — frozen a priori, R=2" |

Both definitions are **complete on their face and carry no fold qualifier**:
- "trailing-252d" is a chain-temporal extent law — the window is the chain's
  trailing sessions. Nothing scopes it to the current fold.
- "20 range RTH session **liền trước**" (immediately-prior) is a chain-
  **adjacency** law. A fold-fenced donor window would have to break adjacency
  at every fold boundary (skip the previous fold's tail, or truncate) — i.e.
  it would contradict "liền trước" rather than leave it unspecified.
- "strict-past" is a time-direction (anti-lookahead) law: the window is the
  chain's past. It adds no fold constraint; it also subtracts none.

### 2.2 The fold system in the same corpus is evaluation-only

| artifact | location | exact wording | role of folds |
|---|---|---|---|
| SPEC_PB1_ES r3 `445f7499…` | §6 L135-136 | "Mọi identity đã chạy vào observed denominator; era-checks = evaluation views; **fold nhân evaluation không nhân identity**" | evaluation multiplier ONLY |
| SPEC_PB1_ES r3 `445f7499…` | §7 L139-143 | "4 folds tuần tự: F1 2010-06..2012-12 · F2 2013-01..2017-12 · F3 2018-01..2021-12 · F4 2022-01..2026-09 (sau EXCLUDE). K1 đo trên 3 era OVN-share … (views)" | eval windows + gate counting |
| SPEC_PB1_ES r3 `445f7499…` | §8 G3/G4 | "G3 ≥ 2/4 folds positive tại S2 · G4 K1 era-sign ổn định" | gate arithmetic |
| PLAYBOOKS_DRAFT r5 `7610ed3c…` | L67 (stand-aside row) | "(iv) **warmup 252d**" — listed under "Đứng ngoài (stand-aside)" | fold-head protection is assigned to the TRADING surface |
| selection_freeze_v2 `cf150e24…` | `fold_structure[].warmup_carve_out` | law field verbatim: "**SPEC_PB1_ES §3/§7: warmup 252 sessions per fold head**"; per-fold positional carve-outs F1 2010-06-07..2011-06-09 · F2 2013-01-02..2014-01-16 · F3 2018-01-02..2019-01-17 · F4 2022-01-03..2023-01-17, each n=252; each fold's `eval_sessions.first` starts exactly at warmup end | the FROZEN config itself fences fold heads via warmup, leaving donor windows chain-wide |
| ESNQ_HYPOTHESES `9f9176e5…` | §0.5 L101-105 | "The PB1-linked OVN pair … **q80-strict-past OVN tail**, CONT vs REV, both tails … remains exactly as specified in the v3 addenda §8-§11" | no fold qualifier |
| ES_DEEPFOUR_V3_ADDENDUM `d18d5422…` | §9 L271, L276 | "condition \|m\| ≥ q80(\|m\|, trailing-252d, strict-past) — q80 from anatomy, not tuned"; "SL = 1.0 × median of prior-20 RTH session ranges (strict past, era-correct close marks, short/flagged sessions excluded)" | identical window law, no fold qualifier |
| NQ_DEEPFOUR_V3_ADDENDUM `e78548a6…` | §9 L292, L300 | "\|m\| ≥ q80(\|m\|, trailing-252d, strict-past)"; "SL 1.0× median prior-20 RTH session ranges (strict past, era-correct marks, flagged sessions excluded)" | identical |

### 2.3 Negative sweep (the ruling that does NOT exist)

`grep -rni "fold-fenc|fold fenc|fenced|fencing"` across every law corpus
directory (FUTURES-ES-V1-PACKET, FUTURES-ES-PB1-V1, FUTURES-DATACONTRACT-
QUAL-V1, FUTURES-DEEPRESEARCH-V2-20261003, FUTURES-BLOCKER-UNLOCK-DEEPFOUR-
20261003, DAYTRADE-PLAYBOOKS-PROGRAM-V1, FUTURES-OVERNIGHT-PREP-20261003,
FUTURES-TEN-HYPO-PREP-20261004) — **every hit is inside the dry-run lane's
own artifacts** (DRYRUN_REPORT, builder module headers/digests, this cycle's
handoffs, and A7 N-4 quotes of them). **No law artifact ever mentions
fold-fencing of donor windows.** The concept enters the record only as the
dry-run lane's negative declaration ("NOT fold-fenced") — i.e., the corpus
contains the chain-wide ruling by completeness and contains the competing
concept nowhere.

### 2.4 Design-consistency corroboration (frozen config only, outcome-blind)

- The frozen warmup carve-outs are **positional, 252 sessions per fold head**,
  and each eval surface starts exactly at its fold's warmup end. This frozen
  structure is coherent under chain-wide windows: fold-head trading protection
  is deliberately supplied by the warmup, so the window law needs no fold
  qualifier. Under fold-fenced windows the warmup would be a **redundant
  second buffer** (≈252+252 trade-free sessions at every F2-F4 head) — a
  design no law text authorizes or even mentions.
- Fold-fenced SL donors would leave the **frozen C4 identity** (and every
  primary, full TP/SL mechanics per SPEC §4) with an **under-filled/undefined
  SL window at each fold head** — a state no law text defines. The chain-wide
  reading is fully defined from the chain's 253rd session onward; it is the
  only reading with no undefined states.
- Note on the dry-run's own corroboration sentence (quoted in §0): its
  strongest form relies on rehearsal-adjacent reasoning; this packet's
  classification does NOT rely on it. The dispositive basis is §2.1-§2.2
  (definition completeness + evaluation-only fold role) plus §2.4's
  frozen-config coherence — all readable before any run.

### 2.5 Verdict, owner text, overturn impact

**authority_verdict: AUTHORITY_EXISTS (SPEC-text dispositive).** The chain-wide
strict-past reading is not a guessed parameter; it is the only reading the
frozen text admits. The dry-run was *correct* to declare a pin (the law never
writes the words "not fold-fenced"), and this adjudication closes that gap.

What remains for the owner (one line, formal only):
> **D-A4**: "Confirmed: q80 and SL-donor windows are chain-wide strict-past
> (trailing-252 computable-|m| / trailing-20 immediately-prior non-short-
> flagged RTH sessions); folds fence TRADING only (frozen per-fold-head
> positional warmup carve-outs + frozen eval windows) — per SPEC §3
> 'trailing-252d, strict-past', §4 'liền trước', §6 'fold nhân evaluation
> không nhân identity'."

Impact-if-overturned (owner ordered fold-fenced windows — NOT recommended,
would be a freeze amendment): the donor-window assembly in the machinery of
record changes (window inputs become fold-scoped); warmup carve-outs become
double-buffered (a new design element); an undefined-state law for
under-filled fold-fenced windows must be written (SL/q80 at fold heads) —
new family definition territory; trade membership across all F2-F4 eval
heads changes; **enumeration invariance holds** (still exactly the frozen
24; only within-identity trade membership moves); G3/K1 fold arithmetic
unchanged; all gate-4 determinism evidence must be regenerated at the new
builder sha.

## 3. D-A5 — cost booking + TP/SL level anchor

### 3.1 Cost half: USD-line booking — denomination-dispositive

| artifact (sha256, prefix) | location | exact wording |
|---|---|---|
| SPEC_PB1_ES r3 `445f7499…` | §5 L95 header | "## 5. **Chi phí MODELED COST (per side, USD)** — sửa review điểm 2+3" |
| SPEC_PB1_ES r3 `445f7499…` | §5 all-in row | "**All-in/side (mặc định NFA 0.02)** \| **S1 21.006 · S2 33.506 · S3 46.006** \| cửa sổ 2014-10-01→2017-12-31 trừ 0.01 (NFA 0.01); **round-trip ×2**" |
| PLAN_futures_es_pb1_v1 (registered) `06140882…` (root plans/, read-only) | §2 | "**Variant A** … = **2.25/side fees**; spread half-turn 6.25 … ⇒ all-in/side **21.00 / 33.50 / 46.00**, RT 42.00/67.00/92.00 (window rows 20.99/33.49/45.99). **Stress ladder ×1.0/×1.5/×2.0 (×1.0 is the gate number)**. … The values 1.386 and 21.006/33.506/46.006 are retired footnote-glue prints — never consumable (COST_FREEZE_ERRATUM law)." |
| A7_SPEC audit (packet) | cost check | "… **S1 21.006 / S2 33.506 / S3 46.006 per side** — matches SPEC exactly; window 2014-10-01..2017-12-31 (inclusive) −0.01" |

Costs are **denominated as per-side USD amounts** in every authority. A
per-side USD amount with an RT ×2 rule and a ×1.0/×1.5/×2.0 stress ladder is
consumable **only** as USD lines booked against the trade (net PnL =
gross − RT cost), with fill prices unadjusted: there is no tick/price-space
cost representation anywhere in the law to consume instead, and multiplying
"prices" by a cost ladder is undefined. The gross identity itself is
USD-space: `dir × (exit − entry) × 50` (mult 50, SPEC §1). **Booking as USD
lines at the pinned table values is the only reading; the SPEC §5 text is
dispositive for the semantics, and the registered plan §2 (Variant A,
COST_FREEZE_ERRATUM) is dispositive for WHICH table values are pinned.**

### 3.2 Anchor half: TP/SL levels from fill price — dispositive by R-multiple + fill law

| artifact | location | exact wording |
|---|---|---|
| SPEC_PB1_ES r3 `445f7499…` | §4 L85-86 | "Entry: bar 1m đầu 08:30 CT (D0) hoặc 09:00 CT (D30) theo hướng arm; **fill = open bar 1m kế tiếp**. Không claim limit/queue (D5)." |
| SPEC_PB1_ES r3 `445f7499…` | §4 L87-89 | "**TP = 2.0 × SL-distance**; [ERRATUM A7-SPEC-M5] **SL = 1.0 × median của 20 range RTH session liền trước** … — frozen a priori, **R=2**" |
| SPEC_PB1_ES r3 `445f7499…` | §4 L90 | "**Same-bar TP/SL**: bar chạm cả hai ⇒ **SL ưu tiên** (giá xấu hơn), deterministic." |
| PLAYBOOKS_DRAFT r5 `7610ed3c…` | L66, L69-71 | "fill = open bar kế"; "TP \| 2.0 × SL-distance [PROVISIONAL R=2]"; same-bar SL priority law |
| DATACONTRACT_QUALIFICATION `df175a2d…` | L135 | "IBKR daily closes **KHÔNG dùng làm fill price**" |

The law defines TP/SL as **distances** and frames them as an **R-multiple**
("R=2": TP sits 2R from entry) — R-multiple semantics are entry-price-relative
by definition. The **only entry price the law transacts at is the fill**
(next 1m bar open; the signal bar's open_0830 is a signal input, never a
transaction price; DATACONTRACT explicitly bars substituting non-fill marks).
Anchoring the levels anywhere else would (i) break the R=2 semantics the SPEC
freezes, (ii) book exits triggered against a level measured from a price that
was never transacted while PnL is measured from the fill — an incoherence no
law text countenances, and (iii) for D30, anchor a 09:01 fill at the 08:30
open. The same-bar touch rule ("bar chạm") compares bar extremes against the
position's levels. No competing anchor appears anywhere in the corpus.

### 3.3 Verdict, owner text, overturn impact

**authority_verdict: AUTHORITY_EXISTS (SPEC-text dispositive; cost half by
denomination, anchor half by R-multiple + fill law).** The dry-run's recorded
implementation (v2_1 builder header: "D-A5 costs applied as USD lines per
side at pinned table values (fill prices unadjusted); TP/SL levels derive
from the fill price per SPEC §4") matches exactly.

What remains for the owner (one line, formal only):
> **D-A5**: "Confirmed: all costs are booked as per-side USD lines at the
> pinned Variant-A table (fees 2.25 / 2.24-in-NFA-window + spread 6.25 + tier
> slippage; RT ×2; stress ladder multiplies USD lines; SPEC §5 values retired
> per COST_FREEZE_ERRATUM), fill prices unadjusted; TP/SL levels derive from
> the fill price per SPEC §4 (R=2 semantics)."

Impact-if-overturned: embedding costs into fill prices would void the pinned
USD table, the RT ×2 arithmetic and the stress ladder (all gate-4 cost
evidence regenerated); anchoring TP/SL at open_0830 instead of the fill would
change every exit on entries with nonzero 08:30→fill drift and break R=2;
**enumeration invariance holds** in both cases (24 identities untouched;
only within-identity trade economics move).

## 4. Consistency statement

Both pins are read-only implementations of definitions the SPEC already
freezes; neither adds, removes, or re-parameterizes any identity. Under both
adjudicated readings the enumeration stays exactly the frozen 24
(`selection_freeze_v2.json` identity_table, byte-exact) and every stage-A
gate input surface is unchanged. If the owner declines to acknowledge either
pin, the status quo is that the reading above stands as adjudicated law-text
implication and the scored run may NOT silently deviate from it — any
different choice is a freeze amendment with gate re-runs (per-pin overturn
impacts in §2.5/§3.3). **CRITICAL flag count: 0.**

## 5. Discipline record

- ONE bare `git -C <worktree> rev-parse HEAD` at start →
  `456dac6bc75f84ea860a977068568f9688053743`; `git status --porcelain` empty
  at start. No other git command; no commit/stage/push.
- Zero network; root repo read-only (root `plans/PLAN_futures_es_pb1_v1.md`
  and root `plans/CYCLE_REGISTRY.json` READ only, never written).
- Quarantine law: zero reads of `dryrun/quarantine*/**` numerics; no
  rehearsal PnL or trade count used anywhere in this packet.
- Write boundary: `research/control/FUTURES-ES-PB1-V1/pins2/**` only
  (Part A) — plus the gate6/handoff surfaces of the same lane's Part B.
- sha256 prefixes cited: SPEC_PB1_ES `445f7499`; DRYRUN_REPORT `97a4ff6a`;
  PLAYBOOKS_DRAFT `7610ed3c`; ES_DEEPFOUR `d18d5422`; NQ_DEEPFOUR `e78548a6`;
  ESNQ_HYPOTHESES `9f9176e5`; DATACONTRACT `df175a2d`; selection_freeze_v2
  `cf150e24`; dryrun_builder_v2_1 `00141bf0`; registered plan `06140882`;
  REGISTRATION_PACKET `2d0d3014`; DONOR_LAW_CARRYOVER `314ae947`.

— End DA45_DECISION_PACKET.
