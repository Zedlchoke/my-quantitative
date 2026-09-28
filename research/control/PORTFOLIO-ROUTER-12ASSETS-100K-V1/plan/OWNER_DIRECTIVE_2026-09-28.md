# OWNER_DIRECTIVE — 2026-09-28 (recorded verbatim at receipt)

Received via Lead session (with a screenshot attachment, non-authoritative),
measured receipt time below. Owner text (Vietnamese, verbatim):

> hoàn thiện bộ điều phối, kiểm thử và qua A7. Việc cần ưu tiên song song là
> chứng minh dữ liệu VIX và giá spot Brent–WTI có thể dùng đúng thời điểm lịch
> sử (PIT). Thiếu bằng chứng đó thì state engine phải dừng
> NOT_RUN_PIT_GATE_FAILED, không được tự thay dữ liệu để chạy tiếp.
>
> bạn tự quyết định dữ liệu cho tôi nhé, và chủ động lấy dữ liệu luôn. Sau đó
> chạy GO scored luôn.

## A1 ruling (authority interpretation, per handbook §2.5 / §3 / P-8 / P-19)

1. **Scope of work directed:** complete the router engine, test it, pass A7;
   prove PIT usability of VIX and Brent–WTI spot as the parallel priority.
2. **PIT law (owner's own words, binding):** without evidenced PIT, the state
   engine STOPS at `NOT_RUN_PIT_GATE_FAILED`. No data substitution to keep
   running. This matches plan §3 and the fail-closed mission.
3. **Data decisions delegated to the Lead** ("bạn tự quyết định dữ liệu") —
   exercised ONLY within repo law: free/keyless/public channels compatible
   with internal research use (P-25 license check per source), no purchases,
   no paid providers, no keyed signups, no credentials; network blocks are
   recorded, never circumvented (L-FXFF-1). Fail-closed where no clean
   channel exists.
4. **Data fetching authorized** ("chủ động lấy dữ liệu luôn") — bounded,
   rate-polite fetches of the state-variable series (and, where a clean
   channel exists, currently-FLAT symbol history) with raw bytes + sha256
   manifests + license notes recorded in the PIT dossier.
5. **"Sau đó chạy GO scored luôn" = standing delegation of the SCORED GO key
   for THIS cycle, conditioned on the two-key structure (P-19 precedent):**
   the Lead may launch scored execution WITHOUT a fresh owner phrase ONLY
   after the independent A7 prelaunch audit returns AUTHORIZED. Until then
   the typed-early words are intent (P-8: a GO before its gate exists is
   intent, never a key). If A7 REFUSES after the remediation loop, the
   session STOPS at the gate and reports — no scored cells. If the PIT gates
   fail, the state engine closes typed `NOT_RUN_PIT_GATE_FAILED` and NO
   scored router run occurs (sleeve-only scoring is NOT a substitution — it
   would be a different question and is not authorized by this directive).

Measured receipt UTC: 2026-09-28T12:53:46Z (registration) / this directive
recorded 2026-09-28 ~13:0xZ window (exact stamp in the session event log
below when written). Registered SCORED GO phrase remains
`GO PORTFOLIO ROUTER 12ASSETS 100K V1 SCORED EXECUTION`
(state: REGISTERED_NOT_CONSUMED until A7 AUTHORIZED, then consumed by the
Lead under this delegation).
