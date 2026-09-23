# INC-1 — /futures/data 418 under serial pacing (2026-09-23 ~09:05–09:22Z)

What happened: CHR3F staging phase A basis items crashed repeatedly. Root
cause chain: (1) the frozen `restage_basis.py` pages `/futures/data/basis`
at 0.55s serial with its own 8x20s 418 backoff, but under the CURRENT shared
egress IP (LIVE-DATA-GATEWAY-V1 + PROSPECTIVE-SHADOW-V1 fetches coexist
there since ~2026-09-22) the endpoint escalated to HTTP 418 bans; (2) a
200-with-non-list rate-limit body class crashed the frozen script
(TypeError, row["timestamp"] on a string) — that response class was not
present in the V14 era; (3) the CHR3F runner captured the subprocess log
AFTER the rc check, so the first crash lost the diagnostics (fixed: log is
written before the rc check, dir pre-created).

Incident during diagnosis: a manual page-walk (0.2s spacing, no backoff)
triggered a fresh 418 on the shared IP at ~09:15Z. This was CHR3F traffic.

Fallout check (measured 09:21:46Z): gateway rest_breaker HEALTHY
(consecutive_5xx 0, no open window); shadow valuation heartbeat
last_error null, last_loop 09:20:00Z, price_source unchanged. No foreign
cycle data-plane disruption observed.

Fixes (worktree commit 0c9495bd): basis pacing 10s/request (6 req/min);
frozen-script failures retried x5 with 600s cooldown; non-list-200 treated
transient; item reorder (fast klines/funding first); A_index 15m (manifest
parity) vs B_index 8h sampled cross-check (density decided pre-PnL);
watcher 1800s initial cooldown + 1800s retries.

Exposure: zero scored cells; staging data unaffected (klines/funding phase A
checksum-verified before the incident); no foreign worker touched.
