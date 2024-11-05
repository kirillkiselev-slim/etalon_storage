from datetime import datetime

from sqlalchemy import (Integer, String, Text, ForeignKey, DECIMAL,
                        DateTime, func, UniqueConstraint, CheckConstraint)
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates

from .db import Base
from app.core.constants import (PRODUCTS_STATUSES, PRODUCTION_BATCHES_STATUSES,
                                SHIPMENTS_STATUSES)

class Product(Base):
    """
    Класс для представления продукта. Содержит поля:
    id, name, description, price, amount_left и связь с OrderItem.
    Обеспечивает уникальность имени и проверку на положительные
    значения цены и количества.
    """

    __tablename__ = 'products'
    __table_args__ = (
        CheckConstraint(f'status in {PRODUCTS_STATUSES}',
                        name='check_status')
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default='OUT_OF_STOCK',
    )
    # description: Mapped[str] = mapped_column(Text, nullable=True)
    # price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    # amount_left: Mapped[int] = mapped_column(Integer, nullable=False)

    shipment_items: Mapped[list['ShipmentItems']] = relationship(
        'ShipmentItem', back_populates='product', cascade='all, delete-orphan')

    def validate_status(self, statuses, value):
        return super().validate_status(
            statuses=PRODUCTS_STATUSES, value=self.status)

    def __repr__(self):
        return (f'<Product(id={self.id}, name="{self.name}",'
                f' price={self.price})>')

    def __str__(self):
        return (f'Product "{self.name}" (ID: {self.id}) - '
                f'Price: {self.price}, Stock: {self.amount_left}')


class Shipment(Base):
    """
    Класс для представления shipment. Содержит поля:
    id, shipped_at, product_id и связь с OrderItem.
    По умолчанию статус - "PENDING", дата создания устанавливается автоматически.
    """

    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(
        String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default='OUT_OF_STOCK')
    shipped_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    # order_items: Mapped[list['OrderItem']] = relationship(
    #     'OrderItem', back_populates='order', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Shipment(id={self.id}, status="{self.status}"'

    def __str__(self):
        return f'Shipment #{self.id} - Status: {self.status}'


class ShipmentItems(Base):
    """
    Класс для представления позиции заказа (ShipementItem).
    Связывает заказ и продукт, указывая количество продукта в заказе.
    Содержит уникальное ограничение на сочетание order_id и
    product_id для предотвращения дублирования.
    """

    __tablename__ = 'shipment_items'
    __table_args__ = (
        UniqueConstraint('shipment_id', 'product_id',
                         name='unique_order_product'),
        CheckConstraint('quantity >= 0', name='check_amount')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_id: Mapped[int] = mapped_column(
        ForeignKey('shipment.id',  ondelete='CASCADE'))
    product_id: Mapped[int] = mapped_column(
        ForeignKey('products.id',  ondelete='CASCADE'))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    shipment: Mapped['Shipment'] = relationship('Shipment',
                                                back_populates='shipment_items')
    product: Mapped['Product'] = relationship('Product',
                                              back_populates='shipment_items')

    def __repr__(self):
        return (f'<ShipmentItem(id={self.id}, product_id={self.product_id},'
                f'quantity ={self.quantity})>')

    def __str__(self):
        product_model = self.product.model
        return (f'OrderItem #{self.id} Product: "{product_model}",'
                f' Quantity: {self.quantity}')
