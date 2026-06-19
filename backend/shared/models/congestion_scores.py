import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from shared.models.database import Base


class CongestionScore(Base):
    __tablename__ = "congestion_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    speed_drop_percent = Column(Float, default=0.0)
    violation_count = Column(Integer, default=0)
    impact_score = Column(Float, default=0.0)
    traffic_density = Column(Float, default=0.0)
    weather_factor = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
