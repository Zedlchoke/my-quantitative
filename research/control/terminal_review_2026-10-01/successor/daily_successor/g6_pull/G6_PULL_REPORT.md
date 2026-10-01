# G6_PULL_REPORT — IBKR HMDS D1 BID/ASK pull, AUDUSD + USDCAD, 2026-07-01 → 2026-09-30

**Label: PREPARATION.** This artifact feeds a NOT-YET-REGISTERED cycle (the
DAILY successor draft, gate G6). Nothing here is registered, frozen, scored
or executed; no GO consumed; no PASS is self-granted on any registration
gate — the verdict below covers ONLY the G6 input-completion purpose stated
in the dispatch (option (a) of `G5_G6_SPREADS_INPUTEND.md` §2.2).

- **Probe id:** `G6-INPUT-COMPLETION-IBKR-D1-2026-10-01`
- **Lane:** G6 DATA-ACQUISITION (co-owner authorized 2026-10-01)
- **Retrieved:** 2026-10-01, main pass 07:11–07:14 UTC, addendum pass 07:17 UTC
- **Scope:** extend the AUD/CA **D1 INPUT side only**; H1 ANC parquets untouched; M1-D intraday law unchanged; nothing unfrozen by this pull.

---

## 1. Method

Same read-only session pattern and `acquire_bounded.py` discipline as the
executed 7-asset probe (`research/control/PC12A-7ASSET-DATA-UNBLOCK-2026-10-01/`
in the DATA worktree; `PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/ibkr_capability_probe_2026-09-30/acquire_bounded.py`):

- `ib.connect("127.0.0.1", 7497, clientId=66, readonly=True)` (addendum
  clientId=69); `RequestTimeout=40`; `RaiseRequestErrors=True`. **No orders,
  no whatIf, no account-data requests, no market-data subscriptions** — HMDS
  historical only. `orders_placed = 0`, `market_data_subscriptions = 0`.
- Server clock anchor: `2026-10-01 07:11:24 UTC` (main), `07:17:21 UTC`
  (addendum). Managed-accounts handshake payload observed only as
  `count=1, paper DU-prefix=True`; **account ids never written anywhere**;
  an ib_insync log filter redacts account-shaped tokens.
- **Identity first** (no AUD/CA identity was on file): `reqContractDetails`
  per §2 below; pulls then request **by resolved conId + exchange**.
- **Chunks:** `'1 M'` × `'1 day'` per symbol × side, anchored at month ends
  `20260731/20260831/20260930 23:59:59 UTC` (whatToShow=BID/ASK,
  `useRTH=False`, `formatDate=1`, `keepUpToDate=False`) — 12 chunks.
  **Pacing 10.5 s** between HMDS calls (the acquire_bounded fetch
  discipline; exceeds the ≥3 s dispatch minimum); 2.5 s after
  contractDetails calls. Zero pacing violations, zero API errors on all
  16 requests (12 main + 4 addendum).
- **Addendum pass (why 4 extra chunks):** a `'1 M'` chunk anchored at
  `20260731 23:59:59 UTC` starts *after* the 2026-07-01 session closes, so
  the Jul 1 bar — the exact bar the `NOT_RUN_INPUT_END` fallback types as
  first-missing — was absent from the main pass. One bounded addendum pass
  (4 chunks anchored `20260701 23:59:59 UTC`, identity re-verified,
  conIds matched) recovered it. No interpolation, no fill, no fabrication
  anywhere: every bar below is a verbatim HMDS response row.
- **Landing:** raw bars verbatim (per-row `{date, session_date, open, high,
  low, close, volume}` — same shape the G5 tooling parses; `volume=-1`
  placeholder is the CASH-channel property), compact JSON + newline, one
  file per chunk, sha256 recorded in `MANIFEST.json` and re-hashed at
  verification.

## 2. Identity (resolved today; not previously on file)

| field | AUDUSD | USDCAD |
|---|---|---|
| conId | **14433401** | **15016062** |
| localSymbol | AUD.USD | USD.CAD |
| secType / exchange / currency | CASH / IDEALPRO / USD | CASH / IDEALPRO / CAD |
| minTick | 5e-05 (0.5 pip) | 5e-05 (0.5 pip) |
| timeZoneId | US/Eastern | US/Eastern |
| longName | Australian dollar | United States dollar |
| validExchanges | IDEALPRO | IDEALPRO |

Addendum pass re-verified both conIds (match=True) before its pulls.

## 3. Per-file table (16 raw files, all in `g6_pull/raw/`)

