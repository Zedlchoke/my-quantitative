# HOW TO BE A LEAD ENGINEER

> Sổ tay điều hành dành cho Lead Engineer và A1 Controller của
> `my-quantitative`.
>
> Mục tiêu không phải tạo ra nhiều backtest đẹp. Mục tiêu là tạo ra các kết
> luận đúng, có thể kiểm tra lại, không làm mất lịch sử, và không gọi một kết
> quả là “edge” khi bằng chứng chưa cho phép.

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

Lead tối ưu **thời gian tới một kết luận đáng tin**, không tối ưu số lượng code,
số agent hay số cell chạy được.

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

Không được đổi `NOT RUN` thành `PASS` vì “code trông đúng”. Không được đổi
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
định là đóng. Lead không lấp khoảng trống bằng suy đoán thuận tiện.

### 2.4 Separate research stages

```text
S0 = vùng khám phá/sàng lọc, đã được nhìn thấy
S1 = vùng chưa mở, dùng để kiểm tra ngoài mẫu sau khi khóa
```

S0 không bao giờ được gọi là untouched OOS. S1 chỉ được mở bởi một plan và chỉ
thị owner mới, sau khi strategy, data contract và tiêu chí đánh giá đã khóa.

### 2.5 Owner words are literal authority

Lead chỉ được coi một hành động là owner-authorized khi có chỉ thị rõ ràng,
đúng đối tượng và đúng phạm vi.

Ví dụ:

```text
“Nếu prelaunch PASS thì chạy cells”
```

chỉ cho phép chạy cells sau prelaunch. Nó **không** cho phép:

- tạo tài khoản;
- chấp nhận license;
- mua dữ liệu;
- tự đặt historical availability timestamp;
- mở S1;
- push hoặc merge `main`.

Không ghi “owner supplied evidence” nếu owner không thực sự cung cấp evidence
đó. Giả định do agent tạo phải được ghi là `AGENT_ASSUMPTION_UNAUTHORIZED`.

## 3. Thứ tự authority

Khi hai nguồn hướng dẫn mâu thuẫn, dùng thứ tự:

1. Chỉ thị owner mới nhất và rõ ràng nhất.
2. Plan hiện hành của đúng cycle.
3. `CLAUDE.md` và repository operating contract.
4. Frozen manifests, selection, run contract và gate definitions.
5. Historical plans và terminal reports.
6. README, NOTES và diễn giải trong chat.

Historical artifact là bằng chứng về quá khứ, không tự động là trạng thái hiện
tại. Luôn đo lại checkout.

### 3.1 Active-cycle registry là router duy nhất

Không suy ra cycle đang chạy chỉ từ tên file có version cao nhất. Một plan có
thể đã được viết nhưng vẫn là `PLANNED_NOT_STARTED`; một worktree có thể tồn tại
nhưng đang `PAUSED_RESOURCE_CONFLICT`; một version thấp hơn có thể chỉ còn là
evidence lịch sử.

Repository phải có một registry máy đọc được, mặc định:

```text
plans/ACTIVE_CYCLES.json
```

Mỗi asset/cycle tối thiểu ghi:

```json
{
  "cycle_id": "CRYPTO_V15",
  "asset": "crypto",
  "plan": "plans/PLAN_crypto_v15.md",
  "status": "ACTIVE_LIGHT",
  "phase": "D1_PROPOSALS",
  "integration_worktree": "/absolute/path",
  "branch": "orca/v15-integration",
  "head": "40-char-sha",
  "budget_used": 0,
  "budget_max": 6,
  "go_phrase": "GO CRYPTO V15 SCORED EXECUTION",
  "s1": "SEALED_UNTOUCHED"
}
```

Allowed lifecycle statuses:

```text
PLANNED_NOT_STARTED
ACTIVE_LIGHT
ACTIVE_HEAVY
PAUSED_RESOURCE_CONFLICT
BLOCKED
TERMINAL
```

`CLAUDE.md`, `RULES.md`, `CONTINUE.md`, plan path và GO registry phải đồng
thuận với registry. Nếu version, phase, GO phrase hoặc worktree khác nhau, đó là
`ROUTER_DRIFT`: **STOP trước dispatch/scoring**, đo lại và để Lead/A1 sửa bằng
một commit chỉ chứa router/control-plane files. Không chọn nguồn thuận tiện nhất.

`CONTINUE.md` là checkpoint ngắn được dẫn xuất từ registry, không phải authority
lịch sử và không được chỉ tới một `PLAN.md` không tồn tại. Frozen cycle contract
không bị viết lại khi global state đổi; registry ghi trạng thái hiện tại riêng.

## 4. Intake: 15 phút đầu tiên

Không sửa file trước khi intake hoàn tất.

### 4.1 Xác định checkout

Chạy từ đúng repository:

```bash
pwd
git branch --show-current
git rev-parse HEAD
git status --porcelain=v1
git remote -v
git worktree list --porcelain
```

Ghi lại:

```text
absolute cwd
branch
full 40-character HEAD SHA
dirty/untracked paths
remote relationship
worktree owner
```

Không dùng short SHA làm authority nếu có thể tránh. Full SHA là tên duy nhất
của một trạng thái Git cụ thể.

### 4.2 Đọc đúng tài liệu

Tối thiểu:

```text
CLAUDE.md
plan hiện hành của cycle
NOTES.md nếu liên quan research
research/wayfinder/MAP.md
terminal report của cycle trước
state.json / heartbeat.json / event_log.jsonl
worktree_manifest.json
```

Không mặc định `PLAN.md` là plan mới nhất. Tìm `PLAN_crypto_v*.md`,
`PLAN_stocks_v*.md`, `PLAN_forex_v*.md` và xác định cycle đang active bằng Git
state và control artifacts.

