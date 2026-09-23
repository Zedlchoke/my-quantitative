# PLAN STOCKS-AMIHUD-IDENTITY-EXECUTION-RETEST-V1 — identity/execution remediation retest

> Status: `PLANNED_NOT_STARTED` (2026-09-23). Authority: explicit owner
> directive 2026-09-23 "OWNER DIRECTIVE — STOCKS-AMIHUD-IDENTITY-
> EXECUTION-RETEST-V1" (Vietnamese, verbatim anchors preserved in §0a).
> Class: **OUTCOME_OBSERVED_RETROSPECTIVE_RETEST** — this is a
> data/implementation remediation AFTER the predecessor cycle's scored
> outcome was observed. Whatever the numbers say, they are NEVER called
> untouched OOS, never self-promoted, and carry the retrospective label on
> every artifact. A P0 close with zero scored cells is a valid result.

## 0. Cycle identity

```text
cycle_id     STOCKS-AMIHUD-RETEST-V1 (owner name: STOCKS-AMIHUD-
             IDENTITY-EXECUTION-RETEST-V1)
predecessor  STOCKS-AMIHUD-V1 (TERMINAL; its 3 observed cells, SHAs and
             verdicts are immutable history — never edited, never deleted)
asset        stocks
plan         plans/PLAN_stocks_amihud_retest_v1.md
branch       orca/stocks-amihud-retest-v1-integration
worktree     /Users/hoangminhlong/my-quantitative/.worktrees/stocks-amihud-retest-v1/integration
budget       3 scored cells max (same three arms as the predecessor:
             RETEST-ILLIQ21 / RETEST-ILLIQ63 / RETEST-REVERSAL5)
folds        UNCHANGED: F1=CY2019, F2=CY2020 (2020-03 inside F2 alone),
             F3=CY2021–22 (annual split 2021/2022 always reported)
calendar     UNCHANGED: 21-session grid, decision at t close, t+1 fills
go_phrase    GO STOCKS AMIHUD RETEST V1 SCORED EXECUTION
             (typed ONLY if the standing-directive adjudication in §11
             comes back "interactive GO still required"; never typed by
             an agent; never fabricated; never laundered as diagnostic)
S1           SEALED_UNTOUCHED
orders       NONE — no paper/testnet/live; no purchases; EODHD /eod under
             the existing entitlement only; key never echoed
```

## 0a. Owner directive anchors (verbatim intent, frozen)

- "tôi muốn bạn tự làm tới cuối nếu các gate cho phép, không hỏi tôi thêm
  một GO chỉ để tiếp tục công việc này" — proceed to the end if gates
  allow; do not ask for another GO just to continue THIS work.
- Scope grant: "tối đa 3 scored cells đã định nghĩa (ILLIQ21, ILLIQ63,
  REVERSAL5), trên các fold 2019, 2020, 2021–2022; không paper/live/order,
  không S1, không mua dữ liệu."
- "Ghi chỉ thị owner này vào plan mới và yêu cầu A7 độc lập xét rõ liệu
  nó có thể thay thế GO tương tác theo luật repo hay không. KHÔNG tự tạo,
  tự gõ hoặc giả mạo GO của owner. Nếu P-8 bắt buộc GO mới sau A7 và
  không cho phép ngoại lệ này, hãy dừng đúng tại gate và báo chính xác
  trở ngại; tuyệt đối không lách bằng cách gọi scored PnL là
  'diagnostic'."
- Known-bug register (owner-supplied, to verify not assume): HTV in the
  universe is Hearst-Argyle Television (delisted 2009) yet the panel
  carries 2019–2021 bars; a buy at 1.36 on a volume=0/near-zero day
  created the fake PnL. Check also NLG, alias BYON/OSTK, and the whole
  anomaly class — not only the tickers already seen in PnL.

## 1. What the predecessor measured (immutable context)

