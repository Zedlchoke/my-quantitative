# PLAN — SOL-MEME-SHADOW-PILOT-V1 (ORC-4 read-only shadow pilot ≤7 days, ZERO scored, $0)

- cycle_id: SOL-MEME-SHADOW-PILOT-V1 · asset: crypto · budget 0/0 (ZERO
  scored cells — no strategy PnL, no policy comparison, no skill claims may
  be computed or implied) · base snapshot: orca/smwfp-v1-integration @
  a3e35cd3e5b824b67fe8decc432601a749fd369f (owner-pinned) · registered
  2026-10-16.
- Predecessor SOL-MEME-WALLET-FOLLOW-PREP-V1 is TERMINAL and its artifacts
  are NEVER modified. Interpretation fixes are recorded on THIS branch as
  new artifacts referencing (not editing) predecessor docs.

## Owner authorization (verbatim clauses; full text in AUTHORIZATION_RECORD.md)

- "Tôi chọn hướng ORC-4: chuẩn bị và chạy một pilot shadow READ-ONLY tối đa
  7 ngày để đo khả năng quan sát và mô phỏng thực thi."
- "Mục tiêu không phải chứng minh có edge trong 7 ngày. Mục tiêu: biết hệ
  thống có nhận đúng giao dịch ví, đúng thời điểm và lấy được quote vào/thoát
  đủ trung thực để đáng đầu tư bước tiếp theo không."
- "Tôi cho phép đăng ký successor cycle CHỈ cho pilot read-only này qua
  researchctl nếu quy trình repo yêu cầu, budget scored PnL = 0. Không mở
  cycle scored strategy hoặc đăng ký GO phrase cho việc tính PnL."
- "Sau khi spec freeze + tests + independent preactivation audit PASS: tôi
  cho phép kích hoạt collector read-only này, không cần hỏi lại cùng quyền
  activation." (No repo GO phrase exists for a read-only collector; none is
  registered.)
- "Cho phép một scheduled task/service có phạm vi đúng pilot ≤7 ngày, có
  end_at và auto-stop, chỉ khi cơ chế môi trường hỗ trợ. Dùng công cụ
  automation/service chính thức … Không tạo một exec ngủ nhiều ngày. Không
  để agent chiếm phiên chờ suốt 7 ngày. Nếu môi trường không hỗ trợ chạy
  bền, giao start/stop commands, readiness report và ghi NOT_ACTIVATED."
- "Hết pilot phải auto-stop. Không tự gia hạn, không mở scored, không mua
  dữ liệu, không PnL, không giao dịch, không push/merge."

## Hard boundaries

$0 new spend; no account creation, no terms acceptance, no paid endpoint,
no bot-wall bypass, no scraping of REJECTED_LICENSE frontends (pump.fun web
ToS §21(h) stands). No private keys/signing/funding; no sendTransaction /
sendBundle / approve / orders / claim-airdrop / token-link interaction;
network allowlist = read-only data + quote endpoints only; token metadata
and API payloads are untrusted input. No scored computation of any kind.
Quota/storage/time self-stop is a HARD law. No push, no merge, no history
rewrite. Missing evidence = NOT_RUN / UNAVAILABLE_FAIL_CLOSED.

## F2/F3 closure (preconditions for activation; verifier-confirmed first)

- **F2 (timestamp ordering, production path)**: every signal→decision→quote
  step carries real timestamps: source event (slot/blockTime/signature) →
  provider_received_at (measured at ingest) → decision_at = signal
  availability + locked modeled latency, computed ONLY after the signal row
  is journaled → quote_requested_at/quote_received_at → entry eligibility.
  No decision may exist before its signal row; missing/untrusted timestamp →
  typed refusal (reason recorded), never an imputed time. Follower fill is
  NEVER the source transaction price. chain blockTime never substitutes for
  a receive timestamp.
- **F3 (wallet eligibility snapshots)**: `eligibility_snapshots` module —
  immutable snapshot files (cutoff ts, selection rule id + version, source
  hashes, member list, labels). Law: wallets are selected only from history
  strictly before the cutoff; missing history ⇒ `INSUFFICIENT_HISTORY`, and
  the word "smart money"/skill is forbidden; the pilot cohort is a declared
  activity criterion cohort labelled `TECHNICAL_MONITORING` (first-appearance
  in-cohort, mechanical, declared before any results); NO re-selection after
  seeing pilot numbers.
- **D (version gate)**: decoder reads the transaction version from the raw
  payload; supports `legacy`/`0`/`1`; any other/unknown version → typed
  `UNKNOWN_VERSION_GAP` refusal row (no silent drop); version support is
  never enabled "just to pass an error" without raw-payload + official-docs
  evidence (cross-ref predecessor SOURCE_MATRIX).
- **C (fill model)**: primary fill evidence = quote received AFTER
  decision_at for the locked size (`EXECUTABLE_QUOTE_CANDIDATE`) or
  curve-state derived price (`MODELED_FROM_STATE`) — price may be better OR
  worse than the whale's. The "follower always worse than whale" grid is
  demoted to a STRESS-ONLY scenario (`stress_worse_than_whale`), never the
  primary model. Quote ≠ fill; quotes carry age and are never marked as
  executed.