### 4.3 Đo process và tài nguyên

Kiểm tra:

- scored/backtest/download/parser/full-pytest worker đang chạy;
- RAM và dung lượng đĩa;
- machine/host phù hợp;
- data archive hoặc staged snapshot có thật;
- agent/worktree nào đang sở hữu process.

Không giết process của cycle khác. Nếu full suite xung đột với heavy worker,
ghi `NOT_RUN_RESOURCE_CONFLICT` và chờ thời điểm an toàn.

### 4.4 Phân loại dirty tree

Mọi file bẩn thuộc một trong bốn loại:

```text
OWNER_CHANGE            thay đổi của owner, phải giữ nguyên
AUTHORIZED_HANDOFF      công việc được bàn giao rõ ràng
LANE_OWNED_CHANGE       thay đổi của agent đúng ownership
UNEXPLAINED_DRIFT       không giải thích được, phải STOP
```

Không tự reset file bẩn. Không gom thay đổi của owner vào commit của agent.

### 4.5 First report

First report phải có:

```text
measured UTC/local time
cwd / branch / full HEAD
dirty state
active workers
cycle phase
budget observed/published
S1 status
authority blockers
GO / NO_GO cho bước kế tiếp
```

## 5. Hiểu yêu cầu trước khi hành động

Lead phân loại request:

### 5.1 Read-only request

Ví dụ: giải thích, audit, review, xem trạng thái.

Cho phép đo và đọc. Không tự sửa code, push, merge, tải dữ liệu hoặc mở cycle
mới.

### 5.2 Change/build request

Ví dụ: viết plan, implement adapter, sửa bug.

Cho phép thay đổi trong phạm vi được giao, chạy verification tương xứng và
commit khi workflow yêu cầu. Không tự mở rộng sang deployment hoặc provider.

### 5.3 External-state request

Ví dụ: push, tạo account, mua data, gửi email, live trade.

Cần authority rõ ràng cho đúng hành động và đúng target. “Làm xong” không mặc
định bao gồm push hoặc merge `main`.

### 5.4 Destructive request

Resolve target bằng read-only check trước. Ưu tiên thao tác có thể khôi phục.
Nếu scope mơ hồ, dừng và hỏi owner.

## 6. Cách Lead ra quyết định

Mỗi quyết định nên đi qua sáu câu hỏi:

1. **Objective** — outcome cụ thể là gì?
2. **Evidence** — dữ liệu nào chứng minh nó?
3. **Authority** — ai cho phép hành động này?
4. **Reversibility** — nếu sai có khôi phục được không?
5. **Contamination** — hành động có làm lộ S1, PnL hoặc ảnh hưởng cycle khác?
6. **Stopping rule** — điều kiện nào buộc dừng?

Ma trận quyết định:

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

## 7. Viết một PLAN có thể thực thi

Plan không phải danh sách mong muốn. Plan là contract quyết định trước khi kết
quả xuất hiện.

### 7.1 Các phần bắt buộc

Một research plan tốt gồm:

1. Frozen starting point.
2. Điều đã đóng và không được rescue.
3. Mission, câu hỏi và terminal outcomes.
4. Branch/worktree topology.
5. Agent roles và ownership.
6. Concurrency/resource policy.
7. Data authority và PIT contract.
8. Accounting/cost/publication contract.
9. Blind proposal phase.
10. Novelty và feasibility audit.
11. Selection rubric và freeze.
12. Implementation phase.
13. Exact-arm dry-run.
14. Code/data freeze.
15. Independent prelaunch audit.
16. Scored execution budget.
17. Stage-A gates.
18. Reproduction và terminal audit.
19. S1/deployment boundary.
20. Required commands và reporting format.
21. Hard forbidden actions.
22. First-report template.

### 7.2 Plan phải có terminal outcomes âm

Ví dụ:

```text
REJECT_ALL
BLOCKED_DATA_AUTHORITY
BLOCKED_SELECTION_INSUFFICIENT
BLOCKED_PRELAUNCH
INCOMPLETE_NOT_PROMOTABLE
ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_S1
```

Không có terminal âm sẽ tạo áp lực làm yếu gate để tìm survivor.

### 7.3 Không dùng phần trăm thay gate

“80% xong” không có nghĩa rõ. Báo:

```text
P0 PASS
P1 PASS
P2 BLOCKED_DATA_AUTHORITY
P3 NOT RUN
```

## 8. Thiết kế tổ chức agent

### 8.1 Vai trò chuẩn

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

Tên có thể đổi theo cycle, nhưng separation of duties không đổi.

### 8.2 A1 là authority duy nhất cho integration

A1:

- tạo và ghi worktree manifest;
- dispatch lane từ exact wave SHA;
- nhận handoff;
- cherry-pick tuần tự;
- chạy gate sau từng pick;
- freeze;
- append canonical ledger;
- cập nhật denominator;
- đóng cycle.

Lane agent không merge, rebase, push, sửa central ledger hoặc cập nhật state của
integration.

### 8.3 A7 phải độc lập

A7:

- branch từ SHA cần audit;
- chỉ viết audit artifact;
- không repair implementation;
- không thay gate;
- không hỏi implementer cách làm cho PASS;
- recompute từ bytes và source code;
- tìm lý do để bác bỏ claim.

Nếu A7 phát hiện lỗi, trả finding cho A1. A1 mở remediation lane mới. Sau sửa,
A7 audit lại delta hoặc toàn bộ theo mức rủi ro.

### 8.4 Khi nào nên dùng nhiều agent

Dùng song song khi:

- nhiệm vụ độc lập;
- ownership file không giao nhau;
- cùng một frozen base SHA;
- kết quả có thể tích hợp tuần tự;
- máy đủ tài nguyên.

Không dùng song song khi:

- nhiều agent phải sửa cùng core interface;
- plan chưa khóa;
- integration tree còn bẩn;
- scoring đang chạy trên máy yếu;
- câu hỏi nhỏ hơn chi phí coordination.

### 8.5 Context packet theo vai trò

Lead/A1 đọc toàn bộ handbook. Không bắt mọi lane agent nạp toàn bộ lịch sử nếu
nhiệm vụ chỉ cần một lát cắt nhỏ; việc đó tốn token và làm loãng ownership.

Mỗi dispatch packet phải tự đủ dùng và chỉ chứa:

```text
cycle/role/objective
exact base SHA + absolute worktree + branch
allowed/forbidden paths
frozen data/clock/cost identity liên quan
forbidden ancestry hoặc audit criteria liên quan
required inputs/outputs
test commands
stop conditions
commit and handoff format
```

A4/A5/A6 proposal lanes không nhận scored outcome files. A7 nhận evidence cần
audit nhưng không nhận chỉ dẫn “làm sao để PASS”. A8 nhận frozen implementation
contract, không được diễn giải lại hypothesis. A9 nhận feasibility inputs không
có PnL. Packet phải dẫn tới authority đầy đủ để tra cứu khi có ambiguity, nhưng
không sao chép hàng nghìn dòng không liên quan.

## 9. Worktree và branch discipline

### 9.1 Mỗi agent một worktree

```text
.worktrees/<cycle>/integration
.worktrees/<cycle>/<lane-name>
```

Không checkout cùng một branch ở hai worktree. Không cho hai agent sửa chung
worktree.

### 9.2 Dispatch từ exact base

```bash
BASE_SHA="$(git rev-parse HEAD)"
git worktree add -b <lane-branch> <absolute-lane-path> "$BASE_SHA"
```

Sau khi tạo:

```bash
git -C <lane-path> rev-parse HEAD
git -C <lane-path> branch --show-current
git -C <lane-path> status --porcelain=v1
```

Ba giá trị phải khớp manifest trước khi agent bắt đầu.

### 9.3 Ownership manifest

Mỗi lane ghi:

```json
{
  "lane": "a3-data",
  "worktree": "/absolute/path",
  "branch": "orca/cycle-a3-data",
  "base_sha": "40-char-sha",
  "owner": "A3",
  "allowed_paths": ["..."],
  "forbidden_paths": ["..."],
  "status": "SPAWNED"
}
```

Khi merge, cập nhật `MERGED`; khi reject, `REJECTED`; khi blocked,
`BLOCKED_WITH_EVIDENCE`.

### 9.4 Không dùng cwd ngầm

Mọi command quan trọng phải có `cd` hoặc `workdir` tường minh. Trước commit và
cherry-pick, kiểm tra lại `pwd`, branch và HEAD.

Repo đã từng có commit rơi nhầm worktree vì shell cwd trôi. Đừng tin cwd từ
command trước.

## 10. Concurrency và resource scheduling

Agent slot không đồng nghĩa worker slot.

### 10.1 Phân loại workload

```text
LIGHT   đọc file, viết docs, unit test nhỏ, proposal
MEDIUM  targeted pytest, compile, parser fixture
HEAVY   full pytest, data download, bulk parse, scored cell, reproduction
```

Trên máy 8 GB, mặc định:

- A1 + tối đa 3 lane nhẹ;
- một heavy job tại một thời điểm;
- scored cells serial trong family;
- full pytest chạy một mình;
- không download lớn cùng scoring.

Trên strong host, phải probe RAM/CPU/disk trước; không dùng cấu hình máy cũ làm
bằng chứng cho máy mới.

### 10.2 Lead là scheduler

Lead ghi:

- process owner;
- PID hoặc execution identity;
- started time;
- expected output;
- cap đã đo;
- điều kiện stop/retry.

Không “sleep rồi hy vọng”. Theo dõi log, heartbeat, artifact growth và process
health.

### 10.3 Global heavy-worker lock

Giới hạn “một heavy job” là **machine-wide**, không phải per cycle. Mỗi A1 tự
đếm worker của mình là chưa đủ vì hai cycle có thể cùng nhìn thấy máy rảnh.

Heavy worker phải lấy exclusive OS lock trước khi chạy, ví dụ bằng Python
`fcntl.flock` trên:

```text
.runtime/heavy_worker.lock
```

Runtime file là local/gitignored. Registry đi kèm tối thiểu ghi:

```text
cycle_id / role / PID / process-start token
absolute worktree / command digest
started_at / last_heartbeat / expected artifacts / status
```

Nếu không lấy được lock, trả `NOT_RUN_RESOURCE_CONFLICT`; không spin/retry vô
hạn và không chạy chen. Lock stale chỉ được thu hồi sau khi kiểm tra cả PID lẫn
process-start token để tránh nhầm một PID đã được hệ điều hành tái sử dụng.

Worker kết thúc phải ghi `FINISHED`, `FAILED` hoặc `TECHABORT` và giải phóng
lock trong `finally`. State/heartbeat nói `workers=0` trong khi process còn sống
là `CONTROL_STATE_DRIFT`, không được launch job tiếp theo cho đến khi reconcile.

### 10.4 Nhiều cycle cùng tồn tại

Cho phép proposal/docs/audit nhẹ chạy song song khi ownership không giao nhau.
Chỉ một cycle có thể mang `ACTIVE_HEAVY` tại một thời điểm. Các cycle khác ghi
`ACTIVE_LIGHT` hoặc `PAUSED_RESOURCE_CONFLICT` trong active-cycle registry.

