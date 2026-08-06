from __future__ import annotations

import logging

import pandas as pd

from core.config import load_settings, require_llm_credentials
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex

logger = logging.getLogger(__name__)


def main() -> None:
    """Run corruption -> evaluate -> repair -> compare flow.

    Steps:
    1. Load baseline metrics and clean dataset.
    2. Create corrupted dataframe.
    3. Save corrupted artifacts.
    4. Rebuild index and evaluate on corrupted data.
    5. Run quality checks/freshness on corrupted data.
    6. Repair from raw records.
    7. Evaluate repaired dataset.
    8. Generate comparison report.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # 1. Load settings and baseline data
    settings = load_settings()
    require_llm_credentials(settings)
    paths = settings.paths
    run_date = now_utc()

    logger.info("=== Phase 2: Corruption, Repair & Comparison ===")

    # Verify baseline exists
    if not paths.baseline_metrics.exists():
        raise RuntimeError(
            "Baseline metrics not found. Run Phase 1 first: uv run python script/run_phase1.py"
        )

    baseline_metrics = read_json(paths.baseline_metrics)
    logger.info("Loaded baseline metrics: %s", baseline_metrics)

    # Load baseline clean data
    if not paths.clean_csv.exists():
        raise RuntimeError("Baseline clean CSV not found. Run Phase 1 first.")

    baseline_df = pd.read_csv(paths.clean_csv)
    # Restore list columns from string representation
    for col in ["authors", "categories"]:
        if col in baseline_df.columns:
            baseline_df[col] = baseline_df[col].apply(
                lambda x: eval(x) if isinstance(x, str) and x.startswith("[") else x  # noqa: S307
            )
    logger.info("Loaded baseline clean data: %d rows", len(baseline_df))

    # =========================================================================
    # 2. Create corrupted dataframe
    # =========================================================================
    logger.info("Corrupting data...")
    corrupted_df = corrupt_clean_dataframe(baseline_df, paths.corruption_log)
    logger.info("Corrupted dataset: %d rows (from %d baseline)", len(corrupted_df), len(baseline_df))

    # 3. Save corrupted artifacts
    write_csv(corrupted_df, paths.corrupted_clean_csv)
    corrupted_json = corrupted_df.copy()
    for col in ["authors", "categories"]:
        if col in corrupted_json.columns:
            corrupted_json[col] = corrupted_json[col].apply(lambda x: x if isinstance(x, str) else str(x))
    write_json(paths.corrupted_clean_json, corrupted_json.to_dict(orient="records"))
    logger.info("Saved corrupted data")

    # 4. Rebuild index for corrupted data and evaluate
    logger.info("Building corrupted index...")
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df, settings, embeddings_output_path=paths.corrupted_embeddings_json
    )

    logger.info("Evaluating corrupted pipeline...")
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=paths.eval_testset,
        metrics_output_path=paths.corrupted_metrics,
        answers_output_path=paths.corrupted_answers,
    )
    logger.info("Corrupted metrics: %s", corrupted_bundle.summary)

    # 5. Quality checks/freshness on corrupted data
    logger.info("Running quality checks on corrupted data...")
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")

    corrupted_freshness_path = paths.quality_dir / "corrupted_freshness_report.json"
    corrupted_freshness = build_freshness_report(corrupted_df, settings, corrupted_freshness_path)

    # =========================================================================
    # 6. Repair from raw records
    # =========================================================================
    logger.info("Repairing data from raw source...")
    if not paths.raw_records_json.exists():
        raise RuntimeError("Raw records not found. Run Phase 1 first.")

    raw_records = load_raw_records(paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, run_date)
    logger.info("Repaired dataset: %d rows", len(repaired_df))

    # Save repaired artifacts
    write_csv(repaired_df, paths.repaired_clean_csv)
    repaired_json = repaired_df.copy()
    for col in ["authors", "categories"]:
        if col in repaired_json.columns:
            repaired_json[col] = repaired_json[col].apply(lambda x: x if isinstance(x, str) else str(x))
    write_json(paths.repaired_clean_json, repaired_json.to_dict(orient="records"))

    # 7. Rebuild index for repaired data and evaluate
    logger.info("Building repaired index...")
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df, settings, embeddings_output_path=paths.repaired_embeddings_json
    )

    logger.info("Evaluating repaired pipeline...")
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=paths.eval_testset,
        metrics_output_path=paths.repaired_metrics,
        answers_output_path=paths.repaired_answers,
    )
    logger.info("Repaired metrics: %s", repaired_bundle.summary)

    # Quality checks/freshness on repaired data
    logger.info("Running quality checks on repaired data...")
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")

    repaired_freshness_path = paths.quality_dir / "repaired_freshness_report.json"
    repaired_freshness = build_freshness_report(repaired_df, settings, repaired_freshness_path)

    # =========================================================================
    # 8. Generate comparison report
    # =========================================================================
    logger.info("Generating comparison report...")
    generate_corruption_report(
        report_path=paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )

    logger.info("=== Phase 2 Complete ===")
    logger.info("Comparison report: %s", paths.comparison_report)

    # Print summary comparison
    logger.info("\n--- Quick Summary ---")
    for metric in ["retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"]:
        b = baseline_metrics.get(metric, "N/A")
        c = corrupted_bundle.summary.get(metric, "N/A")
        r = repaired_bundle.summary.get(metric, "N/A")
        logger.info("%s: baseline=%.4f → corrupted=%.4f → repaired=%.4f", metric, b, c, r)