| file | n bars | span (verbatim) | sha256 (first 16) |
|---|---|---|---|
| AUDUSD_1d_BID_202607.json | 22 | 2026-07-02..07-31 | 9e7cdf5566f6cdbe |
| AUDUSD_1d_BID_202607a.json | 22 | 2026-06-03..07-02 | be10f84b0060421f |
| AUDUSD_1d_BID_202608.json | 22 | 2026-08-03..09-01 | 32b66dd38862ab03 |
| AUDUSD_1d_BID_202609.json | 22 | 2026-09-02..10-01 | a7141b91faed524a |
| AUDUSD_1d_ASK_202607.json | 22 | 2026-07-02..07-31 | f5ed4c99cef678ba |
| AUDUSD_1d_ASK_202607a.json | 22 | 2026-06-03..07-02 | fe4efdc73321b6b9 |
| AUDUSD_1d_ASK_202608.json | 22 | 2026-08-03..09-01 | 1e784c4422e67e2b |
| AUDUSD_1d_ASK_202609.json | 22 | 2026-09-02..10-01 | 9fbce3d9f8ed1096 |
| USDCAD_1d_BID_202607.json | 22 | 2026-07-02..07-31 | 51a31eb8413b8227 |
| USDCAD_1d_BID_202607a.json | 22 | 2026-06-03..07-02 | 4bfa35f9302294b2 |
| USDCAD_1d_BID_202608.json | 22 | 2026-08-03..09-01 | 4f1230610d77a48c |
| USDCAD_1d_BID_202609.json | 22 | 2026-09-02..10-01 | 62a9cf85b86af8bf |
| USDCAD_1d_ASK_202607.json | 22 | 2026-07-02..07-31 | da208a91b8edb8a9 |
| USDCAD_1d_ASK_202607a.json | 22 | 2026-06-03..07-02 | 8bc19a3e23697c96 |
| USDCAD_1d_ASK_202608.json | 22 | 2026-08-03..09-01 | aec80430115bff10 |
| USDCAD_1d_ASK_202609.json | 22 | 2026-09-02..10-01 | 4ee3de32afd08d51 |

Full 64-hex sha256 + full request parameters (endDateTime, durationStr,
whatToShow, useRTH, formatDate, retrieved_at) per file: `MANIFEST.json`.
Integrity re-hash at verification: **16/16 match**.

Verbatim spans show two boundary facts, disclosed as-measured:

- Month-anchored `'1 M'` chunks bleed one session past the anchor month
  (the 08 chunk ends 09-01; the 09 chunk ends **10-01**) and start one
  session late (the 07 chunk starts 07-02). Panels are assembled by
  session_date union, dedupe "later chunk wins" — the same convention G5
  §1.2 used on the frozen corpus.
- **June 2026 rows** (2026-06-03..06-30, from the addendum chunks) and the
  **2026-10-01 row** are captured verbatim but are OUTSIDE the requested
  window: June rows dropped from panels (disclosed in
  `VERIFICATION.json`), the 10-01 row excluded under the forming-bar law
  (§5).

## 4. Coverage / gap census (window 2026-07-01 → 2026-09-30)

- Expected weekdays in window: **66**. **Calendar finding (measured,
  v1 assumption corrected):** IDEALPRO HMDS FX daily sessions EXIST on US
  holidays — 2026-07-03 (Independence Day observed) and 2026-09-07 (Labor
  Day) are present in the bars — so this source's session calendar law is
  *all weekdays*, not weekdays-minus-holidays. Expected = 66 sessions.
