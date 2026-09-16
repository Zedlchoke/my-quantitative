# FREE-DATA-FRONTIER-V1 — PUBLIC SOURCE ACQUISITION AND AUTHORITY CENSUS

> Owner instruction, 2026-09-16: collect the previously identified free
> sources; the owner supplies only human-only credentials/terms steps.

## 1. Mission and non-goals

Build a reproducible, fail-closed acquisition layer and a small verified raw
snapshot for these public sources:

1. OFR Short-Term Funding Monitor;
2. Federal Reserve Bank of New York market-data APIs;
3. SEC fails-to-deliver and Form N-PORT bulk data;
4. Coinbase, Kraken Futures and Deribit public market-data streams;
5. EIA Open Data;
6. NOAA/NWS observations;
7. USDA historical WASDE releases.

This is a data-engineering cycle. It performs no strategy proposal, PnL,
scoring, S1 access, paper order, testnet order or live order. A reachable URL
is not evidence of research authorization or point-in-time usability.

## 2. Integration boundary

```text
cycle     FREE-DATA-FRONTIER-V1
branch    orca/free-data-frontier-v1-integration
worktree  .worktrees/free-data-frontier-v1/integration
asset     infra
budget    0 scored cells
```

Root remains owner/control-plane space. Implementation occurs only in the
integration worktree. Raw bytes live under a gitignored external data root;
Git receives code, tiny synthetic fixtures, manifests and evidence only.

## 3. Authority and secret boundary

- `SEC_CONTACT_NAME`, `SEC_CONTACT_EMAIL` and `EIA_API_KEY` are read from the
  root checkout's gitignored `.env` without logging their values.
- Request identities, manifests and errors must redact credential values and
  personal contact values.
- SEC retrieval is capped below the published 10 requests/second limit.
- No account creation or click-through acceptance is performed by automation.
- Source statuses are one of `PASS_SAMPLE`, `PASS_INVENTORY_ONLY`,
  `BLOCKED_TERMS`, `BLOCKED_CREDENTIAL`, `BLOCKED_SCHEMA`, `BLOCKED_NETWORK`,
  or `NOT_RUN_RESOURCE_CONFLICT`.

## 4. Bounded acquisition contract

The first run is intentionally bounded:

- OFR: inventory all mnemonics and acquire a curated funding/liquidity set.
- NY Fed: acquire documented reference-rate series and inventory dealer/repo
  surfaces; never scrape a rendered dashboard when an API/export exists.
- SEC FTD: inventory the full archive and acquire a recent sample plus a
  parameterized historical downloader.
- SEC N-PORT: inventory every quarterly ZIP; acquire at most one recent
  quarter in V1, subject to a preflight disk floor, and inspect/filter without
  committing extracted bytes.
- Crypto: capture short, timestamped public samples for BTC and ETH from each
  venue. These streams begin prospective history; they do not imply historical
  coverage.
- EIA: inventory API routes and acquire a curated energy set relevant to
  commodities; use the key without placing it in a URL stored in evidence.
- NOAA/NWS: acquire station/observation samples for a small preregistered set
  of energy/agriculture locations; do not mirror NOAA.
- USDA: inventory historical WASDE releases and acquire machine-readable
  release artifacts where available, preserving release/repost identity.

Disk guard: refuse a download when free space after the declared content
length would fall below 15 GiB. Unknown-size large downloads fail closed.

## 5. Required artifact for every retrieval

Every raw object records:

```text
source_id, dataset_id, canonical_request_id, source_url_redacted,
retrieved_time_utc, http_status, content_type, content_length,
raw_path, raw_sha256, parser_version, authority_status,
event/effective/available/vintage semantics, notes
```

Historical availability is never invented. When only retrieval time is known,
the object remains useful for prospective collection but is not authorized for
historical scored joins.

## 6. Implementation surface

```text
research/free_data_frontier/
  __init__.py
  contract.py
  env.py
  http.py
  manifest.py
  sources/{ofr,nyfed,sec_bulk,eia,nws,usda}.py
  streams/{coinbase,kraken,deribit}.py
  cli.py
tests/free_data_frontier/
research/control/free_data_frontier_v1_run/
```

Prefer Python standard library. WebSocket support may use an already-installed
dependency; otherwise a small RFC6455 client is not to be improvised and the
stream is recorded `BLOCKED_DEPENDENCY` until an explicit dependency decision.

## 7. Phases and gates

### F0 — bootstrap

- freeze worktree/branch/base SHA and raw-data root;
- prove `.env` variable names exist without printing values;
- prove raw root is ignored/outside Git and disk floor is measurable;
- record active workers and heavy-lock state.

### F1 — license/endpoint census

- pin official documentation and terms URLs;
- inventory endpoints/files without bulk acquisition;
- record key/account requirements and redistribution restrictions;
- fail closed on ambiguous use terms.

### F2 — fixture-tested adapters

- deterministic request identity and secret redaction;
- atomic write, response hash, retry/rate-limit rules;
- strict schema probes and negative tests;
- no retrieval time substituted for availability time.

### F3 — live canaries

- one bounded live canary per source;
- two-pull equality for immutable bulk objects when economical;
- timestamp and sequence continuity checks for public streams;
- manifest every byte retained.

### F4 — bounded historical acquisition

- one heavy download/parser at a time under the machine-wide lock;
- FTD historical acquisition may proceed after canary PASS;
- N-PORT is capped at one quarter in V1;
- no unbounded NOAA or crypto mirroring.

### F5 — audit and terminal

- targeted and full tests as resource permits;
- verify manifests from raw bytes;
- report per-source `usable now`, `prospective only`, `blocked`, and exact
  human action if any;
- terminal result is `FREE_DATA_FRONTIER_V1_PASS_PARTIAL`,
  `FREE_DATA_FRONTIER_V1_BLOCKED_AUTHORITY`, or
  `FREE_DATA_FRONTIER_V1_TECHABORT_PRESERVED`.

## 8. Stop rules

Stop the affected source, not the whole cycle, when credentials are missing,
terms are ambiguous, schema changes, rate limiting persists, TLS validation
fails, content hash changes for a supposedly immutable object, or the disk
floor would be breached. Never bypass a provider restriction.

## 9. Verification

```bash
.venv/bin/python -m pytest tests/free_data_frontier -q
.venv/bin/python -m compileall research/free_data_frontier
git diff --check
```

The full repository suite runs only when the machine-wide heavy slot is free
and the prospective shadow workers remain unaffected.

