import unittest
import pandas as pd
from datetime import datetime, UTC

from ingestion.cleaning import build_clean_dataframe
from observability.quality import run_data_quality_checks

class TestPipeline(unittest.TestCase):
    def setUp(self):
        from ingestion.crossref import PaperRecord
        self.raw_records = [
            PaperRecord(
                paper_id="10.1234/test",
                title="Test Paper",
                summary="This is a test summary for the paper.",
                authors=["John Doe"],
                categories=["Computer Science"],
                primary_category="Computer Science",
                published="2023-05-12",
                updated="",
                abs_url="",
                pdf_url="",
                comment=""
            )
        ]
        self.run_date = datetime(2024, 1, 1, tzinfo=UTC)

    def test_build_clean_dataframe(self):
        df = build_clean_dataframe(self.raw_records, self.run_date)
        
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["paper_id"], "10.1234/test")
        self.assertEqual(df.iloc[0]["title"], "Test Paper")
        self.assertEqual(df.iloc[0]["authors_joined"], "John Doe")
        self.assertEqual(df.iloc[0]["summary"], "This is a test summary for the paper.")
        
    def test_run_data_quality_checks_mock(self):
        # We need a dummy settings object just to provide paths
        from core.config import load_settings
        settings = load_settings()
        
        df = build_clean_dataframe(self.raw_records, self.run_date)
        res = run_data_quality_checks(df, settings, "test_quality")
        self.assertTrue(res["passed"])
        self.assertEqual(res["total_rows"], 1)

if __name__ == '__main__':
    unittest.main()
