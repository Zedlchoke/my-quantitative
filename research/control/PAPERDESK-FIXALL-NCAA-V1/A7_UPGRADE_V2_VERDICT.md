# A7_UPGRADE_V2_VERDICT — independent fresh-context audit (2026-10-21)

**VERDICT: PASS_WITH_FINDINGS — 0 CRITICAL / 0 HIGH / 1 MED / 4 LOW**

Auditor: independent A7 (fresh context, READ-ONLY on code). Scope: the
UPGRADE V2 commits `5c64af01` (U0), `7036aa65` (U1+U2), `545c2ada`
(U3+U4), `2b0a77f7` (U5+U6), `a895cdfa` (U7 + integration wiring) on top
of `51eb78c5`, at HEAD `a895cdfa` on
`orca/paperdesk-fixall-ncaa-v1-integration`. Spec = the owner package
reproduced in HANDOVER_U0/U1_U2/U3_U4/U5_U6/U7 + PAPERDESK_UPGRADE_V2_FINAL.

## 0. Battery (mandatory ×2)

| run | result |
|---|---|
| Run 1 | **281 passed, 0 failed** in 51.34s |
| Run 2 | **281 passed, 0 failed** in 69.29s |

Per-file: test_upgrade_u1=3, u3=20, u4=10, u5=9, u6=14, u7=11; U0's 3
tests live in test_fixall_w4.py (commit 5c64af01 stat confirms). Matches
the package claim (281 at a895cdfa).

## 1. Hard laws

| law | result | evidence |
|---|---|---|
| feature_gates = owner GOs | PASS | config.json feature_gates: `ai_authority_active: true`, `pm_cutover_active: true`; `git diff 51eb78c5..a895cdfa -- config.json` touches ONLY the ai_provider block (fallback_models, model_id, note, low_balance_usd, prompt-sha erratum); no gate key appears in any of the 5 commit diffs |
| seal.js SEALED + throws | PASS | apps/paperdesk/main/seal.js:22-43 — `LIVE_EXECUTION_SEAL.sealed: true`; `submit()` throws `SEALED: LiveExecution has no implementation` (line 38-42) |
| no push | PASS | `git remote -v` shows origin, but branch has **no upstream configured** (`@{u}` → fatal: no upstream); nothing after a895cdfa on the branch |
| production ledger intact | PASS | `/Users/hoangminhlong/.my-quantitative-data/sports-papertrade-exec-v1/ledger/paper_ledger.jsonl` = 86 rows; chain verified **via the pinned core** (`core.ledger.PaperLedger.load().verify_chain()` → True, 0 errors); types GENESIS 1 / FORECAST 29 / MARKET_QUOTE 17 / DECISION 27 / SETTLEMENT 12 — all ledger-plane, growth only by runner rows |

Note: the two U7 adoption docs (HANDOVER_U7_2026-10-21.md,
PAPERDESK_UPGRADE_V2_FINAL_2026-10-21.md) are **untracked** working-tree
files — no commit exists after a895cdfa (see LOW-4).

## 2. U0 — citation / prompt / verdict honesty: PASS

- **[H1] citation filter**: ai_producer.py:836-863 — `captured =
  {s["url"]: s for s in research["sources"]}`; only model sources whose
  URL is in the captured set survive (`sources = [captured[s["url"]] …if
  s["url"] in captured]`, lines 840-842) — fabricated URLs dropped
  entirely, never re-stamped; ALLOW with zero survivors → `.invalid/`
  write (843-858) + `OPINION_INVALID` gate event "citation filter emptied
  an ALLOW (U0/H1)" (860-862).
- **Excerpt law**: ai_gate_v2.validate_opinion:127-137 — every source
  needs url + fetched_at_utc (128-131) AND a non-empty excerpt (132-134);
  ALLOW with zero sources refused (135-137).
