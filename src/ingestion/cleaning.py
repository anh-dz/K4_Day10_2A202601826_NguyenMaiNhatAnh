from __future__ import annotations

import logging
import re
from datetime import datetime

import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord

logger = logging.getLogger(__name__)


def _strip_html(text: str) -> str:
    """Remove any residual HTML/JATS tags."""
    return re.sub(r"<[^>]+>", "", text)


def _safe_parse_date(date_str: str) -> str:
    """Parse a date string and return ISO format, or empty string if invalid."""
    if not date_str:
        return ""
    try:
        # Try standard ISO format
        dt = datetime.strptime(date_str.strip()[:10], "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except (ValueError, IndexError):
        return ""


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records into a DataFrame ready for embedding.

    Steps:
    1. Normalize title, summary, authors, categories.
    2. Parse published/updated dates.
    3. Compute age_days from run_date.
    4. Create helper columns: authors_joined, categories_joined, summary_chars, text_for_embedding.
    5. Drop duplicates and filter bad rows.
    6. Sort by published date descending and return.
    """
    if not records:
        logger.warning("No records to clean.")
        return pd.DataFrame()

    rows = []
    for record in records:
        # Normalize text fields
        title = normalize_whitespace(_strip_html(record.title))
        summary = normalize_whitespace(_strip_html(record.summary))
        authors = [normalize_whitespace(a) for a in record.authors if a.strip()]
        categories = [normalize_whitespace(c) for c in record.categories if c.strip()]
        primary_category = normalize_whitespace(record.primary_category)

        # Parse dates
        published = _safe_parse_date(record.published)
        updated = _safe_parse_date(record.updated)

        # Calculate age_days
        age_days = 0
        if published:
            try:
                pub_dt = datetime.strptime(published, "%Y-%m-%d")
                age_days = (run_date.replace(tzinfo=None) - pub_dt).days
            except ValueError:
                age_days = 0

        # Create joined fields
        authors_joined = ", ".join(authors) if authors else ""
        categories_joined = ", ".join(categories) if categories else ""
        summary_chars = len(summary)

        # Create text_for_embedding
        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Published: {published}\n"
            f"Categories: {categories_joined}\n"
            f"Summary: {summary}"
        )

        rows.append(
            {
                "paper_id": record.paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": primary_category,
                "published": published,
                "updated": updated,
                "abs_url": record.abs_url,
                "pdf_url": record.pdf_url,
                "comment": record.comment,
                "age_days": age_days,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": summary_chars,
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(rows)

    if df.empty:
        logger.warning("Dataframe is empty after building rows.")
        return df

    # Filter rows: must have title and summary
    initial_count = len(df)
    df = df[df["title"].str.len() > 0]
    df = df[df["summary"].str.len() > 10]
    logger.info("Filtered %d rows with missing title/summary (kept %d/%d)", initial_count - len(df), len(df), initial_count)

    # Drop duplicates by paper_id
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    logger.info("Dropped %d duplicate rows by paper_id", before_dedup - len(df))

    # Sort by published date descending
    df = df.sort_values("published", ascending=False).reset_index(drop=True)

    logger.info("Cleaned dataframe: %d rows, %d columns", len(df), len(df.columns))
    return df