STOCKS-AMIHUD-V1 scored 3 cells (observed denominator +3): the anchor and
neighbour "PnL" were 99.73%/99.76% one ticker (HTV) — a single
non-tradable print (2019-12-06 close/adj 1.36→13,050 on volume 10) —
and both arms FAILED the frozen MDD (>15%) and fold-concentration (>50%,
razor) gates; the reversal control was negative (anchor PnL is not a
reversal effect). Forensics (terminal_forensics.json) enumerated the
anomaly classes C1–C7 that THIS cycle's gates must handle as objective
laws. The retest therefore changes ONLY identity/execution/data-validity
laws — the signal idea, arms, folds, calendar, cost bands, weight law and
evaluation battery are re-frozen UNCHANGED from the predecessor (source:
its D1/impl contracts, sha-referenced).

## 2. Identity gate (P0-I) — falsifiable, uniform, frozen before new PnL

Ticker is not identity. For every staged universe code, resolve identity
from available evidence; ambiguous series are QUARANTINED by frozen law
with reason code + manifest + hashes. No name is removed because it made
PnL good or bad; every removal traces to a mechanical rule.

```text
I1 METADATA       symbol-list row (exchange, type, ISIN, name) + staged
                  series span (first/last/barcount).
I2 EDGAR CURRENT  SEC company_tickers.json (declared UA; if EDGAR is
                  unreachable, that channel is UNAVAILABLE — recorded,
                  and I3 tightens accordingly).
I3 QUARANTINE LAWS (mechanical, uniform):
   Q1 GHOST      EDGAR-current-absent AND no-ISIN AND (member of a
                 shared-death-date batch of >= 20 names OR carries >= 1
                 C8 extreme print) — cannot prove the series belongs to
                 the named US company in-window (HTV/NLG fixture class).
   Q2 VENDOR-TEST code matches ^NTEST or contains 'TEST' (C7).
   Q3 DUPLICATE  same-ISIN group with pairwise series return-corr >=
                 0.999 on >= 200 common bars: same security under two
                 codes — keep ONE (lexicographically first code), others
                 quarantined (BYON/OSTK fixture class). ISIN collisions
                 WITHOUT series identity are NOT deduped (noisy key) —
                 flagged only.
   Q4 NO-SERIES  staged file absent or empty (out of window).
   Everything else stays, with flags recorded. Delisted names that
   genuinely traded in-window STAY (death contract unchanged); removal
   happens at the name's own evidence, never by group.
I4 MANIFEST       quarantine_manifest.jsonl: code, reason (Q1..Q4),
                  evidence fields, series sha256; committed before any
                  new PnL; universe_retest_frozen.json = predecessor
                  universe minus quarantined codes (+ counts).
```

## 3. Bar-validity gate (P0-B) — reason-coded line quarantine, no patching

```text
B1 C8 EXTREME PRINT  any bar with |adj_d/adj_{d-1} - 1| >= 9 (order-of-
                     magnitude single-session move): excluded from ALL
                     formations AND never a fill bar (reason C8). Chosen
                     ex ante as a tradability/order-of-magnitude law;
                     uniformly applied; real extreme movers are lost to
                     formation too — accepted conservative cost.
B2 ZERO-VOLUME       Volume == 0 bars: never fill bars; prices retained
                     for marking only (reason C5 on fills).
B3 SPAN/DEATH        last served bar = name stop (unchanged death law);
                     shared-death batches go through I3-Q1, not a new
                     group rule.
B4 OHLC/UNIT         bars failing OHLC sanity (high<low, close<=0,
                     open<0) were already loader-skipped (predecessor);
                     C4 reverse-split basis breaks are caught by B1.
No price is patched, forward-filled, interpolated or deleted per-name
selectively; every rejected line carries its reason code and the raw
file is sha-pinned untouched.
```

## 4. Execution gate (P0-X) — fills must be provable or labeled proxy

