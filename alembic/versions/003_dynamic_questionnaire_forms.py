"""Dynamic questionnaire product forms, requests, answers and media tables

Revision ID: 003_dynamic_forms
Revises: 002_commercial_system
Create Date: 2026-10-17 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_dynamic_forms'
down_revision: Union[str, None] = '002_commercial_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create advertisement_categories table
    op.create_table(
        'advertisement_categories',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('icon', sa.String(length=64), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 2. Create category_fields table
    op.create_table(
        'category_fields',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('category_id', sa.String(length=64), sa.ForeignKey('advertisement_categories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subcategory_id', sa.String(length=64), nullable=True),
        sa.Column('field_name', sa.String(length=64), nullable=False),
        sa.Column('field_label', sa.String(length=255), nullable=False),
        sa.Column('field_type', sa.String(length=50), nullable=False),
        sa.Column('is_required', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('help_text', sa.Text(), nullable=True),
        sa.Column('include_in_ad', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_public', sa.Boolean(), server_default='true', nullable=False),
    )
    op.create_index('ix_category_fields_category_id', 'category_fields', ['category_id'])
    op.create_index('ix_category_fields_subcategory_id', 'category_fields', ['subcategory_id'])
    op.create_index('ix_category_fields_field_name', 'category_fields', ['field_name'])

    # 3. Create category_field_options table
    op.create_table(
        'category_field_options',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('field_id', sa.Integer(), sa.ForeignKey('category_fields.id', ondelete='CASCADE'), nullable=False),
        sa.Column('option_key', sa.String(length=64), nullable=False),
        sa.Column('option_label', sa.String(length=255), nullable=False),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
    )
    op.create_index('ix_category_field_options_field_id', 'category_field_options', ['field_id'])

    # 4. Create advertising_requests table
    op.create_table(
        'advertising_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('request_number', sa.String(length=64), unique=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_id', sa.String(length=64), nullable=False),
        sa.Column('subcategory_id', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='COLLECTING_INFORMATION', nullable=False),
        sa.Column('price', sa.Integer(), nullable=True),
        sa.Column('currency', sa.String(length=10), server_default='UZS', nullable=False),
        sa.Column('card_number', sa.String(length=64), nullable=True),
        sa.Column('cardholder', sa.String(length=255), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('assigned_admin_id', sa.BigInteger(), nullable=True),
        sa.Column('preview_text', sa.Text(), nullable=True),
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('groups.id', ondelete='SET NULL'), nullable=True),
        sa.Column('published_message_id', sa.BigInteger(), nullable=True),
        sa.Column('published_chat_id', sa.BigInteger(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_advertising_requests_request_number', 'advertising_requests', ['request_number'])
    op.create_index('ix_advertising_requests_user_id', 'advertising_requests', ['user_id'])
    op.create_index('ix_advertising_requests_category_id', 'advertising_requests', ['category_id'])
    op.create_index('ix_advertising_requests_status', 'advertising_requests', ['status'])

    # 5. Create advertisement_answers table
    op.create_table(
        'advertisement_answers',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('request_id', sa.Integer(), sa.ForeignKey('advertising_requests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('field_id', sa.String(length=64), nullable=False),
        sa.Column('field_label', sa.String(length=255), nullable=True),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_advertisement_answers_request_id', 'advertisement_answers', ['request_id'])
    op.create_index('ix_advertisement_answers_field_id', 'advertisement_answers', ['field_id'])

    # 6. Create advertisement_media table
    op.create_table(
        'advertisement_media',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('request_id', sa.Integer(), sa.ForeignKey('advertising_requests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('media_type', sa.String(length=50), server_default='PHOTO', nullable=False),
        sa.Column('file_id', sa.String(length=255), nullable=False),
        sa.Column('file_unique_id', sa.String(length=255), nullable=True),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_advertisement_media_request_id', 'advertisement_media', ['request_id'])

    # 7. Create publication_jobs table
    op.create_table(
        'publication_jobs',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('request_id', sa.Integer(), sa.ForeignKey('advertising_requests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('message_id', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_publication_jobs_request_id', 'publication_jobs', ['request_id'])
    op.create_index('ix_publication_jobs_status', 'publication_jobs', ['status'])

    # 8. Update payments table: add request_id, alter order_id nullable
    with op.batch_alter_table('payments') as batch_op:
        batch_op.add_column(sa.Column('request_id', sa.Integer(), nullable=True))
        batch_op.alter_column('order_id', existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    op.drop_table('publication_jobs')
    op.drop_table('advertisement_media')
    op.drop_table('advertisement_answers')
    op.drop_table('advertising_requests')
    op.drop_table('category_field_options')
    op.drop_table('category_fields')
    op.drop_table('advertisement_categories')
