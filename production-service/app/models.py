from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from .database import Base


class ProductionOrder(Base):
    __tablename__ = "production_orders"

    id = Column(Integer, primary_key=True, index=True)
    # Référence unique : ex. PROD-2024-001
    reference = Column(String, unique=True, index=True, nullable=False)
    product_name = Column(String, nullable=False)
    quantity_planned = Column(Integer, nullable=False)
    quantity_produced = Column(Integer, default=0)
    # pending | in_progress | completed | cancelled
    status = Column(String, default="pending")
    # ID de la machine utilisée (référence vers machine-service)
    machine_id = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
