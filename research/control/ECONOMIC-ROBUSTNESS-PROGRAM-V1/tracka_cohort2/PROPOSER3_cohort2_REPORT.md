# PROPOSER LANE P3 — OPEN-CALL REPORT (BLIND), ERP1-TRACKA-COHORT-2

- task_id: `tracka2-proposer3-open-call`
- role: blind-proposer, lane `proposer3-open-call`
- dispatch sha = start sha = `3de439ab988d82cd246731ae6c277a688f6e2c31`
- Outcome-blindness: HONORED (see Blindness Statement at the end). Taint: **NONE**.

## Mandate

Propose 1–2 NEW FX mechanism candidates OUTSIDE the range-edge/band-break fade
family (RANGEFADE/RANGEEXP/PDHLOC ancestry and its gated variants), checked
against the 129-family dead-labels packet (labels only). No outcome numbers were
sought or seen.

---

# PROPOSAL A — `TRACKA2-P3A-QCRD-H1` — Quote-Cycle Replenishment Continuation (H1)

**One-line mechanism.** A one-sided H1 move executed while the pair's measured
spread sits in the LOW tail of its same-hour census continues one more bar,
because the dealer that facilitated institutional flow at tight quotes
redistributes the resulting inventory gradually; the book rides that
redistribution. Home leg **AUDUSD** (replicate USDCAD). Family: quote-behavior /
liquidity-facilitated flow continuation. NOT a fade, NOT band/level/prev-day
based, NOT session-clock based.

### 1. Payer
Dealer banks that just facilitated large institutional / real-money flow at
tight quotes. They are left holding transient inventory; the impact-minimizing
response is to redistribute over the next 1–4 H1 bars, which produces the drift
we ride. They cannot arbitrage it away: accelerating redistribution raises their
own impact cost — that cost is the premium they pay whoever absorbs the
redistribution. The original flow-taker (benchmark/scheduled execution) already
transacted and is price-insensitive by mandate. Competing market makers face the
same inventory mechanics; there is no free offsetting side.

### 2. Premium (declared band — BINDING)
**0.8–2.5 bps per round trip** per signal (1-bar H1 hold). The band is binding
in the cost-ceiling arithmetic: a measured per-RT expectancy below 0.8 bp at
k=1.0 rejects the mechanism as cost-dominated even if positive; below ~2.0 bp
the book fails the k=2.0 stress ceiling.

### 3. Persistence
Premium persists because dealer redistribution is deliberately time-spread
(impact minimization) and must happen regardless of who notices; front-running
capacity is itself bounded by the tight-spread window. Erodes via: accelerated
pre-hedging/unloading algos, inter-desk netting that reduces external
redistribution, venue-published flow-imbalance data, and regime breaks in dealer
risk limits around policy events.

### 4. Risk transferred
(i) Discontinuity risk — a macro/news jump mid-redistribution strands the
position against a gap (the dealer hedges instantly; we cannot);
(ii) adverse-selection risk — a tight-spread one-sided bar can be a
dealer-initiated reprice rather than facilitated flow, in which case the next
bar reverts against us; (iii) truncation risk — the 20:00 UTC flat rule cuts the
tail of late-day redistributions.

### 5. Observable (PIT on authorized M1 bid/ask only)
From the Dukascopy M1 bid/ask corpora (AUDUSD, USDCAD; 2021-01..2026-06), per M1
minute m: mid `m_m=(bid_m+ask_m)/2`, relative spread `s_m=(ask_m−bid_m)/m_m`.
Aggregate to H1 bar `t` with timestamps `[τ_t−1h, τ_t)`:
- `r_t` = H1 mid close/open − 1.
- Flow mass `S_t = Σ_m Δlog m_m / Σ_m |Δlog m_m| ∈ [−1,1]` over the bar's 60 M1
  returns (signed efficiency ratio of the bar).
- Spread state `P_t` = empirical percentile of `median_M1(s)` of bar `t` within
  the trailing same-hour pool: all H1 bars of the same clock-hour over the
  previous 60 calendar days (strictly past values only).
