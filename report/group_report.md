# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K4              |
| Tên nhóm         | BabyShark     |
| Repository         | https://github.com/anh-dz/K4_Day10_2A202601826_NguyenMaiNhatAnh |
| Ngày hoàn thành | 2026-08-06               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Mai Nhật Anh | 2A202601826 | End-to-End Pipeline Lead & Developer | Toàn bộ codebase (`src/`), CLI & validation scripts (`script/`), và dữ liệu thực nghiệm (`data/`) |

## 2. Tóm tắt kết quả

Nhóm cá nhân (1 thành viên) đã xây dựng và hoàn thành 100% hai phase của hệ thống Data Pipeline & Data Observability dành cho RAG Agent.

Ở **Phase 1 (Baseline)**, hệ thống tự động thu thập 24 bản ghi metadata từ Crossref API, làm sạch dữ liệu, lập chỉ mục vector trên ChromaDB với model `all-MiniLM-L6-v2`, tự động tạo bộ synthetic test set 36 câu hỏi kiểm thử và đánh giá chỉ số baseline đạt tuyệt đối: `retrieval_hit_rate` = 1.0, `mean_token_f1` = 1.0, `judge_accuracy` = 0.9722 và `mean_judge_score` = 5.0/5.0. Bộ kiểm tra Data Quality đạt 6/6 PASS và Data Freshness đạt trạng thái FRESH.

Ở **Phase 2 (Corruption & Repair Flow)**, nhóm giả lập 6 loại lỗi dữ liệu (Blank summary, Noise injection, Title truncation, Stale dates, Duplicates, Drop latest records). Dữ liệu rác đã làm suy giảm đo lường được trên RAG Agent: `retrieval_hit_rate` giảm xuống 0.8333, `mean_token_f1` giảm xuống 0.7719, `judge_accuracy` giảm xuống 0.7778 và Data Quality chuyển sang FAIL (chỉ 2/6 checks pass). Khi thực hiện quy trình Repair bằng cách tái làm sạch từ dữ liệu thô (raw JSON immutable snapshot), toàn bộ chỉ số chất lượng và data quality đã phục hồi hoàn hảo về mức Baseline ban đầu.

Hệ thống đi kèm công cụ CLI tiện lợi (`script/cli.py`) và bộ kiểm thử tự động 8/8 bài test PASS (`script/test_pipeline.py`).

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API
    -> raw response / raw records (data/raw/)
    -> cleaning & data modeling (data/clean/)
    -> embedding + ChromaDB index (data/embeddings/ & data/chroma/)
    -> evaluation baseline (data/results/ & data/eval/)
    -> quality/freshness reports (data/quality/ & data/reports/phase1_report.md)
    -> data corruption (data/results/corruption_log.json)
    -> re-index & re-evaluate corrupted pipeline
    -> repair từ dữ liệu nguồn raw records
    -> re-index & re-evaluate repaired pipeline
    -> comparison report (data/reports/corruption_report.md)
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| ----- | ----- | ----------- | --------------- | ----- |
| Ingestion | Crossref API Endpoint | Fetch API với retry backoff, parse payload | `data/raw/crossref_response.json`, `crossref_records.json` | Nguyễn Mai Nhật Anh |
| Cleaning | Raw JSON Records | Strip JATS XML, drop duplicates, tạo `text_for_embedding` | `data/clean/papers_clean.csv`, `papers_clean.json` | Nguyễn Mai Nhật Anh |
| Embedding/index | Clean DataFrame | Sinh embedding bằng MiniLM-L6-v2, index ChromaDB | `data/embeddings/papers_embeddings.json`, `data/chroma/` | Nguyễn Mai Nhật Anh |
| Evaluation | Clean DF & Index | Tạo synthetic test set (36 câu hỏi), đo F1/HitRate/Judge | `data/eval/test_set.json`, `data/results/baseline_metrics.json` | Nguyễn Mai Nhật Anh |
| Observability | Clean/Corrupted DF | Kiểm tra 6 chỉ số Data Quality & Freshness (180 ngày) | `data/quality/baseline_quality.json`, `freshness_report.json` | Nguyễn Mai Nhật Anh |
| Corruption/repair | Clean DF & Raw JSON | Biến đổi 6 lỗi dữ liệu nhân tạo; tái làm sạch từ raw data | `papers_clean_corrupted.csv`, `papers_clean_repaired.csv` | Nguyễn Mai Nhật Anh |
| Orchestration | Settings & CLI | Điều phối luồng Phase 1, Phase 2, CLI & Test suite | `data/reports/phase1_report.md`, `corruption_report.md` | Nguyễn Mai Nhật Anh |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER` | `custom` (LM Studio Local) hoặc `gemini` / `openrouter` |
| `LLM_MODEL` | `google/gemma-4-e4b` hoặc `gemini-2.5-flash` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 records |
| Retrieval `top_k` | 4 |
| Freshness threshold | 180 ngày |
| Random seed, nếu có | Fixed deterministic evaluation seed |

### Lệnh cài đặt

```bash
uv sync
```

### Lệnh chạy

Chạy toàn bộ từ đầu đến cuối (Phase 1 + Phase 2 + Reports):

```bash
uv run python script/cli.py all
```

Hoặc chạy từng pha riêng biệt:

```bash
# Phase 1: Baseline pipeline
uv run python script/run_phase1.py

