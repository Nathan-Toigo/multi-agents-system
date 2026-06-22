"""
Azure Content Safety — couche de protection des entrées/sorties de l'agent.

Filtre les contenus selon 4 catégories :
  - Hate (haine)
  - SelfHarm (auto-mutilation)
  - Sexual (contenu sexuel)
  - Violence

Sévérité : 0 (aucun) → 7 (extrême). Le seuil par défaut est 4 (moyen).
Si le service n'est pas configuré, tous les messages passent sans filtrage.
"""
from __future__ import annotations
import logging

from .config import settings

logger = logging.getLogger(__name__)


def _get_client():
    """Retourne un client Azure Content Safety ou None si non configuré."""
    if not settings.content_safety_enabled:
        return None
    if not settings.azure_content_safety_endpoint or not settings.azure_content_safety_key:
        logger.warning("Content Safety activé mais AZURE_CONTENT_SAFETY_ENDPOINT ou KEY manquants.")
        return None
    try:
        from azure.ai.contentsafety import ContentSafetyClient
        from azure.core.credentials import AzureKeyCredential

        return ContentSafetyClient(
            endpoint=settings.azure_content_safety_endpoint,
            credential=AzureKeyCredential(settings.azure_content_safety_key),
        )
    except ImportError:
        logger.warning("Package azure-ai-contentsafety non installé.")
        return None


def analyze_text(text: str) -> dict:
    """
    Analyse un texte avec Azure Content Safety.

    Returns:
        {
            "safe": bool,
            "blocked_categories": list[str],   # catégories dépassant le seuil
            "details": dict,                   # sévérité par catégorie
        }
    """
    client = _get_client()
    if client is None:
        return {"safe": True, "blocked_categories": [], "details": {}}

    try:
        from azure.ai.contentsafety.models import AnalyzeTextOptions

        # Tronquer à 10 000 caractères (limite Azure)
        truncated = text[:10_000]
        request = AnalyzeTextOptions(text=truncated)
        response = client.analyze_text(request)

        details = {}
        blocked = []
        threshold = settings.content_safety_threshold

        for item in response.categories_analysis:
            details[str(item.category)] = item.severity
            if item.severity is not None and item.severity >= threshold:
                blocked.append(str(item.category))

        return {
            "safe": len(blocked) == 0,
            "blocked_categories": blocked,
            "details": details,
        }

    except Exception as e:
        logger.error(f"Erreur Azure Content Safety : {e}")
        # En cas d'erreur du service, on laisse passer (fail-open)
        return {"safe": True, "blocked_categories": [], "details": {"error": str(e)}}


def check_or_raise(text: str, context: str = "input") -> None:
    """
    Vérifie le texte et lève une exception HTTP si non conforme.
    Utilisé dans les endpoints FastAPI.
    """
    result = analyze_text(text)
    if not result["safe"]:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail={
                "error": "content_safety_violation",
                "message": f"Le {context} contient du contenu non autorisé.",
                "blocked_categories": result["blocked_categories"],
            },
        )
