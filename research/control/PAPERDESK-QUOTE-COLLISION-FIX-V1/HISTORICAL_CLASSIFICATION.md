# W1.4 historical classification (descriptive only)

No historical ledger rows were changed. This table compares the exact source identities retained in HISTORICAL_CASES.json; it is not a replayed production decision or an EV/AI verdict.

| Refused fixture | Price twin | Payload SHA256 (fixture / peer) | Market ID (fixture / peer) | PM event ID (fixture / peer) | Classification |
|---|---|---|---|---|---|
| 401909853 | 401909845 | `5a923cb1a86a93d89f0ca285bd5d9468422ff2d7e37caf7152e75f51bf462770` / `8f605ad49c205564d685f0371977a6ac524ed4ee98590b00c5f4d973a31ccc8f` | 5847746 / 5792072 | 1208439 / 1202603 | PRICE_TWIN_OBSERVED; false price collision |
| 401909095 | 401909093 | `81d560dc4cc83597f9077c52e8ed8c0364c37aec62c0313fd59de8dc80f832ce` / `f26e266689ddebd143e074b4b68fb8af16f962f6ba15a86e25cd81523ccd2d18` | 5792063 / 5765055 | 1202600 / 1197295 | PRICE_TWIN_OBSERVED; false price collision |
| 401909849 | 401909850 | `3ade2297edf47d65d03a7eb00966e431840cff0a5b5c06b219f44e6429da7659` / `0e04ac1484d71605a30cbe1507085acf6ce6121ff097a756f781cd44749a48f2` | 5797983 / 5797986 | 1203773 / 1203774 | PRICE_TWIN_OBSERVED; false price collision |
| 401909850 | 401909849 | `0e04ac1484d71605a30cbe1507085acf6ce6121ff097a756f781cd44749a48f2` / `3ade2297edf47d65d03a7eb00966e431840cff0a5b5c06b219f44e6429da7659` | 5797986 / 5797983 | 1203774 / 1203773 | PRICE_TWIN_OBSERVED; false price collision |

All four historical refusals are price twins with distinct payload, market, and event identities under the owner rule. This does not prove that any fixture would pass EV, AI/VETO, risk, or stake gates.

Existing two-way rows record semantic leg identities HOME/AWAY in pm_walk.legs; no token ID was inferred from price.