Decision at `τ_t` (bar fully CLOSED): **LONG** next bar iff `S_t ≥ +0.25 AND
P_t ≤ 0.40`; **SHORT** iff `S_t ≤ −0.25 AND P_t ≤ 0.40`; else flat. Declared
sensitivity tolerance (pre-registered, not post-hoc searched): mass floor
0.20–0.30, gate p35–p45. No band, no prior-day extreme, no level, no retest
appears anywhere in the decision law.

### 6. Holding horizon + decision clock
Hold exactly 1 H1 bar. Decision on every closed H1 bar with close time
`τ_t ∈ [01:00, 19:00]` UTC so the entry bar completes by the 20:00 UTC flat.
Signals on CLOSED bars; fills at next-bar open at the opposite quote.

### 7. Capacity
Order of magnitude **$50–150M per position; ~$0.5–1bn/day aggregate** before the
edge halves. Reasoning: tight-state windows total ~5–8 tradable hours/day;
participation beyond ~0.2–0.5% of interbank flow inside those windows pushes
fills off the opposite quote and adds impact, halving a 1–2 bp edge.
Visible ECN depth per level ($5–20M) is an order-of-magnitude floor on clips.

### 8. Costs (base + stress)
Two fills per RT (entry next-bar open, exit following open), each charged the
fill bar's measured spread × k, k ∈ {1.0, 1.5, 2.0}, taker at opposite quote.
The sha-pinned per-session spread census is the cost authority; its numbers
replace these declared priors at gate evaluation. Declared prior bands (from
quote-curve magnitudes, NOT from the census, which was not in my blind diet):
tight-state AUDUSD fill spread 0.2–0.4 pip ≈ 0.31–0.62 bp/fill (1 pip ≈ 1.54 bp
at ~0.65) → **RT base (k=1.0) ≈ 0.6–1.2 bp; stress (k=2.0) ≈ 1.2–2.5 bp**.
Because the law trades only `P_t ≤ p40` hours, the cost base is anchored to the
narrow-spread segment of the census curve by construction.

### 9. Falsifier
Kill if ANY of:
- (F1) net per-RT expectancy ≤ 0 at k=1.0 on either leg (EXPECTANCY_NONPOSITIVE);
- (F2) net expectancy fails the k=2.0 ceiling implied by the declared band
  (COST_DOMINATED);
- (F3) the **wide-spread mirror** (same law, `P_t ≥ p60`) reproduces the edge —
  then the gate does not encode liquidity-facilitated flow (mechanism dead);
- (F4) an **hour-of-day shuffle shadow** (signal hours permuted preserving the
  hourly marginal) reproduces the edge — clock-shadow-dominated;
- (F5) a future-window re-anchored percentile run (evaluation-only PIT seam
  probe) differs materially from the PIT run — PIT seam failure.
The specific controls that must NOT reproduce: F3 mirror, F4 shuffle.

### 10. Controls and baseline
- **Causal control:** wide-spread mirror gate (inverts the liquidity state,
  keeps the one-bar directional exposure shape and hour-marginal) — must NOT
  earn; if it does, the spread state carries no mechanism content.
- **Inverted control:** sign-flip of the anchor under the same tight gate (fade
  the redistribution) — must NOT earn.
- **Baseline (beta-matched always-on):** AUDUSD **SHORT_ALWAYS day-session**;
  USDCAD **LONG_ALWAYS**; plus an always-in session H1 book matched to the
  anchor's tradable hours for beta parity.
- Vol-content control (pre-registered): re-run with `P_t` replaced by trailing
  realized-vol percentile of the same bar — if the vol-gated book matches the
  spread-gated book, the gate is a vol-level proxy, not a quote-cycle object.

---

# PROPOSAL B — `TRACKA2-P3B-DINV-1D` — Dealer-Inventory Day Continuation (traded day)

**One-line mechanism.** Day-scale siblings of Proposal A's payer: a one-sided
traded-day move executed while the day's median spread sits in the low tail of
its same-weekday census continues one more traded day, riding day-scale
inventory redistribution and mandate-constrained scheduled flow. Home leg
**USDCAD** (replicate AUDUSD). **Disclosed ancestry coupling:** same payer
family as P3-A at a different horizon; if the skeptic adjudicates them one
family, P3-B is the day-clock arm and the two count as one candidate.

