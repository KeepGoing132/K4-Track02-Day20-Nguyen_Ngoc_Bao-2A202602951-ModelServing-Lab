# Reflection — Day 20 Model Serving

- **Họ Tên:** Nguyễn Ngọc Bảo
- **MSSV:** 2A202602951
- **Cohort:** A20-K4
- **Ngày thực hiện:** 2026-10-06 (UTC+7)

Số liệu dưới đây sinh từ laptop được khai báo, không dùng số viết sẵn của bản nháp trước.
Phần phân tích được AI hỗ trợ soạn thành bản nháp; cần đọc và tự giải thích trước khi nộp.

## 1. Hardware & runtime

- OS: Windows 11 Home Single Language, build 26200, AMD64. Python `platform.release()`
  báo `10` trong hardware.json; caption Windows 11 được đối chiếu bằng CIM.
- CPU: 12th Gen Intel Core i7-12700H, 14 physical / 20 logical cores.
- RAM: 23,6 GiB. GPU có sẵn: NVIDIA GeForce RTX 3050 Ti Laptop GPU, 4096 MiB.
- Python 3.11.9; llama.cpp b10488, commit 9d77fa172, asset
  `llama-b10488-bin-win-cuda-12.4-x64.zip` và cudart DLLs.
- Model: Gemma 4 E2B, UD-Q4_K_XL + UD-Q2_K_XL. Hai file khớp SHA-256 từ Hugging Face;
  revision, hashes và phiên bản packages ở `benchmarks/evidence/model-integrity.json`.
- Chạy **local trên laptop này**, không dùng cloud. Base track dùng **CPU, ngl=0**;
  GPU được phát hiện nhưng không được dùng trong những số đo này.
- Baseline/serve: threads=14, parallel=4, ctx tổng=2048, reasoning off. Benchmark 64
  output tokens, temperature=0,7; load short/long 48/96 tokens, temperature=0,5.
  Context là tổng server, khoảng 512 tokens mỗi slot khi parallel=4.

**Setup story:** Windows cần UTF-8 cho Python/report và decoder ANSI cho ký tự ± của
binary native. Download qua hf_hub_download bị treo; tải trực tiếp từ URL chính thức
bằng curl rồi kiểm tra SHA-256 và ghi manifest. Sweep được chạy lại sau khi sửa decoder.
Không ghim CPU affinity hay kiểm soát nhiệt độ; ghi nhận điều này khi đọc speedup.

## 2. Đo lường

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|:--|--:|--:|--:|--:|--:|--:|
| UD-Q4_K_XL | 2.97 | 5209 | 688 / 933 | 45.0 / 46.7 | 3550 / 3766 / 3766 | 22.2 |
| UD-Q2_K_XL | 2.24 | 4328 | 771 / 931 | 41.4 / 44.7 | 3374 / 3692 / 3692 | 24.2 |

**Quan sát:** 2-bit nhanh 1.09×, giảm 0,73 GiB. Cả hai giải thích sai
TTFT/TPOT; 2-bit còn mô tả prefix cache như web cache. Giữ 4-bit làm baseline,
thêm context RAG và kiểm chứng câu trả lời. Mẫu 64 token chưa đủ kết luận chất lượng tổng thể.

Mỗi quantization có 10/10 request, warm-up bỏ qua, số token lấy từ server timings.
P95/P99 nearest-rank với n=10 đều là max. TTFT bao gồm overhead phía client và token đầu,
không đồng nhất với engine prefill. Cột GB dùng đơn vị GiB. Xem
`benchmarks/01-quality-comparison.md` để đọc các câu trả lời được lưu nguyên văn.

## 3. Serving under load

| Users | Reqs | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 10 | 19 | 0.32 | 24000 | 37000 | 37000 | 6.9 | 0.0% |
| 50 | 19 | 0.32 | 29000 | 59000 | 59000 | 9.3 | 0.0% |

- Tăng users 5×; RPS tăng 1.00×, P95 tăng 1.59×.
- L tại 50 users ≈ 9.3, so với 4 slots.
- Peak average `n_busy_slots_per_decode`: 3.90/4; processing peak=4,
  deferred peak=46. Có 14 mẫu metrics trong cửa sổ load-50.
- Smoke trả completion và `tokens_predicted_total` tăng 0 → 19.

**Saturation reading:** Throughput plateau giữa 10 và 50 users, P95 tăng mạnh;
metrics có 46 request chờ chứng minh queueing. Chưa tìm knee dưới 10, chưa tách
chính xác queue/compute của P95. Thử admission control trước để hạn chế queue,
đo lại goodput và tỷ lệ từ chối; tăng parallel không tự tăng bandwidth.

**SLO phân tích:** HTTP thành công và E2E ≤ 15 s.

| Users | Completed | Thành công ≤ 15 s | Goodput (req/s) |
|--:|--:|--:|--:|
| 10 | 19 | 4 | 0.068 |
| 50 | 19 | 4 | 0.068 |

Goodput tính bằng RPS × tỷ lệ request hoàn thành trong SLO. Mỗi mức chỉ hoàn thành 19
request; request còn chờ khi stop không được tính. Vì thế L là ước lượng từ các request
đã hoàn thành, không phải snapshot backlog, và 0% failures chưa có nghĩa là tất cả
request đến đều được phục vụ. Không diễn giải percentile này như thống kê production.

