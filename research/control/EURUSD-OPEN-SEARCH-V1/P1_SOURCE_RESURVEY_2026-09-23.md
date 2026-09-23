# EURUSD-OPEN-SEARCH-V1 — P1 source re-survey transcript (2026-09-23 UTC)

Light read-only P1 work under the owner directive of 2026-09-23 ("Ưu tiên
khảo sát lại TrueFX từ điều khoản gốc ...; tiếp theo OANDA v20 Practice
NẾU đã có tài khoản/token được owner cấp ...; Dukascopy chỉ khi có văn bản
đồng ý phù hợp. Tự tìm thêm nguồn hợp lệ nếu cần."). GET/HEAD browsing
only; NO registration, NO terms acceptance, NO bulk download, NO secret
printed. Evidence frozen while another cycle
(CRYPTO-HISTORICAL-REPLICATION-3F-V1/data-staging, pid 77456) holds the
machine-wide heavy lock — this survey is light prep, no lock contended.

## 1. TrueFX (owner priority #1 — "điều khoản gốc" re-survey)

| Check | Measured 2026-09-23 | Evidence |
|---|---|---|
| Landing page license text | NONE — "no terms of use link, no data license agreement"; only "TrueFX is a trademark of Integral Development Corp." | https://www.truefx.com/ |
| Historical downloads delivery | **LOGIN/REGISTRATION-GATED**: "Please log in or register for free access to the historical data downloads." No .zip/.csv URL visible anonymously. Links: /truefx-login/, /truefx-registration/ | https://www.truefx.com/truefx-historical-downloads-2/ |
| License/permitted-use text | NONE public. FAQ offers only use-case framing ("indicative, not executable"; uses "including enhanced price verification, historic back-testing and generating a base price") — a use-case mention is NOT a storage/redistribution license | https://www.truefx.com/truefx-market-data-faq/ |
| Legacy anonymous archive URLs | ALL 404 anonymously: `truefx.com/dev/file/2024-03/EURUSD-2024-03.zip`, `www.truefx.com/dev/file/...`, `www.truefx.com/dev/data/2024/EURUSD-2024-03.zip`, `www.truefx.com/downloads/EURUSD-2024-03.zip` | curl HEAD probes 2026-09-23 |
| Live streaming endpoint | `https://webrates.truefx.com/rates/connect.html?f=html&c=EUR/USD` → HTTP 200 — LIVE indicative quotes only; NOT 3–5y history; no public terms document for it | curl probe 2026-09-23 |
| Wayback of legacy `/dev/` page | Wayback wrapper UI only; no archivable license text recovered | web.archive.org capture attempt 2026-09-23 |

**TrueFX status: `CANDIDATE_NOT_AUTHORIZED` (unchanged vs 2026-09-22
owner packet).** The license text exists only behind free login; an agent
may not register or accept terms on the owner's behalf. The free-login
gate also implies download rights are account-bound — anonymous byte
retrieval would not carry a license even if a URL existed.

## 2. OANDA v20 Practice (owner priority #2 — conditional)

Condition: "NẾU đã có tài khoản/token được owner cấp". Measured: root
`.env` variable-NAME census (values never read): `EIA_API_KEY`,
`EODHD_API_KEY`, `FRED_API_KEY`, `SEC_CONTACT_EMAIL`, `SEC_CONTACT_NAME`,
`TWELVE_DATA_API_KEY`, `TYPESAFE_API_KEY`. **No OANDA credential exists.**
No OANDA-related file elsewhere in the root tree (find, name-level). Repo
history since 2026-09-22 contains no new source/license artifacts (git
log --name-only sweep empty). Owner untracked dirs
(d2_curiosity_v1_sources/, bear_opportunity_recon_2026-09/,
SANDBOX-OVERFIT-3ASSETS/) inspected at directory-listing level only —
unrelated D2/curiosity content, no data license.

**OANDA status: `NOT_AVAILABLE_NO_OWNER_CREDENTIAL`.**

## 3. Dukascopy (owner priority #3 — conditional on written consent)

Condition: written consent text in evidence. Measured: no consent
artifact exists anywhere (EURUSD-DATA-QUALIFICATION-V1 evidence
re-checked 2026-09-23: verdict `BLOCKED_SOURCE_LICENSE`, A7
`AUTHORIZED_BLOCKED_SOURCE_LICENSE`; its `probe/license_and_terms.md`
verbatim TCU quotes stand: personal non-commercial only, automated
acquisition forbidden without prior express written consent, no-database
clause, any-service preamble). The datafeed host itself remains
terms-orphaned.

**Dukascopy status: `CANDIDATE_NOT_AUTHORIZED` (unchanged).**

## 4. Additional source sweep (owner: "tự tìm thêm nguồn hợp lệ nếu cần")

| Source | Bid/ask | License reality | Status |
|---|---|---|---|
| Twelve Data (key on hand) | NO bid/ask | internal-use OK but storage time-limited | reconciliation-only; after-cost PASS impossible → `BLOCKED_COST_AUTHORITY` if used alone |
| HistData | Y (tick) | terms silent on storage/redistribution — silence ≠ permission | `CANDIDATE_NOT_AUTHORIZED` (unchanged) |
| TickData.com / OlsenData | Y | commercial licensing, paid | owner purchase decision; agent cannot activate |
| Polygon/Massive | Y (BBO) | $49+/mo tier | owner purchase decision |
| Forex Tester / forexsb "free tick data" | Y | third-party redistribution of Dukascopy-collected bytes; vendor marketing ≠ origin data license | fail-closed |
| Web sweep (2026-09-23, search) | — | surfaced no new public-terms bid/ask FX source vs the 2026-09-22 census | no improvement |

## 5. Conclusion

No source satisfies the §1 qualification checklist today. Since the
2026-09-22 `BLOCKED_SOURCE_LICENSE` verdict of EURUSD-DATA-QUALIFICATION-V1,
no new rights artifact, credential, or terms document has appeared.
Per plan §1 and the owner directive, the campaign cannot compute ANY PnL;
the cycle registers `BLOCKED_SOURCE_LICENSE` with 0 trials executed of the
96-trial cap.
