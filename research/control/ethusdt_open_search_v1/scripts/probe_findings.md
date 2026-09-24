# EOS1 P1 probe findings — Vision CDN behavior (measured 2026-09-24)

Raw machine output: `probe_result.json` (same directory). Three measured
facts, all load-bearing for the stager design:

1. **HEAD is always 404 on `data.binance.vision`** (15/15 HEAD probes 404,
   including keys proven to exist). Stagers must use GET. A 1-byte Range GET
   (`bytes=0-15`) answers `206` + zip magic `PK\x03\x04` on existing keys.

2. **Volume-correlated transient 404s on existing keys (throttle mask).**
   Timeline (same URL `…/ETHUSDT/1h/ETHUSDT-1h-2020-01.zip`, proven to exist
   by yesterday's ES1 staging manifest, sha256 fb4840ec…):
   - 14:xx single GET+Range → 206 ZIP_MAGIC (ok)
   - minutes later: inline retry → 404, then 5/5 × (206 range / 200 plain)
     in a 10-request burst (ok)
   - immediately after ~45 probe requests (15 URLs × 3 retries):
     **all 404, including 3-attempt retries with 1 s backoff**
   - after 90 s of silence → 206 ZIP_MAGIC again (ok)
   The failure mode is NOT per-key; it is request-volume correlated on the
   shared egress IP, and it masks as 404 — the "missing month" signal is
   indistinguishable from "throttled" during bursts. The concurrent
   CRYPTO-HISTORICAL-REPLICATION-3F-V1 bulk staging (heavy-lock owner,
   vision + fapi, same machine/IP since 13:01Z) plausibly contributes.

3. **Consequence for this cycle (stager law, preregistered now):**
   - bulk staging WAITS until the foreign bulk Binance consumer releases
     the wire (CHR3F staging completion) — coexistence etiquette per the
     2026-09-21 418 precedent; no parallel bulk pulls on one IP.
   - stager pacing ≥ 2.0 s between Vision GETs; on any 404: exponential
     backoff (1s/2s/4s) + 60 s cooldown, max 5 attempts; a month is
     declared MISSING only after the 5th attempt at ≥60 s spacing.
   - a "missing month" verdict inside a 404 burst is INVALID evidence —
     the stager must re-verify every missing-month verdict after a
     120 s quiet window before writing it into the census.

Floors NOT yet measured through the throttle (deferred to the quiet-wire
staging pass): ETHUSDT 1h months 2019-10/11/12 (perp launch 2019-11-27;
warmup-only months), fundingRate floor, ETHBTC spot floor, BTCUSDT 1h
floor. Measured-today floors: `klines:ETHUSDT:1h` 2020-01 EXISTS (206 +
ZIP_MAGIC, twice); 2026-08 existence is evidenced by the ES1 manifest
(fetched 2026-09-23, digest pinned) and re-verification at staging time.
