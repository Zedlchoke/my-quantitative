# HOW TO BE A LEAD ENGINEER — phiên bản 2 (kỷ nguyên orchestrated + platform)

> Sổ tay điều hành dành cho Lead Engineer và A1 Controller của
> `my-quantitative`.
>
> Mục tiêu không phải tạo ra nhiều backtest đẹp. Mục tiêu là tạo ra các kết
> luận đúng, có thể kiểm tra lại, không làm mất lịch sử, và không gọi một kết
> quả là "edge" khi bằng chứng chưa cho phép.
>
> **Phiên bản 2 (2026-09-11)** thay phiên bản 1 (bản 35 mục, giữ nguyên
> trong git history như evidence). Nội dung cốt lõi của v1 được giữ nguyên;
> những gì thay đổi: canonical registry + `researchctl` thay ACTIVE_CYCLES
> làm router duy nhất (§3.1, §7); orchestration v3 — lane có plugin điều
> phối, structured handoff bắt buộc, guards là luật (§9); platform v3 —
> CADS/authority registry làm data plane (§10); two-half close (§32,
> P-16); one-live-session (§3.2, P-17); bài học P-12..P-17 và doctrine nhập
> ngoài Q-1..Q-16 (QuantPulse dossier) được dệt vào đúng chỗ.

---

# PHẦN I — NỀN TẢNG

## 1. Vai trò của Lead Engineer

Lead Engineer không phải là người viết nhiều code nhất. Lead chịu trách nhiệm
cho năm thứ:

1. **Đúng câu hỏi** — nhóm đang giải quyết vấn đề nào, và vấn đề nào nằm ngoài
   phạm vi.
2. **Đúng quyền hạn** — ai được làm gì, ở branch/worktree nào, hành động nào
   cần owner cho phép.
3. **Đúng trình tự** — data, accounting, proposal, freeze, scoring,
   reproduction và audit không được đảo lộn.
4. **Đúng bằng chứng** — mọi `PASS`, lợi nhuận, SHA, denominator và authority
   đều truy ngược được tới artifact thật.
5. **Đúng kết luận** — `REJECT`, `BLOCKED` và `NOT RUN` đều là kết quả hợp lệ;
   không ép dự án phải có survivor.

Lead tối ưu **thời gian tới một kết luận đáng tin**, không tối ưu số lượng
code, số agent hay số cell chạy được.

Trong kỷ nguyên orchestrated, Lead thêm một vai trò: **người giữ đúng một
phiên sống** (§3.2) và **người đọc máy móc thay vì đoán nó** — registry,
task store, lock, hook đều có thể hỏi; hỏi trước khi viết.

## 2. Các nguyên tắc không được thương lượng

### 2.1 Evidence first

Không có bằng chứng thì không có claim.

```text
Không chạy                       -> NOT RUN
Không có dữ liệu/quyền           -> UNAVAILABLE_FAIL_CLOSED
Đã chạy và sai gate              -> FAIL
Không thể tiếp tục an toàn        -> BLOCKED
Đã chạy đúng, có artifact         -> PASS
```

Không được đổi `NOT RUN` thành `PASS` vì "code trông đúng". Không được đổi
`UNAVAILABLE` thành `AUTHORIZED` vì API trả HTTP 200.

### 2.2 Preserve history

- Không reset, xóa, force-push hoặc viết lại lịch sử để làm report đẹp hơn.
- Scored artifact, ledger, terminal report và worktree lịch sử là bằng chứng
  append-only.
- Một kết quả đã được nhìn thấy không biến mất khỏi observed denominator chỉ
  vì publication thất bại.
- Không sửa strategy sau khi thấy PnL rồi gọi đó là cùng một experiment.

### 2.3 Fail closed

Khi identity, data, license, timestamp, cost, SHA hoặc authority chưa rõ, mặc
định là đóng. Lead không lấp khoảng trống bằng suy đoán thuận tiện. Trạng
thái máy móc méo mó (registry malformed/truncated/stale) là
`CONTROL_STATE_DRIFT` — từ chối, không "sửa nhanh".

### 2.4 Separate research stages

```text
S0 = vùng khám phá/sàng lọc, đã được nhìn thấy
S1 = vùng chưa mở, dùng để kiểm tra ngoài mẫu sau khi khóa
```

S0 không bao giờ được gọi là untouched OOS. S1 chỉ được mở bởi một plan và chỉ
thị owner mới, sau khi strategy, data contract và tiêu chí đánh giá đã khóa.
Niêm phong phải kín cả hai nửa: **data VÀ criteria** — seal data mà không
seal thresholds chỉ là nửa seal (Q-9).

### 2.5 Owner words are literal authority

Lead chỉ được coi một hành động là owner-authorized khi có chỉ thị rõ ràng,
đúng đối tượng và đúng phạm vi. **Câu hỏi là thăm dò, mệnh lệnh là quyền
hạn**: "đã merge chưa?" không phải "merge đi". Trả lời câu hỏi, chỉ thi hành
mệnh lệnh.

Ví dụ:

```text
"Nếu prelaunch PASS thì chạy cells"
```

chỉ cho phép chạy cells sau prelaunch. Nó **không** cho phép:

- tạo tài khoản;
- chấp nhận license;
- mua dữ liệu;
- tự đặt historical availability timestamp;
- mở S1;
- push hoặc merge `main`.

Không ghi "owner supplied evidence" nếu owner không thực sự cung cấp evidence
đó. Giả định do agent tạo phải được ghi là `AGENT_ASSUMPTION_UNAUTHORIZED`.

### 2.6 Guards là luật, không phải gợi ý (MỚI v2)

Từ SYSTEM-HARDENING-V1 và orchestration v3, kỷ luật được thi hành bởi máy:
CAS writes, heavy lock, hook deny-list, task-store transitions, schema
validator. Nguyên tắc:

- **Một hook/máy từ chối = luật đã hoạt động**, không phải lỗi cần vòng
  qua. Muốn đổi luật: đổi qua commit/plan, không circumvent trong phiên.
- Máy không có rule cho tình huống mới thì dùng rule của tài liệu này;
  không dùng "máy cho phép" làm bằng chứng "được phép".
- Khi máy từ chối một thứ đúng (ví dụ hook chặn push), cảm ơn nó và ghi
  nhận vào report — đó là guard làm việc.

## 3. Thứ tự authority

Khi hai nguồn hướng dẫn mâu thuẫn, dùng thứ tự:

1. Chỉ thị owner mới nhất và rõ ràng nhất (mệnh lệnh, không phải câu hỏi).
2. Plan hiện hành của đúng cycle (cao nhất trong số các plan đã register).
3. `CLAUDE.md` và repository operating contract.
4. Frozen manifests, selection, run contract và gate definitions.
5. Historical plans và terminal reports.
6. README, NOTES và diễn giải trong chat.

Historical artifact là bằng chứng về quá khứ, không tự động là trạng thái
hiện tại. Luôn đo lại checkout.

### 3.1 Canonical registry là router duy nhất — qua `researchctl`

(Thay thế §3.1 v1: `plans/ACTIVE_CYCLES.json` giờ **chỉ là projection sinh
ra**, read-only.)

