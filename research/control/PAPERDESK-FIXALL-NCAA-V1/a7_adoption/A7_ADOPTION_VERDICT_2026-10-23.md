# A7 fresh adoption audit — FAIL / BUG

Date: 2026-10-23. Independent read-only audit of root `/Users/hoangminhlong/my-quantitative`, branch `main`, exact HEAD `25882fad8a31a5432f5f4fc5a848d302864a3e23`. Implementation commit `d62d22d3b732aa82b8e4763d775150bc2f9931a5` is included; changes between it and audited HEAD are adoption evidence/report files, with no additional implementation changes.

**Verdict: FAIL. Proven G1/G6 WSL BUGs trigger the original owner's A7 BUG stop. NBA acceptance remains separately NOT_RUN. G1–G7 adoption cannot be accepted.** Do not treat a truthful skip message as proof that the source could not be fetched. The new WSL quotes contain PM IDs and quote fields, so old-M48's permitted missing-identity exception does not apply.

## Authority and scope

Read owner ADOPTION_ORDER_G1_G7_2026-10-23.md, PROMPT_FIX_AI_DATA_G1_G7_2026-10-23.md, AUDIT_AI_DATA_2026-10-23.md and adoption report in this cycle directory; AGENTS.md, CLAUDE.md, handbook, registry and applicable fixall plan. Used repository `plugins/quant-research-orchestrator/skills/structured-handoff/SKILL.md` for handoff fields. No code repair, restart, heavy test, registry/ledger mutation, scoring or acceptance authorization was performed. Initial untracked owner/control files were preserved. Audit writes are confined to `a7_adoption/`.

## Findings

### A7-ADOPT-01 — HIGH BUG: new WSL Gamma identity is dropped at caller

`research/papertrade_exec/ai_producer.py:752-756` reads only `pm_crosswalk.pm_event_id`; line 771 passes its result to collector. Actual WSL producer writes top-level `event_id` at `wsl_lane.py:522-523,541`. The five new ledger quote rows contain string IDs: M47=1212932, M45=1212936, M46=1212940, M49=1212944, M43=1214408. Independent call of `_gamma_url_from_quote` on all five retained quote objects returned None. These are new 06:00:51Z quotes, not old M48.

All 18 packets have 0 gamma_event and journal `gamma_event skipped: no gamma_event_url provided by caller`. This is a caller schema defect, not demonstrated Polymarket unavailability. No Gamma request was attempted via this path. Owner adoption stop `missing Gamma without an explanatory journal` must be interpreted substantively: the skip accurately reports a missing argument but does not explain away a known ID being discarded. Even if that narrow adoption clause were read as satisfied by any text, the original prompt independently requires STOP when A7 reports BUG; that condition is now satisfied. G1's explicit NBA live criterion is still NOT_RUN; this WSL defect is independently proven.

### A7-ADOPT-02 — HIGH BUG: G6 loses available WSL quote information and DRAW

`ai_research.py:609` reads `pm_walk.legs` only. Lines 614-619 hardcode HOME and AWAY and request fee_cents/depth_ok. Actual WSL records use `pm_outcomes`, with all three HOME/DRAW/AWAY best_ask, vwap_ask, fee_total_usdc, and walk sufficiency evidence (`budget_short_usdc=0`) written at `wsl_lane.py:498-509,541`.

All 18 real packets have HOME/AWAY decimal odds but null best_ask/vwap_ask/depth_ok/fee_cents and omit DRAW. Example M43 quote HOME decimal odds=5.385771923683274; AWAY=1.4333855717526691; DRAW=4.601936033042705. Its DRAW has best_ask=0.2, vwap_ask=0.2090333637 and fee_total_usdc=0.4275901876, all available in the bound quote but absent from market_block. Fields of differing names/units require a documented schema adapter, not invented numeric equivalence. No assertion is made that fee_cents can be copied directly from fee_total_usdc.

This violates G6-a's copied PM data requirement and first-real-slate complete candidate payload criterion. Although G6 uses two-leg wording, the actual chosen soccer market has three outcomes; even ignoring DRAW, both required HOME/AWAY quote-detail fields are missing. Journal `missing fields retained as null` describes the output but does not make loss of present input data acceptable.

### A7-ADOPT-03 — HIGH BUG: G6 team context categorically omitted for WSL

`ai_research.py:624-627` immediately returns for every league other than NBA. All 18 new WSL packets lack team_block, even though ESPN fixture resolution succeeds and team IDs are available. `ai_producer.py:727-728` forwards the resulting missing blocks to the AI payload. G6-b and its acceptance criterion say every candidate must have team_block for both teams. The journal says structured context is not verified for WSL; that documents incomplete implementation, not a completed G6. This is an observed gap, not NBA-window timing.

### A7-ADOPT-04 — MED acceptance gap: official WSL source is only a shell

