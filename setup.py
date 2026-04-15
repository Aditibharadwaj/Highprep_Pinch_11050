"""
setup.py
Run this ONCE after placing your Excel dataset in data/ to:
1. Verify the dataset loads correctly
2. Build the ChromaDB vector index

Usage: python setup.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from tools.data_loader import load_events, summarize_dataset
from tools.embeddings import build_vector_store


def main():
    print("=" * 50)
    print("Conference AI — Setup")
    print("=" * 50)

    # 1. Load dataset
    print("\n[1/2] Loading dataset...")
    try:
        events = load_events()
        summary = summarize_dataset(events)
        print(f"  ✅ Loaded {summary['total_events']} events")
        print(f"  Years: {', '.join(summary['years'])}")
        print(f"  Categories: {', '.join(summary['categories'][:5])}...")
        print(f"  Geographies: {', '.join(summary['geographies'])}")
    except FileNotFoundError as e:
        print(f"  ❌ {e}")
        print("  → Place your merged Excel file at: data/events_merged_2025_2026.xlsx")
        sys.exit(1)

    # 2. Build vector store
    print("\n[2/2] Building ChromaDB vector index (this takes ~30s)...")
    try:
        collection = build_vector_store(events)
        print(f"  ✅ Vector store built with {collection.count()} documents")
    except Exception as e:
        print(f"  ⚠️  Vector store build failed (non-critical): {e}")
        print("  → Semantic search won't work but basic agents will still function.")

    print("\n✅ Setup complete!")
    print("\nNext step: Run the app with:")
    print("  streamlit run ui/app.py")
    print("\nOr test agents from CLI:")
    print("  python agents/orchestrator.py")


if __name__ == "__main__":
    main()
