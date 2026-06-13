import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from ..database import get_db
from ..models import ProductionOrder
from ..schemas import (
    ProductionOrderCreate,
    ProductionOrderUpdate,
    ProductionOrderResponse,
    ProductionProgressUpdate,
)

router = APIRouter(prefix="/productions", tags=["Ordres de Production"])


def _generate_reference() -> str:
    year = datetime.now(timezone.utc).year
    short_id = str(uuid.uuid4())[:6].upper()
    return f"PROD-{year}-{short_id}"


@router.get("/", response_model=List[ProductionOrderResponse], summary="Lister les ordres de production")
def list_productions(
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    db: Session = Depends(get_db),
):
    query = db.query(ProductionOrder)
    if status:
        query = query.filter(ProductionOrder.status == status)
    return query.all()


@router.get("/{production_id}", response_model=ProductionOrderResponse, summary="Détail d'un ordre")
def get_production(production_id: int, db: Session = Depends(get_db)):
    order = db.query(ProductionOrder).filter(ProductionOrder.id == production_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Ordre #{production_id} introuvable")
    return order


@router.post("/", response_model=ProductionOrderResponse, status_code=201, summary="Créer un ordre de production")
def create_production(payload: ProductionOrderCreate, db: Session = Depends(get_db)):
    order = ProductionOrder(
        reference=_generate_reference(),
        **payload.model_dump(),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.put("/{production_id}/start", response_model=ProductionOrderResponse, summary="Démarrer la production")
def start_production(production_id: int, db: Session = Depends(get_db)):
    order = db.query(ProductionOrder).filter(ProductionOrder.id == production_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Ordre #{production_id} introuvable")
    if order.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Impossible de démarrer : statut actuel = '{order.status}'",
        )
    order.status = "in_progress"
    order.started_at = datetime.now(timezone.utc)
    order.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    return order


@router.put("/{production_id}/complete", response_model=ProductionOrderResponse, summary="Terminer la production")
def complete_production(production_id: int, db: Session = Depends(get_db)):
    order = db.query(ProductionOrder).filter(ProductionOrder.id == production_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Ordre #{production_id} introuvable")
    if order.status != "in_progress":
        raise HTTPException(
            status_code=409,
            detail=f"Impossible de terminer : statut actuel = '{order.status}'",
        )
    order.status = "completed"
    order.quantity_produced = order.quantity_planned
    order.completed_at = datetime.now(timezone.utc)
    order.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    return order


@router.put("/{production_id}/cancel", response_model=ProductionOrderResponse, summary="Annuler un ordre")
def cancel_production(production_id: int, db: Session = Depends(get_db)):
    order = db.query(ProductionOrder).filter(ProductionOrder.id == production_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Ordre #{production_id} introuvable")
    if order.status in ("completed", "cancelled"):
        raise HTTPException(
            status_code=409,
            detail=f"Impossible d'annuler : statut actuel = '{order.status}'",
        )
    order.status = "cancelled"
    order.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    return order


@router.put("/{production_id}/progress", response_model=ProductionOrderResponse, summary="Mettre à jour la quantité produite")
def update_progress(production_id: int, payload: ProductionProgressUpdate, db: Session = Depends(get_db)):
    order = db.query(ProductionOrder).filter(ProductionOrder.id == production_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Ordre #{production_id} introuvable")
    if order.status != "in_progress":
        raise HTTPException(status_code=409, detail="L'ordre doit être 'in_progress' pour mettre à jour la progression")
    if payload.quantity_produced > order.quantity_planned:
        raise HTTPException(status_code=400, detail="La quantité produite dépasse la quantité planifiée")
    order.quantity_produced = payload.quantity_produced
    order.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{production_id}", response_model=ProductionOrderResponse, summary="Modifier un ordre (pending uniquement)")
def update_production(production_id: int, payload: ProductionOrderUpdate, db: Session = Depends(get_db)):
    order = db.query(ProductionOrder).filter(ProductionOrder.id == production_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Ordre #{production_id} introuvable")
    if order.status != "pending":
        raise HTTPException(status_code=409, detail="Seuls les ordres 'pending' peuvent être modifiés")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(order, field, value)
    order.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    return order


@router.delete("/{production_id}", status_code=204, summary="Supprimer un ordre")
def delete_production(production_id: int, db: Session = Depends(get_db)):
    order = db.query(ProductionOrder).filter(ProductionOrder.id == production_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Ordre #{production_id} introuvable")
    db.delete(order)
    db.commit()
