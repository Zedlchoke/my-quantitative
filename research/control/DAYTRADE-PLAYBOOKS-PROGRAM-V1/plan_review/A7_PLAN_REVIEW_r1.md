# A7 PLAN REVIEW r1 — DAYTRADE-PLAYBOOKS-PROGRAM-V1 (pre-registration, pre-execution)

- Reviewer: A7 independent reproducer lane (fresh-context subagent, read-only,
  2026-09-27). Agent id: agent_60fce425-be7b-4d37-84c1-6baf957bb951.
- Targets tại thời điểm review: `plans/PLAN_daytrade_playbooks_program_v1.md`,
  `plans/PLAN_dtp_cx_solusdt_c1.md`, `plans/PLAN_dtp_fx_audusd_c1.md`,
  `research/control/DAYTRADE-PLAYBOOKS-PROGRAM-V1/PLAYBOOK_TAXONOMY.md`
  (cả bốn ở dạng draft TRƯỚC remediation r1).
- Báo cáo dưới đây là NGUYÊN VĂN output của A7 (không biên tập). Remediation
  của Lead ghi ở mục cuối.

---

VERDICT: AUTHORIZED_WITH_FINDINGS

## Findings

**F1 — HIGH — Crypto data gate omits owner-mandated components (mark/index, quote/trade).**
Files: `plans/PLAN_daytrade_playbooks_program_v1.md` §3.3 + §7; `plans/PLAN_dtp_cx_solusdt_c1.md` §2.
The owner directive enumerates the crypto data gate as "quote/trade, fees, funding, mark/index per contract." The master §3.3 gates only "funding dual-book + fee declared + spread census"; §7 adds gap/outage/latency. Mark/index per contract appears nowhere in the master or the SOL child. This is not cosmetic: (i) the CX OOS is prospective accumulation (§8) — funding settlement accounting and any funding-adjacent label require mark/index streams per contract; (ii) the child's own flagship direction identity I002 (BTC confirm → enter SOL "khi quote SOL chưa adjust") cannot run its F-0 information test without a gated SOL quote/trade series, yet the child data gate stages only klines 1m/15m + a 6-month spread census. The mechanism's "not yet adjusted" premise is currently un-gated and un-measurable as written. Remediation: add "quote (bookTicker) + trade (aggTrades) + mark/index per contract, coverage-verified" as mandatory CX gate items in master §3.3/§7 and child §2; for I002, state explicitly which series measures the adjustment lag, else the identity enters F-0 as `BLOCKED_DATA` on its own information layer.

**F2 — HIGH — Cross-program stop-rule re-entry onto SOLUSDT is cited but never surfaced as the owner decision it is.**
Files: master §3.2, §9(a), §12.
`research/wayfinder/MAP.md` records that the sibling PWS-CX track fired its §9(a) stop rule: PWS-CX-SOLUSDT-C1 and PWS-CX-BNBUSDT-C1 both closed `NO_ELIGIBLE_PROPOSAL` (0/18 each), and the MAP states "Track PWS-CX stop-rule §9(a) FIRES: 2 consecutive empty pair-children ⇒ viability council mandatory before any new pair-child." The DTP master cites "PWS §9(a) precedent đã từng bắn" inside §9(a) and re-uses PWS-CX-SOLUSDT durable assets in §3.2, but (i) never discloses that pair #1 of the new program is the same pair that just closed empty under the sibling program, and (ii) never states that the charter's claimed lawful basis — the playbook taxonomy + outcome-blind annotation layer as a new observable class (price-level/session playbooks vs the dead funding-run class) — is exactly the §9(a)-required "observable/nguồn/giả thuyết payer mới CÓ BẰNG CHỨNG," and that owner Q1 is implicitly ruling on that. Without this, GO-1 on DTP-CX-SOLUSDT can be read as silently bypassing a fired sibling stop rule. Remediation: in §3.2 (SOL rationale) and §12 (Q1), add explicit disclosure of the PWS-CX SOL/BNB empty closes + fired stop rule, and make Q1 explicitly include the determination that the taxonomy/annotation layer constitutes evidenced new information for the price-level class.

