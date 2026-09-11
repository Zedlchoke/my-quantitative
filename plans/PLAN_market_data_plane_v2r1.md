# MARKET-DATA-PLANE-V2R1 — post-terminal fixture and closure remediation

> Status at authoring: `PLANNED_NOT_STARTED`.
>
> Đây là một engineering-remediation cycle chạy một lần. Nó sửa độ bền của
> test/fixture và hợp đồng terminal của MARKET-DATA-PLANE-V2; nó không mở lại
> nghiên cứu strategy, không thay đổi kết luận khoa học của V2, và không cấp
> data authority mới cho crypto, stocks hoặc forex.

## 0. Owner intent và kết quả cuối cần đạt

Mục tiêu của V2R1 là biến trạng thái hiện tại:

```text
MDP-V2 engineering đã hoàn thành
+ full suite đã chạy
+ 8 lỗi môi trường do worktree/staging ngoài repo bị dọn
+ terminal registry có vòng lặp tự tham chiếu SHA
```

thành:

```text
repo test hermetic và chạy được sau cleanup/fresh clone
+ kiểm tra dữ liệu lịch sử thật được tách thành integration gate fail-closed
+ terminal registry có identity contract không tự tham chiếu
+ full suite PASS từ clean detached reproduction tree
+ A7 độc lập xác nhận không làm yếu các scientific assertions
```

Strongest allowed engineering verdict:

```text
MARKET_DATA_PLANE_V2R1_PASS_REPO_FIXTURES_AND_TERMINAL_CONTRACT_CLEAN
```

Kể cả khi verdict trên PASS, kết luận data/science của V2 vẫn là:

```text
MARKET_DATA_PLANE_V2_BLOCKED_DATA_AUTHORITY
```

V2R1 tuyệt đối không được đổi nó thành `THREE_ASSET_SHADOW_READY`, vì:

- crypto shadow còn precision-mode mismatch ở legacy reader;
- forex và stocks chưa có đủ authorized real S0 snapshot;
- V2R1 không tải, mua, cấp phép hay suy diễn bất kỳ data authority nào.

## 1. Sole authority và lịch sử bất biến

### 1.1 Fresh-context authority

File này là sole fresh-context authority cho cycle `MARKET-DATA-PLANE-V2R1`.
Agent phải đọc toàn bộ trước khi sửa file.

Các tài liệu bắt buộc phải đọc thêm:

1. `CLAUDE.md`;
2. `HOW_TO_BE_A_LEAD_ENGINEER.md`;
3. `plans/PLAN_market_data_plane_v2.md`;
4. `research/control/market_data_plane_v2_run/terminal_report.json`;
5. `research/control/market_data_plane_v2_run/v2_terminal_resumption_addendum.json`;
6. `research/control/market_data_plane_v2_run/gates/V2-G7_resumption.json`;
7. `research/audits/market_data_plane_v2/a7_verdict.json`;
8. `research/wayfinder/MAP.md` và `NOTES.md` nếu tồn tại ở checkout làm việc.

### 1.2 Historical authorities — chỉ đọc

Không rewrite, squash, amend hoặc “làm đẹp” các artifact lịch sử:

- MARKET-DATA-PLANE-V1 terminal và các addendum của nó;
- MARKET-DATA-PLANE-V2 T1/T2/R1/R2;
- `V2-G7_resumption.json`;
- các cycle crypto/stocks/forex;
- ledger, denominators, selection freeze, S0/S1 partition hoặc survivor files.

Nếu cần sửa một khẳng định lịch sử, chỉ append một erratum/addendum mới và ghi
rõ artifact nào bị supersede ở field nào. Không xóa bằng chứng cũ.

## 2. Measured intake snapshot — phải remeasure, không normalize

Snapshot lúc viết plan, chỉ dùng để phát hiện drift:

```text
root checkout             /Users/hoangminhlong/my-quantitative
root branch               main
root dirty                D LabDashboard.command
                          M plans/ACTIVE_CYCLES.json
                          ?? .zcode/
                          ?? plans/PLAN_research_platform_v3.md
                          ?? plans/PLAN_zcode_orchestration_v3.md
MDP-V2 worktree           .worktrees/market-data-plane-v2/integration
MDP-V2 branch             orca/market-data-plane-v2-integration
MDP-V2 tip                597e74c (remeasure full SHA)
V2 resumption R1          41bf9b1
V2 resumption R2          98a1b78
V2 effective verdict      MARKET_DATA_PLANE_V2_BLOCKED_DATA_AUTHORITY
V2 full suite             2 failed, 1722 passed, 6 errors
same signature at V1 tip  2 failed, 1480 passed, 6 errors
MDP-attributable failures 0
workers                   0 for closed MDP-V2
S1                        SEALED_UNTOUCHED
scored-cell delta         0
heavy lock at authoring   HELD_PROVEN by STOCKS-FREE-V13/P0D_PRICE_RESTAGE
```

