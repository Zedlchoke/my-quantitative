# FINAL_REPORT — DATA-FOUNDATION-SIXSOURCE-V1 (controller A1, 2026-09-28)

Owner directive 2026-09-28 (read-only data foundation, six source
groups). 0 scored cells, 0 OOS looks, 0 orders, 0 shadow touches, 0
credentials, 0 purchases, 0 signups. Owner's dirty tree preserved (all
session artifacts are new untracked files; nothing committed — owner
reviews and commits). Registration: none (disclosed in INTAKE.md).

Lanes: L-FX (controller inline) · L-CX (subagent) · L-RATES (controller
inline). Handoffs: `ibkr_fx/HANDOFF_L-FX.json`, `cx/HANDOFF_CX.json`,
`cme_rates/HANDOFF_L-RATES.json` (schema `zcode_orch_v3_handoff@1`).

## Six-source table

| # | Nguồn | Status | Khoảng thời gian | Timestamp authority | SHA / manifest | Dung lượng | License | Chi phí (đo được / chưa đo) | Cơ chế mở được | Hành động owner (1/blocker) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | FX cost-band qua IBKR (IDEALPRO paper, read-only API) | **AVAILABLE_VALIDATED** (two-sided LIVE streaming đo được; chỉ 1/24 hour-bucket + 2 cửa sổ scheduled) | streaming từ 2026-09-28T02:03Z (PROSPECTIVE-từ-hôm-nay; không phải lịch sử) | IB server stamp giây-cấp + receive_ns local; skew p50 ~0.8 s đo được | raw sha256 789e7e45318a86a2…; sanitized + sessions_index | 2.0 MB (S0) | TWS paper session, Read-Only API bật; dữ liệu nội bộ nghiên cứu | spread đo được (p50 0.1–0.6 pip, bucket 02Z); commission/swap/rollover-clock/min-size/slippage UNMEASURED (cần statement) | after-cost FX book tương lai (không tự mở frontier đã đóng — P3-A vẫn đứng theo law, erratum đã ghi) | Xuất Activity/Flex statement chứa giao dịch FX + overnight FX về `~/.my-quantitative-data/ibkr_statement/` (không tạo giao dịch để lấy mẫu) |
| 2 | Crypto orderbook/L2 (Binance spot, BTCUSDT+ETHUSDT) | **AVAILABLE_VALIDATED** (1 cửa sổ 599 s; PROSPECTIVE_FROM_2026-09-28 — không phải lịch sử) | 2026-09-28T02:16:50→02:26:49Z | event `E` ms của sàn + receive_ns; U-chain 100% (0 gap / 0 reconnect / sync rule PASS; spot không có trường `pu` — ghi nhận schema, không phải defect) | `crypto_l2/collector_manifest.json`, ALL_SHA_OK | 14,109,556 B ndjson + manifest | keyless public market data (`data-api.binance.vision` theo spec chính thức); nghiên cứu nội bộ | dữ liệu 0 đồng; execution fee/slippage KHÔNG đo (không đặt lệnh) | collector L2 prospective hoạt động — class phụ thuộc L2 được thiết kế từ nay (chỉ prospective; cấm suy book từ nến giữ nguyên) | không bắt buộc. (Tùy chọn: quyết định capture kéo dài 2 tuần ≤5 GB) |
| 3 | On-chain (Ethereum public RPC) | **AVAILABLE_VALIDATED** (1 provider chạy: PublicNode; các phép so provider còn NOT_RUN/BLOCKED ghi trung thực) | instantaneous 2026-09-28T02:30Z (state as-of-now, không phải PIT history) | block timestamp của chain; head 26.072.973 @02:30:59Z, finalized 26.072.908 @02:17:59Z → finality lag 65 blocks / 780 s (đo được) | `onchain/onchain_manifest.json` | 50.836 B raw + manifest | public goods RPC, keyless | ~6 RPC call nhẹ (0 đồng) | probe state+finality hoạt động; luật chống-gán-nhãn-ví-hồi-củu ghi vào raw+report | không bắt buộc. (Chỉ khi cơ chế cần index history: quyết định vendor/indexer) |
| 4 | Options — crypto (Deribit BTC) | **AVAILABLE_VALIDATED** (scope đã định danh: CRYPTO options; equity/OpRA ngoài phạm vi — cần vendor có license) | census chain: 988 instruments / 13 expiries; sample 10 tickers expiry gần nhất 2026-09-28T08:00Z (58 inst / 29 strikes) | exchange timestamp 10/10; bid/ask hai chiều 10/10; IV (mark/bid/ask) 10/10; đủ 5 greeks 10/10 | `options/options_manifest.json` | ~27,3 KB raw | Deribit public market data keyless; nghiên cứu nội bộ | dữ liệu 0 đồng; execution fee/vol-spread chưa đo | cửa options crypto mở cho thiết kế (prospective; chain membership có census) | không bắt buộc. (Pilot lịch sử: archive chính thức keyless nếu có — chưa mua gì) |
| 5 | Rates intraday (futures quotes) | **BLOCKED_TRANSPORT + BLOCKED_LICENSE** | — (0 bytes toàn hệ, tái xác nhận 2026-09-28) | n/a | n/a | 0 B | CME market data cần entitlement owner | không đo được gì (0 byte) | news→rates-leg class (DTPFX-B) vẫn khóa | Chọn MỘT: mở đường mạng hợp lệ tới *.cmegroup.com (ISP/network config) HOẶC chỉ định venue broker-grade có license cho rate futures intraday |
| 6a | CME (transport) | **BLOCKED_TRANSPORT (SNI-keyed)** — re-measured 2026-09-28 với discrimination experiment (no-SNI handshake OK 0.07 s; with-SNI bị giết post-TLS) | n/a | n/a | transcript `cme_rates/probe_transport_transcript.json` | 0 B fetch được | chưa tới bước license (transport chết trước) | n/a | mọi cơ chế cần CME data | Một hành động: yêu cầu nhà mạng/IT mở SNI cho *.cmegroup.com trên đường mạng được phép (không tự lách) |
| 6b | SOFR/EFFR daily (NY Fed official — để phân biệt với #5) | **AVAILABLE_VALIDATED** (đã có từ trước; liveness re-check 200 hôm nay) | daily, publication-day granularity | effectiveDate + revisionIndicator machine-served | payload 1.149 B mẫu (EFFR 2026-09-24 3.88%) | ~KB/request | official, entitled, keyless | n/a (không phải chi phí giao dịch) | daily conditioning (không phải intraday leg) | không cần |

## Lane artifacts

- L-FX: `ibkr_fx/` (collector sha `b35e2d29…` class, S0 sanitized,
  L-FX_REPORT, HANDOFF_L-FX; scheduled fix 14:50Z + rollover 20:50Z).
- L-CX: `cx/` (collect_binance_l2.py, sample_deribit_options.py,
  probe_onchain.py, 3 reports, HANDOFF_CX — 7 changed paths, 8 tests).
- L-RATES: `cme_rates/` (transcript + L-RATES_REPORT + HANDOFF).
- Erratum: beside the Saturday verdict (see §Erratum).
- Total new bytes this session ≈ 16.5 MB (2.0 MB FX raw + 14.2 MB CX
  raw + control files) — disk 25 GiB free at close.

## Erratum (P1 cross-check)

`research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/broker_cost_probe_FX_majors_2026-09/ERRATUM_2026-09-28_sixsource.md`:
E1 sửa phân loại "NOT_SUBSCRIBED" của verdict thứ Bảy 2026-09-26 →
nguyên nhân thật là weekend closure (cửa sổ đo 01:47 ET thứ Bảy); dữ
liệu two-sided LIVE đang chảy, entitlement tồn tại. E2 ghi rõ tiền đề
"spread tối thiểu 0.5 pip" (từ secdef minTick) mâu thuẫn với stream
thực 0.1 pip — nhưng P3-A KHÔNG được mở lại bởi erratum (no-rescue
law; reopener là gate của owner).

## Đề xuất pilot lịch sử nhỏ + ngân sách (trước bất kỳ mua dữ liệu)

1. **IBKR FX (0 đồng):** tích lũy cost-band bằng các phiên bounded
   read-only đã đặt lịch (fix 14:50Z / rollover 20:50Z hôm nay; sau đó
   2–3 phiên/tuần × 10–25 phút, mỗi phiên <5 MB) + statement của owner
   cho 6 component còn lại. Không mua gì.
2. **Crypto L2 (0 đồng, disk là rào):** capture tiếp 2 symbol × 2 tuần
   với cap gzip ~≤5 GB (đĩa còn 25 GiB — ổn); chỉ sau đó mới cân nhắc
   quote vendor L2 lịch sử (Tardis/Laevitas-class) — quyết định mua là
   owner, chưa đề nghị mua bây giờ.
3. **Deribit options (0 đồng):** nếu sample hợp lệ, pilot lịch sử = One
  expiry-month archive chính thức nếu được phục vụ keyless; không mua
   gói.
4. **On-chain (0 đồng):** giữ ở mức probe; historical on-chain cần
   indexer/vendor — chỉ đề xuất khi một cơ chế preregistered gọi tên.
5. **Rates/CME:** không pilot được cho tới khi blocker transport được
   owner xử lý.

## Standing disclosures

- Hai phiên sampled đã đặt lịch sẽ tự ghi sanitized + sessions_index;
  nếu máy ngủ/TWS đóng tại cửa sổ → NOT_RUN_TWS_DOWN ghi trung thực.
- Không số đẹp nào ở đây là "5 năm phút giá đẹp làm cost-band": duy nhất
  streaming bounded, ghi đầy đủ gap/silence.
