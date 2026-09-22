# PLAN EURUSD-DATA-QUALIFICATION-V1 — can a research-grade EURUSD dataset be built for a FUTURE Jev cycle?

> Status: `ACTIVE_LIGHT` (registered 2026-09-22 by A1 under explicit owner
> instruction of the same date). Owner anchors, verbatim intent preserved in
> §0a. S0 data research ONLY.

## 0. Cycle identity

```text
cycle_id     EURUSD-DATA-QUALIFICATION-V1
class        DATA QUALIFICATION (no strategy, no Jev calls, no PnL, no
             backtest of any strategy arm)
asset        forex (EURUSD only)
budget       0 scored cells (data qualification cycle; nothing is scored)
S1           SEALED_UNTOUCHED (not applicable — no strategy surface exists)
orders       NONE
go_phrase    NONE REGISTERED (no billable/model API surface; owner
             instruction of 2026-09-22 IS the authorization for the
             bounded probe; stage-2 full aggregation additionally requires
             the machine-wide heavy lock, not an owner GO)
forbidden    any JEV-REGIME-ROUTER-V1 surface: its plan, freezes, prompts,
             mapping, runtime, cache, worktree; research/control/
             SANDBOX-OVERFIT-3ASSETS/; research/control/d2_curiosity_v1_sources/
```

Scientific question: can a EURUSD dataset sufficient for a FUTURE
Jev-regime cycle (15m execution bars + H1 regime bars, bid/ask cost
authority, ≥4 chronological folds, ≥1,000 valid H1 decisions/fold after a
192-bar warmup) be built from identifiable, license-cleared, timestamp-clean
sources — or must it be blocked on license / coverage / timestamp / cost?

## 0a. Owner instruction anchors (2026-09-22, binding)

- "tuyệt đối chưa gọi Jev cho EURUSD và chưa backtest strategy".
- Giai đoạn 1 bounded probe: 7–14 ngày EURUSD M1/tick bid+ask từ Dukascopy;
  cùng khoảng từ Twelve Data; ghi source URL, retrieval time, terms/license,
  raw-byte digest; xác định timestamp UTC + candle-open/close convention;
  kiểm tra fields. Không full-history nếu license/schema chưa rõ. Không dùng
  wrapper làm authority nếu không truy ra nguồn gốc bytes.
- Giai đoạn 2 chỉ khi probe PASS: 3–5 năm; deterministic 15m execution bars;
  H1 regime bars từ ĐÚNG BỐN nến 15m; không interpolation; missing bar làm
  H1 invalid; weekend closure theo calendar thật; DST/timezone kiểm tra;
  raw bytes bất biến / normalized / manifests tách biệt; duplicate,
  monotonicity, OHLC invariants, gap census; đối chiếu H1 close với Twelve
  Data theo tolerance ĐĂNG KÝ TRƯỚC; không ép hai vendor giống nhau.
- Volume: không có centralized volume — không gọi tick count là "true
  volume"; báo `tick_activity_proxy`; KHÔNG tự thay f15 `vol_z` của JEV;
  kết luận riêng a) tick-activity proxy + feature identity mới, hay b) bỏ
  volume feature + contract/prompt identity mới. Quyết định này TRƯỚC mọi
  Jev call/PnL của EURUSD.
- Cost authority: spread median/p75/p90/p95/p99; theo phiên Asia/London/NY;
  rollover; weekend/mở cửa tuần; entry/exit next-bar-open; base cost +
  stress 1.5×/2×. Thiếu bid/ask lịch sử ⇒ verdict
  `BLOCKED_COST_AUTHORITY`; cấm bịa fixed spread để PASS.
- Data floor: warmup ≥192 H1 bars; ≥4 folds chronological; mục tiêu ≥1,000
  valid H1 decisions/fold sau warmup; báo exact first/last timestamp,
  valid/invalid count, margin-to-floor.
- Scope: read-only research; không broker/MT5/OANDA repair; không
  paper/live; không S1; không PnL; không strategy selection; không sửa JEV;
  không commit raw vendor data nếu license/size không cho phép; không push.
- Verdict (đúng một): `EURUSD_DATA_QUALIFIED` | `BLOCKED_SOURCE_LICENSE` |
  `BLOCKED_COVERAGE` | `BLOCKED_TIMESTAMP_OR_GAPS` | `BLOCKED_COST_AUTHORITY`
  | `TECHABORT`. `EURUSD_DATA_QUALIFIED` KHÔNG có nghĩa strategy tốt hay Jev
  có edge.

## 1. Sources

- PRIMARY candidate: Dukascopy Bank SA public historical datafeed
  (`https://datafeed.dukascopy.com/datafeed/EURUSD/<YYYY>/<MM-1>/<DD>/<HH>h_ticks.bi5`,
  LZMA, per-tick bid/ask, month 0-indexed). No account required to fetch;
  license/terms must be recorded verbatim URL + retrieval time. If the
  datafeed bytes cannot be attributed to Dukascopy terms, status is
  `CANDIDATE_NOT_AUTHORIZED` and the verdict cannot be QUALIFIED.
- RECONCILIATION (independent, never patches PRIMARY):
  Twelve Data `EUR/USD` time_series (1min/day) via `TWELVE_DATA_API_KEY`
  from root `.env` (env-only; never printed/committed).
- No other source is authority. Wrapper libraries may TRANSPORT bytes but
  provenance must resolve to the raw endpoint URLs above.

## 2. Preregistered reconciliation tolerance (frozen BEFORE any diff is computed)