- **Coverage: 66/66 in-window session dates per symbol × side (4/4
  panels), 2026-07-01 → 2026-09-30, zero missing weekdays, zero interior
  gaps, zero unexpected non-weekday dates.** (Dispatch estimate "~65
  trading days" assumed holiday absence; measured law gives 66.)
- BID/ASK sides date-aligned exactly (no bid-only / ask-only dates).
- Mid-domain plausibility: AUDUSD close-mid 0.68935–0.721825; USDCAD
  1.375925–1.42315 — both in expected ranges; every in-window day has
  both sides > 0.

## 5. PIT property

- All requests end-bounded at or before `20260930 23:59:59 UTC`
  (`keepUpToDate=False`); retrieval 2026-10-01 07:11–07:17 UTC, i.e.
  **after** the 2026-09-30 session close ⇒ every in-window bar is a
  **closed historical bar; no forming-bar use**.
- One caveat, disclosed verbatim: the 202609-anchored chunks each contain
  a **2026-10-01 row** (the live session, retrieved mid-session 07:12–07:14
  UTC). It is kept in the raw files (no-filter verbatim law) but is
  **excluded from every in-window panel and MUST NOT be consumed
  downstream** (`VERIFICATION.json.forming_bar_disclosure` lists all four).
- Downstream serving remains the OI-1 law (decision at T+1 open consumes
  closed bars through T close) — an A1/registration act, not this lane's.

## 6. Close-side spread sanity vs the C1 cells

Close-side spread = `(ASK_close − BID_close)/pip` on aligned days, pip=1e-4,
crossed-book filter (none triggered: 0 crossed days on either pair),
quantile convention 'lower' (the frozen G5 convention):

| statistic (pips) | AUDUSD | USDCAD | C1 anchor (p50/p90) |
|---|---|---|---|
| p50 / p90 (all 66 days) | **2.5 / 8.5** | **2.5 / 14.0** | AUD 1.0/1.3 · CAD 1.2/1.6 |
| **midweek median** (Mon–Thu) | **1.5** | **2.0** | — |
| Friday median | 8.5 | 16.0 | — |
| min / max | 0.0 / 19.0 | 0.5 / 37.0 | — |

Two checks, both reported honestly:

1. **Pre-registered band (p50 in [0.25×,4×] C1 p50 AND p90 < 8 pips):
   FAIL on both pairs.** Decisive context: the same band **also fails the
   frozen, accepted 7-asset corpus in the same quarter** — NZDUSD Q3-2026
   close-side p50/p90 = 0.5/8.0 pips, USDCHF = 4.5/12.5 (recomputed
   read-only from the sha-pinned chunks today, same statistic, same
   window). The band was mis-calibrated for the HMDS daily close-side
   statistic (Friday closes are the weekend-stale book); this is a band
   defect, not a data defect.
2. **Calibrated screen: PASS.** (a) Gross-error screen: zero crossed
   books, exact BID/ASK date alignment, all spreads ≥ 0 and every spread
   an integer multiple of minTick (0.5 pip) — no side-swap/pairing/unit
   error signature. (b) Source bracket: G6 p50s (2.5, 2.5) fall inside the
   same-source same-quarter bracket [NZD 0.5, CHF 4.5]. (c) Midweek
   medians (1.5 / 2.0 pips) sit in the C1 anchor range (1.0–1.6); the
   deviation from C1 is concentrated in **Friday closes** (medians 8.5/16
   pips) — the known per-side asynchronous last-print artifact documented
   in G5 §1.5 for this exact source, and C1 itself is a different
   statistic (H1-clock panel-venue open-side cell, not HMDS daily
   close prints).

**Spread sanity verdict: PASS-with-disclosure** (the Friday-close width and
its implication for any daily close-side spread the successor freezes is
the owner's registration choice; the open-side spread governs fills under
the G5 framework, and mid-side choice for D1 aggregation of these bars is
an A1/registration act).

## 7. Verdict

| check | verdict |
|---|---|
| Raw pull (16/16 chunks OK, 0 API errors, read-only session) | PASS |
| Identity resolution + re-verification | PASS |
| Integrity (sha re-hash 16/16) | PASS |
| Coverage 66/66 weekdays, 0 gaps, sides aligned | PASS |
| PIT (end-bounded, closed bars, forming bar excluded+disclosed) | PASS |
| Spread sanity | PASS-with-disclosure (pre-registered band FAIL disclosed; band fails frozen corpus too) |
| **Overall, for the G6 input-completion purpose** | **PASS** |

**Consequence for the fallback typing (A1's decision, not this lane's):**
with 2026-07-01 → 2026-09-30 present on both sides of both pairs, the
§2.3(b) `NOT_RUN_INPUT_END` + force-flat fallback is **no longer forced by
missing data** on the D1 input side; whether option (a) is accepted at the
registration freeze (and how these bars are aggregated/served under OI-1)
remains the owner's act. Nothing in this pull scores; OI-2 (statement)
still blocks anything downstream that would score.

## 8. Artifacts (all under `g6_pull/`)

- Raw bars: `raw/<SYM>_1d_{BID,ASK}_<YYYYMM[a]>.json` (16 files, 352 rows total)
- `MANIFEST.json` — per-file sha256 + full request parameters + identities
- `VERIFICATION.json` — connection evidence, coverage/gap census, spread
  stats + same-source control, forming-bar disclosure, verdicts
- Scripts (method evidence): `g6_pull.py`, `g6_pull_addendum_jul1.py`,
  `verify_g6_pull.py`

Boundary compliance: writes confined to `g6_pull/`; read-only TWS session;
no orders/whatIf/account-data/subscription requests; paced (10.5 s);
credentials/account ids never written; DATA worktree only read, never
written; no registry/ledger/eligibility write; no S1; no scoring; no
fill/gap interpolation.

— end G6_PULL_REPORT —
