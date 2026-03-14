from __future__ import annotations

from recommendation_engine import RecommendationEngine


def main() -> None:
    engine = RecommendationEngine()
    engine.ensure_ready()
    status = engine.get_status()

    print("Products indexed successfully")
    print(f"Vector backend: {status['vector_backend']}")
    print(f"Embedding model: {status['embedding_model']}")
    print(f"Indexed products: {status['indexed_products']}")
    print(f"Index name: {status['index_name']}")
    print(f"Reindexed this run: {status['reindexed']}")


if __name__ == "__main__":
    main()
