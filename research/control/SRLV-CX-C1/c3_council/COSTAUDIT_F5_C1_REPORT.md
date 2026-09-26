# COSTAUDIT_F5_C1 — Cost/Execution audit report (C3 council, SRLV-CX-C1)

- Lane: cost-execution-auditor. Date: 2026-09-26.
- Worktree verified: `/Users/hoangminhlong/my-quantitative/.worktrees/srlv-cx-c1/integration`,
  branch `orca/srlv-cx-c1-integration`, HEAD `d3f063a05338e498912a16d4678d4451fd0cb838`.
- No PnL exists; this is a cost-feasibility audit of PROPOSAL_P1.md (P1-A, P1-B) and
  PROPOSAL_P2.md (P2-M1, P2-M2) against `plans/PLAN_srlv_program_v1.md` §7.2 (crypto
  cost contract) and §10 (K-COST), and `C1_DATAGATE_VERDICT.md` (what is MEASURED vs
  NOT_RUN). Fail-closed: where measurement is missing, no optimistic number is filled.
- Authority of this lane: **BLOCKED power when a required cost component is missing**
  (K-COST: "ceiling âm hoặc cost auditor BLOCKED vì thiếu thành phần trọng yếu").

---

## 1. Layer discipline (fee / funding / spread: measured vs declared vs NOT_RUN)

| Component | Contract layer (§7.2) | P1-A | P1-B | P2-M1 | P2-M2 |
|---|---|---|---|---|---|
| Fee 5 bps + 1 adverse tick per side | **DECLARED** (venue tier floor + frozen CHR3F convention; measured only after Q-8 validation vs fills) | labeled DECLARED (§8) — correct, never claimed measured | labeled DECLARED — correct | labeled DECLARED — correct | labeled DECLARED — correct |
| Funding | **MEASURED** per settlement while held; structural ≡ 0 for flat-by-settlement fixtures | base book ≡ 0 (flat-by-settlement fixture) ✓ structural, not imputed; stress arm = MEASURED path BTC/ETH only ✓ | same as P1-A ✓ | MEASURED per settlement held (BTC/ETH); SOL/BNB correctly excluded (no arms) ✓ | MEASURED on BTC/ETH arms; SOL/BNB arms structural ≡ 0 flat-by-settlement ✓ |
| Spread census (bookTicker/aggTrades, hour-of-fill) | **NOT_RUN** (C1 verdict); missing ⇒ BLOCKED for mechanisms that *need* it | NOT_RUN disclosed, `FILL_QUALITY_CLASS_declared` ✓ | NOT_RUN disclosed ✓ | NOT_RUN disclosed ✓ | NOT_RUN disclosed ✓ |

No proposal labels the declared fee/tick book as measured. Funding layering is
correct everywhere, including the SOL/BNB funding-block (unstaged) that P1-A
already self-declares for stress arms. The single layering defect class is in the
**numbers** inside the declared book, not the labels — see §2.3.

**Spread-materiality ruling (per proposal, entry style = market-at-open taker in
all four):**
- **BTC/ETH fills**: measured tick burden is 0.005–0.12 bp per tick (§2.2). Even a
  50× spread widening over the 1-tick convention costs ≤ 0.3–6 bp — inside the
  ×1.5/×2.0 declared bands and dominated by the 10 bp fee floor. The census is
  therefore **not ceiling-flipping on BTC/ETH**: it is a **GO-gate** (Q-8 tier-floor
  validation against actual fills) and a declared limitation, not a BLOCK.
- **SOL/BNB fills**: tick burden reaches 0.16–0.94 bp/tick in the 2020–21
  low-price corners (§2.2); a 10–50-tick spread at those prices — typical thin-book
  behavior — is 1.6–47 bp, i.e. the same order as the entire claimed premium. The
  1-adverse-tick convention **cannot bound fill cost there without measurement**.
  ⇒ **CEILING_UNDECIDABLE_MISSING_SPREAD for every SOL/BNB arm** (P1-A, P1-B,
  P2-M2): **BLOCKED_MISSING_COMPONENT** until the fill-hour spread census is staged,
  unless the council removes SOL/BNB from the allowed scored panel (the identity
  then mass-tests on the BTC/ETH panel only).

