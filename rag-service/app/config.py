import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Azure OpenAI (partagé avec agent-service)
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")
    # Déploiement du modèle d'embedding (ex: text-embedding-3-small)
    azure_embedding_deployment: str = os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
    # Répertoires
    chroma_persist_dir: str = "/app/data/chroma"
    docs_dir: str = "/app/docs"


settings = Settings()
