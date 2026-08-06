# Corruption & Repair Comparison Report

> Generated: 2026-08-06 12:29:00 UTC

---

## 1. Executive Summary

This report demonstrates the impact of data corruption on RAG agent quality
and validates that repair from raw source restores performance.

Three pipeline states are compared:

| State | Description |
|-------|-------------|
| **Baseline** | Original clean data — the reference standard |
| **Corrupted** | Data with 6 intentional quality issues injected |
| **Repaired** | Data restored by re-cleaning from raw source |

### Corruption Scenarios Applied

| # | Type | Description | Impact |
|---|------|-------------|--------|
| 1 | **Drop Latest** | Removed newest records | Missing recent papers |
| 2 | **Blank Summary** | Emptied summary on select rows | No content for embedding |
| 3 | **Noise Injection** | Added garbage text to summaries | Polluted semantic search |
| 4 | **Title Truncation** | Cut titles to 10 characters | Broken exact-match lookup |
| 5 | **Stale Dates** | Set dates to 2020-01-01 | Failed freshness checks |
| 6 | **Duplicates** | Added duplicate rows | Inflated corpus, skewed retrieval |

## 2. Metrics Comparison

| Metric | Baseline | Corrupted | Repaired | Δ Corruption | Δ Recovery |
|--------|----------|-----------|----------|:------------:|:----------:|
| retrieval_hit_rate | 1.0000 | 0.8333 | 1.0000 | 🔴 -0.1667 | 🟢 +0.1667 |
| mean_token_f1 | 1.0000 | 0.7719 | 1.0000 | 🔴 -0.2281 | 🟢 +0.2281 |
| judge_accuracy | 0.9722 | 0.7778 | 1.0000 | 🔴 -0.1944 | 🟢 +0.2222 |
| mean_judge_score | 5 | 4.138888888888889 | 5 | 🔴 -0.861111 | 🟢 +0.861111 |
| samples | 36 | 36 | 36 | 🟢 +0 | ⚪ +0 |

### Visual Comparison

```
  retrieval_hit_rate:
    Baseline  |█████████████████████████| 1.0000
    Corrupted |████████████████████     | 0.8333
    Repaired  |█████████████████████████| 1.0000

  mean_token_f1:
    Baseline  |█████████████████████████| 1.0000
    Corrupted |███████████████████      | 0.7719
    Repaired  |█████████████████████████| 1.0000

  judge_accuracy:
    Baseline  |████████████████████████ | 0.9722
    Corrupted |███████████████████      | 0.7778
    Repaired  |█████████████████████████| 1.0000

```

## 3. Data Quality Comparison

| Aspect | Corrupted | Repaired |
|--------|-----------|----------|
| Overall Status | ❌ FAIL | ✅ PASS |
| Checks Passed | 2/6 | 6/6 |

### Corrupted Data Quality Detail

**Overall Status**: FAIL
**Total Rows**: 24
**Passed/Total Checks**: 2/6

| Check | Status | Detail |
|-------|--------|--------|
| row_count | ✅ PASS | Total rows: 24 |
| paper_id_not_null_unique | ❌ FAIL | Null IDs: 0, Unique IDs: 22/24 |
| title_not_null | ✅ PASS | Null titles: 0, Empty titles: 0 |
| summary_length | ❌ FAIL | Short summaries (<20 chars): 2, Empty summaries: 2 |
| freshness | ❌ FAIL | Stale rows (>180 days): 3/24 |
| no_duplicates | ❌ FAIL | Duplicate rows: 2 |

### Repaired Data Quality Detail

**Overall Status**: PASS
**Total Rows**: 24
**Passed/Total Checks**: 6/6

| Check | Status | Detail |
|-------|--------|--------|
| row_count | ✅ PASS | Total rows: 24 |
| paper_id_not_null_unique | ✅ PASS | Null IDs: 0, Unique IDs: 24/24 |
| title_not_null | ✅ PASS | Null titles: 0, Empty titles: 0 |
| summary_length | ✅ PASS | Short summaries (<20 chars): 0, Empty summaries: 0 |
| freshness | ✅ PASS | Stale rows (>180 days): 0/24 |
| no_duplicates | ✅ PASS | Duplicate rows: 0 |

## 4. Freshness Comparison

| Aspect | Corrupted | Repaired |
|--------|-----------|----------|
| Status | ⚠️ STALE | ✅ FRESH |
| Latest Published | 2026-07-10 | 2026-08-01 |
| Oldest Published | 2020-01-01 | 2026-02-12 |
| Stale Rows | 3/24 | 0/24 |

## 5. Impact Analysis

### Degradation from Corruption

- **Retrieval hit rate** dropped by **16.7%** (from 1.0000 to 0.8333)
- **Token F1** dropped by **22.8%** (from 1.0000 to 0.7719)
- **Judge score** dropped from **5.0** to **4.1** (out of 5.0)

### Recovery from Repair

- **Retrieval hit rate**: 0.8333 → **1.0000** ✅ fully recovered
- **Token F1**: 0.7719 → **1.0000** ✅ fully recovered
- **Judge score**: 4.1 → **5.0** ✅ fully recovered

### Root Cause Analysis

| Corruption Type | Expected Impact | Observed |
|----------------|-----------------|----------|
| Drop Latest | Retrieval miss for recent papers | Confirmed ✅ |
| Blank Summary | Empty embeddings → poor retrieval | Confirmed ✅ |
| Noise Injection | Polluted semantic similarity | Confirmed ✅ |
| Title Truncation | Broken exact-match lookup | Confirmed ✅ |
| Stale Dates | Failed freshness checks | Confirmed ✅ |
| Duplicates | Duplicate paper_id check fails | Confirmed ✅ |

## 6. Conclusions

### Key Findings

1. **Data corruption directly impacts RAG agent quality.** Six distinct corruption types
   were applied to the clean dataset, causing measurable degradation across all evaluation
   metrics: retrieval hit rate dropped 16.7%, token F1 dropped 22.8%.

2. **Quality checks detect corruption.** The data quality framework correctly identified
   multiple issues in corrupted data (4 failed checks vs 0 in baseline),
   including duplicates, empty summaries, and stale records.

3. **Repair from raw source restores performance.** Re-cleaning from the original raw
   Crossref records fully recovered all metrics to baseline levels, proving the
   pipeline's resilience when raw data is preserved.

4. **Data observability is essential for production RAG systems.** Automated quality
   checks and freshness monitoring can detect data issues before they propagate to
   end users through degraded agent responses.

### Recommendations

- Run quality checks after every ETL refresh
- Monitor freshness to catch stale data early
- Always preserve raw data for repair/re-processing
- Set up alerts for quality check failures

---

*Report generated by Day 10 Data Observability Lab — 2026-08-06 12:29:00 UTC*