---

## 2. Measured cost anchors (new measurements by this lane, 2026-09-26)

### 2.1 Funding path (MEASURED; BTC fapi parquet N=7,643; ETH Vision zips N=7,305; both 8h-cadence uniformly, 0 duplicate timestamps)

| Anchor | BTCUSDT | ETHUSDT |
|---|---|---|
| Settlements 2020-01..2026-08 | 7,305 | 7,305 |
| Mean per settlement | +1.0774 bp | +1.2737 bp |
| **Annualized mean (8h cadence)** | **+11.80 %/yr** | **+13.95 %/yr** |
| Median per settlement | +0.93 bp | +1.00 bp |
| Share negative (full sample) | 14.11 % | 13.83 % |
| Share negative, bear 2022 | 22.1 % | 34.2 % |
| Share negative, 2022-H1 | 25.8 % | — |
| **Worst settlement** | **−30.00 bp** (2020-03-13 08:00 UTC) | **−35.63 bp** (2021-05-19 16:00 UTC) |
| Settlements worse than −10 bp | 3 of 7,305 | 3 of 7,305 |
| p5 / p95 | −0.52 / +4.69 bp | −0.52 / +5.66 bp |

Reconciliation with the bear-recon precedent quoted in the proposals: BTC
annualized 11.80 %/yr **matches "11.798" exactly**; worst −0.30 %/8h **matches
exactly**; downtrend negative share lands 22.1–25.8 % depending on window
definition (precedent "~24.7 %" is in-band). One correction: the **ETH** worst
settlement is −35.63 bp, not −30 bp — P2-M1/M2 quote the BTC figure as "the"
stress tail.

Usage: long-hold baselines pay the measured mean (+11.80 %/yr BTC, +13.95 %/yr
ETH) on the `FUNDING_PATH_STRESSED` book. Event arms that cross settlements:
expected per-trade funding magnitude ≤ median × P(cross) (≈ 0.9–1.0 bp × ≤1 for
P2-M1's 2–8-bar holds; ≤ 0.5 bp for P2-M2's ≤4-bar holds), sign side-dependent ⇒
dual book with received/paid separated is mandatory (both proposals already
pre-register Q-14). Tail: a trade crossing one of the 3 worst settlements absorbs
−28…−36 bp — see §3 flip condition.

### 2.2 Tick sizes — MEASURED from staged klines

Method (as dispatched): tick = GCD of exact scaled (×1e10) **price increments of
successive closes** over the last ~5,200 bars (last 8 monthly files per pair),
cross-checked two ways: (a) GCD over price levels (same result per pair), (b)
early-sample window (first ~2,500 bars) to detect venue tick-regime changes. All
four bar counts reproduce the C1 datagate exactly (58,440 / 58,440 / 52,145 /
57,472; SOL 2 gap bars).

| Pair | tick (last ~5.2k bars) | tick (first ~2.5k bars) | min low in sample | worst tick burden, bp/tick/side = tick/price×1e4 |
|---|---|---|---|---|
| BTCUSDT | **0.1** | 0.01 | 3,621.81 | 0.028 (early era: 0.01/3,621.81) |
| ETHUSDT | **0.01** | 0.01 | 84.23 | **0.119** (2020-01 floor) |
| SOLUSDT | **0.01** (not 0.001) | 0.0001 | 1.069 | **0.936** (fail-closed: coarsest tick 0.01 at $1.07 floor) |
| BNBUSDT | **0.01** | 0.001 | 6.236 | 0.160 |

The dispatched guess "SOLUSDT 0.001?" is **refuted by the staged record**: the
modern SOLUSDT grid is 0.01. Fail-closed convention for all cost arithmetic: use
the **coarsest** tick observed anywhere in the pair's staged sample at the
**lowest** observed price (overstates the modern-era burden for SOL/BNB; never
understates).

### 2.3 Corrections to numbers the proposals disclose (labels are fine; figures are not)