- **[M1] prompt-sha consumption gate**: load_opinion_for
  ai_gate_v2.py:164-177 — opinion prompt_sha must equal the REGISTERED
  sha measured by `registered_prompt_sha` (ai_producer.py:546-562,
  digest-blanked formula); unmeasurable → fail-closed (172-173).
  **Independently re-measured twice with my own implementation of the
  documented formula: `7a1b30cb9c13ef22eb093c4889fc128729efd46dcaaf87ac11c676f66e967414`
  both times = config `prompt_sha256_measured_at_freeze` = the module's
  value.** Whole-file sha (918c0e25…) ≠ the erratum'd 4365381d…, so the
  old registration is indeed not reproducible from the delivered file.
- **[L1] verdict canonicalization**: at load ai_gate_v2.py:163
  (`op["verdict"] = …strip().upper()`); at apply execute.py:2314
  (`str(op["verdict"]).strip().upper() == "VETO"`) and the JS-opinion
  path execute.py:2198-2199.

## 3. U1 — fee truth: PASS

FEE_ONCE_FINDING.md exists (123 lines) and its central claim matches the
code: standard lane fee baked ONCE into `spend`→`vwap`
(pm_moneyline.py:240-241 fee added into spend; :247 `vwap = spend/filled`)
→ `odds = round(1/vwap_ask, 6)` (execute.py:1533, 1562) — fee once in the
denominator; WSL `fee_law_d_eff = shares/(spend+fee)` (wsl_lane.py:362-374).
Settlement carries NO second fee: pinned core `risk.settle` risk.py:276 =
`int(round(stake * (odds_frozen[leg] - 1.0)))` (pinned
…/sports-papertrade-v1/…/risk.py, verified by reading the pinned bytes).
Flat 0.02 is gate-only: laws.py:29 `FLAT_FEE_PRE_CUTOVER = 0.02` applied
at decision_pipeline.py:93 in the EV formula — never in settlement.
Conservative direction documented with numeric bias table
(FEE_ONCE_FINDING.md:95-101).

## 4. U2 — scorecard truth laws: PASS

ai_scorecard.py (schema `ai_scorecard@2`, line 245):
- Results-plane vetoes: ledger SETTLEMENT rows win, caller
  `results_by_mid` fills the rest (lines 120-132); veto without an
  obtainable result → `unscored_vetoes`, excluded from the denominator
  (205-215, 250-254).
- Headline: `ai_layer_value_cents = -veto_hypo` (line 261) as top line;
  data pair `net_value_of_ai_layer_cents = placed_real − veto_hypo`
  (260).
- 100-gate on actually-scored only: `DOWNGRADE_MIN_SCORED = 100` (line
  40) gated on `veto_scored_actual` (295), proposal discloses denominator
  + excluded unscored count (306-308).
- Unscored excluded from `reviews_scored` (246: allow_settled +
  veto_scored_actual only).