## Frozen pilot scope (the ONLY authorized observation window)

- Venue: pump.fun bonding curve program (measured ID, predecessor
  SOURCE_MATRIX) as the single launch venue path; migration/PumpSwap events
  are OBSERVED and recorded only (no migration modeling).
- Token cohort: first 8 (cap 10) NEW mints discovered from activation on
  that program with a parseable creation transaction and derivable curve
  account; cohort LOCKED at 8 members or 90 minutes after activation,
  whichever first; observed from creation (age 0). Identity = mint address
  only.
- Wallet cohort: `TECHNICAL_MONITORING` per F3; cap 25 wallets by
  first-appearance order; cutoff = end_at; snapshots with source hashes.
- Hypothetical size: primary 0.1% of curve/pool reserves; stress 1.0% only
  on the first 20 entry signals. Quotes only — never an order, never a fill
  claim.
- Quote schedule (locked): entry decision checkpoint, T+30m, T+6h; T+24h
  only while total quota usage <50%. Each checkpoint tries the quote path
  for exit feasibility; results classified
  EXECUTABLE_QUOTE_CANDIDATE | MODELED_FROM_STATE | NO_ROUTE | STALE_QUOTE |
  QUOTA | TOKEN_RESTRICTION | NO_EXIT — refusals stay in the denominator.
- Time: start_at = actual first successful ingestion tick; end_at =
  start_at + 7×24h exactly; both recorded UTC and Asia/Ho_Chi_Minh.
  Auto-stop at end_at, quota ≥90% (5,400 requests), or storage ≥90%
  (108 MB). No renewal, no cohort change after activation.

## Quota & collection budget (committed before first tick)

≤6,000 outbound requests total across ALL endpoints; tick period 20 min
(official cron automation); ≤25 requests/tick; ≤50 transactions/token/day
journaled (cursor-based); ≤120 MB storage; per-tick wall cap 90 s (a tick
that overruns stops itself and records TECH_TICK_OVERRUN). Reads use
finalized commitment; cursor overlap re-read each tick (dedupe absorbs
re-processing); nothing is counted as observed before finalization.

## Interpretation fixes (recorded on this branch; predecessor docs untouched)

A. Block accessibility measured at probe points ≠ continuous/complete
   coverage; the pilot MEASURES observed completeness of its own windows.
B. Archival transactions ≠ historical pool/account state; capabilities are
   ledgered separately (block bytes / tx decode / pool-state reconstruction
   / live quote each have their own row and evidence class).
C. See fill-model law above (stress-only wording for the worse-price grid).
D. See version gate above.

## Activation & operations law

Sequence: F2/F3/D/C implemented + tested → NO_BROADCAST_PROOF re-proven →
independent preactivation audit PASS → THEN activation via the official
cron automation tool (recurring 20-min tick whose prompt executes the
committed runbook tick; self-stops at end_at/quota/storage and instructs its
final fire to delete the automation). The controller observes the first tick
in-session and records ACTIVATION_RECORD (success/failure with automation
id, start_at/end_at UTC + ICT) or NOT_ACTIVATED with the blocking reason.
Durable runtime: canonical code lives on this cycle's branch in git; a
hash-pinned runtime copy + all data live under
`~/.my-quantitative-data/sol-meme-shadow-pilot-v1/` (with sha256 manifests);
the tick verifies the runtime copy hash before running and fails closed on
mismatch. Manual start/stop commands are provided in OPERATIONS_RUNBOOK.
The agent session does NOT stay alive for 7 days; closeout is executed by a
fresh session via the runbook (fresh-context end-of-pilot verifier
dispatched against the frozen closeout SHA). No other program's automation
is touched.

## Reporting law

Pilot reports OBSERVED / MODELED / UNVERIFIED / NOT_RUN for every capability
claim: events/tokens/wallets/sessions, parse + attribution success rates,
receive/decision/quote latency distributions, entry/exit quote availability,
gaps/refusals/stuck cases. NO wallet-skill conclusion, NO strategy
profitability conclusion, NO policy PnL is computed or implied — pilot
feasibility conclusions are limited to A (observability sufficient to design
a scored study?), B (which sources/capabilities are needed and why), C
(not worth continuing at current scope?).

## Deliverables

PILOT_PLAN (this file) · AUTHORIZATION_RECORD (verbatim) · F2/F3/D/C
remediation code+tests (`research/solshadow/`) · wallet snapshot module ·
collector + quote observer + tests · NO_BROADCAST_PROOF (pilot build) ·
ACTIVATION_RECORD or NOT_ACTIVATED · raw/event/decision/quote manifests ·
OPERATIONS_RUNBOOK (incl. closeout runbook) · VERIFIER_REPORT (end-of-pilot,
fresh context) · REPORT_VI · NEXT_GATE_PACKET · structured handoffs
(`zcode_orch_v3_handoff@1`). Control dir:
`research/control/SOL-MEME-SHADOW-PILOT-V1/` on the integration branch.
