"""OLX.uz integration columns for advertising_requests

Revision ID: 004_olx_integration
Revises: 003_dynamic_forms
Create Date: 2026-10-24 21:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004_olx_integration'
down_revision: Union[str, None] = '003_dynamic_forms'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'advertising_requests',
        sa.Column('olx_status', sa.String(length=50), server_default='NONE', nullable=False)
    )
    op.add_column(
        'advertising_requests',
        sa.Column('olx_ad_id', sa.String(length=100), nullable=True)
    )
    op.add_column(
        'advertising_requests',
        sa.Column('olx_ad_url', sa.String(length=500), nullable=True)
    )
    op.add_column(
        'advertising_requests',
        sa.Column('olx_published_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        'advertising_requests',
        sa.Column('olx_error', sa.Text(), nullable=True)
    )
    op.create_index('ix_advertising_requests_olx_status', 'advertising_requests', ['olx_status'])


def downgrade() -> None:
    op.drop_index('ix_advertising_requests_olx_status', table_name='advertising_requests')
    op.drop_column('advertising_requests', 'olx_error')
    op.drop_column('advertising_requests', 'olx_published_at')
    op.drop_column('advertising_requests', 'olx_ad_url')
    op.drop_column('advertising_requests', 'olx_ad_id')
    op.drop_column('advertising_requests', 'olx_status')
