# DISPATCH PACKET — lane CX (crypto L2 + options + on-chain)

- task_id: `sixsource-lane-cx`
- role: A3-data-lane (read-only reconnaissance; 0 scored surface)
- controller: A1 (this session's controller, inline)
- handoff_path (MANDATORY, schema `zcode_orch_v3_handoff@1`):
  `research/control/DATA-FOUNDATION-SIXSOURCE-V1/cx/HANDOFF_CX.json`
  (`commit_sha`: null — no-commit session; disclose changed paths)
- repo: root checkout only, NO worktree, NO branch, NO commit, NO push,
  NO registry/ledger writes, NO touching other cycles' control dirs,
  `~/.env`, credentials, holdout/sealed content, shadow/dashboard.
- python: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`
  (aiohttp + requests available; do NOT pip install anything).
- raw bytes OUTSIDE git: `~/.my-quantitative-data/sixsource-foundation-v1/`
  (`crypto_l2/`, `options/`, `onchain/`) with sha256 manifests per file.

## Scope (three bounded deliverables, in order)

### 1. Binance L2 orderbook collector — BTCUSDT + ETHUSDT (max 2 symbols)

- Snapshot + diff method: REST `GET /api/v3/depth?symbol=…&limit=1000`
  (try host `https://data-api.binance.vision` first, fallback
  `https://api.binance.com`), then WS `wss://stream.binance.com:9443/ws`
  subscribing `btcusdt@depth@100ms` + `ethusdt@depth@100ms`
  (aiohttp `session.ws_connect`; NO api key, NO account).
- Sequence integrity: buffer events pre-snapshot; verify each event's
  `U`/`u`/`pu` chain; count and log every gap/violation + reconnect;
  on reconnect re-snapshot. Record: events received, drops, gaps,
  reconnects, ws latency (send/receive timestamps where available),
  book depth stats (levels, top-of-book) — snapshot only.
- Bounded session: run ONE collector window of 10 minutes
  (configurable), hard caps: raw file ≤ 200 MB (then stop cleanly),
  total HTTP requests ≤ 30. Rate etiquette: sequential, ≥1 s spacing
  on REST.
- Output: raw ndjson (one line per ws event, with receive_ns) +
  `collector_manifest.json` (sha256/bytes/start/end UTC) +
  `L2_SESSION_REPORT.md` (sequence/gap/reconnect table).
- Label law: every artifact carries `PROSPECTIVE_FROM_2026-09-28` —
  this is a from-today sample, NOT historical data; the repo law
  "no order-book/forced-flow inference from candles" stands; nothing
  here may be presented as backtestable history.

### 2. Deribit crypto options sample (keyless public market data)

- Identify scope explicitly: **crypto options (Deribit)** — equity/OpRA
  options are out of scope for this lane (licensed vendor needed; no
  purchase).
- Calls (public, no auth; ≤25 requests total, sequential 1/s):
  `GET https://www.deribit.com/api/v2/public/get_instruments?currency=BTC&kind=option&expired=false`
  → chain membership census (expiries listed, count of strikes per
  expiry); pick ONE nearest expiry, sample up to 10 strikes via
  `public/ticker?instrument=BTC-<date>-<strike>-C/P` → record
  bid/ask/iv/greeks/underlying/index/timestamp fields verbatim.
- Record Deribit API terms class (public market data, no redistribution,
  internal research) with the terms URL in the report — license screen
  BEFORE the first call; if terms cannot be verified, record
  BLOCKED_LICENSE_VERIFY and stop that sub-task.
- Output: `options/Deribit_sample_<ts>.json` (raw) + sanitized rows +
  `OPTIONS_SAMPLE_REPORT.md` (chain membership, quote fields, IV/greeks
  present? timestamps: exchange ts vs receive ts).

### 3. On-chain bounded query (Ethereum mainnet, keyless public RPC)

- ≤8 light JSON-RPC requests total across ≤2 providers from:
  `https://ethereum-rpc.publicnode.com`, `https://eth.llamarpc.com`,
  `https://cloudflare-eth.com`. Queries: `eth_blockNumber`,
  `eth_getBlockByNumber("latest"/"finalized", false)` (number, timestamp,
  hashes). Optional one call to a public explorer/indexer that needs NO
  key (e.g. `https://eth.blockscout.com/api/v2/blocks/latest`) to record
  indexer availability.
- Record per response: provider, method, latency_ms, receive UTC,
  block number, block timestamp (unix), `latest`→`finalized` lag
  (finality distance), provider disagreement across providers.
- Anti-retroactive labeling law (write into the report): any wallet/
  address labeling or balance state is AS-OF-NOW state, never PIT
  history; this session performs NO retroactive wallet labeling and no
  historical balance reconstruction.
- Output: `onchain/onchain_probe_<ts>.json` + section in lane report.

## ToS / budget pre-checks (before ANY fetch)

1. Binance API terms: public market-data endpoints, keyless, rate-limit
   compliant — record terms URL + one-line ruling in the report.
2. Deribit API terms: as above.
3. Public RPC endpoints: public goods, no key — record basis.
4. Disk: `df` check before start (abort below 5 GiB free).
5. No purchase, no signup, no key, no proxy substitution by candles.

## Stop conditions

Any unexpected auth demand, paywall, ToS conflict → that sub-task gets
`BLOCKED_*` with the exact reason and the lane continues with the rest.
Total lane wall time target ≤ 40 min. If a piece exceeds it, record
NOT_RUN + reason and finish the handoff honestly.