Trước mọi `git worktree add`, A1 phải:

```bash
pwd
git rev-parse --show-toplevel
git status --porcelain=v1
git branch --show-current
git rev-parse HEAD
git worktree list --porcelain
```

Nếu SHA, branch, dirty files, cycle lifecycle, lock owner hoặc worker state
khác snapshot, ghi `INTAKE_DRIFT` trong first report. Không tự reset hoặc xóa.

Các dirty files ở root là owner/foreign-cycle state. V2R1 không được đưa chúng
vào commit, sửa thay hoặc clean chúng.

## 3. Exact defects in scope

### D1 — legacy adapter tests phụ thuộc worktree ngoài repo

Hai test hiện gọi trực tiếp các path trong
`research/governance/legacy_adapters.py::LEGACY_SOURCES`, bao gồm:

```text
.worktrees/forex-free-v8/.../state.json
.worktrees/stocks-free-v12/.../cycle_state.json
```

Cleanup worktree làm test lỗi `FileNotFoundError`, dù code adapter không đổi.
Một clean clone hoặc CI host mới cũng không có các path này.

### D2 — V9 universe-audit unit tests phụ thuộc staging ngoài repo

Module fixture trong `tests/test_v9_universe_audit.py` gọi full historical
`scripts/v9_universe_audit.main()` hai lần. Script cần real catalog/funding
inputs đã bị cleanup; vì vậy sáu test setup error ở
`scripts/v9_universe_audit.py:567`.

### D3 — terminal `head` contract tự tham chiếu

`research/governance/terminal_consistency.py` hiện buộc registry row `head`
bằng integration branch tip. Nhưng commit dùng để cập nhật `head` lại tạo ra
một branch tip mới. Repin lần nữa chỉ lặp lại lỗi.

Đây là schema/identity bug, không phải chỉ là một stale SHA đơn lẻ.

### D4 — full-suite closure chưa thể gọi là clean PASS

V2 có bằng chứng mạnh rằng 8 lỗi là environmental drift và không attributable
cho MDP. Tuy nhiên repo vẫn chưa đạt điều kiện đơn giản và quan trọng:

```text
fresh/detached tree + authorized committed fixtures -> full pytest exit 0
```

V2R1 phải đóng điều kiện này thật, không chỉ waive lỗi.

## 4. Non-goals và forbidden actions

V2R1 không được:

- chạy scored strategy cell hoặc tăng denominator;
- đọc/mở S1;
- dùng API key, đăng ký provider, tải lại hoặc mua dữ liệu;
- copy raw licensed provider payload vào git;
- copy secrets, `.env`, key, token hoặc signed URL vào prompt/log/artifact;
- tái tạo real historical bytes rồi tuyên bố byte-identical;
- dùng V10/V11/V13 data thay cho V9 data;
- hạ assertion để test xanh;
- biến một integration check bị thiếu data thành `PASS`;
- xóa evidence worktree, archive, cache hoặc staging;
- kill/interrupt foreign-cycle worker;
- tranh heavy lock;
- merge, rebase, push hoặc sửa `main`;
- sửa kết luận `MARKET_DATA_PLANE_V2_BLOCKED_DATA_AUTHORITY`.

## 5. Architecture decision — hai tầng test rõ ràng

### 5.1 Tier H: hermetic repository tests

Tier H là test bắt buộc cho `pytest tests/ -q`. Nó phải:

- chỉ dùng source và fixture đã commit trong cùng tree;
- không phụ thuộc `.worktrees/`, absolute home path, gitignored staging,
  network, provider account, clock hiện tại hoặc environment secret;
- chạy được từ fresh clone và detached reproduction tree;
- giữ được semantic assertions, negative cases và mutation detection;
- deterministic dưới ít nhất hai cwd khác nhau và hai `PYTHONHASHSEED`;
- không ghi vào tracked source/fixture;
- dùng temp directory cho output.

