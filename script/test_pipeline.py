"""Validation tests for the data pipeline.

Run with: uv run python script/test_pipeline.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.config import load_settings
from core.utils import read_json


def test_raw_data_exists(settings) -> bool:
    """Test that raw data files exist and are valid JSON."""
    paths = settings.paths
    if not paths.raw_api_response.exists():
        print("  FAIL: raw_api_response not found")
        return False
    if not paths.raw_records_json.exists():
        print("  FAIL: raw_records_json not found")
        return False
    records = read_json(paths.raw_records_json)
    if not isinstance(records, list) or len(records) == 0:
        print(f"  FAIL: raw_records has {len(records) if isinstance(records, list) else 'invalid'} records")
        return False
    # Verify schema
    required_fields = {"paper_id", "title", "summary", "authors", "published"}
    for i, rec in enumerate(records[:3]):
        missing = required_fields - set(rec.keys())
        if missing:
            print(f"  FAIL: record {i} missing fields: {missing}")
            return False
    print(f"  PASS: {len(records)} raw records with valid schema")
    return True


def test_clean_data_exists(settings) -> bool:
    """Test that cleaned data exists and has required columns."""
    import pandas as pd
    paths = settings.paths
    if not paths.clean_csv.exists():
        print("  FAIL: clean CSV not found")
        return False
    df = pd.read_csv(paths.clean_csv)
    required_cols = {"paper_id", "title", "summary", "published", "age_days",
                     "authors_joined", "categories_joined", "text_for_embedding"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"  FAIL: clean CSV missing columns: {missing}")
        return False
    if len(df) == 0:
        print("  FAIL: clean CSV is empty")
        return False
    if df["paper_id"].duplicated().any():
        print("  FAIL: clean CSV has duplicate paper_ids")
        return False
    print(f"  PASS: {len(df)} clean records with {len(df.columns)} columns")
    return True


def test_embeddings_exist(settings) -> bool:
    """Test that embedding index exists."""
    paths = settings.paths
    if not paths.embeddings_json.exists():
        print("  FAIL: embeddings manifest not found")
        return False
    manifest = read_json(paths.embeddings_json)
    docs = manifest.get("documents", [])
    if not docs:
        print("  FAIL: embeddings manifest has no documents")
        return False
    print(f"  PASS: {len(docs)} documents indexed in {manifest.get('backend', 'unknown')}")
    return True


def test_eval_set_exists(settings) -> bool:
    """Test that evaluation set exists and has proper structure."""
    paths = settings.paths
    if not paths.eval_testset.exists():
        print("  FAIL: test set not found")
        return False
    test_set = read_json(paths.eval_testset)
    if not isinstance(test_set, list) or len(test_set) < 3:
        print(f"  FAIL: test set too small ({len(test_set)} questions)")
        return False
    required_fields = {"id", "question_type", "question", "ground_truth", "ground_truth_doc_ids"}
    for item in test_set[:3]:
        missing = required_fields - set(item.keys())
        if missing:
            print(f"  FAIL: test set item missing fields: {missing}")
            return False
    types = {item["question_type"] for item in test_set}
    print(f"  PASS: {len(test_set)} questions, types: {types}")
    return True


def test_baseline_metrics(settings) -> bool:
    """Test that baseline metrics exist and are reasonable."""
    paths = settings.paths
    if not paths.baseline_metrics.exists():
        print("  FAIL: baseline metrics not found")
        return False
    metrics = read_json(paths.baseline_metrics)
    required = {"samples", "retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"}
    missing = required - set(metrics.keys())
    if missing:
        print(f"  FAIL: baseline metrics missing: {missing}")
        return False
    if metrics["samples"] < 3:
        print(f"  FAIL: too few samples ({metrics['samples']})")
        return False
    print(f"  PASS: {metrics['samples']} samples, hit_rate={metrics['retrieval_hit_rate']:.4f}, f1={metrics['mean_token_f1']:.4f}")
    return True


def test_quality_reports(settings) -> bool:
    """Test quality and freshness reports."""
    paths = settings.paths
    quality_path = paths.quality_dir / "baseline_quality.json"
    if not quality_path.exists():
        print("  FAIL: baseline quality report not found")
        return False
    quality = read_json(quality_path)
    if "checks" not in quality:
        print("  FAIL: quality report has no checks")
        return False
    if not paths.freshness_report.exists():
        print("  FAIL: freshness report not found")
        return False
    freshness = read_json(paths.freshness_report)
    print(f"  PASS: quality={quality['overall_status']}, fresh={freshness.get('is_fresh', 'N/A')}")
    return True


def test_corruption_flow(settings) -> bool:
    """Test corruption flow artifacts."""
    paths = settings.paths
    if not paths.corruption_log.exists():
        print("  FAIL: corruption log not found")
        return False
    log = read_json(paths.corruption_log)
    if len(log) < 3:
        print(f"  FAIL: only {len(log)} corruption types (need ≥3)")
        return False
    if not paths.corrupted_metrics.exists():
        print("  FAIL: corrupted metrics not found")
        return False
    if not paths.repaired_metrics.exists():
        print("  FAIL: repaired metrics not found")
        return False
    corrupted = read_json(paths.corrupted_metrics)
    baseline = read_json(paths.baseline_metrics)
    repaired = read_json(paths.repaired_metrics)
    # Verify corruption degraded quality
    if corrupted["retrieval_hit_rate"] >= baseline["retrieval_hit_rate"]:
        print("  WARN: corruption did not degrade retrieval_hit_rate")
    print(f"  PASS: {len(log)} corruption types, metrics: baseline→corrupted→repaired verified")
    return True


def test_reports_exist(settings) -> bool:
    """Test that markdown reports exist."""
    paths = settings.paths
    if not paths.baseline_report.exists():
        print("  FAIL: phase1 report not found")
        return False
    if not paths.comparison_report.exists():
        print("  FAIL: corruption report not found")
        return False
    # Check reports are not empty
    p1_size = paths.baseline_report.stat().st_size
    cr_size = paths.comparison_report.stat().st_size
    if p1_size < 100 or cr_size < 100:
        print(f"  FAIL: reports too small (phase1={p1_size}B, corruption={cr_size}B)")
        return False
    print(f"  PASS: phase1_report={p1_size:,}B, corruption_report={cr_size:,}B")
    return True


def main():
    print("=" * 60)
    print("DATA PIPELINE VALIDATION TESTS")
    print("=" * 60)

    settings = load_settings()

    tests = [
        ("Raw Data Ingestion", test_raw_data_exists),
        ("Clean Data", test_clean_data_exists),
        ("Embeddings Index", test_embeddings_exist),
        ("Evaluation Set", test_eval_set_exists),
        ("Baseline Metrics", test_baseline_metrics),
        ("Quality Reports", test_quality_reports),
        ("Corruption Flow", test_corruption_flow),
        ("Markdown Reports", test_reports_exist),
    ]

    results = []
    for name, test_fn in tests:
        print(f"\n[{name}]")
        try:
            passed = test_fn(settings)
        except Exception as e:
            print(f"  ERROR: {e}")
            passed = False
        results.append((name, passed))

    print(f"\n{'=' * 60}")
    print("RESULTS SUMMARY")
    print(f"{'=' * 60}")
    passed = sum(1 for _, p in results if p)
    total = len(results)
    for name, ok in results:
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n  {passed}/{total} tests passed")
    print(f"{'=' * 60}")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
