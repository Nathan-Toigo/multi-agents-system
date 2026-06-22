"""
FastAPI — Point d'entrée de l'agent-service.

Expose :
  POST /chat        → Envoyer un message à l'agent ReAct
  GET  /tools       → Lister les tools disponibles
  GET  /mcp/sse     → Connexion MCP via Server-Sent Events
  POST /mcp/messages → Messages MCP (transport SSE)
  GET  /health      → Santé du service
"""
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.requests import Request
from starlette.routing import Route

from mcp.server.sse import SseServerTransport

from .agent import run_agent, get_agent
from .mcp_server import mcp_server, get_initialization_options
from .tools import ALL_TOOLS
from .config import settings
from .content_safety import check_or_raise, analyze_text


# ─── Lifespan : pré-chargement de l'agent ─────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_agent()
        print(f"✅ Agent LangChain initialisé (provider={settings.llm_provider})")
    except Exception as e:
        print(f"⚠️  Agent non initialisé : {e}")
    if settings.content_safety_enabled:
        print("🛡️  Azure Content Safety activé")
    yield


# ─── Application FastAPI ──────────────────────────────────────────────────
app = FastAPI(
    title="🤖 Agent Service",
    description=(
        "Agent IA multi-outils pour la gestion de l'usine de cartons.\n\n"
        "Combine un **serveur MCP** (SSE) pour les clients externes "
        "et un **agent LangGraph ReAct** (GPT-4o-mini) pour le chat.\n\n"
        "**15 outils** : stock, production, commandes, machines."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── MCP SSE Transport ────────────────────────────────────────────────────
mcp_sse = SseServerTransport("/mcp/messages")


async def mcp_sse_endpoint(request: Request):
    """Connexion SSE pour clients MCP (Claude Desktop, Cursor, etc.)"""
    async with mcp_sse.connect_sse(
        request.scope, request.receive, request._send
    ) as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            get_initialization_options(),
        )


async def mcp_messages_endpoint(request: Request):
    """Réception des messages POST du transport MCP SSE."""
    await mcp_sse.handle_post_message(request.scope, request.receive, request._send)


# Ajout des routes MCP comme routes Starlette directes
app.router.routes.append(
    Route("/mcp/sse", endpoint=mcp_sse_endpoint, methods=["GET"])
)
app.router.routes.append(
    Route("/mcp/messages", endpoint=mcp_messages_endpoint, methods=["POST"])
)


# ─── Schémas API ──────────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Quel est l'état du stock ? Y a-t-il des alertes ?",
                "history": [],
            }
        }
    }


class StepInfo(BaseModel):
    type: str
    tool: str | None = None
    input: dict[str, Any] | None = None
    output: str | None = None


class ChatResponse(BaseModel):
    response: str
    steps: list[StepInfo]
    model: str
    tools_used: list[str]


# ─── Endpoints ────────────────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse, tags=["Agent"], summary="Envoyer un message à l'agent")
async def chat(request: ChatRequest):
    """
    Envoie un message à l'agent ReAct LangGraph.
    L'agent planifie, appelle les outils nécessaires et retourne une réponse.

    Le champ `history` permet de maintenir une conversation multi-tours.
    """
    # ── 1. Filtre Azure Content Safety sur l'entrée ──────────────────
    if settings.content_safety_enabled:
        check_or_raise(request.message, context="message utilisateur")

    try:
        history = [{"role": m.role, "content": m.content} for m in request.history]
        result = await run_agent(request.message, history)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de l'agent : {str(e)}")

    # ── 2. Filtre Azure Content Safety sur la sortie ───────────────────
    if settings.content_safety_enabled:
        check_or_raise(result["response"], context="réponse de l'agent")

    return ChatResponse(**result)


@app.get("/tools", tags=["Agent"], summary="Lister les outils disponibles")
async def list_tools():
    """Retourne la liste des 15 outils disponibles avec leurs descriptions."""
    return {
        "count": len(ALL_TOOLS),
        "tools": [
            {
                "name": t.name,
                "description": (t.description or "").split("\n")[0],
            }
            for t in ALL_TOOLS
        ],
    }


@app.get("/health", tags=["Health"], summary="État du service")
async def health():
    if settings.llm_provider == "azure":
        configured = bool(settings.azure_openai_endpoint and settings.azure_openai_key)
        model_label = f"Azure/{settings.azure_openai_deployment}"
    else:
        configured = bool(settings.openai_api_key)
        model_label = settings.openai_model

    return {
        "status": "ok",
        "service": "agent-service",
        "version": "1.0.0",
        "provider": settings.llm_provider,
        "model": model_label,
        "llm_configured": configured,
        "content_safety_active": settings.content_safety_enabled,
        "tools_count": len(ALL_TOOLS),
        "mcp_endpoint": "/mcp/sse",
    }