# Phase 2: Corruption & Repair flow
uv run python script/run_corruption_flow.py

# Kiểm thử tự động tính toàn vẹn 100%
uv run python script/test_pipeline.py
```

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| ----- | ---------- | ----------------------- | ---------- |
| Baseline pipeline | Thành công 100% | 2026-08-06 19:18 UTC | `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` |
| Corruption flow | Thành công 100% | 2026-08-06 19:29 UTC | `data/results/corrupted_metrics.json`, `repaired_metrics.json`, `corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| ----------- | ------- |
| Source | Crossref API (`https://api.crossref.org/works`) |
| Query/filter | `query=agentic retrieval augmented generation large language model`, `filter=type:journal-article` |
| Thời điểm lấy dữ liệu | 2026-08-06 |
| Số record nhận được | 24 records |
| Cơ chế retry/backoff | Max 3 retries, exponential backoff (1s, 2s, 4s) khi gặp 429/503 HTTP status |

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| ------- | ------------ | ---------- | ------- | ------------------- |
| `paper_id` | `str` | Có | ID duy nhất dạng `crossref:{doi}` | Bắt buộc có, bỏ qua bản ghi nếu rỗng |
| `title` | `str` | Có | Tiêu đề bài báo | Chuẩn hóa khoảng trắng, bỏ bản ghi nếu rỗng |
| `summary` | `str` | Có | Tóm tắt/Abstract bài báo | Strip thẻ XML/JATS bằng Regex, bỏ bản ghi nếu rỗng |
| `authors` | `list[str]` | Không | Danh sách tác giả | Để danh sách rỗng `[]` nếu không có |
| `published` | `str` | Có | Ngày xuất bản (`YYYY-MM-DD`) | Parse từ `published-online` / `published-print` |
| `categories` | `list[str]` | Không | Danh mục chủ đề | Lấy thuộc tính `subject` của Crossref |
| `text_for_embedding` | `str` | Có | Chuỗi văn bản tổng hợp để làm vector embedding | Ghép title + summary + authors + categories |
| `age_days` | `int` | Có | Tuổi của bài báo tính theo ngày | `(now - published).days` |

### Quy tắc cleaning

| Quy tắc | Quality dimension liên quan | Số record bị tác động | Cách xác minh |
| ------- | --------------------------- | ---------------------: | ------------- |
| Lọc bản ghi thiếu title/summary | Completeness | 0/24 | Check `title_not_null` & `summary_length` in `baseline_quality.json` |
| Loại bỏ trùng lặp theo `paper_id` | Uniqueness | 0/24 | Check `no_duplicates` in `baseline_quality.json` |
| Strip thẻ XML/JATS trong Abstract | Validity | 24/24 | Regex replacement `_strip_jats` in `src/ingestion/crossref.py` |
| Chuẩn hóa định dạng ngày xuất bản | Timeliness | 24/24 | Check `published` format `YYYY-MM-DD` in `papers_clean.csv` |

