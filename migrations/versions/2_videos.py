"""videos table

Revision ID: 2
Revises: 1
Create Date: 2026-05-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "2"
down_revision: Union[str, Sequence[str], None] = "1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "videos",
        sa.Column("video_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("channel_id", sa.String(), nullable=True),
        sa.Column("channel_title", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("transcript_language", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("video_id"),
    )

    op.execute(
        """
        INSERT INTO videos (video_id)
        SELECT DISTINCT video_id
        FROM seen_videos ON CONFLICT (video_id) DO NOTHING
        """
    )

    op.create_foreign_key(
        "fk_seen_videos_video_id_videos",
        "seen_videos",
        "videos",
        ["video_id"],
        ["video_id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_seen_videos_video_id_videos", "seen_videos", type_="foreignkey")
    op.drop_table("videos")
