# PACKET — L-ST (stocks data census + validation)

ROLE: A3-class data-authority survey lane. OBJECTIVE: complete §5 authority
rows + gap candidates for every STOCKS dataset the program holds or has held.
WORKTREE: `/Users/hoangminhlong/my-quantitative/.worktrees/data-foundation-v1/lane-st`
BRANCH: `orca/dfv1-lane-st`. Allowed writes: `research/control/DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1/stocks/` only. COMMON.md applies in full.

## Owner priority list (verbatim from OWNER_DIRECTIVE.md)
Stocks: universe không survivorship bias, symbol/identifier history,
split/dividend và corporate actions biết tại thời điểm đó; trades/quotes với
phạm vi SIP/IEX được ghi rõ; earnings/filings có publication timestamp và
revision; halts/auction, borrow/short fees nếu định short; chi phí khớp lệnh
thực tế.

## Census targets
1. EODHD "All World" entitlement (owner-held token in .env — NEVER read the
   key; only record channel rulings from terminal verdicts). Known rulings:
   EOD + US ETP EOD entitled & used (RATES/VOL/COMMODITIES legs; STOCKS-NG6
   panel 2,169 symbols 3.21M rows; AMIHUD cycles delisted-inclusive EOD with
   L-SAMV1-1/2/3 defect laws: reverse-split adjustment NOT smoothed, ghost
   series HTV/NLG, volume-0 bars). Locate panels:
   `.worktrees/stocks-search-v1/` (2.2 G), `stocks-amihud-v1/`,
   `stocks-amihud-retest-v1/`, `stocks-ng6/` — enumerate datasets (per-panel
   rows: symbols, window, adjusted-vs-raw, manifest status). Earnings-history
   channel 403 (STOCKS-NG3) — BLOCKED_ACCOUNT-class row with reopening
   condition.
2. SEC EDGAR substrates (all entitled, declared UA):
   - Form-4 substrate 345,150 XMLs, digest `5d351623…` — locate on disk or
     in `~/staging_backups/` (+ `research/control/staging_backups_manifest.md`);
     status from digest verification (SAMPLED) if present.
   - 4/A amendment corpus 3,062 docs / 1,877 pairs (STOCKS-NG2).
   - FTD full archive 434 zips 2009-07..2026-08 + N-PORT 2026q2 QQQ 102
     holdings + per-file posting-timestamp machinery —
     `~/.my-quantitative-data/free-data-frontier-v1/` (1.0 G) and
     `data-edge-unlock-v1/` (420 M). FTD ≥17-day binding guard (P-26) is a
     PIT contract fact — record it in the row's timing fields.
   - Form-15 death-inclusive cohort census (12B/12G taxonomy) — locate.
3. OFR + NY Fed reference rates (`free-data-frontier-v1r1/`, 276 K) — rows
   with RETRIEVAL_TIME_ONLY ruling.
4. Stooq bulk bundle (owner-downloaded, canary-killed — P-7) + Twelve Data
   Basic (killed) — historical ruling rows (why they can never be primary).
5. FINRA short-sale volume — BLOCKED_LICENSE terminal ruling (P-25), row
   with reopening = FINRA data license.
6. Shared macro that stocks cycles consumed (Treasury par yields, CBOE VIX
   family, FRED granted set) — enumerate with locations (worktrees of
   RATES-NG1/VOL-NG1/COMMODITIES-NG1 + vintaged FRED S2) as cross-asset
   rows (flag asset_class shared; L-PIT will consolidate).

## Gap candidates to draft
- Earnings history with publication timestamps + revisions (EDGAR 8-K/10-Q
  acceptance datetimes exist and are entitled — what a probe would cost;
  vs EODHD entitlement upgrade).
- Trades/quotes with explicit SIP/IEX scope (none on disk — status,
  channels, cost: IEX historical keyless-ish? Alpaca? — runbook inputs
  only, no signup).
- Corporate actions point-in-time (EODHD adjusted series is NOT PIT-safe:
  L-SAMV1-1; what PIT corp-action feed would fix it — EDGAR 8-K + ex-date
  calendars?).
- Borrow/short-fee history for short-side families (no source on disk).
- Halts/auction calendar (none on disk).
- Identity mapping (ticker↔CIK/ISIN with dates) — partial via Form-15/FTD
  machinery; enumerate what exists.
- Real execution cost basis for equities (SIP vs IEX pricing, spread by
  liquidity bucket — no measured source; note Q-2).
