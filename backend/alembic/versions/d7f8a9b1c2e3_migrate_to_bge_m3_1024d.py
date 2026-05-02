"""Migrate embedding dimension from 384 (MiniLM) to 1024 (BGE-M3)

Revision ID: d7f8a9b1c2e3
Revises: fa3575ec42d2
Create Date: 2026-05-03 02:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7f8a9b1c2e3'
down_revision: Union[str, None] = 'fa3575ec42d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old embedding column (384-dim from all-MiniLM-L6-v2)
    op.drop_column('document_chunks', 'embedding')
    # Re-create with 1024-dim for BGE-M3
    op.execute('ALTER TABLE document_chunks ADD COLUMN embedding vector(1024)')


def downgrade() -> None:
    # Revert to 384-dim for all-MiniLM-L6-v2
    op.drop_column('document_chunks', 'embedding')
    op.execute('ALTER TABLE document_chunks ADD COLUMN embedding vector(384)')