| Proposal claim | Measured | Disposition |
|---|---|---|
| P1-A §8: "SOL ~1 bp/tick at ~$100" | 0.01/100×1e4 = **0.01 bp/tick** | overstated ~100× |
| P1-A §8: "up to ~50 bp/tick in the 2020 low-price floor" | **≤ 0.94 bp/tick** (coarsest tick 0.01 at $1.07) | overstated ~50×; directionally right (material corner), magnitude wrong |
| P2-M2 §8: "2 ticks ≈ 0.5–0.7 bps on SOL/BNB" | SOL **0.02 bp** (modern mean) to **1.87 bp** (fail-closed worst corner); BNB 0.03–0.32 bp | not reconcilable per-pair; freeze must carry the measured per-fill-time table |
| P2-M1 §2: "2 ticks ≈ 0.05 bps on BTC" | 0.055 bp worst corner | ✓ correct |
| P1-A §3 / P2-M1 §2: funding anchor "11.798 %/yr", "worst −0.30 %/8h", "median ~1 bp" | 11.80 %/yr, −30.00 bp, 0.93–1.00 bp | ✓ correct for BTC; **ETH worst is −35.63 bp** — quote per pair |
| P1-A §2: "conditioning on settlement adjacency (≤ ~2 % of hours)" | W_k per §5 = 5 close-times/settlement × 3 = **15/24 = 62.5 % of hours** (even the narrowest reading [S, S+3) gives 37.5 %) | **internal inconsistency ~30×**; the "tail selection" premise of the premium estimate does not survive the proposal's own window definition. Design-level: referred to council (also weakens the "new information layer" claim and the ±4h placebo, whose shifted windows overlap the anchor windows on 1–2 bars per settlement) |

---

## 3. F-5 cost-survivability ceiling (§7.1.4/§7.2.5: expected gross premium per hold ≥ full RT stress cost, on the measured distribution; ceiling âm ⇒ VETO before scoring)

Convention: RT cost = 2 sides × (5 bps fee + 1 tick at fill price); ×k = k × the
declared per-side cost (uniform band on fee+tick). Tick term is the fail-closed
worst-corner from §2.2. Funding term added only for funding-exposed arms.

**Round-trip cost book, bps:**

| Pair | base | ×1.5 | ×2.0 | P2-spec stress (fees×2 + 3 ticks) | + worst settlement (funding arms) |
|---|---|---|---|---|---|
| BTCUSDT | 10.06 | 15.08 | 20.11 | 20.19 | **50.19** |
| ETHUSDT | 10.24 | 15.35 | 20.47 | 20.83 | **56.46** |
| SOLUSDT | 11.87 | 17.81 | 23.74 | 26.55 | n/a (flat-by-settlement ≡ 0) |
| BNBUSDT | 10.32 | 15.48 | 20.65 | 21.13 | n/a (flat-by-settlement ≡ 0) |

Funding-exposed base-book add-on: ≤ 1 crossed settlement typical ⇒ +0.93 bp (BTC)
/ +1.00 bp (ETH) median-case.

**Per-proposal ceiling verdicts (claimed gross per trade vs the book above):**