### 1. Payer
Dealer inventory redistribution at the day horizon, plus real-money scheduled
execution (month-average trackers, corporate treasury calendars) whose orders
are spread across days and must continue regardless of level. They cannot
arbitrage it away: their continuation is mandate- or impact-constrained, not
signal-constrained — accelerating execution costs them impact and benchmark
tracking error.

### 2. Premium (declared band — BINDING)
**2–5 bps per round trip** per 1-day signal. Binding: measured expectancy < 2 bp
at k=1.0 → reject; < ~2.7 bp → fails the k=2.0 stress ceiling on the USDCAD
census curve.

### 3. Persistence
Day-scale order schedules persist because of mandate constraints (benchmark
tracking, month-average pricing, treasury calendars) and because inventory
redistribution of day-scale flow takes days. Erodes via execution-algo
innovation (IS/VWAP schedules compressing), crowding by CTA-style momentum that
already arbitrages day continuation, and regime changes in dealer inventory
capacity.

### 4. Risk transferred
Weekend gap risk is structurally excluded (daily 20:00 flat, weekend flat).
Transferred risk: day-scale adverse moves when the tight-spread state misleads —
a tight-spread trending day can be the start of a genuine directional macro
regime that reverses on fresh information; plus 20:00 truncation risk.

### 5. Observable (PIT on authorized M1/H1-derivable bid/ask only)
Traded-day bar = aggregation of the session's H1 bars 00:00→20:00 UTC (H1
derivable from M1 per the data plane).
- `r_d` = day mid return (00:00→20:00).
- Flow mass `S_d = Σ_h Δlog m_h / Σ_h |Δlog m_h|` over the day's H1 bars.
- Spread state `P_d` = percentile of the day's median H1 spread within the
  trailing 60 same-weekday days (strictly past; weekday enters only as PIT
  normalization pool, never as positioning).
Decision at the 20:00 UTC close of day `d` (day CLOSED): **LONG** next traded
day open iff `S_d ≥ +0.20 AND P_d ≤ 0.40`; **SHORT** iff `S_d ≤ −0.20 AND
P_d ≤ 0.40`; else flat. Exit at next traded day 20:00 close. Declared
sensitivity tolerance: mass floor 0.15–0.25, gate p35–p45.

### 6. Holding horizon + decision clock
Hold 1 traded day (entered at day open, exited 20:00 UTC same tradable day —
intra-session book, weekend-safe by construction). Decision clock = traded-day
close; signals on CLOSED bars; fills at opposite quote.

### 7. Capacity
Order of magnitude **$100–300M per position** before the edge halves. Reasoning:
the tight-state day set is roughly 30–40% of trading days; footprint beyond
~0.5% of the pair's daily interbank turnover inside those windows halves a
2–5 bp edge; AUDUSD/USDCAD spot turnover (BIS-order $300–400bn/day AUDUSD,
$150–250bn/day USDCAD) bounds capacity far above deployable strategy capital.

### 8. Costs (base + stress)
Entry + exit at opposite quote, fill-bar measured spread × k, k ∈
{1.0, 1.5, 2.0}; census numbers replace these declared priors at gate
evaluation. Declared prior bands: tight-state USDCAD fill spread 0.4–0.9 pip ≈
0.29–0.66 bp/fill (1 pip ≈ 0.73 bp at ~1.36) → **RT base ≈ 0.6–1.3 bp; stress
(k=2.0) ≈ 1.2–2.7 bp**. AUDUSD replicate: RT base ≈ 0.7–1.5 bp; stress ≈
1.4–3.0 bp (day open/close hours).

### 9. Falsifier
Kill if ANY of:
- (F1) net per-RT expectancy ≤ 0 at k=1.0 on either leg;
- (F2) net expectancy fails the k=2.0 declared-band ceiling;
- (F3) the **ungated same-law** (drop `P_d`, keep `S_d`) earns equal or better —
  the spread state adds no liquidity-mechanism content
  (CONTROL_IDENTIFIABILITY_FAIL);
