"""
Agent LangGraph ReAct — supporte Azure OpenAI (AI Foundry) et OpenAI direct.
Le fournisseur est sélectionné via la variable d'environnement LLM_PROVIDER.
"""
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent

from .config import settings
from .tools import ALL_TOOLS

# ─── Prompt système ───────────────────────────────────────────────────────
SYSTEM_PROMPT = """Tu es un assistant intelligent de l'Usine de Cartons.
Tu peux consulter et gérer en temps réel les données de l'usine grâce à tes outils.

Tes domaines de compétence :
📦 STOCK — Matières premières, produits finis, consommables
🏭 PRODUCTION — Ordres de fabrication (pending → in_progress → completed)
📋 COMMANDES — Commandes clients (pending → confirmed → in_production → delivered)
⚙️ MACHINES — Machines de l'usine (running / stopped / maintenance)

Règles :
- Utilise TOUJOURS les outils pour répondre avec des données réelles et à jour
- Réponds en français, de façon claire et structurée
- Pour les actions (créer, modifier), confirme ce qui a été fait
- Si tu as besoin d'un ID, utilise d'abord l'outil de liste pour le trouver
- En cas d'erreur d'un outil, explique le problème et propose une alternative"""


# ─── Création du LLM (Azure ou OpenAI) ───────────────────────────────────
def _create_llm():
    provider = settings.llm_provider.lower()

    if provider == "azure":
        # ── Azure OpenAI / Azure AI Foundry ──────────────────────────
        if not settings.azure_openai_endpoint or not settings.azure_openai_key:
            raise ValueError(
                "LLM_PROVIDER=azure requiert AZURE_OPENAI_ENDPOINT et AZURE_OPENAI_API_KEY.\n"
                "Récupérez ces valeurs dans Azure AI Foundry → votre projet → 'API keys'."
            )
        from langchain_openai import AzureChatOpenAI

        return AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            azure_deployment=settings.azure_openai_deployment,
            api_key=settings.azure_openai_key,
            openai_api_version=settings.azure_openai_api_version,
            temperature=0,
        )

    elif provider == "openai":
        # ── OpenAI direct (fallback) ──────────────────────────────────
        if not settings.openai_api_key:
            raise ValueError(
                "LLM_PROVIDER=openai requiert OPENAI_API_KEY.\n"
                "Obtenez une clé sur platform.openai.com/api-keys"
            )
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
        )

    else:
        raise ValueError(
            f"LLM_PROVIDER='{provider}' non reconnu. Valeurs acceptées : 'azure', 'openai'."
        )


# ─── Initialisation de l'agent ────────────────────────────────────────────
def create_agent():
    llm = _create_llm()
    return create_react_agent(llm, ALL_TOOLS, state_modifier=SYSTEM_PROMPT)


_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


# ─── Exécution d'une requête ──────────────────────────────────────────────
async def run_agent(user_message: str, history: list[dict] | None = None) -> dict:
    """
    Exécute l'agent ReAct avec le message utilisateur.

    Returns:
        {
            "response": str,
            "steps": list[dict],
            "model": str,
            "provider": str,
            "tools_used": list[str],
        }
    """
    agent = get_agent()

    messages = []
    for msg in (history or []):
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg.get("role") == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_message))

    result = await agent.ainvoke({"messages": messages})

    # Extraction des étapes (tool calls + résultats)
    steps = []
    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                steps.append({"type": "tool_call", "tool": tc["name"], "input": tc["args"]})
        elif hasattr(msg, "name") and msg.name:
            if steps and steps[-1]["type"] == "tool_call":
                steps[-1]["output"] = msg.content

    # Réponse finale = dernier AIMessage avec contenu
    final_response = ""
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            final_response = msg.content
            break

    # Libellé du modèle utilisé
    if settings.llm_provider == "azure":
        model_label = f"Azure/{settings.azure_openai_deployment}"
    else:
        model_label = settings.openai_model

    return {
        "response": final_response,
        "steps": steps,
        "model": model_label,
        "provider": settings.llm_provider,
        "tools_used": list({s["tool"] for s in steps if "tool" in s}),
    }
