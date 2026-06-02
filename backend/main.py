"""FastAPI application entry point for AI Data Extractor."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv()

from routers import agent_router, export_router, extract_router, upload_router


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    Path("uploads").mkdir(exist_ok=True)
    yield


app = FastAPI(
    title="AI Data Extractor",
    description=(
        "Upload documents (PDF, images, Word, Excel, CSV …), OCR/parse them, "
        "define a schema, extract structured data with AI, and export to "
        "JSON / JSONL / CSV / XLSX / TSV."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
origins = [o.strip() for o in origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(upload_router)
app.include_router(extract_router)
app.include_router(export_router)
app.include_router(agent_router)


# ---------------------------------------------------------------------------
# Serve compiled frontend (production)
# ---------------------------------------------------------------------------
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
