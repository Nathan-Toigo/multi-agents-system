from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from .database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    # Référence unique : ex. CMD-2024-001
    reference = Column(String, unique=True, index=True, nullable=False)
    customer_name = Column(String, nullable=False)
    customer_contact = Column(String, nullable=True)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    # pending | confirmed | in_production | delivered | cancelled
    status = Column(String, default="pending")
    delivery_date = Column(DateTime, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
