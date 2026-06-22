"""
Serveur MCP (Model Context Protocol) qui expose les 15 outils
de l'usine de cartons via le transport SSE.

Les clients MCP (Claude Desktop, Cursor, etc.) peuvent s'y connecter
et utiliser les mêmes outils que l'agent LangChain.
"""
import json
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions

from .tools.http import http_get, http_put, http_post, to_text
from .config import settings

# ─── Création du serveur MCP ───────────────────────────────────────────────
mcp_server = Server("usine-de-cartons")

S = settings  # shorthand


# ─── Liste des outils exposés ─────────────────────────────────────────────
@mcp_server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        # ── Stock ──────────────────────────────────────────────────────────
        types.Tool(
            name="list_stocks",
            description="Liste tous les articles en stock. Filtre optionnel par catégorie.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "raw_material | finished_product | consumable"},
                },
            },
        ),
        types.Tool(
            name="get_stock_alerts",
            description="Retourne les articles dont la quantité est sous le seuil critique.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="add_to_stock",
            description="Incrémente la quantité d'un article en stock.",
            inputSchema={
                "type": "object",
                "required": ["item_id", "quantity"],
                "properties": {
                    "item_id": {"type": "integer"},
                    "quantity": {"type": "number"},
                    "reason": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="remove_from_stock",
            description="Décrémente la quantité d'un article en stock.",
            inputSchema={
                "type": "object",
                "required": ["item_id", "quantity"],
                "properties": {
                    "item_id": {"type": "integer"},
                    "quantity": {"type": "number"},
                    "reason": {"type": "string"},
                },
            },
        ),
        # ── Production ─────────────────────────────────────────────────────
        types.Tool(
            name="list_productions",
            description="Liste les ordres de production. Filtre optionnel par statut.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "pending | in_progress | completed | cancelled"},
                },
            },
        ),
        types.Tool(
            name="create_production_order",
            description="Crée un nouvel ordre de production.",
            inputSchema={
                "type": "object",
                "required": ["product_name", "quantity_planned"],
                "properties": {
                    "product_name": {"type": "string"},
                    "quantity_planned": {"type": "integer"},
                    "machine_id": {"type": "integer"},
                    "notes": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="start_production",
            description="Démarre un ordre de production (pending → in_progress).",
            inputSchema={
                "type": "object",
                "required": ["production_id"],
                "properties": {"production_id": {"type": "integer"}},
            },
        ),
        types.Tool(
            name="complete_production",
            description="Termine un ordre de production (in_progress → completed).",
            inputSchema={
                "type": "object",
                "required": ["production_id"],
                "properties": {"production_id": {"type": "integer"}},
            },
        ),
        # ── Commandes ──────────────────────────────────────────────────────
        types.Tool(
            name="list_orders",
            description="Liste les commandes clients. Filtres optionnels par statut et client.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "customer": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="create_order",
            description="Crée une nouvelle commande client.",
            inputSchema={
                "type": "object",
                "required": ["customer_name", "product_name", "quantity"],
                "properties": {
                    "customer_name": {"type": "string"},
                    "product_name": {"type": "string"},
                    "quantity": {"type": "integer"},
                    "notes": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="update_order_status",
            description="Met à jour le statut d'une commande : pending | confirmed | in_production | delivered | cancelled.",
            inputSchema={
                "type": "object",
                "required": ["order_id", "status"],
                "properties": {
                    "order_id": {"type": "integer"},
                    "status": {"type": "string"},
                },
            },
        ),
        # ── Machines ───────────────────────────────────────────────────────
        types.Tool(
            name="list_machines",
            description="Liste les machines de l'usine. Filtre optionnel par statut.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "running | stopped | maintenance"},
                },
            },
        ),
        types.Tool(
            name="set_machine_status",
            description="Change le statut d'une machine : running | stopped | maintenance.",
            inputSchema={
                "type": "object",
                "required": ["machine_id", "status"],
                "properties": {
                    "machine_id": {"type": "integer"},
                    "status": {"type": "string"},
                },
            },
        ),
    ]


# ─── Exécution des outils ─────────────────────────────────────────────────
@mcp_server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    args = arguments or {}

    try:
        result = await _dispatch(name, args)
    except Exception as e:
        result = f"❌ Erreur lors de l'exécution de '{name}': {e}"

    return [types.TextContent(type="text", text=str(result))]


async def _dispatch(name: str, args: dict) -> str:
    # ── Stock ──
    if name == "list_stocks":
        params = {"category": args["category"]} if args.get("category") else {}
        data = await http_get(f"{S.stock_url}/stocks", params)
        return to_text(data) if data else "Stock vide."

    if name == "get_stock_alerts":
        data = await http_get(f"{S.stock_url}/stocks/alerts")
        return to_text(data) if data else "Aucun article en alerte."

    if name == "add_to_stock":
        data = await http_put(
            f"{S.stock_url}/stocks/{args['item_id']}/add",
            {"quantity": args["quantity"], "reason": args.get("reason", "MCP")},
        )
        return f"Stock mis à jour : {data['name']} → {data['quantity']} {data['unit']}"

    if name == "remove_from_stock":
        data = await http_put(
            f"{S.stock_url}/stocks/{args['item_id']}/remove",
            {"quantity": args["quantity"], "reason": args.get("reason", "MCP")},
        )
        return f"Stock consommé : {data['name']} → {data['quantity']} {data['unit']} restants"

    # ── Production ──
    if name == "list_productions":
        params = {"status": args["status"]} if args.get("status") else {}
        data = await http_get(f"{S.production_url}/productions", params)
        return to_text(data) if data else "Aucun ordre."

    if name == "create_production_order":
        body = {"product_name": args["product_name"], "quantity_planned": args["quantity_planned"]}
        if args.get("machine_id"):
            body["machine_id"] = args["machine_id"]
        if args.get("notes"):
            body["notes"] = args["notes"]
        data = await http_post(f"{S.production_url}/productions", body)
        return f"Ordre créé : {data['reference']} ({data['status']})"

    if name == "start_production":
        data = await http_put(f"{S.production_url}/productions/{args['production_id']}/start")
        return f"Production démarrée : {data['reference']}"

    if name == "complete_production":
        data = await http_put(f"{S.production_url}/productions/{args['production_id']}/complete")
        return f"Production terminée : {data['reference']}, {data['quantity_produced']} unités"

    # ── Commandes ──
    if name == "list_orders":
        params = {}
        if args.get("status"):
            params["status"] = args["status"]
        if args.get("customer"):
            params["customer"] = args["customer"]
        data = await http_get(f"{S.order_url}/orders", params)
        return to_text(data) if data else "Aucune commande."

    if name == "create_order":
        body = {
            "customer_name": args["customer_name"],
            "product_name": args["product_name"],
            "quantity": args["quantity"],
        }
        if args.get("notes"):
            body["notes"] = args["notes"]
        data = await http_post(f"{S.order_url}/orders", body)
        return f"Commande créée : {data['reference']}"

    if name == "update_order_status":
        data = await http_put(
            f"{S.order_url}/orders/{args['order_id']}/status",
            {"status": args["status"]},
        )
        return f"Commande {data['reference']} → {data['status']}"

    # ── Machines ──
    if name == "list_machines":
        params = {"status": args["status"]} if args.get("status") else {}
        data = await http_get(f"{S.machine_url}/machines", params)
        return to_text(data) if data else "Aucune machine."

    if name == "set_machine_status":
        data = await http_put(
            f"{S.machine_url}/machines/{args['machine_id']}/status",
            {"status": args["status"]},
        )
        return f"Machine '{data['name']}' → {data['status']}"

    return f"Outil inconnu : {name}"


def get_initialization_options() -> InitializationOptions:
    return mcp_server.create_initialization_options()