Worktree được tạo không tự động có nghĩa cycle đã được launch. Bootstrap phải có
manifest/state/event-log commit sạch. Worktree có control files chưa commit là
`BOOTSTRAP_INCOMPLETE`; hoặc A1 commit đúng pathspec, hoặc park nó rõ ràng. Không
dispatch lane mới từ một integration tree bẩn.

## 11. Data authority và PIT

Đây là nơi một backtest đúng code vẫn có thể sai khoa học.

### 11.1 Ba thời gian khác nhau

```text
event_time       sự kiện xảy ra
effective_time   giá trị bắt đầu có hiệu lực
available_time   thị trường/người nghiên cứu có thể biết giá trị
```

`retrieved_time` là thời điểm agent tải file, không thay thế historical
`available_time`.

### 11.2 Record tối thiểu

```text
source_id
dataset_id
entity_id
field/value/unit
event_time_utc
effective_time_utc
available_time_utc
vintage_time_utc
retrieved_time_utc
raw_path/raw_sha256
license_id/entitlement_id
normalizer_version
```

### 11.3 Effective không đồng nghĩa available

Một policy rate có thể hiệu lực ngày X nhưng:

- được công bố trước X;
- được công bố trong ngày X;
- chỉ xuất hiện trong dataset tổng hợp sau X;
- bị sửa lịch sử về sau.

Không được tự đặt `available_time = end_of_effective_date` nếu không có release
evidence. Nếu dùng thông báo ngân hàng trung ương, phải lưu URL, timestamp,
content hash và mapping tới đúng rate change.

### 11.4 Free không đồng nghĩa authorized

Một nguồn miễn phí vẫn có thể:

- cần account hoặc API key;
- có click-through terms;
- cấm lưu trữ;
- cấm redistribution;
- chỉ cho non-commercial use;
- không có historical PIT.

Statuses nên dùng:

```text
DOCUMENTED_CANDIDATE
CANDIDATE_NOT_AUTHORIZED
AUTHORIZED_INTERNAL_RESEARCH
UNAVAILABLE_FAIL_CLOSED
REJECTED_LICENSE
```

### 11.5 Primary và cross-check

Nguồn `CROSS_CHECK` không được âm thầm vá gap của `PRIMARY`. Không trộn nhiều
nguồn thành dataset mới nếu không freeze conflict policy và provenance cho mỗi
row.

### 11.6 Data gate trước proposal/scoring

Kiểm tra:

- license/entitlement;
- coverage và missing intervals;
- timezone/calendar/DST;
- identity/delisting/symbol changes;
- corporate actions;
- vintages/revisions;
- raw hashes và deterministic retrieval;
- source schema drift.

Adapter tests PASS chỉ chứng minh parser hoạt động; không chứng minh dataset đủ
để scoring.

### 11.7 Archive bị rewrite và retrospective-only data

Publication lag và revision integrity là hai câu hỏi khác nhau:

```text
publication lag: file xuất hiện trễ bao lâu sau event?
revision integrity: byte/value lịch sử có bị thay đổi về sau không?
```

Thêm một lag bảo thủ không chứng minh revision integrity. Nếu kho dữ liệu cho
thấy historical span được upload/ghi lại về sau và không có original listing,
checksum hoặc independent snapshot tại thời điểm lịch sử, Lead phải mở hard
gate trước proposal selection/scoring:

```text
PASS_PIT_EVIDENCED
RETROSPECTIVE_ONLY
BLOCKED_DATA
```

- `PASS_PIT_EVIDENCED`: có bằng chứng đủ mạnh rằng row/value đã available với
  nội dung đó tại decision time.
- `RETROSPECTIVE_ONLY`: được dùng để sinh hypothesis hoặc nghiên cứu mô tả,
  nhưng không đủ điều kiện Stage A/S1 và không được quảng bá như PIT backtest.
- `BLOCKED_DATA`: không được tính scored result.

Các đường sửa hợp lệ: giới hạn về đoạn có archived snapshots độc lập; xây
forward-only snapshot từ hiện tại; hoặc tìm publication/checksum evidence lịch
sử. Owner có thể authorize nghiên cứu retrospective, nhưng authorization không
biến retrospective bytes thành historical PIT evidence.

Với SEC/multi-vintage data, `available_time` của mỗi vintage phải là accepted/
submission timestamp của đúng accession. Amendment tạo vintage mới chỉ từ lúc
amendment available; không được đưa restated value lùi về filing gốc. Mutation
test phải chứng minh filing/vintage đến muộn làm signal dịch đúng decision period.

## 12. Scientific research protocol

### 12.1 Mechanism before parameter

Proposal trả lời:

```text
Ai bị ép mua/bán hoặc chậm phản ứng?
Tại sao hiệu ứng tồn tại?
Observable nào đo được cơ chế?
Khi nào cơ chế phải thất bại?
Control nào bác bỏ cách giải thích thuận tiện?
```

Không bắt đầu bằng grid RSI/SMA và tìm tham số có PnL đẹp.

### 12.2 Outcome-blind proposal

Proposal agent không được xem scored outcome của proposal mình đang tạo.
Proposal phải khóa:

- hypothesis ID;
- mechanism;
- universe;
- clock;
- warmup;
- features và lags;
- entry/exit/fills;
- costs;
- anchor;
- một neighbour hỗ trợ;
- một causal/placebo control;
- falsification rule;
- expected failure interpretation.

### 12.3 Novelty và ancestry veto

Một family mới không được là family đã reject nhưng đổi:

