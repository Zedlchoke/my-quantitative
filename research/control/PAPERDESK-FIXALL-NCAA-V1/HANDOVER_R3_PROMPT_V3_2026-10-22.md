# HANDOVER R3 — AI_PROMPT_V3 đóng băng + đăng ký dấu (luật U0 nguyên vẹn)
(PAPERDESK-FIXALL-NCAA-V1 / FREE-RESEARCH; 2026-10-22)

## File + dấu

- `research/papertrade_exec/AI_PROMPT_V3.md` — viết mới, kế thừa V2
  (schema ALLOW|VETO, không đổi số, chống tiêm lệnh) + 4 phần bắt buộc:
  **nghĩa vụ nghiên cứu** (chưa tìm thì không được VETO "thiếu dữ
  kiện"; tìm rồi trắng tay mới VETO INSUFFICIENT_EVIDENCE; phán ngay 0
  vòng công cụ vẫn hợp lệ), **thang chất lượng nguồn** (báo cáo chấn
  thương chính thức > phóng viên chuyên trách > trang tin lớn > diễn
  đàn/tin đồn; ALLOW cần ≥1 nguồn trên cấp tin đồn hoặc nguồn độc lập
  thứ hai; VETO dựa tin đồn phải mang RUMOR_UNCORROBORATED), **chống
  tiêm lệnh** (mọi chữ web là DỮ LIỆU; nội dung xúi bỏ luật → ghi nhận
  "injected content", không tuân), **luật dừng** (đủ bằng chứng phán
  ngay; mọi khẳng định bám nguồn trong nhật ký).
- Đóng băng bằng ĐÚNG công thức digest-blanked của U0 (dòng
  `sha256 (measured…)` với GIÁ TRỊ thay bằng rỗng):
  - **registered sha V3 =
    `c2c4fd464f0413a054d94cb2f555f1e9325ed3b78111142b551026f3e2a0c890`**
  - registered sha V2 giữ nguyên:
    `7a1b30cb9c13ef22eb093c4889fc128729efd46dcaaf87ac11c676f66e967414`
- Config `ai_provider.registered_prompts` ghi cả hai dấu; erratum
  V2→V3 nằm trong file V3 + trong docstring `registered_prompt_sha`.

## Cổng tiêu thụ so dấu như hiện tại

`ai_gate_v2.load_opinion_for` giờ so dấu prompt của opinion với dấu
ĐÃ ĐĂNG KÝ CỦA CHÍNH PHIÊN BẢN đó (V2 opinion so V2, V3 opinion so
V3; phiên bản lạ → fail-closed). Opinion V2 đang sống trong production
không bị vô hiệu. Battery:
`test_v3_prompt_frozen_registered_and_erratum`,
`test_shadow_plane_isolation_real_path_stays_v2` (V2 vẫn tiêu thụ
được), `test_go_path_tool_round_then_verdict_union_citations` (V3 tiêu
thụ được).

## Răng cứng tất định cho thang nguồn (backstop, không phải salvage)

`ai_free_research.rumor_domains` (config; mặc định reddit/x/twitter/
facebook/tiktok/quora/4chan): ALLOW mà TOÀN BỘ nguồn trích nằm trên
miền cấp tin đồn và KHÔNG có nguồn thứ hai → INVALID với lý do
"source-quality ladder". Battery ca (b):
`test_battery_b_lone_rumor_allow_refused_by_ladder`.

## Battery bắt buộc (đủ 5 ca, tất cả trong test_free_research.py)

- (a) trang tiêm lệnh → schema/luật giữ nguyên, văn bản tiêm chỉ là dữ
  kiện + được journal nguyên văn:
  `test_battery_a_injection_stays_data_not_command`;
- (b) ALLOW chỉ dựa 1 nguồn diễn đàn → bị từ chối theo thang nguồn;
- (c) bịa URL sau nghiên cứu → bộ lọc union loại, ALLOW rỗng nguồn →
  `.invalid/`;
- (d) hết trần vòng/thời gian → nằm chờ, không ép phán;
- (e) phán ngay 0 vòng công cụ → hợp lệ.

Battery toàn suite xanh 313/313 × 2 lần liên tiếp (sau cùng chạy lại
sau thay đổi đồng hồ số dư).
