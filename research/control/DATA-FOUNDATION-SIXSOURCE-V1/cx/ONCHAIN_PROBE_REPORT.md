# ONCHAIN_PROBE_REPORT — lane CX, Ethereum mainnet (bounded keyless query)

**LABEL LAW: `PROSPECTIVE_FROM_2026-09-28`.**

**Anti-retroactive labeling law (binding on any consumer of this artifact):**
every block number, timestamp, balance or state read in this probe is
**AS-OF-NOW state at the recorded receive timestamp** — never point-in-time
(PIT) history. This session performs **no** wallet/address labeling and **no**
historical balance reconstruction. Any later use that back-dates these reads
to earlier timestamps is prohibited by this law.

- Probe window: 2026-09-28T02:31:07.341Z → 02:31:26.022Z
- Probe script: `research/control/DATA-FOUNDATION-SIXSOURCE-V1/cx/probe_onchain.py`
- Raw root (outside git): `~/.my-quantitative-data/sixsource-foundation-v1/onchain/`

## 1. Provider screens (recorded BEFORE first data call)

| Provider | Basis | Ruling |
|---|---|---|
| `https://ethereum-rpc.publicnode.com` | publicnode.com self-description: "Fastest, free-est, and privacy first RPC endpoints for 77 blockchains" | VERIFIED keyless public good — used |
| `https://cloudflare-eth.com` | Cloudflare public Ethereum gateway; keyless HTTP 200, no auth demand on screening call; current Cloudflare docs page no longer documents the gateway (moved) | BASIS RECORDED WITH DISCLOSURE — used, 3 light read-only calls |
| `https://eth.llamarpc.com` | homepage HTTP 526, endpoint unreachable at screen time | **BLOCKED_LICENSE_VERIFY** (basis unverifiable) — not used |

df check: 25.27 GiB free (floor 5 GiB) — PASS. Budget: 6 of ≤8 JSON-RPC calls
across 2 providers, sequential ≥1 s spacing, plus the single keyless explorer
call. No auth demand or paywall appeared.

## 2. Measured results

### PublicNode (all 3 calls HTTP 200, no JSON-RPC error)

| Method | Receive UTC | Latency | Result |
|---|---|---|---|
| `eth_blockNumber` | 02:31:07.936Z | 594.6 ms | head **26,072,973** (0x18dd78d) |
| `eth_getBlockByNumber("latest")` | 02:31:18.835Z | 9,893.8 ms | block **26,072,973**, ts 1790562659 = 2026-09-28T02:30:59Z, hash `0x0976d28342a77f15…` |
| `eth_getBlockByNumber("finalized")` | 02:31:20.689Z | 850.1 ms | block **26,072,908**, ts 1790561879 = 2026-09-28T02:17:59Z, hash `0xdf24d1ad7890b3d0…` |

**latest→finalized lag: 65 blocks / 780 s (13.0 min)** — consistent with
Ethereum's ~2-epoch (≈12.8 min) finality distance; the `finalized` tag is
served and truthful on this provider. (The 9.9 s latency outlier is one slow
response on a free public endpoint, recorded as measured.)

### Cloudflare gateway (all 3 calls HTTP 200 shell, application-level failure)

| Method | Result |
|---|---|
| `eth_blockNumber` | JSON-RPC error **−32046 "Cannot fulfill request"** |
| `eth_getBlockByNumber("latest")` | JSON-RPC error **−32603 "Internal error"** |
| `eth_getBlockByNumber("finalized")` | JSON-RPC error **−32046 "Cannot fulfill request"** |

Reachable and keyless, but unable to fulfill any of the three read methods at
sample time → **provider disagreement: NOT_RUN (single working provider)**.
No disagreement figure is fabricated; the honest datum is "one of two providers
functionally unavailable".

### Indexer availability (one keyless explorer call — budget respected)

`GET https://eth.blockscout.com/api/v2/blocks/latest` → **HTTP 422 in 454.3 ms**
(02:31:26.022Z) with a structured Blockscout validation error: the route now
expects `block_hash_or_number` as a parameter (the packet's example URL no
longer matches the current API shape). Datum recorded: **indexer server alive
and keyless (fast structured rejection), but "latest-block" availability was
not demonstrated in one call**; per the one-call rule no retry was made.

## 3. Authority claims

CAN claim (measured): on 2026-09-28 ~02:31 UTC, via keyless PublicNode, Ethereum
mainnet head was 26,072,973 (block time 02:30:59Z), the `finalized` tag resolved
to 26,072,908 (02:17:59Z), finality distance 65 blocks / 780 s; a second public
provider (Cloudflare) was reachable but application-level broken for these
methods; the Blockscout indexer responded keyless with a route-validation error.
CANNOT claim: any historical chain state, any wallet labeling, any balance at
any time other than the recorded receive instants (anti-retroactive law); any
provider-disagreement statistic (only one provider returned data); indexer
"latest block" availability (route rejected in the single budgeted call).

## 4. Artifacts

| Artifact | Path | Status |
|---|---|---|
| Probe script | `research/control/DATA-FOUNDATION-SIXSOURCE-V1/cx/probe_onchain.py` | AVAILABLE_VALIDATED |
| Raw probe JSON (50,836 B) | `~/.my-quantitative-data/sixsource-foundation-v1/onchain/onchain_probe_20260928T023126Z.json` | AVAILABLE_VALIDATED (sha256 in manifest, re-verified) |
| Manifest | `~/.my-quantitative-data/sixsource-foundation-v1/onchain/onchain_manifest.json` | AVAILABLE_VALIDATED |
