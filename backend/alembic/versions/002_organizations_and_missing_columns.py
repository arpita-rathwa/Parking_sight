"""add organizations table, organization_id to users, roi_polygon to cameras

Revision ID: 002
Revises: 001
Create Date: 2026-06-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "organization_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=True,
        ),
    )

    op.add_column(
        "cameras",
        sa.Column("roi_polygon", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cameras", "roi_polygon")
    op.drop_column("users", "organization_id")
    op.drop_table("organizations")
