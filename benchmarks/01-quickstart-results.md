# 01 - Measure: latency baseline

Model `Gemma 4 E2B` · host `Windows-AMD64` · llama.cpp `b10488`
Settings: `threads=14` `ngl=0` `ctx=2048`
`max_tokens=64` · warm-up discarded
Completed requests: `UD-Q4_K_XL` 10/10 · `UD-Q2_K_XL` 10/10

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|:--|--:|--:|--:|--:|--:|--:|
| UD-Q4_K_XL | 2.97 | 5209 | 688 / 933 | 45.0 / 46.7 | 3550 / 3766 / 3766 | 22.2 |
| UD-Q2_K_XL | 2.24 | 4328 | 771 / 931 | 41.4 / 44.7 | 3374 / 3692 / 3692 | 24.2 |

- **TTFT** = prefill. Short prompts keep it small; long-context RAG is where it explodes.
- **TPOT** = per-output-token decode cost, bounded by memory bandwidth. `decode tok/s = 1000 / TPOT_p50`.
- `UD-Q2_K_XL` decodes **1.09x faster** than `UD-Q4_K_XL` here, for 0.73 GB less on disk.

## Your observation

2-bit nhanh 1,09× (24,2 so với 22,2 tok/s), giảm 0,73 GiB. Cả hai giải thích sai TTFT/TPOT; 2-bit còn mô tả prefix cache như web cache. Giữ 4-bit làm baseline, thêm context RAG và kiểm chứng câu trả lời. Mẫu 64 token chưa đủ kết luận chất lượng tổng thể.

### Giới hạn phép đo

- TTFT đo phía client: gồm HTTP, xử lý prompt và thời gian đến token đầu; không phải phép đo thuần prefill của engine. TPOT dùng số token từ timings của server (cả 20 request đều có timings), không đếm chunk để giả làm token.
- Chỉ 10 mẫu mỗi quantization. Theo nearest-rank, P95 và P99 đều là mẫu lớn nhất; không diễn giải chúng như ước lượng tail latency ổn định.
- Kích thước cột GB thực chất là GiB (bytes / 1024³). Load gồm khởi động server và polling health, không chỉ đọc weights.
- Cùng 10 prompt, temperature 0,7, không cố định seed; nhiều câu trả lời bị giới hạn ở 64 token. Phép thử này phục vụ baseline tốc độ, chưa phải eval chất lượng có kiểm soát.
- Mẫu câu trả lời thật và phân tích: [01-quality-comparison.md](01-quality-comparison.md). Số đo từng request nằm trong JSON cùng tên; command và thời điểm nằm trong [evidence/bench.txt](evidence/bench.txt).
