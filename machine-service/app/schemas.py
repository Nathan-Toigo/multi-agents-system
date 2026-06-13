from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MachineCreate(BaseModel):
    name: str = Field(..., example="Découpeuse Laser L1")
    model: Optional[str] = Field(None, example="BOBST SPO 1600")
    serial_number: Optional[str] = Field(None, example="SN-2024-0042")
    machine_type: str = Field(..., example="découpeuse")
    capacity_per_hour: Optional[int] = Field(None, gt=0, example=800)
    location: Optional[str] = Field(None, example="Ligne A - Zone 2")


class MachineStatusUpdate(BaseModel):
    status: str = Field(..., example="running")


class MachineUpdate(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    machine_type: Optional[str] = None
    capacity_per_hour: Optional[int] = Field(None, gt=0)
    location: Optional[str] = None


class MachineResponse(BaseModel):
    id: int
    name: str
    model: Optional[str]
    serial_number: Optional[str]
    machine_type: str
    status: str
    capacity_per_hour: Optional[int]
    location: Optional[str]
    last_maintenance_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
