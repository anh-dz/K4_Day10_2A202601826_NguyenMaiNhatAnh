from __future__ import annotations

import json
from typing import Any

import pandas as pd

from core.config import Settings


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    total_rows = len(df)
    not_null_id = int(df["paper_id"].notna().sum()) if total_rows > 0 else 0
    unique_id = int(df["paper_id"].nunique()) if total_rows > 0 else 0
    not_null_title = int(df["title"].notna().sum()) if total_rows > 0 else 0
    valid_summary_len = int((df["summary_chars"] > 10).sum()) if total_rows > 0 and "summary_chars" in df else 0
    
    results = {
        "report_name": report_name,
        "total_rows": total_rows,
        "not_null_id": not_null_id,
        "unique_id": unique_id,
        "not_null_title": not_null_title,
        "valid_summary_len": valid_summary_len,
        "passed": total_rows > 0 and (not_null_id == unique_id == total_rows) and (not_null_title == total_rows)
    }
    
    out_path = settings.paths.quality_dir / f"{report_name}_quality.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    return results


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    if df.empty or "published_dt" not in df.columns:
        res = {"error": "empty dataframe or missing published_dt", "is_fresh": False, "stale_rows": 0, "total_rows": 0}
        return res
        
    latest_published = df["published_dt"].max()
    oldest_published = df["published_dt"].min()
    stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
    total_rows = len(df)
    is_fresh = stale_rows == 0
    
    payload = {
        "latest_published": latest_published.isoformat() if pd.notna(latest_published) else None,
        "oldest_published": oldest_published.isoformat() if pd.notna(oldest_published) else None,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "is_fresh": is_fresh
    }
    
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        
    return payload