- no-verdict / invalid / gate-event classes: NOT_PLACED_AI_NO_VERDICT
  counted with hypothetical PnL only when the frozen evidence shape
  exists AND a result is obtainable, never in the veto denominator
  (155-170); `invalid_opinions` = len(.invalid/*.json) (115-116);
  `gate_events` with kinds + verdicts_by_model (60-93, 280-281).
- Breakdowns per_league/per_model/per_reason_code with
  INSUFFICIENT_EVIDENCE share (283-291).
- Caller compatibility: ops_service.py:1301-1303 passes only
  ledger_rows+opinions_dir (new kwargs default) — as the handover claims.

## 5. U3 — cascade state machine: PASS

ai_producer.py:
- Strongest-first, CONFIG-FIRST: slots = `[model_id] + fallback_models`
  (line 615), never re-ordered; `_first_available` walks `_order`
  (352-368); ONE model per request body (184-193) — no fallback array.
- States: UP/COOLDOWN/HALF_OPEN persisted to
  `ai_review/cascade_state.json` sandbox-aware (69-72, 277-301, atomic
  via `atomic_write_json`).
- Trigger table: `classify_failure` 236-257 (400/404→CONFIG_BROKEN,
  401/403→KEY_ALARM, 402→LOW_BALANCE, 429→RATE_LIMITED, ≥500→TRANSIENT,
  below-HTTP→TRANSIENT); `_apply_transport_trigger` 412-480:
  429 → `max(Retry-After, 15 min)` (460-470); 402 → ALL non-`:free`
  slots COOLDOWN indefinite (hold=True, 443-448) + balance check +
  `AI_LOW_BALANCE` (449-459), free slots untouched; 5xx/timeout → 10 min
  doubling cap 4 h (471-479, constants 74-77); garbage → retry SAME model
  ONCE with RETRY_SUFFIX then fall + soft fail, 3-in-1h → 30 min
  (752-796, 396-409); 400/404 → `config_broken` + `AI_CONFIG_BROKEN`
  (423-432), skipped forever by `_first_available` (363); 401/403 →
  `AI_KEY_ALARM` + ALL slots 30 min (433-442). COOLDOWN expiry →
  HALF_OPEN (330-349); trial success → UP (371-381); trial failure →
  doubled cooldown (483-496). Every transition journals `CASCADE_SLOT`
  (304-327).
- Body flags: `"data_collection": "deny"`, `"require_parameters": True`
  on EVERY body (189-193).
- Balance clock: `check_balance` GET /api/v1/key, None on
  failure/unlimited, never revives by crash (516-538); runs at producer
  start (639-642); below floor → paid slots held + alarm (644-659);
  successful check revives balance-held slots at start only (660-669).
- Budget clock: round stops, remaining candidates stay pending
  (680-685, 883-885). QD2 silence: no available slot → candidate keeps
  waiting (731-734, 801-828).

## 6. U4 — plane hygiene: PASS

- M6 sandbox ai_review plane: ai_gate_v2.py:54-62; threaded through
  produce_for_pending (`sandbox` kwarg, ai_producer.py:595-607), ops
  service (self.sandbox at ops_service.py:776/786/837/1366/1382/1417/
  1465/1488), and the decide paths — battery test_upgrade_u4 (10 tests)
  locks byte-identical real plane.
- M8 atomic+flock writes: `atomic_write_json` ai_gate_v2.py:65-82 (tmp +
  os.replace under fcntl.flock on `<name>.lock`); used by `_save_pending`
  (215-218) and `save_cascade` (294-301).
- M4 EV-outlier terminal + no-churn: execute.py:2395-2406 — a FINAL
  `NOT_PLACED_EV_OUTLIER` row is terminal and excluded from the
  quarantine re-entry pool; 2459-2481 — a quarantined match with no fresh
  quote updates the ops plane only (journaled report +
  `EV_OUTLIER_STILL_QUARANTINED` gate event), NEVER a new QUARANTINED
  ledger row.
- L2 real-mode refusal of sandbox hooks: execute.py:3045-3055 — explicit
  `--sandbox-control-dir`/`--sandbox-registry` without `--sandbox` →
  `BLOCKED_TEST_HOOK_IN_REAL_MODE` exit 9; `--now` and pm_probe seams
  likewise (1354-1359, 1458-1464, 1493).

## 7. U5 — richer evidence: PASS

ai_research.py:
- `collect_evidence(..., kickoff_utc=None, team_ids=None)` optional
  params (249-252); the MATCH-date board via
  `…/scoreboard?dates={YYYYMMDD}` from kickoff (337-348, 132-141) plus
  today's board when the dates differ (337-347); unparsable kickoff
  honestly noted, never guessed (340-342); event-absent → journaled,
  0 sources (368-374).
- Roster cache `_ROSTER_CACHE` keyed (league, team_id, day), errors
  cached — strict once-per-team-per-day (47-124); news filter passes on
  team-name OR first+last roster hit (315-317); single-word names never
  match (113-116).
- Injuries endpoint exactly as specified:
  `…/v2/sports/{sport}/leagues/{slug}/teams/{team_id}/injuries`
  (189-198); each readable item → source {url, fetched_at_utc, excerpt,
  published_utc=lastUpdate, kind} (201-231); pure-$ref items skipped;
  404/any error → journaled 0-source, never invented (401-406);
  one-part paths (SOCCER/WSL) → no URL invented, journaled
  (192-194, 383-391).
- Integrator wiring delivered: ai_producer.py:715-723 passes
  kickoff_utc+team_ids from the pending context and auto-looks-up ids on
  the kickoff board (ai_research.py:274-283, shared `_BOARD_CACHE`
  144-157); `cmd_ai_evidence --kickoff-utc/--team-ids` passthrough
  (execute.py:3003-3023, malformed JSON stays dormant 3014-3021).
- Scoreboard sources carry `published_utc: ""` (line 366) — the board
  has no per-event publish time; honest empty, consistent with the
  never-invent law (the excerpt law requires url+time+excerpt only).

## 8. U6 — CLV MEASURE-ONLY: PASS

clv_plane.py:
- Nothing in the decision path reads it: `execute.py`,
  `decision_pipeline.py`, `ai_gate_v2.py`, `ai_producer.py`, `laws.py`,
  `pm_moneyline.py`, `pm_quote_source.py`, `wsl_lane.py` contain ZERO
  references to clv_plane/clv sidecars (grepped). Importers: ops_service
  (the hourly tick), new_law_shadow (imports only the pure
  `no_vig_probabilities` function), tests.
- Writes only `<data_root>/ops/clv/` or `<data_root>/sandbox/ops/clv/`
  (57-60, 157-159, 272-273); no ledger writes, no gate reads.
- No-vig math correct: `p = (1/odds)/Σ(1/odds)` (63-77); hand-checked:
  1/1.5 + 1/2.8 = 43/42 → {28/43 = 0.651163, 15/43 = 0.348837} = the
  docstring values (26-27); degenerate inputs refused (74-75, 219-220).
- NO_RUN honesty: any odds_fetch exception (incl. ProviderQuotaSkip) →
  `NO_RUN_PINNACLE` + why (189-194, 226-229); None/empty/error pm →
  `NO_RUN_PM` + why (233-247); unmapped pinnacle board → honest reason
  (116-117); no stand-in book, no retries inside.
- Formulas: `clv_pin = entry/close − 1` (286-297); `clv_pm =
  entry·pm_prob − 1` (298-301); one record per match per day via
  filename (270-272).
- Hourly wiring: ops_service.py:1424-1472 — verified-rows only
  (`_ledger_state`), near-kickoff window 2 h + 30 min grace (98-100,
  1433-1434), throttled 3600 s, WSL's polymarket pseudo-key EXCLUDED
  (1317-1334), whole call try/except → one `CLV_SAMPLE_ERROR` incident,
  never blocks the tick (1470-1472); called from tick() at 1546.

## 9. U7 — frozen spec + SHADOW log-only + STOPPED: PASS

- Spec frozen + sha: NEW_LAW_SPEC_FROZEN_V1.md registers
  `7a402a534100828d2a85807ab9d988e34940899b1e3c05df96be8a540c7aa986`
  (digest-blanked); **re-measured independently: self-consistent**
  (blank the registered digest string, sha256 → the same digest). The
  battery re-measures every run (test_upgrade_u7.py:311-320,
  `test_spec_sha_registration_remeasures`).
- Constants mirror the spec: SHARP_PRICE_MARGIN=0.03, EDGE_BASE=0.05,
  EDGE_K=0.5, fee-once adjustment `p_pm_eff = p_pm + 0.05·p_pm·(1−p_pm)`
  (new_law_shadow.py:34-43, 106, 114-116); blend is log-odds of MODEL
  and PIN no-vig, NEVER the PM price (117-121); threshold
  `0.05 + 0.5·|p_model − p_pin|` (122-123); provisional w=0.5 labeled
  NOT A FIT, components journaled (41-43, 107-111).
- SHADOW log-only: writes ONLY `<data>/ops/shadow_new_law.jsonl`
  (sandbox-aware, 50-52, 211-212); ledger read-only; no gate read/write;
  every record carries `note: "SHADOW ONLY — no production decision
  (U7)"` (209); hourly dedup via frozen-inputs hash (134-142, 156-162,
  203-205); tick try/except → one `SHADOW_NEW_LAW_ERROR` incident,
  never blocks (ops_service.py:1474-1492, called at 1547).
- No production decision path references the shadow: zero hits for
  `new_law_shadow` outside ops_service.py:1484 (the log tick) — grepped
  across research/ and apps/.
- Stopped state documented: spec header "FROZEN — SHADOW ONLY … the era
  OPENS only on a separate, explicit owner GO" (spec lines 6-12);
  HANDOVER_U7 header; commit message. No activation flag exists anywhere
  in config/execute (grepped) — activation is necessarily a future
  owner-GO'd commit, not a flip. **By design, not a gap.**

## 10. Adversarial probes (executed, not just read)

1. **Fabricated ALLOW citation cannot survive** — probe + code: captured
   -set filter drops `https://FABRICATED.example/x`, keeps the real URL;
   all-fabricated → 0 survivors → producer's `.invalid` + OPINION_INVALID
   branch (ai_producer.py:840-862). Also battery
   test_u0_citation_filter_and_excerpt_law.
2. **Stale-prompt opinion cannot be consumed** — probe: opinion with
   prompt_sha `f*64` and `abc123` → load_opinion_for returns None
   ("prompt era mismatch, opinion void (U0/M1)"); the registered sha
   loads fine. Unmeasurable registered sha → fail-closed
   (ai_gate_v2.py:172-173).
3. **Paid-slot 402 cannot kill free slots** — probe: `_apply_transport_
   trigger(…, 402)` on a 3-slot chain → paid slots COOLDOWN
   (reason=HTTP_402, indefinite hold), `free/b:free` stays UP and is the
   next slot served (ai_producer.py:443-459, 262-267). Battery
   test_upgrade_u3 locks it.
4. **The shadow evaluator cannot alter a real decision** — static proof:
   execute/decision_pipeline/ai_gate/ai_producer never import
   new_law_shadow; the shadow writes only its own journal; the tick is
   try/except-isolated. Nothing reads shadow output back.
5. **The CLV plane cannot gate a bet** — static proof: zero clv
   references in any decision-path file; sidecar-only writes; the tick
   cannot block the tick (ops_service.py:1470-1472).
6. (bonus) **Mixed-case 'Veto' cannot consume as ALLOW** — probe:
   opinion verdict "Veto" loads canonicalized as "VETO"; apply-side
   .upper() compare independently confirmed (execute.py:2314).
7. (bonus) **url+time-only citation refused** — validate_opinion returns
   False: "a source lacks an excerpt" (ai_gate_v2.py:132-134).

## 11. Findings

### MED-1 — producer Keychain lookup MISSES on the shipped `key_ref` (verified; pre-existing config, documented owner item; fails safe)

`config.json ai_provider.key_ref = "com.myquant.paperdesk /
openrouter-api-key (Keychain)"`. `keychain_key` (ai_producer.py:152-167)
splits on the last "/" so the account becomes `openrouter-api-key
(Keychain)`. Reproduced directly: `security find-generic-password -s
com.myquant.paperdesk -a "openrouter-api-key"` FOUND; with the
`" (Keychain)"` suffix NOT FOUND. Consequence: on this HEAD the producer
takes the honest-degrade path (RuntimeError → key=None, ai_producer.py:
633-637) — candidates stay pending, no opinions, no crash, no wrong
money — i.e. the U3 cascade/AI authority is inert on the real plane until
the owner drops the suffix (one string). Not introduced by this upgrade
(the suffix already exists at 51eb78c5); the package surfaced it and
lists it as owner item #2 (PAPERDESK_UPGRADE_V2_FINAL §5/§9.2,
HANDOVER_U7 §5.2). MED because it is a verified defect in the delivered
state that silently inhibits the headline feature if the runner is
restarted without the fix — while failing safe and being loud in the docs.

### LOW-1 — `openrouter/free` is PAID under the `:free`-suffix law

ai_producer.py:262-267 implements the owner letter verbatim (free ⇔ id
ends `:free`); `openrouter/free` does not, so a 402 would hold it with
the paid slots (fail-safe). The handover flags the ambiguity
(HANDOVER_U3_U4 "Left as-is"). Owner may re-letter; no action taken —
correctly.

### LOW-2 — always-true conditional at ai_producer.py:670

`if cascade_changed or True:` — the cascade state save is unconditional
anyway; the condition is dead code that reads as if conditional. Hygiene
only; behavior correct (persisting every pass is the safe direction).

### LOW-3 — (pre-existing, outside the upgrade diff) sandbox ops scorecard reads the REAL opinions dir

ops_service.py:1301-1303 `_maybe_weekly_scorecard` passes
`opinions_dir=self.data_root / "ai_review" / "opinions_v2"` regardless of
`self.sandbox`, unlike every other ai_review consumer in the file. A
sandbox ops would score the real-plane opinions dir against its sandbox
ledger rows (read-only mixing; suggest-only artifact; 7-day paced so
rarely fires in rehearsals). Introduced at af40456f (FIXALL package,
covered by the prior A7); U2 correctly kept caller compatibility — this
is the one caller that was never sandbox-threaded.

### LOW-4 — U7 adoption docs untracked

HANDOVER_U7_2026-10-21.md and PAPERDESK_UPGRADE_V2_FINAL_2026-10-21.md
exist only as untracked working-tree files; no commit follows a895cdfa.
The audit trail for the upgrade's final report should be committed by the
lane's normal pathspec discipline.

## 12. Spec items not fully done (by design / owner-owned — not gaps)

- **U7 STOPS awaiting a separate owner GO** — explicit package design
  (spec header, HANDOVER_U7, commit message). Verified there is no
  code/flag path that opens the era today.
- **Slug verification vs the live OpenRouter models list** — owner item
  (no network budget in the lane); runtime miss = 400/404 →
  CONFIG_BROKEN + `AI_CONFIG_BROKEN`, the safe behavior
  (ai_producer.py:423-432).
- **OpenRouter credit (paid ≥ 10 USD)** — owner item; current free-tier
  key returns `limit_remaining: null` → balance None → the LOW_BALANCE
  clock cannot preemptively hold paid slots; the paid head would 402 at
  first use and fail safe via the trigger. Documented
  (PAPERDESK_UPGRADE_V2_FINAL §5, §9.1).
- **key_ref suffix fix** — owner item (see MED-1; the finding records the
  verification, the fix remains owner-owned).
- **Merge/push, Electron rebuild, production runner restart on this
  HEAD** — owner items; until the restart, U3/U6/U7 planes legitimately
  produce zero records (cascade_state absent, `<data>/ops/clv/` absent,
  shadow journal absent — fail-quiet by design).

## 13. Verdict rationale

Every U0-U7 law I tested behaves as specified, with file:line evidence
and 7 executed adversarial probes all failing to break a law; the battery
is green ×2 (281/281); all hard laws hold (gates byte-identical to the
owner's post-GO state, seal SEALED/throws, no upstream, production ledger
chain-verified through the pinned core at 86 rows all-plane). No money
law, ledger law, or honesty law is broken → no CRITICAL, no HIGH. One
verified config defect (MED-1) that fails safe and is owner-owned, plus
four hygiene/ambiguity LOWs.

**PASS_WITH_FINDINGS — 0 CRITICAL / 0 HIGH / 1 MED / 4 LOW.**

Top residual items for the owner, in order:
1. Fix `ai_provider.key_ref` (drop `" (Keychain)"`) BEFORE restarting the
   runner — otherwise the AI authority produces nothing (fails safe).
2. OpenRouter paid top-up + slug verification — until then the paid head
   402s (fail-safe) and dead slugs surface as CONFIG_BROKEN.
3. The separate U7 era GO (after the §3 fitting protocol and a w locked
   by registered amendment) — the shadow/CLV/cascade planes stay
   zero-record until the runner restart activates them.
