# 02 - Continuous batching under load (u50)

Host `Windows-AMD64` · `--parallel 4` · 14 samples over
60s at 2.0s intervals · raw CSV: `02-server-metrics-u50.csv`

| Gauge | Peak observed |
|:--|--:|
| `n_busy_slots_per_decode` (avg/decode) | 3.90 of 4 slots (97%) |
| `requests_processing` | 4 |
| `requests_deferred` | 46 |
| `kv_cache_usage_ratio` | n/a — not exported by llama.cpp `b10488` |
| `tokens_predicted_total` (final) | 2279 |

Highest sampled value was **3.90 of 4** slots. Note this gauge is llama.cpp's *average* busy slots per decode step, so the number below is the highest average we sampled, not an instantaneous maximum batch width. A peak near 1 means
requests were served one at a time -- either the load was too light to overlap, or
they arrived too far apart. A peak approaching `--parallel` means the scheduler was
genuinely packing concurrent requests into shared decode steps.
`requests_deferred` went above zero: more requests arrived than there were slots, so some waited. That wait is the queue time in your P95.

## Your observation

Highest sampled average busy slots là **3.90/4**, lớn hơn 1 rõ ràng;
đồng thời quan sát processing=4 và deferred=46. Continuous batching hoạt động,
nhưng server vẫn có hàng đợi lớn khi 50 users cùng chờ.

`n_busy_slots_per_decode` là số slots trung bình trên decode step, không phải peak
batch width tức thời hay phần trăm sử dụng CPU. Effective concurrency 9,3 từ load
report gồm cả thời gian chờ và chịu sai lệch vì request chưa hoàn thành; nó không đo
cùng đại lượng với busy slots, nên không ép hai số phải khớp.

Thu được 14 scrape thành công trong cửa sổ 60 s, chạy chồng với load-50;
`--interval 2` là thời gian sleep giữa scrape, thời gian HTTP làm khoảng cách thực tế
dài hơn 2 s. Gauge busy slots ở mẫu đầu còn phản ánh decode trước đó; các mẫu sau
có processing=4/deferred>0 chứng minh được hoạt động dưới tải hiện tại.
Không có metric KV ratio được export nên giữ n/a, không điền 0 thay cho thiếu số đo.