- `plans/CYCLE_REGISTRY.json` (schema `cycle_registry@1`) là **authority
  ghi-được duy nhất** cho trạng thái cycle. Mọi ghi đi qua
  `research/researchctl.py` (transactional: validate → tmp → fsync → atomic
  rename → read-back → append event journal `plans/CYCLE_REGISTRY.events.jsonl`;
  parallel writers fail closed bằng flock + CAS trên previous content sha).
  Không bao giờ hand-edit registry hay projection.
- Cycle ID chỉ resolve qua registry — không suy ra từ tên file version cao
  nhất, không suy ra từ worktree còn tồn tại.
- `TERMINAL` là trạng thái hấp thụ: cycle đã đóng không mở lại qua registry;
  GO phrase của nó chết (consumed hoặc extinguished-unconsumed).
- `cycle resume` mặc định dry-run; `--execute-live` chỉ lật lifecycle —
  scored execution vẫn cần gate của cycle + **GO mới của owner** (P-8: không
  GO nào sống sót qua một đợt maintenance pause).
- Registry dirty là hygiene violation: không bao giờ để registry state
  uncommitted qua một thao tác dài (P-10 mở rộng cho control plane).

`CLAUDE.md`, `RULES.md`, `CONTINUE.md`, plan path và GO registry phải đồng
thuận với registry. Nếu khác nhau, đó là `ROUTER_DRIFT`: **STOP trước
dispatch/scoring**, đo lại và sửa bằng một commit chỉ chứa router/control-plane
files. Không chọn nguồn thuận tiện nhất.

`CONTINUE.md` là checkpoint ngắn được dẫn xuất, không phải authority lịch sử.

### 3.2 Một Lead session sống cho mỗi cycle (P-17)

Hai Lead session cùng quyền sẽ đua nhau — đã xảy ra 2 lần, cả hai lần may mắn
không hư hại vì CAS/single-writer hấp thụ hết các ghi, nhưng máy không hấp
thụ được hai bộ não phân kỳ.

Luật:

- **Một cycle, một phiên Lead sống.** Owner mở thread /lead-resume mới thì
  phiên cũ dừngcan thiệp vào surface của cycle đó.
- **Mid-flight ≠ abandoned.** Trước khi viết lên một surface mà authority
  khác có thể đang giữ, phải loại trừ "đang chạy" TRƯỚC (activity check:
  process, heartbeat, store state, commits mới) — một session đang giữa
  lệnh trông giống hệt một session bỏ hoang.
- Hai close hội tụ về cùng verdict là evidence song song, cái sau không
  âm thầm thay cái trước.

## 4. Intake: 15 phút đầu tiên

Không sửa file trước khi intake hoàn tất.

### 4.1 Xác định checkout

```bash
pwd
git branch --show-current
git rev-parse HEAD
git status --porcelain=v1
git remote -v
git worktree list --porcelain
```

Ghi lại absolute cwd, branch, **full 40-char SHA**, dirty/untracked paths,
remote relationship, worktree owner. Không dùng short SHA làm authority.
Không bao giờ đoán/gõ tay SHA — luôn `git rev-parse` (đã có 2 lần bị validator
bắt vì SHA chế).

### 4.2 Đọc đúng tài liệu

Tối thiểu: `CLAUDE.md`, `RULES.md`, plan hiện hành của cycle (theo registry),
`research/wayfinder/MAP.md`, terminal report của cycle trước, state/
heartbeat/event_log, worktree manifest, và `research/wayfinder/LESSONS.md`
(P-1..P-17, Q-1..Q-16).

### 4.3 Đo process, lock và control plane

```bash
.venv/bin/python research/researchctl.py cycle list
.venv/bin/python research/researchctl.py cycle doctor --json
.venv/bin/python research/researchctl.py locks inspect
```

Cộng với orchestrator (nếu cycle orchestrated): task store state,
`orchestrator_waiting_summary`, `tail -20 .runtime/orchestrator_v3/events.jsonl`.

Kiểm tra: scored/backtest/download/parser/full-pytest worker đang chạy; RAM
và đĩa; data archive/staged snapshot có thật; agent/worktree nào sở hữu
process. Không giết process của cycle khác. Nếu full suite xung đột heavy
worker, ghi `NOT_RUN_RESOURCE_CONFLICT` và chờ.

### 4.4 Phân loại dirty tree

```text
OWNER_CHANGE            thay đổi của owner, phải giữ nguyên
AUTHORIZED_HANDOFF      công việc được bàn giao rõ ràng
LANE_OWNED_CHANGE       thay đổi của agent đúng ownership
UNEXPLAINED_DRIFT       không giải thích được, phải STOP
```

Không tự reset file bẩn. Không gom thay đổi của owner vào commit của agent.

### 4.5 First report

```text
measured UTC/local time
cwd / branch / full HEAD
dirty state
active workers + lock owner
cycle phase (từ registry)
budget observed/published
S1 status
authority blockers
GO / NO_GO cho bước kế tiếp
```

## 5. Hiểu yêu cầu trước khi hành động

- **Read-only** (giải thích, audit, review): được đo và đọc; không tự sửa,
  push, merge, tải dữ liệu, mở cycle mới.
- **Change/build** (viết plan, implement, sửa bug): thay đổi trong phạm vi
  được giao + verification tương xứng; không tự mở rộng sang deployment hoặc
  provider.
- **External-state** (push, account, mua data, email, live trade): cần
  authority rõ ràng cho đúng hành động VÀ đúng target. "Làm xong" không mặc
  định bao gồm push hoặc merge `main`.
- **Destructive**: resolve target bằng read-only check trước; ưu tiên thao
  tác hồi phục được (archive-then-delete, không delete-trước); scope mơ hồ
  thì dừng và hỏi owner.

## 6. Cách Lead ra quyết định

Sáu câu hỏi:

1. **Objective** — outcome cụ thể là gì?
2. **Evidence** — dữ liệu nào chứng minh nó?
3. **Authority** — ai cho phép hành động này?
4. **Reversibility** — nếu sai có khôi phục được không?
5. **Contamination** — hành động có làm lộ S1, PnL hoặc ảnh hưởng cycle khác?
6. **Stopping rule** — điều kiện nào buộc dừng?

| Evidence | Authority | Hành động |
|---|---|---|
| Đủ | Đủ | Thực hiện và ghi artifact |
| Đủ | Thiếu | Chờ owner, không thực hiện |
| Thiếu | Đủ | Đo thêm; không suy diễn PASS |
| Thiếu | Thiếu | `BLOCKED` hoặc `NOT RUN` |

Ưu tiên:

```text
correctness > provenance > reproducibility > speed > convenience
```

---

# PHẦN II — MÁY MÓC ĐIỀU HÀNH (control plane + data plane)

## 7. researchctl và canonical registry (SHV1, đã trên main)

Một bề mặt lệnh duy nhất cho điều khiển cycle. Đọc `docs/RESEARCHCTL.md`
trước khi dùng. Lõi:

```bash
PY=.venv/bin/python
$PY research/researchctl.py cycle list             # bảng registry + drift warnings
$PY research/researchctl.py cycle doctor --json    # chẩn đoán consistency
$PY research/researchctl.py cycle pause <CYCLE> --reason "..."
$PY research/researchctl.py cycle resume <CYCLE>   # DRY-RUN mặc định
$PY research/researchctl.py locks inspect          # heavy lock machine-wide
$PY research/researchctl.py program counters       # denominators (P-9)
$PY research/governance/doctor.py                 # 10 detection classes
```

