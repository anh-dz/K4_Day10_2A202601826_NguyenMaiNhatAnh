from __future__ import annotations

import json
import uuid
from typing import Any

import pandas as pd


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    if len(df) == 0:
        return []
        
    test_set = []
    # Pick top representative papers (up to 5)
    sample_size = min(5, len(df))
    sample_df = df.head(sample_size)
    
    for _, row in sample_df.iterrows():
        paper_id = row.get('paper_id', '')
        title = row.get('title', '')
        summary = row.get('summary', '')
        authors = row.get('authors_joined', str(row.get('authors', '')))
        categories = row.get('categories_joined', str(row.get('categories', '')))
        published = str(row.get('published', ''))
        
        # 1. Summary question
        test_set.append({
            "id": str(uuid.uuid4()),
            "question_type": "summary",
            "question": f"What is the main summary of the paper titled '{title}'?",
            "ground_truth": summary,
            "ground_truth_doc_ids": [paper_id]
        })
        
        # 2. Authors question
        test_set.append({
            "id": str(uuid.uuid4()),
            "question_type": "authors",
            "question": f"Who are the authors of the paper titled '{title}'?",
            "ground_truth": authors,
            "ground_truth_doc_ids": [paper_id]
        })
        
        # 3. Date question
        test_set.append({
            "id": str(uuid.uuid4()),
            "question_type": "date",
            "question": f"When was the paper '{title}' published?",
            "ground_truth": published,
            "ground_truth_doc_ids": [paper_id]
        })
        
        # 4. Categories question
        test_set.append({
            "id": str(uuid.uuid4()),
            "question_type": "categories",
            "question": f"What are the categories or subjects for the paper '{title}'?",
            "ground_truth": categories,
            "ground_truth_doc_ids": [paper_id]
        })
        
    # Make sure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
        
    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(test_set, f, ensure_ascii=False, indent=2)
        
    return test_set
