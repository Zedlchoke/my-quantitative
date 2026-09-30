# INVENTORY_AND_DESIGN — Triple-Barrier Research (Lane TB) — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1

Status: PRE-GO DESIGN + INVENTORY artifact. Verified against worktree
`orca/portfolio-composite-12assets-100k-v1-integration @ a812e73e80f74f12e0819530502f11e3db88d6d2`.
**NO PnL exists or is computed here. NO backtest, NO eligibility change, NO arm
admitted, NO threshold tuned.** This document registers the exit-law inventory
of every implemented leg and the frozen DESIGN of two separated outputs
(TB-LABELS analysis-only; TB-EXIT-OVERLAY research arm class) plus the
variant/budget registration that must precede any PnL, per the owner directive
(amendment 2026-09-29 §2: every exploratory computation is a ledger row;
acceptance bar untouched).

Code citations are `file:line` at the verified HEAD. Corpus citations are
`FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/symbols/<SYM>.md` (Trade/Signal lines).

## 0. Inventory ground truth (count reconciliation)

- `research/pc12a/legs_config/` holds **76 frozen leg configs** = **67 corpus
  legs** (`POOL_B_TRIAGE`) + **9 VOLPROF class candidates** (`POOL_B_VOLPROF`,
  VC1/VC2/VC3 × EURUSD/GBPUSD/USDJPY). The dispatch packet said "66 implemented
  legs"; the direct count at this HEAD is 67 corpus legs — the packet's number
  is off by one and 67 governs (both counts include the same 3 exemplar legs
  USDJPY-S001 / GBPUSD-S027 / EURUSD-S009 implemented in `legs.py`).
- `TRIAL_LEDGER.jsonl` carries 85 A-MECH rows = 76 config legs + 9 `PARKED_IMPL`
  rows (gids with no config: inputs not staged). Config-leg results:
  `IMPLEMENTED` 61 corpus + 6 VOLPROF; `FLOOR_FAIL` (pre-PnL decision-count
  kill, <20 decisions) 6 corpus (EURUSD-S027, USDJPY-S001, USDJPY-S009,
  USDJPY-S029, USDJPY-S044, USDJPY-S045) + 3 VOLPROF (VC1 × 3 pairs).
- Of the 67 corpus legs, **14 (AUDUSD 8 + USDCAD 6) are implemented but
  NOT_RUN** on this checkout: no staged M1 panels for those symbols
  (`build_wave1_ledger.py` `UNSTAGED_SYMBOLS`; stageA manifest note).
- M1 panels exist **only for EURUSD, GBPUSD, USDJPY** (`panels.py` panel roots).
  Every intraday leg (all `MinuteRuleLeg` subclasses, including "H1/H4" clock
  legs) is fed the **M1 stream** and aggregates its own coarser clocks from it —
  so minute-resolution sub-paths are available for the 3 M1 pairs even for
  H1/H4/D1-evaluation legs. The 7 blocked new assets (NZDUSD, USDCHF, XAUUSD,
  XAGUSD, BRENT, WTI, NATGAS) are daily-data-only and BLOCKED (amendment §3);
  no implemented leg runs on them today.

