"""seen_videos.created_at column

Revision ID: 4
Revises: 3
Create Date: 2026-05-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "4"
down_revision: Union[str, Sequence[str], None] = "3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "seen_videos",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_seen_videos_created_at", "seen_videos", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_seen_videos_created_at", table_name="seen_videos")
    op.drop_column("seen_videos", "created_at")
