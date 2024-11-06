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
    Класс для представления продукта. Содержит поля:
    id, name, description, price, amount_left и связь с OrderItem.
    Обеспечивает уникальность имени и проверку на положительные
    значения цены и количества.
    """

    __tablename__ = 'products'
    __table_args__ = (
        CheckConstraint(f'status in {PRODUCTS_STATUSES}',
                        name='check_product_status'),
    )

    model: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default='OUT_OF_STOCK')

    production_batches: Mapped['ProductionBatches'] = relationship(
        'ProductionBatches', back_populates='product',
        cascade='save-update, merge, expunge, refresh-expire')

    warehouse_inventory: Mapped['WarehouseInventory'] = relationship(
        'WarehouseInventory', back_populates='product',
        cascade='save-update, merge, expunge, refresh-expire')

    def __repr__(self):
        return (f'<Product(id={self.id}, name="{self.name}",'
                f' price={self.price})>')

    def __str__(self):
        return (f'Product "{self.name}" (ID: {self.id}) - '
                f'Price: {self.price}, Stock: {self.amount_left}')


class ProductionBatches(BaseEntity):
    """

    """

    __tablename__ = 'production_batches'
    __table_args__ = (
        CheckConstraint(f'current_stage in {PRODUCTION_BATCHES_STATUSES}',
                        name='check_stage'),
    )

    start_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    current_stage: Mapped[str] = mapped_column(String(50), nullable=False,
                                               default='INITIALIZED')
    product_id: Mapped[str] = mapped_column(String, ForeignKey(
        'products.model'))
    product: Mapped['Product'] = relationship(
        'Product', back_populates='production_batches')

    def __repr__(self):
        return (f'<ProductionBatches(id={self.id},'
                f' product_id={self.product_id},'
                f' current_stage="{self.current_stage}")>')

    def __str__(self):
        return (f'ProductionBatches # {self.id} with product'
                f' {self.product.product.model}'
                f' with stage {self.current_stage}')


class WarehouseInventory(BaseEntity):
    """

    """

    __tablename__ = 'warehouse_inventory'

    product_id: Mapped[str] = mapped_column(Integer, ForeignKey(
        'products.id', ondelete='CASCADE'))
    storage_location: Mapped[str] = mapped_column(
        String(50), nullable=False)
    product: Mapped['Product'] = relationship(
        'Product', back_populates='product_warehouse',
        cascade='all, delete-orphan')

    def __repr__(self):
        return (f'<WarehouseInventory(id={self.id},'
                f' product_id="{self.product_id}"'
                f' storage_location="{self.storage_location}")>')

    def __str__(self):
        return (f'WarehouseInventory # {self.id} with product'
                f' {self.producd.product.model}'
                f' located at {self.storage_location}')


class Shipment(BaseEntity):
    """
    Класс для представления shipment. Содержит поля:
    id, shipped_at, product_id и связь с OrderItem.
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
        'OrderItem', back_populates='shipment', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Shipment(id={self.id}, status="{self.status})>"'

    def __str__(self):
        return f'Shipment #{self.id} - Status: {self.status}'


class ShipmentItems(BaseEntity):
    """
    Класс для представления позиции заказа (ShipmentItem).
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
    product_id: Mapped[int] = mapped_column(
        ForeignKey('products.id', ondelete='CASCADE'))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    shipment: Mapped['Shipment'] = relationship(
        'Shipment', back_populates='shipment_items',
        cascade='all, delete-orphan')
    product: Mapped['Product'] = relationship(
        'Product', back_populates='shipment_items',
        cascade='all, delete-orphan')

    def __repr__(self):
        return (f'<ShipmentItem(id={self.id}, product_id={self.product_id},'
                f'quantity={self.quantity})>')

    def __str__(self):
        product_model = self.product.model
        return (f'OrderItem #{self.id} Product: "{product_model}",'
                f' Quantity: {self.quantity}')
