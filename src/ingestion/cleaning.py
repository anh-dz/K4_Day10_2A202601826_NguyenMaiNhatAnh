from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from dataclasses import asdict

from ingestion.crossref import PaperRecord


def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_date(date_str: str) -> pd.Timestamp:
    if not date_str or not isinstance(date_str, str):
        return pd.NaT
    parts = date_str.split('-')
    try:
        if len(parts) == 1:
            return pd.to_datetime(date_str, format='%Y')
        elif len(parts) == 2:
            return pd.to_datetime(date_str, format='%Y-%m')
        else:
            return pd.to_datetime(date_str, format='%Y-%m-%d')
    except ValueError:
        return pd.NaT


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
        
    df = pd.DataFrame([asdict(r) for r in records])
    
    # 1. Normalize strings
    df['title'] = df['title'].apply(clean_text)
    df['summary'] = df['summary'].apply(clean_text)
    
    # 2. Join lists
    df['authors_joined'] = df['authors'].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    df['categories_joined'] = df['categories'].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    
    # 3. Parse dates
    df['published_dt'] = df['published'].apply(parse_date)
    
    # 4. Calculate age_days
    def calc_age(d):
        if pd.isna(d):
            return -1
        diff = run_date.date() - d.date()
        return diff.days
        
    df['age_days'] = df['published_dt'].apply(calc_age)
    
    # 5. Helper columns
    df['summary_chars'] = df['summary'].apply(len)
    
    def build_embedding_text(row):
        return (
            f"Title: {row['title']}\n"
            f"Authors: {row['authors_joined']}\n"
            f"Categories: {row['categories_joined']}\n"
            f"Summary: {row['summary']}"
        )
        
    df['text_for_embedding'] = df.apply(build_embedding_text, axis=1)
    
    # 6. Drop duplicates and filter bad rows
    df = df.dropna(subset=['paper_id', 'title', 'summary'])
    df = df[(df['title'] != '') & (df['summary'] != '')]
    df = df.drop_duplicates(subset=['paper_id'], keep='first')
    
    # 7. Sort
    df = df.sort_values(by='published_dt', ascending=False)
    
    return df


def save_clean_dataframe(df: pd.DataFrame, csv_path: Path, json_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    
    # convert datetime columns to string before saving to json to ensure compatibility
    df_out = df.copy()
    if 'published_dt' in df_out.columns:
        df_out['published_dt'] = df_out['published_dt'].dt.strftime('%Y-%m-%d')
        
    df_out.to_csv(csv_path, index=False, encoding='utf-8')
    df_out.to_json(json_path, orient='records', force_ascii=False, indent=2)