## 4. Integration

| Day | Piece | Real / stub |
|---|---|---|
| N16 | Localhost Windows; không provision cloud/IaC | stub |
| N17 | 6 tài liệu TOY_DOCS in-memory | stub |
| N18 | List/dict tài liệu thay lakehouse | stub |
| N19 | Keyword overlap; không embedding/vector/Feast thực | stub |
| N20 | llama-server /v1/chat/completions | real |

Mean của 3 query: embed **0.0 ms**, retrieve **0.1 ms**,
llm **4869.8 ms**, total **4869.9 ms**.
Stage llm chiếm gần 100%; cả 3 query có context và câu trả lời trong JSON/log.

**Reflection:** LLM stage là bottleneck, phù hợp corpus nhỏ. Đây là wall time HTTP;
engine prefill+decode chỉ khoảng 2496 ms. Muốn giảm 2×, đo overhead kết nối/client
trước, rồi tối ưu prefill/decode. Chưa có bằng chứng prefix cache hay speculative
decoding tự đem lại 2×.

## 5. The single change that mattered most

**Change:** Chọn 14 physical-core threads thay cho dùng hết 20 logical threads,
trên cùng model 4-bit và CPU-only. Nguồn: sweep tg128, mỗi điểm 2 repetitions.

```text
before:  -t 20 → 20.90 tok/s
after:   -t 14 → 25.85 tok/s
speedup: 1.24x
```

Decode liên tục truy cập weights. Thêm thread giúp chia việc, nhưng khi memory/cache
đã thành giới hạn thì logical threads bổ sung không tạo thêm memory channels;
các luồng phải chia sẻ tài nguyên execution/cache và chi phí scheduling tăng.
Curve đạt đỉnh ở 14, giảm ở 20 và giảm sâu khi oversubscribe 40 threads. Kết quả
phù hợp với cơ chế tranh chấp tài nguyên, không phải quy tắc “càng nhiều thread càng nhanh”.

Không có affinity pinning trên CPU lai nên không khẳng định mỗi thread chạy riêng
một physical core. Chưa có memory-bandwidth counters để chứng minh nguyên nhân duy nhất.
Hai repetitions và thứ tự sweep cố định còn nhạy với nhiệt độ/power state. Speedup
1.24× so với **20 logical threads**; default của lab vốn là 14, nên so với default
là **1,00×**. Không trộn throughput HTTP ở §2 với tg128 native để tính gain.

## 6. Bonus

Không làm bonus trong bài này. So sánh hai quantization và thread sweep là base track;
không nhận chúng thành bằng chứng B2/B3 và không tuyên bố đã chạy quantization ladder.

## 7. Điều đáng chú ý

Server chạy và trả HTTP 200 không bảo đảm kiến thức đúng: cả hai quantization đều
hiểu sai acronyms TTFT/TPOT khi thiếu ngữ cảnh. RAG trên toy corpus trả lời bám context
hơn, nhưng retrieval vẫn có tài liệu score=0; cần eval riêng trước khi triển khai.

## 8. Self-check trước khi nộp

- [x] Hardware probe và model manifest sinh từ máy này; hashes đã kiểm tra.
- [x] Benchmark đủ hai quantization và số token thực, thread sweep có raw output.
- [x] Serve + smoke, load 10/50 users mỗi lần 60 s, metrics chạy chồng load-50.
- [x] Pipeline đủ 3 query; khai báo đúng real/stub và latency theo stage.
- [x] Đã thay phần nhận xét bắt buộc và đối chiếu log request với JSON/CSV.
- [x] 5 screenshots thật trong `submission/screenshots/`, hiển thị log của lần chạy thật.
- [x] `lab.ps1 verify` exit 0 sau khi thêm đủ ảnh thật; audit dữ liệu PASS.
- [ ] Đọc, xác nhận và tự giải thích phần lập luận của bản nháp này.
- [ ] Commit và push lên repo public đúng tên
  `K4-L3-DAY20-NguyenNgocBao-2A202602951-ModelServing`.
- [ ] Paste public URL vào LMS trước deadline được coach áp dụng.

Đã mở PowerShell và chụp pixel cửa sổ theo yêu cầu của người học. Ảnh hiển thị log
lưu từ lần chạy thật, không phải demo đang chạy lại. Các ảnh dựng sẵn cũ đã được
chuyển vào backup local. Xem `submission/RUNBOOK.md` và `submission/evidence.html`
để đối chiếu đầu ra gốc. Không đánh dấu đã push/public/nộp LMS khi chưa thực hiện.

## 9. Khai báo sử dụng AI

Sử dụng OpenAI Codex để đọc yêu cầu, sửa lỗi Windows, tự động chạy lab, lưu/đối chiếu
log thực tế và hỗ trợ soạn bản nháp báo cáo. Số đo trong bài này lấy từ các lệnh chạy
trên laptop đã khai báo. Ảnh dựng từ script cũ và số viết sẵn của bản nháp trước không
được dùng làm bằng chứng. Người học cần đọc, xác nhận và tự giải thích các nhận xét
trước khi nộp; AI chưa thay người học thực hiện bước nộp bài.
