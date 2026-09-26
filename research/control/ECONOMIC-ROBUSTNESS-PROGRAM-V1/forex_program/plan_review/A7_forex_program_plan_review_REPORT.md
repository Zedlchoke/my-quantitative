# A7 PLAN AUDIT — ERP-FOREX-PROGRAM-V1 (master charter) + ERP1-TRACKA-COHORT-2 (child) + LESSON_TO_GATE_MATRIX

**Verdict: `AUTHORIZED_WITH_FINDINGS`** — 0 CRITICAL / 3 HIGH / 2 MEDIUM / 5 LOW / 2 INFO.
The plan set is structurally sound: nothing registers, nothing consumes a GO,
no exposed window is re-opened, the replication definition is airtight on its
own terms, and every threshold spot-checked against the cohort-1 source text
matches. The three HIGH findings are all one-line-class fixes (a dangling
ratification path, a packet-blindness self-contradiction, an unbounded
transfer-surface look) that MUST be closed before the owner types GO-1 — see
"Conditions binding on GO-1" at the end.

- Auditor: A7 independent plan-audit lane, fresh context, READ-ONLY on the repo
  except this report + the companion handoff JSON. No strategy/PnL computation,
  no worker/registry/ledger/S1 touch, no commit.
- Measured base: repo root `/Users/hoangminhlong/my-quantitative`, branch
  `main` @ `73ae43e1d04ad6f1f41d3abe1c3a17734da753b3` (`git rev-parse HEAD`,
  2026-09-26). Drafts `plans/PLAN_erp_forex_program_v1.md`,
  `plans/PLAN_erp1_tracka_cohort_2.md`, and
  `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/forex_program/` are
  **untracked** working-tree files (git status `??`); nothing registered.
- Objects under review: master charter (192 lines), child cohort-2 plan
  (331 lines), lesson-to-gate matrix (53 lines), audited against: umbrella
  `PLAN_economic_robustness_program_v1.md` (743 lines), cohort-1 precedent plan
  (826 lines), cohort-1 worktree evidence (`SCORED_REPORT.md`,
  `audits/A7_terminal_REPORT.md`), `INCIDENT_RANGEFADE_PIT_SEAM_2026-09-25.md`,
  `research/wayfinder/LESSONS.md`, `FAMILY_FAILURES.jsonl`,
  `plans/CYCLE_REGISTRY.json`.
- Live re-measure this session: `researchctl cycle list` →
  `ECONOMIC-ROBUSTNESS-PROGRAM-V1 ACTIVE_LIGHT 0/0`, `ERP1-TRACKA-COHORT-1
  TERMINAL 0/24`, **no** `ERP-FOREX-PROGRAM-V1` and **no**
  `ERP1-TRACKA-COHORT-2` row; `cycle doctor --json` → only the
  accepted-historical archived-worktree class (STATE_MISSING LOW ×3,
  WORKTREE_MISSING MEDIUM-class on TERMINAL cycles with archived worktrees —
  umbrella P0-3); `locks inspect` → `FREE_PROVEN`.
- The owner instruction (continue cohorts until ≥1 identity reaches
  `BACKTEST_CANDIDATE_REPLICATED`, else `NO_CANDIDATE`, preserve OOS, never
  lower standards) is carried verbatim as program intent (master:13-17) and is
  correctly treated as a goal, NOT as a GO (master:3-5 "không tiêu GO nào";
  child:3-9 "Registration chỉ qua `researchctl cycle register` sau owner GO").

---

## Section A — Authority / boundary

**CONFIRMED:**
- Registry authority intact: no new cycle registered by the drafts;
  umbrella ACTIVE_LIGHT (`CYCLE_REGISTRY.json:2049-2077`), cohort-1 TERMINAL
  CLOSED_REJECT_ALL (`:2078-2107`); drafts claim exactly the DRAFT status
  (master:3 `DRAFT_FOR_OWNER_DECISION — NOT REGISTERED, NOT EXECUTED`; child:3
  `DRAFT_FOR_OWNER_GO — NOT REGISTERED, NOT EXECUTED`).
