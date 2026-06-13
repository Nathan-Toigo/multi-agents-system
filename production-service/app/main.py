from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .routes.production import router as production_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="🏭 Production Service",
    description=(
        "Service de gestion des ordres de fabrication de l'usine de cartons.\n\n"
        "Gère le cycle de vie complet d'un ordre de production : "
        "création → démarrage → suivi de progression → clôture.\n\n"
        "**Statuts** : `pending` → `in_progress` → `completed` | `cancelled`"
    ),
    version="1.0.0",
    contact={"name": "Usine de Cartons"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(production_router)


@app.get("/health", tags=["Health"], summary="État du service")
def health_check():
    return {"status": "ok", "service": "production-service", "version": "1.0.0"}
