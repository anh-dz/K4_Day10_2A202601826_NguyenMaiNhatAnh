# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Mai Nhật Anh             |
| MSSV               | 2A202601826                    |
| Khóa/Lớp         | K4              |
| Tên nhóm         | BabyShark    |
| Vai trò chính    | End-to-End Pipeline Lead & Developer |
| Repository         | https://github.com/anh-dz/K4_Day10_2A202601826_NguyenMaiNhatAnh |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Raw Data Ingestion | `src/ingestion/crossref.py` | Crossref API HTTP Response | Raw JSON API response & Parsed records in `data/raw/` | Hoàn thành |
| Cleaning & Modeling | `src/ingestion/cleaning.py` | Parsed Paper Records | Clean DataFrame & CSV/JSON artifacts in `data/clean/` | Hoàn thành |
| Embedding & Indexing | `src/retrieval/index.py` | Clean DataFrame | ChromaDB Vector Store & Manifest in `data/embeddings/` | Hoàn thành |
| Testset Generation & Eval | `src/evaluation/testset.py`, `src/evaluation/metrics.py` | Clean DataFrame & ChromaDB Index | Synthetic Test Set, Baseline & Comparison Metrics JSON | Hoàn thành |
| Data Observability & Quality | `src/observability/quality.py` | Clean / Corrupted / Repaired DataFrames | Data Quality JSON & Freshness Report JSON in `data/quality/` | Hoàn thành |
| Reporting & Markdown Export | `src/observability/reporting.py` | Evaluation Metrics & Quality Results | `phase1_report.md` & `corruption_report.md` in `data/reports/` | Hoàn thành |
| Data Corruption & Repair Flow | `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py` | Clean DataFrame & Raw JSON Records | Corrupted & Repaired datasets, Corruption Log JSON | Hoàn thành |
| Pipeline Orchestration & CLI | `src/pipelines/phase1.py`, `script/cli.py`, `script/test_pipeline.py` | Settings & Config | End-to-end execution CLI, Test validation suite (8/8 PASS) | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --------- | ----------------------------- | ------- |
| Tích hợp Local LLM Model (LM Studio) | RAG Agent & LLM Provider Abstraction (`src/retrieval/llm.py`, `src/retrieval/agent.py`) | Giúp hệ thống hoạt động 100% không phụ thuộc Cloud API credit, hỗ trợ test offline mượt mà |
| Xây dựng CLI & Test Suite | Đảm bảo tính Reproducible cho bài tập | Cung cấp lệnh `script/cli.py` và script kiểm thử `script/test_pipeline.py` đạt điểm Bonus tối đa |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Ingestion & Data Cleaning | `src/ingestion/crossref.py`, `cleaning.py` | `data/raw/crossref_records.json`, `data/clean/papers_clean.csv` | `uv run python script/cli.py status` |
| Baseline Pipeline & Evaluation | `src/pipelines/phase1.py` | `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` | `uv run python script/cli.py phase1` |
| Corruption & Repair Flow | `src/pipelines/corruption_flow.py` | `data/results/corrupted_metrics.json`, `repaired_metrics.json`, `corruption_report.md` | `uv run python script/cli.py corruption` |
| Verification Test Suite | `script/test_pipeline.py` | 8/8 automated validation checks passed | `uv run python script/test_pipeline.py` |

**Mô tả output cụ thể:**
Hệ thống tạo ra toàn bộ chuỗi artifacts hoàn chỉnh gồm: dữ liệu thô `crossref_records.json` (24 bài báo), dữ liệu sạch `papers_clean.csv`, bộ test set tổng hợp `test_set.json` (36 câu hỏi thuộc 3 loại), bộ chỉ số đánh giá `baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json`, cùng hai báo cáo Markdown tổng hợp chi tiết (`phase1_report.md` và `corruption_report.md`) kèm biểu đồ trực quan ASCII.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Xây dựng một Data Pipeline chuẩn hóa cho ứng dụng RAG từ khâu thu thập thông tin bài báo khoa học trên Crossref, làm sạch, lập chỉ mục vector trên ChromaDB, đánh giá hiệu năng RAG Agent (Hit Rate, Token F1, LLM Judge Score), thiết lập Data Quality & Freshness Monitoring, và thực nghiệm quy trình Data Corruption - Repair để đo lường tác động của "dữ liệu rác" tới chất lượng câu trả lời của AI.

