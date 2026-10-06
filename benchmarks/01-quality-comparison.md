# So sánh câu trả lời thực tế của hai quantization

Cùng 10 prompt của benchmark, temperature 0,7 và max_tokens=64, reasoning off.
Nguồn: `01-quickstart-results.json`, trường `requests`. Không cố định seed;
đây là quan sát mẫu, không phải eval accuracy hay kết luận thống kê.

## Explain TTFT and TPOT in one sentence each.

**UD-Q4_K_XL — output nguyên văn:**

```text
**TTFT (Time to First Target)** is a metric used to measure the latency from an event or request to the moment the first relevant data or target is received.

**TPOT (Time to Process)** is a metric that quantifies the total time required for a system or process to complete its entire execution or
```

**UD-Q2_K_XL — output nguyên văn:**

```text
**TTFT (Time To Failure)** is a measure of the time it takes for a system or process to completely fail or cease functioning.

**TPOT (Time To Production)** is a measure of the time it takes for a system or process to go from an initial state to a fully functional, productive state.
```

**Nhận xét:** Cả hai sai thuật ngữ trong ngữ cảnh serving. Q4 giải thích TTFT thành Time to First Target và TPOT thành Time to Process; Q2 dùng Time To Failure / Time To Production. Định nghĩa cần dùng là Time To First Token và Time Per Output Token theo docs/labs/01-measure.md.

## Explain prefix caching in two sentences.

**UD-Q4_K_XL — output nguyên văn:**

```text
Prefix caching is a technique used to store the results of common or frequently requested operations based on a shared prefix. This allows the system to quickly retrieve pre-computed answers for similar requests, significantly improving performance and reducing redundant computations.
```

**UD-Q2_K_XL — output nguyên văn:**

```text
Prefix caching is a technique used in web development to store pre-computed results for frequently requested URLs or resources. Instead of recalculating the response every time, the system checks if a cached version is available, and if so, serves that stored result directly, significantly improving performance and reducing server load.
```

**Nhận xét:** Q4 mô tả cache kết quả chung, chưa giải thích KV cache của prefix token. Q2 mô tả cache URL/tài nguyên web, lệch ngữ cảnh inference. Vì vậy cả hai cần context và kiểm chứng khi dùng làm trợ giảng kỹ thuật.

## Why does FlashAttention need less memory than naive attention?

**UD-Q4_K_XL — output nguyên văn:**

```text
FlashAttention achieves significantly less memory usage than naive attention primarily by **changing the way attention is computed and accessed in memory, specifically by leveraging tiling and block-wise operations to minimize the number of slow, high-bandwidth memory accesses.**

Here is a detailed breakdown of why this is the case, contrasting it with naive attention
```

**UD-Q2_K_XL — output nguyên văn:**

```text
FlashAttention needs less memory than naive attention primarily because of **how it handles the computation and memory access during the attention mechanism**, leading to significant memory savings compared to the standard, naive implementation.

Here's a breakdown of the key reasons:

---

## 1. The Core Difference: Tensors and Memory
```

**Nhận xét:** Q4 đề cập tiling/block-wise operations trong đoạn đầu. Q2 mới giới thiệu vấn đề khi hết ngân sách. Không coi câu bị cắt là bằng chứng độc lập rằng quantization làm mất kiến thức: giới hạn 64 token là yếu tố gây nhiễu.

## Quyết định

2-bit tiết kiệm dung lượng và nhanh hơn khoảng 9% trong lần đo này. Với 23,6 GB RAM,
4-bit được giữ làm baseline để hạn chế mất precision, nhưng các lỗi trên cho thấy
không nên triển khai bất kỳ bản nào làm trợ giảng kỹ thuật chỉ từ kiến thức model.
Cần kiểm chứng RAG, thêm prompt ngắn rõ ngữ cảnh và một bộ eval có đáp án trước
khi kết luận bản nào đủ chất lượng. Không dùng quan sát này để khẳng định mọi
câu trả lời 2-bit đều kém hơn hoặc 4-bit luôn chính xác.
