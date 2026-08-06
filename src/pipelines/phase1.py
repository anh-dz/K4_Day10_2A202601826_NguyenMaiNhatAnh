from __future__ import annotations

import json
from datetime import datetime, UTC

from core.config import load_settings
from ingestion.crossref import fetch_source_records, load_raw_records
from ingestion.cleaning import build_clean_dataframe, save_clean_dataframe
from retrieval.index import LocalEmbeddingIndex
from evaluation.testset import build_test_set
from evaluation.metrics import evaluate_pipeline
from observability.quality import run_data_quality_checks, build_freshness_report
from observability.reporting import generate_phase1_report


def main() -> None:
    settings = load_settings()
    run_date = datetime.now(UTC)

    print("1. Load/fetch raw records")
    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        records = fetch_source_records(settings)
    else:
        records = load_raw_records(settings.paths.raw_records_json)

    print("2. Clean data & Save")
    df = build_clean_dataframe(records, run_date)
    save_clean_dataframe(df, settings.paths.clean_csv, settings.paths.clean_json)

    print("3. Build Chroma index")
    index = LocalEmbeddingIndex.build(
        df=df,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json
    )

    print("4. Create/load evaluation set")
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        build_test_set(df, settings.paths.eval_testset)
        
    print("5. Evaluate")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers
    )

    print("6. Run quality checks & freshness report")
    quality_res = run_data_quality_checks(df, settings, "baseline")
    freshness_res = build_freshness_report(df, settings, settings.paths.freshness_report)

    print("7. Create markdown report")
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary={
            "api": settings.source_api,
            "query": settings.source_query,
            "total_raw": len(records),
            "total_clean": len(df),
        },
        metrics=bundle.summary,
        quality=quality_res,
        freshness=freshness_res,
    )
    print(f"Phase 1 report saved at: {settings.paths.baseline_report}")


if __name__ == "__main__":
    main()
