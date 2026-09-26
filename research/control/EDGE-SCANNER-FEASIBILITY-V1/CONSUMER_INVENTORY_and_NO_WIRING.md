# CONSUMER INVENTORY & NO_WIRING DECISION — EDGE-SCANNER-TOOLING-V1 GO-2 precondition

```yaml
decision_id: NO_WIRING_2026-09-26
decided_utc: 2026-09-26 (owner-delegated closeout session)
decided_by: Lead under owner delegation 2026-09-26 ("Việc 2 — tự quyết consumer... Nếu
            không có consumer ASGI phù hợp, quyết định NO_WIRING và ghi lý do")
method: code-measured inventory (grep + read of every local-server surface in the root
        checkout AND all worktrees), NOT from diagrams or plan prose
```

## 1. Measured inventory of every local server surface

| # | Surface (code path) | Framework — MEASURED | Owning cycle | Bind | Write surface? | ASGI-compatible? |
|---|---|---|---|---|---|---|
| 1 | `research/control/SANDBOX-OVERFIT-3ASSETS/shadow_view_server.py` | stdlib `http.server` `ThreadingHTTPServer` + `BaseHTTPRequestHandler` (:14, :222) | PROSPECTIVE-SHADOW-V1 (read-only web view) | 127.0.0.1:8765 | read-only GET | **NO** (no ASGI, no WSGI) |
| 2 | `research/control/SHARED-PORTFOLIO-100K-V1/one/serve_one.py` (+ `one_app_entry.py`) | stdlib `http.server` (:14, :174) | SHARED-PORTFOLIO-100K-V1 (PhorecOne review build, "epoch2 NOT activated") | 127.0.0.1:8768 (fallback: ephemeral) | read-only GET | **NO** |
| 3 | `research/control/SHARED-PORTFOLIO-100K-V1/phorec2/serve_phorec2.py` (+ `phorec2_app_entry.py`) | stdlib `http.server` (:25, :212) | SHARED-PORTFOLIO-100K-V1 (review build; does NOT replace running Phorec 8766) | 127.0.0.1:8767 | read-only GET | **NO** |
| 4 | `research/control/SHARED-PORTFOLIO-100K-V1/crypto_view2.py` | stdlib `http.server` (:15) | SHARED-PORTFOLIO-100K-V1 (Shadow Monitor v2 PREVIEW) | 127.0.0.1:8776 | read-only GET | **NO** |
| 5 | live gateway `.worktrees/live-data-gateway-v1/integration/research/live_gateway/service.py` | **aiohttp.web SERVER**: `from aiohttp import web` (:19), `build_app() -> web.Application` (:538), `web.Application()` + `web.AppRunner` + `web.TCPSite` (:720-733); routes: REST GET `/health /v1/status /v1/prices/latest[/sym] /v1/bars /v1/basis /v1/funding /v1/metrics` + **WebSocket `/ws/market`** (:681); upstream egress via aiohttp `ClientSession` (restgate/wsadapter) | LIVE-DATA-GATEWAY-V1 (listener committed `b2dbbf44` 2026-09-21, remediated `7c0ad5b9` 2026-09-22) | `config.py:14-15` DEFAULT_BIND `127.0.0.1`, DEFAULT_PORT `8792` | REST GET-only; **WS upgrade accepts connections** | **NO** — aiohttp.web is its own server API, not ASGI (no scope/receive/send) |
| 6 | Lab dashboard `research/governance/lab_app.py` via `LabDashboard.command` | pywebview 6.2.1 desktop app wrapping static `dashboard/index.html` (no HTTP server; explicit no-network law) | governance / dashboard program | local OS window | no | N/A |

Additional sweep evidence: repo-wide grep (root + all worktrees, `*.py`) for
`FastAPI(|uvicorn.|from flask|tornado.web|Starlette(|daphne|hypercorn|litestar`
→ zero hits; the only ASGI-family code in the repo is the vendored `local_guard`
itself (this cycle). The one aiohttp.web server is row 5 (gateway worktree).
Corrections ledger: the first draft of this file wrongly recorded row 5 as
"ClientSession only, no listener" (author's grep pattern truncated the hits);
caught and evidence-corrected by the independent A7 delta review, then
re-verified by the Lead against service.py:19/:538/:681/:718-733 and
config.py:14-15 before this corrected version was committed. The NO_WIRING
conclusion is unchanged by the correction; the evidence for it is now accurate.

## 2. ASGI applicability verdict

`local_guard.LocalOnlyMiddleware` is pure-ASGI (`scanner/local_guard.py:87-109`:
scope/receive/send, `scope["type"] in ("http","websocket")`). Of the measured
surfaces: rows 1–4 are stdlib `BaseHTTPRequestHandler` apps (no ASGI, no WSGI —
an ASGI middleware cannot wrap them without an adapter layer that WOULD be a
covert framework change); **row 5 IS a real local server — an aiohttp.web
listener at 127.0.0.1:8792 with REST GET routes and a WebSocket upgrade
(`/ws/market`) — but aiohttp.web is not ASGI** (its app/middleware API is
handler-based; there is no ASGI scope/receive/send contract to wrap), so the
vendored guard cannot mount on it either; row 6 is not a network server.
Owner's constraint honored verbatim: "không ép ASGI guard vào chúng, không đổi
framework ngầm".

## 3. Decision: **NO_WIRING**

- **No suitable ASGI consumer exists today** → GO-2 (`GO EDGE SCANNER TOOLING V1
  WIRE <CONSUMER>`) has no legal target; per owner delegation this is decided
  NO_WIRING rather than left pending.
- What a future wiring WOULD require (documented, not executed): either (a) a
  future local surface built ASGI-native (FastAPI/Starlette/litestar), where the
  vendored guard mounts directly; or (b) a framework-native port of the guard's
  three checks (Host allowlist / same-machine Origin for unsafe+WS / JSON
  content-type for POST) as an aiohttp middleware (row 5) or http.server wrapper
  (rows 1–4) — a reimplementation decision with its own fidelity tests, not a
  silent reuse of the ASGI bytes. Either path = new owner decision; for row 5
  the LIVE-DATA-GATEWAY-V1 amendment law governs (its plan + A7 audit trail),
  and plan §3's GO-2 row stands as the phrase template.
- Residual-risk note (HONEST, corrected per A7 delta finding 1): row 5's
  WebSocket upgrade (`/ws/market`) is exactly the exposure class this guard
  addresses (cross-origin WS from a foreign page against a loopback listener
  with no Origin check measured in the gateway code). This cycle does NOT
  mitigate it and must not be read as having done so: the mitigation paths are
  (i) an aiohttp-native Origin/Host guard implemented under
  LIVE-DATA-GATEWAY-V1's amendment law (recommended reading of the vendored
  guard's refusal() logic as the spec), or (ii) the owner deciding otherwise.
  Rows 1–4 are read-only GET views on loopback with no write surface; their
  DNS-rebinding read-exposure is bounded (no state to mutate) and noted for
  their owning cycles, not this one.

## 4. Consequence for cycle state

GO-1 deliverable (vendored + tested + A7'd) is complete and verified; with
NO_WIRING there is no remaining in-scope work item. Cycle closeout therefore
proceeds to TERMINAL (see CLOSEOUT.md for the parked-vs-terminal reasoning).
The vendored artifact persists in worktree branch
`orca/edge-scanner-tooling-v1-integration` @ `938e80e3`; it is NOT on main
(merge-to-main is an owner-only lever; nothing needs it while unwired).
