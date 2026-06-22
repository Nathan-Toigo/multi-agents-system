import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ── Fournisseur LLM ────────────────────────────────────────────────
    # "azure"  → Azure OpenAI / Azure AI Foundry (recommandé)
    # "openai" → API OpenAI directe (fallback)
    llm_provider: str = os.getenv("LLM_PROVIDER", "azure")

    # ── Azure OpenAI / AI Foundry ──────────────────────────────────────
    # Endpoint : https://<votre-ressource>.openai.azure.com/
    # Ou endpoint Azure AI Foundry : https://<project>.services.ai.azure.com/
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    # Nom du déploiement dans Azure AI Foundry ou Azure OpenAI Service
    azure_openai_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.2")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")
    azure_embedding_deployment: str = os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")

    # ── Azure Content Safety ───────────────────────────────────────────
    # Endpoint : https://<votre-ressource>.cognitiveservices.azure.com/
    azure_content_safety_endpoint: str = os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT", "")
    azure_content_safety_key: str = os.getenv("AZURE_CONTENT_SAFETY_KEY", "")
    # Seuil de sévérité (0-7) : 2=faible, 4=moyen, 6=élevé
    content_safety_threshold: int = int(os.getenv("CONTENT_SAFETY_THRESHOLD", "4"))
    content_safety_enabled: bool = (
        os.getenv("CONTENT_SAFETY_ENABLED", "false").lower() == "true"
    )

    # ── OpenAI direct (fallback) ───────────────────────────────────────
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # ── URLs des microservices ─────────────────────────────────────────
    stock_url: str = os.getenv("STOCK_SERVICE_URL", "http://stock-service:8000")
    production_url: str = os.getenv("PRODUCTION_SERVICE_URL", "http://production-service:8000")
    order_url: str = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000")
    machine_url: str = os.getenv("MACHINE_SERVICE_URL", "http://machine-service:8000")
    rag_url: str = os.getenv("RAG_SERVICE_URL", "http://rag-service:8000")


settings = Settings()
