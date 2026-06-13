from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .routes.order import router as order_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="📋 Order Service",
    description=(
        "Service de gestion des commandes clients de l'usine de cartons.\n\n"
        "Permet de créer et suivre les commandes de boîtes en carton passées par les clients.\n\n"
        "**Statuts** : `pending` → `confirmed` → `in_production` → `delivered` | `cancelled`"
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

app.include_router(order_router)


@app.get("/health", tags=["Health"], summary="État du service")
def health_check():
    return {"status": "ok", "service": "order-service", "version": "1.0.0"}
