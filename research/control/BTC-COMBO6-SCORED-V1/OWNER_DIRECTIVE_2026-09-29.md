# Owner directive — BTC-COMBO6-SCORED-V1 — 2026-09-29

Verbatim (ZCode chat session, 2026-09-29, with 2 screenshots attached):

> "implement cho tôi các strategy này thành 1. Rồi sau đó chạy scored run
> back test. Nhớ phải có A7 kiểm toán độc lập và nhớ tối đa hoá agent để
> công việc nhanh hơn"

Screenshots (sha256 at copy time):
- owner_screenshots/Capture.PNG  — strategy detail: Momentum 1%/4h · TP1/SL1 · 5m, BTC/USD, BUY $10,000
- owner_screenshots/Capture-1.png — table of 5 strategies: MA spread turns ×2, MA cross, RSI 20/55, MA trend

Authority reading (handbook §2.5 "owner words are literal authority"):
- Command (not a question) ⇒ authorizes: implementing the 6 strategies as one
  portfolio, the scored run backtest, independent A7, and maximal agent
  parallelism.
- The scored execution key remains TWO-KEY: A7 prelaunch AUTHORIZED first;
  this directive is consumed as key-2 only at that gate (DAYTRADER-100-V1
  standing-directive precedent). A7 REFUSED ⇒ STOP and report.
- No authority granted for: push, merge to main, S1 opening, purchases,
  live/paper deployment, parameter changes to the owner-pinned specs.
