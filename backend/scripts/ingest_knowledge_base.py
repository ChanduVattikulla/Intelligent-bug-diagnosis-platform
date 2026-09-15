#!/usr/bin/env python
"""
Historical Defect Knowledge Base ingestion pipeline .

Run this from the backend/ folder:
    python scripts/ingest_knowledge_base.py

What it does, end to end:
  1. Reads every CSV in data/raw/
  2. Cleans + standardizes each into the common schema (app/services/data_cleaning.py)
  3. Chunks each bug report by field, splitting long fields with overlap
     (app/services/chunking.py)
  4. Generates embeddings for every chunk (app/services/embeddings.py —
     downloads the model on first run, needs internet once)
  5. Indexes everything into the local vector store (app/services/vector_store.py)

Swapping in real data: download a Mozilla/Apache/Eclipse bug-report CSV from
Kaggle, drop it into data/raw/, and re-run this script — column names don't
need to match exactly, see COLUMN_ALIASES in app/services/data_cleaning.py.
The filename (minus extension) is used as the 'source' label, e.g.
'mozilla_bugs_2023.csv' -> source = 'mozilla_bugs_2023'. Rename the file
first if you want a cleaner source label like 'mozilla'.
"""

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # allow `import app.*`

from app.config import RAW_DATA_DIR, MAX_ROWS_PER_FILE
from app.services.data_cleaning import standardize_dataframe
from app.services.chunking import chunk_bug_report
from app.services import vector_store


def load_and_clean_all() -> pd.DataFrame:
    csv_files = sorted(RAW_DATA_DIR.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in {RAW_DATA_DIR}. Add a dataset and re-run.")
        sys.exit(1)

    cleaned_frames = []
    for csv_path in csv_files:
        source_label = csv_path.stem.replace("sample_", "").replace("_real", "")
        print(f"Loading {csv_path.name} (source='{source_label}')...")

        raw_df = pd.read_csv(csv_path)
        print(f"  columns found: {list(raw_df.columns)}")
        print(f"  total rows in file: {len(raw_df)}")

        if len(raw_df) > MAX_ROWS_PER_FILE:
            print(f"  capping at {MAX_ROWS_PER_FILE} rows for this run (see MAX_ROWS_PER_FILE below)")
            raw_df = raw_df.sample(n=MAX_ROWS_PER_FILE, random_state=42)

        cleaned_df = standardize_dataframe(raw_df, source=source_label)
        usable_pct = (len(cleaned_df) / len(raw_df) * 100) if len(raw_df) else 0
        print(f"  -> {len(cleaned_df)} usable rows after cleaning ({usable_pct:.0f}% of rows had recognizable content)")
        if usable_pct < 30:
            print(
                "  ⚠ LOW MATCH RATE — this dataset's column names probably aren't fully covered "
                "by COLUMN_ALIASES in app/services/data_cleaning.py. Check the 'columns found' "
                "line above against COLUMN_ALIASES and add any missing variants."
            )
        cleaned_frames.append(cleaned_df)
        print()

    return pd.concat(cleaned_frames, ignore_index=True)


def main():
    started = time.time()

    print("=== Step 1-2: Load and clean historical bug datasets ===")
    all_bugs = load_and_clean_all()
    print(f"Total cleaned bug reports: {len(all_bugs)}\n")

    print("=== Step 3: Chunking ===")
    all_chunks = []
    for _, row in all_bugs.iterrows():
        all_chunks.extend(chunk_bug_report(row.to_dict()))
    print(f"Total chunks produced: {len(all_chunks)}\n")

    if not all_chunks:
        print("No chunks were produced — check that your CSVs have text in the expected fields.")
        sys.exit(1)

    print("=== Step 4-5: Embedding + vector store indexing ===")
    print("(First run downloads the embedding model — needs internet once.)")
    indexed_count = vector_store.index_chunks(all_chunks)
    print(f"Indexed {indexed_count} chunks into the vector store.\n")

    elapsed = time.time() - started
    print(f"Done in {elapsed:.1f}s. Vector store now has {vector_store.collection_count()} total chunks.")
    print("Try it: python scripts/test_retrieval.py \"your bug description here\"")


if __name__ == "__main__":
    main()