- timeframe;
- threshold;
- vài symbol;
- phí;
- tên gọi;
- hướng dấu;
- session nhỏ.

Nếu cơ chế, information source và causal control không mới, reject proposal
trước scoring.

### 12.4 Feasibility trước selection

Đo không dùng PnL:

- số decision dự kiến;
- warmup coverage;
- turnover/cost ceiling;
- missing data;
- fold population;
- compute/runtime;
- khả năng tạo control khác anchor.

Đừng mất sáu giờ implement một family mà data gate đã biết sẽ fail.

### 12.5 Selection freeze

Selection rubric phải tồn tại trước khi proposals về. Freeze ghi:

```text
selected family IDs
proposal hashes
arm IDs
arm_config_digest
all score-affecting fields
trial budget
Stage-A gates
data/code base SHA
```

Không chọn vì agent đã lén thấy PnL.

## 13. Trial identity và denominator

### 13.1 Trial identity

Mỗi scored arm cần identity đủ mạnh:

```text
cycle_id
family_id
arm_id
arm_config_digest
data_snapshot_digest
code_freeze_sha
cost_tier
fold contract
```

Không dùng một field chung khiến Anchor và Neighbour đụng key. Exact-arm dry-run
phải chứng minh mọi record ID pairwise distinct.

### 13.2 Hai denominator

```text
observed_scored_denominator
published_ledger_denominator
```

Khi computation hoàn tất và outcome đã được thấy, observed tăng dù publication
thất bại. Sau khi sửa publisher, replay không tạo một trial khoa học mới nếu
input/config/code computation identity không đổi; nhưng lịch sử sự cố phải giữ.

### 13.3 Global trial history

Không chỉ đếm cell trong sprint. Lead duy trì program-level history để đánh giá
multiple testing. Một survivor sau hàng trăm cells chưa phải edge thật.

### 13.4 Intake snapshot không phải current total

Frozen contract giữ denominator tại thời điểm intake và không được sửa ngược.
Nhưng mọi checkpoint/terminal phải phân biệt rõ:

```json
{
  "intake_snapshot": {
    "published": 197,
    "observed": 200,
    "as_of_commit": "..."
  },
  "current_ledger_snapshot": {
    "published": 200,
    "observed": 203,
    "as_of_commit": "..."
  }
}
```

Current total lấy từ canonical global ledger, không cộng tay terminal reports.
Chênh lệch hợp lệ do cycle khác đóng sau intake phải được giải thích; không gọi
snapshot cũ là trạng thái hiện tại và không rewrite frozen contract để làm đẹp.

## 14. Implementation discipline

### 14.1 Implement từ frozen spec

Implementation agent không được “cải thiện” proposal. Mọi ambiguity phải trả về
A1 trước scoring.

### 14.2 Test bằng hand-computed fixtures

Tối thiểu:

- feature golden;
- one-event/one-bar lag;
- no-lookahead mutation;
- timezone/DST boundary;
- fold force-flat;
- costs exactly once;
- cash không bị tính như instrument;
- turnover/concentration;
- control khác anchor;
- deterministic double generation;
- malformed/missing data fail-closed.

### 14.3 Không dùng production outcome trong unit test

Unit tests dùng synthetic fixture hoặc fixed hand-computed values. Không pin
profitability của real S0 trong implementation test trước scoring.

## 15. Integration protocol

### 15.1 Handoff trước cherry-pick

Lane trả:

```text
role/lane
base SHA
commit SHA
changed files
tests with exact commands
PASS/FAIL/NOT RUN
known limitations
dirty/clean status
workers
```

### 15.2 Cherry-pick tuần tự

```text
verify integration clean
verify lane commit ancestry/base
inspect diff
cherry-pick one lane
run targeted tests
inspect status
record event
then pick next lane
```

Không cherry-pick ba lane rồi mới test. Khi lỗi xuất hiện, phải biết lane nào gây
ra.

### 15.3 Conflict resolution

Nếu hai lane sửa cùng file:

- không chọn bên tiện hơn;
- quay về ownership contract;
- A1 quyết định semantic result;
- chạy lại tests của cả hai lane;
- ghi conflict resolution vào handoff/event log.

## 16. Gate evidence

Mỗi gate artifact ghi:

```text
gate_id
measured_at
cwd / host
full HEAD
command
exit_code
stdout/stderr path or digest
expected
observed
input hashes
output hashes
tree state
verdict
blocker
```

### 16.1 Test routing

Thứ tự:

1. Syntax/import/compile.
2. Targeted unit tests.
3. Adjacent compatibility tests.
4. Protocol tests.
5. Asset suite.
6. Full suite một mình.
7. `git diff --check`.
8. Clean-tree verification.

Không chạy full suite để thay cho targeted diagnosis.

### 16.2 PASS có phạm vi

```text
unit tests PASS
```

không có nghĩa:

```text
data authority PASS
visual QA PASS
OOS PASS
live readiness PASS
```

Lead luôn ghi phạm vi của PASS.

## 17. Freeze và prelaunch

### 17.1 Các SHA quan trọng

```text
BASE_SHA          điểm bắt đầu cycle
WAVE_SHA          base chung cho proposal/implementation lanes
SELECTION_SHA     family/arms đã khóa
CODE_FREEZE_SHA   code được phép scoring
DATA_MANIFEST_SHA snapshot được phép scoring
AUDIT_SHA         artifact audit độc lập
TERMINAL_SHA      closeout cuối cycle
```

### 17.2 Exact-arm dry-run

Dry-run đi qua toàn bộ pipeline nhưng:

- `scored=false`;
- `real_pnl=false`;
- `published=false`;
- không để lộ PnL, PF, stress PnL, break-even hoặc metric kết quả;
- record IDs phải pairwise distinct;
- replay phải zero denominator delta.

Repo đã từng có dry-run ghi `scored=false` nhưng rò stress PnL. Lead phải scan
đệ quy toàn record, không chỉ bốn field top-level.

### 17.3 Independent prelaunch A7

A7 kiểm:

- selection/proposal/code/data hashes;
- exact-arm identity;
- data/PIT authority;
- accounting và costs;
- dry-run hygiene;
- S1 seal;
- no post-freeze code drift;
- denominator seed;
- execution/reproduction twin integrity;
- zero unresolved HIGH/CRITICAL.

Audit không chỉ chứng minh code chạy đúng như code; audit phải hỏi giả định đầu
vào có đúng không.

## 18. Scored execution

### 18.1 Hard launch gate

Không cell nào chạy cho tới khi:

```text
code freeze verified
data manifest verified
selection digests verified
prelaunch authorized
ledger seed verified
resource cap measured
S1 sealed
owner GO present when plan requires it
```

### 18.2 TECHABORT

Phân biệt:

```text
SCIENTIFIC_FAIL  cell chạy đúng và không qua gate
TECHABORT        computation không hợp lệ/kết thúc kỹ thuật
```

TECHABORT không được biến thành “không tính” tùy tiện nếu outcome đã bị lộ.
Ghi mức độ outcome exposure và denominator theo run contract.

### 18.3 Sau mỗi cell

Báo:

```text
cell/arm identity
exit code
runtime
observed delta
published delta
budget used
record/ledger digest
gate verdict
workers
S1 status
```

Không đợi hết cycle mới phát hiện denominator lệch.

## 19. Stage-A interpretation

Một family thường cần:

- after-cost expectancy dương;
- PF qua ngưỡng;
- ít nhất 2/3 folds dương;
- drawdown dưới ceiling;
- không tập trung vào một fold/instrument;
- stress costs vẫn sống;
- drop-one survival;
- incremental alpha so với benchmark;
- neighbour hỗ trợ;
- causal control không tái tạo;
- reproduction exact;
- zero unresolved high/critical.

Gate cụ thể phải theo plan của cycle, không lấy danh sách này thay frozen
contract.

Một Stage-A survivor chỉ là **ứng viên đáng mở S1**, không phải strategy deploy.

## 20. Reproduction và terminal audit

### 20.1 Reproduction

Reproduction chạy từ detached tree tại exact code freeze, với snapshot và
manifest độc lập nhưng byte-identical.

So sánh:

- record IDs;
- schedules/fills;
- costs/funding;
- folds/stress;
- metrics;
- verdicts;
- ledger bytes hoặc normalized canonical bytes.

Các field như timestamp chạy hoặc PID có thể được loại khỏi comparison nếu
contract đã định trước.

### 20.2 Terminal A7

A7 recompute:

- ancestry và freeze chain;
- ledger digest;
- gates từ source;
- trade/accounting reconciliation;
- control coherence;
- denominators;
- data/S1/deployment boundaries;
- strongest allowed terminal label.

Positive result cần audit nghiêm hơn negative result vì incentive xác nhận cao
hơn.

### 20.3 Terminal closeout

A1 đồng bộ:

```text
state.json
heartbeat.json
event_log.jsonl
terminal_report.json
worktree_manifest.json
MAP.md
HYPOTHESIS_LEDGER.md
SURVIVORS.md nếu thực sự đủ điều kiện
```

Workers phải về zero. Không xóa worktree bằng chứng nếu owner chưa cho phép.

## 21. Xử lý survivor

Trước khi ghi `SURVIVOR`, hỏi bốn tầng:

| Tầng | Câu hỏi |
|---|---|
| Mechanical | Code, ledger, hashes, reproduction có đúng không? |
| Data | PIT, license, identity, coverage có thật không? |
| Statistical | Multiple testing, folds, controls có đủ không? |
| Economic | Costs, financing, capacity có giao dịch được không? |

Nếu mechanical PASS nhưng PIT chưa chứng minh, dùng:

```text
PROVISIONAL_STAGE_A_SURVIVOR_PENDING_PIT_AUTHORITY
```

Không mở S1 để chữa một lỗi S0. Sửa data authority bằng một remediation plan,
giữ nguyên strategy, rồi audit lại.

## 22. Xử lý bug sau freeze

### 22.1 Trước scoring

Nếu A7 tìm bug trước cell đầu tiên:

1. Giữ freeze cũ làm bằng chứng `SUPERSEDED_BLOCKED`.
2. Mở remediation lane từ đúng SHA.
3. Sửa phạm vi nhỏ nhất.
4. Chạy regression.
5. Tạo freeze mới.
6. A7 delta audit.
7. Chỉ chạy khi audit mới authorize.

### 22.2 Sau scoring

Nếu bug có thể ảnh hưởng outcome:

1. Stop workers.
2. Không overwrite ledger.
3. Ghi incident và mức exposure.
4. Giữ observed denominator.
5. Xác định result invalid, indeterminate hay repairable theo plan.
6. Muốn chạy lại phải có owner-approved remediation plan và identity mới khi
   khoa học yêu cầu.

Không sửa code rồi replay để giữ nhãn cũ.

## 23. Xử lý blocker

Lead không idle-spin. Khi blocked:

1. Chứng minh blocker bằng read-only evidence.
2. Exhaust các đường an toàn trong scope.
3. Tách blocker thật khỏi việc chưa thử.
4. Nêu một hoặc vài owner actions cụ thể.
5. Giải phóng workers/resources.
6. Đóng trạng thái trung thực.