| Proposal | Claimed gross/trade | Verdict | Arithmetic |
|---|---|---|---|
| **P1-A** SETTLE-SWEEP-ABSORB | 10–30 bps | **BTC/ETH: CEILING_SURVIVABLE** (K-COST-marginal by its own design). **SOL/BNB arms: CEILING_UNDECIDABLE_MISSING_SPREAD ⇒ BLOCKED** | claim lower edge == base cost (zero net at 10 bps); claim clears ×1.5 (15.08/15.35) only in its upper half; P1-A's own pre-registered ceiling "median gross ≥ stress RT (~17 bp)" is consistent with measured ×1.5. SOL/BNB base 10.32–11.87 vs claim floor 10 ⇒ lower band below cost there too; and fill cost unbounded without census (§1) |
| **P1-B** SETTLE-BREAK-CASCADE | 15–50 bps | **BTC/ETH: CEILING_SURVIVABLE** (marginal at the bottom edge). **SOL/BNB arms: CEILING_UNDECIDABLE_MISSING_SPREAD ⇒ BLOCKED** | claim clears base everywhere (15 > 10.24); bottom edge 15 ≈ ×1.5 (15.08/15.35); clears ×2.0 above 20.5 ⇒ survivable conditional on F-g |
| **P2-M1** PDSR | 20–40 bps; own ceiling "≥22–25 base, ≥30 stress" | **CEILING_SURVIVABLE** (BTC/ETH only — SOL/BNB correctly has no arms) | clears base (10.06–10.24 + ≤1 bp funding) with 2–4× margin; straddles fee-stress (20.19/20.83 + median funding) at its bottom edge. **Flip condition:** against the full §7.2.2 stress line including worst-settlement funding (50.19/56.46) the claim band 20–40 is **negative**; if the freeze pins the per-trade ceiling at worst-settlement-inclusive stress, verdict flips to **CEILING_NEGATIVE_VETO**. On the measured distribution the tail is rare (3 settlements of 7,305 worse than −10 bp; P(trade crosses one) ≈ 0.01–0.1 %), so the distribution reading survives — the council must pin the ceiling convention **before scoring** |
| **P2-M2** WSA | 15–40 bps; same ceiling discipline | **BTC/ETH arms: CEILING_SURVIVABLE** (marginal). **SOL/BNB flat arms: CEILING_UNDECIDABLE_MISSING_SPREAD ⇒ BLOCKED** | BTC/ETH: claim clears base, lower half (15–20.8) below fee-stress ⇒ conditional F-g. SOL/BNB: claim clears base (10.32–11.87) but SOL fee-stress reaches 26.55 at the worst corner AND the fill-hour spread is unmeasured where tick burden is largest ⇒ blocked per §1 |

Standing condition on every SURVIVABLE verdict: the freeze-time F-g test must show
**measured median gross/trade ≥ the stress RT on the anchor's own fill
distribution** (§7.1.4); claimed bands are not evidence. No proposal may quote a
GO before the spread census validates the 5 bps tier floor (Q-8).

---

## 4. Turnover sanity vs the ≥100-closed-RT power floor (paper census — event counts only, no fills, no PnL, no backtest; counts are UPPER bounds: one-position-per-pair dedup not applied)

Census implemented exactly per each proposal's observable definitions (P2-M1:
prior-UTC-day extreme close-through + reclaim back inside range; P2-M2: rolling
168h shelf close-through + acceptance, SOL/BNB under the 9-hour admissible-entry
mask; P1: N=6 pivot confirmation, intact-level bookkeeping by first far-side
close, 5-bar settlement windows W_k (open hours {S−2..S+2}, S∈{0,8,16}),
0.25×ATR24 buffers, P1-B break = first far-side close beyond buffer (the only
candidate once "intact entering bar" is enforced)).

**P1-A (reclaim events, per direction):**

| Pair | long | short | /yr (direction) | thinnest fold cell |
|---|---|---|---|---|
| BTCUSDT | 1,875 | 1,758 | ~264–281 | F1 long 308 |
| ETHUSDT | 2,085 | 1,769 | ~265–313 | F1 short 306 |
| SOLUSDT | 1,519 | 1,425 | ~239–255 | F1 long 94 |
| BNBUSDT | 1,794 | 1,548 | ~236–273 | F1 short 283 |

**P1-B (first-far-side-close-beyond-buffer events, per direction):**
BTC 1,380 L / 1,560 S; ETH 1,487 L / 1,527 S; SOL 1,157 L / 1,202 S; BNB 1,334 L
/ 1,316 S. Thinnest fold cell: SOL F1 long 102.

