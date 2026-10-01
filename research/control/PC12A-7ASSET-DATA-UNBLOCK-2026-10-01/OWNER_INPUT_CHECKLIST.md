# OWNER_INPUT_CHECKLIST — minimal owner inputs per asset (2026-10-01, lane rev 3)

One action per line, no technical placeholders — everything else is already
measured and committed on `orca/pc12a-7asset-unblock-20261001`
(`cbae7556`+). Defaults are fail-closed: doing nothing keeps every current
label. **Proxies (SLV/GLD), CONTFUT (TRADES or ADJUSTED_LAST) and EIA spot
are NEVER executable futures prices — they are signal-side/proxy evidence
only; execution legs need D-4.**

## Cross-asset (one decision covers multiple assets)

- [ ] **OI-1 · PIT availability law (NZDUSD, USDCHF, XAUUSD, XAGUSD + energy
  signal).** Choose ONE: (a) declare IBKR HMDS D1 panel-of-record with
  availability = same-evening closed-bar (measured point-1; point-2 status
  in AVAILABILITY_EVIDENCE) labeled `LAG_DECLARED_BY_OWNER (DECLARED, NOT
  MEASURED-beyond-point-evidence)`; or (b) fund a vintage/publish-timestamp
  measurement. Also freeze cross-check thresholds per the σ-law
  (OWNER_PACKET v2 D-1b — tripwire 1σ/5σ/0.5σ, tight bars demote ECB, bar
  unmoved). *Without this: PIT stays MEASURED_BASIS, unfrozen.*
- [ ] **OI-2 · IBKR Activity/Flex statement export (all 4 spot/metals at
  once).** Export FX trades + Interest Accruals to
  `~/.my-quantitative-data/ibkr_statement/`. This is the ONLY remaining
  unmeasured cost component (commission/swap/slippage; spreads already
  measured 6y). *Without this: costs stay NOT_RUN_STATEMENT and after-cost
  evaluation is impossible.*
- [ ] **OI-3 · XAU archive canonical pin.** Pin the forex-ng6 staging path
  (sha `49c2684e…`, re-verified twice) or order a manifested copy under a
  `research/control/` data home. One line. *Without this: F-2 stands.*

## Per asset

- [ ] **NZDUSD / USDCHF** — nothing asset-specific remains. Data-ready
  (daily clock) under OI-1 + plan amendment; class-(b) rows (5+4 triage
  rows) become admissible inputs upon registration.
- [ ] **XAUUSD** — OI-1 + OI-3 only. (GLD proxy is second-check evidence,
  never a panel.)
- [ ] **XAGUSD** — **OI-4 · name the independent silver archive.** Every
  free/lawful path from THIS environment is measured-blocked (TwelveData
  plan-gated; stooq "Access denied" served to a real browser; LBMA
  Cloudflare; Yahoo ToS-rejected; SGE serves only an HTML template without
  deeper AJAX work, which was not attempted — licensing page on-site).
  Choose: (a) YOU download a silver daily CSV from a vendor of your choice
  on YOUR browser/network into
  `~/.my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/raw/owner_drop/`
  and say "XAG archive dropped" (lane re-runs the frozen join); (b) declare
  IBKR panel-of-record under OI-1(a) and accept no independent spot archive;
  (c) accept the SLV proxy as cross-check (weakest, proxy-class only);
  (d) buy a licensed feed (a purchase — needs your explicit authorization,
  none exists today).
- [ ] **BRENT / WTI / NATGAS** — **OI-5 · certified futures chain + roll
  rule + entitlement** (execution side only; signal side is done and
  adoptable via the draft amendment): name the certified outright/back-
  adjusted source (licensed vendor, ICE/CME-direct, or accept a CONTFUT
  convention WITH the synthetic disclosure — measured: expired months
  16/16 unresolved via IBKR; ADJUSTED_LAST divergence ≤$1.73/6y = not a
  real adjustment; no free certified source exists from this network), AND
  enable ICE(IPE)/NYMEX market-data subscriptions on the paper account if
  live quotes are wanted. NATGAS additionally: AECO + TTF are not IBKR
  instruments — name those hub sources or drop those two corpus rows.
- [ ] **All 7** — **OI-6 · register the successor cycle** (draft:
  DRAFT_AMENDMENT_SUCCESSOR.md). Registration is owner-only; any GO is
  typed at that cycle's own gate, never here.

## What does NOT need the owner (already done, evidence committed)

Spreads measured (6y, 4 spot/metals; 29-30d sample, 3 energy fronts);
cross-source bases measured (FRED/ECB/TD/EIA, byte-evidenced); independence
split stated vs byte-evidenced; coverage/interior gaps quantified (no holes
>5d anywhere; FX archive cover 96-98.7%, streak 1552d); same-evening
closed-bar availability point-1 measured on all 7; FRED channel lags
measured 2 manifested points; every negative (expired months, ADJUSTED_LAST
as chain, XAG browser paths, blocked estates) measured and recorded, not
assumed.
