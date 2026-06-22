"""
Couche d'accès au vector store ChromaDB avec Azure OpenAI Embeddings.
"""
from __future__ import annotations
import logging
import os
from pathlib import Path

from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from .config import settings

logger = logging.getLogger(__name__)

# ─── Embeddings Azure OpenAI ──────────────────────────────────────────────
def _create_embeddings() -> AzureOpenAIEmbeddings:
    return AzureOpenAIEmbeddings(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        azure_deployment=settings.azure_embedding_deployment,
        openai_api_version=settings.azure_openai_api_version,
    )


# ─── Vector store (singleton) ─────────────────────────────────────────────
_vectorstore: Chroma | None = None


def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        embeddings = _create_embeddings()
        _vectorstore = Chroma(
            collection_name="factory_docs",
            embedding_function=embeddings,
            persist_directory=settings.chroma_persist_dir,
        )
        logger.info(f"ChromaDB initialisé → {settings.chroma_persist_dir}")
    return _vectorstore


# ─── Chunking & ingestion ─────────────────────────────────────────────────
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=80,
    separators=["\n## ", "\n### ", "\n\n", "\n", " "],
)


def ingest_text(content: str, source: str, metadata: dict | None = None) -> int:
    """
    Découpe le texte en chunks et les indexe dans ChromaDB.
    Retourne le nombre de chunks créés.
    """
    chunks = _splitter.split_text(content)
    docs = [
        Document(
            page_content=chunk,
            metadata={"source": source, **(metadata or {})},
        )
        for chunk in chunks
    ]
    get_vectorstore().add_documents(docs)
    logger.info(f"Ingéré '{source}' → {len(chunks)} chunks")
    return len(chunks)


def ingest_file(file_path: str) -> int:
    """Lit un fichier .md/.txt et l'ingère dans ChromaDB."""
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")
    return ingest_text(content, source=path.name)


# ─── Recherche sémantique ─────────────────────────────────────────────────
def search(query: str, k: int = 4) -> list[dict]:
    """
    Recherche sémantique : retourne les k chunks les plus similaires.
    """
    vs = get_vectorstore()
    results = vs.similarity_search_with_relevance_scores(query, k=k)
    return [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source", "inconnu"),
            "score": round(float(score), 3),
        }
        for doc, score in results
        if score > 0.3  # filtre les résultats trop éloignés
    ]


# ─── Liste des documents indexés ─────────────────────────────────────────
def list_sources() -> list[str]:
    """Retourne la liste des noms de fichiers indexés (sources uniques)."""
    try:
        vs = get_vectorstore()
        result = vs._collection.get(include=["metadatas"])
        sources = sorted({m.get("source", "?") for m in result["metadatas"]})
        return sources
    except Exception as e:
        logger.warning(f"Impossible de lister les sources : {e}")
        return []


def already_indexed(source_name: str) -> bool:
    """Vérifie si une source est déjà dans l'index."""
    return source_name in list_sources()
