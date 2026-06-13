from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .routes.machine import router as machine_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="⚙️ Machine Service",
    description=(
        "Service de gestion des machines de l'usine de cartons.\n\n"
        "Gère l'inventaire des machines, leur état opérationnel et la traçabilité des maintenances.\n\n"
        "**Statuts** : `stopped` | `running` | `maintenance`\n\n"
        "**Types de machines** : découpeuse, plieuse, imprimeuse, colleuse, cerclage…"
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

app.include_router(machine_router)


@app.get("/health", tags=["Health"], summary="État du service")
def health_check():
    return {"status": "ok", "service": "machine-service", "version": "1.0.0"}
