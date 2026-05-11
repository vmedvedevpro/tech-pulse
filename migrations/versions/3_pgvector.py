"""pgvector extension and summary_embedding column

Revision ID: 3
Revises: 2
Create Date: 2026-05-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "3"
down_revision: Union[str, Sequence[str], None] = "2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "videos",
        sa.Column("summary_embedding", Vector(1024), nullable=True),
    )
    op.execute(
        "CREATE INDEX videos_summary_embedding_hnsw_idx "
        "ON videos USING hnsw (summary_embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_index("videos_summary_embedding_hnsw_idx", table_name="videos")
    op.drop_column("videos", "summary_embedding")