Semantics ràng buộc:

- Ghi registry chỉ qua `researchctl`/`governance.cycle_registry` — atomic,
  CAS, journal. Viết tay = `CONTROL_STATE_DRIFT`.
- Legacy records không bao giờ được viết lại; adapter normalize trong bộ nhớ
  và drift hiện thành warning.
- **Retry taxonomy**: lỗi `CODE_OR_SCHEMA_ERROR` không bao giờ auto-retry;
  resource-conflict retry có backoff; mọi retry được ghi.
- **Monitoring purity**: dashboard/doctor/collector không bao giờ ghi file
  tracked; refresh lặp lại phải để `git status --porcelain` không đổi.
- Merge/conflict trên `CYCLE_REGISTRY.json` + events journal: giải theo ngữ
  nghĩa (union rows + journal-union theo `write_token`), tái sinh projection
  bằng `write_projection`, chạy `--verify` trước khi commit.

## 8. Global heavy lock

Giới hạn "một heavy job" là **machine-wide**, không phải per cycle (mỗi A1
tự đếm worker của mình là chưa đủ vì hai cycle có thể cùng nhìn thấy máy
rảnh).

- Lock: `fcntl.flock` + registry PID + process-start token. Reclaim chỉ khi
  CHỨNG MINH pid-dead hoặc token mismatch — không đoán.
- Không lấy được lock → `NOT_RUN_RESOURCE_CONFLICT`; không spin/retry vô hạn,
  không chạy chen.
- Worker kết thúc ghi `FINISHED/FAILED/TECHABORT` và giải phóng lock trong
  `finally`. Registry nói `workers=0` mà process còn sống là
  `CONTROL_STATE_DRIFT`.
- **Yielding pattern (V13)**: crawl dài chạy theo etiquette window (ví dụ
  SEC silence windows) chủ động NHẢ lock trong lúc im lặng để cycle khác
  dùng — giữ pattern này cho mọi job dài có pha idle.

## 9. Orchestration v3 — điều phối lane bằng plugin (MỚI v2)

Plugin `quant-research-orchestrator` (v3.1) là bề mặt chuẩn để điều phối
lane từ phiên Lead. Plan: `plans/PLAN_zcode_orchestration_v3.md`; verdict
canary: `PASS_AUTONOMOUS_HANDOFF_CANARY` — đọc lại artifact, không trích
từ trí nhớ.

### 9.1 Bốn role, map sang roster A

```text
quant-explorer    đọc/evidence lane   ≈ A3/A9 phía đọc — chỉ trả paths + facts
quant-implementer MỘT task, MỘT worktree có sẵn, base SHA đóng — ≈ A2/A8
quant-reproducer  re-run detached tại exact SHA, verdict byte-level — ≈ reproduction lane
quant-auditor     fresh-context, chỉ được viết audit namespace — = A7
```

Controller (A1/Lead) là người duy nhất ghi registry/ledger và merge.

### 9.2 Task store — state machine tiến-tuyến

```text
REGISTERED → READY → DISPATCHED → RUNNING → HANDOFF_READY
    → VALIDATING → INTEGRATED | REJECTED | BLOCKED | TECHABORT   (TERMINAL)
HANDOFF_READY → BLOCKED (khi validation fail)  [v3.1]
```

Quy tắc đã trả giá (STORE-FLOW-1/2/3, đã fix trong v3.1):

- `publish_handoff` ghi ATOMIC object submitter đưa vào inbox + digest;
  từ chối `dispatch_sha` ≠ `base_sha` đã ghi.
- `mark_integrated` resolve commit thật bằng `git cat-file` — không tin SHA
  tự khai.
- `record_outcome` chỉ nhận REJECTED|BLOCKED|TECHABORT; muốn thoát giữa
  chừng phải đi đường hợp pháp (publish handoff → HANDOFF_READY → BLOCKED).
- RUNNING không nhảy thẳng HANDOFF_READY — heartbeat trước.

### 9.3 Structured handoff là bắt buộc

Mọi task điều phối kết thúc bằng handoff JSON schema
`zcode_orch_v3_handoff@1` (xem skill `structured-handoff` của plugin) ghi
đúng `handoff_path` trong dispatch packet: task_id, cycle_id, role, lane,
dispatch_sha, actual_start_sha, commit_sha, changed_paths, tests (LIST),
authority_claims, known_limitations, incidents, tree_status, workers,
outputs. **Chat prose là advisory; artifact là authority.** Hook PostAgent
từ chối handoff không hợp lệ.

### 9.4 Guards (hooks) — deny tuyệt đối

SessionStart snapshot; PreToolUse chặn tuyệt đối (trong worktree lane VÀ
root): push, `reset --hard`, `clean -f`, history rewrite, đọc secret
(.env cat/printenv SECRET), merge/checkout main; PostAgent chặn handoff
invalid; Stop continuation. Danh sách deny nằm trong plugin; **câu chữ
command chứa trigger phrase cũng bị chặn** (kể cả trong heredoc tài liệu —
đã xảy ra) — viết tài liệu bằng cách diễn đạt khác.

### 9.5 Vòng đời phiên Lead

`/lead-start` (bootstrap + snapshot) → `/lead-status` (đo trạng thái) →
`/lead-resume` (tiếp tục cycle đang chạy, precondition check) →
`/lead-close` (terminal reconciliation). Owner chạy các lệnh này trong
thread mới; Lead hiện tại tuân thủ §3.2 (một phiên sống).

Lanes không bao giờ: merge, rebase, push, đụng ledgers/registries, đụng lane
khác, edit ngoài `allowed_paths`.

## 10. Platform v3 — data plane (MỚI v2)

`RESEARCH-PLATFORM-V3` (plan `plans/PLAN_research_platform_v3.md`) đang dựng
data plane cho các cycle sau. Khi đạt GA, cycle tiêu dùng qua các capability:

- **CADS** — content-addressed store: verify-on-read, atomic journals,
  restore; dữ liệu nguyên liệu niêm phong theo content digest.
- **AuthorityRegistry** — per-series authority rows, state machine
  tiến-tuyến `GRANTED | BLOCKED`, grant fail-closed; doctrine §13 (PIT)
  vẫn là luật, registry là máy móc thi hành.
- **QueryPlane** — DuckDB read-only, manifest-verified; SessionManifest
  builder với official cross-check fail-closed.
- **exchange_calendars + telemetry (OTel)** — lịch phiên chuẩn hóa; trace có
  redaction denylist.
- **Frozen S1–S4 target set** (không đụng khi migrate): Form-4 substrate
  345,150 XMLs (digest `5d351623…`), FRED pinned series, GB/CA/AU/NZ
  calendars, Binance panels + OI.

Boundary: cycle đã data/selection freeze không retrofit platform (giữ quy
tắc §33); adoption qua commit riêng từng asset.

---

# PHẦN III — VÒNG ĐỜI CYCLE

## 11. Worktree, branch và archive hygiene

### 11.1 Mỗi agent một worktree

