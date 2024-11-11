import uuid
from datetime import datetime

from sqlalchemy import (Integer, String, ForeignKey, DECIMAL,
                        DateTime, func, UniqueConstraint, CheckConstraint)
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates

from .db import Base
from app.core.constants import (PRODUCTS_STATUSES, PRODUCTION_BATCHES_STATUSES,
                                SHIPMENTS_STATUSES)


class BaseEntity(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)


class Product(BaseEntity):
    """
    Класс для представления продукта.
    """

    __tablename__ = 'products'
    __table_args__ = (
        CheckConstraint(f'status in {PRODUCTS_STATUSES}',
                        name='check_product_status'),
    )
    product_uuid: Mapped[uuid.UUID] = mapped_column(
        index=True, nullable=False, unique=True
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    serial_number: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True)
    model_name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default='IN_PRODUCTION')

    production_batches: Mapped['ProductionBatches'] = relationship(
        'ProductionBatches', back_populates='product',
        cascade='save-update, merge, expunge, refresh-expire')

    warehouse_inventory: Mapped['WarehouseInventory'] = relationship(
        'WarehouseInventory', back_populates='product',
        cascade='save-update, merge, expunge, refresh-expire')
    shipment_items: Mapped['ShipmentItems'] = relationship(
        'ShipmentItems', back_populates='product'
    )

    def __repr__(self):
        return f'<Product(id={self.id}, model_name="{self.model_name}">'

    def __str__(self):
        return (f'Product "{self.name}" (ID: {self.id}) - '
                f'Name: {self.name}, Model name: {self.model_name}')


class ProductionBatches(BaseEntity):
    """

    """

    __tablename__ = 'production_batches'
    __table_args__ = (
        CheckConstraint(f'current_stage in {PRODUCTION_BATCHES_STATUSES}',
                        name='check_stage'),
        CheckConstraint('quantity_in_batch >= 1', name='check_quantity_batch')
    )

    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    current_stage: Mapped[str] = mapped_column(String(50), nullable=False,
                                               default='INITIALIZED')
    quantity_in_batch: Mapped[int] = mapped_column(Integer, nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey(
        'products.id'))
    product: Mapped['Product'] = relationship(
        'Product', back_populates='production_batches')
    warehouse_inventory: Mapped['WarehouseInventory'] = relationship(
        'WarehouseInventory', back_populates='batch')

    def __repr__(self):
        return (f'<ProductionBatches(id={self.id},'
                f' product_id={self.product_id},'
                f' current_stage="{self.current_stage}">')

    def __str__(self):
        return (f'ProductionBatches # {self.id} with product'
                f' {self.product.product.model_name}'
                f' with stage {self.current_stage}')


class WarehouseInventory(BaseEntity):
    """

    """

    __tablename__ = 'warehouse_inventory'
    __table_args__ = (
        CheckConstraint('quantity_received >= 0', name='check_amount'),
    )

    product_id: Mapped[int] = mapped_column(ForeignKey(
        'products.id', ondelete='CASCADE'))
    storage_location: Mapped[str] = mapped_column(
        String(50), nullable=False)
    product: Mapped['Product'] = relationship(
        'Product', back_populates='warehouse_inventory')
    quantity_received: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey('production_batches.id'), nullable=False)
    batch: Mapped['ProductionBatches'] = relationship(
        'ProductionBatches', back_populates='warehouse_inventory')

    def __repr__(self):
        return (f'<WarehouseInventory(id={self.id},'
                f' product_id="{self.product_id}"'
                f' storage_location="{self.storage_location}">')

    def __str__(self):
        return (f'WarehouseInventory # {self.id} with product'
                f' {self.product_id}'
                f' located at {self.storage_location}')


class Shipment(BaseEntity):
    """
    Класс для представления shipment. Содержит поля:
    id, shipped_at, product_id и связь ShipmentItems.
    По умолчанию статус - "PENDING", дата создания устанавливается автоматически.
    """

    __tablename__ = 'shipment'
    __table_args__ = (
        CheckConstraint(f'status in {SHIPMENTS_STATUSES}',
                        name='check_shipment_status'),
    )

    order_id: Mapped[str] = mapped_column(
        String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default='PENDING')
    shipped_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    shipment_items: Mapped[list['ShipmentItems']] = relationship(
        'ShipmentItems', back_populates='shipment', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Shipment(id={self.id}, status="{self.status}>"'

    def __str__(self):
        return f'Shipment #{self.id} - Status: {self.status}'


class ShipmentItems(BaseEntity):
    """
    Класс для представления позиции заказа (ShipmentItems).
    Связывает заказ и продукт, указывая количество продукта в заказе.
    Содержит уникальное ограничение на сочетание order_id и
    product_id для предотвращения дублирования.
    """

    __tablename__ = 'shipment_items'
    __table_args__ = (
        UniqueConstraint('shipment_id', 'product_id',
                         name='unique_order_product'),
        CheckConstraint('quantity >= 1', name='check_amount')
    )

    shipment_id: Mapped[int] = mapped_column(
        ForeignKey('shipment.id', ondelete='CASCADE'))
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('products.id', ondelete='CASCADE'))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    shipment: Mapped['Shipment'] = relationship(
        'Shipment', back_populates='shipment_items')
    product: Mapped['Product'] = relationship(
        'Product', back_populates='shipment_items', )

    def __repr__(self):
        return (f'<ShipmentItem(id={self.id}, product_id={self.product_id},'
                f'quantity={self.quantity}>')

    def __str__(self):
        product_model = self.product.model_name
        return (f'OrderItem #{self.id} Product: "{product_model}",'
                f' Quantity: {self.quantity}')
