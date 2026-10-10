# V10 VERIFY — Round-10 GO-state reconciliation (independent fresh-context verifier)

- Cycle: `SPORTS-PAPERTRADE-EXEC-V1` · branch `orca/spt-exec-v1-integration`
- Verifier: A7-style independent fresh context. Recomputed from bytes; tried to
  refute; repaired nothing. $0 spent.
- Measured start head: `14871d762b51cc2176ce3c60520e06086fe3c2d0`
  (ERRATUM_EXEC_6 commit) — matches claim. Root main measured
  `105318e682c85f5014073f7267e640ea90c84ceb` (~105318e6) — matches claim.
- Locks: `researchctl.py locks inspect` → `FREE_PROVEN` (no row, flock free).
- Worktree porcelain clean before and after all verifier runs.
- Verifier runs that wrote outside this repo: one read-only Polymarket probe
  (journal `journal_V10_VERIFY_PROBE_20261010T035757Z.jsonl` +
  `probe_report_V10_VERIFY_PROBE_20261010T035757Z.json` in the CUTOVER-PREP
  cycle's own data plane, per its live_probe.py non-interference assertions);
  read-only curl of the live dashboard. The real ledger was NOT written by the
  verifier (mtime unchanged, 19 rows before and after).

## OVERALL: RECONCILIATION_CONFIRM

All controller claims (1)–(4) are proven from bytes. Zero FAIL items.
One MEDIUM finding **F1** (residual stale phrase row in the sibling cycle —
must be corrected with, or before, the next owner decision; see Item 4) and
three observations O1–O3. Typed-GO state coherence for the next owner decision:
the program row's new phrase is coherent and lawful (Section "Coherence" at the
end); the stale sibling row is the one incoherence left standing.

---

## Item 1 — GO timeline re-derivation: PASS

(a) GO_TOKEN.json (worktree `research/control/SPORTS-PAPERTRADE-EXEC-V1/GO_TOKEN.json`):
`go_phrase_typed_by_owner` == `GO SPORTS PAPERTRADE EXEC V1 RUN ALL`,
`typed_at_utc` == `2026-10-07T11:08:47Z`, transcribed-by note present. Exact match to claim.

(b) Journal = ROOT `plans/CYCLE_REGISTRY.events.jsonl` (1994 lines; the
worktree mirror journal is a snapshot that ends at this cycle's registration
2026-10-07T08:48:33Z — the root journal is the authority):
- line 1758, `2026-10-07T11:08:47Z` REGISTRY_SAVED, write_token
  `update:SPORTS-PAPERTRADE-EXEC-V1:OWNER GO typed and transcribed (P-8 two-key: …` (truncated token);
- line 1759, `2026-10-07T11:08:47Z` CYCLE_UPDATED phase →
  `GO_CONSUMED 2026-10-07 — owner typed verbatim 'GO SPORTS PAPERTRADE EXEC V1 RUN ALL' in a new message at 2026-10-07T11:08:47Z; transcribed to GO_TOKEN.json` (verbatim phrase + "owner typed" present);
- line 1762, `2026-10-07T11:19:08Z` CYCLE_UPDATED →
  `GO_CONSUMED CAPTURE_ACTIVE (owner typed THE ONE phrase verbatim 11:08:47Z; consumed root+mirror per ERRATUM_EXEC_1 D-1; first REAL rows audited: GENESIS 1000 USD …)`;
- commit `b250bfb16c6fe68ecd24473b3fc8c8bd7c2c3c83` — message starts
  `GO CONSUMED (P-8): owner typed 'GO SPORTS PAPERTRADE EXEC V1 RUN ALL' verbatim 2026-10-07T11:08:47Z …`; committed 2026-10-07T18:09:14+07:00 == 11:09:14Z; `merge-base --is-ancestor` confirms it IS an ancestor of HEAD 14871d76.

(c) Real ledger GENESIS row 1: `at_utc 2026-10-07T11:09:54Z`, wallet 100000¢,
`key_fingerprint 2f08a3d2a61b`, prev `000…0`, row_sha `15421b7ea412…`.

