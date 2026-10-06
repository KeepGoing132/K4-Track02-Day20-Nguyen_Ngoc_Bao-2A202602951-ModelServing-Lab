# 03 - Integrate: RAG pipeline run

Host `Windows-AMD64` · llama.cpp `b10488` ·
retrieval backend: **keyword overlap** · 3 queries

| Query | Contexts retrieved | embed (ms) | retrieve (ms) | llm (ms) | total (ms) |
|:--|--:|--:|--:|--:|--:|
| Why is goodput more useful than raw throughp... | goodput, paged, radix | 0.0 | 0.1 | 5452.4 | 5452.5 |
| What problem does PagedAttention actually so... | paged, radix, disagg | 0.0 | 0.1 | 4580.9 | 4581.0 |
| When does splitting prefill and decode help?... | disagg, radix, batching | 0.0 | 0.1 | 4576.0 | 4576.1 |

Mean per stage (ms): embed **0.0** · retrieve **0.1** ·
llm **4869.8** · total **4869.9**
Dominant stage: **llm** (100% of total)

## Answers returned

**Why is goodput more useful than raw throughput?**

> Goodput@SLO counts only the requests per second that met the TTFT and TPOT targets. Throughput at saturation ignores SLOs.

**What problem does PagedAttention actually solve?**

> PagedAttention stores the KV cache in non-contiguous pages, removing the internal fragmentation that wasted most GPU memory.

**When does splitting prefill and decode help?**

> Splitting prefill and decode helps because prefill is compute-bound and decode is memory-bandwidth-bound.


## Which N16-N19 pieces are real

| Day | Thành phần được dùng | Real / stub |
|---|---|---|
| N16 | Localhost trên laptop Windows, không provision cloud/IaC | stub |
| N17 | 6 tài liệu TOY_DOCS trong bộ nhớ, không có DAG thực | stub |
| N18 | List/dict tài liệu, không có lakehouse service | stub |
| N19 | Keyword overlap, không có vector index/Feast hay embedding endpoint | stub |
| N20 | llama-server b10488, /v1/chat/completions | real |

Ba query có context provenance và câu trả lời thật trong JSON. Query goodput còn lấy
hai tài liệu score=0 do chọn top-3: retrieval toy chưa có relevance threshold.

LLM stage chiếm gần 100% tổng thời gian (4869.8 ms so với
4869.9 ms), phù hợp với corpus chỉ 6 tài liệu. Tuy nhiên stage
`llm` là **wall time của lời gọi HTTP**, không chỉ thời gian chạy model: mean server
prefill + decode ≈ 2495.7 ms, thấp hơn mean client khoảng
2374.1 ms. Chưa đo riêng DNS/connect/client setup nên
không quy toàn bộ khoảng chênh thành compute hay queue time.

Muốn giảm latency 2×, trước hết tách overhead HTTP (thử reuse client và so localhost
với 127.0.0.1), rồi đo lại. Sau đó tối ưu prefill/decode hoặc thử GPU offload với cùng
prompt. Prefix caching chỉ giảm phần prefix được tái sử dụng; speculative decoding
chưa được chạy và không có bằng chứng đảm bảo speedup 2× ở đây.

Log gốc: [evidence/pipeline.txt](evidence/pipeline.txt).