Two vendors WILL differ (different snapshots/aggregation); the goal is
bounded divergence, not equality. For each compared H1 close:
`|close_dukascopy − close_twelvedata| ≤ max(1.5 pips, 3 × spread_p50 of the
same hour)` counts as MATCH. Report the FULL divergence distribution
regardless (median/p95/max, count-out ratio, by-session breakdown). A
match-rate ≥95% of compared hours is `RECONCILIATION_PASS`; 85–95% is
`RECONCILIATION_THIN` (disclosed, verdict may still qualify only if the
divergence mechanism is identified, e.g., rollover bars); <85% is
`RECONCILIATION_FAIL` → `BLOCKED_TIMESTAMP_OR_GAPS` unless the divergence
is fully explained by a named, verified convention difference AND the
primary source is internally consistent.

## 3. Stages and gates

```text
P1 BOUNDED PROBE (LIGHT, no heavy lock):
   10 consecutive days (2024-03-04 → 2024-03-14 UTC, a known FX week
   containing a US DST switch on 2024-03-10) of Dukascopy EURUSD tick
   bi5 bid/ask + the SAME window from Twelve Data 1min. Record: source
   URLs, retrieval times, license/terms URLs + verbatim quotes, raw
   byte sha256, timestamp decoding (epoch ms UTC, candle open/close
   convention), field inventory, coverage census, gap census.
   GATE P1 → probe verdict PROBE_PASS / PROBE_FAIL (fail = any of: license
   unresolved, schema uninterpretable, timestamps ambiguous, coverage
   broken). PROBE_FAIL stops the cycle at the matching BLOCKED_* verdict.
P2 QUALIFICATION (heavy lock REQUIRED for the full download; light prep
   allowed anytime): 3–5 years Dukascopy ticks (target 2021-01-01 →
   2025-12-31 UTC window), immutable raw bytes (gitignored, manifest
   digests only in git), deterministic 15m execution bars (bid/ask
   separately: open=first tick, close=last tick, high/low=extremes,
   tick_count, NO interpolation), deterministic H1 from EXACTLY four
   consecutive 15m bars (missing 15m ⇒ H1 INVALID), weekend closure by
   the real FX calendar (Fri 21:00/22:00 UTC → Sun 21:00/22:00 UTC
   measured from data, not assumed), DST/timezone checks vs 2024-03-10
   anchor, duplicate/monotonicity/OHLC-invariant/gap-census checks,
   Twelve Data H1-close reconciliation per §2, cost authority per §4,
   data floor per §5, tick_activity_proxy decision per §6.
P3 VERDICT + A7: single verdict enum + evidence bundle; fresh-context A7
   audit of the verdict artifact; remediation only for A7-found technical
   errors; registry update; STOP.
```

## 4. Cost authority (measured, never stated)

From historical bid/ask (execution = marketable order at the OPPOSITE
side's quote; a buy fills at ask, a sell at bid):
spread(t) = ask(t) − bid(t) at the bar-close decision tick and at the
next-bar-open fill tick. Report p50/p75/p90/p95/p99 in pips; by session
(Asia 00:00–07:00, London 07:00–12:00, overlap NY 12:00–16:00,
NY-late 16:00–21:00 UTC); rollover hour (21:00–22:00 UTC) separately;
Sunday-open and Friday-close separately. Base cost = median next-bar-open
spread; stress tiers 1.5× and 2.0×. If historical bid/ask is unusable →
`BLOCKED_COST_AUTHORITY`. A FIXED invented spread is FORBIDDEN.

## 5. Data floor

Warmup 192 H1 bars; ≥4 chronological folds (equal-length decision spans);
target ≥1,000 valid H1 decisions per fold after warmup; report exact
first/last timestamp, valid/invalid counts per fold, margin-to-floor
(valid/floor ratio). Floor miss ⇒ verdict downgrade to `BLOCKED_COVERAGE`.

## 6. Volume identity (blocking decision for any future Jev-EURUSD cycle)

FX has no centralized volume. This cycle must END with exactly one of:
a) `VOLUME_TICK_ACTIVITY_PROXY` — future extension defines a NEW feature
   identity (e.g., f15' = tick_activity_z with its own prompt schema) —
   the JEV f15 `vol_z` identity is NOT portable;
b) `VOLUME_FEATURE_DROPPED` — future extension runs a 15-feature contract
   without any volume feature, new contract/prompt identity.
The decision is recorded in the verdict and MUST precede any future Jev
call/PnL for EURUSD. No change to JEV-REGIME-ROUTER-V1 is authorized here.

## 7. Boundaries

- Read-only market research; no orders, no broker, no MT5/OANDA repair, no
  paper/live, no S1, no PnL, no strategy selection or comparison.
- Raw vendor bytes: stored under the cycle's `data_local/` (gitignored);
  only digests + manifests + normalized derivatives are committable; no
  bulk raw commit.
- One heavy job machine-wide: stage-2 full download acquires
  `governance.heavy_lock`; NEVER while JEV-REGIME-ROUTER-V1 holds the lock.
- Lanes never merge/push; A1 integrates via cherry-pick on the cycle
  integration branch; registry only via researchctl.
- Owner-untracked dirs (SANDBOX-OVERFIT-3ASSETS/, .zcode/,
  d2_curiosity_v1_sources/) never touched.
- Structured handoff (`zcode_orch_v3_handoff@1`) ends every dispatched task
  at its exact `handoff_path`.
