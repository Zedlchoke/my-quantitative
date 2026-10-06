# Fees By Code — Public-Reference Component & All-In Table (Lane A4-FEES)

Task: FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003 · Lane: A4-FEES · Run date: 2026-10-03
Worktree: `prep/futures-behavior-10syms-20261002` @ `7149425d` (no commits; $0 read-only lane)
Access session (UTC): 12:54–14:19 (successful primary fetches 13:05–13:25)

**Framing: MODELED_COST.** Every number below comes from PUBLIC fee-schedule pages fetched
2026-10-03. Nothing is a measured cost from any account. **Every row: SOURCE=PUBLIC_REFERENCE,
VERIFIED_VS_ACCOUNT=NOT_RUN.** Owner account verification is a separate NOT_RUN item; there is
NO account evidence and none was fabricated. Public documents prove document content, never
account behavior. This table extends the ES precedent (D2-FEESRC,
`research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d2_feesrc/ES_FEE_SOURCES.md`) using
the same source classes, the same IBKR offset-table route, and the same arithmetic convention
(components summed per side; round-trip = 2× single side).

Codes: **NQ, 6E, 6B, 6J, 6A** (primary) + **CL, NG, GC, SI** (feasible subset — all four
obtained). All-in for all 9 codes was COMPUTED from public components; nothing was NOT_FETCHED
among the three modeled components (commission / exchange offset / regulatory offset).

---

## 1. Sources (all accessed 2026-10-03 UTC)

| ID | Class | Publisher / what | URL | Access (UTC) | Status |
|----|-------|------------------|-----|--------------|--------|
| A1 | LIVE_OFFICIAL | IBKR public futures commissions page (US tier table, uniform for all US futures incl. all 9 codes) | https://www.interactivebrokers.com/en/pricing/commissions-futures.php?re=amer | 13:25 | FETCHED_FULL |
| A2 | LIVE_OFFICIAL | IBKR "Fees Charged to Offset CME (Electronic-Globex) Exchange and Regulatory Fees Paid by IBKR" (NQ + FX rows) | https://www.interactivebrokers.com/en/accounts/fees/CME.php | 13:05 | FETCHED_FULL |
| A3 | LIVE_OFFICIAL | IBKR "Fees Charged to Offset NYMEX Exchange and Regulatory Fees Paid by IBKR" (CL, NG rows) | https://www.interactivebrokers.com/en/accounts/fees/NYMEX.php | 13:06 | FETCHED_FULL |
| A4 | LIVE_OFFICIAL | IBKR "Fees Charged to Offset COMEX Exchange and Regulatory Fees Paid by IBKR" (GC, SI rows) | https://www.interactivebrokers.com/en/accounts/fees/COMEX.php | 13:12 | FETCHED_FULL |
| A5 | LIVE_OFFICIAL (reused in-repo, same-day D2-FEESRC fetch) | NFA Bylaw 1301 CFTC filing 2017-11-17 (assessment-fee timeline 0.02→0.01→0.02) | https://www.nfa.futures.org/news/PDF/CFTC/2010-2019/20171117-Bylaw-1301-FCM-Assessment-Fee-Increase.pdf | ~08:07 (D2) | REUSED_PER_MISSION |
| A6 | PUBLIC_MIRROR (reused in-repo, same-day D2-FEESRC fetch) | TradeStation exchange-fee table (NQ $1.38; E7 E-mini Euro FX $0.85 rows) | https://www.tradestation.com/pricing/exchange-execution-and-clearing-fees/ | ~08:05 (D2) | REUSED (own re-fetch BLOCKED_TRANSPORT) |

Blocked this session (attempts in `fetch_log.jsonl`): TradeStation live page, CME official
fee-schedule PDF (eff. 2026-02-01), AMP dated mirror (2025-02-01 notice), IBKR HK regional
mirror. WebFetch to interactivebrokers/tradestation/ampfutures/cmegroup hosts returned
ECONNREFUSED (target-host egress filtering — WebFetch itself works, verified on example.com);
web_reader was saturated by 429s after 13:25Z.

## 2. IBKR commission by plan/tier — VERBATIM (A1), identical for all 9 codes

US futures (monthly cumulative contracts across ALL futures/FOPs regardless of exchange,
applied marginally — footnote verbatim in `fees_table_all.json` source A1):

| Plan | Tier (contracts/mo) | IBKR execution fee USD/contract/side | SOURCE | VERIFIED_VS_ACCOUNT |
|------|--------------------|---------------------------------------|--------|---------------------|
| Tiered | ≤ 1,000 | 0.85 | PUBLIC_REFERENCE (A1) | NOT_RUN |
| Tiered | 1,001–10,000 | 0.65 | PUBLIC_REFERENCE (A1) | NOT_RUN |
| Tiered | 10,001–20,000 | 0.45 | PUBLIC_REFERENCE (A1) | NOT_RUN |
| Tiered | > 20,000 | 0.25 | PUBLIC_REFERENCE (A1) | NOT_RUN |
| Fixed | no volume tiers published | 0.85 | PUBLIC_REFERENCE (A1) | NOT_RUN |