**P2-M1 (reclaim events; expansion-filtered = the anchor's absorption subset):**
BTC raw 942 up / 831 dn, expansion-filtered **656 / 613**; ETH raw 920/797,
filtered **646 / 588**. The proposal's own event-rate claim ("1–2/pair/month ⇒
80–160 events/pair over the panel") is ~10× conservative vs the census ⇒ the
feared NOT_RUN_THIN death is **unlikely on BTC/ETH**. Sweep vs acceptance split
measured: 9,179 close-throughs up on BTC of which 8,233 accepted, 942 reclaimed —
consistent with the M1/M2 disjointness design.

**P2-M2 (acceptance events):**
BTC 569 up / 341 dn; ETH 678 / 345 (unmasked); **SOL masked 247 / 157; BNB masked
282 / 142** (~38 % hour mask, matching the proposal's disclosed 9/24). Claim
"10–25/pair/year" vs measured ~64–136/pair/yr — again conservative.

**Flags:**
- NOT_RUN_THIN risk **LOW** on BTC/ETH for all four proposals (≥5× floor even
  after a 50 % dedup haircut).
- NOT_RUN_THIN risk **MEDIUM** on **SOL/BNB short-side masked arms of P2-M2**
  (142–157 raw vs the 100 floor, dedup unquantified without the backtest) — and
  those arms are already BLOCKED on spread (§3), so the practical exposure is
  limited.
- Per-fold cells below 100 exist (SOL F1 long 94 for P1-A; P2-M2 SOL/BNB F1 dn
  16–19): legal if the pre-registered floor is per pair per direction (F-h as
  written), but the pooled-panel adjudication must not be used to rescue a
  per-pair row the floor kills — as pre-registered, pooling is adjudication
  carry, not selection.

---

## 5. Missing components the freeze must record (DECLARED bands; BLOCKED items marked)

1. **BLOCKED — fill-hour spread census** (bookTicker/aggTrades at the actual fill
   hours; coverage-verified): required for every arm, **ceiling-flipping
   (BLOCKING) for all SOL/BNB arms** of P1-A, P1-B, P2-M2; GO-gate + Q-8 tier-floor
   validation for BTC/ETH arms.
2. **BLOCKED-carryover — SOL/BNB funding series** (unstaged): already
   NOT_RUN_BLOCKED_PENDING_STAGING in C1; consistent — P1-A/B SOL/BNB stress arms
   self-blocked; P2-M2 SOL/BNB arms are lawful only as flat-by-settlement.
3. **BTC funding dual-source cross-check** (fapi vs Vision zip): NOT_RUN (BTC
   Vision funding zips not staged). C1 assigns it to this lane "if mechanisms hold
   across settlements" — P2-M1 and P2-M2 BTC/ETH arms do ⇒ required **before any
   GO** on those arms; the freeze may proceed on the single-source measured path
   with the dual book, provided the cross-check is a named GO gate.
4. Latency (decision close → next-open fill): **DECLARED_UNMEASURED**, folded
   into ×1.5/×2.0.
5. Outage / gap-reopen at the settlement boundary; miss-one-settlement band:
   **DECLARED** (P1-A/B declare it; this audit requires it for P2 arms too).
   SOL's 2 disclosed gap bars: no-fill rule already pinned in C1 (fail-closed) —
   re-affirmed.
6. Adverse selection at sweep/acceptance bars (fill quality beyond quoted
   spread): **DECLARED_UNMEASURABLE** on klines; partially detected by the
   pre-registered delay-1 falsifier; folded into the bands.
7. Funding-cadence regime change (venues historically move 8h→4h in stress):
   **DECLARED** band; both staged series are 8h-uniform today (7,643 / 7,305 rows,
   all `funding_interval_hours = 8`). Ties into the PIT lane's F-GRID gate for
   flat-by-settlement arms.
8. **Flat-boundary convention pin (P1-A/B):** entries may occur as late as open
   S+6 while the pre-registered flat exit is "open of the last bar whose close
   precedes S_{k+1}−2h" — for late entries the rule as written yields zero/negative
   hold, and an exit AT the S_{k+1} open would break the structural funding ≡ 0
   claim. Must be pinned as: exit strictly before the settlement print, events
   whose flat-exit precedes the entry open are **skipped** (corroborates the PIT
   lane's F-1 defect and its fail-closed resolution). Structural funding ≡ 0 holds
   only under that pin.
9. Fee tier floor (5 bps) vs actual fills (Q-8): pending the census; not
   substitutable by any current measurement.

---

## 6. Verdict summary

| Proposal | Verdict (proposal level) | Ceiling verdict | Blocked arms | Power |
|---|---|---|---|---|
| P1-A | **PASS conditional** | CEILING_SURVIVABLE (BTC/ETH, conditional on F-g) | SOL/BNB arms BLOCKED_MISSING_COMPONENT (spread census) | LOW thin-risk (BTC/ETH & SOL/BNB) |
| P1-B | **PASS conditional** | CEILING_SURVIVABLE (BTC/ETH, conditional on F-g) | SOL/BNB arms BLOCKED_MISSING_COMPONENT (spread census) | LOW thin-risk |
| P2-M1 | **PASS conditional** | CEILING_SURVIVABLE (BTC/ETH; **flip to CEILING_NEGATIVE_VETO** if the freeze pins the per-trade ceiling at worst-settlement-inclusive stress — claim 20–40 < 50.19/56.46) | none (SOL/BNB correctly absent) | LOW–MEDIUM (expansion-filtered 588–656/direction raw) |
| P2-M2 | **PASS conditional** | CEILING_SURVIVABLE (BTC/ETH, conditional on F-g) | SOL/BNB arms BLOCKED_MISSING_COMPONENT (spread census); MEDIUM thin-risk on their short side | BTC/ETH LOW |

Fail-closed defaults if the council takes no action: SOL/BNB arms are excluded
from the allowed scored panel (block stands); the ceiling convention for
funding-exposed arms must be pinned before any scored run; no GO on any arm before
the spread census (BTC/ETH) and the BTC funding cross-check (funding-exposed arms).

---

## 7. Commands run (reproduction; all read-only; light jobs, no heavy lock taken)

1. `pwd; git -C <worktree> branch --show-current; git -C <worktree> rev-parse HEAD`
2. Funding anchors: python (root `.venv`, pandas 3.0.5) over
   `research/control/SRLV-CX-C1/data_local/funding_events.parquet` and
   `data_local/vision/fundingRate_um_ETHUSDT/*.zip` (80 zips): per-settlement
   distribution, negative share, worst, annualized (×1,095), per-year, bear-window
   variants (2022, 2022-H1, 2021-11..2022-12).
3. Ticks: GCD of ×1e10-scaled successive close increments over the last 8 monthly
   kline zips per pair (~5,832 bars; also first 3 months), cross-checked with
   GCD-over-levels; min-low per sample for burden.
4. Event census: vectorized python over `/tmp` parquet caches built from the
   staged kline zips (counts only): P2-M1 daily-extreme sweep/reclaim
   (± expansion filter), P2-M2 rolling-168h break/acceptance (± 9-hour mask on
   SOL/BNB), P1 pivot machinery (N=6 strict both sides, intact-by-first-far-side-
   close, settlement windows, 0.25×ATR24 buffers) — no PnL, no fills, no exits.

## 8. Known limitations

- Census event counts are upper bounds (no one-position dedup, no fold force-flat
  skips); the ≥100-RT floor verdicts are therefore optimistic-side only in count,
  never in cost — costs here are fail-closed everywhere else.
- The census is this lane's own re-derivation of the proposal observables, not the
  frozen implementation; the freeze fixtures (PIT lane F1–F7) adjudicate the real
  counts.
- Tick measurement is on the staged kline record; a venue tick change inside a
  sampled month would be averaged into the GCD, not dated. Fail-closed coarsest-
  tick convention covers this.
- The ceiling verdicts compare CLAIMED gross bands against MEASURED cost books;
  measured gross medians do not exist before the trial freeze (by law) — F-g is
  the binding test, this audit only decides whether the ceiling is decidable now
  and what may block it.
- ETH funding comes from Vision zips, BTC from the bear-recon fapi parquet (sha
  manifest in `data_local/funding_sha256.json`); cross-source consistency is
  asserted only via the precedent reconciliation (§2.1), not a row-level
  cross-check (component 3 above).
