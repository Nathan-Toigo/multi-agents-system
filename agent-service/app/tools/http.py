"""
Client HTTP partagé pour appeler les microservices de l'usine.
"""
import json
import httpx


async def http_get(url: str, params: dict | None = None) -> list | dict:
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        resp = await client.get(url, params=params or {})
        resp.raise_for_status()
        return resp.json()


async def http_post(url: str, body: dict) -> dict:
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        resp = await client.post(url, json=body)
        resp.raise_for_status()
        return resp.json()


async def http_put(url: str, body: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        resp = await client.put(url, json=body or {})
        resp.raise_for_status()
        return resp.json()


async def http_delete(url: str) -> None:
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        resp = await client.delete(url)
        resp.raise_for_status()


def to_text(data) -> str:
    """Convertit un objet Python en texte JSON lisible."""
    if isinstance(data, (list, dict)):
        return json.dumps(data, ensure_ascii=False, indent=2)
    return str(data)
