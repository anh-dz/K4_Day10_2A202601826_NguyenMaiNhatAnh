from __future__ import annotations

import logging
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json

logger = logging.getLogger(__name__)

CROSSREF_API_URL = "https://api.crossref.org/works"


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _strip_jats(text: str) -> str:
    """Remove JATS/HTML tags from abstract text."""
    return re.sub(r"<[^>]+>", "", text)


def _extract_date(item: dict, key: str) -> str:
    """Extract a date string from Crossref date-parts format."""
    date_obj = item.get(key)
    if not date_obj:
        return ""
    parts = date_obj.get("date-parts", [[]])
    if not parts or not parts[0]:
        return ""
    date_parts = parts[0]
    year = str(date_parts[0]) if len(date_parts) > 0 else "0000"
    month = str(date_parts[1]).zfill(2) if len(date_parts) > 1 else "01"
    day = str(date_parts[2]).zfill(2) if len(date_parts) > 2 else "01"
    return f"{year}-{month}-{day}"


def _extract_authors(item: dict) -> list[str]:
    """Extract author names from Crossref author field."""
    authors_raw = item.get("author", [])
    authors = []
    for author in authors_raw:
        given = author.get("given", "")
        family = author.get("family", "")
        name = f"{given} {family}".strip()
        if name:
            authors.append(name)
    return authors


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref API response payload into list of PaperRecord.

    Steps:
    1. Iterate payload["message"]["items"].
    2. Extract DOI, title, abstract, authors, subject, dates, URLs.
    3. Normalize text and skip records missing title or abstract.
    4. Return list of PaperRecord.
    """
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        # Extract DOI as paper_id
        doi = item.get("DOI", "").strip()
        if not doi:
            continue

        # Extract title
        title_list = item.get("title", [])
        title = normalize_whitespace(title_list[0]) if title_list else ""
        if not title:
            continue

        # Extract abstract (remove JATS tags)
        abstract_raw = item.get("abstract", "")
        summary = normalize_whitespace(_strip_jats(abstract_raw))
        if not summary:
            continue

        # Extract authors
        authors = _extract_authors(item)

        # Extract categories/subjects
        categories = item.get("subject", [])
        primary_category = categories[0] if categories else ""

        # Extract dates
        published = _extract_date(item, "published")
        updated = _extract_date(item, "deposited")

        # Extract URLs
        abs_url = item.get("URL", "")
        pdf_url = ""
        for link in item.get("link", []):
            if link.get("content-type", "") == "application/pdf":
                pdf_url = link.get("URL", "")
                break
            if link.get("URL", "").endswith(".pdf"):
                pdf_url = link.get("URL", "")
                break
        if not pdf_url:
            pdf_url = f"https://doi.org/{doi}"

        # Extract comment (container-title or publisher)
        container = item.get("container-title", [])
        comment = container[0] if container else item.get("publisher", "")

        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch records from Crossref API with retry/backoff, save raw data, parse into records.

    Steps:
    1. Build params from settings (query, filter, rows).
    2. Call API with retry for 429/503 status codes.
    3. Save raw response to settings.paths.raw_api_response.
    4. Parse payload with parse_crossref_payload.
    5. Save records to settings.paths.raw_records_json.
    """
    params: dict[str, Any] = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
        "sort": "relevance",
        "order": "desc",
    }

    headers = {
        "User-Agent": "Day10DataObservabilityLab/1.0 (mailto:student@example.com)",
    }

    logger.info("Fetching records from Crossref API: query=%s, rows=%d", settings.source_query, settings.max_results)

    # Retry with exponential backoff
    max_retries = 5
    response = None
    for attempt in range(max_retries):
        try:
            response = requests.get(CROSSREF_API_URL, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                break
            if response.status_code in (429, 503):
                wait_time = 2 ** attempt
                logger.warning(
                    "Crossref returned %d, retrying in %ds (attempt %d/%d)",
                    response.status_code, wait_time, attempt + 1, max_retries,
                )
                time.sleep(wait_time)
                continue
            response.raise_for_status()
        except requests.exceptions.Timeout:
            wait_time = 2 ** attempt
            logger.warning("Request timed out, retrying in %ds (attempt %d/%d)", wait_time, attempt + 1, max_retries)
            time.sleep(wait_time)
    else:
        if response is not None:
            response.raise_for_status()
        raise RuntimeError("Failed to fetch data from Crossref API after retries.")

    payload = response.json()

    # Save raw API response
    write_json(settings.paths.raw_api_response, payload)
    logger.info("Saved raw API response to %s", settings.paths.raw_api_response)

    # Parse records
    records = parse_crossref_payload(payload)
    logger.info("Parsed %d records from Crossref response", len(records))

    # Save parsed records
    records_data = [asdict(record) for record in records]
    write_json(settings.paths.raw_records_json, records_data)
    logger.info("Saved %d raw records to %s", len(records), settings.paths.raw_records_json)

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load JSON snapshot and map back to PaperRecord objects."""
    data = read_json(path)
    records = []
    for item in data:
        records.append(
            PaperRecord(
                paper_id=item["paper_id"],
                title=item["title"],
                summary=item["summary"],
                authors=item.get("authors", []),
                categories=item.get("categories", []),
                primary_category=item.get("primary_category", ""),
                published=item.get("published", ""),
                updated=item.get("updated", ""),
                abs_url=item.get("abs_url", ""),
                pdf_url=item.get("pdf_url", ""),
                comment=item.get("comment", ""),
            )
        )
    return records
