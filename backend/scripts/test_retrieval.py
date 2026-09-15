#!/usr/bin/env python
"""
Quick manual test of semantic retrieval (M1.4's last checklist item:
"Build and test semantic retrieval of similar historical bugs").

Usage:
    python scripts/test_retrieval.py "app crashes when resizing a CSS grid layout"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services import vector_store


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/test_retrieval.py "your bug description"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    count = vector_store.collection_count()
    if count == 0:
        print("Vector store is empty. Run scripts/ingest_knowledge_base.py first.")
        sys.exit(1)

    print(f'Query: "{query}"')
    print(f"(searching across {count} indexed chunks)\n")

    matches = vector_store.search_similar(query, top_k=5)
    for i, m in enumerate(matches, start=1):
        meta = m["metadata"]
        print(f"#{i}  score={m['similarity_score']}  bug={meta['bug_id']}  "
              f"source={meta['source']}  field={meta['chunk_type']}")
        preview = m["text"][:160].replace("\n", " ")
        print(f"     {preview}{'...' if len(m['text']) > 160 else ''}\n")


if __name__ == "__main__":
    main()
