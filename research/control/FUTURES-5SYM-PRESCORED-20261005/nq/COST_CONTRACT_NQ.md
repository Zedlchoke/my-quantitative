# COST_CONTRACT_NQ — NQ modeled cost contract (all-in RT ladder S1/S2/S3 × 1.0/1.5/2.0; every number MODELED / UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN)

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **NQ**, 2026-10-05. DRAFT-PENDING-OWNER.
- **Labels binding on every number below: MODELED COST / UNDER REVIEW /
  `VERIFIED_VS_ACCOUNT=NOT_RUN`.** The words "measured cost" and "complete cost" are forbidden on
  any output (`esnq_hypotheses.json::cost_law.forbidden_words`, sha256 `68e21c56…6605`).
- Fee A7: **EXECUTED — AUTHORIZED_WITH_FINDINGS, 0 HIGH / 0 CRITICAL unresolved**
  (`research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/fee_a7/A7_FEE_REAUDIT.md`, sha256
  `2c1095d6…11ad`; machine mirror `a7_fee_digest.json`). The A7 adjudicates the fee SOURCES and
  arithmetic; it does NOT choose the basis and does NOT authorize scoring.

## 1. Fee components (NQ row — FULL mapping corroboration; NQ printed verbatim in the IBKR row)

| component | Variant A — NFA basis | Variant B — IBKR offset basis | source (committed bytes) |
|---|---|---|---|
| IBKR commission (Fixed = Tier-1) | 0.85 | 0.85 | `fees_erratum/source/fees_corrected.json` `commission_tiers_common_all_codes` (sha256 `7cd65f25…aca8`); `FEES_CORRECTED.md` §2 (sha256 `006d6372…1bef`) |
| CME exchange fee (E-mini Equity row, NQ verbatim) | 1.38 | 1.38 | RAW HTML `1.38<sup>6</sup>` exactly ×2 (NQ L1694, ES L1706); glued-superscript adjudication; **1.386 is RETIRED — never consumable** (`COST_FREEZE_ERRATUM.md` §1.1, sha256 `cf83bc2d…9ae8`) |
| Clearing | 0.00 | 0.00 | IBKR worked examples print "Clearing Fee USD 0.00" (`fees_corrected.json::excluded_or_unresolved_components`) |
| Regulatory | **0.02** default; **0.01** only 2014-10-01→2017-12-31 (official NFA timeline, single source) | **0.01** throughout (current capture epoch) | `COST_FREEZE_ERRATUM.md` §2 table (the only internally consistent dual-variant statement in the program — A7_FEE_REAUDIT §8) |
| **Fee all-in / side** | 0.85 + 1.38 + 0.02 = **2.25** | 0.85 + 1.38 + 0.01 = **2.24** | same §2 table; DERIVED sums shown explicitly |
| Give-up 0.05 | excluded (waived when IBKR is prime+executing; self-directed assumption, disclosed) | same | `FEES_CORRECTED.md` §4 |

**Delta A−B = +$0.01/side = +$0.02/RT per contract** — applied to NQ exactly as the A7 tabulates.
D3 (= e.4) is an OPEN owner input; fail-closed default if unruled: **Variant A, basis only** (the
NFA-basis RULE inherits; the glued VALUE 1.386 does not — `COST_FREEZE_ERRATUM.md` §3.4).

## 2. NQ-specific execution components (MODELED, assumption D1)

| component | value | basis |
|---|---|---|
| Spread half-turn | **$16.25** | 6.5-tick close proxy, HIGH-BIASED. Arithmetic: committed front-spread census NQ median full spread = **6.5 ticks = $32.50** (`S6_FRONT_SPREADS.json`, committed at ROOT `d8cf8eca`, **not present in this worktree** — read-only root evidence, disclosed); half-turn = 32.50 / 2 = **16.25** [`DERIVED` division; both inputs committed]. Mirrors the ES law (1.0-tick full $12.50 → half-turn $6.25). Carried composition string: "2.24 fees + 16.25 spread half-turn proxy (6.5-tick close proxy, high-biased)" (`esnq_hypotheses.json::cost_law.nq_modeled_all_in_per_side.composition`) |
| Slippage tier S1 | **$5.00/side** | 1 tick × $5.00 (research assumption D1 — NOT a measurement) |
| Slippage tier S2 | **$10.00/side** | 2 ticks × $5.00 (D1) |
| Slippage tier S3 | **$15.00/side** | 3 ticks × $5.00 (D1) |
| BBO / fill / queue | **NOT_RUN** | synchronous quotes absent (D5 law); conservative fill binds: fill = next 1m bar open, no limit/queue claims, close proxies only, SL priority on same-bar TP/SL |

