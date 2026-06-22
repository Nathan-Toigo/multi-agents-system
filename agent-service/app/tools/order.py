"""
Outils LangChain pour le service Commandes.
"""
from langchain_core.tools import tool
from ..config import settings
from .http import http_get, http_put, http_post, to_text

BASE = settings.order_url


@tool
async def list_orders(status: str = "", customer: str = "") -> str:
    """
    Liste les commandes clients de l'usine.
    Paramètres optionnels :
      - status : 'pending', 'confirmed', 'in_production', 'delivered', 'cancelled'
      - customer : filtrer par nom de client (recherche partielle)
    Retourne les références, clients, produits, quantités et statuts.
    """
    params = {}
    if status:
        params["status"] = status
    if customer:
        params["customer"] = customer
    data = await http_get(f"{BASE}/orders", params)
    if not data:
        return "Aucune commande trouvée."
    return to_text(data)


@tool
async def create_order(customer_name: str, product_name: str, quantity: int, notes: str = "") -> str:
    """
    Crée une nouvelle commande client.
    Paramètres :
      - customer_name : nom du client ou de l'entreprise
      - product_name : produit commandé (ex: 'Boîte américaine 400x300mm')
      - quantity : nombre d'unités commandées
      - notes : remarques optionnelles (livraison, conditionnement…)
    Retourne la référence de la commande (format CMD-YYYY-XXXXXX).
    """
    body = {
        "customer_name": customer_name,
        "product_name": product_name,
        "quantity": quantity,
    }
    if notes:
        body["notes"] = notes
    data = await http_post(f"{BASE}/orders", body)
    return f"✅ Commande créée : {data['reference']} — {data['customer_name']}, {data['quantity']} × {data['product_name']}"


@tool
async def update_order_status(order_id: int, status: str) -> str:
    """
    Met à jour le statut d'une commande client.
    Valeurs acceptées : 'pending', 'confirmed', 'in_production', 'delivered', 'cancelled'.
    Utilise 'list_orders' pour trouver l'order_id.
    Paramètres : order_id (int), status (str).
    """
    data = await http_put(f"{BASE}/orders/{order_id}/status", {"status": status})
    return f"✅ Commande {data['reference']} → statut : {data['status']}"