Exit-class legend used below: **TP** = level take-profit (incl. ratcheting
targets and z/EMA9 targets evaluated on closes); **SL** = level stop (initial
or standing); **TRAIL** = ratcheting/trailing stop; **TIME** = time/session/
window stop; **SIG** = signal/rule-state exit (vote flip, gate state, rule
condition). "SIGNAL-EXIT-ONLY" = no TP/SL/TRAIL/TIME at all.
Check basis: **C-D1** = evaluated on the completed D1 bar's close
(`DailyRuleLeg._manage`, `leg_rules.py:348-360`; daily decision at 00:00 UTC,
fill at the day's first tradable M1 bar, `leg_rules.py:10-13`); **C-M1** =
evaluated on every completed M1 bar's mid close
(`MinuteRuleLeg._manage`, `leg_rules.py:1446-1459`; declared mechanization,
module docstring `leg_rules.py:16-18` "conservative, deterministic, PIT-clean");
**T-QUOTE** = touch on the quoted-side bar extreme (bid for long exits, ask for
short exits — VOLPROF only, `legs.py:413-417`, per CLASS_SPEC §4.3/§5).
Overnight/weekend: **INTRADAY-FLAT** (flat same trading day, no O/N);
**O/N** (holds overnight, no structural weekend flat); **O/N+W/E** (holds
through weekends); flat-by-Friday noted where structural.

---

## 1. EXIT INVENTORY TABLE (76 legs)

### 1.1 A-TREND (17 legs)

| leg | sym | horizon / clock | exit classes | basis | code | O/N | corpus divergence |
|---|---|---|---|---|---|---|---|
| AUDUSD-S002 | AUDUSD | D1 multi-day | SIG (55-ch SAR flip) | C-D1 | `leg_rules.py:417-443` | O/N+W/E | no (corpus: stop-and-reverse by close) |
| AUDUSD-S003 | AUDUSD | D1 multi-day | SIG (ADX<20) | C-D1 | `leg_rules.py:491-514` | O/N+W/E | no |
| AUDUSD-S006 | AUDUSD | D1 multi-week (weekly rebal) | SIG (sign flat / rebalance) | C-D1 | `leg_rules.py:581-617` | O/N+W/E | no |
| EURUSD-S003 | EURUSD | D1 multi-week (monthly rebal) | SIG | C-D1 | `leg_rules.py:581-617` | O/N+W/E | no |
| EURUSD-S009 | EURUSD | D1 multi-week | SIG (MACD-H dual divergence) | C-D1 | `legs.py:715-764,766-789` | O/N+W/E | no |
| GBPUSD-S001 | GBPUSD | D1 multi-week | TRAIL+SL (2.5×ATR14, no TP) | C-D1 | `leg_rules.py:459-481` | O/N+W/E | **YES** — corpus "stop trailing 2.5×ATR" is a live trailing stop (touch); impl checks D1 close |
| GBPUSD-S002 | GBPUSD | M1 session day | SL (range ±2 pip) + TIME (16:00 London) | C-M1 | `leg_rules.py:1981-2017` | INTRADAY-FLAT | minor (declared M1-close) |
| GBPUSD-S003 | GBPUSD | H4 multi-day | TRAIL+SL (chandelier 3×ATR(H4), ratcheted on H4 closes) | C-M1 | `leg_rules.py:1538-1566` | O/N+W/E | minor |
| GBPUSD-S004 | GBPUSD | D1 multi-week (weekly rebal) | SIG (weekly close through MA20) | C-D1 | `leg_rules.py:945-974` | O/N+W/E | no (corpus exit IS the weekly close) |
| GBPUSD-S007 | GBPUSD | H4 multi-day | TP (3R) + SL (half channel) + TIME (30-day timeout) | C-M1 | `leg_rules.py:1504-1531` | O/N+W/E | minor — corpus "stop nửa kênh; target 3R" implies touch orders |
| USDCAD-S002 | USDCAD | D1 multi-day | SIG (SAR flip) | C-D1 | `leg_rules.py:417-443` | O/N+W/E | no |
| USDCAD-S004 | USDCAD | D1 multi-day | SL (halfway to 200DMA) + SIG (dislocation unwound) | C-D1 | `leg_rules.py:624-646` | O/N+W/E | **YES** — "stop nửa đường về 200DMA" touch intent vs D1-close check |
| USDCAD-S006 | USDCAD | D1 multi-week (weekly clock) | SL (prior-week swing) | C-D1 | `leg_rules.py:888-933` | O/N+W/E | **YES** — swing-low stop, touch intent |
| USDJPY-S001 | USDJPY | D1 multi-week | SL (2×ATR20 from channel) + TRAIL (opposite 10-day channel) | C-D1 | `legs.py:580-624` (exit :598-617) | O/N+W/E | **YES** — turtle-canon touch stop/trail vs D1-close check |
| USDJPY-S002 | USDJPY | D1 multi-week | SL (20-day swing) + SIG (ADX<20 ×2) | C-D1 | `leg_rules.py:525-561` | O/N+W/E | **YES** — swing stop, touch intent |
| USDJPY-S003 | USDJPY | D1 multi-week (monthly rebal) | SIG | C-D1 | `leg_rules.py:581-617` | O/N+W/E | no |
| USDJPY-S009 | USDJPY | D1 multi-week | SL (cluster entry−2N) + TRAIL (2N from best) | C-D1 | `leg_rules.py:664-707` | O/N+W/E | **YES** — corpus Risk names "gap qua stop (weekend)" ⇒ touch stop orders; impl D1-close |

A-TREND counts: SIGNAL-EXIT-ONLY 8 · TP 1 · SL 8 · TRAIL 4 · TIME 2.

### 1.2 B-MEANREV (15 legs)

| leg | sym | horizon / clock | exit classes | basis | code | O/N | corpus divergence |
|---|---|---|---|---|---|---|---|
| EURUSD-S012 | EURUSD | H1, ~8 bars | SL (1×ATR(H1)) + TP (EMA9-H1 target) + SIG (RSI2→50) + TIME (8 bars) | C-M1 | `leg_rules.py:1703-1759` | O/N possible | minor |
| EURUSD-S013 | EURUSD | H4, no time bound | TP (SMA20) + SL (2.8σ) | C-M1 | `leg_rules.py:1662-1689` | O/N+W/E possible | minor — corpus "target SMA20, stop tại 2.8σ" |
| EURUSD-S020 | EURUSD | M5 session night (01:00–06:00 UTC) | TP (mid-band) + SL (6 pip) | C-M1, **exit eval only inside the 01:00–06:00 window** (`leg_rules.py:2150-2154` early return) | `leg_rules.py:2146-2193` | O/N possible (residual carries to next window) | minor — corpus "stop 6 pip" touch intent |
| GBPUSD-S011 | GBPUSD | M1 session day | TP (mid-range) + SL (fake-extreme +2 pip) + TIME (12:00 UTC) | C-M1 | `leg_rules.py:2195-2240` | INTRADAY-FLAT | minor |
| GBPUSD-S012 | GBPUSD | H1, ~8 bars | SL (1.2×ATR(H1)) + SIG (RSI2→50) + TIME (8 bars) | C-M1 | `leg_rules.py:1703-1759` | O/N possible | minor |
| GBPUSD-S013 | GBPUSD | M15 session night (22:00–05:00) | TP (mid-band) + SL (half BB width) + TIME (08:00) | C-M1 | `leg_rules.py:2442-2471` | INTRADAY-FLAT | minor |
| GBPUSD-S014 | GBPUSD | H4, no time bound | TP (50 pip) + SL (15 pip) | C-M1 | `leg_rules.py:2941-2977` | O/N+W/E possible | minor — fixed-pip levels are classic touch orders |
| GBPUSD-S016 | GBPUSD | Sun 22:30 → Mon | TP (Friday close) + SL (half gap) + TIME (~12 h hold) | C-M1 | `leg_rules.py:2115-2144` | O/N (weekend-adjacent entry; flat within ~12 h) | minor |
| GBPUSD-S017 | GBPUSD | M1 NY afternoon (15:30–18:30 London) | TP (VWAP) + SL (+1σ) | C-M1, **exit eval only inside the window** (`leg_rules.py:2415-2416` early return) | `leg_rules.py:2413-2440` | O/N possible (carry to next window) | minor |
| GBPUSD-S019 | GBPUSD | D1 multi-day | SL (1×ATR14) + SIG (z→1 target, `Z_TARGET_ONE`) | C-D1 | `leg_rules.py:1204-1253` | O/N+W/E | **YES** — corpus "stop 1×ATR" touch intent vs D1-close |
| USDCAD-S011 | USDCAD | D1 multi-day | SL (1.5×ATR14) + SIG (RSI2>60 / <40) | C-D1 | `leg_rules.py:719-743` | O/N+W/E | **YES** — corpus "stop 1.5×ATR" touch intent |
| USDCAD-S016 | USDCAD | D1 multi-day | TP (mid band) + SL (1×ATR14) | C-D1 | `leg_rules.py:815-841` | O/N+W/E | **YES** — "target giữa range, stop 1×ATR" touch intent |
| USDJPY-S014 | USDJPY | H4, ~8 bars | SL (1×ATR(H4)) + SIG (RSI2→50) + TIME (8 bars) | C-M1 | `leg_rules.py:1703-1759` | O/N possible | minor |
| USDJPY-S017 | USDJPY | M1 London morning | TP (Tokyo open) + SL (Asia H/L ±2 pip) + TIME (London window end 10:30) | C-M1 | `leg_rules.py:2353-2411` | INTRADAY-FLAT | minor |
| USDJPY-S018 | USDJPY | M1 Monday Tokyo | TP (50% gap) + SL (0.6×gap) + TIME (Tokyo 18:00) | C-M1 | `leg_rules.py:2086-2113` | INTRADAY-FLAT (Monday day) | minor |

B-MEANREV counts: SIGNAL-EXIT-ONLY 0 · TP 11 · SL 15 · TRAIL 0 · TIME 8 (SIG present on 5).

### 1.3 C-BREAKOUT (15 legs)

| leg | sym | horizon / clock | exit classes | basis | code | O/N | corpus divergence |
|---|---|---|---|---|---|---|---|
| AUDUSD-S023 | AUDUSD | D1 multi-week (weekly bracket) | SL (prior-week mid) | C-D1 | `leg_rules.py:3033-3077` | O/N+W/E | **YES** — "stop trong squeeze-range" touch intent |
| AUDUSD-S026 | AUDUSD | D1 multi-day | TP (2× squeeze width) + SL (mid band) + TIME (8-day timeout) | C-D1 | `leg_rules.py:764-800` | O/N+W/E | **YES** — corpus adds "timeout 8 ngày" (time, exact) but stop/target are touch-intent |
| AUDUSD-S029 | AUDUSD | H4 multi-day | SL (prior-week level) + TP ratchet (2×ATR-W1) | C-M1 | `leg_rules.py:1573-1603` | O/N+W/E | minor |
| EURUSD-S024 | EURUSD | M1/D1 multi-day | TRAIL+SL (2×ATR(10) ratchet); no TP, no TIME | C-M1 | `leg_rules.py:2706-2746` | O/N+W/E | minor — corpus trail; ENTRY stop-orders mechanized on M1 mid close (declared) |
| EURUSD-S027 | EURUSD | H4 multi-day | SL (1×ATR5 ratchet = TRAIL) + SIG (ratio<1) | C-M1 | `leg_rules.py:1799-1831` | O/N+W/E | minor |
| GBPUSD-S021 | GBPUSD | M5 session morning | TP (1.5R) + SL (mid-box) + TIME (11:30) | C-M1 | `leg_rules.py:2473-2527` | INTRADAY-FLAT | minor |
| GBPUSD-S023 | GBPUSD | M30 session day | TP (2R) + SL (mid-range) + TIME (21:00) | C-M1 | `leg_rules.py:2761-2799` | INTRADAY-FLAT | minor |
| GBPUSD-S024 | GBPUSD | M15 session afternoon | TP (day-range extreme) + SL (mid-box) + TIME (19:00) | C-M1 | `leg_rules.py:2473-2527` | INTRADAY-FLAT | minor |
| GBPUSD-S025 | GBPUSD | M15 session day | TP (1× Asian range) + SL (5 pip inside) + TIME (16:00) | C-M1 | `leg_rules.py:2242-2307` | INTRADAY-FLAT | minor |
| GBPUSD-S028 | GBPUSD | H1 afternoon (after 14:00 London) | SL (PDH/PDL level) + TP (measured 1× day range) | C-M1 | `leg_rules.py:1838-1909` | O/N possible | minor |
| GBPUSD-S029 | GBPUSD | M30 Wed→Fri | TP (2R) + SL (opposite range edge) + TIME (Fri 16:00 London) | C-M1 | `leg_rules.py:2572-2606` | O/N, **flat-by-Friday** | minor |
| USDJPY-S022 | USDJPY | M5 NY session | SL (opposite OR) + TRAIL (1×ATR(H1)) + TIME (15:00 ET) | C-M1 | `leg_rules.py:2529-2570` | INTRADAY-FLAT | minor |
| USDJPY-S023 | USDJPY | D1 multi-day | TP (2× squeeze width) + SL (opposite band); **no timeout** (`timeout_days` absent) | C-D1 | `leg_rules.py:764-800` | O/N+W/E | **YES** — touch-intent levels on D1-close check |
| USDJPY-S026 | USDJPY | H1 session (London ∪ NY) | SL (0.5×ATR(H1)) + TP ratchet (1×ATR(D1)) | C-M1 | `leg_rules.py:1838-1909` | O/N possible | minor |
| USDJPY-S029 | USDJPY | D1 multi-day | SL (1.5×ATR5) + SIG (ratio<1) | C-D1 | `leg_rules.py:848-875` | O/N+W/E | **YES** — "stop 1.5×ATR5" touch intent |

C-BREAKOUT counts: SIGNAL-EXIT-ONLY 0 · TP 10 · SL 15 · TRAIL 3 · TIME 6 (SIG present on 2).

### 1.4 E-SESSION (9 legs)

| leg | sym | horizon / clock | exit classes | basis | code | O/N | corpus divergence |
|---|---|---|---|---|---|---|---|
| AUDUSD-S044 | AUDUSD | D1 window 24–28/06 | SL (1×ATR-D1) + TIME (window end 01–02/07) | C-D1 | `leg_rules.py:988-1056` | O/N+W/E (multi-day window) | **YES** — "stop 1×ATR-D1" touch intent |
| EURUSD-S044 | EURUSD | D1 last week of quarter | TIME (quarter-roll exit); no SL/TP | C-D1 | `leg_rules.py:1002-1004,1032-1039` | O/N+W/E | no |
| EURUSD-S046 | EURUSD | D1 ≤4 sessions around month-turn | TIME (window end + max-hold); no SL/TP | C-D1 | `leg_rules.py:1005-1011,1040-1046` | O/N | no |
| GBPUSD-S027 | GBPUSD | D1 daily ADJUST | SIG (weekday meta-gate; flat on zero move) | C-D1 | `legs.py:657-681` | O/N+W/E | no |
| GBPUSD-S042 | GBPUSD | M1 Friday evening 18:30–21:00 | SL (30 pip) + TIME (flat pre-21:30) | C-M1 | `leg_rules.py:2608-2652` | INTRADAY-FLAT, Friday-only, **flat-by-Friday** | minor |
| GBPUSD-S048 | GBPUSD | D1 daily | SIG (weekday allocation realign) | C-D1 | `leg_rules.py:1151-1164` | O/N+W/E | no |
| USDJPY-S044 | USDJPY | D1 window 10–31/03 | SL (1.5×ATR-week) + TIME (31/03) | C-D1 | `leg_rules.py:999-1001,1020-1031` | O/N+W/E (3-week hold) | **YES** — "stop 1.5×ATR tuần" touch intent |
| USDJPY-S045 | USDJPY | D1 last September week, 5 sessions | SL (1×ATR-week) + TIME (5 sessions) | C-D1 | `leg_rules.py:1012-1017,1047-1055` | O/N | **YES** — "stop 1×ATR tuần" touch intent |
| USDJPY-S050 | USDJPY | M30 slot (30 min) | SL (0.5×ATR(M30)) + TIME (slot end) | C-M1 | `leg_rules.py:2825-2867` | INTRADAY-FLAT | minor |

E-SESSION counts: SIGNAL-EXIT-ONLY 2 · TP 0 · SL 5 · TRAIL 0 · TIME 8.

### 1.5 G-XASSET (2), I-STATARB (5), J-REGIME_OPT (4)

| leg | family | sym | horizon / clock | exit classes | basis | code | O/N | divergence |
|---|---|---|---|---|---|---|---|---|
| GBPUSD-S063 | G-XASSET | GBPUSD | D1 multi-day router | SIG (ratio-router realign) | C-D1 | `leg_rules.py:1303-1315` | O/N+W/E | no |
| GBPUSD-S065 | G-XASSET | GBPUSD | H1 session | SL (level) + TP (2R) | C-M1 | `leg_rules.py:1838-1909` | O/N possible | minor |
| GBPUSD-S083 | I-STATARB | GBPUSD | D1 multi-day router | SIG (beta-router realign) | C-D1 | `leg_rules.py:1278-1302` | O/N+W/E | no |
| GBPUSD-S084 | I-STATARB | GBPUSD | H1 multi-day gate | SIG (AR gate neutral/flip; `stop=None`) | C-M1 | `leg_rules.py:2992-3017` | O/N+W/E | no |
| GBPUSD-S086 | I-STATARB | GBPUSD | H1 multi-day gate | SL (3×ATR(D1)) + SIG (gate flip) | C-M1 | `leg_rules.py:1936-1964` | O/N+W/E | minor |
| GBPUSD-S087 | I-STATARB | GBPUSD | D1 multi-day | SIG (z-target 2.8 / z-flip) | C-D1 | `leg_rules.py:1254-1277` | O/N+W/E | no (z-exits are close-basis by corpus) |
| GBPUSD-S090 | I-STATARB | GBPUSD | M5 London morning | TP (overnight-range mid) + SL (sweep-extreme +2 pip) + TIME (13:00) | C-M1 | `leg_rules.py:2309-2351` | INTRADAY-FLAT | minor |
| AUDUSD-S096 | J-REGIME_OPT | AUDUSD | D1 multi-week overlay | SIG (vol-target realign) | C-D1 | `leg_rules.py:1165-1176` | O/N+W/E | no |
| EURUSD-S091 | J-REGIME_OPT | EURUSD | D1 multi-day gate | SIG (RV-band realign) | C-D1 | `leg_rules.py:1109-1123` | O/N+W/E | no |
| GBPUSD-S091 | J-REGIME_OPT | GBPUSD | D1 multi-day gate | SIG (RV-trio realign) | C-D1 | `leg_rules.py:1124-1141` | O/N+W/E | no |
| USDCAD-S091 | J-REGIME_OPT | USDCAD | D1 multi-day gate | SIG (RV-weight realign) | C-D1 | `leg_rules.py:1142-1150` | O/N+W/E | no |

G+I+J counts: SIGNAL-EXIT-ONLY 8 · TP 2 · SL 3 · TRAIL 0 · TIME 1.

### 1.6 VOLPROF (9 legs — POOL_B_VOLPROF)

| leg | sym | horizon / clock | exit classes | basis | code | O/N | divergence |
|---|---|---|---|---|---|---|---|
| VC1-VAEDGE × {EURUSD,GBPUSD,USDJPY} | 3 pairs | M1 intraday (London ∪ NY entry windows) | TP (POC, M1 mid-close crossing) + SL (1×ATR60) + TIME (19:55 hard flat; VC1 rides to the flat call, no tmax) | TP C-M1; SL **T-QUOTE** (bid_low ≤ stop / ask_high ≥ stop, `legs.py:413-417`) | `legs.py:358-423` (TP :408-411, SL :413-417, flat :389-399) | INTRADAY-FLAT (19:55 UTC daily; weekend-free by construction) | **none** — CLASS_SPEC §4.3/§5.1 prescribes exactly this (touch on quoted side; TP on mid-close crossing) |
| VC2-LVNFAIL × 3 pairs | 3 pairs | M1 intraday | TP (POC) + SL (1×ATR60 beyond node) + TIME (tmax 240 min + 19:55) | same | `legs.py:402-423` (tmax :419-422) | INTRADAY-FLAT | none |
| VC3-POCMAG × 3 pairs | 3 pairs | M1 intraday | TP (POC ±0.5×W_BIN) + SL (1×ATR60) + TIME (tmax 240 + 19:55) | same | `legs.py:402-423` | INTRADAY-FLAT | none |

VOLPROF counts: SIGNAL-EXIT-ONLY 0 · TP 9 · SL 9 · TRAIL 0 · TIME 9.

### 1.7 Inventory summary (flags are non-exclusive; 76 legs)

| family | legs | SIGNAL-EXIT-ONLY | TP | SL | TRAIL | TIME |
|---|---|---|---|---|---|---|
| A-TREND | 17 | 8 | 1 | 8 | 4 | 2 |
| B-MEANREV | 15 | 0 | 11 | 15 | 0 | 8 |
| C-BREAKOUT | 15 | 0 | 10 | 15 | 3 | 6 |
| E-SESSION | 9 | 2 | 0 | 5 | 0 | 8 |
| G-XASSET | 2 | 1 | 1 | 1 | 0 | 0 |
| I-STATARB | 5 | 3 | 1 | 2 | 0 | 1 |
| J-REGIME_OPT | 4 | 4 | 0 | 0 | 0 | 0 |
| VOLPROF (3 families) | 9 | 0 | 9 | 9 | 0 | 9 |
| **total** | **76** | **18** | **33** | **55** | **7** | **34** |

### 1.8 Divergence list — close-basis implementation where the corpus intended touch-basis

**Strong (D1-close check of level stops that the corpus text states as stop
levels; a live stop order is a touch instrument — the D1-close mechanization
lets adverse intraday excursions escape if the day closes back inside):**

1. GBPUSD-S001 (trail 2.5×ATR) — `leg_rules.py:459-481`
2. USDCAD-S004 (halfway-to-200DMA stop) — `leg_rules.py:624-646`
3. USDCAD-S006 (prior-week swing stop) — `leg_rules.py:888-933`
4. USDJPY-S001 (2×ATR channel stop + 10-day channel trail) — `legs.py:598-617`
5. USDJPY-S002 (20-day swing stop) — `leg_rules.py:525-561`
6. USDJPY-S009 (turtle cluster stop + 2N trail; corpus risk line explicitly
   prices "gap qua stop" — a touch-order concept) — `leg_rules.py:664-707`
7. GBPUSD-S019 (1×ATR stop) — `leg_rules.py:1204-1253`
8. USDCAD-S011 (1.5×ATR stop) — `leg_rules.py:719-743`
9. USDCAD-S016 (1×ATR stop + mid-band TP) — `leg_rules.py:815-841`
10. AUDUSD-S023 (squeeze-range stop) — `leg_rules.py:3033-3077`
11. AUDUSD-S026 + USDJPY-S023 (squeeze stop + 2×width TP) — `leg_rules.py:764-800`
12. USDJPY-S029 (1.5×ATR5 stop) — `leg_rules.py:848-875`
13. AUDUSD-S044, USDJPY-S044, USDJPY-S045 (ATR-week stops) — `leg_rules.py:988-1056`

**Declared-minor (M1 mid-close check — one-minute-granularity touch proxy;
declared mechanization `leg_rules.py:16-18`):** all intraday legs with SL/TP
(corpus fixed-pip levels, e.g. GBPUSD-S014 "stop 15 pip / target 50 pip",
EURUSD-S020 "stop 6 pip", GBPUSD-S011/S090 "+2 pip", GBPUSD-S025 "5 pip").
Divergence is bounded by one M1 bar's intra-minute excursion.

**No divergence:** VOLPROF 9 (spec-prescribed touch-on-quoted-side; implemented
exactly), all pure signal-exit legs (18), window/time exits.

---

## 2. TWO SEPARATED OUTPUTS (design)

### 2a. TB-LABELS — analysis-only trade labeling

**Purpose.** For every FILLED trade in a journal, label the trade
`{upper_hit | lower_hit | timeout}` with the hit timestamp and the barrier
values used, computed OFFLINE from the M1/H1 bid/ask path between fill and the
trade's actual close. Labels serve (i) loss analysis and (ii) the
JOURNAL_SCHEMA §3 loss taxonomy as descriptive diagnostics only (e.g. a
`LOSS_SIGNAL` trade whose path hit a 1×ATR lower barrier before any upper
excursion vs one that timed out inside the noise band).

**Definition (frozen form).** For trade t with entry fill price e (mid at
fill), direction d, actual exit at time τ: barriers U = e + k_U × ATR20_entry,
L = e − k_L × ATR20_entry (mirrored for shorts), horizon H bars on the trade's
own clock from fill; the label is the first barrier touched on the exit-side
quoted series (long: bid_low path for L, bid_high for U; shorts mirrored) or
`timeout` at H. Label basis for diagnosis: k_U = k_L = 1.0 and H = the trade's
own realized holding time (labels describe the realized path, they do not
re-trade it).

**Firewall (exact).**
- Label file path: `research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/
  triple_barrier/labels/TB_LABELS_v1.jsonl` (schema `tb_label@1`: journal
  order_id, fold_id, leg ids, entry ts/price, direction, barriers, label,
  hit_ts, ambiguous_flag). It lives under `control/`, NEVER under
  `research/pc12a/` (engine tree).
- No import by engine: the engine (`legs.py`, `leg_rules.py`, `policy.py`,
  `run_dry.py`, `journal.py`, `cost_kernel.py`) has zero references to
  `triple_barrier/` — verifiable by grep at any freeze; the label producer is
  an offline analysis script that READS committed journals/panels and WRITES
  only under `triple_barrier/`. Engine code is not modified by this lane
  (dispatch law).
- Leak law: a TB label is a function of POST-ENTRY future path — its
  information time is the hit timestamp, strictly after entry. Under campaign
  §1 (PIT clock law) and GROUPING_PROPOSAL §3 (pre-trade feature inventory +
  FORBIDDEN list), no feature may carry available_time > decision time, so TB
  labels can NEVER be features, eligibility inputs, policy inputs, sizing
  inputs, or arm-selection inputs — by construction, not by convention.
- Fold discipline: labels computed on TRAIN-fold journals during Stage-A/B
  analysis; TEST-fold labels are produced only inside Stage-C reporting, after
  the scored runs they describe exist; sealed tail untouched.
- Eligibility: labels change no eligibility state, add no ledger row type
  beyond their own analysis file, and never feed any PASS bar input.

### 2b. TB-EXIT-OVERLAY — new research arm class (exit-law comparison)

**Arm definition.** An overlay arm keeps the leg's original ENTRY law, unit
sizing, clock, PIT joins and cost tier EXACTLY (same `arm_config_digest`
inputs on the entry side) and REPLACES the exit law with the triple-barrier
set {TP, SL, horizon time-stop} evaluated against BID/ASK. The ORIGINAL exit
law (the leg as frozen in wave-1) stays as the **control arm** — same entries,
original exits. Structural hard flats that are facts of the venue/leg clock
(fold-edge force-flat per PASS_BARS E-Law 2) still apply to overlay arms;
leg-own session flats (e.g. 16:00 London) are part of the ORIGINAL exit law
and are replaced by the overlay horizon.

**The four touch cases (TP checked on the side you SELL into; both barriers of
a long are checked on BID, of a short on ASK):**

1. **Long TP** (level above entry): triggered when `bid_high(bar) ≥ TP` — the
   bid (the side a long sells into) rises to the level; exit fill at the touch
   bar's quoted side (bid) per §6.
2. **Long SL** (level below entry): triggered when `bid_low(bar) ≤ SL` — the
   bid falls to the level; exit fill at bid.
3. **Short TP** (level below entry): triggered when `ask_low(bar) ≤ TP` — the
   ask (the side a short buys into) falls to the level; exit fill at ask.
4. **Short SL** (level above entry): triggered when `ask_high(bar) ≥ SL`; exit
   fill at ask.

Touch fills execute at the touch bar's quoted side under the spread-once
kernel (§6); a bar whose quotes GAP THROUGH the barrier fills at the fx6
worst-fill grade (worst of the touch bar's open/close on the quoted side),
never at the barrier price. Evaluation granularity: M1 bars where an M1 panel
exists (all 3 staged pairs — including H1/H4/D1-clock overlay legs, whose
barriers are walked on the M1 sub-path per §4); D1 bars elsewhere (§4
ambiguity law).

**Comparison metric (frozen).** Per leg: net PnL (NET book, full kernel) and
maxDD (USD, PASS_BARS E-Law 1 definition) on TRAIN folds, overlay vs its
control; survivors then run UNTOUCHED folds under the existing gates. No
overlay arm may enter the portfolio or the scored surface except through the
campaign's own Stage-B/C law — the overlay is a Stage-A discovery arm class.

**Profits-cut-early accounting (mandatory, journaled).** Every overlay trade
whose TP truncated a winner is matched to its control twin's outcome on the
same entry: journal `opportunity_cost_pips = control_exit − overlay_exit`
(signed, overlay-direction-adjusted) and the fold roll-up
`profits_cut_early_usd` = Σ over TP-truncated winners of (control net −
overlay net). This is the ONOFF dual-side law (GROUPING_PROPOSAL §4 /
JOURNAL_SCHEMA §3 "no cherry side") applied to exit laws: reporting the
losses-avoided side without the profits-cut side is a STOP-3 integrity trip.

---

## 3. THRESHOLD / HORIZON SELECTION LAW (frozen forms, preregistered)

**Entry-information-only law.** Barriers are functions of information
available AT ENTRY only:

```
ATR20_entry = ATR(20) on the leg's own decision-clock bars, value frozen at
              the entry fill (D1 legs: ATR20(D1); H1/H4 legs: ATR(20) of the
              aggregate clock; M1 session legs: ATR(60 M1 bars) — the leg's
              own existing risk unit).
TP  = entry_fill ± k_TP  × ATR20_entry   (favorable side)
SL  = entry_fill ∓ k_SL  × ATR20_entry   (adverse side)
H   = horizon time-stop in the leg's own decision-clock bars from entry fill
```

**Horizon law.** H is derived from the **family's** TRAIN holding-time
distribution measured from the wave-1 dry-run journals (decision/fill/exit
timestamps, no PnL needed): `H_p90 = ceil(p90)`, `H_2p50 = ceil(2 × p50)`,
both capped at the family's structural day/session boundary where one exists
(session-flat families cap at their flat minute; bar-clock families cap at
5 trading days = the fold-agnostic structural cap; the cap is frozen with the
node list). Two horizons only.

**The frozen node list (at most 18 nodes per leg-FAMILY, not per leg):**

```
k_TP ∈ {1.5, 2.5, 4.0}
k_SL ∈ {1.0, 1.5, 2.5}
H    ∈ {H_p90, H_2p50}      (family-measured, capped, frozen before any run)
18 = 3 × 3 × 2 nodes per applicable family; every leg in the family runs the
same 18 nodes — the multipliers bind at family level.
```

**Total variant count (registered BEFORE any PnL):** applicable families =
B-MEANREV, C-BREAKOUT, E-SESSION (conditional, §5) → up to **3 × 18 = 54
overlay arms + 3 control arms (one per family: the family's legs at their
frozen original-exit configs) = 57 discovery-ledger rows maximum**, stage
`A-MECH`, fold_scope `DISCOVERY_PRE_PNL`, each row carrying
`arm_config_digest` + node id `(family, k_TP, k_SL, H)`. Ledger headroom check:
85 existing rows + 57 = 142 ≤ 1,500 cap (plan §4). If E-SESSION fails its §5
measurement, the registration shrinks to 36 + 2 = 38 rows — the budget is a
ceiling, never a target.

**Explicit prohibitions (owner law, restated):** NO per-leg optimization (a
leg's barriers are its family's node values, never fitted per leg); NO
threshold grids beyond the frozen 18-node list; NO node added after the first
overlay PnL exists (adding one is a plan amendment, §7); NO barrier parameter
derived from post-entry data (§2a leak law).

---

## 4. AMBIGUOUS-TOUCH LAW

**Definition.** On an evaluation bar B where BOTH barrier levels lie inside
the bar's quoted-side range — long: `bid_low(B) ≤ SL < TP ≤ bid_high(B)`
(shorts mirrored on ask) — and the intrabar path is unknown, the touch order
is undetermined: record **AMBIGUOUS** (count per run, per arm).

**Frozen pessimistic default.** ALL ambiguous bars of a run resolve
**SL-first** (the adverse order): the SL is treated as touched first. Applied
uniformly to every ambiguous bar of every overlay arm (no per-run choice, no
per-leg choice). The **ambiguous-bar fraction** (ambiguous bars / evaluated
bars) is reported per arm; a run with **> 20 % ambiguous bars is
`NOT_RUN_TOUCH_RESOLUTION`** — its PnL is not comparable and does not exist as
evidence (recorded, never inferred PASS; campaign §2 typed-NOT_RUN law).

**Resolution upgrade by M1 availability (the 3 staged pairs).** EURUSD,
GBPUSD, USDJPY have full M1 bid/ask panels (`panels.py`), and every intraday
leg clock is aggregated from the M1 stream — so for these pairs, barrier
evaluation on any clock coarser than M1 (H1 legs, H4 legs, D1 legs) resolves
the sub-path by **walking the M1 bars inside the evaluation bar**: the first
barrier touched in time order wins; if both barriers are touched within the
SAME M1 bar, that M1 bar is itself ambiguous (no deeper recursion exists) and
the SL-first default applies to it. Net effect: for the 3 M1 pairs the
ambiguous fraction collapses to same-M1-bar double-touches only.

**Unresolvable cases (named, honest).**
- **AUDUSD / USDCAD legs** (14 legs): no staged M1 panels on this checkout —
  the legs are NOT_RUN today anyway; if panels arrive, D1-clock evaluation
  cannot resolve within the day and the >20 % law binds on measured ambiguity.
- **The 7 blocked new assets** (NZDUSD, USDCHF, XAUUSD, XAGUSD, BRENT, WTI,
  NATGAS): daily data only — within-day resolution is IMPOSSIBLE at any
  horizon; any future TB arm on them measures its ambiguous fraction first
  and defaults to `NOT_RUN_TOUCH_RESOLUTION` unless intraday data is unlocked
  (owner data authority, amendment §3 — BLOCKED stays BLOCKED).

---

## 5. WHERE THE OVERLAY MAY NOT APPLY (applicability law)

**Owner warning (design law).** Trend/persistent families exist to let
winners run; a TP overlay on them truncates the very tail moves that pay for
the family. Therefore:

**Applicability rule (conjunctive, preregistered).** Overlay arms are created
ONLY for families where (a) the family's TRAIN holding-time **p50 < the
proposed horizon H** of §3 (the original exit typically fires BEFORE any
barrier would — the overlay is an alternative exit, not a contradiction) AND
(b) the original exit is a **close-basis exit law** (close-evaluated levels or
rule-state signal exits — i.e. not already touch-evaluated barriers).
Interpretation note: condition (b) reads "close-basis signal-exit" from the
dispatch as "close-basis exit law" — legs whose exits are ALREADY touch-basis
barriers (VOLPROF) need no overlay (it would duplicate their control), and
that is stated as the reason for their exclusion, not silently.

**Family × applicable table:**

| family | original-exit basis | holding p50 vs H (expected, measured Stage-A) | overlay applicable | rationale |
|---|---|---|---|---|
| A-TREND (17) | mixed: 8 signal-only (SAR/ADX/TSMOM/gates), 4 trailing, 5 SL-bearing — ALL close-basis (C-D1) | weeks ≫ H | **NO (default exclusion)** | owner warning: winners must run; trend persistence is the edge; inclusion requires its own preregistered amendment naming the legs and why barriers will not truncate tail moves |
| B-MEANREV (15) | close-basis (C-M1 intraday 11, C-D1 daily 4) | hours–days < H | **YES** | short-horizon fades; barrier exit is mechanism-consistent (fade-to-target is the corpus's own intent) |
| C-BREAKOUT (15) | close-basis (C-M1 11, C-D1 4) | hours–days < H | **YES** (with mandatory profits-cut-early accounting on the trail-bearing legs EURUSD-S024, USDJPY-S022, EURUSD-S027 — their originals let winners run; the overlay TP is exactly the truncation hypothesis under test, journaled both sides) | breakout families already carry TPs in-corpus (1.5R/2R/2×width) — barrier geometry comparison is the question |
| E-SESSION (9) | time/window (8), gates (2 signal-only) | bimodal: intraday members (GBPUSD-S042, USDJPY-S050) hours < H; calendar members (AUDUSD-S044, EURUSD-S044, EURUSD-S046, USDJPY-S044, USDJPY-S045) days–weeks > H; gates persistent | **CONDITIONAL** — 18 nodes allocated only if the intraday members' measured p50 < H; calendar members excluded (horizon dominates); gate members (GBPUSD-S027, GBPUSD-S048) fail condition (a) | session/time geometry families |
| G-XASSET (2) | S063 router signal-only; S065 has levels (C-M1) | S063 weeks; S065 session | **NO** | S063 fails (a); S065 fails (b) read strictly (original exit already level-based; family is a router family) |
| I-STATARB (5) | 4 persistent gates/routers (signal-only); S090 intraday session | bimodal | **NO** (family default) — GBPUSD-S090 is the one member that passes both conjuncts by mechanism; its inclusion requires the same preregistered justification as a trend-leg inclusion (named exception, not silent) | stat-arb persistence is the mechanism |
| J-REGIME_OPT (4) | signal-only realign overlays | days–weeks | **NO** | persistent regime overlays; fail (a) |
| VOLPROF × 3 (9) | **touch-basis already** (T-QUOTE SL, POC TP, 19:55/tmax) | minutes | **NO** | the class IS a triple-barrier implementation; an overlay would re-test its own control (CLASS_SPEC §5 is the frozen exit law) |

Applicable families for budget: **B-MEANREV + C-BREAKOUT + E-SESSION
(conditional)** → §3's 57-row ceiling.

---

## 6. COSTS / ACCOUNTING (binding for any overlay implementation)

- **Touch fills** execute at the touch bar's quoted side (bid for long-exits /
  sells, ask for short-exits / buys) under the **spread-once kernel**
  (FILL_ACCOUNTING_SPEC §1–§2): `cross_cost = |fill − mid_at_fill|` charged
  exactly once through the fill price, decomposed `spread_once +
  slip_beyond_halfspread` with the exact identity per fill; commission U2
  (0.35 bps/side) on both entry and exit; **no second crossing line**.
- **Slippage U3** bands at the touch bar: 0.2 pip non-event / 1.0 pip inside
  event windows (rollover 21:00–23:00 UTC, Sunday reopen first 15 min — the
  overlay inherits the leg clock's exposure to these windows unchanged).
- **Gap-through-barrier** (touch bar's quotes entirely beyond the level):
  **fx6 worst-fill grading** — fill at the worst of the touch bar's open and
  close on the quoted side, then ± U3; never at the barrier price; the excess
  beyond the ordinary crossing books inside `slip_beyond_halfspread` with
  `LOSS_FILL` candidacy (FILL_ACCOUNTING_SPEC §1.5, fixture
  `journal/fixtures/fx6_worst_fill_grading.json`).
- **Swap accrual unchanged**: U4/U5 per-night accrual at 22:00 UTC boundaries,
  Wed ×3, never income; overlay arms that hold overnight where the original
  was intraday-flat accrue swap honestly (that is part of the comparison, not
  an artefact).
- **All numbers NET** (NET book, full kernel, `NET_DEFAULT_COST` /
  `PROVISIONAL_PENDING_COST_AUTHORITY` labels until the owner statement
  lands); GROSS/NET dual books per FILL_ACCOUNTING_SPEC §9; the §6 equity
  identity must reconcile to 1e-9 for every overlay run or the run is
  `NOT_RUN_INTEGRITY` (STOP-3).

---

## 7. REGISTRATION REQUIREMENTS (what must be frozen BEFORE any overlay arm runs)

1. **Node list**: the exact 54 `(family, k_TP, k_SL, H)` triples with the
   measured H values (family TRAIN holding p90 / 2×p50, capped) written into
   the registration packet.
2. **Ambiguous-touch law**: §4 verbatim (SL-first, >20 % →
   `NOT_RUN_TOUCH_RESOLUTION`, M1 sub-path upgrade, unresolvable cases).
3. **Applicability table**: §5 verbatim, including the E-SESSION conditional
   and the named-exception paths (A-TREND, GBPUSD-S090).
4. **Control-arm identity**: the family control arms = the frozen wave-1
   original-exit legs (their `arm_config_digest`s already in TRIAL_LEDGER A-MECH
   rows; controls add no new mechanism, only their comparison role).
5. **Budget rows**: ≤ 57 discovery rows registered in TRIAL_LEDGER
   (`stage=A-MECH`, `fold_scope=DISCOVERY_PRE_PNL`) BEFORE any overlay engine
   run; ledger overflow at any point → STOP → owner decision.
6. **Costs law**: §6 verbatim (spread-once at touch bars, U3, fx6, swap, NET).

**Plan-amendment requirement (owner law).** The cycle plan (v2 draft, §4
budget table) does not know this arm class; adding TB-EXIT-OVERLAY arms to the
FROZEN cycle needs a plan amendment at the registration gate. Draft scope
(5 lines, not the amendment):

1. Add TB-EXIT-OVERLAY as a Stage-A research arm class: same entries, barrier
   exits vs original-exit controls; discovery-side only.
2. Freeze the barrier grid at 18 nodes per applicable family (§3) and the
   SL-first ambiguous-touch law with the >20 % NOT_RUN gate (§4).
3. Freeze the applicability table (§5): B-MEANREV + C-BREAKOUT +
   E-SESSION-intraday only; A-TREND, VOLPROF, routers/gates excluded by
   default with named-exception paths.
4. Register ≤ 57 discovery-ledger rows inside the 1,500-row cap; no scored
   cells added, no eligibility change, no PASS-bar change, no per-leg
   optimization.
5. TB-LABELS stay analysis-only under `triple_barrier/labels/` with the §2a
   firewall (no engine import, no feature use, TRAIN-first, sealed tail
   untouched).

---

## 8. STATUS TABLE (this DESIGN step)

Design done = PASS; anything unresolvable from current data = NOT_RUN with the
named blocker. (Per-family runtime facts are recorded, not resolved here.)

| family | original-exit basis | overlay applicable | resolution available | expected variants | DESIGN status |
|---|---|---|---|---|---|
| A-TREND (17 legs) | close-basis D1 (signal/trail/SL) | NO (default; exception path defined) | M1 for 3 pairs' legs; D1-only for AUDUSD/USDCAD legs | 0 | **PASS** (rule fully specified) |
| B-MEANREV (15) | close-basis (M1/D1) | YES | M1 (11 legs on staged pairs); D1-only: GBPUSD-S019/USDCAD-S011/S016 (USDCAD legs NOT_RUN: no staged panel) | 18 | **PASS** |
| C-BREAKOUT (15) | close-basis (M1/D1) | YES (trail legs flagged for dual-side accounting) | M1 (11); D1-only: AUDUSD-S023/S026, USDJPY-S023/S029 (AUDUSD legs NOT_RUN: no staged panel) | 18 | **PASS** |
| E-SESSION (9) | time/window + gates | CONDITIONAL (intraday members) | M1 (S042, S050, S027); D1 (calendar members) | 18 if measured applicable, else 0 | **PASS** (condition measurable Stage-A from existing dry-run journals) |
| G-XASSET (2) | router signal / levels | NO | M1 | 0 | **PASS** |
| I-STATARB (5) | gates/routers + 1 session | NO (S090 named exception) | M1 | 0 | **PASS** |
| J-REGIME_OPT (4) | signal-only overlays | NO | D1 | 0 | **PASS** |
| VOLPROF ×3 (9) | touch-basis (spec-faithful) | NO (already triple-barrier) | M1 | 0 | **PASS** |

**NOT_RUN items (data facts, named blockers — not design gaps):**
- 14 AUDUSD/USDCAD legs: `NOT_RUN_NO_STAGED_PANEL` (existing trial-ledger
  state; overlay inherits it).
- Any TB arm on the 7 blocked assets: `NOT_RUN_TOUCH_RESOLUTION_NO_INTRADAY_DATA`
  (daily-only data; within-day ambiguity unresolvable).
- E-SESSION node allocation: `NOT_RUN_HOLDING_TIME_UNMEASURED` until the
  Stage-A holding-time measurement runs on the existing journals.

**Overall design-step verdict: PASS** — every element of the dispatch (§1–§8)
is specified from evidence on this checkout; no PnL, no backtest, no
eligibility change, no arm admitted. Everything above is design +
registration-ready and stops before GO by law.
