# DRAFT AMENDMENT A4 (v2) — PORTFOLIO ONE: SHARED $100K EPOCH-2, SLEEVES = FX-RANGEFADE-2M + BTC4H-BANDRIDGE

> **Status: DRAFT_FOR_OWNER_GO — NOT REGISTERED, NOT EXECUTED, NOT ACTIVATED.
> Gate A deliverable (plan + preview + independent review); STOPS HERE for
> owner approval.** Nothing is live law until the owner types this draft's GO
> phrase at its own gate. No worker stop/restart, no ledger mutation, no
> cutover, no decommission, no order, no S1, no scored run is authorized by
> this draft.
>
> **v2 (2026-09-25, owner directive)** supersedes v1's sleeve set and UI spec.
> v1 artifacts (engine, first preview app, screenshots) remain evidence under
> `research/control/SHARED-PORTFOLIO-100K-V1/`.
>
> Compatibility alignment: `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/PORTFOLIO_MIGRATION_COMPAT.md`
> (other lane's ruling, read-only here) — this consolidation is a NEW portfolio
> identity (working name **PORTFOLIO ONE / PORTFOLIO-CONSOLIDATION-V1**) that
> needs its own plan + review + owner GO; per-sleeve mount decisions; ILLIQ
> ineligible by construction (D5); A2 sizing-B needs re-expression on the
> shared book — solved here by **sleeve-fenced capital** (§4).

## 0. Identity

```text
umbrella cycles     FX-RANGEFADE-2M-SHADOW-V1 (USD sleeve) +
                    PROSPECTIVE-SHADOW-V1 sleeve 4 BTC4H-BANDRIDGE (USDT sleeve)
amendment id        A4-v2-portfolio-one-epoch2
computation home    research/control/SHARED-PORTFOLIO-100K-V1/
                    (portfolio_lib.py = verified data layer, UNCHANGED;
                     one/ = new minimal read model + single .app)
config of record    epoch_config.json @2 (status PENDING_OWNER_GO)
GO phrase (draft)   GO PORTFOLIO ONE EPOCH2 ACTIVATE T_STAR=<ISO8601_UTC>
                    OPEN_POSITION_LAW=<FLAT_START|REOPEN_AT_MARK>
```

## 1. What epoch 2 is

ONE shadow account with opening equity **100,000 USD-equivalent**, effective
only from `T_STAR`. Epoch-2 PnL starts at **0 at `T_STAR`**. No epoch-1 PnL
carries, no backfill, no relabeling; epoch-1 journals/ledgers/marks/hashes are
append-only evidence and stay the sole authority for history. "Reset" is an
epoch marker in the NEW book only (PORTFOLIO_MIGRATION_COMPAT §1).

**USDT=USD 1:1 is a REPORTING ASSUMPTION** (`usdt_usd_ref`, labeled on every
surface). USD and USDT remain separate books joined only by the declared
reference; no cross-venue transferability; this is a simulated paper account,
never a broker account.

## 2. Sleeve census (epoch-2 members = exactly two)

| Sleeve | Section | Class | Capital | Sizing law on the shared book |
|---|---|---|---|---|
| FX-RANGEFADE-2M (EURUSD+GBPUSD) | Forex | KEEP_PROSPECTIVE · **NOT_PROMOTABLE** | fenced $50,000 | 1.5 lot/pair/signal (frozen FX law) against sleeve capital; **GROSS/HYPOTHETICAL** — journal has no commission/slippage/funding fields (spread implicit in opposite-side fills); **cost/A1 gap DISCLOSED** (§6) |
| BTC4H-BANDRIDGE | Crypto | CONDITIONAL_KEEP · **A2 Phase A ACTIVATED** (T_act=2026-09-25T03:57:05Z) | fenced $50,000 | A2 sizing B (0.99946) + fill law A + 6 bps/side apply **to the sleeve capital** — fencing preserves the pins' semantics (solves COMPAT §2 re-expression); cost-regime digest boundary at T_act respected |

**Excluded from epoch-2 (continue under current law in their own append-only
books — no portfolio capital, no headline PnL):**

| Sleeve | Disposition | Authority |
|---|---|---|
| BASISLV-PREMFADE-28D | OBSERVATION_ONLY; price-only vs funding separated; no promote from thin sample | ERP/PSV1 current law |
| ILLIQ-AMIHUD-28D-W | DIAGNOSTIC_ONLY — **not eligible by construction** (ERP D5); gate D13 time-stop; no promotion/rescue | ERP D5 / §5.12 |
| XSECT-FUND-CARRY-7D | RETIRE_CURRENT_IDENTITY; run-off to flat; terminal row per A3 when GOed; successor needs new strategy ID | ERP §4.5 / PSCTV1-A3 draft |
| ETHUSDT-OPEN-SEARCH-V1 | TERMINAL (NO_INCREMENTAL_VALUE) | HYPOTHESIS_LEDGER |
| ETHUSDT-OPEN-SEARCH-V2 | ACTIVE_LIGHT at STOP-1 AWAITING OWNER GO — separate cycle, no self-granted GO | its own lane |

**Conflict statement (owner decision not needed — laws agree):** PSCTV1 A1
(2026-09-24) locked "no shared capital anywhere"; the owner's 2026-09-25
directives supersede it for epoch-2 only, exactly like A1 superseded the
original group design. No registry/worker change is made by this draft; the
supersession takes effect only via the GO. The old per-sleeve dashboards keep
running until the separate gate-B decommission GO (COMPAT §1 "additive, no
automatic cutover").

## 3. Accounting design (frozen BEFORE activation; precedes UI)

1. Opening equity 100,000 USD-eq at `T_STAR`; cumulative PnL = 0; per-sleeve
   fenced capitals 50,000 + 50,000 (allocation `EQUAL_2WAY` — the only
   performance-independent split for two sleeves; NOT tuned on seen PnL).
2. **Cost law**: FX sleeve PnL is GROSS/HYPOTHETICAL and is never displayed or
   summed as net (no fee/slippage/funding fields exist; spread is implicit in
   fills). BANDRIDGE carries its 6 bps/side executor cost with the A2
   cost-regime digest boundary. No gross number is ever labeled net.
3. **Shared-capital / risk check (R1–R5)**: risk-reducing closes always
   allowed; new risk in fixed order FX → BANDRIDGE; scale-down by
   min(class headroom, total headroom); BLOCK below min unit (0.10 lot / 10
   USDT); carried book grandfathered and displayed.
4. **Caps proposal (unchanged from the pre-PnL audit — deliberately NOT
   re-picked after seeing PnL)**: total gross ≤ 250% equity; FX ≤ 150%;
   crypto ≤ 150%; max aggregate stress loss ≤ 15% equity
   (`AUDIT_sizing_fx_shared_100k_v1.md`, corrected math $10/pip/lot). 1.5 lot
   against a $50k sleeve fence ≈ 730% of sleeve capital (~369% of the whole
   book). **ENFORCEABILITY (explicit, reviewer finding):** in this preview
   R1–R5 are DECISION-SUPPORT/DISPLAY ONLY — nothing enforces them on any
   worker (the workers keep their own frozen laws; the app is read-only).
   Until the owner defines an enforcement point (e.g. portfolio-level
   pre-trade check inside a future worker change, which needs its own
   amendment + GO), the frozen 1.5-lot FX law vs the 150% cap is a DISCLOSED
   CONFLICT, resolved only by an explicit owner sizing decision at/before GO
   — never by silent scaling.
5. **Open positions at `T_STAR`** — owner must choose in the GO:
   - `FLAT_START`: epoch-2 books start flat; open epoch-1 positions stay in
     their own books under their own laws; residual exposure displayed
     separately; nothing force-closed.
   - `REOPEN_AT_MARK`: epoch-boundary CLOSING row (mark, MTM PnL → epoch-1) +
     epoch-2 OPENING row (same symbol/dir/qty, entry = T* mark); exposure
     continuity, PnL splits at the mark, no cost-basis transfer.
   Cutover is BLOCKED until this choice exists.

## 4. BANDRIDGE mount (gate A2 interaction)

A2 Phase A is ACTIVATED (T_act=2026-09-25T03:57:05Z, other lane's authority —
read-only here). Mounting BANDRIDGE into epoch-2 does NOT modify A2 law; it
re-expresses the capital base via **sleeve fencing** ($50,000), which keeps
sizing B / fill law A / cost law byte-equivalent in semantics. Remaining A2
phases/tests belong to A2's own gate. If A2 later changes pins, the portfolio
inherits them only through a recorded config digest update — never silently.

## 5. FX gap statement (A1-controls)

The FX sleeve carries **KEEP_PROSPECTIVE · NOT_PROMOTABLE**: no short-beta
control, no explicit cost fields (commission/slippage/funding), no aggregate
USD-exposure report until the FX A1-controls amendment is GOed (draft in
`plans/DRAFT_amendment_FX-RANGEFADE-2M-SHADOW-V1_A1_controls.md`). The
portfolio view discloses this on every FX surface (GROSS/HYPOTHETICAL banner)
and does not wait for A1 to exist.

## 6. The single app (preview built; gate A)

ONE `.app` (PhorecOne) + GET-only loopback server. Read-only: no order
endpoint anywhere (pinned by test); closing the app never touches workers.
UI shows ONLY the two sleeves, grouped **Forex / Crypto**: one-account equity
chart ($100,000 baseline; NOT_ACTIVATED until GO — never a fabricated line),
PnL calendar day/week/month with per-day drill-down, pending orders, open
positions, closed trades, PnL, and per-sleeve data status + timestamps.
USDT=USD 1:1 labeled as reporting assumption. Backend read model is
adapter-based (`one/read_model.py`); default registry = the two sleeves;
**no auto-mount** — adding a strategy is an explicit config entry + written
adapter + owner GO. Old ledgers remain viewable as evidence (collapsed
"Trước khi reset" section), never summed into the new account.

## 7. Tests (gate A, all passing)

Reconciliation equity↔calendar↔trades; restart/idempotent replay (full
journal duplication); missing boundary marks → UNAVAILABLE (never $0); open
positions survive replay; USD/USDT reference changes move accounting; open-
position-law attribution (pre-T* open closing post-T* stays in epoch-1 under
FLAT_START; REOPEN_AT_MARK without a boundary manifest → UNAVAILABLE, never
silently booked); activation fail-closed (incl. PREVIEW_FORCED computing no
epoch-2 numbers); no-order surface. Engine suite from v1 (19 tests) still
passes unchanged — the verified data layer is reused, not rewritten.
**Cold launch of the built `.app` is a MANUAL check** (performed 2026-09-25:
binary start → loopback GET 200 → window open/close leaves workers running);
it is not an automated test.

## 8. Gate B (SEPARATE owner GO — inventory to be re-measured then)

Decommission candidates (dashboards only, NEVER workers/daemons; pids are the
2026-09-25 snapshot — re-measure at gate B):
1. `~/Applications/Phorec.app` + FX-worktree `dashboard/serve.py` (pid 8093,
   port 8766) — move aside Phorec-prev-<ts>.app style, restorable;
2. `research/control/SANDBOX-OVERFIT-3ASSETS/shadow_view_server.py` (pid
   22766, port 8765);
3. Quant Shadow Dashboard (`prospective-shadow-v1/dashboard/dashboard_app/`,
   port 8791) — pidfile records 57257 but NO listener at 2026-09-25 04:30Z
   (already stopped by its own lane); verify before acting.
Not touched at gate B: shadow daemon (pid 35609), PSV1 decision/valuation
workers, CHR3F scored run, any ledger/journal/audit/history, S1. Restorable
copies first, stop second, only with the owner's typed GO.

## 9. Non-goals

No worker restart/stop; no change to frozen strategy laws; no S1; no scored
run; no live broker anything; no push/merge; no epoch-1 rewrite; no allocation
or cap tuning on observed PnL; the preview is never called a running account.
