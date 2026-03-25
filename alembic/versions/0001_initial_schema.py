"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "codes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("code_type", sa.String(20), nullable=False),
        sa.Column("short_code", sa.String(12), unique=True, nullable=False, index=True),
        sa.Column("target_url", sa.String(2048), nullable=False),
        sa.Column("barcode_value", sa.String(255), nullable=True),
        sa.Column("generation_config", JSONB, server_default="{}"),
        sa.Column("status", sa.String(20), server_default="active", index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column("scan_count_total", sa.Integer, server_default="0"),
        sa.Column("scan_count_last_7d", sa.Integer, server_default="0"),
        sa.Column("scan_count_last_30d", sa.Integer, server_default="0"),
        sa.Column("last_scanned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("tags", ARRAY(sa.String), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "scan_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("code_id", UUID(as_uuid=True), sa.ForeignKey("codes.id"), nullable=True, index=True),
        sa.Column("short_code", sa.String(12), nullable=False, index=True),
        sa.Column("ip_hash", sa.String(64), nullable=True),
        sa.Column("country_code", sa.String(2), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("device_type", sa.String(20), nullable=True),
        sa.Column("os_family", sa.String(50), nullable=True),
        sa.Column("browser_family", sa.String(50), nullable=True),
        sa.Column("referer", sa.String(500), nullable=True),
        sa.Column("utm_source", sa.String(100), nullable=True),
        sa.Column("utm_medium", sa.String(100), nullable=True),
        sa.Column("utm_campaign", sa.String(100), nullable=True),
        sa.Column("scanned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )


def downgrade() -> None:
    op.drop_table("scan_events")
    op.drop_table("codes")
