from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
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
    # --- Generate Visualization ---
    chart_path = report_path.parent / "comparison_chart.png"
    labels = ['Baseline', 'Corrupted', 'Repaired']
    
    hr_b = baseline_metrics.get('retrieval_hit_rate', 0)
    hr_c = corrupted_metrics.get('retrieval_hit_rate', 0)
    hr_r = repaired_metrics.get('retrieval_hit_rate', 0)
    
    js_b = baseline_metrics.get('mean_judge_score', 0)
    js_c = corrupted_metrics.get('mean_judge_score', 0)
    js_r = repaired_metrics.get('mean_judge_score', 0)
    
    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    rects1 = ax.bar(x - width/2, [hr_b, hr_c, hr_r], width, label='Hit Rate', color='#3b82f6')
    rects2 = ax.bar(x + width/2, [js_b/5.0, js_c/5.0, js_r/5.0], width, label='Judge Score (Normalized)', color='#ef4444')

    ax.set_ylabel('Scores (0-1)')
    ax.set_title('Pipeline Performance Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    fig.tight_layout()
    plt.savefig(chart_path)
    plt.close()

    # --- Dynamic Analysis ---
    drop_pct = (js_b - js_c) / js_b * 100 if js_b > 0 else 0
    analysis = f"Khi dữ liệu bị hỏng, chất lượng hệ thống giảm sút rõ rệt (điểm Judge Score giảm {drop_pct:.1f}%). "
    if js_r >= js_b * 0.95:
        analysis += "Tuy nhiên, sau khi thực hiện Data Repair, hệ thống đã khôi phục lại hiệu năng tương đương Baseline. Điều này cho thấy tầm quan trọng tối thượng của việc bảo vệ Data Quality trong quá trình xây dựng RAG."
    else:
        analysis += "Hệ thống đã phục hồi một phần sau khi Repair."

    content = f"""# Corruption & Repair Report

## 1. Phân Tích Chuyên Sâu (Dynamic Analysis)
{analysis}

![Comparison Chart](./comparison_chart.png)

## 2. Metrics Comparison
| Metric | Baseline | Corrupted | Repaired |
|---|---|---|---|
| Retrieval Hit Rate | {hr_b:.2%} | {hr_c:.2%} | {hr_r:.2%} |
| Mean Judge Score | {js_b:.2f} | {js_c:.2f} | {js_r:.2f} |
| Token F1 | {baseline_metrics.get('mean_token_f1', 0):.4f} | {corrupted_metrics.get('mean_token_f1', 0):.4f} | {repaired_metrics.get('mean_token_f1', 0):.4f} |

## 3. Quality Status
- Corrupted Data Passed Quality: **{corrupted_quality.get('passed')}** (Errors simulated)
- Repaired Data Passed Quality: **{repaired_quality.get('passed')}** (Data restored)

## 4. Freshness Status
- Corrupted Data Is Fresh: **{corrupted_freshness.get('is_fresh')}**
- Repaired Data Is Fresh: **{repaired_freshness.get('is_fresh')}**
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)