Tick value anchor: 0.25 pt × $20/pt = $5.00/tick (identity arithmetic chain in `SPEC_NQ.md` §1;
the `DATA_READINESS_NQ.md` §1 "$2.50" pointer line is a disclosed non-load-bearing defect,
**P5-NQ4** — no number here consumes it).

## 3. All-in per-side ladder (fee + spread half-turn + slippage; DERIVED sums)

**Window note (Variant A only):** inside 2014-10-01→2017-12-31 the NFA reg drops to 0.01, so A's
all-ins equal B's (23.49 / 28.49 / 33.49) in that window (`COST_FREEZE_ERRATUM.md` §2 window note).

| variant | S1 (/side) | S2 (/side) | S3 (/side) | arithmetic |
|---|---|---|---|---|
| **B — IBKR offset** (2.24) | **23.49** | **28.49** | **33.49** | 2.24 + 16.25 + {5, 10, 15} |
| **A — NFA basis** (2.25) | **23.50** | **28.50** | **33.50** | 2.25 + 16.25 + {5, 10, 15} |

Variants A and B NQ per-side ladders are **tabulated** in `COST_FREEZE_ERRATUM.md` §2 (23.50/28.50/
33.50 and 23.49/28.49/33.49); the component sums above re-derive them exactly. The committed
cost_law ladder (23.49/28.49/33.49) is the **Variant-B** composition.

## 4. Round-trip ladder and stress multipliers (×1.0 / ×1.5 / ×2.0) — DERIVED (RT = 2 × per-side; ladder convention per `CYCLE_LAUNCH_DRAFT.md` §3 stress law)

| variant | RT ×1.0 S1/S2/S3 | RT ×1.5 S1/S2/S3 | RT ×2.0 S1/S2/S3 |
|---|---|---|---|
| **B** | **46.98 / 56.98 / 66.98** | 70.47 / 85.47 / 100.47 | 93.96 / 113.96 / 133.96 |
| **A** | **47.00 / 57.00 / 67.00** | 70.50 / 85.50 / 100.50 | 94.00 / 114.00 / 134.00 |

The ×1.0 after-cost number is the gate number; ×1.5/×2.0 are disclosed robustness views; a survivor
that dies at ×1.5 is disclosed as such, never hidden. No slippage claim beyond the {1,2,3}-tick
tier triple is legal anywhere (double-stress forbidden).

## 5. bp-of-notional conversion (formula + committed anchors; all conversions DERIVED)

- **Formula**: `bp_of_notional = RT_USD / notional_USD`, with `notional_USD = price_level ×
  multiplier($20)`. Equivalently in points: `bp = RT_points / price_level` where
  `RT_points = RT_USD / 20` (S2: 56.98/20 = **2.849 pts** B; 57.00/20 = **2.850 pts** A).
- **Committed anchors** (both recovered from the committed EXPWITCH MDE arithmetic
  `HYPOTHESES_ESNQ_R3.md` §2 field 7: "RT(S2) 2.849 pts = 15.8 bp conservative / 1.1 bp modern" —
  sha256 `9dfe7b12…d288`): era-conservative NQ price ≈ **1,800** (notional ≈ $36,000 ⇒ S2 ×1.0 =
  56.98/36,000 ≈ **15.8 bp**); modern NQ price ≈ **25,900** (notional ≈ $518,000 ⇒ S2 ×1.0 ≈
  **1.1 bp**). Both anchor prices are DERIVED-back from that committed sentence (the underlying
  source tables carry vol anchors, not price anchors); the formula is the binding part, the
  example numbers are illustrative DERIVED views.
- **Power honesty carried**: at S2 ×1.0 the RT cost is ~15.8 bp of a conservative-era notional —
  the same order as family MDEs computed from committed dispersion proxies ⇒ NQ event families are
  power-marginal at realistic n; a null at feasible n is the pre-registered K2-class death, NOT
  evidence of absence (same court finding as `SPEC_6E.md` §9; per-family MDE tables on the
  repaired series are post-freeze arithmetic — NOT_RUN now).

## 6. Never-consumable list (binding on every freeze consuming this contract)

1. **1.386** (glued superscript) — retired by the erratum chain; no NQ number may inherit it.
2. **Stale 21.006-class prints** (ES 21.006/33.506/46.006 and any analog re-derivation of them) —
   historical evidence of the SPEC, never executable cost.
3. **$2.50/tick** for NQ (`DATA_READINESS_NQ.md` §1 pointer-line defect) — inconsistent with the
   committed arithmetic; flagged P5-NQ4; zero numbers in this packet depend on it.
4. Any account-behavior claim — **VERIFIED_VS_ACCOUNT=NOT_RUN everywhere**; no account was read.

— End COST_CONTRACT_NQ. MODELED everywhere; nothing ratified; D3 open; BBO NOT_RUN.
