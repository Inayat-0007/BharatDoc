"""add pgvector and embedding column

Revision ID: b9e2a1f73c01
Revises: fa3575ec42d2
Create Date: 2026-05-02 07:16:00.000000

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b9e2a1f73c01'
down_revision: Union[str, None] = 'fa3575ec42d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    # Add embedding column (vector type from pgvector)
    op.execute('ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding vector(384)')


def downgrade() -> None:
    op.execute('ALTER TABLE document_chunks DROP COLUMN IF EXISTS embedding')
    op.execute('DROP EXTENSION IF EXISTS vector')
