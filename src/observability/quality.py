from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json

logger = logging.getLogger(__name__)


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run a suite of data quality checks on the cleaned dataframe.

    Checks:
    1. Row count > 0
    2. paper_id not null and unique
    3. title not null
    4. summary length >= 20 chars
    5. Freshness: age_days <= threshold
    """
    checks: list[dict[str, Any]] = []
    total_rows = len(df)

    # Check 1: Row count
    row_count_pass = total_rows > 0
    checks.append({
        "check": "row_count",
        "description": "Dataset has at least 1 row",
        "passed": row_count_pass,
        "detail": f"Total rows: {total_rows}",
    })

    # Check 2: paper_id not null and unique
    if total_rows > 0:
        null_ids = int(df["paper_id"].isna().sum())
        unique_ids = int(df["paper_id"].nunique())
        id_pass = null_ids == 0 and unique_ids == total_rows
        checks.append({
            "check": "paper_id_not_null_unique",
            "description": "paper_id is not null and unique",
            "passed": id_pass,
            "detail": f"Null IDs: {null_ids}, Unique IDs: {unique_ids}/{total_rows}",
        })
    else:
        checks.append({
            "check": "paper_id_not_null_unique",
            "description": "paper_id is not null and unique",
            "passed": False,
            "detail": "No rows to check",
        })

    # Check 3: title not null
    if total_rows > 0:
        null_titles = int(df["title"].isna().sum())
        empty_titles = int((df["title"].str.strip() == "").sum())
        title_pass = null_titles == 0 and empty_titles == 0
        checks.append({
            "check": "title_not_null",
            "description": "All titles are non-empty",
            "passed": title_pass,
            "detail": f"Null titles: {null_titles}, Empty titles: {empty_titles}",
        })
    else:
        checks.append({
            "check": "title_not_null",
            "description": "All titles are non-empty",
            "passed": False,
            "detail": "No rows to check",
        })

    # Check 4: summary length >= 20 chars
    if total_rows > 0:
        short_summaries = int((df["summary"].str.len() < 20).sum())
        empty_summaries = int((df["summary"].isna() | (df["summary"].str.strip() == "")).sum())
        summary_pass = short_summaries == 0 and empty_summaries == 0
        checks.append({
            "check": "summary_length",
            "description": "All summaries have at least 20 characters",
            "passed": summary_pass,
            "detail": f"Short summaries (<20 chars): {short_summaries}, Empty summaries: {empty_summaries}",
        })
    else:
        checks.append({
            "check": "summary_length",
            "description": "All summaries have at least 20 characters",
            "passed": False,
            "detail": "No rows to check",
        })

    # Check 5: Freshness
    if total_rows > 0 and "age_days" in df.columns:
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
        freshness_pass = stale_rows == 0
        checks.append({
            "check": "freshness",
            "description": f"All records within {settings.freshness_threshold_days} days freshness threshold",
            "passed": freshness_pass,
            "detail": f"Stale rows (>{settings.freshness_threshold_days} days): {stale_rows}/{total_rows}",
        })
    else:
        checks.append({
            "check": "freshness",
            "description": f"All records within {settings.freshness_threshold_days} days freshness threshold",
            "passed": False,
            "detail": "No age_days column or no rows",
        })

    # Check 6: No duplicate paper_ids
    if total_rows > 0:
        dup_count = int(df["paper_id"].duplicated().sum())
        dup_pass = dup_count == 0
        checks.append({
            "check": "no_duplicates",
            "description": "No duplicate paper_ids",
            "passed": dup_pass,
            "detail": f"Duplicate rows: {dup_count}",
        })
    else:
        checks.append({
            "check": "no_duplicates",
            "description": "No duplicate paper_ids",
            "passed": False,
            "detail": "No rows to check",
        })

    # Overall result
    all_passed = all(c["passed"] for c in checks)
    result = {
        "report_name": report_name,
        "total_rows": total_rows,
        "checks": checks,
        "overall_status": "PASS" if all_passed else "FAIL",
        "passed_count": sum(1 for c in checks if c["passed"]),
        "failed_count": sum(1 for c in checks if not c["passed"]),
    }

    # Save report
    report_path = settings.paths.quality_dir / f"{report_name}_quality.json"
    write_json(report_path, result)
    logger.info("Data quality report '%s': %s (%d/%d checks passed)", report_name, result["overall_status"], result["passed_count"], len(checks))

    return result


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Build freshness report from cleaned dataframe.

    Steps:
    1. Find latest and oldest published dates.
    2. Count stale rows (age_days > threshold).
    3. Build payload with latest_published, oldest_published, stale_rows, total_rows, is_fresh.
    4. Write JSON report.
    """
    total_rows = len(df)

    if total_rows == 0 or "published" not in df.columns:
        payload: dict[str, Any] = {
            "latest_published": "",
            "oldest_published": "",
            "stale_rows": 0,
            "total_rows": 0,
            "is_fresh": False,
            "freshness_threshold_days": settings.freshness_threshold_days,
        }
        write_json(report_path, payload)
        return payload

    # Find latest and oldest published dates
    published_dates = df["published"].dropna()
    published_dates = published_dates[published_dates.str.len() > 0]

    if len(published_dates) > 0:
        latest_published = str(published_dates.max())
        oldest_published = str(published_dates.min())
    else:
        latest_published = ""
        oldest_published = ""

    # Count stale rows
    stale_rows = 0
    if "age_days" in df.columns:
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())

    is_fresh = stale_rows == 0 and total_rows > 0

    payload = {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "is_fresh": is_fresh,
        "freshness_threshold_days": settings.freshness_threshold_days,
    }

    write_json(report_path, payload)
    logger.info(
        "Freshness report: latest=%s, oldest=%s, stale=%d/%d, is_fresh=%s",
        latest_published, oldest_published, stale_rows, total_rows, is_fresh,
    )

    return payload
