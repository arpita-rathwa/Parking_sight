import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from shared.models.database import Base


class Violation(Base):
    __tablename__ = "violations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    coordinates = Column(Geometry("POINT", srid=4326), nullable=False)
    confidence_score = Column(Float, nullable=False)
    vehicle_type = Column(String(50), nullable=True)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    violation_type = Column(String(100), nullable=True)
    image_url = Column(String(500), nullable=True)