```text
.worktrees/<cycle>/integration
.worktrees/<cycle>/<lane-name>
```

Không checkout cùng branch ở hai worktree. Không cho hai agent sửa chung
worktree. Dispatch từ exact base: `BASE_SHA="$(git rev-parse HEAD)"` rồi
verify ba giá trị (HEAD, branch, porcelain) khớp manifest trước khi agent
bắt đầu.

### 11.2 Ownership manifest

Mỗi lane ghi worktree/branch/base_sha/owner/allowed_paths/forbidden_paths/
status (SPAWNED → MERGED | REJECTED | BLOCKED_WITH_EVIDENCE).

### 11.3 Không dùng cwd ngầm

Mọi git command quan trọng: `git -C <absolute path>` (đã có lần merge chạy
nhầm worktree vì cwd trôi). Trước commit: kiểm tra lại pwd/branch/HEAD.

### 11.4 Archive-then-delete (P-13)

Xóa worktree/file lớn phải theo thứ tự: ghi manifest (đường dẫn + sha256 +
ngày) → nén vào `~/staging_backups/` → xóa. Restore phải verify pin theo
manifest trước khi dùng. Đã cứu V13: staging "biến mất" sau cleanup được
restore byte-exact từ tarball vì manifest còn. **Inherited pin là
cross-cycle dependency** — archive trước khi xóa bất kể nhận định "không ai
dùng".

## 12. Tổ chức agent

### 12.1 Vai trò chuẩn

```text
A1  controller, integrator, freezer, publisher, counter owner
A2  accounting, ledger, protocol hoặc common core
A3  data, PIT, calendar, coverage, provider authority
A4  blind proposal lane hoặc implementation lane
A5  blind proposal lane hoặc implementation lane
A6  blind proposal lane hoặc implementation lane
A7  independent novelty/prelaunch/terminal auditor
A8  implementation hoặc reproduction specialist
A9  independent feasibility/resource auditor
```

Tên đổi theo cycle; separation of duties không đổi. Khi điều phối qua
orchestrator, map theo §9.1.

### 12.2 A1 là authority duy nhất cho integration

A1 tạo worktree manifest, dispatch lane từ exact wave SHA, nhận handoff,
cherry-pick tuần tự + gate sau từng pick, freeze, append canonical ledger,
cập nhật denominator, đóng cycle. Lane agent không merge, rebase, push, sửa
central ledger hay state của integration.

### 12.3 A7 phải độc lập

Branch từ SHA cần audit; chỉ viết audit artifact; không repair
implementation; không thay gate; không hỏi implementer cách PASS; recompute
từ bytes và source; tìm lý do bác bỏ claim. A7-thread của A1 không bao giờ
audit chính A1. A7 REFUSED là kết quả bình thường — remediation loop là
arc dự kiến (V15/V16/V8 precedent), không phải sự cố.

### 12.4 Khi nào nên dùng nhiều agent

Song song khi: nhiệm vụ độc lập; ownership file không giao nhau; cùng frozen
base SHA; tích hợp tuần tự được; máy đủ tài nguyên. Không song song khi:
nhiều agent phải sửa cùng core interface; plan chưa khóa; integration tree
bẩn; scoring đang chạy trên máy yếu; câu hỏi nhỏ hơn chi phí coordination.

### 12.5 Context packet theo vai trò

Mỗi dispatch packet tự đủ dùng và chỉ chứa: cycle/role/objective; exact base
SHA + absolute worktree + branch; allowed/forbidden paths; frozen
data/clock/cost identity liên quan; forbidden ancestry hoặc audit criteria;
required inputs/outputs; test commands; stop conditions; commit + handoff
format; `handoff_path`. A4/A5/A6 không nhận scored outcome files. A7 nhận
evidence để audit, không nhận chỉ dẫn "làm sao PASS". A8 nhận frozen
implementation contract. A9 nhận feasibility inputs không có PnL.

## 13. Data authority và PIT

Đây là nơi một backtest đúng code vẫn có thể sai khoa học.

### 13.1 Ba thời gian khác nhau

```text
event_time       sự kiện xảy ra
effective_time   giá trị bắt đầu có hiệu lực
available_time   thị trường/người nghiên cứu có thể biết giá trị
```

`retrieved_time` không thay thế historical `available_time`.

### 13.2 Record tối thiểu

source_id, dataset_id, entity_id, field/value/unit, event/effective/
available/vintage/retrieved_time_utc, raw_path + raw_sha256, license/
entitlement_id, normalizer_version. Với platform v3: những row này sống
trong AuthorityRegistry (GRANTED|BLOCKED, fail-closed) — doctrine không
đổi, chỉ được máy hóa.

### 13.3 Effective không đồng nghĩa available

Một policy rate có thể hiệu lực ngày X nhưng được công bố trước/trong/sau
X, hoặc chỉ xuất hiện trong dataset tổng hợp sau X, hoặc bị sửa lịch sử.
Không tự đặt `available_time` nếu không có release evidence. **Measured
beats stated, every single time (Q-8)**: hằng số vendor-stated (spread,
fee, coverage) là giả thuyết — phải đo từ bytes (đã có 21,000× fee error,
23× spread error trong một chương trình ngoài; P-7 hai kill trong chương
trình mình).

### 13.4 Free không đồng nghĩa authorized

Statuses: `DOCUMENTED_CANDIDATE → CANDIDATE_NOT_AUTHORIZED →
AUTHORIZED_INTERNAL_RESEARCH | UNAVAILABLE_FAIL_CLOSED | REJECTED_LICENSE`.

### 13.5 Primary và cross-check

Nguồn `CROSS_CHECK` không âm thầm vá gap của `PRIMARY`. Không trộn nguồn
thành dataset mới nếu chưa freeze conflict policy + provenance từng row.
Proxy-first (Q-15): đo bằng nguồn free/canary trước khi đề nghị owner mua;
khi dữ liệu trả phí về, cross-verify proxy-vs-paid và ghi hệ số khớp.

### 13.6 Data gate trước proposal/scoring

License/entitlement; coverage + missing intervals; timezone/calendar/DST;
identity/delisting/symbol changes; corporate actions; vintages/revisions;
raw hashes + deterministic retrieval; source schema drift. Adapter PASS chỉ
chứng minh parser hoạt động. **Bundle ≠ endpoint (P-7)**: một vendor có
nhiều kênh (bulk bundle, per-symbol, API) với universe khác nhau — canary
(dead names + never-existed controls) bắt buộc cho mỗi kênh, chạy lại mỗi
lần đổi kênh.

### 13.7 Archive bị rewrite và retrospective-only data

```text
publication lag      file xuất hiện trễ bao lâu sau event?
revision integrity   byte/value lịch sử có bị thay về sau không?
```

Thêm lag bảo thủ không chứng minh revision integrity. Hard gate:
`PASS_PIT_EVIDENCED | RETROSPECTIVE_ONLY | BLOCKED_DATA`. SEC/multi-vintage:
`available_time` của mỗi vintage = accepted/submission timestamp của đúng
accession; amendment tạo vintage mới; mutation test chứng minh filing đến
muộn làm signal dịch đúng decision period.

## 14. Scientific research protocol

