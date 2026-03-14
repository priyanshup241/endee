from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

import msgpack
import numpy as np
import requests
from requests import Response
from sklearn.metrics.pairwise import cosine_similarity


class EndeeAPIError(RuntimeError):
    """Raised when the Endee API returns an unexpected response."""


@dataclass
class SyncResult:
    backend: str
    indexed_count: int
    reindexed: bool
    index_name: str


class VectorStore:
    backend_name = "unknown"

    def sync_products(
        self,
        products: Sequence[Dict[str, Any]],
        embeddings: np.ndarray,
        checksum: int,
    ) -> SyncResult:
        raise NotImplementedError

    def search(
        self,
        query_vector: Sequence[float],
        top_k: int = 5,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def get_status(self) -> Dict[str, Any]:
        raise NotImplementedError


class EndeeConnector(VectorStore):
    backend_name = "Endee"

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        index_name: str = "product_recommendations",
        auth_token: str = "",
        timeout_seconds: int = 10,
    ) -> None:
        self.base_url = f"http://{host}:{port}/api/v1"
        self.index_name = index_name
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

        if auth_token:
            self.session.headers.update({"Authorization": auth_token})

    def _request(self, method: str, path: str, **kwargs: Any) -> Response:
        response = self.session.request(
            method,
            f"{self.base_url}{path}",
            timeout=kwargs.pop("timeout", self.timeout_seconds),
            **kwargs,
        )
        return response

    def health_check(self) -> bool:
        try:
            response = self._request("GET", "/health", timeout=3)
            return response.ok
        except requests.RequestException:
            return False

    def get_index_info(self) -> Optional[Dict[str, Any]]:
        response = self._request("GET", f"/index/{self.index_name}/info")
        if response.status_code == 404:
            return None
        if not response.ok:
            raise EndeeAPIError(f"Failed to get index info: {response.text}")
        return response.json()

    def delete_index(self) -> None:
        response = self._request("DELETE", f"/index/{self.index_name}/delete")
        if response.status_code == 404:
            return
        if not response.ok:
            raise EndeeAPIError(f"Failed to delete index: {response.text}")

    def create_index(self, dimension: int, checksum: int) -> None:
        payload = {
            "index_name": self.index_name,
            "dim": dimension,
            "space_type": "cosine",
            "precision": "float32",
            "checksum": checksum,
        }
        response = self._request("POST", "/index/create", json=payload)
        if response.status_code not in (200, 201):
            raise EndeeAPIError(f"Failed to create index: {response.text}")

    def insert_products(
        self,
        products: Sequence[Dict[str, Any]],
        embeddings: np.ndarray,
    ) -> None:
        payload: List[Dict[str, Any]] = []

        for product, embedding in zip(products, embeddings, strict=True):
            filter_payload = {
                "category": product["category"],
                "brand": product["brand"],
            }
            payload.append(
                {
                    "id": str(product["id"]),
                    "vector": embedding.tolist(),
                    "meta": json.dumps(product, separators=(",", ":"), ensure_ascii=True),
                    "filter": json.dumps(filter_payload, separators=(",", ":"), ensure_ascii=True),
                }
            )

        response = self._request(
            "POST",
            f"/index/{self.index_name}/vector/insert",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        if not response.ok:
            raise EndeeAPIError(f"Failed to insert vectors: {response.text}")

    def sync_products(
        self,
        products: Sequence[Dict[str, Any]],
        embeddings: np.ndarray,
        checksum: int,
    ) -> SyncResult:
        info = self.get_index_info()
        needs_reindex = False

        if info is None:
            needs_reindex = True
        else:
            current_dimension = int(info.get("dimension", -1))
            current_count = int(info.get("total_elements", -1))
            current_checksum = int(info.get("checksum", -1))

            needs_reindex = (
                current_dimension != embeddings.shape[1]
                or current_count != len(products)
                or current_checksum != checksum
            )

        if needs_reindex and info is not None:
            self.delete_index()

        if needs_reindex:
            self.create_index(embeddings.shape[1], checksum)
            self.insert_products(products, embeddings)

        return SyncResult(
            backend=self.backend_name,
            indexed_count=len(products),
            reindexed=needs_reindex,
            index_name=self.index_name,
        )

    def search(
        self,
        query_vector: Sequence[float],
        top_k: int = 5,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "vector": [float(value) for value in query_vector],
            "k": top_k,
        }

        if category:
            payload["filter"] = json.dumps(
                [{"category": {"$eq": category}}],
                separators=(",", ":"),
                ensure_ascii=True,
            )

        response = self._request(
            "POST",
            f"/index/{self.index_name}/search",
            json=payload,
            timeout=15,
        )
        if not response.ok:
            raise EndeeAPIError(f"Search failed: {response.text}")

        unpacked = msgpack.unpackb(response.content, raw=False)
        raw_results = self._extract_results(unpacked)
        results: List[Dict[str, Any]] = []

        for item in raw_results:
            similarity, result_id, meta_blob = self._unpack_result(item)
            meta = self._decode_meta(meta_blob)
            if not meta:
                meta = {"id": result_id}

            meta["score"] = similarity
            meta["score_percent"] = max(0.0, min(100.0, similarity * 100.0))
            results.append(meta)

        return results

    def _extract_results(self, unpacked: Any) -> List[Any]:
        if isinstance(unpacked, dict):
            return unpacked.get("results", [])
        if isinstance(unpacked, list):
            return unpacked
        return []

    def _unpack_result(self, item: Any) -> tuple[float, str, Any]:
        if isinstance(item, dict):
            return (
                float(item.get("similarity", 0.0)),
                str(item.get("id", "")),
                item.get("meta"),
            )

        if isinstance(item, list) and len(item) >= 3:
            return (
                float(item[0]),
                str(item[1]),
                item[2],
            )

        return (0.0, "", None)

    def _decode_meta(self, meta_blob: Any) -> Dict[str, Any]:
        if meta_blob in (None, b"", ""):
            return {}

        if isinstance(meta_blob, str):
            payload = meta_blob
        elif isinstance(meta_blob, (bytes, bytearray)):
            payload = bytes(meta_blob).decode("utf-8")
        elif isinstance(meta_blob, list):
            payload = bytes(meta_blob).decode("utf-8")
        else:
            return {}

        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError:
            return {}

        if "brand" not in decoded and "name" in decoded:
            decoded["brand"] = decoded["name"].split(" ", 1)[0]
        return decoded

    def get_status(self) -> Dict[str, Any]:
        try:
            info = self.get_index_info()
        except Exception:
            return {
                "backend": self.backend_name,
                "connected": False,
                "index_name": self.index_name,
                "indexed_products": 0,
            }
        return {
            "backend": self.backend_name,
            "connected": True,
            "index_name": self.index_name,
            "indexed_products": int(info["total_elements"]) if info else 0,
        }


class InMemoryVectorDB(VectorStore):
    backend_name = "InMemory"

    def __init__(self, index_name: str = "product_recommendations") -> None:
        self.index_name = index_name
        self._products: List[Dict[str, Any]] = []
        self._embedding_matrix = np.empty((0, 0), dtype=np.float32)
        self._checksum = -1

    def sync_products(
        self,
        products: Sequence[Dict[str, Any]],
        embeddings: np.ndarray,
        checksum: int,
    ) -> SyncResult:
        self._products = [dict(product) for product in products]
        self._embedding_matrix = np.asarray(embeddings, dtype=np.float32)
        self._checksum = checksum
        return SyncResult(
            backend=self.backend_name,
            indexed_count=len(self._products),
            reindexed=True,
            index_name=self.index_name,
        )

    def search(
        self,
        query_vector: Sequence[float],
        top_k: int = 5,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if self._embedding_matrix.size == 0:
            return []

        scores = cosine_similarity(
            np.asarray(query_vector, dtype=np.float32).reshape(1, -1),
            self._embedding_matrix,
        )[0]

        ranked: List[Dict[str, Any]] = []
        for product, score in zip(self._products, scores, strict=True):
            if category and product["category"] != category:
                continue

            result = dict(product)
            result["score"] = float(score)
            result["score_percent"] = max(0.0, min(100.0, float(score) * 100.0))
            ranked.append(result)

        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked[:top_k]

    def get_status(self) -> Dict[str, Any]:
        return {
            "backend": self.backend_name,
            "connected": True,
            "index_name": self.index_name,
            "indexed_products": len(self._products),
            "checksum": self._checksum,
        }


def get_vector_db(
    host: str = "127.0.0.1",
    port: int = 8080,
    index_name: str = "product_recommendations",
    auth_token: str = "",
) -> VectorStore:
    db = EndeeConnector(
        host=host,
        port=port,
        index_name=index_name,
        auth_token=auth_token,
    )
    if db.health_check():
        return db
    return InMemoryVectorDB(index_name=index_name)