### 5.2 Tier R: real historical/environment integration gates

Tier R giữ kiểm tra thực địa mà Tier H không thể chứng minh. Nó chạy bằng CLI
riêng, không tự động kéo vào unit-suite, và chỉ có ba trạng thái:

```text
PASS
FAIL
NOT_RUN_DATA_UNAVAILABLE
```

`NOT_RUN_DATA_UNAVAILABLE` là truthful gate state, không phải PASS và không
được dùng làm bằng chứng reproduction. CLI phải trả artifact có:

- expected inputs và paths/manifest IDs;
- availability/authority checks;
- SHA-256 nếu bytes tồn tại;
- command, cwd, code SHA, UTC, host class;
- verdict và exact blocker;
- khẳng định không network/no secret nếu chạy offline;
- zero mutation before/after hash cho real legacy states.

Thiếu real data không được làm `pytest tests/ -q` crash. Nhưng cũng không được
che khuất việc Tier R chưa chạy.

## 6. Fixture authority contract

### 6.1 Allowed fixture classes

Chỉ được commit fixture thuộc một trong các class:

1. `SYNTHETIC_HAND_COMPUTED` — tự tạo, nhỏ, expected result tính tay;
2. `SCHEMA_MINIMAL` — chỉ mô phỏng shape/schema, không chứa provider payload;
3. `REDISTRIBUTABLE_PINNED` — có source/license evidence rõ ràng và manifest;
4. `DERIVED_NON_REVERSIBLE` — chỉ khi A7 xác nhận không thể tái dựng raw data
   và license cho phép derivative.

Mặc định cho V2R1 là class 1 và 2. Class 3/4 cần evidence explicit; không
suy luận từ việc file từng tồn tại trên máy.

### 6.2 Fixture manifest bắt buộc

Tạo một manifest versioned, ví dụ:

```text
tests/fixtures/governance_fixture_manifest.json
```

Mỗi entry tối thiểu có:

```json
{
  "fixture_id": "...",
  "path": "tests/fixtures/...",
  "class": "SYNTHETIC_HAND_COMPUTED|SCHEMA_MINIMAL|...",
  "purpose": "...",
  "sha256": "64 lowercase hex",
  "license_authority": "repo-authored synthetic|documented reference",
  "contains_real_provider_payload": false,
  "contains_secret": false,
  "expected_consumers": ["test id"],
  "expected_semantics": ["assertion name"]
}
```

Manifest validator phải fail khi path escape, duplicate ID/path, digest sai,
unknown class, missing consumer, secret-like content hoặc unaccounted fixture.

## 7. Workstream ownership và agents

A1 là controller/integration authority duy nhất. Các lane branch từ cùng một
frozen `WAVE_SHA` và không sửa file chồng nhau.

| Lane | Role | Ownership chính | Không được làm |
|---|---|---|---|
| A1 | controller | run-control, worktree manifest, integration, gates | tự audit implementation của mình |
| A2 | legacy fixture remediation | `legacy_adapters.py`, related fixtures/tests | terminal schema, registry, V9 audit |
| A3 | V9 audit test split | V9 script/test, V9 fixtures, Tier-R CLI | registry/terminal contract |
| A4 | terminal identity contract | terminal validator, registry schema/API, tests/docs | legacy/V9 fixtures |
| A7 | independent adversarial audit | audit artifacts only | repair code hoặc đổi gate |
| A9 | detached reproduction | reproduction evidence only | sửa implementation |

Máy có tối đa ba light implementation lane song song nếu resource probe cho
phép. Full pytest/perf/reproduction là heavy và chạy tuần tự dưới global lock.
Nếu foreign cycle giữ lock, light lanes có thể tiếp tục; heavy gates ghi
`NOT_RUN_RESOURCE_CONFLICT` và scheduler/wait state. Không spin, không kill.

## 8. Phase R0 — intake, freeze và first report

Trước edit implementation, A1 phải:

1. remeasure root và V2 worktree;
2. xác nhận `597e74c...` hoặc ghi drift;
3. kiểm tra plan commit là ancestor của future integration base;
4. xác nhận không có branch/worktree V2R1 trùng tên;
5. inspect canonical cycle registry bằng read-only command;
6. inspect lock, job registry và OS processes;
7. reparse T1/T2/R1/R2, A7 và G7 evidence;
8. chạy `git diff --check` ở source base;
9. freeze exact list 8 failing/error test nodes;
10. tạo `p0_first_report.json`, `run_contract.json`, `state.json`,
    `heartbeat.json`, append-only `event_log.jsonl` và
    `worktree_manifest.json`.

