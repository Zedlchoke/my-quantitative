# A7_RECON_AUDIT — fresh-context audit of the NO_ELIGIBLE_PROPOSAL close

A7 · 2026-09-23 · verdict: **CONFIRM_WITH_FINDINGS** (closure stands; 7 findings, 0 blocking). Start HEAD 66d58e2a…; audit HEAD 6fdbd00a…; heavy lock HELD_PROVEN by CRYPTO-HISTORICAL-REPLICATION-3F-V1 (pid 77456) — inspected, never acquired; light jobs only; no commits. Canonical recompute: `audits_a7/a7_recompute.py` → `a7_recompute_out.json` (all numbers below A7-recomputed from primary data).

## 1. Recomputed decisive numbers vs A4 claims

| quantity | A4 | A7 recompute | match |
|---|---|---|---|
| B θ-signals raw / in-gate | 425 / 350 | 425 / 350; gated set == a4_B_trades.sig_i exactly | EXACT |
| clusters (12h merge) | 13; top-1 91.1%; top-3 95.1% | 13 / 0.9114 / 0.9514; top-1 = 2020-03-12 11:00 → 2020-03-20 01:30 UTC | EXACT |
| 350 matched pairs | −4.55pp; worse 68.6% | −4.34pp; worse 64.0% (control def n=7,246 vs their 12,753 — F-4) | DIRECTION+MAG |
| traded short fwd | −4.87%/−1.58%; excl-COVID −1.54/−1.33 | −4.87/−1.58; excl-COVID −1.54/−1.33 | EXACT |
| class-7 premium LEVEL rho | −0.418 / −0.515 ev | −0.4181 / −0.5146 (prem=(last−index)/index, gated n=140,160 = A4's n) | EXACT |
| construction identity | S vs fast prem −0.684 | −0.6831 (EMA 288=24h; "12h" label → −0.6622, F-3) | EXACT at 24h |
| class-7 fade \|z\|>2 rho | +0.369 / +0.542 | value not reproduced; best analogues +0.36–0.37 ev (low-side z, 576–1152w), gated ≤0.10 | direction OK (F-3) |
| A entries / confirming / fakeouts | 284 / 34 / 250 | 284 / 34 / 250 (independent state machine) | EXACT |
| A median conf lag | 3.5 bars | 3.5 | EXACT |
| A max full-grid \|Pearson\| | 0.151 (honest PASS) | 0.1514 | EXACT |
| census (trim 153) | 2932/6772/0.7365/0.000137/TU 6371 | identical incl. TU 6371 | EXACT |

A2 re-probes (keyless): um liquidationSnapshot 404 @2020-06, 2021-06, 2019-10, daily 2020-03-12 → zero-coverage
CONFIRMED. 5m klines 200 @2020-01 & 2026-08 CONFIRMED. fundingRate 2019-12 404 / 2020-01 200 CONFIRMED.
ANCESTRY_TABLE spot-checks vs FAMILY_FAILURES.jsonl (rows #2,3,7,8,9,12,13 + RSM-V1): all quote-match, 0 misquotes.

## 2. Process law — CLEAN
Boundary: lanes wrote only under the recon dir + their handoffs. plans/ mtime 21:14 and HYPOTHESIS_LEDGER
20:49 = controller commit 675af1cb (foreign-cycle closeout, its authority; ledger git-clean vs HEAD).
wayfinder unmodified (FAMILY_FAILURES mtime 17:52 predates recon). No S1/sec.gov traces. DESCRIPTIVE_EVENT_
STUDY law holds: fwd_last/short_fwd are raw forward returns — no fees, funding, or sizing in A4's study.
A3 outcome-blindness plausible: predates A4 (20:41 vs 20:51+), inputs = A2 artifacts + ancestry statuses only,
no PnL-derived constants (θ=12bps is the declared cost floor). A4's fee-drag finding on A3 is disclosed, not hidden.

## 3. Verdict logic — CORRECT
A: FICTIONAL_COUNTERPARTY is the right category — the "compelled cohort" is defined on the program-internal
PSV1 label (nobody external is compelled by it), and A's entry bar coincides with the SMA-lens flip (rho +0.151),
so A doesn't front-run lens books, it is one; program G6 timing-kill on the same label corroborates. Power floors
faithful: A 34≥30 (barely, as stated); B 350≥40 met on A3's preregistered unit (F-2 on A4's extra cluster
convention). No proposal survives: B is dead on reproduced sign-flip + reproduced class-7 LEVEL/identity
(|rho| 0.42–0.68 ≫ 0.20). NO_ELIGIBLE_PROPOSAL stands.

## 4. Findings (0 blocking)
- **F-1 MEDIUM-LOW**: A4 §1/§5 fee-drag comparison 10× off — "A3-implied ~0.7%/71bps" should be 59×12bps=708bps≈7.1%; "48×" → ~4.8×. Load-bearing 34.1% (284×12bps) and the 284-vs-≤59 overstatement are correct/reproduced. Veto-invariant.
- **F-2 LOW**: B's VETOED_POWER_INDEPENDENT_EVENTS labelled kill (ii) is not A3's preregistered floor (θ-events 350≥40 met); it's A4's census independent-episode convention — disclosed, corroborative, not load-bearing.
- **F-3 LOW**: class-7 fade-row rho (+0.369/+0.542) value not reproduced (~120 conventions tried); direction corroborated; immaterial — LEVEL row + identity reproduce exactly and independently exceed the 0.20 bar. "12h-EMA" label = 24h span.
- **F-4 LOW/INFO**: A4's matched-control set (n=12,753) not exactly reconstructable (A7 7,246); paired result reproduces.
- **F-5 INFO**: A3 groundwork P(DT∧¬lens)=0.000394 vs measured 0.000137 — both ≈0, conclusions unchanged.
- **F-6 INFO**: bounce-share proxy 0.4743 vs 0.4857 (staged 5m panel lacks kline open column).
- **F-7 INFO**: ledger mtime bump in recon window attributed to controller commit 675af1cb; content identical to HEAD.
