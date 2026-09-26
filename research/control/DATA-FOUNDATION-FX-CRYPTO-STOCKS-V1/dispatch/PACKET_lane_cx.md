# PACKET — L-CX (crypto data census + validation)

ROLE: A3-class data-authority survey lane. OBJECTIVE: complete §5 authority
rows + gap candidates for every CRYPTO dataset the program holds or has held.
WORKTREE: `/Users/hoangminhlong/my-quantitative/.worktrees/data-foundation-v1/lane-cx`
BRANCH: `orca/dfv1-lane-cx`. Allowed writes: `research/control/DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1/cx/` only. COMMON.md applies in full.

## Owner priority list (verbatim from OWNER_DIRECTIVE.md)
Crypto: trades/quotes, spot–perp basis, mark/index, funding đã settle so với
funding dự báo, fees và exchange rules theo thời gian; OI, liquidation và L2
chỉ khi thật sự có lịch sử PIT, coverage và license hợp lệ. **Không suy ra
order book hay forced flow từ nến** — this prohibition must appear verbatim
in your LANE_REPORT and in any gap row touching OI/liquidation/L2.

## Census targets
1. `~/.my-quantitative-data/crypto-ng4-ws/` (2.1 G; TERMINAL CRYPTO-NG4) —
   WS collector outputs; manifests sha-chained 19/19 per DEU/NG4 records.
   Validate via committed manifests (SAMPLED ok).
2. `~/.my-quantitative-data/data-edge-unlock-v1/` (420 M) — Coinbase/Kraken/
   Deribit keyless WS collectors + FTD/N-PORT (FTD belongs to stocks
   content-wise; still row it here if co-located, cross-reference).
3. `.worktrees/pws-cx-solusdt-c1/` (12 G; TERMINAL) — SOL klines 52,145
   bars, funding 6,580 settlements, 6-month bookTicker spread census (p50
   0.469 bps), sha-pinned inventory + license ToU captured. Validate from
   its committed inventory manifests (SAMPLED).
4. `.worktrees/pws-cx-bnbusdt-c1/` — ACTIVE_LIGHT, GO-1 executing NOW:
   F5 rule, metadata only, committed manifests only.
5. `.worktrees/crypto-historical-replication-3f-v1/` (1.6 G; ACTIVE_LIGHT
   scored execution) — F5 rule, metadata only.
6. `.worktrees/ethusdt-open-search-v1|v2/` (v2 ACTIVE_LIGHT, workers=0, GO
   pending — heartbeat >24h old; still prefer inherited manifests; sampling
   allowed if no writer process: check `ps` before any read of its data dirs)
   — 7-series Vision corpus + ES1 cross-check + funding settlements.
7. Binance Vision panels + funding + OI + mark/index across
   `.worktrees/phase-strategy-v1/` (BTC H1/H4 2020–2026), `btc-h4-*`,
   `srlv-cx-c1/` (BTC/ETH 1h + funding 8h), `regime-strategy-mapping-v1/`,
   `illiq-reg-v1|illiq-loss-mech-v1/`, `jev-regime-router-v1|v2/`,
   `erp1-trackb-cohort-1/` (carry/funding planes). Enumerate distinct
   dataset families (klines per symbol-set, funding, OI, mark/index,
   bookTicker, aggTrades from the archived V16 — check
   `~/staging_backups` + `research/control/staging_backups_manifest.md`).
   Rows are per dataset family, not per cycle.
8. `research/control/crypto_frontier_2026-09/`, `ng5_ng6_frontier` dossiers —
   pointers only.
9. LIVE-DATA-GATEWAY-V1 surface (`~/.my-quantitative-data`? locate) —
   ACTIVE worker: F5 metadata only.

## Measured-cost pointers to carry (for L-COST)
- BTC funding measured 11.798%/yr = 7.824× frozen constant (BTC-H4-EDGE);
  SRLV 11.81/13.96%/yr; SOL funding sign autocorr +0.853.
- Fees: 5bps+1tick DECLARED (SRLV) — class: declared, not broker-measured.
- Spread censuses: SOL p50 0.469 bps; BNB (pws-bnb census in flight — do not
  read, metadata only).

## Gap candidates to draft
- Multi-year PIT OI / liquidation / L2 history (bear-recon: liquidation
  404; OI/L2 none) — with the no-candle-inference law stated.
- Spot–perp basis + mark/index PIT corpus for majors (CHR3F has partial —
  enumerate what it covers).
- Settled vs forecast funding: settled exists (8h); forecast funding stream
  (premiumIndex history) — gap?
- Exchange fee/rules history over time (vip tiers, changes) — status?
- Cross-venue (Coinbase/Kraken/Deribit) historical depth: PROSPECTIVE-only
  (coverage floors unmet) — record as WAITING_COVERAGE-class row with the
  14-day floors contract pointer.
