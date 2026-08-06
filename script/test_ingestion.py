import sys
from pathlib import Path
from datetime import datetime, UTC

# Add src to sys.path so we can import from it easily
sys.path.append(str(Path(__file__).parent.parent / "src"))

from core.config import load_settings
from ingestion.crossref import fetch_source_records
from ingestion.cleaning import build_clean_dataframe, save_clean_dataframe
from evaluation.testset import build_test_set

def main():
    print("🚀 Bắt đầu test các hàm Bước 3, 4, 5...\n")
    
    # Tải cấu hình (Settings)
    settings = load_settings()
    
    print("--- 1. Testing Fetch (Bước 3) ---")
    records = fetch_source_records(settings)
    print(f"✅ Đã fetch thành công {len(records)} bài báo từ Crossref API.")
    print(f"✅ Đã lưu raw api response vào: {settings.paths.raw_api_response}")
    print(f"✅ Đã lưu raw records vào: {settings.paths.raw_records_json}\n")
    
    print("--- 2. Testing Clean (Bước 4) ---")
    df = build_clean_dataframe(records, datetime.now(UTC))
    print(f"✅ Làm sạch xong. Dataframe có shape: {df.shape}")
    save_clean_dataframe(df, settings.paths.clean_csv, settings.paths.clean_json)
    print(f"✅ Đã lưu cleaned CSV vào: {settings.paths.clean_csv}")
    print(f"✅ Đã lưu cleaned JSON vào: {settings.paths.clean_json}\n")
    
    print("--- 3. Testing Test Set (Bước 5) ---")
    test_set = build_test_set(df, settings.paths.eval_testset)
    print(f"✅ Đã sinh ra {len(test_set)} câu hỏi đánh giá.")
    print(f"✅ Đã lưu test set vào: {settings.paths.eval_testset}")
    
    if test_set:
        print(f"\n📝 Câu hỏi mẫu sinh ra:\n- Loại: {test_set[0]['question_type']}\n- Câu hỏi: {test_set[0]['question']}\n- Đáp án (Ground Truth): {test_set[0]['ground_truth'][:100]}...")

if __name__ == "__main__":
    main()
