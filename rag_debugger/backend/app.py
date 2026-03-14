from __future__ import annotations

import traceback

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from recommendation_engine import RecommendationEngine


app = FastAPI(title="AI Product Recommendation Engine")
engine = RecommendationEngine()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "AI Product Recommendation Engine running"}


@app.get("/status")
def status() -> dict:
    try:
        return engine.get_status()
    except Exception as exc:
        return {
            "ready": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }


@app.get("/products")
def get_products(
    limit: int = Query(default=12, ge=1, le=50),
    category: str | None = Query(default=None),
) -> dict:
    try:
        products = engine.list_products(limit=limit, category=category)
        return {
            "products": products,
            "count": len(products),
            "category": category,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        ) from exc


@app.get("/recommend")
def recommend(
    query: str = Query(..., min_length=2),
    top_k: int = Query(default=6, ge=1, le=20),
    category: str | None = Query(default=None),
) -> dict:
    try:
        recommendation_result = engine.recommend_with_context(
            query=query,
            top_k=top_k,
            category=category,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        ) from exc

    return {
        "query": query,
        "category": category,
        "available": recommendation_result["available"],
        "message": recommendation_result["message"],
        "recommendations": recommendation_result["recommendations"],
        "rag_brief": recommendation_result["rag_brief"],
        "status": engine.get_status(),
    }
