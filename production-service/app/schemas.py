from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


VALID_STATUSES = {"pending", "in_progress", "completed", "cancelled"}


class ProductionOrderCreate(BaseModel):
    product_name: str = Field(..., example="Boîte américaine 300x200x150mm")
    quantity_planned: int = Field(..., gt=0, example=1000)
    machine_id: Optional[int] = Field(None, example=1)
    notes: Optional[str] = Field(None, example="Commande urgente client Dupont")


class ProductionOrderUpdate(BaseModel):
    product_name: Optional[str] = None
    quantity_planned: Optional[int] = Field(None, gt=0)
    machine_id: Optional[int] = None
    notes: Optional[str] = None


class ProductionProgressUpdate(BaseModel):
    quantity_produced: int = Field(..., ge=0, example=250)


class ProductionOrderResponse(BaseModel):
    id: int
    reference: str
    product_name: str
    quantity_planned: int
    quantity_produced: int
    status: str
    machine_id: Optional[int]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}
