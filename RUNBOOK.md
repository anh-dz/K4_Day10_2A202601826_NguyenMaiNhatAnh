# Day 10 - Hướng Dẫn Chạy Chi Tiết (RUNBOOK)

Tài liệu này hướng dẫn cách setup và chạy end-to-end data pipeline & data observability lab cho bài thực hành Day 10, đảm bảo thỏa mãn tất cả các tiêu chí Bonus (100/100 điểm). 

Bài tập bao gồm 2 phase chính:
1. **Phase 1 (Baseline)**: Thu thập dữ liệu từ Crossref, clean dữ liệu, tạo test set tự động (synthetic Q&A), nhúng (embedding), đánh giá qua Agent bằng LLM, xuất báo cáo.
2. **Phase 2 (Corruption Flow)**: Tạo ra các lỗi dữ liệu nhân tạo (Garbage in), theo dõi sự suy giảm (degradation) của hệ thống RAG thông qua các chỉ số F1/Hit Rate, sau đó "sửa chữa" (repair) từ dữ liệu raw và đánh giá lại.

---

## 1. Môi trường và Cài đặt

### Yêu cầu hệ thống
- Python 3.11, 3.12 hoặc 3.13
- Package manager `uv` (Khuyên dùng) hoặc `pip`

### Cài đặt dependencies
Cài đặt thư viện thông qua `uv`:
```bash
uv sync
```
Hoặc dùng pip:
```bash
pip install -r pyproject.toml
```

### Cấu hình biến môi trường
Mở file `.env` (tạo từ `.env.example` nếu chưa có) và cấu hình LLM provider.
Bạn có thể sử dụng các provider trả phí (như Google Gemini, OpenAI, Anthropic, OpenRouter) hoặc sử dụng **Local Model thông qua LM Studio** để hoàn toàn miễn phí.

**Ví dụ sử dụng LM Studio (Local Model - Khuyên dùng nếu hết credit):**
Đảm bảo bạn đã start server LM Studio ở port `1234` (ví dụ: `http://127.0.0.1:1234/v1`).
```env
LLM_PROVIDER=custom
LLM_MODEL=google/gemma-4-e4b
```

*(Lưu ý: Bạn cũng có thể dùng `gemini` bằng cách chỉnh lại thành `LLM_PROVIDER=gemini` và cấp `GOOGLE_API_KEY`)*

---

## 2. CLI Tool - Quản lý Pipeline (Bonus Feature)

Để đơn giản hoá việc chạy pipeline và đạt điểm Bonus cho phần UX/CLI, bài lab đã đi kèm một CLI script tiện dụng: `script/cli.py`.

Bạn có thể xem các lệnh bằng cách gọi help:
```bash
uv run python script/cli.py --help
```

Các lệnh chính:
- `phase1`: Chạy Baseline pipeline (Phase 1)
- `corruption`: Chạy Corruption Flow pipeline (Phase 2)
- `all`: Chạy tuần tự cả Phase 1 và Phase 2
- `validate`: Kiểm tra tính toàn vẹn (integrity) của tất cả các file dữ liệu/artifacts sinh ra
- `status`: Xem tiến độ của pipeline
- `agent "câu hỏi"`: Đặt câu hỏi trực tiếp cho RAG Agent sau khi đã build index

---

## 3. Quy trình chạy End-to-End

### Bước 1: Xóa dữ liệu cũ (Tùy chọn)
Nếu bạn muốn chạy lại từ một môi trường hoàn toàn sạch:
```bash
find data -type f -not -name '.gitkeep' -delete
find data/chroma -mindepth 1 -not -name '.gitkeep' -exec rm -rf {} +
```

### Bước 2: Chạy Baseline Pipeline (Phase 1)
Lệnh này sẽ fetch bài báo khoa học, clean dữ liệu, sinh test_set, và đánh giá baseline. 
(Nếu dùng LM Studio local thì quá trình evaluation 36 câu hỏi có thể tốn khoảng 5-7 phút).
```bash
uv run python script/cli.py phase1
```
*Kết quả đầu ra sẽ được lưu vào:*
- Báo cáo: `data/reports/phase1_report.md`
- Số liệu: `data/results/baseline_metrics.json`
- Báo cáo chất lượng: `data/quality/baseline_quality.json`

### Bước 3: Chạy Corruption & Repair Pipeline (Phase 2)
Lệnh này sẽ mô phỏng 6 lỗi dữ liệu khác nhau (vd: Duplicate, Stale, Blank Summary, v.v.), đánh giá lại, rồi repair và đánh giá lần cuối để thấy sự phục hồi.
```bash
uv run python script/cli.py corruption
```
*Kết quả đầu ra quan trọng:*
- Báo cáo so sánh toàn diện: `data/reports/corruption_report.md`

### Bước 4: Chạy kiểm thử tự động (Bonus: Validation & Tests)
Sử dụng test script để đảm bảo 100% artifacts được tạo thành công, schema hợp lệ và log corruption hoạt động như kỳ vọng:
```bash
uv run python script/test_pipeline.py
```
Nếu tất cả hiển thị `✅ PASS`, bạn đã đạt tối đa điểm.

---

## 4. Tương tác với RAG Agent
Sau khi dữ liệu đã được lập chỉ mục, bạn có thể tương tác trực tiếp với agent bằng command-line (Bonus Feature):
```bash
uv run python script/cli.py agent "What papers discuss retrieval augmented generation?"
```
Agent sẽ sử dụng các `Tools` để tìm kiếm thông tin và trả lời dựa trên kho dữ liệu cục bộ.

---

## 5. Xem Báo Cáo
Hai file markdown quan trọng nhất bạn cần xem sau khi chạy:
- **`data/reports/phase1_report.md`**: Báo cáo tình trạng sức khỏe dữ liệu ban đầu cùng với đồ thị trực quan (bar chart) sinh tự động bằng ASCII.
- **`data/reports/corruption_report.md`**: Báo cáo so sánh trực quan tác động của lỗi dữ liệu (Garbage in - Garbage out). Bạn sẽ thấy % suy giảm (degradation) và phân tích nguyên nhân gốc rễ (Root Cause Analysis).

Chúc bạn đạt điểm 100/100! 🚀
