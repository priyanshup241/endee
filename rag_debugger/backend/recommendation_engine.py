from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from endee_connector import EndeeAPIError, InMemoryVectorDB, SyncResult, VectorStore, get_vector_db

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency import
    SentenceTransformer = None


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "products.json"

IGNORED_QUERY_TERMS = {
    "a",
    "an",
    "and",
    "best",
    "built",
    "daily",
    "designed",
    "device",
    "fast",
    "for",
    "in",
    "of",
    "on",
    "portable",
    "practical",
    "product",
    "professional",
    "reliable",
    "setup",
    "smart",
    "the",
    "to",
    "use",
    "wireless",
    "with",
}


class ProductEmbedder:
    def __init__(self) -> None:
        self.backend_name = "tfidf"
        self.model_name = "TF-IDF (fallback)"
        self._sentence_model = None
        self._tfidf = TfidfVectorizer(max_features=384, stop_words="english")
        self._use_sentence_transformers = os.getenv("USE_SENTENCE_TRANSFORMERS", "0") == "1"

    @property
    def dimension(self) -> int:
        if self.backend_name == "sentence-transformers":
            return int(self._sentence_model.get_sentence_embedding_dimension())
        return len(self._tfidf.get_feature_names_out())

    def fit_transform(self, texts: Sequence[str]) -> np.ndarray:
        if self._use_sentence_transformers and SentenceTransformer is not None:
            try:
                self._sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
                self.backend_name = "sentence-transformers"
                self.model_name = "all-MiniLM-L6-v2"
                return self._sentence_model.encode(
                    list(texts),
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                ).astype(np.float32)
            except Exception:
                self._sentence_model = None

        self.backend_name = "tfidf"
        self.model_name = "TF-IDF (fallback)"
        matrix = self._tfidf.fit_transform(texts)
        return matrix.toarray().astype(np.float32)

    def transform_query(self, text: str) -> np.ndarray:
        if self.backend_name == "sentence-transformers" and self._sentence_model is not None:
            return self._sentence_model.encode(
                [text],
                convert_to_numpy=True,
                normalize_embeddings=True,
            )[0].astype(np.float32)

        return self._tfidf.transform([text]).toarray()[0].astype(np.float32)


