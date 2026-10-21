"""Build the retrieval index from the curated corpus.

Usage:
    python ingest.py
"""
from src import index as index_mod
import config


def main():
    records = index_mod.build_index()
    print(f"Index built: {len(records)} chunks -> {config.INDEX_PATH}")


if __name__ == "__main__":
    main()
