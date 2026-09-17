# Lane A2 dossier — Dukascopy Historical Data as candidate FX tick source

Task `fibv1-a2` · cycle `FOREX-INTRA-BIDASK-V1` · branch `orca/fibv1-a2`
base `74d0632cfe14a186fdedf7d9ff1666d9b596dc6c` · 2026-09-17

## 1. Mission and frozen design

Measure Dukascopy Historical Data as the plan-frozen candidate source for
exactly EURUSD, GBPUSD, AUDUSD, USDCAD, NZDUSD: canary manifest frozen before
any fetch (`canary_manifest.json`), HEAD-only availability census per the
frozen etiquette, two-sided BID/ASK proof decoded from raw `.bi5` bytes
(`decode_bi5.py`), determinism re-fetch ALL_MATCH, license/terms evidence from
hashed official pages only, hard byte cap 300 MB, raw bytes only in the
governed root `/Users/hoangminhlong/.my-quantitative-data/forex-intra-bidask-v1/raw/`.

## 2. Terminal finding: BLOCKED_TRANSPORT

The official surface is **unreachable from this environment** because of
network-path filtering of the dukascopy domain. This is a measured result, not
an assumption:

| Evidence | Result |
|---|---|
| System resolver (192.168.0.1) | returns `127.0.0.1` for `datafeed.dukascopy.com` and `www.dukascopy.com` (transcript `verify/dns_system`) |
| DNS-over-HTTPS (cloudflare-dns.com, TLS OK) | real addresses: datafeed → CNAME chain → `194.8.15.180` (Dukascopy origin range); www → `104.20.28.213`, `172.66.145.22` (Cloudflare) |
| TLS to `194.8.15.180`, SNI `datafeed.dukascopy.com` | ConnectionResetError, 3/3 attempts (retries per frozen etiquette) |
| TLS to `104.20.28.213`, SNI `www.dukascopy.com` | ConnectionResetError, 3/3 attempts |
| Plain HTTP/80 to `194.8.15.180`, `Host: datafeed.dukascopy.com` | TCP connects, request reset, 3/3 attempts |
| Control: TLS to `example.com` via default path | **TLS_OK** (115/120 ms) — general internet works |
| Control: TLS to `104.20.28.213` (Dukascopy's own address) with SNI `example.com` | **TLS_OK** — the destination IP is NOT blocked |
| Census representative probes: pattern HEAD, one per pair (5/5 pairs, 2026 DST-boundary cell) | ConnectionResetError, 3/3 attempts each |
| License page GETs (3 candidate official URLs) | ConnectionResetError, 3/3 attempts each |

The SNI-discrimination control proves the filter is **hostname-keyed**
(SNI / HTTP Host), not destination-IP-based and not a dead source. 33 of 33
dukascopy-bound attempts failed at connection level; zero response bytes ever
existed. Per the frozen etiquette, any 4XX/5XX pattern is evidence and never a
reason to escalate volume — a connection-level reset for every URL is
stronger evidence still, so the remaining 185 census probes were **withheld**
(`census_results.json`: 200 cells recorded `UNREACHABLE_TRANSPORT`, 5
representative probes executed, 185 withheld with rationale).

What was **not** done, deliberately: no VPN, no ECH, no domain fronting, no SNI
spoofing, no proxy. Defeating a network filter would be unlawful circumvention
(guards/refusals are LAW; unreachability is a verdict input). The plain-HTTP
path was tested once for diagnosis (it is also filtered); downloading data
over an unauthenticated channel was never an option anyway.

## 3. Execution state per frozen manifest order

| Order | Phase | State |
|---|---|---|
| 1 | transport verification probes | EXECUTED — all source-bound attempts reset; controls pass |
| 2 | availability HEAD-census (200 cells) | BLOCKED — 5 representative probes FAIL; 185 withheld by etiquette |
| 3 | license/terms pages | BLOCKED — UNAVAILABLE_FAIL_CLOSED; 0 pages hashable |
| 4 | DST-transition window GETs | NOT_RUN — gate `SKIPPED_UNREACHABLE` |
| 5 | historical day 2019-10-30 GETs | NOT_RUN |
| 6 | recent day 2026-09-09 GETs | NOT_RUN |
| 7 | determinism re-fetch (≥5 files) | NOT_RUN — zero files exist |

Bytes: **664 total downloaded** (two DoH JSON answers, ~0.0002% of the 300 MB
cap). **Zero bytes from the source.** Byte-cap guard was armed but never
triggered. `raw_byte_index.json` records exactly 2 meta artifacts
(`raw/_meta/dns/*.json`, hashed) and 0 source tick files.

## 4. What this verdict does NOT establish

- **Nothing about Dukascopy's licensing.** Zero official pages were readable,
  so the license class is `UNAVAILABLE_FAIL_CLOSED` — an availability failure,
  not a rejection. No clause was quoted because none was seen. Nothing was
  accepted, agreed or clicked on the owner's behalf.
- **Nothing about the data schema.** The two-sided BID/ASK question,
  stride-20/LZMA/scale-1e5 candidates, monotonicity, and the UTC hour-boundary
  convention are all **UNVERIFIED** — measured claims require fetched bytes
  and none exist. `decode_bi5.py` is committed and validated 13/13 on a
  synthetic fixture (tool-only scope; `decode_report.json` keeps source decode
  at `NOT_RUN`).
- **Nothing about Dukascopy as a vendor.** A different network path may reach
  the source fine; this lane measured one environment at one time.

## 5. Verdict mapping

Plan §7, first matching rule: rule 2 — *A2 transport fails* →
**`BLOCKED_TRANSPORT`**. Rule 1 is not applied (license did not fail on
substance; it is unavailable from the identical root cause) but is recorded as
co-blocker B2 that must be re-cleared independently. The two-sided proof (rule
3) was never reached and is not adjudicated.

## 6. Incidents (transparent, same session)

- **INC-FIBV1-A2-1**: the command sandbox initially resolved ALL hostnames to
  127.0.0.1. Re-verification with sandbox disabled showed real addresses for
  `example.com` but 127.0.0.1 specifically for dukascopy domains — genuine
  network filtering, not a sandbox artifact.
- **INC-FIBV1-A2-2**: self-caught defect — the driver's reachability gate
  counted a DNS record's `"OK"` (the poisoned 127.0.0.1 answer) as transport
  success, wrongly skipping census/license/canary once. Fixed in-session
  (gate now considers only HTTP/TLS-level successes) and the phases re-run.
- **INC-FIBV1-A2-3**: pre-manifest ad-hoc reachability diagnostics (~6 DNS
  lookups, 6 TCP/TLS probes, 1 curl control; zero content) predate the frozen
  manifest; disclosed here. All subsequent probing ran through the driver.

## 7. Recommended next actions for the Lead

1. Treat this as an **environment** finding: re-measure transport from a
   different network path (owner decision — this lane may not alter network
   configuration) before concluding anything about Dukascopy itself.
2. If transport is restored, lane A2 must be re-run **from the frozen
   manifest** (it is fetch-order-complete); the license gate and the two-sided
   byte proof remain fully open questions.
3. Per plan §7 rule 7, this lane's NOT_RUN items must stay NOT_RUN — they are
   not inferable PASSes and no successor may assume them.
