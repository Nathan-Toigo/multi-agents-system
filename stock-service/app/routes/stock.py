from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from ..database import get_db
from ..models import StockItem
from ..schemas import (
    StockItemCreate,
    StockItemUpdate,
    StockItemResponse,
    StockQuantityChange,
    StockAlertResponse,
)

router = APIRouter(prefix="/stocks", tags=["Stocks"])


@router.get("/", response_model=List[StockItemResponse], summary="Lister tout le stock")
def list_stocks(
    category: Optional[str] = Query(None, description="Filtrer par catégorie"),
    db: Session = Depends(get_db),
):
    query = db.query(StockItem)
    if category:
        query = query.filter(StockItem.category == category)
    return query.all()


@router.get("/alerts", response_model=List[StockAlertResponse], summary="Articles sous le seuil critique")
def get_low_stock_alerts(db: Session = Depends(get_db)):
    """Retourne tous les articles dont la quantité est inférieure au seuil minimum."""
    items = db.query(StockItem).filter(StockItem.quantity <= StockItem.min_threshold).all()
    return items


@router.get("/{item_id}", response_model=StockItemResponse, summary="Détail d'un article")
def get_stock_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(StockItem).filter(StockItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Article #{item_id} introuvable")
    return item


@router.post("/", response_model=StockItemResponse, status_code=201, summary="Créer un article en stock")
def create_stock_item(payload: StockItemCreate, db: Session = Depends(get_db)):
    item = StockItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}/add", response_model=StockItemResponse, summary="Incrémenter le stock")
def add_to_stock(item_id: int, payload: StockQuantityChange, db: Session = Depends(get_db)):
    """Ajoute une quantité au stock (réception marchandise, retour, etc.)."""
    item = db.query(StockItem).filter(StockItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Article #{item_id} introuvable")
    item.quantity += payload.quantity
    item.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}/remove", response_model=StockItemResponse, summary="Décrémenter le stock")
def remove_from_stock(item_id: int, payload: StockQuantityChange, db: Session = Depends(get_db)):
    """Retire une quantité du stock (consommation production, expédition, etc.)."""
    item = db.query(StockItem).filter(StockItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Article #{item_id} introuvable")
    if item.quantity < payload.quantity:
        raise HTTPException(
            status_code=409,
            detail=f"Stock insuffisant. Disponible : {item.quantity} {item.unit}, demandé : {payload.quantity}",
        )
    item.quantity -= payload.quantity
    item.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=StockItemResponse, summary="Mettre à jour un article")
def update_stock_item(item_id: int, payload: StockItemUpdate, db: Session = Depends(get_db)):
    item = db.query(StockItem).filter(StockItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Article #{item_id} introuvable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    item.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204, summary="Supprimer un article")
def delete_stock_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(StockItem).filter(StockItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Article #{item_id} introuvable")
    db.delete(item)
    db.commit()