```text
X1 FILL LAW    a fill at bar b requires: volume_b > 0 AND order notional
               <= 15% x (close_b x volume_b). Entry orders failing at
               t+1 are UNFILLED (position not opened; counted, reason
               X1-UNFILLED — the book runs without the name that date).
               Exit orders failing roll to the NEXT in-fold bar meeting
               X1; if none, the fold/death marking law applies (last
               provable close — labeled EXECUTION-PROXY in the report).
X2 INFO TIMING signal and sizing use data <= t only (unchanged). The
               fill-bar volume enters ONLY the execution simulation of
               t+1 mechanics — it can never alter the signal, the book
               membership at t, or sizing (golden test T-X2 mutates
               fill-bar volumes and asserts identical decisions at t).
X3 DISCLOSURE  if the illiquid book cannot be defended this way, the
               result is BLOCKED_EXECUTION/DATA — the 3 cells are NOT
               forced. "Execution proxy" labeling is mandatory wherever
               marking (not provable fills) produced a PnL number.
```

## 5. What is re-frozen UNCHANGED from the predecessor

ILLIQ formula (21/63 formation over served sessions, quorum floor(D/2),
winsorization NONE) · reversal control (-5-session return) · 21-session
grid + fold force-flat at fold-last close · adjusted-open fills via adj
factor · rank-count quintile, ties lexicographic · N_book >= 10
bookability · weights min(1/N_book, 0.15*DVmed60/AUM_ref $1M), excess to
cash · dynamic warmup 252 served sessions · price floor $1 · DVmed60 >=
$2M with >= 30/60 present · band costs {A:10,B:15,C:25}bps on DVmed60
bands, once per fill, stress 2.0 · death contract final-served-close ·
division-site register classes i–iv with FailLoud iii/iv · evaluation
battery §9 (folds, annual split, SPY per-fold B&H + matched book +
random twin seed 20260923, beta, drop-one, concentration, stress) ·
Stage-A gates (net expectancy>0, PF>=1.10, >=2/3 folds, MDD<=15%,
concentration<=50%, SPY-excess>=2/3, stress positive, drop-one, control
adjudication). Changes vs predecessor are ONLY: I3 quarantine laws, B1/B2
bar laws, X1/X2 execution law, and their counters/tests — each frozen
here before any new PnL, chosen for evidential reasons (C1–C7 measured
classes), never selected by outcome.

## 6. Golden tests (owner-named fixtures mandatory)

T1 ghost: an HTV-like series (EDGAR-absent, no-ISIN, batch + extreme
print) is quarantined by Q1 and can never enter the panel · T2
zero-volume fill: order at a V=0 bar is UNFILLED (counted) · T3 double
alias: two codes, same ISIN, corr>=0.999 -> exactly one survives · T4
forward split smooth + reverse split extreme print caught by B1 (bar
excluded from formation, never a fill) · T5 price-unit jump (10x on
tiny volume) caught · T6 missing identity: no metadata + flags ->
quarantine; metadata+no flags -> stays · T7 lookahead: mutating fill-bar
volumes changes fills but NEVER decisions/book at t · T8–T22: the
predecessor's full suite re-run against the retest engine (no-lookahead,
next-bar, fold law, cost-once, guards i/ii/iii/iv, death contract,
bookability, quintile, determinism, S1 refusal, exact-3, leak scan,
annual split, register completeness) · negative controls: poisoned
fixtures (ghost injected into a clean panel; fake 10x print; V=0 fill)
must be BLOCKED — each guard demonstrably fires.

## 7. Phases

