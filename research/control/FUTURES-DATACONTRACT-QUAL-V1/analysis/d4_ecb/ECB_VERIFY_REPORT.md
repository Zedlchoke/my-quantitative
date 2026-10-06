# D4-ECBVERIFY — ECB GC decision-date machine verification (55/55)

Cycle: `FUTURES-DATACONTRACT-QUAL-V1` · Lane: `D4-ECBVERIFY` (read-only, no commits)
Access date: 2026-10-03 · Worktree: `prep/futures-behavior-10syms-20261002` @ `73abf15c`
Per-date evidence: `ecb_dates_verification.json` (same directory)

**PB2 remains HOLD regardless of this outcome.** This lane only upgrades the
PIT-quality of the ECB event table for a *future* PB2 court. It opens nothing.

## Bottom line

| Metric | Before lane | After lane |
|---|---|---|
| Per-date direct-fetch machine verification | 10 / 55 (dossier count; identities not preserved on disk) | **55 / 55** |
| Delta | — | **+45** |
| Unverified / failed dates | 45 | **0** |
| SDW MRO effective-date machine cross-check | 20 rate-change meetings (A7, effective−6 convention) | **19/19 exact** (fresh fetch, all map into the 55-set) |

Every one of the 55 dates now has: canonical press-release URL fetched by plain
HTTP GET → **HTTP 200**, page **title** match, and the **long-form date string
present in the page content** (e.g. "23 January 2020"). 54 dates carry the
standard title "Monetary policy decisions". One title variant:

- **2020-03-18** (emergency GC meeting): the decision was announced as
  *"ECB announces €750 billion Pandemic Emergency Purchase Programme (PEPP)"*
  (`ecb.pr200318_1~3949d6f266.en.html` — `pr` slug prefix, not `mp`). Monetary
  policy decision content (PEPP envelope + conditionality) is on the page;
  date string "18 March 2020" in content. Verified as the GC monetary-policy
  announcement of that date, title variant disclosed.

## Accounting caveat (evidence-first)

The dossier's "10 machine-verified" is a **count without preserved identities**
— no on-disk artifact lists which 10 dates the DEEP-6E lane fetched. The
strongest on-disk per-date evidence was the A7 audit (2026-10-03): 4 dates
direct-URL-fetched (2020-01-23, 2021-03-11, 2025-03-06, 2026-02-05), 1 via SDW
series (2023-06-15), plus a 20/20 rate-change cross-check. Therefore this lane
verified **all 55 dates**, which covers any possible identity of the original
10 and all of the 45 unverified ones. The "+45" delta is stated against the
dossier's 10/55 count.

## Method (normal public routes, plain HTTP GETs, no credentials)

1. **Enumeration** — the canonical URL scheme
   `ecb.europa.eu/press/pr/date/YYYY/html/ecb.mpYYMMDD~<hash>.en.html` cannot be
   guessed (hash segment; hash-less variant → 404). The hash-bearing URLs were
   enumerated from the **ECB website's own search backend** (`api.addsearch.com`,
   site key public in the site's `slow.min.js` — the identical call every
   visitor's browser makes when rendering the ECB listing pages), using
   single-day `dateFrom`/`dateTo` windows with the phrase query
   `"Monetary policy decisions"` (2020-03-18 required its distinct PEPP title).
2. **Direct verification** — each enumerated canonical URL fetched once
   (paced ~2.5 s), recording HTTP status, `<title>`, and in-content date string.
3. **Independent cross-check** — ECB SDW Data Portal API series
   `FM.B.U2.EUR.4F.KR.MRR_FR.LEV` (MRO rate, fresh CSV fetch): every rate-change
   effective date 2020+ minus 6 days (ECB convention) lands exactly on a date in
   the 55-set (19/19).

Release-time corroboration: the rendered mopo index page states verbatim that
decisions "are published in a press release at **14:15 CET** on the day of the
Governing Council monetary policy meeting" — consistent with the dossier FACT;
the 14:45 press-conference time remains unverifiable from that page (not re-checked).

## Failure taxonomy of the routes that did NOT work

| Route | Class | Detail |
|---|---|---|
| Wayback Machine CDX | **offline (503)** | "Internet Archive: Temporarily Offline" at access; same failure class as the original lane's 2026-10-02 attempt |
| Hash-less canonical URL | **404 by design** | confirms the dossier's "hash prevents enumeration" finding |
| `sitemap.xml` | **insufficient (200)** | 478 index-level URLs only; no per-press-release entries |
| mopo/press archive raw HTML | **JS-rendered** | HTTP 200, correct title, zero `ecb.mp*` links server-side (listing built client-side via the search API) |
| web_reader render of mopo index | **partial** | renders 2024–2026 listing but truncates ~Jan-2024 and strips hrefs; used as corroboration only |
| Year-window search enumeration | **partial (30/55)** | superseded by single-day windows (full coverage) |

**Zero dates ended UNVERIFIED**; the taxonomy above covers blocked *routes*,
not blocked *dates*.

## Laws kept

Read-only outside `analysis/d4_ecb/**` + this lane's handoff; no purchases; no
credentials; no scraping storm (≤ 2 distinct URL patterns per date, ~2–2.5 s
pacing); missing evidence is never PASS — every VERIFIED row carries its own
URL, HTTP status, title and date-string evidence.
