"""
Outils LangChain pour le service Production.
"""
from langchain_core.tools import tool
from ..config import settings
from .http import http_get, http_put, http_post, to_text

BASE = settings.production_url


@tool
async def list_productions(status: str = "") -> str:
    """
    Liste les ordres de production de l'usine.
    Paramètre optionnel 'status' pour filtrer :
    'pending' (en attente), 'in_progress' (en cours),
    'completed' (terminé), 'cancelled' (annulé).
    Retourne les références, produits, quantités et statuts.
    """
    params = {"status": status} if status else {}
    data = await http_get(f"{BASE}/productions", params)
    if not data:
        return "Aucun ordre de production trouvé."
    return to_text(data)


@tool
async def create_production_order(product_name: str, quantity_planned: int, machine_id: int = 0, notes: str = "") -> str:
    """
    Crée un nouvel ordre de production.
    Paramètres :
      - product_name : nom du produit à fabriquer (ex: 'Boîte américaine 300x200mm')
      - quantity_planned : nombre d'unités à produire
      - machine_id : ID de la machine à utiliser (0 = non assignée)
      - notes : remarques optionnelles
    Retourne la référence de l'ordre créé (format PROD-YYYY-XXXXXX).
    """
    body = {
        "product_name": product_name,
        "quantity_planned": quantity_planned,
    }
    if machine_id:
        body["machine_id"] = machine_id
    if notes:
        body["notes"] = notes
    data = await http_post(f"{BASE}/productions", body)
    return f"✅ Ordre créé : {data['reference']} — {data['product_name']} × {data['quantity_planned']} unités (statut: {data['status']})"


@tool
async def start_production(production_id: int) -> str:
    """
    Démarre un ordre de production (passe de 'pending' à 'in_progress').
    Utilise 'list_productions' pour trouver le production_id.
    Paramètre : production_id (int).
    """
    data = await http_put(f"{BASE}/productions/{production_id}/start")
    return f"▶️ Production démarrée : {data['reference']} — {data['product_name']} (démarré à {data['started_at']})"


@tool
async def complete_production(production_id: int) -> str:
    """
    Termine un ordre de production (passe de 'in_progress' à 'completed').
    Utilise 'list_productions' pour trouver le production_id.
    Paramètre : production_id (int).
    """
    data = await http_put(f"{BASE}/productions/{production_id}/complete")
    return f"✅ Production terminée : {data['reference']} — {data['quantity_produced']} unités produites"