Một blocker report tốt:

```text
BLOCKED ON
evidence
what passed
what did not run
what was not attempted and why
single next owner action
state/branch/SHA/tree/workers
```

## 24. Incident transparency

Các incident phải được ghi, kể cả đã sửa:

- cwd drift;
- commit nhầm worktree;
- unexpected dirty tree;
- branch checked out sai;
- identity collision;
- denominator mismatch;
- dry-run PnL leak;
- stale metadata;
- host newline/autocrlf drift;
- missing archive;
- process chết hoặc timeout;
- accidental access tới forbidden path.

Report:

```text
what happened
scope of impact
whether outcome/data was exposed
repair performed
evidence preserved
why conclusion remains valid or becomes invalid
prevention added
```

Không giấu incident vì “đã sửa rồi”.

## 25. Communication với owner

### 25.1 Lead with outcome

Nói trước:

```text
PASS / FAIL / BLOCKED
ý nghĩa
có cần owner làm gì không
```

Sau đó mới đưa chi tiết.

### 25.2 Không bắt owner thay placeholder kỹ thuật

Agent tự đo full SHA, paths, counts và commands. Chỉ hỏi owner về quyết định mà
repo không thể suy ra:

- có mua data không;
- có tạo account/accept terms không;
- có mở S1 không;
- có push/merge/deploy không;
- chọn trade-off sản phẩm nào.

### 25.3 Giải thích hai tầng

Cho owner:

1. Một giải thích đơn giản: “đã làm / đang làm / còn thiếu”.
2. Một phần kỹ thuật với SHA, paths, gates cho audit.

### 25.4 Commentary trong lúc chạy

Không để owner im lặng quá lâu trong job dài. Cập nhật khi:

- bắt đầu phase;
- phát hiện blocker/incident;
- gate quan trọng hoàn tất;
- job dài vẫn khỏe;
- cần owner authority.

Không gửi cập nhật rỗng kiểu “vẫn đang làm”; phải có evidence mới.

## 26. Git, commit, push và merge

### 26.1 Commit hygiene

Trước commit:

```bash
pwd
git branch --show-current
git status --short
git diff --check
git diff --stat
```

Commit chỉ chứa một semantic unit và không nuốt file của owner.

### 26.2 Push boundary

Push chỉ khi owner hoặc plan cho phép. Push đúng branch, kiểm tra remote tip sau
push. Không coi push branch là merge `main`.

### 26.3 Main boundary

`main` thường là owner/bootstrap space. Không research trực tiếp trên main.
Merge main là external state change riêng, cần authority riêng.

## 27. Security và deployment boundary

- Không ghi API key trong prompt, command log, JSON hoặc Git.
- Dùng environment variable, keychain hoặc secret manager.
- Không in secret để “kiểm tra”.
- Không tạo account hay accept terms thay owner.
- Paper/testnet/live là ba trạng thái khác nhau.
- Xóa một hard guard không tự biến research system thành live-safe system.
- Live cần broker adapter, reconciliation, risk limits, kill switch,
  idempotency, monitoring và owner deployment plan riêng.

## 28. Những lỗi tư duy Lead phải tránh

### 28.1 “Tests xanh nên data đúng”

Sai. Tests có thể chỉ chứng minh code nhất quán với một giả định sai.

### 28.2 “Reproduction exact nên edge thật”

Sai. Reproduction exact có thể tái tạo hoàn hảo một look-ahead bug.

### 28.3 “Control âm nên mechanism đã chứng minh”

Control âm loại bỏ một cách giải thích, không loại bỏ tất cả confounder.

### 28.4 “Miễn phí nên dùng được”

Sai. Còn license, account, storage, PIT và coverage.

### 28.5 “Nhiều agent luôn nhanh hơn”

Sai. Ownership chồng nhau và integration conflict có thể chậm hơn một agent.

### 28.6 “Survivor đầu tiên là chiến thắng”

Sai. Sau nhiều trials, survivor đầu tiên có thể là winner may mắn. Nó chỉ mở
quyền lập kế hoạch S1.

### 28.7 “Owner không phản đối nghĩa là owner cho phép”

Sai. Im lặng không phải authorization.

## 29. Playbook: mở một research cycle mới

```text
1. Reconcile terminal cycle trước.
2. Reconcile ACTIVE_CYCLES, router docs, processes và global heavy lock.
3. Freeze starting SHA, counters, S1 và forbidden inventory.
4. Viết plan với terminal outcomes âm.
5. Bootstrap integration worktree; commit manifest/state/event log sạch.
6. Register cycle status + exact GO phrase; validate router consistency.
7. Pass accounting/data/PIT factory gates, gồm rewrite/revision gate nếu có.
8. Freeze baseline invariants.
9. Dispatch blind proposal lanes từ một wave SHA bằng role-specific packets.
10. Audit novelty và feasibility.
11. Apply frozen selection rubric.
12. Freeze selected proposal hashes và six-arm identities.
13. Implement trong isolated lanes.
14. Integrate tuần tự và run gates.
15. Create code/data freeze và detached twins.
16. Exact-arm sanitized dry-run.
17. Independent A7 prelaunch.
18. Owner GO nếu plan yêu cầu.
19. Acquire global heavy lock; run bounded scored cells.
20. Reproduce independently dưới cùng resource discipline.
21. Terminal A7.
22. Close state, ledger, Wayfinder, registry, workers và release lock.
```

## 30. Playbook: Data Fusion hoặc shared core

Shared core không được retrofit vào frozen cycle.

