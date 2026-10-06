# 02 - Serve: load test + saturation reading

Host `Windows-AMD64` · llama.cpp `b10488` ·
`--parallel 4` · `ctx=2048` · `threads=14` ·
`ngl=0`

| Users | Reqs | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 10 | 19 | 0.32 | 24000 | 37000 | 37000 | 6.9 | 0.0% |
| 50 | 19 | 0.32 | 29000 | 59000 | 59000 | 9.3 | 0.0% |

*Effective concurrency = RPS x average latency (Little's Law) -- how many requests were
really in flight, regardless of how many users locust simulated. It counts queued requests
too, so the occupancy/slot ratio can legitimately exceed 1.0; it is occupancy, not
utilisation. For true slot utilisation use the server's own gauges (`make metrics`).*

## What these two runs say

| Going from 10 to 50 users | |
|:--|--:|
| Offered load | 5x |
| Throughput actually delivered | **1.00x** (20% of linear) |
| P95 latency | **1.59x** |
| Effective concurrency at 50 users | 9.3 vs `--parallel 4` slots (occupancy/slot ratio 2.33) |

**Saturated.** Throughput delivered only 1.00x for 5x the offered load, and effective concurrency (9.3) is at or above all 4 decode slots. Saturation sets in somewhere at or below 50 users; the load you added beyond that point became queue time rather than throughput.

Throughput moved 1.00x while P95 moved 1.59x. That gap is the goodput argument: past saturation you buy throughput by spending latency, and if your SLO is a P95 target then the requests you added are no longer being served within it. (This lab does not fix an SLO number for you -- pick one in your write-up and state how much goodput you keep at it.)

> **Small sample.** Only 19 requests completed in the
> shorter run, so these percentiles are indicative rather than solid. Note also that
> locust averages only *completed* requests: when the run ends with requests still
> queued, effective concurrency is an **under**-estimate. Trust the throughput-scaling
> row over the concurrency row here, and run longer (`-t 3m`) if you want firmer numbers.

## Your reading

Tăng số users 10 → 50 (5×) chỉ cho throughput 1.00×, trong khi P95 tăng
1.59× (37 → 59 giây). Throughput gần như plateau.
Ở 10 users, L ≈ 6.9 đã vượt 4 slots; ở 50 users,
L ≈ 9.3. Dấu hiệu quá tải xuất hiện ngay ở mức 10;
chưa xác định knee dưới 10 vì chỉ thử hai mức.

Bằng chứng trực tiếp là metrics có `requests_processing=4` và
`requests_deferred=46` khi chạy 50 users. Các request đã phải chờ slot.
Không dùng Little's Law để suy ra một tỷ lệ chính xác của **P95** là queue time:
L dùng latency trung bình, không dùng percentile; prefill/decode cũng có thể chậm đi
dưới tải và workload short/long không đồng nhất.

### Goodput theo SLO đã chọn

SLO: request HTTP thành công và **E2E ≤ 15.000 ms**. Đây là ngưỡng để phân tích,
chưa phải cam kết production. Đếm từ từng request hoàn thành trong log JSONL:

| Users | Completed | Thành công ≤ 15 s | Goodput (req/s) |
|--:|--:|--:|--:|
| 10 | 19 | 4 | 0.068 |
| 50 | 19 | 4 | 0.068 |

Goodput = RPS của Locust × số request thành công trong SLO / tổng request hoàn thành.
Hai mức đều không đạt mục tiêu P95 ≤ 15 s. Knob thử đầu tiên là admission control:
giới hạn in-flight/queue để request còn cơ hội hoàn thành trong ngân sách, rồi đo lại
goodput và tỷ lệ từ chối. Đây là **đề xuất chưa triển khai**, không tuyên bố đã cải thiện.
Tăng `--parallel` cần thử riêng vì nhiều slot không làm tăng memory bandwidth.

### Giới hạn kết luận

- Mỗi lần chỉ hoàn thành 19 request trong 60 s; percentile mỏng, Locust làm tròn bin.
- Request chưa xong khi stop bị censored, không nằm trong các percentile này. 0% failures
  chỉ áp dụng cho request **đã ghi nhận hoàn thành**, không nghĩa là mọi request đã được phục vụ.
- 5× ở đây là số users, không chứng minh arrival rate tăng đúng 5×: Locust là tải closed loop.
- RPS × W ≈ 9,3 khác ảnh backlog 4 + 46 là hợp lý: một bên là ước lượng trung bình
  từ request đã hoàn thành, bên kia là peak tức thời. Không yêu cầu chúng bằng nhau.
- Đối chiếu số liệu: `scripts/audit-results.py`; dữ liệu SLO: `02-goodput-slo.json`;
  log gốc: [evidence/locust-10.txt](evidence/locust-10.txt), [evidence/locust-50.txt](evidence/locust-50.txt).
