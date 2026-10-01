# HANDOFF_TO_PORTFOLIO_CHAT — data lane → successor-cycle integrator (2026-10-01)

Coordination surface per owner instruction: **committed evidence only**
(this branch; nothing in your worktree is touched). Read this file plus the
artifacts it names; do not edit this lane's directory.

## Source of truth

- Branch `orca/pc12a-7asset-unblock-20261001`, worktree
  `.worktrees/pc12a-7asset-unblock-20261001`, control dir
  `research/control/PC12A-7ASSET-DATA-UNBLOCK-2026-10-01/`.
- Commit chain: `f947fc19` (session 1 acquisition/validation) → `eaea0116`
  (handoff close) → `8b8c24a5` (amendment 1: D-1 fixes + skeptic) →
  `cbae7556` (session 2: gate table v2 + IBKR RO probes + skeptic) →
  **this commit** (rev 3: point-2 status, checklist, this handoff).
- Raw bytes (never in git): `~/.my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/`
  — 15 session-1 files + 4 staleness files (`MANIFEST_RAW.json`, sha256 per
  file) and `raw/ibkr_ro_20261001/` 13 files (`MANIFEST_IBKR_RO.json`).
  IBKR session-1 panels: `~/.my-quantitative-data/portfolio-composite-12assets-100k-v1/ibkr_acq_20260930/`
  (131 files, DV-verified 2026-09-30, identity frozen).

## Exact gate deltas this lane delivered (vs 2026-09-30 baseline GATE_TABLE_7ASSETS)

| gate | before (09-30) | after (this lane) | class |
|---|---|---|---|
| NZDUSD/USDCHF PIT basis | NOT_RUN | **MEASURED** (FRED p50 9.38/9.32 bps; ECB 21.52/18.43; per-year tables) | data+measurement |
| NZDUSD/USDCHF availability | NOT_RUN | **MEASURED point-1** same-evening closed bar (22:52 ET) + forming next-fx-day bar; point-2: see AVAILABILITY_EVIDENCE rev of this commit | measurement |
| XAUUSD PIT | MEASURED (TD) | re-reproduced exact (p50 3.2462) + GLD proxy r 0.9857 (proxy-class) | verification |
| XAGUSD PIT archive | NOT_RUN | **MEASURED-BLOCKED on every free/lawful path from this environment** (TwelveData plan-gate, stooq in-browser denial, LBMA Cloudflare, Yahoo ToS, SGE template-only) | measured negative |
| BRENT/WTI/NATGAS signal price | BLOCKED_NO_PRICE_DATA (NG) / dossier-only | **PASS as signal-side** — EIA official dailies span-complete, dual-channel retrieval-confirmed, SINGLE-SOURCE label; serving lag 1bd (2 manifested obs) | opened |
| Futures execution chain | FAIL (probe) | **CONFIRMED FAIL, now exhaustive**: expired months 16/16 unresolved (2 resolution shapes); ADJUSTED_LAST channel exists but divergence ≤$1.73/$1.11/$0.057 per 6y → not a certified adjustment; roll rule absent in API | measured negative |
| Energy front spreads | REPORT_ONLY (F-3) | **MEASURED-SAMPLE** 29-30d: COIL 12.60 / CL 3.23 / NG 6.54 bps p50 | data |
| Costs (commission/swap/slippage) | NOT_RUN | still **NOT_RUN_STATEMENT** (owner export — OI-2) | unchanged, owner-gated |
| Coverage | daily span only | **quantified**: archive cover 96-99.2%, isolation 1-12d, streaks 1531-1552d; CONTFUT flat-by-year (synthetic backfill boundary: clean only 2025+ BRENT/WTI, 2024+ NG) | measurement |
| FRED FX channel timeliness | unknown | **MEASURED-BLOCKED as timely source** (≥3bd serving lag, 2 manifested obs) — historical cross-check only | measured negative |

## Hard laws the successor must inherit (already encoded in DRAFT_AMENDMENT_SUCCESSOR.md)

1. Proxies (SLV/GLD), CONTFUT (TRADES or ADJUSTED_LAST) and EIA spot are
   **never executable futures prices** — signal-side/proxy evidence only.
2. CONTFUT not admissible as price evidence before 2025-01-01 (BRENT/WTI) /
   2024-01-01 (NATGAS) — flat-OHLC majority per COVERAGE_REPORT.
3. FRED FX channel is never a timely signal source (≥3bd measured).
4. PIT PASS only under an evidenced or DECLARED (labeled) availability
   protocol; thresholds per the σ-law (tripwire 1σ/5σ/0.5σ; tight bars
   demote ECB; bar never moved to fit data).
5. Pre-cost results are not admissible as survival evidence (statement =
   OI-2).

## Open items the successor inherits (owner checklist: OWNER_INPUT_CHECKLIST.md)

OI-1 availability declaration + threshold freeze · OI-2 statement export ·
OI-3 XAU pin · OI-4 XAG archive (or panel-of-record declaration) · OI-5
certified chain + subscriptions (+ AECO/TTF naming) · OI-6 registration.

## Point-2 (next-business-day persistence): EXECUTED

2026-10-01T04:00:32–34Z (Thu 00:00 ET): the 2026-09-30 closed bar persisted,
with closes landed, on all 7 instruments; forming 10-01 bar live on the 4
FX/metals. Energy 10-01 absent on TRADES is a CHANNEL property (the 10-01
sessions were already open per d5 hours; ADJUSTED_LAST serves that forming
bar) — not closure. Class
`PERSISTENCE_PRESENCE_MEASURED_2pts`; value-stability across points not
measurable (point-1 stored dates only) — point-2 landed closes, so one
future re-run closes that gap (`ibkr_point2_probe.py` ships in-repo; no
connector is ever self-scheduled). Full detail: `AVAILABILITY_EVIDENCE.json`
rev 3 + `d1_point2_result.json` (manifested).

## Session-3 addenda (this commit)

- Point-2 executed as above (label change: availability cells).
- SGE (last lawful free XAG candidate): public pages serve HTML templates
  only; the quoted data URL returns a page, not data; deeper AJAX
  reverse-engineering NOT attempted (site carries an explicit /data_Licensed
  page). Recorded — XAG free-path verdict unchanged: measured-blocked.
- Light independent recheck of headline numbers from raw: all confirmed
  (NZD/FRED p50 9.3832, XAU/TD 3.2462, EIA HH 1496 rows, ECB-vs-FRED 100%
  nonzero). One recheck-side arithmetic slip (WTI median index) was
  diagnosed — the gate-table value 3.225 is correct; checker fixed.