ORDERING: typed 11:08:47Z → journal GO_CONSUMED + CAS save 11:08:47Z →
commit b250bfb1 11:09:14Z → ledger GENESIS 11:09:54Z → journal
"consumed root+mirror per ERRATUM_EXEC_1 D-1" 11:19:08Z. Consumption evidence
strictly precedes the first REAL ledger row: the capture was authorized by the
consumed GO. Ordering proves consumption.

NO RE-TYPING: grep of the entire root journal for `RUN ALL` → 9 events:
1757 (pre-GO registration text), 1759/1762 (the 2026-10-07 consumption), and
1966/1969/1978/1980/1989/1994 (2026-10-10 descriptive phase/registration texts
— the stale "standing phrase REGISTERED_NOT_CONSUMED" wording, i.e. exactly
the drift, never a typing event). Worktree mirror journal: 0 hits. Root
`.runtime/orchestrator_v3/events.jsonl` (1684 lines): 0 hits. No event of any
kind re-types RUN ALL after 2026-10-07.

## Item 2 — Stale-field history: PASS

ERRATUM_EXEC_5_LIVE_SERVICE.md (written 2026-10-08, before round 9) §D-4,
quoted:
> "The registry row's `phase` field truthfully reads `GO_CONSUMED CAPTURE_ACTIVE`
> (evidence above) while the `go_phrase_state` field still reads
> `REGISTERED_NOT_CONSUMED`. … `go_phrase_state` is a stale bookkeeping field the
> researchctl `cycle update` surface does not expose. Resolution: recorded here
> (CAS-only policy — no hand edits to `plans/CYCLE_REGISTRY.json`), and the
> refreshed `--phase` label via `researchctl cycle update` carries the drift
> note. If a future researchctl version exposes the field, it may be
> CAS-normalized with this erratum as the reason reference."

Journal DRIFT NOTE carried since 2026-10-08: first at line 1818
`2026-10-08T09:25:46Z` — "DRIFT NOTE: go_phrase_state field still
REGISTERED_NOT_CONSUMED is stale bookkeeping — consumption evidenced by journal
2026-10-07T11:19:08Z + GO_TOKEN.json (ERRATUM_EXEC_5 D-4), CAS-only, no hand
edits" — and again at 1821 (10-08T09:39:27Z), 1969 (10-10T02:17:06Z),
1978 (02:38:26Z), 1980 (02:38:59Z), 1994-from (03:46:05Z), each citing
ERRATUM_EXEC_5 D-4.

## Item 3 — CAS fix: PASS (observations O1, O2)

Root registry row `SPORTS-PAPERTRADE-EXEC-V1` (measured at root main 105318e6):
- `go_phrase` == `GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER` ✓
- `go_phrase_state` starts `REGISTERED_NOT_CONSUMED (registered
  2026-10-10T03:45:02Z for the Polymarket cutover scope per
  AMENDMENT_SOURCE_SWITCH_POLYMARKET + ERRATUM_EXEC_6; previous phrase
  'GO SPORTS PAPERTRADE EXEC V1 RUN ALL' was OWNER_GO_TYPED 2026-10-07T11:08:47Z
  and CONSUMED 11:19:08Z per GO_TOKEN.json + journal + ledger genesis — the
  stale REGISTERED_NOT_CONSUMED reading flagged in ERRATUM_EXEC_5 D-4 is hereby
  corrected)` — inline consumed-history present ✓
- journal save event line 1991 `2026-10-10T03:45:02Z` REGISTRY_SAVED, writer
  "controller: R10 GO-state reconciliation (CAS + ERRATUM_EXEC_6)",
  write_token `update:SPORTS-PAPERTRADE-EXEC-V1:GO_STATE_FIX:2026-10-10T03:45:02Z`,
  content_sha256 `8daa51c223df60cbb269cfd0436ab2c9b11fb93e90ef5975f3755122045e13be` ✓

