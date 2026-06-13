import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from ..database import get_db
from ..models import Order
from ..schemas import OrderCreate, OrderUpdate, OrderStatusUpdate, OrderResponse

router = APIRouter(prefix="/orders", tags=["Commandes"])

VALID_STATUSES = {"pending", "confirmed", "in_production", "delivered", "cancelled"}


def _generate_reference() -> str:
    year = datetime.now(timezone.utc).year
    short_id = str(uuid.uuid4())[:6].upper()
    return f"CMD-{year}-{short_id}"


@router.get("/", response_model=List[OrderResponse], summary="Lister les commandes")
def list_orders(
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    customer: Optional[str] = Query(None, description="Filtrer par nom de client"),
    db: Session = Depends(get_db),
):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    if customer:
        query = query.filter(Order.customer_name.ilike(f"%{customer}%"))
    return query.all()


@router.get("/{order_id}", response_model=OrderResponse, summary="Détail d'une commande")
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Commande #{order_id} introuvable")
    return order


@router.post("/", response_model=OrderResponse, status_code=201, summary="Créer une commande")
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    order = Order(
        reference=_generate_reference(),
        **payload.model_dump(),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.put("/{order_id}/status", response_model=OrderResponse, summary="Mettre à jour le statut")
def update_order_status(order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db)):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Statut invalide. Valeurs acceptées : {sorted(VALID_STATUSES)}",
        )
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Commande #{order_id} introuvable")
    if order.status == "delivered":
        raise HTTPException(status_code=409, detail="Une commande livrée ne peut pas être modifiée")
    order.status = payload.status
    order.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}", response_model=OrderResponse, summary="Modifier une commande")
def update_order(order_id: int, payload: OrderUpdate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Commande #{order_id} introuvable")
    if order.status in ("delivered", "cancelled"):
        raise HTTPException(status_code=409, detail=f"Impossible de modifier une commande '{order.status}'")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(order, field, value)
    order.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=204, summary="Supprimer une commande")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Commande #{order_id} introuvable")
    if order.status in ("in_production", "delivered"):
        raise HTTPException(
            status_code=409,
            detail=f"Impossible de supprimer une commande en statut '{order.status}'",
        )
    db.delete(order)
    db.commit()
