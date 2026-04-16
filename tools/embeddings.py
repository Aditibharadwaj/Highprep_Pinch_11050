"""
tools/embeddings.py
Builds a ChromaDB vector store from the event dataset for semantic search (RAG).
"""
import chromadb
from chromadb.utils import embedding_functions
import json
import os

COLLECTION_NAME = "conference_events"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/chroma_db")

def _event_to_document(event: dict) -> str:
    """Serialize an event dict into a searchable text document."""
    parts = []
    for key, val in event.items():
        if val:
            parts.append(f"{key}: {val}")
    return " | ".join(parts)


def build_vector_store(events: list[dict]) -> chromadb.Collection:
    """Build or load a ChromaDB collection from events."""
    client = chromadb.PersistentClient(path=DB_PATH)
    ef = embedding_functions.DefaultEmbeddingFunction()

    # Delete existing collection to rebuild fresh
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
    )

    documents = [_event_to_document(e) for e in events]
    ids = [f"event_{i}" for i in range(len(events))]
    metadatas = [
        {
            "event_name": str(e.get("Event Name", "")),
            "category": str(e.get("Category", "")),
            "geography": str(e.get("Geography", "")),
            "year": str(e.get("Year", "")),
        }
        for e in events
    ]

    # Add in batches of 100
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i : i + batch_size],
            ids=ids[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )

    print(f"[Embeddings] Indexed {len(documents)} events into ChromaDB.")
    return collection


def get_collection() -> chromadb.Collection:
    """Load existing ChromaDB collection."""
    client = chromadb.PersistentClient(path=DB_PATH)
    ef = embedding_functions.DefaultEmbeddingFunction()
    return client.get_collection(name=COLLECTION_NAME, embedding_function=ef)


def semantic_search(query: str, n_results: int = 10) -> list[dict]:
    """Run semantic search against the vector store."""
    collection = get_collection()
    results = collection.query(query_texts=[query], n_results=n_results)
    return results["metadatas"][0] if results["metadatas"] else []
