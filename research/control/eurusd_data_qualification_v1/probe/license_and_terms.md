# EDQ1 — License and Terms record (P1 probe)

Cycle: EURUSD-DATA-QUALIFICATION-V1 · Lane: eurusd-source-qualification
Retrieval of terms pages: 2026-09-22 UTC (this probe).

## License status line

```
Dukascopy public datafeed (datafeed.dukascopy.com): UNCLEAR
Twelve Data (api.twelvedata.com, time_series):      CLEAR_FOR_INTERNAL_RESEARCH
```

No license status below is fabricated. Statuses follow strictly from the
verbatim quotes and the gaps between them.

---

## 1. Dukascopy

### 1.1 What Dukascopy says about the historical data service (descriptive, not a license)

Source: https://www.dukascopy.com/swiss/english/marketwatch/historical/
("Forex Historical Data Export :: Dukascopy Bank SA", retrieved 2026-09-22)

> "provides historical price data for variety of financial instruments (e.g.
> Forex, Commodities and Indices)"

> "It is free through Dukascopy's Historical Data Export tool"

> FAQ usage example: "Backtesting: Test and adjust trading strategies using
> past data"

The page describes purpose (backtesting) but contains NO data license grant,
NO ownership statement for the tick data, and no mention of the
`datafeed.dukascopy.com` host. A dedicated terms page for the datafeed host
was NOT FOUND during this probe (probed
`.../marketwatch/historical/datafeed/` → HTTP 404 on 2026-09-22).

### 1.2 Site Terms of Use (TCU) — the only terms found

Source: https://www.dukascopy.com/swiss/english/legal-pages/terms-of-use/
("Terms of Use :: Dukascopy Bank SA", retrieved 2026-09-22). The TCU governs
"the WEBSITE" (www.dukascopy.com); it does not name `datafeed.dukascopy.com`.
Verbatim, under "Restrictions on Use":

> "Except written agreement between you and DUKASCOPY, you agree to use the
> WEBSITE solely for your own non-commercial use and benefit, and not for
> resale or other transfer or disposition to, or use by or for the benefit
> of, any other person or entity."

> "You may not copy, reproduce, recompile, decompile, disassemble, reverse
> engineer, distribute, publish, display, perform, modify, upload to, create
> derivative works from, transmit, or in any way exploit any part of the
> WEBSITE, except that you may download material from the WEBSITE and/or make
> one print copy for your own personal, non-commercial use, provided that you
> retain all copyright and other proprietary notices."

> "The WEBSITE and the information contained therein may not be used to
> construct a database of any kind. Nor may the WEBSITE be stored (in its
> entirety or in any part) in databases for access by you or any third party
> or to distribute any database WEBSITEs containing all or part of the
> WEBSITE."

> "You shall not use or attempt to use any 'scraper,' 'robot,' 'bot,'
> 'spider,' 'data mining,' 'computer code,' or any other automate device,
> program, tool, algorithm, process or methodology to access, acquire, copy,
> or monitor any portion of the WEBSITE, any data or content found on or
> accessed through the WEBSITE, or any other WEBSITE information without the
> prior express written consent of DUKASCOPY."

Under "License":

> "Should you choose to download content from the WEBSITE, you must do so in
> accordance with the TCU. Such download is licensed to you by DUKASCOPY ONLY
> for your own personal, non-commercial use in accordance with the TCU and
> does not transfer any other rights to you."

Under "Disclaimer and Limitation of Liability":

> "(iii) You acknowledge that: (i) the WEBSITE is provided for information
> purposes only; ... (iii) DUKASCOPY does not guarantee the sequence,
> accuracy, completeness, fitness for a specific purpose or timeliness of the
> WEBSITE"

### 1.3 Assessment (why UNCLEAR)

1. No terms document specific to `datafeed.dukascopy.com` was found. The
   bytes ARE attributable to Dukascopy Bank SA (the host and URL scheme are
   Dukascopy's published Historical Data Feed layout), but the applicable
   license for that host is not stated anywhere we could locate.
2. If the site TCU is held to apply: download is allowed ONLY for "your own
   personal, non-commercial use"; automated acquisition ("scraper... without
   the prior express written consent") and "construct a database of any kind"
   are prohibited. A multi-year local tick archive for a research factory
   plausibly collides with both clauses.
3. If the TCU does NOT apply to the datafeed host, then NO license governs
   the bytes at all — which is also not clearance.

Therefore: `UNCLEAR`. This lane does NOT accept terms on anyone's behalf and
does not conclude that research use is forbidden — only that it is not
demonstrably permitted. Per plan §1, until this is resolved the Dukascopy
source is `CANDIDATE_NOT_AUTHORIZED`. Resolution paths (owner action, not
engineering): obtain Dukascopy's prior express written consent, or an owner
legal decision that the TCU/datafeed combination is acceptable for internal
research.

---

## 2. Twelve Data

Source: https://twelvedata.com/terms ("Twelve Data Terms of Use", retrieved
2026-09-22). Verbatim:

> §2.1: "Twelve Data grants Customer a limited, revocable, non-exclusive,
> non-transferable, non-sublicensable license"

> §2.2(a): permits customers to "Access, receive, process, and store Data
> solely for Internal Use"

> §1: "'Internal Use' ... use solely for Customer's internal business
> purposes and not for redistribution or external commercial purposes"

> §2.3(l): prohibition on "Use Free Tier data for commercial purposes"

> §2.3(b): "Redistribute, resell, sublicense, or transfer any Data or access
> rights to third parties" is prohibited.

> §2.3(g): "Store or cache Data beyond permitted timeframes specified in the
> Documentation" is prohibited.

> §16.2: after termination "All Data must be deleted within 30 days"

> §6.1: "All rights in the Platform and Data remain with Twelve Data or
> licensors"

### Assessment

Internal research (this cycle: retrieval, digests, reconciliation analysis,
no redistribution) fits "Internal Use". Free-tier commercial-use prohibition
and post-termination deletion duty are noted as constraints.
Status: `CLEAR_FOR_INTERNAL_RESEARCH`.

Field caveat discovered in the probe (matters for cost authority, separate
from license): on this plan the EUR/USD 1min time_series returns OHLC only —
no bid/ask and no volume fields. Twelve Data can be a reconciliation source
but NOT a bid/ask cost authority.

---

## 3. Consequence for the probe verdict

Gate `LICENSE_RESOLVED` requires both sources resolved to a clearance state.
Dukascopy = UNCLEAR → gate FAILS → probe verdict `PROBE_FAIL` (per plan §3 P1:
"fail = any of: license unresolved, ..."), mapping to cycle verdict candidate
`BLOCKED_SOURCE_LICENSE` at P3 unless the license question is resolved first.
All TECHNICAL gates passed (see probe_verdict.json).