First report phải nêu:

```text
measured UTC / host / RAM / CPU
root SHA + dirty files
V2 branch/worktree/tip + ancestry
V2 effective verdict
exact eight residual nodes
current registry row + head semantics
lock owner / workers / job state
S1 / denominator / scored delta
WAVE_SHA
planned lanes and ownership
GO/NO_GO for light work
GO/NO_GO for heavy work
```

R0 gate:

```text
R0_PASS_LIGHT
R0_BLOCKED_INTAKE_DRIFT
R0_BLOCKED_CONTROL_STATE_DRIFT
```

## 9. Phase R1 — characterize failures before repair

Nếu required inputs vẫn thiếu, chạy targeted commands đủ để tái hiện signature
mà không cần heavy lock. Không download hoặc fabricate input.

Phải lưu:

- exact traceback digest;
- missing path/input census;
- test-to-authority dependency graph;
- proof rằng failure đến trước assertion science nào;
- proof các pure/synthetic helper tests vẫn chạy;
- classification `HERMETICITY_DEFECT`, không gọi chung là flaky.

Acceptance:

- 2 legacy failures map tới external worktree paths;
- 6 V9 errors map tới external catalog/funding dependency;
- không có failure mới bị gộp vào cùng waiver;
- baseline stdout/stderr được hash, không chép secrets.

## 10. Phase R2 — A2 legacy adapter remediation

A2 phải làm API path-injectable nhưng giữ default production behavior. Thiết kế
tối thiểu:

```python
build_registry_from_legacy(measured_heads, source_paths=None)
```

Hoặc một immutable source descriptor tương đương. Yêu cầu:

- production default vẫn resolve known legacy authorities fail-closed;
- tests truyền explicit temp/fixture paths, không monkeypatch global home;
- missing source sinh typed error có cycle ID + path;
- read path hash before/after để chứng minh không mutation;
- fixture chứa đủ ba historical shapes và known drift cases;
- composed registry vẫn validate đúng schema;
- stale/prose head warning semantics giữ nguyên;
- unknown cycle và undeterminable lifecycle vẫn fail closed;
- path confinement không cho fixture root escape nếu API nhận root.

Tier R CLI riêng phải có thể đọc các real `LEGACY_SOURCES` khi chúng tồn tại,
và trả `NOT_RUN_DATA_UNAVAILABLE` khi cleanup làm mất chúng.

Không được đơn giản `pytest.skip()` trong hai test hiện lỗi.

R2 targeted gate phải có:

- hand-computed fixture tests;
- byte-preservation test;
- missing/malformed/path-escape negative tests;
- registry composition validation;
- repeated-run equality.

## 11. Phase R3 — A3 V9 universe-audit remediation

Tách pure engine khỏi environment loader:

```text
load_inputs(authority_descriptor) -> typed bundle or typed unavailable
run_audit_from_bundle(bundle, frozen_config) -> manifest/audit/gate
run_real_historical_audit(descriptor) -> PASS|FAIL|NOT_RUN_DATA_UNAVAILABLE
```

Tên API có thể đổi, nhưng separation phải giữ.

Tier H synthetic bundle phải nhỏ nhưng chứng minh đủ semantic contract cũ:

- deterministic byte-identical rerun;
- BTC chỉ là benchmark context, không vào rank/weights/PnL;
- pre/scored window intersection đúng;
- zero unexplained gaps;
- documented capture-boundary gap được phân loại đúng;
- funding completeness cho held exposure;
- missing funding interval fail;
- timestamp boundary và listing-age checks;
- committed expected artifacts tái lập được từ fixture.

Không được hardcode output JSON để bypass engine. A7 phải có mutation tests:

- đưa BTC vào selected set -> fail;
- xóa một required bar -> unexplained gap fail;
- xóa một funding event cần thiết -> completeness fail;
- đổi selection volume -> deterministic digest hoặc pin fail;
- đổi cwd/hash seed -> output không đổi.

Tier R wrapper giữ khả năng chạy historical V9 data khi owner cung cấp đúng
manifest/bytes. Nếu data absent, nó phải tạo availability artifact và exit code
được document rõ; không tạo fake manifest/audit/gate mang nhãn PASS.