### Cách triển khai
- **Ingestion & Cleaning**: Sử dụng HTTP GET với cơ chế exponential backoff khi gặp HTTP 429/503. Làm sạch thẻ XML/JATS bằng Regex. Ghép các thuộc tính tiêu đề, tóm tắt, tác giả, danh mục thành thuộc tính `text_for_embedding`. Loại bỏ bài trùng `paper_id` hoặc thiếu tiêu đề/tóm tắt.
- **Evaluation Set & Indexing**: Sinh bộ câu hỏi kiểm thử tổng hợp (Synthetic QA) gồm 36 câu hỏi từ 12 bài báo tiêu biểu. Sử dụng model `sentence-transformers/all-MiniLM-L6-v2` để tạo embedding vector lưu trong ChromaDB persistent store.
- **Observability**: Triển khai 6 bài kiểm tra Data Quality (row_count, paper_id_not_null_unique, title_not_null, summary_length, freshness 180 ngày, no_duplicates).
- **Corruption & Repair Flow**: Giả lập 6 lỗi dữ liệu (Drop latest, Blank summary, Noise injection, Title truncation, Stale dates, Duplicates) làm suy giảm chất lượng dữ liệu. Sau đó khôi phục (Repair) bằng cách tái làm sạch từ file raw JSON lưu trữ ban đầu.

### Input, output và contract

| Thành phần | Mô tả |
| ---------- | ------ |
| Input | Crossref API works endpoint (`query=agentic retrieval augmented generation large language model`, `rows=24`) |
| Output | Data artifacts (`raw/`, `clean/`, `embeddings/`, `eval/`, `quality/`, `results/`, `reports/`) |
| Module phụ thuộc | `src/core/config.py`, `src/core/utils.py` |
| Module sử dụng output | `src/retrieval/agent.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` |
| Điều kiện lỗi cần xử lý | Lỗi rate limit 429/503 từ API, dữ liệu thiếu abstract/title, trùng lặp paper_id, lỗi out-of-credit từ LLM API |

### Cách xác minh

```bash
uv run python script/test_pipeline.py
```

- **Kết quả mong đợi:** 8/8 bài test tự động vượt qua (PASS), xác nhận toàn bộ 18+ artifacts tồn tại, đúng cấu trúc schema và các chỉ số đo đạc đúng logic.
- **Kết quả thực tế:** 8/8 tests passed 100%.
- **Artifact/log:** `data/reports/phase1_report.md`, `data/reports/corruption_report.md`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn phương án tích hợp LLM Provider để đánh giá RAG Agent và làm LLM Judge. Các Cloud API như Gemini / OpenAI / OpenRouter dễ bị lỗi 503 (high demand), 429 (rate limit) hoặc 402 (Out of credit) khi thực hiện đánh giá số lượng lớn câu hỏi.
- **Các phương án đã cân nhắc:**
  1. Phương án 1: Phụ thuộc hoàn toàn vào Cloud LLM API.
  2. Phương án 2: Xây dựng Abstraction tương thích với OpenAI SDK, cho phép tùy chọn chuyển sang Local LLM (LM Studio / Ollama) thông qua tùy chỉnh `.env`.
