from __future__ import annotations

import logging

from core.config import load_settings, require_llm_credentials
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex

logger = logging.getLogger(__name__)


def main() -> None:
    """Build and run the baseline pipeline end-to-end.

    Steps:
    1. Load settings.
    2. Load or fetch raw records from Crossref.
    3. Clean data.
    4. Save clean CSV/JSON.
    5. Build ChromaDB index with embeddings.
    6. Create or load evaluation test set.
    7. Evaluate pipeline on test set.
    8. Run data quality checks and freshness report.
    9. Generate markdown report.
    10. Demo agent on sample questions.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # 1. Load settings
    settings = load_settings()
    require_llm_credentials(settings)
    paths = settings.paths
    run_date = now_utc()

    logger.info("=== Phase 1: Baseline Pipeline ===")
    logger.info("Provider: %s, Model: %s", settings.llm_provider, settings.model_name)

    # 2. Load or fetch raw records
    if paths.raw_records_json.exists() and not settings.refresh_source:
        logger.info("Loading cached raw records from %s", paths.raw_records_json)
        records = load_raw_records(paths.raw_records_json)
    else:
        logger.info("Fetching fresh records from Crossref API...")
        records = fetch_source_records(settings)

    logger.info("Raw records: %d", len(records))

    # 3. Clean data
    logger.info("Cleaning data...")
    df = build_clean_dataframe(records, run_date)
    logger.info("Cleaned dataset: %d rows", len(df))

    # 4. Save clean CSV/JSON
    write_csv(df, paths.clean_csv)
    # Convert list columns to strings for JSON serialization
    df_json = df.copy()
    for col in ["authors", "categories"]:
        if col in df_json.columns:
            df_json[col] = df_json[col].apply(lambda x: x if isinstance(x, str) else str(x))
    write_json(paths.clean_json, df_json.to_dict(orient="records"))
    logger.info("Saved clean data to %s and %s", paths.clean_csv, paths.clean_json)

    # 5. Build ChromaDB index
    logger.info("Building embedding index...")
    index = LocalEmbeddingIndex.build(df, settings, embeddings_output_path=paths.embeddings_json)
    logger.info("Index built with %d documents", len(index.documents))

    # 6. Create or load test set
    if paths.eval_testset.exists() and not settings.refresh_test_set:
        logger.info("Loading existing test set from %s", paths.eval_testset)
        test_set = read_json(paths.eval_testset)
    else:
        logger.info("Building evaluation test set...")
        test_set = build_test_set(df, paths.eval_testset)
    logger.info("Test set: %d questions", len(test_set))

    # 7. Evaluate
    logger.info("Evaluating baseline pipeline...")
    eval_bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=paths.eval_testset,
        metrics_output_path=paths.baseline_metrics,
        answers_output_path=paths.baseline_answers,
    )
    logger.info("Baseline metrics: %s", eval_bundle.summary)

    # 8. Quality checks and freshness report
    logger.info("Running data quality checks...")
    quality_result = run_data_quality_checks(df, settings, "baseline")

    logger.info("Building freshness report...")
    freshness_result = build_freshness_report(df, settings, paths.freshness_report)

    # 9. Generate markdown report
    source_summary = {
        "source": settings.source_api,
        "query": settings.source_query,
        "filter": settings.source_filter,
        "max_results": settings.max_results,
        "records_fetched": len(records),
        "records_after_cleaning": len(df),
        "embedding_model": settings.embedding_model,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.model_name,
    }

    logger.info("Generating phase 1 report...")
    generate_phase1_report(
        report_path=paths.baseline_report,
        source_summary=source_summary,
        metrics=eval_bundle.summary,
        quality=quality_result,
        freshness=freshness_result,
    )

    # 10. Demo agent on sample questions (optional, log-only)
    logger.info("--- Demo: answering sample questions ---")
    from retrieval.qa import answer_question

    demo_questions = [
        "What papers discuss retrieval augmented generation?",
        "What papers are about large language models?",
    ]
    demo_answers = []
    for q in demo_questions:
        result = answer_question(q, settings=settings, index=index)
        logger.info("Q: %s\nA: %s\n", q, result.answer)
        demo_answers.append({
            "question": result.question,
            "answer": result.answer,
            "retrieved_doc_ids": result.retrieved_doc_ids,
            "retrieved_titles": result.retrieved_titles,
        })
    write_json(paths.demo_answers, demo_answers)

    logger.info("=== Phase 1 Complete ===")
    logger.info("Reports: %s", paths.baseline_report)
    logger.info("Metrics: %s", paths.baseline_metrics)