- (F4) the **wide-spread mirror** (`P_d ≥ p60`) reproduces the edge;
- (F5) a **weekday-shuffle shadow** (`S_d` reassigned to random weekdays
  preserving marginals) reproduces the edge — calendar-geometry dominated;
- (F6) future-window re-anchored percentile run (PIT seam probe) diverges.
Must-not-reproduce controls: F3 ungated book, F4 mirror, F5 shuffle.

### 10. Controls and baseline
- **Causal control:** drop the spread-state gate (keeps day-directional exposure
  shape, removes the mechanism content).
- **Inverted control:** sign-flip under the same tight gate (day-scale fade) —
  must NOT earn.
- **Baseline (beta-matched always-on):** USDCAD **LONG_ALWAYS day-session**;
  AUDUSD **SHORT_ALWAYS day-session**.

---

# SIX ECONOMIC QUESTIONS

## Proposal A (QCRD-H1)
1. **Ai trả premium và vì sao không bị arbitrage đi?** Dealer vừa đẩy flow tổ
chức ở spread hẹp trả premium qua chi phí impact của việc redistribute
inventory từ từ; họ không thể arbitrage đi vì đẩy nhanh redistribution làm
tăng impact cost của chính họ, còn flow gốc đã khớp và price-insensitive theo
mandate.
2. **Premium kỳ vọng + rủi ro đuôi?** 0.8–2.5 bps/RT (band ràng buộc); đuôi gánh:
gap/news jump giữa redistribution, adverse selection khi bar tight-spread hóa
ra là dealer-reprice, và truncation 20:00 UTC.
3. **Vì sao tồn tại, cái gì xói mòn?** Tồn tại vì redistribution là tối ưu
impact-minimizing và bắt buộc phải xảy ra; xói mòn bởi pre-hedging algo, netting
liên desk, dữ liệu imbalance công khai, và regime break risk-limit của dealer.
4. **Observable PIT, nguồn nào?** `S_t` (signed M1 efficiency mass) và `P_t`
(percentile median spread cùng-giờ, cửa sổ 60 ngày trễ) đo trên M1 bid/ask
AUDUSD/USDCAD Dukascopy đã cấp quyền; mọi input từ bar đã đóng trước bar lệnh.
5. **Kết quả nào bác bỏ, control nào phải KHÔNG tái tạo?** Net ≤ 0 ở k=1.0, hoặc
thua ceiling k=2.0; mirror wide-spread và hour-shuffle shadow phải KHÔNG tái tạo
edge; future-window re-anchor phải không đổi kết luận (PIT seam).
6. **Chi phí toàn chuyến base/stress ×2.0 còn dư?** Base 0.6–1.2 bp, stress
1.2–2.5 bp (priors, census thay thế khi gate); dư chỉ khi realized edge nằm
phía trên ~1.2 bp (k=1.5) / ~2.0 bp (k=2.0) — nếu edge < 0.8 bp thì cơ chế chết
vì chi phí dù dương.

## Proposal B (DINV-1D)
1. **Ai trả?** Dealer inventory day-scale + scheduled execution (month-average,
treasury) trả qua impact/tracking-error cost của việc phải tiếp tục lịch đặt
lệnh; không thể arbitrage vì ràng buộc bởi mandate, không bởi signal.
2. **Premium + đuôi?** 2–5 bps/RT (band ràng buộc); đuôi gánh: day-scale đảo
chiều khi tight-spread day là regime thật đảo bởi thông tin mới; weekend gap đã
loại cấu trúc (flat 20:00 + weekend).
3. **Vì sao tồn tại, xói mòn?** Tồn tại vì mandate kéo dài lịch thực hiện nhiều
ngày; xói mòn bởi execution-algo nén lịch, crowding CTA momentum, đổi regime
inventory capacity.
4. **Observable PIT, nguồn nào?** `S_d`, `P_d` (same-weekday 60-day trailing pool)
trên H1 derivable từ M1 bid/ask; weekday chỉ vào như normalization PIT, không
phải positioning; mọi input từ ngày đã đóng trước ngày vào lệnh.
5. **Bác bỏ + control không tái tạo?** Net ≤ 0 base, thua ceiling stress, ungated
book ngang-bằng anchor, mirror tái tạo, weekday-shuffle tái tạo — bất kỳ cái nào
đều giết; ungated + mirror + shuffle là các control phải KHÔNG tái tạo.
6. **Chi phí còn dư?** USDCAD base 0.6–1.3 bp, stress 1.2–2.7 bp (AUDUSD
replicate 0.7–1.5 / 1.4–3.0); band 2–5 bp cho dư ~0–3.8 bp sau stress — âm ở
cận dưới band nghĩa là cơ chế chết vì chi phí, band là ràng buộc.

