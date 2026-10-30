# PLAN — A2-INDEX-DATA-PREP-V1, owner-authorized bootstrap only
Trạng thái: OWNER_BOOTSTRAP_APPROVED; registry/worktree being established, execution NOT_AUTHORIZED. Đây là plan vận hành lane, không sửa R3/spec chiến lược, không GO chạy. Chỉ budget0 scored, S1 sealed, ngân sách0. Owner đã duyệt rõ tạo cycle/worktree chuẩn bị trong chat; xem research/control/A2-INDEX-DATA-PREP-V1/BOOTSTRAP_AUTHORITY.md. Không cần hỏi lại bootstrap; quyền chạy không được suy ra. Không ghi authority bằng cách suy tên file.

## Danh tính bootstrap đã được owner duyệt
cycle_id: A2-INDEX-DATA-PREP-V1
branch: codex/a2-index-data-prep-v1
integration_worktree: /Users/hoangminhlong/my-quantitative/.worktrees/a2-index-data-prep-v1/integration
base SHA đo lúc soạn: 8461fb814a68e2186946817b04d0b097584df1b7 (BASE_ONLY, không phải actual lane HEAD; chưa có branch/worktree).
Lifecycle đăng ký dự kiến PLANNED_NOT_STARTED, asset shared, budget_max0, go_phrase rỗng. Không tạo token GO hoặc kích hoạt từ kế hoạch này.

## Scope và thứ tự
Giữ nguồn pin/owner C4>/RAW/tốc độ(a)/NQM6 ack ở revision_07. Đã có verdict signed R07, chỉ soát prompt chuẩn bị; trước chạy cần registry/plan hợp lệ, identity thực đo, namespace sạch và plan cơ học đã soát.
Trong quyền bootstrap owner đã cấp: lead đặt plan đăng ký cuối trong plans/ và dùng researchctl cycle register qua CAS; tạo branch/worktree đúng tên, copy nguồn nguyên bytes vào input snapshot riêng hoặc đọc nguồn absolute đã pin, dùng env workspace có sẵn (không cài). Ghi manifest/identity đo từ lane, không mượn HEAD root làm lane HEAD. Commit/bootstrap control artifacts chỉ đúng paths, không gom untracked owner; không push/merge. Kiểm doctor targeted, global lock và activity trước dispatch.
Đăng ký chỉ trong phạm vi bootstrap đã được owner duyệt; không register thêm cycle khác. Root vẫn chỉ đọc/viết tài liệu chuẩn bị. Không đụng lane khác hoặc đổi registry thủ công.

## Phân quyền giao việc
Lead một writer, coordinator soát/audit. Khi có lane, probe và count thực hiện tuần tự trong integration worktree với allowed_paths tách research/control/A2-INDEX-DATA-PREP-V1/probe/ và .../count/. Không hai agent ghi cùng worktree. Không tự dispatch agent trước signed mechanical/dispatch review.
Probe output absolute: /Users/hoangminhlong/orca/ai_desk_ibkr/DATA_PROBE_LEAD_R07_20261030/ (output-only subtree, không sửa lane cha).
Count output absolute dự kiến trong lane: /Users/hoangminhlong/my-quantitative/.worktrees/a2-index-data-prep-v1/integration/research/control/A2-SIGNAL-COUNTS-R07-20261030/.
Handoff probe: /Users/hoangminhlong/my-quantitative/.worktrees/a2-index-data-prep-v1/integration/research/control/A2-INDEX-DATA-PREP-V1/handoffs/probe.json
Handoff count: /Users/hoangminhlong/my-quantitative/.worktrees/a2-index-data-prep-v1/integration/research/control/A2-INDEX-DATA-PREP-V1/handoffs/count.json
Handoff schema zcode_orch_v3_handoff@1 theo schema thật workspace, không tự giả giá trị commit/test.

## Kiểm tra namespace và stop
Trước dispatch mỗi task đo pwd/branch/full HEAD/status, registry equality, plan path, allowed_paths, input digests, lock, workers và output namespace. Có output/dirty chưa rõ => STOP, không ghi đè. Probe hết scope thì handoff+coordinator kiểm toán, count mới được giao khi đúng thứ tự/điều kiện. Không backtest P&L, không tính số freeze, không activate/shadow/AI trả phí/orders, không sửa TWS/A1/IBKR/PaperDesk source hoặc journal.

## Bằng chứng kỹ thuật và gate
Plan cơ học: /Users/hoangminhlong/my-quantitative/research/control/LEAD-FOUR-STREAMS-PREP-2026-10-30/revision_08/MECHANICAL_PROBE_PLAN_R08.md và TECHNICAL_SOURCES.md cùng thư mục. Các trần vận hành là đề xuất lead, cần coordinator soát, không giả vendor quota đã đo. Nếu roll/reference/timestamp làm đổi spec/nguồn phải owner quyết riêng.
Kết thúc chuẩn bị có signed review+exact dispatch và nguồn verified mới đủ xét giao chạy; bootstrap không tự là GO thực thi. Không có kết quả dữ liệu mới trong việc soạn plan.
Terminal chuẩn bị: READY_FOR_OWNER_EXECUTION_GATE hoặc BLOCKED_<missing evidence>, không mặc định PASS vì đã có file. Evidence source/registry snapshots/handoff/audit giữ append-only.

## Lệnh bootstrap (chỉ lead)
Đo bootstrap commit chứa plan này trước; researchctl cycle register --cycle A2-INDEX-DATA-PREP-V1 --plan plans/PLAN_a2_index_data_prep_v1.md --branch codex/a2-index-data-prep-v1 --asset shared --lifecycle PLANNED_NOT_STARTED --budget-max 0 --worktree /Users/hoangminhlong/my-quantitative/.worktrees/a2-index-data-prep-v1/integration (head dùng full SHA đo tại bootstrap, không chép tay).
Chỉ sau root registry chứa row đúng path/branch: git -C /Users/hoangminhlong/my-quantitative worktree add -b codex/a2-index-data-prep-v1 /Users/hoangminhlong/my-quantitative/.worktrees/a2-index-data-prep-v1/integration <MEASURED_CONTROL_BOOTSTRAP_SHA>. Placeholder lệnh được thay tự động bằng git rev-parse ở bước thực hiện; không thực thi nguyên văn.
Tạo manifest/dispatch draft cục bộ và commit pathspec, root researchctl update --head về actual lane HEAD rồi commit control-plane riêng. Root plans/CYCLE_REGISTRY.json là canonical; bản registry lịch sử trong lane không tự là authority live. Không cập nhật ledger/outcome/counters vì không chạy kết quả khoa học.
Đầu ra bootstrap cần: clean exact lane identity, root registry HEAD/path/branch match, source digests, manifest allowed/forbidden/targeted checks, handoff paths, status NOT_ISSUED. Plan cơ học vẫn pending coordinator; không dispatch execution.