**F3 — MEDIUM — `CRYPTO-HISTORICAL-REPLICATION-3F-V1` (and `SHADOW-PAPER-REVIEW-V1`) missing from the explicit no-touch list.**
File: master §1.2.
§1.2 names six shadow/dashboard cycles plus ETHUSDT-OPEN-SEARCH-V2, but `CRYPTO-HISTORICAL-REPLICATION-3F-V1` is ACTIVE_LIGHT with scored execution under heavy lock (`OUTCOME_EXPOSURE_MAP.md` §2.1 records exactly this non-interference obligation for the sibling SRLV program), and `SHADOW-PAPER-REVIEW-V1` is ACTIVE_LIGHT in the registry. The heavy-lock law in §3.2 partially covers the conflict, but a pre-registered program overlapping all four Binance perp pairs should name the cycle it must not collide with. Remediation: add both cycles to §1.2's enumeration with the same "read-only public data, no restart/state touch" clause.

**F4 — MEDIUM — No pre-registration intake/re-measure snapshot.**
File: master (missing section).
The owner directive requires, before cycle creation: re-measure registry/HEAD/worktrees/lock/workers/data foundation/GO gates. The draft records only one number (disk 6.1 GiB, §3.4). PWS had the same gap; the ERP umbrella did not (it carried a full intake snapshot §"Intake snapshot"). Remediation: add a Phase-0 intake block to the master or make it a binding precondition of charter registration (measured at this review: `main` @ `96d65aae`, heavy lock `FREE_PROVEN`, no DTP registry row, DTP files untracked).

**F5 — MEDIUM — "One-look cấp chương trình" on the FX sealed window is program-scoped wording over a lineage-shared asset.**
Files: master §8; `plans/PLAN_dtp_fx_audusd_c1.md` §2; cf. `plans/PLAN_pws_program_v1.md` §8.
AUDUSD/USDCAD 2026-H1 are `SEALED-UNREAD` lineage assets (OUTCOME_EXPOSURE_MAP §3). PWS §8 and now DTP §8 both declare the same window "một cửa sổ transfer = MỘT look cấp chương trình (matrix L5)." If DTP-FX opens after a reopener and consumes the AUDUSD one-look, nothing in the drafts pins that this exhausts the window lineage-wide (for PWS-successors too). Two sibling programs could each take one "program-level" look at the same bytes. Remediation: one sentence in master §8: consumption is recorded in OUTCOME_EXPOSURE_MAP at child close and exhausts the window for the whole lineage, not just DTP.

**F6 — LOW — Disk figure drift.** Master §3.4 / taxonomy Bảng 2 claim "disk 6.1GiB"; `df -h /` re-measures 6.2 GiB avail today. BNB conclusion unchanged (25 GB needed). Pin a measurement timestamp on the number.

**F7 — LOW — SOL child overstates its own exposure class.** `PLAN_dtp_cx_solusdt_c1.md` §1: "1h/15m/1m đều outcome-exposed ở 1h." OUTCOME_EXPOSURE_MAP classifies SOL 1h as `OUTCOME_EXPOSED_baseline` only (cross-section baselines; "không có search directional riêng") — which is precisely why SOL is pair #1. Master §3.2 states it correctly; align the child wording.

