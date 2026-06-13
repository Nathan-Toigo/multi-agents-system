from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from .database import Base


class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    model = Column(String, nullable=True)
    serial_number = Column(String, unique=True, nullable=True)
    # Type de machine : découpeuse, plieuse, imprimeuse, colleuse…
    machine_type = Column(String, nullable=False)
    # running | stopped | maintenance
    status = Column(String, default="stopped")
    # Capacité en boîtes/heure
    capacity_per_hour = Column(Integer, nullable=True)
    # Zone ou ligne de production
    location = Column(String, nullable=True)
    last_maintenance_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
