# THIRD-PARTY NOTICES — vendored edge-scanner components

## edge-scanner (`research/platform_tools/thirdparty/edge-scanner/`)

Source: https://github.com/simonro/edge-scanner @ `c927dcb0c5e8122269812d2cdfdc4a3ae71b2ab3`
License: **MIT** — full text in `LICENSE` (vendored verbatim). Copyright (c) 2026 "Tape to Edge".
Vendored under cycle EDGE-SCANNER-TOOLING-V1 (GO-1, owner decision recorded
2026-09-26); see `VENDOR_PIN.md` for digests and the re-pin law.

Vendored component: `scanner/local_guard.py` (localhost-only ASGI guard
middleware). Its only third-party runtime dependency is `starlette`
(`starlette.responses.JSONResponse`), installed in the workspace `.venv` as
`starlette 1.7.0` + `anyio 4.15.1` (additive; no existing package upgraded).

The upstream `NOTICE` (vendored verbatim) additionally names:
- TradingView Lightweight Charts (Apache-2.0, attribution-logo requirement) —
  a dependency of upstream's `dashboard-v2`, **not vendored here**; the
  obligation would attach only if any chart code were ever vendored (forbidden
  by plan §0 non_goals).
- schwabdev (MIT) — a dependency of upstream's Schwab provider, **not vendored
  here**.

Runtime market data/news fetched by the full upstream project (Alpaca, Yahoo,
Nasdaq, yfinance, Schwab) is NOT part of this vendoring and carries no
obligation for this workspace: we vendor no provider code and run none of it.