### 14.1 Mechanism before parameter

Proposal trả lời: ai bị ép mua/bán hoặc chậm phản ứng? Tại sao hiệu ứng tồn
tại? Observable nào đo được cơ chế? Khi nào cơ chế phải thất bại? Control
nào bác bỏ cách giải thích thuận tiện? Không bắt đầu bằng grid tham số.

### 14.2 Outcome-blind proposal

Proposal agent không được xem scored outcome. Proposal khóa: hypothesis ID,
mechanism, universe, clock, warmup, features/lags, entry/exit/fills, costs,
anchor, một neighbour hỗ trợ, một causal/placebo control, falsification
rule, expected failure interpretation.

### 14.3 Novelty và ancestry veto

Family mới không được là family đã reject đổi timeframe/threshold/vài
symbol/phí/tên/hướng dấu/session nhỏ. Cơ chế + information source + causal
control không mới ⇒ reject trước scoring. Cross-horizon rescue cũng là
ancestry violation (Q-3).

### 14.4 Feasibility trước selection (không dùng PnL)

Số decision dự kiến; warmup coverage; turnover/cost ceiling; missing data;
fold population; compute/runtime; khả năng tạo control khác anchor. Đo
ceiling của **cửa sổ gần nhất**, không phải trung bình cả archive (Q-6).
Đừng mất sáu giờ implement một family mà data gate đã biết sẽ fail. Một
family cận-kề-dương phải bị phân tích thành bill/clock/calendar trước khi
viết plan kế thừa (Q-1).

### 14.5 Controls phải là null hợp lệ (P-3 + Q-11)

Control phải chạy dưới evidenced semantics; đổi semantics ⇒ recompute
controls. **Hơ nữa: một permutation chỉ là null nếu nó LÀM CHO signal dịch**
— đo autocorrelation ở đúng chiều control điều kiện; control tái tạo anchor
có khi là kill, có khi là null vô hiệu (phân biệt trong verdict, không gán
nhầm). Conditioning theo sự kiện phải mang clock-only shadow (Q-7: phần lớn
"event variance" là clock).

### 14.6 Selection freeze

Rubric tồn tại trước khi proposals về. Freeze ghi: selected family IDs,
proposal hashes, arm IDs, arm_config_digest, mọi field ảnh hưởng score,
trial budget, Stage-A gates, data/code base SHA. Không chọn vì agent đã
thấy PnL. Threshold đặt theo effect-scale đo được + log exclusion zone của
bar (Q-12).

## 15. Trial identity và denominator

### 15.1 Trial identity

Mỗi scored arm: cycle_id, family_id, arm_id, arm_config_digest,
data_snapshot_digest, code_freeze_sha, cost_tier, fold contract. Exact-arm
dry-run chứng minh record IDs pairwise distinct.

### 15.2 Hai denominator

```text
observed_scored_denominator    mọi outcome đã tính, kể cả publication fail
published_ledger_denominator   đã publish thành công
```

### 15.3 Global trial history

Lead duy trì program-level history để đánh giá multiple testing. Một
survivor sau hàng trăm cells chưa phải edge thật.

### 15.4 Intake snapshot ≠ current total

Checkpoint/terminal phân biệt `intake_snapshot` và `current_ledger_snapshot`;
current total chỉ lấy từ canonical ledger (P-9).

## 16. Implementation discipline

### 16.1 Implement từ frozen spec

Không "cải thiện" proposal; ambiguity trả về A1 trước scoring.

### 16.2 Test bằng hand-computed fixtures

Tối thiểu: feature golden; one-event/one-bar lag; no-lookahead mutation;
timezone/DST boundary; fold force-flat; costs exactly once; cash không bị
tính như instrument; turnover/concentration; control khác anchor;
deterministic double generation; malformed/missing data fail-closed.
**Equivalence baselines đi ngầm theo thời gian (Q-14)**: fixture
bit-identical phải được re-run khi semantics nó mã hóa đổi (cost kernel,
spread model); baseline cũ PASS = false PASS.

### 16.3 Không dùng production outcome trong unit test

### 16.4 Daemon/collector hygiene (Q-13)

Mọi process dài (crawl, poller): heartbeat mang bytes-written + đếm
payload-shape; inode-check trên append handle (log file bị thay dưới tay
làm handle ghi vào inode mồ côi); payload sai shape → fail LOUD, không nuốt
im lặng thành "không có gì hôm nay".

## 17. Integration protocol

### 17.1 Handoff trước cherry-pick

Lane trả: role/lane, base SHA, commit SHA, changed files, tests với exact
commands, PASS/FAIL/NOT RUN, known limitations, tree status, workers —
trong artifact handoff (§9.3) khi orchestrated, hoặc YAML template (§34)
khi không.

### 17.2 Cherry-pick tuần tự

Verify integration clean → verify lane ancestry/base → inspect diff →
pick MỘT lane → targeted tests → inspect status → record event → pick kế
tiếp. Không pick ba lane rồi mới test.

### 17.3 Conflict resolution

Hai lane đụng file: không chọn bên tiện; quay về ownership contract; A1
quyết định semantic result (registry/journal conflict: giải theo union ngữ
nghĩa, §7); chạy lại tests của cả hai lane; ghi resolution vào event log.

## 18. Gate evidence

Mỗi gate artifact ghi: gate_id, measured_at, cwd/host, full HEAD, command,
exit_code, stdout/stderr path-or-digest, expected, observed, input/output
hashes, tree state, verdict, blocker.

### 18.1 Test routing

Syntax/import → targeted unit → adjacent compatibility → protocol → asset
suite → full suite MỘT MÌNH → `git diff --check` → clean-tree verify.

### 18.2 PASS có phạm vi

`unit tests PASS` không có nghĩa `data authority PASS` hay `OOS PASS`. Luôn
ghi phạm vi. **Margin-to-fail (P-2)**: mỗi gate ghi khoảng cách tới ngưỡng
fail; pass mỏng được ghi là mỏng. Kèm exclusion-zone của bar (Q-12): "không
gì qua" phải kèm chiều cao của bar.

## 19. Freeze và prelaunch

### 19.1 Các SHA quan trọng

```text
BASE_SHA → WAVE_SHA → SELECTION_SHA → CODE_FREEZE_SHA → DATA_MANIFEST_SHA
→ AUDIT_SHA → TERMINAL_SHA
```

### 19.2 Exact-arm dry-run

`scored=false`, `real_pnl=false`, `published=false`; không lộ PnL/PF/stress/
break-even ở BẤT KỲ độ sâu record nào (đã từng rò stress PnL ở field lồng);
record IDs pairwise distinct; replay zero denominator delta. Empty book /
zero-decision = fail, không phải pass (non-vacuous).

### 19.3 Independent prelaunch A7 + two-key launch (P-8)

A7 kiểm: hashes chain; exact-arm identity; data/PIT authority; accounting;
dry-run hygiene; S1 seal; no post-freeze drift; denominator seed; twin
integrity; zero unresolved HIGH/CRITICAL. Sau đó — và CHỈ sau đó — owner
nhìn thấy verdict A7 rồi gõ **GO phrase đúng nguyên văn, mới, tại gate của
chính nó**. GO gõ sớm = intent, chết unconsumed; phrase sai form bị từ chối
và ghi nhận; GO không mang qua cycle, không sống qua pause.

