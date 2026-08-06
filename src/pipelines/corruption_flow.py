from __future__ import annotations

import json
from datetime import datetime, UTC

import pandas as pd

from core.config import load_settings
from ingestion.crossref import load_raw_records
from ingestion.cleaning import build_clean_dataframe, save_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from retrieval.index import LocalEmbeddingIndex
from evaluation.metrics import evaluate_pipeline
from observability.quality import run_data_quality_checks, build_freshness_report
from observability.reporting import generate_corruption_report


def main() -> None:
    settings = load_settings()
    run_date = datetime.now(UTC)

    print("1. Load baseline dataset & metrics")
    with open(settings.paths.baseline_metrics, "r", encoding="utf-8") as f:
        baseline_metrics = json.load(f)
        
    df_clean = pd.read_json(settings.paths.clean_json)
    df_clean['published_dt'] = pd.to_datetime(df_clean['published_dt'])

    print("2. Corrupt data")
    df_corrupted = corrupt_clean_dataframe(df_clean, settings.paths.corruption_log)

    print("3. Save corrupted data")
    save_clean_dataframe(df_corrupted, settings.paths.corrupted_clean_csv, settings.paths.corrupted_clean_json)

    print("4. Rebuild index & Evaluate (Corrupted)")
    corrupted_index = LocalEmbeddingIndex.build(
        df=df_corrupted,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json
    )
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers
    )

    print("5. Run quality checks & freshness (Corrupted)")
    def calc_age(d):
        if pd.isna(d):
            return -1
        return (run_date.date() - d.date()).days
    df_corrupted['age_days'] = df_corrupted['published_dt'].apply(calc_age)

    corrupted_quality = run_data_quality_checks(df_corrupted, settings, "corrupted")
    corrupted_freshness = build_freshness_report(df_corrupted, settings, settings.paths.quality_dir / "corrupted_freshness.json")

    print("6. Repair data from raw records")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    df_repaired = build_clean_dataframe(raw_records, run_date)
    save_clean_dataframe(df_repaired, settings.paths.repaired_clean_csv, settings.paths.repaired_clean_json)

    print("7. Rebuild index & Evaluate (Repaired)")
    repaired_index = LocalEmbeddingIndex.build(
        df=df_repaired,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json
    )
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers
    )
    repaired_quality = run_data_quality_checks(df_repaired, settings, "repaired")
    repaired_freshness = build_freshness_report(df_repaired, settings, settings.paths.quality_dir / "repaired_freshness.json")

    print("8. Generate comparison report")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness
    )
    print(f"Comparison report saved at: {settings.paths.comparison_report}")


if __name__ == "__main__":
    main()