A1 Note 3 verbatim: Fixed = "Exchange Fee (which will differ by product), plus Regulatory
Fees" — i.e. the exchange component is the per-exchange offset below. Account's actual
plan/tier UNKNOWN; all variants enumerated, none selected (owner boundary, per ES precedent).

## 3. Exchange + regulatory offsets — VERBATIM (A2/A3/A4), non-member regular

| Code | Exchange | Offset-page row (verbatim anchor) | Exchange USD/side | Regulatory USD/side | SOURCE | Symbol printed verbatim? |
|------|----------|-----------------------------------|-------------------|---------------------|--------|--------------------------|
| NQ | CME | "E-mini Equity Futures … BQX, ER2, **NQ**, QCN, RS1, RSG, RSV, RTY, SPSOX, XAZ" | **1.386** | **0.011** | A2 | YES |
| 6E | CME | "Forex Futures … **EUR**, GBP, …" (product-alias row, see §6 caveat) | **1.60** | **0.011** | A2 | NO (alias EUR) |
| 6B | CME | same row, alias **GBP** | **1.60** | **0.011** | A2 | NO (alias GBP) |
| 6J | CME | same row, alias **JPY** | **1.60** | **0.011** | A2 | NO (alias JPY) |
| 6A | CME | same row, alias **AUD** | **1.60** | **0.011** | A2 | NO (alias AUD) |
| CL | NYMEX | "**Crude Oil (CL)**, Heating Oil (HO), RBOB Regular Gasoline (RB)" — Tier 1 | **1.50** | **0.02** | A3 | YES |
| NG | NYMEX | "**Natural Gas (NG)**" — Tier 1 | **1.60** | **0.02** | A3 | YES |
| GC | COMEX | "**Gold (GC)**, Copper (HG), Silver (SI)" — Non-Member | **1.65** | **0.01** | A4 | YES |
| SI | COMEX | same row, **SI** | **1.65** | **0.01** | A4 | YES |

- NYMEX Tier definitions verbatim (A3 fn.1): "Tier 1 (Non-member), Tier 2 (Incentive
  Program) or Tier 3 (Member/Lessee)" — non-member regular = Tier 1 values above.
- Regulatory rows: A2 "All Products … 0.011 (Tier I & II Non-Members & IIP)"; A3 "All
  Products … Tier 1 … 0.02"; A4 "All … 0.01" — each page footnotes "Regulatory fees are
  assessed by the NFA". These are IBKR's published per-exchange recovery charges.
- All three pages: give-up surcharge USD 0.05/contract, "waived when IBKR is both prime and
  executing broker" — excluded from modeled all-in (standard self-directed flow), disclosed.
- All three pages disclaimer: fees "generally reflect the exchange fee structure, but in
  certain circumstances may be higher or lower than the fees charged by the exchange";
  changeable by IBKR at any time. No effective date rendered on any page.

## 4. Modeled all-in per code — arithmetic line by line (USD, per contract, per side)

Same convention as ES E3/E4 (sum of commission + exchange offset + regulatory offset;
clearing not separately published for these codes — see §6; Overnight Position Fee
NOT_FETCHED, excluded; round-trip = 2×).

### 4.1 NQ (CME)
- Tiered ≤1k / Fixed: 0.85 + 1.386 + 0.011 = **2.247**
- Tier 2: 0.65 + 1.386 + 0.011 = **2.047** · Tier 3: 0.45 + … = **1.847** · Tier 4: 0.25 + … = **1.647**
- Cross-ref: same-day in-repo mirror (A6, verbatim) "NQ | E-mini Nasdaq-100 … $1.38 per
  side, per contract"; consistent with the 1.386 IBKR offset (mirror rounds and combines
  execution+clearing in one column, same as it did for ES 1.38 vs 1.386).
- Note: components identical to ES (2.247) — NQ sits in the same CME equity-offset row value.

### 4.2 6E / 6B / 6J / 6A (CME FX group row, 1.60; mapping caveat §6)
- Tiered ≤1k / Fixed: 0.85 + 1.60 + 0.011 = **2.461**
- Tier 2: 0.65 + 1.60 + 0.011 = **2.261** · Tier 3: 0.45 + … = **2.061** · Tier 4: 0.25 + … = **1.861**
- Same four values for each of 6E, 6B, 6J, 6A (single group row at 1.60 non-member;
  A2 fn.9: non-member FX spread orders charged $0.12/contract — different order type, listed
  for completeness, not used).

### 4.3 CL (NYMEX)
- Tiered ≤1k / Fixed: 0.85 + 1.50 + 0.02 = **2.37**
- Tier 2: 0.65 + 1.50 + 0.02 = **2.17** · Tier 3: 0.45 + … = **1.97** · Tier 4: 0.25 + … = **1.77**

### 4.4 NG (NYMEX)
- Tiered ≤1k / Fixed: 0.85 + 1.60 + 0.02 = **2.47**
- Tier 2: 0.65 + 1.60 + 0.02 = **2.27** · Tier 3: 0.45 + … = **2.07** · Tier 4: 0.25 + … = **1.87**