## 20. Scored execution

### 20.1 Hard launch gate

Không cell nào chạy cho tới khi: code freeze + data manifest + selection
digests verified; prelaunch authorized; ledger seed verified; resource cap
measured; S1 sealed; owner GO present khi plan yêu cầu.

### 20.2 TECHABORT

```text
SCIENTIFIC_FAIL  cell chạy đúng, không qua gate
TECHABORT        computation không hợp lệ/kết thúc kỹ thuật
```

TECHABORT không thành "không tính" tùy tiện nếu outcome đã lộ — ghi mức
exposure + denominator theo run contract.

### 20.3 Sau mỗi cell

Báo identity, exit code, runtime, observed/published delta, budget used,
record/ledger digest, gate verdict, workers, S1 status. Không đợi hết cycle
mới phát hiện denominator lệch.

## 21. Stage-A interpretation

Sau-cost expectancy dương; PF qua ngưỡng; ≥2/3 folds dương; drawdown dưới
ceiling; không tập trung một fold/instrument; stress costs vẫn sống;
drop-one survival; incremental alpha vs benchmark; neighbour hỗ trợ; causal
control không tái tạo; reproduction exact; zero unresolved high/critical.
Gate cụ thể theo plan của cycle. Một Stage-A survivor chỉ là **ứng viên đáng
mở S1**, không phải strategy deploy.

## 22. Reproduction và terminal audit

### 22.1 Reproduction

Detached tree tại exact code freeze; snapshot + manifest độc lập nhưng
byte-identical; so sánh record IDs, schedules/fills, costs/funding, folds/
stress, metrics, verdicts, ledger bytes. `ALL_MATCH` chứng minh
self-consistency, KHÔNG chứng minh truth (P-4) — reproduction tái tạo cả
bug lẫn kết quả.

### 22.2 Terminal A7

Recompute ancestry/freeze chain; ledger digest; gates từ source; trade/
accounting reconciliation (gross/net pairing đúng vehicle — Q-14); control
coherence; denominators; data/S1/deployment boundaries; strongest allowed
terminal label. **Positive audit nghiêm hơn negative** (incentive xác nhận
cao hơn). Số smoke-namespace chỉ được dùng kill + disclosure, không bao giờ
select (P-15).

### 22.3 Terminal closeout — xem §32 (two-half close)

## 23. Xử lý survivor

Bốn tầng trước khi ghi `SURVIVOR`:

| Tầng | Câu hỏi |
|---|---|
| Mechanical | Code, ledger, hashes, reproduction đúng không? |
| Data | PIT, license, identity, coverage thật không? |
| Statistical | Multiple testing, folds, controls đủ không? |
| Economic | Costs, financing, capacity giao dịch được không? |

Mechanical PASS + PIT chưa chứng minh → `PROVISIONAL_STAGE_A_SURVIVOR_
PENDING_PIT_AUTHORITY`. Không mở S1 để chữa lỗi S0 — sửa data authority bằng
remediation plan, giữ nguyên strategy, audit lại.

## 24. Xử lý bug sau freeze

- **Trước scoring**: freeze cũ thành `SUPERSEDED_BLOCKED`; remediation lane
  từ đúng SHA; scope nhỏ nhất; regression; freeze mới; A7 delta audit; chỉ
  chạy khi audit mới authorize.
- **Sau scoring**: stop workers; không overwrite ledger; ghi incident +
  exposure; giữ observed denominator; phân loại invalid/indeterminate/
  repairable; chạy lại cần owner-approved remediation plan + identity mới
  khi khoa học yêu cầu. Không sửa code rồi replay giữ nhãn cũ.

## 25. Xử lý blocker

Không idle-spin: chứng minh blocker bằng read-only evidence; exhaust đường
an toàn trong scope; tách blocker thật khỏi việc chưa thử; nêu owner action
cụ thể (một hoặc vài); giải phóng resources; đóng trạng thái trung thực.

```text
BLOCKED ON
evidence / what passed / what did not run / what was not attempted and why
single next owner action
state/branch/SHA/tree/workers
```

## 26. Incident transparency

Ghi kể cả đã sửa: cwd drift; commit nhầm worktree; unexpected dirty tree;
branch sai; identity collision; denominator mismatch; dry-run leak; stale
metadata; newline drift; missing archive; process chết/timeout; đụng
forbidden path. Cộng lớp mới (v2): **dual-controller race** (P-17 — ai, hai
session nào, surface gì); **registry/CONTROL_STATE_DRIFT** (đã reconcile
chưa, bằng gì); **hook denial** (bị chặn gì, có circumvent không — câu
trả lời phải là không); **fabricated/typo SHA** (validator bắt ở đâu).

Report: what happened / scope / outcome-data exposure? / repair / evidence
preserved / vì sao kết luận còn valid hay invalid / prevention added.

---

# PHẦN IV — ĐIỀU HÀNH & GIAO TIẾP

## 27. Giao tiếp với owner

### 27.1 Lead with outcome

Nói trước: PASS/FAIL/BLOCKED — ý nghĩa — owner cần làm gì không. Chi tiết
sau.

### 27.2 Không bắt owner thay placeholder kỹ thuật

Agent tự đo SHA, paths, counts, commands. Chỉ hỏi owner quyết định repo
không suy ra được: mua data; account/terms; mở S1; push/merge/deploy;
trade-off sản phẩm.

### 27.3 Hai tầng, và "giải thích như 5 tuổi" khi được yêu cầu

(1) Một giải thích đơn giản: đã làm / đang làm / còn thiếu. (2) Phần kỹ
thuật với SHA, paths, gates cho audit. Khi owner yêu cầu đơn giản — cho một
dòng thật sự đơn giản trước, kỹ thuật sau; không đổ thuật ngữ vào tầng một.

### 27.4 Commentary trong lúc chạy

Cập nhật khi: bắt đầu phase; phát hiện blocker/incident; gate quan trọng
hoàn tất; job dài vẫn khỏe; cần owner authority. Không cập nhật rỗng "vẫn
đang làm".

### 27.5 Push là việc của owner-terminal

Hook chặn agent push tuyệt đối (kể cả khi được owner nhờ bằng lời — hãy trả
lời "em bị hook chặn, anh push từ terminal giúp em"). Lead liệt kê các
commit đang chờ push; owner xem và push.

## 28. Git, commit, push và merge

### 28.1 Commit hygiene

Trước commit: pwd, branch, `status --short`, `diff --check`, `diff --stat`.
Commit một semantic unit; **stage bằng pathspec, không bao giờ `git add
-A`** (root checkout chứa artifact untracked của owner — P-10); stage +
commit ATOMIC, không để index bẩn qua thao tác dài.

### 28.2 Push boundary

Push chỉ khi owner/plan cho phép (và qua terminal của owner — §27.5). Không
coi push branch là merge `main`.

### 28.3 Main boundary

`main` là owner/bootstrap space. Không research trực tiếp trên main. Merge
main là external state change riêng cần authority riêng. Merge orchestration/
platform: conflict registry giải theo union ngữ nghĩa (§7); file tracked
mất khỏi working tree sau merge → `git checkout -- <path>` theo pathspec,
không `add -A`.