## 12. Phase R4 — A4 terminal identity contract v2

### 12.1 Frozen semantic decision

Một commit không thể chứa SHA của chính nó. Vì vậy từ V2R1:

```text
terminal_anchor_sha = commit cuối chứa code/evidence mà A7 đã audit
branch_tip          = giá trị resolve live khi validator chạy
```

Không persist yêu cầu `branch_tip == SHA nằm trong chính branch-tip commit`.

Đối với row lifecycle `TERMINAL`, registry phải khai báo explicit semantics:

```json
{
  "head": "<terminal_anchor_sha>",
  "head_semantics": "TERMINAL_ANCHOR",
  "terminal_anchor_sha": "<same SHA>",
  "post_terminal_policy": "ALLOWLISTED_APPEND_ONLY_DESCENDANTS"
}
```

Validator phải:

1. verify SHA grammar 40 lowercase hex;
2. verify anchor tồn tại và là ancestor của live branch tip;
3. verify terminal report/addendum bind đúng anchor;
4. inspect toàn bộ diff `anchor..branch_tip`;
5. chỉ cho phép append-only descendant paths đã freeze;
6. fail nếu descendant sửa implementation, tests, fixture, plan, ledger,
   denominator, S1, result hoặc historical event lines;
7. fail nếu non-descendant, missing branch, malformed row hoặc ambiguous schema;
8. không sinh `REGISTRY_HEAD_STALE` chỉ vì evidence-only closure commit đứng sau
   anchor;
9. vẫn fail stale head cho ACTIVE cycle;
10. vẫn hiển thị live branch tip trong output để operator nhìn thấy.

### 12.2 Minimal allowlist

Allowlist mặc định cho post-terminal descendants:

```text
research/control/<cycle>/... append-only reconciliation/addendum/gate evidence
research/audits/<cycle>/... independent audit artifacts
canonical registry transition/journal/projection generated by approved writer
```

Không allowlist code, tests, plan, research results hoặc arbitrary docs.

Nếu V2R1 sửa code/tests sau anchor cũ, nó phải có anchor mới sau A7; không thể
dựa vào allowlist để che implementation change.

### 12.3 Mandatory contract tests

Test matrix tối thiểu:

- active row head equals tip -> PASS;
- active row stale -> FAIL;
- terminal anchor equals tip -> PASS;
- terminal anchor ancestor + one allowed addendum commit -> PASS;
- terminal anchor ancestor + registry journal/projection commit -> PASS;
- terminal anchor ancestor + code change -> FAIL HIGH;
- terminal anchor ancestor + test/fixture change -> FAIL HIGH;
- non-ancestor SHA -> FAIL;
- malformed/missing SHA -> FAIL;
- deleted/reordered historical event -> FAIL;
- T1/T2/R1/R2-style chain -> no self-reference loop;
- repeated reconciliation does not require another repin commit.

Schema migration là additive. Legacy `cycle_registry@1` rows vẫn đọc được;
ambiguous terminal rows phải tạo visible compatibility finding, không silent
normalize. Chỉ canonical writer/CAS+journal được cập nhật registry.

## 13. Phase R5 — integration order

A1 tích hợp tuần tự từ exact WAVE_SHA:

1. A2 legacy fixture remediation;
2. chạy A2 targeted gate;
3. A3 V9 audit split;
4. chạy A3 targeted gate;
5. chạy combined fixture suite;
6. A4 terminal identity contract;
7. chạy governance/registry/terminal targeted gate;
8. run manifest/secret/path portability scanners;
9. freeze `V2R1_IMPLEMENTATION_CANDIDATE_SHA`.

Sau mỗi cherry-pick:

```text
clean before pick
exact lane SHA recorded
no conflict or conflict resolution recorded file-by-file
targeted tests PASS
git diff --check PASS
clean after gate
```

Nếu ownership overlap xuất hiện, dừng lane sau, rebase bị cấm; A1 tạo wave mới
từ integrated SHA.

## 14. Phase R6 — independent A7 audit

A7 branch từ `V2R1_IMPLEMENTATION_CANDIDATE_SHA`, không từ lane SHA.
A7 chỉ viết audit artifact và phải cố bác bỏ claim.

Audit checklist:

1. inventory mọi changed file từ V2 tip đến candidate;
2. xác nhận zero strategy/scored/S1/provider mutation;
3. fixture license/class/digest/secret review;
4. prove Tier H không chạm `.worktrees`, home path, network hoặc secrets;
5. mutate fixture để chắc assertions thực sự bắt lỗi;
6. verify Tier R absent-data state là NOT_RUN, không PASS;
7. verify scientific semantics V9 không bị hạ;
8. verify legacy byte-preservation và warning semantics;
9. adversarial terminal identity matrix;
10. detect self-referential repin cycle;
11. verify post-terminal allowlist không rộng quá;
12. verify historical T1/T2/R1/R2 bytes unchanged.

Verdict:

```text
A7_AUTHORIZE_V2R1_CLOSURE
A7_BLOCK_HIGH_OR_CRITICAL
A7_CONDITIONAL_MUST_FIX
```

HIGH/CRITICAL bắt buộc mở remediation lane mới. A7 không tự sửa code. Sau sửa,
A7 audit lại delta hoặc toàn candidate tùy blast radius.

## 15. Phase R7 — heavy battery và reproduction

Chỉ chạy khi global heavy lock là `FREE_PROVEN`. A1 acquire lock bằng canonical
API, ghi PID/role/host/start UTC. Không dùng file lock tự chế.

Nếu lock đang do foreign cycle giữ:

- không tranh;
- không chạy full suite/perf song song;
- state = `WAITING_RESOURCE_CONFLICT`;
- heartbeat ghi lock owner và next poll/trigger;
- không close PASS khi mandatory heavy gates chưa chạy.

Khi lock free, chạy tuần tự bằng `.venv/bin/python`:

```bash
.venv/bin/python -m compileall research/market_data_plane research/data_fusion research/governance scripts
.venv/bin/python -m pytest <A2 targeted nodes> -q
.venv/bin/python -m pytest <A3 targeted nodes> -q
.venv/bin/python -m pytest <A4 targeted nodes> -q
.venv/bin/python -m pytest tests/ -q
git diff --check
```

Full suite acceptance:

- exit 0;
- zero failures/errors;
- skips/xfails phải có exact known inventory và không bao gồm 8 node remediated;
- no network/key access;
- tree clean before và after;
- stdout/stderr digest, duration, peak RSS, host, SHA, lock token ghi vào gate;
- real-data Tier R có thể `NOT_RUN_DATA_UNAVAILABLE`, nhưng trạng thái đó phải
  nằm trong artifact riêng và owner-visible.

### Detached reproduction

A9 tạo fresh detached tree từ exact candidate/authorized SHA, không reuse test
cache hoặc local untracked fixture. Chạy lại:

- fixture manifest validation;
- three targeted suites;
- full `pytest tests/ -q`;
- terminal consistency matrix;
- deterministic output với cwd khác và `PYTHONHASHSEED` khác;
- secret/path scan;
- `git diff --check` và clean-tree check.

Kết quả phải exact-match về verdict/count/digests trừ UTC, PID, temp path và
host-measurement fields đã khai báo.

Perf benchmark chỉ bắt buộc nếu diff chạm production MDP/data path. Nếu chỉ
fixture/test/governance validator đổi, ghi `NOT_RUN_NOT_APPLICABLE` kèm diff
proof. Nếu chạy, chỉ so với baseline cùng host class; không so chéo host.

## 16. Phase R8 — closure without SHA self-reference

Closure order:

1. freeze A7-audited `terminal_anchor_sha`;
2. update registry row bằng canonical CAS+journal với
   `head_semantics=TERMINAL_ANCHOR`;
3. append V2R1 terminal report/addendum/event/projection;
4. run terminal-consistency validator against live branch tip;
5. validator verifies anchor ancestry + allowlisted descendant diff;
6. không tạo commit chỉ để repin live tip;
7. run final clean-tree and worker-zero checks;
8. release lock/job resources;
9. report no push/no merge.

Nếu terminal artifact commit khiến validator đòi repin thêm một lần, contract
vẫn sai: verdict phải `FAIL_TERMINAL_IDENTITY`, không tạo chuỗi repin mới.

Canonical surfaces cần đồng thuận:

```text
run_contract.json
state.json
heartbeat.json
event_log.jsonl
worktree_manifest.json
terminal_report.json
terminal identity/registry transition artifact
plans/CYCLE_REGISTRY.json + journal
plans/ACTIVE_CYCLES.json projection (canonical writer only)
MAP.md nếu cycle status cần projection
```

