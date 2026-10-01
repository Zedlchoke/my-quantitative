# ACTION_PACKET — statement-free gates done; OI-2 blocked at Portal access (2026-10-01)

## Gate completion after this session (no statement needed anywhere below)

| gate | status | evidence |
|---|---|---|
| G3 VIX | **PASS** (freeze-time re-run stands) | 50/50 sha re-verified; CBOE 9,281 rows 1990→2026-09-25, holidays-only gaps; dual-channel law reproduced (9,278 common, 0 diffs); t→t+1-close usability PASS. NOTE: 2026-09-28/29/30 post-date the frozen fetch — extend at registration | G3_G4_VIX_SIGMA.md |
| G4 σ tripwire | **COMPUTED freeze-ready** | NZD 64.6388 / CHF 49.6150 verified Δ0.0000 vs lane; **XAU NEW: IBKR σ 112.1838 bps = freeze basis (OI-1 panel-of-record); TD archive 104.5190 cross-check (7.3% apart, venue calendar — disclosed not harmonized)**; tripwire 1σ/5σ/0.5σ table complete | G3_G4_VIX_SIGMA.md |
| G5 daily spreads | **COMPUTED freeze-ready** | 48/48 chunk sha match; probe's 8 p50/p90 + 4 maxima reproduce exactly (quantile convention pinned); XAU crossed-book filter restated. **NEW LOAD-BEARING FINDING: fill-facing OPEN-side bands are 3–13× wider than the probe's close-side stats** (async first prints: XAU O p50/p90 38.4/167.4 vs C 5.5/18.6 bps; XAG 83.2/524.0; CHF 24.7/55.6; NZD 2.5/18.9). Not a double-charge (spread-once holds — kernel fills at side quotes); tail is stale-print-pessimistic; NO trim invented — owner freeze decision | G5_G6_SPREADS_INPUTEND.md |
| G6 AUD/CAD D1 | **NOT_RUN — 2 lawful options ready** | (a) PROPOSAL: IBKR HMDS D1 BID/ASK pull AUD/USD.CAD 2026-07-01→09-30 via the 7497 read-only precedent (identity resolution first; NOT executed); (b) typed fallback EXACT: last lawful AUD/CA decision 2026-07-01; 2026-07-02→09-24 = 61/130 fold-8 sessions `NOT_RUN_INPUT_END` (DS-05 only; force-flat at boundary recommended) | G5_G6 file |
| G7 vehicle/PARAM-GAP | **COMPLETE (draft)** | DS-03/DS-05 sets; parked legs frozen-as-parked with named un-park conditions | G7_G8_G10_FREEZE_DRAFTS.md |
| G8 selection freeze | manifest draft COMPLETE — freeze ACT at registration | same file |
| G9 quote-CCY | SPEC complete (plan §7b + journal law + identity/reconciliation tests); engine build = registered-cycle work | plan |
| G10 prospective law | draft COMPLETE (collection law per input; earliest honest eval ≈2029-09) | same file |

**Depends on OI-2 (owner file):** G1 (statement absent — Access-Denied
blocker 13:45 ICT recorded; NOT asking retries; NO paper trades; NO
inferred MEASURED) + G2 (attribution law ready and frozen-in-draft:
commission per-trade matched; swap Σ u(n⁻)×r_ccy(n); slippage NEVER
statement-measured).
**Registration acts:** G11/G12.

## Owner decisions (each ONE action)

1. **OI-2 access path**: resolve Portal access (network/browser) OR
   enable Flex-via-API/email delivery OR accept option (c) — the cycle
   may run EXPLORATORY-only under DECLARED costs with NO after-cost PASS
   (current law, no relaxation).
2. **G5 freeze choice**: adopt the recommended cells (fill-facing =
   O-FOLDS; continuity = C-FULL) with the stale-print tail disclosed —
   or name a trim rule (that would be a new parameter: it enters the
   freeze as a declared owner decision, not silently).
3. **G6 pick**: authorize the AUD/CAD HMDS D1 pull (owner action or
   inside the registered cycle) OR freeze the typed truncation +
   force-flat boundary (61/130 fold-8 sessions typed).

Then: when G1–G12 ALL PASS → register (researchctl) → freeze → A7 →
STOP before scored GO. Fail-closed unchanged; TERMINAL cycles and S1
untouched.
