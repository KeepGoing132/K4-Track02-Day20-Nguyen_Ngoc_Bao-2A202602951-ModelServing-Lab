# 01 - Tune: thread-count sweep

Model `gemma-4-E2B-it-UD-Q4_K_XL.gguf` · host `Windows-AMD64` · llama.cpp `b10488`
CPU: **14 physical · 20 logical** cores · `ngl=0` · metric `tg128`

| threads (-t) | tg128 (tok/s) | vs best |
|:--|--:|--:|
| 1 | 2.7 | 10% |
| 7 | 23.9 | 92% |
| 14 | 25.9 | 100% |
| 20 | 20.9 | 81% |
| 40 | 11.8 | 46% |

**Best**: `-t 14` at 25.9 tok/s
**Slowest tested**: `-t 1` at 2.7 tok/s (9.57x spread)
**Against the physical-core default** (`-t 14`, 25.9 tok/s): 1.00x

Use this in your run:

```bash
LAB_N_THREADS=14 make bench
```

## Your explanation

Đỉnh của lưới thử nằm ở `-t 14`: 25.85 tok/s.
Chọn 20 logical threads thay vì 14 physical cores làm throughput giảm từ 25.85
xuống 20.90 tok/s; đổi 20 → 14 cải thiện 1.24×. 40 threads chỉ đạt
11.81 tok/s.

Decode lặp lại việc truy cập weights; thêm thread giúp chia việc cho tới khi các
tài nguyên chung như bộ nhớ/cache trở thành giới hạn. Thêm logical threads không
thêm memory channels, còn 40 threads vượt 20 logical processors gây oversubscription
và tăng chi phí scheduling/cache. Curve này phù hợp với cơ chế tranh chấp tài nguyên,
nhưng chưa đo hardware counters để chứng minh memory bandwidth là nguyên nhân duy nhất.

i7-12700H có kiến trúc lai; không ghim affinity nên không khẳng định mỗi thread ở
cấu hình 14 chạy trên một physical core riêng. Mỗi điểm có 2 repetitions, thứ tự tăng
thread, chưa kiểm soát nhiệt độ/power state. `raw_output` trong JSON giữ cả mean và `±`.
Default của lab vốn là 14 threads: speedup so với **default** vẫn là 1,00×;
1.24× là so với lựa chọn dùng hết 20 logical threads, không đổi tên baseline.

Lần sweep đầu hiển thị hỏng ký tự `±` do binary Windows dùng ANSI; đã sửa decoder
và chạy lại toàn bộ sweep cùng cấu hình. Không ghép số của hai lần chạy để tạo speedup.
Log lần cuối: [evidence/tune.txt](evidence/tune.txt).