Không đụng HYPOTHESIS_LEDGER/SURVIVORS vì cycle này có zero hypothesis/cell.

## 17. Gates và terminal verdicts

| Gate | Điều kiện PASS |
|---|---|
| V2R1-G0 | intake measured, ownership frozen, no control drift |
| V2R1-G1 | exact 8-defect baseline characterized |
| V2R1-G2 | legacy adapter hermetic + Tier R fail-closed |
| V2R1-G3 | V9 audit hermetic + scientific mutation tests |
| V2R1-G4 | terminal identity v2 matrix PASS, no self-reference loop |
| V2R1-G5 | combined integration targeted gates PASS |
| V2R1-G6 | independent A7 authorize, 0 unresolved HIGH/CRITICAL |
| V2R1-G7 | full suite exit 0 under lock |
| V2R1-G8 | detached reproduction exact-match |
| V2R1-G9 | terminal consistency PASS at live post-closure tip |

Allowed terminal labels:

```text
MARKET_DATA_PLANE_V2R1_PASS_REPO_FIXTURES_AND_TERMINAL_CONTRACT_CLEAN
MARKET_DATA_PLANE_V2R1_BLOCKED_RESOURCE_CONFLICT
MARKET_DATA_PLANE_V2R1_BLOCKED_FIXTURE_AUTHORITY
MARKET_DATA_PLANE_V2R1_BLOCKED_CONTROL_STATE_DRIFT
MARKET_DATA_PLANE_V2R1_FAIL_COMPATIBILITY
MARKET_DATA_PLANE_V2R1_FAIL_TERMINAL_IDENTITY
MARKET_DATA_PLANE_V2R1_INCOMPLETE
```

Không dùng `PASS_WITH_RESIDUALS` nếu bất kỳ mandatory gate nào còn FAIL/ERROR.
Resource conflict chỉ hợp lệ khi lock thực sự HELD_PROVEN và mandatory heavy
gate chưa thể chạy. Khi lock free, cycle phải resume thay vì coi BLOCKED là
engineering complete.

## 18. Definition of done

V2R1 chỉ done khi:

- tất cả 8 node cũ chạy qua hermetic path và PASS;
- full repo suite exit 0 từ integration tree;
- detached reproduction full suite exit 0;
- no test bắt buộc phụ thuộc `.worktrees` hoặc untracked staging;
- Tier R real-data gates vẫn tồn tại và truthful;
- fixture manifest đầy đủ, digest/license/secret checks PASS;
- V9 semantic mutation tests PASS;
- terminal anchor/descendant contract không tự tham chiếu;
- terminal validator PASS tại live post-closure tip mà không repin lần nữa;
- A7 độc lập authorize, zero unresolved HIGH/CRITICAL;
- workers zero, lock released, tree sạch;
- zero scored cell, zero denominator delta, S1 untouched;
- V2 scientific verdict vẫn `BLOCKED_DATA_AUTHORITY`;
- no push, no merge, no cleanup/delete.

## 19. Sau V2R1 sẽ có gì và còn thiếu gì

### Có

- full suite không vỡ khi owner dọn worktree/cache/staging;
- fixture nhỏ, audit được, có checksum và authority rõ;
- clean clone/CI/reproduction chạy cùng một test contract;
- real historical checks vẫn được giữ nhưng báo thiếu data trung thực;
- registry terminal không còn vòng lặp commit-pinning;
- MDP V2 có closure mechanics đủ sạch để làm nền cho Research Platform V3 và
  Zcode Orchestration V3.

### Còn thiếu — cycle khác xử lý

- crypto high-precision catalog/legacy reader decision;
- authorized real forex/stocks snapshots;
- L3 shadow parity đủ ba asset;
- một full future research cycle mỗi asset dùng MDP canonical input;
- provider/license/entitlement mới;
- strategy edge hoặc live-trading readiness.

## 20. Fresh-session one-shot prompt

Copy nguyên prompt dưới đây vào một session agent mới:

