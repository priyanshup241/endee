# AI Product Recommendation Engine

An Endee-powered retrieval-augmented product discovery project built for the Endee.io assessment. The application lets a user search a curated product catalog in natural language, retrieves the most relevant items from the Endee vector database, and presents both ranked product cards and an AI-style recommendation brief.

## Project Overview

Traditional product search often fails when users search by intent instead of exact product names. A user may type:

- `headphones for gaming and calls`
- `portable storage for creators`
- `laptop accessories for desk setup`

This project solves that problem by converting product descriptions into embeddings, storing them in Endee, and using semantic retrieval to return relevant products even when the wording does not exactly match the catalog.

## Problem Statement

Keyword search is brittle for recommendation-style discovery. Users usually describe use case, context, or need rather than exact SKU names. The goal of this project is to build a retrieval-first AI product advisor that:

- understands search intent semantically
- retrieves relevant products from a vector database
- supports category-aware browsing
- returns a compact recommendation brief on top of the result set

## Why This Project Fits The Assessment

This project directly aligns with the assessment requirements because it demonstrates:

- Endee as the vector database
- semantic search and recommendation workflows
- retrieval-augmented product exploration
- a production-style frontend + backend + vector database flow

## Key Features

- Endee-based vector indexing and semantic retrieval
- natural-language product search
- category-aware filtering
- unavailable-product handling with clean fallback messaging
- AI-style recommendation brief generated from retrieved context
- premium frontend dashboard with a Canva-inspired visual design
- INR pricing and product cards for a realistic marketplace feel

## Dataset Snapshot

The current catalog contains:

- `250` indexed products
- `25` distinct product varieties
- `9` product categories

Example categories:

- Accessories
- Audio
- Computers
- Creator
- Gaming
- Mobile
- Office
- Smart Home
- Wearables

## System Design

The project has three layers:

### 1. Frontend

- static HTML, CSS, and JavaScript UI
- search bar, category filter, recommendation cards, and AI summary panel
- served through a static server such as VS Code Live Server

### 2. Application Backend

- FastAPI backend in `backend/app.py`
- loads catalog data from `data/products.json`
- builds embeddings and prepares retrieval metadata
- synthesizes a recommendation brief from the retrieved results

### 3. Vector Database Layer

- Endee stores product vectors
- product embeddings are inserted with metadata payloads
- user queries are embedded and searched through Endee
- top semantic matches are returned to the backend for response generation

## How Endee Is Used

Endee is the core retrieval engine in this project.

Endee is used to:

- create the product index
- store embeddings for catalog items
- perform nearest-neighbor vector search
- return matched items with metadata
- support semantic recommendation instead of plain string matching

This means the backend does not rely on keyword-only search. The product recommendations are driven by vector retrieval.

## Retrieval-Augmented Flow

This project uses a retrieval-augmented recommendation flow:

1. The user enters a natural-language query.
2. The backend converts the query into an embedding.
3. Endee retrieves the most relevant products from the vector index.
4. The backend ranks, diversifies, and formats the results.
5. A compact AI-style recommendation brief is generated from the retrieved context.
6. The frontend displays both the summary and the product cards.

## Project Structure

```text
rag_debugger/
|-- backend/
|   |-- app.py
|   |-- endee_connector.py
|   |-- ingest_products.py
|   |-- recommendation_engine.py
|   `-- requirements.txt
|-- data/
|   |-- generate_products.py
|   `-- products.json
`-- frontend/
    |-- index.html
    |-- script.js
    `-- style.css
```

## Setup And Execution

### 1. Build Endee Docker Image

From the repository root:

```powershell
docker build --build-arg BUILD_ARCH=avx2 -t endee-oss:latest -f ./infra/Dockerfile .
```

### 2. Start Endee

From the repository root:

```powershell
docker compose up -d
```

Endee will run on:

```text
http://127.0.0.1:8080
```

### 3. Create A Python Virtual Environment

From `rag_debugger/backend`:

```powershell
python -m venv .venv2
```

### 4. Install Backend Dependencies

From `rag_debugger/backend`:

```powershell
.\.venv2\Scripts\python.exe -m pip install -r requirements.txt
```

### 5. Start The FastAPI Backend

From `rag_debugger/backend`:

```powershell
.\.venv2\Scripts\python.exe -m uvicorn app:app --port 8000 --log-level debug
```

The backend automatically:

- loads the dataset
- builds embeddings
- syncs the product catalog into Endee
- exposes the product and recommendation endpoints

### 6. Open The Frontend

Serve `rag_debugger/frontend` using VS Code Live Server or any simple static server, then open:

```text
http://127.0.0.1:5500/endee/rag_debugger/frontend/index.html
```

## API Endpoints

- `GET /status`
  Returns backend readiness, embedding mode, indexed product count, and available categories.

- `GET /products?limit=12&category=<optional>`
  Returns highlighted catalog products for browsing.

- `GET /recommend?query=<text>&top_k=8&category=<optional>`
  Returns semantic recommendations, availability status, and an AI-style recommendation brief.

## Demo Queries

Use these during evaluation:

- `wireless headphones`
- `gaming setup for students`
- `portable storage for creators`
- `desk setup for laptop`
- `audio device for calls`
- `smart home monitoring`

Unavailable example:

- `washing machine`

Expected behavior:

- if relevant products exist, ranked cards and a summary are shown
- if the item is not available in the catalog, the UI shows `Product not available.`

## Technical Notes

- Sentence Transformers can be used for richer embeddings when available.
- The backend can fall back to TF-IDF for compatibility on constrained local setups.
- Result diversification prevents the UI from filling with too many copies of the same product type.
- Product metadata includes brand, product type, category, description, price, and search-oriented terms.

## What Makes The Project Strong

- real vector-database integration through Endee
- semantic retrieval instead of basic keyword matching
- retrieval-augmented recommendation presentation
- complete working stack: frontend, backend, vector database, and dataset
- polished UI built for demo and evaluation

## Submission Checklist

Before final submission:

- make sure Docker Desktop and Endee are running
- confirm `GET /status` shows the indexed catalog correctly
- test at least 4 demo queries
- capture 2 to 3 screenshots of the UI
- push the project from your forked Endee repository
- include this README in the final GitHub submission
