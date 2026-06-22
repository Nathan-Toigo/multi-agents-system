"""
FastAPI — RAG Service
Indexation vectorielle et recherche sémantique sur les documents de l'usine.

Endpoints :
  GET  /health          → état du service
  GET  /documents       → liste les documents indexés
  POST /search          → recherche sémantique
  POST /ingest/file     → upload et indexation d'un fichier
  POST /ingest/text     → indexation de texte brut
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .vector_store import ingest_file, ingest_text, search, list_sources, already_indexed
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─── Ingestion automatique au démarrage ───────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    docs_dir = Path(settings.docs_dir)
    if docs_dir.exists():
        for file in sorted(docs_dir.glob("*.md")):
            if not already_indexed(file.name):
                try:
                    n = ingest_file(str(file))
                    logger.info(f"✅ Indexé : {file.name} ({n} chunks)")
                except Exception as e:
                    logger.error(f"❌ Erreur indexation {file.name} : {e}")
            else:
                logger.info(f"⏭  Déjà indexé : {file.name}")
    else:
        logger.warning(f"Répertoire docs introuvable : {docs_dir}")
    yield


# ─── Application ─────────────────────────────────────────────────────────
app = FastAPI(
    title="📚 RAG Service",
    description=(
        "Service de Retrieval-Augmented Generation pour l'Usine de Cartons.\n\n"
        "Indexe les documents techniques (manuels, procédures, normes) "
        "et permet une **recherche sémantique** via Azure OpenAI Embeddings + ChromaDB.\n\n"
        "Utilisé par l'agent IA pour répondre à des questions sur la documentation."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Schémas ──────────────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str
    k: int = 4

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "procédure de maintenance de la découpeuse",
                "k": 3,
            }
        }
    }


class SearchResult(BaseModel):
    content: str
    source: str
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int


class IngestTextRequest(BaseModel):
    content: str
    source: str
    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "La maintenance préventive doit être effectuée...",
                "source": "mon_document.txt",
            }
        }
    }


# ─── Endpoints ────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    sources = list_sources()
    return {
        "status": "ok",
        "service": "rag-service",
        "version": "1.0.0",
        "embedding_model": f"Azure/{settings.azure_embedding_deployment}",
        "indexed_documents": len(sources),
        "sources": sources,
    }


@app.get("/documents", tags=["Documents"], summary="Lister les documents indexés")
async def list_documents():
    """Retourne la liste de tous les documents/sources présents dans l'index vectoriel."""
    sources = list_sources()
    return {"count": len(sources), "documents": sources}


@app.post("/search", response_model=SearchResponse, tags=["RAG"], summary="Recherche sémantique")
async def semantic_search(request: SearchRequest):
    """
    Effectue une recherche sémantique sur l'ensemble des documents indexés.
    Retourne les chunks les plus similaires à la requête (score de similarité cosinus).
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="La requête ne peut pas être vide.")
    try:
        results = search(request.query, k=min(request.k, 10))
        return SearchResponse(
            query=request.query,
            results=[SearchResult(**r) for r in results],
            total=len(results),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de recherche : {e}")


@app.post("/ingest/text", tags=["Documents"], summary="Indexer du texte brut")
async def ingest_raw_text(request: IngestTextRequest):
    """Indexe un texte brut avec un nom de source spécifié."""
    try:
        n = ingest_text(request.content, source=request.source)
        return {"message": f"Texte indexé avec succès.", "source": request.source, "chunks": n}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'indexation : {e}")


@app.post("/ingest/file", tags=["Documents"], summary="Uploader et indexer un fichier")
async def ingest_uploaded_file(file: UploadFile = File(...)):
    """
    Upload et indexe un fichier texte ou markdown.
    Formats supportés : .txt, .md
    """
    if not file.filename.endswith((".txt", ".md")):
        raise HTTPException(status_code=400, detail="Format supporté : .txt ou .md uniquement.")
    try:
        content = (await file.read()).decode("utf-8")
        n = ingest_text(content, source=file.filename)
        return {
            "message": "Fichier indexé avec succès.",
            "source": file.filename,
            "chunks": n,
            "size_bytes": len(content),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'indexation : {e}")
