"""
Outils LangChain pour le service Machines.
"""
from langchain_core.tools import tool
from ..config import settings
from .http import http_get, http_put, to_text

BASE = settings.machine_url


@tool
async def list_machines(status: str = "") -> str:
    """
    Liste les machines de l'usine de cartons avec leur état opérationnel.
    Paramètre optionnel 'status' : 'running' (en marche), 'stopped' (arrêtée), 'maintenance'.
    Retourne le nom, type, localisation, capacité et statut de chaque machine.
    """
    params = {"status": status} if status else {}
    data = await http_get(f"{BASE}/machines/", params)
    if not data:
        return "Aucune machine trouvée."
    return to_text(data)


@tool
async def get_machine(machine_id: int) -> str:
    """
    Retourne les informations détaillées d'une machine spécifique.
    Utilise 'list_machines' pour trouver le machine_id.
    Paramètre : machine_id (int).
    """
    data = await http_get(f"{BASE}/machines/{machine_id}")
    return to_text(data)


@tool
async def set_machine_status(machine_id: int, status: str) -> str:
    """
    Change le statut opérationnel d'une machine.
    Valeurs acceptées : 'running' (démarrer), 'stopped' (arrêter), 'maintenance' (mise en maintenance).
    Passer en 'maintenance' enregistre automatiquement la date de dernière maintenance.
    Utilise 'list_machines' pour trouver le machine_id.
    Paramètres : machine_id (int), status (str).
    """
    data = await http_put(f"{BASE}/machines/{machine_id}/status", {"status": status})
    status_labels = {"running": "▶️ En marche", "stopped": "⏹ Arrêtée", "maintenance": "🔧 En maintenance"}
    label = status_labels.get(data["status"], data["status"])
    return f"{label} : Machine '{data['name']}' (id={data['id']}) — statut mis à jour"