- **Phương án đã chọn:** Phương án 2 (`LLM_PROVIDER=custom`, endpoint `http://127.0.0.1:1234/v1`).
- **Lý do:** Tối ưu chi phí, khả năng chạy offline không giới hạn credit, đảm bảo quy trình kiểm thử và đánh giá hoàn toàn tin cậy và có thể tái hiện (reproducible).
- **Bằng chứng quyết định phù hợp:** Chạy đánh giá thành công 100% với model local `google/gemma-4-e4b` trên LM Studio, đạt điểm số chính xác và nhất quán.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ValueError: Unknown format code 'd' for object of type 'float'` tại dòng 288 file `src/observability/reporting.py`.
- **Lệnh hoặc bước tái hiện:** `uv run python script/run_corruption_flow.py`
- **Nguyên nhân gốc:** Format specifier `:d` chỉ chấp nhận kiểu số nguyên (int), nhưng biến khoảng chênh lệch `diff_corrupt` / `diff_repair` có thể là kiểu số thực (float) khi chỉ số `mean_judge_score` là số thập phân (ví dụ: 4.1388).
- **Cách xử lý:** Thay đổi định dạng từ `:d` thành `:+g` trong `src/observability/reporting.py` để xử lý linh hoạt cả số nguyên và số thực.
- **Cách xác minh sau khi sửa:** Chạy `uv run python script/cli.py corruption` -> Báo cáo `corruption_report.md` được sinh ra thành công mà không gặp lỗi.
- **Bài học:** Cần chú ý type handling trong Python f-string formatting khi làm việc với các chỉ số đo đạc có thể biến động kiểu dữ liệu.

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời:**

1. **Dữ liệu đi từ Crossref đến vector index:** Dữ liệu raw JSON từ Crossref API được parse thành các đối tượng `PaperRecord`, sau đó qua bước cleaning để lọc bỏ trùng lặp/bản ghi lỗi và tạo cột `text_for_embedding`. Thuộc tính văn bản này được đưa qua model `sentence-transformers/all-MiniLM-L6-v2` để sinh ra các định dạng vector embeddings 384 chiều, sau đó được đưa vào lưu trữ lâu dài tại ChromaDB Vector Collection.
2. **Evaluation set và ground-truth document IDs:** Bộ Synthetic Test Set được sinh tự động chứa các câu hỏi kiểm thử kèm theo `ground_truth` (câu trả lời chuẩn) và `ground_truth_doc_ids` (ID tài liệu chứa đáp án). Khi RAG Agent tìm kiếm và trả lời, hệ thống so sánh các tài liệu agent tìm được với `ground_truth_doc_ids` để đo `retrieval_hit_rate`, và so sánh văn bản câu trả lời với `ground_truth` để tính `mean_token_f1` cùng `judge_accuracy`.
3. **Quality checks vs Freshness monitoring:** Quality checks tập trung vào tính toàn vẹn của cấu trúc dữ liệu tĩnh (dữ liệu không null, tiêu đề không rỗng, không trùng paper_id, độ dài summary đạt chuẩn). Trong khi đó, Freshness monitoring tập trung vào tính mới theo thời gian (kiểm tra ngày xuất bản gần nhất, xa nhất và số bản ghi quá hạn 180 ngày so với mốc thời gian chạy).
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired:** Để đảm bảo nguyên tắc kiểm thử cùng điều kiện (apples-to-apples comparison / controlled benchmark). Giữ nguyên test set giúp số liệu phản ánh chính xác sự thay đổi của chất lượng hệ thống RAG do yếu tố dữ liệu đầu vào gây ra, chứ không phải do câu hỏi khó/dễ thay đổi.
5. **Repair được xem là thành công dựa trên artifact và metric:** Repair thành công khi `repaired_quality.json` chuyển trạng thái từ `FAIL` thành `PASS` (6/6 checks pass), `repaired_freshness_report.json` đạt `is_fresh: true`, và trong `repaired_metrics.json`, các chỉ số `retrieval_hit_rate` phục hồi từ 0.8333 lên 1.0, `mean_token_f1` phục hồi từ 0.7719 lên 1.0.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |   1.0000 |    0.8333 |   1.0000 | Dữ liệu rác làm suy giảm 16.67% khả năng tìm kiếm tài liệu đúng do tiêu đề bị cắt ngắn và tóm tắt rỗng. Sau khi repair, chỉ số phục hồi 100%. |
| `mean_token_f1`      |   1.0000 |    0.7719 |   1.0000 | Chất lượng nội dung câu trả lời giảm 22.81% do bị nhiễu thông tin (noise injection) và thiếu abstract. Phục hồi hoàn toàn về 1.0. |
| `judge_accuracy`     |   0.9722 |    0.7778 |   1.0000 | Tỷ lệ đánh giá chính xác giảm mạnh ở bản corrupted do thông tin sai lệch và phục hồi tối đa sau khi khôi phục dữ liệu thô. |
| `mean_judge_score`   |   5.0000 |    4.1389 |   5.0000 | Điểm đánh giá trung bình bị giảm từ 5.0 xuống 4.14/5.0 và đạt điểm tuyệt đối 5.0 sau repair. |
| Quality checks         | PASS (6/6)| FAIL (2/6)| PASS (6/6)| Hệ thống quality checks phát hiện chính xác 4 lỗi dữ liệu được bơm vào (duplicate, short summary, stale date, non-unique id). |
| Freshness status       |    FRESH |     STALE |    FRESH | Freshness monitoring phát hiện đúng 3 bản ghi bị sửa ngày xuất bản về quá khứ (năm 2020). |

### Kết luận từ số liệu

1. **[Data corruption]** (Blank summary, title truncation, noise injection, stale dates) → **[quality checks FAIL 2/6, freshness STALE 3/24]** → **[retrieval_hit_rate giảm xuống 0.8333, mean_token_f1 giảm xuống 0.7719]**.
2. **[Repair action từ raw Crossref JSON]** → **[quality checks khôi phục PASS 6/6, freshness status FRESH]** → **[retrieval_hit_rate và mean_token_f1 phục hồi hoàn toàn về 1.0000]**.

**Corruption nào ảnh hưởng rõ nhất và vì sao?**
Kịch bản **Blank Summary** và **Noise Injection** ảnh hưởng nặng nề nhất tới `mean_token_f1` và `judge_score` vì chúng làm sai lệch nội dung vector embedding của tài liệu, khiến RAG Agent trả lời thiếu ý hoặc lan man. Kịch bản **Title Truncation** làm hỏng cơ chế tra cứu chính xác (`lookup_paper`), khiến `retrieval_hit_rate` sụt giảm rõ rệt.

**Kết quả nào khác với kỳ vọng ban đầu?**
Ban đầu tôi dự đoán `retrieval_hit_rate` ở bản corrupted có thể giảm sâu hơn nữa (dưới 0.70). Tuy nhiên kết quả thực tế chỉ giảm về 0.8333 do model embedding `all-MiniLM-L6-v2` vẫn nhận diện được một số từ khóa liên quan từ tiêu đề chưa bị xóa hoặc từ các bản ghi không bị corrupt.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Data Pipeline**: Việc lưu trữ dữ liệu thô ban đầu (Raw Data Ingestion) dưới dạng Immutable Snapshot là vô cùng quan trọng để hệ thống có khả năng tự khôi phục (Self-healing / Repair) khi gặp sự cố dữ liệu rác.
2. **Data Quality & Observability**: Việc thiết lập các chốt kiểm duyệt dữ liệu tự động (Quality & Freshness Checks) ở cuối giai đoạn ETL giúp phát hiện sớm các bất thường dữ liệu trước khi chúng làm hỏng trải nghiệm người dùng cuối.
3. **Ảnh hưởng của Data đến RAG Agent**: "Garbage In, Garbage Out" — hiệu năng của một RAG Agent phụ thuộc rất lớn vào chất lượng dữ liệu làm sạch. Ngay cả khi dùng LLM tiên tiến, dữ liệu bẩn vẫn gây ra hiện tượng suy giảm chất lượng nghiêm trọng.

### Nếu có thêm thời gian

Tôi sẽ triển khai thêm cơ chế **Automated Real-time Alerts** (gửi thông báo qua Slack/Webhook khi Quality check bị FAIL) và tích hợp thư viện **Great Expectations / Ragas** nâng sâu để tự động hóa hoàn toàn khâu Data Auditing trong sản xuất.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Mai Nhật Anh  
**Ngày xác nhận:** 2026-08-06  
