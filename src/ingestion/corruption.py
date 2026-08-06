from __future__ import annotations

import json
import random
import pandas as pd


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    df_corrupted = df.copy()
    logs = []
    
    random.seed(42)
    
    # 1. Drop mot so latest records
    if len(df_corrupted) > 2:
        df_corrupted = df_corrupted.sort_values(by="published_dt", ascending=False)
        dropped = df_corrupted.head(2)
        df_corrupted = df_corrupted.iloc[2:]
        logs.append({"action": "drop_latest", "count": 2, "paper_ids": dropped["paper_id"].tolist()})
        
    # 2. Blank summary o mot so dong
    if len(df_corrupted) >= 2:
        indices = random.sample(list(df_corrupted.index), 2)
        df_corrupted.loc[indices, "summary"] = ""
        logs.append({"action": "blank_summary", "count": 2, "indices": indices})
        
    # 3. Inject noise vao text
    if len(df_corrupted) >= 2:
        indices = random.sample(list(df_corrupted.index), 2)
        df_corrupted.loc[indices, "summary"] = df_corrupted.loc[indices, "summary"] + " NOISE NOISE CORRUPTION "
        logs.append({"action": "inject_noise", "count": 2, "indices": indices})
        
    # 4. Lam title bi truncate
    if len(df_corrupted) >= 2:
        indices = random.sample(list(df_corrupted.index), 2)
        df_corrupted.loc[indices, "title"] = df_corrupted.loc[indices, "title"].apply(lambda x: str(x)[:10])
        logs.append({"action": "truncate_title", "count": 2, "indices": indices})
        
    # 5. Lam published date cu di
    if len(df_corrupted) >= 2:
        indices = random.sample(list(df_corrupted.index), 2)
        df_corrupted.loc[indices, "published_dt"] = df_corrupted.loc[indices, "published_dt"] - pd.Timedelta(days=1000)
        logs.append({"action": "stale_date", "count": 2, "indices": indices})
        
    # 6. Add duplicate rows
    if len(df_corrupted) >= 1:
        row_to_dup = df_corrupted.sample(1)
        df_corrupted = pd.concat([df_corrupted, row_to_dup], ignore_index=True)
        logs.append({"action": "add_duplicate", "count": 1, "paper_id": str(row_to_dup["paper_id"].values[0])})
        
    # 7. Rebuild text_for_embedding
    def build_embedding_text(row):
        return (
            f"Title: {row['title']}\n"
            f"Authors: {row['authors_joined']}\n"
            f"Categories: {row['categories_joined']}\n"
            f"Summary: {row['summary']}"
        )
    df_corrupted["text_for_embedding"] = df_corrupted.apply(build_embedding_text, axis=1)
    df_corrupted['summary_chars'] = df_corrupted['summary'].apply(lambda x: len(str(x)))
    
    # 8. Ghi corruption log
    output_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_log_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)
        
    return df_corrupted