---

# SELF-CHECK (mandated)

- **(a) Strip-gate law test — PASS with disclosed neighbors.** Strip all gates:
  P3-A reduces to all-hours 1-bar H1 momentum; P3-B to 1-day momentum. Neither
  equals any dead family's decision law in the packet: the packet's FX
  continuations are session-clock-specific (FXFV1-A3-P1 London-open), and its
  run-persistence/aggressor families are crypto-asset (RUNPERSIST, M01
  aggressor panel, TAKER-SAT). Neither proposal reduces to any fade/band/level
  law: no prior-day extreme, no band, no retest, no displacement. Nearest-neighbor
  risk explicitly flagged for skeptic adjudication: FXFV1-A3-P1 (session
  continuation), RUNPERSIST (crypto daily), CRYPTO-V9 TSMOM (crypto weekly).
- **(b) Clock-shadow test — PASS.** Decision laws are state-conditioned at any
  tradable hour (A) / any day (B); no fixed clock positioning. Both falsifiers
  include a shuffle shadow (hour-of-day / weekday) that must NOT reproduce,
  directly closing the clock-shadow veto path (cf. CONTROL_OUT_EARNS_CLOCK_RE_CLOCK
  class). P3-B's same-weekday pool is PIT normalization only; the weekday-shuffle
  control addresses it.
- **(c) PIT seam test — PASS.** Every input (`r`, `S`, `P`) is computed from bars
  strictly CLOSED before the fill bar; percentile pools strictly trailing;
  future-window re-anchored runs included as evaluation-only seam probes (F5/F6).

# ANCESTRY SCREEN vs DEAD PACKET (labels only)

Checked against all 129 labeled families and the mandated classes. NOT in any
dead class: not re-clock, not calendar geometry (shuffle-controlled), not
displaced-fade, not nominal-level, not vol-level (explicit vol-content control
in P3-A field 10), not premium-fade, not retest/second-probe, not
clock-shadow-dominated. Not a relabel of the core ban: no band/prev-day break,
no fade of range edges, no gating of a fade. Not a session law: no London-open,
Tokyo, late-NY, CPI, release-order, CA-revision, PPP, commodity-bloc, PC1,
lead-lag, pre-release, carry/funding, DGS10, Dow geometry, hour-reversal, or
stochastic/Bollinger content. Limitation: FXFV3-A5-P1-family1/family2 are
untitled in the packet ("see cycle artifacts") and were not verifiable within
the blind diet; flagged for the skeptic's full adjudication.

---

# BLINDNESS STATEMENT

What I READ:
1. `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort2/PACKET_dead_family_labels.json` —
   labels only, as authorized.
2. The inlined mechanism/economic context in the dispatch (no cohort plans).
3. Directory and file NAME listings only (repo root, `research/`,
   `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/`, data dirs) to locate the
   sha-pinned spread census; the census could NOT be located within safe scope,
   so no census numbers were read and cost figures above are declared prior
   bands, flagged for replacement at gate evaluation.
4. Top-level JSON KEY NAMES (no values) of one existing handoff file
   (`plan_review/HANDOFF_datacost_critic.json`) to confirm the handoff schema.

What I did NOT read: `tracka_cohort2/GO1_RECORDED.json`, any gate
`GO_RECORDED/GO_METADATA` file, any `*REPORT.md` or skeptic/review artifact, any
cohort plan or ancestry-number section, any PnL/PF/win-rate file, shadow
journal, series file, or trial ledger. No outcome number was seen at any point.

Incidents: none. Accidental outcome exposure: none. Taint: **NONE** — both
proposals are UNTAINTED.
