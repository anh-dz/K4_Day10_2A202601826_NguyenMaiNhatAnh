from __future__ import annotations

import json
import time
import requests
from dataclasses import dataclass, asdict
from pathlib import Path

from core.config import Settings


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


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    records = []
    items = payload.get("message", {}).get("items", [])
    
    for item in items:
        # DOI
        paper_id = item.get("DOI", "")
        if not paper_id:
            continue
            
        # title
        title_list = item.get("title", [])
        title = title_list[0] if title_list else ""
        
        # summary (abstract)
        summary = item.get("abstract", "")
        
        # authors
        authors = []
        for author in item.get("author", []):
            if "given" in author and "family" in author:
                authors.append(f"{author['given']} {author['family']}")
            elif "name" in author:
                authors.append(author["name"])
                
        # categories
        categories = item.get("subject", [])
        primary_category = categories[0] if categories else ""
        
        # published
        published_obj = item.get("published", item.get("published-print", item.get("published-online", {})))
        date_parts = published_obj.get("date-parts", [[]])[0]
        published = "-".join(f"{part:02d}" for part in date_parts) if date_parts else ""
        
        # updated
        indexed_obj = item.get("indexed", {})
        indexed_date_parts = indexed_obj.get("date-parts", [[]])[0]
        updated = "-".join(f"{part:02d}" for part in indexed_date_parts) if indexed_date_parts else ""
        
        # urls
        abs_url = item.get("URL", "")
        pdf_url = ""
        for link in item.get("link", []):
            if link.get("content-type") == "application/pdf":
                pdf_url = link.get("URL", "")
                break
                
        comment = ""
        
        records.append(PaperRecord(
            paper_id=paper_id,
            title=title,
            summary=summary,
            authors=authors,
            categories=categories,
            primary_category=primary_category,
            published=published,
            updated=updated,
            abs_url=abs_url,
            pdf_url=pdf_url,
            comment=comment
        ))
        
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results
    }
    
    max_retries = 3
    payload = {}
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params)
            if response.status_code in [429, 503]:
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            payload = response.json()
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)

    settings.paths.raw_api_response.parent.mkdir(parents=True, exist_ok=True)
            
    with open(settings.paths.raw_api_response, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        
    records = parse_crossref_payload(payload)
    
    settings.paths.raw_records_json.parent.mkdir(parents=True, exist_ok=True)
    with open(settings.paths.raw_records_json, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in records], f, ensure_ascii=False, indent=2)
        
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [PaperRecord(**r) for r in data]
