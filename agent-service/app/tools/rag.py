"""
Outil LangChain pour la recherche dans la documentation technique de l'usine.
Connecté au rag-service via HTTP.
"""
from langchain_core.tools import tool
from ..config import settings
from .http import http_post, to_text


@tool
async def search_documentation(query: str) -> str:
    """
    Recherche dans la documentation technique de l'usine de cartons.
    À utiliser pour répondre aux questions sur :
    - Les procédures de maintenance des machines (Découpeuse L1, Lamineuse CL2, Plieuse PC3)
    - Les processus de production (boîte américaine, boîte agrafée, caisse télescopique)
    - Les normes qualité ISO et les critères de contrôle
    - Les paramètres techniques (grammages, tolérances, températures…)
    - Les temps de cycle et les taux de rebut acceptables
    Paramètre : query (str) — la question ou les mots-clés à rechercher.
    """
    try:
        data = await http_post(
            f"{settings.rag_url}/search",
            {"query": query, "k": 3},
        )
        results = data.get("results", [])
        if not results:
            return f"Aucune documentation trouvée pour : '{query}'"

        lines = [f"📚 Documentation pour '{query}' :\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"[{i}] Source : {r.get('source', '?')} (score: {r.get('score', 0):.2f})")
            lines.append(r.get("content", ""))
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        return f"Service RAG inaccessible ({settings.rag_url}) : {e}"
