from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .routes.stock import router as stock_router

# Création des tables au démarrage
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="📦 Stock Service",
    description=(
        "Service de gestion du stock de l'usine de cartons.\n\n"
        "Permet de gérer les matières premières (plaques de carton, rouleaux, colles) "
        "et les produits finis (boîtes fabriquées). "
        "Chaque article peut être incrémenté ou décrémenté avec traçabilité."
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

app.include_router(stock_router)


@app.get("/health", tags=["Health"], summary="État du service")
def health_check():
    return {"status": "ok", "service": "stock-service", "version": "1.0.0"}