**Cách tạo `text_for_embedding`, document ID và `age_days`:**
- `document_id`: Đặt trùng với `paper_id` (dạng `crossref:10.xxx/yyy`) để dễ tra cứu chính xác.
- `text_for_embedding`: Định dạng chuỗi ghép `Title: {title} | Abstract: {summary} | Authors: {authors} | Subjects: {categories}`.
- `age_days`: Tính số ngày chênh lệch giữa mốc `run_date` (UTC) và `published_date`.

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| ---------- | ---------------- |
| Số câu hỏi | 36 câu hỏi tổng hợp |
| Các `question_type` | `summary`, `authors`, `date` |
| Ground-truth document ID | Đối chiếu chính xác theo `paper_id` của bài báo gốc sinh ra câu hỏi |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| Vector store/collection | ChromaDB persistent store (`data/chroma/`) collection `papers_collection` |
| Retrieval `top_k` | 4 |
| LLM provider/model | `custom` / `google/gemma-4-e4b` (LM Studio Local) |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` (36 samples) |

**Vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:**
Giữ cố định bộ test set là điều kiện bắt buộc để thực hiện bài thử nghiệm kiểm chứng độc lập (controlled experiment / apples-to-apples comparison). Điều này đảm bảo mọi biến động của các chỉ số (Hit Rate, Token F1, Judge Score) hoàn toàn do sự thay đổi của **chất lượng dữ liệu trong Vector DB**, chứ không phải do sự thay đổi của độ khó câu hỏi.

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn thực tế | Trạng thái | Ghi chú |
| -------- | ----------------- | ---------- | ------- |
| Raw response/records | `data/raw/` | Có | `crossref_response.json` (174KB) & `crossref_records.json` (26KB) |
| Cleaned dataset | `data/clean/` | Có | `papers_clean.csv` (25KB) & `papers_clean.json` (28KB) |
| Embedding manifest/index | `data/embeddings/` & `data/chroma/` | Có | `papers_embeddings.json` (24 docs) & SQLite database |
| Evaluation set | `data/eval/` | Có | `test_set.json` (36 câu hỏi tổng hợp) |
| Baseline metrics | `data/results/baseline_metrics.json` | Có | hit_rate=1.0, f1=1.0, judge_accuracy=0.9722, score=5.0 |
| Quality/freshness | `data/quality/` | Có | `baseline_quality.json` (PASS 6/6) & `freshness_report.json` (FRESH) |
| Baseline report | `data/reports/phase1_report.md` | Có | Markdown report kèm biểu đồ ASCII |

### Baseline metrics

| Metric | Giá trị | Diễn giải |
| ------ | -------: | --------- |
| `retrieval_hit_rate` | 1.0000 | 100% câu hỏi tìm kiếm đúng tài liệu gốc chứa đáp án |
| `mean_token_f1` | 1.0000 | Tỷ lệ trùng khớp từ vựng giữa câu trả lời RAG và ground-truth đạt điểm tuyệt đối |
| `judge_accuracy` | 0.9722 | 35/36 câu hỏi được LLM Judge chấm điểm chính xác (>= 4/5) |
| `mean_judge_score` | 5.0000 | Điểm đánh giá chất lượng câu trả lời đạt mức tối đa 5/5 |
| Ragas, nếu có | Skipped | Đã tắt Ragas pass mặc định để tối ưu tốc độ (bật lại bằng `RUN_RAGAS=1`) |

## 8. Data quality và freshness

### Quality checks

| Check | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
| ----- | ----------------- | ------------------ | ----------------------- | ------------ |
| `row_count` | Completeness | Total rows >= 1 | ✅ PASS (24 rows) | `baseline_quality.json` |
| `paper_id_not_null_unique` | Uniqueness | Unique IDs: 24/24 | ✅ PASS (24/24 unique) | `baseline_quality.json` |
| `title_not_null` | Validity | Null/empty titles: 0 | ✅ PASS (0 empty) | `baseline_quality.json` |
| `summary_length` | Completeness | Summaries >= 20 chars | ✅ PASS (0 short) | `baseline_quality.json` |
| `freshness` | Timeliness | Stale rows (>180d): 0 | ✅ PASS (0 stale) | `baseline_quality.json` |
| `no_duplicates` | Uniqueness | Duplicate rows: 0 | ✅ PASS (0 duplicate) | `baseline_quality.json` |

### Freshness

| Thuộc tính | Giá trị |
| ---------- | ------- |
| Freshness được đo tại | Cleaned DataFrame `papers_clean.csv` |
| Timestamp mới nhất | `2026-08-01` |
| Timestamp xa nhất | `2026-02-12` |
| Ngưỡng freshness | 180 ngày |
| Trạng thái baseline | **FRESH** (`is_fresh: true`) |
| Lý do | Tất cả 24 bản ghi đều có ngày xuất bản trong vòng 180 ngày so với thời điểm chạy |

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair |
| ---------- | -------- | ------------------: | ---------------------- | --------------------- | ----------- |
| Drop Latest | Xóa 2 bản ghi mới nhất | 2 records | Thất thoát bài báo mới | Giảm retrieval hit rate | Khôi phục lại từ `crossref_records.json` |
| Blank Summary | Xóa sạch abstract | 2 rows | `summary_length` FAIL | RAG trả lời lan man, F1 giảm | Load lại abstract thô từ raw JSON |
| Noise Injection | Bơm từ rác vào summary | 2 summaries | Nhiễu thông tin vector | Giảm similarity score & LLM score | Tái làm sạch văn bản gốc |
| Title Truncation | Cắt tiêu đề còn 10 ký tự | 2 titles | Hỏng tra cứu exact-match | Tra cứu exact ID/title thất bại | Lấy lại title chuẩn từ raw JSON |
| Stale Dates | Sửa ngày xuất bản về 2020-01-01 | 3 records | `freshness` FAIL (Stale) | Freshness report chuyển STALE | Khôi phục đúng date từ raw JSON |
| Duplicates | Nhân đôi 2 bản ghi bất kỳ | 2 rows | `no_duplicates` FAIL | Nhân bản ID, làm nhiễu index | Áp dụng lại `drop_duplicates` |

**Corruption log:**
- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log ghi nhận đầy đủ 6 loại corruption, danh sách các record_id bị tác động và các tham số áp dụng.

**Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy:**
Quy trình Repair không dùng kỹ thuật "sửa chữa vá lỗi thủ công" trên dataframe bẩn mà thực hiện **re-ingestion & re-cleaning** trực tiếp từ file immutable raw JSON snapshot (`data/raw/crossref_records.json`). Kỹ thuật này đảm bảo dữ liệu phục hồi hoàn toàn nguyên bản, tin cậy và không để lại tác dụng phụ của dữ liệu bẩn.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét |
| ------------- | -------: | --------: | -------: | ----------------------: | -------------: | -------- |
| `retrieval_hit_rate` | 1.0000 | 0.8333 | 1.0000 | -0.1667 (-16.67%) | +0.1667 (100%) | Phục hồi hoàn hảo về 1.0 |
| `mean_token_f1` | 1.0000 | 0.7719 | 1.0000 | -0.2281 (-22.81%) | +0.2281 (100%) | Phục hồi hoàn hảo về 1.0 |
| `judge_accuracy` | 0.9722 | 0.7778 | 1.0000 | -0.1944 (-19.44%) | +0.2222 (100%) | Đạt điểm tuyệt đối 100% |
| `mean_judge_score` | 5.0000 | 4.1389 | 5.0000 | -0.8611 (-0.86/5) | +0.8611 (100%) | Đạt mức điểm tối đa 5/5 |
| Quality checks pass/fail | PASS (6/6) | FAIL (2/6) | PASS (6/6) | -4 checks pass | +4 checks pass | Phát hiện và khắc phục 100% lỗi |
| Freshness status | FRESH | STALE (3/24) | FRESH | Chuyển thành STALE | Trở lại FRESH | Loại bỏ hoàn toàn bản ghi quá hạn |

**Hai kết luận nhân quả dựa trên artifacts:**

1. **[Data corruption (Blank summary, Title truncation, Stale dates)]** → **[Quality checks FAIL 2/6, Freshness status STALE (3/24)]** → **[Retrieval hit rate giảm 16.67%, Mean token F1 giảm 22.81%]**.
2. **[Repair action từ raw Crossref JSON]** → **[Quality checks khôi phục PASS 6/6, Freshness status FRESH]** → **[Retrieval hit rate và Mean token F1 phục hồi 100% về mốc 1.0000]**.

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Khi sinh báo cáo so sánh ở bước cuối Phase 2, chương trình văng lỗi `ValueError: Unknown format code 'd' for object of type 'float'`.
- **Nguyên nhân:** Xâu chuỗi f-string định dạng `:d` bắt buộc biến số là `int`, nhưng thuộc tính hiệu số `diff_corrupt` lại nhận giá trị `float` (khi metric là `mean_judge_score = 4.1389`).
- **Cách xử lý:** Đổi định dạng từ `:d` thành `:+g` trong file `src/observability/reporting.py` để hỗ trợ định dạng linh hoạt cho cả kiểu số nguyên lẫn số thực.
- **Cách xác minh:** Chạy lại `uv run python script/cli.py corruption` -> Báo cáo `data/reports/corruption_report.md` được sinh ra thành công mà không gặp lỗi crash.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Đánh giá Ragas pass hiện bị tắt mặc định | Chưa có đầy đủ chỉ số Faithfulness và Answer Relevancy của Ragas | Bật lại tùy chọn `RUN_RAGAS=1` khi chạy trên môi trường có API LLM ổn định |
| Quy mô dữ liệu nhỏ (24 bài báo) | Chưa kiểm thử được hiệu năng của ChromaDB ở quy mô lớn (hàng vạn bài báo) | Tăng cấu hình `max_results=500` trong Crossref fetcher để đo latency retrieval |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
