"""
Outils LangChain pour le service Stock.
"""
from langchain_core.tools import tool
from ..config import settings
from .http import http_get, http_put, http_post, to_text

BASE = settings.stock_url


@tool
async def list_stocks(category: str = "") -> str:
    """
    Liste tous les articles en stock de l'usine de cartons.
    Retourne les quantités disponibles, unités et catégories.
    Paramètre optionnel 'category': 'raw_material', 'finished_product' ou 'consumable'.
    """
    params = {"category": category} if category else {}
    data = await http_get(f"{BASE}/stocks", params)
    if not data:
        return "Le stock est vide."
    return to_text(data)


@tool
async def get_stock_alerts() -> str:
    """
    Retourne la liste des articles en stock critique,
    c'est-à-dire dont la quantité est inférieure au seuil minimum configuré.
    Utile pour identifier les ruptures de stock imminentes.
    """
    data = await http_get(f"{BASE}/stocks/alerts")
    if not data:
        return "Aucun article en stock critique. Tous les niveaux sont satisfaisants."
    return f"⚠️ {len(data)} article(s) sous le seuil critique :\n" + to_text(data)


@tool
async def add_to_stock(item_id: int, quantity: float, reason: str = "Réapprovisionnement") -> str:
    """
    Incrémente la quantité d'un article en stock.
    Utilise 'list_stocks' d'abord pour trouver l'item_id correct.
    Paramètres : item_id (int), quantity (float > 0), reason (str optionnel).
    """
    data = await http_put(
        f"{BASE}/stocks/{item_id}/add",
        {"quantity": quantity, "reason": reason},
    )
    return f"✅ Stock mis à jour : {data['name']} → {data['quantity']} {data['unit']}"


@tool
async def remove_from_stock(item_id: int, quantity: float, reason: str = "Consommation production") -> str:
    """
    Décrémente la quantité d'un article en stock.
    Échoue si le stock disponible est insuffisant.
    Utilise 'list_stocks' d'abord pour trouver l'item_id correct.
    Paramètres : item_id (int), quantity (float > 0), reason (str optionnel).
    """
    data = await http_put(
        f"{BASE}/stocks/{item_id}/remove",
        {"quantity": quantity, "reason": reason},
    )
    return f"✅ Stock consommé : {data['name']} → {data['quantity']} {data['unit']} restants"


@tool
async def create_stock_item(name: str, quantity: float, unit: str, category: str, min_threshold: float = 0.0) -> str:
    """
    Crée un nouvel article dans le stock.
    Paramètres :
      - name : nom de l'article
      - quantity : quantité initiale
      - unit : unité de mesure (ex: 'unités', 'kg', 'm2')
      - category : 'raw_material', 'finished_product' ou 'consumable'
      - min_threshold : seuil d'alerte (optionnel, défaut 0)
    """
    data = await http_post(f"{BASE}/stocks", {
        "name": name,
        "quantity": quantity,
        "unit": unit,
        "category": category,
        "min_threshold": min_threshold,
    })
    return f"✅ Article créé (id={data['id']}) : {data['name']}, {data['quantity']} {data['unit']}"