```text
You are the A1 Controller for cycle MARKET-DATA-PLANE-V2R1.

Authority: read /Users/hoangminhlong/my-quantitative/plans/PLAN_market_data_plane_v2r1.md
IN FULL before any change. It is the sole fresh-context authority. Also read
CLAUDE.md, HOW_TO_BE_A_LEAD_ENGINEER.md, plans/PLAN_market_data_plane_v2.md,
the V2 terminal report, v2_terminal_resumption_addendum.json,
gates/V2-G7_resumption.json, and the V2 A7 verdict. Historical V1/V2 records
are immutable; corrections are append-only.

Objective: execute V2R1 end-to-end. Repair the two legacy-adapter failures,
the six V9-universe-audit setup errors, and the terminal registry SHA
self-reference bug. Build hermetic committed fixtures for the mandatory repo
suite, preserve real historical checks as separate fail-closed Tier-R gates,
and close only after a clean full-suite run plus detached reproduction and an
independent A7 audit.

Measured anchors at plan authoring (remeasure; report drift, never normalize):
- MDP-V2 integration worktree:
  /Users/hoangminhlong/my-quantitative/.worktrees/market-data-plane-v2/integration
- branch: orca/market-data-plane-v2-integration
- tip: 597e74c (resolve full SHA)
- effective V2 verdict: MARKET_DATA_PLANE_V2_BLOCKED_DATA_AUTHORITY
- residual signature: 2 failed + 6 errors at V2, identical 2 failed + 6
  errors at V1; zero MDP-attributable failures
- heavy lock at authoring: held by STOCKS-FREE-V13/P0D_PRICE_RESTAGE
- S1 SEALED_UNTOUCHED; zero scored/denominator delta
- root has owner/foreign dirty files; preserve and never commit them

Operating rules:
1. Produce the plan Section 8 first report before implementation edits.
2. pwd + branch + HEAD + clean-tree assertion before every worktree action.
3. One cycle = one A1 integration thread. Verify no V2R1 branch/worktree
   exists before bootstrap. Create lane worktrees from one frozen WAVE_SHA.
4. Dispatch independent A2 legacy-fixture, A3 V9-audit, and A4 terminal-
   identity lanes with disjoint ownership. A1 alone integrates and writes
   canonical state/registry/terminal surfaces. A7 is independent and never
   repairs implementation. A9 reproduces from a detached clean tree.
5. Light lanes may run while a foreign cycle holds the heavy lock. Never
   contend, kill, or interrupt it. Full pytest/perf/reproduction run alone
   only after FREE_PROVEN and canonical lock acquisition.
6. Use .venv/bin/python. No network, provider signup, credential use, data
   purchase, S1 access, scored cells, denominator changes, push, main merge,
   rebase, reset, cleanup, deletion, or historical rewrite.
7. Never commit raw licensed provider data or secrets. Synthetic/schema-only
   fixtures need manifest, SHA-256, purpose, consumers and authority class.
8. Do not fix tests by skipping them or weakening assertions. Keep BTC
   exclusion, gap census, funding completeness, deterministic rerun, legacy
   byte-preservation and drift-warning semantics. Prove them with mutations.
9. Real historical data absence is NOT_RUN_DATA_UNAVAILABLE in a separate
   Tier-R artifact, never PASS and never a repo-unit-suite error.
10. Fix terminal identity structurally: TERMINAL_ANCHOR must be an ancestor
    of the live tip and all descendants must be allowlisted evidence-only.
    Do not create an endless commit chain that repins the latest tip.
11. Run targeted gates after every pick; then independent A7; then full
    pytest alone under lock; then detached reproduction with a different cwd
    and PYTHONHASHSEED; finally terminal consistency at the live closure tip.
12. Continue autonomously through all phases. Do not stop for routine
    checkpoints. Send concise progress checkpoints, but request owner input
    only for a genuine blocker requiring new authority. A held heavy lock is
    a wait/resume condition, not permission to declare PASS.

Strongest allowed engineering verdict:
MARKET_DATA_PLANE_V2R1_PASS_REPO_FIXTURES_AND_TERMINAL_CONTRACT_CLEAN.
This must not upgrade the standing V2 scientific/data verdict
MARKET_DATA_PLANE_V2_BLOCKED_DATA_AUTHORITY.

At terminal, report exact SHAs, branch/worktrees, changed files, fixture
manifest, test commands/counts/exits, A7 findings, reproduction equality,
registry/terminal identity proof, lock lifecycle, workers, dirty status,
scientific invariants, remaining blockers, and no-push/no-merge status.
```

## 21. Owner dispatch phrase

Plan này không cần GO phrase cho scored execution vì nó cấm scored cells.
Để bắt đầu engineering cycle, owner chỉ cần gửi prompt Section 20. Không được
suy diễn prompt đó thành authorization cho data access, push hoặc asset cycle.

