"""New changes

Revision ID: 8fd7a9b32868
Revises: 67bee086f30a
Create Date: 2024-11-17 17:25:26.672137

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8fd7a9b32868'
down_revision: Union[str, None] = '67bee086f30a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('products',
    sa.Column('product_uuid', sa.String(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('serial_number', sa.String(length=255), nullable=False),
    sa.Column('name_model', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.CheckConstraint("status in ('IN_PRODUCTION', 'IN_STOCK', 'OUT_OF_STOCK')", name='check_product_status'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('serial_number')
    )
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=True)
    op.create_index(op.f('ix_products_name_model'), 'products', ['name_model'], unique=True)
    op.create_index(op.f('ix_products_product_uuid'), 'products', ['product_uuid'], unique=True)
    op.create_table('shipment',
    sa.Column('order_id', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('shipped_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.CheckConstraint("status in ('PENDING', 'SHIPPED', 'CANCELLED')", name='check_shipment_status'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('order_id')
    )
    op.create_table('production_batches',
    sa.Column('start_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('current_stage', sa.String(length=50), nullable=False),
    sa.Column('quantity_in_batch', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.CheckConstraint("current_stage in ('INITIALIZED', 'PRODUCTION_STARTED', 'COMPLETED')", name='check_stage'),
    sa.CheckConstraint('quantity_in_batch >= 1', name='check_quantity_batch'),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('shipment_items',
    sa.Column('shipment_id', sa.Integer(), nullable=False),
    sa.Column('batch_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['batch_id'], ['production_batches.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['shipment_id'], ['shipment.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('shipment_id', 'batch_id', name='check_batche_shipment')
    )
    op.create_table('warehouse_inventory',
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('storage_location', sa.String(length=50), nullable=False),
    sa.Column('stock_quantity', sa.Integer(), nullable=False),
    sa.Column('batch_id', sa.Integer(), nullable=False),
    sa.Column('in_shipment', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.CheckConstraint('stock_quantity >= 0', name='check_amount'),
    sa.ForeignKeyConstraint(['batch_id'], ['production_batches.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('warehouse_inventory')
    op.drop_table('shipment_items')
    op.drop_table('production_batches')
    op.drop_table('shipment')
    op.drop_index(op.f('ix_products_product_uuid'), table_name='products')
    op.drop_index(op.f('ix_products_name_model'), table_name='products')
    op.drop_index(op.f('ix_products_name'), table_name='products')
    op.drop_table('products')
    # ### end Alembic commands ###
