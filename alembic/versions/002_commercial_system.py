"""Commercial advertising orders, payments and advertisement workflow tables

Revision ID: 002_commercial_system
Revises: 001_initial
Create Date: 2026-10-17 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_commercial_system'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add extra columns to advertisements table
    with op.batch_alter_table('advertisements') as batch_op:
        batch_op.add_column(sa.Column('chat_id', sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column('username', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('first_name', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('media_type', sa.String(length=50), server_default='TEXT', nullable=False))
        batch_op.add_column(sa.Column('media_file_id', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('media_file_unique_id', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('original_text', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('original_caption', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('ocr_text', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('combined_text', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('detected_keywords', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('risk_score', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('status', sa.String(length=50), server_default='DELETED', nullable=False))
        batch_op.add_column(sa.Column('published_message_id', sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column('published_chat_id', sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column('published_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
        batch_op.create_index(op.f('ix_advertisements_telegram_message_id'), ['telegram_message_id'], unique=False)
        batch_op.create_index(op.f('ix_advertisements_chat_id'), ['chat_id'], unique=False)
        batch_op.create_index(op.f('ix_advertisements_status'), ['status'], unique=False)

    # 2. Create orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_number', sa.String(length=64), nullable=False),
        sa.Column('advertisement_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=True),
        sa.Column('price', sa.Integer(), nullable=True),
        sa.Column('currency', sa.String(length=10), server_default='UZS', nullable=False),
        sa.Column('card_number', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='CREATED', nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['advertisement_id'], ['advertisements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_order_number'), 'orders', ['order_number'], unique=True)
    op.create_index(op.f('ix_orders_advertisement_id'), 'orders', ['advertisement_id'], unique=False)
    op.create_index(op.f('ix_orders_user_id'), 'orders', ['user_id'], unique=False)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)
    op.create_index(op.f('ix_orders_created_at'), 'orders', ['created_at'], unique=False)

    # 3. Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('advertisement_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=True),
        sa.Column('currency', sa.String(length=10), server_default='UZS', nullable=False),
        sa.Column('receipt_file_id', sa.String(length=255), nullable=False),
        sa.Column('receipt_file_unique_id', sa.String(length=255), nullable=False),
        sa.Column('receipt_hash', sa.String(length=128), nullable=True),
        sa.Column('receipt_type', sa.String(length=50), server_default='PHOTO', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('reviewed_by', sa.BigInteger(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['advertisement_id'], ['advertisements.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_order_id'), 'payments', ['order_id'], unique=False)
    op.create_index(op.f('ix_payments_advertisement_id'), 'payments', ['advertisement_id'], unique=False)
    op.create_index(op.f('ix_payments_user_id'), 'payments', ['user_id'], unique=False)
    op.create_index(op.f('ix_payments_receipt_file_unique_id'), 'payments', ['receipt_file_unique_id'], unique=False)
    op.create_index(op.f('ix_payments_receipt_hash'), 'payments', ['receipt_hash'], unique=False)
    op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)
    op.create_index(op.f('ix_payments_created_at'), 'payments', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('payments')
    op.drop_table('orders')
    with op.batch_alter_table('advertisements') as batch_op:
        batch_op.drop_index(op.f('ix_advertisements_status'))
        batch_op.drop_index(op.f('ix_advertisements_chat_id'))
        batch_op.drop_index(op.f('ix_advertisements_telegram_message_id'))
        batch_op.drop_column('updated_at')
        batch_op.drop_column('published_at')
        batch_op.drop_column('published_chat_id')
        batch_op.drop_column('published_message_id')
        batch_op.drop_column('status')
        batch_op.drop_column('risk_score')
        batch_op.drop_column('detected_keywords')
        batch_op.drop_column('combined_text')
        batch_op.drop_column('ocr_text')
        batch_op.drop_column('original_caption')
        batch_op.drop_column('original_text')
        batch_op.drop_column('media_file_unique_id')
        batch_op.drop_column('media_file_id')
        batch_op.drop_column('media_type')
        batch_op.drop_column('first_name')
        batch_op.drop_column('username')
        batch_op.drop_column('chat_id')