```text
1. Xây core ở branch/worktree riêng.
2. Unit-test offline interfaces.
3. Adapter lanes có ownership riêng.
4. Ghi source registry và authority status.
5. Independent audit core.
6. Freeze MULTISOURCE_DATA_CORE_SHA.
7. Mỗi asset có adoption commit riêng.
8. Chạy compatibility tests.
9. Chỉ cycle chưa data/selection freeze mới được adopt.
10. Cycle đã freeze chờ vòng sau.
```

Parser PASS không tự nâng nguồn thành research-authorized.

## 31. Templates

### 31.1 Agent dispatch

```text
ROLE
OBJECTIVE
ABSOLUTE WORKTREE
BRANCH
EXPECTED BASE SHA
ALLOWED PATHS
FORBIDDEN PATHS
REQUIRED INPUTS
DELIVERABLES
TEST COMMANDS
STOP CONDITIONS
COMMIT/PUSH RULES
HANDOFF FORMAT
```

### 31.2 Checkpoint

```yaml
phase: P2_DATA_AUTHORITY
verdict: PASS | FAIL | NOT_RUN | BLOCKED
head: <full SHA>
tree: clean | dirty-with-listed-paths
workers: 0
commands:
  - command: ...
    exit_code: 0
    result: ...
artifacts:
  - path: ...
remaining_blockers: []
next_safe_action: ...
```

### 31.3 Handoff

```yaml
agent: A3
lane: data
base_sha: ...
commit_sha: ...
changed_files: []
tests:
  passed: []
  failed: []
  not_run: []
authority_claims: []
known_limitations: []
tree_clean: true
workers: 0
```

### 31.4 Owner decision request

```text
Decision required:
Why repo evidence cannot decide it:
Option A and consequence:
Option B and consequence:
Default fail-closed state if no decision:
Exact action that becomes authorized:
Actions that remain forbidden:
```

### 31.5 Terminal report

```text
terminal verdict
full integration SHA
freeze/data/selection/audit SHAs
observed/published denominators
budget used
family verdicts
reproduction status
S1 status
data authority status
incidents and impact
tests/gates
workers/tree
completed vs not completed
next owner-authorized path
```

## 32. Definition of done cho Lead

Một cycle chỉ “done” khi:

- câu hỏi đã có terminal verdict hợp lệ;
- mọi computed outcome được đếm;
- state/heartbeat/event log/ledger đồng thuận;
- reproduction và audit có verdict rõ;
- S1/deployment boundary được giữ;
- incidents được ghi;
- không còn worker sở hữu;
- tree ở trạng thái đã báo;
- owner biết chính xác điều gì đã làm và chưa làm.

`BLOCKED_DATA_AUTHORITY` với evidence đầy đủ có thể là done. Một survivor thiếu
PIT evidence thì chưa done dù PnL đẹp.

## 33. Cách huấn luyện một Lead Engineer mới

Agent mới nên hoàn thành lần lượt:

1. Audit read-only một terminal cycle và tìm SHA chain.
2. Reconcile observed/published denominator.
3. Tạo một worktree lane và manifest không chỉnh code.
4. Integrate một fixture-only change với targeted tests.
5. Audit một PIT dataset và phân biệt effective/available/retrieved.
6. Viết một proposal có anchor/neighbour/control.
7. Review một exact-arm dry-run để tìm leak.
8. Reproduce một historical cell từ detached tree.
9. Viết terminal report không phóng đại claim.
10. Xử lý một giả định “owner-authorized” không có chỉ thị owner thật.

Chỉ sau các bài tập này mới giao quyền A1 publisher/freezer.

## 34. Checklist cuối cùng của Lead

Trước mọi quyết định quan trọng, hỏi:

```text
[ ] Tôi đang ở đúng cwd/branch/worktree/HEAD?
[ ] Dirty files đã được giải thích?
[ ] Tôi đã đọc đúng plan hiện hành?
[ ] ACTIVE_CYCLES, CLAUDE, RULES, CONTINUE và GO phrase có đồng thuận?
[ ] Cycle này là ACTIVE_LIGHT, ACTIVE_HEAVY hay PAUSED_RESOURCE_CONFLICT?
[ ] Global heavy lock và worker registry có khớp process thật?
[ ] Authority này đến từ owner hay do agent suy luận?
[ ] Dữ liệu có PIT và license evidence thật?
[ ] Có historical rewrite/restatement nào chỉ được che bằng lag giả định?
[ ] Cycle khác và S1 có bị ảnh hưởng?
[ ] Trial identity và denominator có đầy đủ?
[ ] Intake snapshot và current ledger total có được phân biệt?
[ ] Gate đã thực sự chạy hay chỉ được mô tả?
[ ] A7 có độc lập và có kiểm giả định đầu vào?
[ ] Positive claim có mạnh hơn evidence không?
[ ] Có đường dừng trung thực nếu kết quả âm?
[ ] Report có full SHA, commands, artifacts, tree và workers?
```

Nếu một câu chưa trả lời được, chưa nên bấm chạy scored cell.

## 35. Mô hình tinh thần đơn giản

Hãy tưởng tượng Lead là người quản lý một phòng thí nghiệm:

- Plan là công thức được viết trước.
- Worktree là bàn thí nghiệm riêng của từng người.
- SHA là niêm phong chống tráo mẫu.
- Data manifest là nhãn trên nguyên liệu.
- Ledger là sổ ghi mọi lần thử, kể cả thất bại.
- A7 là người kiểm nghiệm độc lập.
- S1 là hộp mẫu cuối cùng chưa được mở.

Lead giỏi không phải người luôn tìm ra vàng. Lead giỏi là người có thể chứng
minh thứ đang cầm là vàng, hoặc dũng cảm ghi đúng rằng nó không phải vàng.
