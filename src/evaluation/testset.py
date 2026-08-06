from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json

logger = logging.getLogger(__name__)

# Minimum number of documents required to build a test set
MIN_DOCS = 3


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Build evaluation test set from cleaned dataframe.

    Steps:
    1. Verify minimum document count.
    2. Select representative papers (with sufficient summary, authors, categories).
    3. Generate multiple question types per paper: summary, authors, date, categories.
    4. Each sample has: id, question_type, question, ground_truth, ground_truth_doc_ids.
    5. Write JSON to output_path.
    """
    if len(df) < MIN_DOCS:
        raise ValueError(f"Need at least {MIN_DOCS} documents to build test set, got {len(df)}.")

    test_set: list[dict[str, Any]] = []
    question_id = 0

    # Select papers with enough information for good questions
    candidates = df[
        (df["summary"].str.len() >= 50)
        & (df["authors_joined"].str.len() > 0)
        & (df["published"].str.len() > 0)
    ].copy()

    if len(candidates) < MIN_DOCS:
        # Fallback: use all papers if not enough candidates
        candidates = df.copy()

    # Limit to a reasonable number of papers to keep evaluation manageable
    max_papers = min(len(candidates), 12)
    selected = candidates.head(max_papers)

    for _, row in selected.iterrows():
        paper_id = row["paper_id"]
        title = row["title"]
        doc_ids = [paper_id]

        # 1. Summary question
        question_id += 1
        summary_answer = first_sentence(row["summary"])
        test_set.append(
            {
                "id": f"q{question_id:03d}",
                "question_type": "summary",
                "question": f"What is the paper '{title}' about?",
                "ground_truth": summary_answer,
                "ground_truth_doc_ids": doc_ids,
            }
        )

        # 2. Authors question
        if row["authors_joined"]:
            question_id += 1
            test_set.append(
                {
                    "id": f"q{question_id:03d}",
                    "question_type": "authors",
                    "question": f"Who authored the paper '{title}'?",
                    "ground_truth": row["authors_joined"],
                    "ground_truth_doc_ids": doc_ids,
                }
            )

        # 3. Date question
        if row["published"]:
            question_id += 1
            test_set.append(
                {
                    "id": f"q{question_id:03d}",
                    "question_type": "date",
                    "question": f"When was '{title}' published?",
                    "ground_truth": row["published"],
                    "ground_truth_doc_ids": doc_ids,
                }
            )

        # 4. Categories question
        if row.get("categories_joined"):
            question_id += 1
            test_set.append(
                {
                    "id": f"q{question_id:03d}",
                    "question_type": "categories",
                    "question": f"What categories does the paper '{title}' belong to?",
                    "ground_truth": row["categories_joined"],
                    "ground_truth_doc_ids": doc_ids,
                }
            )

    write_json(output_path, test_set)
    logger.info("Built test set with %d questions from %d papers, saved to %s", len(test_set), len(selected), output_path)
    return test_set