All 18 packets count league_official=1. The saved excerpt is navigation plus `common-loading`, without fixture data. `ai_research.py:470-477` returns a source even when team_name_hit=no and otherwise a navigation-name hit can count as yes. The saved M43 excerpt begins `Fantasy Live Blog Scores Fixtures Tables Clubs Players Stats...` and ends `common-loading ..`. HTTP fetch/source presence is real; useful official fixture context is not demonstrated. eng.w.1 name resolution and real scoreboard events do pass, including M43 ESPN event 401902886. Do not report this as a fully validated official-page fixture source.

## Measured checks

| Check | Result | Evidence |
|---|---|---|
| Root identity | PASS | main at exact requested 25882fad8a31a5432f5f4fc5a848d302864a3e23 |
| Adopted collector bytes | PASS | sha256 28207b5a63da7c48baa4e0d9113d8fce7e84daaa61a4b61f247ff8d90f3e5ad2 |
| PDF helper tracked | PASS | nba_injury_pdf.js included in implementation commit |
| Prompt digest | PASS | Recomputed registered_prompt_sha AI_PROMPT_V3 = c2c4fd464f0413a054d94cb2f555f1e9325ed3b78111142b551026f3e2a0c890; 5 opinions match |
| Full root battery artifact | PASS, log inspection only | 323 passed in 62.64s; log SHA c05c184e6d7d4e81a0392eafe05e50a06c9f115b3f4b63ec4b630b605ed64e81; no independent rerun |
| git diff --check | PASS | exit 0 |
| G2 saved probes | PASS artifact requirements | Five per-competition JSON summaries, news+board 200, URLs and genuine fixture excerpt with event ID/two teams; not independently re-fetched |
| WSL retained bytes | PASS | 28 manifest entries all hash/size match; matching currently available source files; 18 packets/5 journals/5 opinions |
| New packet stamps | PASS | 18/18 equal root collector SHA |
| WSL ESPN path/name matching | PASS | eng.w.1 scoreboard with two teams and genuine event |
| WSL Gamma + full PM/team context | FAIL / BUG | Findings 01-03 |
| Useful WSL official fixture excerpt | FAIL | Loading/navigation shell |
| NBA Gamma/rest/B2B/PDF live acceptance | NOT_RUN | No retained first post-adoption NBA acceptance slate |
| G5 real NBA timestamp/stale examples | NOT_RUN | WSL injuries=0; cannot prove NBA citation behavior from those packets |
| Heavy lock | PASS | researchctl locks inspect = FREE_PROVEN; no heavy audit job launched |

G2 artifact inspection validates the requested saved probe contents, not independent contemporary network transport. Some board probes deliberately use historical event dates; this proves the slug resolves a real fixture, not current market availability. Battery green does not negate the production schema failures: new tests chiefly construct pm_crosswalk/pm_walk inputs and NBA context.

Per candidate packet attempts are M43=3, M45=3, M46=3, M47=4, M49=5. Every packet contains exactly scoreboard_status=1 and league_official=1, with news_48h=0, injuries=0, gamma_event=0, official_injury_report=0. Detailed counts and quote-row pins are in audit_checks.json. Evidence is nonempty but materially incomplete.

Five V3 journals are bound to the five opinion candidate hashes. Opinions are VETO M43/M45 and ALLOW M46/M47/M49. Snapshot ledger has 5 FORECAST, 5 MARKET_QUOTE and 4 DECISION rows. Gate events show M43 VETO, then M45 VETO and M46/M47 ALLOW consumed, and M49 ALLOW produced at 06:38:02Z with no consumption in this snapshot. Opinion production does not prove complete required input data, and four decisions are not five. Retained journals include autonomous web research; such later research does not repair missing structured base payload or prove a Gamma base request occurred.

## Runtime qualification

Read-only ps and lsof independently find PID 15385 alive, start Fri Oct 23 09:56:51 2026, command `python -m research.papertrade_exec.ops_service --data-root /Users/hoangminhlong/.my-quantitative-data/sports-papertrade-exec-v1`, cwd `/Users/hoangminhlong/my-quantitative`. Together with all 18 post-start packet stamps and exact root bytes, this strongly supports correct adopted collector path. It is not a direct dump of Python's in-memory module bytes. Collector stamping at ai_research.py:765-766 hashes disk bytes on invocation, not loaded function bytecode, so avoid an absolute claim of direct in-memory SHA attestation. An rg inventory (including hidden directories, excluding .git/.venv) finds only the root ai_research.py. No restart or runtime intervention by A7.

## Required disposition

STOP adoption acceptance and report these BUGs to owner/coordinator now. Under the adoption-only order, no repair is authorized here; amendments to the exact pinned collector require owner handling. Do not wait for NBA to classify already observed WSL failures. Do not claim G1–G7 acceptance until an authorized correction has been reviewed, targeted real-schema tests and required root battery pass, new WSL artifacts demonstrate actual PM identity/detail and both-team context, NBA actual first-slate Gamma/rest/B2B/PDF checks complete, then fresh A7 PASS and coordinator reconciliation occur. G7-ii remains diagnostic-only and unchanged.

This audit is complete as a FAIL report; the adoption cycle is not complete or accepted.
