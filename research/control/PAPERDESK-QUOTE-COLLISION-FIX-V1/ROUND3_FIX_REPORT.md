# W1.4 round3 micro-fix

Baseline `6026fb9328a670b4e2df81db3f88e5d0f6218aff`; code commit `81ba710f0480bade3fde145569f3b8944c9e46dd`. Only source delta is an exact block move in wsl_lane.cmd_decide: run the existing W1.4 guard immediately after selecting qrow and before downstream quote field indexing, stake and recheck construction. Existing zero-stake terminal decision/note/journal path is reused. No new helper or identity semantics. Complete candidates retain the same downstream construction/evaluation path.

Original two A7 caller probes are regression tests in test_quote_collision_wsl_caller.py, with unchanged quote/fixture/Led data. They run actual wsl_lane.cmd_decide and actual quote_collision; only core/fixture/ledger seams mocked. Missing bookmaker/hash/event/market/leg yields one zero-stake QUOTE_IDENTITY_MISSING DECISION, a missing-field reason and journal entry, no exception, EV/stake/recheck not called. Complete-candidate control reaches unchanged downstream evaluation.

Standard caller scan: execute.cmd_decide passes selected qrow into quote_collision before risk/AI. Earlier crosswalk_ok reads fixture team/kickoff only, not bookmaker/payload/event/market/leg identity. No matching premature source-field access was found. Two actual standard cmd_decide missing-book/hash regressions pass; execute.py is entirely byte-identical to round3 baseline. Its first-quote freeze law is preserved.

Full battery twice: **372 passed/0 failed/0 skipped** each, durations **65.06s / 62.2s**; sequential exit0, identical result counts. Command `PYTHONPATH=. /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest -q tests/papertrade_exec`; verbatim ROUND3_BATTERY_1.txt and ROUND3_BATTERY_2.txt. Targeted caller+identity+W1 suite: 63/63. Heavy lock FREE_PROVEN before sequential runs.

Full current ledger still contains exactly the frozen 46 MARKET_QUOTE rows, unchanged. All four original candidates CLEAR with INCOMPLETE_PEERS_SKIPPED=10 each; exact summary ROUND3_VERIFICATION.json. Round2 full per-row disclosure dossier remains valid. No production DECISION replay or historical edit.

V3 registered digest c2c4fd464f0413a054d94cb2f555f1e9325ed3b78111142b551026f3e2a0c890; frozen56 FORECAST f12710e2d5f89b5d232d5b49358d791d7fa0b49d77152dc9c61baf8ac02cf0f4; first48 f6dd607c6ebb6e6173047a06208b9c6ea733e67599a43e99068cfa36dadc5240 unchanged. Entire execute.py (including F1/F2/two-tier), V3/producer/gate/laws/config/decision pipeline files unchanged. Entire WSL file equals baseline with only the exact block movement above; W1.5/EV/AI/stake/selection expressions unchanged.

Fresh independent A7 R3 pending on committed HEAD. Only PASS/PASS_WITH_FINDINGS with zero HIGH/MEDIUM permits merge main, rebuild/restart, adoption rounds1–3 dossier and commit+push. Otherwise BLOCKED/STOP.