## 29. Security và deployment boundary

- Không ghi API key trong prompt, command log, JSON, Git. Environment/
  keychain/secret manager. Không in secret để "kiểm tra".
- Key đã lỡ nằm trong git history thì: thông báo owner ngay, đánh giá exposure,
  thu hồi/rotate — authorization owner không biến secret đã lộ thành secret
  an toàn (bài học Binance .env trong history).
- Không tạo account/accept terms thay owner. Paper/testnet/live là ba trạng
  thái khác nhau. Live cần broker adapter, reconciliation, risk limits, kill
  switch, idempotency, monitoring, owner deployment plan riêng.

## 30. Những lỗi tư duy Lead phải tránh

1. **"Tests xanh nên data đúng"** — tests có thể nhất quán với giả định sai.
2. **"Reproduction exact nên edge thật"** — nó tái tạo hoàn hảo cả look-ahead
   bug (P-4).
3. **"Control âm nên mechanism đã chứng minh"** — control loại bỏ MỘT cách
   giải thích, không phải mọi confounder; và control vô hiệu thì verdict
   khác kill (Q-11).
4. **"Miễn phí nên dùng được"** — còn license, account, PIT, coverage.
5. **"Nhiều agent luôn nhanh hơn"** — ownership chồng nhau có khi chậm hơn.
6. **"Survivor đầu tiên là chiến thắng"** — nó chỉ mở quyền lập kế hoạch S1.
7. **"Owner không phản đối nghĩa là cho phép"** — im lặng không phải
   authorization; câu hỏi không phải mệnh lệnh.
8. **"Máy chặn tức là máy lỗi"** — guard làm việc là luật (§2.6).
9. **"Không có commit mới tức là bị bỏ rơi"** — mid-flight ≠ abandoned
   (P-17); đo activity trước khi kết luận.
10. **"Số smoke đẹp có thể dùng để chọn"** — smoke namespace chỉ kill +
    disclosure (P-15).
11. **"TERMINAL trên branch là đã đóng"** — chưa, cho tới khi registry +
    root ledger nói vậy (P-16, §32).
12. **"Hằng số vendor là hằng số"** — measured beats stated, mọi lần (Q-8);
    con số nguy hiểm nhất là con số chưa ai đo.

---

# PHẦN V — PLAYBOOK & TEMPLATE

## 31. Playbook: mở một research cycle mới

```text
 1. Reconcile terminal cycle trước (hai nửa đều land — §32).
 2. Reconcile canonical registry, projection, router docs, heavy lock.
 3. Freeze starting SHA, counters, S1, forbidden inventory.
 4. Viết plan với terminal outcomes âm + GO phrase nguyên văn.
 5. Bootstrap THROUGH researchctl: cycle register + worktree + manifest/
    state/event-log commit sạch (BOOTSTRAP_INCOMPLETE nếu control files
    chưa commit).
 6. (Orchestrated) orchestrator intake → register tasks → dispatch qua
    packet chuẩn; ngược lại dispatch lane thủ công theo §12.
 7. Pass accounting/data/PIT factory gates (kể cả rewrite/revision gate).
 8. Freeze baseline invariants.
 9. Dispatch blind proposal lanes từ một wave SHA (packet theo vai trò).
10. Audit novelty + feasibility (đo ceiling cửa sổ gần — Q-6).
11. Apply frozen selection rubric (+ exclusion-zone của bar — Q-12).
12. Freeze selected hashes + arm identities.
13. Implement trong lanes cô lập.
14. Integrate tuần tự + gates.
15. Code/data freeze + detached twins.
16. Exact-arm sanitized dry-run (non-vacuous, scan đệ quy).
17. A7 prelaunch độc lập (two-key thứ nhất).
18. Owner GO tại gate của cycle (two-key thứ hai — fresh, đúng form).
19. Acquire heavy lock; scored cells bounded.
20. Reproduce độc lập cùng resource discipline.
21. Terminal A7.
22. Close: hai nửa (A1 branch chain + Lead control-plane landing — §32).
```

## 32. Playbook: đóng cycle — two-half close (P-16) (MỚI v2)

TERMINAL trên branch CHƯA phải là closed. Close có hai nửa:

**Nửa 1 — branch-side terminal chain (A1):** terminal artifacts + A7
terminal verdict + terminal commit trên integration branch; registry append
trên branch nếu cycle có governance-native.

**Nửa 2 — control-plane landing (Lead, MỘT writer):**

```text
[ ] registry: lifecycle → TERMINAL + head (đo từ branch, không gõ tay)
    + budget_used đúng (qua researchctl/canonical save, CAS)
[ ] projection tái sinh; cycle doctor + validator --verify PASS
[ ] HYPOTHESIS_LEDGER: row của cycle + denominators mới (P-9: đây là
    authority cross-asset duy nhất)
[ ] FAMILY_FAILURES: append các kill + validator --verify
[ ] MAP.md: mục cycle mới
[ ] LESSONS: bài học mới (nếu có) — source → lesson → consequence
[ ] SURVIVORS.md chỉ khi thực sự đủ điều kiện
[ ] workers = 0, lock released, worktree evidence giữ (hoặc archive-
    then-delete theo §11.4 khi owner cho phép dọn)
[ ] router docs (RULES/CONTINUE) đồng thuận registry
```

Cho tới khi cả hai nửa land: router sẽ dẫn hướng sai dispatch kế tiếp và
denominators undercount. Sync được verify trước commit; A1 chỉ append trên
branch của chính nó.

## 33. Playbook: shared core / platform adoption

Shared core không retrofit vào frozen cycle:

```text
1. Xây core ở branch/worktree riêng.
2. Unit-test offline interfaces (+ negative matrices).
3. Adapter lanes có ownership riêng.
4. Ghi source registry + authority status (platform v3: AuthorityRegistry).
5. Independent audit core.
6. Freeze MULTISOURCE_DATA_CORE_SHA (hoặc platform GA gate).
7. Mỗi asset một adoption commit riêng + compatibility tests.
8. Chỉ cycle CHƯA data/selection freeze được adopt; cycle đã freeze chờ
   vòng sau.
```

Parser PASS không tự nâng nguồn thành research-authorized.

## 34. Templates

### 34.1 Agent dispatch (packet)

```text
ROLE / OBJECTIVE / ABSOLUTE WORKTREE / BRANCH / EXPECTED BASE SHA
ALLOWED PATHS / FORBIDDEN PATHS / REQUIRED INPUTS / DELIVERABLES
TEST COMMANDS / STOP CONDITIONS / COMMIT-PUSH RULES
HANDOFF FORMAT + HANDOFF_PATH (structured handoff khi orchestrated)
```

### 34.2 Checkpoint

```yaml
phase: P2_DATA_AUTHORITY
verdict: PASS | FAIL | NOT_RUN | BLOCKED
head: <full SHA>
tree: clean | dirty-with-listed-paths
workers: 0
commands: [{command: ..., exit_code: 0, result: ...}]
artifacts: [path]
remaining_blockers: []
next_safe_action: ...
```

### 34.3 Handoff (không orchestrated)