```text
P0 close predecessor (done before this cycle opens: two-half close with
   verdicts immutable — reproduction and A7 terminal were waived by
   explicit owner instructions at close ('bỏ reproduction đi', 'không
   dispatch A7 terminal gì hết'), recorded verbatim in the predecessor's
   registry row and ledger row; this plan does not re-open them)
R1 register this cycle; commit plan; A7 plan audit (fresh) — audit item
   #1 is the §11 standing-directive adjudication
P0-I/B identity + bar censuses; quarantine manifest; universe re-frozen
D1 re-freeze set (family/execution/cost/eval contracts re-committed with
   §5 provenance + new laws §2–§4)
I  engine v2 (predecessor engine + I3/B1/B2/X1 laws + counters)
Z  sanitized exact-arm dry-run (no outcome at any depth)
A7 prelaunch (fresh): all predecessor checklist items + the new gates +
   the §11 adjudication explicitly
E  ONLY IF A7 authorizes BOTH the gates AND the §11 substitution: run the
   3 cells under the machine-wide heavy lock (clean tree, freeze-verified
   launcher); every computed outcome counts; negative results kept
R  independent reproduction (detached twin, byte-compare)
A7 terminal (fresh) — positive outcomes face the harsher bar
T  close per handbook §32; label OUTCOME_OBSERVED_RETROSPECTIVE_RETEST
   on every artifact; no promotion of any kind
```

If any gate FAILs, or the §11 adjudication says an interactive GO is
still required: STOP at the gate, report `NOT_RUN`/`BLOCKED` truthfully
with the exact obstacle. No scored PnL is ever labeled "diagnostic".

## 8. Report contract (final, owner-specified shape)

Old-vs-fixed comparison (which anomaly classes, how many codes/bars/
orders removed, with reason codes) · net after costs by 2019, 2020,
2021, 2022 AND by fold · gross vs net · trades/entries · MDD ·
concentration by symbol and by year · stress costs · drop-one-symbol ·
SPY and matched-book comparisons · every gate PASS/FAIL/NOT_RUN ·
explicit statement whether the new result still depends on one symbol
or a few anomalous bars · execution-proxy disclosures · R0_NOT_RUN
(ancestry unmeasured — carried from predecessor A3).

## 9. Terminal vocabulary

```text
STOCKS_AMIHUD_RETEST_V1_REJECT_ALL | STOCKS_AMIHUD_RETEST_V1_STAGE_A_
CANDIDATE_RETROSPECTIVE (planning-only; never deployment/paper) |
BLOCKED_DATA_OR_IDENTITY | BLOCKED_EXECUTION | BLOCKED_PRELAUNCH |
STOPPED_GATE_INTERACTIVE_GO_REQUIRED | TECHABORT
```

## 10. Standing prohibitions

No edits to predecessor artifacts · no crypto-ILLIQ import · no
parameter rescue (§5 is exactly the predecessor's frozen set + the
evidential gates) · no S1 · no orders/paper/live · no purchases · no
credentials in logs · heavy lock never contended · SANDBOX-OVERFIT-
3ASSETS never read.

## 11. Standing-directive adjudication (audit item #1 — the exact question for A7)

The owner's 2026-09-23 directive grants, for THIS cycle only: "tự làm
tới cuối nếu các gate cho phép, không hỏi tôi thêm một GO chỉ để tiếp
tục công việc này", scoped to the 3 named cells on the named folds, with
every boundary (no S1/orders/purchases) restated. The question A7 must
adjudicate BEFORE any scored execution: **does this explicit, scoped,
conditional owner instruction lawfully substitute the interactive GO
that P-8 otherwise requires at this cycle's own gate — given authority
order #1 (latest explicit owner instruction outranks plans and the
operating contract), the P-8 rationale (the gate exists so the owner
decides with A7's verdict visible, and the owner has here pre-decided
exactly that conditional), and the standing-delegation precedent
(handbook §27.5 push delegation)?** A7 must answer
SUBSTITUTION_VALID_AUTO_RUN_ALLOWED or INTERACTIVE_GO_STILL_REQUIRED
with written reasoning, and is forbidden from treating agent
convenience as authority. If INTERACTIVE_GO_STILL_REQUIRED: the cycle
stops at the gate (`STOPPED_GATE_INTERACTIVE_GO_REQUIRED`), the GO
phrase is reported to the owner, and nothing is laundered. The typed
phrase, if later given by the owner, is consumed only at this cycle's
own gate (P-8).
