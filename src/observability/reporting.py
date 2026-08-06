from __future__ import annotations

from typing import Any


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    content = f"""# Phase 1 Baseline Report

## Source Summary
- API: {source_summary.get('api')}
- Query: {source_summary.get('query')}
- Total Raw Records: {source_summary.get('total_raw')}
- Total Clean Records: {source_summary.get('total_clean')}

## Evaluation Metrics
- Samples: {metrics.get('samples')}
- Retrieval Hit Rate: {metrics.get('retrieval_hit_rate', 0):.2%}
- Mean Token F1: {metrics.get('mean_token_f1', 0):.4f}
- Judge Accuracy: {metrics.get('judge_accuracy', 0):.2%}
- Mean Judge Score: {metrics.get('mean_judge_score', 0):.2f}

## Data Quality
- Passed: {quality.get('passed')}
- Total Rows: {quality.get('total_rows')}
- Unique IDs: {quality.get('unique_id')}

## Freshness
- Is Fresh: {freshness.get('is_fresh')}
- Stale Rows: {freshness.get('stale_rows')} / {freshness.get('total_rows')}
- Latest Published: {freshness.get('latest_published')}
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    content = f"""# Corruption & Repair Report

## Metrics Comparison
| Metric | Baseline | Corrupted | Repaired |
|---|---|---|---|
| Retrieval Hit Rate | {baseline_metrics.get('retrieval_hit_rate', 0):.2%} | {corrupted_metrics.get('retrieval_hit_rate', 0):.2%} | {repaired_metrics.get('retrieval_hit_rate', 0):.2%} |
| Mean Judge Score | {baseline_metrics.get('mean_judge_score', 0):.2f} | {corrupted_metrics.get('mean_judge_score', 0):.2f} | {repaired_metrics.get('mean_judge_score', 0):.2f} |

## Quality Status
- Corrupted Data Passed Quality: {corrupted_quality.get('passed')}
- Repaired Data Passed Quality: {repaired_quality.get('passed')}

## Freshness Status
- Corrupted Data Is Fresh: {corrupted_freshness.get('is_fresh')}
- Repaired Data Is Fresh: {repaired_freshness.get('is_fresh')}
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)
