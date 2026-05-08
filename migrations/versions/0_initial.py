"""initial

Revision ID: 0
Revises:
Create Date: 2026-05-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "channel_subscriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("handle", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "handle"),
    )
    op.create_index("ix_channel_subscriptions_user_id", "channel_subscriptions", ["user_id"])

    op.create_table(
        "user_repos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("repo", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "repo"),
    )
    op.create_index("ix_user_repos_user_id", "user_repos", ["user_id"])

    op.create_table(
        "user_interests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("interest", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "interest"),
    )
    op.create_index("ix_user_interests_user_id", "user_interests", ["user_id"])

    op.create_table(
        "seen_releases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("release_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "release_id"),
    )
    op.create_index("ix_seen_releases_user_id", "seen_releases", ["user_id"])

    op.create_table(
        "seen_videos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("video_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "video_id"),
    )
    op.create_index("ix_seen_videos_user_id", "seen_videos", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_seen_videos_user_id", table_name="seen_videos")
    op.drop_table("seen_videos")

    op.drop_index("ix_seen_releases_user_id", table_name="seen_releases")
    op.drop_table("seen_releases")

    op.drop_index("ix_user_interests_user_id", table_name="user_interests")
    op.drop_table("user_interests")

    op.drop_index("ix_user_repos_user_id", table_name="user_repos")
    op.drop_table("user_repos")

    op.drop_index("ix_channel_subscriptions_user_id", table_name="channel_subscriptions")
    op.drop_table("channel_subscriptions")