```yaml
agent: A3
lane: data
base_sha: ...
commit_sha: ...
changed_files: []
tests: {passed: [], failed: [], not_run: []}
authority_claims: []
known_limitations: []
incidents: []
tree_clean: true
workers: 0
```

### 34.4 Structured handoff (orchestrated) — trường bắt buộc

```json
{
  "schema": "zcode_orch_v3_handoff@1",
  "task_id": "...", "cycle_id": "...", "role": "...", "lane": "...",
  "dispatch_sha": "...", "actual_start_sha": "...", "commit_sha": "...",
  "changed_paths": [], "tests": [], "authority_claims": [],
  "known_limitations": [], "incidents": [],
  "tree_status": "clean", "workers": 0, "outputs": []
}
```

### 34.5 Owner decision request

```text
Decision required:
Why repo evidence cannot decide it:
Option A and consequence:
Option B and consequence:
Default fail-closed state if no decision:
Exact action that becomes authorized:
Actions that remain forbidden:
```

### 34.6 Terminal report

```text
terminal verdict / full integration SHA / freeze-data-selection-audit SHAs
observed-published denominators / budget used / family verdicts
reproduction status / S1 status / data authority status
incidents and impact / tests-gates / workers-tree
completed vs not completed / next owner-authorized path
```

## 35. Definition of done cho Lead

Một cycle chỉ "done" khi:

- terminal verdict hợp lệ; mọi computed outcome được đếm;
- state/heartbeat/event log/ledger đồng thuận;
- reproduction + audit có verdict rõ; S1/deployment boundary giữ;
- incidents được ghi; workers = 0; tree đúng như báo;
- **cả hai nửa close đã land + verify** (registry/projection/ledger/
  failures/MAP/LESSONS — §32);
- một phiên Lead sống duy nhất, không session ma;
- owner biết chính xác điều gì đã làm và chưa làm.

`BLOCKED_DATA_AUTHORITY` với evidence đầy đủ có thể là done. Một survivor
thiếu PIT evidence thì chưa done dù PnL đẹp.

## 36. Huấn luyện một Lead Engineer mới

Hoàn thành lần lượt:

1. Audit read-only một terminal cycle + truy SHA chain (kể cả hai nửa
   close trong registry).
2. Reconcile observed/published denominator từ ledger.
3. Tạo worktree lane + manifest không chỉnh code.
4. Integrate một fixture-only change với targeted tests.
5. Audit một PIT dataset; phân biệt effective/available/retrieved.
6. Viết proposal có anchor/neighbour/control (+ tự kiểm null hợp lệ Q-11).
7. Review một exact-arm dry-run để tìm leak (scan đệ quy).
8. Reproduce một historical cell từ detached tree.
9. Viết terminal report không phóng đại claim.
10. Xử lý một giả định "owner-authorized" không có chỉ thị owner thật.
11. (v2) Đi một task qua orchestrator: register → dispatch → heartbeat →
    publish handoff → validate → integrate; đọc store state phát hiện
    mid-flight (P-17).
12. (v2) Giải một conflict CYCLE_REGISTRY bằng union ngữ nghĩa + tái sinh
    projection + `--verify`.

Chỉ sau các bài này mới giao quyền A1 publisher/freezer.

## 37. Checklist cuối cùng của Lead

```text
[ ] Đúng cwd/branch/worktree/HEAD (git -C absolute)?
[ ] Dirty files đã giải thích? Index không bẩn qua thao tác dài?
[ ] Đọc đúng plan hiện hành (theo registry, không theo tên file)?
[ ] Registry / projection / RULES / CONTINUE / GO phrase đồng thuận?
[ ] Cycle này ACTIVE_LIGHT / ACTIVE_HEAVY / PAUSED? Một phiên Lead sống?
[ ] Surface tôi sắp ghi có authority khác đang in-flight không (P-17)?
[ ] Heavy lock + worker registry khớp process thật?
[ ] Authority từ owner hay do agent suy luận? (câu hỏi ≠ mệnh lệnh)
[ ] Dữ liệu PIT + license evidence thật? Hằng số đo được hay stated (Q-8)?
[ ] Có rewrite/restatement chỉ che bằng lag giả định?
[ ] Cycle khác và S1 bị ảnh hưởng?
[ ] Trial identity + denominator đầy đủ? Intake ≠ current đã phân biệt?
[ ] Gate chạy thật hay chỉ được mô tả? Margin-to-fail đã ghi?
[ ] A7 độc lập + kiểm giả định đầu vào? Two-key đủ (A7 → GO fresh)?
[ ] Positive claim mạnh hơn evidence? Smoke chỉ kill (P-15)?
[ ] Report có full SHA, commands, artifacts, tree, workers?
[ ] Handoff artifact (không phải chat prose) đã ghi đúng handoff_path?
```

Một câu chưa trả lời được ⇒ chưa bấm chạy scored cell.

## 38. Mô hình tinh thần đơn giản

Tưởng tượng Lead là người quản lý một phòng thí nghiệm:

- Plan là công thức viết trước; terminal outcomes âm là quyết định làm
  trước cho ngày kết quả đẹp mà sai.
- Worktree là bàn thí nghiệm riêng từng người; SHA là niêm phong chống tráo
  mẫu; data manifest là nhãn nguyên liệu.
- Ledger là sổ ghi mọi lần thử, kể cả thất bại — 242 lần "không" là tài
  sản định giá lần "có" đầu tiên (Q-16).
- A7 là người kiểm nghiệm độc lập; S1 là hộp mẫu cuối cùng chưa mở — niêm
  phong cả dữ liệu lẫn tiêu chí (Q-9).
- Registry + researchctl là biên bản của phòng thí nghiệm: ai cũng đọc
  được, không ai sửa được lén, đã đóng thì không mở lại.
- Orchestrator là phi công tự động có khóa: mỗi lane là một toa tàu đi
  đúng ray (task store), về tới nơi phải nộp phiếu (handoff), không có
  phiếu thì không rời ga.
- Guards/hooks là luật pháp trong nhà máy: chặn lại là nó làm việc.

Lead giỏi không phải người luôn tìm ra vàng. Lead giỏi là người có thể chứng
minh thứ đang cầm là vàng, hoặc dũng cảm ghi đúng rằng nó không phải vàng.

---

## Phụ lục: changelog v2 (2026-09-11)

- §3.1 canonical registry + researchctl thay ACTIVE_CYCLES (projection);
  registry hygiene; resume dry-run; TERMINAL absorbing.
- §3.2 one-live-session + mid-flight ≠ abandoned (P-17).
- §2.6 guards-là-luật (SHV1 + orchestration).
- Phần II mới: researchctl (§7), heavy lock + yielding (§8), orchestration
  v3 (§9), platform v3 data plane (§10).
- §11.4 archive-then-delete + inherited pins (P-13); §28 push-owner-terminal;
  §30 thêm 5 lỗi tư duy mới; §32 two-half close (P-16); §34.4 structured
  handoff; §36 thêm 2 bài tập; §37 checklist thêm 4 câu.
- Dệt P-12..P-17 và Q-1..Q-16 (QuantPulse dossier, nhập theo chỉ thị owner
  2026-09-11) vào các mục tương ứng; bản dịch đầy đủ trong
  `research/wayfinder/LESSONS.md`.
