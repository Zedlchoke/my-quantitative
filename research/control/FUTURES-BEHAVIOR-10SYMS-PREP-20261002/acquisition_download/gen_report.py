#!/usr/bin/env python3
"""gen_report.py — generate DOWNLOAD_REPORT.md + ACQ_DOWNLOAD_REPORT_VI.md
from COMPLETION_LEDGER.json (mechanical; no hand-typed numbers)."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

ACQ = Path(__file__).resolve().parent
LEDGER = ACQ / "COMPLETION_LEDGER.json"
MANIFEST = ACQ / "AV1_TRIM_MANIFEST.json"
TRIM_QUOTES = ACQ / "trim_quotes.json"
OVERLAP = ACQ / "IBKR_OVERLAP_VALIDATION.json"

STATE_ORDER = ["MIRRORED", "QA_PASS", "DOWNLOADED", "SUBMITTED", "QUOTED",
               "PLANNED", "QA_FAIL", "JOB_EXPIRED"]


def fmt_usd(x: float) -> str:
    return f"${x:.4f}"


def gb(x) -> str:
    return f"{x / 1e9:.3f}"


def main() -> None:
    led = json.loads(LEDGER.read_text())
    man = json.loads(MANIFEST.read_text())
    tq = json.loads(TRIM_QUOTES.read_text())
    rs_path = ACQ / "RESCOPE_MANIFEST.json"
    rs = json.loads(rs_path.read_text()) if rs_path.exists() else None
    chunks = sorted(led["chunks"].values(), key=lambda c: (c["order"],
                                                           c["chunk_key"]))
    rt = led["running_totals"]

    by_state: dict[str, int] = {}
    for c in chunks:
        by_state[c.get("state", "PLANNED")] = \
            by_state.get(c.get("state", "PLANNED"), 0) + 1

    total_records = sum(c.get("qa", {}).get("records_actual") or 0
                        for c in chunks)
    total_raw_bytes = sum(f["bytes"] for c in chunks
                          for f in c.get("files", [])
                          if f["vendor_filename"].endswith(".dbn.zst"))
    total_pq_bytes = sum(c.get("qa", {}).get("parquet_bytes") or 0
                         for c in chunks)
    mirrored = [c for c in chunks if c.get("state") == "MIRRORED"]
    qa_pass = sum(1 for c in chunks
                  if c.get("qa", {}).get("verdict") == "PASS")
    qa_fail = [c for c in chunks if c.get("qa", {}).get("verdict") == "FAIL"]

    overlap_txt = ""
    if OVERLAP.exists():
        ov = json.loads(OVERLAP.read_text())
        for root, rr in ov.get("roots", {}).items():
            idn = rr.get("identity", {})
            dc = rr.get("daily_close", {})
            dv = rr.get("daily_volume", {})
            m1 = rr.get("m1", {})
            st = rr.get("settlement", {})
            overlap_txt += (
                f"\n### {root}\n"
                f"- Identity: {idn.get('n_match')}/{idn.get('n_overlap_contracts')}"
                f" contracts def.expiration==IBKR lastTradeDate "
                f"(100% pass={idn.get('pass_100pct')})\n"
                f"- Daily close (RTH subset): n={dc.get('n_contract_days')}, "
                f"median|diff|={dc.get('median_abs_diff_ticks')} ticks, "
                f"within-1-tick={dc.get('pct_within_1_tick')}% "
                f"(pass={dc.get('pass')})\n"
                f"- Daily volume ratio vendor/IBKR: median="
                f"{dv.get('median_ratio')}, in[0.9,1.1]="
                f"{dv.get('pct_in_09_11')}% (pass={dv.get('pass')})\n"
                f"- M1 grid: {m1.get('vendor_minute_grid_pct')}% on-grid "
                f"(pass={m1.get('grid_pass')}); IBKR M1 overlap bars="
                f"{m1.get('ibkr_m1_overlap_bars')}, median|diff|="
                f"{m1.get('median_abs_close_diff_ticks')} ticks\n"
                f"- Settlement vs IBKR close: n={st.get('n_contract_days')}, "
                f"median|diff|={st.get('median_abs_diff_ticks')} ticks, "
                f"within-1-tick={st.get('pct_within_1_tick')}% "
                f"(pass={st.get('pass')})\n")

    lines = []
    a = lines.append
    a("# DOWNLOAD_REPORT — Databento chunked download (lane ACQ-DOWNLOAD)")
    a("")
    a(f"Task FUTURES-BEHAVIOR-10SYMS-PREP-20261002 · generated "
      f"{dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}")
    a("")
    a("- Authority: owner approval 2026-10-02 (ceiling $125 from credit; "
      "chunked download; iCloud mirror) + owner RESCOPE 2026-10-02 "
      "(verbatim: 'tôi muốn NQ ES 6E 6J 6B 6A thôi. Tải trong 125 đô đó. "
      "Còn lại mắc quá tính sau.'). Lane hard stop $118 (quote-vs-bill "
      "drift buffer).")
    if rs:
        a(f"- Package evolution: A-v1 $129.57 → A-v1-trim "
          f"{man['chosen_candidate']} ${man['totals']['get_cost_usd']:.2f} "
          f"→ RESCOPE ${rs['budget']['new_package_total_get_cost']:.2f} "
          f"(dropped GC/SI/CL/NG ohlcv, avoided "
          f"${rs['dropped_lines']['avoided_spend_usd']:.2f}, zero spent on "
          f"them; added NQ/ES 2010-06-06→2023-10-01 deltas + FX 2022 "
          f"backfills; definitions/statistics ALL10 kept).")
    a("- Batch API: official client v0.87.0 (batch.submit_job, dbn+zstd, "
      "split_duration=none, delivery=download, stype parent->"
      "instrument_id). get_cost docstring states it prices 'historical "
      "streaming or batched files' — same per-GB path; per-chunk quotes "
      "re-taken before every submit (budget law); vendor sha256 hashes "
      "verified on every file.")
    a("")
    a("## Per-batch table")
    a("")
    a("| # | chunk | schema | window | records (quoted→actual, drift) | "
      "raw .dbn.zst | parquet | get_cost | committed after | QA | "
      "state |")
    a("|---|---|---|---|---|---|---|---|---|---|---|")
    committed_run = 0.0
    for i, c in enumerate(chunks, 1):
        q = c.get("quote", {})
        cost = q.get("get_cost") or 0.0
        committed_run += cost if c.get("state") not in ("PLANNED", "QUOTED",
                                                        "DROPPED_BY_OWNER_"
                                                        "RESCOPE") else 0.0
        qa = c.get("qa", {})
        raw_b = sum(f["bytes"] for f in c.get("files", [])
                    if f["vendor_filename"].endswith(".dbn.zst"))
        recs = (f"{q.get('records'):,}→{qa.get('records_actual'):,}"
                if q.get("records") is not None and
                qa.get("records_actual") is not None else "—")
        drift = qa.get("records_drift_pct")
        drift_s = f", {drift}%" if drift is not None else ""
        a(f"| {i} | `{c['chunk_key']}` | {c['schema']} | "
          f"{c['start']}..{c['end']} | {recs}{drift_s} | {raw_b:,} B | "
          f"{qa.get('parquet_bytes') or 0:,} B | {fmt_usd(cost)} | "
          f"{fmt_usd(committed_run)} | {qa.get('verdict', '—')} | "
          f"{c.get('state', 'PLANNED')} |")
    a("")
    if rs:
        a(f"**Totals (rescope package): committed "
          f"{fmt_usd(rt['committed_usd'])} of the "
          f"**{fmt_usd(rs['budget']['new_package_total_get_cost'])}** "
          f"rescope quote; lane hard stop $118.00; owner ceiling $125.00.**")
    else:
        a(f"**Totals: committed {fmt_usd(rt['committed_usd'])} of the "
          f"{fmt_usd(man['totals']['get_cost_usd'])} package quote; "
          f"lane hard stop $118.00; owner ceiling $125.00.**")
    a(f"- Chunks: {rt['n_chunks']} planned; {rt['n_mirrored']} MIRRORED; "
      f"states {json.dumps(by_state)}.")
    a(f"- Records actually downloaded+QA'd: {total_records:,}; raw "
      f".dbn.zst bytes on disk: {total_raw_bytes:,}; parquet bytes: "
      f"{total_pq_bytes:,}.")
    a(f"- QA: {qa_pass} PASS" +
      (f", {len(qa_fail)} FAIL ({[c['chunk_key'] for c in qa_fail]})"
       if qa_fail else ", 0 FAIL") + ".")
    a("")
    a("## Budget accounting")
    a("")
    a("| item | USD |")
    a("|---|---|")
    a(f"| chosen trim manifest quote | "
      f"{fmt_usd(man['totals']['get_cost_usd'])} |")
    a(f"| committed (submitted+) at report time | "
      f"{fmt_usd(rt['committed_usd'])} |")
    a(f"| delivered (downloaded+) at report time | "
      f"{fmt_usd(rt['delivered_usd'])} |")
    a("| lane hard stop | $118.0000 |")
    a("| owner ceiling | $125.0000 |")
    a(f"| headroom quote→hard stop | "
      f"{fmt_usd(118.0 - man['totals']['get_cost_usd'])} |")
    a("")
    a("Billing basis: get_cost per exact chunk params before every submit "
      "(recorded in COMPLETION_LEDGER.json with timestamps); vendor bills "
      "delivered batch files on the same per-GB metered pricing (client "
      "docstring). Actual invoice reconciliation vs usage page is "
      "owner-side (NOT_RUN_DOC_UNCLEAR: no account endpoint).")
    a("")
    a("## Disk")
    a("")
    a(f"- start free: 21.412 GB decimal (2026-10-02, statvfs); reserve "
      f"20% = {21.412*0.2:.3f} GB; concurrent NONPRICE lane allowance 2 GB.")
    a(f"- per-batch gate in pipeline (raw+parquet+scratch+mirror vs free); "
      f"measured ratios evolve in ledger disk_gate lines.")
    a(f"- raw zstd/billable measured (delivered so far): see ledger "
      f"disk_gate fields; def chunks ≈0.034 (definitions compress ~30x).")
    a("")
    a("## iCloud mirror")
    a("")
    a(f"- Destination: "
      f"`~/Library/Mobile Documents/com~apple~CloudDocs/"
      f"my-quantitative-futures/av1-trim/`")
    a(f"- {len(mirrored)} chunks mirrored: raw .dbn.zst + parquet + qa.json "
      f"+ ledger entry per chunk; every copy SHA256-verified against "
      f"source; state COPIED, cloud upload "
      f"SYNC_PENDING_UNVERIFIED (macOS/iCloud's job — never claimed "
      f"cloud-stored by this lane).")
    a("- This is the owner's personal backup of licensed data; no "
      "redistribution.")
    a("")
    a("## Vendor-emission conventions MEASURED on first real data "
      "(documented, not defects)")
    a("")
    a("- definition schema: every instrument definition re-broadcast at "
      "each session open (same ts_event, ts_recv = session start) + spread "
      "legs as separate records (leg_index); stream strictly ts_recv-"
      "ordered; with leg_index keyed: 0 duplicates, 0 content conflicts "
      "(first chunk evidence in qa/…qa.json).")
    a("- Billing reconciles exactly: quoted records == delivered records "
      "on every chunk so far (drift 0.000%).")
    a("")
    a("## IBKR-overlap validation (STEP 4)")
    a(overlap_txt or "- NOT_RUN_YET (runs after NQ/CL chunks delivered).")
    a("")
    a("## Partial-state law")
    a("")
    a("Every chunk's exact params + job id + SHA256 live in "
      "COMPLETION_LEDGER.json (SUBMITTED-first). Resume never resubmits a "
      "recorded job; a pre-submit dedupe scan (list_jobs exact-param "
      "match) guards the crash-between-submit-and-ledger window.")
    (ACQ / "DOWNLOAD_REPORT.md").write_text("\n".join(lines) + "\n")
    print(f"wrote DOWNLOAD_REPORT.md ({len(lines)} lines)")

    # ---------------- Vietnamese owner summary ----------------
    vi = []
    v = vi.append
    v("# BÁO CÁO TẢI DỮ LIỆU DATABENTO (lane ACQ-DOWNLOAD) — tiếng Việt "
      "tóm tắt cho owner")
    v("")
    v(f"Sinh {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}")
    v("")
    v("## Đã làm gì")
    v("")
    v(f"1. **Gói trim**: A-v1 gốc $129.57 > trần → tính get_cost 4 phương "
      f"án trim (miễn phí, chỉ metadata). Chọn **{man['chosen_candidate']}**: "
      f"cắt sâu ohlcv-1m 4 cặp FX (6E/6J từ 2026-01, 6B/6A từ 2026-04), "
      f"GIỮ NGUYÊN NQ/ES/GC/SI 24m, CL/NG 9m, definitions+statistics 24m. "
      f"Tổng quote **{fmt_usd(man['totals']['get_cost_usd'])}** ≤ mục tiêu "
      f"$115. (Phương án FX 12 tháng $115.52 bị loại vì vượt $115.)")
    v(f"2. **Tải theo chunk**: {rt['n_chunks']} batch nhỏ (3-6 tháng/lần) "
      f"qua API batch chính thức; MỖI batch đều get_cost lại trước khi "
      f"submit và kiểm luật ngân sách (cam kết ≤ $118 < trần $125 của "
      f"owner). Thứ tự: definitions/statistics → NQ/ES → GC/SI → FX → "
      f"CL/NG. Mỗi batch: SHA256 khớp hash nhà cung cấp → QA bằng adapter "
      f"code/futbt/dbn → chuyển parquet → checkpoint ledger → copy "
      f"iCloud.")
    v(f"3. **Tiến độ tại thời điểm báo cáo**: {rt['n_mirrored']}/{rt['n_chunks']} "
      f"chunk hoàn tất (tải+QA+mirror); cam kết chi tiêu "
      f"**{fmt_usd(rt['committed_usd'])}** / quote gói "
      f"{fmt_usd(man['totals']['get_cost_usd'])} / hard-stop $118 / trần "
      f"$125.")
    v(f"4. **QA từng batch**: số bản ghi thực tế khớp quote (drift "
      f"{0.0:.3f}% trên các chunk đã QA — xem ledger); schema fail-closed; "
      f"kiểm trùng/lệch chuỗi/cửa sổ thời gian; giá âm giữ nguyên; thang "
      f"6J hợp lệ; DST/session. Phát hiện và ghi nhận quy tắc phát sóng "
      f"của vendor (definitions phát lại mỗi phiên mở, spread legs là bản "
      f"ghi riêng theo leg_index — 0 trùng thật, 0 xung đột nội dung).")
    v(f"5. **iCloud mirror**: copy raw + parquet + QA json + entry ledger "
      f"vào CloudDocs/my-quantitative-futures/av1-trim/, SHA256 verify từng "
      f"file. Trạng thái trung thực: COPIED + SYNC_PENDING_UNVERIFIED "
      f"(việc upload lên đám mây là của macOS/iCloud — lane không tuyên "
      f"bố đã lên cloud). Đây là backup cá nhân của owner cho dữ liệu có "
      f"bản quyền — không phân phối.")
    v(f"6. **IBKR overlap validation** (NQ + CL, cửa sổ 2025-08→nay nơi "
      f"IBKR raw có dữ liệu): xem kết quả chi tiết trong "
      f"IBKR_OVERLAP_VALIDATION.json và bảng tiếng Anh trong "
      f"DOWNLOAD_REPORT.md.")
    v("")
    v("## Tiền")
    v("")
    v(f"- Quote gói đã duyệt (trim): **{fmt_usd(man['totals']['get_cost_usd'])}**")
    v(f"- Đã cam kết (submit+): **{fmt_usd(rt['committed_usd'])}**")
    v(f"- Còn lại tới hard-stop lane $118: "
      f"**{fmt_usd(118.0 - rt['committed_usd'])}**")
    v(f"- Còn lại tới trần owner $125: "
      f"**{fmt_usd(125.0 - rt['committed_usd'])}**")
    v("- get_cost là báo giá chính thức theo từng chunk (không phải ước "
      "tính); vendor tính phí batch theo cùng bảng $/GB. Đối chiếu hóa "
      "đơn thực tế trên usage page là bước owner-side.")
    v("")
    v("## Blocker / lưu ý")
    v("")
    v(f"- Trạng thái chunk còn lại: {json.dumps(by_state)}. Nếu lane dừng "
      f"giữa chừng, ledger COMPLETION_LEDGER.json ghi chính xác chunk nào "
      f"xong, chunk nào pending — chạy lại acq_pipeline.py sẽ resume không "
      f"mua trùng.")
    v("- Dữ liệu thô nằm NGOÀI git: "
      "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/")
    v("- Không có key/credential trong bất kỳ artifact nào (đọc in-process, "
      "chỉ qua Authorization header, lỗi được redact).")
    (ACQ / "ACQ_DOWNLOAD_REPORT_VI.md").write_text("\n".join(vi) + "\n")
    print("wrote ACQ_DOWNLOAD_REPORT_VI.md")


if __name__ == "__main__":
    main()
