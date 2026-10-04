# PLAN_futures_es_pb1_v1 — FUTURES-ES-PB1-V1 (registered plan)

- Registered: 2026-10-04, by the owner-delegated root registration session
  (owner delegation verbatim: "tôi uỷ quyền đăng ký cho bạn. Sau khi đăng
  ký thì sẽ kiếm tra những gì? Strategy gì?" — registration ONLY; every
  gate beyond it still requires its own authority; the typed GO is never
  delegated).
- Authority chain: D3 = Variant A signed by owner ("tôi chọn 2.25$",
  recorded `auth/D3_RECORDED.json` in the freeze worktree lineage);
  cost-freeze errata `COST_FREEZE_ERRATUM.md` + `SHORTLIST_STALE_COST_
  ERRATUM.md` + `PIN_SUPERSESSION.md`; registration packet
  `FUTURES-ES-PB1-REGPREP-20261004/synth/REGISTRATION_PACKET.md`;
  freeze-authority commit **`e7fc1d8db00e91af74683cee7e999620fa8ff361`**
  on branch **`prep/futures-es-reg-20261004`** (worktree
  `.worktrees/futures-es-reg/prep`), whose
  `freeze/freeze_pins_v2.json` is the AUTHORITATIVE 34-pin manifest
  (PINS_STABLE_VERIFIED by fresh-context verifiers at committed SHAs
  77a763ac / 19f42a8d + read-only rerun at e7fc1d8d: 34/34).

## 1. Scope (one family, one symbol)

CME E-mini S&P 500 futures (**ES**), single parent family **PB1 OVN pair**
(overnight→RTH continuation/reversal pair, M-A/M-B arms): **exactly 24
trial identities** per SPEC_PB1_ES §6 A-r4 table — P-A 8 + P-B 8 + FOMC 4
+ controls C1-C4 4 (transcription: freeze lineage
`freeze/identity_table_24.json`, reconciled vs census zero-discrepancy).
The frozen ES cap 24 is fully consumed by this table; **no other family
and no ES amendment rides on this cycle** (ES-F1..F4 / EXPWITCH remain
out; EXPWITCH is moreover dead at its pre-declared F5-K6 gate).

## 2. Cost contract (frozen at registration)

**Variant A** (owner D3): commission 0.85 + exchange **1.38** + NFA reg
**0.02** (0.01 only 2014-10-01→2017-12-31) = **2.25/side fees**; spread
half-turn 6.25 (close-proxy); slippage S1/S2/S3 = 12.50/25.00/37.50
(1/2/3 ticks × $12.50, research assumption D1) ⇒ all-in/side
**21.00 / 33.50 / 46.00**, RT 42.00/67.00/92.00 (window rows
20.99/33.49/45.99). Stress ladder ×1.0/×1.5/×2.0 (×1.0 is the gate
number). BBO NOT_RUN ⇒ conservative fill law (next-bar open, no
limit/queue claims, close proxies, SL-priority same-bar).
**Labels: MODELED COST; documentation-A7 clean (AUTHORIZED_WITH_FINDINGS,
0 HIGH/CRITICAL); VERIFIED_VS_ACCOUNT = NOT_RUN.** The values 1.386 and
21.006/33.506/46.006 are retired footnote-glue prints — never consumable
(COST_FREEZE_ERRATUM law).

## 3. Data + PIT laws (frozen by pin)

Chain of record: ES baseline chain per SPEC_PB1_ES §1 (68/68 expiries
re-derived; 66/66 data-side; panel pin in the v2 manifest). Exclude set:
FOMC 132-statement day-exclude law; BLS vintage law incl. the D5 pin
(CPI Jan-2026 = 2026-02-13 08:30 ET); holiday fail-closed (ES 2026
CAL-CLOSE FACT cells + product-level NOT_OBTAINED ⇒ excluded windows);
RTH-core <60% coverage sessions excluded by bar-count rule, never
imputed. NOT_RUN stays NOT_RUN (BBO, surprise content, latency).
Folds: 4-fold shape F1 2010-06..2012-12 · F2 2013-01..2017-12 · F3
2018-01..2021-12 · F4 2022-01..2026-09, warmup 252 sessions/fold head;
era K-views (session-close eras; fee-tier window; FOMC/COVID regimes).
All 34 freeze pins: `freeze/freeze_pins_v2.json` @ e7fc1d8d (above).

## 4. Gates (two-key law; order binding)

1. ~~Registration~~ (this act; registry row + this plan + control-plane
   commit by pathspec).
2. **Deterministic exclude list + selection freeze** (post-registration,
   0-cost; from the pinned laws only).
3. **Prelaunch A7 — key 1 of 2** (independent fresh-context audit:
   identity enumeration vs frozen 24; cost arithmetic vs §2; PIT/exclude
   coverage; budget accounting; freeze integrity vs the v2 manifest;
   language scan). Required verdict: 0 HIGH/CRITICAL unresolved.
4. **Exact-arm dry-run** (single-shot rehearsal of the 24 identities at
   ×1.0 declared costs; heavy-lock checked; budget counters untouched;
   output quarantined descriptive-only; pass = byte-exact identity
   enumeration + cost recomputation match).
5. **Typed owner GO — key 2 of 2** (owner only; NEVER delegated).
6. Scored under heavy lock + reproduction twin + terminal A7 (terminal
   outcomes pre-decided; REJECT_ALL valid).

## 5. Canonical GO phrase (F-A5 resolution, audited authority)

**`GO FUTURES-ES-PB1-V1 SCORED EXECUTION`** — exactly this string, typed
fresh at this cycle's own gate after gates 2-4 pass. The historical
PLAN_futures_es_v1.md §6 example string (`GO FUTURES ES V1 SCORED
EXECUTION`) is a pre-registration illustration, **superseded by this
registered rule** (adjudicated in the registration packet §5 and verified
by the independent verifiers at 77a763ac/19f42a8d). **No aliases; a
paraphrased or early GO = intent only, dies unconsumed.**

## 6. Budget + accounting

24 identities = budget ceiling 24 (observed denominator law: every
scientifically computed scored result counts, publication failure
included; dry-run/quarantined passes do NOT). S1 data stays
SEALED_UNTOUCHED until its own explicitly authorized stage. No orders,
no purchases, no push/merge in this cycle's authorized surface.

— End registered plan. Registration is not a GO; nothing has run.
