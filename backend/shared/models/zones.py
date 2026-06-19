import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from shared.models.database import Base


class Zone(Base):
    __tablename__ = "zones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    boundary = Column(Geometry("POLYGON", srid=4326), nullable=False)
    priority_score = Column(Float, default=0.0)
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)
    city = Column(String(100), default="Bengaluru")
    police_station = Column(String(255), nullable=True)
