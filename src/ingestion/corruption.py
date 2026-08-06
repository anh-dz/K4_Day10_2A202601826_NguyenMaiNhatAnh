from __future__ import annotations

import logging
import random
from typing import Any

import pandas as pd

from core.utils import write_json

logger = logging.getLogger(__name__)


def _rebuild_text_for_embedding(row: pd.Series) -> str:
    """Rebuild text_for_embedding from current row values."""
    return (
        f"Title: {row['title']}\n"
        f"Authors: {row['authors_joined']}\n"
        f"Published: {row['published']}\n"
        f"Categories: {row['categories_joined']}\n"
        f"Summary: {row['summary']}"
    )


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate multiple types of data corruption for testing pipeline robustness.

    Corruption types:
    1. Drop some latest records.
    2. Blank summary on some rows.
    3. Inject noise into summary text.
    4. Truncate titles.
    5. Make published dates stale.
    6. Add duplicate rows.
    7. Rebuild text_for_embedding.
    8. Write corruption log.
    """
    corrupted = df.copy()
    log: list[dict[str, Any]] = []
    n = len(corrupted)

    if n == 0:
        write_json(output_log_path, log)
        return corrupted

    random.seed(42)

    # 1. Drop latest records (remove top 2 newest by published date)
    drop_count = min(2, n // 4)
    if drop_count > 0:
        sorted_df = corrupted.sort_values("published", ascending=False)
        drop_ids = sorted_df.head(drop_count)["paper_id"].tolist()
        corrupted = corrupted[~corrupted["paper_id"].isin(drop_ids)].copy()
        log.append({
            "type": "drop_latest",
            "description": f"Dropped {drop_count} latest records",
            "affected_ids": drop_ids,
            "count": drop_count,
        })
        logger.info("Corruption: dropped %d latest records", drop_count)

    # Refresh n after dropping
    n = len(corrupted)
    if n == 0:
        write_json(output_log_path, log)
        return corrupted

    # 2. Blank summary on some rows (2 rows)
    blank_count = min(2, n // 3)
    if blank_count > 0:
        blank_indices = random.sample(list(corrupted.index), blank_count)
        blank_ids = corrupted.loc[blank_indices, "paper_id"].tolist()
        corrupted.loc[blank_indices, "summary"] = ""
        corrupted.loc[blank_indices, "summary_chars"] = 0
        log.append({
            "type": "blank_summary",
            "description": f"Blanked summary on {blank_count} rows",
            "affected_ids": blank_ids,
            "count": blank_count,
        })
        logger.info("Corruption: blanked summary on %d rows", blank_count)

    # 3. Inject noise into summary (add random garbage text to 2 rows)
    noise_count = min(2, n // 3)
    if noise_count > 0:
        available_indices = [i for i in corrupted.index if i not in (blank_indices if blank_count > 0 else [])]
        noise_indices = random.sample(available_indices, min(noise_count, len(available_indices)))
        noise_ids = corrupted.loc[noise_indices, "paper_id"].tolist()
        noise_text = " XYZZY GIBBERISH DATA CORRUPTED Lorem ipsum dolor sit amet NOISE_INJECTED "
        for idx in noise_indices:
            original = corrupted.loc[idx, "summary"]
            corrupted.loc[idx, "summary"] = noise_text + str(original) + noise_text
            corrupted.loc[idx, "summary_chars"] = len(corrupted.loc[idx, "summary"])
        log.append({
            "type": "noise_injection",
            "description": f"Injected noise into {noise_count} summaries",
            "affected_ids": noise_ids,
            "count": noise_count,
        })
        logger.info("Corruption: injected noise into %d summaries", noise_count)

    # 4. Truncate titles (cut titles to first 10 chars for 2 rows)
    trunc_count = min(2, n // 3)
    if trunc_count > 0:
        trunc_indices = random.sample(list(corrupted.index), trunc_count)
        trunc_ids = corrupted.loc[trunc_indices, "paper_id"].tolist()
        for idx in trunc_indices:
            original_title = corrupted.loc[idx, "title"]
            corrupted.loc[idx, "title"] = str(original_title)[:10] + "..."
        log.append({
            "type": "truncate_title",
            "description": f"Truncated {trunc_count} titles to 10 chars",
            "affected_ids": trunc_ids,
            "count": trunc_count,
        })
        logger.info("Corruption: truncated %d titles", trunc_count)

    # 5. Stale published dates (set dates to 2 years ago for 3 rows)
    stale_count = min(3, n // 3)
    if stale_count > 0:
        stale_indices = random.sample(list(corrupted.index), stale_count)
        stale_ids = corrupted.loc[stale_indices, "paper_id"].tolist()
        for idx in stale_indices:
            corrupted.loc[idx, "published"] = "2020-01-01"
            corrupted.loc[idx, "age_days"] = 2000
        log.append({
            "type": "stale_dates",
            "description": f"Set {stale_count} records to stale publication date (2020-01-01)",
            "affected_ids": stale_ids,
            "count": stale_count,
        })
        logger.info("Corruption: made %d records stale", stale_count)

    # 6. Add duplicate rows (duplicate 2 random rows)
    dup_count = min(2, n // 3)
    if dup_count > 0:
        dup_indices = random.sample(list(corrupted.index), dup_count)
        dup_ids = corrupted.loc[dup_indices, "paper_id"].tolist()
        dup_rows = corrupted.loc[dup_indices].copy()
        corrupted = pd.concat([corrupted, dup_rows], ignore_index=True)
        log.append({
            "type": "duplicates",
            "description": f"Added {dup_count} duplicate rows",
            "affected_ids": dup_ids,
            "count": dup_count,
        })
        logger.info("Corruption: added %d duplicate rows", dup_count)

    # 7. Rebuild text_for_embedding for all rows
    corrupted["text_for_embedding"] = corrupted.apply(_rebuild_text_for_embedding, axis=1)

    # 8. Write corruption log
    write_json(output_log_path, log)
    logger.info("Corruption log saved to %s with %d corruption types applied", output_log_path, len(log))

    return corrupted