**F8 — LOW — Spread-census extrapolation risk.** The 6-month SOL bookTicker census will price fills across a 2020–2026 dev window (child §2.4). "Re-verify coverage" is necessary but not sufficient: out-of-census-window fills should be explicitly costed as declared-band ×1.5/×2.0 (the master's own gap/outage treatment) with a coverage label, or the measured/declared boundary silently degrades.

**F9 — LOW — Falsifier-battery numbering mismatch.** Master §11 promises "falsifier battery (F-0…F-7)"; the SOL child enumerates F-0, F-1, F-2, F-3, F-5, F-6/Q-6, Q-12 — F-4 and F-7 never defined. Align or state the master set governs.

**F10 — LOW — Dangling decision-artifact pointer.** Master §12 says "xem GO1_OWNER_PACKET.md"; `research/control/DAYTRADE-PLAYBOOKS-PROGRAM-V1/` currently contains only PLAYBOOK_TAXONOMY.md. Acceptable for a draft, but the packet must exist before/at charter approval since all five owner decisions route through it.

**F11 — LOW (informational) — Citation provenance in the taxonomy.** `ROUNDNUM` and `PDHLOC-C2` (rows 5 and 6) are not rows in FAMILY_FAILURES.jsonl; they are backed by OUTCOME_EXPOSURE_MAP §1's 12-family census line and the FX-MAJORS/MAP artifacts, both of which the taxonomy lists as sources. The verdicts stand; keep the provenance labels distinct (census-family vs registry-family) when the artifact is frozen.

## DECISIVE NUMBERS RECHECKED

1. FAMILY_FAILURES.jsonl row count: `wc -l` = 137 — MATCH (master §1.2, taxonomy header).
2. Free disk: `df -h /` = 6.2 GiB avail — MISMATCH vs claimed 6.1 GiB (drift only; F6).
3. SRLV M1 SETTLE-RESOLVE kill: MAP lines 94–109 + `SRLVCX1-M1` in registry — died dev gates both pairs, K-CTRL inverted out-earns — MATCH.
4. TRACKA1-M1 PIT-seam kill: registry line 127, `KILL_PIT_SEAM`, PF 1.0334/1.0509, net<0 @k1.5 — MATCH ("PIT-clean PF 1.03–1.05 chết ở 1.5×").
5. SOL klines 1h floor 2020-09-14 gapless: DATACOST §2 + OUTCOME_EXPOSURE_MAP §2 — MATCH.
6. SOL funding 6,580 settlements bit-exact: MAP PWS-CX-SOLUSDT bullet — MATCH.
7. SOL spread census p50 0.469 bps (6-month bookTicker, sha-pinned): MAP — MATCH.
8. SOL funding sign autocorr +0.853: MAP — MATCH.
9. BNB spread census `NOT_RUN_DISK_CONSTRAINT` (~25 GB): MAP ("df 7GB < 25GB") — MATCH; BNB funding 7,261 — MATCH.
10. VIABILITY: 0/12 FX classes, stressed RT floor 3.6/4.4 pips zero remainder: MAP viability verdict + OUTCOME_EXPOSURE_MAP §1.1 — MATCH.
11. ERP umbrella §5.3 = ten mandatory fields: read — MATCH.
12. P-8 GO-phrase discipline: LESSONS.md line 122 — MATCH; P-27/P-28/P-29/Q-7/Q-16 all present — MATCH.
13. BTC funding measured 11.798%/yr; 15m catalog 2024-08+; CHR3F declared fee 5bps+1tick; G5 conc 0.50 unpassable long-biased: DATACOST §2 + OUTCOME_EXPOSURE_MAP §2 — MATCH. ETH 7,305 settlements — MATCH.
14. FX spreads: AUDUSD crossing 0.9–1.0 / USDCAD 1.1–1.2, stressed RT 3.6/4.4; EURUSD/GBPUSD/USDJPY p50 0.3/0.8/0.5 pip; USDCHF 0 bytes `BLOCKED_DATA_LICENSE`: DATACOST §1 + OUTCOME_EXPOSURE_MAP §1/§1.1 — MATCH.
15. Registry/lock/HEAD: ECONOMIC-ROBUSTNESS-PROGRAM-V1 ACTIVE_LIGHT 0/0; the six checklist ACTIVE_LIGHT cycles all confirmed ACTIVE_LIGHT; no DTP cycle registered; heavy lock `FREE_PROVEN`; `main` @ `96d65aae`; all three DTP files untracked — MATCH (nothing registered, nothing executed).
16. DFV1 §8 storage law (abort acquisition below 5.0 free, `BLOCKED_STORAGE`): PLAN_data_foundation_fx_crypto_stocks_v1.md lines 177–180 — MATCH.
17. Collision citations present in FAMILY_FAILURES.jsonl: FXFV2-A4-P1/P2, FXFV1-A3-P1/P2, FXOS-04, FXNG1/3/4, FXFV5/6/7, CNG1-A4, CNG2-A4/A5, V17-A6-P1/P2, V17-a5-P1, TRACKA1/2, SRLVCX1-M1, PWSCXSOL1-I001, EOS1-E1/E2, H-VOLCOMP-BRKOUT, PSV1-BTC_H4 — all MATCH. ROUNDNUM/PDHLOC-C2: not registry rows, backed by OUTCOME_EXPOSURE_MAP §1 census — MATCH with F11 caveat.
18. Base-rate claims (ERP1-TA-C2 7/7 pre-PnL; SRLV 3/4 veto + 1/1 dev-gate death; EURUSD 1/48 then holdout fail; DSR V14 0.00224 N=146): MAP + umbrella §5.2 — MATCH.

**Collision-table check (D):** No false-OPEN found. Row 12 (BTC→SOL lead-lag) correctly stays OPEN-KILLRISK: the nearest dead families are FXFV7-A6-P2 (FX cross-pair, different asset), EOS1-E1 (BTC-state gates on ETH at H4, died on the always-on beta wall, not as a diffusion kill), daily cross-sectional momentum, and TRACKA1-M2-XCONF (FX cross-pair gating on ancestry observables) — none is a measured crypto intraday BTC→alt diffusion kill, and the draft names the three kill-risks (K-ANC representation, K-COST ceiling ≈11–13 bps, fictional-counterparty veto) that would close it. No over-kill either: every DEAD verdict traces to a named measured skeleton or class death (rows 1–11), and the intraday/session transfers rest on the owner's own re-clock/anti-variant law (2026-09-27 instruction, Q-3, P-29) rather than on invented measurements, with council F-0 preserved as the final arbiter in every row.

**Internal consistency (E):** Budget arithmetic reconciles (≤3 identities × 4–6 cells = 4–18/pair ≤ 18; 4 CX pairs ≤ 72; FX amendment 2 pairs ≤ 36; lineage one-look caveats in F5). GO-phrase table matches both child plans and P-8 law. FX child dormancy matches master §5 and the GO table. Power floors inherit umbrella §5.14 (master is slightly stricter on crypto intraday than the DATACOST baseline — lawful, children may only raise). Anti-variant §2.3 is verbatim PWS §2.3. CX prospective vs FX sealed OOS rules are consistent across master and children.

**Violations (F):** None found. No scored grid (the "ceiling×power grid một dòng" is the pre-PnL P-29 kill pattern, not a scored scan), no parameter rescue, no proxy substitution (news → `BLOCKED_DATA`; spread census missing → BLOCKED), no maker-only assumptions (I002 is taker-side; maker-only remains banned until queue position is measured), no leverage (unlevered 1×), S1 sealed everywhere, no shadow/worker/dashboard touch (gap in F3), no registration, no GO consumed.

This is a faithful, adversarially-designed pre-registration: the drafts encode nearly every clause of the 2026-09-27 owner directive, correctly refuse to register or execute anything, and their factual spine survives every spot-check I ran. The two HIGH findings are completeness defects, not breaches: the crypto data gate drops the owner's mark/index and quote/trade components (leaving the program's own flagship identity information-untestable as written), and the SOLUSDT re-entry onto a track where the sibling program's two-consecutive-empty stop rule just fired is cited but not surfaced as the explicit owner decision it must be. Fix F1–F5 before the owner packet is drafted; none requires changing the research design.

