# Chạy lại và hoàn tất bài nộp

## Đo trên máy này

Môi trường được cài trong `.venv`, model nằm trong `models/` và runtime nằm trong
`runtime/b10488/`. Các file lớn này được Git bỏ qua đúng theo đề bài.

```powershell
.venv\Scripts\python.exe scripts\run-lab.py
```

Lệnh chạy probe, benchmark hai quantization, sweep thread, server, smoke,
load 10 users, load 50 users đồng thời với metrics, rồi 3 query RAG. Hai load test
dùng đúng 60 giây; server được chờ hết request giữa các bước và tắt khi hoàn tất.
Các phép đo dùng CPU (`ngl=0`), 14 threads, 4 slots, context tổng 2048,
reasoning off, 64 tokens cho benchmark, 48/96 tokens cho load test.

Lần chạy lại sẽ ghi đè báo cáo được sinh tự động. Cần đọc số mới và cập nhật phần
nhận xét cùng `REFLECTION.md`; không giữ lại nhận xét cho số liệu của lần cũ.

## Bằng chứng gốc

`benchmarks/evidence/` chứa stdout/stderr thực tế, command, cấu hình và thời điểm UTC.
`01-quickstart-results.json` giữ từng prompt/câu trả lời/số đo; tuning JSON giữ output
gốc của `llama-bench`. `requests-10.jsonl` và `requests-50.jsonl` giữ thời gian của
từng request hoàn thành để đối chiếu thống kê và goodput.

## Năm ảnh chụp thật

Đã chụp đủ 5 ảnh thật của cửa sổ PowerShell trong `submission/screenshots/` theo
yêu cầu của người học. Ảnh hiển thị **log lưu từ lần chạy thật**, không phải phép đo
chạy lại vào thời điểm chụp. Cỡ chữ được giảm trong cửa sổ để bảng hiện đầy đủ.
Các ảnh dựng sẵn từ script cũ đã được chuyển vào thư mục sao lưu local, không dùng
trong bài nộp.

Chụp lại tự động trên desktop Windows đang mở khóa:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/capture-screenshots.ps1
```

Script mở từng cửa sổ PowerShell riêng, hiển thị log gốc, chụp pixel màn hình của
cửa sổ đó rồi đóng tiến trình vừa tạo. Có thể chụp thủ công như sau.

Mở PowerShell, phóng cửa sổ đủ rộng, chạy từng lệnh sau và dùng Snipping Tool để
chụp sát vùng dữ liệu. Đây là **log lưu từ lần chạy thật**, không chạy lại phép đo:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/show-evidence.ps1 probe
powershell -ExecutionPolicy Bypass -File scripts/show-evidence.ps1 bench
powershell -ExecutionPolicy Bypass -File scripts/show-evidence.ps1 smoke
powershell -ExecutionPolicy Bypass -File scripts/show-evidence.ps1 load-10
powershell -ExecutionPolicy Bypass -File scripts/show-evidence.ps1 load-50
```

Lưu lần lượt vào `submission/screenshots/01-hardware-probe.png`, `02-bench.png`,
`03-serve-and-smoke.png`, `04-locust-10.png`, `05-locust-50.png`. Hai ảnh Locust phải
thấy request count, RPS và cột 50%/95%/99%. Có thể xem cùng log bằng trình duyệt:

```powershell
.venv\Scripts\python.exe scripts/gen_screenshots.py
# Mở submission/evidence.html để xem; script này không tạo ảnh giả.
```

Nếu coach yêu cầu ảnh demo trực tiếp đang chạy, mở hai terminal với cùng cấu hình:

```powershell
$env:LAB_N_GPU_LAYERS='0'
$env:LAB_N_THREADS='14'
$env:LAB_PARALLEL='4'
.\lab.ps1 serve
# Terminal thứ hai: .\lab.ps1 smoke
```

Chụp server và smoke cùng nhau hoặc thành `03a-` / `03b-` theo hướng dẫn gốc.

## Kiểm tra và nộp

Đọc lại phần phân tích, kiểm tra mình giải thích được cơ chế và giữ khai báo dùng AI.
Kiểm tra lại sau khi cập nhật file:

```powershell
git add submission/screenshots
.\lab.ps1 verify
```

Lần kiểm tra hiện tại đã đạt `verify exit 0`; đối chiếu dữ liệu bằng
`.venv\Scripts\python.exe scripts\audit-results.py` cũng đạt. Commit các thay đổi,
tạo repo **public** tên `K4-L3-DAY20-NguyenNgocBao-2A202602951-ModelServing`, push,
rồi paste URL vào LMS. Remote hiện tại là repo đề bài; không push bài cá nhân lên đó.
Việc public repo/push/LMS chưa được thực hiện trong phiên hỗ trợ này.