- Boundary declarations complete on both drafts: no worker/shadow touch
  (child:36-37 names FX-RANGEFADE-2M-SHADOW-V1 and PROSPECTIVE-SHADOW-V1 as
  read-only citation; child:90-91 explicitly disclaims the PSV1 engine-fix arc
  as "không phải quyền của cycle này"); S1 SEALED (master:28; child:33);
  orders NONE (master:29; child:34); no download except the GO-1-gated bounded
  probe (child:4-5); registration only via `researchctl cycle register` after
  owner GO (child:8-9); forbidden-list includes registry edits outside
  researchctl and merge/push (child:48-53).
- GO phrases are defined fresh at their own gates with explicit preconditions
  and a hard stop after GO-1 (child:38-47: GO-1 "...VÀ DỪNG"; GO-2 "chỉ sau A7
  prelaunch PASS"; GO-3 "chỉ cho identity qua đủ dev gates + R5 freeze...
  không có identity nào qua thì GO-3 không tồn tại"). P-8 intent law restated:
  "GO gõ trước gate = intent... Early-typed GO không bao giờ thành quyền thường
  trực" (master:181). Master consumes no GO and scores nothing, budget 0/0
  (master:21-23).
- No weakening of umbrella or cohort-1 law found anywhere in the drafts; the
  child repeatedly tightens (e.g., F-1a class adjudication before rho;
  ancestry gate extended to cohort-1's own shadows, child:117-121). Drafting
  snapshot sha in child:88-89 (`73ae43e1`) equals the measured root HEAD.

**Findings:**

- **F1 [HIGH] — The master charter's ratification mechanism points at a file
  that does not exist.** master:9-11: "Owner phê chuẩn bản charter này bằng
  quyết định ghi vào `forex_program/OWNER_PACKET_cohort2_2026-09-26.md`" — but
  `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/forex_program/` contains
  ONLY `LESSON_TO_GATE_MATRIX.md` (measured 2026-09-26). child:311-313 also
  routes the reader to "(xem OWNER_PACKET)". As written, GO-1 would ratify a
  charter whose approval record has no home; the owner's D2-1..D2-4 decisions
  (child:316-321) would land nowhere durable. Fix before GO-1: create the
  OWNER_PACKET (or amend both drafts to cite the real decision-record path),
  containing this A7 verdict + findings disposition and the D2 decision list.
- **F2 [HIGH] — The child's packet-blindness instruction is self-contradictory
  and could inject R-ORIG's winning numbers into blind proposer packets.**
  child:114-116: "proposer packets chứa §3 disclosure + §4 candidate text + §5
  source table + KHÔNG PnL/PF/win-rate/trade-count...". But §3.1
  (child:103-107) carries outcome numbers: "M1 KILL_PIT_SEAM (S=2884.1/4348.6
  pips...)", "PIT-clean law PF 1.033/1.051", and — decisive — R-ORIG passing
  all 8 gates at +3207/+5030 pips (the lookahead arm's numbers). Cohort-1's
  inherited law (child:100 "Kế thừa nguyên văn §3 cohort-1") says "numbers NOT
  cited in proposer packets" (cohort-1:108-110), so the laws conflict on their
  face; a literal packet build from §3 hands blind proposers the exact
  leak-shaped incentive the program exists to suppress, tainting the cohort.
  Fix: one line in child §3.4 — "§3 disclosure enters packets in LABEL-ONLY
  form, all PnL/PF/pip numbers elided (cohort-1 §3.2 law)"; A7 prelaunch
  verifies packet bytes against the blindness law.
- **F3 [LOW] — The master layer lacks its own explicit non-weakening pin, and
  the child's authority order seats the (unregistered) master ABOVE the
  umbrella.** child:83-85: "owner instruction > child plan (khi registered) >
  master program plan > umbrella > CLAUDE.md + handbook". The master inherits
  umbrella law wholesale ("kế thừa toàn bộ luật umbrella §§1–11", master:7-8),
  which implicitly forbids weakening, but there is no sentence "the master plan
  may never be weaker than the umbrella; amendments are owner decisions". A
  future master amendment could then legally outrank umbrella law in child
  reads. Fix: one pin sentence in master §0/§2 and mirror in child §2.
- **F4 [INFO] — Master requires an A7 check between dev-gate pass and GO-3;
  the child's A7 arc does not restate it.** master:177-180: "GO-2 scored dev →
  nếu identity qua đủ dev gates: A7 kiểm → GO-3"; child:309-315 lists A7
  prelaunch (pre-GO-2) and terminal only. Silence is not weakening (master law
  survives per child §2), but restate in child §11 to remove the ambiguity.

## Section B — Replication definition (master §4, R0–R6)

**CONFIRMED:**
- The three-limb structure is genuinely conjunctive: R5 requires "(i) impl độc
  lập... (ii) thời gian chưa dùng để chọn... (iii) bề mặt độc lập... **Thiếu
  một limb ⇒ KHÔNG được viết 'replicated'**" (master:117-123); no single limb
  suffices and the paper-tier claim-void rule for 1/3-limb claims is in the
  matrix (matrix:18 FAIL column). R5(i) bans importing the implementer's
  engine; R5(ii) is per-identity window novelty; R5(iii) offers pair OR source.
- Paper-tier bound and wording bans survive end-to-end: master:128-132
  (labels `SINGLE_SOURCE_PANEL`, `PAPER_TIER`,
  `FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK`; mandatory spoken disclaimer
  "KHÔNG phải strategy chắc chắn kiếm tiền"; no live/shadow without separate
  GO); child §6 inherits cohort-1 §6 wording bans verbatim-by-reference
  (child:191-201 vs cohort-1:289-362).
- R5(iii) USDCHF design preserves one-look semantics **per identity**: one
  frozen evaluation pass over the full merged window with identity + criteria
  frozen from the home pair (master:120-122; child:176-180, 261-264), inside
  GO-3, ledgered `TRANSFER_PASS_ONE` (child:304-306). R4 sealed OOS one-look
  with membership sha256 before pass and dead arms excluded (master:113-115;
  child:255-257). R0 freeze-before-outcome, R1 PIT+authority, R2 dev gates
  (floors ≥100 RT + ≥6 months; power ≥236 RT or bootstrap CI excluding 1.0),
  R3 control/inverted/beta bands (all match cohort-1 §9.4: 0.5× placebo band;
  inverted strictly below incl. OOS; beta margin 0.5× ⇔ anchor ≥ 2× baseline),
  R6 A7 independent PASS — all present and consistent with the child §9
  thresholds (spot-checks in Section E).

**Findings:**

- **F5 [HIGH] — The USDCHF transfer window has no program-level one-look
  ceiling and is not registered into the sealed map; after its first pass, any
  further transfer pass violates the program's own L5 void law.** The
  one-window-one-identity-one-look rule is written for the home-pair holdout:
  "Nếu home pair của một identity là pair mà cửa sổ 2026-H1 đã bị tiêu bởi
  identity khác ⇒ identity đó không được dùng cửa sổ đó (một cửa sổ - một
  identity - một look; sổ đăng ký sealed map do A1 giữ)" (child:258-260). The
  USDCHF transfer pass, by contrast, is scoped per identity only ("MỘT
  evaluation pass trên toàn window USDCHF", child:261-263; master:120-122).
  With ≤3 identities per cohort and the program explicitly looping cohorts
  until one identity replicates (master:13-17, §6), the same USDCHF
  2021-01..2026-06 window could absorb one look per surviving identity, per
  cohort, forever — and from the second look on, each pass cites an
  already-exposed window as replication evidence, which matrix L5 voids:
  "Bất kỳ artifact nào trích cửa sổ đã lộ làm evidence mới/OOS/replication ⇒
  verdict void" (matrix:21). This is the exact cross-identity/cross-cohort
  shopping vector the audit was asked to hunt. Fix (binding): USDCHF full
  window = ONE program-level look — the first identity reaching GO-3 consumes
  it; later identities need a different outcome-free pair (or an
  owner-unblocked independent source for R5(iii)-source); every transfer pass
  is registered in A1's sealed map and the matrix exposure table is refreshed
  at the two-half close (child §11 already refreshes the map; make transfer
  windows explicitly in scope).
- **F6 [MEDIUM] — The sealed-OOS pass membership list (companions) is not
  restated in child §9.1, leaving a legal-looking path to a second look.**
  Cohort-1 §9.1 (one-look law, P2 extension) requires the causal control,
  inverted control and baseline books to be computed IN THE SAME single pass,
  "never as independent consumers", precisely so "'inverted strictly below
  anchor' must be evaluable on the holdout too, else a holdout-only inversion
  passes unchecked" (cohort-1:523-537). Master R3 carries the requirement
  ("inverted strictly below (cả trên OOS)", master:111-113), but the child's
  §9.2–9.4 verbatim inheritance excludes §9.1 (child §9.1 is new text,
  child:250-260) and does not list the companions. A literal child-only
  reading could freeze membership = anchor arms only, then discover R3's OOS
  inversion test cannot be evaluated without a SECOND holdout pass — burning
  the program's only sealed asset twice. Fix: one line in child §9.1 (or an
  explicit "cohort-1 §9.1 inherited verbatim" clause) naming anchor + causal +
  inverted + baseline companions as members of the single pass.

## Section C — Outcome-exposure integrity

**CONFIRMED (map vs measured facts):**
- EURUSD/GBPUSD/USDJPY 2021-01..2026-06 OUTCOME-EXPOSED — matches cohort-1 §3.3
  (cohort-1:125-129) and the ancestry registry entries (FX-MAJORS/ V1/V2 rows
  in `CYCLE_REGISTRY.json`).
- AUDUSD/USDCAD dev 2021-01..2025-12-31 OUTCOME-EXPOSED for the range-fade
  class — matches cohort-1 SCORED_REPORT (12 scored dev cells across both
  pairs, worktree `SCORED_REPORT.md:6-104`) and A7 terminal §A/§G.
- AUDUSD/USDCAD holdout 2026-01-01..2026-06-30 SEALED-UNREAD — matches A7
  terminal condition C-3 ("the holdout windows... remain UNREAD",
  `audits/A7_terminal_REPORT.md:309-311`) and the ledger bookkeeping rows
  `HOLDOUT_UNREAD_CONSUMED_BY_NONE` (`SCORED_REPORT.md:52,102`).
- USDCHF OUTCOME-FREE — matches cohort-1: USDCHF was the owner-amendment-only
  spare, never downloaded, never searched (cohort-1:236-239, 713-716).
- The three exposure statements (master §2 table master:66-73; matrix map
  matrix:36-45; child §3 + §5.1) are mutually consistent, and the matrix is
  declared "binding input for every child plan; refreshed at each intake"
  (matrix:36) with the child adopting it as "phụ lục binding" (child:108-112).
- Exposed-window citation ban present in all three artifacts (matrix:21 FAIL;
  child forbidden list:52 "re-score cửa sổ đã lộ làm evidence mới"; master §2
  "Không bao giờ evidence mới/OOS" column, master §1.2).

**Findings:**

- **F7 [LOW] — No defined per-identity closure when the sealed map has no
  window left for an identity's home pair.** Child §5.2 allows the council to
  propose the same home pair for two mechanisms ("mỗi cơ chế 1 home pair do
  council đề xuất", child:172-174); if both survive dev, only one can consume
  the pair's 2026-H1 window (child §9.1 rule). The second identity is left in
  limbo: R4 cannot run, and master §7(c) "hết OOS sạch" is a program-level
  stop, not a per-identity label. Fix: preregister an honest per-identity
  label (e.g., `NOT_RUN_NO_CLEAN_OOS` / `CANDIDATE_PENDING_*` ceiling without
  the program-goal label) so the identity cannot quietly borrow another
  window.

## Section D — Lesson-to-gate coverage (five owner-mandated lessons)

**CONFIRMED — each mandated lesson has concrete evidence, a prevention gate,
and a FAIL condition (matrix:17-21), mapped into the child's binding battery:**
- **L1 whole-day-amplitude PIT seam + third-law daemon:** evidence = incident
  + M-5 replay (R-ORIG changes output on 936/1298 ≈ 72% truncated replays,
  verified in worktree `FALSIFIER_REPORT.md:43` and LESSONS P-18(ERP1):911-925)
  + seam S=2884.1/4348.6 vs thresholds 20.0/24.0 (`SCORED_REPORT.md:25-29,75-79`).
  Gate = F-PIT-1/F-2 battery standing pre-PnL, now extended with future-data
  mutation (child F-2(vi)) and byte-identical panel-truncation replay
  (child F-2(v)), same-day statistic audit (F-2(vii)), EVIDENCED/ASSERTED/
  UNEVIDENCED table (F-2(viii), P-1 asserted ⇒ NOT_RUN). FAIL = KILL_PIT_SEAM
  + artifact void. Third-law daemon handled by F-2(iii) with honest N/A
  scoping (no daemon runs cohort-2 signals).
- **L2 same-code parity reproduces bugs:** evidence = P-4 + A7 cohort-1 16/16
  exact recompute of a leak-carrying engine (`A7_terminal_REPORT.md:22-24`).
  Gate = R5(i) independent implementation + M-1 shift-equivalence per
  mechanism. FAIL = any "replicated" claim on 1/3 limbs void.
- **L3 PIT-clean dies at ×1.5 while lookahead wins = leak:** evidence =
  R-ANCHOR +323.3/−652.35 and +681.0/−509.4 at k=1.0/1.5 vs R-ORIG +2232.5/
  +3838.9 @1.5 (`SCORED_REPORT.md:21,44,117`). Gate = F-5 declared-band
  ceiling pre-PnL (conditional break-bar spread; M3 died on exactly this law)
  + G4 net>0 @1.5 + gross/declared/measured split. FAIL = ceiling negative ⇒
  veto; net ≤0 @1.5 ⇒ G4 FAIL terminal.
- **L4 baseline/beta/clock-placebo/inverted/measured costs:** evidence =
  SHORT_ALWAYS +314.0 > C3 +274.0 (umbrella §4.1); clock-shadow out-earn
  precedents; KILL_INVERSION fired on fold-residue in cohort-1
  (`SCORED_REPORT.md:33,83`). Gate = F-3 clock-placebo with Q-11 non-vacuity
  predicates + mode-sham + per-hour tables + DST splits + Q-7 clock-only
  shadow for event/calendar mechanisms; F-4 per-pair frozen beta directions
  (USDCHF drift-sign rule carried, child:236-238); inverted companion on
  holdout (via R3, see F6); P-20 distinct-state-source control law. FAIL =
  the KILL_CONTROL/KILL_BETA/KILL_INVERSION set with exact bands.
- **L5 outcome-exposed pairs never fresh OOS:** evidence = 12-family census +
  consumed holdouts + cohort-1 dev scoring + UNREAD holdout (all verified
  Section C). Gate = binding exposure map + one-look law + membership freeze +
  blind packets. FAIL = verdict void / ancestry violation terminal.
- **F-1a class adjudication BEFORE rho is correct per cohort-1 A.3:** the
  precedent's binding instruction is exactly "a future cohort's D2 must
  adjudicate the class question BEFORE any rho fixture" (cohort-1:786-790);
  child §8 F-1a + §4 C2 implement it verbatim (child:137-141, 216-220) —
  class dies ⇒ candidate dies without spending a fixture.

**Findings:**

- **F8 [MEDIUM] — The matrix's L1 gate scope is narrower than the child's F-2
  scope, and the matrix claims to be binding on every future child.** Matrix
  L1 gates the PIT battery on "MỌI cơ chế **có biến trạng thái theo
  ngày/biên ngày**" (matrix:17), while child F-2 applies the full battery —
  panel-truncation (v), future-mutation (vi) — to "mỗi signal code"
  (child:220-231). A future cohort drafting from the matrix alone could
  legally skip truncation/mutation fixtures for a signal without day-boundary
  state — the exact class of leak (e.g., an hour-boundary or rolling-window
  leak) that L1's scoping wording does not name. Fix: matrix L1 gate text →
  "every new signal code" (the child is already stricter; align the binding
  input).
- **F9 [LOW] — No ±1-bar fill-delay disclosure fixture for the H1 clock.**
  Q-4's own lesson scopes the delay-pair battery to sub-hour cadence
  (LESSONS.md:414-423), and master §3 matches ("delay-pair Q-4 cho sub-hour",
  master:85-88) — so nothing mandatory is violated for an all-H1 cohort. But
  cohort-1's A7 terminal disclosed the ghost-trip mechanic (a prior-day
  last-in-session-bar signal filling at the next day's first bar; 17/11
  anchor fills; `A7_terminal_REPORT.md:288-291`) — precisely the class of
  fill-timing seam a delay-0/delay-1 disclosure quantifies cheaply. Fix
  (recommended, not blocking): add a ±1-bar fill-delay non-vacuity fixture or
  record N/A-with-reason per mechanism at freeze.

## Section E — Cohort-2 design coherence

**CONFIRMED:**
- **≤3 mechanisms hard law:** child:156-158 "Cơ chế thứ 4 bị cấm"; master §3
  item 2; excess proposals parked as `NOT_FROZEN_SLATE_FULL` future
  candidates (child:156-159).
- **Slate legality:** P1/P2 future-cohort candidates consumed no slot, no
  cell, no look — cohort-1 §A.3: "None consumed a slot, a cell, or a look"
  (cohort-1:780-795); cohort-1 scored exactly the M1 arms (12 cells;
  `SCORED_REPORT.md:121`, A7 terminal §D). Child Appendix A cites this
  provenance honestly (child:324-330) and the child re-vets each candidate
  through the full 10-field + 6-question + novelty law (child:125-156).
- **Budget 24-cell cap and gate order:** GO-1 (register+council+falsifiers+
  freeze, STOP) → A7 prelaunch → GO-2 (scored dev) → dev-gate pass → GO-3
  (sealed OOS + replication, one look each) → A7 terminal → two-half close;
  falsification battery completes before the first PnL-bearing cell
  (child:246-247 ordering law); "audit before PnL" and "sealed OOS one-look
  after own GO" both hold in the chain (master §8; child §0, §10.1).
- **Kill-law inheritance spot-checks vs cohort-1 source text — ALL MATCH:**
  G2 PF ≥1.20 (cohort-1:541 / child:267); G3 ≥4/6 folds net>0 (cohort-1:541 /
  child:267); G5 ≥100 closed RT AND ≥6 months (cohort-1:542-543 / child:267);
  G8 top session-hour share ≤50% (cohort-1:545 / child:268); seam limbs
  10×/3×(4-of-6 folds)/1× c_rt (cohort-1:594-601 / child:283-285); limb-iii
  minimum-N 20 fail-closed (cohort-1:651-652 / child:284); power gate ≥236 RT
  or preregistered bootstrap CI excluding 1.0, `NOT_POWERED_CANDIDATE` as
  ceiling (cohort-1:558-565 / child:277-278); holdout net ≤0 terminal with
  the no-pair/no-threshold rescue ban (cohort-1:570-571 / child:276-277);
  TIME-STOP freeze+60 days (cohort-1:575-577 / child:278-279).
- **REJECT_ALL / NO_CANDIDATE first-class:** master:42 ("kết quả hợp lệ và
  được kỳ vọng là kết quả modal"), master §7 stop conditions; child:77-78.

**Findings:**

- **F10 [LOW] — Budget arithmetic: the stated composition computes 18, not
  24.** child:28-29 and child:297-299: "24 scored cells MAX (≤3 cơ chế × 6
  arms × 1 home pair)". 3×6×1 = 18; the 24 cap is inherited vestigially from
  cohort-1 (whose Task-1 justified 12 + Task-2 12). The cap is an upper bound
  so no overrun is possible, but the 6-cell slack invites a future reading of
  "room for a fourth arm-class" even though the fourth mechanism is
  forbidden. Fix at freeze: state the cap as 18 (=3×6×1) or document what the
  extra 6 are for.
- **F11 [LOW] — PBO pre-declaration is likely wrong for a 3-mechanism
  cohort.** child:306-307: "PBO NOT_RUN trừ khi ≥8 configs (sẽ không có —
  6-arm classes)". Cohort-1's <8 reasoning held because arms shared configs
  across pairs (A7 terminal: "12 cells but < 8 distinct CONFIG classes",
  `A7_terminal_REPORT.md:171-172`). With 3 distinct mechanisms × 6 arms, the
  distinct config class count plausibly reaches 18 ≥ 8 — the law's own
  trigger (umbrella §5.14, umbrella:600-601). Fix at freeze: count distinct
  config classes and compute PBO if ≥8; do not pre-declare NOT_RUN.

## Section F — Data / cost law

**CONFIRMED:**
- **Five binding conditions** inherited from cohort-1 §6 (which itself carries
  the critic's conditions verbatim, cohort-1:289-362; umbrella §5.4 list,
  umbrella:395-410) by explicit verbatim-by-reference with a faithful binding
  summary (child:191-201): verdict class bounded paper tier; structural-zero
  financing by executor fixture; per-session measured spread at the FILL BAR
  ×k∈{1.0,1.5,2.0}, never global p50; adverse selection declared-unmeasurable
  with the taker wording bans ("cấm mọi từ 'capture/earn the spread', 'fill
  at mid'"); marks-vs-fills seam disclosed. Unfundable-arm veto retained
  (child:199-200; sub-M1 sequencing ⇒ veto — C3 explicitly adjudicated on the
  H1 clock, child:146-147).
- **SINGLE_SOURCE_PANEL posture:** master §2 (Dukascopy only authority;
  independent sources 0 bytes until owner unblock, master:59-64); child §5.3
  (BLOCKED; label retained until an unblocked source is actually used for
  R5(iii), child:184-189). No silent unblock anywhere: "không mở nguồn mới
  trong cycle này trừ owner amendment" (child:150-152).
- **USDCHF download bounded:** owner amendment (D2-2) precedes it; data gate
  cohort-1 §5.2 in full; "~44MB+probe, heavy lock, yield" (child:176-179);
  heavy-job law under machine-wide lock (child:92-93). Measured this session:
  heavy lock `FREE_PROVEN`.
- **Measured-cost / Q-8 doctrine:** "Mọi hằng số theo Q-8: measured hoặc chết
  conservative" (child:200-201); census-schema hardening and charging
  semantics inherited verbatim-by-reference (child §6 vs cohort-1:314-335).
- G0 reachability probe law for any new domain retained via matrix L11
  (matrix:32) and master §2 (L-FXFF-1 filter disclosure, master:63-64).

No findings in Section F beyond the cross-cutting ones already filed (F5
affects transfer-pass exposure accounting; F10/F11 affect ledger statistics).

## Section G — Consistency risks & shopping vectors

**CONFIRMED (resistance against shopping):**
- **Pair swap:** home slate owner-fixed at GO-1 (child:170-174; D2-2,
  child:317-318); holdout kill forbids pair/threshold re-tries ("KHÔNG đổi
  pair/ngưỡng để thử lại", child:276-277); NZDUSD/crosses exclusions carried
  with reasons (child:181-183).
- **Mechanism rename / re-tune:** novelty law cohort-1 §7.4 inherited
  verbatim (child:154-156); F-1a class adjudication; M2's V-4_BLEND precedent
  on record (cohort-1:729-738); lo_q/hi_q re-tune explicitly forbidden
  (child:48-49).
- **Window substitution:** "không substitute fold sau khi thấy PnL"
  (child:253-254); fold contract frozen; no mid-cohort replacement
  (child:278).
- **Control rebuild abuse:** matrix L4 FAIL — "null không move ⇒ control
  REBUILT trước khi score, không phải PASS" (matrix:20); P-20 distinct
  state-source law cited; controls carry gross/net decomposition (cohort-1
  M3 condition, inherited via child §6/§9).
- **Ceilings preserved:** `NOT_POWERED_CANDIDATE` remains the sub-power
  ceiling (child:278; cohort-1:561-565); PROMOTE output label stays
  `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION` via R-chain paper-tier bound;
  `BACKTEST_CANDIDATE_REPLICATED` is a program-goal label bounded paper tier
  (master:23, 130-132; child:22-24).
- **Master vs child contradiction scan:** master §6 cohort list = child §4
  slate (C1/C2/C3 naming and the C2 class-adjudication precondition match);
  master §2 exposure table = matrix = child §5; master §8 budget note =
  child §10.2; dev/holdout window dates identical; gate chains identical.
  Residual inconsistencies are filed as F1/F3/F4/F5/F6/F10/F11.
- **F12 [INFO] — Registry hygiene context (not a defect of the drafts):**
  cohort-1's post-close registry row still shows `budget.used: 0` of 24
  (`CYCLE_REGISTRY.json:2087-2090`) while A7 terminal condition C-2 and the
  audit body certified 12 cells consumed (`A7_terminal_REPORT.md:160-168,
  305-308`); the P-9 hypothesis ledger remains the cross-cycle authority, and
  child §2 Phase-0 correctly mandates re-measurement at intake. Cohort-2's
  own budget accounting must anchor to its ledger, not to any inherited
  registry budget field. Also noted: drafting snapshot `73ae43e1` matches the
  measured root HEAD exactly (child:88-89).

---

## Conditions binding on GO-1

The owner must NOT type GO-1 until each condition below is closed in the plan
text / packet (all are one-line-to-one-file fixes; none requires re-running
anything):

1. **BC-1 (F1, HIGH):** Create
   `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/forex_program/OWNER_PACKET_cohort2_2026-09-26.md`
   — or amend both drafts to cite the actual owner decision-record path. The
   packet must carry: this A7 verdict + finding dispositions, the D2-1..D2-4
   decision list, and the explicit statement that owner approval = charter
   ratification + registration gate authority only (not a scored GO).
2. **BC-2 (F2, HIGH):** Amend child §3.4 to state that §3 disclosure enters
   proposer packets in LABEL-ONLY form with ALL PnL/PF/pip numbers elided
   (cohort-1 §3.2 law); A7 prelaunch must verify packet bytes against this
   law before any council dispatch.
3. **BC-3 (F5, HIGH):** Bind the transfer surface into the sealed-map regime:
   USDCHF 2021-01..2026-06 = ONE program-level look, consumed by the first
   identity reaching GO-3; any later identity (this cohort or future cohorts)
   requires a different outcome-free pair or an owner-unblocked independent
   source; every transfer pass is recorded in A1's sealed map and the matrix
   exposure table is refreshed accordingly at each two-half close.
4. **BC-4 (F6, MEDIUM):** Restate in child §9.1 the single-pass membership
   list — anchor arms + causal control + inverted control + baseline books,
   computed in the SAME one pass (cohort-1 §9.1 P2-extension) — so R3's
   OOS inversion test never motivates a second holdout look.
5. **BC-5 (F8, MEDIUM):** Align matrix L1's gate scope to "every new signal
   code" (child F-2 wording governs), so the binding input cannot be read
   narrower than the child battery.
6. **BC-6 (F10/F11, LOW):** At freeze: state the scored-cell cap as 18
   (=3×6×1) or document the residual 6; count distinct config classes and
   compute PBO if ≥8 instead of pre-declaring NOT_RUN.
7. **BC-7 (owner action, ties to D2-2):** The USDCHF slate amendment must be
   typed as its own explicit owner decision at the GO-1 gate; GO-1 alone must
   not be read as authorizing the USDCHF download — amendment first, then the
   bounded (~44MB, heavy-lock, yielding) data gate.

Non-blocking recorded items: F3 (master non-weakening pin), F4 (restate
pre-GO-3 A7 check in child §11), F7 (per-identity no-clean-window close
label), F9 (±1-bar H1 fill-delay fixture or reasoned N/A), F12 (registry
budget field context).

**Final statement:** with BC-1..BC-5 applied, this plan set is fit for the
owner to type GO-1 at its own gate. Nothing in this audit authorizes,
registers, scores, downloads, or consumes anything.
