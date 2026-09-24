# SLEEVE 4 — BTC4H-BANDRIDGE (PROSPECTIVE-SHADOW-V1)

Mounted by owner directive 2026-09-24 ("không cho dùng chung nữa… strategy đó
sẽ được cấp 100k vào PROSPECTIVE-SHADOW-V1 và chạy như các strategy kia").
Shadow law = `plans/PLAN_prospective_shadow_v1.md` §2 (forward-only, no
orders, append-only virtual ledger, no API keys, no backfill as
prospective performance).

## Frozen sleeve law (NEVER edited while the shadow lives)

```text
capital    $100,000 virtual, seeded at ACTIVATION (own sleeve — no shared
           equity; the shared-equity design was withdrawn by the owner)
gate       C3 band state: ON when close > SMA200(H4)*1.03; OFF when close <
           SMA200*0.97 (hysteretic; NO extra dilation)
book       PSV1 Donchian VERBATIM: entry close > max(prior 30 closes) only
           while gate ON; exits DONCHIAN_STOP (close < min(prior 15), after
           min-hold 12), GATE_INACTIVE (gate off), MAX_HOLD 450
exec       decision at H4 close; fill at NEXT H4 open; 6 bps/side full stack;
           funding measured per settlement on held notional (Vision monthly
           archive + public keyless fapi REST for the tail; a failed lookup
           is recorded as 0 = disclosed undercharge risk)
ACTIVATION 2026-09-24T00:00:00Z — no bar before it may enter the ledger
S0 basis   freezes/shadow_group_s0.json (POSTHOC, descriptive): BANDRIDGE
           2020-01→2026-09 +972,763 measured / +1,177,xxx constant,
           GATE-SHUFFLE control +137,080 measured (timing carries real
           information), DD 0.2494; fold nets incl. F4 +175,801 measured
ceiling    everything historical is POSTHOC DISCOVERY; the ONLY thing this
           sleeve can prove is forward behavior from ACTIVATION onward
```

## Operation

```bash
cd .worktrees/btc-h4-band-risk-v1/integration/research/control/btc_h4_band_risk_v1/shadow_bandridge
/Users/hoangminhlong/my-quantitative/.venv/bin/python update_shadow_bandridge.py
```

Idempotent, append-only (`ledger.jsonl` + `state.json`). Run as often as
wanted; only buckets after ACTIVATION are ever recorded. No daemon, no
orders, no keys. The ledger is evidence: never rewrite, never delete.
A failed prelaunch-style audit is WAIVED by the owner this cycle
("khởi A7 lúc này", recorded) — compensating controls: the identical law
was S0-verified against the RECONCILED engine (9e-10 vs PSV1 ledger).
