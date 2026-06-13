from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class StockItemCreate(BaseModel):
    name: str = Field(..., example="Plaque carton ondulé B-flute")
    description: Optional[str] = Field(None, example="Format 1200x800mm, épaisseur 3mm")
    unit: str = Field("unités", example="unités")
    quantity: float = Field(0.0, ge=0, example=500.0)
    min_threshold: float = Field(0.0, ge=0, example=50.0)
    category: str = Field("raw_material", example="raw_material")


class StockItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    min_threshold: Optional[float] = Field(None, ge=0)
    category: Optional[str] = None


class StockQuantityChange(BaseModel):
    quantity: float = Field(..., gt=0, example=100.0)
    reason: Optional[str] = Field(None, example="Réception fournisseur")


class StockItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    unit: str
    quantity: float
    min_threshold: float
    category: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StockAlertResponse(BaseModel):
    id: int
    name: str
    quantity: float
    min_threshold: float
    unit: str