No collateral change — structured JSON diff of `plans/CYCLE_REGISTRY.json`
between root commits `0c110b73` (pre) and `105318e6` (post): 135 cycles before
and after, cycle-id sets equal, and the ONLY row that differs is
SPORTS-PAPERTRADE-EXEC-V1, with fields exactly {go_phrase, go_phrase_state,
head, phase, updated_at_utc}. Spot checks (dict-equality proven for ALL rows,
including these three): `SPORTS-POLYMARKET-CUTOVER-PREP-V1`,
`SOCCER-INTL-WC-EURO-PAPER-PREP-V1`, `CRYPTO-NG1` — unchanged. Top-level
`updated_at_utc`/`writer`/`write_token` changed as metadata of the saves.
`head` now `14871d762b51cc2176ce3c60520e06086fe3c2d0` == program branch HEAD ✓.
`phase` at the CAS save was the B1R_RESEAL text (untouched); the R10 phase
replace landed 63 s later as its own journal-recorded save (line 1992) with
field events 1993 (head db53d8dc→14871d76) and 1994 (phase from/to both
preserved; "B1R_RESEAL carried").

- O1 (observation): the go_phrase/go_phrase_state field change has no
  per-field CYCLE_UPDATED events — the REGISTRY_SAVED event 1991 with the
  GO_STATE_FIX write_token is the sole journal record of that save. The claim
  only requires the save event (present); noting the asymmetry with the
  head/phase saves which do emit field events.
- O2 (observation): ERRATUM_EXEC_6 §2 "phase carried forward untouched
  (including the B1R_RESEAL text)" is true of the 03:45:02Z CAS save; the
  immediately following 03:46:05Z save (separately journaled, event 1994)
  replaced the phase's verbatim B1R_RESEAL + SOURCE_SWITCH_AMENDMENT text with
  the condensed R10 text. Nothing lost: the old verbatim text survives in
  event 1994 `from` (and events 1969/1978/1980), and the amendment terms live
  in AMENDMENT_SOURCE_SWITCH_POLYMARKET.md on the branch.

## Item 4 — Lawfulness: PASS_WITH_FINDING (finding F1)

- Repo law supports consumed-GO irreusability: HOW_TO_BE_A_LEAD_ENGINEER.md
  §19.3 (P-8): owner types the GO phrase "đúng nguyên văn, mới, tại gate của
  chính nó. GO gõ sớm = intent, chết unconsumed; … GO không mang qua cycle,
  không sống qua pause" (GO must be typed fresh at its own gate; a GO does not
  carry across cycles or survive a pause); §16 house rules: a closed cycle's
  "GO phrase của nó chết (consumed hoặc extinguished-unconsumed)"; line 159:
  "scored execution vẫn cần gate của cycle + GO mới của owner (P-8)".
- ERRATUM_EXEC_6 does NOT reuse RUN ALL: §1 "Conclusion: RUN ALL was CONSUMED
  and is spent (P-8)"; §2 registers the NEW phrase for the cutover scope. ✓
- NEW phrase distinctness: all 97 non-empty `go_phrase` values across the 135
  registry rows enumerated; `GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER`
  appears exactly once (this row); zero collisions anywhere (exact or
  whitespace/case-normalized); no other phrase contains "POLYMARKET". ✓

