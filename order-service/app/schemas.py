from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OrderCreate(BaseModel):
    customer_name: str = Field(..., example="Entreprise Dupont SA")
    customer_contact: Optional[str] = Field(None, example="contact@dupont.fr")
    product_name: str = Field(..., example="Boîte américaine 300x200x150mm")
    quantity: int = Field(..., gt=0, example=5000)
    delivery_date: Optional[datetime] = Field(None, example="2024-12-31T00:00:00")
    notes: Optional[str] = Field(None, example="Livraison en palette filmée")


class OrderStatusUpdate(BaseModel):
    status: str = Field(..., example="confirmed")


class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_contact: Optional[str] = None
    product_name: Optional[str] = None
    quantity: Optional[int] = Field(None, gt=0)
    delivery_date: Optional[datetime] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    reference: str
    customer_name: str
    customer_contact: Optional[str]
    product_name: str
    quantity: int
    status: str
    delivery_date: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
