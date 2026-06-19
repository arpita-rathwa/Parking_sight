"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-19
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects.postgresql import UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="officer"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("device_token", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "zones",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("boundary", geoalchemy2.Geometry("POLYGON", srid=4326), nullable=False),
        sa.Column("priority_score", sa.Float(), server_default="0.0"),
        sa.Column("last_updated", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("city", sa.String(100), server_default="Bengaluru"),
        sa.Column("police_station", sa.String(255), nullable=True),
    )

    op.create_table(
        "cameras",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("location", geoalchemy2.Geometry("POINT", srid=4326), nullable=False),
        sa.Column("zone_id", UUID(as_uuid=True), sa.ForeignKey("zones.id"), nullable=False),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("rtsp_url", sa.String(500), nullable=True),
    )

    op.create_table(
        "violations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("camera_id", UUID(as_uuid=True), sa.ForeignKey("cameras.id"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("coordinates", geoalchemy2.Geometry("POINT", srid=4326), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("vehicle_type", sa.String(50), nullable=True),
        sa.Column("violation_type", sa.String(100), nullable=True),
        sa.Column("resolved", sa.Boolean(), server_default="false"),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "congestion_scores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("zone_id", UUID(as_uuid=True), sa.ForeignKey("zones.id"), nullable=False, index=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("speed_drop_percent", sa.Float(), server_default="0.0"),
        sa.Column("violation_count", sa.Integer(), server_default="0"),
        sa.Column("impact_score", sa.Float(), server_default="0.0"),
        sa.Column("traffic_density", sa.Float(), server_default="0.0"),
        sa.Column("weather_factor", sa.Float(), server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "enforcement_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("officer_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("zone_id", UUID(as_uuid=True), sa.ForeignKey("zones.id"), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("arrived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.String(50), server_default="pending"),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("enforcement_log")
    op.drop_table("congestion_scores")
    op.drop_table("violations")
    op.drop_table("cameras")
    op.drop_table("zones")
    op.drop_table("users")