**F1 (MEDIUM — residual stale row, same drift class, uncorrected):** the
sibling row `SPORTS-POLYMARKET-CUTOVER-PREP-V1` still carries
`go_phrase` == `GO SPORTS PAPERTRADE EXEC V1 RUN ALL` (the CONSUMED phrase)
with `go_phrase_state` == plain `REGISTERED_NOT_CONSUMED` (no inline
correction), and its `phase` still reads "both gates REGISTERED_NOT_CONSUMED
('GO SPORTS PAPERTRADE EXEC V1 RUN ALL' shared + 'GO WSL WINPROB PROSPECTIVE
PAPER V1 BET_PAPER' split)". That row was registered 2026-10-10T02:15:33Z
under the round-9 stale belief and the R10 CAS fix did not touch it (proven by
the Item-3 diff). The registry therefore presents TWO conflicting activation
phrases for the same cutover: the program row's lawful new phrase vs the
sibling row's spent phrase. ERRATUM_EXEC_6 §4's "both REGISTERED_NOT_CONSUMED"
repeats the stale framing. Same CAS mechanism that fixed the program row can
fix the sibling row. Remediation belongs to the controller plane (this
verifier repairs nothing). Note: the WSL split phrase `GO WSL WINPROB
PROSPECTIVE PAPER V1 BET_PAPER` is registered in plan text
(PLAN_sports_polymarket_cutover_prep_v1.md line 9), not in any registry
go_phrase field (the WSL row's own phrase is …FIRST BATCH) — informational.

## Item 5 — Settlement 401918299 recompute (verifier's own code): PASS

Ledger `/Users/hoangminhlong/.my-quantitative-data/sports-papertrade-exec-v1/ledger/paper_ledger.jsonl`:
19 rows.
- pnl: stake 500¢ × (AWAY 2.34 − 1) with result AWAY ⇒ exact Fraction
  arithmetic = **670** exactly (float artefact 669.999…9 is binary
  representation; ledger integer 670 correct). Row 19 `pnl_cents` = 670 ✓.
- equity chain recomputed: 100000 (GENESIS) → +395 = 100395 (row 10) →
  +405 = 100800 (row 11) → +670 = **101470** (row 19) — all equal the rows'
  `equity_after_cents` ✓.
- sha chain: canonicalization read from the byte-pinned writer
  (`research/papertrade/ledger.py` sha256 66921271… == pins.json pin):
  `sha256(json.dumps(row_minus_row_sha256, sort_keys=True, separators=(",",":"), ensure_ascii=True))`, prev-link chain. Verifier's independent walk of ALL 19 rows: every
  row_sha256 recomputes and every prev_row_sha256 links; chain head =
  `53449ef5ad920c900f6a9236cd5bc1709d2dc39a0aa24ddc095ddcbeea044bb3`
  (53449ef5…) ✓.
- source_ref row 19: `espn_scoreboard wnba_nba path=wnba event=401918299
  completed=true detail='Final' home=NY:83 away=ATL:85 fetched_at=2026-10-10T02:30:29Z`,
  settled_at 02:30:31Z ✓ (claim's 02:30:29Z = the fetch instant).
- EV/p recovery: DECISION row 14 `ev_net_by_leg.AWAY` = 0.2717682648202573,
  `p_frozen.AWAY` = 0.552037720008657, `odds_frozen.AWAY` = 2.34; ops incident
  `CADENCE_DECIDE_OK` ts_utc `2026-10-08T17:24:01Z` journaled BET_PAPER 401918299
  reason "EV_net 0.271768 >= 0.05 on AWAY; fixed stake law" ✓. Own algebra:
  implied fee c = p·d − 1 − EV_net = 0.02 EXACTLY for both legs (AWAY and
  HOME; HOME: 0.44796228×1.61 − 1 − 0.02 = −0.298780729… matches). Recovering
  p from EV: (EV+1+0.02)/2.34 = 0.5520377200086570 — bit-identical to
  p_frozen/FORECAST p. What is recoverable: the row identity is
  **EV_net = p·d − 1 − 0.02** (c = 0.02 frozen fee law); the dispatch's
  alternative parametrization d_eff = 1/(a+f) does NOT reproduce the row
  (gives p·d_eff−1 = 0.234016 ≠ 0.271768) — stated as instructed.
- quote==frozen odds equality verified (MARKET_QUOTE row 13 odds == DECISION
  odds_frozen == {AWAY 2.34, HOME 1.61}).

## Item 6 — Dashboard /api/state: PASS

`curl http://127.0.0.1:8791/api/state` (read-only), `generated_at_utc
2026-10-10T03:57:15Z` (fresh, seconds before fetch parse): `mode REAL`,
`chain.ok true` errors [], rows_count 19, genesis 2026-10-07T11:09:54Z,
`wallet.equity_cents 101470`, peak 101470, `open_count 1` (401918300 BET_PAPER
AWAY, 500¢ exposure), `settled_count 3`, total_pnl 1470 = 395+405+670,
outcomes WIN 3 / LOSE 0. Reconciles exactly with the ledger truth recomputed
in Item 5.

## Item 7 — PM re-probe (verifier's own re-run): PASS — ZERO DELTA

Controller probe report `probe_report_20261010T034402Z.json`: asof
2026-10-10T03:44:02Z, n_events_scanned 2100, NBA 82 / WNBA 15 / SOCCER 2 /
WSL 147 fixtures, all with_market 0, with_quote 0, bet_paper_possible 0.
Verifier re-ran the same live_probe.py (read-only public Gamma GETs, $0):
`probe_report_V10_VERIFY_PROBE_20261010T035757Z.json`, asof 03:57:57Z,
n_events_scanned 2100 — identical counts, all four leagues 0 markets, WSL
fixtures 147. **No listing appeared; no delta to report.** Total 246 fixtures
all NOT_RUN_NO_MARKET.

## Item 8 — Isolation: PASS

- ERRATUM_EXEC_6 commit 14871d76: `git show --stat` = exactly 1 file,
  `…/SPORTS-PAPERTRADE-EXEC-V1/ERRATUM_EXEC_6.md`, 61 insertions, 0 deletions. ✓
- CAS save touched only the spt-exec row: Item-3 structured diff (0c110b73 →
  105318e6) — 134/135 rows byte-equal. ✓
- No controller ledger writes: ledger mtime = 09:30:31 +07 == 2026-10-10
  02:30:31Z == the settlement row's settled_at_utc; 19 rows before and after
  the R10 work (03:45–03:46Z); the verifier's own probe asserted the live
  ledger's non-interference. ✓
- Dashboard live (mode REAL); /api/state chain.ok true; the state payload is
  re-derived from disk per tick by ops_service (generated_at moves per
  request) — shas/content movement is service cadence, no manual edit
  indicated (informational).

---

## Coherence for the next owner decision

- PROVEN: `GO SPORTS PAPERTRADE EXEC V1 RUN ALL` was typed 2026-10-07T11:08:47Z,
  consumed (journal 11:08:47Z + 11:19:08Z, commit b250bfb1), and is spent under
  P-8. It cannot be re-typed; nothing in any journal attempts to.
- COHERENT: the program row's live gate is the NEW phrase
  `GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER`, REGISTERED_NOT_CONSUMED
  with the consumed history inline; typing it activates the frozen source
  switch for leagues READY at that moment (today: none — READY_LEAGUES_NONE,
  0/246 markets, re-confirmed independently).
- INCOHERENCE REMAINING (F1): the CUTOVER-PREP row still advertises the spent
  RUN ALL phrase as its unconsumed "shared gate" (row field + phase text +
  ACTIVE_CYCLES.json projection). An owner reading that row could be misled
  into typing RUN ALL — a dead phrase. Correct the sibling row (same CAS +
  erratum mechanism) with, or before, the next owner decision.

## Evidence paths

- Root journal: /Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.events.jsonl (lines 1757–1765, 1818–1821, 1966–1994)
- Root registry: /Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json (diffed 0c110b73 → 105318e6)
- GO token: research/control/SPORTS-PAPERTRADE-EXEC-V1/GO_TOKEN.json (worktree)
- Errata: ERRATUM_EXEC_5_LIVE_SERVICE.md §D-4, ERRATUM_EXEC_6.md (worktree)
- Ledger: /Users/hoangminhlong/.my-quantitative-data/sports-papertrade-exec-v1/ledger/paper_ledger.jsonl (19 rows, head 53449ef5…)
- Ops: /Users/hoangminhlong/.my-quantitative-data/sports-papertrade-exec-v1/ops/state/incidents.jsonl (CADENCE_DECIDE_OK 2026-10-08T17:24:01Z)
- Probes: /Users/hoangminhlong/.my-quantitative-data/sports-polymarket-cutover-prep-v1/live/probe_report_20261010T034402Z.json and probe_report_V10_VERIFY_PROBE_20261010T035757Z.json
- Pinned hash scheme: .worktrees/sports-papertrade-v1/integration/research/papertrade/ledger.py (sha 66921271… == pins.json)
