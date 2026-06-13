from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone
from .database import Base


class StockItem(Base):
    __tablename__ = "stock_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    # Unité : unités, kg, m2, rouleaux…
    unit = Column(String, default="unités")
    quantity = Column(Float, default=0.0)
    # Seuil d'alerte en dessous duquel le stock est critique
    min_threshold = Column(Float, default=0.0)
    # raw_material | finished_product | consumable
    category = Column(String, default="raw_material")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