### 4.5 GC (COMEX)
- Tiered ≤1k / Fixed: 0.85 + 1.65 + 0.01 = **2.51**
- Tier 2: 0.65 + 1.65 + 0.01 = **2.31** · Tier 3: 0.45 + … = **2.11** · Tier 4: 0.25 + … = **1.91**

### 4.6 SI (COMEX)
- Identical to GC (same row, same values): 2.51 / 2.31 / 2.11 / 1.91; Fixed 2.51.

### 4.7 Summary grid (single side, USD; Tiered tiers 1–4 and Fixed)

| Code | T1 (0.85) | T2 (0.65) | T3 (0.45) | T4 (0.25) | Fixed (0.85) |
|------|-----------|-----------|-----------|-----------|--------------|
| NQ | 2.247 | 2.047 | 1.847 | 1.647 | 2.247 |
| 6E | 2.461 | 2.261 | 2.061 | 1.861 | 2.461 |
| 6B | 2.461 | 2.261 | 2.061 | 1.861 | 2.461 |
| 6J | 2.461 | 2.261 | 2.061 | 1.861 | 2.461 |
| 6A | 2.461 | 2.261 | 2.061 | 1.861 | 2.461 |
| CL | 2.37 | 2.17 | 1.97 | 1.77 | 2.37 |
| NG | 2.47 | 2.27 | 2.07 | 1.87 | 2.47 |
| GC | 2.51 | 2.31 | 2.11 | 1.91 | 2.51 |
| SI | 2.51 | 2.31 | 2.11 | 1.91 | 2.51 |

Every cell: SOURCE=PUBLIC_REFERENCE (A1 + A2/A3/A4), VERIFIED_VS_ACCOUNT=NOT_RUN, label
MODELED_COST.

## 5. NFA regulatory fee — reused in-repo official history (A5, per mission)

0.02 → 0.01 (2014-10-01) → 0.02 (2018-01-01, last official document). Reused from the ES
precedent; NOT re-derived. Open item unchanged: no official post-2018 change document fetched
in either session. Relationship between the official NFA assessment and IBKR's per-exchange
regulatory offsets (0.011 / 0.02 / 0.01) is not resolvable from public fetches — the offsets
are what IBKR charges, not a transcript of the assessment.

## 6. Caveats

1. **Offsets, not tariff.** All exchange/regulatory values are IBKR's published fee-recovery
   (offset) rates; IBKR's own disclaimer says they may be higher or lower than exchange fees.
   Official CME/NYMEX/COMEX tariff cross-checks: BLOCKED_TRANSPORT this session (logged).
2. **FX mapping (6E/6B/6J/6A) PARTIAL corroboration.** The CME.php full-size FX fee is a
   product-GROUP row listing aliases (EUR, GBP, JPY, AUD … and one 6-prefixed code, 6H);
   6E/6B/6J/6A are not printed verbatim. Mapping rests on standard CME product-code
   convention, partially corroborated by the same-day mirror row "E7 | E-mini Euro FX | $0.85"
   matching IBKR's E-mini Forex row value. Rows flagged mapping_corroboration=PARTIAL in the
   JSON. Hard binding needs one dated public page listing 6E/6B/6J/6A explicitly
   (TradeStation re-fetch, AMP notice, or CME PDF — all blocked today).
3. **No effective dates** rendered on the four fetched pages; as-of = fetch date 2026-10-03.
   IBKR states rates may change at any time.
4. **Clearing**: no separate clearing line published on any fetched offset page for these
   codes, and no worked example with a clearing line rendered (unlike ES's doc example).
   No clearing value asserted — any clearing element inside the offset line is unbifurcated
   on the public page.
5. **Excluded add-ons**: Tiered Overnight Position Fee NOT_FETCHED (JS tables never render);
   give-up surcharge 0.05 published but waived in the standard flow and excluded; spread/
   implied/EFP order types carry different published offsets (not used here).
6. **Historical years**: no official per-year schedule obtained for any of the 9 codes
   (CME hosts blocked). Any historical use ⇒ CURRENT_SCHEDULE_AS_APPROXIMATION with
   disclosure that NFA changed 2014/2018 (A5) and CME Group increases inside 2010–2026 are
   publicly referenced (e.g. eff. 2022-02-01, 2025-02-01 — surfaced, not fetched), so the
   current schedule is KNOWN-WRONG for at least some past years.
7. **No account verification** — owner redacted-account documentation remains the open item
   for cost authority; nothing here states or implies account behavior.

## 7. Deliverables of this lane

- `FEES_BY_CODE.md` (this file)
- `fees_table_all.json` (machine-readable; one row per code×plan×component + ALL_IN rows,
  each with source URL, as_of, SOURCE=PUBLIC_REFERENCE, VERIFIED_VS_ACCOUNT=NOT_RUN)
- `fetch_log.jsonl` (every fetch attempt, UTC, tool, outcome)
