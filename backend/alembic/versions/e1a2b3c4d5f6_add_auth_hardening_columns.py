"""Add auth hardening columns to users table

Revision ID: e1a2b3c4d5f6
Revises: d7f8a9b1c2e3
Create Date: 2026-05-03 05:45:00.000000+05:30

Phase 18: Auth Hardening
Adds: is_verified, failed_login_attempts, locked_until, password_changed_at
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1a2b3c4d5f6'
down_revision = 'd7f8a9b1c2e3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'password_changed_at')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'is_verified')