---

## Remediation record (Lead, 2026-09-27 — sau review, trước GO-1 packet)

- F1 ĐÃ SỬA: master §3.3 + §7 (CX) thêm quote/trade + mark/index per contract
  làm gate bắt buộc + luật "identity phải khai bề mặt đo của chính nó, thiếu
  series ⇒ BLOCKED_DATA tại F-0"; child SOL §2.4 + I002 nêu rõ series đo độ
  trễ (aggTrades + bookTicker SOL) và nhánh BLOCKED_DATA.
- F2 ĐÃ SỬA: master §3.2 thêm đoạn công khai PWS-CX SOL/BNB đóng trống +
  stop-rule đã bắn; §12 Q1 nâng thành quyết định định nghĩa "observable mới
  có bằng chứng" kèm nhánh thay thế (BTCUSDT đầu, hoặc CX DORMANT).
- F3 ĐÃ SỬA: §1.2 thêm CRYPTO-HISTORICAL-REPLICATION-3F-V1 +
  SHADOW-PAPER-REVIEW-V1.
- F4 ĐÃ SỬA: master thêm §0.1 Phase-0 intake snapshot đầy đủ.
- F5 ĐÃ SỬA: §8 thêm câu one-look cấp lineage + ghi OUTCOME_EXPOSURE_MAP tại
  two-half close.
- F6 ĐÃ SỬA: §3.4 pin timestamp + 6.2 GiB (đo A7 cùng ngày).
- F7 ĐÃ SỬA: child §1 exposure class = `OUTCOME_EXPOSED_baseline`.
- F8 ĐÃ SỬA: child §2.4 out-of-census-window fill = declared band ×1.5/×2.0
  + coverage label.
- F9 ĐÃ SỬA: §11 + child §4 thống nhất "umbrella numbering, master governs".
- F10 ĐƯỢC ĐÓNG BỜI file này cùng GO1_OWNER_PACKET.md (cùng commit).
- F11 ĐÃ SỬA: taxonomy rows 5/6 gắn nhãn census-family + provenance.