class RecommendationEngine:
    def __init__(self, data_path: Path = DATA_PATH) -> None:
        self.data_path = data_path
        self._lock = threading.Lock()
        self._ready = False
        self._products: List[Dict[str, Any]] = []
        self._categories: List[str] = []
        self._catalog_terms: set[str] = set()
        self._catalog_varieties = 0
        self._embedder = ProductEmbedder()
        self._vector_db: Optional[VectorStore] = None
        self._sync_result: Optional[SyncResult] = None

    def ensure_ready(self) -> None:
        if self._ready:
            return

        with self._lock:
            if self._ready:
                return

            products = self._load_products()
            product_texts = [self._product_to_text(product) for product in products]
            embeddings = self._embedder.fit_transform(product_texts)
            checksum = self._build_checksum(products, self._embedder.model_name, embeddings.shape[1])

            vector_db = self._connect_vector_db()

            try:
                sync_result = vector_db.sync_products(products, embeddings, checksum)
            except (EndeeAPIError, OSError, ValueError):
                vector_db = InMemoryVectorDB(index_name=self._index_name())
                sync_result = vector_db.sync_products(products, embeddings, checksum)

            self._products = products
            self._categories = sorted({product["category"] for product in products})
            self._catalog_terms = self._build_catalog_terms(products)
            self._catalog_varieties = len(
                {
                    product.get("product_type", product["name"].split(" ", 1)[-1])
                    for product in products
                }
            )
            self._vector_db = vector_db
            self._sync_result = sync_result
            self._ready = True

    def get_status(self) -> Dict[str, Any]:
        self.ensure_ready()
        try:
            db_status = self._vector_db.get_status() if self._vector_db else {}
        except Exception:
            db_status = {
                "backend": self._sync_result.backend if self._sync_result else "unknown",
                "connected": False,
                "index_name": self._index_name(),
                "indexed_products": len(self._products),
            }
        return {
            "ready": self._ready,
            "vector_backend": db_status.get("backend", "unknown"),
            "connected": db_status.get("connected", False),
            "index_name": db_status.get("index_name", self._index_name()),
            "indexed_products": db_status.get("indexed_products", len(self._products)),
            "embedding_backend": self._embedder.backend_name,
            "embedding_model": self._embedder.model_name,
            "categories": self._categories,
            "catalog_varieties": self._catalog_varieties,
            "reindexed": self._sync_result.reindexed if self._sync_result else False,
        }

    def list_products(
        self,
        limit: Optional[int] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        self.ensure_ready()
        products = [dict(product) for product in self._products]
        if category:
            products = [product for product in products if product["category"] == category]
            products = self._dedupe_by_product_type(
                self._diversify_products(products),
                limit=limit or len(products),
            )
        else:
            products = self._diversify_products(products)
        if limit is not None:
            return products[:limit]
        return products

    def recommend(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return self.recommend_with_context(query=query, top_k=top_k, category=category)["recommendations"]

    def recommend_with_context(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.ensure_ready()
        query_vector = self._embedder.transform_query(query)
        if not self._query_has_catalog_match(query, query_vector):
            return {
                "available": False,
                "message": "Product not available.",
                "recommendations": [],
                "rag_brief": None,
            }

        results = self._vector_db.search(
            query_vector,
            top_k=max(top_k * 10, 40),
            category=category,
        )
        recommendations = self._filter_recommendations(results, top_k=top_k)
        if len(recommendations) < top_k:
            recommendations.extend(
                self._keyword_backfill(
                    query=query,
                    category=category,
                    exclude_product_types={
                        item.get("product_type", item["name"])
                        for item in recommendations
                    },
                    limit=top_k - len(recommendations),
                )
            )
        minimum_results = min(top_k, 4)
        if recommendations and len(recommendations) < minimum_results:
            recommendations.extend(
                self._category_backfill(
                    category=category or recommendations[0]["category"],
                    exclude_product_types={
                        item.get("product_type", item["name"])
                        for item in recommendations
                    },
                    limit=minimum_results - len(recommendations),
                )
            )
        if recommendations:
            return {
                "available": True,
                "message": None,
                "recommendations": recommendations,
                "rag_brief": self._build_rag_brief(
                    query=query,
                    category=category,
                    recommendations=recommendations,
                ),
            }

        message = "Product not available in the selected category." if category else "Product not available."
        return {
            "available": False,
            "message": message,
            "recommendations": [],
            "rag_brief": None,
        }

    def _connect_vector_db(self) -> VectorStore:
        return get_vector_db(
            host=os.getenv("ENDEE_HOST", "127.0.0.1"),
            port=int(os.getenv("ENDEE_PORT", "8080")),
            index_name=self._index_name(),
            auth_token=os.getenv("ENDEE_AUTH_TOKEN", os.getenv("NDD_AUTH_TOKEN", "")),
        )

    def _index_name(self) -> str:
        return os.getenv("ENDEE_INDEX_NAME", "product_recommendations")

    def _load_products(self) -> List[Dict[str, Any]]:
        with self.data_path.open(encoding="utf-8-sig") as file:
            raw_products = json.load(file)

        products: List[Dict[str, Any]] = []
        for item in raw_products:
            product = dict(item)
            if "brand" not in product:
                name_parts = product["name"].split(" ", 1)
                product["brand"] = name_parts[0]
            if "product_type" not in product:
                product["product_type"] = product["name"].split(" ", 1)[-1]
            product["title"] = product["name"]
            product["description"] = product["description"].strip()
            product["price_inr"] = int(product.get("price_inr", 2999))
            product["image_query"] = product.get("image_query", product["product_type"])
            products.append(product)
        return products

    def _product_to_text(self, product: Dict[str, Any]) -> str:
        return " ".join(
            [
                product["name"],
                product["brand"],
                product.get("product_type", ""),
                product["category"],
                product["description"],
                product.get("search_terms", ""),
            ]
        )

    def _query_has_catalog_match(self, query: str, query_vector: np.ndarray) -> bool:
        if not np.any(np.abs(query_vector) > 1e-9):
            return False

        query_terms = self._tokenize_terms(query)
        if not query_terms:
            return True

        return any(term in self._catalog_terms for term in query_terms)

    def _filter_recommendations(
        self,
        results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        if not results:
            return []

        top_score = float(results[0].get("score", 0.0))
        min_score = 0.08 if self._embedder.backend_name == "tfidf" else 0.22

        if top_score < min_score:
            return []

        cutoff = max(min_score, top_score * 0.82)
        strict_matches = [
            result
            for result in results
            if float(result.get("score", 0.0)) >= cutoff
        ]
        recommendations = self._dedupe_by_product_type(strict_matches, limit=top_k)

        if len(recommendations) >= top_k:
            return recommendations

        relaxed_matches = [
            result
            for result in results
            if float(result.get("score", 0.0)) >= min_score
        ]
        additional = self._dedupe_by_product_type(
            relaxed_matches,
            limit=top_k,
            used_product_types={
                item.get("product_type", item["name"])
                for item in recommendations
            },
        )
        return (recommendations + additional)[:top_k]

    def _build_catalog_terms(self, products: Sequence[Dict[str, Any]]) -> set[str]:
        catalog_terms: set[str] = set()
        for product in products:
            catalog_terms.update(self._tokenize_terms(product["name"]))
            catalog_terms.update(self._tokenize_terms(product.get("brand", "")))
            catalog_terms.update(self._tokenize_terms(product.get("product_type", "")))
            catalog_terms.update(self._tokenize_terms(product["category"]))
            catalog_terms.update(self._tokenize_terms(product.get("search_terms", "")))
        return catalog_terms

    def _diversify_products(self, products: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        buckets: dict[str, List[Dict[str, Any]]] = {}
        for product in products:
            bucket_key = f"{product['category']}::{product.get('product_type', product['name'])}"
            buckets.setdefault(bucket_key, []).append(product)

        ordered_products: List[Dict[str, Any]] = []
        bucket_keys = sorted(buckets.keys())
        index = 0

        while True:
            added_any = False
            for bucket_key in bucket_keys:
                bucket = buckets[bucket_key]
                if index < len(bucket):
                    ordered_products.append(bucket[index])
                    added_any = True
            if not added_any:
                break
            index += 1

        return ordered_products

    def _dedupe_by_product_type(
        self,
        results: Sequence[Dict[str, Any]],
        limit: int,
        used_product_types: Optional[set[str]] = None,
    ) -> List[Dict[str, Any]]:
        collected: List[Dict[str, Any]] = []
        seen_product_types = set(used_product_types or set())

        for result in results:
            product_type = result.get("product_type", result["name"])
            if product_type in seen_product_types:
                continue
            collected.append(result)
            seen_product_types.add(product_type)
            if len(collected) >= limit:
                break

        return collected

    def _keyword_backfill(
        self,
        query: str,
        category: Optional[str],
        exclude_product_types: set[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        if limit <= 0:
            return []

        query_terms = self._tokenize_terms(query)
        if not query_terms:
            return []

        candidates: List[Dict[str, Any]] = []
        for product in self._products:
            if category and product["category"] != category:
                continue

            product_type = product.get("product_type", product["name"])
            if product_type in exclude_product_types:
                continue

            product_terms = self._tokenize_terms(
                " ".join(
                    [
                        product["name"],
                        product.get("product_type", ""),
                        product["category"],
                        product.get("search_terms", ""),
                        product["description"],
                    ]
                )
            )
            overlap = query_terms & product_terms
            if not overlap:
                continue

            match_ratio = len(overlap) / max(len(query_terms), 1)
            candidate = dict(product)
            candidate["score"] = 0.12 + min(match_ratio, 1.0) * 0.24
            candidate["score_percent"] = candidate["score"] * 100.0
            candidate["_overlap"] = len(overlap)
            candidates.append(candidate)

        candidates.sort(
            key=lambda item: (
                item["_overlap"],
                item["score"],
                item["category"],
            ),
            reverse=True,
        )

        unique_results = self._dedupe_by_product_type(candidates, limit=limit)
        for item in unique_results:
            item.pop("_overlap", None)
        return unique_results

    def _category_backfill(
        self,
        category: str,
        exclude_product_types: set[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        if limit <= 0:
            return []

        candidates = [
            dict(product)
            for product in self._products
            if product["category"] == category
            and product.get("product_type", product["name"]) not in exclude_product_types
        ]

        for candidate in candidates:
            candidate["score"] = 0.11
            candidate["score_percent"] = 11.0

        return self._dedupe_by_product_type(candidates, limit=limit)

    def _build_rag_brief(
        self,
        query: str,
        category: Optional[str],
        recommendations: Sequence[Dict[str, Any]],
    ) -> Dict[str, Any]:
        top_pick = recommendations[0]
        categories = sorted({item["category"] for item in recommendations})
        product_types = [item.get("product_type", item["name"]) for item in recommendations]
        min_price = min(int(item.get("price_inr", 0)) for item in recommendations)
        max_price = max(int(item.get("price_inr", 0)) for item in recommendations)
        use_case_terms = sorted(self._tokenize_terms(query))
        if category:
            use_case_label = f"{category} focused search"
        elif use_case_terms:
            use_case_label = ", ".join(use_case_terms[:4])
        else:
            use_case_label = "general product discovery"

        reasons = [
            f"{top_pick['name']} is the strongest match because its metadata closely overlaps with your query intent.",
            f"The retrieved set covers {len(categories)} category{'ies' if len(categories) != 1 else ''} and avoids showing only one repeated product type.",
            f"The recommendation range stays between INR {min_price:,} and INR {max_price:,} so the results feel comparable and practical.",
        ]

        comparison = (
            f"Top matches include {', '.join(product_types[:3])}. "
            f"This gives you a mix of adjacent options instead of repeating one exact item."
        )

        summary = (
            f"For '{query}', the retrieval layer pulled the most relevant products from Endee and the advisor ranked "
            f"{top_pick['name']} as the clearest starting point. "
            f"These results are best suited for {use_case_label}."
        )

        return {
            "headline": f"AI recommendation for '{query}'",
            "summary": summary,
            "top_pick": {
                "name": top_pick["name"],
                "category": top_pick["category"],
                "price_inr": int(top_pick.get("price_inr", 0)),
            },
            "comparison": comparison,
            "reasons": reasons,
            "follow_up": "Refine the query with budget, use case, or preferred category to make the next retrieval even sharper.",
        }

    def _tokenize_terms(self, text: str) -> set[str]:
        normalized_terms: set[str] = set()
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            if token in IGNORED_QUERY_TERMS:
                continue
            normalized_terms.add(self._normalize_token(token))
        return normalized_terms

    def _normalize_token(self, token: str) -> str:
        if token.endswith("ies") and len(token) > 4:
            return token[:-3] + "y"
        if token.endswith("s") and len(token) > 4 and not token.endswith("ss"):
            return token[:-1]
        return token

    def _build_checksum(
        self,
        products: Sequence[Dict[str, Any]],
        embedding_model: str,
        dimension: int,
    ) -> int:
        payload = json.dumps(
            {
                "embedding_model": embedding_model,
                "dimension": dimension,
                "products": products,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha1(payload).digest()
        return int.from_bytes(digest[:4], "big") & 0x7FFFFFFF
